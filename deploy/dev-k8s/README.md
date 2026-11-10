# NOLI (npd-shop) — dev-k8s

GitOps shop trên cụm kubeadm NPD. Infra (Vault, Harbor, Postgres, Kafka, HAProxy, f5-lb) do `cloud-native-platform`. Thư mục `deploy/argocd` (Routes/ESO/mesh) là OCP — **không** sync trên k8s.

## Cấu trúc

| Đường dẫn | Nội dung |
|-----------|----------|
| `argocd/appproject.yaml` | AppProject `npd-shop` |
| `argocd/app-of-apps.yaml` | Root `npd-shop-root-dev-k8s` |
| `argocd/applications/` | `noli-db-init` (0) → `npd-shop` (1) → `ingress` (2) |
| `manifests/db-init/` | Job Vault Agent tạo user/DB `noli` |
| `manifests/ingress/` | `npd-shop.co` → `shop-web:8080` (class `haproxy`) |
| `values/` | Vault, images `npd-harbor.co`, OTEL, Kafka, merchant |

```
LAN ── npd-shop.co ── f5-lb (10.100.1.100) ── HAProxy ── shop-web:8080
                                                         └─ /api → gateway → auth/catalog/order
order/payment ── Kafka (TLS+SCRAM) ── banking shop-bridge (CK)
```

## Secret

| Vault | Role | SA | Dùng |
|-------|------|-----|------|
| `secret/npd-shop/app` | `npd-shop-app` | gateway, auth, catalog, order, payment | `/vault/secrets/env` |
| `secret/npd-shop/noli-db` | `npd-shop-db-init` | noli-db-init @ postgres | password user `noli` |
| `secret/npd-shop/harbor-pull` | — | — | `create-harbor-pull-secret.sh` |
| `secret/npd-shop/harbor` | jenkins-kaniko | — | CI push |

## Triển khai

```bash
# 1) Seed Vault (REGISTRY home cluster)
export VAULT_TOKEN=...
v() { kubectl exec -i -n vault vault-0 -- env VAULT_ADDR=http://127.0.0.1:8200 VAULT_TOKEN="$VAULT_TOKEN" vault "$@"; }
# Nếu chưa có secret (hoặc registry sai):
# kubectl exec -i -n vault vault-0 -- env VAULT_ADDR=http://127.0.0.1:8200 VAULT_TOKEN=$VAULT_TOKEN \
#   REGISTRY=npd-harbor.co HARBOR_PULL_TOKEN='...' HARBOR_PUSH_TOKEN='...' \
#   bash -s < scripts/vault-seed-npd-shop.sh

# 2) Policy/role + harbor-pull-creds
bash cloud-native-platform/phase9-gitops-platform/environments/dev-k8s/scripts/vault-setup-k8s-auth.sh
VAULT_PATH=secret/npd-shop/harbor-pull NAMESPACES=npd-shop \
  bash cloud-native-platform/phase9-gitops-platform/environments/dev-k8s/scripts/create-harbor-pull-secret.sh

# 3) Kafka client secrets
bash deploy/scripts/sync-kafka-client-secrets.sh

# 4) ArgoCD
kubectl apply -f deploy/dev-k8s/argocd/appproject.yaml
kubectl apply -f deploy/dev-k8s/argocd/app-of-apps.yaml

# 5) Verify
kubectl -n npd-shop get pods,ingress
curl -skI https://npd-shop.co/
curl -sk https://npd-shop.co/api/health
```

Hosts client: `10.100.1.100  npd-shop.co`
