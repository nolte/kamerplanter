# Inference Service -- ONNX Runtime only, no PyTorch in the runtime image.
#
# Multi-target: a shared "model-export" stage produces the DINOv2 ONNX artifact
# (torch only there). A shared "base" runtime carries onnxruntime + model + app.
# dev and prod both build on base — one Dockerfile, no separate Dockerfile.dev.
#   prod (default, built by CI):   docker build .
#   dev  (built by skaffold):      docker build --target dev .
#
# LICENCE: the DINOv2 base backbone is Apache-2.0 (re-verify before release,
# REQ-029-A 2.3 / 5). Never ship PlantCLEF fine-tuned weights (CC-BY-NC).

# -- Export stage: produce model.onnx + modelinfo.json (torch only here) -----
FROM python:3.14-slim AS model-export

WORKDIR /export
# CPU-only torch: the GPU build pulls multi-GB nvidia/CUDA wheels that are
# unnecessary for a CPU ONNX export and exhaust the CI runner disk. onnx is not
# hosted on the PyTorch index, so install it separately from PyPI.
# hadolint ignore=DL3013
RUN pip install --no-cache-dir --root-user-action=ignore \
        torch torchvision --index-url https://download.pytorch.org/whl/cpu \
 && pip install --no-cache-dir --root-user-action=ignore onnx onnxscript

COPY scripts/export_dinov2_onnx.py ./export_dinov2_onnx.py
RUN python export_dinov2_onnx.py --arch dinov2_vits14 --input-size 224 --output /model

# -- Shared runtime base (onnxruntime + exported model + app code) -----------
FROM python:3.14-slim AS base

LABEL org.opencontainers.image.title="kamerplanter-inference-service" \
      org.opencontainers.image.description="DINOv2 embedding + pgvector species matching for Kamerplanter" \
      org.opencontainers.image.source="https://github.com/nolte/kamerplanter" \
      org.opencontainers.image.vendor="Kamerplanter" \
      org.opencontainers.image.licenses="MIT"

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --root-user-action=ignore -r requirements.txt

COPY --from=model-export /model/ /app/models/dinov2/
COPY app/ ./app/

ENV MODEL_PATH=/app/models/dinov2

# -- Development target: hot-reload (skaffold dev syncs app/**/*.py) ----------
FROM base AS dev
# Own /app as UID 1000 for the non-root dev pod (hot-reload + skaffold sync).
# hadolint ignore=DL3013
RUN pip install --no-cache-dir --root-user-action=ignore watchfiles \
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
HEALTHCHECK --interval=30s --timeout=5s --start-period=45s --retries=3 \
    CMD python -c "import socket,sys; s=socket.socket(); s.settimeout(3); sys.exit(s.connect_ex(('127.0.0.1',8000)))"
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
