---
req_id: REQ-007
title: "Gattungsspezifisches Erntemanagement & Reifegradprüfung"
category: Erntezyklus
test_count: 42
coverage_areas:
  - Ernte-Batch-Listenansicht (HarvestBatchListPage)
  - Ernte-Batch-Erstellen (HarvestCreateDialog)
  - Ernte-Batch-Detailansicht (HarvestBatchDetailPage, Tab Details)
  - Ernte-Batch-Bearbeiten (HarvestBatchDetailPage, Tab Bearbeiten)
  - Qualitätsbewertung erstellen (Tab Qualität)
  - Qualitätsbewertung anzeigen (Tab Qualität)
  - Ertragsmetriken erstellen (Tab Ertrag)
  - Ertragsmetriken anzeigen (Tab Ertrag)
  - Erntereife-Karte (HarvestReadinessCard)
  - Formularvalidierung (Pflichtfelder, Bereichsgrenzen)
  - Navigationsmuster (Liste -> Detail -> Tabs)
  - Ungespeicherte Änderungen Guard
  - Karenzzeit-Gate (REQ-010 Integration, UI-seitig)
  - Qualitäts-Grading (A+/A/B/C/D, Farbkodierung)
generated: "2026-03-21"
version: "2.3"
---

# Testfälle: REQ-007 – Gattungsspezifisches Erntemanagement & Reifegradprüfung

**Anforderungsbezug:** REQ-007 v2.3 – Ernte-Chargen, Reife-Indikatoren, Qualitätsbewertung, Ertragsmetriken
**Frontend-Seiten:** `src/frontend/src/pages/ernte/`
**Routen:** `/ernte/batches` (Liste), `/ernte/batches/:key` (Detail)

---

## Überblick

Dieser Testfall-Katalog deckt die gesamte Ernte-Funktionalität aus Nutzerperspektive ab: vom Anlegen einer Erntecharge über die Qualitätsbewertung und Ertragserfassung bis hin zur Erntereife-Visualisierung. Alle Testschritte beschreiben ausschließlich Browser-Aktionen (Klicken, Ausfüllen, Navigieren) und Browser-sichtbare Ergebnisse.

**Wichtige UI-Konzepte:**
- Ernte-Chargen-Liste unter `/ernte/batches` mit DataTable (Suche, Sortierung, Paginierung)
- Detail-Seite mit 4 Tabs: "Details" (Tab 0), "Qualität" (Tab 1), "Ertrag" (Tab 2), "Bearbeiten" (Tab 3)
- Qualitäts-Stufen werden als farbige Chips dargestellt: A+ / A = grün, B = blau, C = orange, D = rot
- `UnsavedChangesGuard` auf Tab "Bearbeiten": Browser-Dialog bei Navigieren mit ungespeicherten Änderungen

---

## Gruppe 1: Ernte-Batch-Listenansicht

### TC-007-001: Ernte-Batch-Liste anzeigen (Happy Path)

**Anforderung:** REQ-007 §6 DoD – Listenansicht mit Batch-ID, Datum, Gewicht, Qualitätsstufe
**Priorität:** Critical
**Kategorie:** Happy Path / Listenansicht

**Vorbedingungen:**
- Nutzer ist eingeloggt und hat Mitgliedschaft im aktiven Tenant
- Mindestens 1 Erntecharge existiert im System (z. B. Batch-ID "PLANT_001_20260215_001", Pflanze "Pflanze-1", Erntedatum 15.02.2026, Nassgewicht 450 g, Qualitätsstufe B)

**Testschritte:**
1. Nutzer navigiert zu `/ernte/batches`
2. Nutzer wartet, bis die Seite vollständig geladen ist

**Erwartetes Ergebnis:**
- Seiten-Überschrift "Erntechargen" ist sichtbar
- Einleitungstext "Erntechargen dokumentieren den Ernteprozess vom Nassgewicht bis zur Qualitätsbewertung und Ertragsanalyse. Klicken Sie auf eine Charge für Details." ist sichtbar
- DataTable enthält die vorhandene Charge mit den Spalten: "Chargen-ID", "Erntedatum", "Erntetyp", "Nassgewicht (g)", "Qualitätsstufe"
- Zeile zeigt: "PLANT_001_20260215_001", "15.2.2026", Chip "Endernte", "450 g", Chip "B" (blau)
- Schaltfläche "Erntecharge erstellen" ist sichtbar und aktiviert

**Postconditions:**
- Keine Datenänderung

**Tags:** [REQ-007, harvest, list, happy-path, DataTable]

---

### TC-007-002: Leere Ernte-Batch-Liste (Empty State)

**Anforderung:** REQ-007 §6 DoD – Listenansicht
**Priorität:** Medium
**Kategorie:** Listenansicht / Empty State

**Vorbedingungen:**
- Nutzer ist eingeloggt
- Keine Erntechargen im System vorhanden

**Testschritte:**
1. Nutzer navigiert zu `/ernte/batches`

**Erwartetes Ergebnis:**
- DataTable zeigt Empty-State-Illustration (kamiHarvest-Illustration)
- Schaltfläche "Erntecharge erstellen" im Empty State ist sichtbar und klickbar
- Klick auf diese Schaltfläche öffnet den Erstellungs-Dialog

**Postconditions:**
- Keine Datenänderung

**Tags:** [REQ-007, harvest, list, empty-state]

---

### TC-007-003: Ernte-Batch-Liste – Suche in Tabelle

**Anforderung:** REQ-007 §6 DoD – Listenansicht-Filter (UI-NFR-010)
**Priorität:** High
**Kategorie:** Listenansicht / Suche

**Vorbedingungen:**
- Nutzer ist eingeloggt
- Mindestens 3 Erntechargen vorhanden: eine mit Typ "Teilernte", eine mit "Endernte", eine mit "Fortlaufend"

**Testschritte:**
1. Nutzer navigiert zu `/ernte/batches`
2. Nutzer gibt "Teilernte" in das Suchfeld "Tabelle durchsuchen..." ein

**Erwartetes Ergebnis:**
- Tabelle filtert sofort (nach ca. 300 ms Debounce) und zeigt nur Chargen mit Erntetyp "Teilernte"
- Chargen mit "Endernte" und "Fortlaufend" sind nicht mehr sichtbar
- Zeigt Paginierungsinfo z. B. "Zeigt 1–1 von 1 Einträgen"

**Postconditions:**
- Keine Datenänderung
- Such-Parameter ist in der URL persistent

**Tags:** [REQ-007, harvest, list, suche, filter]

---

### TC-007-004: Ernte-Batch-Liste – Sortierung nach Erntedatum

**Anforderung:** REQ-007 §6 DoD – Listenansicht
**Priorität:** Medium
**Kategorie:** Listenansicht / Sortierung

**Vorbedingungen:**
- Nutzer ist eingeloggt
- Mindestens 2 Chargen mit unterschiedlichen Erntedaten vorhanden (z. B. 01.01.2026 und 15.02.2026)

**Testschritte:**
1. Nutzer navigiert zu `/ernte/batches`
2. Nutzer klickt auf die Spaltenüberschrift "Erntedatum"
3. Nutzer klickt erneut auf "Erntedatum"

**Erwartetes Ergebnis:**
- Beim ersten Klick: Spaltenüberschrift zeigt Aufwärts-Pfeil; Chargen sind aufsteigend nach Datum sortiert (älteste zuerst)
- Beim zweiten Klick: Spaltenüberschrift zeigt Abwärts-Pfeil; neueste Charge erscheint zuerst

**Postconditions:**
- Keine Datenänderung

**Tags:** [REQ-007, harvest, list, sortierung]

---

### TC-007-005: Ernte-Batch-Liste – Qualitätsstufen-Farbkodierung

**Anforderung:** REQ-007 §6 DoD – Grade-Distribution / Qualitätsstufe sichtbar in Liste
**Priorität:** High
**Kategorie:** Listenansicht / Visuelle Darstellung

**Vorbedingungen:**
- Nutzer ist eingeloggt
- Erntechargen mit verschiedenen Qualitätsstufen vorhanden: A+ (a_plus), A (a), B (b), C (c), D (d)

**Testschritte:**
1. Nutzer navigiert zu `/ernte/batches`

**Erwartetes Ergebnis:**
- Charge mit Qualitätsstufe A+ zeigt grünen Chip mit Beschriftung "A+"
- Charge mit Qualitätsstufe A zeigt grünen Chip mit Beschriftung "A"
- Charge mit Qualitätsstufe B zeigt blauen Chip mit Beschriftung "B"
- Charge mit Qualitätsstufe C zeigt orangen Chip mit Beschriftung "C"
- Charge mit Qualitätsstufe D zeigt roten Chip mit Beschriftung "D"
- Charge ohne Qualitätsstufe zeigt "—"

**Postconditions:**
- Keine Datenänderung

**Tags:** [REQ-007, harvest, list, qualitaet, farbkodierung, chip]

---

### TC-007-006: Ernte-Batch-Liste – Navigation zur Detailseite

**Anforderung:** REQ-007 – Navigation List → Detail
**Priorität:** Critical
**Kategorie:** Navigation

**Vorbedingungen:**
- Nutzer ist eingeloggt
- Mindestens 1 Erntecharge vorhanden

**Testschritte:**
1. Nutzer navigiert zu `/ernte/batches`
2. Nutzer klickt auf eine Tabellenzeile (Erntecharge)

**Erwartetes Ergebnis:**
- Browser navigiert zu `/ernte/batches/{key}` der angeklickten Charge
- Detailseite der Charge wird geladen

**Postconditions:**
- Keine Datenänderung

**Tags:** [REQ-007, harvest, navigation, list-to-detail]

---

## Gruppe 2: Ernte-Batch erstellen

### TC-007-007: Ernte-Batch erstellen (Happy Path – Minimal)

**Anforderung:** REQ-007 §6 DoD – Batch-Erstellung, Batch-ID-Generierung
**Priorität:** Critical
**Kategorie:** Happy Path / Dialog

**Vorbedingungen:**
- Nutzer ist eingeloggt
- Mindestens 1 Pflanzen-Instanz im System vorhanden (z. B. "Pflanze Alpha")

**Testschritte:**
1. Nutzer navigiert zu `/ernte/batches`
2. Nutzer klickt auf "Erntecharge erstellen"
3. Dialog "Erntecharge erstellen" öffnet sich
4. Nutzer wählt im Dropdown "Pflanze" die vorhandene Pflanze aus
5. Nutzer wählt im Dropdown "Erntetyp" den Wert "Endernte"
6. Nutzer klickt auf "Erstellen"

**Erwartetes Ergebnis:**
- Dialog schließt sich
- Erfolgsbenachrichtigung "Erntecharge erfolgreich erstellt." erscheint als Snackbar
- Tabellenliste aktualisiert sich und zeigt die neue Charge
- Neue Charge erscheint in der Tabelle mit Erntedatum (heute), Erntetyp "Endernte" und Qualitätsstufe "B" (Standard)

**Postconditions:**
- Neue Erntecharge im System angelegt

**Tags:** [REQ-007, harvest, create, happy-path, dialog]

---

### TC-007-008: Ernte-Batch erstellen – Pflichtfeld Pflanze fehlt

**Anforderung:** REQ-007 – Formularvalidierung (plant_key ist Pflichtfeld)
**Priorität:** High
**Kategorie:** Formularvalidierung

**Vorbedingungen:**
- Nutzer ist eingeloggt
- Mehrere Pflanzen-Instanzen vorhanden

**Testschritte:**
1. Nutzer navigiert zu `/ernte/batches`
2. Nutzer klickt auf "Erntecharge erstellen"
3. Dialog öffnet sich
4. Nutzer wählt keinen Wert für das Pflichtfeld "Pflanze" aus
5. Nutzer klickt auf "Erstellen"

**Erwartetes Ergebnis:**
- Dialog schließt sich NICHT
- Unter dem Feld "Pflanze" erscheint eine Fehlermeldung
- Keine Erfolgsbenachrichtigung

**Postconditions:**
- Keine neue Charge angelegt

**Tags:** [REQ-007, harvest, create, validierung, pflichtfeld]

---

### TC-007-009: Ernte-Batch erstellen – Chargen-ID manuell vergeben (optional)

**Anforderung:** REQ-007 §6 DoD – Batch-ID-Generierung (Schema PLANT_YYYYMMDD_SEQ)
**Priorität:** Medium
**Kategorie:** Happy Path / Dialog

**Vorbedingungen:**
- Nutzer ist eingeloggt
- Pflanze "Pflanze-Beta" existiert

**Testschritte:**
1. Nutzer navigiert zu `/ernte/batches`
2. Nutzer klickt auf "Erntecharge erstellen"
3. Dialog öffnet sich
4. Nutzer wählt "Pflanze-Beta" als Pflanze
5. Nutzer gibt im Feld "Chargen-ID" den Wert "ERNTE-2026-001" ein
6. Nutzer wählt Erntetyp "Teilernte"
7. Nutzer klickt auf "Erstellen"

**Erwartetes Ergebnis:**
- Erfolgsbenachrichtigung "Erntecharge erfolgreich erstellt." erscheint
- Neue Charge erscheint in der Liste mit Chargen-ID "ERNTE-2026-001"
- Erntetyp-Chip zeigt "Teilernte"

**Postconditions:**
- Charge mit manuell vergebener Chargen-ID angelegt

**Tags:** [REQ-007, harvest, create, batch-id, teilernte]

---

### TC-007-010: Ernte-Batch erstellen – Nassgewicht und Notizen eingeben

**Anforderung:** REQ-007 §6 DoD – Erntegewicht-Tracking (Nassgewicht)
**Priorität:** High
**Kategorie:** Happy Path / Dialog

**Vorbedingungen:**
- Nutzer ist eingeloggt
- Pflanze "Pflanze-Gamma" existiert

**Testschritte:**
1. Nutzer navigiert zu `/ernte/batches`
2. Nutzer klickt auf "Erntecharge erstellen"
3. Nutzer wählt "Pflanze-Gamma" als Pflanze
4. Nutzer wählt Erntetyp "Fortlaufend"
5. Nutzer gibt ins Feld "Nassgewicht (g)" den Wert "120" ein
6. Nutzer gibt ins Feld "Erntehelfer" den Wert "Max Mustermann" ein
7. Nutzer gibt ins Feld "Notizen" den Wert "Morgens geerntet, gutes Aroma" ein
8. Nutzer klickt auf "Erstellen"

**Erwartetes Ergebnis:**
- Erfolgsbenachrichtigung "Erntecharge erfolgreich erstellt." erscheint
- Charge erscheint in der Liste mit Nassgewicht "120 g" und Erntetyp-Chip "Fortlaufend"

**Postconditions:**
- Charge mit Nassgewicht und Notizen angelegt

**Tags:** [REQ-007, harvest, create, nassgewicht, notizen, fortlaufend]

---

### TC-007-011: Ernte-Batch erstellen – Negativer Nassgewicht-Wert (Grenzwert)

**Anforderung:** REQ-007 – Formularvalidierung (wet_weight_g min=0)
**Priorität:** Medium
**Kategorie:** Formularvalidierung / Grenzwert

**Vorbedingungen:**
- Nutzer ist eingeloggt
- Eine Pflanze existiert

**Testschritte:**
1. Nutzer öffnet Dialog "Erntecharge erstellen"
2. Nutzer wählt eine Pflanze aus
3. Nutzer gibt "-1" ins Feld "Nassgewicht (g)" ein
4. Nutzer klickt auf "Erstellen"

**Erwartetes Ergebnis:**
- Dialog schließt sich NICHT
- Fehlermeldung am Feld "Nassgewicht (g)" erscheint (Wert muss >= 0 sein)
- Keine Erfolgsbenachrichtigung

**Postconditions:**
- Keine neue Charge angelegt

**Tags:** [REQ-007, harvest, create, validierung, grenzwert, nassgewicht]

---

### TC-007-012: Ernte-Batch erstellen – Dialog abbrechen

**Anforderung:** REQ-007 – Abbruch-Verhalten
**Priorität:** Medium
**Kategorie:** Dialog / Abbruch

**Vorbedingungen:**
- Nutzer ist eingeloggt

**Testschritte:**
1. Nutzer navigiert zu `/ernte/batches`
2. Nutzer klickt auf "Erntecharge erstellen"
3. Dialog öffnet sich
4. Nutzer füllt das Feld "Chargen-ID" mit "TEST-123" aus
5. Nutzer klickt auf "Abbrechen"

**Erwartetes Ergebnis:**
- Dialog schließt sich
- Keine Erfolgs- oder Fehlermeldung erscheint
- Liste der Chargen bleibt unverändert
- Beim erneuten Öffnen des Dialogs sind alle Felder leer (Formular zurückgesetzt)

**Postconditions:**
- Keine neue Charge angelegt

**Tags:** [REQ-007, harvest, create, abbruch, reset]

---

### TC-007-013: Ernte-Batch erstellen – Karenzzeit-Verletzung (Fehlermeldung)

**Anforderung:** REQ-007 §6 DoD – Karenzzeit-Gate (karenz_check_passed), REQ-010 Integration
**Priorität:** Critical
**Kategorie:** Fehlermeldung / Business Rule

**Vorbedingungen:**
- Nutzer ist eingeloggt
- Pflanze "Pflanze-Delta" hat eine aktive IPM-Behandlung mit nicht abgelaufener Karenzzeit
- (Systemkonfiguration: letzte chemische Behandlung liegt weniger als die Karenzzeit zurück)

**Testschritte:**
1. Nutzer klickt auf "Erntecharge erstellen"
2. Nutzer wählt "Pflanze-Delta" als Pflanze
3. Nutzer wählt Erntetyp "Endernte"
4. Nutzer klickt auf "Erstellen"

**Erwartetes Ergebnis:**
- Dialog schließt sich NICHT
- Fehlerbenachrichtigung erscheint (z. B. "Karenzzeit nicht eingehalten – Ernte derzeit nicht möglich")
- Keine neue Erntecharge wird angelegt
- Hinweis auf den sicheren Erntetermin ist ggf. sichtbar (gemäß i18n "karenzSafeDate")

**Postconditions:**
- Keine neue Charge angelegt

**Verweis:** Siehe auch TC-007-007 für den positiven Karenzzeit-Fall

**Tags:** [REQ-007, REQ-010, harvest, create, karenzzeit, fehler]

---

## Gruppe 3: Ernte-Batch Detailansicht

### TC-007-014: Detailseite laden (Happy Path)

**Anforderung:** REQ-007 – Detailansicht mit Tabs
**Priorität:** Critical
**Kategorie:** Happy Path / Detailansicht

**Vorbedingungen:**
- Nutzer ist eingeloggt
- Erntecharge "PLANT_001_20260215_001" existiert mit: Erntetyp "Endernte", Nassgewicht 450 g, Qualitätsstufe "a_plus"

**Testschritte:**
1. Nutzer navigiert zu `/ernte/batches/{key}` der Charge

**Erwartetes Ergebnis:**
- Seitenüberschrift zeigt "PLANT_001_20260215_001"
- Grüner Chip "A+" ist neben der Überschrift sichtbar
- 4 Tabs sind sichtbar: "Details", "Qualität", "Ertrag", "Bearbeiten"
- Tab "Details" ist standardmäßig aktiv
- Detailtabelle zeigt alle Felder: Chargen-ID, Pflanze, Erntedatum, Erntetyp "Endernte", Nassgewicht "450 g"

**Postconditions:**
- Keine Datenänderung

**Tags:** [REQ-007, harvest, detail, happy-path, tabs]

---

### TC-007-015: Detailseite – Tab Details – alle Felder sichtbar

**Anforderung:** REQ-007 §6 DoD – Batch-Tracking mit Nass/Trockengewicht
**Priorität:** High
**Kategorie:** Detailansicht / Datenverifikation

**Vorbedingungen:**
- Nutzer ist eingeloggt
- Erntecharge existiert mit: Nassgewicht 500 g, geschätztes Trockengewicht 125 g, tatsächliches Trockengewicht 118 g, Erntehelfer "Maria Schmidt", Notiz "Top-Buds zuerst geerntet"

**Testschritte:**
1. Nutzer navigiert zur Detailseite der Charge
2. Nutzer ist auf Tab "Details" (Tab 0)

**Erwartetes Ergebnis:**
- Tabelle zeigt alle folgenden Zeilen mit korrekten Werten:
  - "Nassgewicht (g)": "500 g"
  - "Geschätztes Trockengewicht (g)": "125 g"
  - "Tatsächliches Trockengewicht (g)": "118 g"
  - "Erntehelfer": "Maria Schmidt"
  - "Notizen": "Top-Buds zuerst geerntet"
- Felder ohne Wert zeigen "—"

**Postconditions:**
- Keine Datenänderung

**Tags:** [REQ-007, harvest, detail, tabs, daten, trockengewicht]

---

### TC-007-016: Detailseite – Nicht gefunden (404)

**Anforderung:** REQ-007 – Fehlerbehandlung bei ungültigem Schlüssel
**Priorität:** Medium
**Kategorie:** Fehlermeldung / Edge Case

**Vorbedingungen:**
- Nutzer ist eingeloggt

**Testschritte:**
1. Nutzer navigiert zu `/ernte/batches/existiert-nicht`

**Erwartetes Ergebnis:**
- Seite zeigt eine Fehlermeldung (ErrorDisplay-Komponente)
- Meldung "Nicht gefunden" oder ähnlich ist sichtbar
- Kein Absturz oder leere weiße Seite

**Postconditions:**
- Keine Datenänderung

**Tags:** [REQ-007, harvest, detail, fehler, 404]

---

## Gruppe 4: Ernte-Batch Bearbeiten (Tab 3)

### TC-007-017: Batch bearbeiten – Erntetyp und Qualitätsstufe ändern (Happy Path)

**Anforderung:** REQ-007 §6 DoD – Batch-Update-Funktionalität
**Priorität:** Critical
**Kategorie:** Happy Path / Formular

**Vorbedingungen:**
- Nutzer ist eingeloggt
- Erntecharge mit Erntetyp "Endernte" und Qualitätsstufe "B" existiert

**Testschritte:**
1. Nutzer navigiert zur Detailseite der Charge
2. Nutzer klickt auf Tab "Bearbeiten"
3. Nutzer ändert im Dropdown "Erntetyp" den Wert auf "Teilernte"
4. Nutzer ändert im Dropdown "Qualitätsstufe" den Wert auf "A"
5. Nutzer klickt auf "Speichern"

**Erwartetes Ergebnis:**
- Erfolgsbenachrichtigung "Speichern" erscheint als Snackbar (gemäß i18n `common.save`)
- Detailseite wird neu geladen
- Tab "Details" zeigt den aktualisierten Erntetyp "Teilernte"
- Chip in der Kopfzeile zeigt jetzt "A" (grün)

**Postconditions:**
- Charge im System mit Erntetyp "Teilernte" und Qualitätsstufe "A" aktualisiert

**Tags:** [REQ-007, harvest, edit, happy-path, qualitaet, chip]

---

### TC-007-018: Batch bearbeiten – Trockengewichte nachtragen

**Anforderung:** REQ-007 §6 DoD – Erntegewicht-Tracking (Nass + artspezifisches geschätztes Trockengewicht)
**Priorität:** High
**Kategorie:** Happy Path / Formular

**Vorbedingungen:**
- Nutzer ist eingeloggt
- Erntecharge ohne Trockengewicht existiert (estimated_dry_weight_g und actual_dry_weight_g sind null)

**Testschritte:**
1. Nutzer navigiert zur Detailseite der Charge
2. Nutzer klickt auf Tab "Bearbeiten"
3. Nutzer gibt ins Feld "Geschätztes Trockengewicht (g)" den Wert "112" ein
4. Nutzer gibt ins Feld "Tatsächliches Trockengewicht (g)" den Wert "108" ein
5. Nutzer klickt auf "Speichern"

**Erwartetes Ergebnis:**
- Erfolgsbenachrichtigung erscheint
- Tab "Details" zeigt "Geschätztes Trockengewicht (g)": "112 g" und "Tatsächliches Trockengewicht (g)": "108 g"

**Postconditions:**
- Charge mit Trockengewichten aktualisiert

**Tags:** [REQ-007, harvest, edit, trockengewicht, nachtragen]

---

### TC-007-019: Batch bearbeiten – "Speichern"-Button inaktiv bei unveränderten Daten

**Anforderung:** REQ-007 – UX: Bearbeiten-Formular
**Priorität:** Medium
**Kategorie:** Formular / UX

**Vorbedingungen:**
- Nutzer ist eingeloggt
- Erntecharge existiert

**Testschritte:**
1. Nutzer navigiert zur Detailseite und wechselt auf Tab "Bearbeiten"
2. Nutzer liest die Formularwerte, ändert jedoch nichts

**Erwartetes Ergebnis:**
- Schaltfläche "Speichern" ist deaktiviert (disabled), da keine Änderungen vorliegen (isDirty = false)

**Postconditions:**
- Keine Datenänderung

**Tags:** [REQ-007, harvest, edit, isDirty, disabled-button]

---

### TC-007-020: Batch bearbeiten – UnsavedChangesGuard bei Verlassen mit ungespeicherten Daten

**Anforderung:** REQ-007 – UnsavedChangesGuard
**Priorität:** High
**Kategorie:** Navigation / Guard

**Vorbedingungen:**
- Nutzer ist eingeloggt
- Erntecharge existiert

**Testschritte:**
1. Nutzer navigiert zur Detailseite und wechselt auf Tab "Bearbeiten"
2. Nutzer ändert den Wert im Feld "Erntehelfer" zu einem neuen Namen
3. Nutzer klickt im Browser auf "Zurück" oder navigiert zu einer anderen Seite

**Erwartetes Ergebnis:**
- Browser zeigt einen Bestätigungs-Dialog: "Sie haben ungespeicherte Änderungen. Möchten Sie die Seite wirklich verlassen?"
- Wenn Nutzer "Abbrechen" klickt: bleibt auf der Bearbeitungsseite, Daten sind noch im Formular
- Wenn Nutzer "Verlassen" klickt: Navigation erfolgt, Änderungen gehen verloren

**Postconditions:**
- Abhängig von Nutzerauswahl

**Tags:** [REQ-007, harvest, edit, unsaved-changes, guard]

---

### TC-007-021: Batch bearbeiten – Negativer Gewichtswert (Validierung)

**Anforderung:** REQ-007 – Formularvalidierung
**Priorität:** Medium
**Kategorie:** Formularvalidierung

**Vorbedingungen:**
- Nutzer ist eingeloggt
- Erntecharge existiert

**Testschritte:**
1. Nutzer navigiert auf Tab "Bearbeiten"
2. Nutzer löscht den Wert im Feld "Nassgewicht (g)" und gibt "-5" ein
3. Nutzer klickt auf "Speichern"

**Erwartetes Ergebnis:**
- Speichern wird abgebrochen
- Fehlermeldung unter dem Feld "Nassgewicht (g)" erscheint
- Keine Erfolgsbenachrichtigung

**Postconditions:**
- Keine Datenänderung

**Tags:** [REQ-007, harvest, edit, validierung, grenzwert]

---

## Gruppe 5: Qualitätsbewertung (Tab 1)

### TC-007-022: Qualitätsbewertung erstellen (Happy Path)

**Anforderung:** REQ-007 §6 DoD – Quality-Scoring (appearance, aroma, color)
**Priorität:** Critical
**Kategorie:** Happy Path / Formular

**Vorbedingungen:**
- Nutzer ist eingeloggt
- Erntecharge existiert, noch KEINE Qualitätsbewertung vorhanden

**Testschritte:**
1. Nutzer navigiert zur Detailseite der Charge
2. Nutzer klickt auf Tab "Qualität"
3. Nutzer sieht das Formular "Qualitätsbewertung erstellen" mit Abschnitten: "Qualitätsbewertung erstellen", "Bewertungen", "Mängel & Notizen"
4. Nutzer gibt ins Pflichtfeld "Bewertet von" den Wert "Dr. Anna Müller" ein
5. Nutzer gibt ins Feld "Erscheinungsbewertung (0-100)" den Wert "95" ein
6. Nutzer gibt ins Feld "Aromabewertung (0-100)" den Wert "90" ein
7. Nutzer gibt ins Feld "Farbbewertung (0-100)" den Wert "92" ein
8. Nutzer klickt auf "Erstellen"

**Erwartetes Ergebnis:**
- Erfolgsbenachrichtigung "Qualitätsbewertung erfolgreich erstellt." erscheint
- Tab "Qualität" zeigt jetzt die erstellte Bewertung als Tabelle (nicht mehr das Formular)
- Tabelle zeigt: "Bewertet von": "Dr. Anna Müller", Erscheinungsbewertung: Fortschrittsbalken bei 95 mit Wert "95", Aromabewertung: 90, Farbbewertung: 92
- Gesamtbewertung (LinearProgress) ist sichtbar mit farbenem Balken

**Postconditions:**
- Qualitätsbewertung für die Charge angelegt

**Tags:** [REQ-007, harvest, quality, create, happy-path, scores]

---

### TC-007-023: Qualitätsbewertung – Pflichtfeld "Bewertet von" fehlt

**Anforderung:** REQ-007 – Formularvalidierung (assessed_by min=1)
**Priorität:** High
**Kategorie:** Formularvalidierung

**Vorbedingungen:**
- Nutzer ist eingeloggt
- Erntecharge ohne Qualitätsbewertung existiert

**Testschritte:**
1. Nutzer öffnet Tab "Qualität"
2. Nutzer lässt das Pflichtfeld "Bewertet von" leer
3. Nutzer gibt Erscheinungsbewertung 80, Aromabewertung 75, Farbbewertung 70 ein
4. Nutzer klickt auf "Erstellen"

**Erwartetes Ergebnis:**
- Formular wird NICHT abgeschickt
- Fehlermeldung unter "Bewertet von" erscheint
- Keine Erfolgsbenachrichtigung

**Postconditions:**
- Keine Qualitätsbewertung angelegt

**Tags:** [REQ-007, harvest, quality, validierung, pflichtfeld]

---

### TC-007-024: Qualitätsbewertung – Score außerhalb Bereich 0–100

**Anforderung:** REQ-007 – Formularvalidierung (scores 0–100)
**Priorität:** Medium
**Kategorie:** Formularvalidierung / Grenzwert

**Vorbedingungen:**
- Nutzer ist eingeloggt
- Erntecharge ohne Qualitätsbewertung existiert

**Testschritte:**
1. Nutzer öffnet Tab "Qualität"
2. Nutzer gibt ins Feld "Bewertet von" "Tester" ein
3. Nutzer gibt ins Feld "Erscheinungsbewertung" den Wert "150" ein (über Maximum)
4. Nutzer klickt auf "Erstellen"

**Erwartetes Ergebnis:**
- Formular wird NICHT abgeschickt
- Fehlermeldung unter "Erscheinungsbewertung" erscheint (Wert muss zwischen 0 und 100 liegen)

**Postconditions:**
- Keine Qualitätsbewertung angelegt

**Tags:** [REQ-007, harvest, quality, validierung, grenzwert, score]

---

### TC-007-025: Qualitätsbewertung – Mängel als Chips hinzufügen

**Anforderung:** REQ-007 §6 DoD – Quality-Scoring mit Defects
**Priorität:** High
**Kategorie:** Happy Path / Formular / Chip-Input

**Vorbedingungen:**
- Nutzer ist eingeloggt
- Erntecharge ohne Qualitätsbewertung existiert

**Testschritte:**
1. Nutzer öffnet Tab "Qualität"
2. Nutzer gibt "Dr. Tester" als Bewerter ein
3. Nutzer gibt im Feld "Mängel" den Text "Schimmelfleck" ein und drückt Enter
4. Nutzer gibt im Feld "Mängel" den Text "Hermaphroditismus" ein und drückt Enter
5. Nutzer gibt Scores ein (jeweils 60) und klickt auf "Erstellen"

**Erwartetes Ergebnis:**
- Nach dem ersten Enter erscheint ein roter Chip "Schimmelfleck" im Mängelfeld
- Nach dem zweiten Enter erscheint ein zweiter Chip "Hermaphroditismus"
- Nach dem Erstellen zeigt die Bewertungs-Tabelle den Abschnitt "Mängel" mit roten Chips "Schimmelfleck" und "Hermaphroditismus"

**Postconditions:**
- Qualitätsbewertung mit 2 Mängeln angelegt

**Tags:** [REQ-007, harvest, quality, defekte, chip-input]

---

### TC-007-026: Qualitätsbewertung anzeigen – Gesamtbewertung Farbe (80+/60+/<60)

**Anforderung:** REQ-007 §6 DoD – Grade-Distribution / Qualitätsscore-Visualisierung
**Priorität:** Medium
**Kategorie:** Detailansicht / Visuelle Darstellung

**Vorbedingungen:**
- Nutzer ist eingeloggt
- 3 Erntechargen mit Qualitätsbewertungen: overall_score = 85, 65, 40

**Testschritte:**
1. Nutzer navigiert zu jeder der 3 Chargen, Tab "Qualität"

**Erwartetes Ergebnis:**
- Charge mit overall_score 85: Gesamtbewertungs-LinearProgress ist grün (success), Grade-Chip zeigt "A" (grün)
- Charge mit overall_score 65: LinearProgress ist orange (warning)
- Charge mit overall_score 40: LinearProgress ist rot (error)

**Postconditions:**
- Keine Datenänderung

**Tags:** [REQ-007, harvest, quality, farbe, linearprogresss, score]

---

### TC-007-027: Qualitätsbewertung anzeigen – Bewertung bereits vorhanden (kein Formular)

**Anforderung:** REQ-007 – Quality Tab: entweder Anzeige-Tabelle ODER Erstellungsformular
**Priorität:** Medium
**Kategorie:** Detailansicht / State

**Vorbedingungen:**
- Nutzer ist eingeloggt
- Erntecharge mit bereits vorhandener Qualitätsbewertung existiert

**Testschritte:**
1. Nutzer navigiert zur Detailseite, Tab "Qualität"

**Erwartetes Ergebnis:**
- Die Anzeige-Tabelle mit den Bewertungswerten ist sichtbar
- Das Erstellungsformular ist NICHT sichtbar
- Kein "Erstellen"-Button in diesem Tab

**Postconditions:**
- Keine Datenänderung

**Tags:** [REQ-007, harvest, quality, readonly, bereits-vorhanden]

---

## Gruppe 6: Ertragsmetriken (Tab 2)

### TC-007-028: Ertragsmetriken erstellen (Happy Path)

**Anforderung:** REQ-007 §6 DoD – Yield-Analytics, Gram/m²/Tag-Berechnung
**Priorität:** Critical
**Kategorie:** Happy Path / Formular

**Vorbedingungen:**
- Nutzer ist eingeloggt
- Erntecharge existiert, noch KEINE Ertragsmetriken vorhanden

**Testschritte:**
1. Nutzer navigiert zur Detailseite der Charge
2. Nutzer klickt auf Tab "Ertrag"
3. Nutzer sieht das Formular "Ertragsmetriken erstellen"
4. Nutzer gibt in "Ertrag pro Pflanze (g)" den Wert "450" ein
5. Nutzer gibt in "Ertrag pro m² (g)" den Wert "900" ein
6. Nutzer gibt in "Gesamtertrag (g)" den Wert "450" ein
7. Nutzer gibt in "Nutzbarer Ertrag (g)" den Wert "420" ein
8. Nutzer gibt in "Verschnitt (%)" den Wert "6.7" ein
9. Nutzer klickt auf "Erstellen"

**Erwartetes Ergebnis:**
- Erfolgsbenachrichtigung "Ertragsmetriken erfolgreich erstellt." erscheint
- Tab "Ertrag" zeigt die Ertragsmetriken als Tabelle:
  - "Ertrag pro Pflanze (g)": "450 g"
  - "Ertrag pro m² (g)": "900 g/m2"
  - "Gesamtertrag (g)": "450 g"
  - "Verschnitt (%)": "6.7%"
  - "Nutzbarer Ertrag (g)": "420 g"

**Postconditions:**
- Ertragsmetriken für die Charge angelegt

**Tags:** [REQ-007, harvest, yield, create, happy-path]

---

### TC-007-029: Ertragsmetriken – Nutzbarer Ertrag > Gesamtertrag (Validierung)

**Anforderung:** REQ-007 – Formularvalidierung (usable_yield_g <= total_yield_g)
**Priorität:** High
**Kategorie:** Formularvalidierung / Business Rule

**Vorbedingungen:**
- Nutzer ist eingeloggt
- Erntecharge ohne Ertragsmetriken existiert

**Testschritte:**
1. Nutzer öffnet Tab "Ertrag"
2. Nutzer gibt "Gesamtertrag (g)" = "200" ein
3. Nutzer gibt "Nutzbarer Ertrag (g)" = "250" ein (größer als Gesamtertrag)
4. Nutzer klickt auf "Erstellen"

**Erwartetes Ergebnis:**
- Formular wird NICHT erfolgreich abgeschickt
- Fehlermeldung erscheint (Nutzbarer Ertrag kann nicht größer als Gesamtertrag sein)
- Keine Erfolgsbenachrichtigung

**Postconditions:**
- Keine Ertragsmetriken angelegt

**Tags:** [REQ-007, harvest, yield, validierung, business-rule]

---

### TC-007-030: Ertragsmetriken – Verschnitt außerhalb 0–100% (Grenzwert)

**Anforderung:** REQ-007 – Formularvalidierung (trim_waste_percent 0–100)
**Priorität:** Medium
**Kategorie:** Formularvalidierung / Grenzwert

**Vorbedingungen:**
- Nutzer ist eingeloggt
- Erntecharge ohne Ertragsmetriken existiert

**Testschritte:**
1. Nutzer öffnet Tab "Ertrag"
2. Nutzer gibt "Verschnitt (%)" = "110" ein (über Maximum)
3. Nutzer klickt auf "Erstellen"

**Erwartetes Ergebnis:**
- Formular wird NICHT abgeschickt
- Fehlermeldung unter "Verschnitt (%)" erscheint

**Postconditions:**
- Keine Ertragsmetriken angelegt

**Tags:** [REQ-007, harvest, yield, validierung, grenzwert, verschnitt]

---

### TC-007-031: Ertragsmetriken anzeigen – Tabelle und Einheiten

**Anforderung:** REQ-007 §6 DoD – Yield-Analytics mit Einheitenanzeige
**Priorität:** Medium
**Kategorie:** Detailansicht / Datenverifikation

**Vorbedingungen:**
- Nutzer ist eingeloggt
- Erntecharge mit Ertragsmetriken existiert (yield_per_m2_g = 850.5)

**Testschritte:**
1. Nutzer navigiert zur Detailseite, Tab "Ertrag"

**Erwartetes Ergebnis:**
- "Ertrag pro m² (g)"-Zeile zeigt "850.5 g/m2" (mit korrekter Einheit)
- Alle anderen Gewichtsfelder zeigen Einheit "g"
- "Verschnitt (%)"-Zeile zeigt Prozentwert mit "%"-Einheit

**Postconditions:**
- Keine Datenänderung

**Tags:** [REQ-007, harvest, yield, einheiten, anzeige]

---

## Gruppe 7: Erntereife-Karte (HarvestReadinessCard)

### TC-007-032: Erntereife-Karte – Status "Optimal" (Peak)

**Anforderung:** REQ-007 §6 DoD – Harvest-Kalender, Reife-Visualisierung
**Priorität:** Critical
**Kategorie:** Happy Path / Visuelle Darstellung

**Vorbedingungen:**
- Nutzer ist eingeloggt
- Pflanzen-Detailseite oder Kontext mit HarvestReadinessCard ist zugänglich
- Pflanze hat overall_score = 92, recommendation = "optimal", estimated_days = 1
- Indikatoren: trichome (stage "peak", score 100, reliability 0.9), aroma (stage "approaching", score 75, reliability 0.7)

**Testschritte:**
1. Nutzer navigiert zu einer Seite, die die `HarvestReadinessCard` für die Pflanze zeigt
   (z. B. Pflanzen-Detailseite in der Übersicht oder eine verknüpfte Ernte-Readiness-Ansicht)

**Erwartetes Ergebnis:**
- Karten-Überschrift "Erntereife" ist sichtbar
- Gesamtbewertungs-LinearProgress zeigt grünen Balken bei Wert 92
- Großer Wert "92" ist neben der Fortschrittsanzeige sichtbar
- Grüner Chip "Erntebereit" erscheint bei "Empfehlung"
- "Geschätzte Tage bis Ernte: 1 Tage" ist sichtbar
- Indikator-Tabelle zeigt 2 Zeilen:
  - Zeile 1: Indikator "trichome", Stadium-Chip "Optimal" (grün), Score 100, Zuverlässigkeit "90%"
  - Zeile 2: Indikator "aroma", Stadium-Chip "Heranreifend" (orange), Score 75, Zuverlässigkeit "70%"

**Postconditions:**
- Keine Datenänderung

**Tags:** [REQ-007, harvest, readiness, card, peak, trichom]

---

### TC-007-033: Erntereife-Karte – Status "Überreif" (overripe)

**Anforderung:** REQ-007 §6 DoD – Reife-Stadien: overripe
**Priorität:** High
**Kategorie:** Fehlermeldung / Visuelle Darstellung

**Vorbedingungen:**
- Nutzer ist eingeloggt
- Pflanze hat recommendation = "immature" (default-Fall, entspricht overripe-Stadium), overall_score = 20
- Indikator mit stage = "overripe" vorhanden

**Testschritte:**
1. Nutzer öffnet Erntereife-Karte der Pflanze

**Erwartetes Ergebnis:**
- LinearProgress zeigt roten Balken (score < 50)
- Chip für recommendation zeigt roten Chip mit entsprechendem Label
- Indikator mit stage "overripe" wird als roter Chip "Überreif" dargestellt

**Postconditions:**
- Keine Datenänderung

**Tags:** [REQ-007, harvest, readiness, card, overripe, warnung]

---

### TC-007-034: Erntereife-Karte – Keine geschätzte Erntezeit (estimated_days null)

**Anforderung:** REQ-007 – Erntereife-Anzeige Edge Case
**Priorität:** Low
**Kategorie:** Edge Case / Visuelle Darstellung

**Vorbedingungen:**
- Nutzer ist eingeloggt
- Erntereife-Daten haben estimated_days = null (kein Schätzwert verfügbar)

**Testschritte:**
1. Nutzer öffnet Erntereife-Karte der entsprechenden Pflanze

**Erwartetes Ergebnis:**
- Der Abschnitt "Geschätzte Tage bis Ernte" ist NICHT sichtbar (conditional rendering)
- Alle anderen Abschnitte der Karte sind normal sichtbar

**Postconditions:**
- Keine Datenänderung

**Tags:** [REQ-007, harvest, readiness, card, null, conditional-rendering]

---

### TC-007-035: Erntereife-Karte – Indikatoren-Stadium-Chips Farbkodierung

**Anforderung:** REQ-007 §6 DoD – Reife-Stadien sichtbar in UI
**Priorität:** Medium
**Kategorie:** Visuelle Darstellung

**Vorbedingungen:**
- Nutzer ist eingeloggt
- Pflanze hat 4 Indikatoren mit allen möglichen Stadien: "peak", "approaching", "overripe", "developing"

**Testschritte:**
1. Nutzer öffnet Erntereife-Karte

**Erwartetes Ergebnis:**
- Stadium "peak": Chip "Optimal" in Farbe grün (success)
- Stadium "approaching": Chip "Heranreifend" in Farbe orange (warning)
- Stadium "overripe": Chip "Überreif" in Farbe rot (error)
- Stadium "developing" (und sonstige): Chip "Unreif" in Standardfarbe (default/grau)

**Postconditions:**
- Keine Datenänderung

**Tags:** [REQ-007, harvest, readiness, card, indikatoren, chips, farbe]

---

## Gruppe 8: Vollständige Nutzer-Journey

### TC-007-036: Vollständige Ernte-Journey – Charge anlegen, bewerten, Ertrag erfassen

**Anforderung:** REQ-007 §6 DoD – kompletter Zyklus Batch → Quality → Yield
**Priorität:** Critical
**Kategorie:** Happy Path / End-to-End

**Vorbedingungen:**
- Nutzer ist eingeloggt
- Pflanze "Cannabis Alpha" existiert, keine aktiven Karenzzeiten

**Testschritte:**
1. Nutzer navigiert zu `/ernte/batches`
2. Nutzer klickt auf "Erntecharge erstellen"
3. Nutzer wählt "Cannabis Alpha", Erntetyp "Endernte", Nassgewicht 500 g, Erntehelfer "Hans" und klickt "Erstellen"
4. Neue Charge erscheint in der Liste; Nutzer klickt darauf
5. Nutzer prüft Tab "Details": Nassgewicht "500 g" ist sichtbar
6. Nutzer klickt auf Tab "Qualität"
7. Nutzer sieht das Erstellungsformular
8. Nutzer gibt ein: Bewertet von "Hans", Erscheinungsbewertung 90, Aromabewertung 85, Farbbewertung 88, Mängel keiner
9. Nutzer klickt "Erstellen"
10. Nutzer klickt auf Tab "Ertrag"
11. Nutzer sieht Ertrags-Erstellungsformular
12. Nutzer gibt ein: Ertrag/Pflanze 500 g, Gesamtertrag 500 g, Nutzbarer Ertrag 475 g, Verschnitt 5%
13. Nutzer klickt "Erstellen"
14. Nutzer navigiert zu `/ernte/batches` (zurück zur Liste)

**Erwartetes Ergebnis:**
- Schritt 3: Erfolgsmeldung "Erntecharge erfolgreich erstellt."
- Schritt 5: "500 g" sichtbar, Erntetyp "Endernte" sichtbar
- Schritt 9: Erfolgsmeldung "Qualitätsbewertung erfolgreich erstellt.", Bewertungs-Tabelle erscheint
- Schritt 13: Erfolgsmeldung "Ertragsmetriken erfolgreich erstellt.", Ertrags-Tabelle erscheint
- Schritt 14: Charge erscheint in der Liste

**Postconditions:**
- Vollständig dokumentierte Erntecharge mit Qualitätsbewertung und Ertragsmetriken

**Tags:** [REQ-007, harvest, e2e, journey, quality, yield, create]

---

### TC-007-037: Navigations-Breadcrumb: Liste → Detail → zurück

**Anforderung:** REQ-007 – Navigation
**Priorität:** Medium
**Kategorie:** Navigation

**Vorbedingungen:**
- Nutzer ist eingeloggt
- Mindestens 1 Erntecharge vorhanden

**Testschritte:**
1. Nutzer navigiert zu `/ernte/batches`
2. Nutzer klickt auf eine Charge (navigiert zur Detailseite)
3. Nutzer klickt im Browser auf den "Zurück"-Button

**Erwartetes Ergebnis:**
- Browser navigiert zurück zu `/ernte/batches`
- Liste zeigt alle Chargen unverändert

**Postconditions:**
- Keine Datenänderung

**Tags:** [REQ-007, harvest, navigation, back-button]

---

## Gruppe 9: Tablet-Responsive und Sonderfälle

### TC-007-038: Tablet-Ansicht – Spalte "Pflanze" ausgeblendet

**Anforderung:** REQ-007 §6 DoD – Tablet-Spaltenprioritäten (UI-NFR-010 §8.1): Pflanzen-Key auf Tablet ausgeblendet
**Priorität:** Medium
**Kategorie:** Responsive / Tablet

**Vorbedingungen:**
- Nutzer verwendet ein Tablet-Gerät oder Browser mit Viewport-Breite < 960px (md-Breakpoint)
- Mindestens 1 Erntecharge vorhanden

**Testschritte:**
1. Nutzer setzt Viewport-Breite auf 800px (oder verwendet Tablet-Gerät)
2. Nutzer navigiert zu `/ernte/batches`

**Erwartetes Ergebnis:**
- Spalte "Pflanze" ist NICHT sichtbar in der Tabelle (hideBelowBreakpoint: 'md')
- Spalte "Erntetyp" ist ebenfalls NICHT sichtbar (hideBelowBreakpoint: 'md')
- Sichtbare Spalten: "Chargen-ID", "Erntedatum", "Nassgewicht (g)", "Qualitätsstufe"
- MobileCard-Renderer wird für Chargen verwendet und zeigt Batch-ID als Titel, Datum als Untertitel

**Postconditions:**
- Keine Datenänderung

**Tags:** [REQ-007, harvest, responsive, tablet, spalten, NFR-010]

---

### TC-007-039: Ernte-Batch erstellen – Dialog vollbild auf Mobilgerät

**Anforderung:** REQ-007 – Mobile Dialog (fullScreen)
**Priorität:** Medium
**Kategorie:** Responsive / Mobile

**Vorbedingungen:**
- Nutzer verwendet Mobilgerät oder Browser mit Viewport < 600px (sm-Breakpoint)

**Testschritte:**
1. Nutzer navigiert zu `/ernte/batches` auf Mobilgerät
2. Nutzer klickt auf "Erntecharge erstellen"

**Erwartetes Ergebnis:**
- Dialog öffnet sich im Vollbildmodus (fullScreen = true)
- Alle Formularfelder sind scrollbar und bedienbar

**Postconditions:**
- Keine Datenänderung

**Tags:** [REQ-007, harvest, create, mobile, dialog, responsive]

---

### TC-007-040: Tab-Navigation per URL-Parameter (useTabUrl)

**Anforderung:** REQ-007 – Tab-Persistenz
**Priorität:** Low
**Kategorie:** Navigation / URL

**Vorbedingungen:**
- Nutzer ist eingeloggt
- Erntecharge existiert

**Testschritte:**
1. Nutzer navigiert zur Detailseite der Charge
2. Nutzer klickt auf Tab "Qualität" (Tab 1)
3. Nutzer kopiert die aktuelle URL
4. Nutzer öffnet diese URL in einem neuen Browser-Tab

**Erwartetes Ergebnis:**
- Im neuen Tab öffnet sich die Detailseite direkt auf Tab "Qualität"
- Tab "Qualität" ist vorausgewählt (useTabUrl persistiert den aktiven Tab in der URL)

**Postconditions:**
- Keine Datenänderung

**Tags:** [REQ-007, harvest, detail, tab, url-persistenz, useTabUrl]

---

## Gruppe 10: Erntereife-Beobachtungen (API-Ebene, UI-seitig)

### TC-007-041: Erntereife-Beobachtung erstellen (createObservation)

**Anforderung:** REQ-007 §6 DoD – Trichom-Mikroskop-Guide, Harvest-Indikatoren
**Priorität:** High
**Kategorie:** Happy Path / Formular

**Vorbedingungen:**
- Nutzer ist eingeloggt
- Pflanzen-Instanz mit konfigurierten Harvest-Indikatoren existiert
- UI-Einstiegspunkt für Beobachtungen ist zugänglich (z. B. aus Pflanzen-Detail oder dedizierter Seite)

**Testschritte:**
1. Nutzer navigiert zur Seite/zum Abschnitt "Beobachtung erstellen" für eine Pflanze
2. Nutzer gibt Pflichten-Felder ein: "Beobachter", Indikatortyp (z. B. "trichome"), Reifebeurteilung "Optimal" (peak), geschätzte Tage bis Ernte "2"
3. Nutzer klickt auf "Erstellen"

**Erwartetes Ergebnis:**
- Erfolgsbenachrichtigung "Beobachtung erfolgreich erstellt." erscheint
- Erntereife-Karte der Pflanze aktualisiert sich und zeigt aktualisierte Gesamt-Readiness-Score

**Postconditions:**
- Neue Harvest-Beobachtung im System

**Tags:** [REQ-007, harvest, observation, create, trichom]

---

### TC-007-042: Qualitätsbewertung – Score-Fortschrittsbalken Grenzwert 80 und 60

**Anforderung:** REQ-007 – Qualitätsscore-Visualisierung (Farbschwellen bei 80 und 60)
**Priorität:** Medium
**Kategorie:** Grenzwert / Visuelle Darstellung

**Vorbedingungen:**
- Nutzer ist eingeloggt
- 3 Chargen mit Qualitätsbewertungen: overall_score = 80, 60, 59

**Testschritte:**
1. Nutzer öffnet Charge mit overall_score = 80, Tab "Qualität"
2. Nutzer öffnet Charge mit overall_score = 60, Tab "Qualität"
3. Nutzer öffnet Charge mit overall_score = 59, Tab "Qualität"

**Erwartetes Ergebnis:**
- Score 80: Gesamtbewertungs-LinearProgress ist GRÜN (>= 80)
- Score 60: LinearProgress ist ORANGE (>= 60 und < 80)
- Score 59: LinearProgress ist ROT (< 60)

**Postconditions:**
- Keine Datenänderung

**Tags:** [REQ-007, harvest, quality, score, grenzwert, farbschwellen, linearprogress]

---

## Abdeckungs-Matrix

| Spezifikations-Abschnitt | Beschreibung | Abgedeckte Testfälle |
|---|---|---|
| §1 – Business Case / Ernte-Strategien | Partial/Final/Continuous Harvest-Typen | TC-007-009, TC-007-010, TC-007-017 |
| §2 – ArangoDB-Modell / batches-Collection | Batch-Felder (ID, Datum, Typ, Gewichte, Grade) | TC-007-014, TC-007-015, TC-007-017, TC-007-018 |
| §2 – quality_assessments-Collection | Scores (0–100), Defects, Grade-Zuweisung | TC-007-022, TC-007-023, TC-007-024, TC-007-025, TC-007-026 |
| §2 – yield_metrics-Collection | Yield/Pflanze, Yield/m², Verschnitt | TC-007-028, TC-007-029, TC-007-030, TC-007-031 |
| §3 – TrichomeIndicator / Reife-Visualisierung | Erntereife-Karte mit Stage-Chips und Score | TC-007-032, TC-007-033, TC-007-034, TC-007-035 |
| §4 – Auth & Tenant (Mitglied-Rechte) | Eingeloggt-Zustand Voraussetzung für alle Tests | Alle Testfälle (Vorbedingung) |
| §5 – Abhängigkeit REQ-010 Karenz-Gate | Batch-Erstellung blockiert bei offener Karenzzeit | TC-007-013 |
| §6 DoD – Batch-ID-Generierung | Manuell + automatisch generierte Batch-ID | TC-007-007, TC-007-009 |
| §6 DoD – Erntegewicht-Tracking | Nassgewicht, geschätztes + tatsächliches Trockengewicht | TC-007-010, TC-007-011, TC-007-018 |
| §6 DoD – Listenansicht-Filter (UI-NFR-010) | Such- und Sortier-Funktionalität | TC-007-003, TC-007-004 |
| §6 DoD – Tablet-Spaltenprioritäten (UI-NFR-010) | Spalten-Responsive-Verhalten | TC-007-038 |
| §6 DoD – Qualitäts-Grade Distribution | Farbkodierung A+/A/B/C/D | TC-007-005, TC-007-026, TC-007-042 |
| §6 Testszenarien – Szenario 3 (Batch QR-Code) | Batch-ID im Format PLANT_YYYYMMDD_SEQ | TC-007-007, TC-007-009 |
| §6 Testszenarien – Szenario 4 (Quality Grading) | Qualitätsscore und Grading sichtbar | TC-007-022, TC-007-026 |
| Listenansicht-Navigation | List → Detail-Navigation | TC-007-006 |
| UnsavedChangesGuard | Warnung bei ungespeicherten Änderungen | TC-007-020 |
| Tab-Persistenz (useTabUrl) | URL-Parameter für aktiven Tab | TC-007-040 |
| Mobile/Responsive | Vollbild-Dialog auf Mobilgeräten | TC-007-039 |
| Empty State | Leere Liste mit Illustration | TC-007-002 |
| End-to-End Journey | Vollständige Harvest-Workflow | TC-007-036 |
