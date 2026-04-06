# ADR-006: Embedding Model multilingual-e5-base and Hybrid Search for RAG

**Status:** Accepted
**Date:** 2026-03-30
**Deciders:** Kamerplanter Development Team

## Context

The Kamerplanter AI assistant (REQ-031) uses a RAG pipeline (Retrieval-Augmented Generation) to answer plant care questions from a curated knowledge base. The pipeline consists of:

1. **Embedding Service** (ONNX Runtime) — generates vectors from text
2. **pgvector** (PostgreSQL) — stores and searches vectors via cosine similarity
3. **LLM** (Ollama/Claude) — generates answers from retrieved context chunks

### Problem: Retrieval quality was unusable

During RAG smoke testing with the previous embedding model `paraphrase-multilingual-MiniLM-L12-v2` (384 dimensions), vector search for the question *"My lower leaves are turning yellow, the upper ones are still green. What's missing?"* returned:

| Rank | Chunk | Score |
|------|-------|-------|
| 1 | Pre-harvest safety interval | 0.7909 |
| 2 | Topping and FIM — forcing branching | 0.7867 |
| 3 | Seed pre-treatment — stratification | 0.7380 |
| 4 | Flowering in vegetables and fruit | 0.7346 |
| 5 | Gray mold (Botrytis) detection | 0.7345 |

The correct chunk *"Nitrogen (N) Deficiency"* — which exactly describes these symptoms — was completely absent from the top 5. All scores fell between 0.73 and 0.79 with virtually no differentiation. The LLM received irrelevant context and hallucinated a wrong diagnosis (potassium instead of nitrogen).

### Root cause

`paraphrase-multilingual-MiniLM-L12-v2` is a small model (118M parameters, 384 dimensions) optimized for general paraphrase detection. It encodes all German plant care texts into too narrow a region of the vector space — cosine similarity between completely different chunks ranges from 0.73 to 0.88. The vector space is too low-dimensional to capture domain-specific nuances.

## Decision

### 1. Switch to `multilingual-e5-base` (768 dimensions)

We replace `paraphrase-multilingual-MiniLM-L12-v2` with `intfloat/multilingual-e5-base`:

- **278M parameters** (vs. 118M) — double the model capacity
- **768 dimensions** (vs. 384) — double the vector resolution
- **E5 architecture** requires prefixes: `"query: "` for search queries, `"passage: "` for documents. This asymmetric encoding significantly improves retrieval quality over symmetric models.
- **MTEB benchmark**: E5-base substantially outperforms MiniLM-L12-v2 on multilingual retrieval tasks.

#### Rejected alternative: `multilingual-e5-large` (1024 dimensions)

Was implemented first but rejected because:
- ONNX model is ~2.2 GB (split across `model.onnx` + `model.onnx_data`)
- Docker build times exceeding 15 minutes for the download
- Significantly higher RAM usage during inference (~2 GB vs. ~1 GB)
- Quality gain from 768 to 1024 dimensions does not justify the cost for 241 chunks

### 2. Hybrid Search with Reciprocal Rank Fusion (RRF)

Pure vector search is fragile when the embedding model does not encode domain terms well enough. We supplement the search with PostgreSQL full-text search (BM25) and fuse both rankings with RRF:

```
RRF_score = 0.5 / (60 + vector_rank) + 0.5 / (60 + text_rank)
```

- **Vector search**: Semantic similarity — finds conceptually related content
- **Full-text search** (`tsvector` with German stemmer): Keyword match — finds exact terms like "Stickstoff", "gelb", "untere Blaetter"
- **RRF fusion**: Chunks ranking high in both systems are preferred

This requires:
- New `search_text tsvector` column in `ai_vector_chunks` (GIN index)
- Ingest pipeline populates `search_text` automatically from `title || content`

## Affected components

| Component | Change |
|-----------|--------|
| `docker/embedding-service/Dockerfile` | Model download `intfloat/multilingual-e5-base` |
| `docker/embedding-service/main.py` | `prefix` field in EmbedRequest, default model |
| Migration 002 | `vector(384)` to `vector(768)`, IVFFlat to HNSW, `search_text tsvector` + GIN |
| `vector_chunk_repository.py` | New `hybrid_search()` method, `search_text` in upsert |
| `embedding_engine.py` | `prefix` parameter for query/passage distinction |
| `knowledge_ingestor.py` | `prefix="passage: "` when embedding documents |
| `knowledge_service.py` | `prefix="query: "` when embedding queries, `hybrid_search` |
| `tools/rag-eval/eval_rag.py` | Hybrid search + E5 prefix in standalone eval tool |
| Helm values-dev | `EMBEDDING_MODEL` environment variable |
| Backend settings | Default `embedding_model` |

## Consequences

### Positive
- Significantly better retrieval quality through higher vector resolution and asymmetric query/passage encoding
- Hybrid search as safety net: even when semantic search fails, keyword matches find the correct chunk
- RRF is parameter-light and robust — no expensive tuning required
- HNSW index scales better than IVFFlat at higher dimensions

### Negative
- Embedding service requires ~1 GB RAM instead of ~500 MB (acceptable for dev/prod)
- Docker image ~1.5 GB instead of ~600 MB
- All existing embeddings must be regenerated after migration 002 (reindex via Celery task)
- E5 prefix convention must be consistently applied across all callers

### Neutral
- Chunk count (241) is small enough that the model switch has immediately measurable impact
- PostgreSQL German stemmer handles domain terms like "Naehrstoffmangel" or "Ueberwaesserung" well
