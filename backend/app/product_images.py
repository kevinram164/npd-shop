"""Reliable product gallery URLs — 5 per SKU.

Uses Picsum seeds (always HTTP 200) + optional Unsplash hero when available.
Broken Unsplash IDs previously caused empty/broken tiles in the shop UI.
"""

from __future__ import annotations

PICSUM = "https://picsum.photos/seed/{seed}/900/900"

# Optional Unsplash heroes (verified). If missing, all 5 slots are Picsum.
HERO: dict[str, str] = {
    "headphones": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?auto=format&fit=crop&w=1000&q=80",
    "mouse": "https://images.unsplash.com/photo-1527864550417-7fd91fc51a46?auto=format&fit=crop&w=1000&q=80",
    "keyboard": "https://images.unsplash.com/photo-1511467687858-23d96c32e4ae?auto=format&fit=crop&w=1000&q=80",
    "sneakers": "https://images.unsplash.com/photo-1542291026-7eec264c27ff?auto=format&fit=crop&w=1000&q=80",
    "watch": "https://images.unsplash.com/photo-1523275335684-37898b6baf30?auto=format&fit=crop&w=1000&q=80",
    "tshirt": "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?auto=format&fit=crop&w=1000&q=80",
    "coffee": "https://images.unsplash.com/photo-1447933601403-0c6688de566e?auto=format&fit=crop&w=1000&q=80",
    "book": "https://images.unsplash.com/photo-1544947950-fa07a98d237f?auto=format&fit=crop&w=1000&q=80",
    "thermos": "https://images.unsplash.com/photo-1602143407151-7111542de6e8?auto=format&fit=crop&w=1000&q=80",
    "serum": "https://images.unsplash.com/photo-1620916569809-dfdb3825243f?auto=format&fit=crop&w=1000&q=80",
    "yoga": "https://images.unsplash.com/photo-1544367567-0f2fcb009e0b?auto=format&fit=crop&w=1000&q=80",
    "speaker": "https://images.unsplash.com/photo-1545454675-3531b543be5d?auto=format&fit=crop&w=1000&q=80",
    "jeans": "https://images.unsplash.com/photo-1542272454315-7ad9f8bbd8ea?auto=format&fit=crop&w=1000&q=80",
    "chocolate": "https://images.unsplash.com/photo-1511381939415-e44015466834?auto=format&fit=crop&w=1000&q=80",
    "notebook": "https://images.unsplash.com/photo-1517842645767-c639042777db?auto=format&fit=crop&w=1000&q=80",
    "lamp": "https://images.unsplash.com/photo-1507473885765-e6ed057f782c?auto=format&fit=crop&w=1000&q=80",
}

SKU_KIND: dict[str, str] = {
    "EL-001": "headphones",
    "EL-002": "mouse",
    "EL-003": "keyboard",
    "EL-004": "powerbank",
    "EL-005": "speaker",
    "EL-006": "webcam",
    "EL-007": "lamp",
    "EL-008": "hub",
    "FS-001": "tshirt",
    "FS-002": "jeans",
    "FS-003": "jacket",
    "FS-004": "sneakers",
    "FS-005": "tote",
    "FS-006": "hat",
    "FS-007": "socks",
    "FS-008": "watch",
    "HM-001": "thermos",
    "HM-002": "bowls",
    "HM-003": "pan",
    "HM-004": "blender",
    "HM-005": "tablecloth",
    "HM-006": "nightlight",
    "HM-007": "containers",
    "HM-008": "mop",
    "FD-001": "coffee",
    "FD-002": "tea",
    "FD-003": "nuts",
    "FD-004": "honey",
    "FD-005": "cookies",
    "FD-006": "fishsauce",
    "FD-007": "rice",
    "FD-008": "chocolate",
    "BK-001": "notebook",
    "BK-002": "pens",
    "BK-003": "book",
    "BK-004": "book",
    "BK-005": "folder",
    "BK-006": "laptopstand",
    "BK-007": "whiteboard",
    "BK-008": "sticky",
    "BT-001": "serum",
    "BT-002": "cleanser",
    "BT-003": "sunscreen",
    "BT-004": "toothbrush",
    "BT-005": "yoga",
    "BT-006": "shaker",
}


def urls_for_sku(sku: str, count: int = 5) -> list[str]:
    kind = SKU_KIND.get(sku, "product")
    out: list[str] = []
    hero = HERO.get(kind)
    if hero:
        out.append(hero)
    while len(out) < count:
        i = len(out)
        out.append(PICSUM.format(seed=f"noli-{sku}-{kind}-{i}"))
    return out[:count]
