"""Structured JSON logs for OpenSearch dashboards (shop)."""

from __future__ import annotations

import json
import logging
import os
import time
from typing import Any

_json_logger: logging.Logger | None = None


def _get_json_logger() -> logging.Logger:
    """Pure JSON lines (no level/logger prefix) — Fluent Bit json parser → field event."""
    global _json_logger
    if _json_logger is not None:
        return _json_logger
    logger = logging.getLogger("noli.business")
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(message)s"))
        logger.addHandler(handler)
        logger.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())
        logger.propagate = False
    _json_logger = logger
    return logger


def log_business(event: str, **fields: Any) -> None:
    """One JSON line per business event — Fluent Bit parser → Dashboards."""
    if os.getenv("LOG_BUSINESS_JSON", "true").lower() not in ("true", "1", "yes"):
        return
    service = os.getenv("OTEL_SERVICE_NAME", "npd-shop")
    payload = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()),
        "event": event,
        "service": service,
        "domain": "shop",
        **fields,
    }
    _get_json_logger().info(json.dumps(payload, ensure_ascii=False))
