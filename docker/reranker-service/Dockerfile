# Cross-encoder reranker service — ONNX Runtime only, no PyTorch
#
# Multi-stage build: each model downloads in a cached stage.
# Build the final image by targeting the desired model stage:
#
#   docker build --target bge-reranker-v2-m3 .   (multilingual, default)
#   docker build --target ms-marco-minilm .       (English-focused, lighter)
#
# See ADR-007 for rationale.

# ── Shared base for downloads ────────────────────────────────────────
FROM python:3.14-slim AS dl-base
# hadolint ignore=DL3013
RUN pip install --no-cache-dir --root-user-action=ignore huggingface-hub optimum[onnxruntime] sentencepiece

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

FROM python:3.14-slim AS runtime

LABEL org.opencontainers.image.title="kamerplanter-reranker-service" \
      org.opencontainers.image.description="ONNX-based cross-encoder reranker for Kamerplanter RAG" \
      org.opencontainers.image.source="https://github.com/nolte/kamerplanter" \
      org.opencontainers.image.vendor="Kamerplanter" \
      org.opencontainers.image.licenses="MIT"

WORKDIR /app
COPY requirements.txt .
# hadolint ignore=DL3013
RUN pip install --no-cache-dir --root-user-action=ignore -r requirements.txt
COPY main.py .
EXPOSE 8081
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8081"]

# ── Final images (one per model, select via --target) ────────────────

FROM runtime AS bge-reranker-v2-m3
ENV RERANKER_MODEL=bge-reranker-v2-m3
COPY --from=dl-bge-reranker-v2-m3 /model/ /app/models/onnx/bge-reranker-v2-m3/

FROM runtime AS ms-marco-minilm
ENV RERANKER_MODEL=ms-marco-MiniLM-L-12-v2
COPY --from=dl-ms-marco-minilm /model/ /app/models/onnx/ms-marco-MiniLM-L-12-v2/
