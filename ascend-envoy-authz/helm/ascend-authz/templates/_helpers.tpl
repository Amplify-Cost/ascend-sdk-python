{{/*
Expand the name of the chart.
*/}}
{{- define "ascend-authz.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "ascend-authz.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "ascend-authz.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "ascend-authz.labels" -}}
helm.sh/chart: {{ include "ascend-authz.chart" . }}
{{ include "ascend-authz.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "ascend-authz.selectorLabels" -}}
app.kubernetes.io/name: {{ include "ascend-authz.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "ascend-authz.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "ascend-authz.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Create the secret name for API key
*/}}
{{- define "ascend-authz.secretName" -}}
{{- if .Values.ascend.existingSecret }}
{{- .Values.ascend.existingSecret }}
{{- else }}
{{- include "ascend-authz.fullname" . }}-secret
{{- end }}
{{- end }}
