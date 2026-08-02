#!/usr/bin/env bash
# Copy Strimzi SCRAM user + cluster CA vào ns npd-shop (chạy trên bastion sau KafkaUser Ready).
set -euo pipefail

SRC_NS="${SRC_NS:-kafka}"
DST_NS="${DST_NS:-npd-shop}"
USER_SECRET="${USER_SECRET:-npd-shop}"
CA_SECRET="${CA_SECRET:-npd-kafka-cluster-ca-cert}"

oc -n "$SRC_NS" get secret "$USER_SECRET" >/dev/null
oc -n "$SRC_NS" get secret "$CA_SECRET" >/dev/null

oc -n "$SRC_NS" get secret "$USER_SECRET" -o json \
  | jq --arg ns "$DST_NS" \
    'del(.metadata.uid,.metadata.resourceVersion,.metadata.creationTimestamp,.metadata.ownerReferences,.metadata.annotations,.metadata.managedFields)
     | .metadata.namespace=$ns
     | .metadata.name="npd-shop-kafka-user"
     | .type="Opaque"' \
  | oc apply -f -

oc -n "$SRC_NS" get secret "$CA_SECRET" -o json \
  | jq --arg ns "$DST_NS" \
    'del(.metadata.uid,.metadata.resourceVersion,.metadata.creationTimestamp,.metadata.ownerReferences,.metadata.annotations,.metadata.managedFields)
     | .metadata.namespace=$ns
     | .metadata.name="npd-shop-kafka-cluster-ca"
     | .type="Opaque"' \
  | oc apply -f -

echo "OK: $DST_NS/npd-shop-kafka-user + $DST_NS/npd-shop-kafka-cluster-ca"
oc -n "$DST_NS" get secret npd-shop-kafka-user npd-shop-kafka-cluster-ca
