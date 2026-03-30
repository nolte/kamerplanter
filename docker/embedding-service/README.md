# Embedding Service

Lightweight embedding microservice for the Kamerplanter Knowledge API (REQ-021). Produces vector embeddings from text using ONNX Runtime — no PyTorch dependency required.

## Models

Two sentence-transformer models are downloaded at build time:

| Model | Purpose | Dimensions |
|-------|---------|------------|
| `paraphrase-multilingual-MiniLM-L12-v2` | Primary — German knowledge base | 384 |
| `all-MiniLM-L6-v2` | English fallback | 384 |

## API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/embed` | POST | Generate embeddings for a list of texts |
| `/health` | GET | Health check (returns `loading` until model is ready) |
| `/ready` | GET | Readiness probe (503 while loading) |

### POST /embed

```json
{
  "texts": ["Tomaten brauchen viel Sonne"],
  "model": "paraphrase-multilingual-MiniLM-L12-v2"
}
```

## Configuration

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `EMBEDDING_MODEL` | `paraphrase-multilingual-MiniLM-L12-v2` | Model to load at startup |
| `HF_TOKEN` | _(empty)_ | Optional Hugging Face token for faster downloads |

## Stack

- Python 3.14, FastAPI, Uvicorn
- ONNX Runtime (CPU)
- HuggingFace Transformers (tokenizer only)

## Build & Run

```bash
docker build -t kamerplanter-embedding-service .
docker run -p 8080:8080 kamerplanter-embedding-service
```

> **Note:** In production this image is built and deployed via Skaffold/Helm, not manually.
