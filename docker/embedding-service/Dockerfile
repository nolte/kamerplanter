# Lightweight embedding service — ONNX Runtime only, no PyTorch
#
# Multi-stage build: each model downloads in a cached stage.
# Build the final image by targeting the desired model stage:
#
#   docker build --target e5-base .    (768 dim, default)
#   docker build --target e5-small .   (384 dim, fast)
#   docker build --target e5-large .   (1024 dim, best quality)
#   docker build --target minilm .     (384 dim, baseline)
#
# See ADR-006 for rationale.

# ── Shared uv layer: the toolchain and the environment settings ──────
# uv is the lock toolchain (NFR-009 §2.3), exactly as in src/backend/Dockerfile:
# one static binary, copied from its own digest-pinned image so Renovate's
# dockerfile manager ages it together with `[tool.uv].required-version`. The
# environment pins uv to the interpreter this image ships (no managed-Python
# download, no cache layer) and puts the project environment on PATH, so the
# stages below resolve `python` and `uvicorn` without an activation step. It
# lives in /opt/venv, OUTSIDE /app, because the runtime stage chowns /app to
# UID 1000 and a venv inside it would end up writable by the server's UID.
FROM python:3.14-slim@sha256:caaf356f40667c496d405780745b9ac25771c189a51dfcc42430d531ea09f8a2 AS uv-base
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

FROM dl-base AS dl-e5-small
# intfloat/multilingual-e5-small — 384 dim, 118M params, MIT
RUN python -c "\
from huggingface_hub import snapshot_download; \
snapshot_download('intfloat/multilingual-e5-small', \
    local_dir='/model', \
    allow_patterns=['onnx/model.onnx', 'tokenizer*', 'special_tokens*', \
                    'sentencepiece*', 'config.json'])" && \
    mv /model/onnx/model.onnx /model/model.onnx && \
    rm -rf /model/onnx /model/.cache

FROM dl-base AS dl-e5-base
# intfloat/multilingual-e5-base — 768 dim, 278M params, MIT
RUN python -c "\
from huggingface_hub import snapshot_download; \
snapshot_download('intfloat/multilingual-e5-base', \
    local_dir='/model', \
    allow_patterns=['onnx/model.onnx', 'tokenizer*', 'special_tokens*', \
                    'sentencepiece*', 'config.json'])" && \
    mv /model/onnx/model.onnx /model/model.onnx && \
    rm -rf /model/onnx /model/.cache

FROM dl-base AS dl-e5-large
# intfloat/multilingual-e5-large — 1024 dim, 560M params, MIT
RUN python -c "\
from huggingface_hub import snapshot_download; \
snapshot_download('intfloat/multilingual-e5-large', \
    local_dir='/model', \
    allow_patterns=['onnx/model.onnx', 'onnx/model.onnx_data', 'tokenizer*', 'special_tokens*', \
                    'sentencepiece*', 'config.json'])" && \
    mv /model/onnx/model.onnx /model/model.onnx && \
    (mv /model/onnx/model.onnx_data /model/model.onnx_data 2>/dev/null || true) && \
    rm -rf /model/onnx /model/.cache

FROM dl-base AS dl-minilm
# Xenova/paraphrase-multilingual-MiniLM-L12-v2 — 384 dim, 118M params, Apache-2.0
RUN python -c "\
from huggingface_hub import snapshot_download; \
snapshot_download('Xenova/paraphrase-multilingual-MiniLM-L12-v2', \
    local_dir='/model', \
    allow_patterns=['onnx/model.onnx', 'tokenizer*', 'special_tokens*', \
                    'sentencepiece*', 'config.json'])" && \
    mv /model/onnx/model.onnx /model/model.onnx && \
    rm -rf /model/onnx /model/.cache

# ── Runtime base (shared across all final targets) ───────────────────

FROM uv-base AS runtime

LABEL org.opencontainers.image.title="kamerplanter-embedding-service" \
      org.opencontainers.image.description="ONNX multilingual text-embedding service turning knowledge and queries into vectors for Kamerplanter's RAG pipeline" \
      org.opencontainers.image.source="https://github.com/nolte/kamerplanter" \
      org.opencontainers.image.vendor="Kamerplanter" \
      org.opencontainers.image.licenses="MIT"

WORKDIR /app
# The lock is the single source of truth for what gets installed (NFR-009
# §2.3/§6.1); `--no-dev` leaves the download toolchain out of the shipped image.
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev
COPY main.py .
# Create the non-root numeric user; each final target COPYs its model with
# --chown=1000 and switches to USER 1000 as its last instruction.
RUN groupadd -g 1000 app && useradd -u 1000 -g 1000 -d /app -s /usr/sbin/nologin app \
    && chown -R 1000:1000 /app
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD ["python", "-c", "import socket,sys; s=socket.socket(); s.settimeout(3); sys.exit(s.connect_ex(('127.0.0.1',8080)))"]
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]

# ── Final images (one per model, select via --target) ────────────────

FROM runtime AS e5-small
ENV EMBEDDING_MODEL=multilingual-e5-small
COPY --from=dl-e5-small --chown=1000:1000 /model/ /app/models/onnx/multilingual-e5-small/
USER 1000

FROM runtime AS e5-base
ENV EMBEDDING_MODEL=multilingual-e5-base
COPY --from=dl-e5-base --chown=1000:1000 /model/ /app/models/onnx/multilingual-e5-base/
USER 1000

FROM runtime AS e5-large
ENV EMBEDDING_MODEL=multilingual-e5-large
COPY --from=dl-e5-large --chown=1000:1000 /model/ /app/models/onnx/multilingual-e5-large/
USER 1000

FROM runtime AS minilm
ENV EMBEDDING_MODEL=paraphrase-multilingual-MiniLM-L12-v2
COPY --from=dl-minilm --chown=1000:1000 /model/ /app/models/onnx/paraphrase-multilingual-MiniLM-L12-v2/
USER 1000
