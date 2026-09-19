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
| **REQ-012 Stammdaten-Import** | **Nein (gegenstandslos)** | Reiner CSV-Import mit definierten Spalten — die Daten sind bereits strukturiert, es gibt nichts zu extrahieren. |
| **REQ-048 Spezies-Dedup-Ranking** | **Nein (marginal)** | Trigram/Levenshtein ist dort bewusst die Startversion; die benannte Folge-Iteration wäre der vorhandene Embedding-Service, nicht ein zweites Modell. |
| **Intent-Routing / Schnellerfassung aus Freitext** | **Möglich — §5.1** | Exakt Needles Kerndisziplin: grammatikgebundenes JSON, kalibrierte Confidence, LoRA-Finetuning auf eigene Werkzeuge. |
| **REQ-051 Tagebuch-Freitext → Tags/Messwerte/Typ** | **Möglich, nur als Vorschlag — §5.2** | Extraktion plus Enum-Klassifikation auf einem Datensatz, der außer Typ und Freitext keine Pflichtfelder kennt. Die Messwert-Grenze aus REQ-050 §4.3 bleibt bestehen. |
| **REQ-010 Symptom-Freitext → Katalogschlüssel** | **Möglich — §5.3** | Klassifikation gegen einen geschlossenen Katalog (`symptoms`, `shows_symptom`); die Grammatik kann keinen Schlüssel erfinden, den es nicht gibt. |
| **Home-Assistant-Sprachbefehl → MCP-Werkzeug** | **Ausblick — §5.4** | Greenfield: eine Spracheingabe ist in keiner REQ spezifiziert. HA ist im Heimbetrieb laut BM-003 der Normalfall. |

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

Es gibt eine Klasse von Aufgaben, an der Needles Zuschnitt und ein echtes Kamerplanter-Problem
zusammenfallen: **Freitext rein, typisiertes JSON raus, auf Pi-Hardware.** Vier Stellen kommen
dafür in Frage, absteigend nach Tragfähigkeit. Keine davon ersetzt etwas Bestehendes; jede wäre
eine neue, optionale Eingabeart.

### 5.1 Schnellerfassung per Satz → Werkzeugaufruf

„gieße die Tomate in Beet 2" oder „Blattläuse an der Monstera, mittel" wird zu einem fertigen
Aufruf gegen ein Werkzeugschema aus REQ-033. Die Eigenschaften passen auffällig genau:

- Der Werkzeugkatalog **existiert bereits** als Schema-Quelle (56 Werkzeuge, REQ-033 §4.1).
- Die byte-level Grammatik garantiert, dass der Aufruf zum Schema passt — keine JSON-Reparatur,
  keine erfundenen Felder.
- Ein leerer `function_calls` ist eine **Ablehnung**, keine Halluzination. Das deckt sich mit dem
  Grundsatz aus REQ-033 („statt einer halluzinierten Antwort").
- Die kalibrierte Confidence (`llms.txt` §Confidence gating) liefert genau die drei Wege, die eine
  Erfassungsmaske braucht: ausführen, zur Bestätigung vorlegen, ablehnen.
- 8–29 MB laufen neben Backend, ArangoDB und Valkey auf einem Pi, wo ein 12B-Modell nicht läuft.
- LoRA-Finetuning auf die eigenen Werkzeuge ist der dokumentierte Normalfall, nicht der
  Ausnahmefall.

**Einschränkung:** Die Retrieval-Auswahl rendert **Top-5 Werkzeuge pro Zug** (`llms.txt` §Tool
retrieval). Bei 56 Werkzeugen muss entweder die Vorauswahl sitzen, oder Needle bekommt nur eine
kuratierte Teilmenge von fünf bis acht Erfassungs-Werkzeugen zu sehen.

### 5.2 Tagebuch-Freitext → `tags`, `measurements`, `entry_type`

REQ-051 §3.4 ist dafür fast eingeladen: außer Typ und Freitext gibt es **keine** Pflichtfelder,
und das ist ausdrücklich Absicht. `tags` ist eine freie Liste, `measurements` ein offenes Dict
(`height_cm`, `leaf_count`, …). Needles zweite Disziplin ist genau das — getypte Felder aus
unsauberem Text, Klassifikation über Enums für `entry_type`.

**Die Grenze steht schon in der Spezifikation und bleibt gültig:** REQ-050 §4.3 hat bewusst
entschieden, dass `add_plant_diary_entry` **kein** Eingabefeld für Messwerte trägt — „ein Agent,
der die Werte schreiben könnte, könnte sie erfinden". Diese Entscheidung wird nicht dadurch
hinfällig, dass das Modell lokal läuft. Tragfähig ist deshalb ausschließlich der **Vorschlag mit
Bestätigung**: die extrahierten Felder erscheinen vorausgefüllt, die Gärtnerin quittiert. Dann
bleibt die Provenienz „handnotiert" (REQ-051 §3.4) ehrlich, statt still zu einer Modellausgabe zu
werden.

### 5.3 Symptom-Freitext → IPM-Katalogschlüssel

REQ-010 führt eine `symptoms`-Collection mit `shows_symptom`-Kanten, also einen **geschlossenen
Katalog**. Freitext einer Inspektion auf diese Schlüssel abzubilden ist reine Klassifikation über
ein Enum — und dafür ist die Grammatik-Constraint gemacht: das Modell *kann* keinen Schlüssel
ausgeben, den es nicht gibt. Das ist die Fehlerart, die ein großes LLM ohne Constrained Decoding
regelmäßig produziert.

### 5.4 Home-Assistant-Sprachbefehl → MCP-Werkzeug (Ausblick)

BM-003 nennt Home Assistant als „Normalfall" im Heimbetrieb, und HA bringt eine eigene
Voice-Pipeline mit. Ein Intent-Parser von 29 MB auf demselben Pi wäre die fehlende Brücke zwischen
HA-Assist und dem MCP-Server. **Greenfield:** eine Spracheingabe ist in keiner REQ spezifiziert,
Sprache taucht nur in UI-NFR-002 (Barrierefreiheit) auf. Also Ausblick, nicht Nahziel.

### 5.5 Wofür ausdrücklich nicht

Naheliegende Ideen, die bei genauer Prüfung nicht tragen:

| Idee | Warum nicht |
|---|---|
| RAG-Chat, Tipp-Karten, „Warum?"-Buttons (REQ-031) | Keine Textgenerierung. Auch kein Teilersatz. |
| KI-Analyse der Tagebuch-Fotos (REQ-050) | Rein textuell, kein Bild — und bewusst als *externer* Agent entworfen. |
| Stammdaten-Import (REQ-012) | Ist reiner CSV-Import. Bereits strukturiert, es gibt nichts zu extrahieren. |
| RAG-Embeddings ersetzen | `multilingual-e5-large` plus `bge-reranker-v2-m3` sind vorhanden und auf Deutsch belegbar besser. |
| Spezies-Dedup-Ranking (REQ-048 §Stufe 1) | Trigram/Levenshtein ist dort bewusst die Startversion; die benannte „Folge-Iteration" wäre der bestehende Embedding-Service, nicht ein zweites Modell. |

**Für alle vier Fälle gilt dieselbe Reihenfolge:** sie stehen und fallen mit B-1 (Deutsch), und das
ist ungemessen. Fällt der Test aus §6.3 durch, ist nicht das Einsatzfeld falsch gewählt — dann
scheitert es am Tokenizer, und die gesamte Liste ist hinfällig.

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
     eine Anforderung reden — in der Reihenfolge §5.1, §5.2, §5.3. §5.4 setzt zusätzlich eine
     Spracheingabe voraus, die es noch nicht gibt.
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
