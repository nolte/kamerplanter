#!/usr/bin/env bash
#
# Prove that an image which ships a build-time-exported model can actually
# SERVE it: start the container and require its readiness signal.
#
#   scripts/ci/smoke_model_image.sh <image> <port> <path> [required-substring]
#   scripts/ci/smoke_model_image.sh <image> model <model-dir> <dim> <input-size>
#
# The first form starts the container and requires its readiness endpoint. The
# second loads the shipped ONNX graph inside the image and runs one inference
# through it — for a service whose readiness legitimately depends on something
# that is not standing here (see below).
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
# class serve `/ready`, which is 503 until the model is loaded, and those are
# started and probed.
#
# The inference service is the exception, and it was MEASURED rather than
# assumed: its lifespan (`src/inference-service/app/main.py`) connects to
# pgvector and runs migrations BEFORE `Embedder.start_load()`, so a lone
# container never serves anything at all — requiring `/ready` there would assert
# the absence of a database, not the presence of a model. Its `model` mode loads
# the shipped graph inside the image instead, which is what this class is about.
# The optional fourth argument of the HTTP form requires a fact in the body, for
# an endpoint whose 200 alone would reproduce exactly the lie this file exists
# to end.
#
# On failure the container's logs are dumped, because the preload traceback is
# the only place the real cause appears.
#
# Known to be able to fail, measured 2026-09-21 against stub containers that
# answer 200, answer 503 forever, answer 200 with the wrong body, and publish no
# port: exit 0, 1, 1, 1 respectively, with the container logs dumped on each red.
# Those runs predate the hardened `docker run` flags of the HTTP form (#1725)
# and were NOT repeated with them; a stub that needs a writable root
# filesystem or root now fails to start, which is a red for a different reason.
# An assertion that has only ever seen its passing input is not known to be able
# to fail (NFR-018 §2). The structural half — that every model-shipping image is
# actually wired to this script — is asserted by
# src/backend/tests/unit/guards/test_model_images_prove_readiness.py.

set -euo pipefail

IMAGE="${1:?usage: smoke_model_image.sh <image> <port|model> ...}"
PORT="${2:?missing container port, or the literal \`model\`}"

# ── `model` mode: load the shipped graph inside the image ────────────
if [ "$PORT" = "model" ]; then
  MODEL_DIR="${3:?missing model directory}"
  EXPECTED_DIM="${4:?missing expected embedding dimension}"
  INPUT_SIZE="${5:?missing model input size}"
  VERIFIER="$(cd "$(dirname "$0")" && pwd)/verify_onnx_model.py"
  echo "smoke: $IMAGE -> loading $MODEL_DIR (expecting dimension $EXPECTED_DIM)"
  # `--entrypoint python` overrides the server CMD; the verifier is mounted
  # read-only rather than baked in, so the shipped image stays unchanged.
  if docker run --rm -v "$VERIFIER:/verify_onnx_model.py:ro" --entrypoint python \
      "$IMAGE" /verify_onnx_model.py "$MODEL_DIR" "$EXPECTED_DIM" "$INPUT_SIZE"; then
    exit 0
  fi
  echo "FAIL: $IMAGE ships a model it cannot load" >&2
  exit 1
fi

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
#
# STARTED THE WAY THE CHART RUNS IT (#1725): read-only root filesystem, a
# small tmpfs for /tmp (the chart's memory-backed emptyDir), no capabilities,
# no privilege escalation, and the image's non-root UID. An image that only
# becomes ready while it can write to its own filesystem — a library caching
# into $HOME, bytecode written next to the code — would pass a plain
# `docker run` here and then crash-loop in the cluster; this makes CI see what
# the cluster sees. Both HTTP-form users (the embedding and reranker images)
# ship `USER 1000` and root-owned files, so `--user 1000:1000` changes nothing
# for them but states the expectation. The `model` form above is unchanged: it
# runs a one-off verifier, not the server.
CONTAINER="$(docker run -d -P \
  --read-only \
  --tmpfs /tmp:rw,noexec,nosuid,size=64m \
  --cap-drop ALL \
  --security-opt no-new-privileges \
  --user 1000:1000 \
  "$IMAGE")"
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
