{{/*
MT-032 (#2128) — one Celery worker per queue (`celeryWorkers.dedicatedQueues`).

Runs BEFORE the bjw-s loader (templates/common.yaml) and rewrites `.Values` in
place, so the copies are derived from the MERGED values: whatever an overlay,
`--set` or an ArgoCD valuesObject sets on `controllers.celery-worker` or
`networkpolicies.celery-worker` reaches every copy. A YAML anchor would not do
that — anchors resolve inside one file, so an overlay hardening the worker
would have left the copies on the base values (security review SEC-001).

With the switch on, for each `celeryWorkers.copies` entry (copy name -> queue):
  * `controllers.<copy>` = a deep copy of `controllers.celery-worker`, with any
    `controllers.<copy>` keys the values set merged over it, and its main
    container's `-Q`/`--queues` value replaced by the copy's queue;
  * every persistence item that mounts into `celery-worker` mounts the same
    paths into the copy;
  * `networkpolicies.<copy>` = a deep copy of `networkpolicies.celery-worker`
    (merged with `networkpolicies.<copy>` keys) selecting the copy;
  * every policy peer that names `app.kubernetes.io/controller: celery-worker`
    gets a sibling peer for the copy (ArangoDB, Valkey, inference-service, and
    any policy an overlay adds).
With the switch off — or with celery-worker itself off — the copies and any
stray `controllers.<copy>` / `networkpolicies.<copy>` keys are removed.
Contracts: scripts/ci/assert_chart_contracts.sh (both states, base and dev).
*/}}
{{- define "kamerplanter.celeryWorkerCopies" -}}
  {{- $values := .Values -}}
  {{- $controllers := $values.controllers | default dict -}}
  {{- $policies := $values.networkpolicies | default dict -}}
  {{- $settings := $values.celeryWorkers | default dict -}}
  {{- $copies := $settings.copies | default dict -}}
  {{- $worker := index $controllers "celery-worker" -}}
  {{- $on := and $settings.dedicatedQueues (kindIs "map" $worker) -}}
  {{- if $on -}}
    {{- if hasKey $worker "enabled" -}}
      {{- if eq (toString (index $worker "enabled")) "false" -}}
        {{- $on = false -}}
      {{- end -}}
    {{- end -}}
  {{- end -}}

  {{- $active := list -}}
  {{- range $copy, $queue := $copies -}}
    {{- $overrides := index $controllers $copy | default dict -}}
    {{- $_ := unset $controllers $copy -}}
    {{- $policyOverrides := index $policies $copy | default dict -}}
    {{- $_ := unset $policies $copy -}}
    {{- if $on -}}
      {{- $spec := deepCopy $worker -}}
      {{- $_ := unset $spec "enabled" -}}
      {{- $spec = mergeOverwrite $spec (deepCopy $overrides) -}}
      {{- $main := index ($spec.containers | default dict) "main" -}}
      {{- if not (kindIs "map" $main) -}}
        {{- fail (printf "celeryWorkers.dedicatedQueues: controllers.celery-worker has no main container to copy into %s (#2128)" $copy) -}}
      {{- end -}}
      {{- $args := list -}}
      {{- $next := false -}}
      {{- $found := false -}}
      {{- range $arg := ($main.args | default list) -}}
        {{- $text := toString $arg -}}
        {{- if $next -}}
          {{- $args = append $args $queue -}}
          {{- $next = false -}}
        {{- else if hasPrefix "--queues=" $text -}}
          {{- $args = append $args (printf "--queues=%s" $queue) -}}
          {{- $found = true -}}
        {{- else if or (eq $text "-X") (eq $text "--exclude-queues") (hasPrefix "--exclude-queues=" $text) -}}
          {{- fail (printf "controllers.celery-worker excludes queues (%s): the copy %s cannot derive its queue from that (#2128)" $text $copy) -}}
        {{- else -}}
          {{- $args = append $args $arg -}}
          {{- if or (eq $text "-Q") (eq $text "--queues") -}}
            {{- $next = true -}}
            {{- $found = true -}}
          {{- end -}}
        {{- end -}}
      {{- end -}}
      {{- if not $found -}}
        {{- $args = concat $args (list "-Q" $queue) -}}
      {{- end -}}
      {{- $_ := set $main "args" $args -}}
      {{- if not (hasKey $overrides "enabled") -}}
        {{- $_ := set $spec "enabled" true -}}
      {{- end -}}
      {{- $_ := set $controllers $copy $spec -}}
      {{- if ne (toString $spec.enabled) "false" -}}
        {{- $active = append $active $copy -}}
        {{- $policy := index $policies "celery-worker" -}}
        {{- if kindIs "map" $policy -}}
          {{- $copyPolicy := mergeOverwrite (deepCopy $policy) (deepCopy $policyOverrides) -}}
          {{- $_ := set $copyPolicy "controller" $copy -}}
          {{- $_ := set $policies $copy $copyPolicy -}}
        {{- end -}}
      {{- end -}}
    {{- end -}}
  {{- end -}}

  {{- if $active -}}
    {{- /* Mounts: the worker's paths in every persistence item, for each copy. */ -}}
    {{- range $name, $item := ($values.persistence | default dict) -}}
      {{- if and (kindIs "map" $item) (kindIs "map" $item.advancedMounts) -}}
        {{- $mounts := index $item.advancedMounts "celery-worker" -}}
        {{- if $mounts -}}
          {{- range $copy := $active -}}
            {{- $_ := set $item.advancedMounts $copy (deepCopy $mounts) -}}
          {{- end -}}
        {{- end -}}
      {{- end -}}
    {{- end -}}

    {{- /* Peers: wherever a policy names the worker, it names the copies too. */ -}}
    {{- range $name, $policy := $policies -}}
      {{- if and (kindIs "map" $policy) (kindIs "map" $policy.rules) (not (has $name $active)) -}}
        {{- range $direction, $field := dict "ingress" "from" "egress" "to" -}}
          {{- $rules := index $policy.rules $direction -}}
          {{- if kindIs "slice" $rules -}}
            {{- range $rule := $rules -}}
              {{- if and (kindIs "map" $rule) (kindIs "slice" (index $rule $field)) -}}
                {{- $peers := list -}}
                {{- range $peer := index $rule $field -}}
                  {{- $peers = append $peers $peer -}}
                  {{- $controller := "" -}}
                  {{- if and (kindIs "map" $peer) (kindIs "map" $peer.podSelector) (kindIs "map" $peer.podSelector.matchLabels) -}}
                    {{- $controller = toString (index $peer.podSelector.matchLabels "app.kubernetes.io/controller") -}}
                  {{- end -}}
                  {{- if eq $controller "celery-worker" -}}
                    {{- range $copy := $active -}}
                      {{- $sibling := deepCopy $peer -}}
                      {{- $_ := set $sibling.podSelector.matchLabels "app.kubernetes.io/controller" $copy -}}
                      {{- $peers = append $peers $sibling -}}
                    {{- end -}}
                  {{- end -}}
                {{- end -}}
                {{- $_ := set $rule $field $peers -}}
              {{- end -}}
            {{- end -}}
          {{- end -}}
        {{- end -}}
      {{- end -}}
    {{- end -}}
  {{- end -}}
{{- end -}}

{{/*
#2128 / #2127 — worker autoscaling by queue length (`celeryWorkers.queueAutoscaling`).

Runs AFTER the copies exist (so a copy is not a copy of an autoscaler) and
BEFORE the bjw-s loader (templates/common.yaml). For every `workers` entry whose
controller exists and is enabled, sets `controllers.<worker>.horizontalPodAutoscaler`
to an autoscaling/v2 spec on one `External` metric: `metricName`, selected on
the `queue` label by the queues the worker's own `-Q` / `--queues` argument
names (rendered, so `dedicatedQueues` decides), with an `AverageValue` target of
`targetPerReplica`. The bjw-s HPA class renders it; the existing render checks
(attachment volume, PDB, renderChecks.autoscalers) then see it like a
hand-written one. Refusals here are about this block's inputs; the HPA shape is
held by renderChecks.autoscalers. Contracts: scripts/ci/assert_chart_contracts.sh.
*/}}
{{- define "kamerplanter.celeryWorkerAutoscaling" -}}
  {{- $root := . -}}
  {{- $values := .Values -}}
  {{- $settings := dig "queueAutoscaling" dict ($values.celeryWorkers | default dict) -}}
  {{- if $settings.enabled -}}
    {{- if not (dig "enabled" false ($values.monitoring | default dict)) -}}
      {{- fail "celeryWorkers.queueAutoscaling.enabled needs monitoring.enabled=true: the queue length is exported on the backend's metrics port and scraped by Prometheus, which the Prometheus Adapter reads. See docs/deployment/helm.md#worker-autoscaling-nach-queue-laenge (#2128)." -}}
    {{- end -}}
    {{- $metric := toString ($settings.metricName | default "") -}}
    {{- if not $metric -}}
      {{- fail "celeryWorkers.queueAutoscaling.metricName is empty: name the External metric the Prometheus Adapter serves (its rule's name.as, default celery_queue_length) (#2128)." -}}
    {{- end -}}
    {{- $controllers := $values.controllers | default dict -}}
    {{- $workers := list "celery-worker" "celery-worker-default" "celery-worker-bulk" -}}
    {{- range $name, $entry := ($settings.workers | default dict) -}}
      {{- if not (has $name $workers) -}}
        {{- fail (printf "celeryWorkers.queueAutoscaling.workers.%s: not a Celery worker of this chart (one of %s) (#2128)." $name (join ", " $workers)) -}}
      {{- end -}}
      {{- $entry = $entry | default dict -}}
      {{- $controller := index $controllers $name -}}
      {{- $on := and (kindIs "map" $controller) (ne (toString (dig "enabled" true $entry)) "false") -}}
      {{- if and $on (hasKey $controller "enabled") -}}
        {{- if eq (toString $controller.enabled) "false" -}}
          {{- $on = false -}}
        {{- end -}}
      {{- end -}}
      {{- if $on -}}
        {{- if $controller.horizontalPodAutoscaler -}}
          {{- fail (printf "controllers.%s carries a horizontalPodAutoscaler and celeryWorkers.queueAutoscaling scales it too: keep one of the two (a copy inherits the autoscaler of controllers.celery-worker) (#2128)." $name) -}}
        {{- end -}}
        {{- if not (hasKey $entry "maxReplicas") -}}
          {{- fail (printf "celeryWorkers.queueAutoscaling.workers.%s.maxReplicas is required (#2128)." $name) -}}
        {{- end -}}
        {{- $max := int $entry.maxReplicas -}}
        {{- $min := 1 -}}
        {{- if hasKey $entry "minReplicas" -}}
          {{- $min = int $entry.minReplicas -}}
        {{- end -}}
        {{- if lt $min 1 -}}
          {{- fail (printf "celeryWorkers.queueAutoscaling.workers.%s.minReplicas must be at least 1, got %d: scaling a worker to zero needs a feature gate and leaves its queue unread (#2128)." $name $min) -}}
        {{- end -}}
        {{- if ge $min $max -}}
          {{- fail (printf "celeryWorkers.queueAutoscaling.workers.%s: minReplicas %d is not below maxReplicas %d, so the autoscaler can never change the replica count (#2128)." $name $min $max) -}}
        {{- end -}}
        {{- $target := "" -}}
        {{- if hasKey $entry "targetPerReplica" -}}
          {{- $target = toString $entry.targetPerReplica -}}
        {{- end -}}
        {{- if or (not (regexMatch "^[0-9]+(\\.[0-9]+)?$" $target)) (le (float64 (default "0" $target)) 0.0) -}}
          {{- fail (printf "celeryWorkers.queueAutoscaling.workers.%s.targetPerReplica must be a number above 0 (waiting messages per worker pod), got %q (#2128)." $name $target) -}}
        {{- end -}}
        {{- $queues := list -}}
        {{- $next := false -}}
        {{- range $arg := (dig "containers" "main" "args" list $controller) -}}
          {{- $text := tpl (toString $arg) $root -}}
          {{- if $next -}}
            {{- $queues = splitList "," $text -}}
            {{- $next = false -}}
          {{- else if hasPrefix "--queues=" $text -}}
            {{- $queues = splitList "," (trimPrefix "--queues=" $text) -}}
          {{- else if or (eq $text "-Q") (eq $text "--queues") -}}
            {{- $next = true -}}
          {{- end -}}
        {{- end -}}
        {{- if not $queues -}}
          {{- fail (printf "controllers.%s names no queue (-Q / --queues), so its queue length cannot be selected (#2128)." $name) -}}
        {{- end -}}
        {{- $selector := dict "matchExpressions" (list (dict "key" "queue" "operator" "In" "values" $queues)) -}}
        {{- $external := dict "metric" (dict "name" $metric "selector" $selector) "target" (dict "type" "AverageValue" "averageValue" $target) -}}
        {{- $hpa := dict "minReplicas" $min "maxReplicas" $max "metrics" (list (dict "type" "External" "external" $external)) -}}
        {{- $behavior := $entry.behavior | default $settings.behavior -}}
        {{- if $behavior -}}
          {{- $_ := set $hpa "behavior" (deepCopy $behavior) -}}
        {{- end -}}
        {{- $_ := set $controller "horizontalPodAutoscaler" $hpa -}}
      {{- end -}}
    {{- end -}}
  {{- end -}}
{{- end -}}
