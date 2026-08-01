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

Bật shop: uncomment `gitops/values-kafka.yaml` trong `deploy/argocd/npd-shop.yaml`.
