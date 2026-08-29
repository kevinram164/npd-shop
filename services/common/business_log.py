"""Structured JSON logs for OpenSearch dashboards (shop)."""

from __future__ import annotations

import json
import logging
import os
import time
from typing import Any

log = logging.getLogger("noli.business")


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
    line = json.dumps(payload, ensure_ascii=False)
    logging.getLogger().info(line)
