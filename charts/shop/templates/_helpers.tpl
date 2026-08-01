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
