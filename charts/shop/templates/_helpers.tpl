{{- define "shop.labels" -}}
app.kubernetes.io/name: npd-shop
app.kubernetes.io/part-of: npd-shop
{{- end }}

{{/*
Vault Agent Injector → /vault/secrets/env (export KEY='value').
Usage: include "shop.vault.podAnnotations" $
*/}}
{{- define "shop.vault.podAnnotations" -}}
{{- $v := .Values.vault -}}
vault.hashicorp.com/agent-inject: "true"
vault.hashicorp.com/agent-init-first: "true"
vault.hashicorp.com/agent-pre-populate-only: "true"
vault.hashicorp.com/role: {{ $v.role | quote }}
vault.hashicorp.com/agent-inject-secret-env: {{ $v.appPath | quote }}
vault.hashicorp.com/agent-inject-template-env: |
  {{`{{ with secret "`}}{{ $v.appPath }}{{`" }}`}}
  {{- range $v.secretKeys }}
  export {{ . }}='{{`{{ .Data.data.`}}{{ . }}{{` }}`}}'
  {{- end }}
  {{`{{ end }}`}}
{{- end -}}

{{/* Source Vault env then start uvicorn. Usage: include "shop.vault.containerCommand" (dict "port" 8080) */}}
{{- define "shop.vault.containerCommand" -}}
command: ["/bin/sh", "-c"]
args:
  - . /vault/secrets/env && exec /app/venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port {{ .port }} --no-access-log
{{- end -}}

{{- define "shop.secretEnv" -}}
{{- /* App secrets: K8s Secret (OCP/ESO) hoặc Vault Agent (dev-k8s) */ -}}
{{- if and $.Values.appSecretName (not $.Values.vault.enabled) }}
- name: DATABASE_URL
  valueFrom:
    secretKeyRef:
      name: {{ $.Values.appSecretName }}
      key: DATABASE_URL
- name: JWT_SECRET
  valueFrom:
    secretKeyRef:
      name: {{ $.Values.appSecretName }}
      key: JWT_SECRET
- name: INTERNAL_TOKEN
  valueFrom:
    secretKeyRef:
      name: {{ $.Values.appSecretName }}
      key: INTERNAL_TOKEN
{{- end }}
{{- if and $.Values.kafka.enabled $.Values.kafka.userSecretName }}
- name: KAFKA_PASSWORD
  valueFrom:
    secretKeyRef:
      name: {{ $.Values.kafka.userSecretName }}
      key: {{ $.Values.kafka.userSecretPasswordKey | default "password" }}
{{- end }}
{{- end }}

{{- define "shop.kafkaVolumes" -}}
{{- if and .Values.kafka.enabled .Values.kafka.caSecretName }}
volumes:
  - name: kafka-cluster-ca
    secret:
      secretName: {{ .Values.kafka.caSecretName }}
{{- end }}
{{- end }}

{{- define "shop.kafkaVolumeMounts" -}}
{{- if and .Values.kafka.enabled .Values.kafka.caSecretName }}
volumeMounts:
  - name: kafka-cluster-ca
    mountPath: {{ .Values.kafka.caMountPath | default "/etc/kafka/certs" }}
    readOnly: true
{{- end }}
{{- end }}

{{- define "shop.httpProbes" -}}
startupProbe:
  httpGet:
    path: {{ .path }}
    port: http
  failureThreshold: 30
  periodSeconds: 5
readinessProbe:
  httpGet:
    path: {{ .path }}
    port: http
  periodSeconds: 10
  failureThreshold: 3
livenessProbe:
  httpGet:
    path: {{ .path }}
    port: http
  periodSeconds: 20
  failureThreshold: 3
{{- end }}
