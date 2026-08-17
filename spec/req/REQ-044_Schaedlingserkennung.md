# Spezifikation: REQ-044 - Bildbasierte Schädlingserkennung

```yaml
ID: REQ-044
Titel: Bildbasierte Schädlingserkennung (Direkt-Detektion + Schadbild/Symptom)
Kategorie: KI & Schädlingsmanagement
Fokus: Beides
Technologie: Python 3.14+, FastAPI, ArangoDB, Celery, ONNX Runtime (quantisierte Detektoren + Tiling), optional Kindwise-Cloud-API (crop.health/insect.id), optional lokales VLM (LLaVA/Qwen2.5-VL/Agri-LLaVA) + RAG (REQ-031), React 19, TypeScript 5.9, MUI 7
Status: Entwurf
Version: 1.1 (Erfassungsverweis auf REQ-052 umgehängt)
Abhängigkeit: REQ-052 v1.0 (Bilderfassung — Profil `recognition`), REQ-010 v1.1 (IPM — Pests/Inspections/Treatments, Karenz-Gate, Ziel der Befund-Brücke), REQ-043 v1.0 (Health-Fusion — konsumiert das Schädlings-Bild-Signal), REQ-038 v1.1 (CV-Pflanzendiagnose — geteilte Vision-/Tiling-Infrastruktur), REQ-029 v1.0 (Adapter-Interface, EXIF/Consent), REQ-029-A v1.2 (Self-Hosted-Inferenz-Infrastruktur, ONNX), REQ-031 v2.0 (Knowledge-Service / RAG für Erklärungs-Layer), REQ-025 v1.4 (DSGVO/Consent), REQ-013 v2.0 (PlantInstance/Run), REQ-021 v1.0 (Erfahrungsstufen)
Wird benoetigt von: —
```

## Versionshistorie

| Version | Datum | Änderung |
|---------|-------|----------|
| 1.0 | 2026-06-20 | Initialer Entwurf — leitet aus dem Methodenvergleich `spec/analysis/pest-detection-research.md` eine dedizierte Schädlingserkennung mit zwei Modi (Direkt-Detektion + Schadbild) ab; definiert Self-Hosted-First-Phasen-Strategie, Tiling-Pflicht, Abstention und Einspeisung als Bild-Signal in IPM/Health ohne Auto-Treatment. <!-- Quelle: spec/analysis/pest-detection-research.md --> |
| 1.1 | 2026-06-20 | Offene Punkte (§10) durch fokussierte Recherche geklärt (`spec/analysis/pest-detection-implementation-prep.md`): **Modellwahl korrigiert — YOLO entfällt (AGPL-3.0), RF-DETR-S/D-FINE (Apache-2.0)**; **Cloud-Produkt korrigiert — `plant.health` statt `crop.health` für Indoor**; Architektur-Präzisierung **zwei Domänen** (on-leaf Few-Shot-Klassifikation via DINOv2 / Gelbtafel RF-DETR+SAHI); Abstention-Schwelle als Tag-1-Default + Risk-Coverage-Verfahren. <!-- Quelle: spec/analysis/pest-detection-implementation-prep.md --> |

## 0. Verhältnis zu benachbarten REQs (verbindliche Abgrenzung)

REQ-044 ist die **dedizierte Spec für die bildbasierte Erkennung von Schädlingen** — sowohl des Schädlings selbst auf dem Foto (Modus 1) als auch indirekt über sein Schadbild (Modus 2). Sie erzeugt ein **Schädlings-Bild-Signal**, das in bestehende REQs einspeist, und trifft die methodische Grundsatzentscheidung, **wie** diese Erkennung realisiert wird.

| REQ | Leistung | Verhältnis zu REQ-044 |
|-----|----------|------------------------|
| **REQ-010** (IPM) | Manuelle Inspektionen, Pests/Diseases/Treatments, Karenz-Gate, Stammdaten | **Ziel der Befund-Brücke.** REQ-044 mappt erkannte Schädlinge gegen `pests`-Stammdaten und schlägt höchstens eine `inspection` vor. REQ-044 löst **nie** ein `treatment_application` aus und umgeht **nie** das Karenz-Gate. |
| **REQ-043** (Health-Fusion) | Multi-Signal-Vitalitäts-Assessment | **Konsument des Signals.** Ein bestätigter Schädlingsbefund verstärkt das IPM-/Befall-Signal in der `HealthAssessmentEngine`. REQ-043 bleibt das Dach-Assessment; REQ-044 liefert eine spezialisierte Signalquelle. |
| **REQ-038** (CV-Pflanzendiagnose) | Punktuelle Krankheits-/Mangel-Diagnose aus einem Blattfoto (Klassifikator + PlantCV) | **Geteilte Infrastruktur, andere Aufgabe.** REQ-038 erkennt Krankheit/Mangel; REQ-044 erkennt Schädlinge/Schadbild. Beide teilen Vision-Inferenz (REQ-029-A) und den **Tiling-Baustein** (§4.3). REQ-044 ergänzt small-object-Object-Detection, die REQ-038s Klassifikation nicht leistet. |
| **REQ-029 / REQ-029-A** | Artbestimmung + Self-Hosted-Inferenz-Infrastruktur | **Wiederverwendete Infrastruktur** (Adapter-Registry, EXIF-Strip, Consent, ONNX-Inference-Service). Keine inhaltliche Überschneidung. |
| **REQ-031** (Knowledge/RAG) | RAG-Wissensbasis | **Optionaler Erklärungs-Layer.** Liefert dem optionalen VLM den Wissenskontext zur Erklärung/Differenzierung. |

**Kernunterschied in einem Satz:** REQ-038 fragt *„Welche Krankheit/welcher Mangel auf diesem Blatt?"*, REQ-043 fragt *„Wie gesund ist die Pflanze insgesamt?"*, REQ-044 fragt *„Ist hier ein Schädling — sichtbar als Insekt oder erkennbar an seinem Schadbild — und welcher?"* und trifft die methodische Grundsatzentscheidung für die Schädlingserkennung.

## 1. Business Case

### 1.1 User Stories

**User Story (Casual User — „Was krabbelt da?"):** „Als Zimmerpflanzen-Besitzer möchte ich ein Foto von kleinen Tierchen oder Schäden an meiner Pflanze machen und erfahren, ob das ein Schädling ist und welcher — ohne den Namen kennen zu müssen — damit ich weiß, ob ich handeln muss."

**User Story (Schadbild ohne sichtbares Insekt):** „Als Nutzer sehe ich Gespinste, klebrigen Belag oder Saugschäden, aber kein Insekt — ich möchte trotzdem eine Einschätzung erhalten, welcher Schädling dahinterstecken könnte, denn die Tiere sind oft zu klein oder versteckt."

**User Story (Grower — Früherkennung):** „Als Grower möchte ich Spinnmilben, Thripse oder Trauermücken früh erkennen, bevor sich eine Population aufbaut — auch wenn die einzelnen Tiere winzig sind."

**User Story (Nützling nicht verwechseln):** „Als erfahrener Nutzer möchte ich, dass die Erkennung Nützlinge (Marienkäfer-Larve, Florfliege, Raubmilbe) nicht fälschlich als Schädling meldet — sonst bekämpfe ich meine eigenen Helfer."

**User Story (Datenschutz/Self-Hosting):** „Als Betreiber einer Self-Hosted-Instanz möchte ich die Schädlingserkennung vollständig lokal betreiben, ohne dass Fotos meine Infrastruktur verlassen und ohne Pro-Foto-Kosten — Cloud-Erkennung nur als bewusst aktivierte, einwilligungspflichtige Option."

**User Story (Vorsicht/Verbindlichkeit):** „Als Nutzer möchte ich klar erkennen, dass die Schädlings-Erkennung eine Einschätzung mit Unsicherheit ist — damit ich keine unnötige oder pflanzenschädliche Behandlung auf Basis einer überkonfidenten KI-Aussage durchführe."

### 1.2 Problemstellung und Zielsetzung

Bildbasierte Schädlingserkennung ist nach Forschungsstand (2025/2026, Details `spec/analysis/pest-detection-research.md`) deutlich schwieriger, als Labor-Benchmarks suggerieren. Drei Befunde prägen jede sinnvolle Lösung:

1. **Small-Object-Problem:** Schädlinge belegen in realistischen In-the-wild-Benchmarks nur Bruchteile eines Prozents der Bildfläche (AgriPest Ø 0,16 %); tiefe Detektoren übersehen so kleine Objekte systematisch. Genau Kamerplanters Indoor-Schädlinge (Spinnmilben, Thripse, Trauermücken) sind winzig.
2. **Reliability-Gap:** Lab-Genauigkeit (>95 %) bricht im Feld drastisch ein (kommerziell belegt: Kindwise crop.health 93 % → 66 % Top-3 auf realen Bildern). Realistisch erreichbar sind eher **~63–71 % mAP** auf In-the-wild-Benchmarks.
3. **Verwechslungsgefahr:** Schädling ↔ Nützling ↔ Krankheit ↔ Nährstoffmangel sind visuell oft nicht trennscharf.

Zielsetzung von REQ-044 ist daher **kein** überkonfidenter „Schädlings-Automat", sondern eine **konfidenz-gewichtete Schädlings-Einschätzung** mit zwei sich ergänzenden Modi (Direkt-Detektion + Schadbild), **Tiling** gegen das Small-Object-Problem, **Abstention** bei Unsicherheit, **Human-in-the-Loop** und durchgängigem **Disclaimer** — eingespeist als Signal in IPM/Health, nie als automatische Behandlung.

## 2. Lösungsraum & Methodenvergleich (Entscheidungsgrundlage)

<!-- Quelle: spec/analysis/pest-detection-research.md (Mehrquellen-Web-Recherche, adversarial verifiziert, Stand Juni 2026) -->

### 2.1 Beherrschende Faktoren

- **Small-Object-Detection** ist der zentrale Engpass für Modus 1 *und* (auf Canopy-Ebene) für Modus 2. **Image-Tiling/Slicing** (hochauflösendes Bild → Kacheln → Detektion pro Kachel → Box-Merge) ist die etablierte, nachweislich wirksame Gegenmaßnahme und damit **Pflicht-Baustein**.
- **Reliability-Gap:** realistisch ~63–71 % mAP@0.5 in-the-wild (AgriPest: Cascade R-CNN 70,83 %, FPN 70,20 %, SSD512 63,38 %; Pest24: YOLOv3 ~63,54 %). → Kalibrierung, Abstention, Disclaimer, HITL sind konstitutiv. Keine „>90 %"-Erwartung in UI/Marketing.
- **Datensatz-Lücke:** AgriPest/Pest24/IP102 sind **feldkultur-fokussiert** und decken Kamerplanters Indoor-Saugschädlinge nicht ab → eigenes Indoor-Datenset + Few-Shot/Finetuning nötig.

### 2.2 Die vier grundlegenden Lösungsansätze

**Ansatz A — Cloud-API (Kindwise `plant.health` / insect.id).** EU-orientiert (FlowerChecker s.r.o., Brno/CZ), DSGVO-beworben, Credit-Preise €0,05–0,01/Call. **Korrektur v1.1:** Für Indoor-Zierpflanzen ist **`plant.health`** das richtige Produkt (548 Klassen, „houseplants and ornamentals"), **nicht `crop.health`** (nur 23 essbare Feldkulturen — das „93→66 %"-Argument betraf crop.health). insect.id deckt >14.000 Taxa inkl. Milben ab (Modus 1). **Einschränkungen:** AVV ist öffentlich geklärt (T&C Art. 20), aber 6-Monats-Bildspeicherung **mit Trainingsnutzung ohne dokumentiertes Opt-out**, Hosting Google Cloud + DigitalOcean (US-Konzerne) ohne EU-Residenz-Garantie; plant.health-Indoor-Abdeckung der 5 Zielschädlinge **unbelegt** (keine öffentliche Klassenliste). Details + 9 Vor-Vertrags-Fragen: `spec/analysis/pest-detection-implementation-prep.md` §5.

**Ansatz B — Self-Hosted Direkt-Detektor (Modus 1).** Kleiner, ONNX-exportierbarer Detektor + Tiling, trainiert auf eigenem Indoor-Datenset (Few-Shot gegen AgriPest/Pest24-Backbones). Voll offline, keine Pro-Foto-Kosten. **Korrektur v1.1:** **YOLO (Ultralytics v8/v10/v11) entfällt — AGPL-3.0** zieht einen self-hosted HTTP-Inferenzdienst ins Copyleft (§13). Empfehlung: **RF-DETR-S (Apache-2.0, DINOv2-Backbone)** als 1. Wahl, **D-FINE-S/N (Apache-2.0)** als compute-sparsame Alternative, RT-DETRv2-S für Reife. Aufwand: eigenes Datenset + Training; CPU-only-Inferenz großer Modelle unpraktikabel → klein + asynchron via Celery (INT8 nur für CNNs sinnvoll, bei DETR zurückhaltend). **Präzisierung:** Der robuste **on-leaf-Default ist eine Few-Shot-DINOv2-Klassifikation** (kein Detektor; nutzt REQ-029-A-Embedding-Service); der RF-DETR-Detektor ist primär der **Gelbtafel-/Zähl-Pfad**. Details: `spec/analysis/pest-detection-implementation-prep.md` §2–4.

**Ansatz C — Self-Hosted Schadbild-Detektor (Modus 2).** Symptom-orientiert (Fraß/Saugschäden, Gespinste, Honigtau, Verfärbung), artenagnostischer, hängt nicht von der Sichtbarkeit winziger Insekten ab; mit Tiling. Robustester *Einstieg*, aber kein Ersatz für die Artbestimmung.

**Ansatz D — VLM / VLM+RAG (Erklärungs-Layer).** Konzeptionell geeignet zur Erklärung und Schädling↔Nützling↔Krankheit↔Mangel-Differenzierung, aber **nur als Erklärungs-/Triage-Layer** — Zero-Shot-VLMs brechen unter Domain-Shift dramatisch ein (CLIP bis 6,77 % auf PlantDoc). Niemals alleiniger Erkenner.

### 2.3 Vergleichstabelle

Bewertung: ●●● = stark/gut, ●● = mittel, ● = schwach/problematisch.

| Kriterium | **A: Cloud** (Kindwise) | **B: Direkt-Detektor** (Modus 1) | **C: Schadbild** (Modus 2) | **D: VLM/RAG** (Erklärung) |
|---|---|---|---|---|
| **Genauigkeit** | ●● intern 85–93 %, real ~66 % Top-3 | ●● ~63–71 % mAP in-the-wild | ●● machbar mit Tiling | ● Zero-Shot bricht unter Domain-Shift ein |
| **Kosten** | ●● €0,01–0,05/Call | ●●● ~null/Inferenz | ●●● ~null/Inferenz | ●● GPU lokal / Token Cloud |
| **Datenschutz/DSGVO** | ●● EU-beworben, Upload an Dritt + AVV | ●●● bleibt im System | ●●● bleibt im System | lokal ●●● / Cloud ● |
| **Offline** | ● Konnektivität nötig | ●●● voll offline (async) | ●●● voll offline (async) | lokal ●● / Cloud ● |
| **Wartung** | ●●● Anbieter | ●● Datenset + Training | ●● Tiling-Pipeline + Training | ● GPU + RAG-Kopplung |
| **Erklärbarkeit** | ●● Symptome/Treatment | ● Klasse + Box | ●● Symptom lokalisiert | ●●● Sprache + RAG |
| **Integration** | ●●● REST/JSON | ●● ONNX + Tiling + Datenset | ●● ONNX + Tiling | ● höchster |
| **Abdeckung Indoor-Schädlinge** | ●● breit, aber **unbelegt** | ● Datensätze decken Indoor **nicht** ab | ●● artenagnostischer | ●● breit per Wissen, unsicher |

### 2.4 Fachliche Knackpunkte (für alle Ansätze gültig)

- **Small-Object** → Tiling Pflicht; ein „nichts gefunden" ist kein Beweis für Schädlingsfreiheit (konservative Formulierung).
- **Überkonfidenz** → Kalibrierung + Abstention zwingend.
- **Nützling-Verwechslung** → Nützlinge als eigene Klasse/Abstention behandeln, nie als Schädling melden.
- **Indoor-Datenlücke** → eigenes Datenset über Nutzerbilder + HITL aufbauen.

## 3. Lösungsentscheidung & Phasen-Strategie

**Kein einzelner Ansatz ist optimal.** REQ-044 entscheidet sich — konsistent zu REQ-043/REQ-029-A — für eine **Self-Hosted-First-Phasen-Strategie** mit durchgängiger **Adapter-Abstraktion**. Self-Hosted ist Default, Cloud ist opt-in. Ergebnis ist immer ein **Schädlings-Bild-Signal**, nie eine automatische Behandlung.

### 3.1 Phase 1 — Robuster, artenagnostischer Einstieg + Cloud-Opt-in

- **`LocalPestSymptomAdapter`** (Ansatz C, Modus 2, Default): symptom-orientierte Erkennung mit **Tiling**, liefert ein Signal auch ohne sichtbares Insekt.
- **`KindwisePestAdapter`** (Ansatz A, optional): **standardmäßig deaktiviert, einwilligungspflichtig** (neuer Consent-Zweck `pest_detection_cloud`, REQ-025). EXIF doppelt gestrippt; AVV/EU-Hosting vertraglich verifiziert; Indoor-Eignung vor Produktivnahme empirisch testen.

### 3.2 Phase 2 — Self-Hosted Direkt-Detektor (Zielarchitektur)

- **`LocalPestDetectorAdapter`** (Ansatz B, Modus 1): kleiner, **quantisierter ONNX-Detektor** + Tiling; asynchron via Celery (Multi-Sekunden-Latenz pro Bild akzeptabel, da kein Live-Video).
- **Daten:** eigenes **Indoor-Schädlings-Datenset** (Spinnmilben, Thripse, Trauermücken, Schmierläuse, Weiße Fliege, Blattläuse) aus Nutzerbildern (mit Consent) + Few-Shot/Finetuning gegen AgriPest/Pest24/IP102-Backbones.

### 3.3 Querschnittsprinzipien (für beide Phasen verbindlich)

- **Adapter-Abstraktion / Default-Privacy:** austauschbarer Adapter; Self-Hosted Default, Cloud opt-in; Light-Modus rein lokal/blockiert.
- **Tiling Pflicht** für beide Modi.
- **Human-in-the-Loop + Konfidenz/Abstention:** kalibrierte Konfidenz; bei niedriger Konfidenz **abstain** statt überkonfidenter Falschklasse; Nutzer-Feedback („Schädling bestätigt / falsch / war Nützling") als Adaptions-/Trainingssignal und zum Aufbau des Indoor-Datensets.
- **VLM+RAG nur als Erklärungs-Layer** (optional, GPU-abhängig, Graceful Degradation).
- **Kein Auto-Treatment / Karenz-Gate unangetastet** (REQ-010); REQ-044 erzeugt höchstens einen `suggested_next_step`.
- **Disclaimer-Pflicht** durchgängig; besonders bei Cannabis.

## 4. Zielarchitektur

### 4.1 Signal-Übersicht

```
                         ┌─────────────────────────────────────────────┐
   Foto (Nutzer)  ─────► │  Tiling-Vorverarbeitung (Pflicht, §4.3)      │
                         └─────────────────────────────────────────────┘
                                              │  Kacheln
                                              ▼
                         ┌─────────────────────────────────────────────┐
                         │  PestDetectionAdapter (austauschbar)         │
                         │   Default:  LocalPestSymptomAdapter (Modus 2)│
                         │   Phase 2:  LocalPestDetectorAdapter (Modus 1)│──► PestDetectionResult
                         │   Opt-in:   KindwisePestAdapter (Cloud)      │     (findings, Boxen,
                         └─────────────────────────────────────────────┘      confidence, Abstention)
                                              │
              optional (GPU) ────────────────▼
              RAG-(V)LM-Erklärungs-Layer (REQ-031) ──► natürlichsprachliche Einordnung + Nützling-Differenzierung
                                              │
                                              ▼
   ┌──────────────────────┐   bestätigter Befund   ┌──────────────────────┐
   │ REQ-010 IPM          │ ◄──── suggested ─────── │ REQ-043 Health-Fusion │
   │ (inspection-Vorschlag,│        next_step        │ (Befall-Signal-Verstärkung)│
   │  pests-Mapping)       │                         └──────────────────────┘
   └──────────────────────┘
```

### 4.2 PestDetectionAdapter-Interface

Wiederverwendung der `IdentificationAdapterRegistry` (REQ-029 §3.4).

```python
from abc import abstractmethod
from pydantic import BaseModel, Field


class BoundingBox(BaseModel):
    x: float; y: float; width: float; height: float   # normalisiert 0–1


class PestFinding(BaseModel):
    """Ein erkannter Schädlings- oder Schadbild-Befund."""
    label: str
    category: str            # 'pest' | 'beneficial' | 'symptom' | 'unknown'
    common_name: str
    confidence: float = Field(ge=0.0, le=1.0)
    mode: str                # 'direct' | 'symptom'
    bounding_box: BoundingBox | None = None
    matched_pest_key: str | None = None   # gegen REQ-010 pests gemappt


class PestDetectionResult(BaseModel):
    """Vereinheitlichtes Ergebnis (Cloud ODER self-hosted, Modus 1 ODER 2)."""
    is_plant: bool = True
    findings: list[PestFinding] = []
    is_confident: bool = True              # False → Abstention
    tiles_processed: int = 0
    adapter_key: str = ""
    source: str = ""                        # 'cloud_kindwise' | 'local_detector' | 'local_symptom'
    inference_time_ms: int = 0
    disclaimer: str = (
        "Nur eine Einschätzung der Bilderkennung — keine gesicherte Schädlings-Bestimmung. "
        "Bitte den Befund prüfen, bevor du behandelst; Nützlinge nicht verwechseln."
    )


class PestDetectionAdapter:
    """Gemeinsamer Vertrag für Cloud- und Self-Hosted-Schädlingserkennung.

    Phase 1: LocalPestSymptomAdapter (Modus 2) + optional KindwisePestAdapter (Cloud)
    Phase 2: LocalPestDetectorAdapter (Modus 1, quantisiertes ONNX + Tiling)
    """
    adapter_key: str
    requires_consent: str | None    # z. B. 'pest_detection_cloud' (Cloud) bzw. None (lokal)
    supports_modes: list[str]       # ['direct'] | ['symptom'] | ['direct', 'symptom']

    @abstractmethod
    async def detect(
        self, tiles: list[bytes], *, language: str = "de"
    ) -> PestDetectionResult: ...
```

### 4.3 Tiling-Baustein (Pflicht)

Wiederverwendbarer Vorverarbeitungs-Service (geteilt mit REQ-038), gegen das Small-Object-Problem:

```python
ABSTAIN_CONFIDENCE = 0.40   # darunter: keine belastbare Aussage → Abstention

class ImageTiler:
    """Zerlegt ein hochauflösendes Bild in überlappende Kacheln, führt die
    Detektion pro Kachel aus und merged überlappende Boxen (NMS) zurück ins
    Vollbild-Koordinatensystem. Ohne Tiling werden winzige Schädlinge/Symptome
    systematisch übersehen (Small-Object-Problem, siehe Recherche §2.1)."""

    def tile(self, image: bytes, *, tile: int = 640, overlap: float = 0.2) -> list[bytes]: ...
    def merge_boxes(self, per_tile: list[list[PestFinding]]) -> list[PestFinding]: ...
```

Bei allen Findings unter `ABSTAIN_CONFIDENCE` und ohne starkes Kontext-Signal wird `is_confident=False` gesetzt (Abstention statt überkonfidenter Aussage).

## 5. Datenmodell (ArangoDB)

### 5.1 Neue Document Collection: `pest_detections`

```json
{
  "_key": "pestdet_20260620_a1b2c3",
  "tenant_key": "tenant_personal_anna",
  "user_key": "user_anna",
  "plant_instance_key": "plant_anna_monstera_01",
  "planting_run_key": null,
  "source": "local_symptom",                 // cloud_kindwise | local_detector | local_symptom
  "adapter_key": "local_pest_symptom",
  "is_confident": true,
  "trigger": "user_photo",                    // user_photo | scheduled | manual
  "findings": [
    {
      "label": "spider_mite_webbing", "category": "symptom",
      "common_name": "Spinnmilben-Gespinst", "confidence": 0.52, "mode": "symptom",
      "bounding_box": { "x": 0.41, "y": 0.33, "width": 0.12, "height": 0.09 },
      "matched_pest_key": "pest_tetranychus_urticae"
    }
  ],
  "tiles_processed": 9,
  "suggested_next_step": "ipm_inspection",    // ipm_inspection | none
  "llm_explanation": null,                     // optional Phase 2 (RAG-(V)LM)
  "image_hash": "sha256:...",                  // Bild nicht persistiert
  "image_deleted_at": "2026-06-20T14:30:02Z",
  "disclaimer": "Nur eine Einschätzung — keine gesicherte Schädlings-Bestimmung.",
  "created_at": "2026-06-20T14:30:00Z"
}
```

**Indexes:** Persistent auf `tenant_key`, `plant_instance_key`, `created_at`, `is_confident`.

### 5.2 Neue Edge Collections

```aql
// pest_detection_of (pest_detections → plant_instances / planting_runs)
//   Dual-Support analog REQ-013 v2.0

// pest_detection_flagged (pest_detections → pests)
//   Wenn ein Finding gegen REQ-010 pests-Stammdaten gemappt wurde
//   Felder: confidence: float, mode: string, confirmed: bool (HITL)

// pest_detection_suggested_inspection (pest_detections → inspections)
//   Wenn aus einem Befund eine REQ-010-Inspektion vorgeschlagen/angelegt wurde
```

### 5.3 Feedback (Human-in-the-Loop)

Nutzer-Feedback pro Finding (`confirmed: bool`, optional `actual_label`, `was_beneficial: bool`) wird an `pest_detection_flagged` bzw. einer `pest_detection_feedback`-Collection persistiert — Quelle für Kalibrierung und Aufbau des Indoor-Datensets.

## 6. Backend-API

Tenant-scoped unter `/api/v1/t/{tenant_slug}/pests/`. JWT + Tenant-Membership.

| Methode | Pfad | Beschreibung | Consent |
|---------|------|-------------|---------|
| `GET` | `/status` | Verfügbarkeit: welcher Adapter aktiv (cloud/local-detector/local-symptom/none)? | — |
| `POST` | `/plants/{plant_key}/detect` | Neue Schädlingserkennung; `image` (multipart, Pflicht). Tiling + Detektion | `pest_detection_cloud` *nur* wenn Cloud-Adapter aktiv |
| `GET` | `/plants/{plant_key}/history` | Verlauf der Erkennungen | — |
| `POST` | `/detections/{key}/feedback` | „bestätigt / falsch / war Nützling" + optionales Korrekt-Label (HITL) | — |
| `POST` | `/detections/{key}/create-inspection` | aus Befund eine REQ-010-Inspektion anlegen (kein Treatment!) | — |

```python
@router.post("/plants/{plant_key}/detect")
async def detect_pests(
    tenant_slug: str,
    plant_key: str,
    image: UploadFile = File(..., description="JPEG/PNG, max 8 MB"),
    language: str = Form("de"),
    user=Depends(get_current_user),
    service=Depends(get_pest_detection_service),
) -> dict:
    """Erkennt Schädlinge (Modus 1) und/oder Schadbilder (Modus 2) im Foto.

    EXIF wird vor jeder Verarbeitung entfernt (REQ-029 §5.4). Das Bild wird
    in Kacheln zerlegt (Tiling, Pflicht). Cloud-Erkennung erfordert Consent
    'pest_detection_cloud'; self-hosted/lokal nicht. Antwort trägt IMMER einen
    Disclaimer und löst NIE automatisch ein Treatment aus.
    """
    ...
```

## 7. Frontend-Integration

| Komponente / Seite | Integration | Erfahrungsstufe (REQ-021) |
|---|---|---|
| **`PestScanButton`** | „Auf Schädlinge prüfen" → Foto-Erfassung nach REQ-052 §2, Profil `recognition` (wiederverwendet REQ-029 §4.1) | alle |
| **`PestDetectionDialog`** | Ergebnis mit Bounding-Boxen-Overlay (Modus 1) bzw. markierten Symptom-Regionen (Modus 2) | alle |
| Disclaimer-Banner | **Immer sichtbar**, prominent | alle |
| Abstention-Hinweis | bei `is_confident=false`: „Keine sichere Erkennung — bitte manuell prüfen" + Verweis auf IPM-Inspektion | alle |
| Nützling-Hinweis | bei `category=beneficial`: „Das ist vermutlich ein Nützling — nicht bekämpfen" | alle |
| Findings-Liste | common_name + Konfidenz + Modus; Mapping-Link zu REQ-010-Pest-Stammdaten | Intermediate/Expert; Beginner nur Top-Finding |
| Nächster-Schritt-CTA | `suggested_next_step` → „Inspektion anlegen" (REQ-010) | alle |
| Feedback-Buttons | „bestätigt / falsch / war Nützling" (HITL) | alle |

**Light-Modus (REQ-027):** Die **Self-Hosted-/Demo-Adapter sind verfügbar** (rein lokal, keine Einwilligung, kein Daten-Egress — konsistent zu §3.3 „Light-Modus rein lokal"; tenant-scoped läuft über den Light-Tenant + System-User). **Nur der Cloud-Adapter** (Kindwise) ist im Light-Modus **blockiert**, da dort kein Consent-Subsystem existiert — Hinweis „Cloud-Erkennung im Light-Modus nicht verfügbar; lokale Erkennung nutzbar". <!-- Quelle: Nutzer-Entscheidung 2026-06-21, Implementierung PR #256 -->

### 7.1 i18n-Keys (Auszug, `pages.pests.*`)

```json
{
  "pages": {
    "pests": {
      "title": "Schädlingserkennung",
      "scanButton": "Auf Schädlinge prüfen",
      "noFindings": "Keine Schädlinge erkannt — das ist aber kein Beweis für Schädlingsfreiheit.",
      "abstain": "Keine sichere Erkennung. Bitte prüfe die Pflanze manuell.",
      "beneficial": "Das ist vermutlich ein Nützling — bitte nicht bekämpfen.",
      "disclaimer": "Dies ist eine Einschätzung der Bilderkennung und keine gesicherte Bestimmung. Bitte prüfe den Befund, bevor du behandelst.",
      "createInspection": "Inspektion anlegen",
      "feedbackConfirm": "Stimmt das?"
    }
  }
}
```

## 8. Sicherheit & Datenschutz (REQ-025, NFR-007, NFR-011)

| Aspekt | Umsetzung |
|--------|-----------|
| **Consent** | Neuer Zweck `pest_detection_cloud` — **nur** erforderlich, wenn der Cloud-Adapter aktiv ist. Self-Hosted ohne externen Consent. |
| **EXIF-Stripping** | Wiederverwendung REQ-029 §5.4, doppelt (Frontend + Backend), **vor** Tiling/Verarbeitung — kritisch, da API-Uploads EXIF nicht automatisch strippen. |
| **Bild-Persistenz** | Bilddaten **nicht** dauerhaft gespeichert (`image_deleted_at`); nur Hash + Findings bleiben. |
| **Drittland/AVV (Cloud)** | Kindwise = Auftragsverarbeiter (Art. 28); AVV + EU-Hosting **vertraglich verifizieren** (Vendor-Selbstauskunft genügt nicht); Indoor-Eignung empirisch testen. |
| **Retention** | `pest_detections` unterliegt NFR-011-Retention; Default-Löschfrist konfigurierbar. |
| **Default-Privacy** | `pest_detection_enabled=False`; Self-Hosted-Adapter Default, Cloud opt-in. |
| **Audit** | Cloud-Aufrufe erscheinen im `ai_audit_log` (REQ-031) ohne Klartext-PII. |
| **Kein Auto-Treatment** | Eine Erkennung erzeugt höchstens einen Inspektions-Vorschlag; das Karenz-Gate (REQ-010) wird nie umgangen. |
| **Disclaimer/Haftung** | Jede API-Antwort und UI-Anzeige trägt den Disclaimer; automatisierter Test prüft, dass `disclaimer` nie leer ist. |

## 9. Akzeptanzkriterien

### 9.1 Definition of Done

- [ ] **`PestDetectionAdapter`-Vertrag** definiert; `LocalPestSymptomAdapter` (Modus 2, Default) implementiert; `KindwisePestAdapter` (Cloud, opt-in) und `LocalPestDetectorAdapter` (Modus 1, Phase 2) implementieren denselben Vertrag; `/status` meldet den aktiven Adapter, ohne Adapter bleibt die App voll funktionsfähig.
- [ ] **Tiling Pflicht:** `ImageTiler` zerlegt Uploads in überlappende Kacheln, detektiert pro Kachel, merged Boxen (NMS) zurück ins Vollbild; `tiles_processed` wird berichtet.
- [ ] **Abstention:** Bei allen Findings < `ABSTAIN_CONFIDENCE` und ohne starkes Kontext-Signal wird `is_confident=false` zurückgegeben — **keine** überkonfidente Aussage.
- [ ] **Beide Modi:** Direkt-Detektion (`mode=direct`, mit Bounding-Box) und Schadbild (`mode=symptom`) werden im Ergebnis unterschieden.
- [ ] **Nützling-Differenzierung:** erkannte Nützlinge erhalten `category=beneficial` und werden **nie** als zu bekämpfender Schädling dargestellt.
- [ ] **`pest_detections`-Collection** + Edges (`pest_detection_of`, `pest_detection_flagged`, `pest_detection_suggested_inspection`) angelegt; Verlauf abfragbar.
- [ ] **IPM-Brücke (REQ-010):** Findings werden gegen `pests`-Stammdaten gemappt; `create-inspection` legt eine REQ-010-Inspektion an — **kein** automatisches `treatment_application`, Karenz-Gate unangetastet.
- [ ] **Health-Brücke (REQ-043):** ein bestätigter Befund verstärkt das Befall-/IPM-Signal der `HealthAssessmentEngine`.
- [ ] **Disclaimer immer präsent** in jeder API-Antwort und UI-Anzeige (automatisierter Test über alle Pfade).
- [ ] **Consent + EXIF:** Cloud-Pfad erfordert `pest_detection_cloud`; EXIF wird doppelt vor Tiling entfernt; Bilddaten nicht persistiert.
- [ ] **Frontend:** `PestScanButton`, `PestDetectionDialog` (Box-/Symptom-Overlay), Abstention-/Nützling-Hinweise, Feedback-Buttons, Inspektions-CTA implementiert; Erfahrungsstufen respektiert; Light-Modus blockiert mit Hinweis.
- [ ] **Human-in-the-Loop:** Feedback („bestätigt / falsch / war Nützling") wird gespeichert und steht als Adaptions-/Trainingssignal zur Verfügung.
- [ ] **Default-Privacy:** `pest_detection_enabled=False`; Self-Hosted-Adapter Default, Cloud opt-in.
- [ ] **i18n** DE+EN vollständig (`pages.pests.*`).
- [ ] **Pytest** für Tiling+Box-Merge, Abstention, Nützling-Klassifikation, Adapter-Dispatch, Cloud-ohne-Consent (403), kein Auto-Treatment, Cleanup; **Vitest** für Dialog/Overlay/Feedback.

### 9.2 Testszenarien

**Szenario 1: Schadbild ohne sichtbares Insekt (Modus 2)**
```
GIVEN: LocalPestSymptomAdapter aktiv; Foto mit Spinnmilben-Gespinst, kein Insekt sichtbar
WHEN:  detect läuft (Tiling aktiv)
THEN:
  - finding mode=symptom, category=symptom, matched_pest_key=Spinnmilbe, confidence im mittleren Bereich
  - suggested_next_step = "ipm_inspection"; Disclaimer vorhanden; KEIN Treatment
```

**Szenario 2: Abstention bei zu kleinen/unsicheren Objekten**
```
GIVEN: Foto mit unruhigem Hintergrund; alle Findings < ABSTAIN_CONFIDENCE
WHEN:  detect läuft
THEN:
  - is_confident = false; UI zeigt "Keine sichere Erkennung — bitte manuell prüfen"
  - Verweis auf manuelle IPM-Inspektion (REQ-010)
```

**Szenario 3: Nützling nicht als Schädling melden**
```
GIVEN: Foto einer Marienkäfer-Larve
WHEN:  detect läuft
THEN:
  - finding category=beneficial; UI: "vermutlich ein Nützling — nicht bekämpfen"
  - kein suggested_next_step zur Bekämpfung
```

**Szenario 4: Cloud-Adapter ohne Consent**
```
GIVEN: KindwisePestAdapter aktiv, Consent 'pest_detection_cloud' NICHT erteilt
WHEN:  Nutzer ruft detect mit Foto auf
THEN:  HTTP 403 / Consent-Aufforderung; kein Bild verlässt die Anwendung; Hinweis auf lokalen Pfad
```

**Szenario 5: Direkt-Detektion mit Tiling (Modus 1, Phase 2)**
```
GIVEN: LocalPestDetectorAdapter aktiv; hochauflösendes Foto mit mehreren Thripsen
WHEN:  detect läuft
THEN:
  - tiles_processed > 1; mehrere findings mode=direct mit bounding_box im Vollbild-Koordinatensystem
  - Boxen korrekt via NMS gemerged (kein Doppel-Zählen an Kachelgrenzen)
```

**Szenario 6: Disclaimer-Invariante**
```
WHEN:  beliebige detect-Antwort (cloud/local-detector/local-symptom/abstain)
THEN:  Feld disclaimer ist nie leer (automatisierter Test über alle Pfade)
```

**Szenario 7: Feature deaktiviert**
```
GIVEN: pest_detection_enabled == false
WHEN:  Frontend lädt PlantInstance-Seite
THEN:  /status meldet kein aktiver Adapter; Button ausgeblendet; App voll funktionsfähig
```

## 10. Offene Punkte (geklärt durch Implementierungs-Vorbereitung)

> Die ursprünglich offenen Punkte wurden durch eine fokussierte Recherche geklärt: **`spec/analysis/pest-detection-implementation-prep.md`**. Zusammenfassung pro Punkt; verbleibende externe/empirische Aktions-Items dort in §10.

- **Indoor-Datenset → geklärt (Prep §3):** AgriPest/Pest24/IP102 nur als Backbone-Prior. Cold-Start über **iNaturalist/GBIF** (CC0/CC-BY-gefiltert) + **HITL-Nutzerbilder**; **Few-Shot via frozen DINOv2 + Prototypical/kNN** (~30 Bilder/Klasse → live, nutzt REQ-029-A-Service). Datenlage: Weiße Fliege/Thripse gut, Spinnmilben brauchbar (oft Schadbild), **Trauermücken = echte Lücke, Wollläuse fast**.
- **Kindwise-Vertragslage → geklärt (Prep §5):** AVV (Art. 28) öffentlich in T&C Art. 20; **`plant.health` statt `crop.health`**; kritisch: Trainingsnutzung ohne Opt-out + keine EU-Residenz-Garantie. **9 Vor-Vertrags-Fragen** dokumentiert (Aktions-Item). Alternative Plantix/PEAT (DE-Sitz, schwächere Indoor-Eignung).
- **Modell/ONNX/Tiling → geklärt (Prep §4):** **YOLO entfällt (AGPL)** → **RF-DETR-S (Apache-2.0)** 1. Wahl, D-FINE-S/N Alternative; **SAHI**-Tiling (512px/0.2 Overlap/GREEDYNMM, eigener ONNX-Wrapper nötig); INT8 nur für CNNs/optional; realistische Latenz **1–5 s/Foto** mit Tiling.
- **Abstention-Schwelle → geklärt (Prep §6):** `ABSTAIN_CONFIDENCE=0.40` ist **nur Tag-1-Default**; richtig: **Temperature Scaling + Energy-OOD-Gate + klassenweise Schwelle über Risk-Coverage-Kurve auf Feld-Kalibrierungsdaten**; explizite **`beneficial`/`unknown`-Klasse**; Conformal Prediction erst Phase 2 (≥~1000 Feld-Kalibrierbeispiele, SSBC).
- **`beneficials`-Stammdaten → geklärt (Prep §8):** REQ-010 um eine **`beneficials`-Collection** (Nützlinge) ergänzen, analog `pests`; bis dahin `category=beneficial` Slug-basiert ohne `matched_*_key`.
- **RAG-(V)LM-Erklärungsstufe → geklärt (Prep §7):** CPU-machbar als **„Sekunden-pro-Bild"-Feature** (Qwen2.5-VL-3B-Q4 / Moondream2 / SmolVLM2), opt-in/asynchron mit **Graceful Degradation**; interaktiv → GPU. VLM = **Erklärer, nie Erkenner**.
- **Proaktive geplante Scans → präzisiert (Prep §8):** Celery-Beat-Task analog REQ-022; **keine** automatische Aufnahme, sondern Re-Evaluierung vorhandener Galerie-Fotos (REQ-034). Detail-Spec v2.

---

**Hinweise für RAG-Integration:**
- Keywords: Schädlingserkennung, Pest Detection, Small-Object-Detection, Tiling, Direkt-Detektion, Schadbild, Symptom, Spinnmilben, Thripse, Trauermücken, Schmierläuse, Weiße Fliege, Blattläuse, Nützling, Reliability Gap, mAP, Abstention, Kalibrierung, Human-in-the-Loop, Disclaimer, Kindwise, crop.health, insect.id, AgriPest, Pest24, IP102, ONNX, EXIF, Consent
- Verknüpfung: REQ-010 (IPM/Pests, Befund-Brücke & Karenz-Gate), REQ-043 (Health-Fusion, konsumiert Signal), REQ-038 (CV-Diagnose, geteilte Vision/Tiling-Infrastruktur), REQ-029/029-A (Adapter/Infra/ONNX), REQ-031 (RAG-(V)LM), REQ-025 (DSGVO/Consent)
- Fachbegriffe: Small-Object-Detection, Image-Tiling/Slicing, Reliability Gap, mAP@0.5, Abstention, Few-Shot, Domain-Shift, Bounding-Box-NMS
- Lösungsentscheidung: Self-Hosted-First-Phasen-Strategie — Phase 1 Schadbild-Adapter (Modus 2, Default) + Kindwise-Cloud-Opt-in (Consent); Phase 2 Self-Hosted Direkt-Detektor (Modus 1, quantisiertes ONNX + Tiling, eigenes Indoor-Datenset); Tiling Pflicht, Abstention zwingend, Einspeisung als Bild-Signal in IPM/Health ohne Auto-Treatment
- Quelle des Methodenvergleichs: `spec/analysis/pest-detection-research.md`
