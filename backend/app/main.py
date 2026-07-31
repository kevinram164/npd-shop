from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect, text

from app.config import settings
from app.database import Base, SessionLocal, engine
from app.routers import router
from app.seed import seed_admin, seed_products


def _migrate_sqlite() -> None:
    """Add new columns on existing SQLite DB without wiping data."""
    if not settings.database_url.startswith("sqlite"):
        return
    insp = inspect(engine)
    tables = insp.get_table_names()
    with engine.begin() as conn:
        if "products" in tables:
            cols = {c["name"] for c in insp.get_columns("products")}
            if "images_json" not in cols:
                conn.execute(
                    text("ALTER TABLE products ADD COLUMN images_json TEXT DEFAULT '[]'")
                )
        if "orders" in tables:
            cols = {c["name"] for c in insp.get_columns("orders")}
            if "user_id" not in cols:
                conn.execute(text("ALTER TABLE orders ADD COLUMN user_id INTEGER"))


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    _migrate_sqlite()
    if settings.seed_on_startup:
        db = SessionLocal()
        try:
            n = seed_products(db)
            if n:
                print(f"Seeded {n} products")
            if seed_admin(db):
                print(f"Seeded admin {settings.admin_email}")
        finally:
            db.close()
    yield


app = FastAPI(title=settings.app_name, version="0.2.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router, prefix="/api")
