# NOLI Shop (`npd-shop`)

Cửa hàng lifestyle demo — **microservices** (gateway / auth / catalog / order / payment-worker) để Instana/Coroot có dependency graph đẹp.

Xem chi tiết: [ARCHITECTURE.md](ARCHITECTURE.md)

## Quick start

```bash
docker compose up --build
```

- UI: http://localhost:5173  
- Gateway (Docker): http://localhost:8080/api/health  
- Gateway (local script, tránh đụng monolith cũ): http://localhost:8090/api/health  

## Services

| Service | Port |
|---------|------|
| gateway | 8080 |
| auth-service | 8001 |
| catalog-service | 8002 |
| order-service | 8003 |
| payment-worker | 8004 |
| shop-web | 5173 |
| postgres | 5433 |
| redpanda (Kafka) | 19092 |

## Auth & Admin

| Role | Email | Password |
|------|-------|----------|
| Admin | `admin@noli.shop` | `admin123` |

## Giả lập thanh toán

```bash
curl -X POST http://localhost:8080/api/payments/confirm \
  -H "Content-Type: application/json" \
  -d "{\"transfer_ref\":\"NOLI-XXXXXX\",\"amount_vnd\":249000}"
```

Luồng Instana: **gateway → payment-worker → order-service**.

## OTLP

```bash
export OTEL_EXPORTER_OTLP_ENDPOINT=http://opentelemetry-collector.observability.svc:4317
docker compose up --build
```

## Legacy

Thư mục `backend/` là monolith cũ — không dùng cho runtime mới. Dùng `services/`.
