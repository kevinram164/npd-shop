"""API Gateway — single entry for frontend; fans out to microservices (Instana hub)."""

from __future__ import annotations

from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from common.config import settings
from common.observability import instrument_fastapi

SERVICE = "noli-shop-gateway"

ROUTES: list[tuple[str, str]] = [
    ("/api/auth", "auth_url"),
    ("/api/categories", "catalog_url"),
    ("/api/products", "catalog_url"),
    ("/api/admin/catalog", "catalog_url"),
    ("/api/orders", "order_url"),
    ("/api/admin", "order_url"),
    ("/api/payments", "payment_url"),
]


def _upstream(path: str) -> str | None:
    for prefix, attr in ROUTES:
        if path == prefix or path.startswith(prefix + "/") or path.startswith(prefix + "?"):
            return getattr(settings, attr)
        # also match exact resource roots
        if path.startswith(prefix):
            return getattr(settings, attr)
    return None


@asynccontextmanager
async def lifespan(_: FastAPI):
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
    """Liveness for K8s probes — gateway process only (no upstream fan-out)."""
    return {"status": "ok", "service": SERVICE}


@app.get("/api/health")
async def health_deep():
    """Deep check — upstreams; may return 503 when dependencies are down."""
    results = {}
    async with httpx.AsyncClient(timeout=3.0) as client:
        for name, url in [
            ("auth", settings.auth_url),
            ("catalog", settings.catalog_url),
            ("order", settings.order_url),
            ("payment", settings.payment_url),
        ]:
            try:
                r = await client.get(f"{url}/health")
                results[name] = r.json()
            except Exception as exc:
                results[name] = {"status": "down", "error": str(exc)}
    ok = all(v.get("status") == "ok" for v in results.values())
    return JSONResponse(
        {"status": "ok" if ok else "degraded", "service": SERVICE, "upstreams": results},
        status_code=200 if ok else 503,
    )


@app.api_route("/api/{full_path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
async def proxy(full_path: str, request: Request):
    path = f"/api/{full_path}"
    base = _upstream(path)
    if not base:
        return JSONResponse({"detail": f"No route for {path}"}, status_code=404)

    url = f"{base}{path}"
    if request.url.query:
        url = f"{url}?{request.url.query}"

    headers = {
        k: v
        for k, v in request.headers.items()
        if k.lower() not in ("host", "content-length")
    }
    body = await request.body()

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            upstream = await client.request(
                request.method, url, headers=headers, content=body
            )
        except httpx.RequestError as exc:
            return JSONResponse(
                {"detail": f"Upstream error: {exc}"}, status_code=502
            )

    excluded = {"content-encoding", "transfer-encoding", "content-length"}
    resp_headers = {
        k: v for k, v in upstream.headers.items() if k.lower() not in excluded
    }
    return Response(
        content=upstream.content,
        status_code=upstream.status_code,
        headers=resp_headers,
        media_type=upstream.headers.get("content-type"),
    )
