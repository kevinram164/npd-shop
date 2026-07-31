"""Seed catalog SKUs + image galleries."""

import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from common.models import Product
from common.product_images import urls_for_sku

# Re-export catalog rows from monolith seed content
from common._catalog_data import CATALOG  # noqa: E402


def _with_images(row: dict) -> dict:
    data = dict(row)
    data["images_json"] = json.dumps(urls_for_sku(row["sku"], 5), ensure_ascii=False)
    return data


def seed_products(db: Session) -> int:
    existing = db.execute(select(Product.id).limit(1)).first()
    if existing:
        products = db.execute(select(Product)).scalars().all()
        updated = 0
        for p in products:
            new_json = json.dumps(urls_for_sku(p.sku, 5), ensure_ascii=False)
            if getattr(p, "images_json", None) != new_json:
                p.images_json = new_json
                updated += 1
        if updated:
            db.commit()
        return 0
    for row in CATALOG:
        db.add(Product(**_with_images(row)))
    db.commit()
    return len(CATALOG)
