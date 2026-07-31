from __future__ import annotations

import secrets
import string
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.auth import (
    create_access_token,
    find_user_by_email,
    get_current_user,
    get_optional_user,
    hash_password,
    require_admin,
    verify_password,
)
from app.config import settings
from app.database import get_db
from app.models import Order, OrderItem, OrderStatus, Product, User
from app.product_images import urls_for_sku
from app.schemas import (
    AdminOrderStatusIn,
    AdminStatsOut,
    BankTransferInfo,
    CategoryOut,
    CheckoutIn,
    LoginIn,
    MarkPaidIn,
    OrderOut,
    ProductOut,
    RegisterIn,
    TokenOut,
    UserOut,
)

router = APIRouter()

VALID_STATUSES = {s.value for s in OrderStatus}


def _product_out(product: Product) -> ProductOut:
    return ProductOut(
        id=product.id,
        sku=product.sku,
        name=product.name,
        description=product.description,
        category=product.category,
        price_vnd=product.price_vnd,
        stock=product.stock,
        image_hue=product.image_hue,
        image_emoji=product.image_emoji,
        images=urls_for_sku(product.sku, 5),
        badge=product.badge,
    )


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


@router.get("/health")
def health():
    return {"status": "ok", "service": "noli-shop-api"}


# ── Auth ──────────────────────────────────────────────────────────────


@router.post("/auth/register", response_model=TokenOut, status_code=201)
def register(payload: RegisterIn, db: Session = Depends(get_db)):
    email = payload.email.lower().strip()
    if find_user_by_email(db, email):
        raise HTTPException(409, "Email đã được đăng ký")
    user = User(
        email=email,
        password_hash=hash_password(payload.password),
        full_name=payload.full_name.strip(),
        phone=payload.phone.strip(),
        is_admin=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token(user.id, user.is_admin)
    return TokenOut(access_token=token, user=UserOut.model_validate(user))


@router.post("/auth/login", response_model=TokenOut)
def login(payload: LoginIn, db: Session = Depends(get_db)):
    user = find_user_by_email(db, payload.email.lower().strip())
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(401, "Email hoặc mật khẩu không đúng")
    token = create_access_token(user.id, user.is_admin)
    return TokenOut(access_token=token, user=UserOut.model_validate(user))


@router.get("/auth/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user


# ── Catalog ───────────────────────────────────────────────────────────


@router.get("/categories", response_model=list[CategoryOut])
def list_categories(db: Session = Depends(get_db)):
    rows = db.execute(
        select(Product.category, func.count(Product.id))
        .group_by(Product.category)
        .order_by(Product.category)
    ).all()
    return [CategoryOut(name=name, count=count) for name, count in rows]


@router.get("/products", response_model=list[ProductOut])
def list_products(
    category: str | None = None,
    q: str | None = None,
    db: Session = Depends(get_db),
):
    stmt = select(Product).order_by(Product.category, Product.name)
    if category:
        stmt = stmt.where(Product.category == category)
    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where(
            (Product.name.ilike(like))
            | (Product.description.ilike(like))
            | (Product.sku.ilike(like))
        )
    return [_product_out(p) for p in db.execute(stmt).scalars().all()]


@router.get("/products/{product_id}", response_model=ProductOut)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(404, "Không tìm thấy sản phẩm")
    return _product_out(product)


# ── Orders ────────────────────────────────────────────────────────────


@router.post("/orders", response_model=OrderOut, status_code=201)
def create_order(
    payload: CheckoutIn,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
):
    product_ids = [i.product_id for i in payload.items]
    products = {
        p.id: p
        for p in db.execute(select(Product).where(Product.id.in_(product_ids))).scalars()
    }
    if len(products) != len(set(product_ids)):
        raise HTTPException(400, "Có sản phẩm không tồn tại")

    line_rows: list[tuple[Product, int]] = []
    total = 0
    for item in payload.items:
        product = products[item.product_id]
        if product.stock < item.quantity:
            raise HTTPException(
                409,
                f"«{product.name}» chỉ còn {product.stock} sản phẩm",
            )
        line_rows.append((product, item.quantity))
        total += product.price_vnd * item.quantity

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
    for product, qty in line_rows:
        product.stock -= qty
        order.items.append(
            OrderItem(
                product_id=product.id,
                product_name=product.name,
                unit_price_vnd=product.price_vnd,
                quantity=qty,
            )
        )
    db.add(order)
    db.commit()
    db.refresh(order)
    order = db.execute(
        select(Order).options(selectinload(Order.items)).where(Order.id == order.id)
    ).scalar_one()
    return _order_out(order)


@router.get("/orders/mine", response_model=list[OrderOut])
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


@router.get("/orders/{order_code}", response_model=OrderOut)
def get_order(
    order_code: str,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
):
    order = db.execute(
        select(Order)
        .options(selectinload(Order.items))
        .where(Order.order_code == order_code)
    ).scalar_one_or_none()
    if not order:
        raise HTTPException(404, "Không tìm thấy đơn hàng")
    # Private orders: owner or admin can always view; public code still viewable for CK UX
    return _order_out(order)


@router.post("/payments/confirm", response_model=OrderOut)
def confirm_payment(payload: MarkPaidIn, db: Session = Depends(get_db)):
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
    return _order_out(order)


# ── Admin ─────────────────────────────────────────────────────────────


@router.get("/admin/stats", response_model=AdminStatsOut)
def admin_stats(_: User = Depends(require_admin), db: Session = Depends(get_db)):
    def count_status(status: str) -> int:
        return db.execute(
            select(func.count(Order.id)).where(Order.status == status)
        ).scalar() or 0

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


@router.get("/admin/orders", response_model=list[OrderOut])
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


@router.patch("/admin/orders/{order_code}", response_model=OrderOut)
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
