# Review: Smart-Home-Enthusiast & Home-Assistant-Integration

**Erstellt von:** Smart-Home-Enthusiast & HA-Power-User (Subagent)
**Datum:** 2026-02-27
**Fokus:** Bidirektionale Home-Assistant-Anbindung -- Entitaeten-Export -- Sensor-Import -- Aktor-Steuerung -- Optionalitaet
**Analysierte Dokumente:** REQ-001 bis REQ-027, NFR-001 bis NFR-011, UI-NFR-001 bis UI-NFR-013, stack.md, HA-CUSTOM-INTEGRATION.md
**Smart-Home-Profil:** HA OS auf Odroid N2+, 300+ Entitaeten, 2x 120x120 Growzelte + 3x4m Gewaechshaus, Mosquitto MQTT, Zigbee2MQTT, ESPHome, Node-RED
**Version:** 2.0 (aktualisiert nach Erstellung von HA-CUSTOM-INTEGRATION.md und REQ-023 v1.4)

---

## Integrations-Architektur: Zwei-Seiten-Modell

### Zusammenfassung

| Integrationsrichtung | Bewertung | Status | Kommentar |
|---------------------|-----------|--------|-----------|
| **Seite A:** Kamerplanter -> HA (Entitaeten/Dashboard) | 4/5 | Stark verbessert | REST API versioniert, M2M API-Keys (REQ-023 v1.4), Health-Check, iCal-Feed. HA-CUSTOM-INTEGRATION.md definiert Entity-Mapping, Coordinators, Config Flow. Einzige Luecke: kein Event-basiertes Push (MQTT/SSE) -- alles Polling. |
| **Seite B:** HA -> Kamerplanter (Sensordaten) | 5/5 | Exzellent | REQ-005 ist das Paradebeispiel: `ha_entity_id` auf Sensor-Node, `source`-Tracking, Fallback-Kette (HA -> MQTT -> Wetter -> manuell), `HomeAssistantConnector` mit REST+History-API, Wetter-Integration fuer Outdoor. |
| **Seite C:** Kamerplanter -> HA Aktoren (Steuerung) | 5/5 | Exzellent | REQ-018 definiert `protocol: home_assistant/mqtt/manual`, `ha_entity_id` auf Actuator, Service-Calls, Graceful Degradation, Fail-Safe-States, Prioritaetssystem, Hysterese, VPD-Controller, DLI-Steuerung. HA-CUSTOM-INTEGRATION.md klaert Steuerungsmodi (A vs B). |
| **Optionalitaet:** Kamerplanter ohne HA | 5/5 | Vorbildlich | Manueller Modus ueberall, Sensor-Fallback auf manuelle Eingabe, Aktoren mit `protocol: manual` generieren Tasks statt Befehle. REQ-027 Light-Modus ideal fuer lokale HA-Nutzer. |
| **Ausfallverhalten:** HA offline | 4/5 | Gut | >6h Sensor-Ausfall -> Task-Generierung, <2h Interpolation, Fail-Safe-States pro Aktortyp, Graceful Degradation zu manuellen Tasks. Reconnect-Strategie nicht explizit dokumentiert. |
| **API-Stabilitaet / M2M-Auth** | 5/5 | Geloest | API versioniert (`/api/v1/...`), REQ-023 v1.4 M2M API-Keys (`kp_`-Prefix, SHA-256-Hash, revokable), OpenAPI-Schema. Light-Modus eliminiert Auth-Overhead fuer lokale Setups. |
| **Custom Integration Spec** | 5/5 | Neu | HA-CUSTOM-INTEGRATION.md spezifiziert komplette HACS-Integration: Config Flow, Entity Registry, Coordinators, NFRs, Steuerungsmodi, Automation Blueprints. |

**Gesamteinschaetzung:** Seit dem ersten Review hat sich die HA-Integrationslage **grundlegend verbessert**. Die drei kritischen Luecken (M2M-Auth, Health-Check, Custom-Integration-Spec) sind geschlossen. REQ-023 v1.4 liefert langlebige API-Keys, HA-CUSTOM-INTEGRATION.md definiert die komplette Custom Integration als eigenes Projekt, und die Steuerungsmodi (Modus A: KP regelt direkt vs. Modus B: KP liefert Sollwerte) sind dokumentiert. Die verbleibende Hauptluecke ist das fehlende Event-Publishing (MQTT/SSE) -- aktuell muss alles gepollt werden. Fuer die meisten Anwendungsfaelle ist Polling mit 60s-5min Intervallen aber akzeptabel.

---

## Integrationslandkarte

### Seite A: Kamerplanter -> Home Assistant

#### Entitaeten-Mapping-Tabelle (aus HA-CUSTOM-INTEGRATION.md HA-003)

| HA-Entity-ID-Pattern | Kamerplanter-Quelle | HA-Entity-Typ | Einheit | API-Endpoint | Polling-Intervall |
|----------------------|---------------------|---------------|---------|-------------|-------------------|
| `sensor.kp_{plant}_phase` | `current_phase` | `sensor` | -- | `GET /plants/` | 300s |
| `sensor.kp_{plant}_days_in_phase` | `phase_histories.entered_at` (berechnet) | `sensor` | `d` | `GET /plants/` | 300s |
| `sensor.kp_{plant}_vpd_target` | `requirement_profiles.vpd_target_kpa` | `sensor` | `kPa` | `GET /plants/` | 300s |
| `sensor.kp_{plant}_ec_target` | `nutrient_profiles.target_ec_ms` | `sensor` | `mS/cm` | `GET /plants/` | 300s |
| `sensor.kp_{plant}_photoperiod` | `requirement_profiles.photoperiod_hours` | `sensor` | `h` | `GET /plants/` | 300s |
| `sensor.kp_{plant}_gdd_accumulated` | GDD-Tracking (berechnet) | `sensor` | `GDd` | `GET /plants/` | 300s |
| `sensor.kp_{plant}_harvest_readiness` | `GET /harvest/readiness/{id}` | `sensor` | `%` | `GET /harvest/readiness/` | 300s |
| `sensor.kp_{plant}_karenz_remaining` | Karenz-Gate (berechnet) | `sensor` | `d` | berechenbar | 300s |
| `sensor.kp_{plant}_next_watering` | `GET /care-reminders/` | `sensor` | -- | `GET /care-reminders/` | 300s |
| `sensor.kp_{plant}_health_score` | IPM + Quality (aggregiert) | `sensor` | `%` | aggregierbar | 300s |
| `binary_sensor.kp_{plant}_needs_attention` | Alerts + ueberfaellige Tasks | `binary_sensor` | -- | `GET /alerts/` | 60s |
| `sensor.kp_{location}_active_plants` | Slot-Belegung | `sensor` | -- | `GET /locations/` | 300s |
| `sensor.kp_{location}_vpd_current` | Berechneter VPD | `sensor` | `kPa` | berechenbar | 300s |
| `sensor.kp_{tank}_ec` | `TankState.ec_ms` | `sensor` | `mS/cm` | `GET /tanks/{id}/states/latest` | 120s |
| `sensor.kp_{tank}_ph` | `TankState.ph` | `sensor` | `pH` | `GET /tanks/{id}/states/latest` | 120s |
| `sensor.kp_{tank}_fill_level` | `TankState.fill_level_percent` | `sensor` | `%` | `GET /tanks/{id}/states/latest` | 120s |
| `sensor.kp_{tank}_water_temp` | `TankState.water_temp_celsius` | `sensor` | `C` | `GET /tanks/{id}/states/latest` | 120s |
| `sensor.kp_{actuator}_state` | `Actuator.current_state` | `sensor` | -- | `GET /actuators/` | 300s |
| `binary_sensor.kp_sensor_offline` | SensorHealth | `binary_sensor` | -- | `GET /alerts/` | 60s |
| `calendar.kp_tasks` | CalendarFeed (iCal) | `calendar` | -- | `GET /calendar/feeds/{id}/feed.ics` | iCal |
| `todo.kp_{location}_tasks` | `GET /tasks/?status=pending` | `todo` | -- | `GET /tasks/` | 300s |
| `button.kp_refresh_all` | Manueller Refresh | `button` | -- | Coordinator Refresh | -- |

#### Anforderungen an Kamerplanter (Seite A)

| # | Anforderung | Status | Kommentar |
|---|------------|--------|-----------|
| A-001 | Stabile REST API mit Versionierungsgarantie | Vorhanden | `/api/v1/...` versioniert, FastAPI generiert OpenAPI-Spec. NFR-001 definiert API-Stabilitaet. |
| A-002 | Event-Publishing (MQTT/SSE) bei Zustandsaenderungen | Fehlt | Weiterhin die groesste Luecke. REQ-009 erwaehnt WebSocket fuer Dashboard-Updates. HA-CUSTOM-INTEGRATION.md vermerkt MQTT als "zukuenftiges Upgrade" (HA-004 Hinweis). Redis Pub/Sub ist im Stack. |
| A-003 | API-Key-Authentifizierung fuer M2M-Zugriff | Vorhanden (NEU) | REQ-023 v1.4: `api_keys` Collection, `kp_`-Prefix, SHA-256-Hash, Bearer-Erkennung, Rate Limit 1000 req/min. 3 Endpoints (erstellen/auflisten/revoken). HA-CUSTOM-INTEGRATION.md referenziert dies. |
| A-004 | Health-Check-Endpoint (`/api/health`) | Vorhanden | HA-CUSTOM-INTEGRATION.md HA-001: Config Flow prueft `GET /api/health -> {"status": "healthy", ...}`. Server-Version wird fuer Device Registry ausgelesen. |
| A-005 | Bulk/List-Endpoints fuer effizientes Polling | Vorhanden | FastAPI List-Endpoints mit Pagination. HA-CUSTOM-INTEGRATION.md HA-004 definiert Coordinators die List-Endpoints nutzen. |
| A-006 | Konsistente JSON-Antwortformate | Vorhanden | Pydantic-Modelle, NFR-006 Error-Schema. HA-CUSTOM-INTEGRATION.md referenziert dies. |
| A-007 | OpenAPI-Schema als versioniertes Artefakt | Vorhanden | FastAPI generiert `/docs` und `/openapi.json`. NFR-005 definiert Schema-Versionierung. |
| A-008 | iCal-Feed fuer Calendar-Entity | Vorhanden | REQ-015 CalendarFeed mit Token-basiertem webcal://-Zugang. HA-CUSTOM-INTEGRATION.md HA-006 nutzt dies direkt. |

#### Anforderungen an die HA Custom Integration

| # | Anforderung | Status | Kommentar |
|---|------------|--------|-----------|
| HA-001 | Config Flow (URL + API-Key + Tenant) | Spezifiziert | HA-CUSTOM-INTEGRATION.md: 4-Step Config Flow (URL -> Auth -> Tenant -> Entities). Light-Modus Skip fuer Auth. |
| HA-002 | Device Registry | Spezifiziert | 1 KP-Instanz = 1 Device. Identifiers aus `(kamerplanter, {url}_{tenant_slug})`. |
| HA-003 | Entity Registry | Spezifiziert | 21 Entity-Typen definiert. Entity-IDs aus ArangoDB `_key` abgeleitet. |
| HA-004 | Coordinators mit Polling | Spezifiziert | 5 Coordinators (Plant 300s, Location 300s, Tank 120s, Alert 60s, Task 300s). Konfigurierbares Intervall. |
| HA-005 | HACS-Repository | Spezifiziert | Verzeichnisstruktur, manifest.json, hacs.json definiert. |
| HA-006 | Calendar-Entity via iCal | Spezifiziert | Nutzt REQ-015 CalendarFeed-Endpoint. Token-basiert, kein JWT. |
| HA-007 | Todo-Entity | Spezifiziert | Mapped REQ-006 Tasks. `async_update_todo_item` fuer Task-Completion. |
| HA-008 | Diagnostics | Spezifiziert | Config-Entry-Diagnostics: KP-Version, Counts, Update-Intervalle, Last Success. |
| HA-NFR-001 bis 007 | 7 Non-Funktionale Anforderungen | Spezifiziert | Entity-Referenzen via hass.data, Service-Idempotenz, Sofort-Propagierung, RestoreEntity, Event-Bus, Reload, ButtonEntity. Sehr solide. |

---

### Seite B: Home Assistant -> Kamerplanter

#### Sensor-Import-Matrix

| HA-Sensor-Typ | Kamerplanter-Parameter | Mapping vorhanden? | Fallback (ohne HA) | REQ-Referenz |
|---------------|----------------------|-------------------|-------------------|-------------|
| `sensor.temperature` | Lufttemperatur (temp) | Ja (`ha_entity_id`) | Manuelle Eingabe / Interpolation / Wetter-API | REQ-005 |
| `sensor.humidity` | Luftfeuchte (humidity) | Ja | Manuelle Eingabe / Wetter-API | REQ-005 |
| `sensor.co2` | CO2-Konzentration (co2) | Ja | Manuelle Eingabe | REQ-005 |
| `sensor.illuminance` / `sensor.ppfd` | Lichtintensitaet (ppfd) | Ja | Manuelle Eingabe | REQ-005 |
| `sensor.soil_moisture` | Bodenfeuchte (soil_moisture) | Ja | Manuelle Eingabe | REQ-005 |
| `sensor.ec` / `sensor.conductivity` | EC-Wert (ec) | Ja | Manuelle Eingabe | REQ-005 |
| `sensor.ph` | pH-Wert (ph) | Ja | Manuelle Eingabe | REQ-005 |
| `sensor.water_temperature` | Wassertemperatur (water_temp) | Ja | Manuelle Eingabe | REQ-005/REQ-014 |
| `sensor.water_level` | Fuellstand (water_level) | Ja | Manuelle Eingabe | REQ-014 |
| `sensor.leaf_temperature` | Blatttemperatur (leaf_temp) | Ja | Offset-Berechnung (leaf_temp_offset_c) | REQ-005 |
| `sensor.substrate_temperature` | Substrat-Temperatur | Ja | Manuelle Eingabe | REQ-005 |
| `sensor.dissolved_oxygen` | Geloester Sauerstoff (do) | Ja | Manuelle Eingabe | REQ-005 |
| `sensor.flow_rate` | Durchflussrate (L/h) | Ja | Nicht verfuegbar | REQ-005 |
| `sensor.air_quality` (Ammoniak) | TAN (Aquaponik) | Ja | Manuelle Eingabe (Tropfen-Tests) | REQ-026 |
| `sensor.power` / `sensor.energy` | Stromverbrauch (W/kWh) | Nein (nicht spezifiziert) | Nicht verfuegbar | -- |
| `sensor.wind_speed` | Windgeschwindigkeit | Indirekt (Wetter-API) | Wetter-API-Daten | REQ-005 |

#### Anforderungen an Kamerplanter (Seite B)

| # | Anforderung | Status | Kommentar |
|---|------------|--------|-----------|
| B-001 | HA REST API Client mit Entity-Subscription | Vorhanden | REQ-005 `HomeAssistantConnector` mit `get_sensor_state()`, `get_sensor_history()`, `test_connection()`. HA Long-Lived Access Token. |
| B-002 | Konfigurierbares Entity-Mapping pro Standort | Vorhanden | Sensor-Node hat `ha_entity_id: Optional[str]` + `mqtt_topic: Optional[str]`. Zuordnung via `located_at`-Edge. |
| B-003 | Daten-Provenance (Quelle: ha/mqtt/manual/weather) | Vorhanden | `Observation.source: Literal['ha_auto', 'mqtt_auto', 'modbus_auto', 'manual', 'interpolated', 'fallback', 'weather_api']`. Vorbildlich. |
| B-004 | Graceful Fallback bei HA-Ausfall | Vorhanden | >6h ohne Daten -> Task-Generierung. <2h -> Interpolation. AQL-Query spezifiziert. |
| B-005 | Polling-Intervall konfigurierbar | Teilweise | `measurement_interval_seconds` auf Sensor-Node. Ob es den HA-Polling-Intervall steuert, ist unklar. |
| B-006 | Einheiten-Konvertierung (F -> C, PSI -> kPa) | Nicht explizit | `_infer_parameter_from_entity()` erkennt Unit aus `unit_of_measurement`. Konvertierungslogik fehlt. |
| B-007 | HA-State-Validierung (unavailable/unknown) | Implizit | `get_sensor_state()` prueft `float(data['state'])` -- `unavailable` wuerde ValueError werfen. Korrekt, aber nicht dokumentiert. |
| B-008 | Mapping-UI (HA-Entity-Auswahl) | Nicht explizit | Sensor-Node hat `ha_entity_id` Textfeld. Kein Dropdown mit HA-Entity-Browser. |
| B-009 | Mehrere HA-Instanzen | Nicht spezifiziert | Nur eine `ha_url` + `ha_token`. Fortgeschrittene Setups mit mehreren HA-Instanzen nicht abgedeckt. |
| B-010 | MQTT als Alternative zu HA REST | Vorhanden | `mqtt_topic: Optional[str]`, Source `mqtt_auto`. MQTT-Client-Implementierung nicht detailliert. |
| B-011 | WebSocket-Subscription | Erwaehnt | REQ-005 erwaehnt WebSocket. `HomeAssistantConnector` implementiert nur REST. HA WebSocket API waere effizienter. |
| B-012 | Wetter-API als Fallback fuer Outdoor | Vorhanden | REQ-005 WeatherForecast mit DWD/OpenWeatherMap/Open-Meteo. 3 Celery-Tasks. 6 Warnungstypen. |

---

### Seite C: Kamerplanter -> HA Aktoren

#### Steuerungs-Matrix

| Kamerplanter-Aktion | HA-Service-Call | Trigger | Steuerungsmodus | REQ |
|---------------------|----------------|---------|----------------|-----|
| Phase -> Bluete: Licht 18h -> 12h | `light.turn_on/off` (Zeitplan) | Phasenwechsel (REQ-003) | Modus A (KP steuert) oder Modus B (KP publiziert Photoperiode, HA regelt) | REQ-018 |
| VPD zu hoch -> Befeuchter ein | `switch.turn_on` (Befeuchter) | Sensor-Schwellwert | Modus A oder B (VPD-Sollwert als Entity) | REQ-018 |
| Uebertemperatur (>35C) -> Abluft 100% | `switch.turn_on` (Abluft) | Safety-Rule | Modus A (immer KP -- Sicherheitsregel) | REQ-018 |
| CO2 < Sollwert bei PPFD >200 | `switch.turn_on` (CO2-Doser) | Compound-Rule | Modus A (CO2-PPFD-Kopplung erfordert Domaenenwissen) | REQ-018 |
| Bewaesserung faellig | `switch.turn_on` (Ventil/Pumpe) | Schedule oder Bodenfeuchte | Modus A oder B | REQ-018/REQ-014 |
| Duenger dosieren | `number.set_value` (Dosierpumpe) | Schedule/FeedingEvent | Modus A (Volumen-Berechnung in KP) | REQ-018/REQ-004 |
| DIF/DROP Nacht-Temp | `climate.set_temperature` | Schedule | Modus A (Pre-Dawn-Drop-Timing) | REQ-018 |
| DLI-Defizit -> Dimmer anpassen | `light.turn_on(brightness=X)` | DLI-Tracking | Modus A (KP akkumuliert PPFD ueber Tag) | REQ-018 |
| Frostschutz Gewaechshaus | `switch.turn_on` (Heizung) | Wetter-API (<2C) | Modus A oder B | REQ-005/REQ-018 |
| Emergency Stop: Wasseraustritt | `switch.turn_off` (alle Pumpen) | Manueller Trigger | Modus A (immer KP) | REQ-018 |
| Substratfeuchte-Bewaesserung | `switch.turn_on` (Ventil) | Sensor < Schwellwert | Modus A oder B | REQ-018 |
| CO2-Ventilations-Konflikt | Abluft auf Minimum | Conflict-Group | Modus A (Konfliktgruppen-Logik in KP) | REQ-018 |

#### Steuerungsmodi (aus HA-CUSTOM-INTEGRATION.md Abschnitt 5)

| Modus | Beschreibung | Empfohlen fuer | Wichtig |
|-------|-------------|----------------|---------|
| **Modus A: KP steuert direkt** | KP ControlEngine steuert Aktoren via HA-Service-Calls. HA-Automationen fuer dieselben Aktoren werden deaktiviert. | Einsteiger, Nutzer ohne eigene HA-Automationen | Beide Modi duerfen NICHT gleichzeitig fuer denselben Aktor aktiv sein -- Oszillation! |
| **Modus B: KP liefert Sollwerte, HA regelt** | KP publisht VPD-Target, EC-Target, Photoperiode als Sensor-Entities. HA-Automationen lesen Sollwerte und regeln selbst. | HA-Power-User, Node-RED-Nutzer, bestehende Regelkreise | |

**Meine Einschaetzung als HA-Power-User:** Modus B ist fuer mich der klare Favorit. Ich habe bereits funktionierende VPD-Regelkreise in Node-RED -- Kamerplanter soll mir die *Sollwerte* liefern (welches VPD-Ziel bei welcher Phase), nicht meine Regler ersetzen. Modus A ist sinnvoll fuer Nutzer, die HA nur als Aktor-Bridge nutzen (Shelly-Relais schalten). Die Konfigurierbarkeit pro Location/Aktor ist genau richtig.

#### Anforderungen an Kamerplanter (Seite C)

| # | Anforderung | Status | Kommentar |
|---|------------|--------|-----------|
| C-001 | Aktor-Mapping (KP-Aktor -> HA-Entity) | Vorhanden | `Actuator.ha_entity_id`, `protocol: home_assistant/mqtt/manual`. Pydantic-Validator erzwingt `ha_entity_id` bei HA-Protokoll. |
| C-002 | Korrekte HA-Service-Calls | Spezifiziert | REQ-018 benennt `light.turn_on`, `switch.turn_off`, `climate.set_temperature` explizit. |
| C-003 | Aktor-Zustandsverifikation | Vorhanden | `ControlEvent.success: bool`. MQTT State-Topic fuer MQTT-Aktoren. |
| C-004 | Graceful Degradation (HA offline -> Task) | Vorhanden | `EventSource.FALLBACK_TASK`. Automatische Task-Generierung bei HA-Ausfall. |
| C-005 | Prioritaetslogik | Vorhanden | 4 Stufen: Manual Override > Safety Rules > Sensor Rules > Schedules. |
| C-006 | Audit-Log | Vorhanden | `ControlEvent`-Collection (immutable) mit vollstaendiger Nachvollziehbarkeit. |
| C-007 | Hysterese | Vorhanden | `HysteresisConfig` mit on/off-threshold, min_on/off_duration, cooldown. |
| C-008 | Fail-Safe-States | Vorhanden | Pro Aktortyp definiert: Abluft=ON, Heizung=OFF, Bewaesserung=OFF, CO2=OFF. |
| C-009 | Konfliktgruppen | Vorhanden | `conflict_group`: co2_ventilation, heat_cool. Koordinierte Steuerung. |
| C-010 | Notabschaltung | Vorhanden | `POST /api/v1/emergency-stop` mit 3 Szenarien (Wasser, CO2, Brand). |

---

## Fehlt komplett -- Verbleibende Luecken

### HA-F-001: Event-Publishing fuer Zustandsaenderungen (MQTT/SSE)
**Integrationsrichtung:** Seite A (KP -> HA)
**Status:** Weiterhin die groesste verbleibende Luecke nach dem Update.
**Was fehlt:** Wenn eine Pflanze die Phase wechselt, ein Alert ausgeloest wird oder ein Tank-Zustand kritisch wird, muss HA das *sofort* erfahren. Die Custom Integration pollt aktuell alle 60s-300s. HA-CUSTOM-INTEGRATION.md HA-004 vermerkt korrekt: "Zukuenftiges Upgrade: Bei Implementierung eines MQTT-Event-Bus koennen Alert- und Phase-Transition-Events per Push empfangen werden."
**Warum kritisch:** Eine HA-Automation "Wenn Phase -> Bluete -> Lichtprogramm aendern" funktioniert mit 5-Minuten-Polling, aber ein Tank-Leck-Alert, der erst nach 60 Sekunden ankommt, ist suboptimal. Sicherheitsrelevante Events sollten in <5 Sekunden bei HA sein.
**Konkreter Vorschlag:** MQTT-Publisher als Celery-Task. Topic-Struktur: `kamerplanter/{tenant}/events/{event_type}`. Payload als JSON mit Entity-Key, Timestamp, Old/New State. Redis ist bereits Celery-Broker -- MQTT-Bridge oder direkter Paho-Client in Celery-Task ist low-effort. Die Custom Integration haette dann einen `MqttAlertListener` neben dem `AlertCoordinator`.
**Prioritaet:** Mittel (Polling ist akzeptabel fuer MVP, aber MQTT-Events waeren ein grosses Upgrade fuer Safety-Szenarien)

### HA-F-004: Energiemonitoring-Integration
**Integrationsrichtung:** Seite B (HA -> KP)
**Was fehlt:** Kein Modell fuer Stromverbrauch (W/kWh) pro Aktor oder Location. Jeder meiner Aktoren hat einen Shelly mit Power-Monitoring -- die Daten liegen in HA, aber KP kann nichts damit anfangen.
**Warum relevant:** Kosten-pro-Pflanze und Kosten-pro-Ernte sind fuer jeden Grower relevant. REQ-018 hat `Actuator.power_watts` als statische Leistungsangabe, aber keine dynamische Energieerfassung.
**Konkreter Vorschlag:** `energy_entity_id: Optional[str]` auf Actuator fuer HA-Energie-Sensor. Celery-Task aggregiert taeglichen Verbrauch pro Location. Dashboard-Widget "Energiekosten letzte 30 Tage".
**Prioritaet:** Niedrig (nice-to-have, kein Blocker)

### HA-F-005: Webhook-Callback von HA zurueck an KP
**Integrationsrichtung:** Seite B/C (HA -> KP Feedback)
**Was fehlt:** Wenn HA eine Bewaesserung ausloest (Modus B: HA regelt selbst), muss KP davon erfahren, um ein `WateringEvent` (REQ-014) zu erstellen. Aktuell gibt es keinen Mechanismus fuer HA -> KP Callbacks.
**Warum relevant:** Im Modus B (KP liefert Sollwerte, HA regelt) entsteht eine Dokumentationsluecke: Die Bewaesserung findet statt, aber KP weiss nichts davon. Die Pflegeerinnerung (REQ-022) wuerde weiter "Giessen faellig" anzeigen.
**Konkreter Vorschlag:** Webhook-Endpoint `POST /api/v1/webhooks/ha-event` der Aktionen wie `watering_completed`, `actuator_state_changed` entgegennimmt. HA sendet via `rest_command` oder `webhook`-Automation. Alternativ: MQTT-Subscribe in KP fuer HA-State-Changes.
**Prioritaet:** Mittel (nur relevant fuer Modus B; im Modus A steuert KP selbst und kennt alle Aktionen)

---

## Unvollstaendig -- Richtung stimmt, Details fehlen

### HA-U-001: HA WebSocket API statt REST-Polling fuer Sensor-Import
**Vorhandene Anforderung:** REQ-005 erwaehnt "REST API und WebSocket fuer Live-Updates"
**Was fehlt:** `HomeAssistantConnector` implementiert nur REST-Polling. Die HA WebSocket API (`/api/websocket`) ist effizienter: einmalige `subscribe_events` statt periodische GET-Requests.
**HA-Perspektive:** Mein HA-Server hat aktuell 300+ Entitaeten. 15 Sensoren alle 30 Sekunden per REST abfragen = 30 Requests/Minute. Mit WebSocket-Subscription: 1 Connection, Events nur bei Aenderung.
**Empfehlung:** Neben REST-Connector einen WebSocket-Connector als Alternative. REST fuer einfache Setups, WebSocket fuer Power-User. Prioritaet: Mittel.

### HA-U-002: Einheiten-Konvertierung bei Sensor-Import
**Was fehlt:** Keine explizite Konvertierungslogik fuer imperiale Einheiten. HA liefert in der vom Nutzer konfigurierten Einheit (Fahrenheit, PSI, gallons).
**Empfehlung:** Konvertierungslayer im `HomeAssistantConnector` basierend auf `data['attributes']['unit_of_measurement']`. Prioritaet: Niedrig (hauptsaechlich US-Nutzer betroffen).

### HA-U-003: Multi-HA-Instanz-Support
**Was fehlt:** Nur eine HA-Instanz. Fortgeschrittene haben separate HA pro Gebaeudeteil.
**Empfehlung:** Registry-Pattern analog zu `AdapterRegistry` (REQ-011). Niedrige Prioritaet.

### HA-U-004: Sensor-Mapping-UI im Frontend
**Was fehlt:** Kein Entity-Browser im Frontend. `ha_entity_id` ist ein Freitext-Feld statt Dropdown.
**Empfehlung:** "HA-Entity-Browser": KP ruft `GET /api/states` auf HA ab, zeigt Dropdown gefiltert nach Parametertyp. Mittlere Prioritaet fuer UX.

### HA-U-005: Reconnect-Strategie bei HA-Ausfall
**Was fehlt:** REQ-005/REQ-018 definieren Fallback-Verhalten (Tasks generieren, Fail-Safe-States). Aber keine explizite Reconnect-Strategie: Wie oft versucht KP, die HA-Verbindung wiederherzustellen? Exponentielles Backoff? Maximale Retry-Dauer?
**Empfehlung:** Reconnect-Policy auf `HomeAssistantConnector`: Initial-Retry nach 30s, exponentielles Backoff bis max 5 Minuten, Alert nach 3 fehlgeschlagenen Versuchen. Niedrige Prioritaet (implizit durch Celery-Task-Scheduling abgedeckt).

### HA-U-006: Aquaponik-Sensoren (REQ-026)
**Was fehlt:** REQ-026 definiert TAN/NH3/NO2/NO3/DO als kritische Parameter fuer Aquaponik. Diese Sensoren sind typischerweise Atlas Scientific Probes via ESPHome -> HA. Die Sensor-Import-Matrix in REQ-005 deckt die Standard-Parameter ab, aber Aquaponik-spezifische Sensoren (Ammoniak, Nitrit) sind nicht explizit als `parameter`-Typ aufgefuehrt.
**Empfehlung:** `parameter`-Enum in REQ-005 um `ammonium`, `nitrite`, `nitrate` erweitern. Niedrige Prioritaet (betrifft nur Aquaponik-Nutzer).

---

## Grenzziehung unklar -- Wer macht was?

### HA-G-001: VPD-Regelung -- KP ControlEngine vs. HA-Automation
**Status:** Durch HA-CUSTOM-INTEGRATION.md Abschnitt 5 weitgehend geklaert.
**Verbleibende Frage:** Bei Modus B (KP liefert Sollwerte): Welche Entities braucht HA genau? `sensor.kp_{plant}_vpd_target` ist definiert, aber HA braucht auch die aktuellen Hysterese-Parameter (on/off-Schwellwerte), um die Regelung korrekt zu implementieren.
**Empfehlung:** Bei Modus B zusaetzliche Entities: `sensor.kp_{plant}_vpd_target_high` (= target + 0.2) und `sensor.kp_{plant}_vpd_target_low` (= target - 0.1). Oder als Attribute des Target-Sensors.

### HA-G-002: Bewaesserung -- KP-Schedule vs. HA-Automation
**Status:** Steuerungsmodi geklaert, aber Feedback-Loop bei Modus B offen (siehe HA-F-005).
**Empfehlung:** Bei Modus B: HA -> KP Webhook fuer WateringEvent-Dokumentation.

### HA-G-003: Lichtsteuerung -- Photoperiode vs. DLI
**Status:** REQ-018 definiert beide Steuerungsarten.
**Empfehlung:** Klare Dokumentation: Indoor-Zeitplan -> HA-Automation (einfacher Timer). DLI-Anpassung -> KP ControlEngine (nur KP hat den DLI-Akkumulator). Gewaechshaus-Supplemental-Light -> KP entscheidet, HA fuehrt aus. Modus B: KP publisht `sensor.kp_{location}_dli_deficit` als Trigger fuer HA.

---

## Gut geloest -- Das passt fuer die HA-Integration

1. **Sensor-Datenmodell (REQ-005):** `ha_entity_id` und `mqtt_topic` direkt auf dem Sensor-Node, `source`-Tracking auf jeder Observation, Quality-Scoring, 4-stufige Fallback-Kette (HA -> MQTT -> Wetter -> manuell). Die `HomeAssistantConnector`-Klasse zeigt HA-REST-API-Erfahrung.

2. **Aktor-Modell (REQ-018):** `protocol: home_assistant/mqtt/manual` mit Pydantic-Validator. 19 Aktortypen decken alles ab. Fail-Safe-States durchdacht (Abluft=ON bei Ausfall). VPD-Controller als gekoppelter Regelkreis statt isolierte Schwellwerte. CO2-PPFD-Kopplung und DIF/DROP-Steuerung zeigen tiefes Domaenenwissen.

3. **Graceful Degradation:** Durchgaengiges Muster: HA offline -> manueller Task. Kein Feature bricht ohne HA. Das ist der wichtigste Grundsatz fuer optionale Integrationen.

4. **M2M API-Keys (REQ-023 v1.4, NEU):** `kp_`-Prefix, SHA-256-Hash, revokable, 1000 req/min Rate Limit. Genau was die Custom Integration braucht. Light-Modus eliminiert Auth komplett fuer lokale Setups.

5. **iCal-Export (REQ-015):** CalendarFeed mit Token-basiertem webcal://-Zugang. Direkt als HA Calendar-Entity nutzbar. HA-CUSTOM-INTEGRATION.md HA-006 definiert die Implementierung.

6. **Hysterese und Prioritaeten (REQ-018):** HysteresisConfig mit min_on/off_duration und Cooldown verhindert Relais-Klickern. Prioritaetssystem (Override > Safety > Rules > Schedules) klar definiert.

7. **Light-Modus (REQ-027):** Fuer lokale HA-Setups perfekt: KP auf Home-Server, kein Login, HA greift direkt zu. KAMERPLANTER_MODE=light eliminiert Auth-Overhead fuer Custom Integration.

8. **Wetter-Integration (REQ-005):** DWD/OpenWeatherMap/Open-Meteo als Adapter fuer Outdoor. Frostwarnung als HA Binary Sensor nutzbar. 6 Warnungstypen mit passenden Aktionen.

9. **Emergency Stop (REQ-018):** `POST /api/v1/emergency-stop` mit 3 Szenarien. Kann als HA-Service exponiert werden fuer physischen Notfall-Button.

10. **Audit-Trail (REQ-018):** `ControlEvent`-Collection mit `sensor_reading_at_trigger`. Perfekt fuer Debugging von Regelkreisen.

11. **HA-CUSTOM-INTEGRATION.md (NEU):** Komplette Spezifikation der Custom Integration als eigenstaendiges Projekt. Config Flow, Entity Registry, 5 Coordinators, 7 NFRs, Steuerungsmodi, 5 Automation Blueprints. Professionelle Qualitaet.

12. **Steuerungsmodi dokumentiert (NEU):** Modus A vs. B klar definiert mit Warnung: "Beide Modi duerfen NICHT gleichzeitig fuer denselben Aktor aktiv sein". Genau richtig.

---

## HA Custom Integration Feature-Scope

Die Custom Integration (`kamerplanter-ha`) ist ein **separates Repository** und wird ueber HACS installiert. Sie ist NICHT Teil des Kamerplanter-Backends. HA-CUSTOM-INTEGRATION.md definiert den vollstaendigen Scope.

### Architektur (aus HA-CUSTOM-INTEGRATION.md)

```
custom_components/kamerplanter/
  __init__.py          # Setup, Config Entry, Platform-Registrierung
  manifest.json        # HACS-Manifest (iot_class: cloud_polling)
  config_flow.py       # 4-Step: URL -> Auth -> Tenant -> Entities
  coordinator.py       # 5 DataUpdateCoordinators
  sensor.py            # 15+ Sensor-Entities
  binary_sensor.py     # needs_attention, sensor_offline
  calendar.py          # iCal-Feed via CalendarEntity
  todo.py              # Tasks als TodoListEntity
  button.py            # Refresh-Buttons (HA-NFR-007)
  diagnostics.py       # Config-Entry-Diagnostics
  const.py             # Konstanten, Event-Typen
  strings.json         # DE/EN
  translations/
```

### Coordinator-Design (aus HA-CUSTOM-INTEGRATION.md HA-004)

| Coordinator | Polling-Intervall | API-Endpoint | Entities | Min-Intervall |
|-------------|-------------------|-------------|----------|---------------|
| `PlantCoordinator` | 300s (5 min) | `GET /api/v1/t/{slug}/plants/` | Phase, Days, VPD Target, EC Target, Harvest Readiness, Karenz, Health Score | 120s |
| `LocationCoordinator` | 300s (5 min) | `GET /api/v1/t/{slug}/locations/` | Active Plants, Capacity, VPD Current | 120s |
| `TankCoordinator` | 120s (2 min) | `GET /api/v1/t/{slug}/tanks/` + `/states/latest` | EC, pH, Fill Level, Water Temp | 60s |
| `AlertCoordinator` | 60s (1 min) | `GET /api/v1/t/{slug}/alerts/?active=true` | Needs Attention, Sensor Offline | 30s |
| `TaskCoordinator` | 300s (5 min) | `GET /api/v1/t/{slug}/tasks/?status=pending` | Todo Items | 120s |

### NFR-Qualitaet

HA-CUSTOM-INTEGRATION.md definiert 7 NFRs (HA-NFR-001 bis HA-NFR-007) die zeigen, dass der Autor HA-Custom-Integration-Erfahrung hat:
- **HA-NFR-001:** Entity-Referenzen via `hass.data` statt String-Konstruktion -- verhindert ULID-Probleme
- **HA-NFR-002:** Service-Idempotenz-Guard (`has_service` Check) -- verhindert doppelte Registrierung
- **HA-NFR-003:** `async_write_ha_state()` fuer sofortige UI-Updates nach User-Aktionen
- **HA-NFR-004:** `RestoreEntity` fuer alle Sensors + `helpers.storage` mit Schema-Versionierung
- **HA-NFR-005:** Event-Bus fuer Cross-Plattform-Kommunikation statt direkte Imports
- **HA-NFR-006:** `add_update_listener` mit `async_on_unload` fuer sofortigen Options-Reload
- **HA-NFR-007:** `ButtonEntity` fuer serverseitige Aktionen statt Jinja-Templates

Das ist weit ueber dem Niveau der meisten HACS-Integrationen. Respekt.

---

## Optionalitaets-Checkliste (aus HA-CUSTOM-INTEGRATION.md Abschnitt 7)

| Feature | Ohne HA nutzbar? | Ohne MQTT nutzbar? | Nur manuell nutzbar? | Kommentar |
|---------|:----------------:|:------------------:|:--------------------:|-----------|
| Phasensteuerung (REQ-003) | Ja | Ja | Ja | Manuell oder zeitbasiert. Aktor-Anpassung nur bei HA. |
| Duenge-Logik (REQ-004) | Ja | Ja | Ja | Reine Berechnungslogik. |
| Sensor-Monitoring (REQ-005) | Ja | Ja | Ja | Manuelle Eingabe als vollwertiger Fallback. |
| Aktor-Steuerung (REQ-018) | Eingeschraenkt | Eingeschraenkt | Ja (Tasks) | `protocol: manual` -> Tasks statt Befehle. |
| Aufgabenplanung (REQ-006) | Ja | Ja | Ja | HA-unabhaengig. Mehr Tasks bei HA-Ausfall. |
| Erntemanagement (REQ-007) | Ja | Ja | Ja | Reine Domaenenlogik. |
| IPM-System (REQ-010) | Ja | Ja | Ja | Manuelle Inspektionen. |
| Kalenderansicht (REQ-015) | Ja | Ja | Ja | iCal-Export HA-unabhaengig. |
| Tankmanagement (REQ-014) | Ja | Ja | Ja | `source: manual`. |
| Pflegeerinnerungen (REQ-022) | Ja | Ja | Ja | Serverseitige Generierung. |
| Onboarding (REQ-020) | Ja | Ja | Ja | Rein UI-basiert. |
| Aquaponik (REQ-026) | Ja | Ja | Ja | Manuelle Wassertests als Fallback. |

---

## Typische HA-Automations-Blueprints

### Blueprint 1: Phasenwechsel -> Lichtprogramm aendern

```yaml
# Modus B: KP liefert Phase, HA steuert Licht
alias: "KP: Bluete-Start -> 12/12 Licht"
description: "Lichtprogramm auf 12h/12h umstellen wenn Kamerplanter Bluete meldet"
trigger:
  - platform: state
    entity_id: sensor.kp_northern_lights_phase
    to: "flowering"
condition: []
action:
  - service: automation.turn_off
    target:
      entity_id: automation.licht_18_6_veg
  - service: automation.turn_on
    target:
      entity_id: automation.licht_12_12_bloom
  - service: notify.mobile_app_phone
    data:
      title: "Kamerplanter: Bluete gestartet"
      message: "Northern Lights wechselt in Bluete. Licht auf 12/12 umgestellt."
mode: single
```

### Blueprint 2: VPD-Sollwert -> Befeuchter-Steuerung

```yaml
# Modus B: KP liefert VPD-Sollwert, HA regelt Befeuchter
alias: "KP: VPD-Regelung mit KP-Sollwert"
description: "Befeuchter ein/aus basierend auf Kamerplanter VPD-Ziel"
trigger:
  - platform: template
    value_template: >
      {{ states('sensor.growzelt_vpd') | float(0) >
         (states('sensor.kp_northern_lights_vpd_target') | float(1.0) + 0.2) }}
    id: vpd_too_high
  - platform: template
    value_template: >
      {{ states('sensor.growzelt_vpd') | float(0) <
         (states('sensor.kp_northern_lights_vpd_target') | float(1.0) - 0.1) }}
    id: vpd_ok
condition: []
action:
  - choose:
      - conditions:
          - condition: trigger
            id: vpd_too_high
        sequence:
          - service: switch.turn_on
            target:
              entity_id: switch.befeuchter_zelt_1
      - conditions:
          - condition: trigger
            id: vpd_ok
        sequence:
          - service: switch.turn_off
            target:
              entity_id: switch.befeuchter_zelt_1
mode: single
```

### Blueprint 3: Erntebereitschaft -> Push-Benachrichtigung

```yaml
# Trigger: Erntebereitschaft > 80% UND Karenz abgelaufen
alias: "KP: Ernte bald bereit"
description: "Benachrichtigung wenn Erntebereitschaft 80% erreicht"
trigger:
  - platform: numeric_state
    entity_id: sensor.kp_white_widow_harvest_readiness
    above: 80
condition:
  - condition: template
    value_template: >
      {{ states('sensor.kp_white_widow_karenz_remaining') | int(99) == 0 }}
action:
  - service: notify.mobile_app_phone
    data:
      title: "Ernte bereit!"
      message: >
        White Widow Readiness: {{ states('sensor.kp_white_widow_harvest_readiness') }}%.
        Karenz abgelaufen. Trichome pruefen!
  - service: persistent_notification.create
    data:
      title: "Kamerplanter: Ernte bereit"
      message: "White Widow ist erntereif. Readiness Score: {{ states('sensor.kp_white_widow_harvest_readiness') }}%"
mode: single
```

### Blueprint 4: Frostwarnung -> Gewaechshaus-Heizung

```yaml
# Nutzt KP Wetter-Integration (REQ-005) oder direkte HA-Wetter-Integration
alias: "KP: Frostwarnung -> Heizung ein"
description: "Gewaechshaus-Heizung einschalten bei KP-Frostwarnung"
trigger:
  - platform: state
    entity_id: binary_sensor.kp_gewaechshaus_frost_warning
    to: "on"
condition:
  - condition: state
    entity_id: switch.gewaechshaus_heizung
    state: "off"
action:
  - service: switch.turn_on
    target:
      entity_id: switch.gewaechshaus_heizung
  - service: climate.set_temperature
    target:
      entity_id: climate.gewaechshaus
    data:
      temperature: 5
  - service: notify.mobile_app_phone
    data:
      title: "Frostwarnung!"
      message: >
        Kamerplanter meldet Frost fuer {{ state_attr('binary_sensor.kp_gewaechshaus_frost_warning', 'location') }}.
        Heizung eingeschaltet (Frostschutz 5 Grad C).
mode: single
```

### Blueprint 5: Tank niedrig -> Auffuell-Erinnerung

```yaml
# Trigger: Tank-Fuellstand unter 20%
alias: "KP: Tank fast leer"
description: "Warnung wenn Tank unter 20% Fuellstand"
trigger:
  - platform: numeric_state
    entity_id: sensor.kp_haupttank_zelt1_fill_level
    below: 20
condition:
  - condition: template
    value_template: >
      {{ (as_timestamp(now()) - as_timestamp(
          states.sensor.kp_haupttank_zelt1_fill_level.last_changed)) > 3600 }}
action:
  - service: notify.mobile_app_phone
    data:
      title: "Tank fast leer!"
      message: >
        Haupttank Zelt 1: {{ states('sensor.kp_haupttank_zelt1_fill_level') }}% Restfuellstand.
        EC: {{ states('sensor.kp_haupttank_zelt1_ec') }} mS/cm,
        pH: {{ states('sensor.kp_haupttank_zelt1_ph') }}.
        Bitte auffuellen!
mode: single
```

---

## Empfehlung: Top-5-Massnahmen

1. **MQTT-Event-Bus fuer kritische Zustandsaenderungen (HA-F-001):** Phase-Transitions, Tank-Alerts, Emergency-Events auf MQTT publishen. Redis ist im Stack, Paho-MQTT-Client in einem Celery-Task ist low-effort. Die Custom Integration kann dann `AlertCoordinator` durch MQTT-Listener ersetzen. -- Verantwortung: Kamerplanter

2. **Webhook-Endpoint fuer HA-Callbacks (HA-F-005):** `POST /api/v1/webhooks/ha-event` fuer Aktionen die HA im Modus B ausfuehrt (Bewaesserung, Licht, Temperatur). Ohne das entsteht eine Dokumentationsluecke bei Modus-B-Nutzern. -- Verantwortung: Kamerplanter

3. **Sensor-Mapping-UI mit HA-Entity-Browser (HA-U-004):** Statt `ha_entity_id` als Freitextfeld ein Dropdown das `GET /api/states` von HA abruft und nach Parametertyp filtert. Grosser UX-Gewinn, mittlerer Aufwand. -- Verantwortung: Kamerplanter Frontend

4. **WebSocket-Connector als Alternative zu REST-Polling (HA-U-001):** `HomeAssistantWebSocketConnector` neben dem bestehenden REST-Connector. Effizienter fuer kontinuierliches Sensor-Monitoring (1 Connection statt periodische Requests). -- Verantwortung: Kamerplanter

5. **HA Custom Integration MVP starten (HA-001 bis HA-008):** Alle Voraussetzungen sind erfuellt (API-Keys, Health-Check, Entity-Mapping spezifiziert). MVP: Config Flow + PlantCoordinator + TankCoordinator + Sensor-Entities. Community-Projekt auf GitHub starten. -- Verantwortung: Separates Repository

---

## Feature-Relevanz-Tabelle (alle REQs)

| REQ | Titel | HA-Relevanz | Integrationsrichtung | Kommentar |
|-----|-------|:-----------:|---------------------|-----------|
| REQ-001 | Stammdatenverwaltung | Keine | -- | Reine App-Logik (Species, Cultivar, Botanical Family). |
| REQ-002 | Standortverwaltung | Niedrig | Seite A | Location-Kapazitaet als Sensor. GPS fuer Wetter-API. |
| REQ-003 | Phasensteuerung | Hoch | Seite A + C | Kern-Trigger fuer HA-Automations. VPD/EC-Targets als Sollwerte. |
| REQ-004 | Duenge-Logik | Mittel | Seite A + C | EC-Targets fuer Dosier-Automations. Mixing rein KP-intern. |
| REQ-005 | Hybrid-Sensorik | Hoch | Seite B | KERN der Sensor-Integration. HA-Entity-Mapping, Fallback, Provenance, Wetter-API. |
| REQ-006 | Aufgabenplanung | Mittel | Seite A | Tasks als HA Todo-Entity. Fallback-Tasks bei HA-Ausfall. Timer als Countdown-Sensor moeglich. |
| REQ-007 | Erntemanagement | Mittel | Seite A | ReadinessScore + Karenz als Sensor. Ernte-Push. |
| REQ-008 | Post-Harvest | Niedrig | Seite B | Trockenraum-Klima koennte ueber HA-Sensoren kommen. |
| REQ-009 | Dashboard | Mittel | Seite A | WebSocket-Updates als Basis fuer Event-Publishing nutzbar. |
| REQ-010 | IPM-System | Niedrig | Seite A | Befall-Warnung als Binary Sensor. Karenz-Gate fuer Ernte-Automation. |
| REQ-011 | Externe Stammdatenanreicherung | Keine | -- | GBIF/Perenual -- reine Backend-Logik. |
| REQ-012 | Stammdaten-Import | Keine | -- | CSV/JSON-Import -- reine App-Funktion. |
| REQ-013 | Pflanzdurchlauf | Niedrig | Seite A | Run-Status als Sensor (planned/active/harvesting). |
| REQ-014 | Tankmanagement | Hoch | Seite A + B | TankState mit `source: home_assistant`. EC/pH/Fuellstand als Sensor-Entities. |
| REQ-015 | Kalenderansicht | Hoch | Seite A | iCal-Feed direkt als HA Calendar-Entity. Eleganteste Integration. |
| REQ-016 | InvenTree-Integration | Keine | -- | Inventarverwaltung -- kein HA-Bezug. |
| REQ-017 | Vermehrungsmanagement | Keine | -- | Genetische Lineage -- Graph-Logik. |
| REQ-018 | Umgebungssteuerung | Hoch | Seite C | KERN der Aktor-Integration. Service-Calls, Fail-Safe, Hysterese, VPD-Controller, DLI. |
| REQ-019 | Substratverwaltung | Keine | -- | Substrat-Typen, Wiederverwendung -- reine Domaenenlogik. |
| REQ-020 | Onboarding-Wizard | Niedrig | -- | Starter-Kits koennten HA-Entity-Mapping vorschlagen (Future). |
| REQ-021 | UI-Erfahrungsstufen | Keine | -- | Reine Frontend-Logik (Field-Visibility). |
| REQ-022 | Pflegeerinnerungen | Mittel | Seite A | Care-Reminders als Sensor. Naechste Giess-Erinnerung als Trigger. |
| REQ-023 | Benutzerverwaltung | Mittel | Seite A | M2M API-Keys (v1.4) fuer Custom Integration. Light-Modus fuer lokale Setups. |
| REQ-024 | Mandantenverwaltung | Niedrig | Seite A | Tenant-Scope in API-URLs. Config Flow Tenant-Auswahl. |
| REQ-025 | Datenschutz (DSGVO) | Keine | -- | Rechtliche Compliance. |
| REQ-026 | Aquaponik-Management | Mittel | Seite B + C | Aquaponik-Sensoren (TAN, NO2, DO) ueber HA. Pumpen/Belueftung steuern. Fisch-Fuetterung als Task. |
| REQ-027 | Light-Modus | Hoch | Seite A | Ideal fuer lokale HA-Integration: kein Auth-Overhead. |
| NFR-001 | Separation of Concerns | Mittel | Seite A | API-Stabilitaet, M2M-Consumer-Garantie. 5-Schichten sichern stabile Schnittstelle. |
| NFR-002 | Kubernetes-Plattform | Niedrig | -- | Deployment -- kein direkter HA-Bezug. Docker Compose fuer lokale Setups relevant. |
| NFR-005 | Technische Dokumentation | Mittel | Seite A | OpenAPI-Schema als versioniertes Artefakt fuer Custom Integration. |
| NFR-006 | API-Fehlerbehandlung | Mittel | Seite A | Strukturierte Error-Responses fuer Coordinator-Fehlerbehandlung. |
| NFR-007 | Betriebsstabilitaet | Niedrig | -- | SLIs/SLOs intern. Health-Check-Endpoint fuer Custom Integration relevant. |
| NFR-011 | Retention Policy | Keine | -- | Datensparsamkeit -- kein HA-Bezug. |
| UI-NFR-011 | Kiosk-Modus | Niedrig | Grenzfall | Kiosk-Tablet im Growroom -- HA Dashboard Alternative/Ergaenzung. |
| UI-NFR-012 | PWA-Offline | Niedrig | Grenzfall | Offline-Erfassung -- HA hat eigene Offline-Story (ESPHome lokal). |
| HA-INTEGRATION | Custom Integration Spec | Hoch | Alle | Definiert die komplette kamerplanter-ha Integration. Eigenstaendiges Dokument. |
