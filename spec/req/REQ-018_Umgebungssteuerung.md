# Spezifikation: REQ-018 - Umgebungssteuerung & Aktorik

```yaml
ID: REQ-018
Titel: Umgebungssteuerung, Aktorik-Integration & Automatisierungsregeln
Kategorie: Automatisierung
Fokus: Beides
Technologie: Python, FastAPI, ArangoDB, Celery, Home Assistant, MQTT
Status: Entwurf
Version: 1.1
```

## 1. Business Case

**User Story:** "Als Gärtner möchte ich meine Umgebungsbedingungen (Licht, Temperatur, Luftfeuchtigkeit, CO₂, Bewässerung) nicht nur überwachen, sondern auch aktiv steuern — entweder automatisch basierend auf Regeln und Zeitplänen oder per manuellem Eingriff — damit meine Pflanzen durchgehend optimale Bedingungen erhalten, ohne dass ich jeden Regler selbst bedienen muss."

**User Story (Regelbasiert):** "Als Gärtner möchte ich Automatisierungsregeln definieren können, die auf Sensordaten reagieren — z.B. 'Wenn VPD > 1.5 kPa, dann Luftbefeuchter einschalten' — damit das System bei Abweichungen sofort korrigiert, auch wenn ich nicht vor Ort bin."

**User Story (Phasengebunden):** "Als Gärtner möchte ich, dass Lichtprogramme und Klimaziele automatisch angepasst werden, wenn eine Pflanze die Phase wechselt — z.B. von 18h auf 12h Licht beim Übergang in die Blüte — damit ich keine manuelle Umstellung vergesse."

**Beschreibung:**
Das System schließt den Regelkreis zwischen Sensorik (REQ-005, Input) und Aktorik (Output). Während REQ-005 die Datenerfassung abdeckt, spezifiziert REQ-018 die **Steuerungsseite**: Welche Geräte können angesprochen werden, nach welchen Regeln, und wie wird jede Aktion protokolliert.

**Kernkonzepte:**

**Aktor als Infrastruktur-Objekt:**
Ein Aktor (Actuator) ist ein steuerbares Gerät — Lampe, Lüfter, Heizung, Befeuchter, CO₂-Doser, Bewässerungsventil, Abluftventilator. Jeder Aktor wird einer Location zugeordnet und kann über verschiedene Protokolle angesprochen werden:

- **Home Assistant (primär):** Service-Calls über REST API (z.B. `light.turn_on`, `switch.turn_off`, `climate.set_temperature`)
- **MQTT (direkt):** Publish-Commands an MQTT-Topics für IoT-Geräte ohne HA-Integration
- **Manuell (Fallback):** Aktor existiert im System, wird aber physisch von Hand gesteuert — System erzeugt Tasks (REQ-006) statt direkte Befehle

**Steuerungsebenen:**

| Ebene | Beschreibung | Beispiel |
|-------|-------------|---------|
| **Zeitplan (Schedule)** | Feste Zeiten, tägliche Wiederholung | Licht an 06:00, aus 00:00 (18/6) |
| **Regelbasiert (Rule)** | Sensor-Schwellwert → Aktor-Aktion | VPD > 1.5 → Befeuchter ein |
| **Phasengebunden (Phase-Profile)** | Automatische Anpassung bei Phasenwechsel | Blüte → 12/12 Licht, Temp ↓ 2°C |
| **Manuell (Override)** | Nutzer übersteuert jede Automatik | Abluft manuell auf 100% |

**Hysterese & Debouncing:**
Regelbasierte Steuerung verwendet Hysterese, um Oszillation zu verhindern:
- **Ein-Schwellwert:** Aktor schaltet ein (z.B. VPD > 1.5)
- **Aus-Schwellwert:** Aktor schaltet aus (z.B. VPD < 1.2)
- **Mindestlaufzeit:** Aktor läuft mindestens N Minuten (verhindert schnelles An/Aus)
- **Mindestpause:** Zwischen Aus und erneutem Ein mindestens N Minuten
- **Cooldown:** Nach Zustandswechsel keine erneute Auswertung für N Sekunden

**Prioritätssystem bei Konflikt:**
Wenn mehrere Regeln denselben Aktor ansprechen, gilt:
1. **Manueller Override** (höchste Priorität, zeitlich begrenzt)
2. **Sicherheitsregeln** (z.B. Abluft bei Übertemperatur)
3. **Regelbasierte Steuerung** (Sensor-Schwellwerte)
4. **Zeitplan** (niedrigste Priorität)

**Home-Assistant-Integration (bidirektional):**
- **Outbound:** Kamerplanter sendet Service-Calls an Home Assistant (Aktoren steuern)
- **Inbound:** Home Assistant meldet Zustandsänderungen zurück (Bestätigung)
- **Entity-Mapping:** Jeder Aktor hat eine optionale `ha_entity_id` (z.B. `light.growzelt_1`, `switch.exhaust_fan`)
- **Graceful Degradation:** Wenn HA nicht erreichbar, erzeugt das System stattdessen einen manuellen Task (REQ-006)

**Phasengebundene Profile:**
Das System verknüpft REQ-003 `requirement_profiles` mit konkreten Aktor-Einstellungen:
- Bei Phasenübergang → System lädt neues Profil → setzt Aktoren um
- Graduelle Übergänge möglich (z.B. Photoperiode 18h → 12h über 7 Tage)
- Nutzer kann Profile pro Location/Phase anpassen (Override auf requirement_profile-Werte)

**VPD als gekoppelter Regelkreis:**
VPD (Dampfdruckdefizit) ist eine Funktion aus Temperatur und Luftfeuchtigkeit: `VPD = SVP(T_leaf) - AVP(T_air, rH)`. Temperatur und Luftfeuchtigkeit dürfen nicht als isolierte Regelgrößen behandelt werden, da sonst Oszillation entsteht (Befeuchter → rH↑ → VPD↓ → Befeuchter aus → Abluft → rH↓ → VPD↑ → ...). Der ControlEngine implementiert einen **VPD-Controller** als übergeordneten Regelkreis, der Befeuchter, Entfeuchter, Abluft und Heizung koordiniert steuert. Aus dem Soll-VPD des PhaseControlProfile werden die optimalen Schwellwerte für alle beteiligten Aktoren abgeleitet:
- `vpd_humidifier_on = target_vpd + 0.2 kPa`, `vpd_humidifier_off = target_vpd - 0.1 kPa`
- Schwellwerte werden bei Phasenwechsel automatisch aktualisiert

**DLI-basierte Lichtsteuerung:**
Daily Light Integral (DLI = PPFD × Stunden × 0.0036, in mol/m²/d) ist dem reinen Zeitplan überlegen. Das System akkumuliert PPFD-Messwerte (REQ-005) über den Tag:
- Gewächshaus (light_type: mixed): Kunstlicht ergänzt bei trüben Tagen, bis DLI-Ziel erreicht
- Indoor: Intensität (Dimmer) anpassen statt Photoperiode ändern
- **Kurztagspflanzen:** Photoperiode darf NICHT verlängert werden — stattdessen Intensität erhöhen

**CO₂-PPFD-Kopplung:**
CO₂-Anreicherung ist nur bei ausreichend hohem PPFD sinnvoll (Liebigs Minimumgesetz). Bei niedrigem PPFD (<200 µmol/m²/s) ist Licht der limitierende Faktor — CO₂ wird nicht genutzt. Kopplung:
- PPFD <200 µmol/m²/s: Kein CO₂-Supplement
- PPFD 200–600: CO₂ auf 600–800 ppm
- PPFD >600: CO₂ auf 800–1200 ppm (je nach Art und Nährstoffversorgung)

**DIF/DROP-Temperatursteuerung:**
DIF (Differenz Tag – Nacht) steuert Streckungswachstum über Gibberellin-Synthese:
- Positiver DIF (+2 bis +8°C): Normales Streckungswachstum
- Negativer DIF / DROP-Technik: In den 1.5–2h vor Licht-Ein Temperatur um 5–8°C absenken, dann bei Licht-Ein schnell auf Tagesniveau → kompakter Wuchs ohne chemische Wuchshemmer
- ControlEngine muss den Lichtplan der Location kennen, um zwischen Tag-/Nacht-/DROP-Sollwerten umzuschalten

**Substratfeuchte-basierte Bewässerung:**
Zusätzlich zu zeitbasierter Bewässerung ermöglicht das System sensorgesteuerte Bewässerung:
- Substratfeuchte (REQ-005) < Schwellwert → Bewässerungsventil ein (mit Hysterese)
- Tank-Füllstand (REQ-014 TankState.fill_level_percent) als Sicherheitseingang: Bei <5% → Bewässerung stoppen (Trockenlaufschutz für Pumpen)
- Bewässerungsbedarf korreliert mit VPD, PPFD und Pflanzenphase

**Konfliktgruppen:**
Aktoren in derselben `conflict_group` können nicht gleichzeitig in entgegengesetzte Richtungen arbeiten. Der ControlEngine koordiniert solche Konflikte:
- Gruppe `co2_ventilation`: Bei CO₂-Anreicherung läuft Abluft auf Minimum (z.B. 20%), um CO₂-Verlust zu minimieren, aber Übertemperatur zu verhindern
- Gruppe `heat_cool`: Heizung und Kühlung nicht gleichzeitig aktiv

**Fail-Safe-States & Notabschaltung:**
Für jeden Aktor muss ein physischer Fail-Safe-Zustand definiert sein, der bei Kommunikationsverlust (HA/MQTT-Ausfall) gilt:

| Aktor-Typ | Fail-Safe-State | Begründung |
|-----------|----------------|------------|
| Abluft | ON (100%) | Übertemperatur verhindern |
| Heizung | OFF | Brand-/Überhitzungsschutz |
| Bewässerung | OFF | Überflutungsschutz |
| CO₂-Doser | OFF | Vergiftungsschutz bei Personen |
| Licht | Letzter Zustand | Dunkelphase kritisch bei Kurztagspflanzen |
| Dosierpumpe | OFF | Überdosierungsschutz |
| Chiller | ON | Wurzelgesundheit schützen |

**Notabschaltung (Emergency Stop):** `POST /api/v1/emergency-stop` mit vordefinierten Szenarien:
- **Wasseraustritt:** Alle Pumpen/Ventile OFF
- **CO₂-Leck:** CO₂-Doser OFF, Abluft 100%
- **Brand-Alarm:** Alle Stromverbraucher OFF

## 2. ArangoDB-Modellierung

### Document-Collections:

- **`:Actuator`** — Steuerbares Gerät
  - Collection: `actuators`
  - Properties:
    - `name: str` (z.B. "Hauptlicht Zelt 1", "Abluftventilator Zelt 2")
    - `actuator_type: ActuatorType` (light | exhaust_fan | circulation_fan | heater | cooler | humidifier | dehumidifier | co2_doser | irrigation_valve | pump | dosing_pump | chiller | air_pump | uv_sterilizer | shade_screen | roof_vent | energy_screen | fogger | generic_switch)
    - `protocol: Literal['home_assistant', 'mqtt', 'manual']`
    - `ha_entity_id: Optional[str]` (Home Assistant Entity ID, z.B. `light.growzelt_1`)
    - `mqtt_command_topic: Optional[str]` (z.B. `kamerplanter/actuators/light1/set`)
    - `mqtt_state_topic: Optional[str]` (z.B. `kamerplanter/actuators/light1/state`)
    - `capabilities: list[ActuatorCapability]` (on_off | dimmable | speed_control | temperature_setpoint | timer | spectrum_control | volume_dosing)
    - `min_value: Optional[float]` (z.B. 0 für Dimmer)
    - `max_value: Optional[float]` (z.B. 100 für Dimmer)
    - `unit: Optional[str]` (z.B. "%", "°C")
    - `current_state: Optional[str]` (z.B. "on", "off", "75%")
    - `current_value: Optional[float]` (z.B. 75.0)
    - `last_state_change: Optional[datetime]`
    - `is_online: bool` (HA/MQTT-Erreichbarkeit)
    - `last_seen: Optional[datetime]`
    - `power_watts: Optional[float]` (Leistungsaufnahme für Energiekalkulation)
    - `installed_on: Optional[date]`
    - `notes: Optional[str]`

- **`:ControlSchedule`** — Zeitbasierter Steuerungsplan
  - Collection: `control_schedules`
  - Properties:
    - `name: str` (z.B. "Veg-Lichtprogramm 18/6", "Bewässerung 3x täglich")
    - `schedule_type: Literal['daily', 'weekly', 'interval', 'sunrise_sunset']`
    - `is_active: bool`
    - `priority: int` (1–100, höher = wichtiger)
    - `entries: list[ScheduleEntry]` (siehe Embedded-Modell unten)
    - `valid_from: Optional[date]` (Zeitlich begrenzter Plan)
    - `valid_until: Optional[date]`
    - `notes: Optional[str]`

- **`:ControlRule`** — Sensorbasierte Automatisierungsregel
  - Collection: `control_rules`
  - Properties:
    - `name: str` (z.B. "VPD-Korrektur Befeuchter", "Übertemperatur-Abluft")
    - `is_active: bool`
    - `priority: int` (1–100, höher = wichtiger)
    - `rule_type: Literal['threshold', 'range', 'delta', 'compound']`
    - `sensor_parameter: str` (z.B. "vpd", "temperature", "humidity", "co2")
    - `sensor_location_key: Optional[str]` (Sensor an welcher Location)
    - `condition: RuleCondition` (siehe Embedded-Modell unten)
    - `action: RuleAction` (siehe Embedded-Modell unten)
    - `hysteresis: HysteresisConfig` (siehe Embedded-Modell unten)
    - `is_safety_rule: bool` (Sicherheitsregeln haben höchste Priorität nach Override)
    - `notes: Optional[str]`

- **`:ControlEvent`** — Protokollierte Steuerungsaktion (immutable)
  - Collection: `control_events`
  - Properties:
    - `timestamp: datetime`
    - `event_source: Literal['schedule', 'rule', 'phase_change', 'manual', 'safety', 'fallback_task']`
    - `command: str` (z.B. "turn_on", "turn_off", "set_brightness", "set_temperature")
    - `value: Optional[float]` (z.B. 75.0 für Dimmer)
    - `previous_state: Optional[str]` (Zustand vorher)
    - `new_state: str` (Zustand nachher)
    - `success: bool` (HA-Bestätigung oder MQTT-ACK)
    - `error_message: Optional[str]` (bei Fehler)
    - `triggered_by_rule_key: Optional[str]` (Referenz auf ControlRule)
    - `triggered_by_schedule_key: Optional[str]` (Referenz auf ControlSchedule)
    - `triggered_by_user: Optional[str]` (Bei manuellem Override)
    - `sensor_reading_at_trigger: Optional[float]` (Sensorwert der die Regel ausgelöst hat)
    - `notes: Optional[str]`

- **`:ManualOverride`** — Temporärer manueller Eingriff
  - Collection: `manual_overrides`
  - Properties:
    - `started_at: datetime`
    - `expires_at: datetime` (Pflicht — Override darf nicht ewig gelten)
    - `override_value: Optional[float]` (z.B. 100.0 für "Abluft auf 100%")
    - `override_state: Optional[str]` (z.B. "on", "off")
    - `reason: Optional[str]` (z.B. "Hitze-Notfall, manuell Abluft aufgedreht")
    - `created_by: str`
    - `is_active: bool` (false wenn abgelaufen oder manuell beendet)

- **`:PhaseControlProfile`** — Aktoren-Konfiguration pro Phase
  - Collection: `phase_control_profiles`
  - Properties:
    - `name: str` (z.B. "Indoor Cannabis Veg", "Indoor Cannabis Bloom")
    - `target_photoperiod_hours: float` (z.B. 18.0)
    - `target_light_ppfd: int` (z.B. 600)
    - `target_light_dimmer_percent: Optional[float]`
    - `target_temperature_day_c: float`
    - `target_temperature_night_c: float`
    - `target_humidity_day_percent: int`
    - `target_humidity_night_percent: int`
    - `target_vpd_kpa: Optional[float]`
    - `co2_enrichment_ppm: Optional[int]` (null = keine CO₂-Dosierung)
    - `co2_only_during_lights_on: bool` (CO₂ nur bei Licht)
    - `irrigation_frequency_per_day: Optional[int]`
    - `irrigation_duration_seconds: Optional[int]`
    - `transition_days: int` (Tage für graduellen Übergang, z.B. 7 für Lichtumstellung)
    - `is_template: bool`
    - `notes: Optional[str]`

### Embedded-Modelle (Pydantic, nicht als separate Collections):

```python
class ScheduleEntry(BaseModel):
    """Einzelner Zeitplan-Eintrag."""
    time_on: str  # HH:MM Format (z.B. "06:00")
    time_off: str  # HH:MM Format (z.B. "00:00")
    value: Optional[float] = None  # Dimm-Level, Geschwindigkeit, etc.
    days_of_week: Optional[list[int]] = None  # 0=Mo..6=So, null=täglich

class RuleCondition(BaseModel):
    """Bedingung für eine Steuerungsregel."""
    operator: Literal['gt', 'lt', 'gte', 'lte', 'between', 'outside']
    threshold: Optional[float] = None  # für gt/lt/gte/lte
    range_min: Optional[float] = None  # für between/outside
    range_max: Optional[float] = None
    # Compound-Regeln (AND/OR-Verknüpfung)
    compound_operator: Optional[Literal['and', 'or']] = None
    sub_conditions: Optional[list['RuleCondition']] = None

class RuleAction(BaseModel):
    """Aktion bei Regelauslösung."""
    command: Literal['turn_on', 'turn_off', 'set_value', 'increase', 'decrease']
    value: Optional[float] = None  # Zielwert bei set_value
    step: Optional[float] = None  # Schrittweite bei increase/decrease

class HysteresisConfig(BaseModel):
    """Hysterese-Konfiguration gegen Oszillation."""
    on_threshold: float  # Aktor einschalten
    off_threshold: float  # Aktor ausschalten
    min_on_duration_seconds: int = 60  # Mindestlaufzeit
    min_off_duration_seconds: int = 60  # Mindestpause
    cooldown_seconds: int = 30  # Keine Neubewertung nach Zustandswechsel
```

### Edge-Collections:
```
# Aktor-Zuordnungen
has_actuator:          locations → actuators               // Location besitzt Aktor
controls_location:     actuators → locations               // Aktor steuert Location (Wirkbereich)

# Steuerungs-Verknüpfungen
has_schedule:          actuators → control_schedules       // Aktor folgt Zeitplan
has_rule:              actuators → control_rules           // Aktor wird durch Regel gesteuert
has_override:          actuators → manual_overrides        // Aktiver manueller Override

# Event-Protokollierung
actuator_event:        actuators → control_events          // Aktor hat Steuerungsaktion ausgeführt
triggered_by_rule:     control_events → control_rules      // Event wurde durch Regel ausgelöst
triggered_by_schedule: control_events → control_schedules  // Event wurde durch Zeitplan ausgelöst

# Phasen-Verknüpfung
phase_profile:         growth_phases → phase_control_profiles  // Phase → Aktor-Konfiguration
location_profile:      locations → phase_control_profiles      // Location-spezifisches Override-Profil

# Sensor-Aktor-Kopplung
monitors:              control_rules → sensors              // Regel überwacht diesen Sensor (REQ-005)
```

**ArangoDB-Graph-Definition:**
```json
{
  "edge_collection": "has_actuator",
  "from_vertex_collections": ["locations"],
  "to_vertex_collections": ["actuators"]
}
```
```json
{
  "edge_collection": "controls_location",
  "from_vertex_collections": ["actuators"],
  "to_vertex_collections": ["locations"]
}
```
```json
{
  "edge_collection": "has_schedule",
  "from_vertex_collections": ["actuators"],
  "to_vertex_collections": ["control_schedules"]
}
```
```json
{
  "edge_collection": "has_rule",
  "from_vertex_collections": ["actuators"],
  "to_vertex_collections": ["control_rules"]
}
```
```json
{
  "edge_collection": "has_override",
  "from_vertex_collections": ["actuators"],
  "to_vertex_collections": ["manual_overrides"]
}
```
```json
{
  "edge_collection": "actuator_event",
  "from_vertex_collections": ["actuators"],
  "to_vertex_collections": ["control_events"]
}
```
```json
{
  "edge_collection": "phase_profile",
  "from_vertex_collections": ["growth_phases"],
  "to_vertex_collections": ["phase_control_profiles"]
}
```
```json
{
  "edge_collection": "location_profile",
  "from_vertex_collections": ["locations"],
  "to_vertex_collections": ["phase_control_profiles"]
}
```
```json
{
  "edge_collection": "monitors",
  "from_vertex_collections": ["control_rules"],
  "to_vertex_collections": ["sensors"]
}
```

### AQL-Beispielqueries:

**1. Alle Aktoren einer Location mit aktuellem Zustand und aktiven Regeln:**
```aql
FOR actuator IN actuators
    FOR edge IN has_actuator
        FILTER edge._to == actuator._id
        FILTER edge._from == CONCAT('locations/', @location_key)
    LET active_rules = (
        FOR rule IN control_rules
            FOR re IN has_rule
                FILTER re._from == actuator._id AND re._to == rule._id
                FILTER rule.is_active == true
                RETURN { key: rule._key, name: rule.name, priority: rule.priority }
    )
    LET active_schedules = (
        FOR schedule IN control_schedules
            FOR se IN has_schedule
                FILTER se._from == actuator._id AND se._to == schedule._id
                FILTER schedule.is_active == true
                RETURN { key: schedule._key, name: schedule.name }
    )
    LET active_override = FIRST(
        FOR ov IN manual_overrides
            FOR oe IN has_override
                FILTER oe._from == actuator._id AND oe._to == ov._id
                FILTER ov.is_active == true AND ov.expires_at > DATE_NOW()
                RETURN ov
    )
    RETURN {
        actuator: actuator,
        active_rules: active_rules,
        active_schedules: active_schedules,
        has_override: active_override != null,
        override: active_override
    }
```

**2. Steuerungshistorie eines Aktors (letzte 24h):**
```aql
FOR actuator IN actuators
    FILTER actuator._key == @actuator_key
    LET events = (
        FOR event IN control_events
            FOR ee IN actuator_event
                FILTER ee._from == actuator._id AND ee._to == event._id
                FILTER event.timestamp >= DATE_SUBTRACT(DATE_NOW(), 1, "day")
                SORT event.timestamp DESC
                RETURN {
                    timestamp: event.timestamp,
                    source: event.event_source,
                    command: event.command,
                    value: event.value,
                    previous_state: event.previous_state,
                    new_state: event.new_state,
                    success: event.success,
                    sensor_value: event.sensor_reading_at_trigger,
                    rule_name: event.triggered_by_rule_key != null
                        ? FIRST(FOR r IN control_rules FILTER r._key == event.triggered_by_rule_key RETURN r.name)
                        : null
                }
    )
    RETURN {
        actuator: { key: actuator._key, name: actuator.name, type: actuator.actuator_type },
        events: events,
        total_events_24h: LENGTH(events),
        state_changes: LENGTH(events[* FILTER CURRENT.previous_state != CURRENT.new_state])
    }
```

**3. Aktive Regeln die auf einen Sensor-Parameter reagieren:**
```aql
FOR rule IN control_rules
    FILTER rule.is_active == true
    FILTER rule.sensor_parameter == @parameter  // z.B. "vpd"
    LET actuators = (
        FOR actuator IN actuators
            FOR re IN has_rule
                FILTER re._to == rule._id AND re._from == actuator._id
                RETURN { key: actuator._key, name: actuator.name, type: actuator.actuator_type }
    )
    LET sensor = FIRST(
        FOR s IN sensors
            FOR me IN monitors
                FILTER me._from == rule._id AND me._to == s._id
                RETURN { key: s._key, sensor_id: s.sensor_id, ha_entity_id: s.ha_entity_id }
    )
    RETURN {
        rule: {
            key: rule._key,
            name: rule.name,
            condition: rule.condition,
            action: rule.action,
            hysteresis: rule.hysteresis,
            is_safety: rule.is_safety_rule
        },
        actuators: actuators,
        sensor: sensor
    }
```

**4. Energieverbrauch pro Location (Aktoren mit Laufzeit):**
```aql
FOR actuator IN actuators
    FOR edge IN has_actuator
        FILTER edge._from == CONCAT('locations/', @location_key)
        FILTER edge._to == actuator._id
        FILTER actuator.power_watts != null
    LET on_events = (
        FOR event IN control_events
            FOR ee IN actuator_event
                FILTER ee._from == actuator._id AND ee._to == event._id
                FILTER event.timestamp >= @start_date AND event.timestamp <= @end_date
                FILTER event.new_state == 'on' OR (event.value != null AND event.value > 0)
                SORT event.timestamp ASC
                RETURN event
    )
    // Berechnung aus ControlEvent-Paaren (On/Off): exakte On-Zeiten
    // Für dimmbare Aktoren: Leistung = Nennleistung × (Dimmer/100)
    LET event_pairs = (
        FOR i IN 0..LENGTH(on_events)-1
            LET on_event = on_events[i]
            LET off_event = i + 1 < LENGTH(on_events) ? on_events[i+1] : null
            LET end_ts = off_event ? off_event.timestamp : @end_date
            LET duration_h = DATE_DIFF(on_event.timestamp, end_ts, "hour")
            LET dimmer = on_event.value != null ? on_event.value / 100 : 1.0
            RETURN { duration_h: duration_h, dimmer: dimmer }
    )
    LET on_hours = SUM(event_pairs[*].duration_h)
    LET weighted_kwh = SUM(
        FOR ep IN event_pairs
            RETURN (actuator.power_watts * ep.dimmer * ep.duration_h) / 1000
    )
    RETURN {
        actuator_key: actuator._key,
        actuator_name: actuator.name,
        power_watts: actuator.power_watts,
        on_hours: on_hours,
        estimated_kwh: weighted_kwh
    }
```

**5. Phasen-Profil für aktuelle Phase einer Location laden:**
```aql
LET location = DOCUMENT('locations', @location_key)

// Location-spezifisches Override-Profil?
LET location_override = FIRST(
    FOR profile IN phase_control_profiles
        FOR lp IN location_profile
            FILTER lp._from == location._id AND lp._to == profile._id
            RETURN profile
)

// Aktuelle Phase der Pflanzen an dieser Location
LET current_phases = (
    FOR plant IN plant_instances
        FILTER plant.location_key == @location_key AND plant.status == 'active'
        FOR phase IN 1..1 OUTBOUND plant GRAPH 'kamerplanter_graph'
            OPTIONS { edgeCollections: ['current_phase'] }
            RETURN DISTINCT phase._key
)

// Phasen-Profil laden (erstes Match)
LET phase_profile = FIRST(
    FOR phase_key IN current_phases
        FOR profile IN phase_control_profiles
            FOR pp IN phase_profile
                FILTER pp._from == CONCAT('growth_phases/', phase_key)
                FILTER pp._to == profile._id
                RETURN profile
)

RETURN {
    location_key: @location_key,
    has_override: location_override != null,
    profile: location_override != null ? location_override : phase_profile,
    current_phases: current_phases,
    source: location_override != null ? 'location_override' : 'phase_default'
}
```

## 3. Technische Umsetzung

### Domänenmodelle:

```python
from datetime import datetime, date, time
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, model_validator


class ActuatorType(str, Enum):
    LIGHT = "light"
    EXHAUST_FAN = "exhaust_fan"
    CIRCULATION_FAN = "circulation_fan"
    HEATER = "heater"
    COOLER = "cooler"
    HUMIDIFIER = "humidifier"
    DEHUMIDIFIER = "dehumidifier"
    CO2_DOSER = "co2_doser"
    IRRIGATION_VALVE = "irrigation_valve"
    PUMP = "pump"
    DOSING_PUMP = "dosing_pump"        # pH/EC-Korrektur, Nährstoff-Dosierung (Hydroponik)
    CHILLER = "chiller"                # Nährlösungskühlung (<22°C gegen Pythium)
    AIR_PUMP = "air_pump"              # Nährlösungsbelüftung (DWC/Hydroponik)
    UV_STERILIZER = "uv_sterilizer"    # UV-C Sterilisation Nährlösung (Rezirkulation)
    SHADE_SCREEN = "shade_screen"      # Gewächshaus-Schattierung (PPFD-Reduktion)
    ROOF_VENT = "roof_vent"            # Gewächshaus-Lüftungsklappen
    ENERGY_SCREEN = "energy_screen"    # Energieschirm (Wärmeretention nachts)
    FOGGER = "fogger"                  # Hochdruck-Vernebelung (Kühlung + Befeuchtung)
    GENERIC_SWITCH = "generic_switch"


class ActuatorCapability(str, Enum):
    ON_OFF = "on_off"
    DIMMABLE = "dimmable"
    SPEED_CONTROL = "speed_control"
    TEMPERATURE_SETPOINT = "temperature_setpoint"
    TIMER = "timer"
    SPECTRUM_CONTROL = "spectrum_control"  # Mehrkanallampen: unabhängig dimmbare Lichtkanäle
    VOLUME_DOSING = "volume_dosing"        # Dosierpumpen: exakte Volumendosierung (ml)


class ActuatorProtocol(str, Enum):
    HOME_ASSISTANT = "home_assistant"
    MQTT = "mqtt"
    MANUAL = "manual"


class ScheduleType(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    INTERVAL = "interval"
    SUNRISE_SUNSET = "sunrise_sunset"


class RuleType(str, Enum):
    THRESHOLD = "threshold"
    RANGE = "range"
    DELTA = "delta"
    COMPOUND = "compound"


class ConditionOperator(str, Enum):
    GT = "gt"
    LT = "lt"
    GTE = "gte"
    LTE = "lte"
    BETWEEN = "between"
    OUTSIDE = "outside"


class ActionCommand(str, Enum):
    TURN_ON = "turn_on"
    TURN_OFF = "turn_off"
    SET_VALUE = "set_value"
    INCREASE = "increase"
    DECREASE = "decrease"


class EventSource(str, Enum):
    SCHEDULE = "schedule"
    RULE = "rule"
    PHASE_CHANGE = "phase_change"
    MANUAL = "manual"
    SAFETY = "safety"
    FALLBACK_TASK = "fallback_task"


# --- Embedded Models ---

class ScheduleEntry(BaseModel):
    """Einzelner Zeitplan-Eintrag."""
    time_on: str = Field(pattern=r'^\d{2}:\d{2}$')
    time_off: str = Field(pattern=r'^\d{2}:\d{2}$')
    value: Optional[float] = None
    days_of_week: Optional[list[int]] = Field(None, description="0=Mo..6=So, null=täglich")

    @model_validator(mode='after')
    def validate_days(self):
        if self.days_of_week is not None:
            for d in self.days_of_week:
                if d < 0 or d > 6:
                    raise ValueError(f"Ungültiger Wochentag: {d} (0=Mo..6=So)")
        return self


class RuleCondition(BaseModel):
    """Bedingung für eine Steuerungsregel."""
    operator: ConditionOperator
    threshold: Optional[float] = None
    range_min: Optional[float] = None
    range_max: Optional[float] = None
    compound_operator: Optional[str] = Field(None, pattern=r'^(and|or)$')
    sub_conditions: Optional[list['RuleCondition']] = None

    @model_validator(mode='after')
    def validate_condition(self):
        if self.operator in (ConditionOperator.GT, ConditionOperator.LT,
                            ConditionOperator.GTE, ConditionOperator.LTE):
            if self.threshold is None:
                raise ValueError(f"threshold erforderlich für Operator {self.operator}")
        elif self.operator in (ConditionOperator.BETWEEN, ConditionOperator.OUTSIDE):
            if self.range_min is None or self.range_max is None:
                raise ValueError(f"range_min und range_max erforderlich für Operator {self.operator}")
            if self.range_min >= self.range_max:
                raise ValueError("range_min muss kleiner als range_max sein")
        return self


class RuleAction(BaseModel):
    """Aktion bei Regelauslösung."""
    command: ActionCommand
    value: Optional[float] = None
    step: Optional[float] = None

    @model_validator(mode='after')
    def validate_action(self):
        if self.command == ActionCommand.SET_VALUE and self.value is None:
            raise ValueError("value erforderlich für set_value")
        if self.command in (ActionCommand.INCREASE, ActionCommand.DECREASE):
            if self.step is None:
                raise ValueError(f"step erforderlich für {self.command}")
        return self


class HysteresisConfig(BaseModel):
    """Hysterese-Konfiguration gegen Oszillation."""
    on_threshold: float
    off_threshold: float
    min_on_duration_seconds: int = Field(default=60, ge=0, le=3600)
    min_off_duration_seconds: int = Field(default=60, ge=0, le=3600)
    cooldown_seconds: int = Field(default=30, ge=0, le=600)

    @model_validator(mode='after')
    def validate_thresholds(self):
        if self.on_threshold == self.off_threshold:
            raise ValueError(
                "on_threshold und off_threshold müssen unterschiedlich sein "
                "(sonst keine Hysterese)"
            )
        return self


# --- Hauptmodelle ---

class Actuator(BaseModel):
    """Steuerbares Gerät."""

    key: Optional[str] = Field(None, alias='_key')
    name: str = Field(min_length=1, max_length=200)
    actuator_type: ActuatorType
    protocol: ActuatorProtocol
    ha_entity_id: Optional[str] = Field(None, max_length=200)
    mqtt_command_topic: Optional[str] = Field(None, max_length=500)
    mqtt_state_topic: Optional[str] = Field(None, max_length=500)
    capabilities: list[ActuatorCapability] = Field(default_factory=lambda: [ActuatorCapability.ON_OFF])
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    unit: Optional[str] = Field(None, max_length=20)
    current_state: Optional[str] = None
    current_value: Optional[float] = None
    last_state_change: Optional[datetime] = None
    is_online: bool = True
    last_seen: Optional[datetime] = None
    power_watts: Optional[float] = Field(None, ge=0, le=100000)
    fail_safe_state: Optional[str] = Field(
        None,
        description="Physischer Zustand bei Kommunikationsverlust (HA/MQTT-Ausfall). "
                    "Empfehlungen: Abluft→'on', Heizung→'off', Bewässerung→'off', "
                    "CO₂-Doser→'off' (Vergiftungsschutz), Licht→'last' (Dunkelphase "
                    "kritisch bei Kurztagspflanzen)."
    )
    fail_safe_value: Optional[float] = Field(
        None,
        description="Wert für fail_safe_state, z.B. 100.0 für Abluft auf 100%."
    )
    conflict_group: Optional[str] = Field(
        None, max_length=50,
        description="Konfliktgruppe für Aktoren, die nicht gleichzeitig in "
                    "entgegengesetzte Richtungen arbeiten sollen. "
                    "Z.B. 'co2_ventilation': CO₂-Doser und Abluft."
    )
    installed_on: Optional[date] = None
    notes: Optional[str] = Field(None, max_length=2000)

    @model_validator(mode='after')
    def validate_protocol_fields(self):
        if self.protocol == ActuatorProtocol.HOME_ASSISTANT:
            if not self.ha_entity_id:
                raise ValueError("ha_entity_id erforderlich für Home Assistant-Protokoll")
        elif self.protocol == ActuatorProtocol.MQTT:
            if not self.mqtt_command_topic:
                raise ValueError("mqtt_command_topic erforderlich für MQTT-Protokoll")
        return self

    @model_validator(mode='after')
    def validate_dimmable_range(self):
        if ActuatorCapability.DIMMABLE in self.capabilities:
            if self.min_value is None or self.max_value is None:
                raise ValueError("min_value und max_value erforderlich für dimmbare Aktoren")
        return self


class ControlSchedule(BaseModel):
    """Zeitbasierter Steuerungsplan."""

    key: Optional[str] = Field(None, alias='_key')
    name: str = Field(min_length=1, max_length=200)
    schedule_type: ScheduleType
    is_active: bool = True
    priority: int = Field(default=50, ge=1, le=100)
    entries: list[ScheduleEntry] = Field(min_length=1)
    valid_from: Optional[date] = None
    valid_until: Optional[date] = None
    notes: Optional[str] = Field(None, max_length=2000)

    @model_validator(mode='after')
    def validate_date_range(self):
        if self.valid_from and self.valid_until:
            if self.valid_from >= self.valid_until:
                raise ValueError("valid_from muss vor valid_until liegen")
        return self


class ControlRule(BaseModel):
    """Sensorbasierte Automatisierungsregel."""

    key: Optional[str] = Field(None, alias='_key')
    name: str = Field(min_length=1, max_length=200)
    is_active: bool = True
    priority: int = Field(default=50, ge=1, le=100)
    rule_type: RuleType
    sensor_parameter: str = Field(min_length=1, max_length=50)
    sensor_location_key: Optional[str] = None
    condition: RuleCondition
    action: RuleAction
    hysteresis: HysteresisConfig
    is_safety_rule: bool = False
    notes: Optional[str] = Field(None, max_length=2000)


class ControlEvent(BaseModel):
    """Protokollierte Steuerungsaktion — immutable."""

    key: Optional[str] = Field(None, alias='_key')
    timestamp: datetime
    event_source: EventSource
    command: str = Field(min_length=1, max_length=100)
    value: Optional[float] = None
    previous_state: Optional[str] = None
    new_state: str
    success: bool
    error_message: Optional[str] = Field(None, max_length=1000)
    triggered_by_rule_key: Optional[str] = None
    triggered_by_schedule_key: Optional[str] = None
    triggered_by_user: Optional[str] = None
    sensor_reading_at_trigger: Optional[float] = None
    notes: Optional[str] = Field(None, max_length=2000)


class ManualOverride(BaseModel):
    """Temporärer manueller Eingriff."""

    key: Optional[str] = Field(None, alias='_key')
    started_at: datetime
    expires_at: datetime
    override_value: Optional[float] = None
    override_state: Optional[str] = None
    reason: Optional[str] = Field(None, max_length=500)
    created_by: str = Field(min_length=1, max_length=100)
    is_active: bool = True

    @model_validator(mode='after')
    def validate_expiry(self):
        if self.expires_at <= self.started_at:
            raise ValueError("expires_at muss nach started_at liegen")
        return self

    @model_validator(mode='after')
    def validate_override_value(self):
        if self.override_value is None and self.override_state is None:
            raise ValueError("Entweder override_value oder override_state erforderlich")
        return self


class PhaseControlProfile(BaseModel):
    """Aktoren-Konfiguration pro Phase."""

    key: Optional[str] = Field(None, alias='_key')
    name: str = Field(min_length=1, max_length=200)
    target_photoperiod_hours: float = Field(ge=0, le=24)
    target_light_ppfd: int = Field(ge=0, le=2000)
    target_light_dimmer_percent: Optional[float] = Field(None, ge=0, le=100)
    target_temperature_day_c: float = Field(ge=5, le=45)
    target_temperature_night_c: float = Field(ge=5, le=45)
    target_humidity_day_percent: int = Field(ge=0, le=100)
    target_humidity_night_percent: int = Field(ge=0, le=100)
    target_vpd_kpa: Optional[float] = Field(None, ge=0, le=5)
    co2_enrichment_ppm: Optional[int] = Field(None, ge=0, le=2000)
    co2_only_during_lights_on: bool = True
    co2_min_ppfd_threshold: Optional[int] = Field(
        None, ge=0, le=2000,
        description="Mindest-PPFD für CO₂-Dosierung (Liebigs Minimumgesetz: "
                    "bei niedrigem PPFD ist Licht der limitierende Faktor, "
                    "zusätzliches CO₂ wird nicht genutzt). "
                    "Typisch: 200 µmol/m²/s"
    )
    target_dli_mol: Optional[float] = Field(
        None, ge=0, le=65,
        description="Tageslicht-Integral (DLI) in mol/m²/d. "
                    "Salate: 12–17, Kräuter: 15–20, Cannabis: 35–45, Tomate: 20–30. "
                    "System kann Lichtintensität anpassen, um DLI-Ziel zu erreichen. "
                    "Achtung: Bei Kurztagspflanzen Photoperiode NICHT verlängern — "
                    "stattdessen Intensität erhöhen."
    )
    target_light_spectrum: Optional[dict] = Field(
        None,
        description="Ziel-Lichtspektrum als Anteilswerte {blue, green, red, far_red, uv_a}. "
                    "Analog zu REQ-003 requirement_profiles.light_spectrum. "
                    "Ermöglicht Kanal-Steuerung bei Mehrkanallampen."
    )
    photoperiod_is_critical: bool = Field(
        default=False,
        description="Wenn True, ist die ununterbrochene Dunkelphase biologisch kritisch "
                    "(Kurztagspflanzen wie Cannabis). Jede Lichtexposition >1 µmol/m²/s "
                    "während der Nacht kann Blüteninduktion stören. Kein Licht-Aktor "
                    "darf während der Dunkelphase aktiviert werden."
    )
    dif_target_c: Optional[float] = Field(
        None, ge=-4, le=12,
        description="Ziel-DIF (Tag minus Nacht Temperatur). "
                    "Positiver DIF: Streckungswachstum. "
                    "Negativer DIF: Kompakter Wuchs (Gibberellin-Hemmung). "
                    "Wird aus target_temperature_day/night_c abgeleitet, wenn nicht gesetzt."
    )
    pre_dawn_drop_c: Optional[float] = Field(
        None, ge=0, le=10,
        description="DROP-Technik: Temperaturabsenkung in °C in den Stunden vor Licht-Ein. "
                    "Hemmt Gibberellin-Synthese → kompakter Wuchs ohne chemische Wuchshemmer."
    )
    pre_dawn_drop_hours: Optional[float] = Field(
        None, ge=0, le=4,
        description="Dauer der DROP-Phase in Stunden vor Licht-Ein (typisch 1.5–2h)."
    )
    irrigation_frequency_per_day: Optional[int] = Field(None, ge=0, le=48)
    irrigation_duration_seconds: Optional[int] = Field(None, ge=0, le=3600)
    irrigation_volume_ml_per_event: Optional[int] = Field(
        None, ge=0, le=100000,
        description="Bewässerungsvolumen pro Ereignis in ml (präziser als Dauer × Druck)."
    )
    target_drain_percent: Optional[int] = Field(
        None, ge=0, le=50,
        description="Ziel-Drainageanteil bei Drain-to-Waste (typisch 10–30%). "
                    "Hilft Salzakkumulation im Substrat zu verhindern."
    )
    transition_days: int = Field(default=0, ge=0, le=30)
    is_template: bool = False
    notes: Optional[str] = Field(None, max_length=2000)

    @model_validator(mode='after')
    def validate_temperature_differential(self):
        """
        DIF (Differenz Tag-Nacht) validieren:
        - Positiver DIF (Tag > Nacht): Normal, max +12°C
        - Negativer DIF (Nacht > Tag): Kompakter Wuchs, max -4°C
        Extremer DIF schädigt Pflanzen durch Dunkelatmungs-Überschuss
        oder Temperaturschock.
        """
        dif = self.target_temperature_day_c - self.target_temperature_night_c
        if dif > 12:
            raise ValueError(
                f"Tag-/Nachttemperatur-Differenz zu groß ({dif:.1f}°C). "
                f"Maximaler DIF: 12°C (empfohlen: 2–8°C)"
            )
        if dif < -4:
            raise ValueError(
                f"Negativer DIF von {dif:.1f}°C ist physiologisch extrem. "
                f"Maximaler negativer DIF: -4°C"
            )
        return self
```

### Engines:

**1. ControlEngine — Zentrale Steuerungslogik:**
```python
class ControlEngine:
    """Entscheidet basierend auf Regeln, Zeitplänen und Overrides was ein Aktor tun soll."""

    PRIORITY_LEVELS = {
        'manual_override': 1000,
        'safety_rule': 900,
        'rule': 500,
        'schedule': 100,
    }

    def evaluate_actuator_state(
        self,
        actuator: dict,
        active_rules: list[dict],
        active_schedules: list[dict],
        active_override: Optional[dict],
        current_sensor_readings: dict[str, float],
        now: datetime,
    ) -> Optional[dict]:
        """
        Bestimmt den gewünschten Zustand eines Aktors.
        Returns: {command, value, source, source_key, priority} oder None (keine Änderung).
        """
        desired_states: list[dict] = []

        # 1. Manueller Override (höchste Priorität)
        if active_override and active_override.get('is_active'):
            if now < active_override['expires_at']:
                desired_states.append({
                    'command': 'set_value' if active_override.get('override_value') else 'turn_on',
                    'value': active_override.get('override_value'),
                    'state': active_override.get('override_state', 'on'),
                    'source': 'manual',
                    'source_key': active_override['_key'],
                    'priority': self.PRIORITY_LEVELS['manual_override'],
                })

        # 2. Sicherheitsregeln
        for rule in active_rules:
            if rule.get('is_safety_rule'):
                result = self._evaluate_rule(rule, current_sensor_readings, actuator)
                if result:
                    result['priority'] = self.PRIORITY_LEVELS['safety_rule']
                    desired_states.append(result)

        # 3. Reguläre Regeln
        for rule in active_rules:
            if not rule.get('is_safety_rule'):
                result = self._evaluate_rule(rule, current_sensor_readings, actuator)
                if result:
                    result['priority'] = self.PRIORITY_LEVELS['rule'] + rule.get('priority', 50)
                    desired_states.append(result)

        # 4. Zeitpläne
        for schedule in active_schedules:
            result = self._evaluate_schedule(schedule, now)
            if result:
                result['priority'] = self.PRIORITY_LEVELS['schedule'] + schedule.get('priority', 50)
                desired_states.append(result)

        if not desired_states:
            return None

        # Höchste Priorität gewinnt
        desired_states.sort(key=lambda x: x['priority'], reverse=True)
        winner = desired_states[0]

        # Prüfe ob Zustandsänderung nötig
        if self._is_same_state(actuator, winner):
            return None

        return winner

    def _evaluate_rule(
        self,
        rule: dict,
        sensor_readings: dict[str, float],
        actuator: dict,
    ) -> Optional[dict]:
        """Prüft ob eine Regel auslöst."""
        param = rule['sensor_parameter']
        if param not in sensor_readings:
            return None

        reading = sensor_readings[param]
        condition = rule['condition']
        hysteresis = rule['hysteresis']

        current_state = actuator.get('current_state', 'off')
        is_on = current_state != 'off'

        # Hysterese-Logik
        should_on = self._check_condition(condition, reading, hysteresis['on_threshold'])
        should_off = not self._check_condition(condition, reading, hysteresis['off_threshold'])

        # Mindestlaufzeit/-pause prüfen
        last_change = actuator.get('last_state_change')
        if last_change:
            seconds_since = (datetime.now() - last_change).total_seconds()
            if is_on and seconds_since < hysteresis.get('min_on_duration_seconds', 60):
                return None  # Noch in Mindestlaufzeit
            if not is_on and seconds_since < hysteresis.get('min_off_duration_seconds', 60):
                return None  # Noch in Mindestpause

        if not is_on and should_on:
            return {
                'command': rule['action']['command'],
                'value': rule['action'].get('value'),
                'state': 'on',
                'source': 'safety' if rule.get('is_safety_rule') else 'rule',
                'source_key': rule['_key'],
                'sensor_reading': reading,
            }
        elif is_on and should_off:
            return {
                'command': 'turn_off',
                'value': None,
                'state': 'off',
                'source': 'safety' if rule.get('is_safety_rule') else 'rule',
                'source_key': rule['_key'],
                'sensor_reading': reading,
            }

        return None

    def _check_condition(
        self,
        condition: dict,
        value: float,
        threshold: float,
    ) -> bool:
        """Prüft eine Schwellwert-Bedingung."""
        op = condition['operator']
        if op == 'gt':
            return value > threshold
        elif op == 'lt':
            return value < threshold
        elif op == 'gte':
            return value >= threshold
        elif op == 'lte':
            return value <= threshold
        elif op == 'between':
            return condition['range_min'] <= value <= condition['range_max']
        elif op == 'outside':
            return value < condition['range_min'] or value > condition['range_max']
        return False

    def _evaluate_schedule(
        self,
        schedule: dict,
        now: datetime,
    ) -> Optional[dict]:
        """Prüft ob ein Zeitplan-Eintrag aktiv ist."""
        current_time = now.strftime('%H:%M')
        current_weekday = now.weekday()

        for entry in schedule.get('entries', []):
            # Wochentag-Filter
            if entry.get('days_of_week') and current_weekday not in entry['days_of_week']:
                continue

            time_on = entry['time_on']
            time_off = entry['time_off']

            # Mitternachts-Übergang (z.B. 06:00 → 00:00)
            if time_on <= time_off:
                is_active = time_on <= current_time < time_off
            else:
                is_active = current_time >= time_on or current_time < time_off

            if is_active:
                return {
                    'command': 'set_value' if entry.get('value') is not None else 'turn_on',
                    'value': entry.get('value'),
                    'state': 'on',
                    'source': 'schedule',
                    'source_key': schedule['_key'],
                }

        # Wenn kein Eintrag aktiv → Aktor aus
        return {
            'command': 'turn_off',
            'value': None,
            'state': 'off',
            'source': 'schedule',
            'source_key': schedule['_key'],
        }

    def _is_same_state(self, actuator: dict, desired: dict) -> bool:
        """Prüft ob der Aktor bereits im gewünschten Zustand ist."""
        if actuator.get('current_state') != desired.get('state'):
            return False
        if desired.get('value') is not None:
            if actuator.get('current_value') != desired['value']:
                return False
        return True
```

**2. HomeAssistantClient — HA Service-Calls:**
```python
class HomeAssistantClient:
    """Kommunikation mit Home Assistant REST API."""

    def __init__(self, base_url: str, access_token: str):
        self.base_url = base_url.rstrip('/')
        self.access_token = access_token
        self.headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json',
        }

    async def call_service(
        self,
        domain: str,
        service: str,
        entity_id: str,
        data: Optional[dict] = None,
    ) -> dict:
        """
        Ruft einen Home Assistant Service auf.
        z.B. domain='light', service='turn_on', entity_id='light.growzelt_1'
        """
        url = f"{self.base_url}/api/services/{domain}/{service}"
        payload = {'entity_id': entity_id}
        if data:
            payload.update(data)
        # HTTP POST an HA API
        # Returns: response dict
        ...

    async def get_entity_state(self, entity_id: str) -> dict:
        """Aktuellen Zustand einer HA-Entity abrufen."""
        url = f"{self.base_url}/api/states/{entity_id}"
        # HTTP GET
        ...

    def map_command_to_ha_service(
        self,
        actuator_type: str,
        command: str,
        value: Optional[float],
    ) -> tuple[str, str, dict]:
        """
        Übersetzt Kamerplanter-Command in HA-Service-Call.
        Returns: (domain, service, service_data)
        """
        mapping = {
            'light': {
                'turn_on': ('light', 'turn_on', {}),
                'turn_off': ('light', 'turn_off', {}),
                'set_value': ('light', 'turn_on', {'brightness_pct': value}),
            },
            'exhaust_fan': {
                'turn_on': ('fan', 'turn_on', {}),
                'turn_off': ('fan', 'turn_off', {}),
                'set_value': ('fan', 'set_percentage', {'percentage': value}),
            },
            'heater': {
                'turn_on': ('climate', 'turn_on', {}),
                'turn_off': ('climate', 'turn_off', {}),
                'set_value': ('climate', 'set_temperature', {'temperature': value}),
            },
            'humidifier': {
                'turn_on': ('humidifier', 'turn_on', {}),
                'turn_off': ('humidifier', 'turn_off', {}),
                'set_value': ('humidifier', 'set_humidity', {'humidity': value}),
            },
            'generic_switch': {
                'turn_on': ('switch', 'turn_on', {}),
                'turn_off': ('switch', 'turn_off', {}),
            },
        }
        # Fallback für unbekannte Typen
        type_map = mapping.get(actuator_type, mapping['generic_switch'])
        return type_map.get(command, ('switch', command, {}))
```

**3. PhaseTransitionHandler — Phasengebundene Steuerung:**
```python
class PhaseTransitionHandler:
    """Reagiert auf Phasenübergänge (REQ-003) und passt Aktoren an."""

    def on_phase_transition(
        self,
        plant_instance_key: str,
        location_key: str,
        old_phase_key: str,
        new_phase_key: str,
        new_profile: Optional[dict],
    ) -> list[dict]:
        """
        Erzeugt Steuerungsanweisungen für den Phasenübergang.
        Returns: Liste von {actuator_key, command, value, transition_days}
        """
        if new_profile is None:
            return []

        commands = []
        transition_days = new_profile.get('transition_days', 0)

        # Licht-Anpassung
        if new_profile.get('target_photoperiod_hours'):
            commands.append({
                'actuator_type': 'light',
                'parameter': 'photoperiod',
                'target_value': new_profile['target_photoperiod_hours'],
                'transition_days': transition_days,
                'note': f"Photoperiode → {new_profile['target_photoperiod_hours']}h",
            })

        if new_profile.get('target_light_dimmer_percent') is not None:
            commands.append({
                'actuator_type': 'light',
                'parameter': 'dimmer',
                'target_value': new_profile['target_light_dimmer_percent'],
                'transition_days': transition_days,
                'note': f"Lichtintensität → {new_profile['target_light_dimmer_percent']}%",
            })

        # Temperatur-Anpassung
        if new_profile.get('target_temperature_day_c'):
            commands.append({
                'actuator_type': 'heater',
                'parameter': 'temperature',
                'target_value': new_profile['target_temperature_day_c'],
                'transition_days': 0,  # Temperatur sofort
                'note': f"Tagtemperatur → {new_profile['target_temperature_day_c']}°C",
            })

        # CO₂-Anpassung
        if new_profile.get('co2_enrichment_ppm') is not None:
            commands.append({
                'actuator_type': 'co2_doser',
                'parameter': 'co2_ppm',
                'target_value': new_profile['co2_enrichment_ppm'],
                'transition_days': 0,
                'note': f"CO₂ → {new_profile['co2_enrichment_ppm']} ppm",
            })

        return commands

    def calculate_gradual_transition(
        self,
        current_value: float,
        target_value: float,
        transition_days: int,
        current_day: int,
    ) -> float:
        """
        Berechnet den Wert für den aktuellen Tag eines graduellen Übergangs.
        Linear interpolation.
        """
        if transition_days <= 0 or current_day >= transition_days:
            return target_value
        progress = current_day / transition_days
        return round(current_value + (target_value - current_value) * progress, 1)
```

### Datenvalidierung:

```python
class ActuatorAssignmentValidator(BaseModel):
    """Validiert die Zuordnung Aktor → Location."""

    actuator_key: str
    location_key: str
    actuator_type: ActuatorType
    location_type: str  # 'indoor', 'outdoor', 'greenhouse'

    @model_validator(mode='after')
    def validate_type_compatibility(self):
        """CO₂-Doser und Befeuchter nur bei geschlossenen Räumen sinnvoll."""
        indoor_only = {ActuatorType.CO2_DOSER, ActuatorType.DEHUMIDIFIER}
        if self.actuator_type in indoor_only and self.location_type == 'outdoor':
            raise ValueError(
                f"{self.actuator_type.value} ist nur für Indoor-Locations sinnvoll, "
                f"nicht für Outdoor ('{self.location_key}')"
            )
        return self


class SchedulePhotoperiodValidator(BaseModel):
    """Validiert ein Licht-Zeitplan gegen Photoperioden-Anforderungen."""

    schedule_entries: list[ScheduleEntry]
    target_photoperiod_hours: float

    @model_validator(mode='after')
    def validate_photoperiod(self):
        """Prüft ob die Schedule-Einträge die gewünschte Photoperiode ergeben."""
        total_on_hours = 0.0
        for entry in self.schedule_entries:
            on_h, on_m = map(int, entry.time_on.split(':'))
            off_h, off_m = map(int, entry.time_off.split(':'))
            on_minutes = on_h * 60 + on_m
            off_minutes = off_h * 60 + off_m
            if off_minutes <= on_minutes:
                off_minutes += 24 * 60  # Mitternachtsübergang
            total_on_hours += (off_minutes - on_minutes) / 60

        deviation = abs(total_on_hours - self.target_photoperiod_hours)
        if deviation > 0.5:
            raise ValueError(
                f"Zeitplan ergibt {total_on_hours:.1f}h Beleuchtung, "
                f"Ziel ist {self.target_photoperiod_hours}h "
                f"(Abweichung: {deviation:.1f}h)"
            )
        return self
```

### REST-API-Endpunkte:
```
# Aktoren-CRUD
POST   /api/v1/locations/{location_key}/actuators              — Aktor erstellen und Location zuordnen
GET    /api/v1/locations/{location_key}/actuators               — Alle Aktoren einer Location
GET    /api/v1/actuators                                        — Alle Aktoren (Filter: type, protocol, is_online)
GET    /api/v1/actuators/{actuator_key}                         — Aktor-Details inkl. aktiven Regeln/Schedules
PUT    /api/v1/actuators/{actuator_key}                         — Aktor-Stammdaten aktualisieren
DELETE /api/v1/actuators/{actuator_key}                         — Aktor entfernen

# Manuelle Steuerung
POST   /api/v1/actuators/{actuator_key}/command                 — Direkten Befehl senden (turn_on, turn_off, set_value)
POST   /api/v1/actuators/{actuator_key}/override                — Manuellen Override setzen (zeitlich begrenzt)
DELETE /api/v1/actuators/{actuator_key}/override                — Override aufheben
GET    /api/v1/actuators/{actuator_key}/state                   — Aktuellen Zustand abrufen (inkl. HA-Abfrage)

# Zeitpläne
POST   /api/v1/actuators/{actuator_key}/schedules               — Zeitplan erstellen
GET    /api/v1/actuators/{actuator_key}/schedules               — Alle Zeitpläne eines Aktors
PUT    /api/v1/actuators/{actuator_key}/schedules/{schedule_key} — Zeitplan anpassen
DELETE /api/v1/actuators/{actuator_key}/schedules/{schedule_key} — Zeitplan löschen
POST   /api/v1/actuators/{actuator_key}/schedules/{schedule_key}/toggle — Zeitplan aktivieren/deaktivieren

# Automatisierungsregeln
POST   /api/v1/actuators/{actuator_key}/rules                   — Regel erstellen
GET    /api/v1/actuators/{actuator_key}/rules                   — Alle Regeln eines Aktors
GET    /api/v1/rules                                            — Alle Regeln (Filter: parameter, is_active, is_safety)
PUT    /api/v1/actuators/{actuator_key}/rules/{rule_key}        — Regel anpassen
DELETE /api/v1/actuators/{actuator_key}/rules/{rule_key}        — Regel löschen
POST   /api/v1/actuators/{actuator_key}/rules/{rule_key}/toggle — Regel aktivieren/deaktivieren
POST   /api/v1/rules/{rule_key}/test                            — Regel gegen aktuelle Sensorwerte testen (Dry-Run)

# Steuerungshistorie
GET    /api/v1/actuators/{actuator_key}/events                  — Event-Log (Pagination + Zeitraum-Filter)
GET    /api/v1/actuators/{actuator_key}/events/stats            — Statistik (On-Time, Schaltzyklen, Energieverbrauch)
GET    /api/v1/locations/{location_key}/control-events           — Alle Events einer Location

# Phasen-Profile
POST   /api/v1/phase-control-profiles                           — Profil erstellen
GET    /api/v1/phase-control-profiles                           — Alle Profile (Filter: is_template)
GET    /api/v1/phase-control-profiles/{profile_key}             — Profil-Details
PUT    /api/v1/phase-control-profiles/{profile_key}             — Profil aktualisieren
DELETE /api/v1/phase-control-profiles/{profile_key}             — Profil löschen
POST   /api/v1/phase-control-profiles/{profile_key}/apply       — Profil auf Location anwenden

# Home Assistant Integration
GET    /api/v1/integrations/home-assistant/status                — HA-Verbindungsstatus
GET    /api/v1/integrations/home-assistant/entities              — Verfügbare HA-Entities für Mapping
POST   /api/v1/integrations/home-assistant/test                  — Verbindungstest

# Übergreifend
GET    /api/v1/locations/{location_key}/control-status           — Gesamtstatus aller Aktoren einer Location
GET    /api/v1/locations/{location_key}/energy                   — Energieverbrauch-Schätzung
```

### Seed-Daten:
```json
// actuators collection
{ "_key": "light_zelt1", "name": "Hauptlicht Zelt 1", "actuator_type": "light", "protocol": "home_assistant", "ha_entity_id": "light.growzelt_1", "capabilities": ["on_off", "dimmable"], "min_value": 0, "max_value": 100, "unit": "%", "current_state": "on", "current_value": 100, "is_online": true, "power_watts": 480, "fail_safe_state": "last", "installed_on": "2025-06-01", "notes": "Samsung LM301H 480W LED" }
{ "_key": "exhaust_zelt1", "name": "Abluft Zelt 1", "actuator_type": "exhaust_fan", "protocol": "home_assistant", "ha_entity_id": "fan.abluft_zelt_1", "capabilities": ["on_off", "speed_control"], "min_value": 0, "max_value": 100, "unit": "%", "current_state": "on", "current_value": 60, "is_online": true, "power_watts": 95, "fail_safe_state": "on", "fail_safe_value": 100, "conflict_group": "co2_ventilation", "installed_on": "2025-06-01" }
{ "_key": "humidifier_zelt1", "name": "Befeuchter Zelt 1", "actuator_type": "humidifier", "protocol": "home_assistant", "ha_entity_id": "humidifier.zelt_1", "capabilities": ["on_off"], "current_state": "off", "is_online": true, "power_watts": 30, "fail_safe_state": "off" }
{ "_key": "heater_zelt1", "name": "Heizstrahler Zelt 1", "actuator_type": "heater", "protocol": "mqtt", "mqtt_command_topic": "kamerplanter/actuators/heater_zelt1/set", "mqtt_state_topic": "kamerplanter/actuators/heater_zelt1/state", "capabilities": ["on_off", "temperature_setpoint"], "min_value": 15, "max_value": 30, "unit": "°C", "current_state": "off", "is_online": true, "power_watts": 150, "fail_safe_state": "off" }
{ "_key": "co2_doser_zelt1", "name": "CO₂-Doser Zelt 1", "actuator_type": "co2_doser", "protocol": "home_assistant", "ha_entity_id": "switch.co2_zelt_1", "capabilities": ["on_off"], "current_state": "off", "is_online": true, "power_watts": 10, "fail_safe_state": "off", "conflict_group": "co2_ventilation" }
{ "_key": "irrigation_zelt1", "name": "Bewässerungsventil Zelt 1", "actuator_type": "irrigation_valve", "protocol": "home_assistant", "ha_entity_id": "switch.irrigation_zelt_1", "capabilities": ["on_off", "timer"], "current_state": "off", "is_online": true, "power_watts": 5, "fail_safe_state": "off" }
{ "_key": "fan_outdoor", "name": "Umluft-Ventilator Garten-Setup", "actuator_type": "circulation_fan", "protocol": "manual", "capabilities": ["on_off", "speed_control"], "min_value": 1, "max_value": 3, "unit": "Stufe", "current_state": null, "is_online": false, "notes": "Manuell bedient — System erzeugt Tasks" }

// has_actuator edges
{ "_from": "locations/growzelt1", "_to": "actuators/light_zelt1" }
{ "_from": "locations/growzelt1", "_to": "actuators/exhaust_zelt1" }
{ "_from": "locations/growzelt1", "_to": "actuators/humidifier_zelt1" }
{ "_from": "locations/growzelt1", "_to": "actuators/heater_zelt1" }
{ "_from": "locations/growzelt1", "_to": "actuators/irrigation_zelt1" }

// controls_location edges
{ "_from": "actuators/light_zelt1", "_to": "locations/growzelt1" }
{ "_from": "actuators/exhaust_zelt1", "_to": "locations/growzelt1" }
{ "_from": "actuators/humidifier_zelt1", "_to": "locations/growzelt1" }

// control_schedules collection
{ "_key": "sched_light_veg", "name": "Veg-Lichtprogramm 18/6", "schedule_type": "daily", "is_active": true, "priority": 50, "entries": [{"time_on": "06:00", "time_off": "00:00", "value": 100}], "notes": "Vegetative Phase: 18h Licht / 6h Dunkel" }
{ "_key": "sched_light_bloom", "name": "Bloom-Lichtprogramm 12/12", "schedule_type": "daily", "is_active": false, "priority": 50, "entries": [{"time_on": "06:00", "time_off": "18:00", "value": 100}], "notes": "Blütephase: 12h Licht / 12h Dunkel" }
{ "_key": "sched_irrigation_3x", "name": "Bewässerung 3x täglich", "schedule_type": "daily", "is_active": true, "priority": 50, "entries": [{"time_on": "07:00", "time_off": "07:03"}, {"time_on": "13:00", "time_off": "13:03"}, {"time_on": "19:00", "time_off": "19:03"}] }

// has_schedule edges
{ "_from": "actuators/light_zelt1", "_to": "control_schedules/sched_light_veg" }
{ "_from": "actuators/irrigation_zelt1", "_to": "control_schedules/sched_irrigation_3x" }

// control_rules collection
{ "_key": "rule_vpd_humid", "name": "VPD-Korrektur Befeuchter", "is_active": true, "priority": 60, "rule_type": "threshold", "sensor_parameter": "vpd", "sensor_location_key": "growzelt1", "condition": {"operator": "gt", "threshold": 1.2}, "action": {"command": "turn_on"}, "hysteresis": {"on_threshold": 1.2, "off_threshold": 0.9, "min_on_duration_seconds": 120, "min_off_duration_seconds": 300, "cooldown_seconds": 60}, "is_safety_rule": false, "notes": "Schwellwerte phasenabhängig: werden bei Phasenwechsel aus PhaseControlProfile.target_vpd_kpa abgeleitet (on = target + 0.2, off = target - 0.1). Veg: on=1.2/off=0.9, Bloom: on=1.5/off=1.2" }
{ "_key": "rule_temp_exhaust", "name": "Übertemperatur Abluft", "is_active": true, "priority": 90, "rule_type": "threshold", "sensor_parameter": "temperature", "sensor_location_key": "growzelt1", "condition": {"operator": "gt", "threshold": 30}, "action": {"command": "set_value", "value": 100}, "hysteresis": {"on_threshold": 30, "off_threshold": 27, "min_on_duration_seconds": 300, "min_off_duration_seconds": 60, "cooldown_seconds": 30}, "is_safety_rule": true, "notes": "Sicherheitsregel: Abluft auf 100% bei >30°C (Cannabis: Stress ab 30°C, Tomate: Pollensterilität ab 32°C)" }
{ "_key": "rule_night_temp", "name": "Nachtabsenkung Heizung", "is_active": true, "priority": 50, "rule_type": "threshold", "sensor_parameter": "temperature", "sensor_location_key": "growzelt1", "condition": {"operator": "lt", "threshold": 18}, "action": {"command": "turn_on"}, "hysteresis": {"on_threshold": 18, "off_threshold": 21, "min_on_duration_seconds": 600, "min_off_duration_seconds": 600, "cooldown_seconds": 120}, "is_safety_rule": false }

// has_rule edges
{ "_from": "actuators/humidifier_zelt1", "_to": "control_rules/rule_vpd_humid" }
{ "_from": "actuators/exhaust_zelt1", "_to": "control_rules/rule_temp_exhaust" }
{ "_from": "actuators/heater_zelt1", "_to": "control_rules/rule_night_temp" }

// phase_control_profiles collection
{ "_key": "profile_cannabis_veg", "name": "Indoor Cannabis Vegetativ", "target_photoperiod_hours": 18.0, "target_light_ppfd": 600, "target_light_dimmer_percent": 75, "target_light_spectrum": {"blue": 0.30, "red": 0.50, "far_red": 0.05, "green": 0.15}, "target_temperature_day_c": 26, "target_temperature_night_c": 20, "target_humidity_day_percent": 65, "target_humidity_night_percent": 70, "target_vpd_kpa": 1.0, "co2_enrichment_ppm": 800, "co2_only_during_lights_on": true, "co2_min_ppfd_threshold": 200, "target_dli_mol": 38, "photoperiod_is_critical": false, "dif_target_c": 6, "irrigation_frequency_per_day": 3, "irrigation_duration_seconds": 180, "target_drain_percent": 20, "transition_days": 0, "is_template": true }
{ "_key": "profile_cannabis_bloom", "name": "Indoor Cannabis Blüte", "target_photoperiod_hours": 12.0, "target_light_ppfd": 800, "target_light_dimmer_percent": 100, "target_light_spectrum": {"blue": 0.15, "red": 0.60, "far_red": 0.10, "green": 0.15}, "target_temperature_day_c": 24, "target_temperature_night_c": 18, "target_humidity_day_percent": 50, "target_humidity_night_percent": 55, "target_vpd_kpa": 1.3, "co2_enrichment_ppm": 1000, "co2_only_during_lights_on": true, "co2_min_ppfd_threshold": 300, "target_dli_mol": 40, "photoperiod_is_critical": true, "dif_target_c": 6, "pre_dawn_drop_c": 5, "pre_dawn_drop_hours": 2, "irrigation_frequency_per_day": 4, "irrigation_duration_seconds": 120, "target_drain_percent": 20, "transition_days": 7, "is_template": true, "notes": "Photoperiode gradual über 7 Tage umstellen. Dunkelphase kritisch — keine Lichtunterbrechung!" }

// phase_profile edges (Phase → Profil)
{ "_from": "growth_phases/vegetative", "_to": "phase_control_profiles/profile_cannabis_veg" }
{ "_from": "growth_phases/flowering", "_to": "phase_control_profiles/profile_cannabis_bloom" }
```

## 4. Authentifizierung & Autorisierung

> **Hinweis (SEC-H-001):** Dieser Abschnitt wurde nachträglich ergänzt, um die Auth-Anforderungen
> gemäß REQ-023 (Authentifizierung) und REQ-024 (Mandantenverwaltung) zu dokumentieren.

**Standardregel:** Alle Endpunkte dieses REQ erfordern Authentifizierung (JWT Bearer Token)
und Tenant-Mitgliedschaft, sofern nicht anders angegeben.

| Ressource/Endpoint-Gruppe | Lesen | Schreiben | Löschen |
|---------------------------|-------|-----------|---------|
| Actuators | Mitglied | Mitglied | Admin |
| Schedules | Mitglied | Mitglied | Mitglied |
| Rules | Mitglied | Mitglied | Mitglied |
| Command & Override | — | Mitglied | — |
| HA-Integration | Admin | Admin | Admin |
| Emergency-Stop | — | Mitglied | — |

## 5. Abhängigkeiten

**Erforderliche Module:**
- REQ-002 (Standort): Location für Aktor-Zuordnung, Location-Typ (indoor/outdoor) für Validierung
- REQ-003 (Phasensteuerung): Phasenübergänge triggern Profil-Wechsel; GrowthPhase → RequirementProfile als Basis
- REQ-005 (Sensorik): Sensordaten als Input für regelbasierte Steuerung; Sensor-Entities für Regel-Zuordnung

**Wird benötigt von:**
- REQ-003 (Phasensteuerung): **HOCH** — Phasenwechsel löst automatische Aktor-Anpassung aus
- REQ-005 (Sensorik): **HOCH** — Sensor-Werte triggern Regeln; HA-Entity-Sync bidirektional
- REQ-006 (Aufgabenplanung): **MITTEL** — Fallback-Tasks bei manuellen Aktoren oder HA-Ausfall
- REQ-009 (Dashboard): **HOCH** — Aktor-Status-Widget, Regel-Aktivitäten, Override-Anzeige
- REQ-014 (Tankmanagement): **HOCH** — Bewässerungsventile als Aktoren; Tank-Füllstand als Sicherheitseingang (Trockenlaufschutz <5%); Dosierpumpen für pH/EC-Korrektur; Chiller für Nährlösungstemperatur
- REQ-019 (Substratverwaltung): **MITTEL** — Substrattyp beeinflusst Bewässerungsstrategie (Frequenz, Volumen)

**Celery-Tasks:**
- `evaluate_control_rules` — Alle 30 Sekunden: Sensor-Werte gegen aktive Regeln prüfen, Aktoren steuern. **Hinweis:** Sicherheitsregeln sollten zusätzlich über MQTT-Subscription mit Echtzeit-Trigger reagieren, da 30s bei Übertemperatur (>35°C: Trichom-Verlust bei Cannabis) zu langsam sein kann.
- `expire_manual_overrides` — Stündlich: Abgelaufene Overrides deaktivieren
- `sync_actuator_states` — Alle 5 Minuten: Aktor-Zustände aus HA/MQTT aktualisieren
- `calculate_gradual_transitions` — Stündlich: Photoperiode/Dimmer-Übergänge berechnen und anpassen
- `check_actuator_health` — Alle 15 Minuten: Erreichbarkeit von HA/MQTT-Aktoren prüfen, Alerts bei Offline. Bei >2h ohne State-Update: Alert „Aktor möglicherweise offline"
- `accumulate_dli` — Stündlich: PPFD-Messwerte aufsummieren, bei DLI-Ziel-Erreichung Licht dimmen/abschalten

## 6. Akzeptanzkriterien

### Definition of Done (DoD):

- [ ] **Aktor-CRUD:** Erstellen, Lesen, Aktualisieren, Löschen von Aktoren (19 Typen)
- [ ] **Location-Zuordnung:** Aktor über has_actuator-Edge einer Location zugeordnet
- [ ] **Protokoll-Validierung:** HA-Aktoren erfordern ha_entity_id, MQTT erfordert command_topic
- [ ] **Dimmbare Aktoren:** min_value/max_value für stufenlose Steuerung
- [ ] **Zeitpläne:** CRUD für ScheduleEntries, tägliche/wöchentliche Wiederholung
- [ ] **Photoperioden-Validierung:** Zeitplan-Einträge ergeben korrekte Beleuchtungsdauer
- [ ] **Regelbasierte Steuerung:** Sensor-Schwellwert löst Aktor-Aktion aus
- [ ] **Hysterese:** on/off-Schwellwerte, Mindestlaufzeit, Mindestpause, Cooldown
- [ ] **Sicherheitsregeln:** Höhere Priorität als reguläre Regeln
- [ ] **Compound-Regeln:** AND/OR-Verknüpfung mehrerer Bedingungen
- [ ] **Prioritätssystem:** Override > Safety > Rule > Schedule
- [ ] **Manueller Override:** Zeitlich begrenzt, höchste Priorität, automatische Ablauf
- [ ] **Steuerungshistorie:** Jede Aktion als immutables ControlEvent protokolliert
- [ ] **Event-Quellen:** schedule, rule, phase_change, manual, safety, fallback_task unterschieden
- [ ] **Home Assistant Integration:** Service-Calls (turn_on, turn_off, set_value) über REST API
- [ ] **HA Entity-Mapping:** Kamerplanter-Aktoren auf HA-Entities gemappt
- [ ] **HA Graceful Degradation:** Bei HA-Ausfall → Fallback-Task (REQ-006) statt Steuerungsbefehl
- [ ] **MQTT-Steuerung:** Publish an command_topic, State von state_topic
- [ ] **Manuelle Aktoren:** System erzeugt Tasks statt Befehle
- [ ] **Phasen-Profile:** PhaseControlProfile mit Zielwerten pro Phase
- [ ] **Phasen-Trigger:** Automatische Profil-Anwendung bei Phasenwechsel (REQ-003)
- [ ] **Gradueller Übergang:** Photoperiode/Dimmer schrittweise über N Tage
- [ ] **Dry-Run:** Regel gegen aktuelle Sensorwerte testen ohne Ausführung
- [ ] **Energieverbrauch:** Geschätzte kWh pro Aktor/Location
- [ ] **Celery-Beat:** evaluate_control_rules (30s), sync_actuator_states (5min), check_actuator_health (15min)
- [ ] **VPD-Controller:** Gekoppelter Regelkreis, Schwellwerte aus PhaseControlProfile abgeleitet
- [ ] **DLI-Akkumulation:** PPFD-Tagesintegral berechnen, Lichtintensität anpassen
- [ ] **CO₂-PPFD-Kopplung:** CO₂-Dosierung nur bei ausreichendem PPFD
- [ ] **DIF/DROP:** Tag-/Nacht-Temperatur-Umschaltung basierend auf Lichtplan
- [ ] **Substratfeuchte-Bewässerung:** Sensorgesteuerte Bewässerung mit Tank-Trockenlaufschutz
- [ ] **Konfliktgruppen:** CO₂/Abluft-Koordination, Heizung/Kühlung-Exklusion
- [ ] **Fail-Safe-States:** Default-Zustand pro Aktor bei Kommunikationsverlust
- [ ] **Notabschaltung:** Emergency-Stop-Endpoint mit Szenarien
- [ ] **Photoperiod-Schutz:** Dunkelphase bei Kurztagspflanzen nicht durch Licht-Aktoren unterbrechen
- [ ] **Lichtspektrum-Steuerung:** Mehrkanallampen-Kanalsteuerung bei spectrum_control-Capability

### Testszenarien:

**Szenario 1: VPD-Regel löst Befeuchter aus**
```
GIVEN: Regel "VPD-Korrektur Befeuchter" aktiv (on_threshold: 1.5, off_threshold: 1.2),
       Befeuchter ist AUS, VPD-Sensor meldet 1.6 kPa
WHEN: Celery-Task `evaluate_control_rules` läuft
THEN:
  - Regel erkennt VPD > 1.5 (on_threshold)
  - HA Service-Call: humidifier.turn_on (entity: humidifier.zelt_1)
  - ControlEvent erstellt: source=rule, command=turn_on, sensor_reading=1.6
  - Aktor-State aktualisiert: current_state="on"
```

**Szenario 2: Hysterese verhindert Oszillation**
```
GIVEN: Befeuchter ist EIN (seit 90 Sekunden), VPD sinkt auf 1.35 kPa,
       off_threshold: 1.2, min_on_duration: 120s
WHEN: Celery-Task `evaluate_control_rules` läuft
THEN:
  - VPD 1.35 > off_threshold 1.2 → Befeuchter bleibt AN
  - Keine Zustandsänderung (Hysterese-Band)

WHEN: VPD sinkt auf 1.15 kPa (< off_threshold 1.2), Befeuchter läuft >120s
THEN:
  - HA Service-Call: humidifier.turn_off
  - ControlEvent: source=rule, command=turn_off
  - min_off_duration 300s startet → kein erneutes Einschalten für 5 Minuten
```

**Szenario 3: Sicherheitsregel übersteuert Zeitplan**
```
GIVEN: Abluft-Zeitplan: "50% zwischen 06:00-00:00",
       Sicherheitsregel: "Bei >30°C → Abluft 100%",
       Temperatur steigt auf 31°C
WHEN: System evaluiert
THEN:
  - Sicherheitsregel (Priorität 900) > Zeitplan (Priorität 150)
  - HA Service-Call: fan.set_percentage(100)
  - ControlEvent: source=safety, sensor_reading=31
  - Zeitplan-Wert wird ignoriert bis Temperatur < 27°C (off_threshold)
```

**Szenario 4: Manueller Override mit Ablaufzeit**
```
GIVEN: Abluft hat aktiven Zeitplan (50%)
WHEN: POST /api/v1/actuators/exhaust_zelt1/override
      Body: { override_value: 100, expires_at: "2026-02-27T14:00:00Z",
              reason: "Hitze-Notfall" }
THEN:
  - ManualOverride erstellt (Priorität 1000)
  - Sofortiger Service-Call: fan.set_percentage(100)
  - ControlEvent: source=manual, value=100
  - Nach 14:00 Uhr: Override abgelaufen → Zeitplan-Wert (50%) greift wieder
```

**Szenario 5: Phasenübergang ändert Lichtprogramm**
```
GIVEN: Pflanze wechselt von "vegetative" → "flowering",
       PhaseControlProfile "Cannabis Bloom": 12h, transition_days=7,
       Aktuelles Lichtprogramm: 18h
WHEN: Phasenübergang ausgelöst (REQ-003)
THEN:
  - Tag 1: Photoperiode → 17.14h (18 - (6/7)*1)
  - Tag 2: Photoperiode → 16.29h
  - ...
  - Tag 7: Photoperiode → 12.0h
  - Jeden Tag wird der Licht-Zeitplan angepasst
  - 7 ControlEvents mit source=phase_change
  - Dimmer sofort von 75% auf 100% (kein gradual)
```

**Szenario 6: HA-Ausfall erzeugt Fallback-Task**
```
GIVEN: Licht "light.growzelt_1" soll um 06:00 eingeschaltet werden,
       Home Assistant ist nicht erreichbar
WHEN: Zeitplan triggert um 06:00
THEN:
  - Service-Call an HA schlägt fehl (Timeout/Connection Error)
  - ControlEvent: source=fallback_task, success=false, error="HA not reachable"
  - Automatisch Task erstellt (REQ-006):
    Titel: "Manuell: Licht Zelt 1 einschalten"
    Priorität: high
    Beschreibung: "Home Assistant nicht erreichbar — Licht manuell einschalten"
  - Aktor-State: is_online=false
  - Alert in Dashboard (REQ-009)
```

**Szenario 7: Manueller Aktor erzeugt nur Tasks**
```
GIVEN: Ventilator "fan_outdoor" mit protocol="manual",
       Regel: "Wenn Temperatur >30°C → Ventilator ein"
WHEN: Temperatur-Sensor meldet 31°C
THEN:
  - Kein Service-Call (Protokoll = manual)
  - Automatisch Task erstellt (REQ-006):
    Titel: "Umluft-Ventilator Garten-Setup einschalten"
    Kategorie: maintenance
    Beschreibung: "Temperatur 31°C — bitte Ventilator manuell auf Stufe 3 stellen"
  - ControlEvent: source=rule, event_source=fallback_task
```

**Szenario 8: Energieverbrauch-Schätzung**
```
GIVEN: Location "Grow Zelt 1" mit:
       - Licht 480W (18h/Tag an)
       - Abluft 95W (24h/Tag, 60%)
       - Befeuchter 30W (geschätzt 4h/Tag)
WHEN: GET /api/v1/locations/growzelt1/energy?period=month
THEN:
  - Licht: 480W × 18h × 30d = 259.2 kWh
  - Abluft: 95W × 0.6 × 24h × 30d = 41.0 kWh
  - Befeuchter: 30W × 4h × 30d = 3.6 kWh
  - Gesamt: ~303.8 kWh
```

**Szenario 9: Compound-Regel (AND-Verknüpfung)**
```
GIVEN: Regel "CO₂-Dosierung bei Licht + niedrigem CO₂":
       condition: { compound_operator: "and",
                    sub_conditions: [
                      { operator: "lt", threshold: 600, parameter: "co2" },
                      { operator: "gt", threshold: 0, parameter: "light_state" }
                    ]}
       CO₂-Doser-Aktor zugeordnet
WHEN: CO₂ = 450 ppm UND Licht ist AN
THEN:
  - Beide Sub-Bedingungen erfüllt → CO₂-Doser einschalten
  - ControlEvent: source=rule, sensor_reading=450

WHEN: CO₂ = 450 ppm UND Licht ist AUS (Nacht)
THEN:
  - Nur eine Sub-Bedingung erfüllt → CO₂-Doser bleibt AUS
  - Keine Aktion (CO₂-Dosierung nur bei Licht sinnvoll)
```

**Szenario 10: Regel Dry-Run**
```
GIVEN: Regel "Nachtabsenkung Heizung" (on_threshold: 18°C),
       Aktuelle Temperatur: 16.5°C, Heizung ist AUS
WHEN: POST /api/v1/rules/rule_night_temp/test
THEN:
  - Response: { would_trigger: true, command: "turn_on",
                current_sensor_value: 16.5, threshold: 18,
                note: "Temperatur 16.5°C < 18°C → Heizung würde eingeschaltet" }
  - KEIN Service-Call, KEIN ControlEvent, KEIN State-Update
```

---

**Hinweise für RAG-Integration:**
- Keywords: Umgebungssteuerung, Aktorik, Aktor, Licht, Abluft, Befeuchter, Heizung, CO₂-Doser, Bewässerungsventil, Pumpe, Zeitplan, Lichtprogramm, Photoperiode, Regel, Schwellwert, Hysterese, Oszillation, Debouncing, Override, Sicherheitsregel, Phasenprofil, Gradueller Übergang, Home Assistant, MQTT, Service-Call, Entity, Fallback-Task, Energieverbrauch
- Technische Begriffe: Actuator, ActuatorType, ActuatorCapability, ControlSchedule, ControlRule, ControlEvent, ManualOverride, PhaseControlProfile, ScheduleEntry, RuleCondition, RuleAction, HysteresisConfig, ControlEngine, HomeAssistantClient, PhaseTransitionHandler, VPD-Controller, DLI-Akkumulation, DIF, DROP-Technik, Fail-Safe-State, Konfliktgruppe, Emergency-Stop, Dosierpumpe, Chiller, Spektrum-Steuerung, has_actuator, has_rule, has_schedule, actuator_event, phase_profile, monitors, evaluate_control_rules, sync_actuator_states, accumulate_dli
- Verknüpfung: REQ-002 (Location), REQ-003 (Phasensteuerung — Profil-Trigger, DLI, Lichtspektrum), REQ-005 (Sensorik — Input, PPFD-Akkumulation, Substratfeuchte), REQ-006 (Aufgaben — Fallback), REQ-009 (Dashboard), REQ-014 (Tankmanagement — Bewässerungsventile, Dosierpumpen, Chiller, Trockenlaufschutz), REQ-019 (Substratverwaltung — Bewässerungsstrategie)
