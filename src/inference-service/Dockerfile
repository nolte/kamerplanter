# Inference Service -- ONNX Runtime only, no PyTorch in the runtime image.
#
# Multi-target: a shared "model-export" stage produces the DINOv2 ONNX artifact
# (torch only there). A shared "base" runtime carries onnxruntime + model + app.
# dev and prod both build on base — one Dockerfile, no separate Dockerfile.dev.
#   prod (default, built by CI):   docker build .
#   dev  (built by skaffold):      docker build --target dev .
#
# "built by CI" means BEFORE the merge since #1463: `build-inference-service` in
# docker-lint-build.yml builds this file with the same context and no `target:`
# as the publishing job in docker-publish.yml. Until then only the post-merge
# publish built it, so a pull request could make this unbuildable and every check
# stayed green — the breakage surfaced on develop, on somebody else's change.
#
# Every Python install below comes from uv.lock with hash verification
# (NFR-009 §2.3/§6.1) — the export toolchain through the `build` dependency
# group, the reloader through `dev`, the runtime through [project].dependencies.
#
# LICENCE: the DINOv2 base backbone is Apache-2.0 (re-verify before release,
# REQ-029-A 2.3 / 5). Never ship PlantCLEF fine-tuned weights (CC-BY-NC).

# -- Shared uv layer: the toolchain and the environment settings --------------
# uv is one static binary, copied from its own digest-pinned image so Renovate's
# dockerfile manager ages it exactly like the base image. The environment pins
# uv to the interpreter this image ships (no managed-Python download, no cache
# layer) and puts the project environment on PATH, so the stages below resolve
# `python` and `uvicorn` without an activation step. It lives in /opt/venv,
# OUTSIDE the working directory, because the stages below chown that directory
# to UID 1000 and a venv inside it would end up writable by the server's UID.
FROM python:3.14-slim@sha256:caaf356f40667c496d405780745b9ac25771c189a51dfcc42430d531ea09f8a2 AS uv-base
COPY --from=ghcr.io/astral-sh/uv:0.12.19@sha256:04d046b13e60d6bcec73cbc5e1cad25d680dea90c8573340950a0ac2d1aef424 /uv /bin/uv
ENV UV_PYTHON=/usr/local/bin/python3 \
    UV_PYTHON_DOWNLOADS=never \
    UV_NO_CACHE=1 \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

# -- Export stage: produce model.onnx + modelinfo.json (torch only here) -----
FROM uv-base AS model-export

WORKDIR /export
COPY pyproject.toml uv.lock ./
# CPU-only torch: the GPU build pulls multi-GB nvidia/CUDA wheels that are
# unnecessary for a CPU ONNX export and exhaust the CI runner disk. The CPU
# index is declared per-package in pyproject.toml ([tool.uv.sources]), so the
# rest of the group still resolves from PyPI. `--only-group build` installs the
# export toolchain alone — none of the runtime dependencies and not the project.
RUN uv sync --locked --only-group build --no-install-project

COPY scripts/export_dinov2_onnx.py ./export_dinov2_onnx.py
RUN python export_dinov2_onnx.py --arch dinov2_vits14 --input-size 224 --output /model

# -- Shared runtime base (onnxruntime + exported model + app code) -----------
FROM uv-base AS base

LABEL org.opencontainers.image.title="kamerplanter-inference-service" \
      org.opencontainers.image.description="Plant/pest image-recognition service (DINOv2 ONNX embeddings + pgvector matching) for Kamerplanter health assessment" \
      org.opencontainers.image.source="https://github.com/nolte/kamerplanter" \
      org.opencontainers.image.vendor="Kamerplanter" \
      org.opencontainers.image.licenses="MIT"

WORKDIR /app

# The lock is the single source of truth for what gets installed: `--locked`
# verifies it against pyproject.toml and every artifact against its recorded
# hash, so a stale lock or a tampered wheel fails the build instead of
# installing something else. Copied before the source so the install layer is
# cached independently of application code. The REQ-038 PlantCV extra stays out
# of the image on purpose (see [project.optional-dependencies] in
# pyproject.toml); the service degrades gracefully without it.
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev --no-install-project

COPY --from=model-export /model/ /app/models/dinov2/
COPY app/ ./app/

ENV MODEL_PATH=/app/models/dinov2

# -- Development target: hot-reload (skaffold dev syncs app/**/*.py) ----------
FROM base AS dev
# The `dev` dependency group adds watchfiles (the reload watcher) from the same
# lock — it used to be an unpinned `pip install` outside any lock. Own /app as
# UID 1000 for the non-root dev pod (hot-reload + skaffold sync).
RUN uv sync --locked --no-install-project \
 && chown -R 1000:1000 /app
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# -- Production target (default; last stage) ---------------------------------
FROM base AS prod
# Run as a non-root numeric user.
RUN groupadd -g 1000 app && useradd -u 1000 -g 1000 -d /app -s /usr/sbin/nologin app \
    && chown -R 1000:1000 /app
USER 1000
EXPOSE 8000
# THE HEALTHCHECK ASSERTS READINESS, NOT A SOCKET (#1609).
#
# It used to open a TCP connection to the uvicorn port, which succeeds the
# instant the server binds — long before, and quite independently of, the model
# loading. That is how an image that could never serve a request reported
# healthy for weeks. Docker has no liveness/readiness split: this is the only
# signal `docker ps`, `docker-compose --wait` and `depends_on:
# condition: service_healthy` have, so it must assert the thing that
# distinguishes a usable service from an open port.
#
# `--start-period` is generous because the model load is: a failing probe inside
# it does not count against `--retries`. Kubernetes ignores this instruction
# entirely and uses the chart's probes (helm/kamerplanter/values.yaml, the
# `inference-service` controller), which point at `/ready` for the deployed
# case, where the database is there.
#
# This service is probed on `/health` rather than `/ready`, because its
# `/ready` also requires the pgvector database and would report the DB's
# absence as this container's fault. `/health` answers 200 whatever the model
# did — which is the #1609 lie exactly — so the body is what is asserted:
# `model_loaded` must be true. The smoke step in docker-lint-build.yml
# requires the same fact.
HEALTHCHECK --interval=30s --timeout=10s --start-period=180s --retries=3 \
    CMD ["python", "-c", "import json,sys,urllib.request; sys.exit(0 if json.load(urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=8)).get('model_loaded') else 1)"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
