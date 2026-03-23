---
req_id: REQ-018
title: Umgebungssteuerung, Aktorik-Integration & Automatisierungsregeln
category: Automatisierung
test_count: 72
coverage_areas:
  - Aktoren-Verwaltung (CRUD, Typen, Protokolle)
  - Location-Zuordnung von Aktoren
  - Protokoll-Validierung (HA, MQTT, Manuell)
  - Dimmbare Aktoren (min_value / max_value)
  - Zeitplaene (ControlSchedule CRUD, Zeitplan-Toggle)
  - Automatisierungsregeln (ControlRule CRUD, Regel-Toggle)
  - Hysterese-Konfiguration (on/off-Schwellwerte, Mindestlaufzeit)
  - Sicherheitsregeln (is_safety_rule, Prioritaet)
  - Compound-Regeln (AND/OR-Verknuepfung)
  - Manueller Override (zeitlich begrenzt, Ablauf)
  - Steuerungshistorie (ControlEvent-Log)
  - Energieverbrauch-Ansicht pro Location
  - Phasen-Kontroll-Profile (PhaseControlProfile CRUD)
  - Phasen-Trigger (automatische Profil-Anwendung)
  - DLI-Lichtsteuerung / Photoperiod-Schutz
  - CO2-PPFD-Kopplung
  - DIF/DROP-Temperatursteuerung
  - Fail-Safe-States
  - Notabschaltung (Emergency-Stop)
  - Konfliktgruppen-Anzeige
  - Home-Assistant-Integration (Verbindungsstatus, Entity-Mapping)
  - HA-Visibility-Toggle (ha_token_set Logik)
  - Dry-Run Regeltest
  - Manuelle Aktoren (Fallback-Task-Erzeugung)
generated: 2026-03-21
version: "1.2"
---

# TC-REQ-018: Umgebungssteuerung & Aktorik

Dieses Dokument enthaelt End-to-End-Testfaelle aus **REQ-018 Umgebungssteuerung, Aktorik-Integration & Automatisierungsregeln v1.2**, ausschliesslich aus der Perspektive eines Nutzers im Browser. Keine API-Calls, HTTP-Statuscodes oder Datenbankabfragen erscheinen in diesen Testfaellen. Alle Aussagen beschreiben, was der Nutzer sieht, anklickt, eintippt und auf dem Bildschirm erwartet.

Die UI-Sprache ist **Deutsch** (Standard-Locale). Alle Labels, Buttons und Meldungen referenzieren die deutschen i18n-Texte.

REQ-018 schliesst den Regelkreis zwischen Sensorik (REQ-005, Input) und Aktorik (Output). Die UI erlaubt dem Nutzer Aktoren zu konfigurieren, Zeitplaene und Regeln zu definieren, Overrides zu setzen und das Systemverhalten ueber den Steuerungshistorie-Log nachzuvollziehen.

> **Hinweis:** REQ-018 ist zum Zeitpunkt der Testfallerstellung noch nicht im Frontend implementiert. Diese Testfaelle beschreiben das erwartete UI-Verhalten gemaess Spezifikation und dienen als Grundlage fuer die spaetere Selenium/Playwright-Implementierung. Seitenpfade (z.B. `/standorte/{key}/aktoren`) sind den API-Endpunkten der Spezifikation entnommen und muessen im Frontend entsprechend umgesetzt werden.

---

## 1. Aktoren-Verwaltung

### TC-018-001: Aktor-Listenansicht fuer eine Location oeffnen

**Requirement**: REQ-018 § 3 — REST-API GET /api/v1/locations/{key}/actuators; DoD "Aktor-CRUD"
**Priority**: Critical
**Category**: Listenansicht
**Preconditions**:
- Nutzer ist eingeloggt und Mitglied des aktiven Tenants
- Location "Grow Zelt 1" existiert und hat mindestens 2 Aktoren (z.B. "Hauptlicht Zelt 1", "Abluft Zelt 1")

**Testschritte**:
1. Nutzer navigiert zu `/standorte` und oeffnet die Location "Grow Zelt 1"
2. Nutzer klickt auf den Reiter oder Menuepunkt "Aktoren"

**Erwartete Ergebnisse**:
- Die Aktoren-Liste fuer "Grow Zelt 1" wird angezeigt
- Jeder Eintrag zeigt: Name, Aktor-Typ (z.B. "Licht", "Abluftventilatoren"), Protokoll, aktuellen Zustand (z.B. "AN – 100%") sowie Online-Status (gruener/roter Indikator)
- Nicht erreichbare Aktoren (is_online=false) sind visuell als "Offline" markiert
- Eine Schaltflaeche "Aktor hinzufuegen" ist sichtbar

**Nachbedingungen**:
- Kein Status geaendert (nur Anzeige)

**Tags**: [req-018, aktor, liste, location, standort]

---

### TC-018-002: Neuen Aktor (Home-Assistant-Protokoll) erstellen

**Requirement**: REQ-018 § 3 — POST /api/v1/locations/{key}/actuators; Protokoll-Validierung "HA-Aktoren erfordern ha_entity_id"
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- Nutzer ist eingeloggt
- Location "Grow Zelt 1" existiert
- HA-Integration ist aktiv (ha_token_set=true)

**Testschritte**:
1. Nutzer navigiert zur Aktoren-Liste von "Grow Zelt 1"
2. Nutzer klickt "Aktor hinzufuegen"
3. Im Dialog gibt der Nutzer ein:
   - Name: "Befeuchter Zelt 1"
   - Typ: "Befeuchter" (humidifier)
   - Protokoll: "Home Assistant"
   - HA Entity-ID: "humidifier.zelt_1"
   - Faehigkeiten: "Ein/Aus" (on_off)
   - Nennleistung: "30" W
   - Fail-Safe-Zustand: "Aus"
4. Nutzer klickt "Speichern"

**Erwartete Ergebnisse**:
- Der Dialog schliesst sich
- In der Aktoren-Liste erscheint der neue Eintrag "Befeuchter Zelt 1" mit Typ "Befeuchter", Protokoll "Home Assistant" und Status "Unbekannt" (noch kein State)
- Eine Erfolgs-Benachrichtigung (Snackbar) erscheint: "Aktor wurde erfolgreich erstellt"

**Nachbedingungen**:
- Aktor "Befeuchter Zelt 1" ist in der Liste sichtbar und der Location "Grow Zelt 1" zugeordnet

**Tags**: [req-018, aktor, erstellen, home-assistant, happy-path]

---

### TC-018-003: Aktor erstellen ohne ha_entity_id bei HA-Protokoll schlaegt fehl (Formvalidierung)

**Requirement**: REQ-018 § 3 — Protokoll-Validierung: "ha_entity_id erforderlich fuer Home Assistant-Protokoll"
**Priority**: High
**Category**: Formvalidierung
**Preconditions**:
- Nutzer ist eingeloggt
- HA-Integration ist aktiv (ha_token_set=true)

**Testschritte**:
1. Nutzer oeffnet den Dialog "Aktor hinzufuegen" fuer eine Location
2. Nutzer waehlt Protokoll "Home Assistant"
3. Nutzer laesst das Feld "HA Entity-ID" leer
4. Nutzer klickt "Speichern"

**Erwartete Ergebnisse**:
- Der Dialog bleibt geoeffnet
- Unter dem Feld "HA Entity-ID" erscheint eine Fehlermeldung: "HA Entity-ID ist erforderlich fuer das Protokoll Home Assistant"
- Kein Aktor wird erstellt

**Nachbedingungen**:
- Keine Datenaenderung

**Tags**: [req-018, aktor, formvalidierung, home-assistant, ha-entity-id]

---

### TC-018-004: Aktor erstellen ohne mqtt_command_topic bei MQTT-Protokoll schlaegt fehl (Formvalidierung)

**Requirement**: REQ-018 § 3 — Protokoll-Validierung: "mqtt_command_topic erforderlich fuer MQTT-Protokoll"
**Priority**: High
**Category**: Formvalidierung
**Preconditions**:
- Nutzer ist eingeloggt

**Testschritte**:
1. Nutzer oeffnet den Dialog "Aktor hinzufuegen"
2. Nutzer waehlt Protokoll "MQTT"
3. Nutzer laesst "MQTT Command-Topic" leer
4. Nutzer klickt "Speichern"

**Erwartete Ergebnisse**:
- Der Dialog bleibt geoeffnet
- Fehlermeldung unter dem Feld "MQTT Command-Topic": "MQTT Command-Topic ist erforderlich fuer das Protokoll MQTT"
- Kein Aktor wird erstellt

**Nachbedingungen**:
- Keine Datenaenderung

**Tags**: [req-018, aktor, formvalidierung, mqtt, command-topic]

---

### TC-018-005: Dimmbaren Aktor erstellen ohne min_value und max_value schlaegt fehl

**Requirement**: REQ-018 § 3 — Pydantic-Validierung: "min_value und max_value erforderlich fuer dimmbare Aktoren"
**Priority**: High
**Category**: Formvalidierung
**Preconditions**:
- Nutzer ist eingeloggt

**Testschritte**:
1. Nutzer oeffnet den Dialog "Aktor hinzufuegen"
2. Nutzer waehlt Typ "Licht"
3. Nutzer setzt Faehigkeiten: waehlt "Dimmbar" (dimmable)
4. Nutzer laesst "Minimalwert" und "Maximalwert" leer
5. Nutzer klickt "Speichern"

**Erwartete Ergebnisse**:
- Dialog bleibt geoeffnet
- Fehlermeldung: "Minimalwert und Maximalwert sind fuer dimmbare Aktoren erforderlich"
- Kein Aktor wird erstellt

**Nachbedingungen**:
- Keine Datenaenderung

**Tags**: [req-018, aktor, formvalidierung, dimmbar, min-value, max-value]

---

### TC-018-006: Aktor-Detailseite oeffnen und Stammdaten bearbeiten

**Requirement**: REQ-018 § 3 — PUT /api/v1/actuators/{key}; DoD "Aktor-CRUD"
**Priority**: High
**Category**: Detailansicht
**Preconditions**:
- Aktor "Hauptlicht Zelt 1" existiert mit Nennleistung 480 W
- Nutzer ist eingeloggt

**Testschritte**:
1. Nutzer navigiert zur Aktoren-Liste der zugehoerigen Location und klickt auf "Hauptlicht Zelt 1"
2. Die Aktor-Detailseite oeffnet sich
3. Nutzer klickt "Bearbeiten"
4. Nutzer aendert "Nennleistung (W)" von 480 auf 450
5. Nutzer klickt "Speichern"

**Erwartete Ergebnisse**:
- Erfolgs-Snackbar: "Aktor wurde erfolgreich aktualisiert"
- Die Detailansicht zeigt nun Nennleistung "450 W"

**Nachbedingungen**:
- Aktor "Hauptlicht Zelt 1" hat Nennleistung 450 W in der Datenbank

**Tags**: [req-018, aktor, bearbeiten, stammdaten, detailseite]

---

### TC-018-007: Aktor loeschen mit Bestaetigung

**Requirement**: REQ-018 § 3 — DELETE /api/v1/actuators/{key}; DoD "Aktor-CRUD"
**Priority**: High
**Category**: Dialog
**Preconditions**:
- Nutzer ist eingeloggt als Admin
- Aktor "Befeuchter Zelt 1" existiert ohne aktive Regeln oder Zeitplaene

**Testschritte**:
1. Nutzer navigiert zur Aktoren-Liste und oeffnet den Eintrag "Befeuchter Zelt 1"
2. Nutzer klickt "Loeschen"
3. Ein Bestaetigungs-Dialog erscheint: "Sind Sie sicher, dass Sie 'Befeuchter Zelt 1' loeschen moechten? Diese Aktion kann nicht rueckgaengig gemacht werden."
4. Nutzer klickt "Bestaetigen"

**Erwartete Ergebnisse**:
- Der Dialog schliesst sich
- "Befeuchter Zelt 1" verschwindet aus der Aktoren-Liste
- Erfolgs-Snackbar: "Aktor wurde erfolgreich geloescht"

**Nachbedingungen**:
- Aktor "Befeuchter Zelt 1" ist nicht mehr in der Liste vorhanden

**Tags**: [req-018, aktor, loeschen, bestaetigung, admin]

---

### TC-018-008: HA-Felder ausgeblendet wenn HA-Integration inaktiv

**Requirement**: REQ-018 § 1 — UI-Visibility: "Wenn ha_token_set == false, werden ha_entity_id-Felder und die Protocol-Option home_assistant ausgeblendet"
**Priority**: High
**Category**: Zustandswechsel
**Preconditions**:
- Nutzer ist eingeloggt
- HA-Integration ist NICHT konfiguriert (kein HA-Token gesetzt)

**Testschritte**:
1. Nutzer oeffnet den Dialog "Aktor hinzufuegen"
2. Nutzer betrachtet das Protokoll-Dropdown

**Erwartete Ergebnisse**:
- Im Protokoll-Dropdown ist "Home Assistant" NICHT als Option sichtbar
- Nur "MQTT" und "Manuell" sind waehbar
- Das Feld "HA Entity-ID" ist nicht im Formular vorhanden

**Nachbedingungen**:
- Keine Datenaenderung

**Tags**: [req-018, ha-visibility, feature-toggle, protokoll, ha-token]

---

### TC-018-009: CO2-Doser und Entfeuchter koennen nicht Outdoor-Locations zugeordnet werden

**Requirement**: REQ-018 § 3 — ActuatorAssignmentValidator: "CO2-Doser und Entfeuchter nur bei Indoor-Locations"
**Priority**: Medium
**Category**: Formvalidierung
**Preconditions**:
- Nutzer ist eingeloggt
- Eine Outdoor-Location "Gartenbeet" existiert

**Testschritte**:
1. Nutzer navigiert zur Aktoren-Liste der Location "Gartenbeet"
2. Nutzer oeffnet den Dialog "Aktor hinzufuegen"
3. Nutzer waehlt Typ "CO2-Doser"
4. Nutzer klickt "Speichern"

**Erwartete Ergebnisse**:
- Eine Fehlermeldung wird angezeigt: "CO2-Doser ist nur fuer Indoor-Locations geeignet, nicht fuer Outdoor-Standorte"
- Kein Aktor wird erstellt

**Nachbedingungen**:
- Keine Datenaenderung

**Tags**: [req-018, aktor, validierung, outdoor, co2-doser, location-typ]

---

## 2. Zeitplaene (ControlSchedule)

### TC-018-010: Zeitplan fuer einen Aktor erstellen (18/6 Lichtprogramm)

**Requirement**: REQ-018 § 3 — POST /api/v1/actuators/{key}/schedules; DoD "Zeitplaene: CRUD fuer ScheduleEntries"
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- Nutzer ist eingeloggt
- Aktor "Hauptlicht Zelt 1" existiert

**Testschritte**:
1. Nutzer navigiert zur Detailseite von "Hauptlicht Zelt 1"
2. Nutzer klickt auf den Reiter "Zeitplaene"
3. Nutzer klickt "Zeitplan hinzufuegen"
4. Nutzer gibt ein:
   - Name: "Veg-Lichtprogramm 18/6"
   - Typ: "Taeglich" (daily)
   - Eintrag hinzufuegen: "Ein um 06:00, Aus um 00:00", Wert: 100
5. Nutzer klickt "Speichern"

**Erwartete Ergebnisse**:
- Dialog schliesst sich
- Der neue Zeitplan "Veg-Lichtprogramm 18/6" erscheint in der Zeitplan-Liste des Aktors
- Status: "Aktiv"
- Snackbar: "Zeitplan wurde erfolgreich erstellt"

**Nachbedingungen**:
- Zeitplan "Veg-Lichtprogramm 18/6" ist aktiv und dem Aktor zugeordnet

**Tags**: [req-018, zeitplan, erstellen, licht, 18-6, photoperiode]

---

### TC-018-011: Zeitplan ohne Zeitplan-Eintraege schlaegt fehl

**Requirement**: REQ-018 § 3 — ControlSchedule.entries: list[ScheduleEntry] = Field(min_length=1)
**Priority**: High
**Category**: Formvalidierung
**Preconditions**:
- Nutzer ist eingeloggt

**Testschritte**:
1. Nutzer oeffnet den Dialog "Zeitplan hinzufuegen" fuer einen Aktor
2. Nutzer gibt einen Namen ein, waehlt Typ "Taeglich"
3. Nutzer fuegt keinen Zeitplan-Eintrag hinzu
4. Nutzer klickt "Speichern"

**Erwartete Ergebnisse**:
- Dialog bleibt geoeffnet
- Fehlermeldung: "Mindestens ein Zeitplan-Eintrag ist erforderlich"
- Kein Zeitplan wird erstellt

**Nachbedingungen**:
- Keine Datenaenderung

**Tags**: [req-018, zeitplan, formvalidierung, eintraege, min-length]

---

### TC-018-012: Zeitplan mit valid_from nach valid_until schlaegt fehl

**Requirement**: REQ-018 § 3 — ControlSchedule.validate_date_range: "valid_from muss vor valid_until liegen"
**Priority**: Medium
**Category**: Formvalidierung
**Preconditions**:
- Nutzer ist eingeloggt

**Testschritte**:
1. Nutzer oeffnet den Dialog "Zeitplan hinzufuegen"
2. Nutzer setzt "Gueltig ab": 2026-04-01 und "Gueltig bis": 2026-03-01
3. Nutzer klickt "Speichern"

**Erwartete Ergebnisse**:
- Fehlermeldung: "Das Startdatum muss vor dem Enddatum liegen"
- Kein Zeitplan wird erstellt

**Nachbedingungen**:
- Keine Datenaenderung

**Tags**: [req-018, zeitplan, formvalidierung, gueltigkeitszeitraum, datum]

---

### TC-018-013: Zeitplan aktivieren und deaktivieren (Toggle)

**Requirement**: REQ-018 § 3 — POST /api/v1/actuators/{key}/schedules/{sched_key}/toggle
**Priority**: High
**Category**: Zustandswechsel
**Preconditions**:
- Zeitplan "Veg-Lichtprogramm 18/6" existiert und ist aktiv (is_active=true)

**Testschritte**:
1. Nutzer navigiert zur Zeitplan-Liste des Aktors "Hauptlicht Zelt 1"
2. Nutzer klickt den Toggle-Schalter neben "Veg-Lichtprogramm 18/6" (von Aktiv auf Inaktiv)

**Erwartete Ergebnisse**:
- Der Toggle-Schalter zeigt nun "Inaktiv"
- Die Zeile des Zeitplans wird visuell als inaktiv dargestellt (z.B. ausgegraut)
- Snackbar: "Zeitplan wurde deaktiviert"

**Nachbedingungen**:
- Zeitplan "Veg-Lichtprogramm 18/6" ist inaktiv (is_active=false)

**Tags**: [req-018, zeitplan, toggle, aktivieren, deaktivieren]

---

### TC-018-014: Zeitplan loeschen

**Requirement**: REQ-018 § 3 — DELETE /api/v1/actuators/{key}/schedules/{sched_key}
**Priority**: Medium
**Category**: Dialog
**Preconditions**:
- Zeitplan "Bewässerung 3x taeglich" existiert

**Testschritte**:
1. Nutzer navigiert zur Zeitplan-Liste des Bewässerungsventil-Aktors
2. Nutzer klickt auf das Loeschen-Icon neben "Bewässerung 3x taeglich"
3. Bestaetigungs-Dialog erscheint
4. Nutzer klickt "Bestaetigen"

**Erwartete Ergebnisse**:
- Zeitplan verschwindet aus der Liste
- Snackbar: "Zeitplan wurde erfolgreich geloescht"

**Nachbedingungen**:
- Zeitplan "Bewässerung 3x taeglich" ist geloescht

**Tags**: [req-018, zeitplan, loeschen, bestaetigung]

---

### TC-018-015: Zeitplan mit Wochentag-Einschraenkung (woeffentlicher Zeitplan)

**Requirement**: REQ-018 § 3 — ScheduleEntry.days_of_week (0=Mo..6=So)
**Priority**: Medium
**Category**: Happy Path
**Preconditions**:
- Nutzer ist eingeloggt

**Testschritte**:
1. Nutzer oeffnet den Dialog "Zeitplan hinzufuegen" fuer einen Aktor
2. Nutzer waehlt Typ "Woechentlich" (weekly)
3. Nutzer gibt einen Eintrag ein: Ein 08:00, Aus 20:00
4. Nutzer markiert im Wochentag-Auswahl nur: Montag, Mittwoch, Freitag
5. Nutzer klickt "Speichern"

**Erwartete Ergebnisse**:
- Der Zeitplan wird gespeichert
- In der Detail-Ansicht des Zeitplans wird "Mo, Mi, Fr" als aktive Wochentage angezeigt

**Nachbedingungen**:
- Zeitplan mit Wochentag-Einschraenkung ist aktiv

**Tags**: [req-018, zeitplan, woechentlich, wochentage, schedule-entry]

---

## 3. Automatisierungsregeln (ControlRule)

### TC-018-016: Regel erstellen (VPD-Schwellwert → Befeuchter einschalten)

**Requirement**: REQ-018 § 3 — POST /api/v1/actuators/{key}/rules; DoD "Regelbasierte Steuerung"
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- Nutzer ist eingeloggt
- Aktor "Befeuchter Zelt 1" existiert
- Sensor fuer VPD an Location "Grow Zelt 1" ist konfiguriert (REQ-005)

**Testschritte**:
1. Nutzer navigiert zur Detailseite von "Befeuchter Zelt 1"
2. Nutzer klickt auf den Reiter "Automatisierungsregeln"
3. Nutzer klickt "Regel hinzufuegen"
4. Nutzer gibt ein:
   - Name: "VPD-Korrektur Befeuchter"
   - Regeltyp: "Schwellwert" (threshold)
   - Sensor-Parameter: "VPD (kPa)"
   - Bedingung: "Groesser als" (gt), Schwellwert: 1.5
   - Aktion: "Einschalten" (turn_on)
   - Hysterese Ein-Schwellwert: 1.5, Aus-Schwellwert: 1.2
   - Mindestlaufzeit: 120 Sekunden
   - Mindestpause: 300 Sekunden
5. Nutzer klickt "Speichern"

**Erwartete Ergebnisse**:
- Regel "VPD-Korrektur Befeuchter" erscheint in der Regelliste des Aktors
- Status: "Aktiv"
- Snackbar: "Regel wurde erfolgreich erstellt"

**Nachbedingungen**:
- Regel ist aktiv und dem Befeuchter-Aktor zugeordnet

**Tags**: [req-018, regel, erstellen, vpd, schwellwert, befeuchter, happy-path]

---

### TC-018-017: Regel erstellen als Sicherheitsregel (Uebertemperatur → Abluft 100%)

**Requirement**: REQ-018 § 3 — ControlRule.is_safety_rule; DoD "Sicherheitsregeln: Hoehere Prioritaet als regulaere Regeln"
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- Nutzer ist eingeloggt
- Aktor "Abluft Zelt 1" existiert
- Temperatursensor an Location "Grow Zelt 1" ist konfiguriert

**Testschritte**:
1. Nutzer navigiert zur Detailseite von "Abluft Zelt 1" → Reiter "Automatisierungsregeln"
2. Nutzer klickt "Regel hinzufuegen"
3. Nutzer gibt ein:
   - Name: "Uebertemperatur Abluft"
   - Regeltyp: "Schwellwert"
   - Sensor-Parameter: "Temperatur (°C)"
   - Bedingung: "Groesser als", Schwellwert: 30
   - Aktion: "Wert setzen" (set_value), Zielwert: 100
   - Hysterese: Ein 30°C, Aus 27°C
   - Sicherheitsregel: aktiviert (Checkbox markiert)
4. Nutzer klickt "Speichern"

**Erwartete Ergebnisse**:
- Regel erscheint in der Liste mit einem Sicherheitssymbol (z.B. Schild-Icon) neben dem Namen
- Status: "Aktiv"
- Snackbar: "Sicherheitsregel wurde erfolgreich erstellt"

**Nachbedingungen**:
- Sicherheitsregel "Uebertemperatur Abluft" ist aktiv

**Tags**: [req-018, regel, sicherheitsregel, prioritaet, uebertemperatur, abluft]

---

### TC-018-018: Regel erstellen ohne Namen schlaegt fehl

**Requirement**: REQ-018 § 3 — ControlRule.name: Field(min_length=1)
**Priority**: Medium
**Category**: Formvalidierung
**Preconditions**:
- Nutzer ist eingeloggt

**Testschritte**:
1. Nutzer oeffnet den Dialog "Regel hinzufuegen"
2. Nutzer laesst das Feld "Name" leer
3. Nutzer fuellt alle anderen Pflichtfelder korrekt aus
4. Nutzer klickt "Speichern"

**Erwartete Ergebnisse**:
- Dialog bleibt geoeffnet
- Fehlermeldung unter "Name": "Name ist erforderlich"
- Keine Regel wird erstellt

**Nachbedingungen**:
- Keine Datenaenderung

**Tags**: [req-018, regel, formvalidierung, pflichtfeld, name]

---

### TC-018-019: Regel mit gleichen on/off Hysterese-Schwellwerten schlaegt fehl

**Requirement**: REQ-018 § 3 — HysteresisConfig.validate_thresholds: "on_threshold und off_threshold muessen unterschiedlich sein"
**Priority**: High
**Category**: Formvalidierung
**Preconditions**:
- Nutzer ist eingeloggt

**Testschritte**:
1. Nutzer oeffnet den Dialog "Regel hinzufuegen"
2. Nutzer setzt Hysterese: Ein-Schwellwert: 1.5, Aus-Schwellwert: 1.5 (identisch)
3. Nutzer klickt "Speichern"

**Erwartete Ergebnisse**:
- Fehlermeldung: "Ein-Schwellwert und Aus-Schwellwert muessen unterschiedlich sein (sonst keine Hysterese)"
- Keine Regel wird erstellt

**Nachbedingungen**:
- Keine Datenaenderung

**Tags**: [req-018, regel, formvalidierung, hysterese, schwellwert]

---

### TC-018-020: Regel aktivieren und deaktivieren (Toggle)

**Requirement**: REQ-018 § 3 — POST /api/v1/actuators/{key}/rules/{rule_key}/toggle
**Priority**: High
**Category**: Zustandswechsel
**Preconditions**:
- Regel "VPD-Korrektur Befeuchter" ist aktiv (is_active=true)

**Testschritte**:
1. Nutzer navigiert zur Regelliste von "Befeuchter Zelt 1"
2. Nutzer klickt den Toggle-Schalter neben "VPD-Korrektur Befeuchter"

**Erwartete Ergebnisse**:
- Toggle zeigt "Inaktiv"
- Zeile wird ausgegraut oder mit "Deaktiviert"-Label versehen
- Snackbar: "Regel wurde deaktiviert"

**Nachbedingungen**:
- Regel "VPD-Korrektur Befeuchter" ist inaktiv

**Tags**: [req-018, regel, toggle, deaktivieren]

---

### TC-018-021: Compound-Regel (AND-Verknuepfung) erstellen und anzeigen

**Requirement**: REQ-018 § 3 — RuleCondition.compound_operator ('and'/'or'); DoD "Compound-Regeln: AND/OR-Verknuepfung"
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- Nutzer ist eingeloggt
- CO2-Doser-Aktor existiert
- Sensoren fuer CO2 und Licht-Status sind konfiguriert

**Testschritte**:
1. Nutzer oeffnet den Dialog "Regel hinzufuegen" fuer den CO2-Doser
2. Nutzer waehlt Regeltyp: "Compound"
3. Nutzer setzt Compound-Operator: "UND" (and)
4. Nutzer fuegt Unterbedingung 1 hinzu: Sensor "CO2 (ppm)", Operator "Kleiner als", Wert: 600
5. Nutzer fuegt Unterbedingung 2 hinzu: Sensor "Licht-Zustand", Operator "Groesser als", Wert: 0
6. Nutzer setzt Aktion: "Einschalten"
7. Nutzer klickt "Speichern"

**Erwartete Ergebnisse**:
- Regel erscheint in der Liste mit Typ "Compound (AND)"
- In der Detail-Ansicht der Regel sind beide Unterbedingungen aufgelistet: "CO2 < 600 UND Licht > 0"
- Snackbar: "Regel wurde erfolgreich erstellt"

**Nachbedingungen**:
- Compound-Regel ist aktiv

**Tags**: [req-018, regel, compound, and, co2, ppfd-kopplung]

---

### TC-018-022: Regel-Dry-Run (Test ohne Ausfuehren)

**Requirement**: REQ-018 § 3 — POST /api/v1/rules/{key}/test; DoD "Dry-Run: Regel gegen aktuelle Sensorwerte testen"
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- Regel "Nachtabsenkung Heizung" existiert (on_threshold: 18°C)
- Aktueller Temperatursensor meldet 16.5°C
- Heizung ist AUS

**Testschritte**:
1. Nutzer navigiert zur Detailseite der Regel "Nachtabsenkung Heizung"
2. Nutzer klickt "Regel testen (Dry-Run)"

**Erwartete Ergebnisse**:
- Ein Info-Panel oder Dialog erscheint mit dem Testergebnis:
  "Die Regel wuerde ausloesen: Befehl 'Einschalten' — Aktueller Sensorwert: 16.5°C, Schwellwert: 18°C — 'Temperatur 16.5°C < 18°C → Heizung wuerde eingeschaltet'"
- Es erscheint ein Hinweis: "Dies ist ein Testlauf — kein Befehl wurde an den Aktor gesendet"
- Kein Snackbar ueber eine ausgefuehrte Aktion

**Nachbedingungen**:
- Kein Aktor-Zustand wurde geaendert

**Tags**: [req-018, regel, dry-run, test, heizung, temperatur]

---

### TC-018-023: Alle aktiven Regeln fuer einen Sensor-Parameter anzeigen

**Requirement**: REQ-018 § 3 — GET /api/v1/rules?parameter=vpd&is_active=true
**Priority**: Medium
**Category**: Listenansicht
**Preconditions**:
- Mindestens 2 aktive Regeln fuer den Parameter "vpd" existieren
- Nutzer ist eingeloggt

**Testschritte**:
1. Nutzer navigiert zu einer globalen Regelverwaltungs-Seite (z.B. "Automatisierung" → "Alle Regeln")
2. Nutzer filtert nach Sensor-Parameter: "VPD"
3. Nutzer setzt Filter: nur aktive Regeln

**Erwartete Ergebnisse**:
- Nur Regeln mit Sensor-Parameter "VPD" werden angezeigt
- Inaktive VPD-Regeln sind ausgeblendet (oder als "Inaktiv" markiert, je nach Filter)
- Die Liste zeigt Regelname, zugeordneten Aktor, Hysterese-Werte

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-018, regel, filter, vpd, aktive-regeln, listenansicht]

---

## 4. Manueller Override

### TC-018-024: Manuellen Override fuer einen Aktor setzen

**Requirement**: REQ-018 § 3 — POST /api/v1/actuators/{key}/override; DoD "Manueller Override: Zeitlich begrenzt, hoechste Prioritaet"
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- Nutzer ist eingeloggt
- Aktor "Abluft Zelt 1" existiert mit aktivem Zeitplan (50%)

**Testschritte**:
1. Nutzer navigiert zur Detailseite von "Abluft Zelt 1"
2. Nutzer klickt "Manuellen Override setzen"
3. Im Dialog gibt der Nutzer ein:
   - Ueberschreibungs-Wert: 100 (%)
   - Ablaufzeit: in 2 Stunden (Datum/Uhrzeit-Picker)
   - Begruendung: "Hitze-Notfall"
4. Nutzer klickt "Override aktivieren"

**Erwartete Ergebnisse**:
- Dialog schliesst sich
- Auf der Aktor-Detailseite erscheint ein auffaelliges Banner / Badge: "Manueller Override aktiv — laeuft ab um [Uhrzeit]"
- Der angezeigte aktuelle Wert des Aktors aendert sich auf "100%"
- Der aktive Zeitplan (50%) erscheint als "durch Override uebersteuert" (ausgegraut oder mit Hinweistext)
- Snackbar: "Manueller Override wurde gesetzt — laeuft ab um [Uhrzeit]"

**Nachbedingungen**:
- ManualOverride ist aktiv und wird nach Ablaufzeit automatisch deaktiviert

**Tags**: [req-018, override, manuell, prioritaet, zeitlich-begrenzt]

---

### TC-018-025: Override ohne Ablaufzeit schlaegt fehl (Pflichtfeld)

**Requirement**: REQ-018 § 3 — ManualOverride.expires_at ist Pflicht: "Override darf nicht ewig gelten"
**Priority**: High
**Category**: Formvalidierung
**Preconditions**:
- Nutzer ist eingeloggt

**Testschritte**:
1. Nutzer oeffnet den Dialog "Manuellen Override setzen" fuer einen Aktor
2. Nutzer setzt Ueberschreibungs-Wert, laesst aber "Ablaufzeit" leer
3. Nutzer klickt "Override aktivieren"

**Erwartete Ergebnisse**:
- Dialog bleibt geoeffnet
- Fehlermeldung unter "Ablaufzeit": "Ablaufzeit ist erforderlich — ein Override darf nicht unbegrenzt gelten"
- Kein Override wird erstellt

**Nachbedingungen**:
- Keine Datenaenderung

**Tags**: [req-018, override, formvalidierung, ablaufzeit, pflichtfeld]

---

### TC-018-026: Override ohne override_value UND ohne override_state schlaegt fehl

**Requirement**: REQ-018 § 3 — ManualOverride.validate_override_value: "Entweder override_value oder override_state erforderlich"
**Priority**: High
**Category**: Formvalidierung
**Preconditions**:
- Nutzer ist eingeloggt

**Testschritte**:
1. Nutzer oeffnet den Dialog "Manuellen Override setzen"
2. Nutzer laesst sowohl "Ueberschreibungs-Wert" als auch "Ueberschreibungs-Zustand" leer
3. Nutzer setzt Ablaufzeit und klickt "Override aktivieren"

**Erwartete Ergebnisse**:
- Fehlermeldung: "Entweder ein Ueberschreibungs-Wert oder ein Ueberschreibungs-Zustand ist erforderlich"
- Kein Override wird erstellt

**Nachbedingungen**:
- Keine Datenaenderung

**Tags**: [req-018, override, formvalidierung, override-value, override-state]

---

### TC-018-027: Manuellen Override manuell beenden

**Requirement**: REQ-018 § 3 — DELETE /api/v1/actuators/{key}/override; ManualOverride.is_active=false
**Priority**: High
**Category**: Zustandswechsel
**Preconditions**:
- Aktor "Abluft Zelt 1" hat aktiven Override (Wert: 100%, laeuft erst in 2 Stunden ab)

**Testschritte**:
1. Nutzer navigiert zur Detailseite von "Abluft Zelt 1"
2. Nutzer sieht das Override-Banner
3. Nutzer klickt "Override beenden"
4. Bestaetigungs-Dialog erscheint: "Moechten Sie den aktiven Override wirklich beenden?"
5. Nutzer klickt "Bestaetigen"

**Erwartete Ergebnisse**:
- Das Override-Banner verschwindet
- Der Aktor-Wert zeigt wieder den durch den Zeitplan vorgegebenen Wert (50%)
- Snackbar: "Manueller Override wurde beendet"

**Nachbedingungen**:
- Kein aktiver Override, Zeitplan-Steuerung greift wieder

**Tags**: [req-018, override, beenden, ablauf, zeitplan]

---

## 5. Steuerungshistorie (ControlEvent-Log)

### TC-018-028: Event-Log eines Aktors anzeigen

**Requirement**: REQ-018 § 3 — GET /api/v1/actuators/{key}/events; DoD "Steuerungshistorie: Jede Aktion als immutables ControlEvent"
**Priority**: Critical
**Category**: Listenansicht
**Preconditions**:
- Aktor "Hauptlicht Zelt 1" hat mindestens 5 Events in den letzten 24h
- Nutzer ist eingeloggt

**Testschritte**:
1. Nutzer navigiert zur Detailseite von "Hauptlicht Zelt 1"
2. Nutzer klickt auf den Reiter "Steuerungshistorie"

**Erwartete Ergebnisse**:
- Die Event-Liste zeigt eintraege mit: Zeitstempel, Ereignisquelle (z.B. "Zeitplan", "Regel", "Manuell", "Sicherheit"), Befehl (z.B. "Einschalten", "Ausschalten", "Wert setzen"), Zustand vorher → nachher, Erfolgsstatus (Haken oder Fehlersymbol)
- Bei Regeln: der Name der ausloesenden Regel ist verlinkt oder in einem Tooltip sichtbar
- Bei Sensorwert-getriggerten Events: der Sensorwert zum Ausloesezeit-punkt ist sichtbar
- Die Liste ist absteigend nach Zeitstempel sortiert (neuste zuerst)

**Nachbedingungen**:
- Kein Status geaendert (nur Anzeige)

**Tags**: [req-018, event-log, steuerungshistorie, control-event, listenansicht]

---

### TC-018-029: Event-Log nach Zeitraum filtern

**Requirement**: REQ-018 § 3 — GET /api/v1/actuators/{key}/events mit Zeitraum-Filter
**Priority**: Medium
**Category**: Listenansicht
**Preconditions**:
- Aktor "Hauptlicht Zelt 1" hat Events ueber mehrere Tage

**Testschritte**:
1. Nutzer navigiert zum Event-Log von "Hauptlicht Zelt 1"
2. Nutzer setzt den Zeitraum-Filter: "Letzten 7 Tage"

**Erwartete Ergebnisse**:
- Nur Events aus den letzten 7 Tagen werden angezeigt
- Aeltere Events sind ausgeblendet
- Die Anzahl der angezeigten Events wird aktualisiert

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-018, event-log, filter, zeitraum]

---

### TC-018-030: Event-Log Ereignisquelle "Fallback-Task" ist sichtbar

**Requirement**: REQ-018 § 3 — EventSource.FALLBACK_TASK; DoD "Event-Quellen: fallback_task unterschieden"
**Priority**: High
**Category**: Zustandswechsel
**Preconditions**:
- HA war zeitweise nicht erreichbar
- Ein ControlEvent mit source="fallback_task" und success=false wurde erstellt

**Testschritte**:
1. Nutzer navigiert zum Event-Log von "Hauptlicht Zelt 1"

**Erwartete Ergebnisse**:
- Das Fallback-Event erscheint mit der Quelle "Fallback-Task" (oder "HA nicht erreichbar")
- Das Event zeigt Erfolgsstatus: Fehlgeschlagen (rotes Symbol)
- Eine Fehlermeldung wie "HA nicht erreichbar" ist sichtbar (aus dem error_message-Feld)

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-018, event-log, fallback-task, ha-ausfall, fehler]

---

### TC-018-031: Steuerungshistorie der gesamten Location anzeigen

**Requirement**: REQ-018 § 3 — GET /api/v1/locations/{key}/control-events
**Priority**: Medium
**Category**: Listenansicht
**Preconditions**:
- Location "Grow Zelt 1" hat mehrere Aktoren mit Events

**Testschritte**:
1. Nutzer navigiert zur Detailseite der Location "Grow Zelt 1"
2. Nutzer klickt auf den Reiter "Steuerungshistorie" (Location-Ebene)

**Erwartete Ergebnisse**:
- Events aller Aktoren der Location werden in einer zusammengefassten Liste angezeigt
- Jedes Event zeigt zusaetzlich den Aktor-Namen
- Filtermoeglichkeiten nach Aktor, Ereignisquelle und Zeitraum sind vorhanden

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-018, event-log, location, steuerungshistorie, alle-aktoren]

---

## 6. Phasen-Kontroll-Profile (PhaseControlProfile)

### TC-018-032: Phasen-Kontroll-Profil erstellen (Cannabis Vegetativ)

**Requirement**: REQ-018 § 3 — POST /api/v1/phase-control-profiles; DoD "Phasen-Profile"
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- Nutzer ist eingeloggt als Admin oder Grower
- Keine gleichnamigen Profile existieren

**Testschritte**:
1. Nutzer navigiert zu "Automatisierung" → "Phasen-Profile"
2. Nutzer klickt "Profil erstellen"
3. Nutzer gibt ein:
   - Name: "Indoor Cannabis Vegetativ"
   - Photoperiode: 18 h
   - Ziel-PPFD: 600 µmol/m²/s
   - Dimmer: 75%
   - Tagtemperatur: 26°C
   - Nachttemperatur: 20°C
   - Tagesfeuchtigkeit: 65%
   - Nachtfeuchtigkeit: 70%
   - Ziel-VPD: 1.0 kPa
   - CO2-Anreicherung: 800 ppm
   - CO2 nur bei Licht: Ja
   - CO2 min. PPFD: 200 µmol/m²/s
   - Ziel-DLI: 38 mol/m²/d
   - DIF-Ziel: 6°C
   - Bewaesserungsfrequenz: 3x taeglich
   - Bewaesserungsdauer: 180 s
   - Drain-Anteil: 20%
   - Uebergangs-Tage: 0
   - Als Vorlage: Ja
4. Nutzer klickt "Speichern"

**Erwartete Ergebnisse**:
- Profil "Indoor Cannabis Vegetativ" erscheint in der Profil-Liste
- Das Vorlage-Symbol ist sichtbar
- Snackbar: "Phasen-Profil wurde erfolgreich erstellt"

**Nachbedingungen**:
- Profil "Indoor Cannabis Vegetativ" ist als Vorlage verfuegbar

**Tags**: [req-018, phasenprofil, erstellen, cannabis, vegetativ, happy-path]

---

### TC-018-033: DIF-Validierung — zu grosse Tag-Nacht-Temperaturdifferenz

**Requirement**: REQ-018 § 3 — PhaseControlProfile.validate_temperature_differential: "Maximaler DIF: 12°C"
**Priority**: High
**Category**: Formvalidierung
**Preconditions**:
- Nutzer ist eingeloggt

**Testschritte**:
1. Nutzer oeffnet den Dialog "Profil erstellen"
2. Nutzer setzt Tagtemperatur: 35°C, Nachttemperatur: 20°C (DIF = 15°C)
3. Nutzer klickt "Speichern"

**Erwartete Ergebnisse**:
- Dialog bleibt geoeffnet
- Fehlermeldung: "Tag-/Nachttemperatur-Differenz zu gross (15.0°C). Maximaler DIF: 12°C (empfohlen: 2–8°C)"
- Kein Profil wird erstellt

**Nachbedingungen**:
- Keine Datenaenderung

**Tags**: [req-018, phasenprofil, formvalidierung, dif, temperaturdifferenz]

---

### TC-018-034: DIF-Validierung — zu grosser negativer DIF

**Requirement**: REQ-018 § 3 — PhaseControlProfile.validate_temperature_differential: "Maximaler negativer DIF: -4°C"
**Priority**: High
**Category**: Formvalidierung
**Preconditions**:
- Nutzer ist eingeloggt

**Testschritte**:
1. Nutzer oeffnet den Dialog "Profil erstellen"
2. Nutzer setzt Tagtemperatur: 16°C, Nachttemperatur: 22°C (DIF = -6°C)
3. Nutzer klickt "Speichern"

**Erwartete Ergebnisse**:
- Fehlermeldung: "Negativer DIF von -6.0°C ist physiologisch extrem. Maximaler negativer DIF: -4°C"
- Kein Profil wird erstellt

**Nachbedingungen**:
- Keine Datenaenderung

**Tags**: [req-018, phasenprofil, formvalidierung, negativer-dif, temperatur]

---

### TC-018-035: PhaseControlProfile.target_photoperiod_hours Bereichsvalidierung (0–24)

**Requirement**: REQ-018 § 3 — PhaseControlProfile.target_photoperiod_hours: Field(ge=0, le=24)
**Priority**: Medium
**Category**: Formvalidierung
**Preconditions**:
- Nutzer ist eingeloggt

**Testschritte**:
1. Nutzer oeffnet den Dialog "Profil erstellen"
2. Nutzer gibt Photoperiode: 25 (Stunden) ein
3. Nutzer klickt "Speichern"

**Erwartete Ergebnisse**:
- Fehlermeldung: "Photoperiode muss zwischen 0 und 24 Stunden liegen"
- Kein Profil wird erstellt

**Nachbedingungen**:
- Keine Datenaenderung

**Tags**: [req-018, phasenprofil, formvalidierung, photoperiode, bereichsvalidierung]

---

### TC-018-036: Phasen-Profil-Liste filtern nach Vorlagen

**Requirement**: REQ-018 § 3 — GET /api/v1/phase-control-profiles?is_template=true
**Priority**: Medium
**Category**: Listenansicht
**Preconditions**:
- Mindestens 2 Vorlagen-Profile und 1 standort-spezifisches Profil existieren

**Testschritte**:
1. Nutzer navigiert zu "Phasen-Profile"
2. Nutzer setzt den Filter "Nur Vorlagen anzeigen"

**Erwartete Ergebnisse**:
- Nur Profile mit Vorlage-Markierung werden angezeigt
- Standort-spezifische Profile sind ausgeblendet

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-018, phasenprofil, filter, vorlagen, is-template]

---

### TC-018-037: Profil auf Location anwenden

**Requirement**: REQ-018 § 3 — POST /api/v1/phase-control-profiles/{key}/apply; DoD "Phasen-Trigger"
**Priority**: High
**Category**: Zustandswechsel
**Preconditions**:
- Profil "Indoor Cannabis Vegetativ" existiert
- Location "Grow Zelt 1" hat Aktoren fuer Licht, Temperatur und CO2

**Testschritte**:
1. Nutzer navigiert zur Detailseite des Profils "Indoor Cannabis Vegetativ"
2. Nutzer klickt "Profil anwenden"
3. Nutzer waehlt Location "Grow Zelt 1" aus einem Dropdown
4. Nutzer klickt "Anwenden"

**Erwartete Ergebnisse**:
- Snackbar: "Phasen-Profil wurde erfolgreich auf 'Grow Zelt 1' angewendet"
- Auf der Location-Detailseite von "Grow Zelt 1" ist das aktive Profil "Indoor Cannabis Vegetativ" sichtbar

**Nachbedingungen**:
- Location "Grow Zelt 1" hat das Profil als aktiven Soll-Wert-Satz

**Tags**: [req-018, phasenprofil, anwenden, location, trigger]

---

### TC-018-038: Phasenwechsel loest automatischen Profil-Wechsel aus (UI-Anzeige)

**Requirement**: REQ-018 § 3 — PhaseTransitionHandler; DoD "Phasen-Trigger: Automatische Profil-Anwendung bei Phasenwechsel"
**Priority**: Critical
**Category**: Zustandswechsel
**Preconditions**:
- Pflanze "Testpflanze" ist in Phase "Vegetativ" mit Profil "Indoor Cannabis Vegetativ" (18h)
- Profil "Indoor Cannabis Blüte" (12h, transition_days=7) existiert und ist der Phase "Blüte" zugeordnet

**Testschritte**:
1. Nutzer loest den Phasenwechsel "Vegetativ → Blüte" fuer "Testpflanze" aus (gemaess REQ-003 UI)
2. Nutzer navigiert zur Steuerungshistorie von "Hauptlicht Zelt 1"

**Erwartete Ergebnisse**:
- Im Event-Log ist mindestens ein neues Event mit Quelle "Phasenwechsel" sichtbar
- Der angezeigte Soll-Wert des Licht-Zeitplans zeigt den neuen Zielwert (gradueller Uebergang, Tag 1: ~17.1h)
- Ein Info-Banner auf der Aktor-Detailseite zeigt: "Gradueller Uebergang laeuft — Ziel: 12.0h in 7 Tagen"

**Nachbedingungen**:
- Licht-Zeitplan passt sich taeglich an bis 12h erreicht ist

**Tags**: [req-018, phasenwechsel, profil, gradueller-uebergang, licht, photoperiode]

---

### TC-018-039: Photoperiod-Schutz — Dunkelphase bei Kurztagspflanze wird nicht unterbrochen

**Requirement**: REQ-018 § 3 — PhaseControlProfile.photoperiod_is_critical; DoD "Photoperiod-Schutz: Dunkelphase nicht durch Licht-Aktoren unterbrechen"
**Priority**: Critical
**Category**: Zustandswechsel
**Preconditions**:
- Profil "Indoor Cannabis Blüte" ist aktiv (photoperiod_is_critical=true)
- Es ist Dunkelphase (Licht aus seit 2h)
- Ein Sicherheits-Override oder eine Regel versucht das Licht einzuschalten

**Testschritte**:
1. Nutzer versucht, per manuellem Override das Licht "Hauptlicht Zelt 1" waehrend der Dunkelphase einzuschalten
2. Nutzer setzt Override: Zustand "Ein", Ablaufzeit: 30 Minuten

**Erwartete Ergebnisse**:
- Ein Warn-Dialog erscheint: "Achtung: Das aktive Profil 'Indoor Cannabis Blüte' hat eine kritische Dunkelphase (Kurztagspflanze). Das Einschalten des Lichts kann die Bluehinduktion stoeren."
- Der Nutzer muss explizit bestaetigen ("Trotzdem fortfahren — ich verstehe das Risiko")
- Oder der Override wird abgelehnt (je nach Implementierungsentscheidung der sichersten Option)

**Nachbedingungen**:
- Licht bleibt aus ODER der Nutzer hat aktiv den Risiko-Hinweis bestaetigt

**Tags**: [req-018, photoperiod-schutz, kurztagspflanze, dunkelphase, cannabis, kritisch]

---

## 7. Energieverbrauch

### TC-018-040: Energieverbrauch-Ansicht fuer eine Location

**Requirement**: REQ-018 § 3 — GET /api/v1/locations/{key}/energy; DoD "Energieverbrauch: Geschaetzte kWh pro Aktor/Location"
**Priority**: Medium
**Category**: Detailansicht
**Preconditions**:
- Location "Grow Zelt 1" hat Aktoren mit Nennleistung (power_watts): Licht 480W, Abluft 95W, Befeuchter 30W
- Entsprechende ControlEvents sind vorhanden

**Testschritte**:
1. Nutzer navigiert zur Detailseite der Location "Grow Zelt 1"
2. Nutzer klickt auf den Reiter "Energie / Verbrauch"
3. Nutzer waehlt Zeitraum: "Aktueller Monat"

**Erwartete Ergebnisse**:
- Eine Tabelle oder Karten-Ansicht zeigt pro Aktor: Name, Nennleistung, Betriebsstunden (geschaetzt), Verbrauch in kWh
- Licht: ca. 259.2 kWh (480W × 18h × 30d ÷ 1000)
- Abluft: ca. 41.0 kWh (95W × 0.6 × 24h × 30d ÷ 1000)
- Befeuchter: je nach Laufzeit
- Gesamtverbrauch ist summiert sichtbar
- Ein Hinweis zeigt, dass dies eine Schaetzung basierend auf ControlEvents ist

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-018, energie, verbrauch, kwh, location]

---

## 8. Home Assistant Integration

### TC-018-041: HA-Verbindungsstatus anzeigen

**Requirement**: REQ-018 § 3 — GET /api/v1/integrations/home-assistant/status; DoD "HA-Integration: Service-Calls"
**Priority**: High
**Category**: Detailansicht
**Preconditions**:
- Nutzer ist eingeloggt als Admin
- HA-Integration ist konfiguriert (HA_URL und HA_TOKEN sind gesetzt)

**Testschritte**:
1. Nutzer navigiert zu "Einstellungen" → "Integrationen" → "Home Assistant"

**Erwartete Ergebnisse**:
- Eine Status-Karte zeigt: "Home Assistant verbunden"
- Die HA-URL ist angezeigt (ggf. teilweise maskiert)
- Letztes erfolgreiches Polling-Datum/-Uhrzeit ist sichtbar
- Die Anzahl gemappter Entities ist angegeben

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-018, home-assistant, verbindungsstatus, integration, admin]

---

### TC-018-042: HA-Verbindungstest ausfuehren

**Requirement**: REQ-018 § 3 — POST /api/v1/integrations/home-assistant/test
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- HA-Integration ist konfiguriert
- Nutzer ist Admin

**Testschritte**:
1. Nutzer navigiert zu "Einstellungen" → "Integrationen" → "Home Assistant"
2. Nutzer klickt "Verbindung testen"

**Erwartete Ergebnisse**:
- Ein Lade-Indikator erscheint kurz
- Anschliessend: Snackbar "Verbindung zu Home Assistant erfolgreich — HA Version X.X.X"
- Die Status-Karte aktualisiert die Zeitanzeige "Zuletzt geprueft: jetzt"

**Nachbedingungen**:
- Kein Status geaendert (nur Verbindungsstatus-Aktualisierung)

**Tags**: [req-018, home-assistant, verbindungstest, integration]

---

### TC-018-043: HA nicht erreichbar — Fehlerstatus in Verbindungsanzeige

**Requirement**: REQ-018 § 3 — HA Graceful Degradation; DoD "HA Graceful Degradation: Bei HA-Ausfall → Fallback-Task"
**Priority**: High
**Category**: Fehlermeldung
**Preconditions**:
- HA-Integration ist konfiguriert, aber HA ist nicht erreichbar (z.B. HA-Server down)

**Testschritte**:
1. Nutzer navigiert zu "Einstellungen" → "Integrationen" → "Home Assistant"

**Erwartete Ergebnisse**:
- Status-Karte zeigt "Home Assistant nicht erreichbar" (rotes/oranges Warnsymbol)
- Zeitpunkt des letzten erfolgreichen Kontakts ist sichtbar
- Ein Hinweis: "Bei Ausfall werden automatisch manuelle Aufgaben fuer Aktions-Ereignisse erstellt (Fallback-Modus)"

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-018, home-assistant, ausfall, graceful-degradation, fallback, fehlermeldung]

---

### TC-018-044: HA-Entities fuer Entity-Mapping anzeigen

**Requirement**: REQ-018 § 3 — GET /api/v1/integrations/home-assistant/entities
**Priority**: Medium
**Category**: Listenansicht
**Preconditions**:
- HA-Integration ist aktiv und erreichbar
- HA hat mindestens 3 Entities konfiguriert (z.B. light.growzelt_1, fan.abluft_zelt_1)

**Testschritte**:
1. Nutzer oeffnet den Dialog "Aktor hinzufuegen" mit Protokoll "Home Assistant"
2. Nutzer klickt auf das Feld "HA Entity-ID" (das einen Autocomplete-Picker oeffnet)

**Erwartete Ergebnisse**:
- Eine Liste verfuegbarer HA-Entities wird angezeigt (aus der HA-API abgerufen)
- Entities sind nach Domain gruppiert (light, fan, switch, climate, humidifier)
- Der Nutzer kann per Texteingabe filtern

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-018, home-assistant, entity-mapping, autocomplete, entities]

---

## 9. Manuelle Aktoren und Fallback-Tasks

### TC-018-045: Manueller Aktor — kein Protokoll-Befehl, stattdessen Task

**Requirement**: REQ-018 § 3 — Manuelles Protokoll; DoD "Manuelle Aktoren: System erzeugt Tasks statt Befehle"
**Priority**: High
**Category**: Zustandswechsel
**Preconditions**:
- Aktor "Umluft-Ventilator Garten-Setup" existiert mit Protokoll "Manuell"
- Eine Regel ist konfiguriert: Temperatur > 30°C → Ventilator einschalten

**Testschritte**:
1. Nutzer navigiert zum Aufgaben-Dashboard (REQ-006)
2. Nutzer navigiert zurueck zum Aktor "Umluft-Ventilator Garten-Setup"

**Erwartete Ergebnisse**:
- Auf der Aktor-Detailseite erscheint KEIN "Befehl senden"-Button (da Protokoll=Manuell)
- Im Aufgaben-Dashboard erscheint eine neue Aufgabe: "Umluft-Ventilator Garten-Setup einschalten — Temperatur > 30°C (bitte Ventilator manuell bedienen)"
- In der Steuerungshistorie des Aktors erscheint ein Event mit Quelle "Fallback-Task"

**Nachbedingungen**:
- Eine manuelle Aufgabe wurde erstellt; kein automatischer Steuerungsbefehl gesendet

**Tags**: [req-018, manueller-aktor, fallback-task, aufgabe, protokoll-manuell]

---

### TC-018-046: Direktbefehl an HA-Aktor senden (Sofortsteuerung)

**Requirement**: REQ-018 § 3 — POST /api/v1/actuators/{key}/command
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- Aktor "Hauptlicht Zelt 1" (Protokoll: Home Assistant) ist verbunden und erreichbar
- Aktueller Zustand: "AN"

**Testschritte**:
1. Nutzer navigiert zur Detailseite von "Hauptlicht Zelt 1"
2. Nutzer klickt "Ausschalten" (Direktbefehl)
3. Bestaetigungs-Dialog erscheint (falls implementiert) oder direktes Senden

**Erwartete Ergebnisse**:
- Der angezeigte Aktor-Zustand wechselt auf "AUS"
- Snackbar: "Befehl 'Ausschalten' wurde an 'Hauptlicht Zelt 1' gesendet"
- In der Steuerungshistorie erscheint ein neues Event mit Quelle "Manuell" und Befehl "Ausschalten"

**Nachbedingungen**:
- Aktor "Hauptlicht Zelt 1" ist AUS

**Tags**: [req-018, direktbefehl, turn-off, manuell, home-assistant]

---

## 10. Gesamtstatus einer Location

### TC-018-047: Gesamtstatus aller Aktoren einer Location

**Requirement**: REQ-018 § 3 — GET /api/v1/locations/{key}/control-status
**Priority**: High
**Category**: Detailansicht
**Preconditions**:
- Location "Grow Zelt 1" hat 4 aktive Aktoren, einer davon hat einen aktiven Override

**Testschritte**:
1. Nutzer navigiert zur Detailseite von "Grow Zelt 1"
2. Nutzer klickt auf den Reiter "Steuerungsstatus" oder "Aktoren-Uebersicht"

**Erwartete Ergebnisse**:
- Eine Uebersichtskarte (Dashboard-Widget) zeigt alle Aktoren der Location
- Pro Aktor: aktueller Zustand (AN/AUS/Wert), aktive Quelle (Zeitplan/Regel/Override), Online-Status
- Der Aktor mit aktivem Override ist visuell hervorgehoben (z.B. oranges Icon)
- Sicherheitsregeln die gerade aktiv sind, sind besonders markiert (z.B. rotes Schild-Icon)

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-018, gesamtstatus, location, aktor-uebersicht, dashboard]

---

## 11. Fail-Safe-States

### TC-018-048: Fail-Safe-Zustand bei Aktor-Erstellung sichtbar und pflegbar

**Requirement**: REQ-018 § 3 — Actuator.fail_safe_state; DoD "Fail-Safe-States: Default-Zustand pro Aktor bei Kommunikationsverlust"
**Priority**: High
**Category**: Detailansicht
**Preconditions**:
- Nutzer ist eingeloggt

**Testschritte**:
1. Nutzer oeffnet den Dialog "Aktor hinzufuegen" fuer Typ "Abluftventilator"
2. Nutzer betrachtet das Feld "Fail-Safe-Zustand"

**Erwartete Ergebnisse**:
- Das Feld "Fail-Safe-Zustand" ist vorhanden
- Fuer Abluftventilator gibt es einen Hinweis-Text oder Platzhalter: "Empfehlung: 'Ein' (verhindert Uebertemperatur bei Ausfall)"
- Der Nutzer kann "Ein", "Aus" oder "Letzter Zustand" auswaehlen
- Ein Tooltip erklaert die Bedeutung des Fail-Safe-Zustands

**Nachbedingungen**:
- Keine Datenaenderung

**Tags**: [req-018, fail-safe, aktor, validierung, offline]

---

### TC-018-049: Offline-Aktor zeigt Fail-Safe-Zustand in der Uebersicht

**Requirement**: REQ-018 § 1 — Fail-Safe-States Tabelle; DoD "Fail-Safe-States: Default-Zustand bei Kommunikationsverlust"
**Priority**: Medium
**Category**: Listenansicht
**Preconditions**:
- Aktor "Befeuchter Zelt 1" hat fail_safe_state="off" und ist offline (is_online=false)

**Testschritte**:
1. Nutzer navigiert zur Aktoren-Liste von "Grow Zelt 1"

**Erwartete Ergebnisse**:
- Aktor "Befeuchter Zelt 1" zeigt das Offline-Symbol
- Als Zustand wird der Fail-Safe-Zustand angezeigt: "Aus (Fail-Safe)"
- Ein Warn-Indikator (z.B. gelbes Dreieck) signalisiert den Offline-Status

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-018, fail-safe, offline, is-online, aktor-liste]

---

## 12. Notabschaltung (Emergency Stop)

### TC-018-050: Notabschaltung "Wasseraustritt" ausloesen

**Requirement**: REQ-018 § 1 — "POST /api/v1/emergency-stop: Wasseraustritt → Alle Pumpen/Ventile OFF"; DoD "Notabschaltung: Emergency-Stop"
**Priority**: Critical
**Category**: Zustandswechsel
**Preconditions**:
- Location "Grow Zelt 1" hat aktive Bewässerungsventile und Pumpen
- Nutzer ist eingeloggt (mindestens Grower-Rolle)

**Testschritte**:
1. Nutzer navigiert zum Dashboard oder zur Location-Detailseite
2. Nutzer findet den "Notabschaltung"-Button (auffaelliges rotes Symbol, ggf. in AppBar oder Location-Header)
3. Nutzer klickt "Notabschaltung"
4. Ein Dialog erscheint mit Szenarien-Auswahl
5. Nutzer waehlt "Wasseraustritt (Alle Pumpen und Ventile aus)"
6. Nutzer klickt "NOTABSCHALTUNG AUSLOESEN"

**Erwartete Ergebnisse**:
- Der Dialog fragt nach expliziter Bestaetigung ("Ich bestaetigen, dass dies ein Notfall ist")
- Nach Bestaetigung: Snackbar "Notabschaltung ausgeloest: Wasseraustritt — alle Pumpen und Ventile werden deaktiviert"
- Alle Bewässerungsventil- und Pumpen-Aktoren der Location zeigen Zustand "AUS"
- In der Steuerungshistorie erscheinen Events mit Quelle "Sicherheit" fuer alle betroffenen Aktoren
- Ein Warn-Banner auf der Location-Detailseite ist sichtbar: "Notabschaltung aktiv — Bitte Ursache pruefen"

**Nachbedingungen**:
- Alle Pumpen und Ventile der Location sind deaktiviert

**Tags**: [req-018, notabschaltung, emergency-stop, wasseraustritt, pumpe, ventil]

---

### TC-018-051: Notabschaltung "CO2-Leck" — CO2-Doser aus, Abluft 100%

**Requirement**: REQ-018 § 1 — Emergency-Stop Szenario "CO2-Leck"
**Priority**: Critical
**Category**: Zustandswechsel
**Preconditions**:
- CO2-Doser-Aktor und Abluftventilatoren sind aktiv

**Testschritte**:
1. Nutzer loest Notabschaltung aus (wie TC-018-050)
2. Nutzer waehlt Szenario: "CO2-Leck (CO2-Doser aus, Abluft 100%)"
3. Nutzer bestaetigt

**Erwartete Ergebnisse**:
- CO2-Doser-Aktoren zeigen Zustand "AUS"
- Abluftventilatoren zeigen Zustand "AN – 100%"
- Snackbar: "Notabschaltung CO2-Leck ausgeloest — CO2-Doser deaktiviert, Abluft auf 100%"

**Nachbedingungen**:
- CO2-Doser sind aus, Abluft laeuft auf 100%

**Tags**: [req-018, notabschaltung, co2-leck, emergency-stop, abluft]

---

### TC-018-052: Notabschaltung "Brand-Alarm" — alle Stromverbraucher aus

**Requirement**: REQ-018 § 1 — Emergency-Stop Szenario "Brand-Alarm"
**Priority**: Critical
**Category**: Zustandswechsel
**Preconditions**:
- Mehrere Aktoren sind aktiv (Licht, Abluft, Heizung)

**Testschritte**:
1. Nutzer loest Notabschaltung aus
2. Nutzer waehlt Szenario: "Brand-Alarm (Alle Stromverbraucher aus)"
3. Nutzer bestaetigt mit expliziter Bestaetigung

**Erwartete Ergebnisse**:
- Alle Aktoren zeigen Zustand "AUS"
- Snackbar: "Notabschaltung Brand-Alarm ausgeloest — alle Stromverbraucher wurden deaktiviert"
- Ein persistentes Warn-Banner ist auf der Location sichtbar, bis es manuell quittiert wird

**Nachbedingungen**:
- Alle Aktoren sind deaktiviert

**Tags**: [req-018, notabschaltung, brand-alarm, emergency-stop, alle-aktoren]

---

## 13. Konfliktgruppen

### TC-018-053: Konfliktgruppe "co2_ventilation" wird in UI angezeigt

**Requirement**: REQ-018 § 1 — Konfliktgruppen: "CO2-Doser und Abluft in conflict_group 'co2_ventilation'"
**Priority**: Medium
**Category**: Detailansicht
**Preconditions**:
- Aktor "CO2-Doser Zelt 1" hat conflict_group="co2_ventilation"
- Aktor "Abluft Zelt 1" hat conflict_group="co2_ventilation"

**Testschritte**:
1. Nutzer navigiert zur Detailseite von "CO2-Doser Zelt 1"

**Erwartete Ergebnisse**:
- Im Abschnitt "Konfiguration" ist das Feld "Konfliktgruppe: co2_ventilation" sichtbar
- Ein Hinweistext erklaert die Auswirkung: "Aktoren in derselben Konfliktgruppe werden koordiniert gesteuert (keine gleichzeitige entgegengesetzte Betaetigung)"
- Ein Link oder Chip zeigt die anderen Aktoren derselben Gruppe: "Abluft Zelt 1"

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-018, konfliktgruppe, co2-ventilation, aktor-detail]

---

## 14. DLI-Lichtsteuerung

### TC-018-054: DLI-Ziel im Phasen-Profil konfigurieren und Hinweis bei Kurztagspflanze

**Requirement**: REQ-018 § 1 — DLI-basierte Lichtsteuerung; DoD "DLI-Akkumulation: PPFD-Tagesintegral berechnen"
**Priority**: Medium
**Category**: Detailansicht
**Preconditions**:
- Phasen-Profil "Indoor Cannabis Blüte" mit photoperiod_is_critical=true und target_dli_mol=40 existiert

**Testschritte**:
1. Nutzer oeffnet die Detailseite des Profils "Indoor Cannabis Blüte"

**Erwartete Ergebnisse**:
- Das Feld "Tageslichtsumme (DLI)" zeigt "40 mol/m²/d"
- Da photoperiod_is_critical=true, zeigt die UI einen Hinweis-Text: "Kurztagspflanze: Zur DLI-Erreichung wird ausschliesslich die Lichtintensitaet (Dimmer) angepasst — die Photoperiode wird NICHT verlaengert"
- Das Feld "Photoperiod ist kritisch" zeigt einen roten/orangenen Indikator

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-018, dli, tageslichtsumme, kurztagspflanze, photoperiod-schutz]

---

## 15. CO2-PPFD-Kopplung

### TC-018-055: CO2-PPFD-Schwellwert im Profil konfiguriert und in UI erklaert

**Requirement**: REQ-018 § 1 — CO2-PPFD-Kopplung; DoD "CO2-PPFD-Kopplung: CO2-Dosierung nur bei ausreichendem PPFD"
**Priority**: Medium
**Category**: Detailansicht
**Preconditions**:
- Phasen-Profil mit co2_min_ppfd_threshold=200 und co2_enrichment_ppm=800 existiert

**Testschritte**:
1. Nutzer oeffnet ein Phasen-Profil mit gesetztem CO2-Schwellwert

**Erwartete Ergebnisse**:
- Das Feld "Minimales PPFD fuer CO2-Dosierung" zeigt "200 µmol/m²/s"
- Ein erklaerenden Tooltip oder Hinweistext: "CO2-Anreicherung wird erst bei PPFD ≥ 200 µmol/m²/s aktiviert (Liebigs Minimumgesetz)"
- Die Kopplung Licht → CO2 wird visualisiert

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-018, co2-ppfd, kopplung, liebig, phasenprofil]

---

## 16. DROP-Technik (DIF)

### TC-018-056: DROP-Technik im Phasen-Profil konfigurieren

**Requirement**: REQ-018 § 3 — PhaseControlProfile.pre_dawn_drop_c / pre_dawn_drop_hours; DoD "DIF/DROP: Tag-/Nacht-Umschaltung"
**Priority**: Medium
**Category**: Happy Path
**Preconditions**:
- Nutzer ist eingeloggt

**Testschritte**:
1. Nutzer oeffnet den Dialog "Profil bearbeiten" fuer ein bestehendes Profil
2. Nutzer aktiviert den Bereich "DROP-Technik"
3. Nutzer gibt ein: Temperaturabsenkung: 5°C, Dauer: 2 Stunden
4. Nutzer klickt "Speichern"

**Erwartete Ergebnisse**:
- Profil wird gespeichert mit pre_dawn_drop_c=5, pre_dawn_drop_hours=2
- In der Profil-Detailansicht erscheint: "DROP-Technik: 5°C Absenkung, 2h vor Licht-Ein"
- Ein Tooltip erklaert: "Hemmt Gibberellin-Synthese → kompakter Wuchs ohne chemische Wuchshemmer"

**Nachbedingungen**:
- Profil hat DROP-Konfiguration gespeichert

**Tags**: [req-018, drop-technik, dif, gibberellin, temperatur, phasenprofil]

---

## 17. Berechtigungen und Zugriffsschutz

### TC-018-057: Nicht-Admin kann Aktoren nicht loeschen

**Requirement**: REQ-018 § 4 — Auth-Tabelle: "Aktoren Loeschen: Admin"
**Priority**: High
**Category**: Fehlermeldung
**Preconditions**:
- Nutzer ist eingeloggt mit Rolle "Grower" (nicht Admin)
- Aktor "Befeuchter Zelt 1" existiert

**Testschritte**:
1. Nutzer navigiert zur Detailseite von "Befeuchter Zelt 1"

**Erwartete Ergebnisse**:
- Der "Loeschen"-Button ist entweder nicht sichtbar oder als deaktiviert (disabled) dargestellt
- Falls der Button sichtbar und der Nutzer klickt, erscheint eine Fehlermeldung: "Sie haben keine Berechtigung, Aktoren zu loeschen"

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-018, autorisierung, rbac, loeschen, grower, admin]

---

### TC-018-058: Nicht-Admin kann HA-Integration nicht konfigurieren

**Requirement**: REQ-018 § 4 — Auth-Tabelle: "HA-Integration: Lesen/Schreiben/Loeschen: Admin"
**Priority**: High
**Category**: Fehlermeldung
**Preconditions**:
- Nutzer ist eingeloggt mit Rolle "Grower"

**Testschritte**:
1. Nutzer navigiert zu "Einstellungen" → "Integrationen" → "Home Assistant"

**Erwartete Ergebnisse**:
- Konfigurationsfelder (HA-URL, HA-Token) sind schreibgeschuetzt oder der gesamte Bereich ist ausgeblendet
- Kein "Speichern"-Button fuer die HA-Konfiguration ist sichtbar
- Ggf. erscheint ein Hinweis: "Nur Administratoren koennen die HA-Integration konfigurieren"

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-018, autorisierung, rbac, home-assistant, admin, grower]

---

## 18. Grenzwert-Testfaelle (Boundary Values)

### TC-018-059: PhaseControlProfile — Grenzwert target_photoperiod_hours = 0 (Nacht-Modus)

**Requirement**: REQ-018 § 3 — PhaseControlProfile.target_photoperiod_hours: Field(ge=0, le=24)
**Priority**: Medium
**Category**: Happy Path
**Preconditions**:
- Nutzer ist eingeloggt

**Testschritte**:
1. Nutzer erstellt ein neues Profil mit Photoperiode: 0 (Stunden)
2. Nutzer klickt "Speichern"

**Erwartete Ergebnisse**:
- Profil wird ohne Fehlermeldung gespeichert (0 ist erlaubt = komplette Dunkelphase)
- In der Profil-Liste ist das Profil mit "Photoperiode: 0h" sichtbar

**Nachbedingungen**:
- Profil mit Photoperiode 0h gespeichert

**Tags**: [req-018, phasenprofil, grenzwert, photoperiode, null]

---

### TC-018-060: PhaseControlProfile — Grenzwert target_light_ppfd = 0

**Requirement**: REQ-018 § 3 — PhaseControlProfile.target_light_ppfd: Field(ge=0, le=2000)
**Priority**: Low
**Category**: Happy Path
**Preconditions**:
- Nutzer ist eingeloggt

**Testschritte**:
1. Nutzer erstellt ein neues Profil mit PPFD: 0
2. Nutzer klickt "Speichern"

**Erwartete Ergebnisse**:
- Profil wird gespeichert (0 ist erlaubt — kein Licht)

**Tags**: [req-018, phasenprofil, grenzwert, ppfd, null]

---

### TC-018-061: PhaseControlProfile — Grenzwert target_light_ppfd = 2001 schlaegt fehl

**Requirement**: REQ-018 § 3 — PhaseControlProfile.target_light_ppfd: Field(le=2000)
**Priority**: Medium
**Category**: Formvalidierung
**Preconditions**:
- Nutzer ist eingeloggt

**Testschritte**:
1. Nutzer erstellt ein Profil mit PPFD: 2001
2. Nutzer klickt "Speichern"

**Erwartete Ergebnisse**:
- Fehlermeldung: "PPFD-Wert darf nicht groesser als 2000 µmol/m²/s sein"
- Kein Profil erstellt

**Tags**: [req-018, phasenprofil, grenzwert, ppfd, max-wert]

---

### TC-018-062: HysteresisConfig — min_on_duration_seconds Grenzwert 3600

**Requirement**: REQ-018 § 3 — HysteresisConfig.min_on_duration_seconds: Field(ge=0, le=3600)
**Priority**: Low
**Category**: Formvalidierung
**Preconditions**:
- Nutzer ist eingeloggt

**Testschritte**:
1. Nutzer erstellt eine Regel mit Mindestlaufzeit: 3601 Sekunden
2. Nutzer klickt "Speichern"

**Erwartete Ergebnisse**:
- Fehlermeldung: "Mindestlaufzeit darf nicht groesser als 3600 Sekunden (1 Stunde) sein"
- Keine Regel erstellt

**Tags**: [req-018, regel, hysterese, grenzwert, mindestlaufzeit]

---

### TC-018-063: PhaseControlProfile — co2_enrichment_ppm Grenzwert 2000

**Requirement**: REQ-018 § 3 — PhaseControlProfile.co2_enrichment_ppm: Field(le=2000)
**Priority**: Medium
**Category**: Formvalidierung
**Preconditions**:
- Nutzer ist eingeloggt

**Testschritte**:
1. Nutzer erstellt ein Profil mit CO2-Anreicherung: 2001 ppm
2. Nutzer klickt "Speichern"

**Erwartete Ergebnisse**:
- Fehlermeldung: "CO2-Anreicherung darf nicht groesser als 2000 ppm sein"
- Kein Profil erstellt

**Tags**: [req-018, phasenprofil, formvalidierung, co2, grenzwert]

---

## 19. Edge Cases und Sonderszenarien

### TC-018-064: Aktor online-Status "Offline" — Warnanzeige und kein Befehl moeglich

**Requirement**: REQ-018 § 3 — Actuator.is_online; DoD "check_actuator_health: Alert bei Offline"
**Priority**: High
**Category**: Fehlermeldung
**Preconditions**:
- Aktor "Hauptlicht Zelt 1" ist offline (is_online=false)

**Testschritte**:
1. Nutzer navigiert zur Detailseite von "Hauptlicht Zelt 1"
2. Nutzer versucht, den Befehl "Einschalten" zu senden

**Erwartete Ergebnisse**:
- Ein oranges/rotes Warn-Banner oben auf der Seite: "Aktor nicht erreichbar — letzter Kontakt: [Zeitpunkt]"
- Der "Befehl senden"-Button ist deaktiviert (disabled) mit einem Tooltip: "Aktor ist offline"
- Das System zeigt den Fail-Safe-Zustand an

**Nachbedingungen**:
- Kein Befehl gesendet

**Tags**: [req-018, aktor, offline, is-online, warn-anzeige, disabled-button]

---

### TC-018-065: Aktiver Override laeuft ab — Zeitplan greift automatisch wieder

**Requirement**: REQ-018 § 3 — expire_manual_overrides Celery-Task; DoD "Manueller Override: automatischer Ablauf"
**Priority**: High
**Category**: Zustandswechsel
**Preconditions**:
- Aktor "Abluft Zelt 1" hat einen Override (100%), der in 1 Minute ablaeuft
- Ein Zeitplan (50%) ist aktiv

**Testschritte**:
1. Nutzer navigiert zur Detailseite von "Abluft Zelt 1"
2. Nutzer wartet, bis die Ablaufzeit des Overrides abgelaufen ist (oder der Nutzer refreshed die Seite nach Ablauf)

**Erwartete Ergebnisse**:
- Das Override-Banner ist nicht mehr sichtbar
- Der angezeigte Aktor-Zustand zeigt nun den Zeitplan-Wert (50%)
- In der Steuerungshistorie erscheint ein Event mit Quelle "Zeitplan" nach Ablauf des Overrides
- Ggf. erscheint eine Info-Meldung: "Manueller Override abgelaufen — Zeitplan-Steuerung ist aktiv"

**Nachbedingungen**:
- Override ist inaktiv, Zeitplan ist aktiv

**Tags**: [req-018, override, ablauf, zeitplan, automatisch, celery]

---

### TC-018-066: Zeitplan mit Mitternachts-Uebergang (18/6: Ein 06:00, Aus 00:00)

**Requirement**: REQ-018 § 3 — ScheduleEntry: Mitternachts-Uebergang (time_on <= time_off Logik)
**Priority**: Medium
**Category**: Happy Path
**Preconditions**:
- Nutzer ist eingeloggt

**Testschritte**:
1. Nutzer erstellt einen Zeitplan mit Eintrag: Ein um 06:00, Aus um 00:00 (Mitternacht)
2. Nutzer klickt "Speichern"

**Erwartete Ergebnisse**:
- Zeitplan wird ohne Fehler gespeichert
- In der Detailansicht des Zeitplans wird die Laufzeit korrekt angezeigt: "18 Stunden (06:00–00:00)"

**Nachbedingungen**:
- Zeitplan mit Mitternachts-Uebergang ist gespeichert

**Tags**: [req-018, zeitplan, mitternacht, 18-6, schedule-entry]

---

### TC-018-067: Prioritaetssystem sichtbar in Steuerungshistorie

**Requirement**: REQ-018 § 1 — Prioritaetssystem: Override > Safety > Rule > Schedule; DoD "Prioritaetssystem"
**Priority**: High
**Category**: Listenansicht
**Preconditions**:
- Sicherheitsregel "Uebertemperatur Abluft" wurde ausgeloest und hat einen laufenden Zeitplan uebersteuert

**Testschritte**:
1. Nutzer navigiert zum Event-Log von "Abluft Zelt 1"
2. Nutzer betrachtet die Events aus dem Zeitraum der Sicherheitsregel-Auslosung

**Erwartete Ergebnisse**:
- Das Event der Sicherheitsregel-Auslosung ist mit Quelle "Sicherheit" markiert und einem Schild-Symbol versehen
- Das vorherige Zeitplan-Event ist als "uebersteuert von Sicherheitsregel" oder nachrangig gekennzeichnet
- Der Sensorwert zum Ausloesezeitpunkt (z.B. "Temp: 31°C") ist sichtbar

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-018, prioritaet, sicherheitsregel, uebersteuern, zeitplan, event-log]

---

### TC-018-068: Leerer Zustand — keine Aktoren fuer eine Location

**Requirement**: REQ-018 § 3 — GET /api/v1/locations/{key}/actuators — Empty State
**Priority**: Low
**Category**: Listenansicht
**Preconditions**:
- Location "Neuer Standort" existiert, hat aber noch keine Aktoren

**Testschritte**:
1. Nutzer navigiert zur Aktoren-Liste von "Neuer Standort"

**Erwartete Ergebnisse**:
- Die Liste zeigt einen leeren Zustand (Empty State) mit einer erklaerenden Meldung: "Noch keine Aktoren konfiguriert"
- Eine Schaltflaeche "Ersten Aktor hinzufuegen" ist sichtbar

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-018, empty-state, aktor-liste, neuer-standort]

---

### TC-018-069: Konfliktgruppe "heat_cool" — Heizung und Kuehlsystem

**Requirement**: REQ-018 § 1 — Konfliktgruppen: "heat_cool: Heizung und Kuehlung nicht gleichzeitig aktiv"
**Priority**: Medium
**Category**: Detailansicht
**Preconditions**:
- Aktor "Heizstrahler Zelt 1" und Aktor "Kuehlgeraet Zelt 1" haben conflict_group="heat_cool"

**Testschritte**:
1. Nutzer navigiert zur Detailseite von "Heizstrahler Zelt 1"
2. Nutzer betrachtet den Abschnitt "Konfliktgruppe"

**Erwartete Ergebnisse**:
- Die Konfliktgruppe "heat_cool" ist angezeigt
- Der andere Aktor derselben Gruppe ("Kuehlgeraet Zelt 1") ist verlinkt oder aufgelistet
- Hinweistext: "Aktoren dieser Gruppe werden koordiniert gesteuert — Heizung und Kuehlung koennen nicht gleichzeitig aktiv sein"

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-018, konfliktgruppe, heat-cool, heizung, kuehlung]

---

### TC-018-070: Aktor-Detailseite — Aktueller Zustand mit Quelle

**Requirement**: REQ-018 § 3 — Actuator.current_state + ControlEngine.evaluate_actuator_state
**Priority**: High
**Category**: Detailansicht
**Preconditions**:
- Aktor "Befeuchter Zelt 1" ist AN, ausgeloest durch Regel "VPD-Korrektur"

**Testschritte**:
1. Nutzer navigiert zur Detailseite von "Befeuchter Zelt 1"

**Erwartete Ergebnisse**:
- Aktueller Zustand: "AN"
- Aktive Quelle: "Regel: VPD-Korrektur Befeuchter"
- Die Regel "VPD-Korrektur Befeuchter" ist in einem Chip oder Label sichtbar und klickbar (fuehrt zur Regel-Detailseite)
- Letzter Zustandswechsel: Zeitstempel sichtbar

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-018, aktor, detailseite, zustand, quelle, regel]

---

### TC-018-071: Mehrere Profile — Location-Override-Profil hat Vorrang vor Phasen-Profil

**Requirement**: REQ-018 § 2 — AQL "location_override != null: location_override hat Vorrang vor phase_profile"
**Priority**: Medium
**Category**: Detailansicht
**Preconditions**:
- Phase "Vegetativ" hat Profil "Indoor Cannabis Vegetativ" (18h, 26°C)
- Location "Grow Zelt 1" hat ein standort-spezifisches Override-Profil gesetzt (16h, 24°C)

**Testschritte**:
1. Nutzer navigiert zur Detailseite von Location "Grow Zelt 1"
2. Nutzer betrachtet den Abschnitt "Aktives Profil"

**Erwartete Ergebnisse**:
- Das angezeigte aktive Profil ist das standort-spezifische: "Eigenes Profil Grow Zelt 1 (16h, 24°C)"
- Ein Hinweistext: "Dieses standort-spezifische Profil ueberschreibt das Phasen-Standard-Profil 'Indoor Cannabis Vegetativ'"
- Das Phasen-Standard-Profil ist sichtbar, aber als "uebersteuert" gekennzeichnet

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-018, profil, location-override, phasenprofil, vorrang]

---

### TC-018-072: Authentifizierungs-Test — nicht eingeloggte Nutzer werden redirectet

**Requirement**: REQ-018 § 4 — "Alle Endpunkte erfordern Authentifizierung (JWT Bearer Token)"
**Priority**: High
**Category**: Fehlermeldung
**Preconditions**:
- Nutzer ist NICHT eingeloggt

**Testschritte**:
1. Nutzer versucht direkt die URL `/standorte/growzelt1/aktoren` aufzurufen

**Erwartete Ergebnisse**:
- Nutzer wird auf die Login-Seite weitergeleitet
- Die urspruenglich angesteuerte URL wird nach dem Login wieder aufgerufen (Redirect nach Login)

**Nachbedingungen**:
- Kein Status geaendert; Nutzer muss sich einloggen

**Tags**: [req-018, auth, redirect, login, unauthentifiziert]

---

## Coverage-Zusammenfassung

| Spezifikations-Abschnitt | Beschreibung | Testfaelle |
|---------------------------|--------------|------------|
| § 1 Business Case — Aktor-Infrastruktur | Aktor-Typen, Protokolle, Steuerungsebenen | TC-018-001 bis TC-018-009 |
| § 1 Business Case — Hysterese & Debouncing | on/off-Schwellwerte, Mindestlaufzeit | TC-018-016, TC-018-019, TC-018-062 |
| § 1 Business Case — Prioritaetssystem | Override > Safety > Rule > Schedule | TC-018-024, TC-018-067 |
| § 1 Business Case — HA-Integration | Bidirektional, Graceful Degradation, UI-Visibility | TC-018-008, TC-018-041–044 |
| § 1 Business Case — DLI-Lichtsteuerung | DLI-Ziel, Kurztagspflanzen-Schutz | TC-018-039, TC-018-054 |
| § 1 Business Case — CO2-PPFD-Kopplung | PPFD-Mindest-Schwellwert fuer CO2 | TC-018-055 |
| § 1 Business Case — DIF/DROP | Temperatur-Umschaltung, DROP-Technik | TC-018-034, TC-018-056 |
| § 1 Business Case — Substratfeuchte-Bewaesserung | Sensorgesteuerte Bewaesserung | TC-018-016 (implizit via Regel-Erstellung) |
| § 1 Business Case — Konfliktgruppen | co2_ventilation, heat_cool | TC-018-053, TC-018-069 |
| § 1 Business Case — Fail-Safe-States | Default-Zustand bei Kommunikationsverlust | TC-018-048, TC-018-049 |
| § 1 Business Case — Notabschaltung | Emergency-Stop 3 Szenarien | TC-018-050–052 |
| § 2 ArangoDB-Modell — Location-Override | Standort-Profil vs. Phasen-Profil | TC-018-071 |
| § 3 Aktoren-CRUD | POST/GET/PUT/DELETE | TC-018-001–007 |
| § 3 Protokoll-Validierung | HA erfordert ha_entity_id, MQTT erfordert mqtt_command_topic | TC-018-003–005 |
| § 3 Zeitplaene (ControlSchedule) | CRUD, Toggle, Wochentage, Mitternacht | TC-018-010–015, TC-018-066 |
| § 3 Regeln (ControlRule) | CRUD, Toggle, Sicherheitsregel, Compound | TC-018-016–023 |
| § 3 Manueller Override | Setzen, Beenden, Validierung | TC-018-024–027, TC-018-065 |
| § 3 Steuerungshistorie (ControlEvent) | Log, Filter, Quellen, Fallback-Task | TC-018-028–031 |
| § 3 Phasen-Kontroll-Profile | CRUD, DIF-Validierung, Anwenden | TC-018-032–039 |
| § 3 Energieverbrauch | Schaetzung kWh pro Location | TC-018-040 |
| § 3 Direktbefehl | POST /command | TC-018-046 |
| § 3 Gesamtstatus Location | GET /control-status | TC-018-047 |
| § 3 Dry-Run Regeltest | POST /rules/{key}/test | TC-018-022 |
| § 3 Manuelle Aktoren | Fallback-Task-Erzeugung | TC-018-045 |
| § 4 Authentifizierung & Autorisierung | Admin/Grower/Mitglied-Berechtigungen | TC-018-057, TC-018-058, TC-018-072 |
| Grenzwerte (Boundary) | ge/le Validierungen aus Pydantic-Modellen | TC-018-059–063 |
| Edge Cases | Offline-Aktor, leere Listen, Ueberschreibungs-Logik | TC-018-064, TC-018-068, TC-018-070 |
