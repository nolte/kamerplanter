# RAG-Qualitaetsbewertung — Evaluierungs-Framework

## 1. Ueberblick

Automatisiertes Framework zur Messung der RAG-Antwortqualitaet des KI-Assistenten (REQ-031).
Drei Evaluierungsmodi: Topic-Match (schnell), LLM-as-Judge (genau), A/B-Vergleich (Regression).

---

## 2. Architektur

```
benchmark_questions.yaml (100 Fragen)
         |
         v
+------------------+     +--------------------+
| RAG Pipeline     |     | Baseline (ohne RAG)|
| (Ollama + pgvec) |     | (nur LLM)          |
+--------+---------+     +---------+----------+
         |                         |
         v                         v
   RAG-Antwort A              Baseline-Antwort B
         |                         |
         +----------+--------------+
                    |
                    v
         +------------------+
         | Evaluator        |
         | (3 Methoden)     |
         +------------------+
         | 1. Topic-Match   |  Schnell, deterministisch
         | 2. LLM-as-Judge  |  Genau, teurer
         | 3. A/B-Vergleich |  Regression-Detection
         +--------+---------+
                  |
                  v
         eval_results.json
         (Scores pro Kategorie)
```

---

## 3. Evaluierungsmethoden

### 3.1 Topic-Match (Primaermethode, automatisiert)

Fuer jede Frage aus `benchmark_questions.yaml`:

1. Frage + optionaler Kontext an RAG-Pipeline senden
2. Antwort-Text erhalten
3. Pruefen ob `expected_topics` in der Antwort vorkommen (Keyword-/Semantik-Match)
4. Pruefen ob `expected_NOT` NICHT in der Antwort vorkommen

**Scoring pro Frage:**
```python
topic_hits = count(expected_topics found in answer)
topic_total = len(expected_topics)
false_positives = count(expected_NOT found in answer)

# Score pro Frage: 0.0 bis 1.0
score = max(0.0, (topic_hits / topic_total) - (false_positives * 0.5))
```

**Matching-Strategie:**
- Topics sind semantische Konzepte, keine exakten Strings
- Matching ueber Synonym-Woerterbuch:
  ```yaml
  stickstoff_mangel: [stickstoff, nitrogen, N-Mangel, Stickstoffmangel, gelbe untere]
  calcium_mangel: [calcium, Ca-Mangel, Calciummangel, neue Blaetter braun]
  ueberwaesserung: [uebergiessen, zu viel Wasser, Wurzelfaeule, nass]
  ```
- Oder: Embedding-Similarity zwischen Topic-Description und Antwort-Abschnitt (Schwellenwert 0.75)

**Gesamt-Score:**
```python
category_scores = {cat: mean(scores for q in cat) for cat in categories}
total_score = mean(all question scores)
pass = total_score >= 0.70
```

### 3.2 LLM-as-Judge (Sekundaermethode, fuer Tiefenanalyse)

Ein staerkeres Modell bewertet die Antwort des RAG-Systems.

**Judge-Prompt:**
```
Du bist ein Agrarbiologie-Experte der die Antwortqualitaet eines
Pflanzen-KI-Assistenten bewertet.

FRAGE: {question}
KONTEXT: {context}
ANTWORT DES ASSISTENTEN: {rag_answer}

Bewerte auf einer Skala von 0-5:
1. FACHLICHE KORREKTHEIT: Sind alle Aussagen biologisch korrekt?
2. RELEVANZ: Geht die Antwort auf die spezifische Frage ein?
3. VOLLSTAENDIGKEIT: Fehlen wichtige Aspekte?
4. HALLUZINATIONEN: Werden Fakten erfunden die nicht stimmen?
5. PRAXISTAUGLICHKEIT: Kann der Nutzer die Empfehlung umsetzen?

Antworte als JSON:
{
  "correctness": 0-5,
  "relevance": 0-5,
  "completeness": 0-5,
  "hallucination_free": 0-5,
  "practicality": 0-5,
  "issues": ["Liste konkreter Probleme"],
  "overall": 0-5
}
```

**Judge-Modell:** `claude-haiku-4-5` (schnell + guenstig) oder `claude-sonnet-4-6` (genauer).
Fuer lokale Bewertung: `llama3.1:8b` mit strukturiertem Output.

### 3.3 A/B-Vergleich (Regression-Detection)

Gleiche Frage, zwei Durchlaeufe:
- **A:** LLM + RAG-Chunks (vollstaendige Pipeline)
- **B:** LLM ohne RAG-Kontext (nur System-Prompt)

Judge vergleicht blind:
```
Welche Antwort ist besser fuer die Frage "{question}"?

ANTWORT A: {answer_a}
ANTWORT B: {answer_b}

Bewerte: A_deutlich_besser | A_etwas_besser | gleich | B_etwas_besser | B_deutlich_besser
Begruendung: ...
```

**Erwartung:** RAG-Antwort sollte in >70% der Faelle besser sein als Baseline.
Wenn RAG-Antwort schlechter ist → Retrieval-Problem oder Chunk-Qualitaet pruefen.

---

## 4. Celery-Task Implementation

```python
# Backend: app/tasks/eval_rag_quality.py

@celery_app.task(name="eval-rag-benchmark")
def eval_rag_benchmark(
    method: str = "topic_match",  # topic_match | llm_judge | ab_compare
    categories: list[str] | None = None,  # None = alle
    judge_model: str = "claude-haiku-4-5",
) -> dict:
    """
    Fuehrt RAG-Benchmark durch und speichert Ergebnisse.

    Returns:
        {
            "timestamp": "2026-03-29T...",
            "method": "topic_match",
            "total_score": 0.82,
            "pass": true,
            "category_scores": {
                "diagnostik": 0.85,
                "duengung": 0.80,
                "bewaesserung": 0.78,
                ...
            },
            "questions_evaluated": 100,
            "failures": [
                {"id": "diag-006", "score": 0.3, "reason": "pH-Lockout nicht erwaehnt"}
            ]
        }
    """
```

**Celery Beat Schedule:**
```python
# Woechentlich Sonntag 03:00 UTC
"eval-rag-benchmark-weekly": {
    "task": "eval-rag-benchmark",
    "schedule": crontab(hour=3, minute=0, day_of_week=0),
    "kwargs": {"method": "topic_match"},
}
```

---

## 5. Ergebnis-Speicherung und Alerting

**Speicherung:** TimescaleDB (Zeitreihe fuer Trend-Analyse)
```sql
CREATE TABLE rag_eval_results (
    time        TIMESTAMPTZ NOT NULL,
    method      TEXT NOT NULL,
    category    TEXT NOT NULL,
    score       DOUBLE PRECISION NOT NULL,
    questions   INTEGER NOT NULL,
    failures    JSONB
);
SELECT create_hypertable('rag_eval_results', 'time');
```

**Alerting:**
- Score < 0.70 in einer Kategorie → Warning-Notification
- Score < 0.50 → Critical-Notification
- Score-Drop > 10% gegenueber Vorwoche → Regression-Alert
- Benachrichtigung ueber Apprise (REQ-022 Notification-Pattern)

---

## 6. Wann evaluieren?

| Trigger | Methode | Dauer |
|---------|---------|-------|
| Woechentlich (Celery Beat) | topic_match | ~5 Min (lokal) |
| Nach `reindex_vector_chunks` Task | topic_match | ~5 Min |
| Nach Seed-Daten-Aenderung (CI) | topic_match + llm_judge (Stichprobe 20%) | ~15 Min |
| Manuell (Admin-Dashboard) | Waehlbar | Variabel |
| Vor Release | ab_compare (vollstaendig) | ~30 Min |

---

## 7. Synonym-Woerterbuch (Topic-Match)

Das Woerterbuch mappt semantische Topics auf erkennbare Keywords/Phrasen
in der Antwort. Wird als separate YAML-Datei gepflegt:

```yaml
# tests/rag-eval/topic_synonyms.yaml
topics:
  stickstoff_mangel:
    de: [Stickstoff, Stickstoffmangel, N-Mangel, nitrogen, gelbe untere Blaetter]
    pattern: "(?i)stickstoff|nitrogen|N[- ]?Mangel"

  calcium_mangel:
    de: [Calcium, Calciummangel, Ca-Mangel, neue Blaetter, Triebspitzen]
    pattern: "(?i)calcium|Ca[- ]?Mangel|Bluetenendfaeule"

  ph_lockout:
    de: [pH-Lockout, Lockout, pH zu hoch, pH zu niedrig, nicht verfuegbar]
    pattern: "(?i)pH[- ]?Lockout|nicht.*verfueg|pH.*korrig"

  # ... fuer alle ~80 einzigartigen Topics in benchmark_questions.yaml
```

---

## 8. CLI-Referenz (`tools/rag-eval/eval_rag.py`)

Standalone-Runner ohne Backend-Abhaengigkeit — verbindet sich direkt mit Embedding Service, VectorDB und Ollama.

### Parameter

| Parameter | Default | Beschreibung |
|-----------|---------|-------------|
| `--smoke` | false | Schneller Smoke-Test: bricht beim ersten Fehler ab |
| `--resume` | false | Setzt unterbrochenen Lauf fort (laedt `eval_results_partial.json`, ueberspringt bereits evaluierte Fragen) |
| `--categories` | alle | Nur bestimmte Kategorien evaluieren (z.B. `diagnostik duengung`) |
| `--retrieval-only` | false | Zeigt nur abgerufene Chunks ohne LLM-Generierung (Retrieval-Debugging) |
| `--top-k` | 5 | Anzahl der RAG-Chunks pro Frage |
| `--doc-language` | kein Filter | Chunks nach Sprache filtern: `de`, `en` oder `all` |
| `--prompt-language` | `de` | Sprache des System-Prompts fuer das LLM (`de` oder `en`) |
| `--model` | `gemma3:4b` | Ollama-Modellname |
| `--embedding-url` | `http://localhost:8080` | Embedding Service URL |
| `--ollama-url` | `http://localhost:11434` | Ollama API URL |
| `--vectordb-dsn` | `localhost:5433` | PostgreSQL DSN fuer VectorDB |
| `--output`, `-o` | `eval_results.json` im Eval-Dir | Ausgabepfad fuer Ergebnis-JSON |

### Umgebungsvariablen

Werden als Defaults verwendet wenn kein CLI-Argument gesetzt ist:

| Variable | Default |
|----------|---------|
| `EMBEDDING_SERVICE_URL` | `http://localhost:8080` |
| `VECTORDB_DSN` | `host=localhost port=5433 dbname=kamerplanter_vectors ...` |
| `LLM_API_URL` | `http://localhost:11434` |
| `LLM_MODEL` | `gemma3:4b` |
| `EVAL_DATA_DIR` | `tests/rag-eval/` |

### Typische Workflows

```bash
# Vollstaendiger Benchmark
python tools/rag-eval/eval_rag.py

# Schneller Smoke-Test vor vollem Lauf
python tools/rag-eval/eval_rag.py --smoke

# Unterbrochenen Lauf fortsetzen (z.B. nach Ctrl+C oder Timeout)
python tools/rag-eval/eval_rag.py --resume

# Nur Diagnostik-Fragen mit mehr Chunks
python tools/rag-eval/eval_rag.py --categories diagnostik --top-k 10

# Retrieval debuggen ohne LLM-Kosten
python tools/rag-eval/eval_rag.py --retrieval-only --categories duengung

# Englische Chunks mit englischem Prompt
python tools/rag-eval/eval_rag.py --doc-language en --prompt-language en
```

### Resume-Mechanismus

Bei jedem evaluierten Frage-Ergebnis wird `eval_results_partial.json` geschrieben. Bei `--resume`:
1. Laedt vorherige Ergebnisse aus `eval_results_partial.json`
2. Ueberspringt alle Fragen deren ID bereits evaluiert wurde
3. Mergt alte + neue Ergebnisse fuer den finalen Score
4. Bei `--smoke` wird Resume ignoriert (Smoke ist ohnehin schnell)

---

## 9. Metriken-Dashboard (REQ-009)

Im Admin-Dashboard (oder Grafana) anzeigen:
- RAG-Score Trend (Zeitreihe, letzte 12 Wochen)
- Score pro Kategorie (Balkendiagramm)
- Schwaeachste Fragen (Top-10 Failures)
- A/B-Gewinnrate (RAG vs. Baseline)
- Chunk-Retrieval-Qualitaet (welche Chunks werden am haeufigsten abgerufen)
