# Spezifikation: REQ-005 - Hybrid-Sensorik

```yaml
ID: REQ-005
Titel: Hybrid-Sensorik & Home Assistant Integration
Kategorie: Monitoring
Fokus: Beides
Technologie: Python, Home Assistant API, MQTT, TimescaleDB
Status: Entwurf
Version: 2.2 (U/P-Findings integriert)
```

## 1. Business Case

**User Story:** "Als Gärtner möchte ich Klimadaten entweder automatisch per Smart-Home empfangen oder manuell eingeben, damit das System auch ohne teure Sensorik voll funktionsfähig bleibt und ich flexibel zwischen verschiedenen Monitoring-Levels wählen kann."

**Beschreibung:**
Das System implementiert einen Hybrid-Ansatz für Datenerfassung mit nahtloser Degradation:

**Drei Betriebsmodi:**
- **Vollautomatisch (Auto-Mode):** Home Assistant liefert Echtzeit-Daten via MQTT/REST API
- **Semi-Automatisch:** Kritische Parameter automatisch, optionale Werte manuell
- **Manuell (Manual-Mode):** Komplette Funktionalität durch periodische Nutzer-Eingaben

**Überwachte Parameter:**

**Klima-Monitoring:**
- Temperatur (°C) - Lufttemperatur und Blatttemperatur-Differenz
- Blatttemperatur (°C) - Infrarot-Messung für Leaf-VPD (Leaf-VPD = f(leaf_temp, RH) ist präziser als Air-VPD; Blätter sind typisch 1-3°C kühler als Luft durch Transpiration, abhängig von Transpirationsrate, Lichtintensität und Luftbewegung). Ohne IR-Sensor: konfigurierbarer Offset `leaf_temp_offset_c` pro Lichttyp (LED: -1°C, HPS: -3°C, Sonnenlicht: -2°C, Default: -2°C)
- Luftfeuchte (%) - Relative Luftfeuchtigkeit
- VPD (kPa) - Vapor Pressure Deficit (berechnet oder gemessen)
- CO2-Konzentration (ppm) - Photosynthese-Optimierung
- Luftdruck (hPa) - Wettervorhersage
- Luftbewegung (m/s) - Ventilation-Monitoring

**Substrat-Monitoring:**
- Bodenfeuchte (%) - Tensiometer oder Kapazitive Sensoren
- Substrat-Temperatur (°C) - Wurzelzonen-Überwachung
- EC (mS/cm) - Elektrische Leitfähigkeit
- pH-Wert - Nährstoff-Verfügbarkeit

**Licht-Monitoring:**
- PPFD (μmol/m²/s) - Photosynthetic Photon Flux Density
- DLI (mol/m²/d) - Daily Light Integral (akkumuliert)
- Spektrum-Analyse - Rot/Blau/Far-Red-Verhältnis (R:FR-Ratio steuert Phytochrom-Gleichgewicht und damit Streckungswachstum; relevant für REQ-018 `target_light_spectrum`)
- Fotoperiode - Tatsächliche Beleuchtungsdauer

**Hydro-Systeme:**
- Reservoir-Füllstand (L oder %)
- Wassertemperatur (°C)
- Durchflussrate (L/h)
- TDS (ppm) - Total Dissolved Solids
- Gelöster Sauerstoff (mg/L) - für DWC-Systeme

**Integration-Strategien:**
- **Home Assistant:** REST API und WebSocket für Live-Updates
- **MQTT:** Lightweight Messaging für IoT-Sensoren
- **Modbus/I2C:** Direkte Sensor-Integration für Advanced-User
- **Manuelle Eingabe:** Web-UI und Mobile-App mit Validierung

**Intelligente Fallback-Mechanismen:**
- Automatische Erkennung von Sensor-Ausfällen (>6h ohne Daten)
- Task-Generierung für manuelle Messungen
- Interpolation bei kurzen Ausfällen (<2h)
- Historische Daten-Analyse für Plausibilitätsprüfung

## 2. ArangoDB-Modellierung

### Nodes:
- **`:Sensor`** - Physischer oder virtueller Sensor
  - Properties:
    - `sensor_id: str` (Eindeutige ID)
    - `sensor_type: Literal['physical', 'virtual', 'calculated']`
    - `parameter: str` (z.B. "temperature", "humidity", "ec")
    - `unit: str` (z.B. "°C", "%", "mS/cm")
    - `location_type: Literal['air', 'substrate', 'water', 'light']`
    - `ha_entity_id: Optional[str]` (Home Assistant Entity ID)
    - `mqtt_topic: Optional[str]`
    - `modbus_address: Optional[int]`
    - `calibration_offset: float` (Kalibrierungs-Korrektur)
    - `calibration_factor: float` (Multiplikator)
    - `measurement_interval_seconds: int`
    - `alert_threshold_min: Optional[float]`
    - `alert_threshold_max: Optional[float]`
    - `last_calibration_date: Optional[date]`
    - `sensor_model: Optional[str]` (z.B. "DHT22", "SCD30")
    - `accuracy_percent: Optional[float]`
    - `mounting_height_cm: Optional[int]` (Montagehöhe über Boden/Substrat — Qualitätsfaktor für Repräsentativität)
    - `mounting_position: Optional[Literal['canopy_level', 'above_canopy', 'substrate_level', 'root_zone', 'reservoir', 'wall_mounted', 'freestanding']]`
    - `representative_area_m2: Optional[float]` (Fläche, die der Sensor repräsentativ abdeckt — bei mehreren Sensoren pro Zone dient dies der gewichteten Aggregation)

- **`:Observation`** - Einzelner Messwert
  - Properties:
    - `observation_id: str`
    - `timestamp: datetime`
    - `value: float`
    - `raw_value: Optional[float]` (Vor Kalibrierung)
    - `source: Literal['ha_auto', 'mqtt_auto', 'modbus_auto', 'manual', 'interpolated', 'fallback']`
    - `quality_score: float` (0-1, Vertrauenswürdigkeit)
    - `validated: bool`
    - `outlier: bool` (Statistischer Ausreißer)
    - `validation_notes: Optional[str]`

- **`:SensorCalibration`** - Kalibrierungs-Event
  - Properties:
    - `calibration_id: str`
    - `calibration_date: datetime`
    - `calibration_type: Literal['single_point', 'two_point', 'multi_point']`
    - `reference_values: list[float]` (Sollwerte)
    - `measured_values: list[float]` (Istwerte)
    - `offset_calculated: float`
    - `factor_calculated: float`
    - `r_squared: Optional[float]` (Kalibrierungs-Qualität)
    - `calibrated_by: str` (User-ID)
    - `calibration_solution: Optional[str]` (z.B. "pH 7.0 Buffer")

- **`:Alert`** - Schwellenwert-Überschreitung
  - Properties:
    - `alert_id: str`
    - `triggered_at: datetime`
    - `severity: Literal['info', 'warning', 'critical']`
    - `message: str`
    - `threshold_type: Literal['min', 'max', 'range', 'rate_of_change']`
    - `threshold_value: float`
    - `actual_value: float`
    - `acknowledged: bool`
    - `acknowledged_at: Optional[datetime]`
    - `acknowledged_by: Optional[str]`
    - `resolved_at: Optional[datetime]`
    - `auto_resolved: bool`

- **`:AggregatedMetric`** - Aggregierte Zeitreihen
  - Properties:
    - `metric_id: str`
    - `aggregation_type: Literal['hourly', 'daily', 'weekly']`
    - `period_start: datetime`
    - `period_end: datetime`
    - `value_min: float`
    - `value_max: float`
    - `value_avg: float`
    - `value_stddev: float`
    - `sample_count: int`

- **`:ManualEntry`** - Manuelle Messung
  - Properties:
    - `entry_id: str`
    - `entered_at: datetime`
    - `entered_by: str` (User-ID)
    - `value: float`
    - `confidence: Literal['high', 'medium', 'low']`
    - `measurement_tool: Optional[str]` (z.B. "Apera pH20")
    - `notes: Optional[str]`
    - `photo_reference: Optional[str]`

- **`:SensorHealth`** - Sensor-Status-Tracking
  - Properties:
    - `health_id: str`
    - `checked_at: datetime`
    - `status: Literal['online', 'degraded', 'offline', 'maintenance']`
    - `uptime_percent: float` (Letzte 24h)
    - `last_successful_reading: datetime`
    - `consecutive_failures: int`
    - `battery_level_percent: Optional[int]`
    - `signal_strength_dbm: Optional[int]`

### Edges:
```
Edge Collection          _from              _to                     Attribute
─────────────────────────────────────────────────────────────────────────────
located_at               sensors            slots / locations
recorded                 sensors            observations
validates                observations       requirement_profiles
triggered                observations       alerts
last_calibrated          sensors            sensor_calibrations
has_health_status        sensors            sensor_health
aggregated_into          observations       aggregated_metrics
replaced_by              sensors            sensors                 replacement_date: datetime
confirms                 manual_entries     observations            // Manuelle Verifizierung von Auto-Werten
resolved_by_action       alerts             tasks
part_of_system           sensors            monitoring_systems      // z.B. "Growzelt_1_Climate"
```

### AQL-Beispiellogik:

**Aktuelle Werte mit Fallback-Hierarchie:**
```aql
LET loc_id = @loc_id
LET parameter = @parameter

// Finde Sensoren an diesem Standort
FOR sensor IN sensors
  FILTER sensor.parameter == parameter
  FOR v, e IN 1..1 OUTBOUND sensor located_at
    FILTER v._id == CONCAT("locations/", loc_id) OR v._id == CONCAT("slots/", loc_id)

    // Versuche automatische Readings (letzte 15 Minuten)
    LET auto_observations = (
      FOR obs IN 1..1 OUTBOUND sensor GRAPH 'kamerplanter_graph'
        FILTER IS_DOCUMENT(obs) AND IS_SAME_COLLECTION("observations", obs)
        FILTER obs.source IN ['ha_auto', 'mqtt_auto', 'modbus_auto']
          AND obs.timestamp > DATE_SUBTRACT(DATE_NOW(), 15, "minutes")
        SORT obs.timestamp DESC
        LIMIT 1
        RETURN obs
    )

    // Fallback auf manuelle Eingaben (letzte 1 Stunde)
    LET manual_observations = (
      FOR obs IN 1..1 OUTBOUND sensor GRAPH 'kamerplanter_graph'
        FILTER IS_DOCUMENT(obs) AND IS_SAME_COLLECTION("observations", obs)
        FILTER obs.source == 'manual'
          AND obs.timestamp > DATE_SUBTRACT(DATE_NOW(), 1, "hours")
        SORT obs.timestamp DESC
        LIMIT 1
        RETURN obs
    )

    LET latest_auto = LENGTH(auto_observations) > 0 ? auto_observations[0] : null
    LET latest_manual = LENGTH(manual_observations) > 0 ? manual_observations[0] : null
    LET latest_obs = latest_auto != null ? latest_auto : latest_manual

    LET age_minutes = latest_obs != null
      ? DATE_DIFF(latest_obs.timestamp, DATE_NOW(), "minutes")
      : null

    RETURN {
      sensor_id: sensor.sensor_id,
      parameter: sensor.parameter,
      current_value: latest_obs != null ? latest_obs.value : 'NO_DATA',
      source: latest_obs != null ? latest_obs.source : null,
      age_minutes: age_minutes,
      data_freshness: latest_obs == null ? 'CRITICAL'
        : (age_minutes > 60 ? 'WARNING' : 'OK')
    }
```

**Sensor-Health-Check mit Auto-Task-Generierung:**
```aql
// Finde Sensoren mit Health-Problemen
FOR sensor IN sensors
  FOR health IN 1..1 OUTBOUND sensor has_health_status
    FILTER health.status == 'offline'
      OR health.consecutive_failures > 5
      OR DATE_DIFF(health.last_successful_reading, DATE_NOW(), "hours") > 24

    // Finde zugeordneten Standort
    LET locations = (
      FOR loc IN 1..1 OUTBOUND sensor located_at
        RETURN loc
    )
    LET location = LENGTH(locations) > 0 ? locations[0] : null

    // Prüfe ob bereits Manual-Task existiert
    LET existing_tasks = (
      FOR slot IN 1..1 OUTBOUND location has_slot
        FOR plant IN 1..1 INBOUND slot placed_in
          FOR task IN 1..1 OUTBOUND plant has_task
            FILTER task.status == 'pending'
              AND task.category == 'manual_measurement'
              AND task.due_date >= DATE_FORMAT(DATE_NOW(), "%yyyy-%mm-%dd")
            RETURN task
    )

    // Erstelle Task nur wenn noch keiner existiert
    FILTER LENGTH(existing_tasks) == 0

    // Generiere Manual-Measurement Task
    LET new_task_key = UUID()
    INSERT {
      _key: new_task_key,
      task_id: new_task_key,
      name: CONCAT('Manual ', sensor.parameter, ' Messung erforderlich'),
      category: 'manual_measurement',
      instruction: CONCAT('Sensor ', sensor.sensor_id, ' offline seit ',
                          DATE_DIFF(health.last_successful_reading, DATE_NOW(), "hours"),
                          'h. Bitte manuell messen.'),
      due_date: DATE_FORMAT(DATE_NOW(), "%yyyy-%mm-%dd"),
      priority: 'high',
      status: 'pending',
      created_at: DATE_NOW()
    } INTO tasks
    LET new_task = NEW

    // Verknüpfe Task mit Pflanzen an diesem Standort
    LET linked_plants = (
      FOR slot IN 1..1 OUTBOUND location has_slot
        FOR plant IN 1..1 INBOUND slot placed_in
          INSERT { _from: plant._id, _to: new_task._id } INTO has_task
          RETURN plant._id
    )

    RETURN {
      failed_sensor: sensor.sensor_id,
      generated_task_id: new_task.task_id,
      action: 'Manual measurement task created'
    }
```

**Multi-Sensor-Aggregation für Redundanz:**
```aql
LET loc_id = @loc_id
LET parameter = @parameter

// Sammle neueste validierte Readings pro Sensor
LET readings = (
  FOR sensor IN sensors
    FILTER sensor.parameter == parameter
    FOR loc IN 1..1 OUTBOUND sensor located_at
      FILTER loc._key == loc_id

      // Neueste validierte Observation der letzten 15 Minuten
      LET latest_obs = FIRST(
        FOR obs IN 1..1 OUTBOUND sensor recorded
          FILTER obs.timestamp > DATE_SUBTRACT(DATE_NOW(), 15, "minutes")
            AND obs.validated == true
          SORT obs.timestamp DESC
          LIMIT 1
          RETURN obs
      )

      FILTER latest_obs != null

      RETURN {
        sensor_id: sensor.sensor_id,
        value: latest_obs.value,
        timestamp: latest_obs.timestamp,
        quality: latest_obs.quality_score
      }
)

// Berechne gewichteten Durchschnitt basierend auf Quality-Score
LET weighted_sum = SUM(FOR r IN readings RETURN r.value * r.quality)
LET total_quality = SUM(FOR r IN readings RETURN r.quality)

RETURN {
  aggregated_value: weighted_sum / total_quality,
  sensor_count: LENGTH(readings),
  individual_readings: readings,
  aggregation_method: 'quality_weighted_average',
  confidence: LENGTH(readings) >= 3 ? 'high'
    : (LENGTH(readings) == 2 ? 'medium' : 'low')
}
```

**Trend-Analyse und Anomalie-Erkennung:**
```aql
LET sensor_id = @sensor_id

FOR sensor IN sensors
  FILTER sensor.sensor_id == sensor_id

  // Sammle validierte Observations der letzten 7 Tage
  LET observations = (
    FOR obs IN 1..1 OUTBOUND sensor recorded
      FILTER obs.timestamp > DATE_SUBTRACT(DATE_NOW(), 7, "days")
        AND obs.validated == true
      SORT obs.timestamp ASC
      RETURN { value: obs.value, timestamp: obs.timestamp }
  )

  LET values = observations[*].value
  LET n = LENGTH(values)

  // Berechne statistische Metriken
  LET mean = SUM(values) / n
  LET stddev = SQRT(
    SUM(FOR v IN values RETURN POW(v - mean, 2)) / n
  )

  // Identifiziere Ausreißer (>2 Standardabweichungen)
  FOR idx IN 0..n-1
    LET value = values[idx]
    LET timestamp = observations[idx].timestamp
    LET z_score = ABS(value - mean) / stddev

    // Zweistufige Anomalie-Bewertung:
    // Z-Score > 3.0 = warning (auffällig, prüfenswert)
    // Z-Score > 4.0 = critical (sehr wahrscheinlich Sensor-Fehler oder echtes Extremereignis)
    // Gleitendes Fenster: Statistik basiert auf den letzten 7 Tagen (oben definiert),
    // kann bei stabilen Umgebungen auf 24h reduziert werden für höhere Sensitivität.
    FILTER z_score > 3.0

    LET anomaly_severity = (z_score > 4.0 ? 'critical' : 'warning')

    SORT z_score DESC

    RETURN {
      parameter: sensor.parameter,
      outlier: {
        timestamp: timestamp,
        value: value,
        z_score: z_score,
        deviation_from_mean: value - mean,
        severity: anomaly_severity,
        is_outlier: true
      },
      mean: mean,
      stddev: stddev,
      window_days: 7
    }
```

**Kalibrierungs-Historie und Drift-Erkennung:**
```aql
LET sensor_id = @sensor_id

FOR sensor IN sensors
  FILTER sensor.sensor_id == sensor_id

  // Hole alle Kalibrierungen über Graph-Traversal (bis zu 10 Stufen)
  LET calibrations = (
    FOR v IN 1..10 OUTBOUND sensor last_calibrated
      SORT v.calibration_date DESC
      RETURN v
  )

  LET cal = calibrations[0]  // Neueste Kalibrierung

  LET offset_history = calibrations[*].offset_calculated
  LET date_history = calibrations[*].calibration_date

  // Berechne Drift-Rate
  LET drift_per_day = LENGTH(offset_history) >= 2
    ? (offset_history[0] - LAST(offset_history)) /
      DATE_DIFF(LAST(date_history), date_history[0], "days")
    : 0

  LET days_since_calibration = DATE_DIFF(cal.calibration_date, DATE_NOW(), "days")

  RETURN {
    parameter: sensor.parameter,
    last_calibrated: cal.calibration_date,
    days_since_calibration: days_since_calibration,
    current_offset: cal.offset_calculated,
    drift_per_day: drift_per_day,
    calibration_status: days_since_calibration > 90 ? 'OVERDUE'
      : (ABS(drift_per_day) > 0.01 ? 'HIGH_DRIFT' : 'OK'),
    historical_offsets: offset_history
  }
```

## 3. Technische Umsetzung (Python)

### Logik-Anforderungen:

**1. Sensor Reading mit Quality Scoring:**
```python
from pydantic import BaseModel, Field, field_validator
from typing import Literal, Optional
from datetime import datetime, timedelta
import statistics

class SensorReading(BaseModel):
    """Einzelne Sensor-Messung mit Metadaten"""
    
    sensor_id: str
    parameter: Literal['temp', 'humidity', 'ec', 'ph', 'ppfd', 'co2', 'soil_moisture', 'water_level']
    value: float
    unit: str
    source: Literal['ha_auto', 'mqtt_auto', 'modbus_auto', 'manual', 'interpolated', 'fallback']
    timestamp: datetime = Field(default_factory=datetime.now)
    quality_score: float = Field(default=1.0, ge=0, le=1.0)
    
    # Validierungs-Ranges pro Parameter
    VALID_RANGES = {
        'temp': (-10, 50),
        'humidity': (0, 100),
        'ec': (0, 15),          # Hydro-Stammlösungen bis 12+ mS/cm
        'ph': (0, 14),
        'ppfd': (0, 2500),      # Gewächshäuser mit Supplemental-Beleuchtung erreichen >2000 μmol/m²/s
        'co2': (150, 10000),    # Outdoor-Minimum ~150, Anreicherung bis 10000 ppm
        'soil_moisture': (0, 100),
        'water_level': (0, 100),
        'leaf_temp': (-5, 50),
        'substrate_temp': (-5, 45),
        'water_temp': (0, 40),
        'do': (0, 20),          # Dissolved Oxygen mg/L
        'orp': (-500, 1000),    # Oxidation-Reduction Potential mV
        'flow_rate': (0, 1000), # L/h
        'air_velocity': (0, 20),  # m/s
        'r_fr_ratio': (0.1, 10.0),   # Dimensionslos — typisch 0.5-3.0 (Sonnenlicht ~1.2, LED variabel)
        'blue_fraction': (0, 100),    # Prozent des PAR-Spektrums im Blaubereich (400-500nm)
    }
    
    def validate_plausibility(self) -> dict:
        """
        Plausibilitätsprüfung mit detailliertem Feedback
        Returns: {valid: bool, error: Optional[str], warning: Optional[str]}
        """
        min_val, max_val = self.VALID_RANGES.get(self.parameter, (-1000, 1000))
        
        # Kritische Verletzung
        if not (min_val <= self.value <= max_val):
            return {
                'valid': False,
                'error': f'{self.parameter} = {self.value}{self.unit} außerhalb physikalisch möglichem Bereich: {min_val}-{max_val}{self.unit}',
                'severity': 'critical'
            }
        
        # Warnung bei extremen aber möglichen Werten
        warning_margin = (max_val - min_val) * 0.1
        if self.value < (min_val + warning_margin) or self.value > (max_val - warning_margin):
            return {
                'valid': True,
                'warning': f'{self.parameter} nahe Grenzbereich - bitte visuell bestätigen',
                'severity': 'warning'
            }
        
        return {'valid': True, 'severity': 'ok'}
    
    def calculate_quality_score(
        self,
        previous_values: list[float],
        time_since_last: timedelta
    ) -> float:
        """
        Berechnet Quality-Score basierend auf Konsistenz
        Faktoren:
        - Statistische Konsistenz mit Historie
        - Zeitliche Kontinuität
        - Source-Vertrauenswürdigkeit
        """
        score = 1.0
        
        # 1. Source-basierte Basis-Qualität
        # Manuelle Eingaben differenziert bewerten: Ein kalibriertes Profi-Gerät
        # (z.B. Apera pH20) liefert annähernd Auto-Qualität, während eine
        # grobe Schätzung ohne Werkzeug deutlich weniger zuverlässig ist.
        # Die Basisbewertung 0.85 gilt für manuelle Eingaben MIT kalibriertem
        # Messgerät. Adjustierung erfolgt in calculate_manual_quality_score().
        source_scores = {
            'ha_auto': 1.0,
            'mqtt_auto': 0.95,
            'modbus_auto': 0.95,
            'manual': 0.85,       # Basis — wird durch Gerätegenauigkeit/Kalibrierung adjustiert
            'interpolated': 0.6,
            'fallback': 0.4
        }
        score *= source_scores.get(self.source, 0.5)
        
        # 2. Zeitliche Aktualität (penalisiere alte Daten)
        if time_since_last.total_seconds() > 3600:  # >1h
            age_penalty = 1 - min(0.5, time_since_last.total_seconds() / 7200)
            score *= age_penalty
        
        # 3. Statistische Konsistenz
        if len(previous_values) >= 3:
            mean = statistics.mean(previous_values)
            stddev = statistics.stdev(previous_values) if len(previous_values) > 1 else 0
            
            if stddev > 0:
                z_score = abs(self.value - mean) / stddev
                
                # Penalisiere Ausreißer
                if z_score > 3:  # >3 Standardabweichungen
                    score *= 0.5
                elif z_score > 2:
                    score *= 0.8
        
        self.quality_score = max(0.0, min(1.0, score))
        return self.quality_score

class SensorReadingValidator:
    """Erweiterte Validierung mit Kontext"""
    
    @staticmethod
    def validate_reading_sequence(
        readings: list[SensorReading],
        max_rate_of_change: Optional[dict[str, float]] = None
    ) -> dict:
        """
        Prüft eine Sequenz von Messungen auf Anomalien
        
        Args:
            readings: Chronologisch sortierte Readings
            max_rate_of_change: Dict[parameter, max_change_per_minute]
        
        Returns:
            Validierungs-Bericht
        """
        if not max_rate_of_change:
            # Defaults: Maximale Änderungsrate pro Minute
            max_rate_of_change = {
                'temp': 0.5,           # 0.5°C/min
                'humidity': 2.0,       # 2%/min
                'ec': 0.05,           # 0.05 mS/min
                'ph': 0.1,            # 0.1 pH/min
                'co2': 50.0,          # 50 ppm/min
                'ppfd': 100.0,        # 100 μmol/m²/s/min — Wolkendurchzug oder Lampen-Schaltung
                'soil_moisture': 1.0,  # 1%/min — schnellere Änderungen deuten auf Sensorverschiebung hin
                'water_temp': 0.3,     # 0.3°C/min
                'leaf_temp': 0.8,      # 0.8°C/min — reagiert schneller als Lufttemperatur
            }
        
        anomalies = []
        
        for i in range(1, len(readings)):
            prev = readings[i-1]
            curr = readings[i]
            
            if prev.parameter != curr.parameter:
                continue
            
            # Zeitdifferenz in Minuten
            time_diff = (curr.timestamp - prev.timestamp).total_seconds() / 60
            
            if time_diff == 0:
                continue
            
            # Änderungsrate
            rate_of_change = abs(curr.value - prev.value) / time_diff
            max_allowed = max_rate_of_change.get(curr.parameter, float('inf'))
            
            if rate_of_change > max_allowed:
                anomalies.append({
                    'timestamp': curr.timestamp,
                    'parameter': curr.parameter,
                    'previous_value': prev.value,
                    'current_value': curr.value,
                    'rate_of_change': round(rate_of_change, 3),
                    'max_allowed': max_allowed,
                    'severity': 'critical' if rate_of_change > (max_allowed * 2) else 'warning',
                    'message': f'Unplausibel schnelle Änderung: {rate_of_change:.2f} {curr.unit}/min (Max: {max_allowed})'
                })
        
        return {
            'valid': len(anomalies) == 0,
            'anomaly_count': len(anomalies),
            'anomalies': anomalies,
            'total_readings_checked': len(readings)
        }
```

**2. Home Assistant Connector:**
```python
import requests
from typing import Optional, Dict
import json

class HomeAssistantConnector:
    """Integration mit Home Assistant für automatische Sensor-Daten"""
    
    def __init__(self, ha_url: str, ha_token: str, verify_ssl: bool = True):
        self.base_url = ha_url.rstrip('/')
        self.headers = {
            'Authorization': f'Bearer {ha_token}',
            'Content-Type': 'application/json'
        }
        self.verify_ssl = verify_ssl
        self.timeout = 10
    
    def test_connection(self) -> dict:
        """Prüft Verbindung zu HA"""
        try:
            response = requests.get(
                f'{self.base_url}/api/',
                headers=self.headers,
                timeout=5,
                verify=self.verify_ssl
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'connected': True,
                    'ha_version': data.get('version'),
                    'message': data.get('message')
                }
            else:
                return {
                    'connected': False,
                    'error': f'HTTP {response.status_code}: {response.text}'
                }
        except requests.exceptions.RequestException as e:
            return {
                'connected': False,
                'error': str(e)
            }
    
    def get_sensor_state(self, entity_id: str) -> Optional[SensorReading]:
        """
        Liest aktuellen Zustand eines HA-Sensors
        
        Args:
            entity_id: HA Entity ID (z.B. "sensor.growzelt_temperature")
        
        Returns:
            SensorReading oder None bei Fehler
        """
        try:
            response = requests.get(
                f'{self.base_url}/api/states/{entity_id}',
                headers=self.headers,
                timeout=self.timeout,
                verify=self.verify_ssl
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Extrahiere Wert (HA speichert als String)
                try:
                    value = float(data['state'])
                except (ValueError, KeyError):
                    return None
                
                # Extrahiere Unit
                unit = data.get('attributes', {}).get('unit_of_measurement', '')
                
                # Mapping von HA-Sensor zu Parameter-Typ
                parameter = self._infer_parameter_from_entity(entity_id, unit)
                
                return SensorReading(
                    sensor_id=entity_id,
                    parameter=parameter,
                    value=value,
                    unit=unit,
                    source='ha_auto',
                    timestamp=datetime.fromisoformat(data['last_updated'].replace('Z', '+00:00'))
                )
            
            return None
            
        except requests.exceptions.RequestException as e:
            print(f"HA Request Error: {e}")
            return None
    
    def get_sensor_history(
        self,
        entity_id: str,
        start_time: datetime,
        end_time: Optional[datetime] = None
    ) -> list[SensorReading]:
        """
        Holt historische Daten aus HA
        
        Args:
            entity_id: HA Entity ID
            start_time: Start-Zeitpunkt
            end_time: End-Zeitpunkt (default: jetzt)
        
        Returns:
            Liste von SensorReadings
        """
        if not end_time:
            end_time = datetime.now()
        
        # HA History API Format
        start_iso = start_time.isoformat()
        end_iso = end_time.isoformat()
        
        try:
            response = requests.get(
                f'{self.base_url}/api/history/period/{start_iso}',
                params={
                    'filter_entity_id': entity_id,
                    'end_time': end_iso
                },
                headers=self.headers,
                timeout=self.timeout,
                verify=self.verify_ssl
            )
            
            if response.status_code == 200:
                data = response.json()
                
                readings = []
                for entity_data in data:
                    for state in entity_data:
                        try:
                            value = float(state['state'])
                            unit = state.get('attributes', {}).get('unit_of_measurement', '')
                            parameter = self._infer_parameter_from_entity(entity_id, unit)
                            
                            readings.append(SensorReading(
                                sensor_id=entity_id,
                                parameter=parameter,
                                value=value,
                                unit=unit,
                                source='ha_auto',
                                timestamp=datetime.fromisoformat(state['last_updated'].replace('Z', '+00:00'))
                            ))
                        except (ValueError, KeyError):
                            continue
                
                return readings
            
            return []
            
        except requests.exceptions.RequestException as e:
            print(f"HA History Error: {e}")
            return []
    
    def _infer_parameter_from_entity(self, entity_id: str, unit: str) -> str:
        """
        Inferiert Parameter-Typ aus Entity-ID und Unit.

        EMPFEHLUNG: Die Inferenz basierend auf Entity-Naming ist fehleranfällig —
        z.B. kann 'sensor.garden_humidity' sowohl Luft- als auch Bodenfeuchte sein.
        Bei der erstmaligen Zuordnung eines HA-Sensors SOLLTE das UI den inferierten
        Typ dem Nutzer zur Bestätigung vorlegen. Das Ergebnis wird dann im
        Sensor-Node unter `parameter` persistent gespeichert, sodass die Inferenz
        nur beim Onboarding nötig ist.
        """

        entity_lower = entity_id.lower()
        unit_lower = unit.lower()
        
        # Temperatur
        if 'temp' in entity_lower or unit_lower in ['°c', 'c', 'celsius', '°f', 'f']:
            return 'temp'
        
        # Luftfeuchte
        if 'hum' in entity_lower or unit_lower == '%':
            return 'humidity'
        
        # EC
        if 'ec' in entity_lower or 'conductivity' in entity_lower:
            return 'ec'
        
        # pH
        if 'ph' in entity_lower:
            return 'ph'
        
        # CO2
        if 'co2' in entity_lower or unit_lower == 'ppm':
            return 'co2'
        
        # PPFD/Licht
        if 'light' in entity_lower or 'ppfd' in entity_lower or unit_lower in ['μmol/m²/s', 'umol']:
            return 'ppfd'
        
        # Soil Moisture
        if 'soil' in entity_lower or 'moisture' in entity_lower:
            return 'soil_moisture'
        
        return 'unknown'
    
    def subscribe_to_updates(self, entity_ids: list[str], callback):
        """
        WebSocket-Subscription für Real-Time Updates
        (Vereinfachtes Beispiel - in Produktion mit websocket-client)
        """
        # TODO: Implement WebSocket connection
        pass
```

**3. Sensor Fallback Manager:**
```python
from datetime import datetime, timedelta
from typing import Optional

class SensorFallbackManager:
    """Erkennt Sensor-Ausfälle und orchestriert Fallback-Strategien"""
    
    # Konfigurierbare Schwellenwerte (Defaults — parameterspezifisch überschreibbar)
    MAX_AGE_CRITICAL_HOURS = 24
    MAX_AGE_WARNING_HOURS = 6
    MAX_AGE_INTERPOLATION_HOURS = 2

    # Parameterspezifische Schwellenwerte für Sensor-Ausfälle:
    # Schnell-veränderliche Parameter (Temperatur, VPD) benötigen häufigere Updates
    # als träge Parameter (EC im Substrat, Bodenfeuchte).
    PARAMETER_WARNING_HOURS: dict[str, float] = {
        'temp':           2.0,    # Temperatur ändert sich schnell — 2h Warning
        'humidity':       2.0,    # Feuchte ebenso
        'vpd':            2.0,    # Abgeleiteter Wert von temp+humidity
        'co2':            3.0,    # Moderat dynamisch
        'ppfd':           4.0,    # Relevant nur bei Licht-an — toleranter
        'ec':             6.0,    # Ändert sich langsam im Substrat
        'ph':             6.0,    # Ändert sich langsam
        'soil_moisture':  8.0,    # Träge, besonders in Erde
        'water_level':    8.0,    # Reservoir-Level ändert sich langsam
        'leaf_temp':      2.0,    # Schnell veränderlich (Licht-/Luftbewegung)
        'water_temp':     4.0,    # Reservoir-Temperatur ist träger
        'do':             4.0,    # DWC-kritisch, aber nicht sekundenschnell
    }

    # Parameterspezifische maximale Interpolationsdauer:
    # Schnell-veränderliche Parameter dürfen nur kurz interpoliert werden,
    # da lineare Interpolation bei hoher Dynamik zu ungenauen Werten führt.
    MAX_INTERPOLATION_HOURS: dict[str, float] = {
        'temp':           2.0,
        'humidity':       2.0,
        'vpd':            1.0,    # Abgeleitet — Interpolation weniger zuverlässig
        'co2':            1.0,    # Stark von Lüftung abhängig — nicht linear
        'ppfd':           0.5,    # Licht ändert sich sprunghaft (Wolken, Schaltung)
        'ec':             4.0,    # Träge im Substrat
        'ph':             4.0,
        'soil_moisture':  6.0,    # Sehr träge in Erde
        'water_level':    6.0,
        'leaf_temp':      1.0,
        'water_temp':     3.0,
        'do':             2.0,
    }
    
    def __init__(self, arango_db):
        self.db = arango_db
    
    def check_sensor_health(
        self,
        sensor_id: str,
        last_reading_time: Optional[datetime],
        parameter: Optional[str] = None
    ) -> dict:
        """
        Überprüft Sensor-Gesundheit und empfiehlt Actions
        
        Returns:
            {
                status: 'OK' | 'WARNING' | 'CRITICAL',
                action: Optional[str],
                message: str,
                age_hours: float
            }
        """
        if not last_reading_time:
            return {
                'status': 'CRITICAL',
                'action': 'CREATE_MANUAL_TASK',
                'message': 'Sensor hat noch nie Daten geliefert',
                'age_hours': float('inf')
            }
        
        age = datetime.now() - last_reading_time
        age_hours = age.total_seconds() / 3600

        # Parameterspezifische Schwellenwerte verwenden, falls verfügbar
        warning_hours = self.PARAMETER_WARNING_HOURS.get(
            parameter, self.MAX_AGE_WARNING_HOURS
        ) if parameter else self.MAX_AGE_WARNING_HOURS
        interpolation_hours = self.MAX_INTERPOLATION_HOURS.get(
            parameter, self.MAX_AGE_INTERPOLATION_HOURS
        ) if parameter else self.MAX_AGE_INTERPOLATION_HOURS

        if age_hours > self.MAX_AGE_CRITICAL_HOURS:
            return {
                'status': 'CRITICAL',
                'action': 'CREATE_MANUAL_TASK',
                'message': f'Sensor seit {age_hours:.1f}h offline - Manuelle Messung erforderlich',
                'age_hours': age_hours,
                'task_priority': 'high',
                'suggested_measurement_frequency': 'daily'
            }
        
        elif age_hours > warning_hours:
            return {
                'status': 'WARNING',
                'action': 'NOTIFY_USER',
                'message': f'Sensor seit {age_hours:.1f}h ohne Update - bitte prüfen',
                'age_hours': age_hours,
                'threshold_hours': warning_hours,
                'check_battery': True,
                'check_connectivity': True
            }

        elif age_hours > interpolation_hours:
            return {
                'status': 'OK',
                'action': 'USE_INTERPOLATION',
                'message': f'Kurzer Ausfall ({age_hours:.1f}h) - Interpolation verwenden',
                'age_hours': age_hours
            }
        
        return {
            'status': 'OK',
            'message': 'Sensor liefert aktuelle Daten',
            'age_hours': age_hours
        }
    
    def interpolate_missing_values(
        self,
        sensor_id: str,
        gap_start: datetime,
        gap_end: datetime
    ) -> list[SensorReading]:
        """
        Interpoliert fehlende Werte zwischen zwei bekannten Punkten
        Verwendet lineare Interpolation für kurze Lücken
        """
        # Hole Wert vor und nach der Lücke via AQL
        cursor = self.db.aql.execute("""
            FOR sensor IN sensors
              FILTER sensor.sensor_id == @sensor_id
              LET before_obs = FIRST(
                FOR obs IN 1..1 OUTBOUND sensor recorded
                  FILTER obs.timestamp < @gap_start
                  SORT obs.timestamp DESC
                  LIMIT 1
                  RETURN obs
              )
              LET after_obs = FIRST(
                FOR obs IN 1..1 OUTBOUND sensor recorded
                  FILTER obs.timestamp > @gap_end
                  SORT obs.timestamp ASC
                  LIMIT 1
                  RETURN obs
              )
              RETURN { before_obs, after_obs }
        """, bind_vars={
            'sensor_id': sensor_id,
            'gap_start': gap_start.isoformat(),
            'gap_end': gap_end.isoformat()
        })

        result = next(cursor, None)

        if not result or not result['before_obs'] or not result['after_obs']:
            return []

        before = result['before_obs']
        after = result['after_obs']

        # Lineare Interpolation
        time_span = (after['timestamp'] - before['timestamp']).total_seconds()
        value_span = after['value'] - before['value']

        interpolated = []
        current_time = gap_start

        # Generiere stündliche Interpolations-Punkte
        while current_time < gap_end:
            time_fraction = (current_time - before['timestamp']).total_seconds() / time_span
            interpolated_value = before['value'] + (value_span * time_fraction)

            interpolated.append(SensorReading(
                sensor_id=sensor_id,
                parameter=before['parameter'],
                value=interpolated_value,
                unit=before['unit'],
                source='interpolated',
                timestamp=current_time,
                quality_score=0.6  # Reduzierte Qualität für interpolierte Daten
            ))

            current_time += timedelta(hours=1)

        return interpolated
    
    def create_manual_measurement_task(
        self,
        sensor_id: str,
        parameter: str,
        location_id: str
    ) -> str:
        """
        Generiert einen Task für manuelle Messung
        
        Returns:
            task_id
        """
        # Erstelle Task und verknüpfe mit Pflanzen via AQL
        cursor = self.db.aql.execute("""
            // Erstelle Task
            LET new_task_key = UUID()
            INSERT {
                _key: new_task_key,
                task_id: new_task_key,
                name: CONCAT('Manuelle ', @parameter, ' Messung'),
                category: 'manual_measurement',
                instruction: CONCAT('Sensor ', @sensor_id,
                    ' offline. Bitte ', @parameter,
                    ' manuell messen und eingeben.'),
                due_date: DATE_FORMAT(DATE_NOW(), "%yyyy-%mm-%dd"),
                priority: 'high',
                status: 'pending',
                created_at: DATE_NOW(),
                requires_photo: false,
                estimated_duration_minutes: 5
            } INTO tasks
            LET new_task = NEW

            // Verknüpfe mit Pflanzen an diesem Standort
            FOR location IN locations
              FILTER location._key == @location_id
              FOR slot IN 1..1 OUTBOUND location has_slot
                FOR plant IN 1..1 INBOUND slot placed_in
                  INSERT { _from: plant._id, _to: new_task._id } INTO has_task

            RETURN new_task.task_id
        """, bind_vars={
            'sensor_id': sensor_id,
            'parameter': parameter,
            'location_id': location_id
        })

        result = next(cursor, None)
        return result if result else None
```

**4. Manual Input Validator:**
```python
from datetime import timedelta
from typing import Optional

class ManualInputValidator:
    """Validiert und scored manuelle Eingaben"""
    
    @staticmethod
    def validate_manual_entry(
        parameter: str,
        value: float,
        previous_value: Optional[float],
        time_since_last: Optional[timedelta],
        user_confidence: Literal['high', 'medium', 'low']
    ) -> dict:
        """
        Prüft ob manuelle Eingabe plausibel ist
        
        Returns:
            {
                suspicious: bool,
                confidence_score: float,
                warnings: list[str],
                confirm_required: bool
            }
        """
        warnings = []
        suspicious = False
        
        # 1. Basis-Plausibilität (Wertebereich)
        reading = SensorReading(
            sensor_id='manual',
            parameter=parameter,
            value=value,
            unit='',
            source='manual'
        )
        
        plausibility = reading.validate_plausibility()
        if not plausibility['valid']:
            return {
                'suspicious': True,
                'confidence_score': 0.0,
                'warnings': [plausibility['error']],
                'confirm_required': True
            }
        
        # 2. Vergleich mit letztem Wert
        if previous_value and time_since_last:
            hours = time_since_last.total_seconds() / 3600
            
            # Maximal erwartete Änderung pro Stunde
            max_change_per_hour = {
                'temp': 3.0,
                'humidity': 15.0,
                'ec': 0.3,
                'ph': 0.5,
                'co2': 200.0
            }
            
            expected_max_change = max_change_per_hour.get(parameter, 999) * hours
            actual_change = abs(value - previous_value)
            
            if actual_change > expected_max_change:
                suspicious = True
                warnings.append(
                    f'Ungewöhnlich starke Änderung: {actual_change:.1f} '
                    f'(erwartet max {expected_max_change:.1f} in {hours:.1f}h)'
                )
        
        # 3. User Confidence Score
        confidence_scores = {
            'high': 1.0,
            'medium': 0.8,
            'low': 0.6
        }
        base_confidence = confidence_scores.get(user_confidence, 0.5)
        
        # 4. Finale Bewertung
        if suspicious:
            final_confidence = base_confidence * 0.6  # Penalty für Verdacht
        else:
            final_confidence = base_confidence
        
        return {
            'suspicious': suspicious,
            'confidence_score': final_confidence,
            'warnings': warnings,
            'confirm_required': suspicious and final_confidence < 0.7
        }
    
    @staticmethod
    def calculate_manual_quality_score(
        user_confidence: Literal['high', 'medium', 'low'],
        measurement_tool: Optional[str] = None,
        tool_last_calibrated_days_ago: Optional[int] = None,
        tool_accuracy_percent: Optional[float] = None,
    ) -> float:
        """
        Differenzierter Quality-Score für manuelle Eingaben.
        Berücksichtigt Kalibrierungsstatus und Gerätegenauigkeit statt
        pauschalem Score.

        Returns:
            Quality-Score 0.0-1.0
        """
        # Basis nach User-Confidence
        confidence_scores = {'high': 0.9, 'medium': 0.75, 'low': 0.55}
        score = confidence_scores.get(user_confidence, 0.6)

        # Bonus für bekanntes, kalibriertes Messgerät
        if measurement_tool:
            score += 0.05  # Gerät angegeben = leichter Bonus

            # Kalibrierungsstatus
            if tool_last_calibrated_days_ago is not None:
                if tool_last_calibrated_days_ago <= 7:
                    score += 0.05   # Frisch kalibriert
                elif tool_last_calibrated_days_ago > 90:
                    score -= 0.1    # Überfällige Kalibrierung
                elif tool_last_calibrated_days_ago > 30:
                    score -= 0.05   # Kalibrierung empfohlen

            # Gerätegenauigkeit
            if tool_accuracy_percent is not None:
                if tool_accuracy_percent <= 2.0:
                    score += 0.05   # Hochpräzises Gerät
                elif tool_accuracy_percent > 10.0:
                    score -= 0.1    # Geringes Präzisionsniveau
        else:
            # Kein Messgerät angegeben = Schätzung
            score -= 0.15

        return max(0.1, min(1.0, score))

    @staticmethod
    def suggest_measurement_tool(parameter: str) -> dict:
        """Empfiehlt geeignetes Mess-Tool"""
        
        tools = {
            'temp': {
                'recommended': ['Infrarot-Thermometer', 'DHT22', 'DS18B20'],
                'accuracy': '±0.5°C',
                'notes': 'Für Blatttemperatur IR-Thermometer verwenden'
            },
            'humidity': {
                'recommended': ['DHT22', 'SHT31', 'BME280'],
                'accuracy': '±2%',
                'notes': 'Sensor auf Höhe der Pflanzen positionieren'
            },
            'ec': {
                'recommended': ['Apera EC60', 'Bluelab Conductivity Pen', 'Milwaukee EC59'],
                'accuracy': '±2%',
                'notes': 'Vor Messung kalibrieren, Temperaturkompensation beachten'
            },
            'ph': {
                'recommended': ['Apera pH20', 'Bluelab pH Pen', 'Hanna HI98107'],
                'accuracy': '±0.1 pH',
                'notes': 'Regelmäßig mit pH 4.0 und 7.0 Pufferlösungen kalibrieren'
            },
            'ppfd': {
                'recommended': ['Apogee MQ-500', 'LI-COR LI-250A', 'Dr.Meter LX1330B (Budget)'],
                'accuracy': '±5%',
                'notes': 'In Höhe der Pflanzenspitzen messen'
            }
        }
        
        return tools.get(parameter, {
            'recommended': ['Nicht spezifiziert'],
            'accuracy': 'N/A',
            'notes': 'Verwende kalibriertes Messgerät'
        })
```

### Datenvalidierung (Type Hinting):
```python
from typing import Literal, Optional, List
from pydantic import BaseModel, Field, field_validator
from datetime import datetime, date

SensorType = Literal['physical', 'virtual', 'calculated']
ParameterType = Literal[
    'temp', 'humidity', 'ec', 'ph', 'ppfd', 'co2', 'soil_moisture', 'water_level', 'vpd',
    'leaf_temp',        # Blatttemperatur für Leaf-VPD-Berechnung
    'substrate_temp',   # Wurzelzonen-Temperatur (REQ-019)
    'water_temp',       # Reservoir/Nährlösung
    'do',               # Dissolved Oxygen (Hydro-Systeme)
    'orp',              # Oxidation-Reduction Potential
    'flow_rate',        # Durchfluss (L/h)
    'air_velocity',     # Luftbewegung (m/s)
    'r_fr_ratio',       # Rot/Far-Red-Verhältnis — steuert Phytochrom-Gleichgewicht (Streckungswachstum)
    'blue_fraction',    # Blauanteil (%) im PAR-Spektrum — beeinflusst Kompaktwuchs und Stomata-Öffnung
    'par_spectrum'      # PAR-Spektralverteilung (JSON-kodiert: {nm_range: μmol/m²/s}) — für detaillierte Lichtanalyse
]
SourceType = Literal['ha_auto', 'mqtt_auto', 'modbus_auto', 'manual', 'interpolated', 'fallback']
AlertSeverity = Literal['info', 'warning', 'critical']
SensorStatus = Literal['online', 'degraded', 'offline', 'maintenance']

class SensorDefinition(BaseModel):
    """Vollständige Sensor-Definition"""
    
    sensor_id: str = Field(regex=r'^[a-zA-Z0-9_-]+$')
    sensor_type: SensorType
    parameter: ParameterType
    unit: str = Field(min_length=1, max_length=20)
    location_id: str
    ha_entity_id: Optional[str] = Field(None, regex=r'^[a-z_]+\.[a-z0-9_]+$')
    mqtt_topic: Optional[str] = None
    calibration_offset: float = Field(default=0.0)
    calibration_factor: float = Field(default=1.0, gt=0)
    measurement_interval_seconds: int = Field(ge=10, le=3600)
    alert_threshold_min: Optional[float] = None
    alert_threshold_max: Optional[float] = None
    # Hinweis: Alert-Schwellenwerte sind phasenabhängig (REQ-003).
    # VPD-Ziel vegetativ: 0.8-1.5 kPa, Blüte: 0.4-0.8 kPa.
    # Statische Schwellenwerte hier sind Sicherheits-Maxima;
    # phasenspezifische Thresholds kommen aus PhaseControlProfile.
    sensor_model: Optional[str] = None
    accuracy_percent: Optional[float] = Field(None, ge=0, le=100)
    mounting_height_cm: Optional[int] = Field(None, ge=0, le=500,
        description="Montagehöhe über Boden/Substrat in cm. Qualitätsfaktor: "
                    "PPFD-Sensoren sollten auf Canopy-Level sein, Temperatur-Sensoren "
                    "nicht direkt an der Lichtquelle.")
    mounting_position: Optional[Literal[
        'canopy_level', 'above_canopy', 'substrate_level',
        'root_zone', 'reservoir', 'wall_mounted', 'freestanding'
    ]] = None
    representative_area_m2: Optional[float] = Field(None, ge=0,
        description="Fläche die der Sensor repräsentativ abdeckt. "
                    "Wird bei Multi-Sensor-Aggregation zur Gewichtung genutzt.")

    # Substratfeuchte-Differenzierung: Verschiedene Messprinzipien liefern
    # unterschiedliche Werte und Einheiten. Ein kapazitiver Sensor in Coco
    # misst anders als ein Tensiometer in Erde.
    soil_moisture_method: Optional[Literal[
        'capacitive',        # Kapazitiv (Standard für die meisten Hobby-Sensoren, misst Dielektrizität)
        'resistive',         # Widerstandsmessung (günstig, korrosionsanfällig)
        'tensiometer',       # Saugspannung in kPa/cbar (misst Pflanzenverfügbarkeit direkt)
        'tdr',               # Time Domain Reflectometry (Profi, sehr genau)
        'gravimetric',       # Wiegung (Labor-Referenz)
    ]] = None  # Nur relevant für parameter='soil_moisture'
    soil_moisture_unit: Optional[Literal[
        'percent_vwc',       # Volumetrischer Wassergehalt (%) — Standard für kapazitiv/TDR
        'percent_raw',       # Rohwert des Sensors (%) — oft herstellerspezifisch skaliert
        'kpa',               # Saugspannung (Tensiometer) — 0=gesättigt, 80+=trocken
        'cbar',              # Centibar (= kPa, alternative Einheit für Tensiometer)
    ]] = None
    substrate_type_key: Optional[str] = None  # Referenz auf REQ-019 Substrat — beeinflusst Interpretation der Messwerte
    
    @field_validator('calibration_factor')
    @classmethod
    def validate_reasonable_calibration(cls, v):
        if not (0.5 <= v <= 2.0):
            raise ValueError("Calibration factor außerhalb vernünftigem Bereich (0.5-2.0)")
        return v
    
    @field_validator('ha_entity_id')
    @classmethod
    def validate_ha_entity(cls, v):
        if v and not v.startswith(('sensor.', 'binary_sensor.')):
            raise ValueError("HA Entity muss mit 'sensor.' oder 'binary_sensor.' beginnen")
        return v


class PhaseAlertProfile(BaseModel):
    """
    Phasenabhängiges Alert-Profil: Verknüpft Sensorparameter mit Wachstumsphasen
    für dynamisches Alerting. Statische Schwellenwerte auf dem Sensor-Node sind
    Sicherheits-Maxima; die hier definierten Schwellenwerte kommen aus dem
    PhaseControlProfile (REQ-003) und werden bei jedem Phasenwechsel aktualisiert.

    Beispiel: VPD-Warnung bei 0.6 kPa in der vegetativen Phase (Ziel 0.8-1.5),
    aber VPD-Warnung erst bei 0.3 kPa in der Blüte (Ziel 0.4-0.8).
    """

    profile_id: str
    phase_name: str  # z.B. 'vegetative', 'flowering'
    parameter: ParameterType
    warning_min: Optional[float] = None
    warning_max: Optional[float] = None
    critical_min: Optional[float] = None
    critical_max: Optional[float] = None
    target_min: float  # Optimaler Bereich — untere Grenze
    target_max: float  # Optimaler Bereich — obere Grenze

    # Referenz auf REQ-003 PhaseControlProfile
    # Bei Phasenwechsel: Engine liest PhaseControlProfile und aktualisiert
    # aktive Alert-Schwellenwerte für alle Sensoren am Standort.

    PHASE_DEFAULTS: dict[str, dict[str, tuple]] = {
        'vegetative': {
            'vpd':       (0.4, 0.8, 1.5, 2.0),   # (crit_min, warn_min/target_min, target_max/warn_max, crit_max)
            'temp':      (15, 20, 30, 35),
            'humidity':  (30, 40, 70, 85),
            'ppfd':      (100, 200, 600, 1000),
        },
        'flowering': {
            'vpd':       (0.2, 0.4, 0.8, 1.2),
            'temp':      (18, 20, 28, 32),
            'humidity':  (40, 45, 60, 70),
            'ppfd':      (200, 400, 800, 1200),
        },
        'seedling': {
            'vpd':       (0.2, 0.4, 0.8, 1.0),
            'temp':      (20, 22, 28, 30),
            'humidity':  (50, 60, 80, 90),
            'ppfd':      (50, 100, 300, 500),
        },
    }

class CalibrationRecord(BaseModel):
    """Kalibrierungs-Event"""
    
    sensor_id: str
    calibration_date: datetime
    calibration_type: Literal['single_point', 'two_point', 'multi_point']
    reference_values: List[float] = Field(min_items=1, max_items=10)
    measured_values: List[float] = Field(min_items=1, max_items=10)
    calibrated_by: str
    calibration_solution: Optional[str] = None
    notes: Optional[str] = Field(None, max_length=500)
    
    @field_validator('measured_values')
    @classmethod
    def validate_value_count_match(cls, v, info):
        ref_vals = info.data.get('reference_values', [])
        if len(v) != len(ref_vals):
            raise ValueError("Anzahl measured_values muss reference_values entsprechen")
        return v
    
    def calculate_calibration_params(self) -> dict:
        """Berechnet Offset und Factor aus Kalibrierpunkten"""
        
        if self.calibration_type == 'single_point':
            # Offset-Korrektur
            offset = self.reference_values[0] - self.measured_values[0]
            return {'offset': offset, 'factor': 1.0}
        
        elif self.calibration_type == 'two_point':
            # Lineare Regression
            ref = self.reference_values
            meas = self.measured_values
            
            # y = mx + b wobei y=reference, x=measured
            factor = (ref[1] - ref[0]) / (meas[1] - meas[0])
            offset = ref[0] - (factor * meas[0])
            
            return {'offset': offset, 'factor': factor}
        
        else:
            # Multi-Point: Least-Squares
            import numpy as np
            
            meas = np.array(self.measured_values)
            ref = np.array(self.reference_values)
            
            # Lineare Regression
            coeffs = np.polyfit(meas, ref, 1)
            factor = coeffs[0]
            offset = coeffs[1]
            
            # R²-Berechnung
            predictions = factor * meas + offset
            ss_res = np.sum((ref - predictions) ** 2)
            ss_tot = np.sum((ref - np.mean(ref)) ** 2)
            r_squared = 1 - (ss_res / ss_tot)
            
            return {
                'offset': float(offset),
                'factor': float(factor),
                'r_squared': float(r_squared)
            }
```

### TimescaleDB-Downsampling-Strategie:

Alle Sensor-Rohdaten werden primär in TimescaleDB als Hypertable gespeichert.
ArangoDB-Observations bleiben als Metadaten-Graph (Sensor→Observation-Edges, Quality-Scores,
Alerts); die eigentlichen Zeitreihenwerte liegen in TimescaleDB.

```sql
-- Hypertable für Sensor-Rohdaten
CREATE TABLE sensor_readings (
    time        TIMESTAMPTZ NOT NULL,
    sensor_id   TEXT NOT NULL,
    parameter   TEXT NOT NULL,
    value       DOUBLE PRECISION NOT NULL,
    quality_score DOUBLE PRECISION DEFAULT 1.0,
    source      TEXT NOT NULL  -- 'ha_auto', 'mqtt_auto', 'manual', etc.
);
SELECT create_hypertable('sensor_readings', 'time');

-- Index für häufige Abfragen
CREATE INDEX idx_sensor_readings_sensor_param
    ON sensor_readings (sensor_id, parameter, time DESC);

-- Retention Policy: Rohdaten 90 Tage, danach nur Aggregate
SELECT add_retention_policy('sensor_readings', INTERVAL '90 days');

-- Continuous Aggregate: Stündliche Zusammenfassung
CREATE MATERIALIZED VIEW sensor_hourly
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 hour', time) AS bucket,
    sensor_id,
    parameter,
    AVG(value) AS avg_value,
    MIN(value) AS min_value,
    MAX(value) AS max_value,
    STDDEV(value) AS stddev_value,
    COUNT(*) AS sample_count,
    AVG(quality_score) AS avg_quality
FROM sensor_readings
GROUP BY bucket, sensor_id, parameter;

-- Refresh-Policy: stündlich aktualisieren
SELECT add_continuous_aggregate_policy('sensor_hourly',
    start_offset => INTERVAL '3 hours',
    end_offset   => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour');

-- Continuous Aggregate: Tägliche Zusammenfassung (inkl. DLI-Akkumulation)
CREATE MATERIALIZED VIEW sensor_daily
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 day', time) AS bucket,
    sensor_id,
    parameter,
    AVG(value) AS avg_value,
    MIN(value) AS min_value,
    MAX(value) AS max_value,
    STDDEV(value) AS stddev_value,
    COUNT(*) AS sample_count,
    -- DLI-Akkumulation: Summe der PPFD-Werte × Messintervall in Sekunden / 1e6
    -- Ergibt mol/m²/d bei parameter='ppfd' und regelmäßigem Messintervall
    SUM(CASE WHEN parameter = 'ppfd'
        THEN value * EXTRACT(EPOCH FROM '60 seconds'::interval) / 1e6
        ELSE 0 END) AS dli_mol_m2_d
FROM sensor_readings
GROUP BY bucket, sensor_id, parameter;

SELECT add_continuous_aggregate_policy('sensor_daily',
    start_offset => INTERVAL '3 days',
    end_offset   => INTERVAL '1 day',
    schedule_interval => INTERVAL '1 day');

-- Retention für Aggregate: stündlich 1 Jahr, täglich unbegrenzt
SELECT add_retention_policy('sensor_hourly', INTERVAL '365 days');
-- sensor_daily: keine Retention (dauerhaft aufbewahren)
```

**Downsampling-Stufen:**
| Datenebene | Granularität | Retention | Verwendung |
|-----------|-------------|-----------|------------|
| Rohdaten | Messintervall (10s-60s) | 90 Tage | Echtzeit-Dashboard, Anomalie-Erkennung |
| Stündlich | 1h-Aggregate | 1 Jahr | Trend-Analyse, 7-Tage-Charts |
| Täglich | 1d-Aggregate (+DLI) | Unbegrenzt | Langzeit-Vergleich, Saison-Überblick |

**DLI-Berechnung:** Der Daily Light Integral wird als Continuous Aggregate über die
tägliche PPFD-Summe berechnet (`dli_mol_m2_d`). Bei lückenhaften Daten (z.B. durch
Interpolation) wird der DLI-Wert mit dem Anteil der verfügbaren Datenpunkte skaliert
und ein `dli_confidence`-Flag gesetzt.

## 4. Authentifizierung & Autorisierung

> **Hinweis (SEC-H-001):** Dieser Abschnitt wurde nachträglich ergänzt, um die Auth-Anforderungen
> gemäß REQ-023 (Authentifizierung) und REQ-024 (Mandantenverwaltung) zu dokumentieren.

**Standardregel:** Alle Endpunkte dieses REQ erfordern Authentifizierung (JWT Bearer Token)
und Tenant-Mitgliedschaft, sofern nicht anders angegeben.

| Ressource/Endpoint-Gruppe | Lesen | Schreiben | Löschen |
|---------------------------|-------|-----------|---------|
| Sensor-Daten (Tenant-scoped) | Mitglied | Mitglied | Admin |
| Sensor-Konfiguration | Mitglied | Admin | Admin |
| HA-Integration-Config | Admin | Admin | Admin |
| Manuelle Messwert-Eingabe | — | Mitglied | — |

## 5. Abhängigkeiten

**Erforderliche externe Systeme:**
- Home Assistant (optional, für Auto-Mode)
- MQTT Broker (optional, z.B. Mosquitto)
- TimescaleDB (empfohlen für Zeitreihen)

**Erforderliche Module:**
- REQ-003 (Phasen): RequirementProfile für Soll-Ist-Vergleich
- REQ-002 (Standort): Location für Sensor-Zuordnung

**Wird benötigt von:**
- REQ-003 (Phasen): VPD-Berechnung, Klima-Validierung
- REQ-004 (Düngung): EC/pH für Nährlösungs-Kontrolle
- REQ-009 (Dashboard): Real-Time-Daten für Widgets
- REQ-010 (IPM): Klimadaten für Schädlings-Risiko-Modelle
- REQ-014 (Tankmanagement): **MITTEL** — Tank-Sensoren für automatische Zustandserfassung (pH, EC, Füllstand, Wassertemperatur)

**Python-Bibliotheken:**
- `requests` - HTTP für HA REST API
- `paho-mqtt` - MQTT Client
- `websocket-client` - HA WebSocket
- `psycopg2` / `asyncpg` - TimescaleDB-Client (PostgreSQL)

## 6. Akzeptanzkriterien

### Definition of Done (DoD):

- [ ] **Graceful Degradation:** System voll funktionsfähig ohne HA/Sensoren
- [ ] **HA-Integration:** REST API + WebSocket für 5+ Sensor-Typen
- [ ] **MQTT-Support:** Subscription auf Topics mit JSON-Parsing
- [ ] **Manuelle Eingabe:** Web-Formular mit Plausibilitätsprüfung
- [ ] **Datenquellen-Kennzeichnung:** UI zeigt deutlich Auto vs. Manual
- [ ] **Quality-Scoring:** Jede Observation hat berechneten Quality-Score
- [ ] **Historical Trending:** 30 Tage Verlauf mit Chart-Visualisierung
- [ ] **Multi-Sensor-Aggregation:** Durchschnitt bei 2+ Sensoren pro Parameter/Location
- [ ] **Sensor-Health-Monitoring:** Automatische Erkennung von Ausfällen
- [ ] **Auto-Task-Generation:** Manual-Measurement-Task bei Ausfall >24h
- [ ] **Interpolation:** Kurze Lücken (<2h) werden interpoliert
- [ ] **Kalibrierungs-Workflow:** UI für 1-Point, 2-Point, Multi-Point Calibration
- [ ] **Kalibrierungs-Erinnerung:** Alert bei >90 Tage seit letzter Kalibration
- [ ] **Anomalie-Erkennung:** Statistische Ausreißer-Erkennung (Z-Score)
- [ ] **Rate-of-Change-Validierung:** Warnung bei unplausiblen Sprüngen
- [ ] **Export-Funktion:** CSV-Export für externe Analysen
- [ ] **Leaf-VPD:** Blatttemperatur-basierte VPD-Berechnung (leaf_temp ParameterType)
- [ ] **Erweiterte ParameterTypes:** leaf_temp, substrate_temp, water_temp, do, orp, flow_rate, air_velocity
- [ ] **Zweistufige Anomalie-Schwelle:** Z-Score > 3.0 = warning, > 4.0 = critical; gleitendes Fenster konfigurierbar
- [ ] **Phasenabhängige Alerts:** PhaseAlertProfile mit dynamischen Schwellenwerten aus REQ-003 PhaseControlProfile
- [ ] **Sensorplatzierung:** mounting_height_cm, mounting_position, representative_area_m2 als Qualitätsfaktoren
- [ ] **Parameterspezifische Ausfall-Schwellen:** Schnell-veränderliche Parameter (temp, VPD: 2h) vs. träge (EC, soil_moisture: 6-8h)
- [ ] **Parameterspezifische Interpolation:** ppfd max 0.5h, soil_moisture bis 6h, temp/humidity 2h
- [ ] **Lichtspektrum-Parameter:** r_fr_ratio, blue_fraction, par_spectrum in ParameterType
- [ ] **Substratfeuchte-Differenzierung:** soil_moisture_method + soil_moisture_unit pro Sensor, substrate_type_key
- [ ] **TimescaleDB-Downsampling:** Hypertable + Continuous Aggregates (stündlich, täglich), Retention 90d/1y/unbegrenzt
- [ ] **DLI-Akkumulation:** Daily Light Integral als Continuous Aggregate über PPFD-Summe
- [ ] **Manual Quality-Score:** Differenziert nach Gerätekalibrierung und Gerätegenauigkeit
- [ ] **Entity-ID-Inferenz:** Nutzerbestätigung beim erstmaligen Sensor-Onboarding empfohlen
- [ ] **Alert-System:** Konfigurierbare Min/Max-Schwellenwerte
- [ ] **Battery-Monitoring:** Warnung bei <20% Batterie (wenn verfügbar)
- [ ] **Offline-Modus:** Mobile-App speichert Eingaben lokal und synct später

### Testszenarien:

**Szenario 1: HA-Sensor-Integration**
```
GIVEN: HA läuft mit sensor.growzelt_temperature (DHT22)
WHEN: System ruft get_sensor_state('sensor.growzelt_temperature')
THEN:
  - SensorReading mit value=24.5°C, source='ha_auto' wird erstellt
  - timestamp = HA last_updated
  - quality_score = 1.0 (Auto-Source, aktuelle Daten)
  - Observation wird in ArangoDB gespeichert
```

**Szenario 2: Sensor-Ausfall mit Auto-Task**
```
GIVEN: Temperatur-Sensor seit 25h offline
WHEN: Stündlicher Health-Check läuft
THEN:
  - SensorHealth.status = 'offline'
  - Task "Manuelle Temperatur Messung" wird generiert
  - Task.priority = 'high', Task.due_date = heute
  - Alert an Dashboard: "Sensor offline - manuelle Messung erforderlich"
```

**Szenario 3: Manuelle Eingabe mit Validierung**
```
GIVEN: Letzter pH-Wert war 6.0 (vor 2h)
WHEN: Nutzer gibt manuell pH 4.5 ein (Änderung: -1.5)
THEN:
  - ManualInputValidator.validate_manual_entry()
  - suspicious = True (>0.5 pH-Änderung in 2h ungewöhnlich)
  - UI zeigt Warnung: "Ungewöhnlich starke Änderung - bitte bestätigen"
  - confirm_required = True
  - Nach Bestätigung: Observation mit quality_score = 0.6 gespeichert
```

**Szenario 4: Multi-Sensor-Aggregation**
```
GIVEN: 3 Temperatur-Sensoren in einem Raum:
  - Sensor A: 24.0°C (quality_score: 1.0)
  - Sensor B: 24.5°C (quality_score: 0.9)
  - Sensor C: 23.8°C (quality_score: 0.8)
WHEN: System aggregiert aktuelle Raumtemperatur
THEN:
  - Gewichteter Durchschnitt: (24.0*1.0 + 24.5*0.9 + 23.8*0.8) / (1.0+0.9+0.8) = 24.2°C
  - confidence = 'high' (3 Sensoren)
  - Einzelwerte bleiben verfügbar für Debugging
```

**Szenario 5: pH-Sensor Kalibrierung (2-Point)**
```
GIVEN: pH-Sensor zeigt 7.2 in pH 7.0 Pufferlösung
       pH-Sensor zeigt 4.3 in pH 4.0 Pufferlösung
WHEN: Nutzer führt 2-Point Calibration durch
THEN:
  - calculate_calibration_params():
    - factor = (7.0 - 4.0) / (7.2 - 4.3) = 1.034
    - offset = 7.0 - (1.034 * 7.2) = -0.445
  - SensorCalibration-Node erstellt
  - Sensor.calibration_offset = -0.445
  - Sensor.calibration_factor = 1.034
  - Nächste Kalibrierung fällig: in 90 Tagen
```

**Szenario 6: Interpolation bei kurzem Ausfall**
```
GIVEN: EC-Sensor Werte:
  - 10:00 → 1.8 mS
  - [Lücke: 10:00-12:00]
  - 12:00 → 2.0 mS
WHEN: interpolate_missing_values(gap_start=10:00, gap_end=12:00)
THEN:
  - Generiere stündliche Interpolations-Punkte:
    - 11:00 → 1.9 mS (source='interpolated', quality_score=0.6)
  - Lineare Interpolation zwischen bekannten Punkten
  - UI zeigt gestrichelte Linie für interpolierte Werte
```

**Szenario 7: Anomalie-Erkennung**
```
GIVEN: Luftfeuchte letzte 7 Tage: Mittelwert=55%, Stddev=3%
WHEN: Neuer Wert: 75% (Z-Score = (75-55)/3 = 6.67)
THEN:
  - Observation.outlier = True
  - quality_score *= 0.5 (Penalty für Ausreißer)
  - Alert: "Statistischer Ausreißer erkannt - Sensor prüfen"
  - Dashboard zeigt roten Marker
```

---

**Hinweise für RAG-Integration:**
- Keywords: Sensorik, Home Assistant, MQTT, Kalibrierung, Quality-Score, Anomalie-Erkennung, Interpolation, Leaf-VPD, Blatttemperatur, TimescaleDB, Downsampling, Continuous Aggregates
- Fachbegriffe: PPFD, DLI, Tensiometer, TDS, Z-Score, Lineare Regression, WebSocket, Leaf-VPD, R:FR-Ratio, Phytochrom, Dissolved Oxygen, ORP, Hypertable, Retention Policy, PhaseAlertProfile, VWC, TDR, Saugspannung, PAR-Spektrum
- Verknüpfung: Zentral für REQ-003 (VPD, phasenabhängige Schwellenwerte, PhaseAlertProfile), REQ-004 (EC/pH), REQ-009 (Dashboard), REQ-010 (IPM-Risiko), REQ-018 (Aktorik-Rückkopplung), REQ-019 (Substrat-Temperatur, substrate_type_key)
- Protokolle: REST API, MQTT, WebSocket, Modbus
- Datenbank: TimescaleDB Hypertables (Rohdaten 90d, stündliche Aggregate 1y, tägliche Aggregate unbegrenzt)
