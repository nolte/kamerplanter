# ADR-007: Cross-Encoder Re-Ranking für RAG-Pipeline

**Status:** Akzeptiert
**Datum:** 2026-04-02
**Entscheider:** Kamerplanter Development Team

## Kontext

Die RAG-Pipeline (ADR-006) verwendet Hybrid Search (Vektor + BM25 Full-Text mit Reciprocal Rank Fusion). Der RAG-Benchmark zeigt 29% Gesamtscore mit folgender Fehlerverteilung:

- **57% GENERATION_MISS** — LLM erhält irrelevante Chunks und halluziniert
- **11% RETRIEVAL_MISS** — Hybrid Search findet den richtigen Chunk nicht in Top-K
- **21% SYNONYM_GAP** — Eval-Pattern erkennt korrekte Antworten nicht (unabhängig)

### Problem

Bi-Encoder (E5-base) und BM25 ranken unabhängig voneinander. Ihre Fusion via RRF ist effektiv für Recall, aber nicht optimal für Precision: Irrelevante Chunks mit hohem BM25-Score (Keyword-Match ohne semantische Relevanz) verrauschen den LLM-Kontext. Das führt zur dominierenden Fehlerklasse GENERATION_MISS.

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

1. Cross-Encoder-Inferenz ist CPU-intensiv (~500ms für 20 Paare) — eigenes Memory/CPU-Budget
2. Bestehende Architektur (Embedding-Service) bewährt sich
3. Optional deploybar — keine zusätzliche Python-Dependency im Knowledge-Service

### Warum bge-reranker-v2-m3?

| Kriterium | bge-reranker-v2-m3 | ms-marco-MiniLM-L-12-v2 |
|-----------|-------------------|--------------------------|
| Sprachen | Multilingual (DE/EN) | Englisch-fokussiert |
| Parameter | 568M | 33M |
| BEIR-Benchmark | State-of-the-art | Gut, aber EN-only |
| ONNX-Export | Via optimum (bis 2026-09-24; siehe Nachtrag unten) | Via optimum (bis 2026-09-24; siehe Nachtrag unten) |
| Lizenz | Apache-2.0 | Apache-2.0 |
| Kamerplanter-Usecase | DE-Wissensbasis | Ungeeignet |

### Abgelehnte Alternativen

1. **Nur RRF-Weight-Tuning:** Verbessert Precision minimal, löst das Grundproblem nicht (Keyword-Matches ohne semantische Relevanz)
2. **ColBERT/Late Interaction:** Höherer Recall, aber Re-Ranking war nicht das Recall-Problem
3. **LLM-basiertes Re-Ranking:** Zu langsam (>5s), zu teuer für lokale Inferenz

## Konsequenzen

### Positiv

- Präziserer LLM-Kontext → weniger GENERATION_MISS
- Erwartete Benchmark-Verbesserung: 10-20 Prozentpunkte
- Keine Breaking Changes — Graceful Degradation bei fehlendem Reranker
- Gleiche Deployment-Patterns wie Embedding-Service (bekannt, getestet)

### Negativ

- Zusätzlicher Microservice (+1.5-4 GB RAM, +500ms Latenz pro Query)
- ONNX-Export via `optimum` im Docker-Build (längere Build-Zeit) — bis 2026-09-24, siehe Nachtrag unten
- Erste Docker-Build-Zeit ~10-15 Minuten (Modell-Download + Export) — bis 2026-09-24, siehe Nachtrag unten

### Neutral

- Knowledge-Service-Config: 3 neue Umgebungsvariablen (`RERANKER_URL`, `RERANKER_INITIAL_K`, `RERANKER_TOP_K`)
- Helm/Skaffold: Neuer Controller, Service, NetworkPolicy (analog Embedding-Service)

## Nachtrag (2026-09-24): Export-Mechanismus durch gepinnten Download ersetzt

Seit 2026-09-24 exportiert der `reranker-service` beim Docker-Build keine Modelle mehr selbst per `optimum` nach ONNX. Die Download-Stufen im Dockerfile holen stattdessen Modell-Dateien, die bereits als ONNX vorliegen, direkt von Hugging Face — jeweils an eine feste Commit-Revision gepinnt (`onnx-community/bge-reranker-v2-m3-ONNX` bzw. `cross-encoder/ms-marco-MiniLM-L12-v2`). Zur Laufzeit tokenisiert der Service mit der `tokenizers`-Bibliothek statt mit `transformers`. `transformers`, `optimum` und `torch` sind aus dem Image und aus dem Dependency-Lock entfernt (intern verfolgt als Issue #1480).

**Grund:** `optimum-onnx`, der ONNX-Exporter, begrenzt `transformers` in jeder bislang veröffentlichten Version auf eine Version kleiner als 4.58. Das hielt den Reranker-Service auf `transformers` 4.57.6 fest — einer Version mit drei HIGH- und einer MEDIUM-CVE.

**Gemessen** gegen den vorherigen `optimum`-Export: identische Tokenizer-Ausgabe, identische Graph-Ein- und -Ausgaben sowie eine maximale Score-Abweichung von 4,7 × 10⁻⁶ bei `bge-reranker-v2-m3` (bei `ms-marco-MiniLM-L12-v2` keine messbare Abweichung), jeweils mit identischem Ranking. Die Build-Zeit sinkt entsprechend: Der 10–15-minütige Export entfällt, es bleibt nur noch der Download.

Die API (`/rerank`, `/health`, `/ready`) ist unverändert — mit einer Ausnahme: Eine leere `documents`-Liste liefert seither ein leeres Ergebnis statt eines Fehlers.

Die eigentliche Entscheidung dieses ADRs — Cross-Encoder Re-Ranking mit `bge-reranker-v2-m3` als Standardmodell — sowie ihre Begründung bleiben unverändert; geändert hat sich nur der Beschaffungsweg der ONNX-Datei.

## Nachtrag (2026-09-25): `RERANKER_INITIAL_K`-Default gesenkt, neue Zeichenobergrenze pro Dokument

Der ursprünglich angenommene Aufwand von „~500ms für 20 Paare" (siehe „Warum separater Service statt In-Process?" oben) hat sich am 2-CPU-Limit des Helm-Charts als deutlich zu niedrig erwiesen: `bge-reranker-v2-m3` kostet dort real ~3 Sekunden je (Query, Dokument)-Paar mit 512 Tokens. Ein realer HTTP-Test über alle 100 Benchmark-Fragen gegen den Reranker-Sidecar bestätigt das für den ursprünglichen Default `RERANKER_INITIAL_K=20` mit vollständigen Dokumenten bis 512 Tokens: Jede Anfrage traf die serverseitige 25-Sekunden-Deadline (`{"status": "timeout"}` nach ~27 Sekunden; rechnerisch entspräche das ~54 Sekunden Gesamtaufwand). In der Praxis lief Re-Ranking dadurch nie durch; jede Suche wartete zusätzlich ~27 Sekunden auf einen Fallback, der ohnehin eintrat.

Seit diesem Datum gilt:

- `RERANKER_INITIAL_K` hat den Default **15** (statt 20).
- Neue Umgebungsvariable `RERANKER_MAX_DOCUMENT_CHARS` (Default **500**): Jeder Kandidaten-Chunk (`titel\ninhalt`) wird vor dem Versand an den Reranker-Sidecar auf diese Zeichenzahl gekürzt (Paar-Median 166 Tokens, maximal 222). Der an das LLM übergebene Chunk behält seinen vollständigen Text — nur die Reranker-Eingabe wird verkürzt.
- Beide Werte erfüllen zusammen exakt das vom Reranker-Service erzwungene Zeichenbudget `RERANKER_INITIAL_K × RERANKER_MAX_DOCUMENT_CHARS ≤ 7.500` (`RERANK_SCORED_CHARS_BUDGET` in `config.py`, 15 × 500 = 7.500).
- Die Budget-Grenze bestimmt nur, wie viele Kandidaten neu bewertet werden — nie, wie viele Ergebnisse ein Aufrufer erhält: `KnowledgeService.search()` ruft `max(RERANKER_INITIAL_K, top_k)` Kandidaten ab, bewertet nur den Kopf der Länge `RERANKER_INITIAL_K` neu und hängt den Rest unverändert in Hybrid-Reihenfolge an. Bei einem Fallback entspricht das Gesamtergebnis vollständig der ungerankten Hybrid-Reihenfolge.

Mit den neuen Standardwerten waren im selben Test alle 100 Anfragen erfolgreich (p50 12,9 Sekunden, p90 15,0 Sekunden, maximal 16,0 Sekunden — innerhalb des 25-Sekunden-Budgets). Die Kontextqualität (Anteil der erwarteten Themen im zurückgegebenen Kontext, 54 Fragen/9 Kategorien) hängt vom angeforderten `top_k` ab: Bei `top_k=5` steigt sie von 0,927 ohne Re-Ranking auf 0,974 mit den neuen Standardwerten (ungebremstes Re-Ranking aller Kandidaten: 0,982, passt aber nicht in die Deadline); beim Chat-Standardwert `top_k=10` ist der Gewinn klein (0,978 → 0,979, ungebremst 0,995) — der größere Nutzen liegt bei Aufrufern mit wenigen angeforderten Chunks wie dem Glossar (`top_k=5`) oder dem Diagnose-Assistenten (`top_k=8`). Details zu den Fallback-Gründen (`reranker_fallback`, u. a. `reason=deadline`) stehen in der [KI-Architektur](../architecture/ai-architecture.md#fallback-gruende-und-zeitbudget).

Die Entscheidung für Cross-Encoder Re-Ranking mit `bge-reranker-v2-m3` bleibt unverändert; geändert haben sich nur die Standardwerte für Over-Retrieval, eine neue, zusätzliche Zeichenobergrenze pro Dokument und die explizite Bewertungs-Invariante.
