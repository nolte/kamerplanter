# Analyse: Docling als Erweiterung des Kamerplanter-Stacks

```yaml
Gegenstand: https://github.com/docling-project/docling (docling-slim 2.129.0, MIT, LF AI & Data)
Datum: 2026-09-19
Frage: Erweitert Docling den in spec/stack.md definierten Stack sinnvoll?
Betroffene Dokumente: spec/stack.md §3.4 (KI-Komponenten, "Begründung ONNX statt PyTorch"),
  REQ-010 (IPM — BVL-Datenquelle), REQ-004 (Bodenanalyse), REQ-012 (CSV-Import),
  REQ-031 (RAG-Wissensbasis), NFR-009 §4.3 (Lizenz-Compliance), NFR-013 (Object-Storage)
Ergebnis: Ja — aber nicht im Laufzeit-Stack. Docling gehört in die Wissens-Werkbank
  (Build-Zeit, scripts/ und CI), nicht als Dienst neben Backend, knowledge-service und
  inference-service.
```

## 1. Was Docling ist

Docling parst Dokumente in eine einheitliche Repräsentation (`DoclingDocument`) und exportiert
sie als Markdown, HTML, JSON oder DocTags. Der Schwerpunkt liegt auf **PDF-Verständnis**:
Seitenlayout, Lesereihenfolge, Tabellenstruktur, Formeln, Bildklassifikation.

| Eigenschaft | Wert | Quelle |
|---|---|---|
| Lizenz | MIT | `LICENSE`, `pyproject.toml` |
| Trägerschaft | LF AI & Data Foundation (ursprünglich IBM Research Zürich) | `README.md`, Autorenliste |
| Version / Stand | `docling-slim` 2.129.0, letzter Commit 2026-09-18 | `pyproject.toml`, `git log` |
| Python | `>=3.10,<4.0`, Klassifizierer bis **3.14** | `pyproject.toml` |
| Eingabeformate | PDF, DOCX, PPTX, XLSX, HTML, EPUB, ODF, E-Mail, LaTeX, Bilder, Audio/Video | `README.md` §Features |
| Ausgabeformate | Markdown, HTML, JSON, DocTags, WebVTT | `README.md` §Features |
| OCR-Engines | RapidOCR (ONNX/OpenVINO/Paddle/Torch), EasyOCR, Tesseract, macOS, Nemotron | `pyproject.toml` §OCR ENGINES |
| OCR-Sprachen | `deu` ist in den Voreinstellungen enthalten | `docling/datamodel/pipeline_options.py:622,675` |
| Basis-Installation | 9 Pakete, ~50 MB | `pyproject.toml` §MINIMAL BASE |
| Betriebsarten | Bibliothek, CLI, API-Server (`docling-serve`), MCP-Server | `README.md` §Features |
| Reife | arXiv-Paper 2408.09869, OpenSSF-Best-Practices-Badge, Production/Stable | `README.md` |

Wichtig für die Bewertung: Das Paket ist seit der `docling-slim`-Umstellung **modular**. Die
schweren Abhängigkeiten sitzen in Extras, nicht im Kern. Dazu §4.

## 2. Wo Kamerplanter heute Dokumente verarbeitet

**Zur Laufzeit: nirgends.** Das ist der erste und wichtigste Befund.

- **REQ-012** ist ausdrücklich „Stammdaten-Import via CSV-Upload" mit definierten Spalten und
  einem eigenen `CsvParser`. Die Daten kommen bereits strukturiert an.
- **NFR-013 §5.2** führt `application/pdf` zwar in der Default-Mime-Whitelist
  (`STORAGE_ALLOWED_MIME_TYPES`), aber keine Kategorie und keine Anforderung liest ein solches
  PDF jemals aus — `attachments` sind faktisch Bilder (Diary-, Pflanzen-, IPM-Fotos).
- **REQ-004** nimmt die Bodenanalyse als vier getippte Skalare entgegen (`soil_ph`, `soil_type`,
  `soil_analysis_date`, `soil_notes`). Kein Laborbericht-Upload, kein Parser.
- **`knowledge-service/app/ingestor.py`** indiziert ausschließlich `*.yaml` aus dem kuratierten
  Korpus. Es gibt keinen zweiten Ingest-Pfad.

Ein Docling-Dienst im Cluster wäre also eine Lösung ohne Problem. Wer ihn dort platziert, baut
eine Fähigkeit, die keine Anforderung abruft.

**Zur Build-Zeit: an mehreren Stellen, nur bisher von Hand.** Das ist der zweite Befund, und er
kehrt das Bild um. Der Wissenskorpus entsteht heute daraus, dass jemand — Mensch oder Agent —
Quellen liest und abtippt:

- `spec/knowledge/products/` — Düngerprodukte (Advanced Nutrients, Plagron u. a.). Die
  autoritative Quelle je Produkt ist ein **Herstellerdatenblatt als PDF**.
- `spec/knowledge/nutrient-plans/` — Düngepläne auf Plagron-Basis. Die Quelle ist die
  **Feed-Chart des Herstellers**: eine PDF-Tabelle.
- **REQ-010 §Offene Abhängigkeiten** nennt ausdrücklich die „Pflanzenschutzmittel-Datenbank
  (BVL/EPA) für Zulassungsstatus" als unerfüllte Datenquelle. Karenzzeiten sind in diesem Projekt
  kein Komfortfeature, sondern die Grundlage des Karenz-Gates vor der Ernte (REQ-010 §5, ADR-001)
  — und das BVL veröffentlicht als PDF und CSV.
- `spec/knowledge/rag/` und die 210 Steckbriefe unter `spec/knowledge/plants/` — heute aus
  Websuche und Fachliteratur zusammengetragen.

## 3. Bewertung je Einsatzfeld

| Einsatzfeld | Docling sinnvoll? | Begründung |
|---|---|---|
| **Herstellerdatenblätter → `spec/knowledge/products/`** | **Ja** | Genau die Aufgabe, für die Docling gebaut ist: PDF mit Tabellen → strukturiertes Markdown/JSON. Wiederholbar, wenn der Hersteller das Datenblatt aktualisiert. |
| **Feed-Charts → `spec/knowledge/nutrient-plans/`** | **Ja** | Feed-Charts sind reine Tabellen. Siehe aber die Tabellen-Einschränkung in §4. |
| **BVL-Zulassungen → Karenzzeit-Stammdaten (REQ-010)** | **Ja, mit Vorbehalt** | Schließt eine in der Spezifikation benannte Lücke. Vorbehalt: Bei rechtlich wirksamen Daten ist eine maschinelle Extraktion ohne Abnahme nicht akzeptabel — das Karenz-Gate blockiert Ernten. Extraktion ja, ungeprüfte Übernahme nein. |
| **RAG-Ingestion aus PDF-Fachliteratur (REQ-031)** | **Denkbar** | `feat-chunking` liefert einen HybridChunker für RAG. Kollidiert aber mit dem Grundsatz des Korpus: die Chunks sind **kuratiert**, nicht geschöpft. Ein PDF-Fließband würde die Qualität senken, die `spec/rag-eval/` gerade absichert. |
| **Bodenanalyse-PDF → REQ-004-Felder** | **Nein (unverhältnismäßig)** | Vier Skalare. Dafür eine Dokumenten-Pipeline samt Modellen in den Laufzeit-Stack zu heben, steht in keinem Verhältnis. |
| **REQ-012 CSV-Import** | **Nein (gegenstandslos)** | Bereits strukturiert. Es gibt nichts zu parsen. |
| **PDF-*Export* (REQ-010 §796, UI-NFR-010 §9.2)** | **Nein (falsche Richtung)** | Docling liest Dokumente, es schreibt keine. Der Compliance-Export braucht einen Renderer (WeasyPrint/ReportLab-Klasse), kein Parsing. |
| **Docling als zweiter MCP-Server** | **Nein** | REQ-033 definiert genau eine MCP-Oberfläche mit Mandantenbindung und Audit. Ein zweiter Server daneben verwässert diese Grenze ohne Gegenwert. |

## 4. Der Konflikt mit einer bestehenden Stack-Entscheidung

`spec/stack.md` §3.4.2 begründet ausdrücklich **ONNX statt PyTorch**: „~10x kleineres Docker
Image (kein 2 GB PyTorch)", schnellerer Kaltstart, CPU-only. Der `inference-service` (DINOv2)
folgt derselben Linie. Das ist keine Nebenbemerkung, sondern eine getroffene und begründete
Entscheidung.

Docling stellt sie im Laufzeitfall infrage, im Build-Fall nicht:

- Das Extra `models-local` zieht `torch`, `torchvision`, `accelerate` und `docling-ibm-models`.
  Der Bündel `standard` enthält es. Wer `pip install docling` naiv in ein Service-Image schreibt,
  holt sich genau die 2 GB, die der Stack bewusst vermieden hat.
- **Es gibt einen leichteren Weg:** Layout ist auch als ONNX-Modell verfügbar
  (`docling-project/docling-layout-heron-onnx`, `stage_model_specs.py:1021`), und die
  Engine-Abstraktion trennt sauber zwischen ONNX und Transformers
  (`models/inference_engines/object_detection/onnxruntime_engine.py`). OCR läuft über
  `feat-ocr-rapidocr-onnx` ebenfalls auf `onnxruntime`.
- **Aber:** ONNX-Engines existieren nur für *object detection*, *image classification* und *VLM*.
  Für die **Tabellenstruktur** (TableFormer) gibt es keine — sie läuft über
  `docling-ibm-models`, also über Torch. Und Tabellen sind exakt das, woraus Feed-Charts,
  Datenblätter und Laborberichte bestehen. Wer Tabellen braucht, braucht Torch.

Daraus folgt die Trennlinie dieser Analyse: **In einem CI-Job oder auf dem Entwicklerrechner ist
Torch belanglos.** Er läuft einmal, erzeugt Markdown, und das Ergebnis wird eingecheckt. Im
Deployment-Stack — dessen Referenzhardware laut BM-003 ein Raspberry Pi sein darf — ist er ein
Ausschlussgrund.

## 5. Was gegen die Adoption spricht — und was nicht

Anders als bei der Needle-Prüfung (`needle-local-model-assessment.md`) gibt es hier **kein
Sprach-Gate**: `deu` steht in den OCR-Voreinstellungen, und die Layout-Analyse ist ohnehin
sprachunabhängig. Auch die üblichen Governance-Einwände greifen nicht: MIT ist nach NFR-009 §4.3
ausdrücklich zugelassen, die Trägerschaft liegt bei der LF AI & Data Foundation, das Projekt ist
aktiv und trägt den OpenSSF-Best-Practices-Badge.

Was bleibt:

1. **Abhängigkeitsgewicht** — siehe §4. Lösbar durch die Build-Zeit-Trennung.
2. **Modelldownloads von Hugging Face** zur ersten Nutzung. Für einen CI-Job ein Cache-Thema,
   kein Datenschutzthema — im Gegensatz zu einem Dienst im Nutzer-Deployment.
3. **Extraktion ist nicht Wahrheit.** Für `products/` und `nutrient-plans/` ist ein Fehler
   ärgerlich; für BVL-Karenzzeiten ist er ein Ernte-Gate, das falsch öffnet oder falsch schließt.
   Maschinelle Extraktion gehört dort vor eine menschliche Abnahme, nicht dahinter.
4. **Der Korpus ist kuratiert, nicht geschöpft.** Docling senkt die Kosten des Zusammentragens,
   nicht die Anforderung an die Kuratierung. Wer das verwechselt, bekommt einen größeren und
   schlechteren Wissensbestand.

## 6. Empfehlung

1. **Aufnehmen — als Werkzeug der Wissens-Werkbank, nicht als Stack-Komponente.** Docling gehört
   in eine Dev-/CI-Abhängigkeitsgruppe neben `scripts/`, **nicht** in die `pyproject.toml` eines
   ausgelieferten Dienstes und nicht in `helm/`.
2. **Keine Änderung an `spec/stack.md` §3.4.** Der Laufzeit-Stack bleibt, wie er ist; die
   ONNX-statt-PyTorch-Entscheidung bleibt unangetastet, weil Docling sie nicht berührt, solange
   es die Cluster-Grenze nicht überschreitet.
3. **Erster Zuschnitt, weil dort das Ergebnis messbar ist:** die Plagron- und
   Advanced-Nutrients-Datenblätter gegen den bereits von Hand erstellten Bestand in
   `spec/knowledge/products/` und `spec/knowledge/nutrient-plans/` laufen lassen. Dieser Bestand
   ist die Referenzlösung — die Extraktionsqualität lässt sich also beziffern statt behaupten,
   genau wie `spec/rag-eval/` es für die RAG-Qualität tut.
4. **Erst danach über REQ-010/BVL reden.** Die Karenzzeit-Quelle ist der wertvollste Fall und
   zugleich der mit der höchsten Schadenshöhe. Sie ist der zweite Schritt, nicht der erste, und
   braucht ein Abnahmeverfahren, bevor irgendein extrahierter Wert ein Ernte-Gate speist.
5. **Nicht tun:** Docling als Dienst deployen, `docling-serve` neben den `knowledge-service`
   stellen, oder seinen MCP-Server neben REQ-033 anbieten.

## 7. Grenzen dieser Prüfung

- **Docling wurde nicht ausgeführt.** Keine Extraktion wurde gemessen, kein Datenblatt getestet.
  Alle Aussagen stammen aus dem geklonten Repository (`pyproject.toml`, `README.md`,
  `docling/models/`, `docling/datamodel/`) und dem Abgleich mit den Spezifikationen dieses Repos.
  Deshalb ist §6.3 als Messung formuliert.
- **Die Tabellenqualität auf deutschen Feed-Charts ist unbekannt.** Dass `deu` in den
  OCR-Voreinstellungen steht, sagt nichts über die Trefferquote auf mehrspaltigen Düngetabellen
  mit Wochenachsen.
- **Die Lizenzen der nachgeladenen Modelle** (`docling-project/*` auf Hugging Face) wurden nicht
  geprüft; Hugging Face war aus der Prüfumgebung nicht erreichbar. MIT gilt belegt für den
  GitHub-Quellcode.
- **`docling-serve` und der MCP-Server** liegen in eigenen Repositories und wurden nicht
  betrachtet — sie sind nach §6.5 ohnehin nicht empfohlen.
