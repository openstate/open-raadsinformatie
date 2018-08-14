{{/*
Create neo4j auth using .Values.neo4jPassword or generate if empty.
*/}}
{{- define "..neo4j-auth" -}}
{{- if .Values.neo4jPassword -}}
{{- cat "neo4j/" .Values.neo4jPassword -}}
{{- else -}}
{{- $pw := randAlphaNum 32 -}}
{{- printf "%s%s" "neo4j/" $pw -}}
{{- end -}}
{{- end -}}
