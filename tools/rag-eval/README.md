# RAG Quality Benchmark

Standalone-Tool zur Qualitaetsmessung der Kamerplanter RAG-Pipeline (REQ-031).
Keine Abhaengigkeit zum Backend — verbindet sich direkt zu Embedding Service, VectorDB und Ollama.

## Voraussetzungen

Die folgenden Services muessen laufen (z.B. via `skaffold dev`):

| Service | Port (lokal) | Beschreibung |
|---------|-------------|--------------|
| Embedding Service | `localhost:8080` | ONNX-basierte Vektorisierung |
| VectorDB (pgvector) | `localhost:5433` | PostgreSQL mit ai_vector_chunks |
| Ollama | `localhost:11434` | Lokale LLM-Inferenz |

Die VectorDB muss bereits indexiert sein (`reindex_vector_chunks` Task muss mindestens einmal gelaufen sein).
Anleitung zum manuellen Reindexieren: siehe [RAG-Wissensbasis — Reindexierung](../../docs/de/guides/rag-knowledge-base.md#wissensbasis-reindexieren-operatorentwickler).

Ollama muss ein Modell geladen haben:

```bash
curl http://localhost:11434/api/pull -d '{"name": "gemma3:4b"}'
```

## Setup

```bash
cd tools/rag-eval

python -m venv ~/.venvs/rag-eval
source ~/.venvs/rag-eval/bin/activate    # Linux/macOS
# %USERPROFILE%\.venvs\rag-eval\Scripts\activate  # Windows

pip install -r requirements.txt
```

## CLI-Tool

### Alle Fragen ausfuehren

```bash
python eval_rag.py
```

### Nur bestimmte Kategorien

```bash
python eval_rag.py --categories diagnostik duengung
```

### Anderes Modell testen

```bash
python eval_rag.py --model llama3.2:3b
```

### Eigene Endpoints

```bash
python eval_rag.py \
  --embedding-url http://localhost:8080 \
  --vectordb-dsn "host=localhost port=5433 dbname=kamerplanter_vectors user=postgres password=devpassword" \
  --ollama-url http://localhost:11434 \
  --model gemma3:4b
```

### Ergebnis-Datei

```bash
python eval_rag.py -o ergebnisse.json
```

Der Exit-Code ist `0` bei bestandenem Benchmark (>= 70%) und `1` bei Nicht-Bestehen — direkt nutzbar in CI-Pipelines.

### Alle Optionen

```
python eval_rag.py --help
```

### Konfiguration via Umgebungsvariablen

Alternativ zu CLI-Argumenten:

```bash
export EMBEDDING_SERVICE_URL=http://localhost:8080
export VECTORDB_DSN="host=localhost port=5433 dbname=kamerplanter_vectors user=postgres password=devpassword"
export LLM_API_URL=http://localhost:11434
export LLM_MODEL=gemma3:4b
python eval_rag.py
```

## Jupyter Notebook

Das Notebook bietet interaktive Auswertung mit Visualisierungen.

### Setup (zusaetzliche Dependencies)

```bash
# In der gleichen venv:
pip install jupyter matplotlib pandas
```

### Starten

```bash
jupyter notebook rag_eval.ipynb
```

### Inhalt

| Abschnitt | Beschreibung |
|-----------|--------------|
| Verbindungstest | Prueft ob alle Services erreichbar sind |
| Benchmark | Fuehrt alle 100 Fragen durch die RAG-Pipeline |
| Score pro Kategorie | Balkendiagramm (gruen/rot) mit Pass-Schwelle |
| Score pro Schwierigkeit | Vergleich beginner/intermediate/expert |
| Fehleranalyse | Top-15 schlechteste Fragen mit fehlenden Topics |
| Einzel-Inspektion | Eine Frage im Detail mit Antwort und Chunks |
| Chunk-Similarity | Histogramm der Retrieval-Qualitaet |

## Ausgabe

Beide Varianten schreiben `eval_results.json`:

```json
{
  "timestamp": "2026-03-29T...",
  "model": "gemma3:4b",
  "method": "topic_match",
  "total_score": 0.785,
  "pass": true,
  "min_pass_score": 0.70,
  "category_scores": {
    "diagnostik": 0.85,
    "duengung": 0.80
  },
  "questions_evaluated": 100,
  "failures": []
}
```

## Eval-Daten

| Datei | Beschreibung |
|-------|-------------|
| `tests/rag-eval/benchmark_questions.yaml` | 100 kuratierte Fragen mit erwarteten Topics |
| `tests/rag-eval/topic_synonyms.yaml` | Synonym-Woerterbuch fuer Topic-Match (Regex + Keywords) |
| `tests/rag-eval/RAG_EVAL_SPEC.md` | Vollstaendige Spezifikation des Eval-Frameworks |
