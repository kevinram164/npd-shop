# Deploy NOLI (npd-shop) lên OpenShift — domain `npd-shop.co`

Giống pattern banking (`npd-banking.co`) + CineHome (Helm + ArgoCD + Jenkins).

| Mục | Giá trị lab |
|-----|-------------|
| Repo | `https://github.com/kevinram164/npd-shop.git` |
| Branch | `main` |
| Namespace | `npd-shop` |
| Harbor project | `npd-shop` |
| Domain chính | **https://npd-shop.co** |
| Fallback OCP | https://npd-shop.apps.ocp01.npd.co |
| ArgoCD project | `npd-shop-platform` |

`/api` đi cùng origin qua nginx `shop-web` → Service `gateway` (không cần Route `/api` riêng như banking/Kong).

---

## Checklist

| # | Việc | Xong khi |
|---|------|----------|
| A | Push code `main` | GitHub có Helm/GitOps/Jenkinsfile |
| B | Harbor + **Vault seed** + ESO | `harbor-pull-creds` + `npd-shop-secrets` synced |
| C | DB `noli` (Job init) | Job `noli-db-init` Complete |
| D | DNS `npd-shop.co` → Router | Browser mở được domain |
| E | AppProject + app-of-apps | ArgoCD sync Helm + Routes + ESO |
| F | Jenkins Multibranch + library | Image tag bump trong `gitops/values-images.yaml` |

---

## A — Push repo

```powershell
cd D:\Tai-lieu\LPI-DOCKER-K8S\OCP\npd-shop
git add .
git commit -m "feat: helm gitops routes for npd-shop.co"
git push -u origin main
```

Shared library (catalog `npd-shop`):

```powershell
cd D:\Tai-lieu\LPI-DOCKER-K8S\OCP\jenkins-shared-library
# commit + push main sau khi thêm Projects.groovy entry
```

ArgoCD: Settings → Repositories → connect `https://github.com/kevinram164/npd-shop.git` nếu chưa.

---

## B — Harbor + Vault (không tạo Secret tay)

Toàn bộ secret trên **Vault** → ESO. Chi tiết: [docs/vault-secrets.md](docs/vault-secrets.md).

1. Harbor: project **`npd-shop`** + robot `k8s-pull` + `ci-push` (copy 2 token)
2. Seed Vault:

```bash
oc exec -i -n vault vault-0 -- env \
  VAULT_ADDR=http://127.0.0.1:8200 \
  VAULT_TOKEN=root \
  HARBOR_PULL_TOKEN='...' \
  HARBOR_PUSH_TOKEN='...' \
  bash -s < scripts/vault-seed-npd-shop.sh
```

| Vault | → K8s |
|-------|-------|
| `secret/npd-shop/app` | `npd-shop-secrets` |
| `secret/npd-shop/harbor-pull` | `harbor-pull-creds` |
| `secret/npd-shop/noli-db` | `npd-shop-noli-db` (ns `postgres`) |
| `secret/npd-shop/harbor` | Jenkins Kaniko (đọc trực tiếp) |

3. Policy `jenkins-kaniko` thêm `secret/data/npd-shop/harbor` (xem docs)
4. Sync ESO (app-of-apps gồm `vault-secrets.yaml`)

```bash
oc get externalsecret -n npd-shop
oc get secret harbor-pull-creds npd-shop-secrets -n npd-shop
oc logs job/noli-db-init -n postgres
```

Chart: `imagePullSecrets: harbor-pull-creds`, `appSecretName: npd-shop-secrets`.

---

## C — App secret qua Vault

**Không** `oc create secret generic npd-shop-secrets`. Seed `secret/npd-shop/app`; ESO tạo Secret (`DATABASE_URL`, `JWT_SECRET`, `INTERNAL_TOKEN`).

Job `noli-db-init` tạo user/DB `noli` — password từ `secret/npd-shop/noli-db` phải khớp `DATABASE_URL`.

`SEED_ON_STARTUP=true` trên auth/catalog. Admin demo: `admin@noli.shop` / `admin123`.

---

## D — DNS custom domain

Trỏ **`npd-shop.co`** (và tùy chọn `www`) A/CNAME tới IP OpenShift Router — cùng cách với `npd-banking.co`.

Lab không có DNS public: thêm vào hosts máy client:

```text
<ROUTER_IP>  npd-shop.co
```

Lấy IP router (một cách):

```bash
oc get svc -n openshift-ingress router-default -o wide
```

Route fallback `npd-shop.apps.ocp01.npd.co` luôn dùng được nếu wildcard `*.apps.ocp01.npd.co` đã có.

---

## E — ArgoCD

```bash
export ARGOCD_NS=argocd

oc apply -f deploy/argocd/appproject.yaml -n $ARGOCD_NS
oc apply -f deploy/argocd/app-of-apps.yaml -n $ARGOCD_NS

oc get applications -n $ARGOCD_NS | grep npd-shop
oc get route -n npd-shop
oc get pods -n npd-shop
```

Apps con (từ app-of-apps):

- `npd-shop-eso-app` / `npd-shop-eso-noli-db` / `npd-shop-db-init` — Vault → Secret + DB
- `npd-shop` — Helm `charts/shop`
- `npd-shop-routes` — Routes `npd-shop.co` + apps host

---

## F — Jenkins

1. Đảm bảo shared library `platform@main` đã có entry **`npd-shop`** trong `Projects.groovy`
2. Multibranch Pipeline trỏ repo `kevinram164/npd-shop`, Jenkinsfile ở root
3. Build lần đầu: parameter `BUILD_TARGET=all` (hoặc để `auto` sau khi có baseline image)
4. Pipeline push Harbor + commit bump `gitops/values-images.yaml` → ArgoCD sync

Vault path Jenkins đọc: `secret/npd-shop/harbor` (username/password registry).

---

## Kiểm tra nhanh

```bash
curl -skI https://npd-shop.co/
curl -sk https://npd-shop.co/api/health
# hoặc
curl -sk https://npd-shop.apps.ocp01.npd.co/api/products | head
```

Browser: https://npd-shop.co — catalog, checkout (mã `NOLI-xxxxxx`), admin portal.

---

## Kafka (tùy chọn, sau)

`order-service` / `payment-worker` có `KAFKA_BOOTSTRAP` (mặc định rỗng = tắt). Khi nối banking:

```yaml
# gitops overlay hoặc values
orderService:
  env:
    KAFKA_BOOTSTRAP: "redpanda.kafka.svc.cluster.local:9092"
paymentWorker:
  env:
    KAFKA_BOOTSTRAP: "redpanda.kafka.svc.cluster.local:9092"
```

---

## Troubleshooting

| Triệu chứng | Gợi ý |
|-------------|--------|
| ImagePullBackOff | Harbor project / `harbor-pull-creds` / trust CA Route Harbor |
| CrashLoop `DATABASE_URL` | Secret `npd-shop-secrets` thiếu hoặc DB chưa tạo |
| Route 503 Endpoints none | `targetPort: http` (đã set); kiểm tra Service selector |
| HostAlreadyClaimed | Domain đang bị Route khác giữ — `oc get route -A \| grep npd-shop` |
| CORS lỗi | `gateway.env.CORS_ORIGINS` phải gồm `https://npd-shop.co` |
| Instana không thấy service | Cần OTEL env (đã có trong `values-observability.yaml`) + collector Running |
