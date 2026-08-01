from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from common.config import settings
from common.database import Base, SessionLocal, engine, get_db
from common.db_bootstrap import init_db_in_background
from common.models import Product
from common.observability import instrument_fastapi
from common.product_images import urls_for_sku
from common.schemas import CategoryOut, ProductOut
from common.security import require_internal
from common.seed_catalog import seed_products

SERVICE = "noli-catalog-service"


def _product_out(product: Product) -> ProductOut:
    # Derive gallery from SKU every request — avoids stale/broken Unsplash IDs in DB
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


def _seed_catalog() -> None:
    db = SessionLocal()
    try:
        n = seed_products(db)
        if n:
            print(f"[{SERVICE}] seeded {n} products", flush=True)
    finally:
        db.close()


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db_in_background(
        label=SERVICE,
        create_schema=lambda: Base.metadata.create_all(bind=engine),
        seed=_seed_catalog if settings.seed_on_startup else None,
    )
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


@app.get("/api/categories", response_model=list[CategoryOut])
def list_categories(db: Session = Depends(get_db)):
    rows = db.execute(
        select(Product.category, func.count(Product.id))
        .group_by(Product.category)
        .order_by(Product.category)
    ).all()
    return [CategoryOut(name=name, count=count) for name, count in rows]


@app.get("/api/products", response_model=list[ProductOut])
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


@app.get("/api/products/{product_id}", response_model=ProductOut)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(404, "Không tìm thấy sản phẩm")
    return _product_out(product)


@app.post("/internal/products/reserve")
def reserve_stock(
    payload: dict,
    db: Session = Depends(get_db),
    _: None = Depends(require_internal),
):
    """Called by order-service: {items:[{product_id, quantity}, ...]}"""
    items = payload.get("items") or []
    product_ids = [i["product_id"] for i in items]
    products = {
        p.id: p
        for p in db.execute(select(Product).where(Product.id.in_(product_ids))).scalars()
    }
    if len(products) != len(set(product_ids)):
        raise HTTPException(400, "Có sản phẩm không tồn tại")
    lines = []
    for item in items:
        product = products[item["product_id"]]
        qty = int(item["quantity"])
        if product.stock < qty:
            raise HTTPException(409, f"«{product.name}» chỉ còn {product.stock} sản phẩm")
        product.stock -= qty
        lines.append(
            {
                "product_id": product.id,
                "product_name": product.name,
                "unit_price_vnd": product.price_vnd,
                "quantity": qty,
            }
        )
    db.commit()
    return {"lines": lines}
