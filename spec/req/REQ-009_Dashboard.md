# Spezifikation: REQ-009 - Dashboard

```yaml
ID: REQ-009
Titel: Zentrales Monitoring-Dashboard & Analytics
Kategorie: Visualisierung
Fokus: Beides
Technologie: FastAPI, React, ArangoDB, Plotly/D3.js, WebSocket
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

## 2. ArangoDB-Modellierung

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
    - `data_source: str` (AQL-Query oder API-Endpoint)
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
```aql
// Edge collections and their from/to document collections:
// dashboard_contains_widget:    Dashboard  → Widget
// widget_based_on_template:     Widget     → WidgetTemplate
// widget_displays_metric:       Widget     → Metric
// dashboard_shows_alerts:       Dashboard  → Alert
// user_has_preferences:         User       → UserPreference
// user_owns_dashboard:          User       → Dashboard
// dashboard_uses_snapshot:      Dashboard  → DataSnapshot
// alert_triggered_by:           Alert      → PlantInstance | StorageLocation | Sensor
```

### AQL-Beispiellogik:

**Dashboard-Übersicht (Overview Widget Data):**
```aql
// Aggregiere Key-Metriken für Overview Dashboard
LET plant_stats = (
  FOR plant IN PlantInstance
    LET phase = FIRST(
      FOR v, e IN 1..1 OUTBOUND plant GRAPH 'kamerplanter_graph'
        FILTER IS_SAME_COLLECTION('GrowthPhase', v)
        FILTER e._id LIKE 'current_phase/%'
        RETURN v
    )
    LET pending_tasks = (
      FOR v, e IN 1..1 OUTBOUND plant GRAPH 'kamerplanter_graph'
        FILTER IS_SAME_COLLECTION('Task', v)
        FILTER v.status == 'pending' AND v.due_date <= DATE_NOW()
        RETURN v
    )
    LET unack_alerts = (
      FOR v, e IN 1..1 INBOUND plant GRAPH 'kamerplanter_graph'
        FILTER IS_SAME_COLLECTION('Alert', v)
        FILTER v.acknowledged == false
        RETURN v
    )
    RETURN {
      phase_name: phase.name,
      allows_harvest: phase.allows_harvest,
      tasks_due: LENGTH(pending_tasks),
      alerts: unack_alerts
    }
)

LET total_plants = LENGTH(plant_stats)
LET plants_in_flower = LENGTH(
  FOR s IN plant_stats
    FILTER s.phase_name IN ['flowering', 'early_flowering', 'late_flowering']
    RETURN 1
)
LET plants_ready_harvest = LENGTH(
  FOR s IN plant_stats FILTER s.allows_harvest == true RETURN 1
)
LET tasks_due = SUM(FOR s IN plant_stats RETURN s.tasks_due)
LET all_alerts = FLATTEN(FOR s IN plant_stats RETURN s.alerts)
LET critical_alerts = LENGTH(
  FOR a IN all_alerts FILTER a.severity == 'critical' RETURN 1
)
LET warning_alerts = LENGTH(
  FOR a IN all_alerts FILTER a.severity == 'warning' RETURN 1
)

// Berechne durchschnittliche Tage bis Ernte
LET harvest_estimates = (
  FOR p IN PlantInstance
    LET phase = FIRST(
      FOR v, e IN 1..1 OUTBOUND p GRAPH 'kamerplanter_graph'
        FILTER IS_SAME_COLLECTION('GrowthPhase', v)
        FILTER e._id LIKE 'current_phase/%'
        RETURN v
    )
    FILTER phase.allows_harvest == false
    LET harvest_phase = FIRST(
      FOR sp, e1 IN 1..1 OUTBOUND p GRAPH 'kamerplanter_graph'
        FILTER IS_SAME_COLLECTION('Species', sp)
        FOR hp, e2 IN 1..1 OUTBOUND sp GRAPH 'kamerplanter_graph'
          FILTER IS_SAME_COLLECTION('GrowthPhase', hp)
          FILTER hp.allows_harvest == true
          RETURN hp
    )
    FILTER harvest_phase != null
    RETURN harvest_phase.typical_duration_days - phase.typical_duration_days
)
LET avg_days_to_harvest = LENGTH(harvest_estimates) > 0
  ? AVERAGE(harvest_estimates) : null

// Hole aktuelle Klima-Daten
LET temp_readings = (
  FOR sensor IN Sensor
    FILTER sensor.parameter == 'temp'
    FOR obs, e IN 1..1 OUTBOUND sensor GRAPH 'kamerplanter_graph'
      FILTER IS_SAME_COLLECTION('Observation', obs)
      FILTER obs.timestamp > DATE_SUBTRACT(DATE_NOW(), 15, 'minute')
      RETURN obs.value
)
LET current_temp = LENGTH(temp_readings) > 0
  ? AVERAGE(temp_readings) : null

LET rh_readings = (
  FOR sensor IN Sensor
    FILTER sensor.parameter == 'humidity'
    FOR obs, e IN 1..1 OUTBOUND sensor GRAPH 'kamerplanter_graph'
      FILTER IS_SAME_COLLECTION('Observation', obs)
      FILTER obs.timestamp > DATE_SUBTRACT(DATE_NOW(), 15, 'minute')
      RETURN obs.value
)
LET current_rh = LENGTH(rh_readings) > 0
  ? AVERAGE(rh_readings) : null

RETURN {
  plants: {
    total: total_plants,
    in_flower: plants_in_flower,
    ready_harvest: plants_ready_harvest,
    health_status: critical_alerts > 0 ? 'critical'
      : (warning_alerts > 0 ? 'warning' : 'healthy')
  },
  tasks: {
    due_count: tasks_due,
    status: tasks_due > 10 ? 'overloaded'
      : (tasks_due > 5 ? 'busy' : 'manageable')
  },
  alerts: {
    critical: critical_alerts,
    warning: warning_alerts,
    total: critical_alerts + warning_alerts
  },
  climate: {
    temperature_c: ROUND(current_temp, 1),
    humidity_percent: ROUND(current_rh, 0),
    vpd_kpa: ROUND(
      (1 - current_rh / 100) * 0.61078 * EXP((17.27 * current_temp) / (current_temp + 237.3)),
      2
    ),
    status: (current_temp < 18 OR current_temp > 28) ? 'warning'
      : ((current_rh < 40 OR current_rh > 70) ? 'warning' : 'ok')
  },
  forecast: {
    avg_days_to_harvest: ROUND(avg_days_to_harvest, 0)
  }
}
```

**Plant Grid Widget (Kanban-Style):**
```aql
FOR plant IN PlantInstance
  LET phase = FIRST(
    FOR v, e IN 1..1 OUTBOUND plant GRAPH 'kamerplanter_graph'
      FILTER IS_SAME_COLLECTION('GrowthPhase', v)
      FILTER e._id LIKE 'current_phase/%'
      RETURN v
  )
  LET slot = FIRST(
    FOR v, e IN 1..1 OUTBOUND plant GRAPH 'kamerplanter_graph'
      FILTER IS_SAME_COLLECTION('Slot', v)
      FILTER e._id LIKE 'placed_in/%'
      RETURN v
  )
  LET location = FIRST(
    FOR v, e IN 1..1 INBOUND slot GRAPH 'kamerplanter_graph'
      FILTER IS_SAME_COLLECTION('Location', v)
      FILTER e._id LIKE 'has_slot/%'
      RETURN v
  )
  LET tasks_due = LENGTH(
    FOR v, e IN 1..1 OUTBOUND plant GRAPH 'kamerplanter_graph'
      FILTER IS_SAME_COLLECTION('Task', v)
      FILTER v.status == 'pending' AND v.due_date <= DATE_NOW()
      RETURN v
  )
  LET alerts = (
    FOR v, e IN 1..1 INBOUND plant GRAPH 'kamerplanter_graph'
      FILTER IS_SAME_COLLECTION('Alert', v)
      FILTER v.acknowledged == false
      RETURN v.severity
  )
  LET highest_alert_severity = (
    'critical' IN alerts ? 'critical'
    : ('warning' IN alerts ? 'warning' : null)
  )

  // Berechne Health-Score
  LET health_score = (
    highest_alert_severity == 'critical' ? 0
    : (highest_alert_severity == 'warning' ? 50
    : (tasks_due > 3 ? 70
    : (tasks_due > 0 ? 85 : 100)))
  )

  SORT health_score ASC, tasks_due DESC

  RETURN {
    plant_id: plant.instance_id,
    plant_name: plant.plant_name,
    phase: phase.name,
    location: CONCAT(location.location_name, ' - ', slot.slot_name),
    health_score: health_score,
    tasks_due: tasks_due,
    alert_severity: highest_alert_severity,
    days_in_phase: DATE_DIFF(plant.current_phase_started_at, DATE_NOW(), 'day'),
    color: (
      phase.name == 'seedling' ? 'lightgreen'
      : (phase.name == 'vegetative' ? 'green'
      : (phase.name == 'flowering' ? 'purple'
      : (phase.name == 'ripening' ? 'orange' : 'gray')))
    ),
    status_icon: (
      highest_alert_severity == 'critical' ? '🔴'
      : (highest_alert_severity == 'warning' ? '🟡'
      : (tasks_due > 0 ? '📋' : '✅'))
    )
  }
```

**VPD Calculator Widget:**
```aql
// Hole aktuelle Temp/RH für VPD-Berechnung
LET location = DOCUMENT('Location', @location_id)

LET temp_c = FIRST(
  FOR sensor, e IN 1..1 INBOUND location GRAPH 'kamerplanter_graph'
    FILTER IS_SAME_COLLECTION('Sensor', sensor)
    FILTER sensor.parameter == 'temp'
    FOR obs, e2 IN 1..1 OUTBOUND sensor GRAPH 'kamerplanter_graph'
      FILTER IS_SAME_COLLECTION('Observation', obs)
      FILTER obs.timestamp > DATE_SUBTRACT(DATE_NOW(), 15, 'minute')
      SORT obs.timestamp DESC
      LIMIT 1
      RETURN obs.value
)

LET rh_percent = FIRST(
  FOR sensor, e IN 1..1 INBOUND location GRAPH 'kamerplanter_graph'
    FILTER IS_SAME_COLLECTION('Sensor', sensor)
    FILTER sensor.parameter == 'humidity'
    FOR obs, e2 IN 1..1 OUTBOUND sensor GRAPH 'kamerplanter_graph'
      FILTER IS_SAME_COLLECTION('Observation', obs)
      FILTER obs.timestamp > DATE_SUBTRACT(DATE_NOW(), 15, 'minute')
      SORT obs.timestamp DESC
      LIMIT 1
      RETURN obs.value
)

// Hole Zielbereich aus aktueller Phase
LET vpd_targets = (
  FOR slot, e1 IN 1..1 OUTBOUND location GRAPH 'kamerplanter_graph'
    FILTER IS_SAME_COLLECTION('Slot', slot)
    FOR plant, e2 IN 1..1 INBOUND slot GRAPH 'kamerplanter_graph'
      FILTER IS_SAME_COLLECTION('PlantInstance', plant)
      FOR phase, e3 IN 1..1 OUTBOUND plant GRAPH 'kamerplanter_graph'
        FILTER IS_SAME_COLLECTION('GrowthPhase', phase)
        FILTER e3._id LIKE 'current_phase/%'
        FOR req, e4 IN 1..1 OUTBOUND phase GRAPH 'kamerplanter_graph'
          FILTER IS_SAME_COLLECTION('RequirementProfile', req)
          FOR nutr, e5 IN 1..1 OUTBOUND req GRAPH 'kamerplanter_graph'
            FILTER IS_SAME_COLLECTION('NutrientProfile', nutr)
            RETURN { target: nutr.vpd_target_kpa, tolerance: nutr.vpd_tolerance_kpa }
)
LET target_vpd = AVERAGE(FOR t IN vpd_targets RETURN t.target)
LET vpd_tolerance = AVERAGE(FOR t IN vpd_targets RETURN t.tolerance)

// Berechne VPD
// Formel: VPD = (1 - RH/100) * SVP
// SVP (Sättigungsdampfdruck) = 0.61078 * exp((17.27 * T) / (T + 237.3))
LET svp_kpa = 0.61078 * EXP((17.27 * temp_c) / (temp_c + 237.3))
LET current_vpd = (1 - rh_percent / 100) * svp_kpa

RETURN {
  current_vpd_kpa: ROUND(current_vpd, 2),
  target_vpd_kpa: ROUND(target_vpd, 2),
  tolerance_kpa: ROUND(vpd_tolerance, 2),
  vpd_min: ROUND(target_vpd - vpd_tolerance, 2),
  vpd_max: ROUND(target_vpd + vpd_tolerance, 2),
  current_temp_c: ROUND(temp_c, 1),
  current_rh_percent: ROUND(rh_percent, 0),
  status: current_vpd < (target_vpd - vpd_tolerance) ? 'LOW'
    : (current_vpd > (target_vpd + vpd_tolerance) ? 'HIGH' : 'OPTIMAL'),
  status_color: current_vpd < (target_vpd - vpd_tolerance) ? 'red'
    : (current_vpd > (target_vpd + vpd_tolerance) ? 'red'
    : (ABS(current_vpd - target_vpd) < vpd_tolerance / 2 ? 'green' : 'yellow')),
  recommendation: current_vpd < (target_vpd - vpd_tolerance)
    ? 'VPD zu niedrig - Erhöhe Temp oder senke RLF'
    : (current_vpd > (target_vpd + vpd_tolerance)
    ? 'VPD zu hoch - Senke Temp oder erhöhe RLF'
    : 'VPD optimal - Keine Änderung nötig')
}
```

**Harvest Calendar Widget (Nächste 4 Wochen):**
```aql
LET today = DATE_NOW()

LET harvest_entries = (
  FOR plant IN PlantInstance
    LET phase = FIRST(
      FOR v, e IN 1..1 OUTBOUND plant GRAPH 'kamerplanter_graph'
        FILTER IS_SAME_COLLECTION('GrowthPhase', v)
        FILTER e._id LIKE 'current_phase/%'
        RETURN v
    )
    FILTER phase != null

    // Schätze Ernte-Datum
    LET estimated_harvest_date = (
      phase.allows_harvest == true
        ? today
        : DATE_ADD(today, phase.typical_duration_days, 'day')
    )
    FILTER estimated_harvest_date <= DATE_ADD(today, 28, 'day')

    // Hole letzte Harvest-Observation für genauere Schätzung
    LET latest_obs = FIRST(
      FOR v, e IN 1..1 OUTBOUND plant GRAPH 'kamerplanter_graph'
        FILTER IS_SAME_COLLECTION('HarvestObservation', v)
        FILTER v.observed_at > DATE_SUBTRACT(today, 7, 'day')
        SORT v.observed_at DESC
        LIMIT 1
        RETURN v
    )

    LET harvest_date = (
      latest_obs != null AND latest_obs.days_to_harvest_estimate != null
        ? DATE_ADD(today, latest_obs.days_to_harvest_estimate, 'day')
        : estimated_harvest_date
    )

    LET days_until_harvest = DATE_DIFF(today, harvest_date, 'day')

    // Gruppiere nach Woche
    LET week_label = (
      harvest_date <= today ? 'Overdue'
      : (harvest_date <= DATE_ADD(today, 7, 'day') ? 'This Week'
      : (harvest_date <= DATE_ADD(today, 14, 'day') ? 'Next Week'
      : (harvest_date <= DATE_ADD(today, 21, 'day') ? 'Week 3' : 'Week 4')))
    )

    LET week_order = (
      week_label == 'Overdue' ? 0
      : (week_label == 'This Week' ? 1
      : (week_label == 'Next Week' ? 2
      : (week_label == 'Week 3' ? 3 : 4)))
    )

    RETURN {
      week_label: week_label,
      week_order: week_order,
      plant_id: plant.instance_id,
      plant_name: plant.plant_name,
      harvest_date: harvest_date,
      days_until: days_until_harvest,
      urgency: (
        days_until_harvest < 0 ? 'overdue'
        : (days_until_harvest <= 3 ? 'urgent'
        : (days_until_harvest <= 7 ? 'soon' : 'scheduled'))
      )
    }
)

// Gruppiere nach Woche und sortiere
FOR entry IN harvest_entries
  COLLECT week = entry.week_label, order = entry.week_order INTO plants
  SORT order ASC
  RETURN {
    week: week,
    harvests: plants[*].entry
  }
```

**Yield Analytics Widget:**
```aql
// Analysiere Yields über letzte 6 Monate
LET raw_data = (
  FOR batch IN Batch
    FILTER batch.harvest_date > DATE_SUBTRACT(DATE_NOW(), 180, 'day')

    // Hole Yield-Metriken
    LET yield_metric = FIRST(
      FOR v, e IN 1..1 OUTBOUND batch GRAPH 'kamerplanter_graph'
        FILTER IS_SAME_COLLECTION('YieldMetric', v)
        RETURN v
    )
    FILTER yield_metric != null

    // Hole zugehörige Pflanze für Cycle-Dauer
    LET plant = FIRST(
      FOR v, e IN 1..1 INBOUND batch GRAPH 'kamerplanter_graph'
        FILTER IS_SAME_COLLECTION('PlantInstance', v)
        RETURN v
    )

    LET cycle_days = DATE_DIFF(plant.planted_on, batch.harvest_date, 'day')

    // Gruppiere nach Monat (Truncate auf Monatsanfang)
    LET harvest_month = DATE_FORMAT(batch.harvest_date, '%yyyy-%mm')

    RETURN {
      harvest_month: harvest_month,
      total_yield_g: yield_metric.total_yield_g,
      yield_per_plant_g: yield_metric.yield_per_plant_g,
      yield_per_m2_g: yield_metric.yield_per_m2_g,
      cycle_days: cycle_days
    }
)

FOR entry IN raw_data
  COLLECT month = entry.harvest_month INTO grouped
  LET batches_this_month = LENGTH(grouped)
  LET total_yield_g = SUM(grouped[*].entry.total_yield_g)
  LET avg_yield_per_plant = AVERAGE(grouped[*].entry.yield_per_plant_g)
  LET avg_yield_per_m2 = AVERAGE(grouped[*].entry.yield_per_m2_g)
  LET avg_cycle_days = AVERAGE(grouped[*].entry.cycle_days)

  // Berechne Effizienz-Metrik
  LET grams_per_m2_per_day = (
    avg_yield_per_m2 != null AND avg_cycle_days > 0
      ? avg_yield_per_m2 / avg_cycle_days
      : 0
  )

  SORT month DESC
  LIMIT 6

  RETURN {
    month: month,
    batches: batches_this_month,
    total_yield_g: ROUND(total_yield_g, 0),
    avg_yield_per_plant_g: ROUND(avg_yield_per_plant, 1),
    avg_yield_per_m2_g: ROUND(avg_yield_per_m2, 1),
    avg_cycle_days: ROUND(avg_cycle_days, 0),
    efficiency_g_m2_day: ROUND(grams_per_m2_per_day, 2),
    efficiency_grade: (
      grams_per_m2_per_day >= 1.5 ? 'A+'
      : (grams_per_m2_per_day >= 1.0 ? 'A'
      : (grams_per_m2_per_day >= 0.7 ? 'B'
      : (grams_per_m2_per_day >= 0.5 ? 'C' : 'D')))
    )
  }
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
    # Placeholder - in Produktion: ArangoDB AQL Query
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
    async def calculate_health_scores(arangodb) -> List[Dict]:
        """Berechnet Health-Scores für alle Pflanzen"""

        query = """
            FOR plant IN PlantInstance
              LET alerts = (
                FOR v, e IN 1..1 INBOUND plant GRAPH 'kamerplanter_graph'
                  FILTER IS_SAME_COLLECTION('Alert', v)
                  FILTER v.acknowledged == false
                  RETURN v
              )
              LET alert_count = LENGTH(alerts)
              LET max_severity = (
                'critical' IN alerts[*].severity ? 'critical'
                : ('warning' IN alerts[*].severity ? 'warning' : null)
              )
              LET overdue_tasks = LENGTH(
                FOR v, e IN 1..1 OUTBOUND plant GRAPH 'kamerplanter_graph'
                  FILTER IS_SAME_COLLECTION('Task', v)
                  FILTER v.status == 'pending' AND v.due_date < DATE_NOW()
                  RETURN v
              )

              // Berechne Score (0-100)
              LET severity_penalty = (
                max_severity == 'critical' ? 50
                : (max_severity == 'warning' ? 25 : 0)
              )
              LET health_score = 100 - severity_penalty - (alert_count * 5) - (overdue_tasks * 10)

              SORT health_score ASC
              RETURN {
                plant_id: plant.instance_id,
                name: plant.plant_name,
                health_category: (
                  health_score >= 80 ? 'healthy'
                  : (health_score >= 60 ? 'attention'
                  : (health_score >= 40 ? 'warning' : 'critical'))
                ),
                health_score: health_score,
                alert_count: alert_count,
                overdue_tasks: overdue_tasks
              }
        """
        cursor = arangodb.aql.execute(query)
        return [doc for doc in cursor]

class YieldForecast(BaseModel):
    """Yield Forecasting basierend auf Historie"""
    
    plant_id: str
    current_phase: str
    days_in_current_phase: int
    
    @staticmethod
    async def forecast_yield(plant_id: str, arangodb) -> Dict:
        """Prognostiziert Yield basierend auf ähnlichen Grows"""

        query = """
            // Hole aktuelle Pflanze
            LET current = FIRST(
              FOR p IN PlantInstance FILTER p.instance_id == @plant_id RETURN p
            )
            LET species = FIRST(
              FOR v, e IN 1..1 OUTBOUND current GRAPH 'kamerplanter_graph'
                FILTER IS_SAME_COLLECTION('Species', v)
                RETURN v
            )
            LET substrate = FIRST(
              FOR sb, e1 IN 1..1 OUTBOUND current GRAPH 'kamerplanter_graph'
                FILTER IS_SAME_COLLECTION('SubstrateBatch', sb)
                FOR st, e2 IN 1..1 OUTBOUND sb GRAPH 'kamerplanter_graph'
                  FILTER IS_SAME_COLLECTION('Substrate', st)
                  RETURN st
            )

            // Finde historische Batches gleicher Spezies/Substrat
            LET yields = (
              FOR historical, e1 IN 1..1 INBOUND species GRAPH 'kamerplanter_graph'
                FILTER IS_SAME_COLLECTION('PlantInstance', historical)
                FILTER historical.instance_id != current.instance_id
                // Prüfe gleiches Substrat
                LET hist_substrate = FIRST(
                  FOR sb, e2 IN 1..1 OUTBOUND historical GRAPH 'kamerplanter_graph'
                    FILTER IS_SAME_COLLECTION('SubstrateBatch', sb)
                    FOR st, e3 IN 1..1 OUTBOUND sb GRAPH 'kamerplanter_graph'
                      FILTER IS_SAME_COLLECTION('Substrate', st)
                      FILTER st._key == substrate._key
                      RETURN st
                )
                FILTER hist_substrate != null
                FOR batch, e4 IN 1..1 OUTBOUND historical GRAPH 'kamerplanter_graph'
                  FILTER IS_SAME_COLLECTION('Batch', batch)
                  FILTER batch.harvest_date > DATE_SUBTRACT(DATE_NOW(), 365, 'day')
                  FOR ym, e5 IN 1..1 OUTBOUND batch GRAPH 'kamerplanter_graph'
                    FILTER IS_SAME_COLLECTION('YieldMetric', ym)
                    RETURN ym.yield_per_plant_g
            )

            // Berechne Durchschnitt
            LET sample_size = LENGTH(yields)
            LET avg_historical_yield = AVERAGE(yields)
            LET yield_stddev = STDDEV(yields)
            LET min_yield = MIN(yields)
            LET max_yield = MAX(yields)

            RETURN {
              plant_id: current.instance_id,
              forecast_yield_g: ROUND(avg_historical_yield, 0),
              confidence_range: [
                ROUND(avg_historical_yield - yield_stddev, 0),
                ROUND(avg_historical_yield + yield_stddev, 0)
              ],
              min_yield_g: ROUND(min_yield, 0),
              max_yield_g: ROUND(max_yield, 0),
              sample_size: sample_size,
              confidence: (
                sample_size >= 10 ? 'high'
                : (sample_size >= 5 ? 'medium' : 'low')
              )
            }
        """
        cursor = arangodb.aql.execute(query, bind_vars={'plant_id': plant_id})
        result = next(cursor, None)
        return dict(result) if result else {}
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
from pydantic import BaseModel, Field, field_validator
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
    
    @field_validator('widgets')
    @classmethod
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
- TimescaleDB (Zeitreihen für Charts)

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
