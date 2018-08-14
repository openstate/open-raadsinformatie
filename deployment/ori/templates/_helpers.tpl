{{/*
Create neo4j auth using .Values.neo4jPassword or generate if empty.
*/}}
{{- define "..neo4j-auth" -}}
{{- if .Values.neo4jPassword -}}
{{- printf "%s%s" "neo4j/" .Values.neo4jPassword -}}
{{- else -}}
{{- required "neo4jPassword needs to be set" .Values.neo4jPassword -}}
{{- end -}}
{{- end -}}
