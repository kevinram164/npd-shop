"""Payment worker — HTTP confirm (+ Kafka consumer when bootstrap set)."""

from __future__ import annotations

import json
import logging
import threading
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from common.config import settings
from common.business_log import log_business
from common.observability import consumer_span, get_tracer, instrument_fastapi
from common.schemas import MarkPaidIn, OrderOut

SERVICE = "noli-payment-worker"
log = logging.getLogger(SERVICE)
logging.basicConfig(level=logging.INFO)


def apply_to_order(payload: MarkPaidIn) -> dict:
    # Cross-service: payment-worker → order-service (Instana edge)
    with httpx.Client(timeout=10.0) as client:
        resp = client.post(
            f"{settings.order_url}/internal/orders/apply-payment",
            json=payload.model_dump(),
            headers={"X-Internal-Token": settings.internal_token},
        )
        if resp.status_code >= 400:
            detail = resp.json().get("detail", resp.text) if resp.content else resp.text
            raise HTTPException(resp.status_code, detail)
        return resp.json()


def _kafka_loop(stop: threading.Event) -> None:
    bootstrap = settings.kafka_bootstrap.strip()
    if not bootstrap:
        log.info("Kafka consumer disabled (no KAFKA_BOOTSTRAP)")
        return
    try:
        from kafka import KafkaConsumer
    except ImportError:
        log.warning("kafka-python not installed; consumer disabled")
        return

    from common.kafka_auth import kafka_client_kwargs

    tracer = get_tracer(SERVICE)
    consumer = KafkaConsumer(
        settings.kafka_payments_topic,
        **kafka_client_kwargs(),
        group_id="noli-payment-worker",
        value_deserializer=lambda b: json.loads(b.decode("utf-8")),
        auto_offset_reset="earliest",
        enable_auto_commit=False,
        max_poll_records=50,
    )
    log.info("Kafka consumer started topic=%s", settings.kafka_payments_topic)
    while not stop.is_set():
        records = consumer.poll(timeout_ms=1000)
        for _tp, msgs in records.items():
            for msg in msgs:
                data = msg.value or {}
                # Expect banking-shaped events: payment.completed
                if data.get("event") not in ("payment.completed", "payment.confirm"):
                    consumer.commit()
                    continue
                with consumer_span(
                    tracer,
                    "payments.events process",
                    {"messaging.destination": settings.kafka_payments_topic},
                ):
                    try:
                        result = apply_to_order(
                            MarkPaidIn(
                                transfer_ref=data["transfer_ref"],
                                amount_vnd=int(data["amount_vnd"]),
                                force_status=data.get("force_status"),
                            )
                        )
                        log_business(
                            "payment_received",
                            transfer_ref=data["transfer_ref"],
                            amount_vnd=int(data["amount_vnd"]),
                            order_code=result.get("order_code"),
                            status=result.get("status"),
                            outcome=result.get("status"),
                            source=data.get("source", "kafka"),
                        )
                        consumer.commit()
                    except Exception as exc:
                        log.exception("apply payment failed: %s", exc)
                        # Không commit → message được retry (at-least-once)
    consumer.close()


@asynccontextmanager
async def lifespan(_: FastAPI):
    stop = threading.Event()
    t = threading.Thread(target=_kafka_loop, args=(stop,), daemon=True)
    t.start()
    yield
    stop.set()


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
    return {
        "status": "ok",
        "service": SERVICE,
        "kafka": bool(settings.kafka_bootstrap.strip()),
    }


@app.post("/api/payments/confirm", response_model=OrderOut)
def confirm_payment(payload: MarkPaidIn):
    """Lab / banking webhook entry — routes through payment-worker node on Instana."""
    return apply_to_order(payload)
