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

# ── Shared base for downloads ────────────────────────────────────────

FROM python:3.14-slim@sha256:ce40764625a4ff50df3548277632e7f96c4e77fe75fa848aae9885476e7df5a4 AS dl-base
# hadolint ignore=DL3013
RUN pip install --no-cache-dir --root-user-action=ignore huggingface-hub sentencepiece

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

FROM python:3.14-slim@sha256:ce40764625a4ff50df3548277632e7f96c4e77fe75fa848aae9885476e7df5a4 AS runtime

LABEL org.opencontainers.image.title="kamerplanter-embedding-service" \
      org.opencontainers.image.description="ONNX multilingual text-embedding service turning knowledge and queries into vectors for Kamerplanter's RAG pipeline" \
      org.opencontainers.image.source="https://github.com/nolte/kamerplanter" \
      org.opencontainers.image.vendor="Kamerplanter" \
      org.opencontainers.image.licenses="MIT"

WORKDIR /app
COPY requirements.txt .
# hadolint ignore=DL3013
RUN pip install --no-cache-dir --root-user-action=ignore -r requirements.txt
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
