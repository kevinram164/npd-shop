# Secrets npd-shop — toàn bộ trên Vault → External Secrets Operator

Không `oc create secret` thủ công cho app/pull. Seed Vault → ESO sync K8s Secret.

| Vault path | K8s Secret | Namespace | Dùng cho |
|------------|------------|-----------|----------|
| `secret/npd-shop/app` | `npd-shop-secrets` | `npd-shop` | `DATABASE_URL`, `JWT_SECRET`, `INTERNAL_TOKEN` |
| `secret/npd-shop/harbor-pull` | `harbor-pull-creds` | `npd-shop` | kubelet pull Harbor |
| `secret/npd-shop/harbor` | *(Jenkins đọc trực tiếp)* | — | Kaniko push |
| `secret/npd-shop/noli-db` | `npd-shop-noli-db` | `postgres` | Job tạo user/DB `noli` |

ClusterSecretStore `vault-backend` phải đã có (lab banking/cinehome).

---

## 1. Harbor UI — project + 2 robot

1. https://harbor-platform.apps.ocp01.npd.co → **New Project** `npd-shop`
2. Robot **`k8s-pull`** — Pull only → copy token
3. Robot **`ci-push`** — Push + Pull → copy token

Username đầy đủ:

- `robot$npd-shop+k8s-pull`
- `robot$npd-shop+ci-push`

---

## 2. Seed Vault

Trên bastion / trong pod `vault-0`:

```bash
oc exec -it -n vault vault-0 -- sh
export VAULT_ADDR=http://127.0.0.1:8200
export VAULT_TOKEN=root   # lab; prod dùng token admin

# Copy script vào pod hoặc chạy lệnh tay bên dưới
```

### Cách nhanh — script

Từ máy có `oc` + file repo (pipe vào vault pod):

```bash
oc exec -i -n vault vault-0 -- env \
  VAULT_ADDR=http://127.0.0.1:8200 \
  VAULT_TOKEN=root \
  HARBOR_PULL_TOKEN='PASTE_K8S_PULL_TOKEN' \
  HARBOR_PUSH_TOKEN='PASTE_CI_PUSH_TOKEN' \
  bash -s < scripts/vault-seed-npd-shop.sh
```

### Cách tay — từng path

```bash
NOLI_PASS=$(openssl rand -hex 16)
JWT=$(openssl rand -hex 32)
INT=$(openssl rand -hex 24)
PG=postgres-ha-postgresql-primary.postgres.svc.cluster.local

vault kv put secret/npd-shop/noli-db \
  username='noli' database='noli' password="${NOLI_PASS}"

vault kv put secret/npd-shop/app \
  DATABASE_URL="postgresql+psycopg2://noli:${NOLI_PASS}@${PG}:5432/noli" \
  JWT_SECRET="${JWT}" \
  INTERNAL_TOKEN="${INT}"

vault kv put secret/npd-shop/harbor-pull \
  registry='harbor-platform.apps.ocp01.npd.co' \
  username='robot$npd-shop+k8s-pull' \
  password='PASTE_K8S_PULL_TOKEN'

vault kv put secret/npd-shop/harbor \
  username='robot$npd-shop+ci-push' \
  password='PASTE_CI_PUSH_TOKEN'
```

Kiểm tra:

```bash
vault kv get secret/npd-shop/app
vault kv get secret/npd-shop/harbor-pull
vault kv get secret/npd-shop/harbor
vault kv get secret/npd-shop/noli-db
```

---

## 3. Policy Jenkins đọc `npd-shop/harbor`

Role `jenkins-kaniko` cần thêm path (nếu chưa):

```bash
vault policy write jenkins-kaniko - <<'EOF'
path "secret/data/platform/harbor" {
  capabilities = ["read"]
}
path "secret/data/platform/github" {
  capabilities = ["read"]
}
path "secret/data/cinehome/harbor" {
  capabilities = ["read"]
}
path "secret/data/cinehome/harbor-pull" {
  capabilities = ["read"]
}
path "secret/data/npd-shop/harbor" {
  capabilities = ["read"]
}
path "secret/data/npd-shop/harbor-pull" {
  capabilities = ["read"]
}
EOF
```

*(Giữ các path banking/aiops khác nếu policy hiện tại đã có — merge vào policy đang chạy, đừng xoá quyền cũ.)*

Xem policy hiện tại trước khi ghi đè:

```bash
vault policy read jenkins-kaniko
```

---

## 4. Apply GitOps ESO (sau khi seed Vault)

```bash
oc apply -f deploy/argocd/appproject.yaml -n argocd
oc apply -f deploy/argocd/app-of-apps.yaml -n argocd
# hoặc sync sớm ESO:
oc apply -f deploy/argocd/vault-secrets.yaml -n argocd
```

Checkpoint:

```bash
oc get externalsecret -n npd-shop
oc get secret harbor-pull-creds npd-shop-secrets -n npd-shop
oc get externalsecret npd-shop-noli-db -n postgres
oc get secret npd-shop-noli-db -n postgres
oc get job noli-db-init -n postgres
oc logs job/noli-db-init -n postgres
```

`ExternalSecret` status **SecretSynced** / Secret type `kubernetes.io/dockerconfigjson` cho pull = OK.

---

## 5. Rotate

```bash
vault kv put secret/npd-shop/app ...   # hoặc vault kv patch
oc annotate externalsecret npd-shop-secrets -n npd-shop \
  force-sync="$(date +%s)" --overwrite
```

Đổi password DB: cập nhật **cùng lúc** `noli-db` + `app.DATABASE_URL`, chạy lại Job (xoá Job cũ rồi sync) hoặc `ALTER ROLE` thủ công.
