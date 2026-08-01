#!/usr/bin/env bash
# Seed Vault secrets for npd-shop (lab).
# Chạy trong pod vault-0 hoặc bastion có vault CLI + VAULT_TOKEN admin.
#
# Usage:
#   export VAULT_ADDR=http://127.0.0.1:8200
#   export VAULT_TOKEN=root
#   export HARBOR_PULL_TOKEN='...'   # robot$npd-shop+k8s-pull
#   export HARBOR_PUSH_TOKEN='...'   # robot$npd-shop+ci-push (Jenkins)
#   bash scripts/vault-seed-npd-shop.sh
#
# Optional overrides:
#   NOLI_DB_PASSWORD, JWT_SECRET, INTERNAL_TOKEN, PG_HOST

set -euo pipefail

: "${VAULT_ADDR:?set VAULT_ADDR}"
: "${VAULT_TOKEN:?set VAULT_TOKEN}"
: "${HARBOR_PULL_TOKEN:?set HARBOR_PULL_TOKEN (Harbor robot k8s-pull secret)}"
: "${HARBOR_PUSH_TOKEN:?set HARBOR_PUSH_TOKEN (Harbor robot ci-push secret)}"

REGISTRY="${REGISTRY:-harbor-platform.apps.ocp01.npd.co}"
PG_HOST="${PG_HOST:-postgres-ha-postgresql-primary.postgres.svc.cluster.local}"
NOLI_DB_PASSWORD="${NOLI_DB_PASSWORD:-$(openssl rand -hex 16)}"
JWT_SECRET="${JWT_SECRET:-$(openssl rand -hex 32)}"
INTERNAL_TOKEN="${INTERNAL_TOKEN:-$(openssl rand -hex 24)}"

DATABASE_URL="postgresql+psycopg2://noli:${NOLI_DB_PASSWORD}@${PG_HOST}:5432/noli"

echo "==> secret/npd-shop/noli-db"
vault kv put secret/npd-shop/noli-db \
  username='noli' \
  database='noli' \
  password="${NOLI_DB_PASSWORD}"

echo "==> secret/npd-shop/app"
vault kv put secret/npd-shop/app \
  DATABASE_URL="${DATABASE_URL}" \
  JWT_SECRET="${JWT_SECRET}" \
  INTERNAL_TOKEN="${INTERNAL_TOKEN}"

echo "==> secret/npd-shop/harbor-pull"
vault kv put secret/npd-shop/harbor-pull \
  registry="${REGISTRY}" \
  username='robot$npd-shop+k8s-pull' \
  password="${HARBOR_PULL_TOKEN}"

echo "==> secret/npd-shop/harbor (Jenkins Kaniko push)"
vault kv put secret/npd-shop/harbor \
  username='robot$npd-shop+ci-push' \
  password="${HARBOR_PUSH_TOKEN}"

echo "==> done. Verify:"
echo "  vault kv get secret/npd-shop/app"
echo "  vault kv get secret/npd-shop/harbor-pull"
echo "  vault kv get secret/npd-shop/harbor"
echo "  vault kv get secret/npd-shop/noli-db"
echo
echo "Patch jenkins-kaniko policy to allow secret/data/npd-shop/harbor (see DEPLOY.md)."
