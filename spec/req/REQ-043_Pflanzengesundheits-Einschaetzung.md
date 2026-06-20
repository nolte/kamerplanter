# Spezifikation: REQ-043 - Pflanzengesundheits-Einschätzung (bildgestützt)

```yaml
ID: REQ-043
Titel: Pflanzengesundheits-Einschätzung (ganzheitliches Vitalitäts-Assessment, vorzugsweise bildbasiert)
Kategorie: KI & Schädlingsmanagement
Fokus: Beides
Technologie: Python 3.14+, FastAPI, ArangoDB, Celery, ONNX, DINOv2, optional Kindwise-Cloud-API, optional lokales VLM (LLaVA/Qwen2.5-VL/Agri-LLaVA) + RAG (REQ-031), React 19, TypeScript 5.9, MUI 7
Status: Entwurf
Version: 1.0
Abhängigkeit: REQ-038 v1.1 (CV-Pflanzendiagnose — Vision-Erkennungstechnik), REQ-036 v1.0 (KI-Diagnose-Assistent — Symptom-Signal), REQ-010 v1.1 (IPM — Befall-Signal & Treatment-Brücke), REQ-005 (Hybrid-Sensorik — Sensor-Signal), REQ-022 (Pflegeerinnerungen — Pflege-Signal), REQ-029 v1.0 (Adapter-Interface, EXIF/Consent), REQ-029-A v1.2 (Self-Hosted-Inferenz-Infrastruktur), REQ-031 v2.0 (Knowledge-Service / RAG), REQ-025 v1.4 (DSGVO/Consent), REQ-013 v2.0 (PlantInstance/Run), REQ-021 v1.0 (Erfahrungsstufen)
Wird benoetigt von: —
```

## Versionshistorie

| Version | Datum | Änderung |
|---------|-------|----------|
| 1.0 | 2026-06-20 | Initialer Entwurf — leitet aus dem Methodenvergleich `spec/analysis/plant-health-vision-research.md` ein ganzheitliches, fortlaufendes Gesundheits-Assessment ab; definiert Phasen-Strategie (Cloud-Adapter → Self-Hosted-Hybrid) und Multi-Signal-Fusion. <!-- Quelle: spec/analysis/plant-health-vision-research.md --> |
| 1.1 | 2026-06-20 | Offene Punkte (§10) durch fokussierte Recherche geklärt (`spec/analysis/pest-detection-implementation-prep.md`): Kindwise **`plant.health` statt `crop.health`** für Indoor; Konfidenz/Abstention via **Temperature Scaling + Energy-OOD + Risk-Coverage** statt fester Schwelle; CPU-VLM-Erklärungs-Layer machbar (opt-in/async); `deficiencies`/`beneficials`-Stammdaten-Lücke in REQ-010 benannt; Fusion-Gewinn nicht überversprechen (Evidenzlücke). <!-- Quelle: spec/analysis/pest-detection-implementation-prep.md --> |

## 0. Verhältnis zu benachbarten REQs (verbindliche Abgrenzung)

REQ-043 ist das **strategische Dach- und Integrationsdokument** für die Fragestellung „Wie gesund ist meine Pflanze insgesamt — und wie schätze ich das vorzugsweise per Bild ein?". Es ersetzt keine der bestehenden CV-/Diagnose-REQs, sondern **aggregiert** deren Ergebnisse zu einer fortlaufenden Vitalitäts-Einschätzung und liefert die **fundierte Lösungsentscheidung** (Abschnitt 2–3), aus der die konkreten Vision-Bausteine gespeist werden.

| REQ | Leistung | Verhältnis zu REQ-043 |
|-----|----------|------------------------|
| **REQ-038** (CV-Pflanzendiagnose) | Punktuelle Zustandsdiagnose **eines** Problems aus **einem** Blattfoto (Klassifikator + PlantCV-Phänotyp) → Verdachtsliste | **Liefert das primäre Bild-Signal.** REQ-043 konsumiert `plant_diagnosis_requests` (Klassifikationen + Phänotyp-Metriken) als eine Signalquelle. REQ-043 erweitert den von REQ-038 betrachteten Lösungsraum um den **Cloud-API-Pfad (Phase 1)** und die **VLM/RAG-Erklärungsstufe**, die REQ-038 nicht behandelt. |
| **REQ-036** (KI-Diagnose-Assistent) | Geführter Symptom-Katalog-Dialog als einzelne Diagnose-Session | **Liefert das Symptom-Signal.** Eine offene/akute `diagnosis_session` fließt als Faktor in den Gesundheits-Score ein. REQ-043 startet umgekehrt bei kritischem Status einen Diagnose-Dialog-Vorschlag. |
| **REQ-010** (IPM) | Manuelle Inspektionen, Pests/Diseases/Treatments, Karenz-Gate | **Liefert das Befall-Signal** (aktive `inspections`/`treatment_applications`) und ist Ziel der Treatment-Brücke. REQ-043 löst **nie** automatisch Behandlungen aus. |
| **REQ-005** (Hybrid-Sensorik) | VPD/EC/pH/Klima mit Provenienz & Fallback | **Liefert das Sensor-Signal** (Abweichung von Phasen-Zielbereichen) — laut Forschung der entscheidende Multi-Signal-Hebel gegen Mangel-/Krankheits-Verwechslung. |
| **REQ-022** (Pflegeerinnerungen) | Fällige/überfällige Pflege pro Pflanze | **Liefert das Pflege-Signal** (überfällige Gießungen/Düngung als Stress-Indikator). |
| **REQ-029 / REQ-029-A** | **Artbestimmung** („Welche Pflanze ist das?") + Self-Hosted-Inferenz-Infrastruktur | Stellt **wiederverwendete Infrastruktur** (Adapter-Registry, EXIF-Strip, Consent, Inference-Service) bereit. Keine inhaltliche Überschneidung — Art ≠ Gesundheit. |

**Kernunterschied in einem Satz:** REQ-038 beantwortet *„Was fehlt der Pflanze auf diesem Foto?"* (Momentaufnahme), REQ-043 beantwortet *„Wie ist der Gesundheitszustand dieser Pflanze über die Zeit, fusioniert aus allen verfügbaren Signalen?"* (fortlaufendes Assessment) und trifft die **methodische Grundsatzentscheidung**, wie die Bilderkennung dafür realisiert wird.

## 1. Business Case

### 1.1 User Stories

**User Story (Casual User — „Geht's meiner Pflanze gut?"):** „Als Zimmerpflanzen-Besitzer ohne botanisches Wissen möchte ich auf der Pflanzen-Detailseite auf einen Blick eine Gesundheits-Ampel sehen (grün/gelb/rot) — gespeist vor allem aus einem Foto, das ich aufnehme — damit ich ohne Fachkenntnis erkenne, ob ich handeln muss."

**User Story (Foto-zuerst):** „Als Nutzer möchte ich ein Foto meiner Pflanze machen und eine verständliche Einschätzung erhalten (‚wirkt gesund' / ‚Anzeichen von Stress an den unteren Blättern' / ‚mögliches Schädlingsproblem'), ohne selbst Symptome benennen zu müssen — denn die Bilderkennung soll die Hauptarbeit übernehmen."

**User Story (Grower — Trend statt Momentaufnahme):** „Als Grower möchte ich den Gesundheitsverlauf einer Pflanze über Wochen sehen (Vitalitäts-Score + Bild-Kennzahlen wie verfärbte/nekrotische Blattfläche), damit ich eine Verschlechterung früh erkenne, bevor sie eskaliert."

**User Story (Multi-Signal-Vertrauen):** „Als erfahrener Nutzer möchte ich, dass die Einschätzung nicht nur vom Foto abhängt, sondern auch meine Sensorwerte (VPD/EC/pH), die Pflegehistorie und offene IPM-Befälle berücksichtigt — damit ein Stickstoffmangel nicht fälschlich als Krankheit gewertet wird und umgekehrt."

**User Story (Datenschutz/Self-Hosting):** „Als Betreiber einer Self-Hosted-Instanz möchte ich die Gesundheits-Einschätzung vollständig lokal betreiben können, ohne dass Pflanzenfotos meine Infrastruktur verlassen und ohne Pro-Foto-Kosten — eine Cloud-Erkennung darf nur eine bewusst aktivierte, einwilligungspflichtige Option sein."

**User Story (schneller Start):** „Als Produktverantwortlicher möchte ich frühzeitig eine breit abgesicherte Gesundheits-Erkennung anbieten können, ohne erst ein eigenes ML-Modell trainieren zu müssen — und später auf eine self-hosted Lösung migrieren, ohne dass sich für die Nutzer die Bedienung ändert."

**User Story (Vorsicht/Verbindlichkeit):** „Als Nutzer möchte ich klar erkennen, dass die Gesundheits-Einschätzung eine Vermutung mit Unsicherheit ist und keine gesicherte Diagnose — damit ich keine teuren oder pflanzenschädlichen Fehlbehandlungen auf Basis einer überkonfidenten KI-Aussage durchführe."

### 1.2 Problemstellung und Zielsetzung

Eine belastbare Pflanzengesundheits-Einschätzung **allein aus einem Foto** ist nach aktuellem Forschungsstand (2025/2026) deutlich schwieriger, als Labor-Benchmarks suggerieren. Drei Befunde prägen jede sinnvolle Lösung (Details in Abschnitt 2 und `spec/analysis/plant-health-vision-research.md`):

1. Der **Reliability Gap**: Bild-Klassifikatoren brechen von Labor (>99 %) auf reale Bedingungen (~32 %) ein und bleiben dabei **überkonfident** — Labor-Genauigkeiten sind irreführend.
2. Krankheit, Schädlingsbefall und Nährstoffmangel sind **visuell oft nicht trennscharf** — selbst für Fachleute. Reine Bildmerkmale reichen für eine Differenzierung häufig nicht.
3. Die wirksamsten Gegenmittel sind **multimodale Fusion** (Bild + Kontext/Sensorik: +10–21 Prozentpunkte) und **Human-in-the-Loop** — also genau die Assets, die Kamerplanter bereits besitzt (RAG-Wissensbasis, Sensordaten, Pflanzen-Kontext).

Zielsetzung von REQ-043 ist daher **nicht** ein überkonfidenter „Diagnose-Automat", sondern ein **fortlaufendes, konfidenz-gewichtetes Vitalitäts-Assessment**, das das Bild als primäres, aber nicht alleiniges Signal nutzt, weitere vorhandene Signale fusioniert und das Ergebnis stets als **Einschätzung mit Disclaimer und Mensch-in-der-Schleife** ausgibt.

## 2. Lösungsraum & Methodenvergleich (Entscheidungsgrundlage)

<!-- Quelle: spec/analysis/plant-health-vision-research.md (Mehrquellen-Web-Recherche, Stand Juni 2026) -->

Dieser Abschnitt ist die fachliche Grundlage der Lösungsentscheidung in Abschnitt 3. Zahlen sind dem Recherchebericht entnommen; Anbieter-Selbstauskünfte und schwach belegte Werte sind als solche markiert.

### 2.1 Der beherrschende Faktor: der Reliability Gap

Die aktuellste Cross-Domain-Studie (Frontiers in Plant Science, 2026) zeigt für einen typischen PlantVillage→PlantDoc-Transfer:

- Accuracy bricht von **99,73 % (Labor) auf 32,05 % (Feld)** ein (−67,7 PP).
- Das Modell bleibt **überkonfident** (Ø vorhergesagte Konfidenz 79,76 % trotz nahezu zufälliger Treffer).
- **Keine** Standard-Gegenmaßnahme schließt die Lücke: Temperature Scaling, Selective Prediction, Domain Adaptation (max. 36,6 %), OOD-Rejection (AUROC ≈ 0,61 ≈ Zufall), Ensembles (bestes DINOv2-Ensemble 43,8 %). Stärkere self-supervised Backbones (DINOv2) helfen am meisten, lösen das Problem aber nicht.

**Konsequenz für REQ-043:** Konfidenz-Kalibrierung, Abstention bei Unsicherheit und Disclaimer sind **nicht optional**, sondern konstitutiv. Labor-Benchmark-Zahlen dürfen weder im Marketing noch in der UI als Erwartung kommuniziert werden.

### 2.2 Die vier grundlegenden Lösungsansätze

**Ansatz A — Kommerzielle Cloud-API.**
Genau **ein** Anbieter ist für diesen Use-Case produktionsreif, breit abdeckend und EU-ansässig: **Kindwise / Plant.id „Plant.Health"** (HQ Brno/Prag). Deckt Krankheit + Schädling + abiotischen Stress über **548 Klassen** ab, Anbieterangabe **>73 % korrekte Diagnose in Top-3** (Selbstauskunft, kein unabhängiger Benchmark), Credit-Preis **€0,01–0,05/Diagnose**, Art.-28-AVV (Stand 01.07.2024), REST/JSON. Einschränkung: Bilder werden **mind. 6 Monate** gespeichert (vor Anonymisierung), konkreter Serverstandort öffentlich nicht namentlich genannt → im AVV zu verifizieren. Alternativen sind ungeeignet: Pl@ntNet-Disease zu eng, Plantix B2B-only/crop-fokussiert ohne öffentliche Preise, Google Vertex/Azure erfordern teures Eigen-Training, Nyckel nur 5 grobe Klassen, Flora Incognita ohne Health-Modul.

**Ansatz B — Self-Hosted CNN/ViT-Klassifikator.**
Reine PlantVillage-CNNs sind „in the wild" untauglich (Background-Bias: ein Modell auf nur 8 Hintergrund-Pixeln erreicht 49 % statt 2,6 % Zufall). Tragfähig nur mit **self-supervised Foundation-Backbone (DINOv2, Apache-2.0)** + in-the-wild-Daten (PlantWild-Baseline 67,2 %, PlantDoc als Fine-Tuning) + eigenen Nutzerbildern. **Dies ist exakt der in REQ-038 spezifizierte Pfad.** CPU-Inferenz via ONNX Runtime für Lightweight-Varianten problemlos (einstellige ms, keine GPU nötig).

**Ansatz C — Multimodales LLM / Vision-Language-Model (VLM).**
Cloud-VLMs (GPT-4o, Claude, Gemini) sind **Zero-Shot schwach** (~56 %), Few-Shot/Fine-Tuned stark (73–98 %), aber ohne Spezialisierung unzuverlässig; sie **halluzinieren** und können abiotischen Stress nicht zuverlässig von Krankheit trennen. Stärke: natürliche Sprache, Kontext, Treatment-Erklärung. Lokale offene VLMs (LLaVA-7B, Qwen2.5-VL-7B ~16–24 GB VRAM, domänenspezifisch **Agri-LLaVA**, 221 Schädlings-/Krankheitstypen) ermöglichen Self-Hosting mit GPU. **Allein** ist ein VLM als Erkenner zu unzuverlässig — wertvoll ist es als **Erklärungs-Stufe**.

**Ansatz D — Hybrid (Vision-Backbone + RAG-(V)LM).**
Belegtes State-of-the-Art-Muster: **Vision-Modell perzipiert → RAG-gestütztes (V)LM erklärt** (z. B. RAG-augmented YOLOv8 für Kaffee). Trennt Perzeption (spezialisierter, kalibrierbarer Erkenner) von Erklärung (sprachlich, kontextuell, halluzinations-gedämpft durch abgerufenes Wissen). Höchster Integrationsaufwand, aber bestes Genauigkeits-/Erklärbarkeits-Profil und voll self-hostbar. Nutzt mit der vorhandenen RAG-Wissensbasis (REQ-031) und den Sensordaten genau die Kamerplanter-Assets, die laut Forschung den größten Hebel bilden.

### 2.3 Vergleichstabelle

Bewertung: ●●● = stark/gut, ●● = mittel, ● = schwach/problematisch.

| Kriterium | **A: Cloud-API** (Kindwise) | **B: Self-Hosted CNN/ViT** (DINOv2 + in-the-wild, = REQ-038) | **C: VLM/LLM** (Cloud o. lokal) | **D: Hybrid** (Vision + RAG-(V)LM) |
|---|---|---|---|---|
| **Genauigkeit** | ●●● >73 % Top-3 (Anbieter), breit annotiert | ●● Lab >99 %, Feld ~32–67 % (Reliability Gap) | ●● Zero-Shot ~56 %, Few-Shot/FT 73–98 % | ●●● best-of-both: spezialisierte Erkennung + erklärende Einordnung |
| **Kosten** | ●● €0,01–0,05/Diagnose, kein Eigen-Training | ●●● ~null/Inferenz nach Training | ● Cloud-Token bzw. ●● GPU lokal | ●● GPU-Infrastruktur, kein Per-Call |
| **Datenschutz/DSGVO** | ●● EU-Sitz + AVV, aber Upload an Dritt + 6-Mon.-Speicherung | ●●● Daten bleiben im System | Cloud ● / lokal ●●● | ●●● Daten bleiben im System |
| **Offline-Fähigkeit** | ● erfordert Konnektivität | ●●● voll offline (CPU genügt) | Cloud ● / lokal ●●● (GPU) | ●●● voll offline (GPU) |
| **Wartungsaufwand** | ●●● Anbieter wartet Modell | ●● eigenes (Re-)Training, Datenpflege | lokal ● (GPU/Updates) | ● höchster (zwei Komponenten + Wissensbasis) |
| **Erklärbarkeit** | ●● Confidence + Knowledge-Base + Follow-up-Fragen | ● Klassen-Wahrscheinlichkeit, ggf. Grad-CAM | ●●● natürliche Sprache, Kontext, Treatment | ●●● erklärend + lokalisiert + RAG-gestützt |
| **Integrationsaufwand** | ●●● REST/JSON, sofort nutzbar | ●● ONNX-Inferenzdienst (vorhanden, REQ-029-A) | ●● Cloud-SDK / lokaler Serving-Stack | ● höchster (Vision + RAG + (V)LM-Pipeline) |
| **Abdeckung (Krankheit/Schädling/Mangel)** | ●●● alle drei + abiotischer Stress (548 Klassen) | ●● v. a. Krankheit; Mangel nur über Spezial-Klassen | ●● breit per Wissen, Mangel-vs-Krankheit unsicher | ●●● breit + RAG-Kontext, Mangel-Differenzierung via Multi-Signal |

### 2.4 Fachliche Knackpunkte (für alle Ansätze gültig)

- **Differenzialdiagnose Mangel ↔ Krankheit ↔ Schädling ↔ abiotischer Stress** ist der härteste Knoten und visuell oft nicht auflösbar. → Nur über **Multi-Signal-Fusion** (Sensorik, Pflege-/Düngehistorie, Kontext) praktikabel reduzierbar.
- **Überkonfidenz**: Modelle (CNN wie VLM) geben hohe Konfidenz auch bei falscher Klasse. → Kalibrierung + Abstention zwingend.
- **Frühstadien** sind schwer erkennbar; ein „unauffällig"-Ergebnis ist kein Gesundheits-Beweis. → Konservative Formulierung in der UI.
- **Nährstoffmangel-Erkennung** erreicht in Studien zwar hohe Werte (90–98 %), aber nur **isoliert** auf getrennten Datensätzen — die eigentliche Differenzierung gegen Krankheit wird dort nicht gelöst.

## 3. Lösungsentscheidung & Phasen-Strategie

**Kein einzelner Ansatz ist optimal.** REQ-043 entscheidet sich — konsistent zum bestehenden Projektmuster (REQ-029-A: Cloud-Fallback + Self-Hosted-Primär) — für eine **Phasen-Strategie** mit durchgängiger **Adapter-Abstraktion**, sodass der Wechsel der Erkennungstechnik die Nutzerbedienung nicht verändert.

### 3.1 Phase 1 — Schneller, datenschutzkonformer Produktwert: Cloud-Adapter (opt-in)

- **Entscheidung:** Ein **`KindwiseHealthAdapter`** (Ansatz A) als **standardmäßig deaktivierter, einwilligungspflichtiger** Cloud-Adapter im bestehenden Adapter-Registry-Muster (REQ-029 §3.4). Liefert breite, gepflegte Abdeckung ohne ML-Eigenbetrieb.
- **Verbindliche Leitplanken:**
  - **EXIF/Metadaten serverseitig beim Ingest strippen** (zusätzlich clientseitig), bevor ein Byte die Anwendung verlässt — GPS in EXIF ist personenbezogen, und API-Uploads strippen EXIF **nicht** automatisch.
  - **Granularer Consent** (neuer Zweck `health_assessment_cloud`, REQ-025) als Gate; analog zum bestehenden Consent-Middleware-Muster (HIBP/Sentry/Enrichment).
  - AVV mit Kindwise, Serverstandort verifizieren, 6-Monats-Speicherung transparent im Datenschutzhinweis.
  - Ausgabe als **konfidenz-gewichtete Einschätzung mit Disclaimer**; Kindwise-„follow-up questions" als Multi-Signal-Verfeinerung nutzbar.

### 3.2 Phase 2 — Datenschutz-souveräner Self-Hosted-Hybrid (Zielarchitektur)

Architektur nach dem belegten Muster **„Vision perzipiert → RAG-(V)LM erklärt"** (Ansatz D), aufbauend auf den bereits spezifizierten Bausteinen:

1. **Erkennungs-Stufe (Vision):** der **`CvDiagnosisAdapter` aus REQ-038** (DINOv2-Backbone + PlantDoc/in-the-wild-Fine-Tuning + PlantCV-Phänotyp). REQ-043 fügt hier **keine** neue Erkennungstechnik hinzu, sondern konsumiert REQ-038.
2. **Erklärungs-Stufe (RAG-(V)LM):** optionales **lokales VLM** (LLaVA-7B / Qwen2.5-VL-7B / Agri-LLaVA, ~16–24 GB VRAM) gekoppelt an die **bestehende RAG-Wissensbasis** (REQ-031, `spec/knowledge/rag/`). Das (V)LM erklärt den fusionierten Befund in natürlicher Sprache und dämpft Halluzination durch abgerufenes Wissen. Bei fehlender GPU bleibt diese Stufe aus; das Assessment funktioniert dann ohne sprachliche Erklärung (Graceful Degradation).
3. **Multi-Signal-Fusion (der Genauigkeits-Hebel):** der eigentliche Neubeitrag von REQ-043 — siehe Abschnitt 4.

### 3.3 Querschnittsprinzipien (für beide Phasen verbindlich)

- **Adapter-Abstraktion / Default-Privacy:** Health-Vision ist ein austauschbarer Adapter (Cloud Kindwise ⇄ Self-Hosted REQ-038-CV). Self-Hosted ist Default; Cloud ist ein opt-in-Upgrade. Light-Modus/On-Prem laufen rein lokal.
- **Human-in-the-Loop + Konfidenz/Abstention:** kalibrierte Konfidenz anzeigen; bei niedriger Konfidenz **abstain** („keine sichere Einschätzung — bitte manuell prüfen") statt überkonfidenter Falschaussage. Nutzer-Feedback („trifft zu / trifft nicht zu") wird als Adaptions-/Trainingssignal gespeichert (analog adaptivem Lernen der CareReminderEngine, REQ-022).
- **Disclaimer-Pflicht:** durchgängig „Einschätzung", nie „gesicherte Diagnose". Besonders bei Cannabis (rechtliche Sensibilität) und bei Pflanzenschutz-/Karenz-Bezug. Eine Gesundheits-Einschätzung löst **nie** automatisch ein Treatment aus und umgeht **nie** das Karenz-Gate (REQ-010).

## 4. Zielarchitektur

### 4.1 Signal-Fusion-Übersicht

```
                         ┌─────────────────────────────────────────────┐
   Foto (Nutzer)  ─────► │  Health-Vision-Adapter (austauschbar)        │
                         │   Phase 1: KindwiseHealthAdapter (Cloud)     │ ─┐
                         │   Phase 2: CvDiagnosisAdapter (REQ-038)      │  │  Bild-Signal
                         └─────────────────────────────────────────────┘  │  (Klassen + Phänotyp)
                                                                           ▼
   REQ-036 Diagnose-Sessions ──► Symptom-Signal ─────────►┌──────────────────────────┐
   REQ-005 Sensorik (VPD/EC/pH) ─► Sensor-Signal ────────►│  HealthAssessmentEngine  │──► health_status
   REQ-010 IPM Inspektionen ─────► Befall-Signal ────────►│  (gewichtete Fusion,     │     (Score 0–100,
   REQ-022 Pflege überfällig ────► Pflege-Signal ────────►│   Konfidenz, Abstention) │      Ampel, Trend,
   REQ-038 Phänotyp-Trend ───────► Trend-Signal ─────────►└──────────────────────────┘      Faktoren)
                                                                           │
                                          optional (Phase 2, GPU) ─────────▼
                                          RAG-(V)LM-Erklärungsstufe (REQ-031) ──► natürlichsprachliche Einordnung
```

### 4.2 Health-Vision-Adapter-Interface

Wiederverwendung der `IdentificationAdapterRegistry` (REQ-029 §3.4). REQ-043 definiert einen schmalen Health-Vertrag, den **beide** Phasen erfüllen:

```python
from abc import abstractmethod
from pydantic import BaseModel, Field


class HealthFinding(BaseModel):
    """Ein erkannter Gesundheits-Befund aus dem Bild-Signal."""
    label: str
    category: str  # 'disease' | 'pest' | 'deficiency' | 'abiotic' | 'healthy'
    common_name: str
    confidence: float = Field(ge=0.0, le=1.0)
    matched_disease_key: str | None = None   # gegen REQ-010 gemappt
    matched_pest_key: str | None = None


class HealthVisionResult(BaseModel):
    """Vereinheitlichtes Ergebnis der Bild-Erkennungsstufe (Cloud ODER self-hosted)."""
    is_plant: bool = True
    is_healthy_estimate: bool | None = None     # separates 'is_healthy'-Signal, falls verfügbar
    findings: list[HealthFinding] = []
    phenotype_metrics: dict | None = None        # nur Phase 2 (REQ-038 PlantCV)
    adapter_key: str = ""
    source: str = ""                              # 'cloud_kindwise' | 'local_cv'
    inference_time_ms: int = 0
    disclaimer: str = (
        "Nur eine Einschätzung der Bilderkennung — keine gesicherte Diagnose. "
        "Bitte bei Unsicherheit fachlich bestätigen."
    )


class HealthVisionAdapter:
    """Gemeinsamer Vertrag für Cloud- und Self-Hosted-Health-Erkennung.

    Phase 1: KindwiseHealthAdapter  (data_access/external/kindwise_health_adapter.py)
    Phase 2: delegiert an REQ-038 CvDiagnosisAdapter
    """
    adapter_key: str
    requires_consent: str | None  # z. B. 'health_assessment_cloud' (Cloud) bzw. None (lokal)

    @abstractmethod
    async def assess_health(
        self, image_data: bytes, *, affected_plant_part: str = "whole", language: str = "de"
    ) -> HealthVisionResult: ...
```

### 4.3 HealthAssessmentEngine (Fusion)

Die Engine ist der Kern-Neubeitrag. Sie kombiniert das Bild-Signal mit den vorhandenen Kontext-Signalen zu einem `health_status`.

```python
CONFIDENCE_ABSTAIN = 0.35   # darunter: keine belastbare Bild-Aussage → "unsicher"
WEIGHTS = {                  # konfigurierbar; Summe normalisiert
    "image": 0.40,          # Bild-Signal (primär — "vorzugsweise bildbasiert")
    "sensor": 0.20,         # Abweichung von Phasen-Zielbereichen (REQ-005)
    "ipm": 0.20,            # aktive Inspektionen/Befall (REQ-010)
    "care": 0.10,           # überfällige Pflege (REQ-022)
    "symptom": 0.10,        # offene Diagnose-Session (REQ-036)
}


class HealthAssessmentEngine:
    """Fusioniert Bild- und Kontext-Signale zu einem Vitalitäts-Score mit Konfidenz.

    Liefert NIE eine verbindliche Diagnose. Bei dominanter Unsicherheit
    (Bild-Konfidenz < CONFIDENCE_ABSTAIN und keine starken Kontext-Signale)
    wird `status_class = "unknown"` zurückgegeben (Abstention).
    """

    def assess(
        self,
        *,
        vision: "HealthVisionResult | None",
        sensor_deviations: list[dict],
        active_ipm: list[dict],
        overdue_care: list[dict],
        open_symptom_session: dict | None,
        phenotype_trend: dict | None,
    ) -> "HealthAssessment": ...
        # 1. Pro Signal einen Teil-Score (0–1, gesund→1) + Vorhandensein berechnen.
        # 2. Gewichtete, auf vorhandene Signale renormalisierte Fusion → score 0–100.
        # 3. Ampel ableiten: green ≥ 70, yellow 40–69, red < 40, unknown bei Abstention.
        # 4. Faktoren-Aufschlüsselung (welches Signal trägt wie bei) für Erklärbarkeit.
        # 5. Gesamt-Konfidenz aus Signal-Konfidenzen + Anzahl übereinstimmender Signale.
```

Wenn das Bild-Signal fehlt (kein Foto vorhanden), arbeitet die Engine rein kontextbasiert (Sensorik/IPM/Pflege) — das Foto ist *vorzugsweise*, nicht *zwingend*. Übereinstimmende Signale (z. B. Bild „Chlorose untere Blätter" + Sensor „EC unter Ziel") erhöhen die Konfidenz und adressieren die Mangel-vs-Krankheit-Differenzierung aus §2.4.

## 5. Datenmodell (ArangoDB)

### 5.1 Neue Document Collection: `health_assessments`

Persistiert jede Einschätzung als Zeitpunkt-Snapshot (für Verlauf/Trend).

```json
{
  "_key": "health_20260620_a1b2c3",
  "tenant_key": "tenant_personal_anna",
  "user_key": "user_anna",
  "plant_instance_key": "plant_anna_monstera_01",
  "planting_run_key": null,
  "status_class": "yellow",                 // green | yellow | red | unknown
  "score": 58,                              // 0–100, null bei unknown
  "confidence": 0.62,                       // Gesamt-Konfidenz der Fusion
  "trigger": "user_photo",                  // user_photo | scheduled | sensor_alert | manual
  "vision": {
    "source": "local_cv",                   // cloud_kindwise | local_cv | none
    "adapter_key": "local_cv_classifier",
    "is_healthy_estimate": false,
    "cv_diagnosis_request_key": "cvdiag_20260620_x9",   // Verweis auf REQ-038-Request
    "top_finding": {
      "label": "leaf_chlorosis_lower", "category": "deficiency",
      "common_name": "Chlorose untere Blätter", "confidence": 0.41
    }
  },
  "contributing_signals": [
    { "signal": "image",   "weight": 0.40, "sub_score": 0.45, "present": true,
      "detail": "Verfärbung untere Blätter, Konfidenz 0.41" },
    { "signal": "sensor",  "weight": 0.20, "sub_score": 0.30, "present": true,
      "detail": "EC 1.1 mS unter Ziel 1.4–1.6 (REQ-005)" },
    { "signal": "ipm",     "weight": 0.20, "sub_score": 1.00, "present": true,
      "detail": "kein aktiver Befall" },
    { "signal": "care",    "weight": 0.10, "sub_score": 0.60, "present": true,
      "detail": "Düngung 4 Tage überfällig (REQ-022)" },
    { "signal": "symptom", "weight": 0.00, "sub_score": null, "present": false, "detail": null }
  ],
  "llm_explanation": null,                   // optional Phase 2 (RAG-(V)LM)
  "suggested_next_step": "diagnosis_session", // diagnosis_session | ipm_inspection | adjust_feeding | none
  "image_hash": "sha256:...",                // Bild nicht persistiert
  "image_deleted_at": "2026-06-20T14:30:02Z",
  "disclaimer": "Nur eine Einschätzung — keine gesicherte Diagnose.",
  "created_at": "2026-06-20T14:30:00Z"
}
```

**Indexes:** Persistent auf `tenant_key`, `plant_instance_key`, `created_at`, `status_class`.

### 5.2 Eingebettetes Feld auf `plant_instances`: `latest_health`

Denormalisierter Schnellzugriff für Listen/Dashboard (vermeidet teure Aggregation pro Render):

```json
{
  "latest_health": {
    "assessment_key": "health_20260620_a1b2c3",
    "status_class": "yellow", "score": 58, "confidence": 0.62,
    "assessed_at": "2026-06-20T14:30:00Z"
  }
}
```

### 5.3 Neue Edge Collections

```aql
// health_assessment_of (health_assessments → plant_instances / planting_runs)
//   Dual-Support analog REQ-013 v2.0

// health_assessment_used_cv (health_assessments → plant_diagnosis_requests)
//   Verknüpft das Bild-Signal mit dem zugrunde liegenden REQ-038-Request

// health_assessment_flagged (health_assessments → diseases / pests)
//   Optional: wenn ein Befund gegen REQ-010-Stammdaten gemappt wurde
//   Felder: confidence: float, category: string, confirmed: bool
```

### 5.4 AQL-Beispiel: Gesundheitsverlauf einer Pflanze

```aql
FOR a IN health_assessments
  FILTER a.tenant_key == @tenant_key
     AND a.plant_instance_key == @plant_instance_key
     AND a.status_class != "unknown"
  SORT a.created_at ASC
  RETURN { at: a.created_at, score: a.score, status: a.status_class, confidence: a.confidence }
```

## 6. Backend-API

Tenant-scoped unter `/api/v1/t/{tenant_slug}/health/`. JWT + Tenant-Membership.

| Methode | Pfad | Beschreibung | Consent |
|---------|------|-------------|---------|
| `GET` | `/status` | Verfügbarkeit: welcher Vision-Adapter aktiv (cloud/local/none)? Buttons ein/aus | — |
| `POST` | `/plants/{plant_key}/assess` | Neue Einschätzung; optional `image` (multipart). Ohne Bild rein kontextbasiert | `health_assessment_cloud` *nur* wenn Cloud-Adapter aktiv |
| `GET` | `/plants/{plant_key}/latest` | Aktuelle Einschätzung (`latest_health`) | — |
| `GET` | `/plants/{plant_key}/history` | Verlauf (Zeitreihe Score/Status) | — |
| `POST` | `/assessments/{key}/feedback` | „trifft zu / trifft nicht zu" + optionale Notiz (Human-in-the-Loop-Signal) | — |
| `GET` | `/overview` | Gesundheits-Übersicht aller Pflanzen des Tenants (für Dashboard, sortiert nach Dringlichkeit) | — |

```python
@router.post("/plants/{plant_key}/assess")
async def assess_plant_health(
    tenant_slug: str,
    plant_key: str,
    image: UploadFile | None = File(None, description="optional JPEG/PNG, max 5 MB"),
    affected_plant_part: str = Form("whole"),
    language: str = Form("de"),
    user=Depends(get_current_user),
    service=Depends(get_health_assessment_service),
) -> dict:
    """Erstellt eine fusionierte Gesundheits-Einschätzung.

    Bild ist OPTIONAL ('vorzugsweise bildbasiert', nicht zwingend). Cloud-Vision
    erfordert Consent 'health_assessment_cloud'; self-hosted/lokal nicht.
    EXIF wird vor jeder Verarbeitung entfernt (REQ-029 §5.4). Antwort trägt
    IMMER einen Disclaimer.
    """
    ...
```

## 7. Frontend-Integration

| Komponente / Seite | Integration | Erfahrungsstufe (REQ-021) |
|---|---|---|
| **`HealthStatusBadge`** | Ampel + Score auf `PlantInstanceCard` (Listen) und Detail-Header | alle |
| **`HealthAssessmentDialog`** | „Gesundheit prüfen" → Foto-Erfassung (wiederverwendet aus REQ-029 §4.1) + Ergebnis | alle |
| Disclaimer-Banner | **Immer sichtbar**, prominent (Querschnittsprinzip §3.3) | alle |
| Faktoren-Aufschlüsselung | `contributing_signals` als verständliche Liste („Foto: Verfärbung; Sensor: EC zu niedrig") | Intermediate/Expert; Beginner nur Top-Faktor |
| **`HealthTrendChart`** | Score-/Status-Verlauf auf der Detailseite (Brücke zu REQ-007/REQ-038-Phänotyp) | Intermediate/Expert |
| Nächster-Schritt-CTA | `suggested_next_step` → Button „Diagnose-Dialog starten" (REQ-036) / „Inspektion" (REQ-010) / „Düngung anpassen" | alle |
| Feedback-Buttons | „Trifft zu / Trifft nicht zu" am Ergebnis (HITL) | alle |
| **`HealthOverviewSection`** | Dashboard (REQ-009/REQ-022): Pflanzen nach Gesundheit sortiert, rote zuerst | alle |
| Konfidenz-Darstellung | Beginner: Ampel hoch/mittel/niedrig; Intermediate+: Prozent | gestuft |

**Light-Modus (REQ-027):** Wie REQ-036 nicht verfügbar (braucht Pflanzen-Kontext, tenant-scoped) — Hinweis „Anmelden, um Gesundheits-Einschätzung zu nutzen".

### 7.1 i18n-Keys (Auszug, `pages.health.*`)

```json
{
  "pages": {
    "health": {
      "title": "Gesundheit",
      "statusGreen": "Wirkt gesund",
      "statusYellow": "Anzeichen von Stress",
      "statusRed": "Braucht Aufmerksamkeit",
      "statusUnknown": "Keine sichere Einschätzung",
      "disclaimer": "Dies ist eine Einschätzung der Bilderkennung und keine gesicherte Diagnose. Bitte prüfe den Befund, bevor du behandelst.",
      "assessButton": "Gesundheit prüfen",
      "contributingFactors": "Das fließt in die Einschätzung ein",
      "feedbackHelp": "War diese Einschätzung hilfreich?",
      "nextStepDiagnosis": "Diagnose-Dialog starten",
      "lowConfidence": "Die Bilderkennung ist sich nicht sicher. Bitte prüfe die Pflanze manuell."
    }
  }
}
```

## 8. Sicherheit & Datenschutz (REQ-025, NFR-007, NFR-011)

| Aspekt | Umsetzung |
|--------|-----------|
| **Consent** | Neuer Zweck `health_assessment_cloud` — **nur** erforderlich, wenn der Cloud-Adapter (Phase 1) aktiv ist. Self-Hosted-Pfad ohne externen Consent. |
| **EXIF-Stripping** | Wiederverwendung REQ-029 §5.4, doppelt (Frontend + Backend), **vor** jeder Verarbeitung — kritisch, da API-Uploads EXIF nicht automatisch strippen. |
| **Bild-Persistenz** | Bilddaten werden **nicht** dauerhaft gespeichert (`image_deleted_at`); nur Hash + Ergebnis + Faktoren bleiben. |
| **Drittland/AVV (Phase 1)** | Kindwise = Auftragsverarbeiter (Art. 28), EU-Sitz; 6-Monats-Bildspeicherung transparent machen; Serverstandort im AVV verifizieren. |
| **Retention** | `health_assessments` unterliegt NFR-011-Retention; Default-Löschfrist konfigurierbar. |
| **Default-Privacy** | `health_assessment_enabled=False`; Self-Hosted-Adapter ist Default, Cloud opt-in. |
| **Audit** | Cloud-Aufrufe erscheinen im `ai_audit_log` (REQ-031) ohne Klartext-PII. |
| **Disclaimer/Haftung** | Jede API-Antwort und UI-Anzeige trägt den Einschätzungs-Disclaimer; automatisierter Test prüft, dass `disclaimer` nie leer ist. |

## 9. Akzeptanzkriterien

### 9.1 Definition of Done

- [ ] **`HealthVisionAdapter`-Vertrag** definiert; `KindwiseHealthAdapter` (Phase 1) und Delegation an REQ-038-`CvDiagnosisAdapter` (Phase 2) implementieren ihn; `/status` meldet den aktiven Adapter, ohne Adapter bleibt die App voll funktionsfähig.
- [ ] **`HealthAssessmentEngine`** fusioniert mindestens Bild-, Sensor-, IPM-, Pflege- und Symptom-Signal gewichtet, renormalisiert auf vorhandene Signale und liefert `score`, `status_class`, `confidence` und `contributing_signals`.
- [ ] **Abstention:** Bei Bild-Konfidenz < `CONFIDENCE_ABSTAIN` und schwachen Kontext-Signalen wird `status_class = "unknown"` zurückgegeben — **keine** überkonfidente Aussage.
- [ ] **Bild ist optional:** `assess` funktioniert ohne Foto rein kontextbasiert; mit Foto wird das Bild-Signal mit Gewicht 0.40 (Default) einbezogen.
- [ ] **Multi-Signal-Differenzierung:** Übereinstimmung Bild + Sensor (z. B. Chlorose + niedriger EC) erhöht die Konfidenz und wird in `contributing_signals` nachvollziehbar.
- [ ] **`health_assessments`-Collection** + `latest_health`-Embed + Edges (`health_assessment_of`, `health_assessment_used_cv`, `health_assessment_flagged`) angelegt; Verlauf abfragbar.
- [ ] **REQ-038-Brücke:** Im Self-Hosted-Pfad wird das Bild-Signal über einen REQ-038-`plant_diagnosis_request` erzeugt und via `health_assessment_used_cv` verknüpft.
- [ ] **Kein Auto-Treatment:** Eine Einschätzung erzeugt höchstens einen `suggested_next_step`/Treatment-**Vorschlag**; das Karenz-Gate (REQ-010) wird nie umgangen.
- [ ] **Disclaimer immer präsent** in jeder API-Antwort und UI-Anzeige (automatisierter Test).
- [ ] **Consent + EXIF:** Cloud-Pfad erfordert `health_assessment_cloud`; EXIF wird doppelt entfernt; Bilddaten nicht persistiert.
- [ ] **Frontend:** `HealthStatusBadge`, `HealthAssessmentDialog`, `HealthTrendChart`, `HealthOverviewSection` implementiert; Erfahrungsstufen (REQ-021) respektiert; Light-Modus blockiert mit Hinweis.
- [ ] **Human-in-the-Loop:** Feedback („trifft zu/nicht zu") wird gespeichert und steht als Adaptionssignal zur Verfügung.
- [ ] **Default-Privacy:** `health_assessment_enabled=False`; Self-Hosted-Adapter Default, Cloud opt-in.
- [ ] **i18n** DE+EN vollständig (`pages.health.*`).
- [ ] **Pytest** für Engine-Fusion (inkl. Abstention, fehlendes Bild, Signal-Übereinstimmung), Adapter-Dispatch, Cleanup; **Vitest** für Badge/Dialog/TrendChart/Overview.

### 9.2 Testszenarien

**Szenario 1: Foto-gestützte Einschätzung mit Signal-Übereinstimmung**
```
GIVEN: Self-Hosted-Adapter aktiv; Pflanze hat EC 1.1 mS (Ziel 1.4–1.6, REQ-005), Düngung 4 Tage überfällig (REQ-022)
WHEN:  Nutzer fotografiert die Pflanze; REQ-038-CV meldet "Chlorose untere Blätter" (Konfidenz 0.41, category=deficiency)
THEN:
  - status_class = "yellow", score im mittleren Bereich, confidence erhöht durch Bild+Sensor-Übereinstimmung
  - contributing_signals listet Bild (deficiency), Sensor (EC zu niedrig), Pflege (überfällig)
  - suggested_next_step = "adjust_feeding" (nicht "ipm_inspection")
  - Disclaimer vorhanden; KEIN Treatment automatisch
```

**Szenario 2: Abstention bei unsicherem Bild**
```
GIVEN: Foto mit unruhigem Hintergrund; Bild-Konfidenz aller Findings < CONFIDENCE_ABSTAIN; keine starken Kontext-Signale
WHEN:  assess läuft
THEN:
  - status_class = "unknown", score = null
  - UI zeigt "Keine sichere Einschätzung — bitte manuell prüfen"
  - Verweis auf Diagnose-Dialog (REQ-036) / manuelle Inspektion (REQ-010)
```

**Szenario 3: Einschätzung ohne Foto (rein kontextbasiert)**
```
GIVEN: Kein Foto; aktiver Spinnmilben-Befall aus IPM-Inspektion (REQ-010), VPD außerhalb Ziel
WHEN:  assess ohne image aufgerufen (trigger=sensor_alert)
THEN:
  - Bild-Signal present=false; Fusion renormalisiert auf Sensor + IPM
  - status_class = "red" (aktiver Befall dominiert), suggested_next_step = "ipm_inspection"
```

**Szenario 4: Cloud-Adapter ohne Consent**
```
GIVEN: KindwiseHealthAdapter aktiv, Consent 'health_assessment_cloud' NICHT erteilt
WHEN:  Nutzer ruft assess mit Foto auf
THEN:
  - HTTP 403 / Consent-Aufforderung; kein Bild verlässt die Anwendung
  - alternativ Hinweis auf rein lokale/ kontextbasierte Einschätzung
```

**Szenario 5: Verlauf & Trend**
```
GIVEN: 6 Einschätzungen derselben Pflanze über 4 Wochen, Score fallend 78 → 41
WHEN:  Nutzer öffnet HealthTrendChart
THEN:
  - fallender Trend sichtbar; rote/gelbe Phasen markiert; unknown-Punkte ausgespart
```

**Szenario 6: Feature deaktiviert**
```
GIVEN: health_assessment_enabled == false
WHEN:  Frontend lädt PlantInstance-Seite
THEN:  /status meldet kein aktiver Adapter; Badge/Buttons ausgeblendet; App voll funktionsfähig
```

**Szenario 7: Disclaimer-Invariante**
```
WHEN:  beliebige assess-Antwort
THEN:  Feld disclaimer ist nie leer (automatisierter Test über alle Pfade: cloud/local/none/unknown)
```

## 10. Offene Punkte

> Mehrere dieser Punkte wurden durch die fokussierte Recherche **`spec/analysis/pest-detection-implementation-prep.md`** (gemeinsam mit REQ-044) geklärt; Verweise unten. Verbleibende Aktions-Items dort in §10.

- **Gewichtungs-Kalibrierung → präzisiert (Prep §6.2):** Die Default-`WEIGHTS` bleiben begründete Startannahme. Wichtig: **quantifizierte** Multi-Signal-Fusion-Gewinne fehlen in der Literatur (Evidenzlücke) → den Fusionsvorteil **nicht überversprechen**; datengestützt mit Feedback-Signal nachkalibrieren.
- **Score-Skala vs. Ampel:** unverändert offen — v1.0 zeigt Beginnern nur die Ampel; numerischer Score (0–100) nach Nutzertests prüfen.
- **RAG-(V)LM-Erklärungsstufe → geklärt (Prep §7):** CPU-machbar als **„Sekunden-pro-Bild"-Feature** (Qwen2.5-VL-3B-Q4 / Moondream2 / SmolVLM2), opt-in/asynchron mit **Graceful Degradation**; interaktiv → GPU. VLM = **Erklärer, nie Erkenner**; RAG dämpft Halluzination, garantiert sie aber nicht.
- **Konfidenz/Abstention → geklärt (Prep §6):** **Temperature Scaling + Energy-OOD-Gate + klassenweise Schwelle über Risk-Coverage-Kurve auf Feld-Kalibrierungsdaten** (statt fester Schwelle); explizite **`beneficial`/`unknown`-Klasse**; Conformal Prediction erst Phase 2 (≥~1000 Feld-Kalibrierbeispiele, SSBC).
- **Proaktive geplante Assessments → präzisiert (Prep §8):** Celery-Beat-Task analog REQ-022; bevorzugt Re-Evaluierung vorhandener Galerie-Fotos (REQ-034) statt automatischer Aufnahme. Detail-Spec v2.
- **Kindwise-Benchmark → geklärt (Prep §5):** Für Indoor ist **`plant.health`** das richtige Produkt (548 Klassen, „houseplants and ornamentals"), nicht `crop.health`. AVV öffentlich geklärt; kritisch: Trainingsnutzung ohne Opt-out + keine EU-Residenz-Garantie. Eigener Stichproben-Test + 9 Vor-Vertrags-Fragen (Prep §5.3).
- **`deficiencies`/`beneficials`-Stammdaten → geklärt (Prep §8):** REQ-010 um eigene **`deficiencies`-** und **`beneficials`-Collections** ergänzen; bis dahin `category=deficiency`/`beneficial` Slug-basiert ohne `matched_*_key`.

---

**Hinweise für RAG-Integration:**
- Keywords: Pflanzengesundheit, Gesundheits-Einschätzung, Vitalität, Health-Score, Ampel, Multi-Signal-Fusion, Reliability Gap, Bilderkennung, Kindwise, Plant.Health, DINOv2, VLM, RAG, Konfidenz, Abstention, Human-in-the-Loop, Disclaimer, EXIF, Consent
- Verknüpfung: REQ-038 (CV-Diagnose, Bild-Signal), REQ-036 (Symptom-Signal), REQ-010 (IPM/Befall-Signal), REQ-005 (Sensor-Signal), REQ-022 (Pflege-Signal), REQ-029/029-A (Adapter/Infra), REQ-031 (RAG-(V)LM), REQ-025 (DSGVO)
- Fachbegriffe: Reliability Gap, Differenzialdiagnose, Überkonfidenz, Kalibrierung, Out-of-Distribution, multimodale Fusion, Phänotyp-Metriken
- Lösungsentscheidung: Phasen-Strategie — Phase 1 Cloud-Adapter (Kindwise, EU, opt-in, Consent) → Phase 2 Self-Hosted-Hybrid (DINOv2-Vision aus REQ-038 + RAG-(V)LM) mit Multi-Signal-Fusion; Self-Hosted ist Default (Default-Privacy)
- Quelle des Methodenvergleichs: `spec/analysis/plant-health-vision-research.md`
