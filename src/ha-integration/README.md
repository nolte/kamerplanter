# Kamerplanter Home Assistant Integration

Custom Integration für Home Assistant zur Anbindung an das Kamerplanter-Backend.

## Einrichtung (Config Flow)

1. **Einstellungen > Geräte & Dienste > Integration hinzufügen > Kamerplanter**
2. URL der Kamerplanter-Instanz eingeben (z.B. `http://kamerplanter-backend:8000`)
3. API-Key eingeben (Format `kp_...`) — im Light-Modus optional
4. Tenant auswählen (bei mehreren Tenants wird ein Auswahl-Dialog angezeigt, bei einem einzigen wird automatisch gewählt)

### Options

Unter **Einstellungen > Geräte & Dienste > Kamerplanter > Konfigurieren** lassen sich die Polling-Intervalle anpassen:

| Option | Default | Minimum | Beschreibung |
|--------|---------|---------|--------------|
| Plants | 300s | 120s | Pflanzeninstanzen, Phasen, Dosierungen |
| Locations | 300s | 120s | Standorte, Tanks, Runs |
| Alerts | 60s | 30s | Überfällige Aufgaben, Sensor-Offline |
| Tasks | 300s | 120s | Anstehende Aufgaben |

---

## Entities

### Sensor-Entities

#### Pro Pflanzeninstanz (Device: Plant Instance)

| Entity-ID | Name | Beschreibung |
|-----------|------|--------------|
| `sensor.kp_{key}_phase` | Phase | Aktuelle Wachstumsphase (germination, seedling, vegetative, flowering, ...) |
| `sensor.kp_{key}_days_in_phase` | Days in Phase | Tage seit letztem Phasenwechsel |
| `sensor.kp_{key}_nutrient_plan` | Nutrient Plan | Name des zugewiesenen Nährstoffplans |
| `sensor.kp_{key}_phase_timeline` | Phase Timeline | Gesamte Phasen-Timeline als JSON-Attribute |
| `sensor.kp_{key}_next_phase` | Next Phase | Nächste geplante Phase + voraussichtliches Datum |
| `sensor.kp_{key}_active_channels` | Active Channels | Anzahl aktiver Ausführungskanäle |
| `sensor.kp_{key}_{channel}_mix` | *Channel-Name* | Dosierungen pro Kanal (ml/L als Attribute) |

#### Pro Pflanzdurchlauf (Device: Planting Run)

| Entity-ID | Name | Beschreibung |
|-----------|------|--------------|
| `sensor.kp_{key}_status` | Status | Run-Status (planned, active, harvesting, completed, cancelled) |
| `sensor.kp_{key}_plant_count` | Plant Count | Anzahl Pflanzen im Durchlauf |
| `sensor.kp_{key}_nutrient_plan` | Nutrient Plan | Zugewiesener Nährstoffplan |
| `sensor.kp_{key}_phase_timeline` | Phase Timeline | Phasen-Timeline des Durchlaufs |
| `sensor.kp_{key}_next_phase` | Next Phase | Nächste Phase + Datum |
| `sensor.kp_{key}_{channel}_mix` | *Channel-Name* | Kanal-Dosierungen der aktuellen Woche |

#### Pro Standort (Device: Location)

| Entity-ID | Name | Beschreibung |
|-----------|------|--------------|
| `sensor.kp_loc_{key}_type` | Location Type | Standort-Typ (room, tent, bed, ...) |
| `sensor.kp_loc_{key}_active_run_count` | Active Run Count | Anzahl aktiver Durchläufe |
| `sensor.kp_loc_{key}_active_plant_count` | Active Plant Count | Anzahl aktiver Pflanzen |
| `sensor.kp_loc_{key}_run_phase` | Run Phase | Phase des primären Durchlaufs |
| `sensor.kp_loc_{key}_run_days_in_phase` | Run Days in Phase | Tage in Phase (primärer Run) |
| `sensor.kp_loc_{key}_run_nutrient_plan` | Run Nutrient Plan | Nährstoffplan des primären Runs |
| `sensor.kp_loc_{key}_run_next_phase` | Run Next Phase | Nächste Phase des primären Runs |
| `sensor.kp_loc_{key}_{channel}_mix` | *Channel-Name* | Kanal-Dosierungen des primären Runs |

#### Pro Tank (Device: Tank)

| Entity-ID | Name | Beschreibung |
|-----------|------|--------------|
| `sensor.kp_{key}_info` | Tank Info | Tank-Übersicht (letzte Befüllung, Alter, HA-Sensor-Mappings als Attribute) |
| `sensor.kp_{key}_volume` | Tank Volume | Tank-Nennvolumen in Litern |

#### Server (Device: Kamerplanter Server)

| Entity-ID | Name | Beschreibung |
|-----------|------|--------------|
| `sensor.kp_tasks_due_today` | Tasks Due Today | Anzahl heute fälliger Aufgaben |
| `sensor.kp_tasks_overdue` | Tasks Overdue | Anzahl überfälliger Aufgaben |
| `sensor.kp_next_watering` | Next Watering | Nächste fällige Bewässerung (Pflanze + Datum) |

### Binary-Sensor-Entities

| Entity-ID | Device | Beschreibung |
|-----------|--------|--------------|
| `binary_sensor.kp_{key}_needs_attention` | Plant Instance | Pflanze hat überfällige Aufgaben |
| `binary_sensor.kp_loc_{key}_needs_attention` | Location | Standort hat überfällige Aufgaben |
| `binary_sensor.kp_sensor_offline` | Server | Mindestens ein Sensor ist offline |
| `binary_sensor.kp_care_overdue` | Server | Mindestens eine Pflegeaufgabe ist überfällig (Attribut: `overdue_count`) |

### Calendar-Entities

| Entity-ID | Name | Beschreibung |
|-----------|------|--------------|
| `calendar.kp_phases` | Kamerplanter Phasen | Wachstumsphasen aller aktiven Pflanzen als Mehrtages-Events |
| `calendar.kp_tasks` | Kamerplanter Tasks | Anstehende Aufgaben mit Fälligkeitsdatum |

### Todo-Entity

| Entity-ID | Name | Beschreibung |
|-----------|------|--------------|
| `todo.kp_tasks` | Kamerplanter Tasks | Anstehende Aufgaben als Todo-Liste. Abhaken markiert die Aufgabe im Backend als erledigt. |

### Button-Entity

| Entity-ID | Name | Beschreibung |
|-----------|------|--------------|
| `button.kp_refresh_all` | Refresh All Data | Manueller Refresh aller Coordinators. Feuert `kamerplanter_data_refreshed` Event. |

---

## Services

### `kamerplanter.refresh_data` — Daten aktualisieren

Löst einen sofortigen Re-Poll aller Coordinators aus.

| Parameter | Typ | Pflicht | Beschreibung |
|-----------|-----|---------|--------------|
| `entry_id` | string | nein | Config-Entry-ID einer bestimmten Instanz. Leer = alle Instanzen. |

**Beispiel-Aufruf:**
```yaml
service: kamerplanter.refresh_data
data: {}
```

---

### `kamerplanter.clear_cache` — Cache leeren

Löscht den lokalen Coordinator-Cache und lädt alle Daten neu vom Backend.

| Parameter | Typ | Pflicht | Beschreibung |
|-----------|-----|---------|--------------|
| `entry_id` | string | nein | Config-Entry-ID. Leer = alle Instanzen. |

**Beispiel-Aufruf:**
```yaml
service: kamerplanter.clear_cache
data: {}
```

---

### `kamerplanter.fill_tank` — Tank befüllen

Erstellt ein Tank-Fill-Event im Kamerplanter-Backend. Löst automatisch die aktuellen Dosierungen aus dem zugewiesenen Nährstoffplan auf und sendet diese mit. Nach Erfolg werden alle Coordinators refreshed.

| Parameter | Typ | Pflicht | Default | Beschreibung |
|-----------|-----|---------|---------|--------------|
| `entity_id` | entity | nein* | — | Eine beliebige Tank-Entity (z.B. `sensor.kp_90639_info`). Daraus wird der `tank_key` aufgelöst. |
| `tank_key` | string | nein* | — | Direkter ArangoDB-Key des Tanks. Legacy-Fallback wenn keine Entity-ID verfügbar. |
| `fill_type` | select | nein | `full_change` | `full_change` (Komplettwechsel), `top_up` (Nachfüllen), `adjustment` (Korrektur) |
| `volume_liters` | number | nein | Tank-Nennvolumen | Befülltes Volumen in Litern (0.1–1000) |
| `measured_ec_ms` | number | nein | — | Gemessener EC-Wert nach dem Mischen (0–10 mS/cm) |
| `measured_ph` | number | nein | — | Gemessener pH-Wert nach dem Mischen (0–14) |
| `notes` | text | nein | — | Optionale Bemerkungen |

*Entweder `entity_id` oder `tank_key` muss angegeben werden.

**Entity-ID-Auflösung:** Der Service erkennt Tank-Entities anhand des Patterns `sensor.kp_{slug}_{suffix}` wobei Suffix eines von `_info`, `_volume`, `_fill_level`, `_ec`, `_ph`, `_water_temp`, `_solution_age_days`, `_alert_active` sein kann.

**Beispiel — Komplettwechsel mit Messwerten:**
```yaml
service: kamerplanter.fill_tank
data:
  entity_id: sensor.kp_90639_info
  fill_type: full_change
  measured_ec_ms: 1.8
  measured_ph: 6.2
  notes: "Frische Lösung Woche 4 Blüte"
```

**Beispiel — Nachfüllen über tank_key:**
```yaml
service: kamerplanter.fill_tank
data:
  tank_key: "90639"
  fill_type: top_up
  volume_liters: 20
```

**Automatisierung — Tank bei niedrigem Füllstand befüllen:**
```yaml
automation:
  trigger:
    - platform: numeric_state
      entity_id: sensor.kp_90639_fill_level
      below: 20
  action:
    - service: kamerplanter.fill_tank
      data:
        entity_id: sensor.kp_90639_info
        fill_type: top_up
        volume_liters: 30
```

---

### `kamerplanter.water_channel` — Ausführungskanal gießen

Erstellt einen Watering-Log-Eintrag im Backend für einen bestimmten Ausführungskanal (Delivery Channel) einer Pflanzeninstanz. Löst automatisch die aktuellen Dünger-Dosierungen aus dem Nährstoffplan auf.

| Parameter | Typ | Pflicht | Default | Beschreibung |
|-----------|-----|---------|---------|--------------|
| `entity_id` | entity | nein* | — | Eine Channel-Entity (z.B. `sensor.kp_12345_giesswasser_mix`). Plant-Key und Channel-ID werden automatisch aufgelöst. |
| `plant_key` | string | nein* | — | Direkter ArangoDB-Key der Pflanzeninstanz |
| `channel_id` | string | nein | erster Kanal | ID des Ausführungskanals (z.B. `giesswasser`, `blattpflege`). Nur zusammen mit `plant_key`. |
| `volume_liters` | number | nein | Kanalvolumen | Gegossenes Volumen in Litern (0.01–1000). Fallback: Volumen aus dem Nährstoffplan-Kanal. |
| `application_method` | select | nein | `drench` | `drench` (Gießen), `foliar` (Blattsprühung), `fertigation`, `capillary` (Kapillar) |
| `measured_ec_ms` | number | nein | — | EC-Wert der Nährlösung (0–10 mS/cm) |
| `measured_ph` | number | nein | — | pH-Wert der Nährlösung (0–14) |
| `notes` | text | nein | — | Optionale Bemerkungen |

*Entweder `entity_id` oder `plant_key` muss angegeben werden.

**Entity-ID-Auflösung:** Channel-Entities folgen dem Pattern `sensor.kp_{plant_slug}_{channel_slug}_mix`. Der Service durchsucht den Plant-Coordinator um `plant_key` und `channel_id` aufzulösen.

**Dosierung-Auflösung:** Die Dünger-Dosierungen (ml/L pro Produkt) werden automatisch aus dem dem Channel zugewiesenen Nährstoffplan gelesen. Das Volumen wird, falls nicht angegeben, aus den Kanal-Parametern des Nährstoffplans geholt.

**Beispiel — Pflanze über Entity gießen:**
```yaml
service: kamerplanter.water_channel
data:
  entity_id: sensor.kp_12345_giesswasser_mix
  volume_liters: 2.5
  measured_ec_ms: 1.6
  measured_ph: 6.0
```

**Beispiel — Blattsprühung über plant_key:**
```yaml
service: kamerplanter.water_channel
data:
  plant_key: "12345"
  channel_id: "blattpflege"
  application_method: foliar
  volume_liters: 0.5
```

**Automatisierung — Tägliche Bewässerung per Zeitplan:**
```yaml
automation:
  trigger:
    - platform: time
      at: "08:00:00"
  condition:
    - condition: state
      entity_id: binary_sensor.kp_12345_needs_attention
      state: "on"
  action:
    - service: kamerplanter.water_channel
      data:
        entity_id: sensor.kp_12345_giesswasser_mix
```

---

### `kamerplanter.confirm_care` — Pflegeerinnerung bestätigen

Bestätigt eine Pflegeerinnerung als erledigt oder übersprungen. Wird typischerweise von Actionable Notifications der HA Companion App aufgerufen.

| Parameter | Typ | Pflicht | Default | Beschreibung |
|-----------|-----|---------|---------|--------------|
| `notification_key` | string | ja | — | Key der zu bestätigenden Notification (z.B. `notif_20260321_abc123`) |
| `action` | select | nein | `confirmed` | `confirmed` (Erledigt) oder `skipped` (Übersprungen) |

**Beispiel — Erinnerung bestätigen:**
```yaml
service: kamerplanter.confirm_care
data:
  notification_key: "notif_20260321_abc123"
  action: confirmed
```

**Beispiel — Erinnerung überspringen:**
```yaml
service: kamerplanter.confirm_care
data:
  notification_key: "notif_20260321_abc123"
  action: skipped
```

**Automatisierung — Actionable Notification mit Bestätigung:**
```yaml
automation:
  trigger:
    - platform: event
      event_type: kamerplanter_care_due
  action:
    - service: notify.mobile_app_phone
      data:
        title: "Pflege fällig"
        message: "{{ trigger.event.data.message }}"
        data:
          actions:
            - action: "CONFIRM_CARE_{{ trigger.event.data.notification_key }}"
              title: "Erledigt"
            - action: "SKIP_CARE_{{ trigger.event.data.notification_key }}"
              title: "Überspringen"

  # Companion App Response Handler
  - alias: "Care Notification Confirmed"
    trigger:
      - platform: event
        event_type: mobile_app_notification_action
        event_data:
          action_prefix: "CONFIRM_CARE_"
    action:
      - service: kamerplanter.confirm_care
        data:
          notification_key: "{{ trigger.event.data.action.split('CONFIRM_CARE_')[1] }}"
          action: confirmed
```

---

## Events

Die Integration feuert folgende Events über den HA Event-Bus:

| Event-Typ | Beschreibung | Daten |
|-----------|--------------|-------|
| `kamerplanter_task_completed` | Aufgabe wurde über Todo-Entity abgehakt | `entry_id`, `task_key` |
| `kamerplanter_data_refreshed` | Manueller Refresh über Button ausgelöst | `entry_id`, `timestamp` |
| `kamerplanter_care_due` | Pflegeerinnerung fällig | Notification-Daten |
| `kamerplanter_seasonal` | Saisonale Erinnerung | Notification-Daten |
| `kamerplanter_sensor_alert` | Sensor-Alarm | Notification-Daten |
| `kamerplanter_ipm_alert` | Pflanzenschutz-Alarm | Notification-Daten |
| `kamerplanter_tank_alert` | Tank-Alarm | Notification-Daten |
| `kamerplanter_harvest` | Ernte-Benachrichtigung | Notification-Daten |
| `kamerplanter_task_due` | Aufgabe fällig | Notification-Daten |
| `kamerplanter_weather_alert` | Wetter-Warnung | Notification-Daten |
| `kamerplanter_phase` | Phasenwechsel | Notification-Daten |

---

## Coordinators

Die Integration nutzt 5 DataUpdateCoordinators mit konfigurierbaren Polling-Intervallen:

| Coordinator | Datenquelle | Beschreibung |
|-------------|-------------|--------------|
| `PlantCoordinator` | `/plant-instances` | Pflanzen mit Phase, Dosierungen, Phasen-Timeline, aktiven Kanälen |
| `LocationCoordinator` | `/sites`, `/locations` | Standorte mit Tanks, primärem Run, Phasen-Einträgen, Pflanzen |
| `RunCoordinator` | `/planting-runs` | Durchläufe mit Nährstoffplan, Phase-Timeline, Phasen-Einträgen |
| `AlertCoordinator` | `/tasks/overdue` | Überfällige Aufgaben für Attention-Sensoren |
| `TaskCoordinator` | `/tasks?status=pending` | Anstehende Aufgaben für Todo, Calendar, Task-Sensoren |

---

## Entwicklung: Integration in den HA-Container kopieren

```bash
kubectl exec homeassistant-0 -c homeassistant -- mkdir -p /config/custom_components
kubectl cp -c homeassistant src/ha-integration/custom_components/kamerplanter homeassistant-0:/config/custom_components/kamerplanter
kubectl exec homeassistant-0 -c homeassistant -- rm -rf /config/custom_components/kamerplanter/__pycache__
kubectl delete pod homeassistant-0 -n default
```

**Wichtig:** `__pycache__` muss gelöscht werden, sonst lädt HA den alten Bytecode. Der Pod-Neustart ist nötig damit HA die Integration neu lädt. Das PVC bleibt erhalten.
