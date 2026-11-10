#!/usr/bin/env bash
# Copy Strimzi SCRAM user + cluster CA vào ns npd-shop (sau KafkaUser Ready).
# Dùng kubectl (dev-k8s) hoặc oc (OCP) — tự chọn lệnh có sẵn.
set -euo pipefail

SRC_NS="${SRC_NS:-kafka}"
DST_NS="${DST_NS:-npd-shop}"
USER_SECRET="${USER_SECRET:-npd-shop}"
CA_SECRET="${CA_SECRET:-npd-kafka-cluster-ca-cert}"

if command -v kubectl >/dev/null 2>&1; then
  K=kubectl
elif command -v oc >/dev/null 2>&1; then
  K=oc
else
  echo "ERROR: cần kubectl hoặc oc" >&2
  exit 1
fi

$K -n "$SRC_NS" get secret "$USER_SECRET" >/dev/null
$K -n "$SRC_NS" get secret "$CA_SECRET" >/dev/null
$K create namespace "$DST_NS" --dry-run=client -o yaml | $K apply -f -

$K -n "$SRC_NS" get secret "$USER_SECRET" -o json \
  | jq --arg ns "$DST_NS" \
    'del(.metadata.uid,.metadata.resourceVersion,.metadata.creationTimestamp,.metadata.ownerReferences,.metadata.annotations,.metadata.managedFields)
     | .metadata.namespace=$ns
     | .metadata.name="npd-shop-kafka-user"
     | .type="Opaque"' \
  | $K apply -f -

$K -n "$SRC_NS" get secret "$CA_SECRET" -o json \
  | jq --arg ns "$DST_NS" \
    'del(.metadata.uid,.metadata.resourceVersion,.metadata.creationTimestamp,.metadata.ownerReferences,.metadata.annotations,.metadata.managedFields)
     | .metadata.namespace=$ns
     | .metadata.name="npd-shop-kafka-cluster-ca"
     | .type="Opaque"' \
  | $K apply -f -

echo "OK: $DST_NS/npd-shop-kafka-user + $DST_NS/npd-shop-kafka-cluster-ca"
$K -n "$DST_NS" get secret npd-shop-kafka-user npd-shop-kafka-cluster-ca
