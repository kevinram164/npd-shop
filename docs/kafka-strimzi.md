# Shared Strimzi Kafka (platform infra)

**Deploy:** `banking-demo/phase9-gitops-platform/kafka/DEPLOY.md`

| Listener | Port | Auth |
|----------|------|------|
| ~~plain~~ | — | **tắt** (gần prod) |
| tls | **9093** | TLS + **SCRAM-SHA-512** + ACL |

UI: https://kafka-ui-platform.apps.ocp01.npd.co (SCRAM user `kafka-ui`)

Bootstrap:

```text
npd-kafka-kafka-bootstrap.kafka.svc.cluster.local:9093
```

### Shop wire (SCRAM)

1. Kafka Ready + KafkaUser `npd-shop` Ready  
2. Copy secrets sang ns shop:

```bash
bash deploy/scripts/sync-kafka-client-secrets.sh
# cần jq + oc
```

3. Build/push image order-service + payment-worker (có `kafka_auth.py`)  
4. Sync Argo `npd-shop` (`values-kafka.yaml` đã bật)  
5. Đặt hàng → Kafka UI topic `orders.events`

```bash
oc -n npd-shop get secret npd-shop-kafka-user npd-shop-kafka-cluster-ca
oc -n npd-shop get deploy order-service -o yaml | grep -E 'KAFKA_|kafka'
```

### Banking (sau)

User `npd-banking` + cùng bootstrap SCRAM; consumer `orders.events`, producer `payments.events`.
