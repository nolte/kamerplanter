# Embedding Service

Lightweight embedding microservice for the Kamerplanter Knowledge API. Produces vector embeddings from text using ONNX Runtime — no PyTorch dependency required.

## Models

Multiple sentence-transformer models are available as build targets (see ADR-006):

| Model | Purpose | Dimensions | Build Target |
|-------|---------|------------|--------------|
| `multilingual-e5-base` | **Primary** — German knowledge base, hybrid search | 768 | `e5-base` (default) |
| `multilingual-e5-small` | Fallback — resource-constrained environments | 384 | `e5-small` |
| `multilingual-e5-large` | High-quality — maximum retrieval accuracy | 1024 | `e5-large` |
| `paraphrase-multilingual-MiniLM-L12-v2` | Legacy baseline | 384 | `minilm` |

### E5 Prefix Convention

E5 models use asymmetric encoding — queries and documents require different prefixes:

- **Queries:** `"query: " + text`
- **Documents/Passages:** `"passage: " + text`

Pass the prefix via the `prefix` field in the `/embed` request.

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
  "model": "multilingual-e5-base",
  "prefix": "query: "
}
```

## Configuration

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `EMBEDDING_MODEL` | `multilingual-e5-base` | Model to load at startup |
| `HF_TOKEN` | _(empty)_ | Optional Hugging Face token for faster downloads |

## Stack

- Python 3.14, FastAPI, Uvicorn
- ONNX Runtime (CPU)
- HuggingFace Transformers (tokenizer only)

## Build & Run

```bash
# Default (e5-base, 768 dim):
docker build -t kamerplanter-embedding-service .

# Specific target (e5-small, 384 dim):
docker build --target e5-small -t kamerplanter-embedding-service .

docker run -p 8080:8080 kamerplanter-embedding-service
```

> **Note:** In production this image is built and deployed via Skaffold/Helm, not manually.
