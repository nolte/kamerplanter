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

if [[ "${failures}" -gt 0 ]]; then
  echo "${failures} chart contract(s) violated." >&2
  exit 1
fi
echo "Every chart contract holds."
