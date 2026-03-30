# Lightweight embedding service — ONNX Runtime only, no PyTorch
FROM python:3.14-slim

WORKDIR /app

RUN pip install --no-cache-dir --root-user-action=ignore \
    fastapi>=0.115.0 \
    "uvicorn[standard]>=0.32.0" \
    onnxruntime>=1.20.0 \
    transformers>=4.46.0 \
    numpy \
    sentencepiece \
    protobuf \
    huggingface-hub>=0.26.0

# Download pre-converted ONNX models at build time (no PyTorch needed)
# Optional: set HF_TOKEN for faster downloads (free account sufficient)
ARG HF_TOKEN=""
ENV HF_TOKEN=${HF_TOKEN}

# Multilingual model (German knowledge base) — only download the fp32 ONNX + tokenizer
RUN python -c "\
from huggingface_hub import snapshot_download; \
snapshot_download('Xenova/paraphrase-multilingual-MiniLM-L12-v2', \
    local_dir='/app/models/onnx/paraphrase-multilingual-MiniLM-L12-v2', \
    allow_patterns=['onnx/model.onnx', 'tokenizer*', 'special_tokens*', \
                    'sentencepiece*', 'config.json', 'tokenizer.json']); \
print('Multilingual model downloaded')"

# Move model.onnx from onnx/ subfolder to root (expected by main.py)
RUN mv /app/models/onnx/paraphrase-multilingual-MiniLM-L12-v2/onnx/model.onnx \
       /app/models/onnx/paraphrase-multilingual-MiniLM-L12-v2/model.onnx && \
    rm -rf /app/models/onnx/paraphrase-multilingual-MiniLM-L12-v2/onnx

# English fallback model (pre-converted, small)
RUN python -c "\
from huggingface_hub import snapshot_download; \
snapshot_download('optimum/all-MiniLM-L6-v2', \
    local_dir='/app/models/onnx/all-MiniLM-L6-v2'); \
print('English fallback model downloaded')"

COPY main.py .

EXPOSE 8080

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
