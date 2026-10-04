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

if [[ "${failures}" -gt 0 ]]; then
  echo "${failures} chart contract(s) violated." >&2
  exit 1
fi
echo "Every chart contract holds."
