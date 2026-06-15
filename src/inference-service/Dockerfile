# Inference Service -- ONNX Runtime only, no PyTorch in the runtime image.
#
# Multi-stage: an "export" stage produces the DINOv2 ONNX artifact (torch is
# only needed there, never at runtime). The runtime stage is a slim Python
# image with onnxruntime that copies in the exported model + app code.
#
# Build:
#   docker build -t kamerplanter-inference-service .
#
# LICENCE: the DINOv2 base backbone is Apache-2.0 (re-verify before release,
# REQ-029-A 2.3 / 5). Never ship PlantCLEF fine-tuned weights (CC-BY-NC).

# -- Export stage: produce model.onnx + modelinfo.json (torch only here) -----
FROM python:3.14-slim AS model-export

WORKDIR /export
# hadolint ignore=DL3013
RUN pip install --no-cache-dir --root-user-action=ignore torch torchvision onnx

COPY scripts/export_dinov2_onnx.py ./export_dinov2_onnx.py
RUN python export_dinov2_onnx.py --arch dinov2_vits14 --input-size 224 --output /model

# -- Runtime stage -----------------------------------------------------------
FROM python:3.14-slim AS runtime

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

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
