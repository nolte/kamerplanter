# Spezifikation: REQ-005 - Hybrid-Sensorik

```yaml
ID: REQ-005
Titel: Hybrid-Sensorik & Home Assistant Integration
Kategorie: Monitoring
Fokus: Beides
Technologie: Python, Home Assistant API, MQTT, InfluxDB/TimescaleDB
Status: Entwurf
Version: 2.0 (Maximal Erweitert)
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
- Spektrum-Analyse - Rot/Blau/Far-Red-Verhältnis
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

## 2. GraphDB-Modellierung

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
```cypher
(:Sensor)-[:LOCATED_AT]->(:Slot|:Location)
(:Sensor)-[:RECORDED]->(:Observation)
(:Observation)-[:VALIDATES]->(:RequirementProfile)
(:Observation)-[:TRIGGERED]->(:Alert)
(:Sensor)-[:LAST_CALIBRATED]->(:SensorCalibration)
(:Sensor)-[:HAS_HEALTH_STATUS]->(:SensorHealth)
(:Observation)-[:AGGREGATED_INTO]->(:AggregatedMetric)
(:Sensor)-[:REPLACED_BY {replacement_date: datetime}]->(:Sensor)
(:ManualEntry)-[:CONFIRMS]->(:Observation)  // Manuelle Verifizierung von Auto-Werten
(:Alert)-[:RESOLVED_BY_ACTION]->(:Task)
(:Sensor)-[:PART_OF_SYSTEM]->(:MonitoringSystem)  // z.B. "Growzelt_1_Climate"
```

### Cypher-Beispiellogik:

**Aktuelle Werte mit Fallback-Hierarchie:**
```cypher
MATCH (location:Location {id: $loc_id})<-[:LOCATED_AT]-(sensor:Sensor)
WHERE sensor.parameter = $parameter

// Versuche automatische Readings
OPTIONAL MATCH (sensor)-[:RECORDED]->(auto_obs:Observation)
WHERE auto_obs.source IN ['ha_auto', 'mqtt_auto', 'modbus_auto']
  AND auto_obs.timestamp > datetime() - duration('PT15M')
WITH sensor, auto_obs
ORDER BY auto_obs.timestamp DESC

// Fallback auf manuelle Eingaben wenn kein Auto-Wert
OPTIONAL MATCH (sensor)-[:RECORDED]->(manual_obs:Observation)
WHERE manual_obs.source = 'manual'
  AND manual_obs.timestamp > datetime() - duration('PT1H')
WITH sensor, 
     COLLECT(auto_obs)[0] AS latest_auto,
     COLLECT(manual_obs)[0] AS latest_manual

WITH sensor,
     COALESCE(latest_auto, latest_manual) AS latest_obs

RETURN sensor.sensor_id,
       sensor.parameter,
       CASE 
         WHEN latest_obs IS NULL THEN 'NO_DATA'
         ELSE latest_obs.value
       END AS current_value,
       CASE
         WHEN latest_obs IS NULL THEN null
         ELSE latest_obs.source
       END AS source,
       CASE
         WHEN latest_obs IS NULL THEN null
         ELSE duration.between(latest_obs.timestamp, datetime()).inMinutes
       END AS age_minutes,
       CASE
         WHEN latest_obs IS NULL THEN 'CRITICAL'
         WHEN duration.between(latest_obs.timestamp, datetime()).inMinutes > 60 THEN 'WARNING'
         ELSE 'OK'
       END AS data_freshness
```

**Sensor-Health-Check mit Auto-Task-Generierung:**
```cypher
MATCH (sensor:Sensor)-[:HAS_HEALTH_STATUS]->(health:SensorHealth)
WHERE health.status = 'offline' 
  OR health.consecutive_failures > 5
  OR duration.between(health.last_successful_reading, datetime()).inHours > 24

// Prüfe ob bereits Manual-Task existiert
OPTIONAL MATCH (sensor)-[:LOCATED_AT]->(location)-[:HAS_SLOT]->(slot)
        <-[:PLACED_IN]-(plant:PlantInstance)-[:HAS_TASK]->(task:Task)
WHERE task.status = 'pending' 
  AND task.category = 'manual_measurement'
  AND task.due_date >= date()

WITH sensor, health, task, location

// Erstelle Task nur wenn noch keiner existiert
WHERE task IS NULL

// Generiere Manual-Measurement Task
CREATE (new_task:Task {
  task_id: randomUUID(),
  name: 'Manual ' + sensor.parameter + ' Messung erforderlich',
  category: 'manual_measurement',
  instruction: 'Sensor ' + sensor.sensor_id + ' offline seit ' + 
               duration.between(health.last_successful_reading, datetime()).inHours + 'h. ' +
               'Bitte manuell messen.',
  due_date: date(),
  priority: 'high',
  status: 'pending',
  created_at: datetime()
})

WITH sensor, new_task, location
MATCH (location)<-[:HAS_SLOT]-(loc_parent)
MATCH (loc_parent)<-[:PLACED_IN]-(plant:PlantInstance)

CREATE (plant)-[:HAS_TASK]->(new_task)

RETURN sensor.sensor_id AS failed_sensor,
       new_task.task_id AS generated_task_id,
       'Manual measurement task created' AS action
```

**Multi-Sensor-Aggregation für Redundanz:**
```cypher
MATCH (location:Location {id: $loc_id})<-[:LOCATED_AT]-(sensor:Sensor {parameter: $parameter})
      -[:RECORDED]->(obs:Observation)
WHERE obs.timestamp > datetime() - duration('PT15M')
  AND obs.validated = true

WITH sensor, obs
ORDER BY obs.timestamp DESC

WITH sensor, COLLECT(obs)[0] AS latest_obs

WHERE latest_obs IS NOT NULL

WITH COLLECT({
  sensor_id: sensor.sensor_id,
  value: latest_obs.value,
  timestamp: latest_obs.timestamp,
  quality: latest_obs.quality_score
}) AS readings

// Berechne gewichteten Durchschnitt basierend auf Quality-Score
UNWIND readings AS reading
WITH readings,
     SUM(reading.value * reading.quality) AS weighted_sum,
     SUM(reading.quality) AS total_quality

RETURN {
  aggregated_value: weighted_sum / total_quality,
  sensor_count: SIZE(readings),
  individual_readings: readings,
  aggregation_method: 'quality_weighted_average',
  confidence: CASE
    WHEN SIZE(readings) >= 3 THEN 'high'
    WHEN SIZE(readings) = 2 THEN 'medium'
    ELSE 'low'
  END
} AS result
```

**Trend-Analyse und Anomalie-Erkennung:**
```cypher
MATCH (sensor:Sensor {sensor_id: $sensor_id})-[:RECORDED]->(obs:Observation)
WHERE obs.timestamp > datetime() - duration('P7D')
  AND obs.validated = true

WITH sensor, obs
ORDER BY obs.timestamp ASC

WITH sensor,
     COLLECT(obs.value) AS values,
     COLLECT(obs.timestamp) AS timestamps

// Berechne statistische Metriken
WITH sensor, values, timestamps,
     REDUCE(s = 0.0, val IN values | s + val) / SIZE(values) AS mean,
     SIZE(values) AS n

WITH sensor, values, timestamps, mean, n,
     SQRT(REDUCE(s = 0.0, val IN values | s + (val - mean)^2) / n) AS stddev

// Identifiziere Ausreißer (>2 Standardabweichungen)
UNWIND RANGE(0, SIZE(values)-1) AS idx
WITH sensor, values, timestamps, mean, stddev,
     idx,
     values[idx] AS value,
     timestamps[idx] AS timestamp,
     ABS(values[idx] - mean) / stddev AS z_score

WHERE z_score > 2.0

RETURN sensor.parameter AS parameter,
       {
         timestamp: timestamp,
         value: value,
         z_score: z_score,
         deviation_from_mean: value - mean,
         is_outlier: true
       } AS outlier,
       mean,
       stddev

ORDER BY z_score DESC
```

**Kalibrierungs-Historie und Drift-Erkennung:**
```cypher
MATCH (sensor:Sensor {sensor_id: $sensor_id})-[:LAST_CALIBRATED]->(cal:SensorCalibration)

// Hole alle vorherigen Kalibrierungen
OPTIONAL MATCH (sensor)-[:LAST_CALIBRATED*..10]->(prev_cal:SensorCalibration)

WITH sensor, cal, COLLECT(DISTINCT prev_cal) AS history
ORDER BY cal.calibration_date DESC

WITH sensor, cal, 
     [c IN history | c.offset_calculated] AS offset_history,
     [c IN history | c.calibration_date] AS date_history

// Berechne Drift-Rate
WITH sensor, cal, offset_history, date_history,
     CASE 
       WHEN SIZE(offset_history) >= 2 
       THEN (offset_history[0] - offset_history[-1]) / 
            duration.between(date_history[-1], date_history[0]).inDays
       ELSE 0
     END AS drift_per_day

RETURN sensor.parameter,
       cal.calibration_date AS last_calibrated,
       duration.between(cal.calibration_date, datetime()).inDays AS days_since_calibration,
       cal.offset_calculated AS current_offset,
       drift_per_day,
       CASE
         WHEN duration.between(cal.calibration_date, datetime()).inDays > 90 
         THEN 'OVERDUE'
         WHEN ABS(drift_per_day) > 0.01 
         THEN 'HIGH_DRIFT'
         ELSE 'OK'
       END AS calibration_status,
       offset_history AS historical_offsets
```

## 3. Technische Umsetzung (Python)

### Logik-Anforderungen:

**1. Sensor Reading mit Quality Scoring:**
```python
from pydantic import BaseModel, Field, validator
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
        'ec': (0, 5),
        'ph': (0, 14),
        'ppfd': (0, 2000),
        'co2': (200, 5000),
        'soil_moisture': (0, 100),
        'water_level': (0, 100)
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
        source_scores = {
            'ha_auto': 1.0,
            'mqtt_auto': 0.95,
            'modbus_auto': 0.95,
            'manual': 0.85,
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
                'temp': 0.5,      # 0.5°C/min
                'humidity': 2.0,   # 2%/min
                'ec': 0.05,       # 0.05 mS/min
                'ph': 0.1,        # 0.1 pH/min
                'co2': 50.0       # 50 ppm/min
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
        """Inferiert Parameter-Typ aus Entity-ID und Unit"""
        
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
    
    # Konfigurierbare Schwellenwerte
    MAX_AGE_CRITICAL_HOURS = 24
    MAX_AGE_WARNING_HOURS = 6
    MAX_AGE_INTERPOLATION_HOURS = 2
    
    def __init__(self, neo4j_driver):
        self.driver = neo4j_driver
    
    def check_sensor_health(
        self,
        sensor_id: str,
        last_reading_time: Optional[datetime]
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
        
        if age_hours > self.MAX_AGE_CRITICAL_HOURS:
            return {
                'status': 'CRITICAL',
                'action': 'CREATE_MANUAL_TASK',
                'message': f'Sensor seit {age_hours:.1f}h offline - Manuelle Messung erforderlich',
                'age_hours': age_hours,
                'task_priority': 'high',
                'suggested_measurement_frequency': 'daily'
            }
        
        elif age_hours > self.MAX_AGE_WARNING_HOURS:
            return {
                'status': 'WARNING',
                'action': 'NOTIFY_USER',
                'message': f'Sensor seit {age_hours:.1f}h ohne Update - bitte prüfen',
                'age_hours': age_hours,
                'check_battery': True,
                'check_connectivity': True
            }
        
        elif age_hours > self.MAX_AGE_INTERPOLATION_HOURS:
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
        with self.driver.session() as session:
            # Hole Wert vor und nach der Lücke
            result = session.run("""
                MATCH (s:Sensor {sensor_id: $sensor_id})-[:RECORDED]->(obs:Observation)
                WHERE obs.timestamp < $gap_start OR obs.timestamp > $gap_end
                WITH s, obs
                ORDER BY obs.timestamp
                WITH s,
                     [o IN COLLECT(obs) WHERE o.timestamp < $gap_start][-1] AS before_obs,
                     [o IN COLLECT(obs) WHERE o.timestamp > $gap_end][0] AS after_obs
                RETURN before_obs, after_obs
            """, sensor_id=sensor_id, gap_start=gap_start, gap_end=gap_end).single()
            
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
        with self.driver.session() as session:
            result = session.run("""
                MATCH (location:Location {id: $location_id})
                
                // Erstelle Task
                CREATE (task:Task {
                    task_id: randomUUID(),
                    name: 'Manuelle ' + $parameter + ' Messung',
                    category: 'manual_measurement',
                    instruction: 'Sensor ' + $sensor_id + ' offline. Bitte ' + $parameter + ' manuell messen und eingeben.',
                    due_date: date(),
                    priority: 'high',
                    status: 'pending',
                    created_at: datetime(),
                    requires_photo: false,
                    estimated_duration_minutes: 5
                })
                
                // Verknüpfe mit Pflanzen an diesem Standort
                WITH task, location
                MATCH (location)-[:HAS_SLOT]->(slot:Slot)<-[:PLACED_IN]-(plant:PlantInstance)
                CREATE (plant)-[:HAS_TASK]->(task)
                
                RETURN task.task_id AS task_id
            """, sensor_id=sensor_id, parameter=parameter, location_id=location_id).single()
            
            return result['task_id'] if result else None
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
from pydantic import BaseModel, Field, validator
from datetime import datetime, date

SensorType = Literal['physical', 'virtual', 'calculated']
ParameterType = Literal['temp', 'humidity', 'ec', 'ph', 'ppfd', 'co2', 'soil_moisture', 'water_level', 'vpd']
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
    sensor_model: Optional[str] = None
    accuracy_percent: Optional[float] = Field(None, ge=0, le=100)
    
    @validator('calibration_factor')
    def validate_reasonable_calibration(cls, v):
        if not (0.5 <= v <= 2.0):
            raise ValueError("Calibration factor außerhalb vernünftigem Bereich (0.5-2.0)")
        return v
    
    @validator('ha_entity_id')
    def validate_ha_entity(cls, v):
        if v and not v.startswith(('sensor.', 'binary_sensor.')):
            raise ValueError("HA Entity muss mit 'sensor.' oder 'binary_sensor.' beginnen")
        return v

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
    
    @validator('measured_values')
    def validate_value_count_match(cls, v, values):
        ref_vals = values.get('reference_values', [])
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

## 4. Abhängigkeiten

**Erforderliche externe Systeme:**
- Home Assistant (optional, für Auto-Mode)
- MQTT Broker (optional, z.B. Mosquitto)
- TimescaleDB oder InfluxDB (empfohlen für Zeitreihen)

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
- `influxdb-client` oder `timescaledb` - Zeitreihen-DB

## 5. Akzeptanzkriterien

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
  - Observation wird in Neo4j gespeichert
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
- Keywords: Sensorik, Home Assistant, MQTT, Kalibrierung, Quality-Score, Anomalie-Erkennung, Interpolation
- Fachbegriffe: PPFD, DLI, Tensiometer, TDS, Z-Score, Lineare Regression, WebSocket
- Verknüpfung: Zentral für REQ-003 (VPD), REQ-004 (EC/pH), REQ-009 (Dashboard), REQ-010 (IPM-Risiko)
- Protokolle: REST API, MQTT, WebSocket, Modbus
