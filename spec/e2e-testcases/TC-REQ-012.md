---
req_id: REQ-012
title: Stammdaten-Import via CSV-Upload
category: Stammdaten / Import
test_count: 54
coverage_areas:
  - Upload-Formular (Schritt 1 — Datei hochladen)
  - Entitätstyp-Auswahl (Species, Cultivar, BotanicalFamily)
  - Duplikatstrategie-Auswahl (skip / update / fail)
  - Dateiauswahl und Dateivalidierung (Größe, Typ, Encoding)
  - CSV-Template herunterladen
  - Vorschau-Tabelle (Schritt 2 — Vorschau)
  - Zeilenstatus-Anzeige (grün/rot/gelb Chips)
  - Fehlerdetails per Tooltip
  - Zusammenfassungs-Statistiken (Gesamt/Gültig/Fehler/Duplikate)
  - Import bestätigen (Schritt 2 → Schritt 3)
  - Ergebnis-Anzeige (Schritt 3 — Ergebnis)
  - Ergebnis-Statistiken (Erstellt/Aktualisiert/Übersprungen/Fehlgeschlagen)
  - Neuer Import (Reset-Fluss)
  - Stepper-Navigation (3 Schritte)
  - Fehlerbehandlung (Upload-Fehler, Serverfehler)
  - Sicherheitsregeln (Dateigröße, MIME-Type, Rate-Limit)
  - Feeding-Chart-Import (NutrientPlan via CSV/JSON)
  - Community-Templates (vorinstallierte Feeding-Charts)
  - Template-Klonen (Community-Templates als Ausgangsbasis)
  - Import-Historie (Übersicht vergangener Jobs)
  - Navigations-Sidebar-Eintrag
generated: 2026-03-21
version: "1.0"
---

# TC-REQ-012: Stammdaten-Import via CSV-Upload

Dieses Dokument enthaelt End-to-End-Testfaelle aus **REQ-012 Stammdaten-Import via CSV-Upload v1.0**, ausschliesslich aus der Perspektive eines Nutzers im Browser. Keine API-Calls, HTTP-Statuscodes oder Datenbankabfragen erscheinen in diesen Testfaellen. Alle Aussagen beschreiben, was der Nutzer sieht, anklickt, eintippt und auf dem Bildschirm erwartet.

Der Import folgt einem **3-Schritt-Prozess** (Stepper): Schritt 1 = Datei hochladen, Schritt 2 = Vorschau pruefen, Schritt 3 = Ergebnis. Die Import-Seite ist erreichbar unter `/stammdaten/import` (Sidebar-Menüpunkt "Import" unter "Stammdaten").

Die UI-Sprache ist **Deutsch** (Standard-Locale). Alle Labels, Buttons und Meldungen referenzieren die deutschen i18n-Texte.

---

## 1. Navigation zur Import-Seite

### TC-012-001: Sidebar-Menüeintrag "Import" navigiert zur Upload-Seite

**Requirement**: REQ-012 §4.6 — Navigation
**Priority**: Critical
**Category**: Navigation
**Preconditions**:
- Nutzer ist als Admin eingeloggt und befindet sich auf einer beliebigen Seite der App
- Sidebar ist sichtbar

**Testschritte**:
1. Nutzer öffnet die Sidebar (falls noch nicht sichtbar)
2. Nutzer klickt auf den Menüpunkt "Import" unter der Sektion "Stammdaten"

**Erwartete Ergebnisse**:
- Browser navigiert zu `/stammdaten/import`
- Die Seite trägt den Titel "Stammdaten-Import"
- Der 3-stufige Stepper ist sichtbar mit den Schritten "Datei hochladen", "Vorschau", "Ergebnis"
- Schritt 1 ("Datei hochladen") ist aktiv markiert
- Das Upload-Formular ist sichtbar

**Nachbedingungen**:
- Nutzer befindet sich auf `/stammdaten/import`

**Tags**: [req-012, navigation, sidebar, import-page]

---

### TC-012-002: Direkte Navigation zur Import-Seite per URL

**Requirement**: REQ-012 §4.1 — Upload-Dialog
**Priority**: High
**Category**: Navigation
**Preconditions**:
- Nutzer ist als Admin eingeloggt

**Testschritte**:
1. Nutzer gibt `/stammdaten/import` direkt in die Browser-Adressleiste ein und drückt Enter

**Erwartete Ergebnisse**:
- Import-Seite wird geladen
- Titel "Stammdaten-Import" ist sichtbar
- Stepper zeigt Schritt 1 ("Datei hochladen") als aktiv an
- Kein Fehler oder Redirect

**Nachbedingungen**:
- Nutzer befindet sich auf der Import-Seite, Schritt 1

**Tags**: [req-012, navigation, direct-url]

---

## 2. Upload-Schritt (Schritt 1): Formular-Anzeige und Grundfunktionen

### TC-012-003: Upload-Formular zeigt alle Pflichtfelder mit Standardwerten

**Requirement**: REQ-012 §4.1 — Upload-Dialog
**Priority**: Critical
**Category**: Listenansicht
**Preconditions**:
- Nutzer befindet sich auf der Import-Seite, Schritt 1 ("Datei hochladen")

**Testschritte**:
1. Nutzer betrachtet das Upload-Formular

**Erwartete Ergebnisse**:
- Dropdown "Datentyp" ist sichtbar, Standardwert "Pflanzenarten" (Species) ist vorausgewählt
- Dropdown "Duplikat-Behandlung" ist sichtbar, Standardwert "Überspringen" ist vorausgewählt
- Schaltfläche "CSV-Datei auswählen" ist sichtbar (noch keine Datei ausgewählt)
- Link/Button "Vorlage herunterladen" ist sichtbar
- Schaltfläche "Hochladen" ist sichtbar, aber deaktiviert (da noch keine Datei ausgewählt)

**Nachbedingungen**:
- Keine Statusänderung

**Tags**: [req-012, upload-form, default-values, happy-path]

---

### TC-012-004: Datentyp-Dropdown zeigt alle drei Entitätsoptionen

**Requirement**: REQ-012 §1.1, §4.1 — Unterstützte Entitäten
**Priority**: Critical
**Category**: Formvalidierung
**Preconditions**:
- Nutzer befindet sich auf der Import-Seite, Schritt 1

**Testschritte**:
1. Nutzer klickt auf das Dropdown "Datentyp"

**Erwartete Ergebnisse**:
- Das Dropdown öffnet sich
- Drei Optionen sind sichtbar: "Pflanzenarten", "Sorten", "Pflanzenfamilien"
- "Pflanzenarten" ist als aktuell ausgewählte Option markiert

**Nachbedingungen**:
- Dropdown-Zustand unverändert

**Tags**: [req-012, entity-type, dropdown, species, cultivar, botanical-family]

---

### TC-012-005: Duplikatstrategie-Dropdown zeigt alle drei Strategien

**Requirement**: REQ-012 §1.2 — Duplikatbehandlung
**Priority**: High
**Category**: Formvalidierung
**Preconditions**:
- Nutzer befindet sich auf der Import-Seite, Schritt 1

**Testschritte**:
1. Nutzer klickt auf das Dropdown "Duplikat-Behandlung"

**Erwartete Ergebnisse**:
- Das Dropdown öffnet sich
- Drei Optionen sind sichtbar: "Überspringen", "Aktualisieren", "Fehler melden"
- "Überspringen" ist als Standard vorausgewählt

**Nachbedingungen**:
- Keine Änderung

**Tags**: [req-012, duplicate-strategy, dropdown, skip, update, fail]

---

### TC-012-006: Upload-Button ist deaktiviert solange keine Datei ausgewählt ist

**Requirement**: REQ-012 §4.1 — Verhalten
**Priority**: High
**Category**: Formvalidierung
**Preconditions**:
- Nutzer befindet sich auf der Import-Seite, Schritt 1
- Keine Datei ausgewählt

**Testschritte**:
1. Nutzer betrachtet die Schaltfläche "Hochladen"
2. Nutzer versucht, auf "Hochladen" zu klicken

**Erwartete Ergebnisse**:
- Die Schaltfläche "Hochladen" ist deaktiviert (disabled-Zustand sichtbar)
- Ein Klick auf die deaktivierte Schaltfläche löst keine Aktion aus
- Kein Upload-Prozess wird gestartet

**Nachbedingungen**:
- Keine Statusänderung

**Tags**: [req-012, upload-button, disabled, no-file]

---

### TC-012-007: CSV-Template-Download für Entitätstyp "Pflanzenarten"

**Requirement**: REQ-012 §4.1, §3.1 — CSV-Templates
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- Nutzer befindet sich auf der Import-Seite, Schritt 1
- "Datentyp" ist auf "Pflanzenarten" eingestellt

**Testschritte**:
1. Nutzer klickt auf den Button/Link "Vorlage herunterladen"

**Erwartete Ergebnisse**:
- Browser startet einen Download
- Die heruntergeladene Datei heisst `species_template.csv`
- Die CSV-Datei enthält eine Header-Zeile mit den Spalten: `scientific_name`, `common_names`, `family`, `genus`, `cycle_type`, `photoperiod_type`, `growth_habit`, `root_type`, `hardiness_zones`, `allelopathy_score`, `native_habitat`
- Mindestens eine Beispielzeile ist enthalten (z.B. "Solanum lycopersicum")

**Nachbedingungen**:
- Datei wurde auf dem lokalen Rechner des Nutzers gespeichert

**Tags**: [req-012, template-download, species, csv-template]

---

### TC-012-008: CSV-Template-Download wechselt mit Datentyp-Dropdown

**Requirement**: REQ-012 §4.1 — Template-Download je Entität
**Priority**: Medium
**Category**: Happy Path
**Preconditions**:
- Nutzer befindet sich auf der Import-Seite, Schritt 1

**Testschritte**:
1. Nutzer wählt "Sorten" im Dropdown "Datentyp"
2. Nutzer klickt auf "Vorlage herunterladen"

**Erwartete Ergebnisse**:
- Browser lädt eine Datei mit dem Namen `cultivar_template.csv` herunter
- Die CSV-Datei enthält eine Header-Zeile mit: `name`, `parent_species`, `breeder`, `breeding_year`, `traits`, `days_to_maturity`, `disease_resistances`, `patent_status`

**Nachbedingungen**:
- Cultivar-Template auf lokalem Rechner gespeichert

**Tags**: [req-012, template-download, cultivar, csv-template]

---

### TC-012-009: CSV-Template-Download für "Pflanzenfamilien"

**Requirement**: REQ-012 §4.1 — Template-Download
**Priority**: Medium
**Category**: Happy Path
**Preconditions**:
- Nutzer befindet sich auf der Import-Seite, Schritt 1

**Testschritte**:
1. Nutzer wählt "Pflanzenfamilien" im Dropdown "Datentyp"
2. Nutzer klickt auf "Vorlage herunterladen"

**Erwartete Ergebnisse**:
- Browser lädt eine Datei mit dem Namen `botanical_family_template.csv` herunter
- Die CSV-Datei enthält die Spalten: `name`, `typical_nutrient_demand`, `common_pests`, `rotation_category`

**Nachbedingungen**:
- BotanicalFamily-Template gespeichert

**Tags**: [req-012, template-download, botanical-family, csv-template]

---

### TC-012-010: Dateiauswahl per Klick zeigt Dateinamen im Button

**Requirement**: REQ-012 §4.1 — Dateiauswahl-Dialog
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- Nutzer befindet sich auf der Import-Seite, Schritt 1
- Eine gültige CSV-Datei (z.B. `species_valid.csv`, kleiner als 10 MB) liegt auf dem lokalen Rechner bereit

**Testschritte**:
1. Nutzer klickt auf die Schaltfläche "CSV-Datei auswählen"
2. Dateiauswahl-Dialog öffnet sich
3. Nutzer wählt die Datei `species_valid.csv` aus
4. Nutzer bestätigt die Auswahl im Dateiauswahl-Dialog

**Erwartete Ergebnisse**:
- Der Text auf der Schaltfläche wechselt von "CSV-Datei auswählen" zu `species_valid.csv` (der Dateiname wird angezeigt)
- Die Schaltfläche "Hochladen" wird aktiviert (nicht mehr disabled)

**Nachbedingungen**:
- Datei ist zur Übertragung ausgewählt, aber noch nicht hochgeladen

**Tags**: [req-012, file-select, file-button, filename-display]

---

## 3. Upload und Zwei-Phasen-Prozess (Schritt 1 → Schritt 2)

### TC-012-011: Erfolgreicher Upload einer gültigen Species-CSV leitet zur Vorschau weiter

**Requirement**: REQ-012 §7 Szenario 1 — Erfolgreicher Species-Import
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- Nutzer befindet sich auf der Import-Seite, Schritt 1
- CSV-Datei `species_valid.csv` mit 10 gültigen Species-Zeilen (korrekte Header, alle Pflichtfelder ausgefüllt, keine Duplikate im System) ist ausgewählt
- Datentyp "Pflanzenarten" ist gewählt, Strategie "Überspringen"

**Testschritte**:
1. Nutzer klickt auf "Hochladen"
2. Nutzer wartet auf die Serverantwort

**Erwartete Ergebnisse**:
- Während des Uploads zeigt der "Hochladen"-Button einen Ladeindikator oder ist deaktiviert
- Nach erfolgreichem Upload: Stepper springt automatisch auf Schritt 2 ("Vorschau")
- Die Vorschau-Ansicht wird angezeigt
- Dateiname und Zeilenanzahl sind sichtbar (z.B. "Datei: species_valid.csv — 10 Zeilen")
- Die Vorschau-Tabelle zeigt alle 10 Zeilen
- Alle 10 Zeilen tragen den Status-Chip "valid" (grün)
- Die Schaltfläche "Import bestätigen" ist aktiv

**Nachbedingungen**:
- Import-Job wurde serverseitig erstellt, Nutzer befindet sich in Schritt 2

**Tags**: [req-012, upload-success, preview, step-transition, species, happy-path]

---

### TC-012-012: Vorschau zeigt farbcodierte Status-Chips pro Zeile

**Requirement**: REQ-012 §4.2 — Preview-Tabelle, Farbkodierung
**Priority**: Critical
**Category**: Listenansicht
**Preconditions**:
- Nutzer befindet sich auf der Import-Seite, Schritt 2 (Vorschau)
- Hochgeladene CSV enthält mindestens: 2 gültige Zeilen, 1 ungültige Zeile (fehlende Pflichtfeld), 1 Duplikat-Zeile

**Testschritte**:
1. Nutzer betrachtet die Vorschau-Tabelle

**Erwartete Ergebnisse**:
- Gültige Zeilen zeigen einen grünen Chip (Label "valid")
- Ungültige Zeilen zeigen einen roten Chip (Label "invalid")
- Duplikat-Zeilen zeigen einen gelben Chip (Label "duplicate")
- Die Fehler-Spalte zeigt bei ungültigen Zeilen einen roten Chip mit Fehleranzahl (z.B. "1 Fehler")
- Ein Mouseover/Tooltip auf dem Fehler-Chip zeigt die Feldnamen und Fehlermeldungen (z.B. "scientific_name: scientific_name ist ein Pflichtfeld")

**Nachbedingungen**:
- Keine Statusänderung

**Tags**: [req-012, preview-table, color-coding, status-chips, tooltip, error-details]

---

### TC-012-013: Vorschau-Zusammenfassung zeigt korrekte Statistiken

**Requirement**: REQ-012 §4.2, DoD — Zusammenfassung "X gültig, Y fehlerhaft, Z Duplikate"
**Priority**: High
**Category**: Listenansicht
**Preconditions**:
- Nutzer befindet sich auf der Import-Seite, Schritt 2 (Vorschau)
- Hochgeladene CSV hat 150 Zeilen: 142 gültig, 5 fehlerhaft, 3 Duplikate

**Testschritte**:
1. Nutzer betrachtet den Zusammenfassungsbereich oberhalb der Vorschau-Tabelle

**Erwartete Ergebnisse**:
- Vier Kennzahlen-Kacheln sind sichtbar:
  - "150" mit Beschriftung "Gesamt" (oder ähnlich)
  - "142" mit Beschriftung "Gültig"
  - "5" mit Beschriftung "Fehler"
  - "3" mit Beschriftung "Duplikate"
- Die Werte stimmen mit der Vorschau-Tabelle überein

**Nachbedingungen**:
- Keine Statusänderung

**Tags**: [req-012, preview-statistics, summary, valid-rows, invalid-rows, duplicates]

---

### TC-012-014: "Import bestätigen"-Button zeigt Anzahl der zu importierenden Datensätze

**Requirement**: REQ-012 §4.2 — Button-Beschriftung mit Anzahl
**Priority**: High
**Category**: Listenansicht
**Preconditions**:
- Nutzer befindet sich auf der Import-Seite, Schritt 2 (Vorschau)
- Vorschau zeigt 142 gültige Zeilen, 5 fehlerhafte, 3 Duplikate (Strategie: skip)

**Testschritte**:
1. Nutzer betrachtet die Schaltfläche "Import bestätigen"

**Erwartete Ergebnisse**:
- Die Schaltfläche "Import bestätigen" ist aktiv (nicht disabled)
- Die Schaltfläche zeigt die Anzahl der tatsächlich zu importierenden Datensätze an (z.B. "Import bestätigen (142)" oder "Import bestätigen")
- Die Schaltfläche ist aktiv, da `valid_rows > 0`

**Nachbedingungen**:
- Keine Statusänderung

**Tags**: [req-012, confirm-button, row-count, active-state]

---

### TC-012-015: "Import bestätigen"-Button ist deaktiviert wenn keine gültigen Zeilen vorhanden

**Requirement**: REQ-012 §4.2 — Button nur aktiv wenn valid_rows > 0
**Priority**: High
**Category**: Formvalidierung
**Preconditions**:
- Nutzer befindet sich auf der Import-Seite, Schritt 2 (Vorschau)
- Vorschau zeigt 0 gültige Zeilen (alle Zeilen haben Validierungsfehler)

**Testschritte**:
1. Nutzer betrachtet die Schaltfläche "Import bestätigen"
2. Nutzer versucht, auf "Import bestätigen" zu klicken

**Erwartete Ergebnisse**:
- Die Schaltfläche "Import bestätigen" ist deaktiviert (disabled-Zustand)
- Kein Import wird gestartet

**Nachbedingungen**:
- Nutzer bleibt auf Schritt 2, kein Fortschritt

**Tags**: [req-012, confirm-button, disabled, no-valid-rows]

---

### TC-012-016: "Zurück"-Button in der Vorschau wechselt zurück zu Schritt 1

**Requirement**: REQ-012 §4.2 — Abbrechen/Zurück in Preview
**Priority**: Medium
**Category**: Navigation
**Preconditions**:
- Nutzer befindet sich auf der Import-Seite, Schritt 2 (Vorschau)

**Testschritte**:
1. Nutzer klickt auf die Schaltfläche "Zurück" (oder "Abbrechen") in der Vorschau

**Erwartete Ergebnisse**:
- Stepper springt zurück auf Schritt 1 ("Datei hochladen")
- Das Upload-Formular ist wieder sichtbar
- Die Vorschau-Tabelle ist nicht mehr sichtbar
- Der aktuelle Import-Job wird verworfen (clearCurrentJob)
- Dateiauswahl-Button zeigt wieder "CSV-Datei auswählen" (keine Datei ausgewählt)

**Nachbedingungen**:
- Nutzer befindet sich auf Schritt 1, kein offener Import-Job

**Tags**: [req-012, back-button, step-navigation, cancel-preview]

---

## 4. Import bestätigen und Ergebnis-Anzeige (Schritt 2 → Schritt 3)

### TC-012-017: Bestätigung eines vollständig gültigen Species-Imports

**Requirement**: REQ-012 §7 Szenario 1 — Erfolgreicher Species-Import
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- Nutzer befindet sich auf der Import-Seite, Schritt 2 (Vorschau)
- Alle 10 Zeilen sind gültig (grüne Chips), keine Duplikate, Strategie: Überspringen

**Testschritte**:
1. Nutzer klickt auf "Import bestätigen"
2. Nutzer wartet auf den Abschluss des Imports

**Erwartete Ergebnisse**:
- Während des Imports zeigt die Schaltfläche einen Ladeindikator oder ist deaktiviert
- Nach Abschluss springt der Stepper auf Schritt 3 ("Ergebnis")
- Die Ergebnis-Ansicht zeigt den Titel "Import abgeschlossen"
- Folgender Chip ist sichtbar: "Erstellt: 10" (grün)
- Chip "Übersprungen: 0" ist sichtbar
- Chip "Fehlgeschlagen: 0" ist sichtbar
- Es gibt keine Fehler-Warnung (kein roter Alert)

**Nachbedingungen**:
- 10 neue Species-Einträge sind im System gespeichert
- Nutzer befindet sich auf Schritt 3

**Tags**: [req-012, confirm-import, result-page, records-created, happy-path, species]

---

### TC-012-018: Ergebnis zeigt Fehlerdetails wenn records_failed > 0

**Requirement**: REQ-012 §4.3 — Ergebnis-Anzeige mit Fehlerdetails
**Priority**: High
**Category**: Fehlermeldung
**Preconditions**:
- Nutzer befindet sich auf der Import-Seite, Schritt 2 (Vorschau)
- CSV enthält 2 gültige Zeilen und 5 fehlerhaftige Zeilen
- Nutzer hat "Import bestätigen" geklickt und Import ist abgeschlossen (Schritt 3)

**Testschritte**:
1. Nutzer betrachtet die Ergebnis-Seite in Schritt 3

**Erwartete Ergebnisse**:
- Chip "Erstellt: 2" ist sichtbar (grün)
- Chip "Fehlgeschlagen: 5" ist sichtbar (rot)
- Unterhalb der Statistiken ist ein Warn-Alert oder eine Fehler-Tabelle sichtbar
- Die Fehlerdetails zeigen mindestens: Zeilennummer, Feldname, Fehlermeldung
- (z.B. "Zeile 2 — scientific_name: scientific_name ist ein Pflichtfeld")

**Nachbedingungen**:
- 2 gültige Einträge wurden gespeichert; fehlerhafte Zeilen wurden übersprungen

**Tags**: [req-012, result-page, error-details, records-failed, warning-alert]

---

### TC-012-019: "Neuer Import"-Button auf der Ergebnis-Seite setzt Prozess zurück

**Requirement**: REQ-012 §4.3 — "Neuer Import" navigiert zurück zu Schritt 1
**Priority**: High
**Category**: Navigation
**Preconditions**:
- Nutzer befindet sich auf der Import-Seite, Schritt 3 (Ergebnis)

**Testschritte**:
1. Nutzer klickt auf "Neuer Import"

**Erwartete Ergebnisse**:
- Stepper springt zurück auf Schritt 1 ("Datei hochladen")
- Das Upload-Formular ist wieder vollständig leer
- Dateiauswahl zeigt "CSV-Datei auswählen"
- Datentyp und Strategie sind auf Standardwerte zurückgesetzt
- Die bisherigen Ergebnis-Daten sind nicht mehr sichtbar

**Nachbedingungen**:
- Nutzer befindet sich auf Schritt 1, bereit für einen neuen Import

**Tags**: [req-012, new-import, reset, step-1, navigation]

---

## 5. Duplikatstrategie-Verhalten

### TC-012-020: Duplikatstrategie "Überspringen" — Duplikate werden im Ergebnis als übersprungen gezählt

**Requirement**: REQ-012 §1.2, §7 Szenario 3 — Duplikatbehandlung Skip
**Priority**: Critical
**Category**: Zustandswechsel
**Preconditions**:
- "Solanum lycopersicum" existiert bereits im System
- Nutzer befindet sich auf der Import-Seite, Schritt 1
- CSV enthält 3 Zeilen: 2 neue Arten + "Solanum lycopersicum" als Duplikat
- Duplikat-Strategie "Überspringen" ist ausgewählt

**Testschritte**:
1. Nutzer wählt eine CSV mit 3 Zeilen (1 Duplikat) aus und klickt "Hochladen"
2. Nutzer wartet auf die Vorschau (Schritt 2)
3. Nutzer betrachtet die Vorschau-Tabelle
4. Nutzer klickt "Import bestätigen"
5. Nutzer betrachtet das Ergebnis (Schritt 3)

**Erwartete Ergebnisse**:
- Schritt 2: Die Zeile mit "Solanum lycopersicum" zeigt den gelben Duplikat-Chip
- Schritt 2: Hinweis auf aktive Strategie ist sichtbar (z.B. "Strategie: Überspringen (1 Duplikat wird übersprungen)")
- Schritt 3: Chip "Erstellt: 2" (grün)
- Schritt 3: Chip "Übersprungen: 1" (gelb/orange)
- Schritt 3: Chip "Fehlgeschlagen: 0"
- Der bestehende "Solanum lycopersicum"-Eintrag wurde nicht verändert

**Nachbedingungen**:
- 2 neue Einträge gespeichert, 1 Duplikat übersprungen, bestehender Datensatz unverändert

**Tags**: [req-012, duplicate-strategy, skip, duplicate-skipped, species]

---

### TC-012-021: Duplikatstrategie "Aktualisieren" — Duplikat wird mit CSV-Werten überschrieben

**Requirement**: REQ-012 §1.2, §7 Szenario 4 — Duplikatbehandlung Update
**Priority**: Critical
**Category**: Zustandswechsel
**Preconditions**:
- "Ocimum basilicum" existiert im System mit `allelopathy_score = 0.0`
- Nutzer befindet sich auf der Import-Seite, Schritt 1
- CSV enthält eine Zeile: "Ocimum basilicum" mit `allelopathy_score = 0.5`
- Duplikat-Strategie "Aktualisieren" ist ausgewählt

**Testschritte**:
1. Nutzer wählt CSV und Strategie "Aktualisieren" aus und klickt "Hochladen"
2. Nutzer prüft die Vorschau (Schritt 2)
3. Nutzer klickt "Import bestätigen"
4. Nutzer betrachtet das Ergebnis (Schritt 3)

**Erwartete Ergebnisse**:
- Schritt 2: Die Zeile zeigt den gelben Duplikat-Chip
- Schritt 3: Chip "Aktualisiert: 1" (blau/info) ist sichtbar
- Schritt 3: Chip "Erstellt: 0"
- Wenn Nutzer danach die Species-Detailseite von "Ocimum basilicum" aufruft, wird `allelopathy_score = 0.5` angezeigt

**Nachbedingungen**:
- "Ocimum basilicum" hat den aktualisierten allelopathy_score = 0.5

**Tags**: [req-012, duplicate-strategy, update, records-updated, merge]

---

### TC-012-022: Duplikatstrategie "Fehler melden" — Duplikat wird als fehlgeschlagen gezählt

**Requirement**: REQ-012 §1.2, §7 Szenario 5 — Duplikatbehandlung Fail
**Priority**: High
**Category**: Fehlermeldung
**Preconditions**:
- "Cannabis sativa" existiert bereits im System
- CSV enthält eine Zeile mit "Cannabis sativa"
- Duplikat-Strategie "Fehler melden" ist ausgewählt

**Testschritte**:
1. Nutzer wählt CSV und Strategie "Fehler melden" aus und klickt "Hochladen"
2. Nutzer bestätigt den Import in Schritt 2
3. Nutzer betrachtet das Ergebnis in Schritt 3

**Erwartete Ergebnisse**:
- Schritt 3: Chip "Fehlgeschlagen: 1" ist sichtbar
- Schritt 3: Fehlerdetails enthalten eine Meldung zum Duplikat (z.B. "Duplikat gefunden (Strategie: Fehler melden)")
- Der bestehende "Cannabis sativa"-Eintrag wurde nicht verändert

**Nachbedingungen**:
- Duplikat-Zeile wurde nicht importiert, Fehlerzähler erhöht

**Tags**: [req-012, duplicate-strategy, fail, records-failed, duplicate-error]

---

## 6. Zeilen-Validierung — Pflichtfelder und Feldtypen

### TC-012-023: Fehlende Pflichtfelder in Species-CSV werden als "invalid" markiert

**Requirement**: REQ-012 §3.7, §7 Szenario 2 — Validierungsfehler REQUIRED_FIELD
**Priority**: Critical
**Category**: Formvalidierung
**Preconditions**:
- Nutzer befindet sich auf der Import-Seite, Schritt 1
- CSV-Datei enthält 5 Zeilen: 2 gültig, 2 mit fehlendem `scientific_name` (Zeilen 2 und 4), 1 mit ungültigem `cycle_type`

**Testschritte**:
1. Nutzer wählt die CSV aus und klickt "Hochladen"
2. Nutzer betrachtet die Vorschau-Tabelle in Schritt 2

**Erwartete Ergebnisse**:
- Zeilen 2 und 4 zeigen den roten Chip (invalid)
- Zeile 5 zeigt den roten Chip (invalid)
- Zeilen 1 und 3 zeigen den grünen Chip (valid)
- Tooltip auf Zeile 2: "scientific_name: scientific_name ist ein Pflichtfeld"
- Tooltip auf Zeile 5 zeigt einen INVALID_ENUM-Fehler für `cycle_type`
- Schaltfläche "Import bestätigen" ist aktiv (2 gültige Zeilen vorhanden)

**Nachbedingungen**:
- Keine Daten importiert (noch in Schritt 2)

**Tags**: [req-012, validation, required-field, invalid-rows, REQUIRED_FIELD]

---

### TC-012-024: Ungültiger Enum-Wert für cycle_type zeigt INVALID_ENUM-Fehler

**Requirement**: REQ-012 §3.7 — INVALID_ENUM Validierung
**Priority**: High
**Category**: Formvalidierung
**Preconditions**:
- Nutzer befindet sich auf der Import-Seite, Schritt 1
- CSV enthält eine Zeile mit `cycle_type = "jahrezig"` (ungültiger Wert; erlaubt: `annual`, `biennial`, `perennial`)

**Testschritte**:
1. Nutzer wählt CSV aus und klickt "Hochladen"
2. Nutzer betrachtet die Vorschau-Tabelle in Schritt 2

**Erwartete Ergebnisse**:
- Die betroffene Zeile zeigt den roten Chip (invalid)
- Tooltip zeigt: "cycle_type muss einer der Werte [annual, biennial, perennial] sein"
- (oder sinngemäß äquivalente Fehlermeldung)

**Nachbedingungen**:
- Zeile wird nicht importiert

**Tags**: [req-012, validation, INVALID_ENUM, cycle_type, species]

---

### TC-012-025: Scientific-Name-Validierung — Binomiale Nomenklatur

**Requirement**: REQ-012 §3.4 — INVALID_FORMAT für scientific_name
**Priority**: High
**Category**: Formvalidierung
**Preconditions**:
- Nutzer befindet sich auf der Import-Seite, Schritt 1
- CSV enthält eine Zeile mit `scientific_name = "tomate"` (kein Großbuchstabe, kein zweites Wort)

**Testschritte**:
1. Nutzer wählt CSV aus und klickt "Hochladen"
2. Nutzer betrachtet die Vorschau-Tabelle in Schritt 2

**Erwartete Ergebnisse**:
- Die betroffene Zeile zeigt den roten Chip (invalid)
- Tooltip zeigt eine Fehlermeldung zum binomialen Format, z.B.: "Wissenschaftlicher Name muss binomialer Nomenklatur folgen (z.B. 'Solanum lycopersicum')"

**Nachbedingungen**:
- Zeile wird nicht importiert

**Tags**: [req-012, validation, INVALID_FORMAT, scientific_name, binomial-nomenclature]

---

### TC-012-026: Genus-Konsistenz-Fehler wird in der Vorschau angezeigt

**Requirement**: REQ-012 §3.4 — GENUS_MISMATCH Cross-Field-Validierung, §7 Szenario 8
**Priority**: High
**Category**: Formvalidierung
**Preconditions**:
- Nutzer befindet sich auf der Import-Seite, Schritt 1
- CSV enthält: `scientific_name = "Solanum lycopersicum"`, `genus = "Capsicum"` (Widerspruch)

**Testschritte**:
1. Nutzer wählt CSV aus und klickt "Hochladen"
2. Nutzer betrachtet die Vorschau-Tabelle in Schritt 2

**Erwartete Ergebnisse**:
- Die betroffene Zeile zeigt den roten Chip (invalid)
- Tooltip enthält die Fehlermeldung zum Genus-Widerspruch:
  "genus 'Capsicum' stimmt nicht mit scientific_name überein (erwartet: 'Solanum')"

**Nachbedingungen**:
- Zeile wird nicht importiert

**Tags**: [req-012, validation, GENUS_MISMATCH, cross-field, species]

---

### TC-012-027: Ungültiger float-Wert für allelopathy_score wird als INVALID_TYPE markiert

**Requirement**: REQ-012 §3.7 — INVALID_TYPE für Float-Felder
**Priority**: Medium
**Category**: Formvalidierung
**Preconditions**:
- Nutzer befindet sich auf der Import-Seite, Schritt 1
- CSV enthält: `allelopathy_score = "stark"` (kein Float)

**Testschritte**:
1. Nutzer wählt CSV aus und klickt "Hochladen"
2. Nutzer betrachtet die Vorschau-Tabelle

**Erwartete Ergebnisse**:
- Betroffene Zeile zeigt roten Chip (invalid)
- Tooltip enthält Fehlermeldung: "allelopathy_score muss eine Zahl sein"

**Tags**: [req-012, validation, INVALID_TYPE, allelopathy_score, float]

---

### TC-012-028: Wert ausserhalb des erlaubten Bereichs — allelopathy_score > 1.0

**Requirement**: REQ-012 §3.7 — VALUE_TOO_HIGH
**Priority**: Medium
**Category**: Formvalidierung
**Preconditions**:
- CSV enthält: `allelopathy_score = "1.5"` (Bereich: -1.0 bis 1.0)

**Testschritte**:
1. Nutzer wählt CSV aus und klickt "Hochladen"
2. Nutzer betrachtet die Vorschau-Tabelle

**Erwartete Ergebnisse**:
- Betroffene Zeile zeigt roten Chip (invalid)
- Tooltip: "allelopathy_score muss <= 1.0 sein"

**Tags**: [req-012, validation, VALUE_TOO_HIGH, allelopathy_score, boundary]

---

### TC-012-029: Ungültiges Hardiness-Zone-Format wird als INVALID_FORMAT gemeldet

**Requirement**: REQ-012 §3.4 — INVALID_FORMAT für hardiness_zones
**Priority**: Low
**Category**: Formvalidierung
**Preconditions**:
- CSV enthält: `hardiness_zones = "Zone 7"` (falsch; korrekt wäre z.B. "7a;7b")

**Testschritte**:
1. Nutzer wählt CSV aus und klickt "Hochladen"
2. Nutzer betrachtet die Vorschau-Tabelle

**Erwartete Ergebnisse**:
- Betroffene Zeile zeigt roten Chip (invalid)
- Tooltip enthält: "Ungültige Hardiness Zone: 'Zone 7' (erwartet z.B. '7a')"

**Tags**: [req-012, validation, INVALID_FORMAT, hardiness_zones, list-field]

---

### TC-012-030: Ungültiger Trait-Key wird als INVALID_TRAIT markiert

**Requirement**: REQ-012 §3.4 — INVALID_TRAIT für Cultivar-Traits
**Priority**: Low
**Category**: Formvalidierung
**Preconditions**:
- Nutzer wählt Entitätstyp "Sorten"
- CSV enthält: `traits = "super_plant"` (kein gültiger Trait-Key)

**Testschritte**:
1. Nutzer wählt CSV aus und klickt "Hochladen"
2. Nutzer betrachtet die Vorschau-Tabelle

**Erwartete Ergebnisse**:
- Betroffene Zeile zeigt roten Chip (invalid)
- Tooltip enthält: "Ungültige Traits: super_plant"

**Tags**: [req-012, validation, INVALID_TRAIT, traits, cultivar]

---

## 7. CSV-Dateivalidierung (Schritt 1 — Upload-Fehler)

### TC-012-031: Upload einer Nicht-CSV-Datei wird abgelehnt (Dateiauswahl-Filter)

**Requirement**: REQ-012 §3.6, CI-005 — Nur CSV-Dateien erlaubt
**Priority**: Critical
**Category**: Formvalidierung
**Preconditions**:
- Nutzer befindet sich auf der Import-Seite, Schritt 1
- Eine Nicht-CSV-Datei (z.B. `datei.xlsx` oder `datei.pdf`) liegt auf dem Rechner bereit

**Testschritte**:
1. Nutzer klickt auf "CSV-Datei auswählen"
2. Nutzer versucht, eine `.xlsx`-Datei auszuwählen

**Erwartete Ergebnisse**:
- Im Dateiauswahl-Dialog sind nur Dateien mit den Endungen `.csv`, `.tsv`, `.txt` auswählbar (accept-Filter im input-Element)
- Falls der Browser dennoch eine nicht-erlaubte Datei zulässt und der Nutzer hochlädt: eine Fehlermeldung erscheint ("Nur CSV-Dateien erlaubt" o.ä.)

**Nachbedingungen**:
- Kein Upload gestartet

**Tags**: [req-012, file-validation, non-csv, file-type-filter, CI-005]

---

### TC-012-032: Upload einer CSV-Datei über 10 MB zeigt Fehlermeldung

**Requirement**: REQ-012 §3.3, CI-002 — Maximale Dateigröße 10 MB
**Priority**: Critical
**Category**: Fehlermeldung
**Preconditions**:
- Nutzer befindet sich auf der Import-Seite, Schritt 1
- Eine CSV-Datei mit mehr als 10 MB ist auf dem Rechner verfügbar (z.B. generierte 11-MB-Testdatei)

**Testschritte**:
1. Nutzer wählt die 11-MB-CSV-Datei aus
2. Nutzer klickt "Hochladen"
3. Nutzer wartet auf die Serverantwort

**Erwartete Ergebnisse**:
- Eine Fehlermeldung erscheint im roten Error-Alert über dem Formular
- Die Meldung enthält den Hinweis, dass die Datei die maximale Größe von 10 MB überschreitet
- Der Stepper verbleibt auf Schritt 1 (kein Sprung zur Vorschau)
- "Hochladen"-Button ist danach wieder aktiv

**Nachbedingungen**:
- Kein Import-Job wurde erstellt

**Tags**: [req-012, file-validation, file-size, 10MB-limit, error-message, CI-002]

---

### TC-012-033: Upload einer leeren CSV-Datei zeigt Fehlermeldung

**Requirement**: REQ-012 §3.6 — Leere Datei wird abgelehnt
**Priority**: High
**Category**: Fehlermeldung
**Preconditions**:
- Nutzer befindet sich auf der Import-Seite, Schritt 1
- Eine leere CSV-Datei (0 Bytes) ist auf dem Rechner verfügbar

**Testschritte**:
1. Nutzer wählt die leere CSV-Datei aus
2. Nutzer klickt "Hochladen"
3. Nutzer wartet auf die Serverantwort

**Erwartete Ergebnisse**:
- Eine Fehlermeldung erscheint (roter Alert)
- Die Meldung weist auf die leere Datei hin
- Der Stepper verbleibt auf Schritt 1

**Tags**: [req-012, file-validation, empty-file, EMPTY_FILE, error]

---

### TC-012-034: CSV mit fehlenden Pflichtspalten im Header wird als strukturfehler markiert

**Requirement**: REQ-012 §3.3 — MISSING_COLUMNS Strukturfehler
**Priority**: High
**Category**: Fehlermeldung
**Preconditions**:
- Nutzer befindet sich auf der Import-Seite, Schritt 1
- CSV-Datei enthält einen Header ohne `scientific_name` (Pflichtspalte für Species)
- Datentyp "Pflanzenarten" ist ausgewählt

**Testschritte**:
1. Nutzer wählt die CSV-Datei aus und klickt "Hochladen"
2. Nutzer betrachtet das Ergebnis

**Erwartete Ergebnisse**:
- Entweder: Der Job landet im Status "fehlgeschlagen" und der Fehlertext enthält "Fehlende Pflichtspalten: scientific_name"
- Oder: Ein roter Alert in Schritt 1 zeigt den Strukturfehler an
- In beiden Fällen: Kein Sprung zur Vorschau-Tabelle

**Tags**: [req-012, structural-error, MISSING_COLUMNS, header-validation]

---

## 8. Encoding- und Delimiter-Erkennung

### TC-012-035: CSV mit UTF-8 BOM und Semikolon-Delimiter wird korrekt geparst

**Requirement**: REQ-012 §7 Szenario 7 — Encoding und Delimiter Erkennung
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- Nutzer befindet sich auf der Import-Seite, Schritt 1
- CSV-Datei ist im Format UTF-8-BOM (Byte Order Mark am Anfang) gespeichert
- Als Trennzeichen wird Semikolon (`;`) verwendet
- Die Datei enthält 3 gültige Species-Zeilen

**Testschritte**:
1. Nutzer wählt die BOM-CSV-Datei aus und klickt "Hochladen"
2. Nutzer betrachtet die Vorschau-Tabelle in Schritt 2

**Erwartete Ergebnisse**:
- Alle 3 Zeilen wurden korrekt geparst und zeigen grüne Chips (valid)
- Die Felder wurden korrekt getrennt (keine Artefakte wie "scientific_name;common_names" als einziger Feldinhalt)
- Kein Encoding-Fehler wird angezeigt
- Sonderzeichen (Umlaute, Akzente) werden korrekt dargestellt

**Tags**: [req-012, encoding, utf8-bom, semicolon-delimiter, auto-detect]

---

### TC-012-036: CSV mit Tab-Delimiter wird korrekt erkannt

**Requirement**: REQ-012 §3.3 — Trennzeichen-Erkennung (Tab)
**Priority**: Medium
**Category**: Happy Path
**Preconditions**:
- CSV-Datei verwendet Tab (`\t`) als Trennzeichen
- Datei enthält 2 gültige Species-Zeilen

**Testschritte**:
1. Nutzer wählt die Tab-delimitierte CSV aus und klickt "Hochladen"
2. Nutzer betrachtet die Vorschau-Tabelle

**Erwartete Ergebnisse**:
- Alle Spalten wurden korrekt getrennt
- Beide Zeilen zeigen grüne Chips (valid)
- Kein Parsing-Fehler sichtbar

**Tags**: [req-012, encoding, tab-delimiter, auto-detect]

---

## 9. Cultivar-Import spezifische Validierung

### TC-012-037: Cultivar-Import — Fehlende parent_species wird als REQUIRED_FIELD markiert

**Requirement**: REQ-012 §3.1 Cultivar-CSV — parent_species Pflichtfeld
**Priority**: High
**Category**: Formvalidierung
**Preconditions**:
- Nutzer hat Entitätstyp "Sorten" ausgewählt
- CSV enthält eine Zeile mit leerem `parent_species`-Feld

**Testschritte**:
1. Nutzer wählt CSV aus und klickt "Hochladen"
2. Nutzer betrachtet die Vorschau-Tabelle

**Erwartete Ergebnisse**:
- Betroffene Zeile zeigt roten Chip (invalid)
- Tooltip: "parent_species ist ein Pflichtfeld"

**Tags**: [req-012, validation, cultivar, parent_species, REQUIRED_FIELD]

---

### TC-012-038: Cultivar-Import — breeding_year ausserhalb des Wertebereichs

**Requirement**: REQ-012 §3.1 Cultivar-CSV — breeding_year Bereich 1800–2100
**Priority**: Medium
**Category**: Formvalidierung
**Preconditions**:
- CSV enthält: `breeding_year = "1750"` (unter Minimalwert 1800)

**Testschritte**:
1. Nutzer wählt CSV (Typ "Sorten") aus und klickt "Hochladen"
2. Nutzer betrachtet die Vorschau-Tabelle

**Erwartete Ergebnisse**:
- Betroffene Zeile zeigt roten Chip (invalid)
- Tooltip: "breeding_year muss >= 1800 sein"

**Tags**: [req-012, validation, cultivar, breeding_year, VALUE_TOO_LOW, boundary]

---

### TC-012-039: Cultivar-Import — days_to_maturity Grenzwert 365 (gültiger Maximalwert)

**Requirement**: REQ-012 §3.1 Cultivar-CSV — days_to_maturity max 365
**Priority**: Low
**Category**: Happy Path
**Preconditions**:
- CSV enthält: `days_to_maturity = "365"` (Maximalwert, noch gültig)

**Testschritte**:
1. Nutzer wählt CSV (Typ "Sorten") aus und klickt "Hochladen"
2. Nutzer betrachtet die Vorschau-Tabelle

**Erwartete Ergebnisse**:
- Betroffene Zeile zeigt grünen Chip (valid)
- Kein Fehler für `days_to_maturity`

**Tags**: [req-012, boundary, cultivar, days_to_maturity, max-value, valid]

---

### TC-012-040: Cultivar-Import — days_to_maturity = 366 überschreitet Maximum

**Requirement**: REQ-012 §3.1 Cultivar-CSV — days_to_maturity max 365
**Priority**: Medium
**Category**: Formvalidierung
**Preconditions**:
- CSV enthält: `days_to_maturity = "366"` (ein über dem Maximum)

**Testschritte**:
1. Nutzer wählt CSV (Typ "Sorten") aus und klickt "Hochladen"
2. Nutzer betrachtet die Vorschau-Tabelle

**Erwartete Ergebnisse**:
- Betroffene Zeile zeigt roten Chip (invalid)
- Tooltip: "days_to_maturity muss <= 365 sein"

**Tags**: [req-012, boundary, cultivar, days_to_maturity, VALUE_TOO_HIGH]

---

## 10. BotanicalFamily-Import spezifische Validierung

### TC-012-041: BotanicalFamily-Import — ungültiger typical_nutrient_demand-Wert

**Requirement**: REQ-012 §3.1 BotanicalFamily-CSV — typical_nutrient_demand Enum
**Priority**: High
**Category**: Formvalidierung
**Preconditions**:
- Nutzer hat Entitätstyp "Pflanzenfamilien" ausgewählt
- CSV enthält: `typical_nutrient_demand = "mittel"` (ungültig; erlaubt: light, medium, heavy)

**Testschritte**:
1. Nutzer wählt CSV aus und klickt "Hochladen"
2. Nutzer betrachtet die Vorschau-Tabelle

**Erwartete Ergebnisse**:
- Betroffene Zeile zeigt roten Chip (invalid)
- Tooltip: "typical_nutrient_demand muss einer der Werte [light, medium, heavy] sein"

**Tags**: [req-012, validation, botanical-family, typical_nutrient_demand, INVALID_ENUM]

---

## 11. Sicherheitsanforderungen (CI-Regeln)

### TC-012-042: CSV-Injection-Verdacht wird als SUSPICIOUS_CONTENT markiert

**Requirement**: REQ-012 §5.1 CI-004 — CSV-Injection Sanitisierung
**Priority**: High
**Category**: Fehlermeldung
**Preconditions**:
- CSV enthält eine Zeile, in der ein Feldwert mit `=` beginnt (z.B. `common_names = "=1+1"`)

**Testschritte**:
1. Nutzer wählt die CSV aus und klickt "Hochladen"
2. Nutzer betrachtet die Vorschau-Tabelle

**Erwartete Ergebnisse**:
- Die betroffene Zeile ist in der Vorschau markiert (z.B. mit einer Warnung oder Hinweis "SUSPICIOUS_CONTENT")
- Der Nutzer wird auf den potenziell schädlichen Inhalt hingewiesen
- Import kann dennoch fortgesetzt werden (nicht blockierend), wobei das führende `=`-Zeichen automatisch entfernt wird

**Tags**: [req-012, security, csv-injection, SUSPICIOUS_CONTENT, CI-004]

---

### TC-012-043: Rate-Limit — sechster Upload innerhalb einer Stunde zeigt Fehlermeldung

**Requirement**: REQ-012 §5.1 CI-007 — Rate-Limit 5 Uploads/Stunde
**Priority**: High
**Category**: Fehlermeldung
**Preconditions**:
- Nutzer hat innerhalb der letzten Stunde bereits 5 CSV-Dateien hochgeladen
- Nutzer befindet sich auf der Import-Seite, Schritt 1, mit einer neuen CSV bereit

**Testschritte**:
1. Nutzer wählt eine gültige CSV aus
2. Nutzer klickt auf "Hochladen"
3. Nutzer wartet auf die Serverantwort

**Erwartete Ergebnisse**:
- Eine Fehlermeldung erscheint (roter Alert)
- Die Meldung informiert den Nutzer über das Rate-Limit (z.B. "Upload-Limit erreicht. Bitte warten Sie vor dem nächsten Upload.")
- Der Stepper verbleibt auf Schritt 1

**Tags**: [req-012, rate-limit, CI-007, error-message, security]

---

## 12. Feeding-Chart-Import (NutrientPlan)

### TC-012-044: Erfolgreicher Feeding-Chart-Import (CSV) mit bekannten Produkten

**Requirement**: REQ-012 §3.8, §7 Szenario 9 — Erfolgreicher Feeding-Chart-Import
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- Nutzer ist eingeloggt und navigiert zur Feeding-Chart-Import-Seite (Route noch zu implementieren, analog `/stammdaten/import`)
- Fertilizer "Canna Coco A" und "Canna Coco B" existieren im System
- "Cannazym" existiert NICHT im Fertilizer-Katalog
- CSV-Datei mit Canna Coco Feeding-Chart (10 Wochen, 3 Produkte) liegt vor

**Testschritte**:
1. Nutzer öffnet die Feeding-Chart-Import-Seite
2. Nutzer gibt Plan-Name "Canna Coco Test" ein
3. Nutzer wählt die CSV-Datei aus
4. Nutzer klickt "Hochladen und Validieren"
5. Nutzer betrachtet die Vorschau-Tabelle

**Erwartete Ergebnisse**:
- Alle Zeilen zu "Canna Coco A" und "Canna Coco B" zeigen grüne Chips (valid)
- Zeilen mit "Cannazym" zeigen eine Warnung oder Markierung "UNRESOLVED_PRODUCT"
- Für "Cannazym" sind drei Aktionsoptionen sichtbar: "Vorhandenem Fertilizer zuordnen", "Als neuen Fertilizer anlegen", "Zeile überspringen"
- "Import bestätigen" ist aktiv

**Nachbedingungen**:
- Import-Job wartet auf Bestätigung

**Tags**: [req-012, feeding-chart, nutrient-plan, UNRESOLVED_PRODUCT, product-matching]

---

### TC-012-045: Feeding-Chart — Nutzer legt unbekanntes Produkt als neuen Fertilizer an

**Requirement**: REQ-012 §3.8.3 — Nutzer-Entscheidung bei Nicht-Treffer
**Priority**: High
**Category**: Dialog
**Preconditions**:
- Vorschau zeigt "Cannazym" als UNRESOLVED_PRODUCT (gemäss TC-012-044)

**Testschritte**:
1. Nutzer wählt für "Cannazym" die Option "Als neuen Fertilizer anlegen"
2. Nutzer klickt "Import bestätigen"
3. Nutzer betrachtet das Ergebnis

**Erwartete Ergebnisse**:
- Ergebnis-Seite zeigt erfolgreich importierten NutrientPlan
- Statistik enthält: 1 NutrientPlan erstellt, 10 NutrientPlanPhaseEntries erstellt, 1 neuer Fertilizer ("Cannazym") erstellt
- Navigiert der Nutzer zur Fertilizer-Liste, erscheint "Cannazym" als neuer Eintrag

**Nachbedingungen**:
- NutrientPlan, Phase-Entries und neuer Fertilizer wurden angelegt

**Tags**: [req-012, feeding-chart, unresolved-product, create-new-fertilizer]

---

### TC-012-046: Feeding-Chart-Import — INVALID_PHASE für ungültige Phase

**Requirement**: REQ-012 §3.8.3, §7 Szenario 10 — Feeding-Chart Validierungsfehler
**Priority**: High
**Category**: Formvalidierung
**Preconditions**:
- CSV enthält: `phase = "blüte"` (ungültig; erlaubt: germination, seedling, vegetative, flowering, harvest)

**Testschritte**:
1. Nutzer wählt die CSV aus und startet den Feeding-Chart-Upload
2. Nutzer betrachtet die Vorschau-Tabelle

**Erwartete Ergebnisse**:
- Betroffene Zeile zeigt roten Chip (invalid)
- Fehlerdetail: "INVALID_PHASE — 'blüte' ist keine gültige Phase"
- Import kann mit verbleibenden gültigen Zeilen bestätigt werden

**Tags**: [req-012, feeding-chart, INVALID_PHASE, validation]

---

### TC-012-047: Feeding-Chart-Import — INVALID_DOSAGE bei Überschreitung von 100 ml/l

**Requirement**: REQ-012 §3.8.3 — INVALID_DOSAGE Bereich 0.01–100.0
**Priority**: Medium
**Category**: Formvalidierung
**Preconditions**:
- CSV enthält: `dosage_ml_per_l = "200.0"` (über Maximum 100.0)

**Testschritte**:
1. Nutzer wählt die CSV aus und startet den Feeding-Chart-Upload
2. Nutzer betrachtet die Vorschau-Tabelle

**Erwartete Ergebnisse**:
- Betroffene Zeile zeigt roten Chip (invalid)
- Fehlerdetail enthält "INVALID_DOSAGE" und Grenzwert-Hinweis

**Tags**: [req-012, feeding-chart, INVALID_DOSAGE, boundary, validation]

---

### TC-012-048: Feeding-Chart JSON-Import funktioniert analog zu CSV

**Requirement**: REQ-012 §3.8.1, §7 Szenario 12 — JSON-Format
**Priority**: Medium
**Category**: Happy Path
**Preconditions**:
- JSON-Datei mit BioBizz Organic Feeding-Chart liegt vor
- Alle enthaltenen Produkte existieren im Fertilizer-Katalog

**Testschritte**:
1. Nutzer navigiert zur Feeding-Chart-Import-Seite
2. Nutzer gibt Plan-Name "BioBizz Test" ein
3. Nutzer wählt die JSON-Datei aus
4. Nutzer klickt "Hochladen und Validieren"
5. Nutzer betrachtet die Vorschau-Tabelle
6. Nutzer klickt "Import bestätigen"

**Erwartete Ergebnisse**:
- Vorschau zeigt alle Zeilen als gültig (grüne Chips)
- Nach Bestätigung: NutrientPlan "BioBizz Test" wird erstellt
- Ergebnis-Seite zeigt erfolgreiche Statistiken
- Das Verhalten ist identisch zum CSV-Import

**Tags**: [req-012, feeding-chart, json-format, nutrient-plan]

---

## 13. Community-Templates und Klonfunktion

### TC-012-049: Community-Templates-Liste zeigt alle 5 vorinstallierten Feeding-Charts

**Requirement**: REQ-012 §3.8.5 — Community-Templates, 5 Seed-Templates
**Priority**: High
**Category**: Listenansicht
**Preconditions**:
- Nutzer navigiert zur Community-Templates-Seite (z.B. als Tab auf der NutrientPlan-Liste oder separater Menüpunkt)

**Testschritte**:
1. Nutzer öffnet die Community-Templates-Liste

**Erwartete Ergebnisse**:
- Mindestens 5 Template-Einträge sind sichtbar:
  1. "Canna Coco A+B Complete" (Canna, 10 Wochen)
  2. "BioBizz Organic Indoor" (BioBizz, 12 Wochen)
  3. "AN pH Perfect Sensi" (Advanced Nutrients, 10 Wochen)
  4. "Athena Pro Line" (Athena, 9 Wochen)
  5. "GHE Flora Series Expert" (GHE, 12 Wochen)
- Jeder Eintrag zeigt: Name, Hersteller, Substrat/Anwendung und Wochenanzahl
- Jeder Eintrag hat eine Schaltfläche "Klonen" oder "Als Basis verwenden"

**Tags**: [req-012, community-templates, seed-data, template-list]

---

### TC-012-050: Community-Template klonen erstellt editierbaren NutrientPlan

**Requirement**: REQ-012 §3.8.6, §7 Szenario 11 — Template-Klonen
**Priority**: High
**Category**: Dialog
**Preconditions**:
- Nutzer befindet sich auf der Community-Templates-Liste
- "Canna Coco A+B Complete" Template ist sichtbar

**Testschritte**:
1. Nutzer klickt auf "Klonen" beim "Canna Coco A+B Complete" Template
2. Ein Dialog oder Eingabefeld für den neuen Plan-Namen erscheint
3. Nutzer gibt den Namen "Mein Canna Plan" ein
4. Nutzer bestätigt das Klonen

**Erwartete Ergebnisse**:
- Eine Erfolgsmeldung (Snackbar oder Alert) erscheint: Plan erfolgreich geklont
- Nutzer wird zur NutrientPlan-Detailseite des neuen Plans navigiert (oder zur Liste)
- Der geklonte Plan heisst "Mein Canna Plan"
- Der Plan ist editierbar (Dosierungen, EC, pH sind änderbar — keine read-only Markierung)
- Das ursprüngliche Community-Template ist unverändert in der Templates-Liste vorhanden
- Der geklonte Plan zeigt als Referenz "Quelle: Canna Coco" (oder `source_chart`-Feld)

**Tags**: [req-012, community-templates, clone, nutrient-plan, CLONED_FROM]

---

### TC-012-051: Community-Template selbst ist schreibgeschützt (nicht direkt editierbar)

**Requirement**: REQ-012 §3.8.5 — is_template=true, is_seed_data=true; unveränderbar
**Priority**: Medium
**Category**: Zustandswechsel
**Preconditions**:
- Nutzer navigiert zur Detailseite eines Community-Templates (z.B. "Canna Coco A+B Complete")

**Testschritte**:
1. Nutzer öffnet die Detailseite des Community-Templates
2. Nutzer versucht, einen Dosierungswert direkt zu ändern oder auf "Bearbeiten" zu klicken

**Erwartete Ergebnisse**:
- Bearbeiten-Schaltfläche ist entweder nicht sichtbar oder deaktiviert
- Eine Hinweismeldung erklärt, dass Community-Templates schreibgeschützt sind
- Klon-Schaltfläche ist sichtbar und aktiv

**Tags**: [req-012, community-templates, read-only, is_seed_data, edit-disabled]

---

## 14. Import-Historie

### TC-012-052: Import-Historie zeigt bisherige Import-Jobs

**Requirement**: REQ-012 §4.4 — Import-Historie
**Priority**: High
**Category**: Listenansicht
**Preconditions**:
- Nutzer hat zuvor mindestens 3 Import-Jobs durchgeführt (abgeschlossene und fehlgeschlagene)

**Testschritte**:
1. Nutzer navigiert zur Import-Historie (z.B. `/import/history` oder separater Tab)

**Erwartete Ergebnisse**:
- Eine Tabelle mit bisherigen Import-Jobs ist sichtbar
- Jede Zeile zeigt: Datum, Dateiname, Entitätstyp, Status, Anzahl erstellter Einträge, Fehleranzahl
- Status-Werte werden als farbige Chips dargestellt (Done = grün, Failed = rot, etc.)
- Die Liste ist nach Datum absteigend sortiert (neueste zuerst)

**Tags**: [req-012, import-history, list-view, status-chip]

---

### TC-012-053: Import-Historie Filter nach Entitätstyp

**Requirement**: REQ-012 §4.4 — Filter "Alle Entitäten" Dropdown
**Priority**: Medium
**Category**: Listenansicht
**Preconditions**:
- Import-Historie enthält Jobs für Species, Cultivar und BotanicalFamily

**Testschritte**:
1. Nutzer öffnet die Import-Historie
2. Nutzer wählt im Filter-Dropdown "Pflanzenarten" aus

**Erwartete Ergebnisse**:
- Die Tabelle zeigt nur Import-Jobs mit Entitätstyp "Species"
- Jobs für Cultivar und BotanicalFamily verschwinden aus der Liste
- Die Filterauswahl bleibt aktiv

**Tags**: [req-012, import-history, filter, entity-type-filter]

---

## 15. Fehlerzustände und Edge Cases

### TC-012-054: Serverfehler beim Upload zeigt Fehlermeldung ohne Absturz

**Requirement**: REQ-012 §4.1 — Fehlerbehandlung beim Upload
**Priority**: High
**Category**: Fehlermeldung
**Preconditions**:
- Server ist nicht erreichbar oder gibt einen internen Fehler zurück
- Nutzer befindet sich auf der Import-Seite, Schritt 1, mit einer gültigen CSV

**Testschritte**:
1. Nutzer wählt eine gültige CSV aus
2. Nutzer klickt "Hochladen"
3. Server antwortet mit einem Fehler

**Erwartete Ergebnisse**:
- Ein roter Error-Alert erscheint auf der Seite (nicht ein leerer Bildschirm)
- Die Fehlermeldung ist für den Nutzer verständlich (z.B. "Upload fehlgeschlagen. Bitte versuchen Sie es erneut.")
- Der Stepper verbleibt auf Schritt 1
- Der "Hochladen"-Button ist wieder aktiv

**Nachbedingungen**:
- Nutzer kann den Upload erneut versuchen

**Tags**: [req-012, error-handling, server-error, network-error, graceful-failure]

---

## Abdeckungs-Matrix

| Spezifikations-Abschnitt | Abgedeckte Testfälle |
|--------------------------|---------------------|
| §1.1 Unterstützte Entitäten (Species, Cultivar, BotanicalFamily) | TC-012-004, TC-012-007–009, TC-012-037–041 |
| §1.2 Duplikatbehandlung (skip/update/fail) | TC-012-005, TC-012-020–022 |
| §3.1 CSV-Spalten-Definitionen (alle 3 Entitäten) | TC-012-023–030, TC-012-037–041 |
| §3.3 CSV-Format-Anforderungen (Encoding, Delimiter, Größe) | TC-012-031–036 |
| §3.4 Zeilen-Validator (alle Fehler-Codes) | TC-012-023–030 |
| §3.5 Import-Engine (Status-Übergänge) | TC-012-011, TC-012-017 |
| §3.6 REST-API-Endpunkte (Upload, Confirm, Jobs, Templates) | TC-012-011, TC-012-017, TC-012-007–009 |
| §3.7 Validierungsregeln-Zusammenfassung | TC-012-023–030 |
| §3.8 Feeding-Chart-Import (NutrientPlan, Produkt-Matching) | TC-012-044–048 |
| §3.8.3 Produkt-Matching (exakt, fuzzy, UNRESOLVED_PRODUCT) | TC-012-044–045 |
| §3.8.5 Community-Templates (5 Seed-Templates) | TC-012-049 |
| §3.8.6 Klonfunktion | TC-012-050–051 |
| §4.1 Upload-Dialog (Stepper Schritt 1) | TC-012-003–010 |
| §4.2 Preview-Tabelle (Stepper Schritt 2) | TC-012-012–016 |
| §4.3 Ergebnis-Anzeige (Stepper Schritt 3) | TC-012-017–019 |
| §4.4 Import-Historie | TC-012-052–053 |
| §4.5 Hinweistexte (helper texts) | TC-012-003 (implizit) |
| §4.6 Navigation (Sidebar, i18n) | TC-012-001–002 |
| §5.1 Sicherheitsanforderungen CI-001–CI-009 | TC-012-042–043, TC-012-031–032 |
| §7 Akzeptanzkriterien — alle 12 Testszenarien | TC-012-011, 012-013, 012-020–022, 012-023, 012-025–026, 012-035, 012-044, 012-046, 012-050, 012-048 |

**Gesamtanzahl Testfälle: 54**

**Kritische Pfade (für Smoke-Test):**
1. TC-012-001 → TC-012-003 → TC-012-007 → TC-012-010 → TC-012-011 → TC-012-017 → TC-012-019
   (Navigation → Formular → Template-Download → Dateiauswahl → Upload → Vorschau → Import bestätigen → Neuer Import)

**Nicht abgedeckt in dieser Version (erfordert weitere Spezifikation):**
- Maximale Zeilenanzahl-Grenze 10.000 Zeilen (CI-003) — Testablauf benötigt grosse Testdatei
- Zeilen per Checkbox aus Import ausschliessen (DoD §7) — UI noch nicht im aktuellen `ImportPage.tsx` implementiert
- Status-Filter der Import-Historie mit URL-Parameter `?status=...` (DoD §7) — Route noch nicht vorhanden
- Feeding-Chart-Import-Route — separate Route noch nicht spezifiziert (nur API-Endpunkte in §3.8.7)
