---
name: REQ-014 Tankmanagement — Test Extraction Insights
description: Frontend structure, UI patterns, and key test cases for REQ-014 Tank management
type: project
---

## REQ-014 Tankmanagement — Key Test Extraction Insights

### Frontend Pages
- TankListPage at `/standorte/tanks` — DataTable, useTableUrlState (client-side), "Tank erstellen" button
- TankDetailPage at `/standorte/tanks/{key}` — 6 tabs: Details, Zustand, Wartung, Wartungsplaene, Befuellungen, Bearbeiten
- TankCreateDialog — name, tank_type, material, volume_liters, location (Site cascade), 7 boolean switches
- TankFillCreateDialog — fill_type, volume_liters, water_source (with 'mixed' showing ro_percent), target/measured EC/pH, is_organic flag; returns `warnings[]`
- TankStateCreateDialog — pH, EC, temp, fill_level, DO, ORP
- MaintenanceLogDialog, MaintenanceScheduleDialog, SensorCreateDialog — all dialogs on TankDetailPage

### Tab Structure (TankDetailPage)
Tab indices: 0=Details, 1=Zustand (states), 2=Wartung (maintenance), 3=Wartungsplaene (schedules), 4=Befuellungen (fills), 5=Bearbeiten
- Tab "Details" shows: alerts (MUI Alert), stammdaten card, latestState card (with source-badge + freshness chip), live-query section, sensors section
- Tab "Zustand": stateColumns (recordedAt, pH, EC, waterTemp, fillLevel, TDS), add-state button
- Tab "Wartung": dueColumns (type, nextDue, status chip: overdue=red/due_soon=yellow/ok=green, priority) + logColumns (type, performedAt, performedBy, duration, notes)
- Tab "Wartungsplaene": scheduleColumns with inline Edit/Delete icons per row
- Tab "Befuellungen": fillsColumns sorted desc by filledAt
- Tab "Bearbeiten": react-hook-form edit form + UnsavedChangesGuard

### Source-Badge Colors (MUI Chip)
- manual: 'default' (grey)
- ha_auto: 'primary' (blue)
- ha_live: 'success' (green)
- mqtt_auto: 'secondary' (purple)

### Freshness Logic (getFreshness function)
- < 5 min → color: 'success', key: 'freshLive'
- 5-60 min → color: 'warning', key: 'freshRecent', minutes: N
- > 60 min → color: 'error', key: 'freshStale'
- null → color: 'error', key: 'freshOffline'

### Live-Query Behavior
- Button triggers GET /tanks/{key}/states/live
- liveState.source === 'unavailable' → Alert "noHaConfigured"
- liveState.source === 'ha_live' + values → table + "Alle Messungen uebernehmen" button
- "Alle Messungen uebernehmen" → POST /tanks/{key}/states with all values → notification "adopted"
- Errors per entity shown as warning Alerts below table

### Key Business Rules for Test Cases
- TankType enum: nutrient, irrigation, reservoir, recirculation, stock_solution
- Recirculation-Tank: only at closed systems (hydro, nft, ebb_flow)
- Stock_solution-Tank: cannot be directly assigned to a Location
- Auto-created maintenance schedules: nutrient=5, irrigation=4, reservoir=4, recirculation=6 (all active)
- Maintenance status chips: overdue=error/red, due_soon=warning/yellow, ok=success/green
- FillType: full_change, top_up, adjustment
- Adjustment fill requires at least one of target_ec_ms or target_ph (model_validator)
- Top-up > 50% of tank volume → warning (not error)
- Full change < 50% of tank volume → warning (not error)
- EC deviation > 0.3 mS → warning; pH deviation > 0.5 → warning
- Tank-delete blocked when actively supplying a location (handleError shows notification)

### Watering Event Business Rules
- application_method: fertigation, drench, foliar, top_dress
- is_supplemental=true + fertigation=invalid (model_validator error)
- Foliar volume > 0.5 L/slot → warning
- Default water_source options: tap, osmose, mixed, rainwater, distilled, well

### Giesplan Confirm/Quick-Confirm
- confirm: task_key + application_method + volume + use_plan_dosages + optional overrides
- quick-confirm: only task_key needed (all defaults from NutrientPlan)
- 409 Conflict on already-completed task

### i18n Keys (pages.tanks.*)
- Tabs: tabDetails, tabStates, tabMaintenance, tabSchedules, tabFills
- Actions: liveQuery, liveValues, adoptAllReadings, adopted, noHaConfigured, noSensors
- Status: freshLive, freshRecent, freshStale, freshOffline
- Source badges: sourceManual, sourceHaAuto, sourceHaLive, sourceMqttAuto
- Fills: recordFill, fillRecorded, fillType, fillVolume, targetEc, targetPh, measuredEc, measuredPh, waterSource, roPercent
- Maintenance: maintenanceType, nextDue, intervalDays, reminderDays, performedAt, duration
- Schedules: editSchedule, scheduleDeleted
- Sensors: sensors, addSensor, sensorDeleted

### Alert Thresholds (check_alerts, visible in UI)
- pH nutrient: 5.5-6.5 (critical if >0.5 outside); recirculation: 5.5-6.3; irrigation: 5.8-6.8
- pH drift threshold: recirculation=0.3, others=0.5 (relative to last fill event)
- EC deviation: >20% = medium warning, >30% = high alert
- EC fallback (no target): nutrient/recirculation > 3.5 mS = high alert
- Temperature nutrient: cold_warning=15°C, cold_critical=10°C, warm_warning=22°C, warm_critical=26°C
- Temperature recirculation: warm_critical=25°C (stricter than nutrient due to systemic infection risk)
- DO: <6 mg/L = high, <4 mg/L = critical (nutrient+recirculation only)
- ORP recirculation: <250 mV = high (pathogen risk); <650 mV with UV/ozone = medium
- Fill level: <20% = high alert
- Solution age: organic=5 days, mineral=10 days at 20°C reference (Q10 correction applies)

### Test Output
- 72 test cases in `spec/e2e-testcases/TC-REQ-014.md`
- ID pattern: TC-014-{NNN} (3-digit sequential)
- Grouped: 1.Liste, 2.Erstellen, 3.Details-Tab, 4.Live-Query, 5.Zustand-Tab, 6.Wartung-Tab, 7.Wartungsplaene-Tab, 8.Befuellungen-Tab, 9.Bearbeiten-Tab, 10.Loeschen, 11.Sensor-Binding, 12.Alert-System, 13.Tank-Typ-Regeln, 14.Tank-Safety, 15.WateringEvent, 16.Giesplan-Flow, 17.Wasserquellen-Kaskade, 18.Auth/RBAC, 19.Edge-Cases
