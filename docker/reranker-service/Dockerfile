# Cross-encoder reranker service — ONNX Runtime only, no PyTorch
#
# Multi-stage build: each model downloads in a cached stage.
# Build the final image by targeting the desired model stage:
#
#   docker build --target bge-reranker-v2-m3 .   (multilingual, default)
#   docker build --target ms-marco-minilm .       (English-focused, lighter)
#
# See ADR-007 for rationale.

# ── Shared uv layer: the toolchain and the environment settings ──────
# uv is the lock toolchain (NFR-009 §2.3), exactly as in src/backend/Dockerfile:
# one static binary, copied from its own digest-pinned image so Renovate's
# dockerfile manager ages it together with `[tool.uv].required-version`. The
# environment pins uv to the interpreter this image ships (no managed-Python
# download, no cache layer) and puts the project environment on PATH, so the
# stages below resolve `python` and `uvicorn` without an activation step. It
# lives in /opt/venv, OUTSIDE /app, because the runtime stage chowns /app to
# UID 1000 and a venv inside it would end up writable by the server's UID.
FROM python:3.14-slim@sha256:cad9a2c871761c413caa6fdd6441c783451e740a48aaeba60ae62a8b53525ef6 AS uv-base
COPY --from=ghcr.io/astral-sh/uv:0.12.15@sha256:62f8c047d0a0e9ece6b53fc63df902585a67a47a7f318ddec4a37db586edc8e3 /uv /bin/uv
ENV UV_PYTHON=/usr/local/bin/python3 \
    UV_PYTHON_DOWNLOADS=never \
    UV_NO_CACHE=1 \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

# ── Shared base for downloads ────────────────────────────────────────

FROM uv-base AS dl-base
WORKDIR /src
COPY pyproject.toml uv.lock ./
# The download toolchain comes from the same lock as the runtime, through the
# `build` dependency group: `--only-group` installs that group alone, `--locked`
# verifies every artifact against its recorded hash.
RUN uv sync --locked --only-group build

# ── Download stages (cached independently) ───────────────────────────

FROM dl-base AS dl-bge-reranker-v2-m3
# BAAI/bge-reranker-v2-m3 — multilingual, 568M params, Apache-2.0
# Export to ONNX via optimum
RUN python -c "\
from optimum.onnxruntime import ORTModelForSequenceClassification; \
model = ORTModelForSequenceClassification.from_pretrained('BAAI/bge-reranker-v2-m3', export=True); \
model.save_pretrained('/model')" && \
    rm -rf /root/.cache

FROM dl-base AS dl-ms-marco-minilm
# cross-encoder/ms-marco-MiniLM-L-12-v2 — English-focused, 33M params, Apache-2.0
RUN python -c "\
from optimum.onnxruntime import ORTModelForSequenceClassification; \
model = ORTModelForSequenceClassification.from_pretrained('cross-encoder/ms-marco-MiniLM-L-12-v2', export=True); \
model.save_pretrained('/model')" && \
    rm -rf /root/.cache

# ── Runtime base (shared across all final targets) ───────────────────

FROM uv-base AS runtime

LABEL org.opencontainers.image.title="kamerplanter-reranker-service" \
      org.opencontainers.image.description="ONNX cross-encoder reranker (BGE reranker v2 m3) that re-scores RAG retrieval hits for Kamerplanter" \
      org.opencontainers.image.source="https://github.com/nolte/kamerplanter" \
      org.opencontainers.image.vendor="Kamerplanter" \
      org.opencontainers.image.licenses="MIT"

WORKDIR /app
# The lock is the single source of truth for what gets installed (NFR-009
# §2.3/§6.1); `--no-dev` leaves the export toolchain (optimum, torch) out of the
# shipped image — the runtime needs onnxruntime only.
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev
COPY main.py .
# Create the non-root numeric user; each final target COPYs its model with
# --chown=1000 and switches to USER 1000 as its last instruction.
RUN groupadd -g 1000 app && useradd -u 1000 -g 1000 -d /app -s /usr/sbin/nologin app \
    && chown -R 1000:1000 /app
EXPOSE 8081
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD ["python", "-c", "import socket,sys; s=socket.socket(); s.settimeout(3); sys.exit(s.connect_ex(('127.0.0.1',8081)))"]
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8081"]

# ── Final images (one per model, select via --target) ────────────────

FROM runtime AS bge-reranker-v2-m3
ENV RERANKER_MODEL=bge-reranker-v2-m3
COPY --from=dl-bge-reranker-v2-m3 --chown=1000:1000 /model/ /app/models/onnx/bge-reranker-v2-m3/
USER 1000

FROM runtime AS ms-marco-minilm
ENV RERANKER_MODEL=ms-marco-MiniLM-L-12-v2
COPY --from=dl-ms-marco-minilm --chown=1000:1000 /model/ /app/models/onnx/ms-marco-MiniLM-L-12-v2/
USER 1000
