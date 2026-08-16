# Spezifikation: REQ-038 - CV-gestützte Pflanzendiagnose

```yaml
ID: REQ-038
Titel: Computer-Vision-gestützte Pflanzendiagnose (Krankheits-, Mangel- & Schädlingserkennung)
Kategorie: KI & Schädlingsmanagement
Fokus: Beides
Technologie: Python 3.14+, PlantCV, ONNX, FastAPI, ArangoDB, Celery, React, TypeScript, MUI
Status: Entwurf
Version: 1.2 (Erfassungsverweis auf REQ-052 umgehängt)
Abhängigkeit: REQ-010 (IPM), REQ-029 (Bilderkennung), REQ-029-A (Self-Hosted), REQ-036 (KI-Diagnose-Assistent), REQ-007 (Ernte), REQ-025 (DSGVO), REQ-031 (Knowledge-Service)
```

## Versionshistorie

| Version | Datum | Änderung |
|---------|-------|----------|
| 1.0 | 2026-06-19 | Initialer Entwurf — Integration von PlantVillage + PlantCV (awesome-agriculture) |
| 1.1 | 2026-06-20 | G1-Entscheidung: PlantVillage fallengelassen (Lizenz ungeklärt); PlantDoc (CC-BY-4.0) als primäre Trainingsquelle; PlantCV-Modifikationsverbot ergänzt |

## 1. Business Case

### 1.1 User Stories

**User Story (Casual User — Foto statt Fachbegriff):** „Als Zimmerpflanzen-Besitzer ohne botanisches Wissen möchte ich ein Foto eines kranken Blatts machen und sofort eine Vorab-Vermutung erhalten (z. B. „könnte Mehltau sein"), damit ich im Diagnose-Assistenten (REQ-036) nicht raten muss, welches Symptom ich anklicken soll."

**User Story (Grower — IPM-Vorab-Hypothese):** „Als Grower möchte ich bei der Inspektion (REQ-010) ein Foto eines befallenen Blatts aufnehmen und eine CV-gestützte Verdachtsliste mit Konfidenz erhalten, die ich gegen meine IPM-Stammdaten gematcht bekomme — damit ich schneller eine fundierte Inspektionsentscheidung treffe."

**User Story (Mangel-Erkennung):** „Als Nutzer möchte ich, dass das System bei Verfärbungen abschätzt, ob es sich um einen Nährstoffmangel oder eine Krankheit handelt, damit ich nicht fälschlich ein Fungizid einsetze, wo eigentlich Düngung nötig wäre."

**User Story (Phänotyp-Metriken):** „Als ambitionierter Grower möchte ich quantitative Kennzahlen aus meinen Pflanzenfotos ableiten lassen (Blattfläche, Anteil verfärbter/nekrotischer Fläche, Grün-Index), damit ich Wachstum und Erntereife (REQ-007) objektiv über die Zeit verfolgen kann statt nur subjektiv per Augenmaß."

**User Story (Self-Hosted/Datenschutz):** „Als Betreiber einer Self-Hosted-Instanz möchte ich die Diagnose auf meiner eigenen Hardware betreiben können, ohne pro-Request-Kosten und ohne dass Nutzerfotos die Infrastruktur verlassen — analog zur Vorgabe aus REQ-029-A."

**User Story (Vorsicht/Disclaimer):** „Als Nutzer möchte ich klar erkennen, dass jede CV-Diagnose nur eine Hypothese ist und eine fachliche Bestätigung braucht — damit ich keine teuren Fehlbehandlungen auf Basis einer falsch-positiven KI-Aussage durchführe."

### 1.2 Beschreibung

REQ-038 ergänzt die **bildbasierte Zustandsdiagnose** (Krankheit, Nährstoffmangel, Schädling) als CV-Komponente. Sie grenzt sich von den Nachbar-REQs ab:

- **REQ-029 / REQ-029-A** lösen die **Artbestimmung** („Welche Pflanze ist das?"). REQ-038 löst die **Zustandsdiagnose** („Was fehlt der Pflanze?").
- **REQ-010 (IPM)** dokumentiert Befall heute **manuell** über Inspektionen. REQ-038 liefert die Vorab-Hypothese, die der Inspektor bestätigt oder verwirft.
- **REQ-036 (KI-Diagnose-Assistent)** führt einen strukturierten Symptom-Katalog-Dialog. REQ-038 liefert dem Assistenten eine **Foto-Vorab-Hypothese** als zusätzlichen Kontext (Vorbelegung passender Symptom-Slugs).
- **REQ-007 (Ernte)** nutzt die PlantCV-Phänotyp-Metriken als zusätzliche Ertrags-/Reifeindikatoren.

Zwei technisch getrennte Bausteine:

1. **Klassifikator-Pfad (Krankheit/Mangel/Schädling):** Ein self-hosted ONNX-Klassifikator liefert aus einem Blattfoto eine Verdachtsliste. Primäre, lizenzsaubere Trainings-/Fine-Tuning-Basis ist **PlantDoc (CC-BY-4.0)** plus eigene kuratierte Realdaten (siehe Caveat §1.4). **PlantVillage wird nicht verwendet** — die Lizenz ist ungeklärt (Repo ohne LICENSE, CC-BY-SA↔CC0 widersprüchlich; siehe Lizenzanalyse `spec/analysis/awesome-agriculture-lizenz-und-nutzungsanalyse.md`); es wird allenfalls als historischer Benchmark erwähnt, nicht als genutzte Datenquelle.
2. **Phänotyp-Pfad (PlantCV):** Eine deterministische Bildanalyse-Pipeline extrahiert **quantitative Metriken** (Segmentierung, Blattfläche, Farb-/Form-Kennzahlen, Anteil verfärbter Fläche). Diese Werte sind keine Diagnose, sondern objektive Messgrößen und dienen als Feature-Input und Monitoring-Kennzahl.

### 1.3 Projekt-Steckbrief (awesome-agriculture-Quellen)

| Attribut | PlantDoc (primäre Trainingsquelle) | PlantVillage (NICHT verwendet) | PlantCV |
|----------|------------------------------------|--------------------------------|---------|
| **Name** | PlantDoc | PlantVillage Dataset | PlantCV (Plant Computer Vision) |
| **Repo/Quelle** | `https://github.com/pratikkayal/PlantDoc-Dataset` | `https://github.com/spMohanty/PlantVillage-Dataset` | `https://github.com/danforthcenter/plantcv` |
| **Herausgeber** | Singh et al. 2020 (CoDS-COMAD) | Penn State / EPFL (Hughes & Salathé), Mohanty et al. 2016 | Donald Danforth Plant Science Center (seit 2014) |
| **Lizenz** | **CC-BY-4.0** (kommerziell + Modell-Weitergabe ohne ShareAlike erlaubt, nur Attribution) | **ungeklärt** — Repo ohne LICENSE; CC-BY-SA 3.0 (PSU/Zenodo, mit ShareAlike) ↔ CC0 (Kaggle-Mirror) widersprüchlich; siehe Lizenzanalyse | **MPL-2.0** (Mozilla Public License 2.0) — **nicht** MIT |
| **Sprache/Format** | Bilddaten („in the wild", RGB) + Labels | Bilddaten (RGB, 256 px², JPEG) + Labels | Python-Bibliothek (auf OpenCV, NumPy, Matplotlib) |
| **Typ** | Trainingsdatensatz (reale Feld-/„in the wild"-Bilder) | Trainingsdatensatz (kein Code, keine Modellgewichte) | Bildanalyse-Bibliothek (Phänotyping-Workflows) |
| **Umfang** | ~2.600 Bilder, 13 Arten, 17 Krankheitsklassen | 54.306 Bilder, 38 Klassen, 14 Kulturarten, 26 Krankheiten | v4.11 (Stand April 2026), modulare Workflow-Architektur |
| **Reifegrad** | Klein, aber domänennah (reale Hintergründe); als Fine-Tuning-Schicht | Etabliert, breit zitiert; bekannte Bias-Limitierung (§1.4) — **nur als historischer Benchmark erwähnt** | Aktiv gepflegt, akademisch fundiert (PlantCV v4, 2025/2026) |
| **Was es leistet** | Reale „in the wild"-Blattbilder mit unruhigem Hintergrund | Annotierte Blattbilder unter Laborbedingungen | Segmentierung, Blattflächen-/Form-/Farbmetriken, Morphologie (Blattwinkel), Multispektral (Fluoreszenz/Thermal/Hyperspektral) |
| **Was es NICHT leistet** | Kein Modell; klein → nicht als alleinige Basis, nur Fine-Tuning-Schicht | **Nicht genutzt** (Lizenz ungeklärt); zudem nur Labordaten → Lab→Feld-Gap | **Keine Krankheits-Klassifikation** — nur quantitative Messung |

### 1.4 Caveats (verbindlich zu beachten)

> **C-1 — Lab→Feld-Gap & PlantVillage-Entscheidung (kritisch):** Labordatensätze wie PlantVillage zeigen **einzeln freigestellte Blätter unter Laborbedingungen** (einheitlicher Hintergrund) und decken überwiegend **landwirtschaftliche Nutzpflanzen** ab (Apfel, Traube, Kartoffel, Tomate, …). Mohanty et al. (2016) berichten 99,35 % Genauigkeit *innerhalb* der Lab-Domäne, aber nur **31,4 % auf Feldbildern** desselben Modells. Für reale Zimmerpflanzen-, Indoor- und Garten-Fotos generalisiert ein rein auf solchen Labordaten trainiertes Modell daher **schlecht**. **PlantVillage wird in REQ-038 nicht als Datenquelle verwendet** (G1-Entscheidung): Das Repo enthält **kein LICENSE-File**, maßgebliche Quellen widersprechen sich (PSU/Zenodo: CC-BY-SA 3.0 mit ShareAlike vs. Kaggle-Mirror: CC0) → Lizenz ungeklärt, für eine MIT-Produktiv-App zu riskant; zudem taugen die Labordaten wegen des Lab→Feld-Gaps ohnehin nur als Ergänzung. PlantVillage darf höchstens als **historischer Benchmark** erwähnt werden. Begründung und Beleg: Lizenzanalyse `spec/analysis/awesome-agriculture-lizenz-und-nutzungsanalyse.md`.

> **C-2 — Primäre Trainingsquelle PlantDoc + eigene Realdaten:** Ein produktiver Klassifikator setzt domänennahe Realdaten voraus (Feld-/Indoor-Fotos mit unruhigem Hintergrund). Primäre, lizenzsaubere Trainings-/Fine-Tuning-Quelle ist **PlantDoc (CC-BY-4.0)** — kommerzielle Nutzung und Modell-Weitergabe sind ohne ShareAlike erlaubt (nur Attribution), die Bilder sind reale „in the wild"-Aufnahmen (vgl. REQ-029-A §1.1 Aufgabe B). PlantDoc ist mit ~2.600 Bildern klein und dient daher als **Fine-Tuning-Schicht, nicht als alleinige Basis**; ergänzt um eigene kuratierte Nutzerfotos (nur mit Consent, anonymisiert) und ggf. weitere lizenzgeprüfte Feld-Datensätze. Das Vortraining liefert ein generisches Backbone (ImageNet/DINOv2), nicht PlantVillage.

> **C-3 — Kein Ersatz für Fachdiagnose:** Jedes Ergebnis ist eine **Hypothese**. UI und API tragen immer den Disclaimer „nur Hypothese — fachliche Bestätigung nötig". Eine CV-Diagnose darf **niemals** automatisch eine Behandlung auslösen oder ein Karenz-Gate (REQ-010) umgehen; sie kann nur einen **Vorschlag** erzeugen, den ein Mensch bestätigt.

> **C-4 — Confidence-Disclaimer:** Unterhalb der Anzeige-Schwelle (`CONFIDENCE_SHOW`) werden Ergebnisse verworfen; oberhalb der Auto-Accept-Schwelle erfolgt **kein** Auto-Anlegen — nur eine deutlichere Hervorhebung. Die Auswahl trifft immer der Nutzer.

> **C-5 — DSGVO bei Foto-Uploads:** Nutzerfotos sind potenziell personenbezogene Daten (Metadaten, Hintergrund). EXIF-Stripping (REQ-029 §5.4) und Consent (`plant_diagnosis`, §5.1) werden wiederverwendet. Im Self-Hosted-Pfad (§3) verlassen Fotos die Instanz nicht.

> **C-6 — Lizenz-Hygiene:** PlantCV ist **MPL-2.0** (Datei-Level-Copyleft): PlantCV wird **unverändert als Library/Service** genutzt; PlantCV-**Quelldateien werden NICHT gepatcht** (datei-basiertes Copyleft würde die Offenlegung der geänderten Datei unter MPL-2.0 erzwingen) — der MPL-2.0-Notice wird mitgeliefert. Die primäre Trainingsquelle **PlantDoc ist CC-BY-4.0** (kommerzielle Nutzung und Modell-Weitergabe ohne ShareAlike erlaubt, nur Attribution); daraus abgeleitete Modellgewichte sind unter Attribution frei verwendbar. **PlantVillage wird nicht verwendet** — Lizenz ungeklärt (Repo ohne LICENSE, CC-BY-SA↔CC0 widersprüchlich); siehe Lizenzanalyse `spec/analysis/awesome-agriculture-lizenz-und-nutzungsanalyse.md`.

## 2. Datenmodell-Erweiterung (ArangoDB)

Wiederverwendet wird das Adapter- und Request-Muster aus REQ-029. REQ-038 ergänzt eine eigene Request-Collection und ein Ergebnis-Embedded-Schema sowie Kanten in die IPM-Stammdaten (REQ-010).

### 2.1 Neue Document Collection: `plant_diagnosis_requests`

Analog zu `diagnosis_requests` (REQ-029), aber dediziert für die CV-Zustandsdiagnose mit Phänotyp-Metriken.

```json
{
  "_key": "cvdiag_20260619_a1b2c3",
  "tenant_key": "tenant_personal_anna",
  "user_key": "user_anna",
  "plant_instance_key": "plant_anna_monstera_01",
  "planting_run_key": null,
  "inspection_key": null,
  "diagnosis_session_key": null,
  "adapter_key": "local_cv_classifier",
  "image_hash": "sha256:a1b2c3...",
  "affected_plant_part": "leaf",
  "status": "completed",
  "classifications": [
    {
      "rank": 1,
      "label": "tomato_septoria_leaf_spot",
      "category": "disease",
      "common_name": "Septoria-Blattfleckenkrankheit",
      "confidence": 0.7421,
      "matched_disease_key": "disease_septoria",
      "matched_pest_key": null,
      "is_hypothesis": true
    },
    {
      "rank": 2,
      "label": "nutrient_deficiency_n",
      "category": "deficiency",
      "common_name": "Stickstoffmangel",
      "confidence": 0.1893,
      "matched_disease_key": null,
      "matched_pest_key": null,
      "is_hypothesis": true
    }
  ],
  "phenotype_metrics": {
    "leaf_area_px": 184320,
    "leaf_area_cm2": null,
    "green_index": 0.61,
    "discolored_area_ratio": 0.18,
    "necrotic_area_ratio": 0.07,
    "solidity": 0.93,
    "hue_circular_mean_deg": 102.4,
    "plantcv_version": "4.11"
  },
  "model_meta": {
    "model_name": "kamerplanter-leaf-disease-v1",
    "model_version": "20260601",
    "training_base": "imagenet-dinov2-backbone",
    "fine_tuned_on": "plantdoc-ccby4+curated",
    "onnx_checksum": "sha256:...",
    "inference_time_ms": 142
  },
  "disclaimer": "Nur eine Hypothese — keine gesicherte Diagnose. Bitte fachlich bestätigen.",
  "created_at": "2026-06-19T14:30:00Z",
  "image_deleted_at": "2026-06-19T14:30:02Z"
}
```

**Indexes:**
- Persistent auf `tenant_key`, `user_key`, `created_at`
- Persistent auf `plant_instance_key`
- Persistent auf `status`

### 2.2 Neue Edge Collections

```aql
// Edge Collection: cv_diagnosed_for (plant_diagnosis_requests → plant_instances / planting_runs)
//   Verbindet eine CV-Diagnose mit der betroffenen Pflanze bzw. dem Run (Dual-Support, REQ-013 v2.0)

// Edge Collection: cv_diagnosis_found (plant_diagnosis_requests → diseases / pests)
//   Verbindet eine CV-Diagnose mit den gematchten IPM-Stammdaten aus REQ-010
//   Felder: confidence: float, rank: int, category: ['disease', 'pest', 'deficiency'], confirmed: bool

// Edge Collection: cv_attached_to_inspection (plant_diagnosis_requests → inspections)
//   Optional: CV-Diagnose, die im Rahmen einer IPM-Inspektion (REQ-010) erfasst wurde

// Edge Collection: cv_phenotype_of (plant_diagnosis_requests → harvest_observations)
//   Optional: verknüpft Phänotyp-Metriken mit Ernte-Beobachtungen (REQ-007)
```

> **Anmerkung Stammdaten-Lücke:** REQ-038 kennt die Kategorie **`deficiency` (Nährstoffmangel)**, die in REQ-010 nicht als eigene Stammdaten-Collection existiert (REQ-010 führt `pathogen_type` inkl. `physiological`, aber keine Mangel-Collection). Für `category == "deficiency"` bleibt `matched_disease_key`/`matched_pest_key` daher `null`; das Matching erfolgt stattdessen über die Symptom-Slugs aus REQ-036 (`nutrient_deficiency_n` etc.). Eine spätere Erweiterung um eine `deficiencies`-Collection ist optional.

### 2.3 AQL-Beispielabfragen

**CV-Diagnose-Historie einer Pflanze (für Pflanzen-Detailseite):**
```aql
FOR req IN plant_diagnosis_requests
  FILTER req.tenant_key == @tenant_key
     AND req.plant_instance_key == @plant_instance_key
     AND req.status == "completed"
  SORT req.created_at DESC
  LIMIT @limit
  LET top = req.classifications[0]
  RETURN {
    _key: req._key,
    created_at: req.created_at,
    top_label: top.label,
    top_common_name: top.common_name,
    top_confidence: top.confidence,
    discolored_area_ratio: req.phenotype_metrics.discolored_area_ratio
  }
```

**Phänotyp-Verlauf einer Pflanze (Blattfläche/Verfärbung über Zeit, für REQ-007-Monitoring):**
```aql
FOR req IN plant_diagnosis_requests
  FILTER req.plant_instance_key == @plant_instance_key
     AND req.phenotype_metrics != null
  SORT req.created_at ASC
  RETURN {
    at: req.created_at,
    leaf_area_px: req.phenotype_metrics.leaf_area_px,
    green_index: req.phenotype_metrics.green_index,
    discolored_area_ratio: req.phenotype_metrics.discolored_area_ratio,
    necrotic_area_ratio: req.phenotype_metrics.necrotic_area_ratio
  }
```

**Gematchte IPM-Krankheiten mit Bestätigungsstatus (Brücke zu REQ-010):**
```aql
FOR req IN plant_diagnosis_requests
  FILTER req._key == @request_key
  FOR disease, edge IN 1..1 OUTBOUND req cv_diagnosis_found
    OPTIONS { edgeCollections: ['cv_diagnosis_found'] }
    FILTER IS_SAME_COLLECTION('diseases', disease)
    RETURN {
      disease_key: disease._key,
      disease_name: disease.common_name,
      confidence: edge.confidence,
      confirmed: edge.confirmed
    }
```

## 3. Technische Umsetzung (Python)

### 3.1 Adapter-Interface (Wiederverwendung REQ-029 §3.1)

REQ-038 registriert einen neuen Adapter in der bestehenden `IdentificationAdapterRegistry` (REQ-029 §3.4). Das `PlantIdentificationAdapter`-Interface deckt mit `diagnose()` bereits den Health-Assessment-Pfad ab; REQ-038 nutzt diesen Vertrag und erweitert das Ergebnis um Phänotyp-Metriken über ein eigenes Result-Modell.

```python
from abc import abstractmethod
from pydantic import BaseModel, Field

from app.domain.interfaces.plant_identification_adapter import (
    HealthAssessment,
    HealthIssue,
    PlantIdentificationAdapter,
)


class PhenotypeMetrics(BaseModel):
    """Quantitative, deterministische Bildkennzahlen aus der PlantCV-Pipeline.

    KEINE Diagnose — objektive Messgrößen für Monitoring (REQ-007) und als
    optionaler Feature-Input für den Klassifikator.
    """
    leaf_area_px: int | None = None
    leaf_area_cm2: float | None = None  # nur bei bekanntem Maßstab (Referenzobjekt)
    green_index: float | None = None            # 0.0–1.0
    discolored_area_ratio: float | None = None  # Anteil verfärbter Fläche
    necrotic_area_ratio: float | None = None    # Anteil nekrotischer (brauner) Fläche
    solidity: float | None = None               # Formkennzahl (Konvexität)
    hue_circular_mean_deg: float | None = None  # mittlerer Farbton (zirkulär)
    plantcv_version: str | None = None


class CvDiagnosisResult(BaseModel):
    """Ergebnis einer CV-Zustandsdiagnose."""
    health_assessment: HealthAssessment            # Wiederverwendung REQ-029
    phenotype_metrics: PhenotypeMetrics | None = None
    is_plant: bool = True
    inference_time_ms: int = 0
    disclaimer: str = (
        "Nur eine Hypothese — keine gesicherte Diagnose. "
        "Bitte fachlich bestätigen."
    )


class CvDiagnosisAdapter(PlantIdentificationAdapter):
    """Erweiterung des REQ-029-Adapters um eine kombinierte CV-Diagnose
    (Klassifikator + PlantCV-Phänotyp). supports_health_assessment == True.
    """

    @abstractmethod
    async def diagnose_with_phenotype(
        self,
        image_data: bytes,
        *,
        affected_plant_part: str = "leaf",
        language: str = "de",
        include_phenotype: bool = True,
    ) -> CvDiagnosisResult:
        """Liefert Verdachtsliste + optionale Phänotyp-Metriken."""
```

### 3.2 PlantCV-Phänotyp-Pipeline (Engine)

Deterministische Bildanalyse als Preprocessing- und Monitoring-Schritt. PlantCV läuft als reine Mess-Pipeline; ihre Ausgaben sind keine Diagnose.

```python
import structlog

logger = structlog.get_logger()


class PhenotypeEngine:
    """Kapselt die PlantCV-Pipeline (Segmentierung → Maske → Metriken).

    Hinweis: PlantCV (MPL-2.0) wird als Bibliothek genutzt. Es liefert
    quantitative Messgrößen, KEINE Krankheits-Klassifikation.
    """

    def __init__(self) -> None:
        import plantcv  # lazy import — schwere Abhängigkeit
        self._pcv = plantcv.plantcv

    def analyze(self, image_data: bytes) -> "PhenotypeMetrics":
        """Segmentiert das Pflanzenmaterial und extrahiert Form-/Farbkennzahlen.

        Typische PlantCV-Schritte:
          1. Einlesen + Weißabgleich/Normalisierung
          2. Farbraum-Konvertierung (LAB/HSV) + Schwellwert → Binärmaske
          3. Rauschentfernung (fill/erode/dilate), ROI-Begrenzung
          4. analyze.size() → Fläche, Solidity; analyze.color() → Farbhistogramme
          5. Ableitung discolored/necrotic-Ratios aus Farbklassen
        """
        from app.domain.interfaces.cv_diagnosis_adapter import PhenotypeMetrics
        # ... PlantCV-Workflow ...
        return PhenotypeMetrics(
            leaf_area_px=...,
            green_index=...,
            discolored_area_ratio=...,
            necrotic_area_ratio=...,
            solidity=...,
            hue_circular_mean_deg=...,
            plantcv_version=self._pcv.__version__,
        )
```

### 3.3 ONNX-Klassifikator (Self-Hosted, im Inference-Service)

Der Disease/Deficiency-Klassifikator läuft im **bestehenden Inference-Microservice** (`src/inference-service/`, REQ-029-A §3) bzw. im Knowledge-Service — also dort, wo ONNX-Runtime und das DINOv2-Modell schon liegen. Es wird **kein** neuer Microservice nötig; es kommt nur ein zweiter ONNX-Endpunkt hinzu.

```python
# src/inference-service/app/disease_classifier.py
# Neuer interner Endpunkt:
#   POST /classify/disease  — multipart image → { classifications: [...], model: ..., dim: N }
#
# Modell-Provenienz (Modellkarte, verbindlich dokumentiert):
#   training_base : "imagenet-dinov2-backbone"  # generisches Vortraining (Transfer Learning)
#   fine_tuned_on : "plantdoc-ccby4+curated"     # domänennahe Realdaten (Caveat C-2)
#   license       : PlantDoc = CC-BY-4.0 (Attribution); abgeleitete Gewichte frei (nur Attribution)
#   NICHT verwendet: PlantVillage — Lizenz ungeklärt (Repo ohne LICENSE, CC-BY-SA<->CC0); siehe Lizenzanalyse
#
# Architektur: Transfer Learning auf einem ImageNet-/DINOv2-Backbone, Kopf auf die
# (auf KP-Domäne gemappten) PlantDoc-Krankheitsklassen + Mangel-Klassen fine-getunt,
# nach ONNX exportiert. CPU-Inferenz als Baseline (analog REQ-029-A AE-6).
```

> **Wichtig (Caveat C-1):** PlantVillage wird **nicht** als Datenquelle verwendet (Lizenz ungeklärt, G1-Entscheidung). Das Vortraining liefert ein generisches ImageNet-/DINOv2-Backbone; der ausgelieferte Kopf wird auf **PlantDoc (CC-BY-4.0)** plus eigene Realdaten fine-getunt und auf die IPM-Stammdaten (REQ-010) gemappt. Wegen des Lab→Feld-Gaps wäre ein rein laborbasiertes Modell ohnehin nicht produktionstauglich.

### 3.4 Diagnose-Engine (Orchestrierung + IPM-Mapping)

```python
import hashlib
from datetime import datetime, timezone

import structlog

from app.domain.engines.phenotype_engine import PhenotypeEngine
from app.domain.interfaces.cv_diagnosis_adapter import CvDiagnosisResult

logger = structlog.get_logger()

CONFIDENCE_SHOW = 0.10          # Mindest-Konfidenz für Anzeige
CONFIDENCE_HIGHLIGHT = 0.75     # deutlich hervorheben — KEIN Auto-Accept
MAX_IMAGE_SIZE_BYTES = 5 * 1024 * 1024


class CvDiagnosisEngine:
    """Orchestriert CV-Klassifikator + PlantCV-Phänotyp und matched gegen
    die IPM-Stammdaten aus REQ-010 (diseases / pests).
    """

    def __init__(self, ipm_repo, diagnosis_repo, phenotype_engine: PhenotypeEngine) -> None:
        self._ipm_repo = ipm_repo
        self._diagnosis_repo = diagnosis_repo
        self._phenotype = phenotype_engine

    def _compute_hash(self, image_data: bytes) -> str:
        return f"sha256:{hashlib.sha256(image_data).hexdigest()[:32]}"

    async def diagnose(
        self,
        adapter,  # CvDiagnosisAdapter
        image_data: bytes,
        *,
        tenant_key: str,
        user_key: str,
        plant_instance_key: str | None = None,
        planting_run_key: str | None = None,
        inspection_key: str | None = None,
        affected_plant_part: str = "leaf",
        include_phenotype: bool = True,
        language: str = "de",
    ) -> dict:
        if len(image_data) > MAX_IMAGE_SIZE_BYTES:
            raise ValueError("Image too large")

        result: CvDiagnosisResult = await adapter.diagnose_with_phenotype(
            image_data,
            affected_plant_part=affected_plant_part,
            include_phenotype=include_phenotype,
            language=language,
        )

        # Klassifikationen gegen IPM-Stammdaten (REQ-010) mappen
        classifications: list[dict] = []
        for rank, issue in enumerate(
            self._sorted_issues(result.health_assessment), start=1
        ):
            if issue.confidence < CONFIDENCE_SHOW:
                continue
            matched = await self._match_ipm(issue)
            classifications.append({
                "rank": rank,
                "label": issue.external_id or issue.name,
                "category": issue.category,  # disease | pest | deficiency | abiotic
                "common_name": issue.name,
                "confidence": issue.confidence,
                "matched_disease_key": matched.get("disease_key"),
                "matched_pest_key": matched.get("pest_key"),
                "is_hypothesis": True,
            })

        request_doc = {
            "tenant_key": tenant_key,
            "user_key": user_key,
            "plant_instance_key": plant_instance_key,
            "planting_run_key": planting_run_key,
            "inspection_key": inspection_key,
            "adapter_key": adapter.adapter_key,
            "image_hash": self._compute_hash(image_data),
            "affected_plant_part": affected_plant_part,
            "status": "completed",
            "classifications": classifications,
            "phenotype_metrics": (
                result.phenotype_metrics.model_dump()
                if result.phenotype_metrics else None
            ),
            "disclaimer": result.disclaimer,
            "created_at": datetime.now(tz=timezone.utc).isoformat(),
            "image_deleted_at": datetime.now(tz=timezone.utc).isoformat(),
        }
        saved = await self._diagnosis_repo.create(request_doc)
        # Edges cv_diagnosed_for + cv_diagnosis_found anlegen (siehe §2.2)
        await self._diagnosis_repo.link_results(saved["_key"], classifications)

        return {
            "request_key": saved["_key"],
            "classifications": classifications,
            "phenotype_metrics": request_doc["phenotype_metrics"],
            "disclaimer": result.disclaimer,
        }

    async def confirm_classification(
        self, request_key: str, selected_rank: int, *, tenant_key: str
    ) -> dict:
        """Nutzer bestätigt eine Verdachtsdiagnose. Markiert die cv_diagnosis_found-
        Edge als confirmed und gibt — falls eine IPM-Krankheit/Schädling gematcht
        wurde — den Schlüssel für einen Treatment-Vorschlag (REQ-010) zurück.

        WICHTIG: Erzeugt KEINE Behandlung automatisch und umgeht KEIN Karenz-Gate.
        Liefert nur einen Vorschlag, den der Nutzer in REQ-010 explizit startet.
        """
        ...

    @staticmethod
    def _sorted_issues(assessment):
        issues = assessment.diseases + assessment.pests + assessment.abiotic
        return sorted(issues, key=lambda i: i.confidence, reverse=True)

    async def _match_ipm(self, issue) -> dict:
        """Match per scientific_name/common_name gegen diseases/pests (REQ-010)."""
        ...
```

### 3.5 REST-API-Endpunkte

Tenant-scoped, analog REQ-029 §3.7. Consent `plant_diagnosis` ist Pflicht.

```python
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile

router = APIRouter(
    prefix="/api/v1/t/{tenant_slug}/cv-diagnosis",
    tags=["cv-diagnosis"],
)


@router.get("/status")
async def cv_diagnosis_status(service=Depends(get_cv_diagnosis_service)) -> dict:
    """Verfügbarkeit: Klassifikator-Modell geladen? PlantCV verfügbar? (Buttons ein/aus)."""
    return await service.get_status()


@router.post("/diagnose")
async def cv_diagnose(
    tenant_slug: str,
    image: UploadFile = File(..., description="JPEG/PNG, max 5 MB"),
    plant_instance_key: str | None = Form(None),
    planting_run_key: str | None = Form(None),
    inspection_key: str | None = Form(None),
    affected_plant_part: str = Form("leaf"),
    include_phenotype: bool = Form(True),
    language: str = Form("de"),
    user=Depends(get_current_user),
    consent=Depends(require_consent("plant_diagnosis")),
    service=Depends(get_cv_diagnosis_service),
) -> dict:
    """CV-gestützte Zustandsdiagnose aus einem Foto.

    **Consent erforderlich:** `plant_diagnosis`.
    Antwort enthält IMMER einen Disclaimer (nur Hypothese).
    """
    if image.content_type not in ("image/jpeg", "image/png"):
        raise HTTPException(400, "Only JPEG and PNG images are accepted")
    image_data = await image.read()
    try:
        return await service.diagnose(
            image_data,
            tenant_key=user.tenant_key,
            user_key=user.user_key,
            plant_instance_key=plant_instance_key,
            planting_run_key=planting_run_key,
            inspection_key=inspection_key,
            affected_plant_part=affected_plant_part,
            include_phenotype=include_phenotype,
            language=language,
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc))


@router.post("/diagnose/{request_key}/confirm")
async def confirm_cv_classification(
    tenant_slug: str,
    request_key: str,
    selected_rank: int = Query(..., ge=1, le=10),
    user=Depends(get_current_user),
    service=Depends(get_cv_diagnosis_service),
) -> dict:
    """Bestätigt eine Verdachtsdiagnose und liefert ggf. einen IPM-Treatment-Vorschlag.

    Startet KEINE Behandlung — nur ein Vorschlag (REQ-010 Karenz-Gate bleibt aktiv).
    """
    try:
        return await service.confirm_classification(
            request_key, selected_rank, tenant_key=user.tenant_key
        )
    except ValueError as exc:
        raise HTTPException(404, str(exc))


@router.get("/history")
async def cv_diagnosis_history(
    tenant_slug: str,
    plant_instance_key: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    user=Depends(get_current_user),
    service=Depends(get_cv_diagnosis_service),
) -> list[dict]:
    """CV-Diagnose-Historie (optional pro Pflanze gefiltert)."""
    return await service.get_history(
        tenant_key=user.tenant_key,
        plant_instance_key=plant_instance_key,
        limit=limit,
    )
```

### 3.6 Celery-Task (Latenztoleranz)

```python
# Schwere PlantCV-/ONNX-Inferenz kann via Celery ausgelagert werden, damit der
# Request-Pfad nicht blockiert (analog REQ-029-A AE-6).
#   @celery_app.task(name="cv_diagnosis.run")
#   def run_cv_diagnosis(request_key: str) -> None: ...
# Frontend pollt /history bzw. den Request-Status (status: pending → completed).
```

### 3.7 Konfiguration (Settings)

```python
class Settings(BaseSettings):
    # REQ-038: CV-Pflanzendiagnose (alle optional, self-hosted Default)
    cv_diagnosis_enabled: bool = False
    cv_classifier_model_path: str | None = None          # ONNX-Modellpfad
    cv_classifier_model_version: str = "unset"
    cv_diagnosis_confidence_show: float = 0.10
    cv_diagnosis_confidence_highlight: float = 0.75
    cv_diagnosis_max_image_size_mb: int = 5
    cv_phenotype_enabled: bool = True                    # PlantCV-Metriken
    inference_service_url: str | None = None             # wiederverwendet (REQ-029-A)
```

## 4. Frontend-Integration

### 4.1 Wiederverwendung und neue Komponenten

Die Erfassung (Kamera/Upload, EXIF-Strip) kommt aus **REQ-052** (Profil `recognition`); die Organ-Auswahl aus dem `PlantIdentificationDialog` (REQ-029 §4.1) wiederverwendet. Neu ist die **Ergebnis-Darstellung** mit Disclaimer und Phänotyp-Metriken.

| Komponente | Beschreibung |
|------------|--------------|
| `CvDiagnosisDialog` | Modal mit Foto-Erfassung (wiederverwendet) + Ergebnis-Tab |
| Disclaimer-Banner | **Immer sichtbar**, prominent: „Nur eine Hypothese — bitte fachlich bestätigen" (Caveat C-3) |
| Verdachtsliste | Top-3 Cards mit Konfidenz-Bar, Kategorie-Chip (Krankheit/Mangel/Schädling), gematchtem IPM-Eintrag |
| Bestätigen-Button | „Diese Diagnose bestätigen" → `/confirm` → ggf. IPM-Treatment-Vorschlag (REQ-010) |
| Phänotyp-Panel | Blattfläche, Grün-Index, verfärbter/nekrotischer Flächenanteil (nur Intermediate/Expert, REQ-021) |
| Fehlerzustände | Feature nicht aktiviert, kein Pflanzenmaterial, niedrige Konfidenz, kein Match |

### 4.2 Integration in bestehende Seiten

| Seite | Integration | Bedingung |
|-------|-------------|-----------|
| **IPM-Inspektion** (REQ-010) | Button „Foto-Diagnose" im Inspektions-Dialog; Ergebnis kann als `detected`-Vorschlag übernommen werden | `cv_diagnosis_status.available == true` |
| **KI-Diagnose-Assistent** (REQ-036) | In Schritt 3 (Foto-Anhang): CV-Hypothese belegt passende Symptom-Slugs vor und fließt als Kontext in den KB-Prompt | REQ-036 aktiv + Consent |
| **PlantInstance-Detail** | Tab „CV-Diagnose-Historie" + Phänotyp-Verlaufsdiagramm (REQ-007-Brücke) | immer (Historie) |
| **Pflege-Dashboard** (REQ-022) | Quick-Action „Pflanze krank? Foto-Diagnose" | `cv_diagnosis_status.available == true` |

### 4.3 Erfahrungsstufen (REQ-021)

| Element | Beginner | Intermediate | Expert |
|---------|----------|-------------|--------|
| Disclaimer | Groß, Klartext | Sichtbar | Sichtbar |
| Konfidenz-Werte | Ampel (hoch/mittel/niedrig) | Prozent | Prozent + Raw |
| Phänotyp-Metriken | Ausgeblendet | Kernwerte | Alle Metriken + JSON |
| Modell-Provenienz | Ausgeblendet | Ausgeblendet | Modellkarte sichtbar |

### 4.4 i18n-Keys (Auszug)

```json
{
  "pages": {
    "cvDiagnosis": {
      "title": "Foto-Diagnose",
      "analyzing": "Bild wird analysiert...",
      "disclaimer": "Dies ist nur eine Vermutung der Bilderkennung und keine gesicherte Diagnose. Bitte bestätige den Befund fachlich, bevor du behandelst.",
      "suspectedIssues": "Mögliche Ursachen",
      "categoryDisease": "Krankheit",
      "categoryPest": "Schädling",
      "categoryDeficiency": "Nährstoffmangel",
      "confirm": "Diese Vermutung bestätigen",
      "suggestTreatment": "Behandlung vorschlagen (IPM)",
      "phenotypeTitle": "Bild-Kennzahlen",
      "leafArea": "Blattfläche",
      "discoloredRatio": "Anteil verfärbter Fläche",
      "necroticRatio": "Anteil abgestorbener Fläche",
      "notAvailable": "Foto-Diagnose ist nicht eingerichtet.",
      "lowConfidence": "Keine ausreichend sichere Vermutung. Bitte manuell prüfen.",
      "notAPlant": "Es konnte kein Pflanzenmaterial erkannt werden."
    }
  }
}
```

## 5. Konfiguration, Deployment & Lizenz

### 5.1 DSGVO-Konformität (REQ-025, wiederverwendet aus REQ-029)

| Aspekt | Umsetzung |
|--------|-----------|
| **Consent** | Neuer Zweck `plant_diagnosis` (analog `plant_identification`, REQ-029 §5). Im Self-Hosted-Pfad weist der Hinweis darauf hin, dass Fotos die Instanz nicht verlassen. |
| **EXIF-Stripping** | Wiederverwendung REQ-029 §5.4 (Metadaten vor Verarbeitung entfernen). |
| **Bild-Persistenz** | Bilddaten werden **nicht** dauerhaft gespeichert (`image_deleted_at` gesetzt). Nur Hash + Ergebnisse bleiben. |
| **Retention** | `plant_diagnosis_requests` unterliegt der DSGVO-Retention (NFR-011); Default-Löschfrist konfigurierbar. |
| **Self-Hosted Default** | `cv_diagnosis_enabled=False`; bei Aktivierung läuft Inferenz lokal (keine Drittland-Verarbeitung). |

### 5.2 Deployment

- **Inference-Service** (REQ-029-A §3) wird um den Endpunkt `/classify/disease` erweitert — **kein** neuer Microservice. ONNX-Runtime und CPU-Baseline bleiben.
- **PlantCV** wird als Python-Dependency im Inference-Service (bzw. Backend, falls Phänotyp dort läuft) installiert; bringt OpenCV/NumPy/Matplotlib mit (Container-Größe beachten).
- **Modell-Artefakt** (ONNX) wird wie das DINOv2-Modell über ein Volume/Init-Container bereitgestellt; nicht im Image gebacken.

```yaml
# helm/kamerplanter/values.yaml (Ergänzung)
backend:
  env:
    CV_DIAGNOSIS_ENABLED: "false"          # opt-in
    CV_PHENOTYPE_ENABLED: "true"
    CV_DIAGNOSIS_CONFIDENCE_SHOW: "0.10"
    CV_DIAGNOSIS_CONFIDENCE_HIGHLIGHT: "0.75"
    # CV_CLASSIFIER_MODEL_PATH: "/models/leaf-disease-v1.onnx"  # via secret/volume
```

### 5.3 Lizenz-Hygiene (Caveat C-6)

| Komponente | Lizenz | Pflicht |
|------------|--------|---------|
| PlantDoc-Datensatz (primäre Trainingsquelle) | **CC-BY-4.0** | Attribution; kommerzielle Nutzung + Modell-Weitergabe ohne ShareAlike erlaubt; abgeleitete Gewichte unter Attribution frei verwendbar (Caveat C-2) |
| PlantCV (Bibliothek) | **MPL-2.0** | Datei-Level-Copyleft: **unverändert als Library nutzen, KEINE PlantCV-Quelldateien patchen**; MPL-2.0-Notice mitliefern; reine Nutzung als Dependency unkritisch (Caveat C-6) |
| PlantVillage-Datensatz | **ungeklärt** (Repo ohne LICENSE; CC-BY-SA 3.0 ↔ CC0 widersprüchlich) | **NICHT verwenden** — Lizenzrisiko für MIT-App; höchstens als historischer Benchmark erwähnen; siehe Lizenzanalyse `spec/analysis/awesome-agriculture-lizenz-und-nutzungsanalyse.md` (G1-Entscheidung) |
| ONNX-Backbone (ImageNet/DINOv2) | Apache-2.0 (DINOv2) | `LICENSE` vor Produktivnahme verifizieren (REQ-029-A AE-7-analog) |

## 6. Abhängigkeiten

**Erforderliche existierende Collections/Beziehungen:**
- `diseases`, `pests`, `inspections`, `treatments` aus REQ-010 (IPM) — Matching-Ziele
- `plant_instances` aus REQ-001, `planting_runs` aus REQ-013 (Dual-Support)
- `harvest_observations` aus REQ-007 (Phänotyp-Verknüpfung)
- `symptoms`, `diagnosis_sessions` aus REQ-036 (Symptom-Slug-Vorbelegung)
- `consent_records` aus REQ-025 (Consent `plant_diagnosis`)

**Wiederverwendete Infrastruktur:**
- `PlantIdentificationAdapter`-Interface + `IdentificationAdapterRegistry` (REQ-029 §3.1/§3.4)
- EXIF-Stripping + Consent-Mechanismus (REQ-029 §5)
- Inference-Microservice + ONNX-Runtime-Pattern (REQ-029-A §3)
- Erfassungsbaustein REQ-052 §2 (Profil `recognition`, REQ-052 §3)

**Neue Abhängigkeiten:**
- `plantcv` (MPL-2.0) als Python-Dependency — unverändert als Library, keine Patches an PlantCV-Quelldateien (Caveat C-6)
- ONNX-Disease-Klassifikator-Artefakt (Build-Pipeline: ImageNet/DINOv2-Backbone-Vortraining → PlantDoc-CC-BY-4.0-Fine-Tuning + eigene Realdaten → ONNX-Export; PlantVillage wird nicht verwendet)

**Integrationsschnittstellen:**
- **REQ-010 (IPM):** CV-Diagnose erzeugt `detected`-/Treatment-**Vorschläge**; Karenz-Gate bleibt unberührt
- **REQ-036 (Diagnose-Assistent):** Foto-Hypothese als Vorab-Kontext + Symptom-Slug-Vorbelegung
- **REQ-007 (Ernte):** Phänotyp-Metriken als zusätzliche Reife-/Ertragsindikatoren
- **REQ-031 (Knowledge-Service):** mögliche Co-Lokation des Klassifikator-Endpunkts

## 7. Akzeptanzkriterien

### Definition of Done (DoD)

- [ ] **Adapter registriert:** Ein `CvDiagnosisAdapter` (z. B. `local_cv_classifier`) ist in der bestehenden `IdentificationAdapterRegistry` (REQ-029 §3.4) registriert; ohne Modell/aktiviertes Feature meldet `/status` „nicht verfügbar" und die App bleibt voll funktionsfähig.
- [ ] **Self-hosted Inferenz:** Der Disease-Klassifikator läuft als ONNX-Endpunkt im bestehenden Inference-Service (kein neuer Microservice); Nutzerfotos verlassen die Instanz im Self-Hosted-Pfad nicht.
- [ ] **PlantCV-Phänotyp:** Die `PhenotypeEngine` liefert für ein Blattfoto mindestens Blattfläche, Grün-Index, verfärbten und nekrotischen Flächenanteil; `plantcv_version` wird protokolliert.
- [ ] **IPM-Mapping:** Erkannte Krankheiten/Schädlinge werden über `cv_diagnosis_found`-Edges gegen `diseases`/`pests` (REQ-010) gemappt; nicht gematchte Treffer bleiben mit `matched_*_key == null` erhalten.
- [ ] **Treatment-Vorschlag, kein Auto-Trigger:** Bei Bestätigung einer gematchten Krankheit wird ein IPM-Treatment **vorgeschlagen**, aber **nie** automatisch angelegt; das Karenz-Gate (REQ-010) wird nicht umgangen.
- [ ] **Disclaimer immer präsent:** Jede API-Antwort und jede UI-Ergebnisanzeige trägt den Hypothesen-Disclaimer (Caveat C-3); ein automatisierter Test prüft, dass das Feld `disclaimer` nie leer ist.
- [ ] **Confidence-Schwellen:** Ergebnisse unter `CONFIDENCE_SHOW` werden verworfen; oberhalb `CONFIDENCE_HIGHLIGHT` erfolgt nur Hervorhebung, **kein** Auto-Anlegen.
- [ ] **Consent + EXIF:** `/diagnose` erfordert Consent `plant_diagnosis`; EXIF wird vor Verarbeitung entfernt; Bilddaten werden nicht persistiert (`image_deleted_at` gesetzt).
- [ ] **REQ-036-Brücke:** Bei aktivem Diagnose-Assistenten und Consent belegt eine Foto-Hypothese passende Symptom-Slugs vor und fließt als Kontext in den KB-Prompt.
- [ ] **REQ-007-Brücke:** Phänotyp-Metriken sind pro Pflanze über die Zeit abfragbar und in der Detailseite als Verlauf darstellbar.
- [ ] **Modellkarte/Provenienz:** `model_meta` dokumentiert `training_base` (generisches Backbone, z. B. `imagenet-dinov2-backbone`), `fine_tuned_on` (PlantDoc CC-BY-4.0 + Realdaten), `model_version` und ONNX-Checksumme; PlantVillage ist **nicht** als Trainingsquelle gelistet.
- [ ] **Lizenz-Dokumentation:** PlantDoc (CC-BY-4.0, Attribution) und PlantCV (MPL-2.0) sind in der Lizenz-Übersicht des Projekts erfasst; PlantVillage ist als **nicht verwendet** (Lizenz ungeklärt) markiert (Caveat C-6, Lizenzanalyse `spec/analysis/awesome-agriculture-lizenz-und-nutzungsanalyse.md`).
- [ ] **Erfahrungsstufen:** Phänotyp-Metriken und Modell-Provenienz sind erst ab Intermediate/Expert sichtbar (REQ-021); Konfidenz für Beginner als Ampel.

### Testszenarien

**Szenario 1: Foto-Diagnose mit IPM-Match**
```
GIVEN: CV-Diagnose aktiviert, Consent plant_diagnosis erteilt, IPM-Stammdaten enthalten "Septoria"
WHEN:  Nutzer fotografiert ein Blatt mit braunen Flecken im Inspektions-Dialog (REQ-010)
THEN:
  - Verdachtsliste Top-1 "Septoria-Blattfleckenkrankheit" (Konfidenz 0.74) mit Disclaimer
  - cv_diagnosis_found-Edge zu disease_septoria angelegt
  - "Behandlung vorschlagen" bietet ein IPM-Treatment an (Karenz-Gate aktiv)
  - KEINE Behandlung wird automatisch angelegt
```

**Szenario 2: Mangel statt Krankheit**
```
GIVEN: Blattfoto mit gleichmäßiger Gelbfärbung unterer Blätter
WHEN:  CV-Diagnose läuft
THEN:
  - Top-Kategorie "deficiency" (Stickstoffmangel), matched_disease_key == null
  - REQ-036-Brücke belegt Symptom-Slug "leaves_yellowing_lower" vor
  - Disclaimer weist auf nötige fachliche Bestätigung hin
```

**Szenario 3: Domänen-Gap / niedrige Konfidenz (Caveat C-1)**
```
GIVEN: Foto einer Zimmerpflanze mit unruhigem Hintergrund (nicht Lab-Domäne)
WHEN:  CV-Klassifikator liefert nur Konfidenzen < CONFIDENCE_SHOW
THEN:
  - System zeigt "Keine ausreichend sichere Vermutung — bitte manuell prüfen"
  - Verweis auf manuelle IPM-Suche / Diagnose-Assistent (REQ-036)
  - Phänotyp-Metriken werden dennoch berechnet und gespeichert
```

**Szenario 4: Phänotyp-Verlauf (REQ-007)**
```
GIVEN: 5 CV-Diagnosen derselben Pflanze über 3 Wochen
WHEN:  Nutzer öffnet den Phänotyp-Verlauf in der PlantInstance-Detailseite
THEN:
  - Blattfläche, Grün-Index und verfärbter Flächenanteil als Zeitreihe dargestellt
  - steigender necrotic_area_ratio ist als Trend erkennbar
```

**Szenario 5: Feature deaktiviert**
```
GIVEN: cv_diagnosis_enabled == false
WHEN:  Frontend lädt eine Seite mit Foto-Diagnose-Button
THEN:
  - /status meldet available == false
  - Buttons sind ausgeblendet; restliche App voll funktionsfähig
```

---

**Hinweise für RAG-Integration:**
- Keywords: CV-Diagnose, Bilderkennung, Krankheitserkennung, Mangelerkennung, Schädlingserkennung, PlantDoc, PlantCV, Phänotyp, Blattfläche, ONNX, Transfer Learning, Lab-Feld-Gap, Hypothese, Disclaimer
- Verknüpfung: REQ-010 (IPM), REQ-029/029-A (Bilderkennung Art), REQ-036 (Diagnose-Assistent), REQ-007 (Ernte), REQ-025 (DSGVO), REQ-031 (Knowledge-Service)
- Fachbegriffe: Computer Vision, Segmentierung, Phänotyping, Transfer Learning, Confidence-Schwelle, Nekrose, Chlorose
- Lizenzen: PlantDoc = CC-BY-4.0 (primäre Trainingsquelle, Attribution); PlantCV = MPL-2.0 (nicht MIT; nicht patchen); PlantVillage = Lizenz ungeklärt (Repo ohne LICENSE, CC-BY-SA↔CC0) → **nicht verwendet** (G1); siehe `spec/analysis/awesome-agriculture-lizenz-und-nutzungsanalyse.md`
- Caveat: PlantVillage ist ein Laborbedingungen-Datensatz (99,35 % Lab → 31,4 % Feld) und wird wegen ungeklärter Lizenz nicht genutzt (nur historischer Benchmark); produktiver Klassifikator = generisches Backbone-Vortraining + PlantDoc-Fine-Tuning auf Realdaten
