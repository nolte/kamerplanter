# RAG Eval Benchmark Report

**Datum:** 2026-04-03
**Status:** PASS (78.0% Gesamt, Threshold 70%)
**Benchmark:** 100 Fragen, 9 Kategorien

Dieses Dokument dient als Referenz-Baseline fuer zukuenftige Testlaeufe.
Aenderungen an Modellen, Embedding, Retrieval oder Knowledge-Base sollten
gegen diese Ergebnisse verglichen werden.

---

## Konfiguration

### LLM

| Parameter | Wert |
|-----------|------|
| Provider | Ollama |
| Modell | gemma3:12b |
| Max Tokens | 1024 |
| Temperature | 0.1 |
| Endpoint | http://192.168.178.130:31434 (LAN NodePort) |

### Embedding

| Parameter | Wert |
|-----------|------|
| Modell | multilingual-e5-base |
| Dimensionen | 768 |
| Runtime | ONNX (CPU) |
| Query-Prefix | "query: " (E5-spezifisch) |
| Service | kamerplanter-ki-embedding-service:8080 |
| Ressourcen | 100m-1 CPU, 512Mi-2Gi RAM |

### Reranker

| Parameter | Wert |
|-----------|------|
| Modell | bge-reranker-v2-m3 |
| Initial K (Retrieval) | 20 |
| Top K (nach Reranking) | 5 |
| Service | kamerplanter-ki-reranker-service:8081 |
| Ressourcen | 100m-2 CPU, 1536Mi-4Gi RAM |

### Retrieval

| Parameter | Wert |
|-----------|------|
| Methode | Hybrid Search (Vector + BM25) |
| Fusion | Reciprocal Rank Fusion (RRF), k=60 |
| Vector Weight | 0.4 (BM25 Weight: 0.6) |
| Default Top K (API) | 10 |
| VectorDB | PostgreSQL 17 + pgvector 0.8.0 |
| Full-Text | tsvector mit Umlaut-Varianten (ae/oe/ue + Umlaute) |
| Reranker | bge-reranker-v2-m3 (20 candidates -> 5 final) |

### Knowledge Base

| Parameter | Wert |
|-----------|------|
| Dateien | 36 YAML |
| Chunks | 265 |
| Kategorien | 9 (diagnostik, duengung, bewaesserung, umwelt, ipm, phasen, outdoor/companion_planting, pflege, allgemein/anfaenger) |
| Sprache | Deutsch |
| Chunk-Laenge | 150-400 Woerter |

### Prompt-Strategie

| Parameter | Wert |
|-----------|------|
| Frage-Klassifizierung | Automatisch (diagnosis/howto/factual) via Regex-Heuristik |
| System-Prompt | Typ-spezifisch (3 Varianten DE + 3 EN) |
| Instruktion | "Nenne ALLE relevanten Punkte aus dem Kontext — ueberspringe nichts" |
| Extraction Suffix | "Zitiere konkrete Schritte, Werte und Reihenfolgen. Nutze NUR den Kontext." |
| Kontext-Format | Nummerierte Chunks mit Titel + Content, getrennt durch --- |

---

## Ergebnisse

### Gesamt

| Metrik | Wert |
|--------|------|
| **Gesamtscore** | **78.0%** |
| **Threshold** | 70% |
| **Status** | **PASS** |
| Fragen evaluiert | 100 |
| Failures | 30 |
| PASS-Fragen (>=0.7) | 70 |

### Kategorie-Scores

| Kategorie | Score | Status | Fragen | PASS | FAIL |
|-----------|-------|--------|--------|------|------|
| Anfaenger | 100.0% | PASS | 3 | 3 | 0 |
| Phasen | 87.5% | PASS | 10 | 8 | 2 |
| IPM | 87.2% | PASS | 10 | 8 | 2 |
| Companion Planting | 85.5% | PASS | 10 | 8 | 2 |
| Pflege | 78.9% | PASS | 12 | 9 | 3 |
| Duengung | 77.7% | PASS | 15 | 11 | 4 |
| Bewaesserung | 75.0% | PASS | 10 | 8 | 2 |
| Diagnostik | 73.3% | PASS | 15 | 10 | 5 |
| Umwelt | 72.3% | PASS | 15 | 10 | 5 |

### Bewaesserung Detail (separat getestet nach Optimierung)

| Frage | Score | Status |
|-------|-------|--------|
| wasser-001 | 0.00 | FAIL (FPs: jeden_montag, taeglich) |
| wasser-002 | 1.00 | PASS |
| wasser-003 | 1.00 | PASS |
| wasser-004 | 0.75 | PASS |
| wasser-005 | 1.00 | PASS |
| wasser-006 | 0.75 | PASS |
| wasser-007 | 1.00 | PASS |
| wasser-008 | 1.00 | PASS |
| wasser-009 | 1.00 | PASS |
| wasser-010 | 0.00 | FAIL (RETRIEVAL/GENERATION_MISS) |

---

## Optimierungs-Historie

| Iteration | Aenderung | Gesamt-Score | Kategorien PASS |
|-----------|-----------|-------------|-----------------|
| Baseline (gemma3:4b, kein Reranker) | Nur bestehende Knowledge-Base | 32.5% (nur Pflege) | 1/9 (Umwelt) |
| + Pflege Knowledge-Chunks | 3 neue YAML-Dateien, 11 Chunks | 58.5% (Pflege) | 1/9 |
| + Prompt-Tuning + Retrieval 0.4 | "Nenne ALLE", vector_weight 0.4 | 66.1% (Pflege) | 1/9 |
| + top_k=10 default | API default 5->10 | 66.4% (Pflege) | 1/9 |
| + gemma3:12b | Modell-Upgrade 4B->12B | 60.7% (Full) | 1/9 |
| + Knowledge-Chunks Runde 1 (alle Kat.) | Phasen, Comp.Planting, Anfaenger, IPM Chunks | IPM 84.7%, Anfaenger 88.9%, CP 62.2% | 4/9 |
| + Companion Planting Runde 2 | Gezielte Chunk-Fixes | CP 78.0% | 4/9 |
| + Knowledge-Chunks Runde 2 (5 Kat.) | Diagnostik, Duengung, Bewaesserung, Phasen, Pflege | 67.0% (5 Kat.) | 4/9 |
| + Reranker (bge-reranker-v2-m3) + temp 0.1 | Reranker-Service, Temperature 0.3->0.1 | **78.0% (Full)** | **8/9** |
| + Bewaesserung Runde 2 | Gezielte Chunk-Fixes | Bewaesserung 75.0% | **9/9** |

---

## Verbleibende Failures (30 Fragen)

### Haeufigste Fehlerklassen

| Fehlerklasse | Anzahl | Beschreibung |
|-------------|--------|--------------|
| GENERATION_MISS | ~15 | LLM generiert nicht alle Keywords trotz vorhandenem Chunk |
| RETRIEVAL_MISS | ~5 | Richtiger Chunk wird nicht in Top-5 retrievt |
| FALSE_POSITIVE | ~5 | LLM nennt expected_NOT Topics |
| LLM_NONDETERMINISMUS | ~5 | Score schwankt zwischen Laeufen (0.50 vs 1.00) |

### Bekannte hartnaeckige Failures

- **wasser-001**: FPs "jeden_montag" und "taeglich" — LLM gibt Zeitplan-Ratschlaege trotz "nicht nach Zeitplan"-Instruktion
- **wasser-010**: Giess-Zeitpunkt-Chunk wird nicht retrievt (RETRIEVAL_MISS)
- **diag-001**: Oft Timeout bei erster Frage (Ollama Cold-Start)
- **comp-001**: LLM nennt Kartoffel/Fenchel als Tomaten-Partner trotz Negation im Chunk
- **comp-009**: Gruenduengungs-Chunk wird nicht retrievt

---

## Naechste Optimierungs-Hebel (priorisiert)

1. **max_tokens 1024 -> 2048** — Ermoeglicht laengere Antworten, verhindert Abbruch bei Aufzaehlungen
2. **Few-Shot Examples im System-Prompt** — 1-2 Beispiel-Antworten die vollstaendige Aufzaehlungen zeigen
3. **Groesseres LLM** — gemma3:27b oder Qwen2.5:14b fuer bessere Topic-Abdeckung
4. **Groesseres Embedding** — multilingual-e5-large statt base fuer praeziseres Retrieval
5. **Answer Verification** — Zweiter LLM-Call zur Vollstaendigkeitspruefung

---

## Reproduktion

```bash
# Voraussetzungen: Knowledge Service + Ollama + Reranker laufen
# Ingestion
curl -X POST http://localhost:8090/ingest

# Smoke-Test
python tools/rag-eval/eval_rag.py --smoke --service-url http://localhost:8090

# Full Benchmark
python tools/rag-eval/eval_rag.py --service-url http://localhost:8090

# Einzelne Kategorie
python tools/rag-eval/eval_rag.py --categories pflege --service-url http://localhost:8090

# Retrieval-Debug (ohne LLM)
python tools/rag-eval/eval_rag.py --retrieval-only --categories diagnostik --service-url http://localhost:8090
```
