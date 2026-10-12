#!/usr/bin/env bash
#
# Render-time contracts of the kamerplanter chart.
#
#   scripts/ci/assert_chart_contracts.sh [chart-dir]
#
# Needs `helm` (with the chart dependencies built) and mikefarah `yq` v4. Both
# are on the `skaffold-verify` runner; locally `task verify:chart` runs it.
#
# WHY A RENDER AND NOT A VALUES CHECK. Since bjw-s common 5.2 every string in
# the values is evaluated as a template before the manifests are built, and the
# chart uses that: the attachment storage switch, the backup switch and the
# render-time refusal of a multi-replica ReadWriteOnce attachment volume are
# template expressions in values.yaml. Reading values.yaml shows the
# expression, not what it renders to — only `helm template` answers whether
# `storage.backend: s3` really drops the volume, or whether two backend replicas
# on a ReadWriteOnce volume are really refused. Every contract below is
# therefore asserted on a rendered manifest stream, and every refusal on the
# exit status and message of a render that must fail.
#
# HOW A CONTRACT COMPARES. `expect <render> <description> <expr> <json>` collects
# the values <expr> yields over every rendered document into one list and
# compares that list, serialised as compact JSON, with <json>. Comparing the
# whole list rather than "some element matches" is deliberate: a contract that
# expects `["s3"]` fails on `[]` (the variable vanished) and on
# `["s3","local-fs"]` (two containers disagree) alike.
#
# Each block names the issue whose mechanism it holds. A block that only ever
# saw its passing input is not known to be able to fail (NFR-018 §2): each one
# was run RED against the chart before the change it guards.
set -euo pipefail

CHART="${1:-helm/kamerplanter}"
RELEASE="kamerplanter"

work="$(mktemp -d)"
trap 'rm -rf "${work}"' EXIT

failures=0

fail() {
  echo "::error::$*" >&2
  failures=$((failures + 1))
}

# render <name> [helm args...] — render, then collect every document into one
# YAML list in ${work}/<name>.yaml. A failing render is itself a contract
# failure here (expect_refusal covers the renders that must fail).
render() {
  local name="$1"
  shift
  if helm template "${RELEASE}" "${CHART}" "$@" >"${work}/${name}.raw" 2>"${work}/${name}.err"; then
    yq ea '[.]' "${work}/${name}.raw" >"${work}/${name}.yaml"
  else
    fail "render '${name}' failed: $(tr '\n' ' ' <"${work}/${name}.err")"
    echo '[]' >"${work}/${name}.yaml"
  fi
}

# expect_refusal <name> <message-fragment> [helm args...] — the render MUST fail
# and its error MUST carry the fragment (a refusal for another reason is not
# the refusal under test).
expect_refusal() {
  local name="$1" fragment="$2"
  shift 2
  if helm template "${RELEASE}" "${CHART}" "$@" >/dev/null 2>"${work}/${name}.err"; then
    fail "${name}: the render succeeded, expected a refusal mentioning '${fragment}'"
  elif ! grep -qF -- "${fragment}" "${work}/${name}.err"; then
    fail "${name}: the render failed, but not with '${fragment}': $(tr '\n' ' ' <"${work}/${name}.err")"
  fi
}

# expect <render-name> <description> <yq stream over .[]> <expected compact JSON>
#
# Emit values taken FROM the selected nodes, never a literal: in yq,
# `select(false) | "x"` still yields "x", so a contract ending in a literal
# passes over an empty selection (measured on the first draft of the #2122
# NetworkPolicy contract, which was green against the unchanged chart).
expect() {
  local name="$1" description="$2" expression="$3" expected="$4" got
  got="$(yq e "[.[] | ${expression}] | to_json(0)" "${work}/${name}.yaml" 2>&1 || true)"
  if [[ "${got}" != "${expected}" ]]; then
    fail "${name}: ${description} — expected ${expected}, rendered ${got}"
  fi
}

# Same as expect, for answers that are a SET of names whose order depends on how the
# renderer sequences the documents (helm lists a kind's manifests in render order, which
# is not part of the chart's contract). The rendered names are sorted before comparing.
expect_set() {
  local name="$1" description="$2" expression="$3" expected="$4" got
  got="$(yq e "[.[] | ${expression}] | sort | to_json(0)" "${work}/${name}.yaml" 2>&1 || true)"
  if [[ "${got}" != "${expected}" ]]; then
    fail "${name}: ${description} — expected ${expected}, rendered ${got}"
  fi
}

# Selectors used below.
deploy() { printf 'select(.kind == "Deployment" and .metadata.name == "%s-%s")' "${RELEASE}" "$1"; }
main_of() { printf '%s | .spec.template.spec.containers[] | select(.name == "main")' "$(deploy "$1")"; }
env_of() { printf '%s | .env[] | select(.name == "%s") | .value' "$(main_of "$1")" "$2"; }
# The attachment claim is named after the release by bjw-s; a NEW name would be a
# new, empty claim, so the name is part of the contract.
attachments_pvc='select(.kind == "PersistentVolumeClaim" and .metadata.name == "kamerplanter")'

# ---------------------------------------------------------------------------
# Every values profile in the chart renders. A profile that switches controllers
# off (the ki / recognition overlays) still carries every persistence item and
# every string template of values.yaml, and bjw-s refuses a persistence item
# whose controller is disabled — so a new item must follow its controller's
# switch, or every such overlay (in this repository or in a GitOps repository)
# stops rendering. Measured on the first draft of the #2126 `app-user` scratch
# volume: skaffold's ki render failed with "No enabled controller found with
# identifier 'arangodb'".
# ---------------------------------------------------------------------------
for profile in "${CHART}"/values-*.yaml; do
  render "profile-$(basename "${profile}" .yaml)" -f "${profile}"
done

# ---------------------------------------------------------------------------
# #2124 — attachment storage: `storage.backend` is the one switch.
#
# The `backend-attachments` volume is mounted by the backend AND the
# celery-worker. A ReadWriteOnce volume attaches to one node; a second pod on
# another node stays in ContainerCreating with `Multi-Attach error`. Shared
# operation therefore needs S3 (no volume) or a ReadWriteMany class, and the
# chart refuses more than one replica on a ReadWriteOnce volume unless the
# operator states that the cluster has a single node.
# ---------------------------------------------------------------------------
render storage-default
expect storage-default "the default renders the attachment claim exactly as before (name, mode, size, no class)" \
  "${attachments_pvc} | {\"modes\": .spec.accessModes, \"size\": .spec.resources.requests.storage, \"class\": .spec.storageClassName}" \
  '[{"modes":["ReadWriteOnce"],"size":"20Gi","class":null}]'
for controller in backend celery-worker; do
  expect storage-default "${controller} runs STORAGE_BACKEND=local-fs by default" \
    "$(env_of "${controller}" STORAGE_BACKEND)" '["local-fs"]'
  expect storage-default "${controller} mounts the attachment claim by default" \
    "$(deploy "${controller}") | .spec.template.spec.volumes[] | select(.persistentVolumeClaim) | .persistentVolumeClaim.claimName" \
    '["kamerplanter"]'
done

render storage-s3 --set storage.backend=s3 --set storage.s3.bucket=kp-attachments-render
expect storage-s3 "storage.backend=s3 renders no attachment claim" \
  "${attachments_pvc} | .metadata.name" '[]'
for controller in backend celery-worker; do
  expect storage-s3 "${controller} runs STORAGE_BACKEND=s3" \
    "$(env_of "${controller}" STORAGE_BACKEND)" '["s3"]'
  expect storage-s3 "${controller} reads the bucket from storage.s3.bucket" \
    "$(env_of "${controller}" STORAGE_S3_BUCKET)" '["kp-attachments-render"]'
  # Two scoped keys of the credentials Secret, not the whole Secret.
  expect storage-s3 "${controller} takes exactly the two S3 credential keys from storage.s3.credentialsRef" \
    "$(main_of "${controller}") | .env[] | select(.valueFrom.secretKeyRef.name == \"storage-s3-credentials\") | {\"env\": .name, \"key\": .valueFrom.secretKeyRef.key}" \
    '[{"env":"STORAGE_S3_ACCESS_KEY_ID","key":"STORAGE_S3_ACCESS_KEY_ID"},{"env":"STORAGE_S3_SECRET_ACCESS_KEY","key":"STORAGE_S3_SECRET_ACCESS_KEY"}]'
  expect storage-s3 "${controller} mounts no claim with storage.backend=s3" \
    "$(deploy "${controller}") | .spec.template.spec.volumes[] | select(.persistentVolumeClaim) | .name" '[]'
done

expect_refusal storage-rwo-two-backends "ReadWriteMany" --set controllers.backend.replicas=2
expect_refusal storage-rwo-two-workers "ReadWriteMany" --set controllers.celery-worker.replicas=2

render storage-rwx-two-backends --set controllers.backend.replicas=2 \
  --set storage.localFs.pvc.accessMode=ReadWriteMany --set storage.localFs.pvc.storageClass=nfs-client
expect storage-rwx-two-backends "storage.localFs.pvc drives the claim (ReadWriteMany, class)" \
  "${attachments_pvc} | {\"modes\": .spec.accessModes, \"class\": .spec.storageClassName}" \
  '[{"modes":["ReadWriteMany"],"class":"nfs-client"}]'
expect storage-rwx-two-backends "a ReadWriteMany claim carries two backend replicas" \
  "$(deploy backend) | .spec.replicas" '[2]'

render storage-s3-two-backends --set controllers.backend.replicas=2 --set storage.backend=s3
expect storage-s3-two-backends "S3 carries two backend replicas" "$(deploy backend) | .spec.replicas" '[2]'

render storage-single-node-two-backends --set controllers.backend.replicas=2 --set storage.localFs.singleNode=true
expect storage-single-node-two-backends "an acknowledged single-node cluster may run two backends on ReadWriteOnce" \
  "$(deploy backend) | .spec.replicas" '[2]'

# ---------------------------------------------------------------------------
# #2122 — a real ArangoDB backup: `backup.enabled` renders an arangodump CronJob
# that uploads to S3, off by default, never with a password on a command line.
# ---------------------------------------------------------------------------
cronjob='select(.kind == "CronJob" and .metadata.name == "kamerplanter-arangodb-backup")'
backup_pod="${cronjob} | .spec.jobTemplate.spec.template.spec"

expect storage-default "no backup CronJob unless backup.enabled" "${cronjob} | .metadata.name" '[]'

render backup --set backup.enabled=true --set backup.s3.bucket=kp-backup-render
expect backup "backup.enabled renders the CronJob on backup.schedule, one run at a time" \
  "${cronjob} | {\"schedule\": .spec.schedule, \"concurrency\": .spec.concurrencyPolicy}" \
  '[{"schedule":"15 2 * * *","concurrency":"Forbid"}]'
# Client and server version must match: the dump image follows the database's.
expect backup "the dump runs the database's own arangodb image" \
  "${backup_pod} | .initContainers[] | select(.name == \"dump\") | .image" \
  "[$(yq e '[.[] | select(.kind == "StatefulSet" and .metadata.name == "kamerplanter-arangodb") | .spec.template.spec.containers[] | select(.name == "main") | .image] | to_json(0)' "${work}/backup.yaml" | sed 's/^\[//; s/\]$//')]"
expect backup "the dump invokes arangodump against the application database" \
  "${backup_pod} | .initContainers[] | select(.name == \"dump\") | .args[0] | test(\"arangodump[\\s\\S]*--server.database\")" \
  '[true]'
# A password on a command line is readable from /proc by anything sharing the
# PID namespace and lands in process listings; the tools expand @VAR@ themselves.
expect backup "no backup container passes a password on its command line" \
  "${backup_pod} | (.initContainers + .containers)[] | ((.command // []) + (.args // [])) | join(\" \") | test(\"server.password +[^@ ]\")" \
  '[false,false]'
expect backup "the dump password is the one scoped key, not the whole Secret" \
  "${backup_pod} | (.initContainers + .containers)[] | {\"envFrom\": (.envFrom // []), \"keys\": [.env[] | select(.valueFrom.secretKeyRef) | .valueFrom.secretKeyRef.key]}" \
  '[{"envFrom":[],"keys":["ARANGODB_PASSWORD"]},{"envFrom":[],"keys":["AWS_ACCESS_KEY_ID","AWS_SECRET_ACCESS_KEY"]}]'
expect backup "the upload targets backup.s3.bucket with the retention from values" \
  "${backup_pod} | .containers[] | select(.name == \"main\") | .env[] | select(.name == \"BACKUP_S3_BUCKET\" or .name == \"BACKUP_RETENTION_DAYS\") | .name + \"=\" + .value" \
  '["BACKUP_RETENTION_DAYS=30","BACKUP_S3_BUCKET=kp-backup-render"]'
expect backup "every backup container runs non-root on a read-only root filesystem" \
  "${backup_pod} | ([.securityContext.runAsNonRoot] + [(.initContainers + .containers)[] | .securityContext.readOnlyRootFilesystem])[]" \
  '[true,true,true]'
expect backup "the backup pod has its own NetworkPolicy" \
  "select(.kind == \"NetworkPolicy\" and .metadata.name == \"kamerplanter-arangodb-backup\") | .spec.podSelector.matchLabels[\"app.kubernetes.io/controller\"]" \
  '["arangodb-backup"]'
expect backup "ArangoDB admits the backup pod on 8529" \
  "select(.kind == \"NetworkPolicy\" and .metadata.name == \"kamerplanter-arangodb\") | .spec.ingress[] | .from[] | .podSelector.matchLabels[\"app.kubernetes.io/controller\"] | select(. == \"arangodb-backup\")" \
  '["arangodb-backup"]'
expect_refusal backup-without-bucket "backup.s3.bucket" --set backup.enabled=true

# ---------------------------------------------------------------------------
# #2125 — the backend starts under a startup probe, not under liveness.
#
# The lifespan migrates and seeds before uvicorn listens; liveness alone killed
# it ~35 s in. The budget's relation to the migration barrier is held by
# src/backend/tests/unit/guards/test_chart_backend_startup_budget.py (it reads
# the code constant); here the render must carry the probe at all.
# ---------------------------------------------------------------------------
expect storage-default "the backend container renders a startupProbe on the liveness endpoint" \
  "$(main_of backend) | .startupProbe | {\"path\": .httpGet.path, \"budget\": ((.initialDelaySeconds // 0) + .periodSeconds * .failureThreshold)}" \
  '[{"path":"/api/v1/health/live","budget":900}]'

# ---------------------------------------------------------------------------
# #2126 — least-privilege database credentials.
#
# The ArangoDB pod used to receive the WHOLE application Secret by envFrom
# (JWT_SECRET_KEY, FERNET_KEY, INTERNAL_SERVICE_TOKEN, mail/API keys), and the
# application connected as root. Now the database container takes exactly its
# root password, an `app-user` container in the same pod provisions an account
# with rw on the application database only, and every client of the database
# (backend, worker, beat, backup) uses that account.
# ---------------------------------------------------------------------------
sts_container() { printf 'select(.kind == "StatefulSet" and .metadata.name == "kamerplanter-arangodb") | .spec.template.spec.containers[] | select(.name == "%s")' "$1"; }
secret_keys() { printf '%s | {"envFrom": (.envFrom // []), "keys": [.env[] | select(.valueFrom.secretKeyRef) | .valueFrom.secretKeyRef.key]}' "$1"; }

expect storage-default "the database container takes its root password and nothing else of the application Secret" \
  "$(secret_keys "$(sts_container main)")" '[{"envFrom":[],"keys":["ARANGO_ROOT_PASSWORD"]}]'
expect storage-default "the app-user container takes the root password and the application password, nothing else" \
  "$(secret_keys "$(sts_container app-user)")" '[{"envFrom":[],"keys":["ARANGODB_PASSWORD","ARANGO_ROOT_PASSWORD"]}]'
# The data volume belongs to arangod alone; app-user gets only its scratch /tmp
# (arangosh aborts without a writable temp directory — measured).
expect storage-default "only arangod mounts the database volume; app-user mounts exactly a writable /tmp" \
  "select(.kind == \"StatefulSet\" and .metadata.name == \"kamerplanter-arangodb\") | .spec.template.spec.containers[] | {\"c\": .name, \"m\": [.volumeMounts[] | .mountPath]}" \
  '[{"c":"app-user","m":["/tmp"]},{"c":"main","m":["/var/lib/arangodb3-apps","/var/lib/arangodb3"]}]'
expect storage-default "the app-user container passes no password on its command line" \
  "$(sts_container app-user) | ((.command // []) + (.args // [])) | join(\" \") | test(\"server.password +[^@ ]\")" '[false]'
for controller in backend celery-worker celery-beat; do
  expect storage-default "${controller} connects with the application account, not root" \
    "$(env_of "${controller}" ARANGODB_USERNAME)" '["kamerplanter"]'
done
expect storage-default "the app-user container provisions the account the backend uses" \
  "$(sts_container app-user) | .env[] | select(.name == \"ARANGODB_USERNAME\") | .value" '["kamerplanter"]'
expect backup "the backup dumps with the account the backend uses" \
  "${backup_pod} | .initContainers[] | select(.name == \"dump\") | .env[] | select(.name == \"ARANGODB_USERNAME\") | .value" \
  '["kamerplanter"]'

# An operator who keeps root (escape hatch, documented) keeps it everywhere —
# the provisioner then does nothing and the backup follows the backend.
render root-account --set controllers.backend.containers.main.env.ARANGODB_USERNAME=root \
  --set backup.enabled=true --set backup.s3.bucket=kp-backup-render
expect root-account "a backend overridden to root makes the app-user container provision nothing" \
  "$(sts_container app-user) | .env[] | select(.name == \"ARANGODB_USERNAME\") | .value" '["root"]'
render root-secret --set database.arangodb.rootPasswordSecret=kamerplanter-arangodb-root
expect root-secret "database.arangodb.rootPasswordSecret moves the root password to its own Secret, for both arangodb containers" \
  "select(.kind == \"StatefulSet\" and .metadata.name == \"kamerplanter-arangodb\") | .spec.template.spec.containers[] | .env[] | select(.name == \"ARANGO_ROOT_PASSWORD\") | .valueFrom.secretKeyRef.name" \
  '["kamerplanter-arangodb-root","kamerplanter-arangodb-root"]'
expect root-account "a backend overridden to root makes the backup dump as root" \
  "${backup_pod} | .initContainers[] | select(.name == \"dump\") | .env[] | select(.name == \"ARANGODB_USERNAME\") | .value" \
  '["root"]'

# ---------------------------------------------------------------------------
# #2129 — backend metrics: `monitoring.enabled` is the one switch.
#
# Off (the default): no listener (METRICS_PORT=0), no Service port, no
# ServiceMonitor, no scrape policy. On: all four, on 9464, and the backend's
# own policy still admits nothing but :8000 — the scraper reaches the metrics
# port and nothing else, so the scrape path is no way around nginx (#1159).
# ---------------------------------------------------------------------------
servicemonitor='select(.kind == "ServiceMonitor")'
backend_svc='select(.kind == "Service" and .metadata.name == "kamerplanter-backend")'
netpol() { printf 'select(.kind == "NetworkPolicy" and .metadata.name == "%s-%s")' "${RELEASE}" "$1"; }
expect storage-default "monitoring off: the backend starts no metrics listener" "$(env_of backend METRICS_PORT)" '["0"]'
expect storage-default "monitoring off: no ServiceMonitor" "${servicemonitor} | .metadata.name" '[]'
expect storage-default "monitoring off: the backend Service exposes only http" "${backend_svc} | .spec.ports[] | .name" '["http"]'
expect storage-default "monitoring off: no scrape policy" "$(netpol backend-metrics) | .metadata.name" '[]'

render monitoring --set monitoring.enabled=true
expect monitoring "monitoring.enabled starts the listener on 9464" "$(env_of backend METRICS_PORT)" '["9464"]'
expect monitoring "the backend Service adds the metrics port" \
  "${backend_svc} | .spec.ports[] | select(.name == \"metrics\") | .port" '[9464]'
expect monitoring "the ServiceMonitor scrapes the metrics port of the backend Service" \
  "${servicemonitor} | .spec.endpoints[] | [.port, .path] | join(\" \")" '["metrics /metrics"]'
expect monitoring "the ServiceMonitor selects the backend Service" \
  "${servicemonitor} | .spec.selector.matchLabels.\"app.kubernetes.io/service\"" '["kamerplanter-backend"]'
expect monitoring "the scrape policy admits the metrics port only" \
  "$(netpol backend-metrics) | .spec.ingress[] | .ports[] | .port" '[9464]'
expect monitoring "the scrape policy names the scraper by namespace and pod" \
  "$(netpol backend-metrics) | .spec.ingress[] | .from[] | [.namespaceSelector.matchLabels.\"kubernetes.io/metadata.name\", .podSelector.matchLabels.\"app.kubernetes.io/name\"] | join(\"/\")" \
  '["monitoring/prometheus"]'
expect monitoring "the backend's own policy still admits only :8000" \
  "$(netpol backend) | .spec.ingress[] | .ports[] | .port" '[8000]'
for profile in "${CHART}"/values-*.yaml; do
  render "monitoring-$(basename "${profile}" .yaml)" -f "${profile}" --set monitoring.enabled=true
done

# ---------------------------------------------------------------------------
# #2128 (MT-032) — the worker consumes every queue the application routes to.
#
# app/tasks/routing.py routes tasks to `critical`, `celery` (the default) and
# `bulk`. A queue no worker consumes keeps its tasks in Valkey forever and
# nobody is told. The list must be exactly the code's QUEUES, in every profile
# that runs a worker; tests/unit/guards/test_every_task_has_a_queue.py holds
# the code side (it reads the same values files and the live Celery config).
# ---------------------------------------------------------------------------
worker_queues() { printf '%s | .args | join(" ") | capture("(^| )(-Q|--queues)[ =](?P<q>[^ ]+)") | .q | split(",") | .[]' "$(main_of celery-worker)"; }
expect storage-default "the worker consumes critical, celery and bulk" "$(worker_queues)" '["critical","celery","bulk"]'
expect profile-values-dev "the dev worker consumes critical, celery and bulk" "$(worker_queues)" '["critical","celery","bulk"]'
expect storage-default "the worker excludes no queue" \
  "$(main_of celery-worker) | .args[] | select(test(\"^(-X|--exclude-queues)\"))" '[]'

# ---------------------------------------------------------------------------
# #2128 (MT-032) — `celeryWorkers.dedicatedQueues`: one worker Deployment per queue.
#
# On, celery-worker consumes `critical` only and two copies of it consume
# `celery` and `bulk`. Every queue must still have exactly one consumer, and the
# copies must be the worker in every respect but the queue. The copies are made
# at render time from the MERGED values (templates/_celery_workers.tpl), so an
# overlay that changes or hardens celery-worker — image, env, securityContext,
# egress — must reach them; a YAML anchor would not (security review SEC-001).
# Checked on the base values, on values-dev.yaml and on an overlay: the same
# image, pod and container securityContext and env as the worker, the same
# attachment claim (a new name would be a new, empty claim), one NetworkPolicy
# per worker with identical egress, and a peer on every policy that admits the
# worker (ArangoDB, Valkey, inference-service). Off — the default — nothing of
# it renders. In a profile that switches celery-worker off, no copy appears.
# ---------------------------------------------------------------------------
queues_of() { printf '%s | .args | join(" ") | capture("(^| )(-Q|--queues)[ =](?P<q>[^ ]+)") | .q | split(",") | .[]' "$(main_of "$1")"; }
worker_deploys='select(.kind == "Deployment" and (.metadata.name | test("^kamerplanter-celery-worker")))'
worker_mains="${worker_deploys} | .spec.template.spec.containers[] | select(.name == \"main\")"

# distinct_over <render> <description> <yq expression per worker> — the three
# workers render the expression to ONE value (not "some value": three copies of
# nothing would also be one, so the count of workers is asserted as well).
distinct_over() {
  local name="$1" description="$2" expression="$3" got
  got="$(yq e "[.[] | ${worker_deploys} | (${expression}) | to_json(0)] | {\"workers\": length, \"distinct\": (unique | length)} | to_json(0)" "${work}/${name}.yaml" 2>&1 || true)"
  if [[ "${got}" != '{"workers":3,"distinct":1}' ]]; then
    fail "${name}: ${description} — expected one value over three workers, rendered ${got}"
  fi
}

# worker_set <render> — the contracts every dedicated render must hold.
worker_set() {
  local name="$1" got
  expect "${name}" "celery-worker consumes critical only" "$(queues_of celery-worker)" '["critical"]'
  expect "${name}" "celery-worker-default consumes celery" "$(queues_of celery-worker-default)" '["celery"]'
  expect "${name}" "celery-worker-bulk consumes bulk" "$(queues_of celery-worker-bulk)" '["bulk"]'
  expect_set "${name}" "every queue has exactly one consumer" \
    "${worker_mains} | .args | join(\" \") | capture(\"(^| )(-Q|--queues)[ =](?P<q>[^ ]+)\") | .q | split(\",\") | .[]" \
    '["bulk","celery","critical"]'
  distinct_over "${name}" "the same image" '.spec.template.spec.containers[] | select(.name == "main") | .image'
  distinct_over "${name}" "the same pod securityContext" '.spec.template.spec.securityContext'
  distinct_over "${name}" "the same container securityContext" '.spec.template.spec.containers[] | select(.name == "main") | .securityContext'
  distinct_over "${name}" "the same env and envFrom" '.spec.template.spec.containers[] | select(.name == "main") | {"env": .env, "envFrom": .envFrom}'
  distinct_over "${name}" "the same probes and resources" '.spec.template.spec.containers[] | select(.name == "main") | {"r": .readinessProbe, "s": .startupProbe, "l": .livenessProbe, "res": .resources}'
  distinct_over "${name}" "the same mounts" '.spec.template.spec.containers[] | select(.name == "main") | [.volumeMounts[] | .mountPath] | sort'
  got="$(yq e '[.[] | select(.kind == "NetworkPolicy" and (.metadata.name | test("^kamerplanter-celery-worker"))) | .spec.egress | to_json(0)] | {"policies": length, "distinct": (unique | length)} | to_json(0)' "${work}/${name}.yaml")"
  if [[ "${got}" != '{"policies":3,"distinct":1}' ]]; then
    fail "${name}: every worker needs its own NetworkPolicy with the worker's egress — rendered ${got}"
  fi
  for peer in arangodb valkey inference-service; do
    expect_set "${name}" "the ${peer} policy admits every worker" \
      "$(netpol "${peer}") | .spec.ingress[] | .from[] | .podSelector.matchLabels.\"app.kubernetes.io/controller\" | select(. != null and test(\"^celery-worker\"))" \
      '["celery-worker","celery-worker-bulk","celery-worker-default"]'
  done
}

inference_on=(--set controllers.inference-service.enabled=true --set service.inference-service.enabled=true
  --set networkpolicies.inference-service.enabled=true)
render workers-dedicated --set celeryWorkers.dedicatedQueues=true "${inference_on[@]}"
worker_set workers-dedicated
render workers-dedicated-dev -f "${CHART}/values-dev.yaml" --set celeryWorkers.dedicatedQueues=true "${inference_on[@]}"
worker_set workers-dedicated-dev

# An overlay that hardens / changes the worker reaches the copies (SEC-001).
cat >"${work}/worker-overlay.yaml" <<'OVERLAY'
celeryWorkers:
  dedicatedQueues: true
controllers:
  celery-worker:
    pod:
      securityContext:
        runAsUser: 4242
    containers:
      main:
        image:
          tag: 9.9.9-render
        env:
          OVERLAY_MARKER: "render"
        securityContext:
          privileged: false
networkpolicies:
  celery-worker:
    rules:
      egress:
        - to:
            - podSelector:
                matchLabels:
                  app.kubernetes.io/controller: arangodb
          ports:
            - protocol: TCP
              port: 8529
OVERLAY
render workers-dedicated-overlay -f "${work}/worker-overlay.yaml" "${inference_on[@]}"
worker_set workers-dedicated-overlay
expect workers-dedicated-overlay "the overlay's image reaches every worker" \
  "${worker_mains} | .image" \
  '["ghcr.io/nolte/kamerplanter-backend:9.9.9-render","ghcr.io/nolte/kamerplanter-backend:9.9.9-render","ghcr.io/nolte/kamerplanter-backend:9.9.9-render"]'
expect workers-dedicated-overlay "the overlay's pod securityContext reaches every worker" \
  "${worker_deploys} | .spec.template.spec.securityContext.runAsUser" '[4242,4242,4242]'
expect workers-dedicated-overlay "the overlay's env reaches every worker" \
  "${worker_mains} | .env[] | select(.name == \"OVERLAY_MARKER\") | .value" '["render","render","render"]'
expect workers-dedicated-overlay "the overlay's narrowed egress reaches every worker policy" \
  "select(.kind == \"NetworkPolicy\" and (.metadata.name | test(\"^kamerplanter-celery-worker\"))) | .spec.egress | length" '[1,1,1]'

# A copy can be tuned on its own; the queue is not one of the knobs.
render workers-dedicated-tuned --set celeryWorkers.dedicatedQueues=true \
  --set controllers.celery-worker-bulk.containers.main.resources.limits.memory=3Gi
expect workers-dedicated-tuned "a per-copy key reaches that copy" "$(main_of celery-worker-bulk) | .resources.limits.memory" '["3Gi"]'
for untouched in celery-worker celery-worker-default; do
  expect workers-dedicated-tuned "a per-copy key leaves ${untouched} alone" "$(main_of "${untouched}") | .resources.limits.memory" '["2Gi"]'
done
expect workers-dedicated-tuned "tuning a copy keeps its queue" "$(queues_of celery-worker-bulk)" '["bulk"]'

expect storage-default "no dedicated worker renders by default" \
  "select(.metadata.name | test(\"^kamerplanter-celery-worker-(default|bulk)$\")) | .kind" '[]'
render workers-off-stray --set controllers.celery-worker-bulk.replicas=2
expect workers-off-stray "a copy's key without the switch renders no copy" \
  "select(.metadata.name | test(\"^kamerplanter-celery-worker-(default|bulk)$\")) | .kind" '[]'
expect workers-dedicated "the copies mount the worker's attachment claim, and no second claim exists" \
  "${worker_deploys} | .spec.template.spec.volumes[] | select(.persistentVolumeClaim) | .persistentVolumeClaim.claimName" \
  '["kamerplanter","kamerplanter","kamerplanter"]'
# Chart-owned claims only: since #2127 the valkey subchart renders its own claim.
expect workers-dedicated "one attachment claim" \
  'select(.kind == "PersistentVolumeClaim" and .metadata.labels["app.kubernetes.io/name"] == "kamerplanter") | .metadata.name' '["kamerplanter"]'
expect workers-dedicated "every worker writes and probes its readiness file on its own /tmp" \
  "${worker_mains} | [(.env[] | select(.name == \"WORKER_READY_FILE\") | .value), (.volumeMounts[] | select(.mountPath == \"/tmp\") | .mountPath), (.readinessProbe.exec.command | join(\" \"))] | join(\"|\")" \
  '["/tmp/worker-ready|/tmp|test -f /tmp/worker-ready","/tmp/worker-ready|/tmp|test -f /tmp/worker-ready","/tmp/worker-ready|/tmp|test -f /tmp/worker-ready"]'
render workers-dedicated-s3 --set celeryWorkers.dedicatedQueues=true --set storage.backend=s3 --set storage.s3.bucket=kp-attachments-render
expect workers-dedicated-s3 "with s3 no worker mounts a claim" \
  "${worker_deploys} | .spec.template.spec.volumes[] | select(.persistentVolumeClaim) | .persistentVolumeClaim.claimName" '[]'
for profile in values-dev-ki values-dev-recognition; do
  render "workers-dedicated-${profile}" -f "${CHART}/${profile}.yaml" --set celeryWorkers.dedicatedQueues=true
  expect "workers-dedicated-${profile}" "a profile without the worker gets no copy of it" "${worker_deploys} | .metadata.name" '[]'
done
expect_refusal workers-dedicated-bulk-two-rwo "controllers.celery-worker-bulk scales to 2" \
  --set celeryWorkers.dedicatedQueues=true --set controllers.celery-worker-bulk.replicas=2

# ---------------------------------------------------------------------------
# #2154 — the worker is ready when its consumer runs, and only then.
#
# No readiness probe meant a worker counted ready at container start: an
# upgrade whose worker could not log in to ArangoDB replaced the old worker
# anyway. The worker now writes WORKER_READY_FILE once it consumes (after
# proving its database login); startup and readiness probes test that same
# path. The startup budget's relation to the worker's database gate is held by
# tests/unit/guards/test_chart_worker_probes.py.
# ---------------------------------------------------------------------------
ready_file="$(yq e '[.[] | select(.kind == "Deployment" and .metadata.name == "kamerplanter-celery-worker") | .spec.template.spec.containers[] | select(.name == "main") | .env[] | select(.name == "WORKER_READY_FILE") | .value] | .[0] // ""' "${work}/storage-default.yaml")"
if [[ -z "${ready_file}" ]]; then
  fail "storage-default: the worker sets no WORKER_READY_FILE"
fi
for probe in startupProbe readinessProbe; do
  expect storage-default "the worker ${probe} tests the file the worker writes" \
    "$(main_of celery-worker) | .${probe}.exec.command | join(\" \")" "[\"test -f ${ready_file}\"]"
done
expect storage-default "the worker liveness asks this pod's own worker, not any worker" \
  "$(main_of celery-worker) | .livenessProbe.exec.command | join(\" \") | (contains(\"inspect ping -d\") and contains(\"celery@\") and contains(\"HOSTNAME\"))" '[true]'
expect profile-values-dev "the dev worker carries the readiness probe too" \
  "$(main_of celery-worker) | .readinessProbe.exec.command | join(\" \")" "[\"test -f ${ready_file}\"]"

# ---------------------------------------------------------------------------
# #2153 — every pod on a ReadWriteOnce attachment claim shares one node.
#
# Backend and celery-worker mount the claim; a rolling update (surge 1) or a
# worker scheduled apart from the backend put a second pod on another node,
# where the volume cannot attach (Multi-Attach). Both carry one label and
# require a pod with it on the same hostname; with S3 or ReadWriteMany the
# topology key is `kubernetes.io/os` (one value on every node), i.e. no
# constraint. The rolling strategy stays: no downtime to buy this.
# ---------------------------------------------------------------------------
attach_term() { printf '%s | .spec.template.spec.affinity.podAffinity.requiredDuringSchedulingIgnoredDuringExecution[] | .topologyKey' "$(deploy "$1")"; }
attach_label() { printf '%s | .spec.template.metadata.labels["kamerplanter.io/attachments-volume"]' "$(deploy "$1")"; }
attach_selector() { printf '%s | .spec.template.spec.affinity.podAffinity.requiredDuringSchedulingIgnoredDuringExecution[] | .labelSelector.matchLabels["kamerplanter.io/attachments-volume"]' "$(deploy "$1")"; }
for controller in backend celery-worker; do
  expect storage-default "${controller} carries the attachment-volume label" "$(attach_label "${controller}")" '["kamerplanter"]'
  expect storage-default "${controller} requires a pod with that label" "$(attach_selector "${controller}")" '["kamerplanter"]'
  expect storage-default "${controller} shares the node of the ReadWriteOnce claim" "$(attach_term "${controller}")" '["kubernetes.io/hostname"]'
  expect storage-default "${controller} keeps the zero-downtime rolling update" \
    "$(deploy "${controller}") | .spec.strategy | [.type, .rollingUpdate.maxUnavailable] | join(\" \")" '["RollingUpdate 0"]'
  expect storage-single-node-two-backends "${controller} shares the node on an acknowledged single-node cluster too" \
    "$(attach_term "${controller}")" '["kubernetes.io/hostname"]'
  expect storage-s3 "${controller} is not pinned to a node with storage.backend=s3" "$(attach_term "${controller}")" '["kubernetes.io/os"]'
  expect storage-rwx-two-backends "${controller} is not pinned to a node on a ReadWriteMany claim" \
    "$(attach_term "${controller}")" '["kubernetes.io/os"]'
done
expect_set storage-default "no other pod requires the attachment-volume label" \
  "select(.kind == \"Deployment\" or .kind == \"StatefulSet\") | select(.spec.template.spec.affinity.podAffinity) | .metadata.name" \
  '["kamerplanter-backend","kamerplanter-celery-worker"]'

# ---------------------------------------------------------------------------
# #2144 (audit gap G-10) — the edge body limit follows the upload bound.
#
# The chart's default.conf replaces the image's nginx configuration, and it set
# no client_max_body_size: nginx's 1 MiB default refused every upload above
# 1 MiB with 413 (measured in the nginx-unprivileged image, see
# scripts/ci/probe_proxy_body_limit.sh). nginx and the ingress annotation now
# carry storage.maxFileSizeMb + 1 MiB of multipart headroom — one expression,
# so raising the upload bound raises both. The ingress `main` renders only with
# hosts; when it renders, it carries the annotation. The Settings side of the
# derivation is src/backend/tests/unit/guards/test_proxy_body_limit.py.
# ---------------------------------------------------------------------------
nginx_limit='select(.kind == "ConfigMap" and .metadata.name == "kamerplanter") | .data["default.conf"] | capture("(?m)^\s*client_max_body_size\s+(?P<v>[^;]+);") | .v'
ingress_limit='select(.kind == "Ingress") | .metadata.annotations["nginx.ingress.kubernetes.io/proxy-body-size"]'
ingress_hosts=(--set 'ingress.main.hosts[0].host=kp.example.test'
  --set 'ingress.main.hosts[0].paths[0].path=/'
  --set 'ingress.main.hosts[0].paths[0].service.identifier=frontend')

expect storage-default "nginx limits the body to storage.maxFileSizeMb + 1 MiB" "${nginx_limit}" '["26m"]'
expect storage-default "no ingress renders without hosts" 'select(.kind == "Ingress") | .metadata.name' '[]'

render body-limit-ingress "${ingress_hosts[@]}"
expect body-limit-ingress "the ingress carries the nginx limit as proxy-body-size" "${ingress_limit}" '["26m"]'

render body-limit-raised --set storage.maxFileSizeMb=50 "${ingress_hosts[@]}"
expect body-limit-raised "a raised upload bound raises the nginx limit" "${nginx_limit}" '["51m"]'
expect body-limit-raised "a raised upload bound raises the ingress limit" "${ingress_limit}" '["51m"]'
expect body-limit-raised "the backend receives the raised upload bound" \
  "$(env_of backend STORAGE_MAX_FILE_SIZE_MB)" '["50"]'

render body-limit-ingress-off --set ingress.main.enabled=false "${ingress_hosts[@]}"
expect body-limit-ingress-off "ingress.main.enabled=false still switches the ingress off" \
  'select(.kind == "Ingress") | .metadata.name' '[]'

expect profile-values-dev "the dev ingress carries the nginx limit as proxy-body-size" "${ingress_limit}" '["26m"]'
# /api reaches the backend through the frontend (#1159): the backend policy
# admits only the frontend, and only that path carries the body limit and the
# X-Forwarded-For depth TRUSTED_PROXY_HOPS is set for. Every in-chart ingress
# routes to the frontend Service and nowhere else.
ingress_targets='select(.kind == "Ingress") | .spec.rules[].http.paths[] | .backend.service.name'
expect profile-values-dev "the dev ingress routes every path to the frontend" "${ingress_targets}" '["kamerplanter-frontend"]'
expect body-limit-ingress "the ingress routes every path to the frontend" "${ingress_targets}" '["kamerplanter-frontend"]'

# ---------------------------------------------------------------------------
# #2127 (MT-031) — scaling and secret-store switches are opt-in.
#
# HPA and PDB use the bjw-s keys `controllers.<name>.horizontalPodAutoscaler` /
# `.podDisruptionBudget`, the ExternalSecret `externalSecrets.app`. None of them
# renders by default or in any profile, so an existing release is unchanged.
# What the switches must not do once on: scale a backend or worker past one
# pod on a ReadWriteOnce attachment volume (the #2124 refusal, now also for
# maxReplicas), run a second celery-beat / arangodb / vectordb pod, or ship a
# PodDisruptionBudget that admits no eviction (every drain hangs).
# ---------------------------------------------------------------------------
opt_in_kinds='select(.kind == "HorizontalPodAutoscaler" or .kind == "PodDisruptionBudget" or .kind == "ExternalSecret") | .kind'
expect storage-default "the default renders no HPA, PDB or ExternalSecret" "${opt_in_kinds}" '[]'
for profile in "${CHART}"/values-*.yaml; do
  expect "profile-$(basename "${profile}" .yaml)" "no profile renders an HPA, PDB or ExternalSecret" "${opt_in_kinds}" '[]'
done
expect storage-default "celery-beat stays a single pod replaced by Recreate" \
  "$(deploy celery-beat) | {\"replicas\": .spec.replicas, \"strategy\": .spec.strategy.type}" \
  '[{"replicas":1,"strategy":"Recreate"}]'

render scaling-backend --set storage.backend=s3 --set storage.s3.bucket=kp-attachments-render \
  --set controllers.backend.horizontalPodAutoscaler.minReplicas=2 \
  --set controllers.backend.horizontalPodAutoscaler.maxReplicas=6 \
  --set controllers.backend.podDisruptionBudget.minAvailable=1
expect scaling-backend "the backend HPA targets the backend Deployment with the configured bounds" \
  'select(.kind == "HorizontalPodAutoscaler") | {"kind": .spec.scaleTargetRef.kind, "target": .spec.scaleTargetRef.name, "min": .spec.minReplicas, "max": .spec.maxReplicas}' \
  '[{"kind":"Deployment","target":"kamerplanter-backend","min":2,"max":6}]'
# A fixed replica count next to an HPA makes every sync (helm, ArgoCD) reset
# what the autoscaler scaled to.
expect scaling-backend "the autoscaled backend Deployment carries no fixed replica count" \
  "$(deploy backend) | .spec | has(\"replicas\")" '[false]'
# A PDB whose selector matches no pod protects nothing; it must select exactly
# what the Deployment selects.
expect scaling-backend "the backend PDB selects the backend pods" \
  'select(.kind == "PodDisruptionBudget") | {"min": .spec.minAvailable, "selector": (.spec.selector.matchLabels | sort_keys(.))}' \
  '[{"min":1,"selector":{"app.kubernetes.io/controller":"backend","app.kubernetes.io/instance":"kamerplanter","app.kubernetes.io/name":"kamerplanter"}}]'
expect scaling-backend "the backend Deployment selects the same labels" \
  "$(deploy backend) | .spec.selector.matchLabels | sort_keys(.)" \
  '[{"app.kubernetes.io/controller":"backend","app.kubernetes.io/instance":"kamerplanter","app.kubernetes.io/name":"kamerplanter"}]'

render scaling-frontend --set controllers.frontend.replicas=2 --set controllers.frontend.podDisruptionBudget.minAvailable=1
expect scaling-frontend "two frontend pods with a PDB of one" \
  "select(.kind == \"PodDisruptionBudget\") | .spec.selector.matchLabels[\"app.kubernetes.io/controller\"]" '["frontend"]'

expect_refusal scaling-hpa-backend-rwo "ReadWriteMany" --set controllers.backend.horizontalPodAutoscaler.maxReplicas=4
expect_refusal scaling-hpa-worker-rwo "ReadWriteMany" --set controllers.celery-worker.horizontalPodAutoscaler.maxReplicas=3
expect_refusal scaling-pdb-single-pod "admits no eviction" --set controllers.frontend.podDisruptionBudget.minAvailable=1
expect_refusal scaling-pdb-at-hpa-minimum "admits no eviction" \
  --set storage.backend=s3 --set storage.s3.bucket=kp-attachments-render \
  --set controllers.backend.horizontalPodAutoscaler.minReplicas=2 \
  --set controllers.backend.horizontalPodAutoscaler.maxReplicas=4 \
  --set controllers.backend.podDisruptionBudget.minAvailable=2
for singleton in celery-beat arangodb; do
  expect_refusal "scaling-${singleton}-replicas" "runs exactly one pod" --set "controllers.${singleton}.replicas=2"
  expect_refusal "scaling-${singleton}-hpa" "runs exactly one pod" --set "controllers.${singleton}.horizontalPodAutoscaler.maxReplicas=2"
done
# vectordb is off by default, and the refusal deliberately skips a disabled
# controller — so the contract switches it on, and the disabled case is held too.
expect_refusal scaling-vectordb-replicas "runs exactly one pod" \
  --set controllers.vectordb.enabled=true --set controllers.vectordb.replicas=2
expect_refusal scaling-vectordb-hpa "runs exactly one pod" \
  --set controllers.vectordb.enabled=true --set controllers.vectordb.horizontalPodAutoscaler.maxReplicas=2
render scaling-vectordb-disabled --set controllers.vectordb.replicas=2
expect scaling-vectordb-disabled "a disabled vectordb with replicas=2 renders no vectordb workload" \
  'select(.kind == "StatefulSet" or .kind == "Deployment") | select(.metadata.name == "kamerplanter-vectordb") | .metadata.name' '[]'

# A PDB admits no eviction in more spellings than minAvailable >= pods:
# maxUnavailable 0 (as number, "0" or "0%"), and a percentage minAvailable that
# Kubernetes rounds UP to every pod ("100%" always; "50%" of a single pod).
# A percentage that leaves one pod evictable must still render.
expect_refusal scaling-pdb-max-unavailable-zero "admits no eviction" \
  --set controllers.frontend.replicas=2 --set controllers.frontend.podDisruptionBudget.maxUnavailable=0
expect_refusal scaling-pdb-max-unavailable-zero-string "admits no eviction" \
  --set controllers.frontend.replicas=2 --set-string controllers.frontend.podDisruptionBudget.maxUnavailable=0
expect_refusal scaling-pdb-max-unavailable-zero-percent "admits no eviction" \
  --set controllers.frontend.replicas=2 --set-string controllers.frontend.podDisruptionBudget.maxUnavailable=0%
expect_refusal scaling-pdb-min-available-all-percent "admits no eviction" \
  --set controllers.frontend.replicas=3 --set-string controllers.frontend.podDisruptionBudget.minAvailable=100%
expect_refusal scaling-pdb-min-available-percent-of-one "admits no eviction" \
  --set-string controllers.frontend.podDisruptionBudget.minAvailable=50%
render scaling-pdb-percent --set controllers.frontend.replicas=2 \
  --set-string controllers.frontend.podDisruptionBudget.minAvailable=50%
expect scaling-pdb-percent "a 50% minAvailable of two pods renders unchanged" \
  'select(.kind == "PodDisruptionBudget") | .spec.minAvailable' '["50%"]'
render scaling-pdb-max-unavailable-percent --set controllers.frontend.replicas=2 \
  --set-string controllers.frontend.podDisruptionBudget.maxUnavailable=25%
expect scaling-pdb-max-unavailable-percent "a 25% maxUnavailable renders (Kubernetes rounds it up to one pod)" \
  'select(.kind == "PodDisruptionBudget") | .spec.maxUnavailable' '["25%"]'
render scaling-pdb-max-unavailable-one --set controllers.frontend.replicas=2 \
  --set controllers.frontend.podDisruptionBudget.maxUnavailable=1
expect scaling-pdb-max-unavailable-one "maxUnavailable 1 renders" \
  'select(.kind == "PodDisruptionBudget") | .spec.maxUnavailable' '[1]'

render external-secret --set externalSecrets.app.enabled=true --set externalSecrets.app.secretStoreRef.name=kp-store-render
expect external-secret "the ExternalSecret writes the Secret the pods read, retained when the store entry goes" \
  'select(.kind == "ExternalSecret") | {"secret": .spec.target.name, "creation": .spec.target.creationPolicy, "deletion": .spec.target.deletionPolicy, "store": .spec.secretStoreRef.name}' \
  '[{"secret":"kamerplanter-secrets","creation":"Owner","deletion":"Retain","store":"kp-store-render"}]'
expect external-secret "the pods read their envFrom Secret from that same name" \
  'select(.kind == "Deployment" or .kind == "StatefulSet") | .spec.template.spec.containers[] | (.envFrom // [])[] | .secretRef.name' \
  '["kamerplanter-secrets","kamerplanter-secrets","kamerplanter-secrets"]'
expect_refusal external-secret-without-store "has no SecretStore reference" --set externalSecrets.app.enabled=true

# ---------------------------------------------------------------------------
# #2127 (MT-031) — TimescaleDB as a chart controller, Valkey hardened.
#
# `controllers.timescaledb.enabled` is the one switch: Service, NetworkPolicy,
# scratch volumes and TIMESCALEDB_ENABLED on backend, worker and beat follow
# it. Half a switch fails silently in the cluster — a database without its
# NetworkPolicy is unreachable under the default-deny baseline, an application
# with TIMESCALEDB_ENABLED=false never writes to a running database, one with
# `true` and no database fails every sensor ingestion. The password comes from
# kamerplanter-secrets by secretKeyRef, never as a literal.
#
# Valkey is the Celery broker: the queued tasks live in it. The chart used to
# set `valkey.dataStorage.size`, which the subchart does not read — no claim
# was rendered and /data was an emptyDir, so every restart lost the queue.
# ---------------------------------------------------------------------------
ts_kinds='select(.metadata.name == "kamerplanter-timescaledb") | .kind'
expect storage-default "the default renders no TimescaleDB object" "${ts_kinds}" '[]'
for controller in backend celery-worker celery-beat; do
  expect storage-default "${controller} runs with TIMESCALEDB_ENABLED=false by default" \
    "$(env_of "${controller}" TIMESCALEDB_ENABLED)" '["false"]'
done

render timescaledb --set controllers.timescaledb.enabled=true
expect_set timescaledb "one switch renders the database, its Service and its NetworkPolicy" "${ts_kinds}" \
  '["NetworkPolicy","Service","StatefulSet"]'
for controller in backend celery-worker celery-beat; do
  expect timescaledb "${controller} follows the switch (TIMESCALEDB_ENABLED=true)" \
    "$(env_of "${controller}" TIMESCALEDB_ENABLED)" '["true"]'
  expect timescaledb "${controller} looks for the database under the Service's name" \
    "$(env_of "${controller}" TIMESCALEDB_HOST)" '["kamerplanter-timescaledb"]'
done
ts_main='select(.kind == "StatefulSet" and .metadata.name == "kamerplanter-timescaledb") | .spec.template.spec.containers[] | select(.name == "main")'
expect timescaledb "the database password comes from kamerplanter-secrets by secretKeyRef, under the key the backend reads" \
  "${ts_main} | .env[] | select(.name == \"POSTGRES_PASSWORD\") | {\"value\": has(\"value\"), \"ref\": .valueFrom.secretKeyRef}" \
  '[{"value":false,"ref":{"key":"TIMESCALEDB_PASSWORD","name":"kamerplanter-secrets"}}]'
expect timescaledb "the database reads no Secret in full" "${ts_main} | (.envFrom // [])[]" '[]'
expect timescaledb "the database runs non-root as the image's postgres user, RuntimeDefault seccomp" \
  'select(.kind == "StatefulSet" and .metadata.name == "kamerplanter-timescaledb") | .spec.template.spec.securityContext | {"nonRoot": .runAsNonRoot, "uid": .runAsUser, "fsGroup": .fsGroup, "seccomp": .seccompProfile.type}' \
  '[{"nonRoot":true,"uid":70,"fsGroup":70,"seccomp":"RuntimeDefault"}]'
expect timescaledb "the database container: read-only root, no escalation, no capabilities" \
  "${ts_main} | .securityContext | {\"ro\": .readOnlyRootFilesystem, \"esc\": .allowPrivilegeEscalation, \"drop\": .capabilities.drop}" \
  '[{"ro":true,"esc":false,"drop":["ALL"]}]'
expect timescaledb "the only writable paths besides the data volume are the socket directory and /tmp" \
  "${ts_main} | [.volumeMounts[] | .mountPath] | sort" \
  '[["/tmp","/var/lib/postgresql/data","/var/run/postgresql"]]'
expect timescaledb "the NetworkPolicy admits backend and celery-worker on 5432" \
  'select(.kind == "NetworkPolicy" and .metadata.name == "kamerplanter-timescaledb") | .spec.ingress[] | {"from": [.from[] | .podSelector.matchLabels["app.kubernetes.io/controller"]], "ports": [.ports[] | .port]}' \
  '[{"from":["backend","celery-worker"],"ports":[5432]}]'
# A password literal anywhere in the rendered workloads is a secret in the values.
expect timescaledb "no workload carries a *PASSWORD* env literal" \
  'select(.kind == "Deployment" or .kind == "StatefulSet" or .kind == "CronJob") | .. | select(tag == "!!map" and has("name") and has("value")) | select(.name | test("PASSWORD")) | .name' '[]'
expect_refusal timescaledb-replicas "runs exactly one pod" \
  --set controllers.timescaledb.enabled=true --set controllers.timescaledb.replicas=2
expect_refusal timescaledb-hpa "runs exactly one pod" \
  --set controllers.timescaledb.enabled=true --set controllers.timescaledb.horizontalPodAutoscaler.maxReplicas=2
render timescaledb-workers --set controllers.timescaledb.enabled=true --set celeryWorkers.dedicatedQueues=true
expect_set timescaledb-workers "every dedicated worker reaches the database" \
  'select(.kind == "NetworkPolicy" and .metadata.name == "kamerplanter-timescaledb") | .spec.ingress[].from[] | .podSelector.matchLabels["app.kubernetes.io/controller"]' \
  '["backend","celery-worker","celery-worker-bulk","celery-worker-default"]'
expect profile-values-dev "the dev profile runs TimescaleDB and tells the backend so" \
  "select(.kind == \"StatefulSet\" and .metadata.name == \"kamerplanter-timescaledb\") | .metadata.name" '["kamerplanter-timescaledb"]'

valkey_deploy='select(.kind == "Deployment" and .metadata.name == "kamerplanter-valkey")'
expect storage-default "Valkey keeps its data on a claim, not on an emptyDir" \
  "${valkey_deploy} | .spec.template.spec.volumes[] | select(.name == \"valkey-data\") | {\"claim\": .persistentVolumeClaim.claimName, \"emptyDir\": has(\"emptyDir\")}" \
  '[{"claim":"kamerplanter-valkey","emptyDir":false}]'
expect storage-default "the Valkey claim survives helm uninstall" \
  'select(.kind == "PersistentVolumeClaim" and .metadata.name == "kamerplanter-valkey") | {"size": .spec.resources.requests.storage, "keep": .metadata.annotations["helm.sh/resource-policy"]}' \
  '[{"size":"1Gi","keep":"keep"}]'
expect storage-default "Valkey is replaced by Recreate (its claim is ReadWriteOnce)" \
  "${valkey_deploy} | .spec.strategy.type" '["Recreate"]'
expect storage-default "Valkey refuses writes when full and logs every write (maxmemory, noeviction, AOF)" \
  'select(.kind == "ConfigMap" and .metadata.name == "kamerplanter-valkey-config") | .data["valkey.conf"] | split("\n") | map(select(test("^(maxmemory|appendonly|appendfsync)")))' \
  '[["maxmemory 256mb","maxmemory-policy noeviction","appendonly yes","appendfsync everysec"]]'
expect storage-default "Valkey's memory limit leaves room for the fork of an AOF rewrite (twice maxmemory)" \
  "${valkey_deploy} | .spec.template.spec.containers[] | select(.name == \"kamerplanter-valkey\") | .resources.limits.memory" '["512Mi"]'

# NFR-002 §11 "Resource Limits gesetzt": every container of every workload —
# init containers, the optional database and the backup job included — has a
# memory limit; one without can take the node's memory from the others.
render all-workloads --set controllers.timescaledb.enabled=true \
  --set backup.enabled=true --set backup.s3.bucket=kp-backup-render
expect all-workloads "every container has a memory limit" \
  'select(.kind == "Deployment" or .kind == "StatefulSet" or .kind == "CronJob") | (.spec.template.spec // .spec.jobTemplate.spec.template.spec) | ((.containers // []) + (.initContainers // []))[] | select((.resources.limits.memory // "") == "") | .name' '[]'

if [[ "${failures}" -gt 0 ]]; then
  echo "${failures} chart contract(s) violated." >&2
  exit 1
fi
echo "Every chart contract holds."
