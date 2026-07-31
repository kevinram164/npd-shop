"""OpenTelemetry + Prometheus — Instana/Coroot via OTLP collector."""

from __future__ import annotations

import logging
import os
import threading
import time

from prometheus_client import CollectorRegistry, Counter, Histogram, generate_latest

log = logging.getLogger("noli.otel")

_metrics_registry: CollectorRegistry | None = None
_request_count: Counter | None = None
_request_latency: Histogram | None = None
_heartbeat_started: set[str] = set()


def init_tracing(service_name: str) -> None:
    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "").strip()
    if not endpoint:
        return
    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        from opentelemetry.sdk.resources import SERVICE_NAME, Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        name = os.getenv("OTEL_SERVICE_NAME", service_name).strip() or service_name
        attrs = {
            SERVICE_NAME: name,
            "service.namespace": os.getenv("OTEL_SERVICE_NAMESPACE", "npd-shop"),
            "deployment.environment": os.getenv("DEPLOY_ENV", "local"),
        }
        raw = os.getenv("OTEL_RESOURCE_ATTRIBUTES", "").strip()
        for part in raw.split(","):
            if "=" in part:
                k, v = part.split("=", 1)
                attrs[k.strip()] = v.strip()

        resource = Resource.create(attrs)
        provider = TracerProvider(resource=resource)
        provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(insecure=True)))
        trace.set_tracer_provider(provider)

        try:
            from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
            from common.database import engine

            SQLAlchemyInstrumentor().instrument(engine=engine)
        except Exception:
            pass

        try:
            from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

            HTTPXClientInstrumentor().instrument()
        except Exception:
            pass
    except Exception:
        pass


def get_tracer(service_name: str):
    try:
        from opentelemetry import trace

        return trace.get_tracer(service_name, "1.0")
    except Exception:
        return None


def start_heartbeat(service_name: str) -> None:
    """
    Emit a lightweight SERVER span on an interval so Instana keeps the service
    visible without user traffic.

    Env:
      OTEL_HEARTBEAT=0|false  → disable
      OTEL_HEARTBEAT_SECONDS  → interval (default 30)
    """
    if not os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "").strip():
        return
    flag = os.getenv("OTEL_HEARTBEAT", "1").strip().lower()
    if flag in ("0", "false", "no", "off"):
        return
    if service_name in _heartbeat_started:
        return
    _heartbeat_started.add(service_name)

    try:
        interval = max(10, int(os.getenv("OTEL_HEARTBEAT_SECONDS", "30")))
    except ValueError:
        interval = 30

    tracer = get_tracer(service_name)
    if not tracer:
        return

    def _loop() -> None:
        from opentelemetry.trace import SpanKind, Status, StatusCode

        while True:
            try:
                with tracer.start_as_current_span(
                    "otel.heartbeat",
                    kind=SpanKind.SERVER,
                    attributes={
                        "heartbeat": True,
                        "service.name": service_name,
                        "http.route": "/__heartbeat__",
                    },
                ) as span:
                    span.set_status(Status(StatusCode.OK))
            except Exception as exc:
                log.debug("heartbeat failed: %s", exc)
            time.sleep(interval)

    threading.Thread(
        target=_loop, name=f"otel-hb-{service_name}", daemon=True
    ).start()
    log.info("otel heartbeat started service=%s every=%ss", service_name, interval)


def consumer_span(tracer, name: str, attributes: dict | None = None):
    if not tracer:
        from contextlib import nullcontext

        return nullcontext()
    from opentelemetry.trace import SpanKind

    attrs = {"messaging.system": "kafka", "messaging.operation": "process"}
    if attributes:
        attrs.update(attributes)
    return tracer.start_as_current_span(name, kind=SpanKind.CONSUMER, attributes=attrs)


def setup_metrics(service_name: str) -> None:
    global _metrics_registry, _request_count, _request_latency
    _metrics_registry = CollectorRegistry()
    _request_count = Counter(
        "http_requests_total",
        "Total HTTP requests",
        ["method", "endpoint", "status", "service"],
        registry=_metrics_registry,
    )
    _request_latency = Histogram(
        "http_request_duration_seconds",
        "HTTP request latency",
        ["method", "endpoint", "service"],
        registry=_metrics_registry,
    )


def get_metrics_content() -> bytes:
    if _metrics_registry is None:
        return b""
    return generate_latest(_metrics_registry)


def instrument_fastapi(app, service_name: str) -> None:
    init_tracing(service_name)
    setup_metrics(service_name)
    start_heartbeat(service_name)
    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

        FastAPIInstrumentor.instrument_app(app)
    except Exception:
        pass

    from fastapi import Response
    from starlette.middleware.base import BaseHTTPMiddleware

    class PrometheusMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request, call_next):
            if request.url.path in ("/metrics", "/health", "/api/health", "/__heartbeat__"):
                return await call_next(request)
            start = time.perf_counter()
            response = await call_next(request)
            duration = time.perf_counter() - start
            if _request_count and _request_latency:
                endpoint = request.url.path or "/"
                _request_count.labels(
                    method=request.method,
                    endpoint=endpoint,
                    status=response.status_code,
                    service=service_name,
                ).inc()
                _request_latency.labels(
                    method=request.method, endpoint=endpoint, service=service_name
                ).observe(duration)
            return response

    app.add_middleware(PrometheusMiddleware)

    @app.get("/metrics")
    async def metrics():
        return Response(content=get_metrics_content(), media_type="text/plain; charset=utf-8")
