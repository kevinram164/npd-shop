{{- define "shop.labels" -}}
app.kubernetes.io/name: npd-shop
app.kubernetes.io/part-of: npd-shop
{{- end }}

{{- define "shop.secretEnv" -}}
{{- if $.Values.appSecretName }}
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
{{- $p := $.Values.probes | default dict -}}
startupProbe:
  httpGet:
    path: {{ .path }}
    port: http
  failureThreshold: 30
  periodSeconds: {{ $p.startupPeriodSeconds | default 5 }}
readinessProbe:
  httpGet:
    path: {{ .path }}
    port: http
  periodSeconds: {{ $p.readinessPeriodSeconds | default 10 }}
  failureThreshold: 3
livenessProbe:
  httpGet:
    path: {{ .path }}
    port: http
  periodSeconds: {{ $p.livenessPeriodSeconds | default 20 }}
  failureThreshold: 3
{{- end }}
