# Instana — giữ service luôn hiện

## Vì sao chỉ hiện khi có request?

Instana **Application Perspective** xây service map từ **telemetry gần đây** (span/metric).  
Không còn span trong cửa sổ thời gian → service biến mất khỏi map. Đây là hành vi bình thường (không phải bug).

| Lớp | Hiện khi nào |
|-----|----------------|
| Infrastructure (K8s sensor) | Pod/Deployment **luôn** thấy nếu agent còn scrape |
| APM Services / map | Chỉ khi còn **OTLP spans** (hoặc traffic được instrument) |

## Cách làm trong NOLI

Mỗi microservice gửi heartbeat span `otel.heartbeat` (SERVER) mỗi **30 giây** khi bật OTEL:

```bash
OTEL_EXPORTER_OTLP_ENDPOINT=http://opentelemetry-collector.observability.svc.cluster.local:4317
OTEL_EXPORTER_OTLP_PROTOCOL=grpc
OTEL_SERVICE_NAME=noli-catalog-service          # khác nhau từng service
OTEL_RESOURCE_ATTRIBUTES=deployment.environment=dev-ocp,k8s.namespace.name=npd-shop,k8s.cluster.name=ocp01
OTEL_HEARTBEAT=1                                # mặc định
OTEL_HEARTBEAT_SECONDS=30
```

Tắt: `OTEL_HEARTBEAT=0`.

Code: `services/common/observability.py` → `start_heartbeat()`.

## Cách khác (nếu cần)

1. **CronJob / blackbox** gọi `GET /health` mỗi 30–60s → span HTTP thật (có thêm cạnh gateway nếu đi qua gateway).
2. **Synthetic monitoring** Instana (nếu license có).
3. Đừng kỳ vọng chỉ nhìn Infrastructure map thay cho Application services.

## Filter đúng trên Instana UI

- **Dest Service > Name** = `noli-shop-gateway`, `noli-auth-service`, …
- Tag `kubernetes.namespace.name` = `npd-shop`
- Call technology = `OpenTelemetry`
- **Không** dùng filter `Dest Kubernetes Service > name` (thường trống với pure OTEL)
