# Lightweight embedding service — no PyTorch, no optimum, just ONNX Runtime
FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir \
    fastapi>=0.115.0 \
    "uvicorn[standard]>=0.32.0" \
    onnxruntime>=1.20.0 \
    transformers>=4.46.0 \
    numpy \
    huggingface-hub>=0.26.0

# Download pre-converted ONNX model files at build time
RUN python -c "\
from huggingface_hub import snapshot_download; \
snapshot_download('optimum/all-MiniLM-L6-v2', local_dir='/app/models/onnx/all-MiniLM-L6-v2'); \
print('ONNX model downloaded')"

COPY main.py .

EXPOSE 8080

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
