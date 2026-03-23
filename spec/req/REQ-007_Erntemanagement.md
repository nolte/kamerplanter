# Spezifikation: REQ-007 - Erntemanagement

```yaml
ID: REQ-007
Titel: Gattungsspezifisches Erntemanagement & Reifegradprüfung
Kategorie: Erntezyklus
Fokus: Beides
Technologie: Python, ArangoDB, Computer Vision (optional)
Status: Entwurf
Version: 2.3 (W-007 Ernte-Fenster-Vorhersage integriert)
```

## 1. Business Case

**User Story:** "Als Gärtner möchte ich gattungsspezifische Reife-Indikatoren nutzen, um den optimalen Erntezeitpunkt zu treffen, Qualität und Ertrag zu maximieren, und die gesamte Ernte-zu-Lager-Kette lückenlos zu dokumentieren."

**Beschreibung:**
Das System implementiert einen polymorphen, pflanzenspezifischen Ansatz zur Reifegradbestimmung und Ernteplanung mit vollständiger Rückverfolgbarkeit:

**Pflanzenspezifische Ernte-Indikatoren:**

**1. Blütenstände/Früchte (Cannabis, Hopfen, Blumen):**
- **Trichom-Mikroskopie:**
  - Klar (0-30%) → Unreif, niedriger Wirkstoffgehalt
  - Milchig/Cloudy (50-70%) → Peak THC, ausgewogene Effekte
  - Bernstein/Amber (10-30%) → CBN-Umwandlung, sedierend
- **Calyx-Schwellung:** Blütenhülle vollständig entwickelt
- **Pistil-Färbung:** >70% braun/orange
- **Aroma-Entwicklung:** Terpen-Profil vollständig ausgebildet
- **Harzproduktion:** Maximale Trichom-Dichte

**2. Fruchtgemüse (Tomaten, Paprika, Gurken):**
- **Farbentwicklung:** Grün → Rot/Gelb/Orange (Sortenabhängig)
- **Festigkeit:** Leichter Druck-Nachgabe bei voller Reife
- **Glanz:** Glänzende Schale bei Vollreife
- **Brix-Wert:** Zuckergehalt (Refraktometer-Messung)
- **Größe:** Sorten-typische Dimensionen erreicht

**3. Wurzelgemüse (Kartoffeln, Möhren, Zwiebeln):**
- **Krautsterben:** >80% totes Laub
- **Schalenhärtung:** Feste, nicht-abreibbare Schale
- **Größe/Gewicht:** Optimale Lagerfähigkeit
- **Tage seit Blüte:** Sortenspezifische Richtwerte

**4. Blattgemüse (Salat, Spinat, Kohl):**
- **Kopfgröße:** Fest geschlossen bei Kopfsalaten
- **Textur:** Knackig, nicht bitter
- **Schossgefahr:** Vor Blüten-Bildung ernten
- **Blattfarbe:** Sattgrün, keine Verfärbungen

**Ernte-Strategien:**

**Partial Harvest (Gestaffelte Ernte):**
- Top-Buds zuerst (höchste Lichtexposition = schnellere Reife)
- Lower-Buds 7-10 Tage später
- Kontinuierliche Ernte bei "Cut & Come Again" Kulturen

**Final Harvest (Kompletternte):**
- Einmalige Ernte der gesamten Pflanze
- Optimiert für Uniform-Reife-Sorten

**Pre-Harvest-Protokolle:**

**Flushing (Nährstoffreduktion) — OPTIONAL, wissenschaftlich umstritten:**
Single Source of Truth für substratspezifische Flush-Dauern ist `REQ-004 FlushingProtocol.FLUSH_DURATIONS`. Die folgenden Bereiche dienen als Orientierung:
- **Hydro:** 7–14 Tage nur pH-Wasser (optimal: 10 Tage)
- **Coco:** 10–21 Tage gradueller EC-Abbau (optimal: 14 Tage)
- **Soil:** 21–42 Tage gradueller EC-Abbau (optimal: 28 Tage, CEC-abhängig — siehe REQ-019)
- **Living Soil:** Kein Flushing empfohlen (zerstört Mikrobiom)
- **Kein Flushing (none):** Valide Option — Studie der University of Guelph (2020) fand keinen signifikanten Unterschied in Mineralgehalt, Rauchqualität oder Geschmack zwischen geflushten und ungeflushten Cannabis-Proben. Blindverkostung bevorzugte leicht die ungeflushte Variante.
- **Empfehlung:** System bietet Flushing als optionales Protokoll an. Bei Living Soil oder organischer Düngung wird explizit davon abgeraten.

**Dark Period (Dunkelphase):**
- 24-48h vor Ernte für Terpen-Erhaltung
- Reduziert Photosynthese, erhöht Harzproduktion
- Umstritten, aber in Community weit verbreitet — keine peer-reviewed Evidenz

**Harvest-Timing:**
- **Früh morgens:** Höchste Terpen-Konzentration
- **Nach Dunkelphase:** Weniger Chlorophyll in Pflanze
- **Trockene Bedingungen:** Verhindert Schimmel

**Batch-Tracking & Rückverfolgbarkeit:**

**Seed-to-Shelf Traceability:**
1. **Seed/Clone:** Genetik-ID, Herkunft
2. **Plant Instance:** Standort, Pflege-Historie
3. **Harvest Batch:** Ernte-Datum, Gewicht, Qualität
4. **Processing:** Trocknung, Curing (REQ-008)
5. **Storage:** Lager-Standort, Bestand
6. **Distribution:** Verbrauch/Verkauf

**QR-Code-System:**
- Jeder Batch bekommt eindeutige ID
- QR-Code auf Jar/Verpackung
- Scan zeigt vollständige Historie

## 2. ArangoDB-Modellierung

### Document Collections:
- **`harvest_indicators`** - Reife-Check-Typ
  - Properties:
    - `indicator_id: str`
    - `indicator_type: Literal['trichome', 'foliage', 'brix', 'size', 'color', 'days_since_flowering', 'aroma', 'texture', 'mushroom', 'gdd', 'continuous_harvest']`
    - `measurement_unit: Optional[str]` (z.B. "%", "°Brix", "cm")
    - `measurement_method: str` (z.B. "60x Mikroskop", "Refraktometer")
    - `observation_frequency: Literal['daily', 'weekly', 'biweekly']`
    - `reliability_score: float` (0-1, wie verlässlich ist dieser Indikator)

- **`ripeness_stages`** - Reifestadium
  - Properties:
    - `stage_id: str`
    - `stage_name: str` (z.B. "immature", "approaching", "peak", "overripe")
    - `description: str`
    - `visual_cues: list[str]`
    - `recommended_action: str`
    - `harvest_window_days: Optional[int]` (Fenster bis Überreife)
    - `quality_impact: int` (-100 bis 100, Qualitäts-Score)
    - `potency_level: Optional[str]` (für Wirkstoff-Pflanzen)

- **`batches`** - Ernte-Charge
  - Properties:
    - `batch_id: str` (Format: "PLANT_ID_YYYYMMDD_SEQ")
    - `harvest_date: date`
    - `harvest_time: time`
    - `harvest_type: Literal['partial', 'final', 'continuous']`
    - `wet_weight_g: float`
    - `estimated_dry_weight_g: Optional[float]`
    - `actual_dry_weight_g: Optional[float]` (nach Trocknung)
    - `quality_grade: Literal['A+', 'A', 'B', 'C', 'D']`
    - `harvester: str` (User-ID)
    - `harvest_environment: Optional[HarvestEnvironment]` (strukturierte Umwelterfassung, siehe U-004)
    - `harvest_tool: Optional[str]` (verwendetes Erntewerkzeug, z.B. "Fiskars micro-tip pruner", "Felco 310")
    - `tool_sanitized: Optional[bool]` (Werkzeug vor Ernte desinfiziert? Pflicht bei Partial Harvest)
    - `container_type: Optional[str]` (Erntebehälter, z.B. "mesh_tray", "paper_bag", "bucket")
    - `notes: Optional[str]`
    - `qr_code_url: str`
    - `karenz_check_passed: bool` (REQ-010 Pflicht-Check)

- **`quality_assessments`** - Qualitätsbewertung
  - Properties:
    - `assessment_id: str`
    - `assessed_at: datetime`
    - `assessed_by: str`
    - `appearance_score: int` (0-100)
    - `aroma_score: int` (0-100)
    - `trichome_coverage_score: Optional[int]` (0-100, Cannabis)
    - `bud_density_score: Optional[int]` (0-100)
    - `color_score: int` (0-100)
    - `defects: list[str]` (Schimmel, Schädlinge, Hermaphroditismus)
    - `overall_score: int` (0-100, gewichteter Durchschnitt)
    - `grade: Literal['A+', 'A', 'B', 'C', 'D']`
    - `potency_estimate: Optional[str]` (z.B. "High THC", "Balanced")
    - `terpene_profile: Optional[dict]` (Dominante Terpene)

- **`harvest_observations`** - Reife-Check-Messung
  - Properties:
    - `observation_id: str`
    - `observed_at: datetime`
    - `observer: str`
    - `indicator_type: str`
    - `measurements: dict` (z.B. {"clear": 20, "cloudy": 70, "amber": 10})
    - `photo_refs: list[str]`
    - `ripeness_assessment: str`
    - `days_to_harvest_estimate: Optional[int]`

- **`pre_harvest_protocols`** - Vorbereitungs-Protokoll
  - Properties:
    - `protocol_id: str`
    - `protocol_type: Literal['flushing', 'dark_period', 'drought_stress', 'defoliation', 'none']` (none = bewusst kein Flushing, z.B. Living Soil)
    - `started_at: datetime`
    - `duration_days: int`
    - `completed_at: Optional[datetime]`
    - `parameters: dict` (z.B. {"ec_start": 1.8, "ec_target_additional": 0.0, "base_water_ec": 0.3})

- **`yield_metrics`** - Ertrags-Metrik
  - Properties:
    - `metric_id: str`
    - `yield_per_plant_g: float`
    - `yield_per_m2_g: Optional[float]`
    - `total_yield_g: float`
    - `trim_waste_percent: float`
    - `usable_yield_g: float`

### Edge Collections:
```
has_harvest_indicator:       species → harvest_indicators
has_stage:                   harvest_indicators → ripeness_stages
observed_for_harvest:        planting_runs|plant_instances → harvest_observations   // Dual-Support (REQ-013 v2.0)
uses_indicator:              harvest_observations → harvest_indicators
underwent_protocol:          planting_runs|plant_instances → pre_harvest_protocols  // Dual-Support
harvested_as:                planting_runs|plant_instances → batches                // Dual-Support (Run primaer via run_produced)
assessed_by:                 batches → quality_assessments
has_yield_metric:            batches → yield_metrics
stored_in:                   batches → storage_locations          // Übergabe an REQ-008
derived_from:                batches → plant_instances             // Bei Partial Harvest (Attribut: portion)
triggered_by:                pre_harvest_protocols → harvest_observations
```

### AQL-Beispiellogik:

**Erntebereitschaft mit Multi-Indicator-Aggregation:**
```aql
// Dual-Support (REQ-013 v2.0): entity_id = planting_runs/... oder plant_instances/...
LET entity = DOCUMENT(@entity_id)
// Species-Aufloesung: Bei Runs ueber has_entry → entry_for_species, bei Plants ueber belongs_to_species
LET species = FIRST(
  FOR v IN 1..2 OUTBOUND entity GRAPH 'kamerplanter_graph'
    OPTIONS { edgeCollections: ['belongs_to_species', 'has_entry', 'entry_for_species'] }
    FILTER IS_SAME_COLLECTION('species', v)
    RETURN v
)

// Hole alle Indikatoren der Spezies
LET indicators_raw = (
  FOR indicator IN 1..1 OUTBOUND species GRAPH 'kamerplanter_graph'
    OPTIONS { edgeCollections: ['has_harvest_indicator'] }

    // Hole letzte Observation pro Indikator (innerhalb 7 Tage)
    LET observations = (
      FOR obs IN 1..2 OUTBOUND plant GRAPH 'kamerplanter_graph'
        OPTIONS { edgeCollections: ['observed_for_harvest', 'uses_indicator'] }
        FILTER IS_SAME_COLLECTION('harvest_observations', obs)
        FILTER obs.observed_at > DATE_SUBTRACT(DATE_NOW(), 7, 'days')
        // Prüfe ob Observation diesen Indikator nutzt
        LET uses = (
          FOR target IN 1..1 OUTBOUND obs GRAPH 'kamerplanter_graph'
            OPTIONS { edgeCollections: ['uses_indicator'] }
            FILTER target._id == indicator._id
            RETURN target
        )
        FILTER LENGTH(uses) > 0
        SORT obs.observed_at DESC
        LIMIT 1
        RETURN obs
    )
    LET latest_obs = FIRST(observations)

    // Bestimme Ripeness-Stage basierend auf Observation
    LET stage = (latest_obs != null
      ? FIRST(
          FOR s IN 1..1 OUTBOUND indicator GRAPH 'kamerplanter_graph'
            OPTIONS { edgeCollections: ['has_stage'] }
            FILTER s.stage_name == latest_obs.ripeness_assessment
            RETURN s
        )
      : null
    )

    RETURN {
      indicator: indicator.indicator_type,
      stage: stage.stage_name,
      quality_impact: stage.quality_impact,
      days_to_harvest: latest_obs.days_to_harvest_estimate,
      reliability: indicator.reliability_score,
      observation_age_days: latest_obs != null
        ? DATE_DIFF(latest_obs.observed_at, DATE_NOW(), 'days')
        : null
    }
)

// Berechne gewichteten Gesamt-Score
LET weighted_score = (
  LENGTH(indicators_raw) > 0
    ? SUM(FOR ind IN indicators_raw RETURN ind.quality_impact * ind.reliability)
      / LENGTH(indicators_raw)
    : 0
)

LET days_estimates = (
  FOR ind IN indicators_raw
    FILTER ind.days_to_harvest != null
    RETURN ind.days_to_harvest
)
LET avg_days_to_harvest = LENGTH(days_estimates) > 0
  ? AVERAGE(days_estimates)
  : null

RETURN {
  plant_id: plant.instance_id,
  overall_readiness_score: ROUND(weighted_score, 1),
  estimated_days_to_harvest: ROUND(avg_days_to_harvest),
  harvest_recommendation: (
    weighted_score >= 90 ? 'OPTIMAL - Ernten innerhalb 24-48h' :
    weighted_score >= 70 ? 'APPROACHING - Ernten innerhalb 3-7 Tagen' :
    weighted_score >= 50 ? 'DEVELOPING - Noch 7-14 Tage' :
    'IMMATURE - Mindestens 14 Tage warten'
  ),
  indicators: indicators_raw
}
```

**Flushing-Trigger mit automatischer Protokoll-Erstellung:**
```aql
LET plant = DOCUMENT('plant_instances', @plant_id)

// Hole letzte Observations mit days_to_harvest <= 14 (innerhalb 3 Tage)
LET recent_obs = FIRST(
  FOR obs IN 1..1 OUTBOUND plant GRAPH 'kamerplanter_graph'
    OPTIONS { edgeCollections: ['observed_for_harvest'] }
    FILTER obs.observed_at > DATE_SUBTRACT(DATE_NOW(), 3, 'days')
    FILTER obs.days_to_harvest_estimate <= 14
    SORT obs.observed_at DESC
    LIMIT 1
    RETURN obs
)

// Prüfe ob Flushing bereits läuft
LET existing_flushing = FIRST(
  FOR proto IN 1..1 OUTBOUND plant GRAPH 'kamerplanter_graph'
    OPTIONS { edgeCollections: ['underwent_protocol'] }
    FILTER proto.protocol_type == 'flushing'
    FILTER proto.completed_at == null
    RETURN proto
)

// Hole Substrat-Typ für Flushing-Dauer
LET substrate_info = FIRST(
  FOR sub IN 1..1 OUTBOUND plant GRAPH 'kamerplanter_graph'
    OPTIONS { edgeCollections: ['grown_in'] }
    LET sub_type = FIRST(
      FOR t IN 1..1 OUTBOUND sub GRAPH 'kamerplanter_graph'
        OPTIONS { edgeCollections: ['uses_type'] }
        RETURN t
    )
    RETURN { substrate_type: sub_type.type }
)

LET substrate_type = substrate_info.substrate_type
LET days_to_harvest = recent_obs.days_to_harvest_estimate
// Flush-Dauern: Single Source of Truth ist REQ-004 FlushingProtocol.FLUSH_DURATIONS
// Hier werden die 'optimal'-Werte verwendet. Bereiche siehe REQ-004.
LET required_flush_days = (
  substrate_type == 'living_soil' ? 0 :       // Kein Flushing — Mikrobiom schützen
  substrate_type IN ['none', 'clay_pebbles'] ? 10 :  // Hydro: optimal 10 (Bereich 7–14, REQ-004)
  substrate_type == 'coco' ? 14 :             // Coco: optimal 14 (Bereich 10–21, REQ-004)
  substrate_type == 'soil' ? 28 :             // Soil: optimal 28 (Bereich 21–42, REQ-004, CEC-abhängig)
  14                                          // Fallback für sonstige Substrate
)

// Nur ausführen wenn kein Flushing aktiv und Zeit ausreicht
FILTER existing_flushing == null
FILTER recent_obs != null
FILTER days_to_harvest >= required_flush_days

// Erstelle Flushing-Protokoll
LET protocol = FIRST(
  INSERT {
    protocol_id: UUID(),
    protocol_type: 'flushing',
    started_at: DATE_NOW(),
    duration_days: required_flush_days,
    parameters: {
      substrate_type: substrate_type,
      target_ec_additional: 0.0,  // Additiv zum Basis-Wasser-EC (REQ-004: ec_net)
      base_water_ec: 0.3,        // Lokaler Leitungswasser-EC
      start_ec: 1.8              // Aus letzter Messung
    }
  } INTO pre_harvest_protocols
  RETURN NEW
)

// Verknüpfe Pflanze mit Protokoll
INSERT { _from: plant._id, _to: protocol._id } INTO underwent_protocol

// Erstelle Task für tägliche Überprüfung
LET task = FIRST(
  INSERT {
    task_id: UUID(),
    name: 'Flushing - Tägliche Kontrolle',
    category: 'harvest_prep',
    instruction: 'Prüfe Runoff-EC (Ziel: <0.5 mS). Gieße mit pH-Wasser (6.0-6.5).',
    due_date: DATE_FORMAT(DATE_NOW(), '%yyyy-%mm-%dd'),
    status: 'pending',
    priority: 'high',
    estimated_duration_minutes: 10,
    created_at: DATE_NOW()
  } INTO tasks
  RETURN NEW
)

INSERT { _from: plant._id, _to: task._id } INTO has_task

RETURN {
  flushing_started: true,
  duration_days: required_flush_days,
  substrate_type: substrate_type,
  estimated_harvest_date: DATE_ADD(DATE_NOW(), required_flush_days, 'days'),
  task_created: task.task_id
}
```

**Batch-Erstellung mit QR-Code-Generierung:**
```aql
LET plant = DOCUMENT('plant_instances', @plant_id)

// Generiere Batch-ID
LET batch_id = CONCAT(plant.instance_id, '_', DATE_FORMAT(DATE_NOW(), '%yyyy%mm%dd'), '_001')

// Erstelle Batch
LET batch = FIRST(
  INSERT {
    batch_id: batch_id,
    harvest_date: DATE_FORMAT(DATE_NOW(), '%yyyy-%mm-%dd'),
    harvest_time: DATE_FORMAT(DATE_NOW(), '%hh:%ii:%ss'),
    harvest_type: @harvest_type,
    wet_weight_g: @wet_weight,
    estimated_dry_weight_g: @wet_weight * @dry_weight_factor,  // Artspezifisch: Cannabis 0.25, Tomate 0.06, Kartoffel 0.20 etc.
    quality_grade: 'B',  // Initial, wird später bewertet
    harvester: @user_id,
    qr_code_url: CONCAT('https://api.qrserver.com/v1/create-qr-code/?data=', batch_id, '&size=200x200'),
    notes: @notes
  } INTO batches
  RETURN NEW
)

// Verknüpfe mit Plant
INSERT { _from: plant._id, _to: batch._id, portion: @portion } INTO harvested_as

// Erstelle Yield-Metrik
LET slot = FIRST(
  FOR s IN 1..1 OUTBOUND plant GRAPH 'kamerplanter_graph'
    OPTIONS { edgeCollections: ['placed_in'] }
    RETURN s
)

LET location = FIRST(
  FOR loc IN 1..1 INBOUND slot GRAPH 'kamerplanter_graph'
    OPTIONS { edgeCollections: ['has_slot'] }
    RETURN loc
)

LET area_m2 = location.area_m2

LET yield_metric = FIRST(
  INSERT {
    metric_id: UUID(),
    yield_per_plant_g: batch.wet_weight_g,
    yield_per_m2_g: area_m2 != null ? batch.wet_weight_g / area_m2 : null,
    total_yield_g: batch.wet_weight_g,
    trim_waste_percent: 0  // Wird später aktualisiert
  } INTO yield_metrics
  RETURN NEW
)

INSERT { _from: batch._id, _to: yield_metric._id } INTO has_yield_metric

RETURN {
  batch_id: batch.batch_id,
  qr_code_url: batch.qr_code_url,
  wet_weight_g: batch.wet_weight_g,
  estimated_dry_weight_g: batch.estimated_dry_weight_g,
  harvest_date: batch.harvest_date
}
```

**Seed-to-Shelf Traceability:**
```aql
// Traversiere den vollständigen Pfad: Seed → Plant → Batch → Storage
FOR seed IN seeds
  FOR plant IN 1..1 OUTBOUND seed GRAPH 'kamerplanter_graph'
    OPTIONS { edgeCollections: ['grew_into'] }
    FOR batch IN 1..1 OUTBOUND plant GRAPH 'kamerplanter_graph'
      OPTIONS { edgeCollections: ['harvested_as'] }
      FILTER batch.batch_id == @batch_id
      FOR storage IN 1..1 OUTBOUND batch GRAPH 'kamerplanter_graph'
        OPTIONS { edgeCollections: ['stored_in'] }

        // Hole alle Pre-Harvest-Protokolle
        LET protocols = (
          FOR proto IN 1..1 OUTBOUND plant GRAPH 'kamerplanter_graph'
            OPTIONS { edgeCollections: ['underwent_protocol'] }
            RETURN DISTINCT proto
        )

        // Hole Quality-Assessment
        LET qa = FIRST(
          FOR assessment IN 1..1 OUTBOUND batch GRAPH 'kamerplanter_graph'
            OPTIONS { edgeCollections: ['assessed_by'] }
            RETURN assessment
        )

        // Hole letzte 5 Feedings
        LET recent_feedings = (
          FOR feeding IN 1..1 OUTBOUND plant GRAPH 'kamerplanter_graph'
            OPTIONS { edgeCollections: ['fed_by'] }
            SORT feeding.fed_at DESC
            LIMIT 5
            RETURN DISTINCT feeding
        )

        // Hole Genetik-Info
        LET strain = FIRST(
          FOR s IN 1..1 OUTBOUND seed GRAPH 'kamerplanter_graph'
            OPTIONS { edgeCollections: ['from_strain'] }
            RETURN s
        )

        RETURN {
          seed_to_shelf_id: batch.batch_id,

          genetics: {
            strain: strain.name,
            breeder: strain.breeder,
            seed_id: seed.seed_id,
            germination_date: seed.germinated_at
          },

          cultivation: {
            planted_on: plant.planted_on,
            harvest_date: batch.harvest_date,
            total_days: DATE_DIFF(plant.planted_on, batch.harvest_date, 'days'),
            location: plant.location_id,
            growth_system: plant.growth_system
          },

          pre_harvest: (
            FOR p IN protocols
              RETURN {
                type: p.protocol_type,
                duration_days: p.duration_days,
                started: p.started_at
              }
          ),

          harvest: {
            batch_id: batch.batch_id,
            wet_weight_g: batch.wet_weight_g,
            dry_weight_g: batch.actual_dry_weight_g,
            quality_grade: batch.quality_grade,
            harvester: batch.harvester
          },

          quality: {
            overall_score: qa.overall_score,
            appearance: qa.appearance_score,
            aroma: qa.aroma_score,
            defects: qa.defects,
            potency: qa.potency_estimate
          },

          storage: {
            location: storage.location,
            stored_since: batch.stored_at,
            current_weight_g: storage.current_weight_g
          },

          qr_code: batch.qr_code_url
        }
```

**Yield-Analytics & Performance-Vergleich:**
```aql
// Vergleiche Yield über verschiedene Batches
LET species = FIRST(
  FOR s IN species
    FILTER s.scientific_name == @species_name
    RETURN s
)

LET batches_raw = (
  FOR plant IN 1..1 INBOUND species GRAPH 'kamerplanter_graph'
    OPTIONS { edgeCollections: ['belongs_to_species'] }
    FOR batch IN 1..1 OUTBOUND plant GRAPH 'kamerplanter_graph'
      OPTIONS { edgeCollections: ['harvested_as'] }
      FILTER batch.harvest_date > DATE_SUBTRACT(DATE_NOW(), 365, 'days')
      FOR yield IN 1..1 OUTBOUND batch GRAPH 'kamerplanter_graph'
        OPTIONS { edgeCollections: ['has_yield_metric'] }

        LET cycle_days = DATE_DIFF(plant.planted_on, batch.harvest_date, 'days')

        RETURN {
          batch_id: batch.batch_id,
          yield_g: yield.yield_per_plant_g,
          yield_m2: yield.yield_per_m2_g,
          quality: batch.quality_grade,
          cycle_days: cycle_days
        }
)

LET avg_yield = AVERAGE(batches_raw[*].yield_g)
LET avg_yield_m2 = AVERAGE(batches_raw[*].yield_m2)
LET avg_cycle_days = AVERAGE(batches_raw[*].cycle_days)

// Identifiziere Top-Performer (>120% des Durchschnitts)
LET top_performers = (
  FOR b IN batches_raw
    FILTER b.yield_g > avg_yield * 1.2
    RETURN b
)

RETURN {
  species: species.scientific_name,
  total_batches: LENGTH(batches_raw),
  average_yield_per_plant_g: ROUND(avg_yield, 1),
  average_yield_per_m2_g: ROUND(avg_yield_m2, 1),
  average_cycle_days: ROUND(avg_cycle_days),
  top_performers: LENGTH(top_performers),
  quality_distribution: {
    A_plus: LENGTH(FOR b IN batches_raw FILTER b.quality == 'A+' RETURN 1),
    A: LENGTH(FOR b IN batches_raw FILTER b.quality == 'A' RETURN 1),
    B: LENGTH(FOR b IN batches_raw FILTER b.quality == 'B' RETURN 1),
    C: LENGTH(FOR b IN batches_raw FILTER b.quality == 'C' RETURN 1)
  },
  best_batch: FIRST(
    FOR b IN batches_raw
      SORT b.yield_g DESC
      LIMIT 1
      RETURN b
  )
}
```

## 3. Technische Umsetzung (Python)

### Logik-Anforderungen:

**1. Harvest Indicator Factory Pattern:**
```python
from abc import ABC, abstractmethod
from pydantic import BaseModel, Field
from typing import Literal, Optional, Dict, List
from datetime import datetime, timedelta

class HarvestIndicator(ABC, BaseModel):
    """Abstrakte Basis für Reife-Indikatoren"""

    @abstractmethod
    def assess_ripeness(self, observations: Dict) -> Dict:
        """
        Bewertet Reife basierend auf Observations
        Returns: {
            stage: str,
            recommendation: str,
            quality_impact: int,
            days_to_harvest: Optional[int]
        }
        """
        pass

    @abstractmethod
    def time_to_harvest_estimate(self, observations: Dict) -> Optional[int]:
        """Returns: Geschätzte Tage bis optimaler Ernte"""
        pass

    @abstractmethod
    def get_measurement_instructions(self) -> Dict:
        """Returns: Anleitung wie dieser Indikator gemessen wird"""
        pass

class TrichomeIndicator(HarvestIndicator):
    """
    Für Cannabis, Hopfen - Trichom-Mikroskopie mit Multi-Standort-Sampling.

    Hinweis: effect_profile-Werte in assess_ripeness() sind Konsumenten-orientierte
    Deskriptoren, keine agrarbiologischen Parameter. Effekte hängen primär vom
    Cannabinoid-/Terpenprofil der Sorte ab, nicht nur vom Erntezeitpunkt.
    Diese Felder sind optional und zur Information gedacht.
    """

    indicator_type: Literal['trichome'] = 'trichome'

    # Gewichtung der Probenstellen (Top reift 1-2 Wochen vor Bottom)
    LOCATION_WEIGHTS: dict[str, float] = {
        'top_cola': 0.5,     # Höchste Lichtexposition, reift zuerst
        'mid_canopy': 0.3,   # Mittlere Reife
        'lower_branch': 0.2, # Reift zuletzt, oft 7-14 Tage Unterschied
    }

    def assess_ripeness(self, observations: Dict) -> Dict:
        """
        observations kann zwei Formate haben:

        1. Einfach (Einzelmessung, abwärtskompatibel):
           {'clear_percent': float, 'cloudy_percent': float, 'amber_percent': float}

        2. Multi-Standort (empfohlen für akkurate Bewertung):
           {'samples': [
               {'location': 'top_cola', 'clear': 10, 'cloudy': 75, 'amber': 15},
               {'location': 'mid_canopy', 'clear': 25, 'cloudy': 65, 'amber': 10},
               {'location': 'lower_branch', 'clear': 40, 'cloudy': 50, 'amber': 10},
           ]}
        """
        # Multi-Standort-Modus
        if 'samples' in observations:
            return self._assess_multi_location(observations['samples'])

        # Einzelmessung (Fallback)
        clear = observations.get('clear_percent', 0)
        cloudy = observations.get('cloudy_percent', 0)
        amber = observations.get('amber_percent', 0)
        degraded = observations.get('degraded_percent', 0)  # Abgestorbene/abgebrochene Trichome

        # Einzelwert-Validierung
        for name, val in [('clear', clear), ('cloudy', cloudy), ('amber', amber), ('degraded', degraded)]:
            if not (0 <= val <= 100):
                return {
                    'stage': 'error',
                    'recommendation': f'{name}_percent = {val} (muss 0-100 sein).',
                    'quality_impact': 0,
                }

        # Summen-Validierung (inkl. degraded)
        total = clear + cloudy + amber + degraded
        if abs(total - 100) > 5:  # Toleranz 5%
            return {
                'stage': 'error',
                'recommendation': f'Prozent-Summe = {total} (sollte 100 sein). '
                                  f'Empfehlung: Multi-Standort-Sampling (top, mid, lower) für akkuratere Bewertung.',
                'quality_impact': 0 if degraded < 15 else -20,  # Qualitätsabzug bei >15% degraded
                'days_to_harvest': None
            }

        # Effekt-Profile basierend auf Trichom-Verteilung
        if amber > 30:
            return {
                'stage': 'overripe',
                'recommendation': 'SOFORT ernten - THC degradiert zu CBN',
                'quality_impact': -20,
                'days_to_harvest': 0,
                'effect_profile': 'Sehr sedierend, "Couch-Lock"',
                'thc_status': 'Degrading to CBN',
                'color_description': f'Klar: {clear}%, Milchig: {cloudy}%, Bernstein: {amber}%'
            }

        elif cloudy >= 70 and 5 <= amber <= 15:
            return {
                'stage': 'peak',
                'recommendation': 'OPTIMALER ZEITPUNKT - Ernten innerhalb 24-48h',
                'quality_impact': 100,
                'days_to_harvest': 1,
                'effect_profile': 'Balanced - Peak THC, ausgewogene Effekte',
                'thc_status': 'Maximum THC',
                'harvest_window': '24-48 Stunden für beste Qualität',
                'color_description': f'Klar: {clear}%, Milchig: {cloudy}%, Bernstein: {amber}%'
            }

        elif cloudy >= 50 and amber < 5:
            return {
                'stage': 'approaching',
                'recommendation': 'Noch 3-5 Tage warten',
                'quality_impact': 80,
                'days_to_harvest': 4,
                'effect_profile': 'Eher zerebral, energetisch',
                'thc_status': 'High THC, wenig CBN',
                'color_description': f'Klar: {clear}%, Milchig: {cloudy}%, Bernstein: {amber}%'
            }

        elif clear > 50:
            return {
                'stage': 'immature',
                'recommendation': 'Mindestens 10-14 Tage warten',
                'quality_impact': 40,
                'days_to_harvest': 12,
                'effect_profile': 'Unreif, schwache Wirkung',
                'thc_status': 'THC noch nicht voll entwickelt',
                'color_description': f'Klar: {clear}%, Milchig: {cloudy}%, Bernstein: {amber}%'
            }

        # Default
        return {
            'stage': 'monitoring',
            'recommendation': 'Täglich prüfen',
            'quality_impact': 60,
            'days_to_harvest': 7,
            'color_description': f'Klar: {clear}%, Milchig: {cloudy}%, Bernstein: {amber}%'
        }

    def _assess_multi_location(self, samples: List[Dict]) -> Dict:
        """
        Gewichteter Durchschnitt über mehrere Probenstellen.
        Top-Cola-Reife dominiert die Empfehlung, aber der Reifegrad
        der unteren Branches bestimmt das Partial-Harvest-Potenzial.
        """
        weighted_clear = 0.0
        weighted_cloudy = 0.0
        weighted_amber = 0.0
        total_weight = 0.0

        per_location = []
        for sample in samples:
            location = sample.get('location', 'mid_canopy')
            weight = self.LOCATION_WEIGHTS.get(location, 0.2)
            weighted_clear += sample.get('clear', 0) * weight
            weighted_cloudy += sample.get('cloudy', 0) * weight
            weighted_amber += sample.get('amber', 0) * weight
            total_weight += weight
            per_location.append({
                'location': location,
                'clear': sample.get('clear', 0),
                'cloudy': sample.get('cloudy', 0),
                'amber': sample.get('amber', 0),
            })

        if total_weight > 0:
            weighted_clear /= total_weight
            weighted_cloudy /= total_weight
            weighted_amber /= total_weight

        # Bewerte nach gewichtetem Durchschnitt
        base_result = self.assess_ripeness({
            'clear_percent': round(weighted_clear, 1),
            'cloudy_percent': round(weighted_cloudy, 1),
            'amber_percent': round(weighted_amber, 1),
        })

        # Partial-Harvest-Empfehlung wenn Top reif, Bottom nicht
        top_sample = next((s for s in samples if s.get('location') == 'top_cola'), None)
        bottom_sample = next((s for s in samples if s.get('location') == 'lower_branch'), None)

        partial_harvest_recommended = False
        if top_sample and bottom_sample:
            top_cloudy = top_sample.get('cloudy', 0) + top_sample.get('amber', 0)
            bottom_cloudy = bottom_sample.get('cloudy', 0) + bottom_sample.get('amber', 0)
            if top_cloudy >= 80 and bottom_cloudy < 60:
                partial_harvest_recommended = True

        base_result['sampling_method'] = 'multi_location'
        base_result['per_location'] = per_location
        base_result['weighted_average'] = {
            'clear': round(weighted_clear, 1),
            'cloudy': round(weighted_cloudy, 1),
            'amber': round(weighted_amber, 1),
        }
        if partial_harvest_recommended:
            base_result['partial_harvest'] = (
                'Top-Colas reif, untere Branches noch unreif — '
                'Partial Harvest empfohlen: Tops jetzt, Lowers in 7-10 Tagen.'
            )

        return base_result

    def time_to_harvest_estimate(self, observations: Dict) -> Optional[int]:
        cloudy = observations.get('cloudy_percent', 0)
        amber = observations.get('amber_percent', 0)

        if amber > 15:
            return 0  # Sofort
        elif cloudy >= 70:
            return 2
        elif cloudy >= 50:
            return 5
        elif cloudy >= 30:
            return 10
        else:
            return 14

    def get_measurement_instructions(self) -> Dict:
        return {
            'tool': '60x-100x Mikroskop oder Juwelier-Lupe',
            'sample_location': 'Calyx (Blütenhülle), nicht Zuckerblätter',
            'lighting': 'Natürliches Licht oder LED',
            'procedure': [
                '1. Wähle reife Blüte aus mittlerer Höhe',
                '2. Fokussiere auf Calyx-Trichome',
                '3. Zähle mind. 50 Trichome',
                '4. Kategorisiere: Klar / Milchig / Bernstein',
                '5. Berechne Prozent-Anteile'
            ],
            'best_time': 'Morgens, vor Licht-EIN',
            'frequency': 'Täglich ab 75% der sortenspezifischen Blütezeit. '
                        'Beispiel: 8-Wochen-Sorte → ab Woche 6; 12-Wochen-Sorte → ab Woche 9. '
                        'Autoflower: Ab Woche 5 oder bei ersten Amber-Trichomen.'
        }

class FoliageIndicator(HarvestIndicator):
    """Für Kartoffeln, Zwiebeln - Krautsterben"""

    indicator_type: Literal['foliage'] = 'foliage'

    def assess_ripeness(self, observations: Dict) -> Dict:
        """
        observations = {
            'dead_foliage_percent': float,
            'skin_hardness': str  # 'soft', 'medium', 'hard'
        }
        """
        dead_foliage = observations.get('dead_foliage_percent', 0)
        skin = observations.get('skin_hardness', 'soft')

        if dead_foliage > 80 and skin == 'hard':
            return {
                'stage': 'ready',
                'recommendation': 'Ernten innerhalb 14 Tagen',
                'quality_impact': 100,
                'days_to_harvest': 7,
                'storage_readiness': 'Schale voll ausgehärtet - optimal für Lagerung',
                'notes': 'Schalenhärtung abgeschlossen'
            }

        elif dead_foliage > 50:
            return {
                'stage': 'approaching',
                'recommendation': 'Bewässerung stoppen, Haut härten lassen',
                'quality_impact': 70,
                'days_to_harvest': 14,
                'storage_readiness': 'Schalenhärtung in Progress',
                'action': 'Kein Wasser mehr geben für Schalenhärtung'
            }

        else:
            return {
                'stage': 'immature',
                'recommendation': '2-4 Wochen bis Krautsterben',
                'quality_impact': 40,
                'days_to_harvest': 21,
                'foliage_status': f'{dead_foliage}% abgestorben'
            }

    def time_to_harvest_estimate(self, observations: Dict) -> Optional[int]:
        dead = observations.get('dead_foliage_percent', 0)

        if dead > 80:
            return 7
        elif dead > 50:
            return 14
        else:
            return 21

    def get_measurement_instructions(self) -> Dict:
        return {
            'tool': 'Visuelle Inspektion',
            'procedure': [
                '1. Schätze % totes vs. grünes Laub',
                '2. Teste Schalen-Härte (Daumen-Test)',
                '3. Grabe Probe-Knolle aus',
                '4. Prüfe Schalen-Festigkeit'
            ],
            'skin_test': 'Haut darf sich nicht mit Daumen abreiben',
            'frequency': 'Wöchentlich ab Blüte-Ende'
        }

class BrixIndicator(HarvestIndicator):
    """Für Fruchtgemüse - Zuckergehalt"""

    indicator_type: Literal['brix'] = 'brix'
    target_brix: float = Field(ge=0, le=30)

    def assess_ripeness(self, observations: Dict) -> Dict:
        """
        observations = {
            'brix_value': float,
            'color': str,
            'firmness': str
        }
        """
        brix = observations.get('brix_value', 0)
        color = observations.get('color', 'green')

        deviation = ((brix - self.target_brix) / self.target_brix) * 100

        if abs(deviation) < 10:  # Innerhalb 10% vom Ziel
            return {
                'stage': 'peak',
                'recommendation': 'Optimaler Zuckergehalt erreicht',
                'quality_impact': 100,
                'days_to_harvest': 1,
                'brix_value': brix,
                'target_brix': self.target_brix,
                'sweetness': 'Optimal'
            }
        elif deviation < -20:
            return {
                'stage': 'immature',
                'recommendation': 'Zuckergehalt noch zu niedrig',
                'quality_impact': 50,
                'days_to_harvest': 7,
                'brix_value': brix,
                'target_brix': self.target_brix
            }
        else:
            return {
                'stage': 'approaching',
                'recommendation': 'Noch 2-3 Tage',
                'quality_impact': 80,
                'days_to_harvest': 3,
                'brix_value': brix,
                'target_brix': self.target_brix
            }

    def time_to_harvest_estimate(self, observations: Dict) -> Optional[int]:
        brix = observations.get('brix_value', 0)
        deviation = ((brix - self.target_brix) / self.target_brix) * 100

        if deviation > -10:
            return 1
        elif deviation > -20:
            return 3
        else:
            return 7

    def get_measurement_instructions(self) -> Dict:
        return {
            'tool': 'Refraktometer (0-32 °Brix)',
            'procedure': [
                '1. Schneide reife Frucht auf',
                '2. Presse Saft auf Refraktometer-Prisma',
                '3. Schließe Tageslicht-Platte',
                '4. Lies Brix-Wert an Skala ab',
                '5. Reinige Prisma mit destilliertem Wasser'
            ],
            'calibration': 'Kalibriere mit destilliertem Wasser (0 °Brix)',
            'sampling': 'Teste 3 Früchte, nimm Durchschnitt',
            'best_time': 'Immer zur gleichen Tageszeit messen für Vergleichbarkeit. '
                        'Morgens vor Bewässerung = repräsentativster Wert (höchster Turgor, '
                        'weniger Varianz durch Transpiration).',
            'target_values': {
                'Tomaten (Standard)': '8-10 °Brix',
                'Tomaten (Cherry/Heirloom)': '10-14 °Brix',
                'Paprika (süß)': '7-9 °Brix',
                'Erdbeeren': '10-14 °Brix',
                'Melonen': '12-16 °Brix',
                'Gurken': '3-5 °Brix',
                'Basilikum (Blatt-Saft)': '2-4 °Brix',
            }
        }

class EthyleneRipeningClassifier:
    """
    Unterscheidet klimakterische und nicht-klimakterische Früchte.
    Fundamentaler Einfluss auf Erntezeitpunkt und Nachernte-Handling.

    Klimakterisch: Produzieren Ethylen → reifen NACH Ernte weiter
        → können vor Vollreife geerntet werden ("breaker stage")
        → Beispiele: Tomate, Banane, Apfel, Mango, Avocado, Birne

    Nicht-klimakterisch: Produzieren KEIN Ethylen → reifen NICHT nach
        → MÜSSEN voll ausgereift geerntet werden
        → Beispiele: Paprika, Erdbeere, Gurke, Zitrus, Weintraube, Kirsche

    Cannabis/Hopfen/Kräuter: Nicht-klimakterisch (werden getrocknet, nicht nachgereift)
    """

    CLIMACTERIC_SPECIES: set[str] = {
        'tomato', 'banana', 'apple', 'mango', 'avocado', 'pear',
        'peach', 'plum', 'kiwi', 'papaya', 'cantaloupe', 'honeydew', 'fig',
    }

    # Bedingt klimakterisch: zeigen klimakterisches Verhalten ab Farbumschlag (Breaker-Stage),
    # können in begrenztem Maß nachgereift werden (gängige kommerzielle Praxis).
    WEAKLY_CLIMACTERIC_SPECIES: set[str] = {
        'pepper',      # Paprika im Farbumschlag ist klimakterisch, grüne Paprika nicht
    }

    NON_CLIMACTERIC_SPECIES: set[str] = {
        'strawberry', 'cucumber', 'citrus', 'grape', 'cherry',
        'raspberry', 'blueberry', 'watermelon', 'cannabis', 'hop', 'herb',
        'potato', 'onion', 'carrot', 'lettuce',
        'pineapple',   # Reagiert auf exogenes Ethylen (Blüteninduktion), reift aber
                       # nach Ernte nicht signifikant nach
    }

    @classmethod
    def classify(cls, species_type: str) -> dict:
        species_lower = species_type.lower()
        if species_lower in cls.CLIMACTERIC_SPECIES:
            return {
                'is_climacteric': True,
                'climacteric_level': 'full',
                'can_harvest_early': True,
                'post_harvest_ripening': True,
                'recommendation': 'Kann im "Breaker"-Stadium geerntet und bei Raumtemperatur '
                                  'nachgereift werden. Ethylen-Begasung beschleunigt Reifung.',
                'storage_note': 'Nicht mit nicht-klimakterischen Früchten lagern '
                                '(Ethylen beschleunigt deren Verderb).',
            }
        elif species_lower in cls.WEAKLY_CLIMACTERIC_SPECIES:
            return {
                'is_climacteric': True,
                'climacteric_level': 'weak',
                'can_harvest_early': True,
                'post_harvest_ripening': True,
                'recommendation': 'Bedingt klimakterisch — kann ab Farbumschlag (Breaker-Stadium) '
                                  'geerntet und begrenzt nachgereift werden. Vollfarbige Ernte '
                                  'liefert höchste Qualität.',
                'storage_note': 'Getrennt von stark klimakterischen Früchten lagern.',
            }
        else:
            return {
                'is_climacteric': False,
                'climacteric_level': 'none',
                'can_harvest_early': False,
                'post_harvest_ripening': False,
                'recommendation': 'MUSS voll ausgereift geerntet werden — reift nach Ernte '
                                  'nicht mehr nach. Qualität sinkt nur noch (Wasserverlust, Verderb).',
                'storage_note': 'Kühllagerung verlangsamt Qualitätsverlust.',
            }

    @classmethod
    def adjust_harvest_recommendation(
        cls, species_type: str, readiness_score: float
    ) -> str:
        """
        Passt Ernte-Empfehlung basierend auf Klimakterium an.
        Klimakterische Früchte können bei niedrigerem Score geerntet werden.
        """
        info = cls.classify(species_type)
        if info['is_climacteric'] and readiness_score >= 60:
            return (
                f'APPROACHING aber klimakterisch — kann jetzt geerntet und '
                f'nachgereift werden (Score {readiness_score:.0f}/100).'
            )
        elif not info['is_climacteric'] and readiness_score < 80:
            return (
                f'Noch nicht reif (Score {readiness_score:.0f}/100). '
                f'Nicht-klimakterisch — muss am Pflanze ausreifen.'
            )
        return ''


class AromaIndicator(HarvestIndicator):
    """
    Für Cannabis (Terpene), Kräuter (ätherische Öle), Hopfen.
    Geruchstest ist einer der praktischsten Erntebereitschafts-Indikatoren.
    """

    indicator_type: Literal['aroma'] = 'aroma'

    # Bekannte Cannabis-Terpene und ihre Aromen
    TERPENE_PROFILES: dict[str, str] = {
        'myrcene': 'Mango, erdig, moschusartig',
        'limonene': 'Zitrus, frisch, energetisch',
        'linalool': 'Lavendel, blumig, beruhigend',
        'pinene': 'Kiefer, harzig, scharf',
        'caryophyllene': 'Pfeffer, würzig, holzig',
        'humulene': 'Hopfen, erdig, holzig',
        'terpinolene': 'Kräuter, blumig, leicht süß',
        'ocimene': 'Süß, kräuterartig, holzig',
    }

    def assess_ripeness(self, observations: Dict) -> Dict:
        """
        observations = {
            'intensity': float (0-10, ordinal-kategorisch mit verbaler Verankerung:
                0-1: Kein wahrnehmbares Aroma (muss Blüte reiben),
                2-3: Schwach (nur bei direktem Kontakt),
                4-5: Moderat (wahrnehmbar bei 10 cm Abstand),
                6-7: Stark (wahrnehmbar bei 30 cm, "Room Scent"),
                8-10: Sehr stark (ganzer Raum)),
            'dominant_terpene': Optional[str],
            'secondary_terpenes': Optional[list[str]],
            'consistency': str ('developing', 'stable', 'fading'),
            'notes': Optional[str]
        }
        """
        intensity = observations.get('intensity', 0)
        consistency = observations.get('consistency', 'developing')
        dominant = observations.get('dominant_terpene')

        if consistency == 'fading' or intensity < 3:
            return {
                'stage': 'overripe',
                'recommendation': 'Aroma verblasst — Terpene degradieren bei Überreife. '
                                  'Sofort ernten oder Ernte zurückdatieren.',
                'quality_impact': -10,
                'days_to_harvest': 0,
                'aroma_status': f'Intensität {intensity}/10, abnehmend',
            }

        if consistency == 'stable' and intensity >= 7:
            return {
                'stage': 'peak',
                'recommendation': 'Optimale Terpen-Entwicklung — Ernte innerhalb 1-3 Tagen '
                                  'für maximales Aroma.',
                'quality_impact': 95,
                'days_to_harvest': 1,
                'dominant_terpene': dominant,
                'aroma_description': self.TERPENE_PROFILES.get(dominant, 'Komplexes Profil'),
                'harvest_tip': 'Früh morgens ernten — höchste Terpen-Konzentration.',
            }

        if intensity >= 5:
            return {
                'stage': 'approaching',
                'recommendation': 'Terpene entwickeln sich — täglich Geruchstest. '
                                  'Noch 3-7 Tage bis Peak.',
                'quality_impact': 75,
                'days_to_harvest': 5,
                'aroma_status': f'Intensität {intensity}/10, zunehmend',
            }

        return {
            'stage': 'immature',
            'recommendation': 'Aroma noch schwach entwickelt. 7-14 Tage warten.',
            'quality_impact': 40,
            'days_to_harvest': 10,
            'aroma_status': f'Intensität {intensity}/10',
        }

    def time_to_harvest_estimate(self, observations: Dict) -> Optional[int]:
        intensity = observations.get('intensity', 0)
        consistency = observations.get('consistency', 'developing')

        if consistency == 'fading':
            return 0
        if consistency == 'stable' and intensity >= 7:
            return 1
        if intensity >= 5:
            return 5
        return 10

    def get_measurement_instructions(self) -> Dict:
        return {
            'tool': 'Nase (Geruchstest) oder GC/MS für präzise Analyse',
            'procedure': [
                '1. Reibe sanft an einer reifen Blüte/Blatt',
                '2. Bewerte Intensität (0-10 Skala)',
                '3. Identifiziere dominantes Aroma (Zitrus, Mango, Kiefer, Lavendel, Pfeffer)',
                '4. Prüfe Konsistenz: wird Aroma stärker (developing), stabil (stable), oder schwächer (fading)?',
                '5. Vergleiche über 3-5 Tage — stabiles Peak-Aroma = erntebereit'
            ],
            'best_time': 'Morgens vor Beleuchtung (höchste Terpen-Konzentration)',
            'for_herbs': 'Basilikum: VOR Blüte ernten (Aroma-Peak). '
                         'Thymian/Oregano: WÄHREND Blüte ernten (Öl-Konzentration maximal).',
            'frequency': 'Täglich ab geschätzter Erntereife',
        }


class DaysSinceFloweringIndicator(HarvestIndicator):
    """Fallback für Spezies ohne spezifische Indikatoren"""

    indicator_type: Literal['days_since_flowering'] = 'days_since_flowering'
    typical_flowering_days: int = Field(ge=30, le=150)

    def assess_ripeness(self, observations: Dict) -> Dict:
        days = observations.get('days_since_flowering', 0)
        progress = (days / self.typical_flowering_days) * 100

        if progress >= 100:
            return {
                'stage': 'ready',
                'recommendation': 'Ernten (Richtwert erreicht)',
                'quality_impact': 90,
                'days_to_harvest': 0,
                'days_in_flower': days,
                'expected_days': self.typical_flowering_days
            }
        elif progress >= 90:
            return {
                'stage': 'approaching',
                'recommendation': f'Noch ~{self.typical_flowering_days - days} Tage',
                'quality_impact': 80,
                'days_to_harvest': self.typical_flowering_days - days,
                'progress_percent': round(progress, 1)
            }
        else:
            return {
                'stage': 'developing',
                'recommendation': f'{self.typical_flowering_days - days} Tage verbleibend',
                'quality_impact': int(progress * 0.5),
                'days_to_harvest': self.typical_flowering_days - days,
                'progress_percent': round(progress, 1)
            }

    def time_to_harvest_estimate(self, observations: Dict) -> Optional[int]:
        days = observations.get('days_since_flowering', 0)
        return max(0, self.typical_flowering_days - days)

    def get_measurement_instructions(self) -> Dict:
        return {
            'tool': 'Kalender-Tracking',
            'procedure': [
                '1. Notiere Blüte-Start-Datum',
                '2. Zähle Tage seit Blüte-Einleitung',
                '3. Vergleiche mit Sorten-Richtwert'
            ],
            'note': 'Nur als Richtwert - kombiniere mit visuellen Checks'
        }


class MushroomIndicator(HarvestIndicator):
    """
    Ernte-Indikatoren für Pilzkulturen (U-005).
    Pilze erfordern eigenständige Reife-Kriterien:
    - Velum-Status (Schleier) bestimmt Erntezeitpunkt
    - Flush-Nummer beeinflusst Ertrag und Biological Efficiency
    - Hutdurchmesser ist sortenspezifisch
    """

    indicator_type: Literal['mushroom'] = 'mushroom'
    species_name: str = Field(description="z.B. 'Pleurotus ostreatus', 'Lentinula edodes'")
    expected_flushes: int = Field(default=3, ge=1, le=8)

    # Artspezifische Ernteparameter
    MUSHROOM_HARVEST_SPECS: dict[str, dict] = {
        'Pleurotus ostreatus': {       # Austernpilz
            'cap_diameter_cm': (5, 15),
            'veil_trigger': False,       # Kein Velum — Rand-Einrollung als Indikator
            'harvest_cue': 'Hutrand beginnt sich nach oben zu rollen (flach → aufwärts)',
            'typical_flushes': 3,
            'bio_efficiency_target': 100,  # % des Substratgewichts als Frischpilz
        },
        'Lentinula edodes': {           # Shiitake
            'cap_diameter_cm': (5, 12),
            'veil_trigger': True,        # Velum bricht → erntebereit
            'harvest_cue': 'Velum (Schleier unter dem Hut) beginnt zu reißen',
            'typical_flushes': 4,
            'bio_efficiency_target': 75,
        },
        'Agaricus bisporus': {          # Champignon
            'cap_diameter_cm': (3, 8),
            'veil_trigger': True,
            'harvest_cue': 'Velum geschlossen für weiße Champignons; offen für Portobello',
            'typical_flushes': 3,
            'bio_efficiency_target': 60,
        },
        'Psilocybe cubensis': {         # Psilocybin-Pilz (legal in einigen Jurisdiktionen)
            'cap_diameter_cm': (2, 8),
            'veil_trigger': True,
            'harvest_cue': 'Velum reißt gerade — Ernte SOFORT für maximale Potenz',
            'typical_flushes': 4,
            'bio_efficiency_target': 50,
        },
    }

    def assess_ripeness(self, observations: Dict) -> Dict:
        """
        observations = {
            'cap_diameter_cm': float,
            'veil_status': Literal['intact', 'stretching', 'torn', 'open'],
            'flush_number': int,
            'substrate_weight_g': float,
            'total_harvest_g': float,  # Kumulativer Ertrag aller bisherigen Flushes
        }
        """
        specs = self.MUSHROOM_HARVEST_SPECS.get(self.species_name, {})
        cap = observations.get('cap_diameter_cm', 0)
        veil = observations.get('veil_status', 'intact')
        flush = observations.get('flush_number', 1)

        # Biological Efficiency berechnen
        substrate_g = observations.get('substrate_weight_g', 1)
        total_harvest_g = observations.get('total_harvest_g', 0)
        bio_eff = (total_harvest_g / substrate_g) * 100 if substrate_g > 0 else 0

        # Velum-basierte Bewertung (primär für Arten mit Velum)
        if specs.get('veil_trigger'):
            if veil == 'torn' or veil == 'open':
                return {
                    'stage': 'peak',
                    'recommendation': 'SOFORT ernten — Velum gerissen. Sporen-Abwurf beginnt.',
                    'quality_impact': 100 if veil == 'torn' else 80,
                    'days_to_harvest': 0,
                    'flush_number': flush,
                    'biological_efficiency': round(bio_eff, 1),
                }
            elif veil == 'stretching':
                return {
                    'stage': 'approaching',
                    'recommendation': 'Velum dehnt sich — Ernte in 6-12 Stunden.',
                    'quality_impact': 95,
                    'days_to_harvest': 0,
                    'flush_number': flush,
                }
        else:
            # Hutrand-basierte Bewertung (z.B. Austernpilz)
            cap_range = specs.get('cap_diameter_cm', (5, 15))
            if cap >= cap_range[1]:
                return {
                    'stage': 'overripe',
                    'recommendation': f'Hutrand aufgerollt, Hut > {cap_range[1]}cm — sofort ernten.',
                    'quality_impact': -10,
                    'days_to_harvest': 0,
                }
            elif cap >= cap_range[0]:
                return {
                    'stage': 'peak',
                    'recommendation': specs.get('harvest_cue', 'Erntebereit'),
                    'quality_impact': 95,
                    'days_to_harvest': 0,
                }

        return {
            'stage': 'immature',
            'recommendation': 'Pilze noch in Entwicklung — täglich kontrollieren.',
            'quality_impact': 30,
            'days_to_harvest': 2,
            'flush_number': flush,
            'remaining_flushes': max(0, self.expected_flushes - flush),
            'biological_efficiency': round(bio_eff, 1),
            'bio_eff_target': specs.get('bio_efficiency_target', 50),
        }

    def time_to_harvest_estimate(self, observations: Dict) -> Optional[int]:
        veil = observations.get('veil_status', 'intact')
        if veil in ('torn', 'open'):
            return 0
        if veil == 'stretching':
            return 0  # Stunden, nicht Tage
        return 2

    def get_measurement_instructions(self) -> Dict:
        return {
            'tool': 'Visuelle Inspektion, Lineal/Messschieber',
            'procedure': [
                '1. Hutdurchmesser mit Lineal messen (cm)',
                '2. Velum-Status prüfen: intakt / dehnend / gerissen / offen',
                '3. Flush-Nummer dokumentieren',
                '4. Gesamtertrag wiegen (kumulativ über alle Flushes)',
            ],
            'frequency': 'Zweimal täglich während Fruchtungsphase',
            'note': 'Bei Velum-tragenden Arten: "torn" = sofortige Ernte. '
                    'Bei Austernpilzen: Hutrand-Einrollung beobachten.',
        }


class GDDIndicator(HarvestIndicator):
    """
    GDD-basierte Erntereife-Prognose (U-006).
    Growing Degree Days (Wärmesumme) als objektive, temperaturbasierte
    Erntereife-Metrik. Ergänzt oder ersetzt Kalendertage.

    GDD_tag = max(0, (T_max + T_min) / 2 - T_base)

    Artspezifische Schwellenwerte (GDD bis Ernte) sind kalibrierbar
    und werden aus REQ-005 Sensorik-Daten akkumuliert (REQ-003 GDD-Tracking).
    """

    indicator_type: Literal['gdd'] = 'gdd'
    target_gdd: float = Field(ge=100, le=5000, description="Art-/Sortenspezifische GDD bis Erntereife")
    base_temp_c: float = Field(default=10.0, description="Basistemperatur für GDD-Berechnung")

    # Artspezifische GDD-Schwellenwerte bis Ernte (ab Blüte/Pflanzung)
    SPECIES_GDD_TARGETS: dict[str, dict] = {
        'tomato':     {'gdd_to_harvest': 1200, 'base_temp': 10.0, 'from': 'transplant'},
        'pepper':     {'gdd_to_harvest': 1400, 'base_temp': 10.0, 'from': 'transplant'},
        'cucumber':   {'gdd_to_harvest': 800,  'base_temp': 15.5, 'from': 'transplant'},
        'lettuce':    {'gdd_to_harvest': 600,  'base_temp': 4.4,  'from': 'sowing'},
        'carrot':     {'gdd_to_harvest': 1000, 'base_temp': 4.4,  'from': 'sowing'},
        'potato':     {'gdd_to_harvest': 1200, 'base_temp': 7.0,  'from': 'planting'},
        'cannabis':   {'gdd_to_harvest': 1600, 'base_temp': 10.0, 'from': 'flowering_start'},
        'basil':      {'gdd_to_harvest': 500,  'base_temp': 10.0, 'from': 'transplant'},
    }

    def assess_ripeness(self, observations: Dict) -> Dict:
        """
        observations = {
            'accumulated_gdd': float,   # Aktuelle GDD-Summe (aus REQ-005/REQ-003)
            'daily_gdd_avg': float,     # Durchschnittliche GDD/Tag (letzte 7 Tage)
        }
        """
        accumulated = observations.get('accumulated_gdd', 0)
        daily_avg = observations.get('daily_gdd_avg', 10)
        progress = (accumulated / self.target_gdd) * 100 if self.target_gdd > 0 else 0

        remaining_gdd = max(0, self.target_gdd - accumulated)
        estimated_days = int(remaining_gdd / daily_avg) if daily_avg > 0 else 99

        if progress >= 100:
            return {
                'stage': 'peak',
                'recommendation': f'GDD-Ziel erreicht ({accumulated:.0f}/{self.target_gdd:.0f}) — '
                                  f'Erntefenster offen. Mit visuellen Indikatoren kombinieren.',
                'quality_impact': 95,
                'days_to_harvest': 0,
                'gdd_progress_percent': round(progress, 1),
                'accumulated_gdd': round(accumulated, 1),
            }
        elif progress >= 85:
            return {
                'stage': 'approaching',
                'recommendation': f'GDD {accumulated:.0f}/{self.target_gdd:.0f} '
                                  f'({progress:.0f}%) — noch ~{estimated_days} Tage.',
                'quality_impact': 80,
                'days_to_harvest': estimated_days,
                'gdd_progress_percent': round(progress, 1),
            }
        else:
            return {
                'stage': 'developing',
                'recommendation': f'GDD {accumulated:.0f}/{self.target_gdd:.0f} '
                                  f'({progress:.0f}%) — ca. {estimated_days} Tage verbleibend.',
                'quality_impact': int(progress * 0.6),
                'days_to_harvest': estimated_days,
                'gdd_progress_percent': round(progress, 1),
            }

    def time_to_harvest_estimate(self, observations: Dict) -> Optional[int]:
        accumulated = observations.get('accumulated_gdd', 0)
        daily_avg = observations.get('daily_gdd_avg', 10)
        remaining = max(0, self.target_gdd - accumulated)
        return int(remaining / daily_avg) if daily_avg > 0 else None

    def get_measurement_instructions(self) -> Dict:
        return {
            'tool': 'Automatisch via REQ-005 Sensorik + REQ-003 GDD-Tracking',
            'procedure': [
                '1. GDD wird automatisch aus Tagestemperaturen akkumuliert',
                '2. Formel: GDD_tag = max(0, (T_max + T_min) / 2 - T_base)',
                '3. GDD-Fortschritt gegen artspezifischen Zielwert prüfen',
                '4. Mit visuellen/sensorischen Indikatoren kombinieren',
            ],
            'note': 'GDD ist temperaturabhängig und korreliert besser mit der physiologischen '
                    'Reife als Kalendertage. Besonders wertvoll bei Outdoor-Anbau mit '
                    'Temperatur-Schwankungen.',
        }


class ContinuousHarvestIndicator(HarvestIndicator):
    """
    Indikator für Cut-and-Come-Again (CACA) Kulturen (U-003).
    Blattgemüse (Salat, Spinat, Rucola, Mangold, Kräuter) die wiederholt
    beerntet werden können, solange die Schnittöhe eingehalten wird.
    """

    indicator_type: Literal['continuous_harvest'] = 'continuous_harvest'
    cut_height_cm: float = Field(ge=1, le=30, description="Minimale Schnitthöhe über Boden")
    regrowth_days: int = Field(ge=3, le=60, description="Typische Nachwachszeit zwischen Ernten")
    max_harvests_before_replant: int = Field(ge=1, le=20, description="Max Ernten bevor Qualität nachlässt")

    # Artspezifische CACA-Parameter
    CACA_SPECIES: dict[str, dict] = {
        'lettuce_leaf':  {'cut_height_cm': 3, 'regrowth_days': 14, 'max_harvests': 4, 'note': 'Über dem Vegetationspunkt schneiden'},
        'spinach':       {'cut_height_cm': 3, 'regrowth_days': 21, 'max_harvests': 3, 'note': 'Äußere Blätter zuerst'},
        'arugula':       {'cut_height_cm': 2, 'regrowth_days': 10, 'max_harvests': 5, 'note': 'Vor Blüte ernten, sonst bitter'},
        'chard':         {'cut_height_cm': 5, 'regrowth_days': 21, 'max_harvests': 6, 'note': 'Äußere Stiele abschneiden'},
        'basil':         {'cut_height_cm': 10, 'regrowth_days': 14, 'max_harvests': 8, 'note': 'Über einem Blattpaar schneiden — fördert Verzweigung'},
        'cilantro':      {'cut_height_cm': 3, 'regrowth_days': 21, 'max_harvests': 2, 'note': 'Geht schnell in Blüte (Bolting)'},
        'kale':          {'cut_height_cm': 5, 'regrowth_days': 28, 'max_harvests': 5, 'note': 'Untere Blätter zuerst, Spitze stehen lassen'},
    }

    def assess_ripeness(self, observations: Dict) -> Dict:
        """
        observations = {
            'current_height_cm': float,         # Aktuelle Wuchshöhe
            'days_since_last_harvest': int,      # Tage seit letzter Ernte
            'harvest_count': int,                # Bisherige Anzahl Ernten
            'bolting_signs': bool,               # Zeigt die Pflanze Blütenansätze?
            'leaf_quality': Literal['excellent', 'good', 'declining'],
        }
        """
        height = observations.get('current_height_cm', 0)
        days_since = observations.get('days_since_last_harvest', 0)
        count = observations.get('harvest_count', 0)
        bolting = observations.get('bolting_signs', False)
        quality = observations.get('leaf_quality', 'good')

        if bolting:
            return {
                'stage': 'overripe',
                'recommendation': 'Blütenansatz erkannt — SOFORT final ernten. '
                                  'Blätter werden bitter nach Bolting.',
                'quality_impact': -20,
                'days_to_harvest': 0,
                'harvest_count': count,
                'action': 'final_harvest',
            }

        if count >= self.max_harvests_before_replant:
            return {
                'stage': 'overripe',
                'recommendation': f'Maximum Ernten ({self.max_harvests_before_replant}) erreicht — '
                                  f'Pflanze ersetzen für optimale Qualität.',
                'quality_impact': -10,
                'days_to_harvest': 0,
                'action': 'replant',
            }

        if days_since >= self.regrowth_days and height >= self.cut_height_cm * 2:
            return {
                'stage': 'peak',
                'recommendation': f'Erntebereit (Ernte #{count + 1}). '
                                  f'Auf {self.cut_height_cm} cm schneiden.',
                'quality_impact': 95,
                'days_to_harvest': 0,
                'remaining_harvests': self.max_harvests_before_replant - count,
                'cut_height_cm': self.cut_height_cm,
            }

        remaining_days = max(0, self.regrowth_days - days_since)
        return {
            'stage': 'developing',
            'recommendation': f'Nachwachsphase — noch ~{remaining_days} Tage bis nächste Ernte.',
            'quality_impact': 50,
            'days_to_harvest': remaining_days,
            'harvest_count': count,
        }

    def time_to_harvest_estimate(self, observations: Dict) -> Optional[int]:
        days_since = observations.get('days_since_last_harvest', 0)
        return max(0, self.regrowth_days - days_since)

    def get_measurement_instructions(self) -> Dict:
        return {
            'tool': 'Lineal, saubere Schere/Messer',
            'procedure': [
                f'1. Wuchshöhe messen — Ernte ab {self.cut_height_cm * 2} cm',
                f'2. Auf {self.cut_height_cm} cm über Boden schneiden',
                '3. Blütenansätze (Bolting) prüfen — sofortige Ernte wenn ja',
                '4. Blattqualität bewerten (Farbe, Textur, Bitterkeit)',
                '5. Ertrag wiegen und kumulativ dokumentieren',
            ],
            'frequency': f'Alle {self.regrowth_days} Tage prüfen',
            'note': f'Maximal {self.max_harvests_before_replant} Ernten, danach Pflanze ersetzen.',
        }
```

<!-- Quelle: Cannabis Indoor Grower Review W-007 -->
**Ernte-Fenster-Vorhersage (Harvest Window Prediction):**

Das System kombiniert drei bereits vorhandene Datenquellen, um ein geschätztes Erntefenster vorherzusagen und dieses mit jeder neuen Beobachtung adaptiv zu verfeinern.

**Eingabedaten:**

| Datenquelle | Herkunft | Beschreibung |
|-------------|----------|--------------|
| Cultivar-Blütezeit | REQ-001 (Stammdaten) | Sortenspezifische Blütedauer in Wochen (z.B. 8–10 Wochen), hinterlegt am Cultivar |
| Phase-Start-Datum | REQ-003 (Phasensteuerung) | Zeitpunkt des Übergangs in die Flowering-Phase (Blüte-Einleitung) |
| Trichom-Beobachtungen | REQ-007 (harvest_observations) | Laufende Trichom-Messungen (clear/cloudy/amber %) mit Zeitstempel |

**Berechnungslogik:**

1. **Basis-Fenster aus Cultivar-Daten:**
   Das initiale Erntefenster ergibt sich aus dem Phase-Start-Datum und der sortenspezifischen Blütedauer:
   ```
   basis_start = flowering_start + (cultivar.min_flowering_weeks × 7)
   basis_end   = flowering_start + (cultivar.max_flowering_weeks × 7)
   ```
   Beispiel: Sorte mit 8–10 Wochen Blüte, Blüte-Start am 01.01. → Basis-Fenster Tag 56–70.

2. **Verfeinerung durch Trichom-Beobachtungen:**
   Sobald Trichom-Observations vorliegen, wird das Fenster eingegrenzt:
   - **cloudy ≥ 50%, amber < 5%:** Fenster verschiebt sich auf 3–7 Tage ab Beobachtung
   - **cloudy ≥ 70%, amber 5–15%:** Fenster engt sich auf 0–2 Tage ein (Peak)
   - **amber > 15%:** Fenster = sofort (0 Tage), Warnung vor Überreife
   - **clear > 50%:** Fenster bleibt beim Basis-Fenster, frühestens 10–14 Tage

3. **Adaptive Verfeinerung (Konfidenz-Modell):**
   Die Konfidenz der Vorhersage steigt mit der Datenlage:

   | Datenlage | Konfidenz | Fensterbreite |
   |-----------|-----------|---------------|
   | Nur Cultivar-Daten (keine Observations) | Niedrig | ±14 Tage (breites Fenster) |
   | Cultivar + 1–2 Trichom-Observations | Mittel | ±7 Tage |
   | Cultivar + 3+ Trichom-Observations mit Trend | Hoch | ±3 Tage |
   | Cultivar + Trichom + Aroma (stable/peak) | Sehr hoch | ±1–2 Tage |

   Mit jeder neuen Trichom-Beobachtung wird der Trend (Amber-Zunahme-Rate pro Tag) berechnet und das Fenster entsprechend enger gesetzt.

4. **Trend-Extrapolation:**
   Bei ≥ 2 Trichom-Observations wird die tägliche Amber-Zunahme-Rate berechnet:
   ```
   amber_rate = (amber_current - amber_previous) / days_between_observations
   days_to_target = (target_amber - amber_current) / amber_rate
   ```
   Ziel-Amber: 10–15% für Peak-Ernte (gemäß TrichomeIndicator-Logik).

**Ausgabe:**
```
Geschätztes Erntefenster: Tag 62–68 (4–10 Tage)
Konfidenz: Hoch (3 Trichom-Observations, steigender Amber-Trend)
Nächste empfohlene Prüfung: Morgen (tägliche Trichom-Kontrolle ab 75% der Blütezeit)
```

**Implementierung:**
```python
class HarvestWindowPredictor:
    """
    Kombiniert Cultivar-Blütezeit (REQ-001), Phase-Start-Datum (REQ-003)
    und Trichom-Observations (REQ-007) zu einer adaptiven Erntefenster-Vorhersage.
    """

    # Ziel-Amber-Bereich für Peak-Ernte (konsistent mit TrichomeIndicator)
    TARGET_AMBER_MIN: float = 10.0
    TARGET_AMBER_MAX: float = 15.0

    # Konfidenz-Stufen
    CONFIDENCE_LEVELS: dict[str, dict] = {
        'low':       {'label': 'Niedrig',    'window_margin_days': 14},
        'medium':    {'label': 'Mittel',      'window_margin_days': 7},
        'high':      {'label': 'Hoch',        'window_margin_days': 3},
        'very_high': {'label': 'Sehr hoch',   'window_margin_days': 1},
    }

    def predict_harvest_window(
        self,
        flowering_start_date: date,
        min_flowering_weeks: int,
        max_flowering_weeks: int,
        trichome_observations: list[dict] | None = None,
        aroma_observations: list[dict] | None = None,
    ) -> dict:
        """
        Berechnet das geschätzte Erntefenster.

        Args:
            flowering_start_date: Datum des Blüte-Starts (REQ-003 Phase-Übergang)
            min_flowering_weeks: Minimale Blütedauer laut Cultivar (REQ-001)
            max_flowering_weeks: Maximale Blütedauer laut Cultivar (REQ-001)
            trichome_observations: Sortierte Liste von Trichom-Observations (älteste zuerst)
            aroma_observations: Optionale Aroma-Observations zur Konfidenz-Erhöhung

        Returns:
            {
                'window_start': date,
                'window_end': date,
                'window_start_day': int,  # Tage seit Blüte-Start
                'window_end_day': int,
                'days_remaining': tuple[int, int],  # (min, max) Tage ab heute
                'confidence': str,
                'confidence_label': str,
                'basis': str,  # 'cultivar_only' | 'cultivar_plus_observations' | 'trend_extrapolation'
                'recommendation': str,
            }
        """
        today = date.today()
        days_in_flower = (today - flowering_start_date).days

        # 1. Basis-Fenster aus Cultivar-Daten
        basis_start_day = min_flowering_weeks * 7
        basis_end_day = max_flowering_weeks * 7
        window_start = flowering_start_date + timedelta(days=basis_start_day)
        window_end = flowering_start_date + timedelta(days=basis_end_day)

        confidence = 'low'
        basis = 'cultivar_only'

        # 2. Verfeinerung durch Trichom-Observations
        obs = trichome_observations or []
        if len(obs) >= 1:
            latest = obs[-1]
            amber = latest.get('amber_percent', 0)
            cloudy = latest.get('cloudy_percent', 0)

            confidence = 'medium'
            basis = 'cultivar_plus_observations'

            if amber > 15:
                # Überreife — sofort ernten
                window_start = today
                window_end = today
                confidence = 'very_high'
            elif cloudy >= 70 and 5 <= amber <= 15:
                # Peak — 0-2 Tage
                window_start = today
                window_end = today + timedelta(days=2)
                confidence = 'very_high'
            elif cloudy >= 50 and amber < 5:
                # Approaching — 3-7 Tage
                window_start = today + timedelta(days=3)
                window_end = today + timedelta(days=7)
                confidence = 'high' if len(obs) >= 3 else 'medium'

        # 3. Trend-Extrapolation bei >= 2 Observations
        if len(obs) >= 2:
            amber_rate = self._calculate_amber_rate(obs)
            if amber_rate and amber_rate > 0:
                current_amber = obs[-1].get('amber_percent', 0)
                days_to_target_min = max(0, (self.TARGET_AMBER_MIN - current_amber) / amber_rate)
                days_to_target_max = max(0, (self.TARGET_AMBER_MAX - current_amber) / amber_rate)
                window_start = today + timedelta(days=int(days_to_target_min))
                window_end = today + timedelta(days=int(days_to_target_max))
                confidence = 'high'
                basis = 'trend_extrapolation'

        # 4. Konfidenz-Boost durch Aroma-Observations
        if aroma_observations:
            latest_aroma = aroma_observations[-1]
            if latest_aroma.get('consistency') in ('stable', 'fading') and latest_aroma.get('intensity', 0) >= 7:
                if confidence == 'high':
                    confidence = 'very_high'

        margin = self.CONFIDENCE_LEVELS[confidence]['window_margin_days']

        window_start_day = (window_start - flowering_start_date).days
        window_end_day = (window_end - flowering_start_date).days
        days_remaining_min = max(0, (window_start - today).days)
        days_remaining_max = max(0, (window_end - today).days)

        return {
            'window_start': window_start,
            'window_end': window_end,
            'window_start_day': window_start_day,
            'window_end_day': window_end_day,
            'days_remaining': (days_remaining_min, days_remaining_max),
            'confidence': confidence,
            'confidence_label': self.CONFIDENCE_LEVELS[confidence]['label'],
            'margin_days': margin,
            'basis': basis,
            'recommendation': self._build_recommendation(
                days_remaining_min, days_remaining_max, confidence, days_in_flower,
                basis_start_day,
            ),
        }

    def _calculate_amber_rate(self, observations: list[dict]) -> float | None:
        """Berechnet die durchschnittliche Amber-Zunahme pro Tag."""
        if len(observations) < 2:
            return None

        first = observations[0]
        last = observations[-1]
        days_between = (last['observed_at'] - first['observed_at']).days
        if days_between <= 0:
            return None

        amber_delta = last.get('amber_percent', 0) - first.get('amber_percent', 0)
        return amber_delta / days_between

    def _build_recommendation(
        self,
        days_min: int,
        days_max: int,
        confidence: str,
        days_in_flower: int,
        basis_start_day: int,
    ) -> str:
        """Erzeugt eine menschenlesbare Empfehlung."""
        if days_max == 0:
            return 'Erntefenster erreicht — Ernte innerhalb 24-48h empfohlen.'
        if days_min <= 2:
            return f'Erntefenster beginnt in Kürze ({days_min}-{days_max} Tage). Tägliche Trichom-Kontrolle.'

        # Empfehlung zur Beobachtungsfrequenz
        if days_in_flower >= basis_start_day * 0.75:
            return (
                f'Geschätztes Erntefenster: Tag {days_in_flower + days_min}-'
                f'{days_in_flower + days_max} ({days_min}-{days_max} Tage). '
                f'Tägliche Trichom-Kontrolle empfohlen (>75% der Blütezeit erreicht).'
            )

        return (
            f'Geschätztes Erntefenster in {days_min}-{days_max} Tagen. '
            f'Wöchentliche Kontrolle bis 75% der Blütezeit, dann täglich.'
        )
```

**Ernte-Ergonomie & Werkzeug-Dokumentation (U-007):**

Die Wahl des Erntewerkzeugs und dessen Hygiene beeinflusst Kontaminationsrisiko und Wundverschluss:

```python
class HarvestToolDocumentation:
    """
    Dokumentation von Erntewerkzeug, Hygiene-Status und Behälter.
    Relevant für Rückverfolgbarkeit (Kontaminations-Quelle bei Schimmelbefall)
    und Best-Practice-Empfehlungen.
    """

    # Empfohlene Werkzeuge nach Pflanzentyp
    RECOMMENDED_TOOLS: dict[str, dict] = {
        'cannabis': {
            'tools': ['Fiskars micro-tip pruner', 'Bonsai-Schere', 'Curved Trimming Scissors'],
            'sanitization': 'Isopropanol 70% zwischen Pflanzen',
            'container': 'Edelstahl-Tablett oder Silikon-Matte (kein Papier — klebt an Harz)',
            'gloves': 'Nitril-Handschuhe (Latex sammelt Trichome)',
        },
        'tomato': {
            'tools': ['Gartenschere', 'Tomatenmesser (gezahnt)'],
            'sanitization': 'Reinigung bei Krankheitsverdacht',
            'container': 'Flacher Korb/Kiste (nicht stapeln — Druckstellen)',
        },
        'mushroom': {
            'tools': ['Pilzmesser (gebogen)', 'Sauberes Drehen und Abreißen'],
            'sanitization': 'Messer zwischen Substratblöcken reinigen',
            'container': 'Papiertüte oder offener Korb (KEIN Plastik — Kondensation)',
        },
        'herb': {
            'tools': ['Kräuterschere', 'Scharfes Messer'],
            'sanitization': 'Saubere Klingen für saubere Schnitte (kein Quetschen)',
            'container': 'Feuchtes Tuch in Korb (frisch) oder Trocknungsgitter (Trocknung)',
        },
        'root_vegetable': {
            'tools': ['Grabegabel (nicht Spaten — vermeidet Beschädigung)', 'Hand-Grabewerkzeug'],
            'sanitization': 'Nicht erforderlich',
            'container': 'Kiste mit Erde/Sand für Lagerung',
        },
    }

    @classmethod
    def get_tool_recommendation(cls, species_type: str) -> dict:
        """Gibt artspezifische Werkzeug-Empfehlung zurück."""
        return cls.RECOMMENDED_TOOLS.get(species_type, {
            'tools': ['Scharfe, saubere Gartenschere'],
            'sanitization': 'Reinigung zwischen Pflanzen empfohlen',
            'container': 'Sauberer Behälter',
        })
```

**2. Harvest Batch Manager:**
```python
from datetime import date, time, datetime
from typing import Literal, Optional
import hashlib

class HarvestEnvironment(BaseModel):
    """Strukturierte Umweltbedingungen zum Erntezeitpunkt (statt Freitext)"""
    temperature_c: Optional[float] = None
    humidity_rh: Optional[float] = None
    vpd_kpa: Optional[float] = None
    precipitation_last_24h: Optional[bool] = None  # Outdoor: Schimmelrisiko beim Trocknen
    light_status: Optional[Literal['dark_period', 'lights_on', 'natural_light']] = None


class HarvestBatch(BaseModel):
    """Ernte-Charge mit vollständiger Dokumentation"""

    batch_id: str = Field(description="Format: PLANT_ID_YYYYMMDD_SEQ")
    plant_id: str
    harvest_date: date
    harvest_time: time
    harvest_type: Literal['partial', 'final', 'continuous', 'season_harvest']
    harvest_season: Optional[int] = Field(
        None, ge=1,
        description="Saisonale Ernte-Nummer für Perenniale (REQ-003 Perennial-Modus). "
                    "Ermöglicht Yield-Vergleich über Saisons hinweg."
    )
    season_year: Optional[int] = Field(
        None, ge=2020,
        description="Erntejahr für Perenniale. Zusammen mit harvest_season ergibt sich "
                    "ein eindeutiger Saison-Identifier (z.B. 2026/Saison 3)."
    )
    thinning_performed: Optional[bool] = Field(
        None,
        description="Wurde Fruchtausdünnung (Thinning) vor Ernte durchgeführt? "
                    "Relevant für Obstbäume — beeinflusst Fruchtgröße und -qualität."
    )
    thinning_percent: Optional[float] = Field(
        None, ge=0, le=90,
        description="Prozent der entfernten Früchte bei Ausdünnung (z.B. 30 = 30% entfernt)."
    )
    wet_weight_g: float = Field(gt=0, le=100000)
    quality_grade: Literal['A+', 'A', 'B', 'C', 'D'] = 'B'
    harvester: str
    # Strukturierte Umwelterfassung statt Freitext (U-004)
    harvest_environment: Optional['HarvestEnvironment'] = None
    # Ernte-Ergonomie & Werkzeug-Dokumentation (U-007)
    harvest_tool: Optional[str] = Field(
        None, max_length=100,
        description="Verwendetes Erntewerkzeug (z.B. 'Fiskars micro-tip pruner', 'Grabegabel')"
    )
    tool_sanitized: Optional[bool] = Field(
        None,
        description="Werkzeug vor Ernte desinfiziert? Pflicht bei Partial Harvest und Cannabis."
    )
    container_type: Optional[Literal[
        'mesh_tray', 'paper_bag', 'bucket', 'basket', 'crate',
        'silicone_mat', 'stainless_tray', 'net_bag'
    ]] = Field(None, description="Erntebehälter-Typ")
    notes: Optional[str] = Field(None, max_length=1000)
    karenz_check_passed: bool = Field(
        default=True,
        description="Karenzzeit-Prüfung gegen REQ-010 IPM-Treatment-Log. "
                    "Batch-Erstellung wird blockiert wenn letzte chemische Behandlung "
                    "< Karenzzeit (PHI) zurückliegt. Force-Override nur für "
                    "nicht-essbare Kulturen (Zierpflanzen) mit Dokumentation."
    )

    @staticmethod
    def generate_batch_id(plant_id: str, harvest_date: date, sequence: int = 1) -> str:
        """Generiert eindeutige Batch-ID"""
        date_str = harvest_date.strftime('%Y%m%d')
        seq_str = f'{sequence:03d}'
        return f'{plant_id}_{date_str}_{seq_str}'

    def generate_qr_code_url(self) -> str:
        """Generiert QR-Code URL"""
        base_url = 'https://api.qrserver.com/v1/create-qr-code/'
        params = f'?data={self.batch_id}&size=200x200&format=png'
        return base_url + params

    # Artspezifischer Wassergehalt (% des Nassgewichts)
    # Bestimmt den Trockengewicht-Faktor: dry = wet × (1 - moisture/100)
    SPECIES_MOISTURE_CONTENT: dict[str, float] = {
        'cannabis':     75.0,   # Blüten: ~75% Wasserverlust
        'tomato':       94.0,   # Sehr wasserhaltig (Trockengewicht-Faktor 0.06)
        'pepper':       92.0,   # Faktor 0.08
        'cucumber':     96.0,   # Faktor 0.04
        'lettuce':      95.0,   # Faktor 0.05
        'potato':       80.0,   # Faktor 0.20
        'carrot':       88.0,   # Faktor 0.12
        'onion':        89.0,   # Faktor 0.11
        'basil':        85.0,   # Kräuter: 60-85% je nach Trocknung
        'herb_dried':   70.0,   # Getrocknete Kräuter (Hang-Dry)
        'strawberry':   91.0,   # Faktor 0.09
        'hop':          78.0,   # Hopfendolden ähnlich Cannabis
        'default':      75.0,
    }

    def estimate_dry_weight(
        self,
        moisture_loss_percent: Optional[float] = None,
        species_type: str = 'cannabis',
        drying_method: Literal['hang_dry', 'rack_dry', 'dehydrator', 'fresh'] = 'hang_dry',
    ) -> float:
        """
        Schätzt Trockengewicht basierend auf artspezifischem Wassergehalt.

        Args:
            moisture_loss_percent: Expliziter Override (wenn None, wird species_type verwendet)
            species_type: Pflanzentyp für Wassergehalt-Lookup
            drying_method: Trocknungsmethode beeinflusst den Verlust:
                hang_dry: Standard (Cannabis: 75%, Kräuter: 70-85%)
                rack_dry: Etwas weniger Verlust (Wet Trim)
                dehydrator: Kontrollierte Restfeuchte (~8-12%)
                fresh: Kein Trocknen (für Frischprodukte wie Tomaten, Salat)

        Returns:
            Geschätztes Trockengewicht in Gramm
        """
        if drying_method == 'fresh':
            return self.wet_weight_g  # Frischprodukte: kein Trocknungsverlust

        if moisture_loss_percent is None:
            moisture_loss_percent = self.SPECIES_MOISTURE_CONTENT.get(
                species_type, self.SPECIES_MOISTURE_CONTENT['default']
            )

        # Rack-Dry / Wet-Trim: Blattmaterial wird VOR der Trocknung entfernt.
        # Das reduziert das Nassgewicht (Basis), NICHT den prozentualen Wasserverlust.
        # → Trim-Gewicht aus calculate_trim_waste() abziehen, dann gleichen moisture_loss anwenden.
        effective_wet = self.wet_weight_g
        if drying_method == 'rack_dry' and hasattr(self, '_trim_weight_g'):
            effective_wet = max(0, self.wet_weight_g - self._trim_weight_g)

        dry_weight = effective_wet * (1 - moisture_loss_percent / 100)
        return round(dry_weight, 1)

    def calculate_trim_waste(
        self,
        trim_weight_g: float,
        stem_weight_g: float = 0
    ) -> Dict:
        """Berechnet Verschnitt-Anteil"""

        total_waste = trim_weight_g + stem_weight_g
        waste_percent = (total_waste / self.wet_weight_g) * 100
        usable_weight = self.wet_weight_g - total_waste

        return {
            'trim_weight_g': trim_weight_g,
            'stem_weight_g': stem_weight_g,
            'total_waste_g': total_waste,
            'waste_percent': round(waste_percent, 1),
            'usable_weight_g': round(usable_weight, 1),
            'usable_percent': round(100 - waste_percent, 1)
        }

    def generate_seed_to_shelf_id(self, seed_id: str) -> str:
        """Erstellt Traceability-ID"""
        data = f'{seed_id}_{self.plant_id}_{self.batch_id}'
        hash_obj = hashlib.sha256(data.encode())
        return f'S2S_{hash_obj.hexdigest()[:12].upper()}'

class QualityAssessment(BaseModel):
    """Qualitätsbewertung für Ernte-Batch"""

    batch_id: str
    assessed_at: datetime
    assessed_by: str

    # Bewertungs-Dimensionen (0-100)
    appearance_score: int = Field(ge=0, le=100)
    aroma_score: int = Field(ge=0, le=100)
    trichome_coverage_score: Optional[int] = Field(None, ge=0, le=100)
    bud_density_score: Optional[int] = Field(None, ge=0, le=100)
    color_score: int = Field(ge=0, le=100)

    # Defekte
    defects: List[str] = Field(default_factory=list)

    # Zusätzliche Cannabis-Metriken
    potency_estimate: Optional[Literal['Low', 'Medium', 'High', 'Very High']] = None
    terpene_profile: Optional[Dict[str, str]] = None  # {dominant: 'Myrcene', secondary: 'Limonene'}

    def calculate_overall_score(
        self, species_type: str = 'cannabis', weights: Optional[Dict[str, float]] = None
    ) -> int:
        """
        Berechnet gewichteten Gesamt-Score.
        WICHTIG: species_type bestimmt die Gewichtung — Cannabis-Default wird
        NICHT für andere Arten verwendet. Dimensionen mit Gewicht 0 werden ignoriert.

        Args:
            species_type: Pflanzentyp für artspezifische Gewichtung
            weights: Custom weights für Dimensionen (überschreibt Profil)

        Returns:
            Overall score 0-100
        """
        if not weights:
            # Artspezifische Gewichtung aus Profil laden
            profile = self.get_quality_profile(species_type)
            weights = profile.get('weights', {
                'appearance': 0.30,
                'aroma': 0.20,
                'color': 0.20,
                'trichome': 0.0,  # Nicht für alle Arten relevant
                'density': 0.0,
            })

        scores = {
            'appearance': self.appearance_score,
            'aroma': self.aroma_score,
            'trichome': self.trichome_coverage_score if self.trichome_coverage_score else 0,
            'density': self.bud_density_score if self.bud_density_score else 0,
            'color': self.color_score
        }

        weighted_sum = sum(
            scores[dim] * weights.get(dim, 0)
            for dim in scores
        )

        # Penalty für Defekte
        defect_penalty = len(self.defects) * 5  # -5 Punkte pro Defekt

        final_score = max(0, weighted_sum - defect_penalty)

        return int(final_score)

    def assign_grade(self, overall_score: int) -> Literal['A+', 'A', 'B', 'C', 'D']:
        """Weist Qualitäts-Grade basierend auf Score zu"""

        if overall_score >= 95:
            return 'A+'
        elif overall_score >= 85:
            return 'A'
        elif overall_score >= 70:
            return 'B'
        elif overall_score >= 50:
            return 'C'
        else:
            return 'D'

    def get_quality_report(self) -> Dict:
        """Generiert detaillierten Qualitäts-Report"""

        overall = self.calculate_overall_score()
        grade = self.assign_grade(overall)

        return {
            'overall_score': overall,
            'grade': grade,
            'dimensions': {
                'appearance': self.appearance_score,
                'aroma': self.aroma_score,
                'trichome_coverage': self.trichome_coverage_score,
                'bud_density': self.bud_density_score,
                'color': self.color_score
            },
            'defects': self.defects,
            'defect_count': len(self.defects),
            'potency': self.potency_estimate,
            'terpenes': self.terpene_profile,
            'recommendation': self._get_recommendation(grade),
            'assessed_by': self.assessed_by,
            'assessed_at': self.assessed_at
        }

    # Artspezifische Bewertungsdimensionen und Gewichtungen
    SPECIES_QUALITY_PROFILES: dict[str, dict] = {
        'cannabis': {
            'dimensions': ['appearance', 'aroma', 'trichome_coverage', 'bud_density', 'color'],
            'weights': {'appearance': 0.25, 'aroma': 0.25, 'trichome': 0.20, 'density': 0.15, 'color': 0.15},
            'recommendations': {
                'A+': 'Premium-Qualität - Top-Shelf, maximaler Preis',
                'A': 'Sehr gute Qualität - Mid-to-Top-Shelf',
                'B': 'Gute Qualität - Mid-Shelf, Eigenverbrauch',
                'C': 'Akzeptable Qualität - Budget, Extraktion',
                'D': 'Niedrige Qualität - Nur Extraktion/Hash',
            }
        },
        'tomato': {
            'dimensions': ['appearance', 'firmness', 'taste', 'color', 'shelf_life'],
            'weights': {'appearance': 0.15, 'firmness': 0.20, 'taste': 0.30, 'color': 0.20, 'shelf_life': 0.15},
            'recommendations': {
                'A+': 'Premium - Direkt Verzehr, Marktstand-Qualität',
                'A': 'Sehr gut - Frischverbrauch, Salate',
                'B': 'Gut - Kochen, Saucen',
                'C': 'Akzeptabel - Nur verarbeitet (Sauce, Suppe)',
                'D': 'Kompost / Tierfutter',
            }
        },
        'root_vegetable': {
            'dimensions': ['appearance', 'firmness', 'size_uniformity', 'skin_quality', 'storage_quality'],
            'weights': {'appearance': 0.15, 'firmness': 0.20, 'size_uniformity': 0.20, 'skin_quality': 0.25, 'storage_quality': 0.20},
            'recommendations': {
                'A+': 'Premium-Lagerqualität - 6+ Monate haltbar',
                'A': 'Sehr gut - 3-6 Monate lagerfähig',
                'B': 'Gut - 1-3 Monate, baldiger Verbrauch',
                'C': 'Akzeptabel - Sofortverbrauch',
                'D': 'Beschädigt - Nur sofortige Verarbeitung',
            }
        },
        'herb': {
            'dimensions': ['aroma', 'color', 'leaf_stem_ratio', 'freshness', 'drying_suitability'],
            'weights': {'aroma': 0.35, 'color': 0.20, 'leaf_stem_ratio': 0.20, 'freshness': 0.15, 'drying_suitability': 0.10},
            'recommendations': {
                'A+': 'Premium-Aroma - Frischverkauf oder Top-Trockenware',
                'A': 'Sehr gut - Frisch oder getrocknet',
                'B': 'Gut - Kochen, Tee',
                'C': 'Akzeptabel - Nur Trocknung/Extraktion',
                'D': 'Verblüht/Überreif - Samengewinnung',
            }
        },
    }

    def get_quality_profile(self, species_type: str = 'cannabis') -> dict:
        """Gibt artspezifisches Qualitätsprofil zurück."""
        if species_type in self.SPECIES_QUALITY_PROFILES:
            return self.SPECIES_QUALITY_PROFILES[species_type]
        # Generischer Fallback — nicht Cannabis-Gewichtung für unbekannte Arten
        return {
            'dimensions': ['appearance', 'aroma', 'color'],
            'weights': {'appearance': 0.40, 'aroma': 0.30, 'color': 0.30,
                        'trichome': 0.0, 'density': 0.0},
            'recommendations': {'A+': 'Exzellent', 'A': 'Sehr gut', 'B': 'Gut',
                                'C': 'Befriedigend', 'D': 'Mangelhaft'},
        }

    def _get_recommendation(self, grade: str, species_type: str = 'cannabis') -> str:
        """Gibt artspezifische Verwendungs-Empfehlung basierend auf Grade"""
        profile = self.get_quality_profile(species_type)
        return profile['recommendations'].get(grade, 'Keine Empfehlung')
```

**3. Flushing Protocol Manager:**
```python
from datetime import date, datetime, timedelta

class FlushingProtocol(BaseModel):
    """Nährstoffreduktion vor Ernte"""

    plant_id: str
    substrate_type: Literal['hydro', 'coco', 'soil', 'living_soil']
    current_ec: float = Field(ge=0, le=5)
    days_until_harvest: int = Field(ge=0, le=60)
    is_organic: bool = Field(default=False, description="Organische Düngung — Flushing optional/abgeraten")

    # Substrat-spezifische Flush-Dauer (konsistent mit REQ-004 FlushingProtocol)
    FLUSH_DURATIONS = {
        'hydro':       {'min': 7, 'optimal': 10, 'max': 14},
        'coco':        {'min': 10, 'optimal': 14, 'max': 21},
        'soil':        {'min': 21, 'optimal': 28, 'max': 42},    # Korrigiert: Soil-CEC erfordert längere Flush
        'living_soil': None,  # Kein Flushing — zerstört Mikrobiom
    }

    def get_schedule(self) -> Dict:
        """Erstellt schrittweisen Flush-Plan. Flushing ist optional."""

        duration_map = self.FLUSH_DURATIONS.get(self.substrate_type)

        # Living Soil: Kein Flushing empfohlen
        if duration_map is None or self.substrate_type == 'living_soil':
            return {
                'status': 'SKIP_RECOMMENDED',
                'recommendation': 'Flushing bei Living Soil nicht empfohlen — zerstört das '
                                  'Mikrobiom (Mykorrhiza, Trichoderma, Bakterienkulturen). '
                                  'Einfach nur mit Wasser gießen, ohne aktives Durchspülen.',
                'scientific_note': 'University of Guelph (2020): Kein signifikanter Unterschied '
                                   'in Mineralgehalt oder Geschmack zwischen geflushten/ungeflushten Proben.',
                'emergency_flush': False,
            }

        # Organische Düngung: Warnung
        if self.is_organic:
            return {
                'status': 'OPTIONAL',
                'recommendation': 'Bei organischer Düngung ist Flushing meist nicht nötig — '
                                  'Nährstoffe sind mikrobiell gebunden und lösen sich nicht '
                                  'einfach aus. Normales Gießen mit Wasser reicht.',
                'emergency_flush': False,
            }

        optimal_days = duration_map['optimal']

        # Validierung
        if self.days_until_harvest < duration_map['min']:
            return {
                'status': 'TOO_LATE',
                'warning': f"Nur noch {self.days_until_harvest} Tage - Minimum: {duration_map['min']}",
                'recommendation': 'Notfall-Flush: Täglich mit 3x Topf-Volumen pH-Wasser durchspülen',
                'emergency_flush': True
            }

        # Bestimme tatsächliche Flush-Dauer
        if self.days_until_harvest >= optimal_days:
            flush_days = optimal_days
        else:
            flush_days = self.days_until_harvest

        # Gradueller EC-Abbau
        steps = []
        ec_reduction_per_day = self.current_ec / flush_days

        for day in range(flush_days + 1):
            target_ec = max(0, self.current_ec - (ec_reduction_per_day * day))

            # Strategie basierend auf Tag
            if day == 0:
                action = f"Letzte normale Düngung (EC {target_ec:.1f})"
                dosage_percent = 100
                water_only = False
            elif day <= flush_days // 3:
                action = f"Reduzierte Dosis (EC {target_ec:.1f})"
                dosage_percent = 50
                water_only = False
            elif day <= 2 * flush_days // 3:
                action = f"Minimale Dosis (EC {target_ec:.1f})"
                dosage_percent = 25
                water_only = False
            else:
                action = "Nur pH-Wasser (EC ~0.0)"
                dosage_percent = 0
                water_only = True
                # Ziel: Runoff-EC ≈ Basis-Wasser-EC (nicht 0.0, da unrealistisch)
                target_ec = getattr(self, 'base_water_ec', 0.3)

            steps.append({
                'day': day,
                'days_to_harvest': self.days_until_harvest - day,
                'target_ec': round(target_ec, 2),
                'action': action,
                'dosage_percent': dosage_percent,
                'water_only': water_only,
                'measurement_required': day % 3 == 0,  # Alle 3 Tage messen
                'runoff_ec_target': f'< {target_ec + 0.3:.1f} mS'  # Max. 0.3 über Input-EC
            })

        return {
            'status': 'OK',
            'total_flush_days': flush_days,
            'start_ec': self.current_ec,
            'substrate_type': self.substrate_type,
            'schedule': steps,
            'notes': self._get_substrate_specific_notes(),
            'expected_results': {
                'improved_taste': 'Reduzierter Nährstoff-Geschmack',
                'smoother_smoke': 'Weniger Harshness',
                'ash_color': 'Weißere Asche (weniger Salze)',
                'chlorophyll': 'Reduziertes Chlorophyll = weniger "grüner" Geschmack'
            }
        }

    def _get_substrate_specific_notes(self) -> List[str]:
        """Substrat-spezifische Flush-Hinweise"""

        notes_map = {
            'hydro': [
                'Täglich Reservoir prüfen und auffüllen',
                'EC sollte innerhalb 3 Tagen unter 0.5 mS fallen',
                'pH-Wert konstant halten (5.8-6.2)',
                'Luftsteine laufen lassen für Sauerstoff'
            ],
            'coco': [
                'Mit 3x Topf-Volumen durchspülen bei jedem Gießen',
                'Runoff-EC messen - sollte nahe Input-EC sein',
                'Nicht austrocknen lassen (Coco speichert Salze)',
                'CalMag weglassen ab Tag 5'
            ],
            'soil': [
                'Nicht zu viel wässern - Wurzelfäule-Gefahr',
                'Topf zwischen Gießen leicht antrocknen lassen',
                'Blätter werden gelb = Normal (Nährstoff-Mobilisierung)',
                'Keine Panik bei Blattverfärbungen'
            ],
            'living_soil': [
                'KEIN Flushing empfohlen — zerstört Mikrobiom',
                'Nur mit Wasser gießen reicht aus',
                'Organisch gebundene Nährstoffe lösen sich nicht durch Durchspülen'
            ]
        }

        return notes_map.get(self.substrate_type, [])
```

### Datenvalidierung (Type Hinting):
```python
from typing import Literal, Optional, List, Dict
from pydantic import BaseModel, Field, field_validator
from datetime import date, time, datetime

HarvestType = Literal['partial', 'final', 'continuous']
QualityGrade = Literal['A+', 'A', 'B', 'C', 'D']
PotencyLevel = Literal['Low', 'Medium', 'High', 'Very High']
IndicatorType = Literal['trichome', 'foliage', 'brix', 'size', 'color', 'days_since_flowering', 'aroma', 'texture', 'ethylene', 'mushroom', 'gdd', 'continuous_harvest']

class HarvestObservation(BaseModel):
    """Reife-Check-Dokumentation"""

    plant_id: str
    indicator_type: IndicatorType
    observed_at: datetime
    observer: str
    measurements: Dict
    photo_refs: List[str] = Field(default_factory=list)
    ripeness_assessment: Literal['immature', 'approaching', 'peak', 'overripe']
    days_to_harvest_estimate: Optional[int] = Field(None, ge=0, le=60)
    notes: Optional[str] = Field(None, max_length=500)

    @field_validator('measurements')
    @classmethod
    def validate_measurements(cls, v, info):
        indicator = info.data.get('indicator_type')

        # Trichome braucht Prozent-Werte
        if indicator == 'trichome':
            required = {'clear_percent', 'cloudy_percent', 'amber_percent'}
            if not required.issubset(v.keys()):
                raise ValueError(f"Trichome-Messung benötigt: {required}")

            # Validiere Summe
            total = sum(v.get(k, 0) for k in required)
            if abs(total - 100) > 5:
                raise ValueError(f"Prozent-Summe = {total}, sollte ~100 sein")

        return v

class YieldMetric(BaseModel):
    """Ertrags-Metriken"""

    batch_id: str
    yield_per_plant_g: float = Field(gt=0)
    yield_per_m2_g: Optional[float] = Field(None, gt=0)
    total_yield_g: float = Field(gt=0)
    trim_waste_percent: float = Field(ge=0, le=100)
    usable_yield_g: float = Field(gt=0)

    @field_validator('usable_yield_g')
    @classmethod
    def validate_usable_yield(cls, v, info):
        total = info.data.get('total_yield_g', 0)
        if v > total:
            raise ValueError("Usable yield kann nicht größer als total yield sein")
        return v

    def calculate_efficiency_score(self, grow_area_m2: float, cycle_days: int) -> Dict:
        """Berechnet Effizienz-Metriken"""

        if self.yield_per_m2_g:
            grams_per_m2_per_day = self.yield_per_m2_g / cycle_days
        else:
            grams_per_m2_per_day = 0

        return {
            'yield_per_m2': self.yield_per_m2_g,
            'grams_per_day': self.total_yield_g / cycle_days,
            'grams_per_m2_per_day': round(grams_per_m2_per_day, 2),
            'usable_percent': round((self.usable_yield_g / self.total_yield_g) * 100, 1),
            'cycle_efficiency_score': self._calculate_score(grams_per_m2_per_day)
        }

    # Artspezifische Effizienz-Benchmarks — Cannabis-Schwellenwerte sind NICHT
    # auf andere Kulturen übertragbar (Nass- vs. Trockengewicht-Basis).
    SPECIES_EFFICIENCY_BENCHMARKS: dict[str, dict] = {
        'cannabis':  {'excellent': 1.5, 'good': 1.0, 'average': 0.7, 'weight_basis': 'dry'},
        'tomato':    {'excellent': 5.0, 'good': 3.0, 'average': 2.0, 'weight_basis': 'wet'},
        'lettuce':   {'excellent': 15.0, 'good': 10.0, 'average': 5.0, 'weight_basis': 'wet'},
        'pepper':    {'excellent': 3.0, 'good': 2.0, 'average': 1.0, 'weight_basis': 'wet'},
        'cucumber':  {'excellent': 8.0, 'good': 5.0, 'average': 3.0, 'weight_basis': 'wet'},
        'strawberry': {'excellent': 3.0, 'good': 1.5, 'average': 1.0, 'weight_basis': 'wet'},
        'herb':      {'excellent': 2.0, 'good': 1.0, 'average': 0.5, 'weight_basis': 'dry'},
    }

    def _calculate_score(self, g_m2_day: float, species_type: str = 'cannabis') -> str:
        """Score basierend auf Gram/m²/Tag — artspezifisch kalibriert"""
        benchmarks = self.SPECIES_EFFICIENCY_BENCHMARKS.get(
            species_type,
            self.SPECIES_EFFICIENCY_BENCHMARKS['cannabis']
        )
        if g_m2_day >= benchmarks['excellent']:
            return 'Excellent'
        elif g_m2_day >= benchmarks['good']:
            return 'Good'
        elif g_m2_day >= benchmarks['average']:
            return 'Average'
        else:
            return 'Below Average'
```

## 4. Authentifizierung & Autorisierung

> **Hinweis (SEC-H-001):** Dieser Abschnitt wurde nachträglich ergänzt, um die Auth-Anforderungen
> gemäß REQ-023 (Authentifizierung) und REQ-024 (Mandantenverwaltung) zu dokumentieren.

**Standardregel:** Alle Endpunkte dieses REQ erfordern Authentifizierung (JWT Bearer Token)
und Tenant-Mitgliedschaft, sofern nicht anders angegeben.

| Ressource/Endpoint-Gruppe | Lesen | Schreiben | Löschen |
|---------------------------|-------|-----------|---------|
| HarvestIndicators (globale Stammdaten) | Nein | Ja | Ja |
| HarvestBatches (Tenant-scoped) | Mitglied | Mitglied | Admin |
| HarvestObservations (Tenant-scoped) | Mitglied | Mitglied | Admin |
| QualityAssessments (Tenant-scoped) | Mitglied | Mitglied | Admin |
| YieldMetrics (Tenant-scoped) | Mitglied | Mitglied | Admin |

## 5. Abhängigkeiten

**Erforderliche Module:**
- REQ-001 (Stammdaten): Species für Harvest-Indicators, Ethylen-Klassifikation
- REQ-003 (Phasen): Harvest-Phase, Flowering-Tracking, GDD-Daten für Reife-Prognose, Perennial-Modus für saisonale Ernten
- REQ-004 (Düngung): Flushing-Protokoll (EC-Ziel relativ zu base_water_ec)
- REQ-005 (Sensorik): VPD/Temperatur bei Ernte, GDD-Akkumulation für Reife-Prognose
- REQ-002 (Standort): Area für Yield/m²-Berechnung
- REQ-010 (IPM): **Karenz-Gate** — Batch-Erstellung blockiert wenn Karenzzeit nach letzter chemischer Behandlung nicht eingehalten

**Wird benötigt von:**
- REQ-008 (Post-Harvest): Batch-Übergabe zur Trocknung/Curing
- REQ-009 (Dashboard): Harvest-Kalender, Yield-Analytics
- REQ-010 (IPM): Karenzzeit-Validierung vor Ernte

**Externe Integrationen:**
- QR-Code-Generator API
- Computer Vision (optional) für Trichom-Analyse
- Refraktometer (Hardware) für Brix-Messung

## 6. Akzeptanzkriterien

### Definition of Done (DoD):

- [ ] **6+ Harvest-Indicator-Typen:** Trichome (Multi-Standort), Foliage, Brix, Aroma, Days-Since-Flowering, Color
- [ ] **Trichome Multi-Standort-Sampling:** Gewichteter Durchschnitt über top_cola/mid_canopy/lower_branch mit Partial-Harvest-Empfehlung
- [ ] **Aroma-Indikator:** Intensität (0-10), dominantes Terpen, Konsistenz (developing/stable/fading)
- [ ] **Ethylen/Klimakterium:** Artspezifische Unterscheidung — klimakterische Früchte können vor Vollreife geerntet werden, nicht-klimakterische nicht
- [ ] **Optionales Flushing:** Flushing als optionales Pre-Harvest-Protokoll; `none`/`skip` als valide Wahl; Living Soil = kein Flushing empfohlen
- [ ] **Flushing-Dauern konsistent mit REQ-004:** Soil 21-42d (nicht 14-21d), Hydro 7-14d, Coco 10-21d
- [ ] **Batch-ID-Generierung:** Eindeutige IDs nach Schema PLANT_YYYYMMDD_SEQ
- [ ] **QR-Code-Integration:** Jeder Batch hat QR-Code mit Traceability
- [ ] **Erntegewicht-Tracking:** Nass + artspezifisches geschätztes Trockengewicht (Cannabis 75%, Tomate 94%, Kräuter 85% Wasserverlust)
- [ ] **Quality-Scoring:** Polymorph — artspezifische Dimensionen und Gewichtungen (Cannabis: Trichom/Dichte; Tomate: Geschmack/Festigkeit; Kräuter: Aroma/Blatt-Stiel-Verhältnis)
- [ ] **Photo-Dokumentation:** Before/After-Fotos für jeden Batch
- [ ] **Partial-Harvest-Support:** Top-Buds zuerst, Lower-Buds später
- [ ] **Yield-Analytics:** Gram/m²/Tag-Berechnung
- [ ] **Seed-to-Shelf-ID:** Vollständige Rückverfolgbarkeit
- [ ] **Trichom-Mikroskop-Guide:** Schritt-für-Schritt Anleitung
- [ ] **Brix-Kalibrierung:** Refraktometer-Setup-Guide
- [ ] **Dark-Period-Timer:** Optional 24-48h Dunkelphase vor Ernte
- [ ] **Harvest-Kalender:** Vorschau auf nächste Ernten (14 Tage)
- [ ] **Grade-Distribution:** Statistik über A+/A/B/C-Batches
<!-- Quelle: Tabellen-Analyse UI-NFR-010 §7.2, §9.2 -->
- [ ] **Listenansicht-Filter:** HarvestBatch-Liste bietet Erntezeitraum-Filter (Datums-Range: `?harvested_from=...&harvested_to=...`), optionale Qualitätsgrad- und Erntetyp-Filter (Enum-Chips); alle URL-persistiert (UI-NFR-010 §7.2)
- [ ] **Tablet-Spaltenprioritäten:** HarvestBatch-ListPage blendet auf Tablet Pflanzen-Key aus; Primärspalten: Batch-ID, Datum, Gewicht (UI-NFR-010 §8.1)
- [ ] **Compliance-Export:** HarvestBatch-Liste bietet CSV- und PDF-Export der gefilterten Ansicht für CanG-Dokumentation (Erntemengen, Qualität, Seed-to-Shelf-Rückverfolgbarkeit); UI-NFR-010 §9.2
- [ ] **Karenzzeit-Gate:** Batch-Erstellung prüft automatisch REQ-010 IPM-Treatment-Log auf offene Karenzzeiten
- [ ] **Paprika bedingt klimakterisch:** WEAKLY_CLIMACTERIC-Kategorie für Paprika im Farbumschlag
- [ ] **Melonen-Differenzierung:** Wassermelone → nicht-klimakterisch, Cantaloupe/Honeydew → klimakterisch
- [ ] **Trichom degraded_percent:** Vierte Kategorie für abgestorbene/abgebrochene Trichome
- [ ] **Perennial-Ernte:** harvest_season-Feld für saisonale Ernte bei Dauerkulturen (REQ-003)
- [ ] **CACA-Kulturen:** ContinuousHarvestIndicator mit Schnittöhe, Nachwachszeit, kumulative Yield
- [ ] **Pilz-Ernteindikatoren:** MushroomIndicator (Hutdurchmesser, Velum-Status, Flush-Nummer, Biological Efficiency)
- [ ] **GDD-Erntereife:** GDD-basierte Reife-Prognose statt/ergänzend zu Kalendertagen
- [ ] **Artspezifische Effizienz:** Yield-Score differenziert nach Pflanzentyp und Gewichtsbasis (nass/trocken)
- [ ] **Strukturierte Ernteumgebung:** HarvestEnvironment statt weather_conditions-Freitext
- [ ] **Ernte-Werkzeug-Dokumentation (U-007):** harvest_tool, tool_sanitized, container_type pro Batch; artspezifische Werkzeugempfehlungen
- [ ] **Perennial-Ertragsentwicklung (U-002):** season_year + harvest_season für jahresübergreifende Yield-Analytics; thinning_performed/thinning_percent für Fruchtausdünnung
- [ ] **Ernte-Fenster-Vorhersage (W-007):** HarvestWindowPredictor kombiniert Cultivar-Blütezeit (REQ-001), Phase-Start-Datum (REQ-003) und Trichom-Observations zu adaptivem Erntefenster mit Konfidenz-Stufen (niedrig/mittel/hoch/sehr hoch); Trend-Extrapolation über Amber-Zunahme-Rate; Fenster verengt sich mit jeder Beobachtung

### Testszenarien:

**Szenario 1: Trichom-basierte Erntereife (Cannabis)**
```
GIVEN: Cannabis in Woche 9 der Blüte
      Trichom-Check: Klar 10%, Milchig 75%, Bernstein 15%
WHEN: TrichomeIndicator.assess_ripeness()
THEN:
  - stage = 'peak'
  - recommendation = 'OPTIMALER ZEITPUNKT - Ernten innerhalb 24-48h'
  - quality_impact = 100
  - days_to_harvest = 1
  - effect_profile = 'Balanced - Peak THC'
```

**Szenario 2: Automatischer Flushing-Trigger**
```
GIVEN: Pflanze mit days_to_harvest_estimate = 12
      Substrat = 'coco'
      Aktueller EC = 1.8 mS
WHEN: Täglicher Harvest-Check läuft
THEN:
  - FlushingProtocol wird erstellt (10 Tage optimal für Coco)
  - PreHarvestProtocol-Node angelegt
  - Task "Flushing - Tägliche Kontrolle" generiert
  - Notification: "Flushing gestartet - EC-Reduktion auf 0.0"
```

**Szenario 3: Batch-Erstellung mit QR-Code**
```
GIVEN: Pflanze "PLANT_001" wird am 15.02.2026 geerntet
      Nassgewicht = 450g
WHEN: Batch wird erstellt
THEN:
  - batch_id = "PLANT_001_20260215_001"
  - qr_code_url = "https://api.qrserver.com/v1/create-qr-code/?data=PLANT_001_20260215_001&size=200x200"
  - estimated_dry_weight_g = 112.5 (75% Verlust)
  - quality_grade = 'B' (initial)
```

**Szenario 4: Quality-Assessment & Grading**
```
GIVEN: Batch mit
      appearance_score = 95
      aroma_score = 90
      trichome_coverage_score = 92
      defects = []
WHEN: QualityAssessment.calculate_overall_score()
THEN:
  - overall_score = 92
  - grade = 'A+'
  - recommendation = 'Premium-Qualität - Top-Shelf, maximaler Preis'
```

**Szenario 5: Seed-to-Shelf Traceability**
```
GIVEN: Batch "PLANT_001_20260215_001"
WHEN: Seed-to-Shelf-Query wird ausgeführt
THEN:
  - genetics: {strain: "Gorilla Glue #4", breeder: "GG Strains"}
  - cultivation: {planted_on: "2025-12-01", total_days: 76}
  - harvest: {wet_weight_g: 450, dry_weight_g: 112}
  - quality: {overall_score: 92, grade: 'A+'}
  - storage: {location: "Jar_12", current_weight_g: 110}
```

**Szenario 6: Partial Harvest (Gestaffelt)**
```
GIVEN: Cannabis-Pflanze mit
      Top-Buds = 70% milchige Trichome
      Lower-Buds = 50% milchige Trichome
WHEN: Nutzer wählt "Partial Harvest - Top Only"
THEN:
  - Batch 1: "PLANT_001_20260215_001" (Top-Buds, 300g)
  - Batch 2: (7 Tage später) "PLANT_001_20260222_002" (Lower-Buds, 150g)
  - Plant.status bleibt 'growing' bis Final Harvest
```

**Szenario 7: Yield-Effizienz-Analyse**
```
GIVEN: 5 Batches von gleicher Sorte
      Durchschnitt: 0.8 g/m²/Tag
      Bester Batch: 1.2 g/m²/Tag
WHEN: Yield-Analytics läuft
THEN:
  - avg_yield_per_m2 = 60g
  - top_performer: Batch mit 90g/m²
  - efficiency_score = 'Good'
  - Empfehlung: "Repliziere Bedingungen von Top-Batch"
```

**Szenario 8: Ernte-Fenster-Vorhersage mit adaptiver Verfeinerung (W-007)**
```
GIVEN: Cannabis-Cultivar "Gorilla Glue #4" mit Blütezeit 8-10 Wochen
      Blüte-Start: 01.01.2026
      Trichom-Observations:
        - Tag 42: clear 60%, cloudy 35%, amber 5%
        - Tag 49: clear 40%, cloudy 52%, amber 8%
        - Tag 54: clear 20%, cloudy 68%, amber 12%
WHEN: HarvestWindowPredictor.predict_harvest_window()
THEN:
  - Basis-Fenster (nur Cultivar): Tag 56-70
  - Nach 3 Observations: Amber-Rate = 0.58%/Tag
  - Trend-Extrapolation: Target 10-15% amber
  - window_start_day ≈ 54 (amber bereits bei 12%)
  - window_end_day ≈ 59 (15% amber in ~5 Tagen)
  - confidence = 'high' (3+ Observations mit Trend)
  - recommendation enthält "Tägliche Trichom-Kontrolle"

GIVEN: Gleiche Pflanze, zusätzlich Aroma-Observation:
      - Tag 54: intensity 8/10, consistency 'stable', dominant 'myrcene'
WHEN: HarvestWindowPredictor.predict_harvest_window() mit aroma_observations
THEN:
  - confidence = 'very_high' (Trichom-Trend + stabiles Peak-Aroma)
  - margin_days = 1
```

---

**Hinweise für RAG-Integration:**
- Keywords: Ernte, Trichome, Reife, Flushing, Batch, QR-Code, Yield, Traceability, Aroma, Terpen-Profil, Ethylen, Klimakterisch, Multi-Standort-Sampling, Living Soil, Partial Harvest, Karenzzeit, GDD, Perennial, CACA, Pilzernte, Velum, Erntewerkzeug, Werkzeug-Hygiene, Behälter, Erntefenster, Harvest Window Prediction, Amber-Rate, Trend-Extrapolation, Konfidenz
- Fachbegriffe: Calyx, Pistil, Terpen, CBN, THC, Brix, Chlorophyll, Seed-to-Shelf, Myrcen, Limonen, Linalool, Pinen, Caryophyllen, Klimakterium, Breaker-Stage, Nachreifen, AromaIndicator, EthyleneRipeningClassifier, SPECIES_MOISTURE_CONTENT, WEAKLY_CLIMACTERIC, Biological Efficiency, degraded_percent, HarvestEnvironment, MushroomIndicator, GDDIndicator, ContinuousHarvestIndicator, Wärmesumme, Velum-Status, Flush-Nummer, Bolting, Fruchtausdünnung, HarvestWindowPredictor
- Verknüpfung: Zentral für REQ-004 (Flushing — EC relativ zu base_water_ec), REQ-005 (GDD-Akkumulation), REQ-006 (Karenzzeit-Validierung bei Harvest-Tasks), REQ-008 (Post-Harvest), REQ-009 (Analytics), REQ-010 (Karenz-Gate vor Batch-Erstellung), REQ-003 (GDD-Reife, Perennial-Saisons, Phase-Start-Datum für Erntefenster), REQ-001 (Cultivar-Blütezeit für Erntefenster-Basis)
- Pflanzenwissenschaft: Trichom-Entwicklung (inkl. degraded), Cannabinoid-Degradation, Chlorophyll-Abbau, Terpen-Biosynthese, Ethylen-Produktion, klimakterische/bedingt-klimakterische/nicht-klimakterische Reifung, artspezifischer Wassergehalt, Fruchtausdünnung (Thinning), Cut-and-Come-Again, Pilz-Biological-Efficiency, GDD-Akkumulation (Wärmesumme)
