---
req_id: REQ-013
title: Pflanzdurchlauf-Verwaltung & Batch-Operationen
category: Gruppenmanagement
test_count: 52
coverage_areas:
  - Listenansicht PlantingRun
  - Erstellen-Dialog (Monokultur, Klon, Mischkultur)
  - Formularvalidierung Erstellungsdialog
  - Detailseite Tabs (Details, Pflanzen, Phasen, Nährstoff/Gießen, Aktivitätsplan)
  - Bearbeiten-Dialog
  - Batch-Erstellung (create-plants)
  - Batch-Phasenübergang (batch-transition)
  - Batch-Entfernung / Run-Abschluss
  - Individuelle Pflanzenabtrennung (detach)
  - Nährstoffplan-Zuweisung und Entfernung
  - Gießkalender-Anzeige
  - Löschen-Dialog (nur Status planned)
  - Status-Statusmaschine (Zustandsübergänge sichtbar im UI)
  - Navigationspfade und Breadcrumbs
  - Erfahrungsstufen-Sichtbarkeit (ExpertiseFieldWrapper)
generated: 2026-03-21
version: "1.2"
---

# Testfälle REQ-013: Pflanzdurchlauf-Verwaltung & Batch-Operationen

## Kontext und Testabdeckungsstrategie

REQ-013 führt den **Pflanzdurchlauf (PlantingRun)** als Gruppencontainer für Pflanzen ein. Die
Testfälle decken den vollständigen Lifecycle aus Browser-Sicht ab: Erstellung aller drei Typen
(Monokultur, Klon, Mischkultur), Batch-Aktionen (Pflanzen anlegen, Phasen wechseln, Run beenden),
individuelle Pflanzenabtrennung sowie die Nährstoffplan-Integration mit Gießkalender. Alle
Testschritte beschreiben ausschließlich Browser-Interaktionen — keine API- oder Datenbankzugriffe.

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

**Requirement**: REQ-013 §7 DoD Szenario 2, Clone-Validierung
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

## Gruppe 4: Erstellen-Dialog — Mischkultur

### TC-013-010: Mischkultur-Run mit mehreren Einträgen erstellen

**Requirement**: REQ-013 §7 DoD Szenario 1.1 (Mischkultur), Typ-Validierung (mixed_culture ≥ 2 Entries)
**Priority**: High
**Category**: Happy Path

**Preconditions**:
- Nutzer ist eingeloggt
- Species: "Solanum lycopersicum" (primary), "Ocimum basilicum" (companion), "Tagetes patula" (trap_crop) existieren

**Test Steps**:
1. Nutzer öffnet den Erstellen-Dialog
2. Nutzer gibt Name "Mischkultur Beet B Sommer 2025" ein
3. Nutzer wählt Typ "Mischkultur"
4. Im ersten Eintrag: wählt Art "Solanum lycopersicum", Rolle "Primär", Anzahl "8", ID-Präfix "TOM"
5. Nutzer klickt auf Schaltfläche "Eintrag hinzufügen"
6. Im zweiten Eintrag: wählt Art "Ocimum basilicum", Rolle "Begleitpflanze", Anzahl "12", ID-Präfix "BAS"
7. Nutzer klickt erneut auf "Eintrag hinzufügen"
8. Im dritten Eintrag: wählt Art "Tagetes patula", Rolle "Fangpflanze", Anzahl "6", ID-Präfix "TAG"
9. Nutzer klickt auf "Erstellen"

**Expected Results**:
- Dialog schließt sich
- Erfolgsmeldung erscheint
- In der Liste erscheint "Mischkultur Beet B Sommer 2025" mit Typ "Mischkultur", Status "Geplant", geplanter Anzahl 26

**Postconditions**:
- PlantingRun mit 3 Einträgen (3 Species, 3 Rollen) und planned_quantity=26 existiert

**Tags**: [REQ-013, erstellen, mischkultur, happy-path]

---

### TC-013-011: Mischkultur — Eintrags-Löschen-Schaltfläche deaktiviert bei erstem Eintrag

**Requirement**: REQ-013 Frontend-Validierung (entries.min(1)), `canRemove={fields.length > 1}`
**Priority**: Medium
**Category**: Formvalidierung

**Preconditions**:
- Erstellen-Dialog ist geöffnet

**Test Steps**:
1. Dialog zeigt initial genau einen Eintrag
2. Nutzer prüft den Löschen-Button des ersten Eintrags

**Expected Results**:
- Der Löschen-IconButton (Papierkorb) des ersten Eintrags ist deaktiviert (disabled)
- Nach dem Hinzufügen eines zweiten Eintrags (Klick auf "Eintrag hinzufügen") ist der Löschen-Button des ersten Eintrags aktiv

**Postconditions**:
- Keine Datenänderung

**Tags**: [REQ-013, erstellen, eintrags-verwaltung, button-zustand]

---

## Gruppe 5: Erstellen-Dialog — Formularvalidierung (negative Tests)

### TC-013-012: Pflichtfeld "Name" leer lassen — Fehlermeldung

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

### TC-013-013: Eintrags-Anzahl 0 — Fehlermeldung (min=1)

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

### TC-013-014: ID-Präfix mit ungültigem Format — Fehlermeldung (nur A-Z, 2-5 Zeichen)

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

### TC-013-015: Pflichtfeld "Art" (species) leer lassen — Fehlermeldung

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

### TC-013-016: Backend-Fehler — Clone-Run ohne Mutterpflanzen-Key

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

### TC-013-017: Backend-Fehler — Monokultur mit zwei Einträgen

**Requirement**: REQ-013 §3 Typ-Constraint (monoculture: genau 1 Entry), §4 Fehlerbehandlung 422
**Priority**: High
**Category**: Fehlermeldung

**Preconditions**:
- Nutzer ist eingeloggt
- Erstellen-Dialog ist geöffnet, Typ "Monokultur" gewählt

**Test Steps**:
1. Nutzer füllt den ersten Eintrag aus (Art, Anzahl, ID-Präfix)
2. Nutzer klickt auf "Eintrag hinzufügen"
3. Nutzer füllt den zweiten Eintrag aus
4. Nutzer klickt auf "Erstellen"

**Expected Results**:
- Eine Fehlerbenachrichtigung erscheint
- Die Fehlermeldung weist darauf hin, dass Monokultur-Durchläufe genau einen Eintrag erlauben
- Dialog bleibt geöffnet, Kein Run wird erstellt

**Postconditions**:
- Kein PlantingRun wird erstellt

**Tags**: [REQ-013, fehlermeldung, monokultur, typ-constraint]

---

### TC-013-018: Erfahrungsstufe Beginner — Felder Typ, Standort, Notizen ausgeblendet

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

### TC-013-019: "Alle Felder anzeigen" Toggle schaltet Expertenfelder ein

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

## Gruppe 6: Detailseite — Tab "Details"

### TC-013-020: Detailseite — Summary-Bar zeigt Kern-Metadaten

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

### TC-013-021: Detailseite — Eintrags-Tabelle zeigt Artenzusammensetzung

**Requirement**: REQ-013 §4.2 (GET entries), Frontend PlantingRunDetailsTab Eintrags-Tabelle
**Priority**: High
**Category**: Detailansicht

**Preconditions**:
- PlantingRun "Mischkultur Beet B" (status: active) mit 3 Einträgen (Tomate primary, Basilikum companion, Tagetes trap_crop) existiert

**Test Steps**:
1. Nutzer öffnet die Detailseite des Mischkultur-Runs
2. Tab "Details" ist aktiv, Nutzer scrollt zur Eintrags-Tabelle

**Expected Results**:
- Tabelle "Einträge" zeigt 3 Zeilen
- Tomate-Zeile: Art = "Solanum lycopersicum" (oder Common Name), Rolle = "Primär", Anzahl = 8, ID-Präfix = "TOM", Abstand = "50 cm"
- Basilikum-Zeile: Rolle = "Begleitpflanze", Anzahl = 12
- Tagetes-Zeile: Rolle = "Fangpflanze", Anzahl = 6

**Postconditions**:
- Keine Datenänderung

**Tags**: [REQ-013, detailansicht, einträge-tabelle, mischkultur]

---

### TC-013-022: Detailseite — Notizen-Karte wird angezeigt wenn vorhanden

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

## Gruppe 7: Detailseite — Tab "Pflanzen"

### TC-013-023: Pflanzen-Tab — Leerszustand bei Status "geplant" zeigt Aktionsschaltfläche

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

### TC-013-024: Pflanzen-Tab — Pflanzenliste nach Batch-Erstellung

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
- Jede Zeile enthält: Instance-ID (z.B. HOCHBEETA_TOM_01), Aktuelle Phase (Chip), Gepflanzt am, Entfernt am (—), Abgetrennt (—)
- Jede Zeile hat eine "Abtrennen"-Schaltfläche (da Run status=active)
- Jede Zeile hat einen "Öffnen"-IconButton (externes Link-Symbol) zum Navigieren zur Pflanzdetailseite

**Postconditions**:
- Keine Datenänderung

**Tags**: [REQ-013, pflanzen-tab, pflanzenliste, batch-erstellt]

---

### TC-013-025: Pflanzen-Tab — Navigation zur Pflanzdetailseite über externe Link-Schaltfläche

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

## Gruppe 8: Batch-Operationen von der Detailseite

### TC-013-026: Batch-Erstellung starten (Pflanzen anlegen — geplanter Run)

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

**Tags**: [REQ-013, batch-erstellung, zustandswechsel, planned-zu-active]

---

### TC-013-027: Batch-Phasenübergang öffnen und Zielphase wählen

**Requirement**: REQ-013 §4.3 (batch-transition), §7 DoD Szenario 4
**Priority**: Critical
**Category**: Dialog

**Preconditions**:
- PlantingRun (status: active) mit 20 Pflanzen, alle in Phase "vegetative", existiert
- Die Spezies hat eine definierte nächste Phase "flowering" nach "vegetative"

**Test Steps**:
1. Nutzer öffnet die Detailseite des aktiven Runs
2. Nutzer klickt auf Schaltfläche "Batch-Phasenübergang" (SwapHoriz-Icon)
3. Dialog "Batch-Phasenübergang" öffnet sich (`data-testid="batch-phase-transition-dialog"`)
4. Dialog zeigt ein Dropdown mit verfügbaren Zielphasen (Phasen nach der dominanten Phase)
5. Nutzer wählt im Dropdown "flowering" (inkl. typischer Dauer in Tagen)
6. Ein gelber Warn-Alert erscheint: Bestätigung der Anzahl berechtigter Pflanzen
7. Nutzer klickt auf "Bestätigen"

**Expected Results**:
- Dialog schließt sich
- Erfolgsmeldung erscheint mit Anzahl transitierter Pflanzen: "18 Pflanzen überführt, X übersprungen" (oder i18n-Formulierung)
- Im Pflanzen-Tab zeigen Pflanzen-Chips die neue Phase "flowering"

**Postconditions**:
- Pflanzen haben Phase "flowering"

**Tags**: [REQ-013, batch-phasenübergang, dialog, zustandswechsel]

---

### TC-013-028: Batch-Phasenübergang Dialog — Mischkultur-Hinweis erscheint

**Requirement**: REQ-013 §3 (BatchTransitionRequest entry_key Filter für Mischkulturen), Frontend Warn-Alert
**Priority**: Medium
**Category**: Dialog

**Preconditions**:
- Mischkultur-Run (status: active) mit mindestens 2 verschiedenen Species in den Einträgen existiert

**Test Steps**:
1. Nutzer öffnet den Batch-Phasenübergang-Dialog für den Mischkultur-Run

**Expected Results**:
- Dialog zeigt einen Info-Alert: "Mischkultur-Hinweis" (mixedCultureWarning) — Hinweis dass Phasenübergang nur für erste Art gilt
- Dropdown für Zielphase ist vorhanden

**Postconditions**:
- Keine Datenänderung

**Tags**: [REQ-013, batch-phasenübergang, mischkultur, info-alert]

---

### TC-013-029: Batch-Phasenübergang ohne ausgewählte Zielphase deaktiviert Bestätigen-Schaltfläche

**Requirement**: REQ-013 Frontend (disabled={!targetPhaseKey || saving})
**Priority**: Medium
**Category**: Formvalidierung

**Preconditions**:
- Batch-Phasenübergang-Dialog ist geöffnet

**Test Steps**:
1. Dialog ist geöffnet, kein Wert im Zielphase-Dropdown ausgewählt

**Expected Results**:
- Schaltfläche "Bestätigen" ist deaktiviert (disabled)
- Nach Auswahl einer Zielphase aus dem Dropdown wird die Schaltfläche aktiviert

**Postconditions**:
- Keine Datenänderung

**Tags**: [REQ-013, batch-phasenübergang, button-zustand, validierung]

---

### TC-013-030: Run beenden — Dialog mit Status-Auswahl (Abgebrochen / Abgeschlossen)

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
- Schaltflächen "Batch-Phasenübergang" und "Run beenden" sind nicht mehr sichtbar (Terminal-Status)

**Postconditions**:
- Run hat status=completed
- Alle Pflanzen haben removed_on gesetzt

**Tags**: [REQ-013, run-beenden, zustandswechsel, terminal-status]

---

### TC-013-031: Run im Status "harvesting" — Endstatus ist standardmäßig "Abgeschlossen"

**Requirement**: REQ-013 §3 (ALLOWED_STATUS_TRANSITIONS: harvesting→completed | cancelled), Frontend-Logik `endRunStatus = run?.status === 'harvesting' ? 'completed' : 'cancelled'`
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

## Gruppe 9: Individuelle Pflanzenabtrennung (detach)

### TC-013-032: Einzelne Pflanze vom Run abtrennen

**Requirement**: REQ-013 §4.4 (detach), §7 DoD Szenario 6, Individuelle Abtrennung
**Priority**: High
**Category**: Zustandswechsel

**Preconditions**:
- PlantingRun (status: active) mit mindestens 2 Pflanzen existiert

**Test Steps**:
1. Nutzer öffnet die Detailseite des aktiven Runs
2. Nutzer navigiert zum Tab "Pflanzen"
3. Nutzer klickt auf die Schaltfläche "Abtrennen" neben einer Pflanze (z.B. HOCHBEETA_TOM_05)
4. (Aktion wird direkt ausgeführt, kein extra Dialog laut Frontend-Implementierung)

**Expected Results**:
- Erfolgsmeldung erscheint: "Pflanze abgetrennt" (plantDetached)
- In der Pflanzenliste zeigt die betroffene Pflanze in der Spalte "Abgetrennt" nun "Ja"
- Die "Abtrennen"-Schaltfläche verschwindet für diese Pflanze
- Die Pflanze ist weiterhin in der Liste sichtbar (nicht gelöscht)

**Postconditions**:
- `detached_at` ist auf der `run_contains`-Edge gesetzt
- PlantInstance selbst bleibt bestehen und ist individuell verwaltbar

**Tags**: [REQ-013, abtrennen, detach, soft-binding]

---

### TC-013-033: Abtrennen-Schaltfläche nur bei aktivem Run sichtbar

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

## Gruppe 10: Löschen (nur Status "geplant")

### TC-013-034: Löschen-Dialog erscheint und Löschen wird bestätigt (geplanter Run)

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

### TC-013-035: Löschen-Schaltfläche nicht sichtbar bei aktivem Run

**Requirement**: REQ-013 §4.1 (DELETE nur status=planned → 409 bei aktiven Runs), Frontend-Bedingung `run?.status === 'planned'`
**Priority**: High
**Category**: Detailansicht

**Preconditions**:
- PlantingRun (status: active) existiert

**Test Steps**:
1. Nutzer öffnet die Detailseite des aktiven Runs

**Expected Results**:
- Die rote "Löschen"-Schaltfläche ist NICHT sichtbar
- Stattdessen sind "Batch-Phasenübergang" und "Run beenden" sichtbar

**Postconditions**:
- Keine Datenänderung

**Tags**: [REQ-013, löschen, button-zustand, active-status]

---

### TC-013-036: Löschen abbrechen — Run bleibt erhalten

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

## Gruppe 11: Bearbeiten-Dialog

### TC-013-037: Bearbeiten-Dialog öffnet sich mit vorhandenen Werten

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

### TC-013-038: Bearbeiten — Name ändern und speichern

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

### TC-013-039: Bearbeiten — Standort-Feld löscht Location wenn Site gewechselt wird

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

### TC-013-040: Bearbeiten — Pflichtfeld "Name" leer lassen verhindert Speichern

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

## Gruppe 12: Tab "Phasen"

### TC-013-041: Phasen-Tab zeigt Phasen-Timeline und RunPhaseEditor

**Requirement**: REQ-013 §4.3 (batch-transition), Frontend PhaseKamiTimeline und RunPhaseEditor
**Priority**: High
**Category**: Detailansicht

**Preconditions**:
- PlantingRun (status: active) mit Species die über eine Lifecycle-Konfiguration mit Phasen verfügt

**Test Steps**:
1. Nutzer öffnet die Detailseite des aktiven Runs
2. Nutzer klickt auf Tab "Phasen" (`data-testid="phases-tab"`)

**Expected Results**:
- Tab-Inhalt lädt
- Eine visuelle Phasen-Timeline (Kamilya-Timeline) wird gezeigt mit den Phasen der ersten Spezies
- Der RunPhaseEditor ist sichtbar und erlaubt das Bearbeiten von Phasendaten

**Postconditions**:
- Keine Datenänderung

**Tags**: [REQ-013, phasen-tab, phase-timeline, run-phase-editor]

---

## Gruppe 13: Tab "Nährstoff & Gießen"

### TC-013-042: Nährstoff/Gießen-Tab ohne zugewiesenen Plan zeigt Info-Alert und Zuweisung-Schaltfläche

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

### TC-013-043: Nährstoffplan zuweisen über Zuweisung-Dialog

**Requirement**: REQ-013 §4.5 (POST nutrient-plan), §7 DoD NutrientPlan-Zuweisung und Cascade
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
- FOLLOWS_PLAN-Edges wurden kaskadiert auf bestehende Pflanzen

**Tags**: [REQ-013, nährstoff-tab, plan-zuweisung, cascade]

---

### TC-013-044: Nährstoffplan entfernen — Bestätigungs-Dialog erscheint

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
- Wenn bestätigt: Plan-Zuweisung wird entfernt, FOLLOWS_PLAN-Edges werden kaskadiert entfernt

**Tags**: [REQ-013, nährstoff-tab, plan-entfernen, bestätigung]

---

### TC-013-045: Plan-Zuweisung deaktiviert für abgeschlossene/abgebrochene Runs

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

### TC-013-046: Gießkalender wird bei zugewiesenem Plan mit WateringSchedule angezeigt

**Requirement**: REQ-013 §4.5 (GET watering-schedule), §7 DoD Gießkalender-Endpoint
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

### TC-013-047: Gießkalender-Info wenn kein Plan oder kein Schedule vorhanden

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

## Gruppe 14: Details-Tab — Dosierungsanzeige

### TC-013-048: Details-Tab zeigt aktuelle Dünger-Dosierungen nach zugewiesenem Plan

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

### TC-013-049: Dosierungsmodus wechseln zwischen ml/L und Gesamtvolumen

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

## Gruppe 15: Navigation und Tabs

### TC-013-050: Tab-Navigation — alle 5 Tabs sind bedienbar

**Requirement**: REQ-013 Frontend TAB_SLUGS: details, plants, phases, nutrient-watering, activity-plan
**Priority**: High
**Category**: Navigation

**Preconditions**:
- PlantingRun (status: active) mit Einträgen existiert

**Test Steps**:
1. Nutzer öffnet Detailseite
2. Nutzer klickt nacheinander auf alle 5 Tabs

**Expected Results**:
- Tab 0 "Details": Summary-Bar und Eintrags-Tabelle sichtbar
- Tab 1 "Pflanzen": Pflanzenliste oder Leerszustand sichtbar
- Tab 2 "Phasen": Phase-Timeline und RunPhaseEditor sichtbar
- Tab 3 "Nährstoff & Gießen": Plan-Zuweisung und Gießkalender sichtbar
- Tab 4 "Aktivitätsplan": Aktivitäts-Inhalt sichtbar
- URL enthält den jeweiligen Tab-Slug (z.B. `?tab=plants`)

**Postconditions**:
- Keine Datenänderung

**Tags**: [REQ-013, navigation, tabs, url-zustand]

---

### TC-013-051: Löschen-Bestätigung — Abbrechen kehrt zur Detailseite zurück

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

## Gruppe 16: Edge Cases und Fehlerbehandlung

### TC-013-052: Laden-Ladebalken erscheint bei Seitenaufruf

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

## Abdeckungs-Matrix

| Spezifikations-Abschnitt | Testfall-IDs |
|--------------------------|-------------|
| §1 Business Case — 5 Szenarien (Monokultur, Klon, Mischkultur, Sukzession, Berater) | TC-013-005, TC-013-008, TC-013-010 |
| §2 Datenmodell — Konfigurationsregeln (Typ-Constraints) | TC-013-017, TC-013-016, TC-013-015 |
| §3 Statusmaschine (planned→active→harvesting→completed/cancelled) | TC-013-026, TC-013-030, TC-013-031, TC-013-035 |
| §3 Batch-Operationen Engine (create-plants, batch-transition) | TC-013-026, TC-013-027, TC-013-028, TC-013-029 |
| §3 Individuelle Abtrennung (detach) | TC-013-032, TC-013-033 |
| §4.1 CRUD PlantingRun (Liste, Detail, Bearbeiten, Löschen) | TC-013-001 bis TC-013-004, TC-013-034 bis TC-013-036, TC-013-037 bis TC-013-040 |
| §4.2 Entries (Artenzusammensetzung) | TC-013-021, TC-013-010, TC-013-011 |
| §4.3 Batch-Operationen (create-plants, batch-transition, batch-remove) | TC-013-026, TC-013-027, TC-013-030 |
| §4.4 Pflanzen im Run (Liste, detach) | TC-013-023, TC-013-024, TC-013-025, TC-013-032 |
| §4.5 NutrientPlan-Zuweisung, Cascade, Entfernung, Gießkalender | TC-013-042 bis TC-013-047 |
| §5 Auth — Admin für DELETE | TC-013-034 |
| §7 DoD — Validierungsfehler 422 | TC-013-012 bis TC-013-017 |
| §7 DoD — Erfahrungsstufen UI | TC-013-018, TC-013-019 |
| Frontend-spezifisch — Tabs, Navigation, Breadcrumbs | TC-013-004, TC-013-050 |
| Frontend-spezifisch — Leer-/Lade-/Fehlerzustand | TC-013-002, TC-013-052 |
| Frontend-spezifisch — Dosierungsanzeige | TC-013-048, TC-013-049 |
| Auto-generierung ID-Präfix | TC-013-006, TC-013-007 |

### Noch nicht abgedeckte Bereiche (externe Abhängigkeiten)

| Bereich | Verweis |
|---------|--------|
| Mischkultur-Berater (Empfehlungen, Kompatibilitäts-Check) | REQ-028 §9, §10 — separate Testfälle in TC-REQ-028.md |
| Sukzessions-Plan CRUD (SuccessionPlan Create/Edit/Delete) | REQ-013 §7 DoD Sukzession — noch nicht im Frontend implementiert |
| Batch-Ernte (batch-harvest → HarvestBatch erstellen) | REQ-007 Erntemanagement — Testfälle in TC-REQ-007.md |
| Jährliche Wiederholung (annual_repeat, repeat_month) | REQ-015 Aussaatkalender |
| Per-Plant-Gewichte bei Batch-Ernte | REQ-007 |
