---
req_id: REQ-013
title: Pflanzdurchlauf-Verwaltung & Batch-Operationen
category: Gruppenmanagement
test_count: 67
coverage_areas:
  - Listenansicht PlantingRun
  - Erstellen-Dialog (Monokultur, Klon)
  - Formularvalidierung Erstellungsdialog
  - Detailseite Tabs (Details, Pflanzen, Phasen, Nährstoff/Gießen, Aktivitätsplan)
  - Bearbeiten-Dialog
  - Batch-Erstellung (create-plants)
  - Run-Level Phasenwechsel (transition)
  - Batch-Entfernung / Run-Abschluss
  - Individuelle Pflanzenabtrennung (detach) mit Pflicht-Kategorie
  - Dual-Modell (Run-Managed vs. Standalone — keine Einzelsteuerung im Run)
  - PlantDiaryEntry (CRUD, Tagebuch-Tab, aggregiertes Run-Tagebuch)
  - SuccessionPlan (Erstellen, automatisch generierte Staffel-Runs)
  - Nährstoffplan-Zuweisung und Entfernung
  - Gießkalender-Anzeige
  - Löschen-Dialog (nur Status planned)
  - Status-Statusmaschine (Zustandsübergänge sichtbar im UI)
  - Navigationspfade und Breadcrumbs
  - Erfahrungsstufen-Sichtbarkeit (ExpertiseFieldWrapper)
generated: 2026-04-02
version: "2.0"
---

# Testfälle REQ-013: Pflanzdurchlauf-Verwaltung & Batch-Operationen

## Kontext und Testabdeckungsstrategie

REQ-013 v2.0 führt den **Pflanzdurchlauf (PlantingRun)** als **primäre Verwaltungseinheit** ein.
In v2.0 wurde Mischkultur entfernt (separate Runs pro Art, Companion-Beziehungen über REQ-028) und
drei neue Konzepte eingeführt: **PlantDiaryEntry** (individuelles Pflanzen-Tagebuch), das
**Dual-Modell** (Run-Managed vs. Standalone — innerhalb eines Runs keine Einzelsteuerung für Phase/
Task/Care) sowie **SuccessionPlan** (automatisch generierte Staffel-Runs).

Die Testfälle decken den vollständigen Lifecycle aus Browser-Sicht ab: Erstellung beider Typen
(Monokultur, Klon), Batch-Aktionen (Pflanzen anlegen, Run-Level Phasenwechsel, Run beenden),
individuelle Pflanzenabtrennung mit Pflicht-Kategorie, Tagebuch-Funktionen sowie SuccessionPlan.
Alle Testschritte beschreiben ausschließlich Browser-Interaktionen — keine API- oder Datenbankzugriffe.

Route: `/durchlaeufe/planting-runs` (Liste) | `/durchlaeufe/planting-runs/:key` (Detail)

---

## Gruppe 1: Listenansicht (PlantingRunListPage)

### TC-013-001: Listenansicht lädt alle Pflanzdurchläufe

**Requirement**: REQ-013 §4.1, §7 DoD (PlantingRun-CRUD)
**Priority**: Critical
**Category**: Listenansicht

**Preconditions**:
- Nutzer ist eingeloggt und Tenant-Mitglied
- Mindestens 3 PlantingRuns mit unterschiedlichen Status existieren: einer `planned`, einer `active`, einer `completed`

**Test Steps**:
1. Nutzer navigiert zu `/durchlaeufe/planting-runs`
2. Nutzer wartet bis die Tabelle geladen ist (kein Lade-Spinner mehr sichtbar)

**Expected Results**:
- Seite zeigt Seitentitel (Überschrift der Durchläufe-Liste)
- Tabelle enthält Spalten: Name, Typ, Status, Aktuelle Phase, Geplante Anzahl, Tatsächliche Anzahl, Gestartet am
- Alle vorhandenen PlantingRuns werden als Zeilen aufgelistet
- Status-Chips zeigen korrekte Farben: `planned` = grau (default), `active` = blau (primary), `completed` = grün (success), `cancelled` = rot (error), `harvesting` = orange (warning)
- Schaltfläche "Erstellen" ist in der rechten oberen Ecke sichtbar

**Postconditions**:
- Keine Datenänderung

**Tags**: [REQ-013, listenansicht, status-chip, navigation]

---

### TC-013-002: Listenansicht — Leerszustand zeigt Illustration und Aktionsschaltfläche

**Requirement**: REQ-013 §7 DoD (PlantingRun-CRUD)
**Priority**: Medium
**Category**: Listenansicht

**Preconditions**:
- Nutzer ist eingeloggt
- Kein PlantingRun im System vorhanden (leere Liste)

**Test Steps**:
1. Nutzer navigiert zu `/durchlaeufe/planting-runs`

**Expected Results**:
- Tabelle zeigt keine Zeilen
- Ein Leerszustand-Element (Illustration + Schaltfläche) ist sichtbar
- Aktionsschaltfläche im Leerszustand trägt das Label für "Erstellen"
- Klick auf die Schaltfläche öffnet den Erstellen-Dialog

**Postconditions**:
- Keine Datenänderung

**Tags**: [REQ-013, listenansicht, leerszustand]

---

### TC-013-003: Listenansicht — Suche in der Tabelle filtert nach Name

**Requirement**: REQ-013 §7 DoD (Listenansicht-Filter)
**Priority**: High
**Category**: Listenansicht

**Preconditions**:
- Nutzer ist eingeloggt
- Zwei PlantingRuns existieren: "Tomaten Hochbeet A 2025" und "White Widow Klone Runde 3"

**Test Steps**:
1. Nutzer navigiert zu `/durchlaeufe/planting-runs`
2. Nutzer gibt im Suchfeld "Tomaten" ein und wartet 300ms

**Expected Results**:
- Tabelle zeigt nur die Zeile "Tomaten Hochbeet A 2025"
- Zeile "White Widow Klone Runde 3" ist nicht mehr sichtbar

**Postconditions**:
- Keine Datenänderung

**Tags**: [REQ-013, listenansicht, suche]

---

### TC-013-004: Listenansicht — Klick auf Zeile navigiert zur Detailseite

**Requirement**: REQ-013 §4.1
**Priority**: High
**Category**: Navigation

**Preconditions**:
- Nutzer ist eingeloggt
- Mindestens ein PlantingRun "Tomaten Hochbeet A 2025" existiert

**Test Steps**:
1. Nutzer navigiert zu `/durchlaeufe/planting-runs`
2. Nutzer klickt auf die Tabellenzeile "Tomaten Hochbeet A 2025"

**Expected Results**:
- Browser navigiert zu `/durchlaeufe/planting-runs/{key}` des angeklickten Runs
- Detailseite lädt und zeigt den Titel "Tomaten Hochbeet A 2025"
- Breadcrumbs zeigen: Dashboard > Pflanzdurchläufe > Tomaten Hochbeet A 2025

**Postconditions**:
- Keine Datenänderung

**Tags**: [REQ-013, navigation, breadcrumb]

---

## Gruppe 2: Erstellen-Dialog — Monokultur (Happy Path)

### TC-013-005: Monokultur-Run erstellen (vollständiges Formular)

**Requirement**: REQ-013 §4.1, §7 DoD Szenario 1, Typ-Validierung
**Priority**: Critical
**Category**: Happy Path

**Preconditions**:
- Nutzer ist eingeloggt
- Species "Solanum lycopersicum" und Cultivar "San Marzano" existieren
- Erfahrungsstufe: beliebig (Basisfelder sind immer sichtbar)

**Test Steps**:
1. Nutzer navigiert zu `/durchlaeufe/planting-runs`
2. Nutzer klickt auf Schaltfläche "Erstellen"
3. Dialog "Pflanzdurchlauf erstellen" öffnet sich
4. Nutzer gibt im Feld "Name" den Wert "Tomaten Hochbeet A 2025" ein
5. Nutzer belässt "Typ" auf "Monokultur" (Default)
6. In der Eintrags-Zeile (Entries) wählt Nutzer im Dropdown "Art" den Eintrag "Solanum lycopersicum"
7. Nutzer wählt im Dropdown "Sorte" den Eintrag "San Marzano"
8. Nutzer gibt im Feld "Anzahl" den Wert "20" ein
9. Das Feld "ID-Präfix" ist automatisch auf "SOL" vorbelegt (aus Gattungsname) — Nutzer ändert es auf "TOM"
10. Nutzer klickt auf Schaltfläche "Erstellen"

**Expected Results**:
- Dialog schließt sich
- Erfolgsmeldung (Snackbar/Notification) erscheint mit Bestätigung der Erstellung
- In der Liste erscheint ein neuer Eintrag "Tomaten Hochbeet A 2025" mit Status-Chip "Geplant"
- Spalte "Geplante Anzahl" zeigt "20"

**Postconditions**:
- PlantingRun "Tomaten Hochbeet A 2025" mit Status `planned` und actual_quantity=0 existiert im System

**Tags**: [REQ-013, erstellen, monokultur, happy-path]

---

### TC-013-006: Erstellen-Dialog — ID-Präfix wird automatisch aus Gattungsname generiert

**Requirement**: REQ-013 §3 (Engine-Logik generate_plant_ids, id_prefix), Frontend EntryRow-Logik
**Priority**: Medium
**Category**: Happy Path

**Preconditions**:
- Nutzer ist eingeloggt
- Species "Solanum lycopersicum" (Gattung: Solanum) existiert

**Test Steps**:
1. Nutzer öffnet den Erstellen-Dialog
2. Nutzer wählt im Eintrags-Dropdown "Art" den Eintrag "Solanum lycopersicum"

**Expected Results**:
- Das Feld "ID-Präfix" wird automatisch auf "SOL" gesetzt (erste 3 Buchstaben des Gattungsnamens in Großbuchstaben)

**Postconditions**:
- Keine Datenänderung

**Tags**: [REQ-013, erstellen, id-prefix, auto-generierung]

---

### TC-013-007: Erstellen-Dialog — ID-Präfix wird durch Sortenname überschrieben

**Requirement**: REQ-013 §3 (Frontend EntryRow-Logik)
**Priority**: Low
**Category**: Happy Path

**Preconditions**:
- Nutzer ist eingeloggt
- Species "Solanum lycopersicum" mit Cultivar "San Marzano" existiert

**Test Steps**:
1. Nutzer öffnet den Erstellen-Dialog
2. Nutzer wählt im Eintrags-Dropdown "Art" die Spezies "Solanum lycopersicum" (Präfix wird zu "SOL")
3. Nutzer wählt im Dropdown "Sorte" den Eintrag "San Marzano"

**Expected Results**:
- Das Feld "ID-Präfix" wird auf "SAN" aktualisiert (erste 3 Buchstaben des Sortennamens)

**Postconditions**:
- Keine Datenänderung

**Tags**: [REQ-013, erstellen, id-prefix, sorte]

---

## Gruppe 3: Erstellen-Dialog — Klon-Run

### TC-013-008: Klon-Run erstellen mit Mutterpflanzen-Key

**Requirement**: REQ-013 §7 DoD Szenario 5, Clone-Validierung
**Priority**: High
**Category**: Happy Path

**Preconditions**:
- Nutzer ist eingeloggt
- Erfahrungsstufe: Expert (source_plant_key-Feld ist ExpertiseFieldWrapper mit minLevel=expert)
- Species "Cannabis sativa" und Cultivar "White Widow" existieren

**Test Steps**:
1. Nutzer öffnet den Erstellen-Dialog
2. Nutzer gibt im Feld "Name" den Wert "White Widow Klone Runde 3" ein
3. Nutzer wählt im Feld "Typ" den Wert "Klon"
4. Das Feld "Mutterpflanzen-Key" erscheint (nur beim Typ "Klon" sichtbar)
5. Nutzer gibt im Feld "Mutterpflanzen-Key" den Wert "GROWZELT1_MOTHER_WW01" ein
6. Nutzer wählt in der Eintrags-Zeile die Art "Cannabis sativa" und Sorte "White Widow"
7. Nutzer gibt Anzahl "10" ein
8. Nutzer klickt auf "Erstellen"

**Expected Results**:
- Dialog schließt sich
- Erfolgsmeldung erscheint
- In der Liste erscheint "White Widow Klone Runde 3" mit Status "Geplant" und geplanter Anzahl 10

**Postconditions**:
- Klon-Run mit source_plant_key gespeichert

**Tags**: [REQ-013, erstellen, klon, mutterpflanze, expert-feld]

---

### TC-013-009: Klon-Typ wählen — source_plant_key-Feld erscheint dynamisch

**Requirement**: REQ-013 §3 (PlantingRunCreate Validator), Frontend-Logik `runType === 'clone'`
**Priority**: Medium
**Category**: Formvalidierung

**Preconditions**:
- Nutzer ist eingeloggt, Erfahrungsstufe Expert
- Erstellen-Dialog ist geöffnet

**Test Steps**:
1. Im geöffneten Dialog steht Typ initial auf "Monokultur"
2. Nutzer prüft: Feld "Mutterpflanzen-Key" ist NICHT sichtbar
3. Nutzer wählt im Feld "Typ" den Wert "Klon"

**Expected Results**:
- Das Feld "Mutterpflanzen-Key" erscheint nun im Formular (dynamisch eingeblendet)

**Postconditions**:
- Keine Datenänderung

**Tags**: [REQ-013, erstellen, klon, dynamisches-feld]

---

## Gruppe 4: Erstellen-Dialog — Formularvalidierung (negative Tests)

### TC-013-010: Pflichtfeld "Name" leer lassen — Fehlermeldung

**Requirement**: REQ-013 §3 (name min_length=1, max_length=200), Frontend Zod-Schema
**Priority**: High
**Category**: Formvalidierung

**Preconditions**:
- Erstellen-Dialog ist geöffnet

**Test Steps**:
1. Nutzer lässt das Feld "Name" leer
2. Nutzer gibt im ersten Eintrag eine Species aus der Liste aus
3. Nutzer gibt Anzahl "5" ein
4. Nutzer klickt auf "Erstellen"

**Expected Results**:
- Dialog bleibt geöffnet
- Unter dem Feld "Name" erscheint eine Validierungsfehlermeldung (required/min-length)
- Keine Erfolgsmeldung wird angezeigt

**Postconditions**:
- Kein PlantingRun wird erstellt

**Tags**: [REQ-013, formvalidierung, pflichtfeld, name]

---

### TC-013-011: Eintrags-Anzahl 0 — Fehlermeldung (min=1)

**Requirement**: REQ-013 §3 (quantity ge=1), Frontend Zod entrySchema `quantity: z.number().min(1)`
**Priority**: High
**Category**: Formvalidierung

**Preconditions**:
- Erstellen-Dialog ist geöffnet, eine Species ist ausgewählt

**Test Steps**:
1. Nutzer löscht den Wert im Anzahl-Feld und gibt "0" ein
2. Nutzer klickt auf "Erstellen"

**Expected Results**:
- Dialog bleibt geöffnet
- Unter dem Anzahl-Feld erscheint eine Validierungsfehlermeldung
- Kein Run wird erstellt

**Postconditions**:
- Kein PlantingRun wird erstellt

**Tags**: [REQ-013, formvalidierung, anzahl, grenzwert]

---

### TC-013-012: ID-Präfix mit ungültigem Format — Fehlermeldung (nur A-Z, 2-5 Zeichen)

**Requirement**: REQ-013 §3 (id_prefix pattern `^[A-Z]{2,5}$`), Frontend Zod `z.string().regex(/^[A-Z]{2,5}$/)`
**Priority**: Medium
**Category**: Formvalidierung

**Preconditions**:
- Erstellen-Dialog ist geöffnet, Name und Species sind ausgefüllt

**Test Steps**:
1. Nutzer löscht den automatisch gesetzten ID-Präfix und gibt "tom1" ein (enthält Zahl, nicht alle Großbuchstaben)
2. Nutzer klickt auf "Erstellen"

**Expected Results**:
- Dialog bleibt geöffnet
- Unter dem ID-Präfix-Feld erscheint eine Validierungsfehlermeldung

**Postconditions**:
- Kein PlantingRun wird erstellt

**Tags**: [REQ-013, formvalidierung, id-prefix, regex]

---

### TC-013-013: Pflichtfeld "Art" (species) leer lassen — Fehlermeldung

**Requirement**: REQ-013 §3, Frontend Zod `species_key: z.string().min(1)`
**Priority**: High
**Category**: Formvalidierung

**Preconditions**:
- Erstellen-Dialog ist geöffnet, Name ist ausgefüllt

**Test Steps**:
1. Nutzer gibt im Feld "Name" einen Wert ein
2. Nutzer gibt Anzahl "10" ein
3. Nutzer lässt das Art-Dropdown (species_key) leer / wählt keinen Eintrag
4. Nutzer klickt auf "Erstellen"

**Expected Results**:
- Dialog bleibt geöffnet
- Unter dem Art-Dropdown erscheint eine Validierungsfehlermeldung
- Kein Run wird erstellt

**Postconditions**:
- Kein PlantingRun wird erstellt

**Tags**: [REQ-013, formvalidierung, art-dropdown, pflichtfeld]

---

### TC-013-014: Backend-Fehler — Clone-Run ohne Mutterpflanzen-Key

**Requirement**: REQ-013 §3 (validate_run_type_constraints: source_plant_key Pflicht bei clone), §4 Fehlerbehandlung 422
**Priority**: High
**Category**: Fehlermeldung

**Preconditions**:
- Nutzer ist eingeloggt, Erfahrungsstufe Expert
- Erstellen-Dialog ist geöffnet

**Test Steps**:
1. Nutzer gibt Name "Test Klon" ein
2. Nutzer wählt Typ "Klon"
3. Nutzer lässt das Feld "Mutterpflanzen-Key" absichtlich leer
4. Nutzer füllt die übrigen Pflichtfelder aus (Art, Anzahl, ID-Präfix)
5. Nutzer klickt auf "Erstellen"

**Expected Results**:
- Eine Fehlerbenachrichtigung erscheint (Snackbar oder Alert)
- Die Fehlermeldung enthält einen Hinweis, dass der Mutterpflanzen-Key für Klon-Durchläufe erforderlich ist
- Dialog bleibt geöffnet
- Kein Run wird erstellt

**Postconditions**:
- Kein PlantingRun wird erstellt

**Tags**: [REQ-013, fehlermeldung, klon, validierung-422]

---

### TC-013-015: Backend-Fehler — Entry-Quantity stimmt nicht mit planned_quantity überein

**Requirement**: REQ-013 §3 Quantity-Konsistenz (Summe Entry-Quantities = planned_quantity), §4 Fehlerbehandlung 400
**Priority**: High
**Category**: Fehlermeldung

**Preconditions**:
- Nutzer ist eingeloggt
- Erstellen-Dialog ist geöffnet

**Test Steps**:
1. Nutzer gibt Name "Testlauf" und Typ "Monokultur" ein
2. Nutzer füllt Eintrag aus: Art ausgewählt, Anzahl "15" eingetragen, ID-Präfix gesetzt
3. Das Feld "Geplante Gesamtanzahl" (planned_quantity) ist auf "20" gesetzt (vom Formular abweichend)
4. Nutzer klickt auf "Erstellen"

**Expected Results**:
- Eine Fehlerbenachrichtigung erscheint
- Hinweis: Summe der Eintrag-Mengen muss der geplanten Gesamtanzahl entsprechen
- Dialog bleibt geöffnet, kein Run wird erstellt

**Postconditions**:
- Kein PlantingRun wird erstellt

**Tags**: [REQ-013, fehlermeldung, quantity-konsistenz, validierung]

---

### TC-013-016: Erfahrungsstufe Beginner — Felder Typ, Standort, Notizen ausgeblendet

**Requirement**: REQ-013 §7 DoD, Frontend ExpertiseFieldWrapper (`plantingRunFieldConfig`)
**Priority**: Medium
**Category**: Erfahrungsstufe

**Preconditions**:
- Nutzer ist eingeloggt, Erfahrungsstufe: Beginner
- Erstellen-Dialog ist geöffnet

**Test Steps**:
1. Nutzer prüft das geöffnete Formular ohne "Alle Felder anzeigen" aktiviert zu haben

**Expected Results**:
- Felder, die unter höheren Erfahrungsstufen versteckt sind (run_type, site_key, location_key, notes, substrate_batch_key), sind NICHT sichtbar
- Nur Basisfelder (Name, geplantes Startdatum, Eintrags-Zeile) sind sichtbar
- Toggle-Element "Alle Felder anzeigen" ist sichtbar (da Level nicht Expert)

**Postconditions**:
- Keine Datenänderung

**Tags**: [REQ-013, erfahrungsstufe, beginner, feldkonfiguration]

---

### TC-013-017: "Alle Felder anzeigen" Toggle schaltet Expertenfelder ein

**Requirement**: REQ-013 Frontend ShowAllFieldsToggle, ExpertiseFieldWrapper
**Priority**: Medium
**Category**: Erfahrungsstufe

**Preconditions**:
- Nutzer ist eingeloggt, Erfahrungsstufe: Beginner oder Intermediate
- Erstellen-Dialog ist geöffnet

**Test Steps**:
1. Nutzer klickt auf den Toggle "Alle Felder anzeigen"

**Expected Results**:
- Alle ExpertiseFieldWrapper-Felder werden eingeblendet (run_type, site_key, location_key, notes, substrate_batch_key)
- Toggle zeigt aktiven Zustand

**Postconditions**:
- Keine Datenänderung

**Tags**: [REQ-013, erfahrungsstufe, toggle, felder-einblenden]

---

## Gruppe 5: Detailseite — Tab "Details"

### TC-013-018: Detailseite — Summary-Bar zeigt Kern-Metadaten

**Requirement**: REQ-013 §4.1 (GET planting-runs/{key}), Frontend PlantingRunDetailsTab
**Priority**: Critical
**Category**: Detailansicht

**Preconditions**:
- PlantingRun "Tomaten Hochbeet A 2025" (status: active, planned_quantity: 20, actual_quantity: 20, Location: "Hochbeet A") existiert

**Test Steps**:
1. Nutzer navigiert zu `/durchlaeufe/planting-runs/{key}` des Runs
2. Tab "Details" ist standardmäßig aktiv

**Expected Results**:
- Summary-Bar (`data-testid="run-summary-bar"`) zeigt:
  - Typ: "Monokultur"
  - Geplante Anzahl: 20
  - Tatsächliche Anzahl: 20
  - Gestartet am: Datum in lokalem Format
  - Standort: Link zu "Hochbeet A" (navigierbar zu `/standorte/locations/{key}`)
- Status-Chip "Aktiv" (blau) im Header neben dem Titel sichtbar
- Bearbeiten-IconButton (Stift) ist im Header sichtbar

**Postconditions**:
- Keine Datenänderung

**Tags**: [REQ-013, detailansicht, summary-bar, metadata]

---

### TC-013-019: Detailseite — Eintrags-Tabelle zeigt Artenzusammensetzung

**Requirement**: REQ-013 §4.2 (GET entries), Frontend PlantingRunDetailsTab Eintrags-Tabelle
**Priority**: High
**Category**: Detailansicht

**Preconditions**:
- PlantingRun "Tomaten Hochbeet A 2025" (status: active) mit Entry (Solanum lycopersicum / San Marzano, Anzahl: 20, Abstand: 50 cm) existiert

**Test Steps**:
1. Nutzer öffnet die Detailseite des Runs
2. Tab "Details" ist aktiv, Nutzer scrollt zur Eintrags-Tabelle

**Expected Results**:
- Tabelle "Einträge" zeigt 1 Zeile
- Zeile zeigt: Art = "Solanum lycopersicum" (oder Common Name), Sorte = "San Marzano", Anzahl = 20, ID-Präfix = "TOM", Abstand = "50 cm"

**Postconditions**:
- Keine Datenänderung

**Tags**: [REQ-013, detailansicht, einträge-tabelle, monokultur]

---

### TC-013-020: Detailseite — Notizen-Karte wird angezeigt wenn vorhanden

**Requirement**: REQ-013 §3 (notes Feld), Frontend PlantingRunDetailsTab
**Priority**: Low
**Category**: Detailansicht

**Preconditions**:
- PlantingRun mit Notizen-Text "Erste Runde San Marzano für Passata-Produktion" existiert

**Test Steps**:
1. Nutzer öffnet die Detailseite des Runs
2. Tab "Details" ist aktiv

**Expected Results**:
- Eine Karte mit Überschrift "Notizen" zeigt den Text "Erste Runde San Marzano für Passata-Produktion"

**Postconditions**:
- Keine Datenänderung

**Tags**: [REQ-013, detailansicht, notizen]

---

## Gruppe 6: Detailseite — Tab "Pflanzen" und Dual-Modell

### TC-013-021: Pflanzen-Tab — Leerszustand bei Status "geplant" zeigt Aktionsschaltfläche

**Requirement**: REQ-013 §7 DoD (Batch-Erstellung), Frontend PlantingRunPlantsTab
**Priority**: High
**Category**: Detailansicht

**Preconditions**:
- PlantingRun im Status `planned` (keine Pflanzen erstellt) existiert

**Test Steps**:
1. Nutzer öffnet die Detailseite des geplanten Runs
2. Nutzer klickt auf Tab "Pflanzen"

**Expected Results**:
- Tab zeigt einen Leerszustand mit der Meldung "Noch keine Pflanzen"
- Eine Aktionsschaltfläche "Pflanzen anlegen" ist sichtbar
- Klick auf diese Schaltfläche öffnet einen Bestätigungs-Dialog

**Postconditions**:
- Keine Datenänderung

**Tags**: [REQ-013, pflanzen-tab, leerszustand, batch-erstellung]

---

### TC-013-022: Pflanzen-Tab — Pflanzenliste nach Batch-Erstellung

**Requirement**: REQ-013 §4.3 (create-plants), §7 DoD Batch-Erstellung
**Priority**: Critical
**Category**: Detailansicht

**Preconditions**:
- PlantingRun "Tomaten Hochbeet A 2025" (status: active, 20 Pflanzen vorhanden: HOCHBEETA_TOM_01…20)

**Test Steps**:
1. Nutzer öffnet die Detailseite des Runs
2. Nutzer klickt auf Tab "Pflanzen"

**Expected Results**:
- Tab-Überschrift zeigt "(20)" neben dem Label
- Tabelle zeigt 20 Zeilen
- Jede Zeile enthält: Instance-ID (z.B. HOCHBEETA_TOM_01), Gepflanzt am, Entfernt am (—), Abgetrennt am (—)
- Die aktuelle Phase wird NICHT pro Pflanze angezeigt (Phase liegt auf Run-Ebene)
- Jede Zeile hat eine "Abtrennen"-Schaltfläche (da Run status=active)
- Jede Zeile hat einen "Öffnen"-IconButton (externes Link-Symbol) zum Navigieren zur Pflanzdetailseite

**Postconditions**:
- Keine Datenänderung

**Tags**: [REQ-013, pflanzen-tab, pflanzenliste, batch-erstellt, dual-modell]

---

### TC-013-023: Pflanzen-Tab — Pflanze im Run zeigt KEINE eigenen Phasen-/Task-/Pflege-Steuerelemente

**Requirement**: REQ-013 §1.1 Dual-Modell ("Keine Einzelbearbeitung im Run"), §7 DoD
**Priority**: High
**Category**: Detailansicht

**Preconditions**:
- PlantingRun (status: active) mit mindestens einer Pflanze existiert
- Nutzer öffnet die Detailseite einer einzelnen PlantInstance, die einem aktiven Run zugehört

**Test Steps**:
1. Nutzer navigiert zur Pflanzdetailseite einer Pflanze, die Mitglied eines aktiven Runs ist (z.B. `/pflanzen/plant-instances/{key}`)
2. Nutzer prüft die verfügbaren Tabs und Aktionen auf der Detailseite

**Expected Results**:
- Kein "Phasenwechsel"-Button für diese Pflanze sichtbar (Phase kommt vom Run)
- Kein eigenes Task-Management für diese Pflanze sichtbar
- Kein eigenes Pflege-Profil-Management sichtbar
- Ein Hinweis-Banner zeigt an, dass diese Pflanze Teil eines aktiven Runs ist und über den Run verwaltet wird
- Ein Link zum übergeordneten PlantingRun ist sichtbar

**Postconditions**:
- Keine Datenänderung

**Tags**: [REQ-013, pflanzen-tab, dual-modell, keine-einzelbearbeitung, run-managed]

---

### TC-013-024: Pflanzen-Tab — Navigation zur Pflanzdetailseite über externe Link-Schaltfläche

**Requirement**: REQ-013 §4.4 (GET plants), Frontend Navigation zu `/pflanzen/plant-instances/{key}`
**Priority**: Medium
**Category**: Navigation

**Preconditions**:
- PlantingRun mit mindestens einer Pflanze (z.B. HOCHBEETA_TOM_01) existiert und ist aktiv

**Test Steps**:
1. Nutzer öffnet den Pflanzen-Tab der Detailseite
2. Nutzer klickt auf den externen Link-IconButton (OpenInNew) der ersten Pflanze

**Expected Results**:
- Browser navigiert zu `/pflanzen/plant-instances/{key}` der angeklickten Pflanze
- Pflanzdetailseite lädt und zeigt die Instance-ID (z.B. HOCHBEETA_TOM_01)

**Postconditions**:
- Keine Datenänderung

**Tags**: [REQ-013, pflanzen-tab, navigation, pflanzdetail]

---

## Gruppe 7: Batch-Operationen von der Detailseite

### TC-013-025: Batch-Erstellung starten (Pflanzen anlegen — geplanter Run)

**Requirement**: REQ-013 §4.3 (create-plants), §7 DoD Batch-Erstellung, Szenario 1
**Priority**: Critical
**Category**: Zustandswechsel

**Preconditions**:
- PlantingRun "Tomaten Hochbeet A 2025" (status: planned, planned_quantity: 20) existiert
- Kein Pflanzen existieren noch

**Test Steps**:
1. Nutzer öffnet die Detailseite des Runs (Status: "Geplant")
2. Schaltfläche "Pflanzen anlegen" (create-plants) ist im Header sichtbar
3. Nutzer klickt auf "Pflanzen anlegen"
4. Ein Bestätigungs-Dialog erscheint mit der Frage zur Anlage von 20 Pflanzen
5. Nutzer klickt auf "Bestätigen"

**Expected Results**:
- Dialog schließt sich
- Erfolgsmeldung erscheint: "20 Pflanzen wurden erstellt" (oder ähnliche i18n-Formulierung mit count=20)
- Status-Chip in der Header-Zeile wechselt von "Geplant" (grau) zu "Aktiv" (blau)
- Im Pflanzen-Tab sind nun 20 Pflanzen mit auto-generierten IDs sichtbar
- Spalte "Tatsächliche Anzahl" in der Summary-Bar zeigt 20
- Schaltfläche "Pflanzen anlegen" ist nicht mehr sichtbar (ersetzt durch Batch-Aktionen)

**Postconditions**:
- 20 PlantInstances mit IDs nach Schema `{LOCATION}_{PREFIX}_{SEQ:02d}` existieren
- Run hat status=active
- Phase liegt auf dem Run, NICHT auf den einzelnen Pflanzen

**Tags**: [REQ-013, batch-erstellung, zustandswechsel, planned-zu-active]

---

### TC-013-026: Run-Level Phasenwechsel öffnen und Zielphase wählen

**Requirement**: REQ-013 §4.3 (transition), §7 DoD Szenario 2
**Priority**: Critical
**Category**: Dialog

**Preconditions**:
- PlantingRun (status: active) mit 20 Pflanzen, Run-Phase "vegetative", existiert
- Die Spezies hat eine definierte nächste Phase "flowering" nach "vegetative"

**Test Steps**:
1. Nutzer öffnet die Detailseite des aktiven Runs
2. Nutzer klickt auf Schaltfläche "Phasenwechsel" (SwapHoriz-Icon)
3. Dialog "Phasenwechsel" öffnet sich (`data-testid="run-phase-transition-dialog"`)
4. Dialog zeigt ein Dropdown mit verfügbaren Zielphasen (nächste Phase in der Sequenz)
5. Nutzer wählt im Dropdown "flowering" (inkl. typischer Dauer in Tagen)
6. Ein gelber Warn-Alert erscheint: Bestätigung dass alle Pflanzen im Run übergehen
7. Nutzer klickt auf "Bestätigen"

**Expected Results**:
- Dialog schließt sich
- Erfolgsmeldung erscheint mit der neuen Phase ("Run wechselt zu: Blüte")
- Im Details-Tab zeigt die Summary-Bar die neue Phase "flowering"
- Im Pflanzen-Tab wird kein individueller Phasen-Chip pro Pflanze geändert (Phase lebt auf Run)

**Postconditions**:
- Run hat current_phase_key="flowering"
- Keine eigenen current_phase-Edges auf den Pflanzen

**Tags**: [REQ-013, run-phasenübergang, dialog, zustandswechsel, run-level]

---

### TC-013-027: Run-Level Phasenwechsel — Bestätigungs-Schaltfläche deaktiviert ohne Zielphase

**Requirement**: REQ-013 Frontend (disabled={!targetPhaseKey || saving})
**Priority**: Medium
**Category**: Formvalidierung

**Preconditions**:
- Phasenwechsel-Dialog ist geöffnet

**Test Steps**:
1. Dialog ist geöffnet, kein Wert im Zielphase-Dropdown ausgewählt

**Expected Results**:
- Schaltfläche "Bestätigen" ist deaktiviert (disabled)
- Nach Auswahl einer Zielphase aus dem Dropdown wird die Schaltfläche aktiviert

**Postconditions**:
- Keine Datenänderung

**Tags**: [REQ-013, phasenwechsel, button-zustand, validierung]

---

### TC-013-028: Run beenden — Dialog mit Status-Auswahl (Abgebrochen / Abgeschlossen)

**Requirement**: REQ-013 §3 (ALLOWED_STATUS_TRANSITIONS: active→cancelled | completed), Frontend EndRun-Dialog
**Priority**: Critical
**Category**: Zustandswechsel

**Preconditions**:
- PlantingRun (status: active) mit Pflanzen existiert

**Test Steps**:
1. Nutzer öffnet die Detailseite des aktiven Runs
2. Nutzer klickt auf Schaltfläche "Run beenden" (StopCircle-Icon, rot)
3. Dialog "Run beenden" öffnet sich
4. Dialog zeigt Anzahl der aktiven Pflanzen
5. ToggleButtonGroup bietet Auswahl: "Abgebrochen" (warning) | "Abgeschlossen" (success)
6. Nutzer wählt "Abgeschlossen"
7. Nutzer klickt auf Schaltfläche "Run beenden"

**Expected Results**:
- Dialog schließt sich
- Erfolgsmeldung erscheint mit Anzahl entfernter Pflanzen und neuem Status "Abgeschlossen"
- Status-Chip in der Header-Zeile wechselt zu "Abgeschlossen" (grün)
- Schaltflächen "Phasenwechsel" und "Run beenden" sind nicht mehr sichtbar (Terminal-Status)

**Postconditions**:
- Run hat status=completed
- Alle Pflanzen haben removed_on gesetzt

**Tags**: [REQ-013, run-beenden, zustandswechsel, terminal-status]

---

### TC-013-029: Run im Status "harvesting" — Endstatus ist standardmäßig "Abgeschlossen"

**Requirement**: REQ-013 §3 (ALLOWED_STATUS_TRANSITIONS: harvesting→completed | cancelled), Frontend-Logik
**Priority**: Medium
**Category**: Zustandswechsel

**Preconditions**:
- PlantingRun (status: harvesting) existiert

**Test Steps**:
1. Nutzer öffnet die Detailseite des Runs (status=harvesting)
2. Nutzer klickt auf "Run beenden"

**Expected Results**:
- Im EndRun-Dialog ist die Auswahl standardmäßig auf "Abgeschlossen" (completed) gesetzt (nicht "Abgebrochen")

**Postconditions**:
- Keine Datenänderung (Dialog noch nicht bestätigt)

**Tags**: [REQ-013, run-beenden, harvesting, default-status]

---

## Gruppe 8: Individuelle Pflanzenabtrennung (detach)

### TC-013-030: Einzelne Pflanze vom Run abtrennen — Kategorie-Pflichtfeld

**Requirement**: REQ-013 §4.4 (detach), §7 DoD Szenario 3, DetachPlantRequest (category Pflichtfeld)
**Priority**: High
**Category**: Zustandswechsel

**Preconditions**:
- PlantingRun (status: active) mit mindestens 2 Pflanzen existiert

**Test Steps**:
1. Nutzer öffnet die Detailseite des aktiven Runs
2. Nutzer navigiert zum Tab "Pflanzen"
3. Nutzer klickt auf die Schaltfläche "Abtrennen" neben einer Pflanze (z.B. HOCHBEETA_TOM_05)
4. Ein Dialog "Pflanze abtrennen" öffnet sich
5. Das Dropdown "Kategorie" ist sichtbar mit Optionen: disease, pest, stunted, male_plant, selection, transplant, death, other
6. Das Textfeld "Begründung" (Freitext) ist sichtbar
7. Nutzer wählt Kategorie "disease"
8. Nutzer gibt in das Textfeld "Braunfäule-Verdacht, zur separaten Behandlung" ein
9. Nutzer klickt auf "Abtrennen bestätigen"

**Expected Results**:
- Dialog schließt sich
- Erfolgsmeldung erscheint: "Pflanze abgetrennt" (plantDetached)
- In der Pflanzenliste zeigt die betroffene Pflanze in der Spalte "Abgetrennt am" nun das aktuelle Datum
- Die "Abtrennen"-Schaltfläche verschwindet für diese Pflanze
- Die Pflanze ist weiterhin in der Liste sichtbar (nicht gelöscht)

**Postconditions**:
- `detached_at` und `detach_category=disease` sind auf der `run_contains`-Edge gesetzt
- PlantInstance selbst bleibt bestehen mit kopierter Phase und ist individuell verwaltbar

**Tags**: [REQ-013, abtrennen, detach, kategorie-pflichtfeld, soft-binding]

---

### TC-013-031: Abtrennen-Dialog — "Bestätigen" deaktiviert ohne Kategorie-Auswahl

**Requirement**: REQ-013 §3 (DetachPlantRequest.category Pflichtfeld), Frontend-Validierung
**Priority**: Medium
**Category**: Formvalidierung

**Preconditions**:
- Abtrennen-Dialog ist geöffnet für eine Pflanze

**Test Steps**:
1. Dialog ist geöffnet, kein Wert im Kategorie-Dropdown ausgewählt
2. Nutzer lässt das Textfeld "Begründung" leer

**Expected Results**:
- Schaltfläche "Abtrennen bestätigen" ist deaktiviert (disabled)
- Nach Auswahl einer Kategorie und Eingabe einer Begründung wird die Schaltfläche aktiviert

**Postconditions**:
- Keine Datenänderung

**Tags**: [REQ-013, abtrennen, button-zustand, kategorie-validierung]

---

### TC-013-032: Nach Detach — Pflanze erscheint als Standalone mit eigener Phase und vollem Management

**Requirement**: REQ-013 §1.1 Dual-Modell, §7 DoD Szenario 3 (Detach → Standalone)
**Priority**: High
**Category**: Zustandswechsel

**Preconditions**:
- Eine Pflanze (HOCHBEETA_TOM_05) wurde soeben vom Run (Run-Phase: "vegetative") abgetrennt

**Test Steps**:
1. Nutzer navigiert zur Pflanzdetailseite von HOCHBEETA_TOM_05

**Expected Results**:
- Pflanzdetailseite zeigt KEINE Hinweismeldung mehr, dass die Pflanze Teil eines aktiven Runs ist
- Die Phase "vegetative" ist auf der Pflanzdetailseite sichtbar (vom Run kopiert)
- Phasenwechsel-Button ist sichtbar und aktiv (Pflanze ist jetzt standalone)
- Task-Management-Tab ist zugänglich
- Pflege-Profil-Tab ist zugänglich
- Kein Link zum vorherigen Run ist mehr in der Hauptsteuerung sichtbar

**Postconditions**:
- PlantInstance hat eigene current_phase_key="vegetative" und ist vollständig eigenständig verwaltbar

**Tags**: [REQ-013, abtrennen, standalone, dual-modell, phase-kopie]

---

### TC-013-033: Run-Zähler nach Detach aktualisiert

**Requirement**: REQ-013 §1.2 Szenario 3, §7 DoD (active_plant_count berechnet)
**Priority**: Medium
**Category**: Zustandswechsel

**Preconditions**:
- PlantingRun (status: active) mit 20 aktiven Pflanzen existiert
- Pflanze HOCHBEETA_TOM_05 wird vom Run abgetrennt (Kategorie: disease)

**Test Steps**:
1. Nutzer bleibt auf der Detailseite des Runs
2. Nutzer navigiert zum Tab "Details"

**Expected Results**:
- Summary-Bar zeigt "Tatsächliche Anzahl": 19 (aktualisiert, vorher 20)
- Im Pflanzen-Tab zeigt die Tabelle 20 Zeilen (19 aktiv + 1 abgetrennt, mit Datum in "Abgetrennt am")

**Postconditions**:
- Run.active_plant_count = 19

**Tags**: [REQ-013, abtrennen, zähler-aktualisierung, summary-bar]

---

### TC-013-034: Abtrennen-Schaltfläche nur bei aktivem Run sichtbar

**Requirement**: REQ-013 Frontend-Logik `!r.detached_at && run?.status === 'active'`
**Priority**: Medium
**Category**: Detailansicht

**Preconditions**:
- PlantingRun (status: completed) mit Pflanzen existiert

**Test Steps**:
1. Nutzer öffnet die Detailseite des abgeschlossenen Runs
2. Nutzer navigiert zum Tab "Pflanzen"

**Expected Results**:
- Keine "Abtrennen"-Schaltfläche ist in der Pflanzenliste sichtbar (Run ist nicht active)

**Postconditions**:
- Keine Datenänderung

**Tags**: [REQ-013, abtrennen, button-zustand, completed-run]

---

## Gruppe 9: Löschen (nur Status "geplant")

### TC-013-035: Löschen-Dialog erscheint und Löschen wird bestätigt (geplanter Run)

**Requirement**: REQ-013 §4.1 (DELETE nur status=planned), §7 DoD
**Priority**: High
**Category**: Dialog

**Preconditions**:
- PlantingRun (status: planned) existiert
- Nutzer hat Admin-Rolle (DELETE erfordert Admin gemäß §5)

**Test Steps**:
1. Nutzer öffnet die Detailseite des geplanten Runs
2. Schaltfläche "Löschen" (roter Button mit Papierkorb) ist sichtbar
3. Nutzer klickt auf "Löschen"
4. Bestätigungs-Dialog erscheint mit der Frage: "Sind Sie sicher, dass Sie '[Name]' löschen möchten? Diese Aktion kann nicht rückgängig gemacht werden."
5. Nutzer klickt auf "Löschen bestätigen" (destructive Button)

**Expected Results**:
- Dialog schließt sich
- Erfolgsmeldung erscheint
- Browser navigiert zurück zu `/durchlaeufe/planting-runs`
- Der gelöschte Run erscheint nicht mehr in der Liste

**Postconditions**:
- PlantingRun ist aus dem System entfernt

**Tags**: [REQ-013, löschen, bestätigung-dialog, planned-status]

---

### TC-013-036: Löschen-Schaltfläche nicht sichtbar bei aktivem Run

**Requirement**: REQ-013 §4.1 (DELETE nur status=planned → 409 bei aktiven Runs), Frontend-Bedingung `run?.status === 'planned'`
**Priority**: High
**Category**: Detailansicht

**Preconditions**:
- PlantingRun (status: active) existiert

**Test Steps**:
1. Nutzer öffnet die Detailseite des aktiven Runs

**Expected Results**:
- Die rote "Löschen"-Schaltfläche ist NICHT sichtbar
- Stattdessen sind "Phasenwechsel" und "Run beenden" sichtbar

**Postconditions**:
- Keine Datenänderung

**Tags**: [REQ-013, löschen, button-zustand, active-status]

---

### TC-013-037: Löschen abbrechen — Run bleibt erhalten

**Requirement**: REQ-013 §4.1, Frontend ConfirmDialog
**Priority**: Medium
**Category**: Dialog

**Preconditions**:
- PlantingRun (status: planned) existiert

**Test Steps**:
1. Nutzer klickt auf "Löschen"
2. Bestätigungs-Dialog erscheint
3. Nutzer klickt auf "Abbrechen"

**Expected Results**:
- Dialog schließt sich
- Nutzer verbleibt auf der Detailseite
- Run ist unverändert erhalten

**Postconditions**:
- Keine Datenänderung

**Tags**: [REQ-013, löschen, abbrechen, dialog]

---

## Gruppe 10: Bearbeiten-Dialog

### TC-013-038: Bearbeiten-Dialog öffnet sich mit vorhandenen Werten

**Requirement**: REQ-013 §4.1 (PUT Metadaten), Frontend PlantingRunEditDialog
**Priority**: High
**Category**: Dialog

**Preconditions**:
- PlantingRun "Tomaten Hochbeet A 2025" (mit Notizen, Standort zugewiesen) existiert

**Test Steps**:
1. Nutzer öffnet die Detailseite des Runs
2. Nutzer klickt auf den Bearbeiten-IconButton (Stift-Symbol) im Header

**Expected Results**:
- Dialog "Pflanzdurchlauf bearbeiten" öffnet sich
- Felder "Name", "Geplantes Startdatum", "Standort", "Notizen" sind mit aktuellen Werten vorbelegt
- Schaltfläche "Speichern" ist sichtbar

**Postconditions**:
- Keine Datenänderung

**Tags**: [REQ-013, bearbeiten, dialog, vorbelegt]

---

### TC-013-039: Bearbeiten — Name ändern und speichern

**Requirement**: REQ-013 §4.1 (PUT name, notes, planned_start_date)
**Priority**: High
**Category**: Happy Path

**Preconditions**:
- Bearbeiten-Dialog ist geöffnet für einen beliebigen Run

**Test Steps**:
1. Nutzer löscht den aktuellen Namen und gibt "Tomaten Hochbeet A 2025 (aktualisiert)" ein
2. Nutzer klickt auf "Speichern"

**Expected Results**:
- Dialog schließt sich
- Erfolgsmeldung "Gespeichert" erscheint
- Seiten-Titel der Detailseite aktualisiert sich auf den neuen Namen
- Breadcrumb zeigt den neuen Namen

**Postconditions**:
- Run hat den neuen Namen

**Tags**: [REQ-013, bearbeiten, name-ändern, happy-path]

---

### TC-013-040: Bearbeiten — Standort-Feld löscht Location wenn Site gewechselt wird

**Requirement**: REQ-013 Frontend PlantingRunEditDialog (skipLocationReset-Logik)
**Priority**: Medium
**Category**: Formvalidierung

**Preconditions**:
- Bearbeiten-Dialog ist geöffnet, ein Standort ist zugewiesen (Site + Location)

**Test Steps**:
1. Nutzer wählt im Dropdown "Standort (Site)" einen anderen Standort aus
2. Nutzer beobachtet das Feld "Standort (Location)"

**Expected Results**:
- Das Feld "Standort (Location)" wird zurückgesetzt auf keinen Wert (null / leere Auswahl)
- Nutzer muss eine neue Location aus dem Baum des neuen Sites wählen

**Postconditions**:
- Keine Datenänderung (Dialog noch nicht gespeichert)

**Tags**: [REQ-013, bearbeiten, standort, cascading-reset]

---

### TC-013-041: Bearbeiten — Pflichtfeld "Name" leer lassen verhindert Speichern

**Requirement**: REQ-013 §3 (PlantingRunUpdate name min_length=1), Frontend Zod editSchema
**Priority**: Medium
**Category**: Formvalidierung

**Preconditions**:
- Bearbeiten-Dialog ist geöffnet

**Test Steps**:
1. Nutzer löscht den gesamten Namen
2. Nutzer klickt auf "Speichern"

**Expected Results**:
- Unter dem Namensfeld erscheint eine Validierungsfehlermeldung
- Dialog bleibt geöffnet
- Keine Erfolgsmeldung erscheint

**Postconditions**:
- Keine Datenänderung

**Tags**: [REQ-013, bearbeiten, formvalidierung, name-pflichtfeld]

---

## Gruppe 11: Tab "Phasen"

### TC-013-042: Phasen-Tab zeigt Run-Level Phasen-Timeline

**Requirement**: REQ-013 §4.3 (transition), §7 DoD (Run-Level Phasenwechsel), Frontend RunPhaseEditor
**Priority**: High
**Category**: Detailansicht

**Preconditions**:
- PlantingRun (status: active) mit Species die über eine Lifecycle-Konfiguration mit Phasen verfügt

**Test Steps**:
1. Nutzer öffnet die Detailseite des aktiven Runs
2. Nutzer klickt auf Tab "Phasen" (`data-testid="phases-tab"`)

**Expected Results**:
- Tab-Inhalt lädt
- Eine visuelle Phasen-Timeline wird gezeigt mit den Phasen der Species des Runs
- Die aktuelle Phase des Runs ist hervorgehoben
- Der RunPhaseEditor ist sichtbar und erlaubt das Einleiten eines Phasenwechsels
- Kein Hinweis auf individuelle Pflanzen-Phasen (Phasen sind Run-Level)

**Postconditions**:
- Keine Datenänderung

**Tags**: [REQ-013, phasen-tab, run-level, phase-timeline]

---

## Gruppe 12: Tab "Nährstoff & Gießen"

### TC-013-043: Nährstoff/Gießen-Tab ohne zugewiesenen Plan zeigt Info-Alert und Zuweisung-Schaltfläche

**Requirement**: REQ-013 §4.5 (NutrientPlan zuweisen), §7 DoD NutrientPlan-Zuweisung
**Priority**: High
**Category**: Detailansicht

**Preconditions**:
- PlantingRun (status: active) existiert, kein NutrientPlan zugewiesen

**Test Steps**:
1. Nutzer öffnet die Detailseite
2. Nutzer klickt auf Tab "Nährstoff & Gießen" (`data-testid="nutrient-plan-tab"`)

**Expected Results**:
- Info-Alert "Kein Nährstoffplan zugewiesen" erscheint
- Schaltfläche "Nährstoffplan zuweisen" ist aktiv (enabled)
- Kein Gießkalender wird angezeigt (kein Plan)

**Postconditions**:
- Keine Datenänderung

**Tags**: [REQ-013, nährstoff-tab, kein-plan, info-alert]

---

### TC-013-044: Nährstoffplan zuweisen über Zuweisung-Dialog

**Requirement**: REQ-013 §4.5 (POST nutrient-plan), §7 DoD NutrientPlan-Zuweisung
**Priority**: High
**Category**: Happy Path

**Preconditions**:
- PlantingRun (status: active) existiert, kein NutrientPlan zugewiesen
- NutrientPlan "Tomato Heavy Coco" existiert im System

**Test Steps**:
1. Nutzer navigiert zum Tab "Nährstoff & Gießen"
2. Nutzer klickt auf "Nährstoffplan zuweisen"
3. Zuweisung-Dialog öffnet sich mit einer Liste verfügbarer Nährstoffpläne
4. Nutzer wählt "Tomato Heavy Coco"
5. Nutzer bestätigt die Zuweisung im Dialog

**Expected Results**:
- Dialog schließt sich
- Erfolgsmeldung erscheint
- Tab zeigt nun den Namen des zugewiesenen Plans als Link (navigierbar zu `/duengung/plans/{key}`)
- Schaltflächen "Plan ändern" und "Plan entfernen" sind sichtbar

**Postconditions**:
- RUN_FOLLOWS_PLAN-Edge existiert zwischen Run und NutrientPlan

**Tags**: [REQ-013, nährstoff-tab, plan-zuweisung]

---

### TC-013-045: Nährstoffplan entfernen — Bestätigungs-Dialog erscheint

**Requirement**: REQ-013 §4.5 (DELETE nutrient-plan), §7 DoD NutrientPlan-Entfernung
**Priority**: High
**Category**: Dialog

**Preconditions**:
- PlantingRun (status: active) mit zugewiesenem NutrientPlan existiert

**Test Steps**:
1. Nutzer navigiert zum Tab "Nährstoff & Gießen"
2. Nutzer klickt auf "Plan entfernen" (roter Button mit Papierkorb)
3. Bestätigungs-Dialog erscheint

**Expected Results**:
- Dialog zeigt Bestätigungsfrage mit dem Namen des Plans
- Dialog ist als "destructive" gekennzeichnet (roter Bestätigen-Button)

**Postconditions**:
- Wenn bestätigt: Plan-Zuweisung wird entfernt

**Tags**: [REQ-013, nährstoff-tab, plan-entfernen, bestätigung]

---

### TC-013-046: Plan-Zuweisung deaktiviert für abgeschlossene/abgebrochene Runs

**Requirement**: REQ-013 Frontend-Bedingung `disabled={runStatus === 'completed' || runStatus === 'cancelled'}`
**Priority**: Medium
**Category**: Detailansicht

**Preconditions**:
- PlantingRun (status: completed) existiert

**Test Steps**:
1. Nutzer öffnet Tab "Nährstoff & Gießen" des abgeschlossenen Runs

**Expected Results**:
- Schaltfläche "Nährstoffplan zuweisen" (oder "Plan ändern") ist deaktiviert (disabled)

**Postconditions**:
- Keine Datenänderung

**Tags**: [REQ-013, nährstoff-tab, button-zustand, terminal-status]

---

### TC-013-047: Gießkalender wird bei zugewiesenem Plan mit WateringSchedule angezeigt

**Requirement**: REQ-013 §4.6 (GET watering-schedule), §7 DoD Gießkalender-Endpoint
**Priority**: High
**Category**: Detailansicht

**Preconditions**:
- PlantingRun (status: active) mit zugewiesenem NutrientPlan und konfiguriertem WateringSchedule (Mo/Mi/Fr) existiert

**Test Steps**:
1. Nutzer navigiert zum Tab "Nährstoff & Gießen"

**Expected Results**:
- Abschnitt "Nächste Gießtermine" (WaterDrop-Icon) zeigt den Gießkalender
- Kalender zeigt kommende Gießtermine (Mo/Mi/Fr der nächsten 14 Tage)
- Jeder Termin zeigt Datum und Schaltflächen für "Schnellbestätigung" und "Bestätigung mit Details"

**Postconditions**:
- Keine Datenänderung

**Tags**: [REQ-013, gießkalender, watering-schedule, tab-anzeige]

---

### TC-013-048: Gießkalender-Info wenn kein Plan oder kein Schedule vorhanden

**Requirement**: REQ-013 §7 DoD (Gießkalender ohne Schedule: Alert)
**Priority**: Medium
**Category**: Detailansicht

**Preconditions**:
- PlantingRun (status: active) mit zugewiesenem NutrientPlan aber OHNE WateringSchedule

**Test Steps**:
1. Nutzer navigiert zum Tab "Nährstoff & Gießen"

**Expected Results**:
- Im Abschnitt "Nächste Gießtermine" erscheint ein Info-Alert: "Kein Gießplan konfiguriert" (noPlan i18n-Key)
- Kein Kalender wird angezeigt

**Postconditions**:
- Keine Datenänderung

**Tags**: [REQ-013, gießkalender, kein-schedule, info-alert]

---

## Gruppe 13: Details-Tab — Dosierungsanzeige

### TC-013-049: Details-Tab zeigt aktuelle Dünger-Dosierungen nach zugewiesenem Plan

**Requirement**: REQ-013 §4.5, Frontend PlantingRunDetailsTab (ChannelCard, currentDosages)
**Priority**: Medium
**Category**: Detailansicht

**Preconditions**:
- PlantingRun (status: active) mit NutrientPlan, Pflanzen in Phase "vegetative", Plan hat Einträge für diese Phase

**Test Steps**:
1. Nutzer öffnet Tab "Details"

**Expected Results**:
- Abschnitt "Aktuelle Dosierung" (ScienceIcon) ist sichtbar
- Phase-Chip (z.B. "vegetative") und Wochennummer sind angezeigt
- Karten pro Liefersystem zeigen Dünger-Liste mit ml/L-Werten
- ToggleButtonGroup "ml/L" | "{Volumen} L" ist bedienbar

**Postconditions**:
- Keine Datenänderung

**Tags**: [REQ-013, details-tab, dosierung, nährstoffplan]

---

### TC-013-050: Dosierungsmodus wechseln zwischen ml/L und Gesamtvolumen

**Requirement**: REQ-013 Frontend PlantingRunDetailsTab (`dosageMode`, ToggleButtonGroup)
**Priority**: Low
**Category**: Detailansicht

**Preconditions**:
- Details-Tab mit Dosierungsanzeige ist sichtbar (NutrientPlan zugewiesen)

**Test Steps**:
1. Nutzer klickt auf ToggleButton mit Volumen-Angabe (z.B. "10 L")
2. Nutzer beobachtet Dosierungstabelle

**Expected Results**:
- Spaltenüberschrift wechselt von "ml/L" zu "ml / 10 L"
- Dosierungswerte in der Tabelle zeigen Gesamtmengen statt ml/L-Werte

**Postconditions**:
- Keine Datenänderung

**Tags**: [REQ-013, details-tab, dosierungsmodus, toggle]

---

## Gruppe 14: Pflanzen-Tagebuch (PlantDiaryEntry)

### TC-013-051: Tagebucheintrag für eine Pflanze im Run erstellen

**Requirement**: REQ-013 §4.7 (POST diary), §7 DoD Tagebuch-CRUD, Szenario 4
**Priority**: Critical
**Category**: Happy Path

**Preconditions**:
- PlantingRun (status: active) mit mindestens einer Pflanze (HOCHBEETA_TOM_05) existiert
- Nutzer hat die Pflanzdetailseite von HOCHBEETA_TOM_05 geöffnet

**Test Steps**:
1. Nutzer navigiert zur Pflanzdetailseite: `/pflanzen/plant-instances/{key}`
2. Nutzer klickt auf den Tab "Tagebuch" (`data-testid="diary-tab"`)
3. Nutzer klickt auf Schaltfläche "Tagebucheintrag hinzufügen"
4. Ein Dialog "Tagebucheintrag erstellen" öffnet sich
5. Nutzer wählt im Dropdown "Typ" den Wert "Problem"
6. Nutzer gibt im Feld "Titel" den Wert "Braune Flecken an unteren Blättern" ein
7. Nutzer gibt im Textfeld "Beschreibung" den Wert "Die unteren 3 Blätter zeigen braune Flecken, möglicherweise Septoria. Betroffene Blätter entfernt." ein
8. Nutzer gibt im Feld "Tags" die Werte "septoria, blätter, krankheit" ein
9. Nutzer klickt auf "Speichern"

**Expected Results**:
- Dialog schließt sich
- Erfolgsmeldung erscheint
- Der neue Eintrag erscheint im Tagebuch-Tab als Karte mit Typ-Icon (Problem = oranges Warnsymbol)
- Karte zeigt: Titel, Text, Tags, Erstellungsdatum und Ersteller
- Einträge sind chronologisch absteigend sortiert (neuester oben)

**Postconditions**:
- PlantDiaryEntry mit entry_type="problem" existiert, verknüpft mit HOCHBEETA_TOM_05

**Tags**: [REQ-013, tagebuch, erstellen, problem-eintrag, diary-entry]

---

### TC-013-052: Tagebuch-Tab zeigt Einträge chronologisch sortiert

**Requirement**: REQ-013 §4.7 (GET diary), §7 DoD Tagebuch-CRUD
**Priority**: High
**Category**: Detailansicht

**Preconditions**:
- Pflanze HOCHBEETA_TOM_05 hat 2 Tagebucheinträge:
  - Eintrag 1 (älter): "Braune Flecken" (problem, 2025-07-15)
  - Eintrag 2 (neuer): "Wöchentliche Messung" (measurement, 2025-07-22)

**Test Steps**:
1. Nutzer navigiert zur Pflanzdetailseite
2. Nutzer klickt auf Tab "Tagebuch"

**Expected Results**:
- Tab lädt und zeigt 2 Einträge als Karten
- Neuester Eintrag ("Wöchentliche Messung", 22.07.) steht oben
- Älterer Eintrag ("Braune Flecken", 15.07.) steht darunter
- Measurement-Karte zeigt strukturierte Messwerte (Höhe: 85 cm, Äste: 6, Stängeldurchmesser: 12 mm)
- Typ-Icons sind pro Karte erkennbar: Problem = Warnsymbol, Measurement = Lineal-/Messsymbol

**Postconditions**:
- Keine Datenänderung

**Tags**: [REQ-013, tagebuch, chronologisch, measurement-werte]

---

### TC-013-053: Tagebucheintrag bearbeiten

**Requirement**: REQ-013 §4.7 (PUT diary/{entry_key}), §7 DoD Tagebuch-CRUD
**Priority**: High
**Category**: Happy Path

**Preconditions**:
- Tagebucheintrag "Braune Flecken an unteren Blättern" (problem) für Pflanze existiert

**Test Steps**:
1. Nutzer öffnet den Tagebuch-Tab der Pflanzdetailseite
2. Nutzer klickt auf den Bearbeiten-Button (Stift-Symbol) auf der Karte "Braune Flecken"
3. Bearbeiten-Dialog öffnet sich mit vorausgefüllten Werten
4. Nutzer ändert den Text zu "Septoria bestätigt. Betroffene Blätter entfernt, Behandlung eingeleitet."
5. Nutzer klickt auf "Speichern"

**Expected Results**:
- Dialog schließt sich
- Erfolgsmeldung erscheint
- Karte im Tagebuch-Tab zeigt den aktualisierten Text
- Erstellungsdatum bleibt unverändert, "Bearbeitet am" wird aktualisiert (wenn sichtbar)

**Postconditions**:
- PlantDiaryEntry hat den neuen Text

**Tags**: [REQ-013, tagebuch, bearbeiten, eintrag-aktualisieren]

---

### TC-013-054: Tagebucheintrag löschen — Bestätigungs-Dialog

**Requirement**: REQ-013 §4.7 (DELETE diary/{entry_key}), §7 DoD Tagebuch-CRUD
**Priority**: High
**Category**: Dialog

**Preconditions**:
- Tagebucheintrag für eine Pflanze existiert

**Test Steps**:
1. Nutzer öffnet den Tagebuch-Tab der Pflanzdetailseite
2. Nutzer klickt auf den Löschen-Button (Papierkorb-Symbol) auf einer Tagebuch-Karte
3. Bestätigungs-Dialog erscheint

**Expected Results**:
- Dialog fragt: "Sind Sie sicher, dass Sie diesen Tagebucheintrag löschen möchten? Diese Aktion kann nicht rückgängig gemacht werden."
- Dialog ist als "destructive" gekennzeichnet
- Nach Bestätigung: Dialog schließt sich, Erfolgsmeldung erscheint, Karte ist aus der Liste entfernt

**Postconditions**:
- PlantDiaryEntry ist gelöscht

**Tags**: [REQ-013, tagebuch, löschen, bestätigung-dialog]

---

### TC-013-055: Tagebucheintrag — Pflichtfeld "Beschreibung" (text) leer lassen — Fehlermeldung

**Requirement**: REQ-013 §3 (PlantDiaryEntryCreate.text min_length=1), Frontend Zod-Schema
**Priority**: Medium
**Category**: Formvalidierung

**Preconditions**:
- Tagebucheintrag-Dialog ist geöffnet

**Test Steps**:
1. Nutzer wählt Typ "Beobachtung"
2. Nutzer lässt das Textfeld "Beschreibung" leer
3. Nutzer klickt auf "Speichern"

**Expected Results**:
- Dialog bleibt geöffnet
- Unter dem Textfeld erscheint eine Validierungsfehlermeldung
- Kein Eintrag wird erstellt

**Postconditions**:
- Kein PlantDiaryEntry wird erstellt

**Tags**: [REQ-013, tagebuch, formvalidierung, text-pflichtfeld]

---

### TC-013-056: Aggregiertes Run-Tagebuch zeigt Einträge aller Pflanzen

**Requirement**: REQ-013 §4.7 (GET planting-runs/{key}/diary), §7 DoD Tagebuch-Aggregation
**Priority**: High
**Category**: Detailansicht

**Preconditions**:
- PlantingRun (status: active) mit 3 Pflanzen existiert
- Pflanze TOM_05 hat 2 Einträge, Pflanze TOM_07 hat 1 Eintrag, Pflanze TOM_12 hat 0 Einträge

**Test Steps**:
1. Nutzer öffnet die Detailseite des Runs
2. Nutzer navigiert zum Tab "Tagebuch" (aggregiertes Run-Tagebuch)

**Expected Results**:
- Tab zeigt insgesamt 3 Einträge (von TOM_05 × 2 und TOM_07 × 1)
- Jede Eintrag-Karte zeigt zusätzlich die Instance-ID der Pflanze (z.B. "HOCHBEETA_TOM_05")
- Einträge sind chronologisch absteigend sortiert über alle Pflanzen hinweg
- Pflanze TOM_12 erscheint nicht (keine Einträge)

**Postconditions**:
- Keine Datenänderung

**Tags**: [REQ-013, tagebuch, aggregiert, run-tagebuch, alle-pflanzen]

---

### TC-013-057: Tagebuch-Tab für Standalone-Pflanze (ohne Run) funktioniert identisch

**Requirement**: REQ-013 §4.7 (GET plant-instances/{key}/diary), §7 DoD Tagebuch-Standalone
**Priority**: Medium
**Category**: Detailansicht

**Preconditions**:
- PlantInstance ohne aktiven Run (standalone, z.B. nach Detach oder direkt erstellt)
- Mindestens 1 Tagebucheintrag für diese Pflanze existiert

**Test Steps**:
1. Nutzer navigiert zur Pflanzdetailseite einer Standalone-Pflanze
2. Nutzer klickt auf Tab "Tagebuch"

**Expected Results**:
- Tagebuch-Tab lädt und zeigt alle Einträge
- "Tagebucheintrag hinzufügen" Schaltfläche ist vorhanden und klickbar
- Erstellen/Bearbeiten/Löschen-Funktionen arbeiten identisch wie im Run-Kontext

**Postconditions**:
- Keine Datenänderung

**Tags**: [REQ-013, tagebuch, standalone, ohne-run, dual-modell]

---

## Gruppe 15: SuccessionPlan (Staffelanbau)

### TC-013-058: SuccessionPlan erstellen — vollständiges Formular

**Requirement**: REQ-013 §1.2 Szenario 4, §7 DoD Sukzessions-Plan CRUD
**Priority**: High
**Category**: Happy Path

**Preconditions**:
- Nutzer ist eingeloggt
- Species "Lactuca sativa" (Salat) mit Cultivar "Lollo Rosso" existiert
- Location "Beet C" existiert

**Test Steps**:
1. Nutzer navigiert zu `/durchlaeufe/succession-plans` (oder klickt im Menü auf "Staffelplanung")
2. Nutzer klickt auf "Erstellen"
3. Dialog "Staffelplan erstellen" öffnet sich
4. Nutzer gibt im Feld "Name" den Wert "Salat-Staffel Beet C 2026" ein
5. Nutzer wählt Art "Lactuca sativa" und Sorte "Lollo Rosso"
6. Nutzer gibt im Feld "Intervall (Tage)" den Wert "21" ein
7. Nutzer gibt im Feld "Startdatum" den Wert "01.04.2026" ein
8. Nutzer gibt im Feld "Enddatum" den Wert "31.08.2026" ein
9. Nutzer gibt im Feld "Pflanzen pro Staffel" den Wert "12" ein
10. Nutzer wählt Location "Beet C"
11. Nutzer klickt auf "Erstellen"

**Expected Results**:
- Dialog schließt sich
- Erfolgsmeldung erscheint
- In der Liste der Staffelpläne erscheint "Salat-Staffel Beet C 2026"
- Eine Information zeigt: "8 Staffeln werden generiert" (berechnet: ceil((31.08. - 01.04.) / 21 Tage))

**Postconditions**:
- SuccessionPlan mit name="Salat-Staffel Beet C 2026" und total_batches=8 existiert
- 8 PlantingRuns mit Status "planned" wurden automatisch generiert

**Tags**: [REQ-013, succession-plan, erstellen, staffelanbau, happy-path]

---

### TC-013-059: SuccessionPlan — Automatisch generierte Staffel-Runs in Liste sichtbar

**Requirement**: REQ-013 §1.2 Szenario 4, §7 DoD Sukzessions-Run-Generierung
**Priority**: High
**Category**: Listenansicht

**Preconditions**:
- SuccessionPlan "Salat-Staffel Beet C 2026" mit 8 automatisch generierten Runs existiert

**Test Steps**:
1. Nutzer navigiert zur Detailseite des Succession-Plans
2. Nutzer scrollt zur Übersicht der generierten Staffel-Runs

**Expected Results**:
- 8 Staffel-Runs sind als Tabelle oder Karten aufgelistet
- Run 1: Name = "Salat-Staffel 1/8", Datum = "01.04.2026", Status = "Geplant"
- Run 2: Name = "Salat-Staffel 2/8", Datum = "22.04.2026", Status = "Geplant"
- Run 3: Name = "Salat-Staffel 3/8", Datum = "13.05.2026", Status = "Geplant"
- Alle 8 Runs haben Status "Geplant" (grauer Chip)
- Jeder Run ist als Link zur entsprechenden Detailseite navigierbar

**Postconditions**:
- Keine Datenänderung

**Tags**: [REQ-013, succession-plan, staffel-runs, listenansicht, auto-generiert]

---

### TC-013-060: SuccessionPlan — Staffel-Run manuell aktivieren

**Requirement**: REQ-013 §1.2 Szenario 4 (Lisa bestaetigt → Run-Status wechselt zu active)
**Priority**: High
**Category**: Zustandswechsel

**Preconditions**:
- Staffel-Run "Salat-Staffel 1/8" (status: planned) existiert

**Test Steps**:
1. Nutzer navigiert zur Detailseite des Staffel-Runs "Salat-Staffel 1/8"
2. Nutzer klickt auf "Pflanzen anlegen"
3. Bestätigungs-Dialog erscheint
4. Nutzer klickt auf "Bestätigen"

**Expected Results**:
- Erfolgsmeldung erscheint: "12 Pflanzen wurden erstellt"
- Status des Staffel-Runs wechselt von "Geplant" zu "Aktiv"
- Im Succession-Plan zeigt die Übersicht: Staffel 1 = "Aktiv", Staffeln 2-8 = "Geplant"
- Spalte `completed_batches` im Succession-Plan zeigt noch 0 (dieser Run ist nicht abgeschlossen)

**Postconditions**:
- Staffel-Run "Salat-Staffel 1/8" hat status=active
- 12 PlantInstances wurden erstellt

**Tags**: [REQ-013, succession-plan, staffel-aktivieren, zustandswechsel]

---

### TC-013-061: SuccessionPlan — Pflichtfeld "Intervall" muss positiv sein

**Requirement**: REQ-013 §2 SuccessionPlan (interval_days: int), Frontend Zod-Validierung
**Priority**: Medium
**Category**: Formvalidierung

**Preconditions**:
- Staffelplan-Erstellen-Dialog ist geöffnet

**Test Steps**:
1. Nutzer füllt alle Felder aus
2. Nutzer gibt im Feld "Intervall (Tage)" den Wert "0" ein
3. Nutzer klickt auf "Erstellen"

**Expected Results**:
- Dialog bleibt geöffnet
- Unter dem Intervall-Feld erscheint eine Validierungsfehlermeldung (Wert muss größer als 0 sein)
- Kein SuccessionPlan wird erstellt

**Postconditions**:
- Kein SuccessionPlan wird erstellt

**Tags**: [REQ-013, succession-plan, formvalidierung, intervall-positiv]

---

### TC-013-062: SuccessionPlan — Enddatum vor Startdatum — Fehlermeldung

**Requirement**: REQ-013 §2 SuccessionPlan (end_date >= start_date), Frontend Zod-Validierung
**Priority**: Medium
**Category**: Formvalidierung

**Preconditions**:
- Staffelplan-Erstellen-Dialog ist geöffnet

**Test Steps**:
1. Nutzer gibt Startdatum "31.08.2026" ein
2. Nutzer gibt Enddatum "01.04.2026" ein (liegt vor dem Startdatum)
3. Nutzer klickt auf "Erstellen"

**Expected Results**:
- Dialog bleibt geöffnet
- Fehlermeldung erscheint: Enddatum muss nach Startdatum liegen
- Kein SuccessionPlan wird erstellt

**Postconditions**:
- Kein SuccessionPlan wird erstellt

**Tags**: [REQ-013, succession-plan, formvalidierung, datum-reihenfolge]

---

## Gruppe 16: Navigation und Tabs

### TC-013-063: Tab-Navigation — alle Tabs sind bedienbar

**Requirement**: REQ-013 Frontend TAB_SLUGS: details, plants, phases, nutrient-watering, activity-plan, diary
**Priority**: High
**Category**: Navigation

**Preconditions**:
- PlantingRun (status: active) mit Einträgen und mindestens einer Pflanze existiert

**Test Steps**:
1. Nutzer öffnet Detailseite
2. Nutzer klickt nacheinander auf alle verfügbaren Tabs

**Expected Results**:
- Tab "Details": Summary-Bar und Eintrags-Tabelle sichtbar
- Tab "Pflanzen": Pflanzenliste sichtbar
- Tab "Phasen": Run-Phase-Timeline und RunPhaseEditor sichtbar
- Tab "Nährstoff & Gießen": Plan-Zuweisung und Gießkalender sichtbar
- Tab "Aktivitätsplan": Aktivitäts-Inhalt sichtbar
- URL enthält den jeweiligen Tab-Slug (z.B. `?tab=plants`)

**Postconditions**:
- Keine Datenänderung

**Tags**: [REQ-013, navigation, tabs, url-zustand]

---

### TC-013-064: Löschen-Bestätigung — Abbrechen kehrt zur Detailseite zurück

**Requirement**: REQ-013 Frontend ConfirmDialog
**Priority**: Low
**Category**: Dialog

**Preconditions**:
- Löschen-Dialog für einen geplanten Run ist geöffnet

**Test Steps**:
1. Löschen-Dialog ist geöffnet
2. Nutzer klickt auf "Abbrechen"

**Expected Results**:
- Dialog schließt sich
- Nutzer verbleibt auf der Detailseite
- Run ist unverändert

**Postconditions**:
- Keine Datenänderung

**Tags**: [REQ-013, löschen, abbrechen, detailseite]

---

## Gruppe 17: Edge Cases und Fehlerbehandlung

### TC-013-065: Laden-Skeleton erscheint bei Seitenaufruf

**Requirement**: REQ-013 Frontend LoadingSkeleton
**Priority**: Low
**Category**: Happy Path

**Preconditions**:
- Nutzer ist eingeloggt, Netzwerkverbindung vorhanden (evtl. mit simulierter Latenz)

**Test Steps**:
1. Nutzer navigiert zur Detailseite eines PlantingRuns

**Expected Results**:
- Während des Ladens zeigt die Seite einen Lade-Skeleton (LoadingSkeleton variant="form")
- Nach dem Laden wird der vollständige Inhalt angezeigt

**Postconditions**:
- Keine Datenänderung

**Tags**: [REQ-013, ladezustand, skeleton, ux]

---

### TC-013-066: Standalone-Pflanze zeigt volle Management-Fähigkeiten

**Requirement**: REQ-013 §1.1 Dual-Modell ("Standalone-Modus: volle Management-Fähigkeiten")
**Priority**: High
**Category**: Detailansicht

**Preconditions**:
- PlantInstance ohne aktiven Run existiert (direkt erstellt oder nach Detach)

**Test Steps**:
1. Nutzer navigiert zur Pflanzdetailseite einer Standalone-Pflanze

**Expected Results**:
- Phasenwechsel-Button ist sichtbar und aktiv
- Task-Management-Tab ist zugänglich
- Pflege-Profil-Tab ist zugänglich
- Nährstoffplan-Tab ist zugänglich (eigener follows_plan)
- Tagebuch-Tab ist zugänglich
- Kein Hinweisbanner über Run-Zugehörigkeit sichtbar

**Postconditions**:
- Keine Datenänderung

**Tags**: [REQ-013, standalone, dual-modell, volle-verwaltung]

---

### TC-013-067: Keine Doppelzugehörigkeit — bestehende Run-Pflanze kann nicht nochmals zugewiesen werden

**Requirement**: REQ-013 §1 Grundprinzipien ("Keine Doppelzugehörigkeit"), §4 Fehlerbehandlung 409
**Priority**: High
**Category**: Fehlermeldung

**Preconditions**:
- PlantInstance HOCHBEETA_TOM_03 ist aktives Mitglied in Run A
- Run B (status: planned oder active) existiert

**Test Steps**:
1. Nutzer versucht, HOCHBEETA_TOM_03 in Run B aufzunehmen (via adopt-plants oder UI-Zuweisung)

**Expected Results**:
- Eine Fehlerbenachrichtigung erscheint (409 Conflict)
- Meldung: Die Pflanze gehört bereits einem aktiven Run an
- Pflanze wird NICHT in Run B aufgenommen

**Postconditions**:
- Keine Datenänderung

**Tags**: [REQ-013, keine-doppelzugehörigkeit, konflikt-409, fehlermeldung]

---

## Abdeckungs-Matrix

| Spezifikations-Abschnitt | Testfall-IDs |
|--------------------------|-------------|
| §1 Business Case — Dual-Modell (Run-Managed vs. Standalone) | TC-013-023, TC-013-032, TC-013-066 |
| §1.2 Szenario 1: Monokultur Lebenszyklus | TC-013-005, TC-013-025 |
| §1.2 Szenario 2: Run-Level Phasenwechsel | TC-013-026, TC-013-027, TC-013-042 |
| §1.2 Szenario 3: Detach → Standalone | TC-013-030, TC-013-031, TC-013-032, TC-013-033, TC-013-034 |
| §1.2 Szenario 4: Sukzessions-Aussaat | TC-013-058, TC-013-059, TC-013-060, TC-013-061, TC-013-062 |
| §1.2 Szenario 5: Klon-Durchlauf | TC-013-008, TC-013-009, TC-013-014 |
| §2 Datenmodell — Konfigurationsregeln (Typ-Constraints, Quantity-Konsistenz) | TC-013-015, TC-013-014, TC-013-013 |
| §3 Statusmaschine (planned→active→harvesting→completed/cancelled) | TC-013-025, TC-013-028, TC-013-029, TC-013-036 |
| §3 Batch-Operationen Engine (create-plants, transition, batch-remove) | TC-013-025, TC-013-026, TC-013-028 |
| §3 Individuelle Abtrennung (detach, detach_category Pflichtfeld) | TC-013-030, TC-013-031, TC-013-032, TC-013-033, TC-013-034 |
| §3 Keine Doppelzugehörigkeit | TC-013-067 |
| §4.1 CRUD PlantingRun (Liste, Detail, Bearbeiten, Löschen) | TC-013-001 bis TC-013-004, TC-013-035 bis TC-013-037, TC-013-038 bis TC-013-041 |
| §4.2 Entries (Artenzusammensetzung) | TC-013-019 |
| §4.3 Batch-Operationen (create-plants, transition, batch-remove) | TC-013-025, TC-013-026, TC-013-028 |
| §4.4 Pflanzen im Run (Liste, detach) | TC-013-021, TC-013-022, TC-013-024, TC-013-030 |
| §4.5 NutrientPlan-Zuweisung und Entfernung | TC-013-043 bis TC-013-048 |
| §4.6 Gießkalender | TC-013-047, TC-013-048 |
| §4.7 Pflanzen-Tagebuch (CRUD, Aggregation, Standalone) | TC-013-051 bis TC-013-057 |
| §5 Auth — Admin für DELETE | TC-013-035 |
| §7 DoD — Validierungsfehler 422/400/409 | TC-013-010 bis TC-013-015, TC-013-067 |
| §7 DoD — Erfahrungsstufen UI | TC-013-016, TC-013-017 |
| §7 DoD — Sukzessions-Plan CRUD und Run-Generierung | TC-013-058 bis TC-013-062 |
| Frontend-spezifisch — Tabs, Navigation, Breadcrumbs | TC-013-004, TC-013-063 |
| Frontend-spezifisch — Leer-/Lade-/Fehlerzustand | TC-013-002, TC-013-065 |
| Frontend-spezifisch — Dosierungsanzeige | TC-013-049, TC-013-050 |
| Auto-generierung ID-Präfix | TC-013-006, TC-013-007 |
| Dual-Modell: Standalone volle Management-Fähigkeiten | TC-013-032, TC-013-057, TC-013-066 |

### Änderungsprotokoll gegenüber Version 1.2

| Änderung | Details |
|----------|---------|
| **Entfernt** | TC-013-010 (Mischkultur erstellen), TC-013-011 (Mischkultur Eintrags-Löschen), TC-013-028 (Mischkultur-Hinweis im Batch-Dialog) — Mischkultur in v2.0 komplett entfernt |
| **Neu (Dual-Modell)** | TC-013-023 (Run-Managed: keine Einzelsteuerung), TC-013-032 (Standalone nach Detach), TC-013-066 (Standalone volle Verwaltung), TC-013-067 (Keine Doppelzugehörigkeit) |
| **Erweitert** | TC-013-030/031 (Detach-Dialog mit Pflicht-Kategorie und Begründung), TC-013-033 (Run-Zähler nach Detach), TC-013-022 (Pflanzen-Tab ohne per-Plant Phase) |
| **Neu (PlantDiaryEntry)** | TC-013-051 bis TC-013-057 (Tagebuch erstellen, anzeigen, bearbeiten, löschen, Validation, aggregiertes Run-Tagebuch, Standalone-Tagebuch) |
| **Neu (SuccessionPlan)** | TC-013-058 bis TC-013-062 (Erstellen, generierte Runs, aktivieren, Validation Intervall, Datum-Reihenfolge) |
| **Neu (Run-Level Phasenwechsel)** | TC-013-026/027 ersetzen alten Batch-Phasenübergang: explizit Run-Level ohne exclude/per-Plant-Filter |
| **Nummerierung** | Gruppen 4-16 neu nummeriert; bestehende valide TCs behielten soweit möglich ihre Kernlogik |

### Noch nicht abgedeckte Bereiche (externe Abhängigkeiten oder ausstehend)

| Bereich | Verweis |
|---------|--------|
| Companion-Beziehungen über Standort-Graph (statt Mischkultur-Run) | REQ-028 §9, §10 — TC-REQ-028.md |
| Batch-Ernte (batch-harvest → HarvestBatch erstellen) | REQ-007 Erntemanagement — TC-REQ-007.md |
| Jährliche Wiederholung (annual_repeat, repeat_month, clone_from_run_key) | REQ-015 Aussaatkalender |
| Per-Plant-Gewichte bei Batch-Ernte | REQ-007 |
| Adopt-Plants (bestehende Standalone in Run aufnehmen) | REQ-013 §4.3, noch kein UI-Hinweis in Spec |
| Erinnerung vor nächster Staffel-Aussaat (reminder_days_before) | REQ-022 Pflegeerinnerungen |
