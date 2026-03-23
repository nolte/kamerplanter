---
name: REQ-018 Umgebungssteuerung — UI Patterns and Test Insights
description: Key patterns, validation rules, and notes for REQ-018 test case extraction
type: project
---

## REQ-018 Umgebungssteuerung & Aktorik — UI Test Insights

- Output: `spec/e2e-testcases/TC-REQ-018.md`, 72 test cases, IDs TC-018-{NNN}
- NOT YET IMPLEMENTED in frontend (2026-03-21); no pages in `src/frontend/src/pages/` for Aktoren or Umgebungssteuerung
- All test cases are spec-forward, describing expected UI behavior from REQ-018 v1.2

### Page/Route Structure (Planned)
- Aktoren-Liste: `/standorte/{key}/aktoren` (tab within Location detail page or dedicated page)
- Zeitplaene: Tab within Aktor-Detailseite
- Regeln: Tab within Aktor-Detailseite
- Phasen-Profile: `/automatisierung/phasen-profile` (dedicated list + detail page)
- HA-Integration: `/einstellungen/integrationen/home-assistant`
- Notabschaltung: Button in AppBar or Location-Header (auffaellig rot)

### Key Validation Rules (from Pydantic models)
- Actuator.protocol = HA → ha_entity_id REQUIRED; protocol = MQTT → mqtt_command_topic REQUIRED
- Actuator.capabilities includes DIMMABLE → min_value AND max_value REQUIRED
- HysteresisConfig: on_threshold MUST != off_threshold (no-hysteresis prevention)
- HysteresisConfig: min_on/off_duration_seconds: ge=0, le=3600; cooldown_seconds: ge=0, le=600
- PhaseControlProfile.target_photoperiod_hours: ge=0, le=24
- PhaseControlProfile.target_light_ppfd: ge=0, le=2000
- PhaseControlProfile.target_temperature_day_c: ge=5, le=45
- PhaseControlProfile.co2_enrichment_ppm: ge=0, le=2000
- PhaseControlProfile.target_vpd_kpa: ge=0, le=5
- PhaseControlProfile.target_dli_mol: ge=0, le=65
- PhaseControlProfile DIF validation: day-night difference MUST be <= 12°C, >= -4°C
- ActuatorAssignmentValidator: CO2_DOSER and DEHUMIDIFIER forbidden for Outdoor-Locations
- ManualOverride: expires_at REQUIRED (no eternal overrides); EITHER override_value OR override_state required
- ControlSchedule: entries.min_length=1; valid_from < valid_until if both set

### HA Visibility Rule (REQ-005 §4a)
- When ha_token_set=false: Protocol dropdown hides "Home Assistant"; ha_entity_id field not shown
- When ha_token_set=true: HA option visible + Entity-ID picker (autocomplete from HA entities API)
- HA-specific log columns also hidden when not configured

### Priority System (visible in Event-Log and Override-Banner)
- Override (1000) > Safety Rule (900) > Regular Rule (500+priority) > Schedule (100+priority)
- Override: orange banner on Aktor-Detailseite showing expiry time
- Safety Rule Events: Schild-Icon in event log, source="Sicherheit"
- Active Override: Zeitplan shown as "durch Override uebersteuert"

### Emergency Stop (Notabschaltung)
- 3 scenarios: Wasseraustritt (all pumps/valves OFF), CO2-Leck (CO2 off + exhaust 100%), Brand-Alarm (ALL off)
- Requires explicit confirmation + "Ich bestaetigen, dass dies ein Notfall ist" checkbox
- Persistent Warn-Banner on Location until manually acknowledged

### Photoperiod Protection (photoperiod_is_critical)
- When profile.photoperiod_is_critical=true: warn dialog before any light-on override during dark phase
- Test for Cannabis bloom profile (is_critical=true, 12h)

### Fail-Safe States Table (from spec § 1)
- Exhaust fan → ON (100%); Heizung → OFF; Bewässerung → OFF; CO2-Doser → OFF; Licht → last; Dosierpumpe → OFF; Chiller → ON

### Seed Data (for concrete test preconditions)
- light_zelt1: Hauptlicht Zelt 1, HA, light.growzelt_1, 480W, dimmable 0-100%
- exhaust_zelt1: Abluft Zelt 1, HA, fan.abluft_zelt_1, 95W, speed_control 0-100%, conflict_group=co2_ventilation
- humidifier_zelt1: Befeuchter Zelt 1, HA, humidifier.zelt_1, 30W, on_off, fail_safe=off
- heater_zelt1: Heizstrahler Zelt 1, MQTT, 150W, temperature_setpoint 15-30°C, fail_safe=off
- co2_doser_zelt1: CO2-Doser Zelt 1, HA, switch.co2_zelt_1, 10W, conflict_group=co2_ventilation
- fan_outdoor: Umluft-Ventilator, MANUAL, speed_control 1-3, is_online=false
- Schedules: sched_light_veg (18/6, daily), sched_light_bloom (12/12 inactive), sched_irrigation_3x (3×täglich)
- Rules: rule_vpd_humid (VPD>1.2→Befeuchter on, safety=false), rule_temp_exhaust (Temp>30→Abluft 100%, safety=TRUE), rule_night_temp (Temp<18→Heizung on)
- Profiles: profile_cannabis_veg (18h, 26/20°C, VPD 1.0, DIF 6, transition_days=0, template), profile_cannabis_bloom (12h, 24/18°C, VPD 1.3, DIF 6, DROP 5°C/2h, transition_days=7, critical=true, template)

### Auth Matrix (from § 4)
- Actuators: Read=Mitglied, Write=Mitglied, Delete=ADMIN ONLY
- Schedules/Rules: Read/Write/Delete=Mitglied
- HA-Integration: Read/Write/Delete=ADMIN ONLY
- Emergency-Stop: Write=Mitglied
