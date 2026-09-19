# Analyse: Cactus Needle 3 als lokales Modell in Kamerplanter

```yaml
Gegenstand: https://github.com/cactus-compute/needle (cactus-needle 3.0.1, Apache-2.0)
Datum: 2026-09-19
Frage: Ist Needle als lokales Modell in Kamerplanter einsetzbar?
Betroffene Spezifikationen: REQ-031 (KI-Assistent/RAG), REQ-033 (MCP-Server), REQ-035, REQ-036,
  REQ-050 (KI-Analyse Tagebuch), REQ-027 (Light-Modus §6.1), BM-003 (Self-Hosted-Einzelnutzer),
  NFR-009 (Dependency-/Lizenz-Management), NFR-011 (Datenschutz)
Ergebnis: Kein Ersatz für den lokalen LLM-Pfad. Ein eng umrissener Nischen-Einsatz ist denkbar
  und wird als Spike vorgeschlagen — mit einem harten Vorab-Gate.
```

## 1. Was Needle tatsächlich ist

Needle 3 ist **kein Chat-LLM**. Das ist keine Randnotiz, sondern die zentrale Designentscheidung,
die die Autoren selbst so benennen: *"we trade general chat capacity to beat models 10x its size
on mobile tool calls"* (README). Die Konsequenz steht im Verhaltensvertrag:

> "Off-topic / unsupported request -> empty `function_calls` (a refusal). **There is no free-text
> fallback.** Always handle the empty case." (`llms.txt` §Behaviour contract)

Belegte Fakten aus dem geklonten Repository:

| Eigenschaft | Wert | Quelle |
|---|---|---|
| Parameter | 29M–121M (Ladder, 2–20 Layer) | `README.md`, `llms.txt` Z. 3 |
| Modellgröße | 8–29 MB Binary; `needle3.cact` ≈ 35 MB | `README.md`, `llms.txt` Z. 3 |
| Quantisierung | 2,125 Bit/Gewicht (Cactus Quants) | `README.md` §Guides |
| `d_model` | 768, 20 Layer Basis | `needle/model/architecture.py:43,46` |
| **Vokabular** | **16 384 SentencePiece-Pieces** | `needle/model/architecture.py:42` |
| Kontextfenster | `max_seq_len` 4096, Sliding Window 1024 | `needle/model/architecture.py:49,67` |
| Fähigkeiten | Tool-Calls, Structured Extraction, Satz-Embedding | `README.md` |
| Embedding-API | `Needle.embed(text) -> list[float]` | `needle/__init__.py:229` |
| Laufzeit | vorkompilierte Shared Library via `ctypes.CDLL` | `needle/__init__.py:105` |
| Bezug von Engine + Gewichten | `hf_hub_download` von Hugging Face zur Laufzeit | `needle/agent/fetch.py:87,110,147` |
| Telemetrie | **standardmäßig an** | `README.md`, `llms.txt` §Telemetry |
| Lizenz (Python-Paket) | Apache-2.0 | `LICENSE`, `pyproject.toml` |
| Reife | Version 3.0.1, Repo-Stand September 2026 | `pyproject.toml` |

Das Python-Paket enthält Inferenz-Anbindung, LoRA-Finetuning (JAX/Flax) und Export. Die eigentliche
Inferenz-Engine ist **nicht** Teil des Apache-2.0-Quellcodes, sondern ein Binärblob, den
`fetch.py` pro Plattform von Hugging Face nachlädt.

## 2. Was Kamerplanter heute an lokaler KI hat

Der lokale Pfad existiert bereits und ist im Light-Modus sogar **erzwungen**:

- `src/knowledge-service/` hält die RAG-Pipeline: `embedding.py`, `vectordb/` (pgvector),
  `reranker.py`, `prompt_engine.py` und vier LLM-Adapter (`llm/ollama.py`, `anthropic.py`,
  `openai_compatible.py`, `interface.py`).
- Default-Konfiguration: `embedding_model = "multilingual-e5-large"`, `llm_model = "gemma3:12b"`
  gegen `http://ollama:11434` (`src/knowledge-service/app/config.py:36,42`).
- REQ-027 §6.1 erzwingt im Light-Modus per `validate_light_mode_ai_config()` einen lokalen
  Provider (`ollama` oder loopback-gebundenes `openai_compatible`); ein Cloud-Provider führt zum
  Hard-Crash, ohne Override-Flag.
- `src/inference-service/` macht dasselbe Muster für Bilder (DINOv2 ViT-S/14 via ONNX Runtime).

**Die Lücke, die real ist:** BM-003 beschreibt als Zielumgebung „Docker Compose auf Raspberry
Pi 4/5, NAS, NUC oder Laptop" mit einem Betriebsprofil „Hobby (~3 GB RAM, mit lokaler KI)" —
und nennt zugleich „ein Raspberry Pi mit 2 GB ist die Untergrenze". Ein `gemma3:12b` ist dort
nicht betreibbar. Light-Modus fordert lokale KI, die Referenz-Hardware kann das Default-Modell
nicht tragen. Diese Spannung ist der einzige Grund, warum ein 29-MB-Modell hier überhaupt
interessant klingt.

## 3. Bewertung je Einsatzfeld

| Einsatzfeld | Needle geeignet? | Begründung |
|---|---|---|
| **REQ-031 Tipp-Karten, Tipp des Tages, „Warum?"-Buttons, Chat** | **Nein** | Alle vier Funktionen liefern generierten deutschen Fließtext. Needle hat per Design keine Textgenerierung. Kein Teilersatz möglich. |
| **REQ-035 Fachbegriff-Glossar, REQ-036 Diagnose-Assistent** | **Nein** | Bauen laut Spezifikation auf REQ-031 als Wissens-Backend auf — dieselbe Sperre. |
| **RAG-Embedding (statt multilingual-e5-large)** | **Nein, aber messbar** | `embed()` existiert, jedoch ohne dokumentierte Dimension, ohne MTEB-Zahlen und ohne jede Mehrsprachigkeitsaussage. Gegen einen deutschen Wissenskorpus mit Hybrid-Search und `bge-reranker-v2-m3` wäre das ein wahrscheinlicher Qualitätsverlust. Immerhin: `spec/rag-eval/` könnte ihn beziffern. |
| **REQ-033 MCP-Server** | **Nein (falsche Seite)** | Kamerplanter ist hier der *Werkzeug-Anbieter*; das LLM sitzt im fremden Client (Claude Desktop, Cursor). Needle wäre nur relevant, wenn Kamerplanter einen eigenen lokalen Agenten mitlieferte — tut es nicht. Zusätzlich: 56 Werkzeuge gegen eine Retrieval-Auswahl von Top-5 pro Zug (`llms.txt` §Tool retrieval). |
| **REQ-050 KI-Analyse von Tagebuch-Einträgen** | **Nein** | Der Befund ist eine diagnostische Beurteilung *mit Bildern*. Needle ist rein textuell und generiert keine Befundtexte. Zudem ist der Ablauf bewusst als *externer* Agent über MCP entworfen. |
| **Intent-Routing / Schnellerfassung aus Freitext** | **Möglich — siehe §5** | Das ist exakt Needles Kerndisziplin: grammatikgebundenes JSON, kalibrierte Confidence, LoRA-Finetuning auf eigene Werkzeuge. |

## 4. Die vier Blocker

**B-1 — Deutsch ist nicht belegt.** Ein 16 384-Pieces-Vokabular ist für ein englischzentriertes
Modell typisch. Weder README, `llms.txt`, noch der Quellcode erwähnen Mehrsprachigkeit auch nur
einmal. Kamerplanter ist durchgehend deutschsprachig: Oberfläche, Wissensbasis
(`spec/knowledge/rag/`), Benchmark-Fragen, Nutzereingaben. Ein Modell, das deutsche Ortsangaben,
Pflanzennamen und Mengenangaben nicht sauber in Argumente füllt, ist hier wertlos — unabhängig
davon, wie gut die englischen Benchmark-Zahlen sind. **Das ist das Gate vor allem Weiteren.**

**B-2 — Keine Textgenerierung.** Das schließt REQ-031, REQ-035 und REQ-036 vollständig aus. Needle
ist keine Antwort auf die BM-003-Lücke aus §2, auch wenn es zunächst so aussieht. Die passende
Antwort dort bleiben kleinere Ollama-Modelle (`gemma3:1b`/`4b`, Qwen-Klasse) — ein Wechsel der
Modellgröße, kein Wechsel der Architektur.

**B-3 — Lieferkette und Datenschutz.** Drei Punkte, alle lösbar, aber keiner ignorierbar:
- Die Inferenz-Engine ist ein **Binärblob** von Hugging Face, nicht der Apache-2.0-Quellcode. Der
  CI-Lizenz-Check aus NFR-009 §4.3 (`pip-licenses`) erfasst genau diesen Teil nicht.
- **Telemetrie ist standardmäßig aktiv.** In einer Light-Modus-Instanz, deren gesamte
  Daseinsberechtigung „nichts verlässt das Heimnetz" ist, wäre das ein Fehler in der
  Voreinstellung. `NEEDLE_TELEMETRY=0` und `DO_NOT_TRACK=1` müssten im Image gesetzt sein, nicht
  in der Dokumentation stehen.
- Gewichte und Engine werden **zur Laufzeit** nachgeladen. Für air-gapped Betrieb müssten
  `NEEDLE3_LIB_PATH` und `HF_HUB_OFFLINE` gesetzt und beide Artefakte ins Image gebacken werden.

**B-4 — Reife.** Version 3.0.1, Veröffentlichung 2026, kein Produktionsnachweis außerhalb der
Herstellerangaben, ein einzelner Anbieter hinter Engine, Gewichten und Hosting-Plattform. Für eine
Randfunktion vertretbar, für einen tragenden Pfad nicht.

## 5. Wo es trotzdem passen könnte

Es gibt genau eine Stelle, an der Needles Zuschnitt und ein echtes Kamerplanter-Problem
zusammenfallen: **Freitext → Werkzeugaufruf auf schwacher Hardware.**

Konkret: „gieße die Tomate in Beet 2" oder „Blattläuse an der Monstera, mittel" wird zu einem
typisierten `add_plant_diary_entry(...)`- bzw. Inspektions-Aufruf. Die Eigenschaften passen
auffällig gut:

- 8–29 MB laufen neben Backend, ArangoDB und Valkey auf einem Pi, wo ein 12B-Modell nicht läuft.
- Die byte-level Grammatik garantiert, dass der Aufruf zum Schema passt — keine JSON-Reparatur.
- Die kalibrierte Confidence (`llms.txt` §Confidence gating) erlaubt genau die drei Wege, die
  eine Erfassungsmaske braucht: ausführen, zur Bestätigung vorlegen, ablehnen.
- Ein leerer `function_calls` ist eine *Ablehnung*, keine Halluzination — das deckt sich mit dem
  Grundsatz aus REQ-033 („statt einer halluzinierten Antwort").
- LoRA-Finetuning auf die eigenen Werkzeuge ist der dokumentierte Normalfall, nicht der
  Ausnahmefall; laut Anbieter hebt es jede Subnetz-Größe um 18–36 Punkte.
- Der Werkzeugkatalog aus REQ-033 existiert bereits als Schema-Quelle.

Das ersetzt nichts Bestehendes. Es wäre eine neue, optionale Eingabeart — und die einzige, für die
Needle die passende Technologie und nicht bloß ein kleineres Modell wäre.

## 6. Empfehlung

1. **Nicht übernehmen** als lokales LLM. Needle ist kein Ersatz für den Ollama-Pfad und löst die
   BM-003-Hardwarelücke nicht.
2. **Keine Spezifikationsänderung** an REQ-031/033/035/036/050 aus diesem Anlass.
3. **Ein Spike, mit B-1 als Gate** (Aufwand ~½ Tag, außerhalb des Produktivcodes):
   - Deutscher Werkzeug-Testsatz: 30–50 Sätze gegen 5 reale MCP-Werkzeugschemata aus REQ-033,
     mit erwarteten Argumenten.
   - Basismodell messen: Exact-Match auf Werkzeugwahl und auf jedes Argument.
   - Abbruchkriterium: Bleibt die Argument-Genauigkeit auf Deutsch unter ~70 %, ist das Thema
     erledigt, und zwar ohne Finetuning-Versuch — ein Modell, das deutsche Entitäten nicht
     erfasst, lernt das nicht aus 50 Beispielen.
   - Bei Erfolg: LoRA auf ~500 generierte deutsche Beispiele, erneut messen, und erst dann über
     eine Anforderung für eine Schnellerfassung reden.
4. **Unabhängig davon verfolgen:** die eigentliche BM-003-Lücke — ein Raspberry-Pi-taugliches
   Default-`llm_model` statt `gemma3:12b`. Das ist der Befund mit dem größeren Nutzen und er hat
   mit Needle nichts zu tun.

## 7. Grenzen dieser Prüfung

Ehrlich benannt, damit niemand mehr hineinliest als belegt ist:

- **Das Modell wurde nicht ausgeführt.** Hugging Face ist aus der Prüfumgebung per Egress-Proxy
  gesperrt; Engine und Gewichte konnten nicht geladen werden. Alle Aussagen stammen aus dem
  Quellcode des geklonten Repositories, aus `README.md` und `llms.txt`.
- **Die Aussage zu Deutsch ist eine begründete Erwartung, keine Messung.** Sie stützt sich auf
  Vokabulargröße und das vollständige Fehlen jeder Mehrsprachigkeitsaussage in Repo und
  Dokumentation — nicht auf einen Testlauf. Genau deshalb ist §6.3 als Messung formuliert.
- **Benchmark-Zahlen wurden nicht verifiziert.** Sie liegen ausschließlich als SVG-Grafiken
  (`assets/benchmarks.svg`) und auf der Herstellerseite vor, in Tabellenform nirgends.
- **Die Lizenz der Engine-Binärdateien und der Gewichte auf Hugging Face wurde nicht geprüft** —
  aus demselben Netzgrund. Apache-2.0 gilt belegt nur für den GitHub-Quellcode.
