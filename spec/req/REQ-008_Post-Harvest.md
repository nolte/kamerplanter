# Spezifikation: REQ-008 - Post-Harvest

```yaml
ID: REQ-008
Titel: Post-Harvest: Veredelung, Fermentierung & Lagerreife
Kategorie: Post-Harvest
Fokus: Beides
Technologie: Python, Umweltsensorik, TimescaleDB (Zeitreihen)
Status: Entwurf
Version: 2.0 (Maximal Erweitert)
```

## 1. Business Case

**User Story:** "Als Gärtner möchte ich Trocknungs-, Fermentierungs- und Lagerungsprozesse überwachen und steuern, um Qualität, Aroma, Haltbarkeit und Lagerfähigkeit meiner Ernte zu maximieren."

**Beschreibung:**
Das System implementiert spezies-spezifische Post-Harvest-Protokolle für die Phase zwischen Ernte und Endverbrauch mit präziser Umgebungskontrolle:

**Post-Harvest-Prozesse:**

**1. Trocknung (Drying):**
- **Cannabis/Hopfen/Kräuter:**
  - **Slow-Dry-Methode:** 7-14 Tage bei 15-21°C, 45-55% RLF
  - **Ziel:** 60-65% Gewichtsverlust (von Nass zu Trocken)
  - **Snap-Test:** Zweige brechen aber splittern nicht
  - **Qualitätskriterien:** Langsame Trocknung = besseres Aroma
  
- **Chili/Paprika:**
  - **Lufttrocknung:** 2-4 Wochen bei Raumtemperatur
  - **Dörrgerät:** 50-60°C für 6-12h (schneller aber weniger Aroma)
  
- **Pilze:**
  - **Dehydrator:** 35-40°C bis cracker-dry
  - **Kritisch:** Über 40°C = Wirkstoffverlust
  
- **Zwiebeln/Knoblauch:**
  - **Schalenhärtung:** 2-3 Wochen bei 25-30°C, niedrige RLF
  - **UV-Exposition:** Fördert Schalenhärtung

**2. Curing (Fermentierung/Veredelung):**
- **Cannabis:**
  - **Jar-Curing:** 3-8 Wochen in verschlossenen Gläsern
  - **Burping-Schedule:** 
    - Woche 1-2: 2x täglich 15min lüften
    - Woche 3-4: 1x täglich 10min
    - Woche 5+: Wöchentlich 5min
  - **Ziel-RH im Jar:** 58-62% (Boveda-Packs)
  - **Prozesse:** Chlorophyll-Abbau, Terpen-Entwicklung
  
- **Sauerkraut/Kimchi:**
  - **Fermentation:** 3-6 Wochen bei 18-22°C
  - **Täglich Gasen ablassen**
  - **Salzlake:** 2-3% Salzgehalt
  
- **Tabak:**
  - **Fermentation in Ballen:** 6-12 Monate
  - **Temperatur-kontrolliert:** Nicht über 55°C

**3. Aging/Reifung:**
- **Kürbis/Squash:**
  - **Nachreife:** 2-3 Monate bei 10-15°C
  - **Verbessert:** Geschmack, Textur, Lagerfähigkeit
  
- **Tomaten (grün geerntet):**
  - **Ethylen-Management:** Mit reifen Äpfeln lagern
  - **Nachreife:** 1-3 Wochen bei 18-21°C
  
- **Wein/Käse (optional):**
  - **Langzeitreifung:** Monate bis Jahre
  - **Klima-kontrolliert:** Spezifische Temp/RLF

**4. Storage (Langzeitlagerung):**
- **Temperatur-Zonen:**
  - **Kühl (0-5°C):** Wurzelgemüse, Äpfel, Kohl
  - **Keller (10-15°C):** Kürbis, Zwiebeln, Kartoffeln
  - **Raumtemperatur (18-22°C):** Getrocknete Kräuter, Samen
  
- **Luftfeuchte-Kontrolle:**
  - **Hoch (80-95%):** Wurzelgemüse in Sand
  - **Mittel (60-70%):** Kürbis, Zwiebeln
  - **Niedrig (40-50%):** Getrocknete Produkte

**Kritische Parameter:**

**Temperatur:**
- **Zu hoch:** Schimmel, Degradation, Insekten
- **Zu niedrig:** Gefrierungsschäden, Geschmacksverlust

**Luftfeuchte:**
- **Zu hoch (>65%):** Schimmelgefahr (Botrytis, Aspergillus)
- **Zu niedrig (<40%):** Übertrocknung, Terpen-Verlust, Brüchigkeit

**Luftaustausch:**
- **Zu wenig:** CO2-Akkumulation, Schimmel
- **Zu viel:** Zu schnelle Trocknung, Aroma-Verlust

**Qualitäts-Monitoring:**
- **Gewichtsverlauf:** Tägliche/wöchentliche Messungen
- **Visuelle Inspektion:** Schimmel, Verfärbungen, Schädlinge
- **Geruchstest:** Aroma-Entwicklung, Schimmel-Erkennung
- **Haptik:** Trockenheit, Festigkeit

## 2. GraphDB-Modellierung

### Nodes:
- **`:StorageProtocol`** - Lagerungsvorschrift
  - Properties:
    - `protocol_id: str`
    - `protocol_type: Literal['drying', 'curing', 'aging', 'hardening', 'storage']`
    - `protocol_name: str`
    - `description: str`
    - `typical_duration_days: int`
    - `critical_for_quality: bool`

- **`:CuringPhase`** - Teil-Phase des Protokolls
  - Properties:
    - `phase_id: str`
    - `phase_name: str` (z.B. "early_cure", "burping", "final_cure")
    - `sequence_order: int`
    - `duration_days: int`
    - `action_required: str` (z.B. "Burp jars daily")
    - `action_frequency: str` (z.B. "twice_daily", "weekly")
    - `success_indicators: list[str]`

- **`:StorageCondition`** - Sollwerte für Umgebung
  - Properties:
    - `condition_id: str`
    - `temp_target_c: float`
    - `temp_tolerance_c: float` (±Abweichung)
    - `rh_target_percent: int`
    - `rh_tolerance_percent: int`
    - `air_exchange_per_hour: Optional[float]`
    - `light_exposure: Literal['none', 'minimal', 'indirect', 'direct']`
    - `critical_max_rh: int` (Schimmel-Schwelle)
    - `critical_min_rh: int` (Übertrocknung-Schwelle)

- **`:StorageLocation`** - Physischer Lagerort
  - Properties:
    - `location_id: str`
    - `location_name: str` (z.B. "Drying Room", "Curing Closet", "Root Cellar")
    - `location_type: Literal['room', 'closet', 'cellar', 'fridge', 'jar', 'container']`
    - `capacity_kg: Optional[float]`
    - `current_utilization_percent: float`
    - `has_active_climate_control: bool`
    - `sensor_ids: list[str]`

- **`:StorageObservation`** - Zustandsmessung
  - Properties:
    - `observation_id: str`
    - `timestamp: datetime`
    - `weight_g: Optional[float]`
    - `temperature_c: Optional[float]`
    - `rh_percent: Optional[float]`
    - `visual_condition: Literal['excellent', 'good', 'acceptable', 'concerning', 'critical']`
    - `aroma_quality: Literal['excellent', 'good', 'acceptable', 'off', 'moldy']`
    - `defects_observed: list[str]` (z.B. ["mold_spot", "over_dry"])
    - `photo_refs: list[str]`
    - `observer: str`
    - `notes: Optional[str]`

- **`:BurpingEvent`** - Jar-Lüftung (Cannabis-Curing)
  - Properties:
    - `event_id: str`
    - `burped_at: datetime`
    - `duration_minutes: int`
    - `jar_rh_before: Optional[int]`
    - `jar_rh_after: Optional[int]`
    - `condensation_observed: bool`
    - `aroma_notes: Optional[str]`

- **`:MoldAlert`** - Schimmel-Warnung
  - Properties:
    - `alert_id: str`
    - `triggered_at: datetime`
    - `severity: Literal['warning', 'critical']`
    - `trigger_reason: str` (z.B. "RH >65% for 6h")
    - `affected_location: str`
    - `action_taken: Optional[str]`
    - `resolved_at: Optional[datetime]`

- **`:DryingProgress`** - Trocknungs-Tracking
  - Properties:
    - `progress_id: str`
    - `start_weight_g: float`
    - `current_weight_g: float`
    - `target_weight_g: float`
    - `weight_loss_percent: float`
    - `dryness_progress_percent: float`
    - `snap_test_ready: bool`
    - `estimated_days_remaining: int`

### Edges:
```cypher
(:Species)-[:REQUIRES_POST_HARVEST]->(:StorageProtocol)
(:StorageProtocol)-[:HAS_PHASE {sequence: int}]->(:CuringPhase)
(:CuringPhase)-[:REQUIRES_CONDITIONS]->(:StorageCondition)
(:Batch)-[:UNDERGOING]->(:CuringPhase)
(:Batch)-[:STORED_IN]->(:StorageLocation)
(:StorageLocation)-[:MONITORED_BY]->(:StorageObservation)
(:Batch)-[:HAS_DRYING_PROGRESS]->(:DryingProgress)
(:Batch)-[:BURPING_EVENT]->(:BurpingEvent)
(:StorageLocation)-[:TRIGGERED_ALERT]->(:MoldAlert)
(:StorageObservation)-[:TRIGGERED]->(:MoldAlert)  // RH-basierte Alerts
```

### Cypher-Beispiellogik:

**Burping-Schedule basierend auf Cure-Dauer:**
```cypher
MATCH (batch:Batch {batch_id: $batch_id})-[:UNDERGOING]->(phase:CuringPhase)
WHERE phase.phase_name = 'jar_curing'

// Berechne Tage in Curing
WITH batch, phase,
     duration.between(batch.curing_started, datetime()).days AS days_in_cure

// Bestimme Burping-Frequenz
WITH batch, phase, days_in_cure,
     CASE
       WHEN days_in_cure <= 7 THEN {
         frequency: 'twice_daily',
         duration_min: 15,
         times: ['09:00', '21:00'],
         reason: 'Early cure - high moisture'
       }
       WHEN days_in_cure <= 14 THEN {
         frequency: 'daily',
         duration_min: 10,
         times: ['12:00'],
         reason: 'Mid cure - moisture stabilizing'
       }
       WHEN days_in_cure <= 21 THEN {
         frequency: 'every_2_days',
         duration_min: 10,
         times: ['12:00'],
         reason: 'Late cure - low moisture'
       }
       ELSE {
         frequency: 'weekly',
         duration_min: 5,
         times: ['12:00'],
         reason: 'Final cure - maintenance only'
       }
     END AS burping_schedule

// Hole letzte Burping-Events
OPTIONAL MATCH (batch)-[:BURPING_EVENT]->(last_burp:BurpingEvent)
WHERE last_burp.burped_at > datetime() - duration('P7D')

WITH batch, burping_schedule, days_in_cure,
     COLLECT(last_burp) AS recent_burps
ORDER BY last_burp.burped_at DESC

// Berechne nächstes Burping
WITH batch, burping_schedule, days_in_cure, recent_burps,
     CASE SIZE(recent_burps)
       WHEN 0 THEN datetime()  // Sofort wenn noch nie geburpt
       ELSE recent_burps[0].burped_at + duration({
         hours: CASE burping_schedule.frequency
           WHEN 'twice_daily' THEN 12
           WHEN 'daily' THEN 24
           WHEN 'every_2_days' THEN 48
           ELSE 168  // weekly
         END
       })
     END AS next_burping

RETURN {
  batch_id: batch.batch_id,
  days_in_cure: days_in_cure,
  burping_schedule: burping_schedule,
  last_burped: CASE SIZE(recent_burps) WHEN 0 THEN null ELSE recent_burps[0].burped_at END,
  next_burping: next_burping,
  overdue: next_burping < datetime(),
  notes: [
    'Prüfe auf Schimmel (weiß/grau = schlecht)',
    'Boveda 62% Pack ab Woche 2 empfohlen',
    'Ziel-RH im Jar: 58-62%'
  ]
} AS schedule
```

**Schimmel-Prävention mit RH-Monitoring:**
```cypher
MATCH (location:StorageLocation)-[:MONITORED_BY]->(obs:StorageObservation)
WHERE obs.timestamp > datetime() - duration('PT6H')

// Aggregiere letzte 6h Messungen
WITH location, COLLECT(obs) AS observations,
     AVG(obs.rh_percent) AS avg_rh_6h,
     MAX(obs.rh_percent) AS max_rh_6h,
     MIN(obs.temperature_c) AS min_temp_6h,
     MAX(obs.temperature_c) AS max_temp_6h

// Bestimme Schimmel-Risiko
WITH location, avg_rh_6h, max_rh_6h, min_temp_6h, max_temp_6h,
     CASE
       WHEN avg_rh_6h > 65 THEN 'CRITICAL'
       WHEN avg_rh_6h > 62 THEN 'WARNING'
       WHEN avg_rh_6h > 55 AND max_temp_6h > 22 THEN 'WARNING'
       ELSE 'OK'
     END AS risk_level

WHERE risk_level IN ['WARNING', 'CRITICAL']

// Prüfe ob Alert bereits existiert
OPTIONAL MATCH (location)-[:TRIGGERED_ALERT]->(existing:MoldAlert)
WHERE existing.resolved_at IS NULL

// Erstelle neuen Alert wenn nötig
WITH location, risk_level, avg_rh_6h, max_temp_6h, existing
WHERE existing IS NULL AND risk_level = 'CRITICAL'

CREATE (alert:MoldAlert {
  alert_id: randomUUID(),
  triggered_at: datetime(),
  severity: risk_level,
  trigger_reason: 'RH ' + toString(round(avg_rh_6h, 1)) + '% > 65% über 6h',
  affected_location: location.location_id,
  action_required: CASE risk_level
    WHEN 'CRITICAL' THEN 'SOFORT: Dehumidifier einschalten, Luftaustausch erhöhen, visuell auf Schimmel prüfen'
    ELSE 'Überwachen: RH senken auf <60%'
  END
})

CREATE (location)-[:TRIGGERED_ALERT]->(alert)

RETURN {
  location: location.location_name,
  risk_level: risk_level,
  avg_rh_6h: round(avg_rh_6h, 1),
  max_rh_6h: round(max_rh_6h, 1),
  temp_range: [round(min_temp_6h, 1), round(max_temp_6h, 1)],
  alert_created: true,
  recommendations: [
    'Öffne alle Belüftungen',
    'Stelle Dehumidifier auf',
    'Prüfe alle Batches visuell',
    'Reduziere Raum-Feuchtigkeit auf <55%'
  ]
} AS alert_info
```

**Trocknungs-Fortschritt mit Gewichts-Tracking:**
```cypher
MATCH (batch:Batch {batch_id: $batch_id})-[:HAS_DRYING_PROGRESS]->(progress:DryingProgress)

// Hole aktuelle und historische Gewichte
MATCH (batch)-[:STORED_IN]->(location:StorageLocation)
      -[:MONITORED_BY]->(obs:StorageObservation)
WHERE obs.weight_g IS NOT NULL
  AND obs.timestamp > datetime() - duration('P14D')

WITH batch, progress, 
     COLLECT({timestamp: obs.timestamp, weight: obs.weight_g}) AS weight_history
ORDER BY obs.timestamp DESC

// Berechne Fortschritt
WITH batch, progress, weight_history,
     weight_history[0].weight AS current_weight,
     progress.start_weight_g AS start_weight,
     progress.target_weight_g AS target_weight

WITH batch, progress, weight_history, current_weight, start_weight, target_weight,
     ((start_weight - current_weight) / (start_weight - target_weight) * 100) AS dryness_percent,
     ((start_weight - current_weight) / start_weight * 100) AS weight_loss_percent

// Update Progress
SET progress.current_weight_g = current_weight,
    progress.weight_loss_percent = weight_loss_percent,
    progress.dryness_progress_percent = dryness_percent

// Snap-Test Readiness (bei 70-80% Fortschritt)
WITH batch, progress, weight_history, dryness_percent, weight_loss_percent,
     dryness_percent >= 70 AS snap_test_ready

SET progress.snap_test_ready = snap_test_ready

// Schätze verbleibende Tage (basierend auf Verlaufskurve)
WITH batch, progress, weight_history, dryness_percent, weight_loss_percent, snap_test_ready,
     CASE
       WHEN dryness_percent >= 95 THEN 0
       WHEN dryness_percent >= 80 THEN 2
       WHEN dryness_percent >= 60 THEN 4
       WHEN dryness_percent >= 40 THEN 7
       ELSE 10
     END AS estimated_days_remaining

SET progress.estimated_days_remaining = estimated_days_remaining

RETURN {
  batch_id: batch.batch_id,
  start_weight_g: start_weight,
  current_weight_g: round(current_weight, 1),
  target_weight_g: target_weight,
  weight_loss_percent: round(weight_loss_percent, 1),
  dryness_progress_percent: round(dryness_percent, 1),
  snap_test_ready: snap_test_ready,
  estimated_days_remaining: estimated_days_remaining,
  ready_for_curing: dryness_percent >= 95,
  status: CASE
    WHEN dryness_percent >= 95 THEN 'READY - Start Jar Curing'
    WHEN dryness_percent >= 70 THEN 'APPROACHING - Test Snap daily'
    WHEN dryness_percent >= 40 THEN 'DRYING - On track'
    ELSE 'EARLY - Just started'
  END,
  weight_history: [w IN weight_history | {
    date: date(w.timestamp),
    weight_g: w.weight
  }]
} AS drying_status
```

**Storage-Inventar mit Haltbarkeits-Prognose:**
```cypher
MATCH (location:StorageLocation)<-[:STORED_IN]-(batch:Batch)

// Hole Storage-Protokoll
MATCH (batch)-[:DERIVED_FROM]->(:PlantInstance)-[:BELONGS_TO_SPECIES]->(species:Species)
      -[:REQUIRES_POST_HARVEST]->(protocol:StorageProtocol {protocol_type: 'storage'})

// Berechne Lagerzeit
WITH location, batch, species, protocol,
     duration.between(batch.stored_at, datetime()).days AS days_in_storage

// Hole aktuelle Conditions
OPTIONAL MATCH (location)-[:MONITORED_BY]->(latest_obs:StorageObservation)
WHERE latest_obs.timestamp > datetime() - duration('PT24H')

WITH location, batch, species, protocol, days_in_storage, latest_obs
ORDER BY latest_obs.timestamp DESC

WITH location, batch, species, protocol, days_in_storage,
     COLLECT(latest_obs)[0] AS current_condition

// Haltbarkeits-Schätzung (spezies-abhängig)
WITH location, batch, species, days_in_storage, current_condition,
     CASE species.scientific_name
       WHEN 'Cannabis sativa' THEN 365  // 1 Jahr bei korrekter Lagerung
       WHEN 'Allium cepa' THEN 180      // Zwiebeln 6 Monate
       WHEN 'Solanum tuberosum' THEN 270  // Kartoffeln 9 Monate
       ELSE 90
     END AS shelf_life_days

WITH location, batch, species, days_in_storage, current_condition, shelf_life_days,
     shelf_life_days - days_in_storage AS days_remaining,
     (toFloat(days_in_storage) / shelf_life_days * 100) AS shelf_life_used_percent

// Aggregiere pro Location
WITH location,
     COUNT(batch) AS total_batches,
     SUM(batch.actual_dry_weight_g) AS total_weight_g,
     AVG(days_remaining) AS avg_days_remaining,
     COLLECT({
       batch_id: batch.batch_id,
       species: species.common_names[0],
       weight_g: batch.actual_dry_weight_g,
       days_in_storage: days_in_storage,
       days_remaining: days_remaining,
       shelf_life_percent: round(shelf_life_used_percent, 1),
       condition: current_condition.visual_condition,
       quality_grade: batch.quality_grade
     }) AS batches

RETURN {
  location: location.location_name,
  capacity_kg: location.capacity_kg,
  current_stock_kg: round(total_weight_g / 1000, 2),
  utilization_percent: round((total_weight_g / 1000) / location.capacity_kg * 100, 1),
  total_batches: total_batches,
  average_days_remaining: round(avg_days_remaining, 0),
  batches: batches,
  alerts: [b IN batches WHERE b.days_remaining < 30 | 
    b.batch_id + ' läuft in ' + toString(b.days_remaining) + ' Tagen ab'
  ]
} AS inventory
ORDER BY inventory.location
```

## 3. Technische Umsetzung (Python)

### Logik-Anforderungen:

**1. Drying Protocol Manager:**
```python
from pydantic import BaseModel, Field, validator
from typing import Literal, Optional, List, Dict
from datetime import datetime, date, timedelta

class DryingProtocol(BaseModel):
    """Trocknungs-Management mit Fortschritts-Tracking"""
    
    batch_id: str
    species_type: Literal['flower', 'herb', 'root', 'fruit', 'mushroom']
    initial_weight_g: float = Field(gt=0)
    current_weight_g: float = Field(gt=0)
    target_moisture_percent: float = Field(default=10, ge=5, le=15)
    drying_method: Literal['hang_dry', 'rack_dry', 'dehydrator', 'air_cure']
    
    @validator('current_weight_g')
    def validate_weight_reduction(cls, v, values):
        initial = values.get('initial_weight_g', 0)
        if v > initial:
            raise ValueError("Current weight kann nicht größer als initial weight sein")
        return v
    
    def calculate_dryness_progress(self) -> Dict:
        """
        Berechnet Trocknungs-Fortschritt
        
        Returns:
            Detaillierter Progress-Report
        """
        weight_loss_pct = ((self.initial_weight_g - self.current_weight_g) / 
                          self.initial_weight_g * 100)
        
        # Ziel: 75-80% Gewichtsverlust für ~10% Restfeuchte
        target_loss = 100 - self.target_moisture_percent
        progress = min(100, (weight_loss_pct / target_loss) * 100)
        
        # Snap-Test-Bereitschaft (Zweige brechen aber splittern nicht)
        snap_test_ready = progress >= 70
        
        # Übertrocknung-Warnung
        over_dried = weight_loss_pct > 85
        
        return {
            'weight_loss_percent': round(weight_loss_pct, 1),
            'dryness_progress_percent': round(progress, 1),
            'ready_for_curing': progress >= 95,
            'snap_test_ready': snap_test_ready,
            'over_dried': over_dried,
            'current_weight_g': self.current_weight_g,
            'estimated_final_weight_g': round(self.initial_weight_g * (self.target_moisture_percent / 100), 1),
            'estimated_days_remaining': self._estimate_remaining_days(progress),
            'next_action': self._get_next_action(progress, over_dried)
        }
    
    def _estimate_remaining_days(self, current_progress: float) -> int:
        """Schätzt verbleibende Trocknungs-Tage"""
        
        # Basis-Schätzung nach Methode
        base_days = {
            'hang_dry': 10,    # Langsam, beste Qualität
            'rack_dry': 8,
            'dehydrator': 1,   # Schnell, weniger Aroma
            'air_cure': 14     # Sehr langsam
        }
        
        total_days = base_days.get(self.drying_method, 10)
        
        if current_progress >= 95:
            return 0
        elif current_progress >= 70:
            return 2
        elif current_progress >= 50:
            return int(total_days * 0.3)
        else:
            return int(total_days * 0.7)
    
    def _get_next_action(self, progress: float, over_dried: bool) -> str:
        """Empfiehlt nächste Schritte"""
        
        if over_dried:
            return "WARNUNG: Übertrocknet - Sofort in Jars mit Boveda-Pack (62%)"
        elif progress >= 95:
            return "Bereit für Jar-Curing - Jetzt in luftdichte Gläser umfüllen"
        elif progress >= 70:
            return "Snap-Test täglich durchführen - Zweige sollten brechen aber nicht splittern"
        elif progress >= 40:
            return "Trocknung läuft normal - Temperatur/RLF überwachen"
        else:
            return "Frühe Phase - Sicherstellen dass Luftzirkulation gut ist"
    
    def perform_snap_test(self, snaps_cleanly: bool, splinters: bool) -> Dict:
        """
        Interpretiert Snap-Test-Ergebnis
        
        Args:
            snaps_cleanly: Zweig bricht sauber durch
            splinters: Zweig splittert
        
        Returns:
            Test-Interpretation
        """
        if snaps_cleanly and not splinters:
            return {
                'result': 'OPTIMAL',
                'recommendation': 'Perfekt getrocknet - Bereit für Curing',
                'moisture_estimate': '10-12%',
                'action': 'In Jars umfüllen und mit Curing beginnen'
            }
        elif snaps_cleanly and splinters:
            return {
                'result': 'OVERDRIED',
                'recommendation': 'Zu trocken - Rehydrierung nötig',
                'moisture_estimate': '<8%',
                'action': 'Boveda 62% Pack für 24h in Jar, dann neu testen'
            }
        else:  # Biegt sich nur
            return {
                'result': 'UNDERDRIED',
                'recommendation': 'Noch zu feucht - Weiter trocknen',
                'moisture_estimate': '>15%',
                'action': 'Noch 2-3 Tage hängen lassen, dann neu testen'
            }

class SpeciesSpecificDrying:
    """Spezies-spezifische Trocknungs-Parameter"""
    
    DRYING_SPECS = {
        'Cannabis sativa': {
            'method': 'hang_dry',
            'temp_range': (15, 21),
            'rh_range': (45, 55),
            'duration_days': (7, 14),
            'target_moisture': 10,
            'critical_notes': [
                'Langsame Trocknung = besseres Aroma',
                'Nie über 25°C (Terpen-Verlust)',
                'Dunkelheit (UV degradiert THC)',
                'Luftzirkulation ohne direkten Wind'
            ]
        },
        'Capsicum annuum': {  # Chili
            'method': 'air_cure',
            'temp_range': (20, 30),
            'rh_range': (30, 50),
            'duration_days': (14, 28),
            'target_moisture': 8,
            'critical_notes': [
                'String-Method: An Faden aufhängen',
                'Gute Luftzirkulation wichtig',
                'Dehydrator OK aber weniger Aroma'
            ]
        },
        'Allium cepa': {  # Zwiebel
            'method': 'air_cure',
            'temp_range': (25, 30),
            'rh_range': (20, 40),
            'duration_days': (14, 21),
            'target_moisture': 5,
            'critical_notes': [
                'Schalenhärtung Phase',
                'UV-Exposition fördert Härtung',
                'Laub muss komplett trocken sein'
            ]
        },
        'Agaricus bisporus': {  # Pilze
            'method': 'dehydrator',
            'temp_range': (35, 40),
            'rh_range': (10, 20),
            'duration_days': (0.25, 0.5),  # 6-12h
            'target_moisture': 5,
            'critical_notes': [
                'NICHT über 40°C (Wirkstoffverlust)',
                'Cracker-dry = vollständig trocken',
                'In luftdichten Behältern mit Silica lagern'
            ]
        }
    }
    
    @classmethod
    def get_specs(cls, scientific_name: str) -> Dict:
        """Holt spezies-spezifische Trocknungs-Specs"""
        return cls.DRYING_SPECS.get(
            scientific_name,
            {  # Default
                'method': 'air_cure',
                'temp_range': (18, 24),
                'rh_range': (40, 60),
                'duration_days': (7, 14),
                'target_moisture': 10,
                'critical_notes': ['Allgemeine Trocknung']
            }
        )
```

**2. Jar Curing Manager (Cannabis-spezifisch):**
```python
from datetime import datetime, timedelta

class JarCuringManager(BaseModel):
    """Verwaltet Cannabis Jar-Curing mit Burping"""
    
    batch_id: str
    jar_count: int = Field(ge=1, le=100)
    grams_per_jar: float = Field(gt=0, le=500)
    curing_started_at: datetime
    target_rh_percent: int = Field(default=62, ge=55, le=65)
    
    def get_burping_schedule(self) -> Dict:
        """Generiert dynamischen Burping-Schedule"""
        
        days_in_cure = (datetime.now() - self.curing_started_at).days
        
        if days_in_cure <= 7:
            schedule = {
                'frequency': 'twice_daily',
                'duration_minutes': 15,
                'times': ['09:00', '21:00'],
                'reason': 'Woche 1 - Hohe Restfeuchte',
                'rh_target': '58-62%',
                'condensation_check': True
            }
        elif days_in_cure <= 14:
            schedule = {
                'frequency': 'daily',
                'duration_minutes': 10,
                'times': ['12:00'],
                'reason': 'Woche 2 - Feuchte stabilisiert sich',
                'rh_target': '58-62%',
                'condensation_check': True
            }
        elif days_in_cure <= 21:
            schedule = {
                'frequency': 'every_2_days',
                'duration_minutes': 10,
                'times': ['12:00'],
                'reason': 'Woche 3 - Fast fertig',
                'rh_target': '58-62%',
                'condensation_check': False
            }
        else:
            schedule = {
                'frequency': 'weekly',
                'duration_minutes': 5,
                'times': ['12:00'],
                'reason': 'Final Cure - Nur Wartung',
                'rh_target': '58-62%',
                'condensation_check': False
            }
        
        return {
            'days_in_cure': days_in_cure,
            'current_schedule': schedule,
            'next_burping': self._calculate_next_burping(days_in_cure),
            'total_cure_time': self._get_cure_duration_recommendation(),
            'quality_indicators': self._get_quality_indicators(days_in_cure),
            'notes': [
                'Boveda 62% Packs ab Woche 2 empfohlen',
                'Schimmel-Check bei jedem Burping (weiß/grau = schlecht)',
                'Aroma entwickelt sich über 3-8 Wochen',
                'Chlorophyll-Abbau = weniger "grüner" Geschmack'
            ]
        }
    
    def _calculate_next_burping(self, days_in_cure: int) -> datetime:
        """Berechnet nächsten Burping-Zeitpunkt"""
        
        hours_interval = {
            range(0, 8): 12,      # Twice daily
            range(8, 15): 24,     # Daily
            range(15, 22): 48,    # Every 2 days
            range(22, 365): 168   # Weekly
        }
        
        for day_range, hours in hours_interval.items():
            if days_in_cure in day_range:
                return datetime.now() + timedelta(hours=hours)
        
        return datetime.now() + timedelta(hours=168)
    
    def _get_cure_duration_recommendation(self) -> Dict:
        """Empfiehlt Cure-Dauer basierend auf Qualitätsziel"""
        
        return {
            'minimum': {
                'weeks': 2,
                'quality': 'Acceptable - Grundlegende Chlorophyll-Reduktion'
            },
            'good': {
                'weeks': 4,
                'quality': 'Good - Deutlich verbesserter Geschmack'
            },
            'optimal': {
                'weeks': 6,
                'quality': 'Optimal - Vollständig entwickeltes Terpen-Profil'
            },
            'premium': {
                'weeks': 8,
                'quality': 'Premium - Peak Aroma, maximale Smoothness'
            }
        }
    
    def _get_quality_indicators(self, days_in_cure: int) -> List[str]:
        """Gibt erwartete Qualitäts-Veränderungen an"""
        
        indicators = []
        
        if days_in_cure >= 3:
            indicators.append("✓ Erste Aroma-Veränderungen erkennbar")
        if days_in_cure >= 7:
            indicators.append("✓ Chlorophyll-Abbau begonnen (weniger grün)")
        if days_in_cure >= 14:
            indicators.append("✓ Harshness reduziert, smootherer Rauch")
        if days_in_cure >= 21:
            indicators.append("✓ Terpen-Profil voll entwickelt")
        if days_in_cure >= 42:
            indicators.append("✓ Peak-Qualität erreicht")
        
        return indicators
    
    def assess_jar_rh(self, measured_rh: int) -> Dict:
        """Bewertet Jar-Luftfeuchte und gibt Empfehlungen"""
        
        if measured_rh > 65:
            return {
                'status': 'TOO_HIGH',
                'risk': 'SCHIMMEL-GEFAHR',
                'action': 'SOFORT burpen und länger offen lassen (30min+)',
                'severity': 'critical',
                'explanation': 'RH >65% = hohe Schimmel-Wahrscheinlichkeit'
            }
        elif measured_rh > 62:
            return {
                'status': 'SLIGHTLY_HIGH',
                'risk': 'Erhöhtes Schimmel-Risiko',
                'action': 'Häufiger burpen (täglich statt alle 2 Tage)',
                'severity': 'warning'
            }
        elif 58 <= measured_rh <= 62:
            return {
                'status': 'OPTIMAL',
                'risk': 'Kein Risiko',
                'action': 'Weiter wie bisher',
                'severity': 'ok',
                'explanation': 'Perfekter Cure-Bereich'
            }
        elif 55 <= measured_rh < 58:
            return {
                'status': 'SLIGHTLY_LOW',
                'risk': 'Leichte Übertrocknung',
                'action': 'Boveda 62% Pack hinzufügen',
                'severity': 'info'
            }
        else:  # <55
            return {
                'status': 'TOO_LOW',
                'risk': 'Terpen-Verlust, zu trocken',
                'action': 'Boveda 62% Pack DRINGEND + seltener burpen',
                'severity': 'warning',
                'explanation': 'Material wird brüchig, Aroma-Verlust'
            }
```

**3. Mold Prevention Monitor:**
```python
from typing import List

class MoldPreventionMonitor:
    """Schimmel-Früherkennung und Prävention"""
    
    # Kritische Schwellenwerte
    CRITICAL_RH = 65
    WARNING_RH = 62
    SAFE_RH = 55
    
    # Temperatur-RH Kombinations-Risiko
    HIGH_RISK_COMBOS = [
        {'temp_min': 20, 'temp_max': 25, 'rh_min': 60},
        {'temp_min': 15, 'temp_max': 20, 'rh_min': 65},
    ]
    
    @classmethod
    def assess_mold_risk(
        cls,
        temp_c: float,
        rh_percent: float,
        air_exchange_per_hour: float,
        duration_hours: float = 1.0
    ) -> Dict:
        """
        Bewertet Schimmel-Risiko basierend auf Umgebungsbedingungen
        
        Returns:
            Risiko-Assessment mit Empfehlungen
        """
        
        risk_factors = []
        risk_score = 0
        
        # 1. RH-basiertes Risiko
        if rh_percent > cls.CRITICAL_RH:
            risk_factors.append(f"RH {rh_percent}% über kritischem Schwellenwert ({cls.CRITICAL_RH}%)")
            risk_score += 50
        elif rh_percent > cls.WARNING_RH:
            risk_factors.append(f"RH {rh_percent}% im Warn-Bereich")
            risk_score += 25
        
        # 2. Temp-RH Kombination
        for combo in cls.HIGH_RISK_COMBOS:
            if (combo['temp_min'] <= temp_c <= combo['temp_max'] and 
                rh_percent >= combo['rh_min']):
                risk_factors.append(
                    f"Kritische Temp-RH Kombination: {temp_c}°C + {rh_percent}%"
                )
                risk_score += 30
        
        # 3. Luftaustausch
        if air_exchange_per_hour < 1:
            risk_factors.append("Unzureichender Luftaustausch (<1x/h)")
            risk_score += 20
        
        # 4. Dauer der Exposition
        if duration_hours > 6 and rh_percent > cls.WARNING_RH:
            risk_factors.append(f"Erhöhte RH über {duration_hours}h")
            risk_score += 15
        
        # Bestimme Risiko-Level
        if risk_score >= 70:
            level = 'CRITICAL'
            color = 'red'
            actions = [
                'SOFORTIGE MASSNAHMEN erforderlich!',
                '1. Dehumidifier einschalten',
                '2. Luftaustausch maximieren',
                '3. Alle Batches visuell auf Schimmel prüfen',
                '4. Temperatur senken wenn möglich',
                '5. Betroffene Bereiche isolieren'
            ]
        elif risk_score >= 40:
            level = 'WARNING'
            color = 'yellow'
            actions = [
                '1. RH auf <60% senken',
                '2. Luftzirkulation erhöhen',
                '3. Täglich visuell kontrollieren',
                '4. Erwäge Dehumidifier'
            ]
        elif risk_score >= 20:
            level = 'ATTENTION'
            color = 'orange'
            actions = [
                '1. RH überwachen',
                '2. Bereitmachen für Intervention'
            ]
        else:
            level = 'OK'
            color = 'green'
            actions = ['Bedingungen stabil - Weiter überwachen']
        
        return {
            'risk_level': level,
            'risk_score': risk_score,
            'color': color,
            'risk_factors': risk_factors,
            'actions': actions,
            'current_conditions': {
                'temperature_c': temp_c,
                'rh_percent': rh_percent,
                'air_exchange_h': air_exchange_per_hour,
                'duration_hours': duration_hours
            },
            'safe_targets': {
                'temp_c': '<20°C ideal',
                'rh_percent': f'<{cls.SAFE_RH}%',
                'air_exchange': '>2x/h'
            }
        }
    
    @staticmethod
    def identify_mold_type(visual_description: str, color: str, texture: str) -> Dict:
        """
        Hilft bei Identifikation von Schimmeltypen
        
        (DISCLAIMER: Nur informativ, kein Ersatz für Experten)
        """
        
        mold_types = {
            'botrytis': {
                'names': ['Botrytis', 'Grauschimmel', 'Bud Rot'],
                'appearance': 'Grau/braun, flauschig',
                'danger': 'CRITICAL',
                'action': 'Gesamte Blüte entfernen + 5cm Umkreis',
                'prevention': 'RH <50% in Blüte, gute Luftzirkulation'
            },
            'powdery_mildew': {
                'names': ['Echter Mehltau', 'Powdery Mildew'],
                'appearance': 'Weiß, pudrig, auf Blattoberfläche',
                'danger': 'HIGH',
                'action': 'Betroffene Blätter entfernen, Fungizid erwägen',
                'prevention': 'RH <60%, Luftbewegung'
            },
            'aspergillus': {
                'names': ['Aspergillus', 'Schwarzschimmel'],
                'appearance': 'Schwarz/dunkelgrün, körnig',
                'danger': 'CRITICAL',
                'action': 'KOMPLETTE Entsorgung - gesundheitsgefährlich!',
                'prevention': 'Strikte RH-Kontrolle <55%'
            },
            'penicillium': {
                'names': ['Penicillium', 'Blauschimmel'],
                'appearance': 'Blau/grün, flauschig',
                'danger': 'HIGH',
                'action': 'Batch isolieren, betroffene Teile entfernen',
                'prevention': 'Keine Beschädigungen, saubere Handhabung'
            }
        }
        
        # Einfache Keyword-Matching (in Produktion: ML-basiert)
        color_lower = color.lower()
        
        if 'grau' in color_lower or 'gray' in color_lower:
            identified = mold_types['botrytis']
        elif 'weiß' in color_lower or 'white' in color_lower:
            identified = mold_types['powdery_mildew']
        elif 'schwarz' in color_lower or 'black' in color_lower:
            identified = mold_types['aspergillus']
        elif 'blau' in color_lower or 'grün' in color_lower:
            identified = mold_types['penicillium']
        else:
            identified = {
                'names': ['Unbekannt'],
                'appearance': visual_description,
                'danger': 'UNKNOWN',
                'action': 'Im Zweifelsfall: Komplette Entsorgung',
                'prevention': 'Strikte Hygiene'
            }
        
        return {
            'identified_as': identified['names'][0],
            'alternative_names': identified['names'],
            'danger_level': identified['danger'],
            'immediate_action': identified['action'],
            'prevention': identified['prevention'],
            'health_warning': 'WARNUNG: Einige Schimmelpilze sind gesundheitsgefährlich. Bei Unsicherheit entsorgen!'
        }
```

**4. Storage Location Manager:**
```python
class StorageLocationManager(BaseModel):
    """Verwaltet Lagerorte und Inventar"""
    
    location_id: str
    location_name: str
    location_type: Literal['room', 'closet', 'cellar', 'fridge', 'jar', 'container']
    capacity_kg: float = Field(gt=0, le=1000)
    has_climate_control: bool = False
    
    def calculate_utilization(self, current_stock_kg: float) -> Dict:
        """Berechnet Lagerort-Auslastung"""
        
        utilization_pct = (current_stock_kg / self.capacity_kg) * 100
        
        if utilization_pct > 90:
            status = 'CRITICAL_FULL'
            recommendation = 'Sofort alternative Lagerung suchen'
        elif utilization_pct > 75:
            status = 'HIGH'
            recommendation = 'Platz wird knapp - Verbrauch erhöhen oder erweitern'
        elif utilization_pct > 50:
            status = 'MEDIUM'
            recommendation = 'Normale Auslastung'
        else:
            status = 'LOW'
            recommendation = 'Viel freie Kapazität'
        
        return {
            'capacity_kg': self.capacity_kg,
            'current_stock_kg': current_stock_kg,
            'available_kg': self.capacity_kg - current_stock_kg,
            'utilization_percent': round(utilization_pct, 1),
            'status': status,
            'recommendation': recommendation
        }
    
    def get_ideal_conditions(self, stored_species: List[str]) -> Dict:
        """Gibt ideale Lagerbedingungen basierend auf gespeicherten Spezies"""
        
        # Spezies-spezifische Anforderungen
        species_requirements = {
            'Cannabis sativa': {'temp': (15, 18), 'rh': (58, 62), 'light': 'none'},
            'Allium cepa': {'temp': (10, 15), 'rh': (60, 70), 'light': 'minimal'},
            'Solanum tuberosum': {'temp': (7, 10), 'rh': (85, 90), 'light': 'none'},
            'Cucurbita maxima': {'temp': (10, 15), 'rh': (60, 70), 'light': 'minimal'}
        }
        
        if not stored_species:
            return {'message': 'Keine Spezies im Lager'}
        
        # Finde Überschneidung der Anforderungen
        temp_ranges = [species_requirements.get(sp, {'temp': (15, 20)})['temp'] 
                      for sp in stored_species]
        rh_ranges = [species_requirements.get(sp, {'rh': (50, 60)})['rh'] 
                    for sp in stored_species]
        
        optimal_temp = (
            max(t[0] for t in temp_ranges),
            min(t[1] for t in temp_ranges)
        )
        
        optimal_rh = (
            max(r[0] for r in rh_ranges),
            min(r[1] for r in rh_ranges)
        )
        
        return {
            'location': self.location_name,
            'stored_species': stored_species,
            'optimal_temperature_c': optimal_temp,
            'optimal_rh_percent': optimal_rh,
            'light_exposure': 'Dunkel (alle Spezies)',
            'air_exchange': '2-4x/Tag öffnen für Frischluft',
            'notes': self._get_storage_notes(stored_species)
        }
    
    def _get_storage_notes(self, species: List[str]) -> List[str]:
        """Spezielle Lagerhinweise"""
        
        notes = []
        
        if 'Cannabis sativa' in species:
            notes.append("Cannabis: In luftdichten Jars mit Boveda-Packs")
        if 'Solanum tuberosum' in species:
            notes.append("Kartoffeln: KOMPLETT dunkel (sonst Solanin-Bildung)")
        if 'Allium cepa' in species:
            notes.append("Zwiebeln: Gute Luftzirkulation, nicht mit Kartoffeln lagern")
        
        return notes
```

### Datenvalidierung (Type Hinting):
```python
from typing import Literal, Optional, List
from pydantic import BaseModel, Field, validator
from datetime import datetime, date

ProtocolType = Literal['drying', 'curing', 'aging', 'hardening', 'storage']
DryingMethod = Literal['hang_dry', 'rack_dry', 'dehydrator', 'air_cure']
VisualCondition = Literal['excellent', 'good', 'acceptable', 'concerning', 'critical']
AromaQuality = Literal['excellent', 'good', 'acceptable', 'off', 'moldy']

class StorageObservation(BaseModel):
    """Zustandserfassung während Lagerung"""
    
    batch_id: str
    observed_at: datetime
    observer: str
    
    weight_g: Optional[float] = Field(None, gt=0)
    temperature_c: Optional[float] = Field(None, ge=-10, le=50)
    rh_percent: Optional[int] = Field(None, ge=0, le=100)
    
    visual_condition: VisualCondition
    aroma_quality: AromaQuality
    
    defects_observed: List[str] = Field(default_factory=list)
    photo_refs: List[str] = Field(default_factory=list)
    notes: Optional[str] = Field(None, max_length=1000)
    
    @validator('defects_observed')
    def validate_critical_defects(cls, v, values):
        critical_defects = ['mold', 'mold_spot', 'moldy']
        
        if any(defect in v for defect in critical_defects):
            if values.get('visual_condition') != 'critical':
                raise ValueError("Schimmel erfordert visual_condition='critical'")
        
        return v

class BurpingEvent(BaseModel):
    """Jar-Lüftungs-Ereignis"""
    
    batch_id: str
    burped_at: datetime
    duration_minutes: int = Field(ge=1, le=60)
    jar_rh_before: Optional[int] = Field(None, ge=0, le=100)
    jar_rh_after: Optional[int] = Field(None, ge=0, le=100)
    condensation_observed: bool = False
    aroma_notes: Optional[str] = None
    
    @validator('jar_rh_after')
    def validate_rh_reduction(cls, v, values):
        rh_before = values.get('jar_rh_before')
        if rh_before and v:
            if v > rh_before:
                raise ValueError("RH nach Burping sollte nicht höher sein als vorher")
        return v
```

## 4. Abhängigkeiten

**Erforderliche Module:**
- REQ-007 (Ernte): Batch-Übergabe
- REQ-005 (Sensorik): Temperatur/RLF-Monitoring
- REQ-001 (Stammdaten): Spezies-spezifische Protokolle

**Wird benötigt von:**
- REQ-009 (Dashboard): Storage-Inventar-Widget
- Externes System: Vertriebs-/Verbrauchs-Tracking

**Hardware-Integrationen:**
- Hygrometer (digital, mit Logging)
- Thermometer
- Boveda-Packs (62% RH)
- Dehumidifier (optional)

**Python-Bibliotheken:**
- `timescaledb` oder `influxdb` - Zeitreihen für Gewichts-Tracking

## 5. Akzeptanzkriterien

### Definition of Done (DoD):

- [ ] **5+ Post-Harvest-Protokolle:** Cannabis, Zwiebel, Tomate, Kräuter, Pilze
- [ ] **Gewichts-Tracking:** Täglich in ersten 7 Tagen, dann wöchentlich
- [ ] **Snap-Test-Assistent:** Interpretation von Test-Ergebnissen
- [ ] **Burping-Timer:** Push-Notifications für Jar-Curing
- [ ] **Schimmel-Alert:** Automatische Warnung bei RH >65% für >6h
- [ ] **Lager-Inventar:** Echtzeit-Bestand mit Haltbarkeits-Prognose
- [ ] **Boveda-Pack-Empfehlung:** Auto-Vorschlag bei RH <58%
- [ ] **Jar-ID-System:** QR-Codes für einzelne Gläser
- [ ] **Dryness-Progress-Tracking:** Fortschrittsbalken mit Schätzung
- [ ] **Spezies-spezifische Guides:** Step-by-Step für jede Art
- [ ] **Mold-Type-Identification:** Hilfe bei Schimmel-Erkennung
- [ ] **Storage-Condition-Optimizer:** Ideale Bedingungen für Multi-Species
- [ ] **Curing-Quality-Timeline:** Was passiert in Woche 1, 2, 3, etc.
- [ ] **Emergency-Protocols:** Schimmel-Fund, Übertrocknung, etc.
- [ ] **Photo-Comparison:** Before/After während Cure

### Testszenarien:

**Szenario 1: Cannabis Slow-Dry mit Fortschritts-Tracking**
```
GIVEN: Batch mit 450g Nassgewicht
      Ziel: 10% Restfeuchte (112g Trockengewicht)
      Tag 0: 450g
      Tag 3: 320g (29% Verlust)
      Tag 7: 180g (60% Verlust)
WHEN: Fortschritt wird berechnet
THEN:
  - dryness_progress_percent = 73%
  - snap_test_ready = true
  - estimated_days_remaining = 2
  - next_action = "Snap-Test täglich durchführen"
```

**Szenario 2: Burping-Schedule (Jar-Curing)**
```
GIVEN: Batch in Jar-Curing seit 5 Tagen
WHEN: get_burping_schedule() aufgerufen
THEN:
  - frequency = 'twice_daily'
  - duration_minutes = 15
  - times = ['09:00', '21:00']
  - notes = "Boveda 62% Packs ab Woche 2 empfohlen"
```

**Szenario 3: Schimmel-Alert bei kritischer RH**
```
GIVEN: Drying Room mit:
      RH = 68% (letzte 6 Stunden durchschnittlich)
      Temp = 19°C
WHEN: Stündlicher Health-Check läuft
THEN:
  - MoldAlert erstellt
  - severity = 'CRITICAL'
  - trigger_reason = "RH 68% > 65% über 6h"
  - action_required = "SOFORT: Dehumidifier einschalten..."
  - Push-Notification an User
```

**Szenario 4: Jar-RH Assessment**
```
GIVEN: Jar-Hygrometer zeigt 72% RH
WHEN: assess_jar_rh(72) aufgerufen
THEN:
  - status = 'TOO_HIGH'
  - risk = 'SCHIMMEL-GEFAHR'
  - action = 'SOFORT burpen und länger offen lassen (30min+)'
  - severity = 'critical'
```

**Szenario 5: Snap-Test-Interpretation**
```
GIVEN: Zweig wird getestet
      snaps_cleanly = True
      splinters = True (splittert)
WHEN: perform_snap_test(True, True)
THEN:
  - result = 'OVERDRIED'
  - moisture_estimate = '<8%'
  - action = 'Boveda 62% Pack für 24h in Jar'
```

**Szenario 6: Multi-Species Storage Optimizer**
```
GIVEN: Root Cellar mit:
      - Kartoffeln (ideal: 7-10°C, 85-90% RH)
      - Zwiebeln (ideal: 10-15°C, 60-70% RH)
WHEN: get_ideal_conditions(['Solanum tuberosum', 'Allium cepa'])
THEN:
  - optimal_temperature_c = (10, 10)  # Überschneidung
  - optimal_rh_percent = (85, 70)     # Konflikt!
  - notes = "Zwiebeln und Kartoffeln NICHT zusammen lagern"
```

**Szenario 7: Haltbarkeits-Prognose**
```
GIVEN: Cannabis-Batch in Storage seit 120 Tagen
      Shelf-life: 365 Tage bei korrekter Lagerung
WHEN: Storage-Inventar-Query läuft
THEN:
  - days_remaining = 245
  - shelf_life_used_percent = 33%
  - alert = None (noch > 30 Tage)
```

---

**Hinweise für RAG-Integration:**
- Keywords: Trocknung, Curing, Burping, Fermentierung, Schimmel, Lagerung, Snap-Test
- Fachbegriffe: Chlorophyll-Abbau, Terpen-Entwicklung, Botrytis, Aspergillus, Boveda, Dehumidifier
- Verknüpfung: Direkt nach REQ-007 (Ernte), vor Endverbrauch/Vertrieb
- Pflanzenwissenschaft: Nachreife, Ethylen-Management, Schalenhärtung, Fermentation
