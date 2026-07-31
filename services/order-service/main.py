from __future__ import annotations

import secrets
import string
from contextlib import asynccontextmanager
from datetime import datetime, timezone

import httpx
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from common.config import settings
from common.database import Base, engine, get_db
from common.kafka_bus import publish_json
from common.models import Order, OrderItem, OrderStatus, User
from common.observability import instrument_fastapi
from common.schemas import (
    AdminOrderStatusIn,
    AdminStatsOut,
    BankTransferInfo,
    CheckoutIn,
    MarkPaidIn,
    OrderOut,
)
from common.security import (
    get_current_user,
    get_optional_user,
    require_admin,
    require_internal,
)

SERVICE = "noli-order-service"
VALID_STATUSES = {s.value for s in OrderStatus}


def _payment_info(order: Order) -> BankTransferInfo:
    return BankTransferInfo(
        bank_name=settings.bank_name,
        account_name=settings.bank_account_name,
        account_number=settings.bank_account_number,
        transfer_ref=order.transfer_ref,
        amount_vnd=order.total_vnd,
        instruction=(
            f"Chuyển khoản đúng {order.total_vnd} VND và ghi nội dung "
            f"chính xác: {order.transfer_ref}"
        ),
    )


def _order_out(order: Order) -> OrderOut:
    data = OrderOut.model_validate(order)
    if order.status in (
        OrderStatus.pending_payment.value,
        OrderStatus.amount_mismatch.value,
        OrderStatus.paid.value,
    ):
        data.payment = _payment_info(order)
    return data


def _gen_code(prefix: str, length: int = 6) -> str:
    alphabet = string.ascii_uppercase + string.digits
    return f"{prefix}-{''.join(secrets.choice(alphabet) for _ in range(length))}"


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title=SERVICE, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
instrument_fastapi(app, SERVICE)


@app.get("/health")
def health():
    return {"status": "ok", "service": SERVICE}


@app.post("/api/orders", response_model=OrderOut, status_code=201)
def create_order(
    payload: CheckoutIn,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
):
    # Cross-service call → Instana edge: order-service → catalog-service
    with httpx.Client(timeout=10.0) as client:
        resp = client.post(
            f"{settings.catalog_url}/internal/products/reserve",
            json={"items": [i.model_dump() for i in payload.items]},
            headers={"X-Internal-Token": settings.internal_token},
        )
        if resp.status_code >= 400:
            detail = resp.json().get("detail", resp.text) if resp.content else resp.text
            raise HTTPException(resp.status_code, detail)
        lines = resp.json()["lines"]

    total = sum(l["unit_price_vnd"] * l["quantity"] for l in lines)
    order = Order(
        user_id=user.id if user else None,
        order_code=_gen_code("ORD", 8),
        transfer_ref=_gen_code(settings.transfer_prefix, 6),
        customer_name=payload.customer_name.strip(),
        customer_phone=payload.customer_phone.strip(),
        customer_address=payload.customer_address.strip(),
        total_vnd=total,
        status=OrderStatus.pending_payment.value,
        note=payload.note,
    )
    for line in lines:
        order.items.append(
            OrderItem(
                product_id=line["product_id"],
                product_name=line["product_name"],
                unit_price_vnd=line["unit_price_vnd"],
                quantity=line["quantity"],
            )
        )
    db.add(order)
    db.commit()
    db.refresh(order)
    order = db.execute(
        select(Order).options(selectinload(Order.items)).where(Order.id == order.id)
    ).scalar_one()

    publish_json(
        settings.kafka_orders_topic,
        {
            "event": "order.created",
            "order_code": order.order_code,
            "transfer_ref": order.transfer_ref,
            "total_vnd": order.total_vnd,
            "status": order.status,
        },
        key=order.transfer_ref,
    )
    return _order_out(order)


@app.get("/api/orders/mine", response_model=list[OrderOut])
def my_orders(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    orders = (
        db.execute(
            select(Order)
            .options(selectinload(Order.items))
            .where(Order.user_id == user.id)
            .order_by(Order.created_at.desc())
        )
        .scalars()
        .all()
    )
    return [_order_out(o) for o in orders]


@app.get("/api/orders/{order_code}", response_model=OrderOut)
def get_order(order_code: str, db: Session = Depends(get_db)):
    order = db.execute(
        select(Order)
        .options(selectinload(Order.items))
        .where(Order.order_code == order_code)
    ).scalar_one_or_none()
    if not order:
        raise HTTPException(404, "Không tìm thấy đơn hàng")
    return _order_out(order)


@app.post("/internal/orders/apply-payment", response_model=OrderOut)
def apply_payment(
    payload: MarkPaidIn,
    db: Session = Depends(get_db),
    _: None = Depends(require_internal),
):
    """Called by payment-worker after matching bank transfer."""
    order = db.execute(
        select(Order)
        .options(selectinload(Order.items))
        .where(Order.transfer_ref == payload.transfer_ref.strip().upper())
    ).scalar_one_or_none()
    if not order:
        raise HTTPException(404, "Không tìm thấy mã chuyển khoản")
    if order.status == OrderStatus.paid.value:
        return _order_out(order)

    order.paid_amount_vnd = payload.amount_vnd
    order.paid_at = datetime.now(timezone.utc)
    if payload.force_status:
        if payload.force_status not in VALID_STATUSES:
            raise HTTPException(400, "Trạng thái không hợp lệ")
        order.status = payload.force_status
    elif payload.amount_vnd == order.total_vnd:
        order.status = OrderStatus.paid.value
    else:
        order.status = OrderStatus.amount_mismatch.value
    db.commit()
    db.refresh(order)

    publish_json(
        settings.kafka_payments_topic,
        {
            "event": "payment.applied",
            "transfer_ref": order.transfer_ref,
            "order_code": order.order_code,
            "status": order.status,
            "amount_vnd": order.paid_amount_vnd,
        },
        key=order.transfer_ref,
    )
    return _order_out(order)


@app.get("/api/admin/stats", response_model=AdminStatsOut)
def admin_stats(_: User = Depends(require_admin), db: Session = Depends(get_db)):
    def count_status(status: str) -> int:
        return db.execute(select(func.count(Order.id)).where(Order.status == status)).scalar() or 0

    total = db.execute(select(func.count(Order.id))).scalar() or 0
    revenue = (
        db.execute(
            select(func.coalesce(func.sum(Order.total_vnd), 0)).where(
                Order.status == OrderStatus.paid.value
            )
        ).scalar()
        or 0
    )
    return AdminStatsOut(
        total=total,
        pending_payment=count_status(OrderStatus.pending_payment.value),
        paid=count_status(OrderStatus.paid.value),
        amount_mismatch=count_status(OrderStatus.amount_mismatch.value),
        failed=count_status(OrderStatus.failed.value),
        cancelled=count_status(OrderStatus.cancelled.value),
        expired=count_status(OrderStatus.expired.value),
        revenue_paid_vnd=int(revenue),
    )


@app.get("/api/admin/orders", response_model=list[OrderOut])
def admin_orders(
    status: str | None = None,
    q: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    stmt = (
        select(Order)
        .options(selectinload(Order.items))
        .order_by(Order.created_at.desc())
        .limit(limit)
    )
    if status:
        stmt = stmt.where(Order.status == status)
    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where(
            (Order.order_code.ilike(like))
            | (Order.transfer_ref.ilike(like))
            | (Order.customer_name.ilike(like))
            | (Order.customer_phone.ilike(like))
        )
    return [_order_out(o) for o in db.execute(stmt).scalars().all()]


@app.patch("/api/admin/orders/{order_code}", response_model=OrderOut)
def admin_update_order(
    order_code: str,
    payload: AdminOrderStatusIn,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    if payload.status not in VALID_STATUSES:
        raise HTTPException(400, f"Status hợp lệ: {', '.join(sorted(VALID_STATUSES))}")
    order = db.execute(
        select(Order)
        .options(selectinload(Order.items))
        .where(Order.order_code == order_code)
    ).scalar_one_or_none()
    if not order:
        raise HTTPException(404, "Không tìm thấy đơn hàng")
    order.status = payload.status
    if payload.status == OrderStatus.paid.value and not order.paid_at:
        order.paid_at = datetime.now(timezone.utc)
        order.paid_amount_vnd = order.total_vnd
    db.commit()
    db.refresh(order)
    return _order_out(order)
