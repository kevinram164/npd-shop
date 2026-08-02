"""Optional Kafka publish — no-op if KAFKA_BOOTSTRAP empty.

Supports plain (lab) and SASL_SSL + SCRAM-SHA-512 (near-prod Strimzi).
"""

from __future__ import annotations

import json
import logging
import os

from common.config import settings
from common.kafka_auth import kafka_client_kwargs

log = logging.getLogger("noli.kafka")

_producer = None


def _get_producer():
    global _producer
    if _producer is not None:
        return _producer
    from kafka import KafkaProducer

    kw = kafka_client_kwargs()
    _producer = KafkaProducer(
        **kw,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        key_serializer=lambda v: v.encode("utf-8") if v else None,
        acks="all",
        enable_idempotence=True,
        retries=int(os.getenv("KAFKA_PRODUCER_RETRIES", "2147483647")),
        max_in_flight_requests_per_connection=5,
        linger_ms=int(os.getenv("KAFKA_LINGER_MS", "20")),
        batch_size=int(os.getenv("KAFKA_BATCH_SIZE", "32768")),
        delivery_timeout_ms=int(os.getenv("KAFKA_DELIVERY_TIMEOUT_MS", "120000")),
        compression_type=os.getenv("KAFKA_COMPRESSION", "lz4"),
    )
    return _producer


def publish_json(topic: str, payload: dict, key: str | None = None) -> bool:
    bootstrap = settings.kafka_bootstrap.strip()
    if not bootstrap:
        log.info("kafka skipped (no bootstrap): topic=%s key=%s", topic, key)
        return False
    try:
        producer = _get_producer()
        fut = producer.send(topic, value=payload, key=key)
        fut.get(timeout=30)
        log.info("kafka published topic=%s key=%s", topic, key)
        return True
    except Exception as exc:
        log.warning("kafka publish failed: %s", exc)
        return False
