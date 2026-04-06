# ADR-007: Cross-Encoder Re-Ranking fuer RAG-Pipeline

**Status:** Akzeptiert
**Datum:** 2026-04-02
**Entscheider:** Kamerplanter Development Team

## Kontext

Die RAG-Pipeline (ADR-006) verwendet Hybrid Search (Vektor + BM25 Full-Text mit Reciprocal Rank Fusion). Der RAG-Benchmark zeigt 29% Gesamtscore mit folgender Fehlerverteilung:

- **57% GENERATION_MISS** — LLM erhaelt irrelevante Chunks und halluziniert
- **11% RETRIEVAL_MISS** — Hybrid Search findet den richtigen Chunk nicht in Top-K
- **21% SYNONYM_GAP** — Eval-Pattern erkennt korrekte Antworten nicht (unabhaengig)

### Problem

Bi-Encoder (E5-base) und BM25 ranken unabhaengig voneinander. Ihre Fusion via RRF ist effektiv fuer Recall, aber nicht optimal fuer Precision: Irrelevante Chunks mit hohem BM25-Score (Keyword-Match ohne semantische Relevanz) verrauschen den LLM-Kontext. Das fuehrt zur dominierenden Fehlerklasse GENERATION_MISS.

## Entscheidung

**Cross-Encoder Re-Ranking als optionale Pipeline-Stufe zwischen Retrieval und LLM-Generation.**

### Architektur

```
Query → Hybrid Search (top_k=20) → Cross-Encoder Re-Rank (top_k=5) → LLM
```

- **Separater Microservice** (`reranker-service`), analog zum Embedding-Service (ONNX Runtime + FastAPI)
- **Modell:** `BAAI/bge-reranker-v2-m3` (multilingual, 568M Parameter, Apache-2.0)
- **Graceful Degradation:** Ohne Reranker-URL arbeitet die Pipeline wie bisher (nur Hybrid Search)

### Warum separater Service statt In-Process?

1. Cross-Encoder-Inferenz ist CPU-intensiv (~500ms fuer 20 Paare) — eigenes Memory/CPU-Budget
2. Bestehende Architektur (Embedding-Service) bewaehrt sich
3. Optional deploybar — keine zusaetzliche Python-Dependency im Knowledge-Service

### Warum bge-reranker-v2-m3?

| Kriterium | bge-reranker-v2-m3 | ms-marco-MiniLM-L-12-v2 |
|-----------|-------------------|--------------------------|
| Sprachen | Multilingual (DE/EN) | Englisch-fokussiert |
| Parameter | 568M | 33M |
| BEIR-Benchmark | State-of-the-art | Gut, aber EN-only |
| ONNX-Export | Via optimum | Via optimum |
| Lizenz | Apache-2.0 | Apache-2.0 |
| Kamerplanter-Usecase | DE-Wissensbasis | Ungeeignet |

### Abgelehnte Alternativen

1. **Nur RRF-Weight-Tuning:** Verbessert Precision minimal, loest das Grundproblem nicht (Keyword-Matches ohne semantische Relevanz)
2. **ColBERT/Late Interaction:** Hoeherer Recall, aber Re-Ranking war nicht das Recall-Problem
3. **LLM-basiertes Re-Ranking:** Zu langsam (>5s), zu teuer fuer lokale Inferenz

## Konsequenzen

### Positiv

- Praeziserer LLM-Kontext → weniger GENERATION_MISS
- Erwartete Benchmark-Verbesserung: 10-20 Prozentpunkte
- Keine Breaking Changes — Graceful Degradation bei fehlendem Reranker
- Gleiche Deployment-Patterns wie Embedding-Service (bekannt, getestet)

### Negativ

- Zusaetzlicher Microservice (+1.5-4 GB RAM, +500ms Latenz pro Query)
- ONNX-Export via `optimum` im Docker-Build (laengere Build-Zeit)
- Erste Docker-Build-Zeit ~10-15 Minuten (Modell-Download + Export)

### Neutral

- Knowledge-Service-Config: 3 neue Umgebungsvariablen (`RERANKER_URL`, `RERANKER_INITIAL_K`, `RERANKER_TOP_K`)
- Helm/Skaffold: Neuer Controller, Service, NetworkPolicy (analog Embedding-Service)
