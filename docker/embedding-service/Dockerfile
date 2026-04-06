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

FROM python:3.14-slim AS dl-base
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

FROM python:3.14-slim AS runtime

LABEL org.opencontainers.image.title="kamerplanter-embedding-service" \
      org.opencontainers.image.description="ONNX-based multilingual embedding service for Kamerplanter RAG" \
      org.opencontainers.image.source="https://github.com/nolte/kamerplanter" \
      org.opencontainers.image.vendor="Kamerplanter" \
      org.opencontainers.image.licenses="MIT"

WORKDIR /app
COPY requirements.txt .
# hadolint ignore=DL3013
RUN pip install --no-cache-dir --root-user-action=ignore -r requirements.txt
COPY main.py .
EXPOSE 8080
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]

# ── Final images (one per model, select via --target) ────────────────

FROM runtime AS e5-small
ENV EMBEDDING_MODEL=multilingual-e5-small
COPY --from=dl-e5-small /model/ /app/models/onnx/multilingual-e5-small/

FROM runtime AS e5-base
ENV EMBEDDING_MODEL=multilingual-e5-base
COPY --from=dl-e5-base /model/ /app/models/onnx/multilingual-e5-base/

FROM runtime AS e5-large
ENV EMBEDDING_MODEL=multilingual-e5-large
COPY --from=dl-e5-large /model/ /app/models/onnx/multilingual-e5-large/

FROM runtime AS minilm
ENV EMBEDDING_MODEL=paraphrase-multilingual-MiniLM-L12-v2
COPY --from=dl-minilm /model/ /app/models/onnx/paraphrase-multilingual-MiniLM-L12-v2/
