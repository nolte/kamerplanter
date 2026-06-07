# ADR-006: Embedding-Modell multilingual-e5-base und Hybrid Search für RAG

**Status:** Akzeptiert
**Datum:** 2026-03-30
**Entscheider:** Kamerplanter Development Team

## Kontext

Der Kamerplanter KI-Assistent (REQ-031) nutzt eine RAG-Pipeline (Retrieval-Augmented Generation) um Pflanzenpflege-Fragen anhand einer kuratierten Wissensdatenbank zu beantworten. Die Pipeline besteht aus:

1. **Embedding-Service** (ONNX Runtime) — erzeugt Vektoren aus Text
2. **pgvector** (PostgreSQL) — speichert und durchsucht Vektoren per Cosine-Similarity
3. **LLM** (Ollama/Claude) — generiert Antworten aus den gefundenen Kontext-Chunks

### Problem: Retrieval-Qualität war unbrauchbar

Beim RAG-Smoke-Test mit dem bisherigen Embedding-Modell `paraphrase-multilingual-MiniLM-L12-v2` (384 Dimensionen) lieferte die Vektor-Suche für die Frage *"Meine unteren Blätter werden gelb, die oberen sind noch grün. Was fehlt?"* folgende Top-5 Ergebnisse:

| Rang | Chunk | Score |
|------|-------|-------|
| 1 | Karenzzeit — Sicherheitsabstand vor Ernte | 0.7909 |
| 2 | Topping und FIM — Verzweigung erzwingen | 0.7867 |
| 3 | Samen-Vorbehandlung — Stratifikation | 0.7380 |
| 4 | Blüte bei Gemüse und Obst | 0.7346 |
| 5 | Grauschimmel (Botrytis) erkennen | 0.7345 |

Der korrekte Chunk *"Stickstoff (N) Mangel"* — der exakt die Symptome beschreibt — fehlte komplett im Top-5. Alle Scores lagen zwischen 0.73 und 0.79, es gab praktisch keine Differenzierung. Das LLM erhielt irrelevanten Kontext und halluzinierte eine falsche Diagnose (Kalium statt Stickstoff).

### Ursache

`paraphrase-multilingual-MiniLM-L12-v2` ist ein kleines Modell (118M Parameter, 384 Dimensionen), das für allgemeine Paraphrase-Erkennung optimiert ist. Es kodiert alle deutschen Pflanzenfach-Texte in einen zu engen Bereich des Vektorraums — die Cosine-Similarity zwischen völlig unterschiedlichen Chunks liegt bei 0.73-0.88. Der Vektor-Raum ist zu niedrigdimensional um domainspezifische Nuancen abzubilden.

## Entscheidung

### 1. Wechsel auf `multilingual-e5-base` (768 Dimensionen)

Wir ersetzen `paraphrase-multilingual-MiniLM-L12-v2` durch `intfloat/multilingual-e5-base`:

- **278M Parameter** (vs. 118M) — doppelte Modellkapazität
- **768 Dimensionen** (vs. 384) — doppelte Vektorauflösung
- **E5-Architektur** erfordert Präfixe: `"query: "` für Suchanfragen, `"passage: "` für Dokumente. Diese asymmetrische Kodierung verbessert die Retrieval-Qualität signifikant gegenüber symmetrischen Modellen.
- **MTEB-Benchmark**: E5-base schneidet auf multilingualen Retrieval-Tasks deutlich besser ab als MiniLM-L12-v2.

#### Verworfene Alternative: `multilingual-e5-large` (1024 Dimensionen)

Wurde zuerst implementiert, aber verworfen weil:
- ONNX-Modell ist ~2.2 GB (aufgeteilt in `model.onnx` + `model.onnx_data`)
- Docker-Build-Zeiten von >15 Minuten für den Download
- Deutlich höherer RAM-Verbrauch im Inference (~2 GB vs. ~1 GB)
- Der Qualitätsgewinn von 768 auf 1024 Dimensionen rechtfertigt die Kosten nicht für 241 Chunks

### 2. Hybrid Search mit Reciprocal Rank Fusion (RRF)

Reine Vektor-Suche ist anfällig wenn das Embedding-Modell Domänen-Begriffe nicht gut genug kodiert. Wir ergänzen die Suche um PostgreSQL Full-Text-Search (BM25) und fusionieren beide Rankings mit RRF:

```
RRF_score = 0.5 / (60 + vector_rank) + 0.5 / (60 + text_rank)
```

- **Vektor-Suche**: Semantische Ähnlichkeit — findet konzeptuell verwandte Inhalte
- **Full-Text-Search** (`tsvector` mit German-Stemmer): Keyword-Match — findet exakte Begriffe wie "Stickstoff", "gelb", "untere Blätter"
- **RRF-Fusion**: Chunks die in beiden Rankings hoch stehen werden bevorzugt

Dies erfordert:
- Neue `search_text tsvector`-Spalte in `ai_vector_chunks` (GIN-Index)
- Ingest-Pipeline befüllt `search_text` automatisch aus `title || content`

## Betroffene Komponenten

| Komponente | Änderung |
|-----------|-----------|
| `docker/embedding-service/Dockerfile` | Modell-Download `intfloat/multilingual-e5-base` |
| `docker/embedding-service/main.py` | `prefix`-Feld in EmbedRequest, Default-Modell |
| Migration 002 | `vector(384)` → `vector(768)`, IVFFlat → HNSW, `search_text tsvector` + GIN |
| `vector_chunk_repository.py` | Neue `hybrid_search()` Methode, `search_text` in Upsert |
| `embedding_engine.py` | `prefix`-Parameter für Query/Passage-Unterscheidung |
| `knowledge_ingestor.py` | `prefix="passage: "` beim Einbetten von Dokumenten |
| `knowledge_service.py` | `prefix="query: "` beim Einbetten von Anfragen, `hybrid_search` |
| `tools/rag-eval/eval_rag.py` | Hybrid Search + E5-Prefix im Standalone-Eval-Tool |
| Helm values-dev | `EMBEDDING_MODEL` Environment-Variable |
| Backend settings | Default `embedding_model` |

## Konsequenzen

### Positiv
- Deutlich bessere Retrieval-Qualität durch höhere Vektorauflösung und asymmetrische Query/Passage-Kodierung
- Hybrid Search als Safety-Net: auch wenn semantische Suche versagt, finden Keyword-Matches den richtigen Chunk
- RRF ist parameterarm und robust — kein aufwändiges Tuning nötig
- HNSW-Index skaliert besser als IVFFlat bei höheren Dimensionen

### Negativ
- Embedding-Service braucht ~1 GB RAM statt ~500 MB (akzeptabel für Dev/Prod)
- Docker-Image ~1.5 GB statt ~600 MB
- Alle bestehenden Embeddings müssen nach Migration 002 neu generiert werden (Reindex via Celery-Task)
- E5-Prefix-Konvention muss in allen Callern konsistent eingehalten werden

### Neutral
- Anzahl der Chunks (241) ist klein genug, dass der Modellwechsel sofort messbar ist
- PostgreSQL German-Stemmer ist für Fachbegriffe wie "Nährstoffmangel" oder "Überwässerung" gut geeignet
