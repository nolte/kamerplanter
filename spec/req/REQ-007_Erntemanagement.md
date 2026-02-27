# Spezifikation: REQ-007 - Erntemanagement

```yaml
ID: REQ-007
Titel: Gattungsspezifisches Erntemanagement & Reifegradprüfung
Kategorie: Erntezyklus
Fokus: Beides
Technologie: Python, ArangoDB, Computer Vision (optional)
Status: Entwurf
Version: 2.0 (Maximal Erweitert)
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

**Flushing (Nährstoffreduktion):**
- **Hydro:** 7-10 Tage nur pH-Wasser
- **Coco:** 10-14 Tage gradueller EC-Abbau
- **Soil:** 14-21 Tage Wasser-Only
- **Ziel:** Chlorophyll-Abbau, besserer Geschmack

**Dark Period (Dunkelphase):**
- 24-48h vor Ernte für Terpen-Erhaltung
- Reduziert Photosynthese, erhöht Harzproduktion
- Umstritten, aber in Community weit verbreitet

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
    - `indicator_type: Literal['trichome', 'foliage', 'brix', 'size', 'color', 'days_since_flowering', 'aroma', 'texture']`
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
    - `weather_conditions: Optional[str]`
    - `notes: Optional[str]`
    - `qr_code_url: str`

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
    - `protocol_type: Literal['flushing', 'dark_period', 'drought_stress', 'defoliation']`
    - `started_at: datetime`
    - `duration_days: int`
    - `completed_at: Optional[datetime]`
    - `parameters: dict` (z.B. {"ec_start": 1.8, "ec_target": 0.0})

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
observed_for_harvest:        plant_instances → harvest_observations
uses_indicator:              harvest_observations → harvest_indicators
underwent_protocol:          plant_instances → pre_harvest_protocols
harvested_as:                plant_instances → batches
assessed_by:                 batches → quality_assessments
has_yield_metric:            batches → yield_metrics
stored_in:                   batches → storage_locations          // Übergabe an REQ-008
derived_from:                batches → plant_instances             // Bei Partial Harvest (Attribut: portion)
triggered_by:                pre_harvest_protocols → harvest_observations
```

### AQL-Beispiellogik:

**Erntebereitschaft mit Multi-Indicator-Aggregation:**
```aql
// Hole Pflanze und zugehörige Harvest-Indikatoren über Species
LET plant = DOCUMENT('plant_instances', @plant_id)
LET species = FIRST(
  FOR v IN 1..1 OUTBOUND plant GRAPH 'kamerplanter_graph'
    OPTIONS { edgeCollections: ['belongs_to_species'] }
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
LET required_flush_days = (
  substrate_type == 'hydro_solution' ? 7 :
  substrate_type == 'coco' ? 10 :
  substrate_type == 'soil' ? 14 :
  10
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
      target_ec: 0.0,
      start_ec: 1.8  // Placeholder, sollte aus letzter Messung kommen
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
    estimated_dry_weight_g: @wet_weight * 0.25,  // 75% Wasserverlust
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
    """Für Cannabis, Hopfen - Trichom-Mikroskopie"""
    
    indicator_type: Literal['trichome'] = 'trichome'
    
    def assess_ripeness(self, observations: Dict) -> Dict:
        """
        observations = {
            'clear_percent': float,
            'cloudy_percent': float,
            'amber_percent': float
        }
        """
        clear = observations.get('clear_percent', 0)
        cloudy = observations.get('cloudy_percent', 0)
        amber = observations.get('amber_percent', 0)
        
        # Validierung
        total = clear + cloudy + amber
        if abs(total - 100) > 5:  # Toleranz 5%
            return {
                'stage': 'error',
                'recommendation': f'Prozent-Summe = {total} (sollte 100 sein)',
                'quality_impact': 0,
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
            'frequency': 'Täglich ab Woche 7 der Blüte'
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
            'best_time': 'Mittags (höchster Zuckergehalt)',
            'target_values': {
                'Tomaten': '6-8 °Brix',
                'Paprika': '7-9 °Brix',
                'Erdbeeren': '10-14 °Brix',
                'Melonen': '12-16 °Brix'
            }
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
```

**2. Harvest Batch Manager:**
```python
from datetime import date, time, datetime
from typing import Literal, Optional
import hashlib

class HarvestBatch(BaseModel):
    """Ernte-Charge mit vollständiger Dokumentation"""
    
    batch_id: str = Field(description="Format: PLANT_ID_YYYYMMDD_SEQ")
    plant_id: str
    harvest_date: date
    harvest_time: time
    harvest_type: Literal['partial', 'final', 'continuous']
    wet_weight_g: float = Field(gt=0, le=100000)
    quality_grade: Literal['A+', 'A', 'B', 'C', 'D'] = 'B'
    harvester: str
    weather_conditions: Optional[str] = None
    notes: Optional[str] = Field(None, max_length=1000)
    
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
    
    def estimate_dry_weight(
        self,
        moisture_loss_percent: float = 75.0,
        species_factor: float = 1.0
    ) -> float:
        """
        Schätzt Trockengewicht basierend auf Wasserverlust
        
        Args:
            moisture_loss_percent: Standard 75% bei Cannabis
            species_factor: Artspezifischer Korrekturfaktor
        
        Returns:
            Geschätztes Trockengewicht in Gramm
        """
        dry_weight = self.wet_weight_g * (1 - moisture_loss_percent / 100) * species_factor
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
    
    def calculate_overall_score(self, weights: Optional[Dict[str, float]] = None) -> int:
        """
        Berechnet gewichteten Gesamt-Score
        
        Args:
            weights: Custom weights für Dimensionen
        
        Returns:
            Overall score 0-100
        """
        if not weights:
            # Default-Gewichtung
            weights = {
                'appearance': 0.25,
                'aroma': 0.25,
                'trichome': 0.20,
                'density': 0.15,
                'color': 0.15
            }
        
        scores = {
            'appearance': self.appearance_score,
            'aroma': self.aroma_score,
            'trichome': self.trichome_coverage_score or 50,
            'density': self.bud_density_score or 50,
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
    
    def _get_recommendation(self, grade: str) -> str:
        """Gibt Verwendungs-Empfehlung basierend auf Grade"""
        
        recommendations = {
            'A+': 'Premium-Qualität - Top-Shelf, maximaler Preis',
            'A': 'Sehr gute Qualität - Mid-to-Top-Shelf',
            'B': 'Gute Qualität - Mid-Shelf, Eigenverbrauch',
            'C': 'Akzeptable Qualität - Budget, Extraktion',
            'D': 'Niedrige Qualität - Nur Extraktion/Hash'
        }
        
        return recommendations.get(grade, 'Keine Empfehlung')
```

**3. Flushing Protocol Manager:**
```python
from datetime import date, datetime, timedelta

class FlushingProtocol(BaseModel):
    """Nährstoffreduktion vor Ernte"""
    
    plant_id: str
    substrate_type: Literal['hydro', 'coco', 'soil']
    current_ec: float = Field(ge=0, le=5)
    days_until_harvest: int = Field(ge=0, le=60)
    
    # Substrat-spezifische Flush-Dauer
    FLUSH_DURATIONS = {
        'hydro': {'min': 7, 'optimal': 10, 'max': 14},
        'coco': {'min': 10, 'optimal': 14, 'max': 21},
        'soil': {'min': 14, 'optimal': 21, 'max': 30}
    }
    
    def get_schedule(self) -> Dict:
        """Erstellt schrittweisen Flush-Plan"""
        
        duration_map = self.FLUSH_DURATIONS[self.substrate_type]
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
                target_ec = 0.0
            
            steps.append({
                'day': day,
                'days_to_harvest': self.days_until_harvest - day,
                'target_ec': round(target_ec, 2),
                'action': action,
                'dosage_percent': dosage_percent,
                'water_only': water_only,
                'measurement_required': day % 3 == 0,  # Alle 3 Tage messen
                'runoff_ec_target': f'< {target_ec + 0.5:.1f} mS'
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
IndicatorType = Literal['trichome', 'foliage', 'brix', 'size', 'color', 'days_since_flowering', 'aroma', 'texture']

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
    
    def _calculate_score(self, g_m2_day: float) -> str:
        """Score basierend auf Gram/m²/Tag"""
        if g_m2_day >= 1.5:
            return 'Excellent'
        elif g_m2_day >= 1.0:
            return 'Good'
        elif g_m2_day >= 0.7:
            return 'Average'
        else:
            return 'Below Average'
```

## 4. Abhängigkeiten

**Erforderliche Module:**
- REQ-001 (Stammdaten): Species für Harvest-Indicators
- REQ-003 (Phasen): Harvest-Phase, Flowering-Tracking
- REQ-004 (Düngung): Flushing-Protokoll
- REQ-002 (Standort): Area für Yield/m²-Berechnung

**Wird benötigt von:**
- REQ-008 (Post-Harvest): Batch-Übergabe zur Trocknung/Curing
- REQ-009 (Dashboard): Harvest-Kalender, Yield-Analytics
- REQ-010 (IPM): Karenzzeit-Validierung vor Ernte

**Externe Integrationen:**
- QR-Code-Generator API
- Computer Vision (optional) für Trichom-Analyse
- Refraktometer (Hardware) für Brix-Messung

## 5. Akzeptanzkriterien

### Definition of Done (DoD):

- [ ] **5+ Harvest-Indicator-Typen:** Trichome, Foliage, Brix, Days-Since-Flowering, Color
- [ ] **Automatisches Flushing:** 14 Tage vor Ernte basierend auf Reife-Observation
- [ ] **Batch-ID-Generierung:** Eindeutige IDs nach Schema PLANT_YYYYMMDD_SEQ
- [ ] **QR-Code-Integration:** Jeder Batch hat QR-Code mit Traceability
- [ ] **Erntegewicht-Tracking:** Nass + geschätztes Trockengewicht
- [ ] **Quality-Scoring:** Multi-Dimensionale Bewertung (Appearance, Aroma, etc.)
- [ ] **Photo-Dokumentation:** Before/After-Fotos für jeden Batch
- [ ] **Partial-Harvest-Support:** Top-Buds zuerst, Lower-Buds später
- [ ] **Yield-Analytics:** Gram/m²/Tag-Berechnung
- [ ] **Seed-to-Shelf-ID:** Vollständige Rückverfolgbarkeit
- [ ] **Trichom-Mikroskop-Guide:** Schritt-für-Schritt Anleitung
- [ ] **Brix-Kalibrierung:** Refraktometer-Setup-Guide
- [ ] **Dark-Period-Timer:** Optional 24-48h Dunkelphase vor Ernte
- [ ] **Harvest-Kalender:** Vorschau auf nächste Ernten (14 Tage)
- [ ] **Grade-Distribution:** Statistik über A+/A/B/C-Batches

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

---

**Hinweise für RAG-Integration:**
- Keywords: Ernte, Trichome, Reife, Flushing, Batch, QR-Code, Yield, Traceability
- Fachbegriffe: Calyx, Pistil, Terpen, CBN, THC, Brix, Chlorophyll, Seed-to-Shelf
- Verknüpfung: Zentral für REQ-004 (Flushing), REQ-008 (Post-Harvest), REQ-009 (Analytics)
- Pflanzenwissenschaft: Trichom-Entwicklung, Cannabinoid-Degradation, Chlorophyll-Abbau
