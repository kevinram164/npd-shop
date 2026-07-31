"""Optional Kafka publish — no-op if KAFKA_BOOTSTRAP empty."""

from __future__ import annotations

import json
import logging

from common.config import settings

log = logging.getLogger("noli.kafka")


def publish_json(topic: str, payload: dict, key: str | None = None) -> bool:
    bootstrap = settings.kafka_bootstrap.strip()
    if not bootstrap:
        log.info("kafka skipped (no bootstrap): topic=%s key=%s", topic, key)
        return False
    try:
        from kafka import KafkaProducer

        producer = KafkaProducer(
            bootstrap_servers=bootstrap.split(","),
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            key_serializer=lambda v: v.encode("utf-8") if v else None,
        )
        producer.send(topic, value=payload, key=key)
        producer.flush(timeout=5)
        producer.close()
        log.info("kafka published topic=%s key=%s", topic, key)
        return True
    except Exception as exc:
        log.warning("kafka publish failed: %s", exc)
        return False
