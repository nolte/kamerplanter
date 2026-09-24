# ADR-007: Cross-Encoder Re-Ranking for RAG Pipeline

**Status:** Accepted
**Date:** 2026-04-02
**Decision makers:** Kamerplanter Development Team

## Context

The RAG pipeline (ADR-006) uses Hybrid Search (vector + BM25 full-text with Reciprocal Rank Fusion). The RAG benchmark shows a 29% overall score with the following error distribution:

- **57% GENERATION_MISS** — LLM receives irrelevant chunks and hallucinates
- **11% RETRIEVAL_MISS** — Hybrid Search fails to find the correct chunk in Top-K
- **21% SYNONYM_GAP** — evaluation patterns do not recognise correct answers (independent issue)

### Problem

The Bi-Encoder (E5-base) and BM25 rank independently. Their fusion via RRF is effective for recall but not optimal for precision: irrelevant chunks with high BM25 scores (keyword matches without semantic relevance) pollute the LLM context. This causes the dominant error class GENERATION_MISS.

## Decision

**Cross-Encoder Re-Ranking as an optional pipeline stage between retrieval and LLM generation.**

### Architecture

```
Query → Hybrid Search (top_k=20) → Cross-Encoder Re-Rank (top_k=5) → LLM
```

- **Separate microservice** (`reranker-service`), analogous to the embedding service (ONNX Runtime + FastAPI)
- **Model:** `BAAI/bge-reranker-v2-m3` (multilingual, 568M parameters, Apache-2.0)
- **Graceful degradation:** Without a reranker URL the pipeline operates as before (hybrid search only)

### Why a separate service instead of in-process?

1. Cross-encoder inference is CPU-intensive (~500ms for 20 pairs) — requires its own memory/CPU budget
2. Existing architecture (embedding service) has proven itself
3. Optionally deployable — no additional Python dependency in the knowledge service

### Why bge-reranker-v2-m3?

| Criterion | bge-reranker-v2-m3 | ms-marco-MiniLM-L-12-v2 |
|-----------|-------------------|--------------------------|
| Languages | Multilingual (DE/EN) | English-focused |
| Parameters | 568M | 33M |
| BEIR benchmark | State-of-the-art | Good, but EN-only |
| ONNX export | Via optimum (until 2026-09-24; see amendment below) | Via optimum (until 2026-09-24; see amendment below) |
| Licence | Apache-2.0 | Apache-2.0 |
| Kamerplanter use case | DE knowledge base | Unsuitable |

### Rejected alternatives

1. **RRF weight tuning only:** Improves precision minimally; does not solve the root problem (keyword matches without semantic relevance)
2. **ColBERT / Late Interaction:** Higher recall, but recall was not the problem being addressed
3. **LLM-based re-ranking:** Too slow (>5s), too expensive for local inference

## Consequences

### Positive

- More precise LLM context → fewer GENERATION_MISS errors
- Expected benchmark improvement: 10–20 percentage points
- No breaking changes — graceful degradation when reranker is absent
- Same deployment patterns as the embedding service (known and tested)

### Negative

- Additional microservice (+1.5–4 GB RAM, +500ms latency per query)
- ONNX export via `optimum` during Docker build (longer build time) — until 2026-09-24, see amendment below
- First Docker build takes ~10–15 minutes (model download + export) — until 2026-09-24, see amendment below

### Neutral

- Knowledge service config: 3 new environment variables (`RERANKER_URL`, `RERANKER_INITIAL_K`, `RERANKER_TOP_K`)
- Helm/Skaffold: new controller, service, NetworkPolicy (analogous to embedding service)

## Amendment (2026-09-24): export mechanism replaced by a pinned download

As of 2026-09-24, the `reranker-service` no longer exports any model to ONNX itself via `optimum` at Docker build time. The download stages in the Dockerfile instead fetch model files that are already ONNX, directly from Hugging Face — each pinned to a fixed commit revision (`onnx-community/bge-reranker-v2-m3-ONNX` and `cross-encoder/ms-marco-MiniLM-L12-v2` respectively). At runtime, the service tokenizes with the `tokenizers` library instead of `transformers`. `transformers`, `optimum` and `torch` are gone from the image and from the dependency lock (tracked internally as issue #1480).

**Reason:** `optimum-onnx`, the ONNX exporter, caps `transformers` below 4.58 in every release it has published. That held the reranker service on `transformers` 4.57.6 — a version with three HIGH CVEs and one MEDIUM CVE.

**Measured** against the previous `optimum` export: identical tokenizer output, identical graph inputs/outputs, and a maximum score delta of 4.7 × 10⁻⁶ for `bge-reranker-v2-m3` (no measurable delta for `ms-marco-MiniLM-L12-v2`), with identical rankings in both cases. Build time drops accordingly: the 10–15 minute export is gone, leaving only the download.

The API (`/rerank`, `/health`, `/ready`) is unchanged — with one exception: an empty `documents` list now returns an empty result instead of an error.

This ADR's actual decision — Cross-Encoder re-ranking with `bge-reranker-v2-m3` as the default model — and its rationale remain unchanged; only the way the ONNX file is obtained has changed.
