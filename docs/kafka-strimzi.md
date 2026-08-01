# Shared Strimzi Kafka (platform infra)

**Deploy từng bước:** `banking-demo/phase9-gitops-platform/kafka/DEPLOY.md`

Kafka nằm ở **banking-demo platform infra** (Helm + ArgoCD), không deploy trong repo shop.

| Argo app | Vai trò |
|----------|---------|
| `infra-strimzi` | Helm Operator |
| `infra-kafka` | Helm cluster + topics |
| `infra-kafka-ui` | Helm Kafbat UI |

UI: https://kafka-ui-platform.apps.ocp01.npd.co

### Monitor

| Tool | Mức độ (lab hiện tại) |
|------|------------------------|
| Kafka UI | Topics / messages / groups — đầy đủ |
| Coroot | Pod + traffic eBPF ns `kafka` — một phần |
| Instana | K8s pods + OTEL messaging từ app — một phần (chưa Kafka sensor) |

Bootstrap lab:

```text
npd-kafka-kafka-bootstrap.kafka.svc.cluster.local:9092
```

Shop đã wire: `gitops/values-kafka.yaml` trong `deploy/argocd/npd-shop.yaml`.

```bash
oc -n argocd app sync npd-shop   # hoặc UI Sync
oc -n npd-shop logs -l app.kubernetes.io/name=order-service --tail=30 | grep -i kafka
# Đặt hàng → https://kafka-ui-platform.apps.ocp01.npd.co → topic orders.events
```

**SCRAM (gần prod):** khi Kafka bật `values-prod` (tắt plain + ACL), copy secret:

```bash
oc -n kafka get secret npd-shop -o jsonpath='{.data.password}' | base64 -d; echo
# App: bootstrap :9093 + SASL_SSL SCRAM (cần thêm env/client code)
```

**Banking (bước sau):** consumer `orders.events` / producer `payments.events` với user `npd-banking`.
