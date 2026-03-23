---
req_id: REQ-014
title: Tankmanagement — Tank-Verwaltung fuer Naehrstoffloesungen und Bewaesserung
category: Bewaesserung & Duengung
test_count: 72
coverage_areas:
  - Tank-Listenansicht (TankListPage)
  - Tank-Erstellen-Dialog (TankCreateDialog)
  - Tank-Detailseite (TankDetailPage) — 6 Tabs
  - Tab Details inkl. Alerts und aktuellem Zustand
  - Tab Zustandsmessungen (TankState-Historie)
  - Tab Wartung (MaintenanceLog und DueMaintenance)
  - Tab Wartungsplaene (MaintenanceSchedule CRUD)
  - Tab Befuellungen (TankFillEvent-Historie)
  - Tab Bearbeiten (Tank-Stammdaten-Edit mit UnsavedChangesGuard)
  - Tank-Loeschen mit Aktivversorgungsschutz
  - Befuellung dokumentieren (TankFillCreateDialog)
  - Zustandsmessung manuell erfassen (TankStateCreateDialog)
  - Wartung dokumentieren (MaintenanceLogDialog)
  - Wartungsplan anlegen und bearbeiten (MaintenanceScheduleDialog)
  - Live-Abfrage (HA Live-Query) inkl. Messung uebernehmen
  - Sensor-Binding (SensorCreateDialog, monitors_tank)
  - Alert-System (pH, EC, Temperatur, DO, ORP, Fuellstand, Algenrisiko)
  - Befuellungstypen (full_change, top_up, adjustment)
  - Wasserquellen-Kaskade und Mischverhaeltnis (water_source=mixed)
  - Warnungen bei Befuellung (Volumen, EC/pH-Abweichung, Tank-Safety, Chlor)
  - Giessvorgaenge (WateringEvent: fertigation, drench, foliar, top_dress)
  - Giessvorgaenge als ergaenzende Handduenung (is_supplemental)
  - Authentifizierung und Zugriffsschutz (REQ-023/024)
generated: 2026-03-21
version: "1.5 (HA-Sensor-Binding & Bulk-Endpoints)"
---

# TC-REQ-014: Tankmanagement

Dieses Dokument enthaelt End-to-End-Testfaelle aus **REQ-014 Tankmanagement v1.5**, ausschliesslich aus der Perspektive eines Nutzers im Browser. Keine API-Calls, HTTP-Statuscodes oder Datenbankabfragen erscheinen in diesen Testfaellen. Alle Aussagen beschreiben, was der Nutzer sieht, anklickt, eintippt und auf dem Bildschirm erwartet.

Die UI-Sprache ist **Deutsch** (Standard-Locale). Alle Labels, Buttons und Meldungen referenzieren die deutschen i18n-Texte.

URL-Muster:
- Tank-Liste: `/standorte/tanks`
- Tank-Detail: `/standorte/tanks/{key}`

---

## 1. Tank-Listenansicht

### TC-014-001: Tank-Listenansicht wird geladen und zeigt Tanks

**Requirement**: REQ-014 § 3 REST-API — `GET /api/v1/tanks`; § 6 DoD "Tank-CRUD"
**Priority**: Critical
**Category**: Listenansicht
**Preconditions**:
- Nutzer ist eingeloggt (Tenant-Mitglied)
- Mindestens 2 Tanks sind im System vorhanden (z.B. "Haupttank Grow Zelt 1" und "Regenwassertonne Garten")

**Testschritte**:
1. Nutzer navigiert zu `/standorte/tanks`

**Erwartete Ergebnisse**:
- Seite laedt ohne Fehler
- Seitentitel "Tanks" (oder aequivalente Ueberschrift) ist sichtbar
- Tabelle zeigt mindestens 2 Zeilen mit den Spalten: Name, Typ, Volumen (L), Material
- Jede Zeile zeigt den Tank-Typ als uebersetzten Wert (z.B. "Naehrstoffloesung" fuer `nutrient`)
- Schaltflaeche "Tank erstellen" ist sichtbar

**Nachbedingungen**:
- Keine Daten geaendert

**Tags**: [req-014, tank-liste, listenansicht, navigation]

---

### TC-014-002: Leere Tank-Liste zeigt leeren Zustand mit Erstellen-Aktion

**Requirement**: REQ-014 § 6 DoD "Tank-CRUD"
**Priority**: Medium
**Category**: Listenansicht
**Preconditions**:
- Nutzer ist eingeloggt
- Kein Tank im System vorhanden

**Testschritte**:
1. Nutzer navigiert zu `/standorte/tanks`

**Erwartete Ergebnisse**:
- Tabelle ist leer oder zeigt eine Illustration mit leerem Zustand
- Ein Aktions-Button "Tank erstellen" oder aequivalente Handlungsaufforderung ist direkt im leeren Zustand sichtbar

**Nachbedingungen**:
- Keine Daten geaendert

**Tags**: [req-014, tank-liste, leer, empty-state]

---

### TC-014-003: Tank-Tabelle ist durchsuchbar

**Requirement**: REQ-014 § 6 DoD; UI-NFR-010 § 7.2
**Priority**: Medium
**Category**: Listenansicht
**Preconditions**:
- Nutzer befindet sich auf `/standorte/tanks`
- Tanks "Haupttank Grow Zelt 1" (nutrient) und "Regenwassertonne Garten" (reservoir) sind vorhanden

**Testschritte**:
1. Nutzer gibt "Regen" in das Suchfeld "Tabelle durchsuchen..." ein

**Erwartete Ergebnisse**:
- Tabelle filtert sich nach ca. 300 ms Verzoegerung
- Nur "Regenwassertonne Garten" ist noch sichtbar
- "Haupttank Grow Zelt 1" ist nicht mehr sichtbar

**Nachbedingungen**:
- URL-Parameter fuer Suche ist persistent (Tab-Wechsel haelt Suche)

**Tags**: [req-014, tank-liste, suche, filter]

---

### TC-014-004: Klick auf Tank-Zeile navigiert zur Detailseite

**Requirement**: REQ-014 § 3 REST-API — Navigation
**Priority**: Critical
**Category**: Navigation
**Preconditions**:
- Nutzer befindet sich auf `/standorte/tanks`
- Tank "Haupttank Grow Zelt 1" mit Key `tank_zelt1` ist vorhanden

**Testschritte**:
1. Nutzer klickt auf die Zeile "Haupttank Grow Zelt 1" in der Tabelle

**Erwartete Ergebnisse**:
- Browser navigiert zu `/standorte/tanks/tank_zelt1`
- Tank-Detailseite fuer "Haupttank Grow Zelt 1" wird geladen
- Seitentitel zeigt den Tank-Namen

**Nachbedingungen**:
- Keine Daten geaendert

**Tags**: [req-014, navigation, detail, row-click]

---

## 2. Tank erstellen

### TC-014-005: Tank-Erstellen-Dialog oeffnet sich

**Requirement**: REQ-014 § 6 DoD "Tank-CRUD"
**Priority**: Critical
**Category**: Dialog
**Preconditions**:
- Nutzer befindet sich auf `/standorte/tanks`

**Testschritte**:
1. Nutzer klickt auf "Tank erstellen"

**Erwartete Ergebnisse**:
- Dialog "Tank erstellen" oeffnet sich
- Pflichtfelder: Name (leer), Typ (vorgewaehlt: "Naehrstoffloesung"), Material (vorgewaehlt: "Kunststoff"), Volumen (vorgewaehlt: 50)
- Optionale Felder: Standort (Site-Dropdown dann Location-Dropdown), Ausstattungs-Schalter, Notizen
- Schaltflaechen "Erstellen" und "Abbrechen" sind sichtbar

**Nachbedingungen**:
- Kein Tank erstellt

**Tags**: [req-014, tank-erstellen, dialog, formular]

---

### TC-014-006: Tank erfolgreich erstellen (Happy Path)

**Requirement**: REQ-014 § 6 DoD "Tank-CRUD"; Testszenario 6 (Standard-Wartungsplaene)
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- Dialog "Tank erstellen" ist geoeffnet
- Standort "Grow Zelt 2" mit Location "Grow Zelt 2 Mitte" existiert im System

**Testschritte**:
1. Nutzer gibt "NFT-Rücklauf Zelt 3" in das Feld "Name" ein
2. Nutzer waehlt "Rezirkulation" im Dropdown "Typ"
3. Nutzer gibt "20" in das Feld "Volumen (L)" ein
4. Nutzer waehlt "Kunststoff" im Dropdown "Material"
5. Nutzer aktiviert den Schalter "Luftpumpe"
6. Nutzer aktiviert den Schalter "Umwaelzpumpe"
7. Nutzer aktiviert den Schalter "UV-Sterilisator"
8. Nutzer waehlt im Dropdown "Standort" den Eintrag "Grow Zelt 2"
9. Nutzer waehlt im Dropdown "Bereich" den Eintrag "Grow Zelt 2 Mitte"
10. Nutzer klickt "Erstellen"

**Erwartete Ergebnisse**:
- Dialog schliesst sich
- Erfolgsbenachrichtigung erscheint (z.B. Snackbar "Erstellen" oder aequivalent)
- Tabelle auf der Liste aktualisiert sich und zeigt "NFT-Rücklauf Zelt 3" mit Typ "Rezirkulation"

**Nachbedingungen**:
- Tank "NFT-Rücklauf Zelt 3" existiert im System
- Automatisch wurden Standard-Wartungsplaene fuer Typ "recirculation" angelegt (6 Plaene)
- Tank ist Location "Grow Zelt 2 Mitte" zugeordnet

**Tags**: [req-014, tank-erstellen, happy-path, recirculation, wartungsplaene]

---

### TC-014-007: Pflichtfeld-Validierung beim Tank-Erstellen

**Requirement**: REQ-014 § 3 Pydantic-Modell — `name: str = Field(min_length=1)`; `volume_liters: float = Field(gt=0)`
**Priority**: High
**Category**: Formvalidierung
**Preconditions**:
- Dialog "Tank erstellen" ist geoeffnet

**Testschritte**:
1. Nutzer loescht den vorausgefuellten Wert im Feld "Volumen (L)" (loescht "50")
2. Nutzer laesst "Name" leer
3. Nutzer klickt "Erstellen"

**Erwartete Ergebnisse**:
- Dialog bleibt geoeffnet
- Fehlermarkierung am Feld "Name": Pflichtfeld-Hinweis ist sichtbar
- Fehlermarkierung am Feld "Volumen (L)": Pflichtfeld- oder Mindestwert-Hinweis ist sichtbar
- Kein Tank wird erstellt

**Nachbedingungen**:
- Kein neuer Tank im System

**Tags**: [req-014, formvalidierung, pflichtfeld, name, volumen]

---

### TC-014-008: Location-Dropdown erst aktiv nach Site-Auswahl

**Requirement**: REQ-014 § 3 — Site-Location-Kaskade im Formular
**Priority**: Medium
**Category**: Formvalidierung
**Preconditions**:
- Dialog "Tank erstellen" ist geoeffnet
- Mindestens eine Site mit Location ist im System vorhanden

**Testschritte**:
1. Nutzer betrachtet das Dropdown "Bereich" (Location)

**Erwartete Ergebnisse**:
- Das Dropdown "Bereich" ist deaktiviert (disabled), solange kein Standort ausgewaehlt ist
- Nutzer waehlt im Dropdown "Standort" einen Eintrag aus
- Das Dropdown "Bereich" wird aktiv und zeigt die Locations des ausgewaehlten Standorts

**Nachbedingungen**:
- Kein Tank erstellt

**Tags**: [req-014, formvalidierung, location-kaskade, dropdown]

---

### TC-014-009: Abbrechen schliesst Dialog ohne Aenderungen

**Requirement**: REQ-014 § 6 DoD "Tank-CRUD"
**Priority**: Low
**Category**: Dialog
**Preconditions**:
- Dialog "Tank erstellen" ist geoeffnet
- Nutzer hat "Testname" in das Feld "Name" eingegeben

**Testschritte**:
1. Nutzer klickt "Abbrechen"

**Erwartete Ergebnisse**:
- Dialog schliesst sich
- Kein neuer Tank wurde erstellt
- Liste zeigt unveraenderten Zustand

**Nachbedingungen**:
- Keine Daten geaendert

**Tags**: [req-014, abbrechen, dialog]

---

## 3. Tank-Detailseite — Tab Details

### TC-014-010: Tank-Detailseite laedt alle 6 Tabs

**Requirement**: REQ-014 § 3 Sektion TankDetailPage
**Priority**: Critical
**Category**: Navigation
**Preconditions**:
- Tank "Haupttank Grow Zelt 1" (nutrient, 50 L) existiert

**Testschritte**:
1. Nutzer navigiert zu `/standorte/tanks/tank_zelt1`

**Erwartete Ergebnisse**:
- Seite laedt ohne Fehler
- Seitentitel zeigt "Haupttank Grow Zelt 1"
- Folgende Tabs sind sichtbar: "Details", "Zustand", "Wartung", "Wartungsplaene", "Befuellungen", "Bearbeiten"
- Tab "Details" ist initial aktiv (Index 0)
- Schaltflaeche "Loeschen" ist sichtbar (rot, mit Papierkorb-Icon)

**Nachbedingungen**:
- Keine Daten geaendert

**Tags**: [req-014, detail, tabs, navigation]

---

### TC-014-011: Tab Details zeigt Tank-Stammdaten

**Requirement**: REQ-014 § 6 DoD "Tank-CRUD"; § 2 Nodes `:Tank`
**Priority**: High
**Category**: Detailansicht
**Preconditions**:
- Nutzer ist auf TankDetailPage von "Haupttank Grow Zelt 1" (Tab "Details" aktiv)
- Tank hat: `tank_type=nutrient`, `volume_liters=50`, `material=plastic`, Location "Grow Zelt 1", `has_lid=true`, `has_air_pump=true`, `has_circulation_pump=true`

**Testschritte**:
1. Nutzer betrachtet die Details-Karte auf dem Tab "Details"

**Erwartete Ergebnisse**:
- Typ-Zeile zeigt "Naehrstoffloesung"
- Volumen-Zeile zeigt "50 L"
- Material-Zeile zeigt "Kunststoff"
- Standort/Bereich-Zeile zeigt z.B. "Grow Zelt 1 / Mitte" (Name des Standorts / Name der Location)
- Ausstattungs-Zeile zeigt Chips: "Deckel", "Luftpumpe", "Umwaelzpumpe"

**Nachbedingungen**:
- Keine Daten geaendert

**Tags**: [req-014, detail, stammdaten, tank-typ]

---

### TC-014-012: Tab Details zeigt aktuellen Tank-Zustand mit Source-Badge

**Requirement**: REQ-014 § 3 Datenherkunft-Kennzeichnung; § 6 DoD "Source-Badge"
**Priority**: High
**Category**: Detailansicht
**Preconditions**:
- Nutzer ist auf TankDetailPage von "Haupttank Grow Zelt 1" (Tab "Details" aktiv)
- Ein TankState mit `ph=5.9, ec_ms=1.75, water_temp_celsius=21.5, fill_level_percent=85, source='manual'` ist vorhanden

**Testschritte**:
1. Nutzer betrachtet die Karte "Letzter Zustand" auf dem Tab "Details"

**Erwartete Ergebnisse**:
- Karte "Letzter Zustand" ist sichtbar
- Zeile "pH" zeigt "5.9"
- Zeile "EC (mS/cm)" zeigt "1.75"
- Zeile "Wassertemperatur" zeigt "21.5 °C"
- Zeile "Fuellstand" zeigt "85%"
- Neben der Ueberschrift "Letzter Zustand" ist ein Chip "Manuell" (grau) sichtbar (Source-Badge)
- Neben dem Zeitstempel ist ein Freshness-Chip sichtbar (Farbe abhaengig von Aktualitaet)

**Nachbedingungen**:
- Keine Daten geaendert

**Tags**: [req-014, detail, tank-zustand, source-badge, freshness]

---

### TC-014-013: Tab Details zeigt Alerts bei kritischen Werten

**Requirement**: REQ-014 § 3 `check_alerts`; § 6 DoD "Alert-System (differenziert)"; Testszenario 3
**Priority**: Critical
**Category**: Detailansicht
**Preconditions**:
- Nutzer ist auf TankDetailPage von einem Naehrstofftank
- Letzter TankState hat: `ph=7.0, ec_ms=2.8, water_temp_celsius=27.0, dissolved_oxygen_mgl=3.5, fill_level_percent=15`
- Letzter Vollwechsel hatte `measured_ph=5.8, target_ec_ms=1.8`

**Testschritte**:
1. Nutzer betrachtet den Tab "Details"

**Erwartete Ergebnisse**:
- Mehrere Alerts sind oberhalb der Details-Karte sichtbar (als MUI Alert-Komponenten)
- Mindestens folgende Meldungen erscheinen (als Fehler/Warnung/Info):
  - Ein rot markierter Alert zu pH ausserhalb des Bereichs (5.5-6.5) mit "critical" oder "error" Severity
  - Ein Alert zu pH-Drift (Drift von 5.8 nach 7.0)
  - Ein rot markierter Alert zu EC-Abweichung (2.8 mS vs. Ziel 1.8 mS, >30%)
  - Ein rot markierter Alert zur Wassertemperatur (27°C kritisch)
  - Ein rot markierter Alert zu Geloestsauerstoff (3.5 mg/L kritisch)
  - Ein gelb-orangener Alert zu niedrigem Fuellstand (15%)

**Nachbedingungen**:
- Keine Daten geaendert

**Tags**: [req-014, alerts, pH, EC, temperatur, DO, fuellstand, critical]

---

### TC-014-014: Tab Details zeigt keine Alerts bei Normalwerten

**Requirement**: REQ-014 § 3 `check_alerts`; Testszenario 18
**Priority**: Medium
**Category**: Detailansicht
**Preconditions**:
- Nutzer ist auf TankDetailPage eines Naehrstofftanks
- Letzter TankState: `ph=6.2, ec_ms=1.8, water_temp_celsius=21.0, fill_level_percent=70`
- Letzter Vollwechsel: `measured_ph=6.0, target_ec_ms=1.8`

**Testschritte**:
1. Nutzer betrachtet den Tab "Details"

**Erwartete Ergebnisse**:
- Kein Alert ist oberhalb der Details-Karte sichtbar
- Die Karte "Letzter Zustand" zeigt alle Werte ohne Fehlermarkierung

**Nachbedingungen**:
- Keine Daten geaendert

**Tags**: [req-014, alerts, normalzustand, keine-alerts]

---

### TC-014-015: Tab Details zeigt Live-Abfrage-Bereich

**Requirement**: REQ-014 § 3 Live-Query; § 6 DoD "Live-Tab", "Live-Query Endpoint"
**Priority**: Medium
**Category**: Detailansicht
**Preconditions**:
- Nutzer ist auf TankDetailPage eines beliebigen Tanks

**Testschritte**:
1. Nutzer betrachtet den Tab "Details" und scrollt nach unten

**Erwartete Ergebnisse**:
- Karte "Live-Sensorwerte" (oder aequivalente Bezeichnung) ist sichtbar
- Schaltflaeche "Live abfragen" (oder aequivalent) ist in der Karte sichtbar
- Sensoren-Abschnitt ist sichtbar mit "Sensor hinzufuegen"-Schaltflaeche

**Nachbedingungen**:
- Keine Daten geaendert

**Tags**: [req-014, live-query, sensor, detail]

---

## 4. Tank-Detailseite — Live-Abfrage

### TC-014-016: Live-Abfrage mit HA-Sensoren liefert Live-Werte

**Requirement**: REQ-014 § 3 Live-Query `GET /tanks/{key}/states/live`; § 6 DoD "Live-Query Endpoint"; Testszenario 22
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- Nutzer ist auf TankDetailPage von "Haupttank Grow Zelt 1" (Tab "Details")
- Tank hat 2 HA-Sensoren (EC: `sensor.tank1_ec`, pH: `sensor.tank1_ph`) und 1 MQTT-Sensor (Temperatur)
- HA-Integration ist in den Kontoeinstellungen konfiguriert

**Testschritte**:
1. Nutzer klickt auf "Live abfragen" in der Karte "Live-Sensorwerte"

**Erwartete Ergebnisse**:
- Waehrend der Abfrage zeigt die Schaltflaeche einen Ladeindikator (CircularProgress)
- Nach Abschluss erscheint eine Tabelle mit Messwerten:
  - EC-Zeile: Wert + gruener pulsierender Freshness-Chip (z.B. "Live") + Chip "HA Live" (gruen)
  - pH-Zeile: Wert + gruener pulsierender Freshness-Chip + Chip "HA Live" (gruen)
  - Temperatur-Zeile: Wert + gruener oder gelber Freshness-Chip + Chip "MQTT" (lila)
- Schaltflaeche "Alle Messungen uebernehmen" erscheint unter der Tabelle

**Nachbedingungen**:
- Kein TankState wurde persistent gespeichert (nur Anzeige)

**Tags**: [req-014, live-query, ha-sensor, mqtt-sensor, freshness-badge, source-badge]

---

### TC-014-017: Live-Abfrage ohne HA-Konfiguration zeigt Hinweis

**Requirement**: REQ-014 § 3 Live-Query Fehlerbehandlung `409`; § 6 DoD "Live-Query Voraussetzung"; Testszenario 23
**Priority**: Medium
**Category**: Fehlermeldung
**Preconditions**:
- Nutzer ist auf TankDetailPage eines beliebigen Tanks
- HA-Integration ist NICHT in den Kontoeinstellungen konfiguriert

**Testschritte**:
1. Nutzer klickt auf "Live abfragen" in der Karte "Live-Sensorwerte"

**Erwartete Ergebnisse**:
- Kein Live-Tabelle erscheint
- Ein informativer Hinweis erscheint (z.B. "HA-Integration nicht konfiguriert" oder "Live-Abfrage erfordert Home Assistant")
- Kein Fehlerdialog, sondern ein sanfter Info-Hinweis (MUI Alert, severity="info")

**Nachbedingungen**:
- Keine Daten geaendert

**Tags**: [req-014, live-query, ha-nicht-konfiguriert, hinweis]

---

### TC-014-018: Messung uebernehmen speichert Live-Wert als TankState

**Requirement**: REQ-014 § 3 Live-Query; § 6 DoD "Messung uebernehmen"; Testszenario 24
**Priority**: High
**Category**: Zustandswechsel
**Preconditions**:
- Nutzer ist auf TankDetailPage, Tab "Details"
- Live-Abfrage wurde ausgefuehrt und zeigt Werte (EC=1.85, pH=5.9) aus HA-Sensoren
- Schaltflaeche "Alle Messungen uebernehmen" ist sichtbar

**Testschritte**:
1. Nutzer klickt auf "Alle Messungen uebernehmen"

**Erwartete Ergebnisse**:
- Waehrend des Speicherns zeigt die Schaltflaeche einen Ladeindikator
- Erfolgsbenachrichtigung erscheint (z.B. Snackbar "Uebernommen")
- Live-Werte-Anzeige verschwindet oder wird zurueckgesetzt
- In der Karte "Letzter Zustand" erscheint der uebernommene Wert mit dem Chip "HA" (blau)
- Tab "Zustand" zeigt den neuen TankState-Eintrag

**Nachbedingungen**:
- Neuer TankState ist im System gespeichert

**Tags**: [req-014, messung-uebernehmen, tank-state, ha-live]

---

## 5. Tank-Detailseite — Tab Zustand

### TC-014-019: Manuelle Zustandsmessung erfassen (Happy Path)

**Requirement**: REQ-014 § 3 `POST /tanks/{key}/states`; § 6 DoD "Zustandserfassung"; Testszenario 18
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- Nutzer ist auf TankDetailPage von "Haupttank Grow Zelt 1", Tab "Zustand" aktiv

**Testschritte**:
1. Nutzer klickt "Messung erfassen" (oder aequivalenten Button auf dem Zustand-Tab)
2. Im Dialog gibt Nutzer folgende Werte ein: pH = 6.2, EC = 1.8, Temperatur = 21, Fuellstand (L) = 35
3. Nutzer klickt "Speichern"

**Erwartete Ergebnisse**:
- Dialog schliesst sich
- Erfolgsbenachrichtigung erscheint
- Zustandshistorie-Tabelle zeigt neuen Eintrag mit pH=6.2, EC=1.8, 21°C, 70% (35L von 50L = 70%)
- Zeile zeigt Source "Manuell"
- Tab "Details" aktualisiert "Letzter Zustand" auf die neuen Werte

**Nachbedingungen**:
- Neuer TankState mit `source='manual'` im System gespeichert
- Fuellstand-Prozent wird automatisch aus Literangabe berechnet (35/50 = 70%)

**Tags**: [req-014, zustandsmessung, manuell, fuellstand, fill-level-prozent]

---

### TC-014-020: Zustandshistorie-Tabelle zeigt alle Eintraege sortiert

**Requirement**: REQ-014 § 3 `GET /tanks/{key}/states`; § 6 DoD "Zustandshistorie"
**Priority**: Medium
**Category**: Listenansicht
**Preconditions**:
- Nutzer ist auf TankDetailPage, Tab "Zustand"
- Mehrere TankState-Eintraege unterschiedlicher Zeitpunkte sind vorhanden

**Testschritte**:
1. Nutzer wechselt zu Tab "Zustand"

**Erwartete Ergebnisse**:
- Tabelle zeigt Spalten: Zeitpunkt, pH, EC (mS/cm), Wassertemp., Fuellstand, TDS (ppm)
- Eintraege sind nach Zeitpunkt absteigend sortiert (neuester oben)
- Klick auf Spaltenheader "Zeitpunkt" tauscht Sortierrichtung
- Fehlende Werte werden als "—" dargestellt

**Nachbedingungen**:
- Keine Daten geaendert

**Tags**: [req-014, zustandshistorie, tabelle, sortierung]

---

### TC-014-021: Fuellstand-Plausibilitaet: Uebersteigen des Tank-Volumens wird abgelehnt

**Requirement**: REQ-014 § 3 `FillLevelValidator`; § 6 DoD "Fuellstand-Plausibilitaet"
**Priority**: High
**Category**: Formvalidierung
**Preconditions**:
- Nutzer hat Dialog "Messung erfassen" auf einem 50-L-Tank geoeffnet

**Testschritte**:
1. Nutzer gibt "55" in das Feld "Fuellstand (L)" ein
2. Nutzer klickt "Speichern"

**Erwartete Ergebnisse**:
- Dialog bleibt geoeffnet
- Eine Fehlermeldung erscheint: Fuellstand ueberschreitet das Tankvolumen (55 L > 50 L)
- Kein TankState wird gespeichert

**Nachbedingungen**:
- Kein neuer TankState im System

**Tags**: [req-014, formvalidierung, fuellstand, plausibilitaet]

---

### TC-014-022: DO- und ORP-Felder sind im Zustandsformular erfassbar

**Requirement**: REQ-014 § 2 Nodes `:TankState`; § 6 DoD "DO/ORP-Export"
**Priority**: Medium
**Category**: Formvalidierung
**Preconditions**:
- Nutzer hat Dialog "Messung erfassen" auf einem Naehrstofftank geoeffnet

**Testschritte**:
1. Nutzer gibt "7.5" in das Feld "Geloestsauerstoff (mg/L)" ein
2. Nutzer gibt "720" in das Feld "ORP (mV)" ein
3. Nutzer klickt "Speichern"

**Erwartete Ergebnisse**:
- Dialog schliesst sich
- Erfolgsbenachrichtigung erscheint
- Neuer TankState in der Zustandshistorie zeigt DO=7.5 mg/L und ORP=720 mV

**Nachbedingungen**:
- Neuer TankState mit DO und ORP ist gespeichert

**Tags**: [req-014, dissolved-oxygen, ORP, zustandsmessung]

---

## 6. Tank-Detailseite — Tab Wartung

### TC-014-023: Tab Wartung zeigt faellige Wartungen

**Requirement**: REQ-014 § 3 `GET /tanks/{key}/maintenance/due`; § 6 DoD "Wartungshistorie"; Testszenario 2
**Priority**: High
**Category**: Detailansicht
**Preconditions**:
- Nutzer ist auf TankDetailPage, Tab "Wartung"
- Wasserwechsel-Intervall ist 7 Tage, letzter Wechsel vor 8 Tagen

**Testschritte**:
1. Nutzer wechselt zu Tab "Wartung"

**Erwartete Ergebnisse**:
- Abschnitt "Faellige Wartungen" zeigt mindestens eine Zeile
- Zeile fuer "Wasserwechsel": Spalte "Naechste Faelligkeit" zeigt ein Datum in der Vergangenheit
- Status-Chip zeigt "Ueberfaellig" (rot) fuer den Wasserwechsel
- Abschnitt "Wartungshistorie" zeigt vergangene Wartungseintraege

**Nachbedingungen**:
- Keine Daten geaendert

**Tags**: [req-014, wartung, faellig, ueberfaellig, wasserwechsel]

---

### TC-014-024: Wartung dokumentieren (Happy Path)

**Requirement**: REQ-014 § 3 `POST /tanks/{key}/maintenance`; § 6 DoD "Wartungshistorie"
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- Nutzer ist auf TankDetailPage, Tab "Wartung"

**Testschritte**:
1. Nutzer klickt "Wartung dokumentieren" (oder aequivalente Schaltflaeche)
2. Nutzer waehlt Typ "Kalibrierung" im Dropdown
3. Nutzer gibt "45" in das Feld "Dauer (Minuten)" ein
4. Nutzer gibt "pH 4.0, pH 7.0, EC 1.413 mS" in das Textfeld "Verwendete Produkte" ein
5. Nutzer klickt "Speichern"

**Erwartete Ergebnisse**:
- Dialog schliesst sich
- Erfolgsbenachrichtigung erscheint
- Wartungshistorie-Tabelle zeigt neuen Eintrag: Typ "Kalibrierung", heutiges Datum, 45 min
- Bei naechster Prüfung ist Kalibrierung nicht mehr als ueberfaellig markiert

**Nachbedingungen**:
- Neuer MaintenanceLog-Eintrag im System

**Tags**: [req-014, wartung-dokumentieren, kalibrierung, happy-path]

---

### TC-014-025: Wartungshistorie-Tabelle ist sortierbar und durchsuchbar

**Requirement**: REQ-014 § 6 DoD "Wartungshistorie"
**Priority**: Low
**Category**: Listenansicht
**Preconditions**:
- Nutzer ist auf TankDetailPage, Tab "Wartung"
- Mehrere Wartungseintraege mit verschiedenen Typen sind vorhanden

**Testschritte**:
1. Nutzer gibt "Kalibrierung" in das Suchfeld der Wartungshistorie ein

**Erwartete Ergebnisse**:
- Tabelle filtert sich: nur Kalibrierungs-Eintraege werden angezeigt
- Andere Wartungstypen werden ausgeblendet

**Nachbedingungen**:
- Keine Daten geaendert

**Tags**: [req-014, wartungshistorie, suche, filter]

---

## 7. Tank-Detailseite — Tab Wartungsplaene

### TC-014-026: Tab Wartungsplaene zeigt automatisch erstellte Plaene

**Requirement**: REQ-014 § 3 `DEFAULT_MAINTENANCE_SCHEDULES`; § 6 DoD "Standard-Schedules"; Testszenario 6
**Priority**: High
**Category**: Detailansicht
**Preconditions**:
- Nutzer ist auf TankDetailPage eines neu erstellten "recirculation"-Tanks, Tab "Wartungsplaene"

**Testschritte**:
1. Nutzer wechselt zu Tab "Wartungsplaene"

**Erwartete Ergebnisse**:
- Tabelle zeigt 6 automatisch erstellte Wartungsplaene:
  - Wasserwechsel: 7 Tage, Prioritaet "Kritisch"
  - Reinigung: 14 Tage, Prioritaet "Hoch"
  - Desinfektion: 14 Tage, Prioritaet "Kritisch"
  - Kalibrierung: 7 Tage (inline-Sonden), Prioritaet "Hoch"
  - Pumpeninspektion: 14 Tage, Prioritaet "Mittel"
  - Filterwechsel: 30 Tage, Prioritaet "Hoch"
- Alle Plaene zeigen Status-Chip "Aktiv" (gruen)
- Jede Zeile hat Bearbeiten- und Loeschen-Icons

**Nachbedingungen**:
- Keine Daten geaendert

**Tags**: [req-014, wartungsplaene, default-schedules, recirculation]

---

### TC-014-027: Wartungsplan bearbeiten — Intervall anpassen

**Requirement**: REQ-014 § 3 `PUT /tanks/{key}/schedules/{schedule_key}`; § 6 DoD "Wartungsplaene"
**Priority**: Medium
**Category**: Happy Path
**Preconditions**:
- Nutzer ist auf TankDetailPage, Tab "Wartungsplaene"
- Ein Wasserwechsel-Plan mit 7 Tagen Intervall ist vorhanden

**Testschritte**:
1. Nutzer klickt das Bearbeiten-Icon (Stift) in der Zeile "Wasserwechsel"
2. Dialog oeffnet sich mit vorausgefuellten Werten
3. Nutzer aendert "Intervall (Tage)" von "7" auf "10"
4. Nutzer klickt "Speichern"

**Erwartete Ergebnisse**:
- Dialog schliesst sich
- Erfolgsbenachrichtigung erscheint
- Wasserwechsel-Zeile zeigt jetzt "10" in der Spalte "Intervall (Tage)"

**Nachbedingungen**:
- MaintenanceSchedule fuer Wasserwechsel hat `interval_days=10`

**Tags**: [req-014, wartungsplan-bearbeiten, intervall, happy-path]

---

### TC-014-028: Wartungsplan-Validierung — Erinnerung muss vor Intervall liegen

**Requirement**: REQ-014 § 3 `MaintenanceScheduleDefinition.validate_reminder_before_interval`; § 6 DoD "Wartungsplaene"
**Priority**: Medium
**Category**: Formvalidierung
**Preconditions**:
- Bearbeiten-Dialog eines Wartungsplans ist geoeffnet
- Aktueller Wert: Intervall=7 Tage, Erinnerung=1 Tag vorher

**Testschritte**:
1. Nutzer aendert "Erinnerung (Tage vorher)" von "1" auf "7"
2. Nutzer klickt "Speichern"

**Erwartete Ergebnisse**:
- Eine Fehlermeldung erscheint: Erinnerung (7d) muss kleiner als Intervall (7d) sein
- Dialog bleibt geoeffnet
- Kein Plan wird gespeichert

**Nachbedingungen**:
- Plan bleibt unveraendert

**Tags**: [req-014, formvalidierung, erinnerung, intervall, validierung]

---

### TC-014-029: Wartungsplan loeschen mit Bestaetigung

**Requirement**: REQ-014 § 3 `DELETE /tanks/{key}/schedules/{schedule_key}`
**Priority**: Medium
**Category**: Dialog
**Preconditions**:
- Nutzer ist auf TankDetailPage, Tab "Wartungsplaene"
- Ein Pumpeninspektion-Plan ist vorhanden

**Testschritte**:
1. Nutzer klickt das Loeschen-Icon (Papierkorb) in der Zeile "Pumpeninspektion"
2. Ein Bestaetigungs-Dialog erscheint
3. Nutzer klickt "Loeschen" (oder "Bestaetigen")

**Erwartete Ergebnisse**:
- Dialog schliesst sich
- Erfolgsbenachrichtigung erscheint
- Pumpeninspektion-Zeile ist nicht mehr in der Tabelle sichtbar

**Nachbedingungen**:
- MaintenanceSchedule "Pumpeninspektion" geloescht

**Tags**: [req-014, wartungsplan-loeschen, bestaetigungsdialog]

---

### TC-014-030: Neuen Wartungsplan manuell anlegen

**Requirement**: REQ-014 § 3 `POST /tanks/{key}/schedules`; § 6 DoD "Wartungsplaene"
**Priority**: Medium
**Category**: Happy Path
**Preconditions**:
- Nutzer ist auf TankDetailPage, Tab "Wartungsplaene"
- Schaltflaeche "Wartungsplan hinzufuegen" (oder aequivalent) ist sichtbar

**Testschritte**:
1. Nutzer klickt "Wartungsplan hinzufuegen"
2. Nutzer waehlt "Filterwechsel" im Typ-Dropdown
3. Nutzer gibt "45" ein als Intervall-Tage
4. Nutzer gibt "2" ein als Erinnerung-Tage
5. Nutzer waehlt Prioritaet "Hoch"
6. Nutzer klickt "Speichern"

**Erwartete Ergebnisse**:
- Dialog schliesst sich
- Erfolgsbenachrichtigung erscheint
- Neue Zeile "Filterwechsel" erscheint in der Tabelle mit 45 Tagen und Prioritaet "Hoch"

**Nachbedingungen**:
- Neuer MaintenanceSchedule im System

**Tags**: [req-014, wartungsplan-erstellen, filterwechsel]

---

## 8. Tank-Detailseite — Tab Befuellungen

### TC-014-031: Befuellung dokumentieren — Vollwechsel (Happy Path)

**Requirement**: REQ-014 § 3 `POST /tanks/{key}/fills`; § 6 DoD "Befuellungshistorie", "Befuellungstypen"; Testszenario 8
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- Nutzer ist auf TankDetailPage von "Haupttank Grow Zelt 1" (50 L, nutrient), Tab "Befuellungen"

**Testschritte**:
1. Nutzer klickt "Befuellung dokumentieren" (oder aequivalenten Button)
2. Dialog "Befuellung dokumentieren" oeffnet sich
3. Nutzer waehlt "Vollwechsel" im Dropdown "Befuellungstyp"
4. Nutzer gibt "48" in das Feld "Volumen (L)" ein
5. Nutzer waehlt "Osmosewasser" im Dropdown "Wasserquelle"
6. Nutzer gibt "1.8" in das Feld "Ziel-EC (mS/cm)" ein
7. Nutzer gibt "5.8" in das Feld "Ziel-pH" ein
8. Nutzer gibt "1.75" in das Feld "Gemessen EC (mS/cm)" ein
9. Nutzer gibt "5.9" in das Feld "Gemessen pH" ein
10. Nutzer klickt "Speichern"

**Erwartete Ergebnisse**:
- Dialog schliesst sich
- Erfolgsbenachrichtigung "Befuellung erfasst" (oder aequivalent) erscheint
- Befuellungs-Tabelle zeigt neuen Eintrag: "Vollwechsel", 48 L, Ziel-EC 1.8 / Gemessen 1.75
- Tab "Details" aktualisiert "Letzter Zustand" mit EC=1.75, pH=5.9 (automatisch erzeugter TankState)

**Nachbedingungen**:
- TankFillEvent im System gespeichert
- Automatisch erzeugter TankState mit `source='manual'` im System

**Tags**: [req-014, befuellung, vollwechsel, happy-path, tank-state-automatisch]

---

### TC-014-032: Befuellung — Warnung bei Auffuellung mit mehr als 50% des Volumens

**Requirement**: REQ-014 § 3 `record_fill_event` Volumen-Plausibilitaet; § 6 DoD "Befuellungstypen"; Testszenario 9
**Priority**: High
**Category**: Fehlermeldung
**Preconditions**:
- Dialog "Befuellung dokumentieren" ist fuer 50-L-Tank geoeffnet
- Befuellungstyp "Auffuellung" ist ausgewaehlt

**Testschritte**:
1. Nutzer waehlt "Auffuellung" im Dropdown "Befuellungstyp"
2. Nutzer gibt "30" in das Feld "Volumen (L)" ein (= 60% des Tank-Volumens)
3. Nutzer klickt "Speichern"

**Erwartete Ergebnisse**:
- Dialog speichert die Befuellung (kein Fehler — nur Warnung)
- Eine Warnung erscheint im Dialog oder als Snackbar: "Auffuellung von 30 L ist >50% des Tank-Volumens — Vollwechsel stattdessen?"
- TankFillEvent wird trotzdem gespeichert (Warnung blockiert nicht)

**Nachbedingungen**:
- TankFillEvent mit `fill_type='top_up', volume_liters=30` im System

**Tags**: [req-014, befuellung, auffuellung, volumen-warnung, plausibilitaet]

---

### TC-014-033: Befuellung — Korrektur erfordert Ziel-EC oder Ziel-pH

**Requirement**: REQ-014 § 3 `TankFillEvent.validate_adjustment_has_target`; § 6 DoD "Befuellungstypen"; Testszenario 10
**Priority**: High
**Category**: Formvalidierung
**Preconditions**:
- Dialog "Befuellung dokumentieren" ist geoeffnet

**Testschritte**:
1. Nutzer waehlt "Korrektur" im Dropdown "Befuellungstyp"
2. Nutzer gibt "0.5" in das Feld "Volumen (L)" ein
3. Nutzer laesst "Ziel-EC" und "Ziel-pH" leer
4. Nutzer klickt "Speichern"

**Erwartete Ergebnisse**:
- Eine Fehlermeldung erscheint: Bei einer Korrektur muss mindestens Ziel-EC oder Ziel-pH angegeben werden
- Dialog bleibt geoeffnet
- Kein TankFillEvent wird gespeichert

**Nachbedingungen**:
- Kein neues TankFillEvent im System

**Tags**: [req-014, formvalidierung, korrektur, adjustment, ziel-ec, ziel-ph]

---

### TC-014-034: Befuellung — Wasserquelle "Gemischt" zeigt Mischverhaeltnis-Feld

**Requirement**: REQ-014 § 6 DoD "TankFillEvent water_source 'mixed'", "water_mix_ratio_ro_percent"
**Priority**: Medium
**Category**: Formvalidierung
**Preconditions**:
- Dialog "Befuellung dokumentieren" ist geoeffnet

**Testschritte**:
1. Nutzer waehlt "Gemischt (Osmose/Leitungswasser)" im Dropdown "Wasserquelle"

**Erwartete Ergebnisse**:
- Ein zusaetzliches Feld "Osmose-Anteil (%)" (oder aequivalent) erscheint im Dialog
- Das Feld erlaubt Eingaben von 0 bis 100
- Falls Site-Daten und NutrientPlan vorhanden sind: WaterMixRecommendationBox-Abschnitt erscheint mit Empfehlung und "Uebernehmen"-Schaltflaeche

**Nachbedingungen**:
- Kein TankFillEvent erstellt

**Tags**: [req-014, wasserquelle, gemischt, mischverhaeltnis, water-mix-ratio]

---

### TC-014-035: Befuellung — EC/pH-Abweichungs-Warnung bei grosser Differenz

**Requirement**: REQ-014 § 3 `record_fill_event` EC-Abweichungs-Check; § 6 DoD "Soll/Ist-Vergleich"
**Priority**: Medium
**Category**: Fehlermeldung
**Preconditions**:
- Dialog "Befuellung dokumentieren" ist geoeffnet, Vollwechsel ausgewaehlt

**Testschritte**:
1. Nutzer gibt "1.8" als Ziel-EC ein
2. Nutzer gibt "2.5" als Gemessener EC ein (Abweichung 0.7 > 0.3 Toleranz)
3. Nutzer klickt "Speichern"

**Erwartete Ergebnisse**:
- TankFillEvent wird gespeichert
- Eine Warnung erscheint im Dialog oder als Snackbar: EC-Abweichung von Ziel 1.8 zu gemessen 2.5 (Δ 0.7 mS)
- Warnung blockiert nicht das Speichern

**Nachbedingungen**:
- TankFillEvent mit abweichenden EC-Werten gespeichert

**Tags**: [req-014, befuellung, ec-abweichung, warnung, soll-ist]

---

### TC-014-036: Befuellungshistorie-Tab zeigt Eintraege chronologisch absteigend

**Requirement**: REQ-014 § 3 `GET /tanks/{key}/fills`; § 6 DoD "Befuellungshistorie"; Testszenario 11
**Priority**: High
**Category**: Listenansicht
**Preconditions**:
- Nutzer ist auf TankDetailPage, Tab "Befuellungen"
- 3 TankFillEvents aus Februar sind vorhanden (fill_zelt1_001, _002, _003)

**Testschritte**:
1. Nutzer wechselt zu Tab "Befuellungen"

**Erwartete Ergebnisse**:
- Tabelle zeigt 3 Eintraege, neueste Befuellung zuerst
- Spalten: Zeitpunkt, Befuellungstyp, Volumen (L), Ziel-EC/pH, Gemessen EC/pH
- Befuellungstypen sind uebersetzt: "Vollwechsel", "Auffuellung", "Korrektur"
- Klick auf Spaltenheader "Zeitpunkt" aendert Sortierrichtung

**Nachbedingungen**:
- Keine Daten geaendert

**Tags**: [req-014, befuellungshistorie, tabelle, sortierung, fill-type]

---

## 9. Tank-Detailseite — Tab Bearbeiten

### TC-014-037: Tank-Stammdaten bearbeiten (Happy Path)

**Requirement**: REQ-014 § 3 `PUT /tanks/{key}`; § 6 DoD "Tank-CRUD"
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- Nutzer ist auf TankDetailPage von "Haupttank Grow Zelt 1", Tab "Bearbeiten" aktiv

**Testschritte**:
1. Nutzer wechselt zu Tab "Bearbeiten"
2. Nutzer aendert das Feld "Name" von "Haupttank Grow Zelt 1" auf "Haupttank Zelt 1 v2"
3. Nutzer aktiviert den Schalter "Heizstab"
4. Nutzer klickt "Speichern"

**Erwartete Ergebnisse**:
- Erfolgsbenachrichtigung erscheint
- Seitentitel aktualisiert sich auf "Haupttank Zelt 1 v2"
- Tab "Details" zeigt "Heizstab"-Chip in der Ausstattungszeile

**Nachbedingungen**:
- Tank hat `name='Haupttank Zelt 1 v2'` und `has_heater=true`

**Tags**: [req-014, bearbeiten, stammdaten, happy-path]

---

### TC-014-038: UnsavedChangesGuard verhindert Navigation mit ungespeicherten Aenderungen

**Requirement**: REQ-014 § 3 UnsavedChangesGuard auf TankDetailPage
**Priority**: High
**Category**: Navigation
**Preconditions**:
- Nutzer ist auf TankDetailPage, Tab "Bearbeiten"
- Nutzer hat den Namen geaendert (Formular ist "dirty")

**Testschritte**:
1. Nutzer klickt in der Sidebar auf einen anderen Navigationspunkt (z.B. "Pflanzen")

**Erwartete Ergebnisse**:
- Browser zeigt einen Bestaetigungs-Dialog: "Sie haben ungespeicherte Aenderungen. Moechten Sie die Seite wirklich verlassen?"
- Nutzer klickt "Abbrechen": Browser bleibt auf der Tank-Seite
- Nutzer klickt "Verlassen": Browser navigiert weg, Aenderungen gehen verloren

**Nachbedingungen**:
- Bei "Abbrechen": Tank-Daten unveraendert, Formular zeigt noch die Aenderung
- Bei "Verlassen": Alte Tank-Daten bleiben erhalten

**Tags**: [req-014, unsaved-changes, navigation, bearbeiten]

---

### TC-014-039: Name-Pflichtfeld-Validierung beim Bearbeiten

**Requirement**: REQ-014 § 3 Pydantic — `name: Field(min_length=1, max_length=100)`
**Priority**: Medium
**Category**: Formvalidierung
**Preconditions**:
- Nutzer ist auf TankDetailPage, Tab "Bearbeiten"

**Testschritte**:
1. Nutzer loescht den gesamten Inhalt des Felds "Name"
2. Nutzer klickt "Speichern"

**Erwartete Ergebnisse**:
- Fehlermarkierung am Feld "Name" erscheint
- Kein API-Aufruf wird ausgefuehrt
- Tank-Daten werden nicht gespeichert

**Nachbedingungen**:
- Tank-Name unveraendert

**Tags**: [req-014, formvalidierung, name, pflichtfeld, bearbeiten]

---

## 10. Tank loeschen

### TC-014-040: Tank loeschen mit Bestaetigungsdialog (Happy Path)

**Requirement**: REQ-014 § 3 `DELETE /tanks/{key}`; § 6 DoD "Tank-CRUD", "Loesch-Schutz"
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- Nutzer ist auf TankDetailPage eines Tanks, der KEINER aktiven Location zugeordnet ist

**Testschritte**:
1. Nutzer klickt "Loeschen" (rote Schaltflaeche mit Papierkorb-Icon)
2. Ein Bestaetigungsdialog erscheint
3. Nutzer klickt "Loeschen bestaetigen" (oder aequivalent)

**Erwartete Ergebnisse**:
- Dialog schliesst sich
- Browser navigiert zurueck zur Tank-Listenseite (`/standorte/tanks`)
- Erfolgsbenachrichtigung erscheint
- Geloeschter Tank ist in der Liste nicht mehr sichtbar

**Nachbedingungen**:
- Tank aus dem System entfernt

**Tags**: [req-014, loeschen, bestaetigungsdialog, happy-path]

---

### TC-014-041: Tank loeschen schlaegt fehl, wenn aktiv versorgend

**Requirement**: REQ-014 § 6 DoD "Loesch-Schutz"; Testszenario 7
**Priority**: Critical
**Category**: Fehlermeldung
**Preconditions**:
- Nutzer ist auf TankDetailPage von "Haupttank Grow Zelt 1"
- Tank versorgt aktiv die Location "Grow Zelt 1" mit mindestens 1 aktiven Pflanzen

**Testschritte**:
1. Nutzer klickt "Loeschen"
2. Bestaetigungsdialog erscheint
3. Nutzer klickt "Loeschen bestaetigen"

**Erwartete Ergebnisse**:
- Browser bleibt auf der Tank-Detailseite
- Eine Fehlermeldung erscheint (Snackbar oder Fehler-Alert): Tank kann nicht geloescht werden, da er eine aktive Location versorgt
- Tank existiert weiterhin im System

**Nachbedingungen**:
- Tank unveraendert im System, keine Daten geloescht

**Tags**: [req-014, loeschen, loesch-schutz, aktive-versorgung, fehlermeldung]

---

### TC-014-042: Loeschen-Dialog abbrechen erhalt Tank

**Requirement**: REQ-014 § 6 DoD "Tank-CRUD"
**Priority**: Low
**Category**: Dialog
**Preconditions**:
- Bestaetigungsdialog fuer Tank-Loeschung ist geoeffnet

**Testschritte**:
1. Nutzer klickt "Abbrechen" im Bestaetigungsdialog

**Erwartete Ergebnisse**:
- Dialog schliesst sich
- Tank-Detailseite bleibt unveraendert
- Kein Tank wird geloescht

**Nachbedingungen**:
- Keine Daten geaendert

**Tags**: [req-014, loeschen, abbrechen, dialog]

---

## 11. Sensor-Binding

### TC-014-043: Sensor dem Tank zuordnen (Happy Path)

**Requirement**: REQ-014 § 2 `monitors_tank`-Edge; § 6 DoD "Sensor-Binding via monitors_tank Edge"
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- Nutzer ist auf TankDetailPage, Tab "Details"
- Bereich "Sensoren" ist sichtbar

**Testschritte**:
1. Nutzer klickt "Sensor hinzufuegen" im Sensoren-Bereich
2. Dialog "Sensor hinzufuegen" oeffnet sich
3. Nutzer gibt "EC-Sonde Tank 1" in das Namensfeld ein
4. Nutzer waehlt "EC" im Dropdown "Parameter" (oder Metric Type)
5. Nutzer gibt "sensor.tank1_ec" in das Feld "HA Entity ID" ein
6. Nutzer klickt "Speichern"

**Erwartete Ergebnisse**:
- Dialog schliesst sich
- Erfolgsbenachrichtigung erscheint
- Sensoren-Tabelle zeigt neuen Eintrag: Name "EC-Sonde Tank 1", Parameter "ec", HA Entity ID "sensor.tank1_ec"

**Nachbedingungen**:
- Sensor im System gespeichert, `monitors_tank`-Edge zum Tank erstellt

**Tags**: [req-014, sensor, ha-entity-id, monitors-tank, sensor-binding]

---

### TC-014-044: Sensor bearbeiten und HA Entity ID aendern

**Requirement**: REQ-014 § 2 `monitors_tank`-Edge; § 6 DoD "Sensor-Binding"
**Priority**: Medium
**Category**: Happy Path
**Preconditions**:
- Nutzer ist auf TankDetailPage, Sensoren-Abschnitt zeigt 1 Sensor

**Testschritte**:
1. Nutzer klickt Bearbeiten-Icon in der Sensor-Zeile
2. Dialog oeffnet sich mit vorausgefuellten Werten
3. Nutzer aendert die HA Entity ID von "sensor.tank1_ec" auf "sensor.tank1_ec_v2"
4. Nutzer klickt "Speichern"

**Erwartete Ergebnisse**:
- Dialog schliesst sich
- Erfolgsbenachrichtigung erscheint
- Sensor-Zeile zeigt aktualisierte HA Entity ID "sensor.tank1_ec_v2"

**Nachbedingungen**:
- Sensor mit aktualisierter HA Entity ID im System

**Tags**: [req-014, sensor, bearbeiten, ha-entity-id]

---

### TC-014-045: Sensor loeschen mit Bestaetigungsdialog

**Requirement**: REQ-014 § 6 DoD "Sensor-Binding"
**Priority**: Medium
**Category**: Dialog
**Preconditions**:
- Nutzer ist auf TankDetailPage, Sensoren-Abschnitt zeigt 1 Sensor

**Testschritte**:
1. Nutzer klickt Loeschen-Icon in der Sensor-Zeile
2. Bestaetigungsdialog erscheint
3. Nutzer klickt "Bestaetigen"

**Erwartete Ergebnisse**:
- Dialog schliesst sich
- Erfolgsbenachrichtigung erscheint
- Sensoren-Tabelle ist leer, Hinweis "Kein Sensor zugeordnet" erscheint

**Nachbedingungen**:
- Sensor und `monitors_tank`-Edge aus dem System entfernt

**Tags**: [req-014, sensor, loeschen, bestaetigungsdialog]

---

## 12. Alert-System — Grenzwerte

### TC-014-046: pH-Alert bei pH ausserhalb des Tank-Typ-Bereichs (Naehrstofftank)

**Requirement**: REQ-014 § 3 `check_alerts` pH; § 6 DoD "Alert-System (differenziert)"
**Priority**: Critical
**Category**: Zustandswechsel
**Preconditions**:
- Nutzer ist auf TankDetailPage eines Naehrstofftanks (nutrient)
- TankState wird mit pH=7.5 (> 6.5 Obergrenze) manuell erfasst

**Testschritte**:
1. Nutzer erfasst neue Messung mit pH=7.5 auf dem Tab "Zustand"
2. Nutzer wechselt zu Tab "Details"

**Erwartete Ergebnisse**:
- Tab "Details" zeigt einen roten Alert (severity="error" oder "critical")
- Alert-Text enthaelt Hinweis: pH ausserhalb des Zielbereichs (5.5-6.5) fuer Tank-Typ "Naehrstofftank"

**Nachbedingungen**:
- TankState mit pH=7.5 gespeichert

**Tags**: [req-014, alert, pH, nutrient, grenzwert]

---

### TC-014-047: EC-Alert bei Abweichung >30% vom Ziel-EC

**Requirement**: REQ-014 § 3 `check_alerts` EC-Abweichung; § 6 DoD "EC relativ zum Ziel-EC"
**Priority**: High
**Category**: Zustandswechsel
**Preconditions**:
- Nutzer ist auf TankDetailPage eines Naehrstofftanks
- Letztes TankFillEvent hatte `target_ec_ms=1.8`
- Aktueller TankState hat `ec_ms=2.8` (Abweichung: 56% > 30%)

**Testschritte**:
1. Nutzer betrachtet Tab "Details"

**Erwartete Ergebnisse**:
- Ein Alert ist sichtbar fuer EC-Abweichung
- Alert-Text enthaelt prozentualen Abweichungswert und Richtung ("gestiegen")
- Alert-Severity ist "error" oder "warning" (hoch)

**Nachbedingungen**:
- Keine Daten geaendert

**Tags**: [req-014, alert, EC, abweichung, salzakkumulation]

---

### TC-014-048: Temperatur-Alert fuer Naehrstofftank bei >22°C

**Requirement**: REQ-014 § 3 `TEMP_THRESHOLDS nutrient warm_warning=22.0`; § 6 DoD "Temperatur differenziert"
**Priority**: High
**Category**: Detailansicht
**Preconditions**:
- Nutzer ist auf TankDetailPage eines Naehrstofftanks
- Aktueller TankState hat `water_temp_celsius=23.5`

**Testschritte**:
1. Nutzer betrachtet Tab "Details"

**Erwartete Ergebnisse**:
- Ein Alert mit oranger/gelber Severity ist sichtbar
- Alert-Text enthaelt Hinweis auf Pythium-Risiko und sinkenden Geloestsauerstoff
- Kein kritischer roter Alert (kritisch erst ab 26°C fuer nutrient-Typ)

**Nachbedingungen**:
- Keine Daten geaendert

**Tags**: [req-014, alert, temperatur, pythium, warm-warning]

---

### TC-014-049: Fuellstand-Alert bei <20% Restvolumen

**Requirement**: REQ-014 § 3 `check_alerts` Fuellstand; § 6 DoD "Fuellstandswarnung"
**Priority**: High
**Category**: Detailansicht
**Preconditions**:
- Nutzer ist auf TankDetailPage
- Aktueller TankState hat `fill_level_percent=15`

**Testschritte**:
1. Nutzer betrachtet Tab "Details"

**Erwartete Ergebnisse**:
- Ein Alert erscheint mit Hinweis "Fuellstand 15% — Nachfuellung erforderlich"
- Alert-Severity ist "error" oder "warning"

**Nachbedingungen**:
- Keine Daten geaendert

**Tags**: [req-014, alert, fuellstand, low-fill-level]

---

### TC-014-050: DO-Alert bei kritisch niedrigem Geloestsauerstoff (<4 mg/L)

**Requirement**: REQ-014 § 3 `check_alerts` DO; § 6 DoD "DO-Alerts fuer Hydroponik"
**Priority**: Critical
**Category**: Detailansicht
**Preconditions**:
- Nutzer ist auf TankDetailPage eines Naehrstofftanks
- Aktueller TankState hat `dissolved_oxygen_mgl=3.5`

**Testschritte**:
1. Nutzer betrachtet Tab "Details"

**Erwartete Ergebnisse**:
- Ein roter kritischer Alert erscheint
- Alert-Text enthaelt Hinweis auf anaerobe Bedingungen und akutes Pythium-Risiko
- Belueiftungs-Empfehlung im Alert-Text

**Nachbedingungen**:
- Keine Daten geaendert

**Tags**: [req-014, alert, dissolved-oxygen, DO, kritisch, anaerob, pythium]

---

### TC-014-051: ORP-Alert fuer Rezirkulationstank bei <250 mV

**Requirement**: REQ-014 § 3 `check_alerts` ORP; § 6 DoD "ORP-Alerts fuer Rezirkulation"
**Priority**: High
**Category**: Detailansicht
**Preconditions**:
- Nutzer ist auf TankDetailPage eines Rezirkulationstanks
- Aktueller TankState hat `orp_mv=200`

**Testschritte**:
1. Nutzer betrachtet Tab "Details"

**Erwartete Ergebnisse**:
- Ein Alert mit hoher Severity erscheint
- Alert-Text enthaelt Hinweis auf reduzierende Bedingungen und Pathogen-Risiko
- Desinfektion-Empfehlung ist im Alert-Text enthalten

**Nachbedingungen**:
- Keine Daten geaendert

**Tags**: [req-014, alert, ORP, rezirkulation, desinfektion]

---

## 13. Tank-Typ-Regeln

### TC-014-052: Rezirkulationstank-Zuweisung nur bei geschlossenem Bewaesserungssystem

**Requirement**: REQ-014 § 3 `TankAssignmentValidator`; § 6 DoD "Typ-Kompatibilitaet"; Testszenario 4
**Priority**: Critical
**Category**: Fehlermeldung
**Preconditions**:
- Dialog "Tank erstellen" ist geoeffnet
- Location "Beet A" mit `irrigation_system="drip"` (offenes System) existiert

**Testschritte**:
1. Nutzer waehlt "Rezirkulation" im Typ-Dropdown
2. Nutzer waehlt Standort der Location "Beet A"
3. Nutzer waehlt "Beet A" im Location-Dropdown
4. Nutzer gibt Name und Volumen ein
5. Nutzer klickt "Erstellen"

**Erwartete Ergebnisse**:
- Eine Fehlermeldung erscheint: Rezirkulationstank ist nur bei geschlossenen Systemen (hydro, nft, ebb_flow) erlaubt
- Kein Tank wird erstellt

**Nachbedingungen**:
- Kein Tank erstellt

**Tags**: [req-014, recirculation, typ-kompatibilitaet, validierung, fehlermeldung]

---

### TC-014-053: Stammloesung-Tank kann keiner Location direkt zugeordnet werden

**Requirement**: REQ-014 § 3 `TankAssignmentValidator`; § 6 DoD "Stock-Solution Tank-Typ"
**Priority**: High
**Category**: Fehlermeldung
**Preconditions**:
- Dialog "Tank erstellen" ist geoeffnet

**Testschritte**:
1. Nutzer waehlt "Stammloesung" im Typ-Dropdown
2. Nutzer waehlt eine beliebige Location
3. Nutzer klickt "Erstellen"

**Erwartete Ergebnisse**:
- Eine Fehlermeldung erscheint: Stammloesung-Tanks duerfen nicht direkt einer Location zugeordnet werden
- Kein Tank wird erstellt

**Nachbedingungen**:
- Kein Tank erstellt

**Tags**: [req-014, stock-solution, stammloesung, location-sperre, fehlermeldung]

---

### TC-014-054: Standard-Wartungsplaene fuer nutrient-Tank nach Erstellung

**Requirement**: REQ-014 § 3 `DEFAULT_MAINTENANCE_SCHEDULES['nutrient']`; § 6 DoD "Standard-Schedules"; Testszenario 6
**Priority**: High
**Category**: Zustandswechsel
**Preconditions**:
- Nutzer hat gerade einen Naehrstofftank (nutrient) erstellt

**Testschritte**:
1. Nutzer navigiert zur Detailseite des neuen Tanks
2. Nutzer wechselt zu Tab "Wartungsplaene"

**Erwartete Ergebnisse**:
- 5 Wartungsplaene sind automatisch erstellt worden:
  - Wasserwechsel: 7 Tage, Prioritaet "Hoch"
  - Reinigung: 30 Tage, Prioritaet "Mittel"
  - Desinfektion: 90 Tage, Prioritaet "Hoch"
  - Kalibrierung: 14 Tage, Prioritaet "Mittel"
  - Pumpeninspektion: 30 Tage, Prioritaet "Niedrig"
- Alle Plaene sind aktiv (grunes Chip "Aktiv")

**Nachbedingungen**:
- Keine Daten geaendert

**Tags**: [req-014, wartungsplaene, standard-schedules, nutrient]

---

## 14. Tank-Safety-Warnung

### TC-014-055: Befuellung mit nicht-tanksicherem Duenger erzeugt Warnung

**Requirement**: REQ-014 § 3 `validate_tank_safe_fertilizers`; § 6 DoD "Tank-Safety-Warnung"; Testszenario 14
**Priority**: High
**Category**: Fehlermeldung
**Preconditions**:
- Dialog "Befuellung dokumentieren" ist geoeffnet
- Im System existiert ein Duenger "Fischmehl-Suspension" mit `tank_safe=false`

**Testschritte**:
1. Nutzer befuellt ein optionales Duenger-Feld im Dialog mit "Fischmehl-Suspension" (falls Dünger-Eingabe im Dialog verfuegbar)
2. Nutzer klickt "Speichern"

**Erwartete Ergebnisse**:
- Befuellung wird gespeichert (keine Blockierung)
- Eine Warnung erscheint: "[Dünger-Name] ist nicht tank-sicher (organisch/Schwebstoffe) — manuelles Giessen per Giesskanne empfohlen"
- Empfehlung zur Verwendung von WateringEvent mit application_method='drench' ist sichtbar

**Nachbedingungen**:
- TankFillEvent gespeichert, Warnung protokolliert

**Tags**: [req-014, tank-safety, organisch, warnung, drench-empfehlung]

---

## 15. Giessvorgaenge (WateringEvent)

### TC-014-056: Ergaenzende Handduengung per Giesskanne dokumentieren

**Requirement**: REQ-014 § 1 "Ergaenzende manuelle Bewaesserung"; § 6 DoD "Ergaenzende Handduengung"; Testszenario 13
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- Nutzer ist auf einer Seite, die WateringEvent-Erstellung ermoeglicht (z.B. Pflanzdurchlauf-Detail oder dedizierter Giessbereich)
- Location "Grow Zelt 1" hat `irrigation_system='drip'` und zugeordneten Tank
- Slots "GROWZELT1_A1" und "GROWZELT1_A2" existieren

**Testschritte**:
1. Nutzer navigiert zu einem Bereich, der Giessvorgang-Dokumentation ermoeglicht
2. Nutzer waehlt Applikationsmethode "Drench (Giesskanne)"
3. Nutzer aktiviert "Ergaenzend zu automatischer Bewaesserung"
4. Nutzer gibt "1.5" L als Volumen ein
5. Nutzer waehlt Slots "GROWZELT1_A1" und "GROWZELT1_A2"
6. Nutzer waehlt "Regenwasser" als Wasserquelle
7. Nutzer klickt "Speichern"

**Erwartete Ergebnisse**:
- WateringEvent wird gespeichert
- Erfolgsbenachrichtigung erscheint
- Giesskhistorie der betroffenen Slots zeigt neuen Eintrag mit Methode "Drench", `is_supplemental=true`

**Nachbedingungen**:
- WateringEvent mit `application_method='drench', is_supplemental=true` im System
- FeedingEvents fuer jede Pflanze in den betroffenen Slots wurden automatisch erstellt

**Tags**: [req-014, watering-event, drench, supplemental, organisch]

---

### TC-014-057: Blattduengung (foliar) dokumentieren

**Requirement**: REQ-014 § 1 Applikationsmethoden; § 6 DoD "Applikationsmethoden"; Testszenario 15
**Priority**: Medium
**Category**: Happy Path
**Preconditions**:
- WateringEvent-Erstellungsbereich ist zugaenglich
- 3 Slots sind verfuegbar

**Testschritte**:
1. Nutzer waehlt Applikationsmethode "Foliar (Blattduengung)"
2. Nutzer gibt "0.3" L als Gesamtvolumen ein (0.1 L pro Slot bei 3 Slots)
3. Nutzer waehlt 3 Slots aus
4. Nutzer aktiviert "Ergaenzend"
5. Nutzer klickt "Speichern"

**Erwartete Ergebnisse**:
- WateringEvent wird ohne Warnung gespeichert (0.1 L/Slot < 0.5 L/Slot Warngrenze)
- Erfolgsbenachrichtigung erscheint
- Giessvorgaenge-Ansicht zeigt Foliar-Eintrag

**Nachbedingungen**:
- WateringEvent mit `application_method='foliar'` gespeichert

**Tags**: [req-014, watering-event, foliar, blattduengung]

---

### TC-014-058: Volumen-Warnung bei Blattduengung mit zu hohem Volumen pro Slot

**Requirement**: REQ-014 § 3 `record_watering_event` Foliar-Warnung; § 6 DoD "Volumen-Plausibilitaet"
**Priority**: Medium
**Category**: Fehlermeldung
**Preconditions**:
- WateringEvent-Erstellungsbereich ist zugaenglich
- Applikationsmethode "Foliar" ist ausgewaehlt
- 1 Slot ist ausgewaehlt

**Testschritte**:
1. Nutzer gibt "0.8" L als Gesamtvolumen ein (0.8 L/Slot > 0.5 L/Slot Warngrenze)
2. Nutzer klickt "Speichern"

**Erwartete Ergebnisse**:
- WateringEvent wird gespeichert (Warnung blockiert nicht)
- Warnung erscheint: Foliar-Volumen 0.8 L pro Slot ist sehr hoch (typisch 0.05-0.2 L pro Pflanze)

**Nachbedingungen**:
- WateringEvent gespeichert

**Tags**: [req-014, watering-event, foliar, volumen-warnung, plausibilitaet]

---

### TC-014-059: Validierungsfehler — is_supplemental=true mit fertigation nicht erlaubt

**Requirement**: REQ-014 § 3 `WateringEvent.validate_supplemental_not_fertigation`; § 6 DoD "Ergaenzende Handduengung"
**Priority**: High
**Category**: Formvalidierung
**Preconditions**:
- WateringEvent-Erstellungsbereich ist zugaenglich

**Testschritte**:
1. Nutzer waehlt Applikationsmethode "Fertigation (Tank/Tropfer)"
2. Nutzer aktiviert "Ergaenzend zu automatischer Bewaesserung"
3. Nutzer gibt Volumen und Slots ein
4. Nutzer klickt "Speichern"

**Erwartete Ergebnisse**:
- Eine Fehlermeldung erscheint: Ergaenzende Handduengung (supplemental) kann nicht Fertigation sein — verwende Drench, Foliar oder Top Dress
- WateringEvent wird NICHT gespeichert

**Nachbedingungen**:
- Kein WateringEvent erstellt

**Tags**: [req-014, formvalidierung, supplemental, fertigation, validierung]

---

## 16. Giessvorgaenge — Giesplan-Bestaetigungsflow

### TC-014-060: Giesplan-Task bestaetigen mit vollstaendigen Details

**Requirement**: REQ-014 § 3 `POST /watering-events/confirm`; § 6 DoD "Giesplan-Confirm"; Testszenario 19
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- Nutzer ist auf der Aufgabenliste (REQ-006) oder Pflanzdurchlauf-Seite
- Ein Giesstask "Tomaten Hochbeet A" mit Status "Ausstehend" ist vorhanden
- NutrientPlan "Tomato Heavy Coco" ist dem Pflanzdurchlauf zugewiesen

**Testschritte**:
1. Nutzer oeffnet den Giesstask "Tomaten Hochbeet A"
2. Nutzer klickt "Giessvorgang bestaetigen" (oder "Vollstaendige Bestaetigung")
3. Dialog oeffnet sich
4. Nutzer gibt "10.0" L als Volumen ein
5. Nutzer waehlt "Drench" als Methode
6. Nutzer gibt "1.75" als gemessenen EC und "5.9" als gemessenen pH ein
7. Nutzer aktiviert "Plan-Dosierungen verwenden"
8. Nutzer klickt "Speichern"

**Erwartete Ergebnisse**:
- WateringEvent wird erstellt (mit `task_key` als Rueckreferenz)
- Task-Status aendert sich auf "Abgeschlossen" (gruener Chip oder aequivalent)
- Erfolgsbenachrichtigung erscheint
- Response-Zusammenfassung zeigt: 18 FeedingEvents erstellt, Phasen-Aufschluesselung sichtbar

**Nachbedingungen**:
- WateringEvent gespeichert, FeedingEvents automatisch fuer alle Pflanzen erzeugt, Task abgeschlossen

**Tags**: [req-014, giesplan, confirm, task-completion, feeding-events, use-plan-dosages]

---

### TC-014-061: Giesplan-Quick-Confirm per Ein-Tap

**Requirement**: REQ-014 § 3 `POST /watering-events/quick-confirm`; § 6 DoD "Giesplan-Quick-Confirm"; Testszenario 20
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- Ein Giesstask ist vorhanden mit einem NutrientPlan, der volume_per_feeding und application_method als Defaults hat

**Testschritte**:
1. Nutzer oeffnet den Giesstask
2. Nutzer klickt "Schnell bestaetigen" (oder aequivalente Ein-Tap-Schaltflaeche)

**Erwartete Ergebnisse**:
- WateringEvent wird mit Plan-Defaults erstellt (ohne Dialog mit Detail-Eingaben)
- Task-Status wechselt auf "Abgeschlossen"
- Erfolgsbenachrichtigung erscheint mit Hinweis: "Standardwerte verwendet: [Methode], [Volumen] L aus Plan [Planname]"

**Nachbedingungen**:
- WateringEvent gespeichert, FeedingEvents erstellt, Task abgeschlossen

**Tags**: [req-014, giesplan, quick-confirm, ein-tap, plan-defaults]

---

### TC-014-062: Duplikat-Bestaetigung eines bereits abgeschlossenen Tasks abgelehnt

**Requirement**: REQ-014 § 3 Fehlerbehandlung `409`; § 6 DoD "Duplikat-Schutz"; Testszenario 21
**Priority**: High
**Category**: Fehlermeldung
**Preconditions**:
- Ein Giesstask hat Status "Abgeschlossen" (wurde bereits bestaetigt)

**Testschritte**:
1. Nutzer versucht denselben Task erneut zu bestaetigen (falls Bestaetigen-Schaltflaeche noch sichtbar)

**Erwartete Ergebnisse**:
- Eine Fehlermeldung erscheint: Task bereits abgeschlossen — Giessvorgang existiert bereits
- Kein zweites WateringEvent wird erstellt

**Nachbedingungen**:
- Daten unveraendert

**Tags**: [req-014, duplikat-schutz, task-completed, 409, fehlermeldung]

---

## 17. Wasserquellen-Kaskade

### TC-014-063: Wasserquellen-Defaults werden transparent angezeigt

**Requirement**: REQ-014 § 1 Wasserquellen-Defaults (Kaskade); § 6 DoD "Kaskade-Transparenz", "water_defaults_source"
**Priority**: Medium
**Category**: Detailansicht
**Preconditions**:
- Nutzer hat Dialog "Befuellung dokumentieren" geoeffnet
- Tank ist einer Location zugeordnet, die Site-WaterSource-Profil-Daten hat (TapWaterProfile)
- Kein NutrientPlan mit Mischverhaeltnis verknuepft

**Testschritte**:
1. Nutzer oeffnet Dialog "Befuellung dokumentieren"
2. Nutzer betrachtet die Wasserparameter-Felder

**Erwartete Ergebnisse**:
- Felder fuer `base_water_ec_ms`, Alkalinity, ggf. Chlorwerte sind vorausgefuellt
- Ein Hinweis oder Label neben den vorausgefuellten Feldern zeigt die Quelle: "Aus Standort-Profil" oder "Aus NutrientPlan"
- Nutzer kann die Werte manuell ueberschreiben

**Nachbedingungen**:
- Keine Daten geaendert

**Tags**: [req-014, wasserquellen-kaskade, defaults, transparenz, site-profil]

---

### TC-014-064: Mischverhaeltnis-Empfehlung bei water_source=mixed anwenden

**Requirement**: REQ-014 § 6 DoD "WaterMixCalculator-Integration"; TankFillCreateDialog WaterMixRecommendationBox
**Priority**: Medium
**Category**: Happy Path
**Preconditions**:
- Dialog "Befuellung dokumentieren" ist geoeffnet
- `siteKey` und `nutrientPlanKey` sind bekannt (Tank ist Location zugeordnet, Location hat NutrientPlan)
- Wasserquelle "Gemischt" ist ausgewaehlt

**Testschritte**:
1. Nutzer waehlt "Gemischt" als Wasserquelle
2. WaterMixRecommendationBox erscheint mit einer Empfehlung (z.B. "Empfehlung: 70% Osmose")
3. Nutzer klickt "Uebernehmen" in der Empfehlungsbox

**Erwartete Ergebnisse**:
- Das Feld "Osmose-Anteil (%)" wird mit dem empfohlenen Wert befuellt (z.B. "70")
- Nutzer kann den Wert noch manuell korrigieren

**Nachbedingungen**:
- Kein TankFillEvent erstellt

**Tags**: [req-014, water-mix, recommendation, osmose-anteil, uebernehmen]

---

## 18. Authentifizierung und Zugriffsschutz

### TC-014-065: Nicht-eingeloggter Nutzer wird zur Login-Seite weitergeleitet

**Requirement**: REQ-014 § 4 Authentifizierung; REQ-023
**Priority**: Critical
**Category**: Navigation
**Preconditions**:
- Kein Nutzer ist eingeloggt (kein gueltiges JWT)

**Testschritte**:
1. Nutzer navigiert direkt zu `/standorte/tanks`

**Erwartete Ergebnisse**:
- Browser leitet zu `/login` oder aequivalenter Authentifizierungsseite weiter
- Tank-Liste wird nicht angezeigt

**Nachbedingungen**:
- Keine Daten geaendert

**Tags**: [req-014, auth, zugriffsschutz, redirect-login]

---

### TC-014-066: Viewer-Rolle kann Tank nicht loeschen

**Requirement**: REQ-014 § 4 "Tanks: Loeschen = Admin"; REQ-024 RBAC
**Priority**: High
**Category**: Fehlermeldung
**Preconditions**:
- Nutzer ist eingeloggt mit Rolle "Viewer" (Lese-only)
- Tank-Detailseite ist geoeffnet

**Testschritte**:
1. Nutzer betrachtet die Tank-Detailseite

**Erwartete Ergebnisse**:
- Schaltflaeche "Loeschen" ist entweder nicht sichtbar ODER ist deaktiviert (disabled)
- Nutzer kann keine Loeschaktion ausloesen

**Nachbedingungen**:
- Keine Daten geaendert

**Tags**: [req-014, rbac, viewer, loeschen-gesperrt, zugriffsschutz]

---

## 19. Edge Cases und Grenzwerte

### TC-014-067: Befuellung Volumen-Grenzwert (Minimum 0.1 L)

**Requirement**: REQ-014 § 3 `TankFillEvent.volume_liters: float = Field(gt=0)`; TankFillCreateDialog `min={0.1}`
**Priority**: Medium
**Category**: Formvalidierung
**Preconditions**:
- Dialog "Befuellung dokumentieren" ist geoeffnet

**Testschritte**:
1. Nutzer gibt "0" in das Feld "Volumen (L)" ein
2. Nutzer klickt "Speichern"

**Erwartete Ergebnisse**:
- Fehlermarkierung am Volumen-Feld
- Hinweis auf Mindestwert (Volumen muss groesser als 0 sein)
- Kein TankFillEvent wird erstellt

**Nachbedingungen**:
- Kein neues TankFillEvent

**Tags**: [req-014, formvalidierung, volumen, grenzwert, minimum]

---

### TC-014-068: pH-Grenzwerte im Zustandsformular (0-14)

**Requirement**: REQ-014 § 3 `TankStateRecord.ph: Optional[float] = Field(None, ge=0, le=14)`
**Priority**: Medium
**Category**: Formvalidierung
**Preconditions**:
- Dialog "Messung erfassen" ist geoeffnet

**Testschritte**:
1. Nutzer gibt "15" in das pH-Feld ein (> 14 Maximum)
2. Nutzer klickt "Speichern"

**Erwartete Ergebnisse**:
- Fehlermarkierung am pH-Feld
- Hinweis auf Maximalwert (pH darf nicht groesser als 14 sein)
- Kein TankState wird erstellt

**Nachbedingungen**:
- Kein neuer TankState

**Tags**: [req-014, formvalidierung, pH, grenzwert, maximum]

---

### TC-014-069: Befuellung — Korrektur (adjustment) gueltig mit Ziel-pH

**Requirement**: REQ-014 § 3 `validate_adjustment_has_target`; Testszenario 10
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- Dialog "Befuellung dokumentieren" ist geoeffnet

**Testschritte**:
1. Nutzer waehlt "Korrektur" als Befuellungstyp
2. Nutzer gibt "0.5" L als Volumen ein
3. Nutzer gibt "5.8" als Ziel-pH ein (Ziel-EC bleibt leer)
4. Nutzer gibt "5.7" als gemessenen pH ein
5. Nutzer klickt "Speichern"

**Erwartete Ergebnisse**:
- Dialog schliesst sich ohne Fehlermeldung
- Erfolgsbenachrichtigung erscheint
- Befuellungs-Tabelle zeigt neuen Eintrag: Typ "Korrektur", 0.5 L

**Nachbedingungen**:
- TankFillEvent mit `fill_type='adjustment', target_ph=5.8` gespeichert

**Tags**: [req-014, befuellung, korrektur, adjustment, ziel-ph, happy-path]

---

### TC-014-070: Netzwerkfehler bei Tank-Laden zeigt Fehlerzustand

**Requirement**: REQ-014 allgemein — Fehlerbehandlung
**Priority**: Medium
**Category**: Fehlermeldung
**Preconditions**:
- Nutzer navigiert zur Tank-Detailseite eines Tanks
- Netzwerkverbindung ist unterbrochen oder Server nicht erreichbar

**Testschritte**:
1. Nutzer navigiert zu `/standorte/tanks/tank_zelt1` waehrend Server nicht erreichbar

**Erwartete Ergebnisse**:
- Statt der normalen Seite erscheint eine Fehleranzeige (ErrorDisplay-Komponente)
- Fehlermeldung ist benutzerfreundlich (kein technischer Stack-Trace)
- Seite bietet ggf. eine Option zum erneuten Laden

**Nachbedingungen**:
- Keine Daten geaendert

**Tags**: [req-014, fehlerbehandlung, netzwerkfehler, error-display]

---

### TC-014-071: Vollwechsel mit weniger als 50% des Tank-Volumens zeigt Warnung

**Requirement**: REQ-014 § 3 `record_fill_event` Vollwechsel-Plausibilitaet
**Priority**: Medium
**Category**: Fehlermeldung
**Preconditions**:
- Dialog "Befuellung dokumentieren" ist fuer 50-L-Tank geoeffnet
- "Vollwechsel" ist als Befuellungstyp ausgewaehlt

**Testschritte**:
1. Nutzer gibt "20" L als Volumen ein (= 40% des Tank-Volumens, < 50%)
2. Nutzer klickt "Speichern"

**Erwartete Ergebnisse**:
- TankFillEvent wird gespeichert (Warnung blockiert nicht)
- Warnung erscheint: Vollwechsel mit nur 20 L bei 50 L Tank — wirklich Vollwechsel?

**Nachbedingungen**:
- TankFillEvent gespeichert

**Tags**: [req-014, befuellung, vollwechsel, volumen-warnung, plausibilitaet]

---

### TC-014-072: Tank-Typ-Anzeige in Liste und Detail ist uebersetzt

**Requirement**: REQ-014 § 6 DoD "Tank-Typen"; i18n
**Priority**: Low
**Category**: Listenansicht
**Preconditions**:
- Tanks verschiedener Typen sind im System vorhanden

**Testschritte**:
1. Nutzer navigiert zu `/standorte/tanks`
2. Nutzer betrachtet die "Typ"-Spalte in der Tabelle

**Erwartete Ergebnisse**:
- "nutrient" wird als "Naehrstoffloesung" angezeigt
- "irrigation" wird als "Giesswasser" angezeigt
- "reservoir" wird als "Vorratstank" oder "Reservoir" angezeigt
- "recirculation" wird als "Rezirkulation" angezeigt
- "stock_solution" wird als "Stammloesung" angezeigt

**Nachbedingungen**:
- Keine Daten geaendert

**Tags**: [req-014, i18n, uebersetzung, tank-typ, liste]

---

## Abdeckungs-Matrix

| Spec-Abschnitt | Beschreibung | Test-Cases |
|---|---|---|
| § 1 Business Case — Tank als Infrastruktur | Tank-Typen, Pflicht-Tank bei automatischer Bewaesserung | TC-014-052, TC-014-053, TC-014-072 |
| § 1 Business Case — Befuellungshistorie | TankFillEvent, Typen, Soll/Ist | TC-014-031 bis TC-014-036, TC-014-069, TC-014-071 |
| § 1 Business Case — Wasserquellen-Kaskade | 4-stufige Kaskade, water_defaults_source | TC-014-063, TC-014-064, TC-014-034 |
| § 1 Business Case — WateringEvent | Applikationsmethoden, supplemental | TC-014-056 bis TC-014-059 |
| § 1 Business Case — Zustandsueberwachung / Alerts | pH, EC, Temp, DO, ORP, Fuellstand, Algenrisiko | TC-014-013, TC-014-014, TC-014-046 bis TC-014-051 |
| § 2 Datenmodell — Tank-Nodes | TankDefinition, TankState, TankFillEvent, WateringEvent | TC-014-006, TC-014-019, TC-014-022 |
| § 3 Pydantic-Modelle — Validierung | Pflichtfelder, Grenzwerte, model_validators | TC-014-007, TC-014-021, TC-014-033, TC-014-059, TC-014-067, TC-014-068 |
| § 3 Tank-Service — Wartungslogik | MaintenanceSchedule, default schedules, fällige Wartungen | TC-014-023 bis TC-014-030, TC-014-054 |
| § 3 Tank-Service — Befuellungs-Warnungen | Volumen-Plausibilitaet, EC/pH-Abweichung, Chlor/Safety | TC-014-032, TC-014-035, TC-014-055, TC-014-071 |
| § 3 REST-API — Tank CRUD | Erstellen, Lesen, Aktualisieren, Loeschen | TC-014-001 bis TC-014-009, TC-014-037 bis TC-014-042 |
| § 3 REST-API — Zustandsmessungen | States, Alerts, Latest | TC-014-019 bis TC-014-022 |
| § 3 REST-API — Giesplan-Confirm | confirm, quick-confirm, Duplikat-Schutz | TC-014-060 bis TC-014-062 |
| § 3 Sensor-Binding — monitors_tank | Sensor anlegen, bearbeiten, loeschen | TC-014-043 bis TC-014-045 |
| § 3 Live-Query — HA-Direktanbindung | Live-Werte, Freshness, Messung uebernehmen | TC-014-016 bis TC-014-018 |
| § 3 Datenherkunft-Kennzeichnung | Source-Badge (Manual/HA/MQTT), Freshness-Indikator | TC-014-012, TC-014-016, TC-014-018 |
| § 4 Authentifizierung & Autorisierung | Login-Schutz, RBAC Viewer/Admin | TC-014-065, TC-014-066 |
| § 6 DoD — Vollstaendigkeit | Alle Must-Anforderungen aus der Definition of Done | Verteilt auf alle TC-014-XXX |
| Testszenarien 1-24 aus Spec § 6 | Alle formalen Szenarien abgedeckt | TC-014-032, -033, -035, -036, -046 bis TC-014-055 |
