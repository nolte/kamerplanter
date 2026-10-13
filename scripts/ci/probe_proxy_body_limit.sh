#!/usr/bin/env bash
#
# #2144 (audit gap G-10) — probe the edge body limit in the production nginx.
#
#   scripts/ci/probe_proxy_body_limit.sh [chart-dir]
#
# Needs docker, helm (chart dependencies built) and mikefarah yq v4. Locally
# `task verify:proxy-body-limit`; in CI the skaffold-verify job runs it after
# the chart contracts.
#
# WHY A PROBE AND NOT ONLY A TEXT CHECK. Whether nginx refuses a body depends on
# where the directive sits (http/server/location) and on nginx's own unit
# arithmetic; a configuration that reads right can still answer differently.
# This script runs both configurations that reach users —
#
#   image  src/frontend/nginx.conf (+ its security-header include), baked into
#          the frontend image (docker compose, the E2E stack)
#   chart  the default.conf the chart renders into its ConfigMap, which the
#          chart mounts OVER /etc/nginx/conf.d in every Kubernetes release
#
# — in the nginx image the frontend Dockerfile pins, and sends each a POST to
# /api/v1/… of three sizes:
#
#   2 MiB                       must be forwarded (nginx's 1 MiB default refused it)
#   storage max + 64 KiB        the largest legitimate upload with multipart
#                               framing; must be forwarded
#   30 MiB                      must be refused by nginx with 413
#
# "Forwarded" is proven by a status nginx can only produce after it accepted
# the body: no backend runs behind the probe, so a forwarded request ends in
# 502 (the backend host resolves to the loopback, nothing listens). 413 for
# the first two, or anything but 413 for the third, fails the probe.
#
# Measured RED on develop 6f93331f2 (2026-10-09): both configurations answered
# 413 to 2 MiB and to the 25 MiB upload.
#
# NGINX_IMAGE overrides the image (e.g. a locally cached tag when the pinned
# digest cannot be pulled); the default is the prod stage of the Dockerfile.
set -euo pipefail

CHART="${1:-helm/kamerplanter}"
REPO="$(cd "$(dirname "$0")/../.." && pwd)"
CHART_VALUES="${CHART}/values.yaml"

image="${NGINX_IMAGE:-$(sed -n 's/^FROM \(nginxinc\/nginx-unprivileged[^ ]*\) AS prod$/\1/p' "${REPO}/src/frontend/Dockerfile")}"
if [[ -z "${image}" ]]; then
  echo "::error::no 'FROM nginxinc/nginx-unprivileged… AS prod' line in src/frontend/Dockerfile" >&2
  exit 1
fi

max_mb="$(yq e '.storage.maxFileSizeMb' "${CHART_VALUES}")"
if ! [[ "${max_mb}" =~ ^[0-9]+$ ]]; then
  echo "::error::storage.maxFileSizeMb in ${CHART_VALUES} is not a number: ${max_mb}" >&2
  exit 1
fi

work="$(mktemp -d)"
containers=()
cleanup() {
  for c in "${containers[@]}"; do docker rm -f "${c}" >/dev/null 2>&1 || true; done
  rm -rf "${work}"
}
trap cleanup EXIT

failures=0
fail() {
  echo "::error::$*" >&2
  failures=$((failures + 1))
}

# image configuration: the files the Dockerfile copies into /etc/nginx/conf.d
mkdir -p "${work}/image" "${work}/chart"
cp "${REPO}/src/frontend/nginx.conf" "${work}/image/default.conf"
cp "${REPO}/src/frontend/nginx-security-headers.inc" "${work}/image/"

# chart configuration: exactly what the ConfigMap mounts
helm template kamerplanter "${CHART}" |
  yq e 'select(.kind == "ConfigMap" and .metadata.name == "kamerplanter") | .data["default.conf"]' - \
    >"${work}/chart/default.conf"
if [[ ! -s "${work}/chart/default.conf" ]]; then
  echo "::error::the chart rendered no ConfigMap 'kamerplanter' with a default.conf" >&2
  exit 1
fi

# nginx-unprivileged runs as uid 101: the mounted directories must be readable
# by it on a rootful daemon (mktemp creates them 0700 for the caller).
chmod 0755 "${work}" "${work}/image" "${work}/chart"
chmod 0644 "${work}"/image/* "${work}"/chart/*

head -c $((2 * 1024 * 1024)) /dev/zero >"${work}/body-2mib"
head -c $((max_mb * 1024 * 1024 + 64 * 1024)) /dev/zero >"${work}/body-upload"
head -c $((30 * 1024 * 1024)) /dev/zero >"${work}/body-30mib"

# status <port> <body-file> — POST the body, print the status nginx answers.
status() {
  curl -sS -o /dev/null -w '%{http_code}' --max-time 30 -X POST \
    -H 'Content-Type: application/octet-stream' --data-binary @"$2" \
    "http://127.0.0.1:$1/api/v1/probe-body-limit" || true
}

port=18480
for config in image chart; do
  port=$((port + 1))
  name="kp-body-limit-probe-${config}-$$"
  # Both upstream names the two configurations proxy to resolve to the loopback,
  # where nothing listens: a forwarded request ends in 502.
  docker run -d --name "${name}" \
    --add-host backend:127.0.0.1 --add-host kamerplanter-backend:127.0.0.1 \
    -p "127.0.0.1:${port}:8080" -v "${work}/${config}:/etc/nginx/conf.d:ro" \
    "${image}" >/dev/null
  containers+=("${name}")

  ready=""
  for _ in $(seq 1 30); do
    if [[ "$(curl -s -o /dev/null -w '%{http_code}' --max-time 2 "http://127.0.0.1:${port}/" || true)" != "000" ]]; then
      ready=yes
      break
    fi
    sleep 1
  done
  if [[ -z "${ready}" ]]; then
    fail "${config}: nginx did not answer on :${port}: $(docker logs "${name}" 2>&1 | tail -5 | tr '\n' ' ')"
    continue
  fi

  got="$(status "${port}" "${work}/body-2mib")"
  [[ "${got}" == "502" ]] || fail "${config}: a 2 MiB body must be forwarded (502 without backend), got ${got}"
  got="$(status "${port}" "${work}/body-upload")"
  [[ "${got}" == "502" ]] ||
    fail "${config}: the largest upload (${max_mb} MiB + 64 KiB) must be forwarded (502 without backend), got ${got}"
  got="$(status "${port}" "${work}/body-30mib")"
  [[ "${got}" == "413" ]] || fail "${config}: a 30 MiB body must be refused by nginx with 413, got ${got}"
  echo "${config}: probed with ${image}"
done

if [[ "${failures}" -gt 0 ]]; then
  echo "${failures} body-limit probe(s) failed." >&2
  exit 1
fi
echo "Both nginx configurations forward the largest upload and refuse 30 MiB with 413."
