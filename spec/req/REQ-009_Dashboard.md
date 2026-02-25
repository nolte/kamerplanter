# Spezifikation: REQ-009 - Dashboard

```yaml
ID: REQ-009
Titel: Zentrales Monitoring-Dashboard & Analytics
Kategorie: Visualisierung
Fokus: Beides
Technologie: FastAPI, React, GraphDB (Neo4j), Plotly/D3.js, WebSocket
Status: Entwurf
Version: 2.0 (Maximal Erweitert)
```

## 1. Business Case

**User Story:** "Als Gärtner möchte ich auf einen Blick sehen: Welche Pflanzen brauchen Aufmerksamkeit, welche Tasks sind fällig, wie ist das Klima, was ist im Lager und welche Trends zeigen sich - alles mobil-optimiert für Nutzung vor Ort im Growroom."

**Beschreibung:**
Das System implementiert ein hochgradig konfigurierbares, Echtzeit-Dashboard mit modularem Widget-System für umfassendes Monitoring und datengetriebene Entscheidungsfindung:

**Dashboard-Philosophie:**
- **Information at a Glance:** Wichtigste Metriken in 3 Sekunden erfassbar
- **Actionable Insights:** Jedes Widget führt zu konkreten Handlungen
- **Mobile-First:** Touch-optimiert für Tablet/Smartphone im Growroom
- **Real-Time:** WebSocket-Updates ohne Page-Refresh
- **Customizable:** Drag & Drop Widget-Anordnung
- **Role-Based:** Verschiedene Views für Anfänger/Fortgeschrittene/Experten

**Dashboard-Typen:**

**1. Overview Dashboard (Hauptansicht):**
- **Plant Status Grid:** Visuelle Übersicht aller Pflanzen (Farbe = Phase)
- **Climate Summary:** VPD, Temp, RLF - aktuell vs. Soll
- **Task Queue:** Top 5 fällige/überfällige Tasks
- **Alert Center:** Kritische Warnungen prominent
- **Quick Stats:** Pflanzen gesamt, in Blüte, Tage bis Ernte

**2. Climate Dashboard:**
- **VPD Calculator & Heatmap:** Live-Berechnung mit Zielbereich
- **Temperature Trends:** 24h/7d/30d Charts
- **Humidity Stability:** Schwankungen und Extremwerte
- **DLI Tracker:** Daily Light Integral Akkumulation
- **CO2 Monitoring:** ppm mit Photosynthese-Effizienz
- **Climate Alerts:** Historie aller Schwellenwert-Überschreitungen

**3. Plant Health Dashboard:**
- **Growth Curves:** Höhe/Breite über Zeit pro Pflanze
- **Phase Distribution:** Wie viele in Vegi/Blüte/Ernte
- **Health Scores:** Aggregierte Bewertung pro Pflanze
- **Deficiency Detection:** NPK-Mangel-Indikatoren
- **Pest Pressure Heatmap:** Befallsstärke nach Location

**4. Harvest & Yield Dashboard:**
- **Harvest Calendar:** Nächste 4 Wochen Ernten
- **Yield Forecasting:** Geschätzte Erträge basierend auf Historie
- **Batch Quality Distribution:** A+/A/B/C-Verteilung
- **Dry Weight Tracker:** Trocknungs-Fortschritt aller aktiven Batches
- **Storage Inventory:** Aktueller Bestand mit Haltbarkeit
- **Yield Analytics:** Gram/m²/Tag, ROI, Efficiency-Scores

**5. Resource Dashboard:**
- **Water Consumption:** Liter/Tag, Kosten-Tracking
- **Energy Usage:** kWh für Licht/Klima/Pumpen
- **Fertilizer Stock:** Verbleibender Vorrat in Wochen
- **Substrate Utilization:** Wiederverwendungs-Tracker
- **Cost per Gram:** Break-Even-Analyse

**6. Analytics Dashboard:**
- **Strain Performance Comparison:** Yields, Cycle-Zeit, Qualität
- **Seasonal Trends:** Erfolgsrate nach Jahreszeit
- **Correlation Analysis:** Klima vs. Yield
- **Learning Curves:** Verbesserung über Zeit
- **Optimization Suggestions:** ML-basierte Empfehlungen

**Widget-Kategorien:**

**Status-Widgets:**
- Plant Grid (Kanban-Style)
- Task List (Sortierbar)
- Alert Feed (Real-Time)
- System Health (All-Up-Status)

**Chart-Widgets:**
- Line Charts (Zeitreihen)
- Bar Charts (Vergleiche)
- Heatmaps (Geo-Daten, VPD)
- Scatter Plots (Korrelationen)
- Pie/Donut Charts (Verteilungen)

**Metric-Widgets:**
- KPI Cards (Einzelwerte mit Trend)
- Gauges (VPD, RLF, Temp)
- Progress Bars (Tasks, Drying, Curing)
- Counters (Pflanzen, Batches, Alerts)

**Interactive-Widgets:**
- VPD Calculator (Input: Temp/RLF → Output: VPD)
- EC Calculator (NPK → EC)
- Harvest Date Estimator (Phase + DLI → Date)
- Light Schedule Visualizer (Sunrise/Sunset)

**Design-Prinzipien:**

**Color-Coding:**
- 🟢 **Grün:** Optimal, keine Action nötig
- 🟡 **Gelb:** Attention, Überwachung erhöhen
- 🟠 **Orange:** Warning, bald Action nötig
- 🔴 **Rot:** Critical, sofortige Action erforderlich
- 🔵 **Blau:** Informational, neutral

**Typography:**
- **Headlines:** Bold, große Schrift für Metriken
- **Labels:** Klein, dezent für Beschreibungen
- **Alerts:** Uppercase, fett für Warnungen

**Responsiveness:**
- **Desktop (>1200px):** 3-4 Spalten, alle Widgets sichtbar
- **Tablet (768-1200px):** 2 Spalten, scrollbar
- **Mobile (<768px):** 1 Spalte, geswiped zwischen Dashboards

**Performance-Optimierung:**
- **Lazy Loading:** Widgets laden nur wenn sichtbar
- **Data Aggregation:** Backend gruppiert Daten vor Übertragung
- **Caching:** Redis für häufig abgerufene Metriken
- **WebSocket:** Nur Deltas werden übertragen, nicht komplette Datasets

## 2. GraphDB-Modellierung

### Nodes:
- **`:Dashboard`** - Dashboard-Konfiguration
  - Properties:
    - `dashboard_id: str`
    - `dashboard_name: str`
    - `dashboard_type: Literal['overview', 'climate', 'plant_health', 'harvest', 'resource', 'analytics', 'custom']`
    - `is_default: bool`
    - `created_by: str`
    - `created_at: datetime`
    - `last_modified: datetime`
    - `is_public: bool` (Teilbar mit anderen Nutzern)

- **`:Widget`** - Widget-Instanz
  - Properties:
    - `widget_id: str`
    - `widget_type: str` (z.B. "plant_grid", "vpd_gauge", "task_list")
    - `title: str`
    - `position_x: int` (Grid-Position)
    - `position_y: int`
    - `size_width: int` (Grid-Einheiten)
    - `size_height: int`
    - `config: dict` (Widget-spezifische Einstellungen)
    - `refresh_interval_seconds: int`
    - `data_source: str` (Cypher-Query oder API-Endpoint)
    - `visible: bool`

- **`:WidgetTemplate`** - Vordefinierte Widget-Typen
  - Properties:
    - `template_id: str`
    - `template_name: str`
    - `category: str` (z.B. "climate", "plants", "harvest")
    - `description: str`
    - `default_config: dict`
    - `required_data_sources: list[str]`
    - `preview_image_url: Optional[str]`

- **`:Metric`** - Berechnete KPI
  - Properties:
    - `metric_id: str`
    - `metric_name: str` (z.B. "avg_vpd_7d", "total_yield_current_cycle")
    - `value: float`
    - `unit: str`
    - `calculated_at: datetime`
    - `trend: Literal['up', 'down', 'stable']`
    - `trend_percent: float`

- **`:Alert`** - Dashboard-Alert
  - Properties:
    - `alert_id: str`
    - `severity: Literal['info', 'warning', 'critical']`
    - `message: str`
    - `triggered_at: datetime`
    - `acknowledged: bool`
    - `acknowledged_at: Optional[datetime]`
    - `source: str` (z.B. "climate_monitor", "task_scheduler")
    - `actionable: bool`
    - `action_url: Optional[str]`

- **`:UserPreference`** - Nutzer-spezifische Einstellungen
  - Properties:
    - `user_id: str`
    - `preferred_dashboard: str`
    - `theme: Literal['light', 'dark', 'auto']`
    - `default_view: str`
    - `notification_settings: dict`
    - `unit_preferences: dict` (z.B. {"temp": "celsius", "distance": "cm"})

- **`:DataSnapshot`** - Historische Snapshots für Trends
  - Properties:
    - `snapshot_id: str`
    - `snapshot_type: str` (z.B. "hourly_climate", "daily_summary")
    - `timestamp: datetime`
    - `data: dict` (Aggregierte Daten)

### Edges:
```cypher
(:Dashboard)-[:CONTAINS {position: int}]->(:Widget)
(:Widget)-[:BASED_ON]->(:WidgetTemplate)
(:Widget)-[:DISPLAYS]->(:Metric)
(:Dashboard)-[:SHOWS_ALERTS]->(:Alert)
(:User)-[:HAS_PREFERENCES]->(:UserPreference)
(:User)-[:OWNS]->(:Dashboard)
(:Dashboard)-[:USES_SNAPSHOT]->(:DataSnapshot)
(:Alert)-[:TRIGGERED_BY]->(:PlantInstance|:StorageLocation|:Sensor)
```

### Cypher-Beispiellogik:

**Dashboard-Übersicht (Overview Widget Data):**
```cypher
// Aggregiere Key-Metriken für Overview Dashboard
MATCH (plant:PlantInstance)
OPTIONAL MATCH (plant)-[:CURRENT_PHASE]->(phase:GrowthPhase)
OPTIONAL MATCH (plant)-[:HAS_TASK]->(task:Task {status: 'pending'})
WHERE task.due_date <= date()
OPTIONAL MATCH (alert:Alert {acknowledged: false})
      <-[:TRIGGERED]-(plant)

WITH 
  COUNT(DISTINCT plant) AS total_plants,
  COUNT(DISTINCT CASE WHEN phase.name IN ['flowering', 'early_flowering', 'late_flowering'] THEN plant END) AS plants_in_flower,
  COUNT(DISTINCT CASE WHEN phase.allows_harvest = true THEN plant END) AS plants_ready_harvest,
  COUNT(DISTINCT task) AS tasks_due,
  COUNT(DISTINCT CASE WHEN alert.severity = 'critical' THEN alert END) AS critical_alerts,
  COUNT(DISTINCT CASE WHEN alert.severity = 'warning' THEN alert END) AS warning_alerts

// Berechne durchschnittliche Tage bis Ernte
MATCH (p:PlantInstance)-[:CURRENT_PHASE]->(phase:GrowthPhase)
WHERE phase.allows_harvest = false
OPTIONAL MATCH (p)-[:BELONGS_TO_SPECIES]->(species:Species)
      -[:HAS_GROWTH_PHASE]->(harvest_phase:GrowthPhase)
WHERE harvest_phase.allows_harvest = true

WITH total_plants, plants_in_flower, plants_ready_harvest, 
     tasks_due, critical_alerts, warning_alerts,
     AVG(harvest_phase.typical_duration_days - phase.typical_duration_days) AS avg_days_to_harvest

// Hole aktuelle Klima-Daten
MATCH (location:Location)-[:HAS_SLOT]->(slot:Slot)
OPTIONAL MATCH (location)<-[:LOCATED_AT]-(sensor:Sensor {parameter: 'temp'})
      -[:RECORDED]->(temp_obs:Observation)
WHERE temp_obs.timestamp > datetime() - duration('PT15M')

WITH total_plants, plants_in_flower, plants_ready_harvest,
     tasks_due, critical_alerts, warning_alerts, avg_days_to_harvest,
     AVG(temp_obs.value) AS current_temp

OPTIONAL MATCH (sensor2:Sensor {parameter: 'humidity'})-[:RECORDED]->(rh_obs:Observation)
WHERE rh_obs.timestamp > datetime() - duration('PT15M')

WITH total_plants, plants_in_flower, plants_ready_harvest,
     tasks_due, critical_alerts, warning_alerts, avg_days_to_harvest,
     current_temp, AVG(rh_obs.value) AS current_rh

RETURN {
  plants: {
    total: total_plants,
    in_flower: plants_in_flower,
    ready_harvest: plants_ready_harvest,
    health_status: CASE
      WHEN critical_alerts > 0 THEN 'critical'
      WHEN warning_alerts > 0 THEN 'warning'
      ELSE 'healthy'
    END
  },
  tasks: {
    due_count: tasks_due,
    status: CASE
      WHEN tasks_due > 10 THEN 'overloaded'
      WHEN tasks_due > 5 THEN 'busy'
      ELSE 'manageable'
    END
  },
  alerts: {
    critical: critical_alerts,
    warning: warning_alerts,
    total: critical_alerts + warning_alerts
  },
  climate: {
    temperature_c: round(current_temp, 1),
    humidity_percent: round(current_rh, 0),
    vpd_kpa: round((1 - current_rh/100) * 0.61078 * exp((17.27 * current_temp)/(current_temp + 237.3)), 2),
    status: CASE
      WHEN current_temp < 18 OR current_temp > 28 THEN 'warning'
      WHEN current_rh < 40 OR current_rh > 70 THEN 'warning'
      ELSE 'ok'
    END
  },
  forecast: {
    avg_days_to_harvest: round(avg_days_to_harvest, 0)
  }
} AS overview
```

**Plant Grid Widget (Kanban-Style):**
```cypher
MATCH (plant:PlantInstance)
OPTIONAL MATCH (plant)-[:CURRENT_PHASE]->(phase:GrowthPhase)
OPTIONAL MATCH (plant)-[:PLACED_IN]->(slot:Slot)<-[:HAS_SLOT]-(location:Location)
OPTIONAL MATCH (plant)-[:HAS_TASK]->(task:Task {status: 'pending'})
WHERE task.due_date <= date()
OPTIONAL MATCH (plant)<-[:TRIGGERED]-(alert:Alert {acknowledged: false})

WITH plant, phase, location, slot,
     COUNT(DISTINCT task) AS tasks_due,
     MAX(alert.severity) AS highest_alert_severity

// Berechne Health-Score
WITH plant, phase, location, slot, tasks_due, highest_alert_severity,
     CASE
       WHEN highest_alert_severity = 'critical' THEN 0
       WHEN highest_alert_severity = 'warning' THEN 50
       WHEN tasks_due > 3 THEN 70
       WHEN tasks_due > 0 THEN 85
       ELSE 100
     END AS health_score

RETURN {
  plant_id: plant.instance_id,
  plant_name: plant.plant_name,
  phase: phase.name,
  location: location.location_name + ' - ' + slot.slot_name,
  health_score: health_score,
  tasks_due: tasks_due,
  alert_severity: highest_alert_severity,
  days_in_phase: duration.between(plant.current_phase_started_at, datetime()).inDays,
  color: CASE phase.name
    WHEN 'seedling' THEN 'lightgreen'
    WHEN 'vegetative' THEN 'green'
    WHEN 'flowering' THEN 'purple'
    WHEN 'ripening' THEN 'orange'
    ELSE 'gray'
  END,
  status_icon: CASE
    WHEN highest_alert_severity = 'critical' THEN '🔴'
    WHEN highest_alert_severity = 'warning' THEN '🟡'
    WHEN tasks_due > 0 THEN '📋'
    ELSE '✅'
  END
} AS plant_card
ORDER BY health_score ASC, tasks_due DESC
```

**VPD Calculator Widget:**
```cypher
// Hole aktuelle Temp/RH für VPD-Berechnung
MATCH (location:Location {id: $location_id})<-[:LOCATED_AT]-(temp_sensor:Sensor {parameter: 'temp'})
      -[:RECORDED]->(temp_obs:Observation)
WHERE temp_obs.timestamp > datetime() - duration('PT15M')

WITH location, temp_obs
ORDER BY temp_obs.timestamp DESC
LIMIT 1

WITH location, temp_obs.value AS temp_c

MATCH (location)<-[:LOCATED_AT]-(rh_sensor:Sensor {parameter: 'humidity'})
      -[:RECORDED]->(rh_obs:Observation)
WHERE rh_obs.timestamp > datetime() - duration('PT15M')

WITH location, temp_c, rh_obs
ORDER BY rh_obs.timestamp DESC
LIMIT 1

WITH location, temp_c, rh_obs.value AS rh_percent

// Hole Zielbereich aus aktueller Phase
MATCH (location)-[:HAS_SLOT]->(slot:Slot)<-[:PLACED_IN]-(plant:PlantInstance)
      -[:CURRENT_PHASE]->(phase:GrowthPhase)
      -[:REQUIRES_PROFILE]->(req:RequirementProfile)
      -[:USES_NUTRIENTS]->(nutr:NutrientProfile)

WITH temp_c, rh_percent, 
     AVG(nutr.vpd_target_kpa) AS target_vpd,
     AVG(nutr.vpd_tolerance_kpa) AS vpd_tolerance

// Berechne VPD
// Formel: VPD = (1 - RH/100) * SVP
// SVP (Sättigungsdampfdruck) = 0.61078 * exp((17.27 * T) / (T + 237.3))
WITH temp_c, rh_percent, target_vpd, vpd_tolerance,
     0.61078 * exp((17.27 * temp_c) / (temp_c + 237.3)) AS svp_kpa

WITH temp_c, rh_percent, target_vpd, vpd_tolerance, svp_kpa,
     (1 - rh_percent/100) * svp_kpa AS current_vpd

RETURN {
  current_vpd_kpa: round(current_vpd, 2),
  target_vpd_kpa: round(target_vpd, 2),
  tolerance_kpa: round(vpd_tolerance, 2),
  vpd_min: round(target_vpd - vpd_tolerance, 2),
  vpd_max: round(target_vpd + vpd_tolerance, 2),
  current_temp_c: round(temp_c, 1),
  current_rh_percent: round(rh_percent, 0),
  status: CASE
    WHEN current_vpd < (target_vpd - vpd_tolerance) THEN 'LOW'
    WHEN current_vpd > (target_vpd + vpd_tolerance) THEN 'HIGH'
    ELSE 'OPTIMAL'
  END,
  status_color: CASE
    WHEN current_vpd < (target_vpd - vpd_tolerance) THEN 'red'
    WHEN current_vpd > (target_vpd + vpd_tolerance) THEN 'red'
    WHEN abs(current_vpd - target_vpd) < vpd_tolerance/2 THEN 'green'
    ELSE 'yellow'
  END,
  recommendation: CASE
    WHEN current_vpd < (target_vpd - vpd_tolerance) THEN 
      'VPD zu niedrig - Erhöhe Temp oder senke RLF'
    WHEN current_vpd > (target_vpd + vpd_tolerance) THEN 
      'VPD zu hoch - Senke Temp oder erhöhe RLF'
    ELSE 'VPD optimal - Keine Änderung nötig'
  END
} AS vpd_data
```

**Harvest Calendar Widget (Nächste 4 Wochen):**
```cypher
MATCH (plant:PlantInstance)-[:CURRENT_PHASE]->(phase:GrowthPhase)

// Schätze Ernte-Datum
WITH plant, phase,
     CASE 
       WHEN phase.allows_harvest = true THEN date()
       ELSE date() + duration({days: phase.typical_duration_days})
     END AS estimated_harvest_date

WHERE estimated_harvest_date <= date() + duration('P28D')

// Hole letzte Harvest-Observation für genauere Schätzung
OPTIONAL MATCH (plant)-[:OBSERVED_FOR_HARVEST]->(obs:HarvestObservation)
WHERE obs.observed_at > datetime() - duration('P7D')

WITH plant, phase, estimated_harvest_date, obs
ORDER BY obs.observed_at DESC

WITH plant, phase, estimated_harvest_date, COLLECT(obs)[0] AS latest_obs

WITH plant, phase,
     CASE 
       WHEN latest_obs IS NOT NULL AND latest_obs.days_to_harvest_estimate IS NOT NULL
       THEN date() + duration({days: latest_obs.days_to_harvest_estimate})
       ELSE estimated_harvest_date
     END AS harvest_date

// Gruppiere nach Woche
WITH plant, harvest_date,
     duration.between(date(), harvest_date).inDays AS days_until_harvest,
     CASE
       WHEN harvest_date <= date() THEN 'Overdue'
       WHEN harvest_date <= date() + duration('P7D') THEN 'This Week'
       WHEN harvest_date <= date() + duration('P14D') THEN 'Next Week'
       WHEN harvest_date <= date() + duration('P21D') THEN 'Week 3'
       ELSE 'Week 4'
     END AS week_label

RETURN {
  week: week_label,
  harvests: COLLECT({
    plant_id: plant.instance_id,
    plant_name: plant.plant_name,
    harvest_date: harvest_date,
    days_until: days_until_harvest,
    urgency: CASE
      WHEN days_until_harvest < 0 THEN 'overdue'
      WHEN days_until_harvest <= 3 THEN 'urgent'
      WHEN days_until_harvest <= 7 THEN 'soon'
      ELSE 'scheduled'
    END
  })
} AS calendar_week
ORDER BY 
  CASE week_label
    WHEN 'Overdue' THEN 0
    WHEN 'This Week' THEN 1
    WHEN 'Next Week' THEN 2
    WHEN 'Week 3' THEN 3
    WHEN 'Week 4' THEN 4
  END
```

**Yield Analytics Widget:**
```cypher
// Analysiere Yields über letzte 6 Monate
MATCH (batch:Batch)-[:HAS_YIELD_METRIC]->(yield:YieldMetric)
WHERE batch.harvest_date > date() - duration('P180D')

// Hole zugehörige Pflanze für Cycle-Dauer
MATCH (batch)<-[:HARVESTED_AS]-(plant:PlantInstance)

WITH batch, yield, plant,
     duration.between(plant.planted_on, batch.harvest_date).inDays AS cycle_days

// Gruppiere nach Monat
WITH batch, yield, cycle_days,
     date.truncate('month', batch.harvest_date) AS harvest_month

WITH harvest_month,
     COUNT(batch) AS batches_this_month,
     SUM(yield.total_yield_g) AS total_yield_g,
     AVG(yield.yield_per_plant_g) AS avg_yield_per_plant,
     AVG(yield.yield_per_m2_g) AS avg_yield_per_m2,
     AVG(cycle_days) AS avg_cycle_days

// Berechne Effizienz-Metrik
WITH harvest_month, batches_this_month, total_yield_g,
     avg_yield_per_plant, avg_yield_per_m2, avg_cycle_days,
     CASE 
       WHEN avg_yield_per_m2 IS NOT NULL AND avg_cycle_days > 0
       THEN avg_yield_per_m2 / avg_cycle_days
       ELSE 0
     END AS grams_per_m2_per_day

RETURN {
  month: toString(harvest_month),
  batches: batches_this_month,
  total_yield_g: round(total_yield_g, 0),
  avg_yield_per_plant_g: round(avg_yield_per_plant, 1),
  avg_yield_per_m2_g: round(avg_yield_per_m2, 1),
  avg_cycle_days: round(avg_cycle_days, 0),
  efficiency_g_m2_day: round(grams_per_m2_per_day, 2),
  efficiency_grade: CASE
    WHEN grams_per_m2_per_day >= 1.5 THEN 'A+'
    WHEN grams_per_m2_per_day >= 1.0 THEN 'A'
    WHEN grams_per_m2_per_day >= 0.7 THEN 'B'
    WHEN grams_per_m2_per_day >= 0.5 THEN 'C'
    ELSE 'D'
  END
} AS monthly_analytics
ORDER BY harvest_month DESC
LIMIT 6
```

## 3. Technische Umsetzung (Python)

### Logik-Anforderungen:

**1. FastAPI Backend mit WebSocket:**
```python
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from typing import Dict, List, Set
from datetime import datetime, timedelta
import asyncio
import json

app = FastAPI()

# WebSocket Connection Manager
class ConnectionManager:
    """Verwaltet aktive WebSocket-Verbindungen"""
    
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, dashboard_id: str):
        """Neue Connection registrieren"""
        await websocket.accept()
        if dashboard_id not in self.active_connections:
            self.active_connections[dashboard_id] = set()
        self.active_connections[dashboard_id].add(websocket)
    
    def disconnect(self, websocket: WebSocket, dashboard_id: str):
        """Connection entfernen"""
        if dashboard_id in self.active_connections:
            self.active_connections[dashboard_id].discard(websocket)
    
    async def broadcast_to_dashboard(self, dashboard_id: str, message: dict):
        """Sende Update an alle Clients eines Dashboards"""
        if dashboard_id in self.active_connections:
            dead_connections = set()
            for connection in self.active_connections[dashboard_id]:
                try:
                    await connection.send_json(message)
                except:
                    dead_connections.add(connection)
            
            # Entferne tote Connections
            for conn in dead_connections:
                self.active_connections[dashboard_id].discard(conn)

manager = ConnectionManager()

@app.websocket("/ws/dashboard/{dashboard_id}")
async def websocket_endpoint(websocket: WebSocket, dashboard_id: str):
    """WebSocket-Endpoint für Live-Updates"""
    await manager.connect(websocket, dashboard_id)
    
    try:
        while True:
            # Warte auf Client-Messages (z.B. Widget-Updates anfordern)
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Verarbeite Client-Request
            if message.get('type') == 'request_update':
                widget_id = message.get('widget_id')
                widget_data = await fetch_widget_data(widget_id)
                
                await websocket.send_json({
                    'type': 'widget_update',
                    'widget_id': widget_id,
                    'data': widget_data,
                    'timestamp': datetime.now().isoformat()
                })
    
    except WebSocketDisconnect:
        manager.disconnect(websocket, dashboard_id)

async def fetch_widget_data(widget_id: str) -> dict:
    """Holt Daten für spezifisches Widget"""
    # Placeholder - in Produktion: Neo4j Query
    return {
        'widget_id': widget_id,
        'data': {'value': 42}
    }

# Background Task für periodische Updates
async def broadcast_updates():
    """Sendet regelmäßige Updates an alle Dashboards"""
    while True:
        await asyncio.sleep(10)  # Alle 10 Sekunden
        
        # Hole aktuelle Metriken
        overview_data = await get_overview_data()
        
        # Broadcast an alle Overview-Dashboards
        await manager.broadcast_to_dashboard('overview', {
            'type': 'auto_update',
            'data': overview_data,
            'timestamp': datetime.now().isoformat()
        })

@app.on_event("startup")
async def startup_event():
    """Starte Background-Tasks"""
    asyncio.create_task(broadcast_updates())
```

**2. Dashboard Data Aggregator:**
```python
from pydantic import BaseModel, Field
from typing import Literal, Optional, List, Dict
from datetime import datetime, date

class DashboardOverview(BaseModel):
    """Aggregierte Daten für Overview-Dashboard"""
    
    plants_total: int
    plants_healthy: int = Field(ge=0)
    plants_attention_needed: int = Field(ge=0)
    plants_critical: int = Field(ge=0)
    plants_in_flower: int = Field(ge=0)
    plants_ready_harvest: int = Field(ge=0)
    
    tasks_overdue: int = Field(ge=0)
    tasks_today: int = Field(ge=0)
    tasks_this_week: int = Field(ge=0)
    
    alerts_critical: int = Field(ge=0)
    alerts_warning: int = Field(ge=0)
    alerts_info: int = Field(ge=0)
    
    climate_status: Literal['optimal', 'attention', 'warning', 'critical']
    current_temp_c: Optional[float] = None
    current_rh_percent: Optional[int] = None
    current_vpd_kpa: Optional[float] = None
    
    avg_days_to_harvest: Optional[int] = None
    
    @property
    def total_alerts(self) -> int:
        return self.alerts_critical + self.alerts_warning + self.alerts_info
    
    @property
    def health_percentage(self) -> float:
        if self.plants_total == 0:
            return 100.0
        return (self.plants_healthy / self.plants_total) * 100
    
    def get_priority_actions(self) -> List[str]:
        """Generiert Top-3 Priority-Actions"""
        actions = []
        
        if self.plants_critical > 0:
            actions.append(f"🔴 {self.plants_critical} Pflanzen brauchen SOFORTIGE Aufmerksamkeit")
        
        if self.tasks_overdue > 0:
            actions.append(f"📋 {self.tasks_overdue} überfällige Tasks erledigen")
        
        if self.alerts_critical > 0:
            actions.append(f"⚠️ {self.alerts_critical} kritische Alerts prüfen")
        
        if self.climate_status == 'critical':
            actions.append(f"🌡️ Klima außerhalb kritischer Grenzen")
        
        if self.plants_ready_harvest > 0:
            actions.append(f"✂️ {self.plants_ready_harvest} Pflanzen bereit zur Ernte")
        
        return actions[:3]  # Top 3

class VPDWidget(BaseModel):
    """VPD Calculator Widget"""
    
    current_temp_c: float
    current_rh_percent: float
    target_vpd_kpa: float = 1.0
    vpd_tolerance_kpa: float = 0.2
    
    @property
    def saturation_vapor_pressure_kpa(self) -> float:
        """Berechnet SVP (Sättigungsdampfdruck)"""
        # August-Roche-Magnus Formel
        return 0.61078 * (2.71828 ** ((17.27 * self.current_temp_c) / (self.current_temp_c + 237.3)))
    
    @property
    def current_vpd_kpa(self) -> float:
        """Berechnet aktuellen VPD"""
        return (1 - self.current_rh_percent / 100) * self.saturation_vapor_pressure_kpa
    
    @property
    def vpd_status(self) -> Dict:
        """Bewertet VPD-Status"""
        vpd = self.current_vpd_kpa
        target = self.target_vpd_kpa
        tolerance = self.vpd_tolerance_kpa
        
        if vpd < (target - tolerance):
            status = 'LOW'
            color = 'red'
            action = 'Erhöhe Temperatur oder senke Luftfeuchte'
        elif vpd > (target + tolerance):
            status = 'HIGH'
            color = 'red'
            action = 'Senke Temperatur oder erhöhe Luftfeuchte'
        elif abs(vpd - target) < tolerance / 2:
            status = 'OPTIMAL'
            color = 'green'
            action = 'Keine Änderung nötig - perfekt!'
        else:
            status = 'ACCEPTABLE'
            color = 'yellow'
            action = 'Im Zielbereich, aber optimierbar'
        
        return {
            'status': status,
            'color': color,
            'action': action,
            'current_vpd': round(vpd, 2),
            'target_vpd': target,
            'deviation': round(vpd - target, 2),
            'deviation_percent': round(((vpd - target) / target) * 100, 1)
        }
    
    def calculate_ideal_adjustments(self) -> List[Dict]:
        """Berechnet mögliche Anpassungen um Ziel zu erreichen"""
        current_vpd = self.current_vpd_kpa
        target = self.target_vpd_kpa
        
        if abs(current_vpd - target) < 0.05:
            return [{'message': 'VPD bereits optimal'}]
        
        adjustments = []
        
        # Option 1: Nur Temperatur ändern
        if current_vpd < target:
            # VPD zu niedrig → Temp erhöhen
            temp_increase = (target / (1 - self.current_rh_percent / 100) - self.saturation_vapor_pressure_kpa) / 0.06
            adjustments.append({
                'method': 'Temperatur erhöhen',
                'change': f'+{round(temp_increase, 1)}°C',
                'new_temp': round(self.current_temp_c + temp_increase, 1),
                'rh_stays': self.current_rh_percent
            })
        else:
            # VPD zu hoch → Temp senken
            temp_decrease = (self.saturation_vapor_pressure_kpa - target / (1 - self.current_rh_percent / 100)) / 0.06
            adjustments.append({
                'method': 'Temperatur senken',
                'change': f'-{round(temp_decrease, 1)}°C',
                'new_temp': round(self.current_temp_c - temp_decrease, 1),
                'rh_stays': self.current_rh_percent
            })
        
        # Option 2: Nur RH ändern
        target_rh = (1 - target / self.saturation_vapor_pressure_kpa) * 100
        rh_change = target_rh - self.current_rh_percent
        adjustments.append({
            'method': 'Luftfeuchte anpassen',
            'change': f'{rh_change:+.1f}%',
            'temp_stays': self.current_temp_c,
            'new_rh': round(target_rh, 0)
        })
        
        return adjustments

class PlantHealthWidget(BaseModel):
    """Plant Health Aggregation Widget"""
    
    @staticmethod
    async def calculate_health_scores(neo4j_session) -> List[Dict]:
        """Berechnet Health-Scores für alle Pflanzen"""
        
        result = neo4j_session.run("""
            MATCH (plant:PlantInstance)
            OPTIONAL MATCH (plant)<-[:TRIGGERED]-(alert:Alert {acknowledged: false})
            OPTIONAL MATCH (plant)-[:HAS_TASK]->(task:Task {status: 'pending'})
            WHERE task.due_date < date()
            
            WITH plant,
                 COUNT(DISTINCT alert) AS alert_count,
                 MAX(alert.severity) AS max_severity,
                 COUNT(DISTINCT task) AS overdue_tasks
            
            // Berechne Score (0-100)
            WITH plant, alert_count, max_severity, overdue_tasks,
                 100 - 
                 (CASE max_severity 
                   WHEN 'critical' THEN 50 
                   WHEN 'warning' THEN 25 
                   ELSE 0 
                 END) -
                 (alert_count * 5) -
                 (overdue_tasks * 10) AS health_score
            
            RETURN plant.instance_id AS plant_id,
                   plant.plant_name AS name,
                   CASE 
                     WHEN health_score >= 80 THEN 'healthy'
                     WHEN health_score >= 60 THEN 'attention'
                     WHEN health_score >= 40 THEN 'warning'
                     ELSE 'critical'
                   END AS health_category,
                   health_score,
                   alert_count,
                   overdue_tasks
            ORDER BY health_score ASC
        """).data()
        
        return result

class YieldForecast(BaseModel):
    """Yield Forecasting basierend auf Historie"""
    
    plant_id: str
    current_phase: str
    days_in_current_phase: int
    
    @staticmethod
    async def forecast_yield(plant_id: str, neo4j_session) -> Dict:
        """Prognostiziert Yield basierend auf ähnlichen Grows"""
        
        result = neo4j_session.run("""
            // Hole aktuelle Pflanze
            MATCH (current:PlantInstance {instance_id: $plant_id})
                  -[:BELONGS_TO_SPECIES]->(species:Species)
            MATCH (current)-[:CURRENT_PHASE]->(current_phase:GrowthPhase)
            MATCH (current)-[:GROWN_IN]->(:SubstrateBatch)-[:USES_TYPE]->(substrate:Substrate)
            
            // Finde historische Batches gleicher Spezies/Substrat
            MATCH (species)<-[:BELONGS_TO_SPECIES]-(historical:PlantInstance)
                  -[:HARVESTED_AS]->(batch:Batch)
                  -[:HAS_YIELD_METRIC]->(yield:YieldMetric)
            MATCH (historical)-[:GROWN_IN]->(:SubstrateBatch)-[:USES_TYPE]->(substrate)
            
            WHERE historical.instance_id <> current.instance_id
              AND batch.harvest_date > date() - duration('P365D')
            
            // Berechne Durchschnitt
            WITH current, current_phase,
                 AVG(yield.yield_per_plant_g) AS avg_historical_yield,
                 STDEV(yield.yield_per_plant_g) AS yield_stddev,
                 COUNT(batch) AS sample_size,
                 MIN(yield.yield_per_plant_g) AS min_yield,
                 MAX(yield.yield_per_plant_g) AS max_yield
            
            RETURN {
                plant_id: current.instance_id,
                forecast_yield_g: round(avg_historical_yield, 0),
                confidence_range: [
                    round(avg_historical_yield - yield_stddev, 0),
                    round(avg_historical_yield + yield_stddev, 0)
                ],
                min_yield_g: round(min_yield, 0),
                max_yield_g: round(max_yield, 0),
                sample_size: sample_size,
                confidence: CASE
                    WHEN sample_size >= 10 THEN 'high'
                    WHEN sample_size >= 5 THEN 'medium'
                    ELSE 'low'
                END
            } AS forecast
        """, plant_id=plant_id).single()
        
        return dict(result['forecast']) if result else {}
```

**3. Widget Configuration System:**
```python
from typing import Any

class WidgetConfig(BaseModel):
    """Base-Konfiguration für alle Widgets"""
    
    widget_id: str
    widget_type: str
    title: str
    refresh_interval_seconds: int = Field(default=30, ge=5, le=3600)
    position: Dict[str, int] = Field(default_factory=lambda: {'x': 0, 'y': 0, 'w': 2, 'h': 2})
    visible: bool = True
    config: Dict[str, Any] = Field(default_factory=dict)

class WidgetFactory:
    """Factory für Widget-Typen"""
    
    WIDGET_TYPES = {
        'plant_grid': {
            'default_config': {
                'columns': 4,
                'show_health_score': True,
                'color_by': 'phase'
            },
            'data_source': 'plant_grid_query',
            'refresh_interval': 60
        },
        'vpd_gauge': {
            'default_config': {
                'show_calculator': True,
                'target_vpd': 1.0,
                'tolerance': 0.2
            },
            'data_source': 'vpd_calculation',
            'refresh_interval': 30
        },
        'task_list': {
            'default_config': {
                'max_items': 10,
                'filter_overdue': False,
                'group_by': 'priority'
            },
            'data_source': 'task_query',
            'refresh_interval': 60
        },
        'harvest_calendar': {
            'default_config': {
                'weeks_ahead': 4,
                'show_estimates': True
            },
            'data_source': 'harvest_forecast',
            'refresh_interval': 3600
        },
        'climate_chart': {
            'default_config': {
                'parameters': ['temp', 'humidity', 'vpd'],
                'timerange': '24h',
                'chart_type': 'line'
            },
            'data_source': 'climate_timeseries',
            'refresh_interval': 300
        }
    }
    
    @classmethod
    def create_widget(cls, widget_type: str, **kwargs) -> WidgetConfig:
        """Erstellt Widget mit Defaults"""
        
        if widget_type not in cls.WIDGET_TYPES:
            raise ValueError(f"Unknown widget type: {widget_type}")
        
        template = cls.WIDGET_TYPES[widget_type]
        
        return WidgetConfig(
            widget_id=kwargs.get('widget_id', f'{widget_type}_{datetime.now().timestamp()}'),
            widget_type=widget_type,
            title=kwargs.get('title', widget_type.replace('_', ' ').title()),
            refresh_interval_seconds=template['refresh_interval'],
            config=template['default_config']
        )
```

**4. Mobile-Responsive Layout Engine:**
```python
class ResponsiveLayoutEngine:
    """Berechnet optimale Widget-Layouts für verschiedene Screen-Sizes"""
    
    BREAKPOINTS = {
        'mobile': 768,
        'tablet': 1024,
        'desktop': 1920
    }
    
    @staticmethod
    def calculate_layout(widgets: List[WidgetConfig], screen_width: int) -> Dict:
        """Berechnet Grid-Layout basierend auf Screen-Width"""
        
        if screen_width < ResponsiveLayoutEngine.BREAKPOINTS['mobile']:
            # Mobile: 1 Spalte, Stack
            columns = 1
            widget_width = 12
        elif screen_width < ResponsiveLayoutEngine.BREAKPOINTS['tablet']:
            # Tablet: 2 Spalten
            columns = 2
            widget_width = 6
        else:
            # Desktop: 4 Spalten
            columns = 4
            widget_width = 3
        
        layout = []
        x, y = 0, 0
        
        for widget in widgets:
            if not widget.visible:
                continue
            
            # Bestimme Widget-Größe
            w = widget.position.get('w', widget_width)
            h = widget.position.get('h', 2)
            
            # Prüfe ob Widget in aktuelle Reihe passt
            if x + w > 12:
                x = 0
                y += h
            
            layout.append({
                'widget_id': widget.widget_id,
                'x': x,
                'y': y,
                'w': w,
                'h': h
            })
            
            x += w
        
        return {
            'columns': columns,
            'layout': layout,
            'total_height': y + 2
        }
```

### Datenvalidierung (Type Hinting):
```python
from typing import Literal, Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime

DashboardType = Literal['overview', 'climate', 'plant_health', 'harvest', 'resource', 'analytics', 'custom']
WidgetType = Literal['plant_grid', 'vpd_gauge', 'task_list', 'harvest_calendar', 'climate_chart', 'kpi_card', 'alert_feed']
AlertSeverity = Literal['info', 'warning', 'critical']
HealthStatus = Literal['healthy', 'attention', 'warning', 'critical']

class DashboardConfig(BaseModel):
    """Dashboard-Konfiguration"""
    
    dashboard_id: str
    name: str = Field(min_length=1, max_length=100)
    dashboard_type: DashboardType
    owner_id: str
    is_public: bool = False
    widgets: List[WidgetConfig] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    
    @validator('widgets')
    def validate_unique_widget_ids(cls, v):
        widget_ids = [w.widget_id for w in v]
        if len(widget_ids) != len(set(widget_ids)):
            raise ValueError("Widget-IDs müssen eindeutig sein")
        return v
```

## 4. Abhängigkeiten

**Erforderliche Module:**
- REQ-001 bis REQ-008: Alle (Dashboard aggregiert Daten aus allen Modulen)
- Redis (Caching für Performance)
- TimescaleDB/InfluxDB (Zeitreihen für Charts)

**Frontend-Technologien:**
- React 18+ mit Hooks
- Recharts oder D3.js für Charts
- React-Grid-Layout für Drag & Drop
- TanStack Query für Data-Fetching
- WebSocket-Client

**Python-Bibliotheken:**
- `fastapi` - REST API
- `websockets` - Real-Time Updates
- `plotly` - Chart-Generierung (Server-Side)
- `redis` - Caching
- `pydantic` - Validierung

## 5. Akzeptanzkriterien

### Definition of Done (DoD):

- [ ] **Sub-Second Ladezeit:** Initial Load <1s
- [ ] **WebSocket Live-Updates:** Keine Page-Refreshes nötig
- [ ] **Mobile-Responsive:** Touch-optimiert für Tablets
- [ ] **Dark-Mode:** Automatisch basierend auf System-Preference
- [ ] **Customizable Widgets:** Drag & Drop Neuanordnung
- [ ] **6+ Widget-Typen:** Plant Grid, VPD, Tasks, Harvest, Climate, Yield
- [ ] **VPD Calculator:** Live-Berechnung mit Zielbereich-Anzeige
- [ ] **Alert Center:** Kritische Warnungen prominent
- [ ] **Harvest Calendar:** 4-Wochen-Vorschau
- [ ] **Yield Forecasting:** ML-basierte Schätzungen
- [ ] **PDF-Export:** Dashboard als Report speichern
- [ ] **Multi-User:** Rollen (Viewer/Editor/Admin)
- [ ] **PWA:** Offline-Modus mit Sync
- [ ] **Keyboard Shortcuts:** Power-User-Features
- [ ] **Color-Blind-Mode:** Accessibility

### Testszenarien:

**Szenario 1: Overview Dashboard Load**
```
GIVEN: User öffnet Dashboard
WHEN: /api/dashboard/overview aufgerufen
THEN:
  - Response-Time < 500ms
  - Data enthält: plants, tasks, alerts, climate
  - WebSocket-Connection etabliert
  - Alle Widgets rendern innerhalb 1s
```

**Szenario 2: VPD Widget Live-Update**
```
GIVEN: VPD-Widget im Dashboard
      Temp = 24°C, RH = 55%
WHEN: Temp steigt auf 26°C (Sensor-Update)
THEN:
  - WebSocket sendet Update innerhalb 10s
  - VPD neu berechnet: 1.2 kPa → 1.4 kPa
  - Farbe ändert zu Gelb (außerhalb Toleranz)
  - Empfehlung: "RLF auf 60% erhöhen"
```

**Szenario 3: Plant Grid Health-Scores**
```
GIVEN: 10 Pflanzen im System
      - 7 healthy (keine Alerts, keine Tasks)
      - 2 attention (1 Warning-Alert)
      - 1 critical (1 Critical-Alert)
WHEN: Plant Grid Widget lädt
THEN:
  - 7 grüne Cards
  - 2 gelbe Cards mit 🟡
  - 1 rote Card mit 🔴
  - Sortierung: Critical → Attention → Healthy
```

**Szenario 4: Harvest Calendar**
```
GIVEN: 5 Pflanzen mit geschätzten Ernte-Daten:
      - Pflanze A: Morgen
      - Pflanze B: In 3 Tagen
      - Pflanze C: In 10 Tagen
      - Pflanze D: In 20 Tagen
      - Pflanze E: Überfällig (vor 2 Tagen)
WHEN: Harvest Calendar Widget rendert
THEN:
  - "Overdue": Pflanze E (rot)
  - "This Week": Pflanzen A, B (orange)
  - "Next Week": Pflanze C (gelb)
  - "Week 3": Pflanze D (grün)
```

**Szenario 5: Yield Forecast**
```
GIVEN: Pflanze in Blüte, Tag 35
      Historische Daten: 10 ähnliche Grows
      Durchschnitt: 80g, Stddev: 15g
WHEN: Yield-Forecast-Widget aufgerufen
THEN:
  - forecast_yield_g = 80
  - confidence_range = [65, 95]
  - confidence = 'high' (10 Samples)
  - Anzeige: "80g ± 15g (basierend auf 10 ähnlichen Grows)"
```

**Szenario 6: Mobile-Responsive Layout**
```
GIVEN: Dashboard mit 8 Widgets
      Screen-Width = 375px (iPhone)
WHEN: Layout-Engine berechnet
THEN:
  - columns = 1
  - Alle Widgets full-width
  - Stack-Layout (vertikal)
  - Touch-freundliche Controls
```

**Szenario 7: Alert-Center Real-Time**
```
GIVEN: Alert-Feed-Widget aktiv
WHEN: Neue Critical-Alert triggert (RH >65%)
THEN:
  - WebSocket pusht Update sofort
  - Alert erscheint oben im Feed
  - Browser-Notification (wenn aktiviert)
  - Rote Badge auf Alert-Icon
```

---

**Hinweise für RAG-Integration:**
- Keywords: Dashboard, Widget, VPD, Real-Time, WebSocket, Analytics, Forecast
- Fachbegriffe: KPI, Aggregation, Heat-Map, Correlation-Analysis, Responsive-Design
- Verknüpfung: Zentrale Schnittstelle zu allen anderen REQs
- Tech-Stack: FastAPI, React, WebSocket, Plotly, Redis
