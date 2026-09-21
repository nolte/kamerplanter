#!/usr/bin/env bash
#
# Prove that an image which ships a build-time-exported model can actually
# SERVE it: start the container and require its readiness signal.
#
#   scripts/ci/smoke_model_image.sh <image> <port> <path> [required-substring]
#
# #1609 — the defect this exists against, measured 2026-09-20.
#
# `docker/reranker-service` built green for weeks and could never become ready.
# The ONNX export stage wrote `config.json`, `model.onnx` and `model.onnx_data`
# and no tokenizer at all, so `AutoTokenizer.from_pretrained()` died at startup
# — inside a DAEMON THREAD, which is why the process stayed up. `/health` kept
# answering 200, the image's TCP `HEALTHCHECK` kept passing because uvicorn was
# listening, and `/ready` was a permanent 503. Nothing in the pre-merge lane
# noticed, because `docker-lint-build.yml` builds the image and stops there: a
# build is not a start.
#
# So the signal this script requires is the READINESS one, never `docker ps`'s
# health column and never a successful build. Two of the three images in this
# class serve `/ready`, which is 503 until the model is loaded; the inference
# service's `/ready` additionally requires a database it does not have here, so
# it is smoke-tested on `/health` WITH a body assertion on `model_loaded` —
# hence the optional fourth argument. A plain 200 on `/health` would reproduce
# exactly the lie this file exists to end.
#
# On failure the container's logs are dumped, because the preload traceback is
# the only place the real cause appears.
#
# Known to be able to fail, measured 2026-09-21 against stub containers that
# answer 200, answer 503 forever, answer 200 with the wrong body, and publish no
# port: exit 0, 1, 1, 1 respectively, with the container logs dumped on each red.
# An assertion that has only ever seen its passing input is not known to be able
# to fail (NFR-018 §2). The structural half — that every model-shipping image is
# actually wired to this script — is asserted by
# src/backend/tests/unit/guards/test_model_images_prove_readiness.py.

set -euo pipefail

IMAGE="${1:?usage: smoke_model_image.sh <image> <port> <path> [required-substring]}"
PORT="${2:?missing container port}"
READY_PATH="${3:?missing readiness path}"
REQUIRED="${4:-}"

# Generous by design: the reranker loads a 2.3 GB ONNX graph on a cold page
# cache. Overridable so the guard's falsification run does not wait minutes for
# a container that is never going to become ready.
TIMEOUT_SECONDS="${SMOKE_TIMEOUT_SECONDS:-300}"
POLL_SECONDS="${SMOKE_POLL_SECONDS:-3}"

CONTAINER=""
cleanup() {
  if [ -n "$CONTAINER" ]; then
    docker rm -f "$CONTAINER" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

# Let the kernel pick the host port: several of these may run side by side.
CONTAINER="$(docker run -d -P "$IMAGE")"
# `|| true`: an unpublished port must reach the diagnostic below rather than
# abort the script under `set -e` with docker's own terser message.
HOST_PORT="$(docker port "$CONTAINER" "$PORT/tcp" 2>/dev/null | head -1 | sed 's/.*://' || true)"
if [ -z "$HOST_PORT" ]; then
  echo "FAIL: $IMAGE does not publish container port $PORT" >&2
  docker logs "$CONTAINER" >&2 || true
  exit 1
fi

URL="http://127.0.0.1:${HOST_PORT}${READY_PATH}"
echo "smoke: $IMAGE -> $URL (timeout ${TIMEOUT_SECONDS}s)"

deadline=$(( $(date +%s) + TIMEOUT_SECONDS ))
last_status="(never answered)"
last_body=""
while [ "$(date +%s)" -lt "$deadline" ]; do
  # `|| true`: a not-yet-listening socket must keep the loop alive, not abort it
  # under `set -e`.
  body="$(curl -sS -m 10 -o - -w '\n%{http_code}' "$URL" 2>/dev/null || true)"
  last_status="${body##*$'\n'}"
  last_body="${body%$'\n'*}"
  if [ "$last_status" = "200" ]; then
    if [ -z "$REQUIRED" ] || printf '%s' "$last_body" | grep -qF -- "$REQUIRED"; then
      echo "smoke: READY — $last_body"
      exit 0
    fi
  fi
  sleep "$POLL_SECONDS"
done

echo "FAIL: $URL never became ready within ${TIMEOUT_SECONDS}s" >&2
echo "       last status: $last_status" >&2
echo "       last body:   $last_body" >&2
if [ -n "$REQUIRED" ]; then
  echo "       required in body: $REQUIRED" >&2
fi
echo "--- container logs ---" >&2
docker logs "$CONTAINER" >&2 || true
exit 1
