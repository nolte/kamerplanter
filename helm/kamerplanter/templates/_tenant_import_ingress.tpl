{{/*
#2138 — the tenant import's own body limit at ingress-nginx.

ingress-nginx sets `proxy-body-size` per Ingress object, not per path, so the
import path needs an Ingress of its own. Runs BEFORE the bjw-s loader
(templates/common.yaml) and derives `ingress.tenant-import` from the MERGED
`ingress.main`: the same hosts, className and TLS, but one `Exact` path —
`/api/v1/admin/platform/tenant-imports` — to the service main's first path of
each host routes to (the frontend, #1159), with
`proxy-body-size = tenantExport.importMaxUploadMb + 1 MiB`, request buffering
off and 300 s timeouts. ingress-nginx merges both Ingresses into one server;
the Exact path wins over main's `/` prefix for that path only, every other path
keeps main's limit.

main keeps its name (`<fullname>`, pinned with `forceRename`); the derived one
is `<fullname>-tenant-import`.

Rendered only when main renders (hosts given, `enabled` not "false") and
`tenantExport.importIngress.enabled` is true. Certificate annotations of main
are NOT copied: cert-manager would issue a second Certificate for the same TLS
Secret; the Secret main's certificate fills is reused. Extra annotations go
into `tenantExport.importIngress.annotations`.
Contracts: scripts/ci/assert_chart_contracts.sh (#2138 block).
*/}}
{{- define "kamerplanter.tenantImportIngress" -}}
  {{- $values := .Values -}}
  {{- $ingresses := $values.ingress | default dict -}}
  {{- $_ := unset $ingresses "tenant-import" -}}
  {{- $main := index $ingresses "main" -}}
  {{- $settings := $values.tenantExport | default dict -}}
  {{- $own := $settings.importIngress | default dict -}}
  {{- $on := and (kindIs "map" $main) $own.enabled -}}
  {{- if $on -}}
    {{- if not $main.hosts -}}
      {{- $on = false -}}
    {{- else if hasKey $main "enabled" -}}
      {{- if eq (toString (index $main "enabled")) "false" -}}
        {{- $on = false -}}
      {{- end -}}
    {{- end -}}
  {{- end -}}
  {{- if $on -}}
    {{- $limit := printf "%dm" (add (int $settings.importMaxUploadMb) 1) -}}
    {{- $annotations := dict
          "nginx.ingress.kubernetes.io/proxy-body-size" $limit
          "nginx.ingress.kubernetes.io/proxy-request-buffering" "off"
          "nginx.ingress.kubernetes.io/proxy-read-timeout" "300"
          "nginx.ingress.kubernetes.io/proxy-send-timeout" "300" -}}
    {{- $annotations = merge (deepCopy ($own.annotations | default dict)) $annotations -}}
    {{- $hosts := list -}}
    {{- range $host := $main.hosts -}}
      {{- $first := first ($host.paths | default list) | default dict -}}
      {{- $service := deepCopy ($first.service | default (dict "identifier" "frontend")) -}}
      {{- $path := dict "path" "/api/v1/admin/platform/tenant-imports" "pathType" "Exact" "service" $service -}}
      {{- $hosts = append $hosts (dict "host" $host.host "paths" (list $path)) -}}
    {{- end -}}
    {{- $derived := dict "enabled" true "annotations" $annotations "hosts" $hosts -}}
    {{- if $main.className -}}
      {{- $_ := set $derived "className" $main.className -}}
    {{- end -}}
    {{- if $main.tls -}}
      {{- $_ := set $derived "tls" (deepCopy $main.tls) -}}
    {{- end -}}
    {{- /* bjw-s appends the identifier to every name once two Ingresses render: main
           would turn from `<fullname>` into `<fullname>-main` (a delete and a create
           at the edge). Pin main's name unless the values already name it. */ -}}
    {{- if not (or $main.forceRename $main.prefix $main.suffix) -}}
      {{- /* A template string: bjw-s renders forceRename after its loader merged `global`. */ -}}
      {{- $_ := set $main "forceRename" "{{ include \"bjw-s.common.lib.chart.names.fullname\" . }}" -}}
    {{- end -}}
    {{- $_ := set $ingresses "tenant-import" $derived -}}
    {{- $_ := set $values "ingress" $ingresses -}}
  {{- end -}}
{{- end -}}
