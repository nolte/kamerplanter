---
req_id: REQ-001
title: Stammdatenverwaltung von Pflanzen-Entitätszyklen
category: Stammdaten
test_count: 78
coverage_areas:
  - BotanicalFamily CRUD
  - BotanicalFamily Formvalidierung (aceae, ales, nitrogen_fixing + heavy)
  - BotanicalFamily pH-Bereich-Validierung
  - BotanicalFamily Listenansicht & Suche & Sort
  - Species CRUD
  - Species Formvalidierung (scientific_name, allelopathy, pH)
  - Species wissenschaftlicher Name — Binomial & Hybrid-Notation
  - Species traits Validierung
  - Species Listenansicht & Filter (family, toggles, sowNow, favorites)
  - Species Detailansicht Tabs (Bearbeiten, Anbauperioden, Sorten, Lebenszyklus, Workflows)
  - Species Favoriten & Saisonfilter
  - Cultivar CRUD inkl. Autoflower-Felder
  - Cultivar Autoflower-Validierung (days_to_flower < total_cycle_days)
  - Cultivar Phasen-Bewässerungsüberschreibungen
  - Cultivar Detailseite
  - Navigation & Breadcrumbs
  - Unsaved-Changes-Guard
  - Familien-Filterverlinkung Species→Familie
  - CropRotationPage (CRITICAL/WARNING/OK)
  - Seed-Daten Verifikation (9 + Zierpflanzen-Familien)
  - Toxizitätsdaten Anzeige (Haustiersicherheit)
  - Allergen-Anzeige
  - Vermehrungsmethoden-Anzeige
  - Stammdaten-Scoping (tenant_has_access, Tenant-eigene Species)
  - Tenant-Overlay (has_overlay Indikator, custom_phase_durations)
  - Tenant hidden-Flag
  - Stammdaten-Promotion (Tenant→Global durch KA-Admin)
  - Mobile Card-Ansicht
  - Auth & Redirect unauthenticated
generated: "2026-03-21"
version: "4.0"
---

# Testfälle REQ-001: Stammdatenverwaltung

> Alle Testfälle beschreiben Interaktionen aus der **Nutzerperspektive im Browser**.
> Kein Testfall referenziert API-Aufrufe, HTTP-Status-Codes oder Datenbankzustände direkt.
> Backend-Regeln manifestieren sich als sichtbare UI-Zustände (Fehlermeldungen, deaktivierte Buttons, leere Zustände).

---

## Gruppe 1: Botanische Familie — Listenansicht

---

## TC-001-001: Botanische Familienliste wird vollständig geladen und angezeigt

**Requirement**: REQ-001 §2 — BotanicalFamily Seed-Daten
**Priority**: Critical
**Category**: Listenansicht
**Preconditions**:
- Nutzer ist angemeldet
- Mindestens 9 Seed-Familien sind im System vorhanden (Solanaceae, Brassicaceae, Fabaceae, Cucurbitaceae, Apiaceae, Asteraceae, Poaceae, Lamiaceae, Cannabaceae)

**Test Steps**:
1. Nutzer navigiert zu `/stammdaten/botanical-families`
2. Nutzer wartet bis die Seite vollständig geladen hat (kein Lade-Spinner mehr sichtbar)

**Expected Results**:
- Seitenüberschrift zeigt "Botanische Familien"
- Tabelle enthält mindestens 9 Zeilen
- Jede Zeile zeigt: Botanischer Name (z.B. "Solanaceae"), Allgemeinname (z.B. "Nachtschattengewächse"), Nährstoffbedarf, Frosttoleranz, Wurzeltiefe, Arten-Anzahl, Rotationskategorie
- Button "Familie erstellen" ist oben rechts sichtbar
- Spalte "Name" ist standardmäßig aufsteigend sortiert (A→Z)

**Postconditions**:
- Listenansicht bleibt stabil, kein Fehler-Banner sichtbar

**Tags**: [req-001, botanical-family, liste, stammdaten]

---

## TC-001-002: Tabelle sortieren nach Nährstoffbedarf

**Requirement**: REQ-001 §2 — BotanicalFamily Attribute
**Priority**: High
**Category**: Listenansicht
**Preconditions**:
- Nutzer ist auf `/stammdaten/botanical-families`
- Mindestens 2 Familien mit unterschiedlichem Nährstoffbedarf sind vorhanden

**Test Steps**:
1. Nutzer klickt auf Spaltenüberschrift "Nährstoffbedarf"

**Expected Results**:
- Tabelle wird neu sortiert nach Nährstoffbedarf
- Sortierindikator (Pfeil) erscheint in der Spaltenüberschrift
- Ein zweiter Klick kehrt die Sortierreihenfolge um

**Postconditions**:
- Sortierzustand wird in der URL gespeichert (useTableUrlState)

**Tags**: [req-001, botanical-family, sortierung, liste]

---

## TC-001-003: Suchfunktion in Botanische Familien-Liste

**Requirement**: REQ-001 §2 — BotanicalFamily Suche
**Priority**: High
**Category**: Listenansicht
**Preconditions**:
- Nutzer ist auf `/stammdaten/botanical-families`
- Tabelle enthält Solanaceae und Fabaceae

**Test Steps**:
1. Nutzer klickt in das Suchfeld "Tabelle durchsuchen..."
2. Nutzer gibt "Solanaceae" ein und wartet ca. 300 ms (Debounce)

**Expected Results**:
- Tabelle zeigt nur Zeilen die "Solanaceae" enthalten
- Zeilen für Fabaceae und andere Familien sind nicht mehr sichtbar
- Zähler zeigt "Zeigt 1–1 von X Einträgen" oder ähnlich

**Test Steps (Fortsetzung)**:
3. Nutzer löscht den Suchtext

**Expected Results**:
- Tabelle zeigt wieder alle Familien

**Postconditions**:
- Keine Daueränderung am Datenbestand

**Tags**: [req-001, botanical-family, suche, liste]

---

## TC-001-004: Leerer Zustand — Suche liefert kein Ergebnis

**Requirement**: REQ-001 §2 — BotanicalFamily Leerzustand
**Priority**: Medium
**Category**: Listenansicht
**Preconditions**:
- Nutzer ist auf `/stammdaten/botanical-families`

**Test Steps**:
1. Nutzer gibt in das Suchfeld einen Begriff ein, der keiner Familie entspricht, z.B. "xyzNotExisting"

**Expected Results**:
- Tabelle zeigt die Meldung "Keine Ergebnisse für Ihre Suche gefunden" (data-testid="no-search-results")
- Kein Fehler-Banner erscheint

**Postconditions**:
- Keine Daueränderung

**Tags**: [req-001, botanical-family, leerzustand, liste]

---

## TC-001-005: Navigation von Liste zu Detailansicht einer Botanischen Familie

**Requirement**: REQ-001 §2 — BotanicalFamily Navigation
**Priority**: Critical
**Category**: Navigation
**Preconditions**:
- Nutzer ist auf `/stammdaten/botanical-families`
- Familie "Solanaceae" ist in der Liste sichtbar

**Test Steps**:
1. Nutzer klickt auf die Zeile "Solanaceae" in der Tabelle

**Expected Results**:
- Browser navigiert zu `/stammdaten/botanical-families/{key}`
- Seitenüberschrift zeigt "Solanaceae"
- Bearbeitungsformular ist sichtbar mit vorausgefüllten Daten der Familie
- Abschnitt "Taxonomie" mit den Feldern Name, Deutscher Name, Englischer Name, Ordnung, Beschreibung ist sichtbar

**Postconditions**:
- Keine Daueränderung

**Tags**: [req-001, botanical-family, navigation, detailansicht]

---

## Gruppe 2: Botanische Familie — Erstellen-Dialog

---

## TC-001-006: Neue Botanische Familie erfolgreich erstellen (Happy Path)

**Requirement**: REQ-001 §2 — BotanicalFamily CRUD, §6 — DoD CRUD
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- Nutzer ist auf `/stammdaten/botanical-families`

**Test Steps**:
1. Nutzer klickt auf "Familie erstellen"
2. Erstellen-Dialog öffnet sich
3. Nutzer gibt im Feld "Name" den Wert "Testaceae" ein
4. Nutzer gibt im Feld "Deutscher Name" den Wert "Testgewächse" ein
5. Nutzer gibt im Feld "Englischer Name" den Wert "Test family" ein
6. Nutzer wählt im Dropdown "Nährstoffbedarf" den Wert "Mittelzehrer"
7. Nutzer wählt im Dropdown "Wurzeltiefe" den Wert "Mittel"
8. Nutzer wählt im Dropdown "Frosttoleranz" den Wert "Mäßig"
9. Nutzer wählt im Multiselect "Wuchsformen" mindestens einen Wert aus (z.B. "Kraut")
10. Nutzer wählt im Multiselect "Bestäubungstypen" mindestens einen Wert aus (z.B. "Insekt")
11. Nutzer klickt auf "Erstellen"

**Expected Results**:
- Dialog schließt sich
- Erfolgs-Snackbar erscheint
- "Testaceae" ist in der Familien-Liste sichtbar

**Postconditions**:
- "Testaceae" ist dauerhaft im System angelegt

**Tags**: [req-001, botanical-family, erstellen, happy-path, dialog]

---

## TC-001-007: Validierung — Familienname muss auf "-aceae" enden

**Requirement**: REQ-001 §3 — BotanicalFamilyDefinition.validate_family_name, §6 — DoD Validierung
**Priority**: Critical
**Category**: Formvalidierung
**Preconditions**:
- Erstellen-Dialog für Botanische Familie ist geöffnet

**Test Steps**:
1. Nutzer gibt im Feld "Name" den Wert "Solanales" ein (endet nicht auf "-aceae")
2. Nutzer füllt alle weiteren Pflichtfelder korrekt aus
3. Nutzer klickt auf "Erstellen"

**Expected Results**:
- Fehlermeldung erscheint unter dem Feld "Name": "Muss auf '-aceae' enden"
- Dialog bleibt geöffnet, Eintrag wird NICHT erstellt

**Postconditions**:
- Keine Daueränderung

**Tags**: [req-001, botanical-family, formvalidierung, aceae-endung]

---

## TC-001-008: Validierung — Ordnungsname muss auf "-ales" enden (wenn angegeben)

**Requirement**: REQ-001 §3 — BotanicalFamilyDefinition.validate_order_name, §6 — DoD Validierung
**Priority**: High
**Category**: Formvalidierung
**Preconditions**:
- Erstellen-Dialog für Botanische Familie ist geöffnet

**Test Steps**:
1. Nutzer füllt alle Pflichtfelder korrekt aus (Name z.B. "Testaceae")
2. Nutzer gibt im Feld "Ordnung" den Wert "Solanaceae" ein (endet nicht auf "-ales")
3. Nutzer klickt auf "Erstellen"

**Expected Results**:
- Fehlerbenachrichtigung oder Feldvalidierung erscheint
- Meldung besagt sinngemäß, dass der Ordnungsname auf "-ales" enden muss
- Dialog bleibt geöffnet, Eintrag wird NICHT erstellt

**Test Steps (Korrektheit)**:
4. Nutzer ändert den Ordnungsnamen auf "Solanales" und klickt erneut auf "Erstellen"

**Expected Results**:
- Dialog schließt sich, Eintrag wird erfolgreich erstellt

**Postconditions**:
- Keine Daueränderung im Negativfall; Eintrag ist im Positivfall vorhanden

**Tags**: [req-001, botanical-family, formvalidierung, ales-endung, ordnung]

---

## TC-001-009: Validierung — Pflichtfelder Wuchsformen und Bestäubungstypen min(1)

**Requirement**: REQ-001 §3 — BotanicalFamilyDefinition.typical_growth_forms.min(1), pollination_type.min(1)
**Priority**: High
**Category**: Formvalidierung
**Preconditions**:
- Erstellen-Dialog für Botanische Familie ist geöffnet

**Test Steps**:
1. Nutzer füllt alle Felder aus, lässt aber "Wuchsformen" leer (alle Einträge entfernt)
2. Nutzer lässt "Bestäubungstypen" ebenfalls leer
3. Nutzer klickt auf "Erstellen"

**Expected Results**:
- Fehlermeldung erscheint für "Wuchsformen": mindestens ein Wert erforderlich
- Fehlermeldung erscheint für "Bestäubungstypen": mindestens ein Wert erforderlich
- Dialog bleibt geöffnet

**Postconditions**:
- Keine Daueränderung

**Tags**: [req-001, botanical-family, formvalidierung, min-auswahl, pflichtfeld]

---

## TC-001-010: Botanische Familie bearbeiten und speichern

**Requirement**: REQ-001 §2 — BotanicalFamily Edit
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- Nutzer ist auf der Detailseite einer bestehenden Botanischen Familie (z.B. "Solanaceae")

**Test Steps**:
1. Nutzer ändert das Feld "Beschreibung" auf "Aktualisierte Beschreibung"
2. Nutzer klickt auf "Speichern"

**Expected Results**:
- Erfolgs-Snackbar erscheint
- Beschreibungsfeld zeigt "Aktualisierte Beschreibung" nach dem Speichern
- Kein Fehlerbanner ist sichtbar

**Postconditions**:
- Änderung ist dauerhaft gespeichert

**Tags**: [req-001, botanical-family, bearbeiten, speichern, happy-path]

---

## TC-001-011: Botanische Familie löschen mit Bestätigungsdialog

**Requirement**: REQ-001 §2 — BotanicalFamily Delete
**Priority**: High
**Category**: Dialog
**Preconditions**:
- Nutzer ist auf der Detailseite einer Botanischen Familie ohne zugeordnete Arten
  (z.B. einer Testfamilie aus TC-001-006)

**Test Steps**:
1. Nutzer klickt auf den roten "Löschen"-Button
2. Bestätigungsdialog erscheint mit dem Namen der Familie
3. Nutzer klickt auf "Löschen" im Bestätigungsdialog

**Expected Results**:
- Dialog schließt sich
- Erfolgs-Snackbar erscheint
- Browser navigiert zurück zu `/stammdaten/botanical-families`
- Familie ist nicht mehr in der Liste sichtbar

**Postconditions**:
- Familie ist aus dem System entfernt

**Tags**: [req-001, botanical-family, löschen, confirm-dialog, destructive]

---

## TC-001-012: Löschen abbrechen — Familie bleibt erhalten

**Requirement**: REQ-001 §2 — BotanicalFamily Delete Cancel
**Priority**: Medium
**Category**: Dialog
**Preconditions**:
- Nutzer ist auf der Detailseite einer Botanischen Familie

**Test Steps**:
1. Nutzer klickt auf den "Löschen"-Button
2. Bestätigungsdialog erscheint
3. Nutzer klickt auf "Abbrechen"

**Expected Results**:
- Dialog schließt sich
- Nutzer bleibt auf der Detailseite
- Familie ist unverändert vorhanden

**Postconditions**:
- Keine Daueränderung

**Tags**: [req-001, botanical-family, löschen, abbrechen, dialog]

---

## TC-001-013: pH-Bereich-Validierung — max_ph muss >= min_ph sein

**Requirement**: REQ-001 §3 — PhRange.validate_ph_range, max_ph >= min_ph
**Priority**: High
**Category**: Formvalidierung
**Preconditions**:
- Nutzer ist auf der Detailseite einer Botanischen Familie oder im Erstellen-Dialog

**Test Steps**:
1. Nutzer gibt im Feld "pH-Minimum" den Wert "7" ein
2. Nutzer gibt im Feld "pH-Maximum" den Wert "5" ein (kleiner als Minimum)
3. Nutzer klickt auf "Speichern" oder "Erstellen"

**Expected Results**:
- Fehlerbenachrichtigung oder Feldvalidierung erscheint
- Meldung besagt sinngemäß, dass der maximale pH-Wert größer oder gleich dem minimalen sein muss
- Formular wird nicht gespeichert

**Test Steps (Grenzwert 1)**:
4. Nutzer gibt pH-Min = "3.0" und pH-Max = "3.0" ein und speichert

**Expected Results**:
- Speichern erfolgreich (gleiches Min/Max ist erlaubt)

**Test Steps (Grenzwert 2)**:
5. Nutzer gibt pH-Min = "2.9" ein und speichert

**Expected Results**:
- Fehler: Wert unter 3.0 ist nicht erlaubt

**Postconditions**:
- Keine Daueränderung in den Negativfällen

**Tags**: [req-001, botanical-family, formvalidierung, ph-bereich, grenzwert]

---

## TC-001-014: UnsavedChangesGuard — Botanische Familie mit ungespeicherten Änderungen verlassen

**Requirement**: REQ-001 §2 — BotanicalFamilyDetailPage, UnsavedChangesGuard
**Priority**: High
**Category**: Navigation
**Preconditions**:
- Nutzer ist auf der Detailseite einer Botanischen Familie
- Nutzer hat ein Feld geändert (Formular ist "dirty")

**Test Steps**:
1. Nutzer ändert den Wert im Feld "Beschreibung"
2. Nutzer klickt auf einen Navigationslink (z.B. "Botanische Familien" in der Breadcrumb)

**Expected Results**:
- Browser-nativer Bestätigungsdialog erscheint: "Sie haben ungespeicherte Änderungen. Möchten Sie die Seite wirklich verlassen?"
- Bei Bestätigung: Navigation erfolgt, Änderungen werden verworfen
- Bei Ablehnen: Nutzer bleibt auf der Detailseite

**Postconditions**:
- Bei Ablehnen: Änderungen bleiben im Formular erhalten

**Tags**: [req-001, botanical-family, unsaved-changes, guard, navigation]

---

## Gruppe 3: Botanische Familie — Detailansicht (Spezialfelder)

---

## TC-001-015: Botanische Familie Detailseite zeigt zugeordnete Arten

**Requirement**: REQ-001 §2 — BotanicalFamily.species_count, belongs_to_family Edge
**Priority**: High
**Category**: Detailansicht
**Preconditions**:
- Nutzer ist auf der Detailseite von "Solanaceae"
- Mindestens eine Species ist der Familie Solanaceae zugeordnet (z.B. Solanum lycopersicum)

**Test Steps**:
1. Nutzer scrollt zum Abschnitt "Arten in dieser Familie"

**Expected Results**:
- Liste zeigt alle Arten der Familie Solanaceae
- Jeder Eintrag ist ein klickbarer Link, der zur Species-Detailseite führt
- Falls keine Arten vorhanden: Meldung "Dieser Familie sind noch keine Arten zugeordnet." ist sichtbar

**Postconditions**:
- Keine Daueränderung

**Tags**: [req-001, botanical-family, detailansicht, arten-liste, navigation]

---

## TC-001-016: Alle Arten einer Familie aufrufen — Filterverlinkung

**Requirement**: REQ-001 §6 — DoD Listenansicht-Filter, UI-NFR-010 §7.2
**Priority**: High
**Category**: Navigation
**Preconditions**:
- Nutzer ist auf der Detailseite von "Solanaceae"

**Test Steps**:
1. Nutzer klickt auf den Button "Alle Arten dieser Familie anzeigen"

**Expected Results**:
- Browser navigiert zu `/stammdaten/species?family={key}`
- Species-Liste zeigt nur Arten der Familie Solanaceae
- Filterbadge/Chip mit dem Familiennamen ist im Kopfbereich sichtbar

**Postconditions**:
- Keine Daueränderung

**Tags**: [req-001, botanical-family, navigation, filter, species-liste, url-parameter]

---

## TC-001-017: Nitrogen-Fixing + Heavy Demand Kombination wird abgelehnt

**Requirement**: REQ-001 §3 — BotanicalFamilyDefinition.validate_nitrogen_fixing_demand, §6 — DoD Validierung
**Priority**: High
**Category**: Formvalidierung
**Preconditions**:
- Nutzer ist auf der Detailseite einer Botanischen Familie oder im Erstellen-Dialog

**Test Steps**:
1. Nutzer aktiviert den Schalter "Stickstofffixierung" (nitrogen_fixing = true)
2. Nutzer wählt im Dropdown "Nährstoffbedarf" den Wert "Hoch" (heavy)
3. Nutzer klickt auf "Speichern" oder "Erstellen"

**Expected Results**:
- Fehlerbenachrichtigung erscheint (Server- oder Client-seitige Validierung)
- Meldung enthält sinngemäß: Stickstofffixierung ist inkompatibel mit hohem Nährstoffbedarf
- Formular wird nicht gespeichert

**Postconditions**:
- Keine Daueränderung am Datenbestand

**Tags**: [req-001, botanical-family, formvalidierung, nitrogen-fixing, heavy-demand, inkompatibilität]

---

## TC-001-018: Botanische Familien — Sorten-Anzahl wird in der Liste angezeigt

**Requirement**: REQ-001 §2 — BotanicalFamily.species_count (Spalte "Arten")
**Priority**: Medium
**Category**: Listenansicht
**Preconditions**:
- Nutzer ist auf `/stammdaten/botanical-families`
- Mindestens eine Familie hat zugeordnete Arten

**Test Steps**:
1. Nutzer betrachtet die Spalte "Arten" in der Tabelle
2. Nutzer klickt auf die Spaltenüberschrift "Arten" zum Sortieren

**Expected Results**:
- Spalte zeigt die Anzahl der zugeordneten Arten (numerisch)
- Sortierung nach Anzahl ist möglich (aufsteigend / absteigend)
- Familien mit 0 Arten zeigen "0"

**Postconditions**:
- Keine Daueränderung

**Tags**: [req-001, botanical-family, species-count, liste, sortierung]

---

## Gruppe 4: Pflanzenarten (Species) — Listenansicht

---

## TC-001-019: Species-Liste laden und Grundspalten prüfen

**Requirement**: REQ-001 §2 — Species Attribute, §6 — DoD Listenansicht
**Priority**: Critical
**Category**: Listenansicht
**Preconditions**:
- Nutzer ist angemeldet
- Mindestens eine Species ist im System vorhanden

**Test Steps**:
1. Nutzer navigiert zu `/stammdaten/species`
2. Nutzer wartet bis die Tabelle geladen hat

**Expected Results**:
- Seitenüberschrift "Arten" ist sichtbar
- Tabelle zeigt Spalten: Favorit-Stern, Wissenschaftlicher Name, Allgemeinnamen, Familie (Link), Gattung, Wuchsform, Aktive Pflanzen
- Button "Art erstellen" ist sichtbar
- Filtertaste (FilterList-Icon) ist sichtbar

**Postconditions**:
- Keine Daueränderung

**Tags**: [req-001, species, liste, stammdaten]

---

## TC-001-020: Species nach Familie filtern über URL-Parameter

**Requirement**: REQ-001 §6 — DoD Listenansicht-Filter `?family_key=...`
**Priority**: High
**Category**: Listenansicht
**Preconditions**:
- Nutzer navigiert direkt zu `/stammdaten/species?family={solanaceae-key}`

**Test Steps**:
1. Nutzer öffnet die URL mit dem `family`-Parameter

**Expected Results**:
- Species-Liste zeigt nur Arten der Familie Solanaceae
- Filterbadge/Chip mit dem Familiennamen ist im Header sichtbar
- Chip hat ein "X"-Symbol zum Entfernen des Filters

**Test Steps (Fortsetzung)**:
2. Nutzer klickt auf das "X" am Filterbadge

**Expected Results**:
- Family-Filter wird entfernt
- URL enthält keinen `family`-Parameter mehr
- Tabelle zeigt alle Species

**Postconditions**:
- Keine Daueränderung

**Tags**: [req-001, species, liste, familien-filter, url-parameter]

---

## TC-001-021: Filterbereich öffnen und Toggle-Filter aktivieren

**Requirement**: REQ-001 §6 — DoD Tablet-Spaltenprioritäten, UI-Filter-Panel
**Priority**: High
**Category**: Listenansicht
**Preconditions**:
- Nutzer ist auf `/stammdaten/species`

**Test Steps**:
1. Nutzer klickt auf den Button "Filter" (FilterList-Icon)
2. Das Filterbereich-Panel klappt auf
3. Nutzer klickt auf den Chip "Innen geeignet"

**Expected Results**:
- Filterbereich ist sichtbar mit Toggle-Chips
- Chip "Innen geeignet" ist jetzt hervorgehoben (aktiv)
- Tabelle zeigt nur Species bei denen `indoor_suitable = yes` oder `indoor_suitable = limited`

**Test Steps (Fortsetzung)**:
4. Nutzer klickt erneut auf den Chip "Innen geeignet"

**Expected Results**:
- Filter wird deaktiviert
- Tabelle zeigt wieder alle Species

**Postconditions**:
- Keine Daueränderung

**Tags**: [req-001, species, liste, filter-panel, toggle-filter]

---

## TC-001-022: Jetzt säen-Filter zeigt nur aktuell säbare Arten

**Requirement**: REQ-001 §2 — Species.direct_sow_months, SpeciesListPage.matchesToggleFilter 'sowNow'
**Priority**: High
**Category**: Listenansicht
**Preconditions**:
- Nutzer ist auf `/stammdaten/species`
- Mindestens eine Species hat den aktuellen Monat in `direct_sow_months`
- Mindestens eine Species hat den aktuellen Monat NICHT in `direct_sow_months`

**Test Steps**:
1. Nutzer öffnet den Filterbereich
2. Nutzer aktiviert den Chip "Jetzt säen"

**Expected Results**:
- Tabelle zeigt nur Arten, deren `direct_sow_months` den aktuellen Kalendermonat enthält
- Arten ohne passenden Sämonat sind ausgeblendet

**Postconditions**:
- Keine Daueränderung

**Tags**: [req-001, species, liste, jetzt-saeen, saison-filter, direct-sow-months]

---

## TC-001-023: Favoriten-Filter zeigt nur markierte Arten

**Requirement**: REQ-001 §2 — Species Favoriten, useSowingFavorites
**Priority**: Medium
**Category**: Listenansicht
**Preconditions**:
- Nutzer ist auf `/stammdaten/species`
- Mindestens eine Species ist als Favorit markiert (Stern-Icon in der Liste)

**Test Steps**:
1. Nutzer öffnet den Filterbereich
2. Nutzer aktiviert den Chip "Nur Favoriten"

**Expected Results**:
- Tabelle zeigt nur Species die als Favorit markiert sind
- Nicht-Favoriten sind ausgeblendet

**Postconditions**:
- Keine Daueränderung

**Tags**: [req-001, species, liste, favoriten-filter]

---

## TC-001-024: Favorit in der Species-Liste setzen und entfernen

**Requirement**: REQ-001 §2 — Species Favoriten, SpeciesListPage Stern-Button
**Priority**: Low
**Category**: Listenansicht
**Preconditions**:
- Nutzer ist auf `/stammdaten/species`
- Mindestens eine Species ist vorhanden und noch kein Favorit

**Test Steps**:
1. Nutzer klickt auf den leeren Stern (StarBorderIcon) in der Zeile einer Species

**Expected Results**:
- Icon wechselt zu gefülltem Stern (StarIcon) mit gelber Farbe
- Species ist jetzt als Favorit markiert

**Test Steps (Fortsetzung)**:
2. Nutzer klickt erneut auf den gefüllten Stern

**Expected Results**:
- Icon wechselt zurück zu StarBorderIcon
- Species ist nicht mehr als Favorit markiert

**Postconditions**:
- Favoritenstatus ist im localStorage gespeichert

**Tags**: [req-001, species, favoriten, stern-button, liste]

---

## Gruppe 5: Pflanzenarten (Species) — Erstellen-Dialog

---

## TC-001-025: Neue Species erfolgreich erstellen (Happy Path)

**Requirement**: REQ-001 §2 — Species CRUD, §6 — DoD Taxonomische Vollständigkeit
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- Nutzer ist auf `/stammdaten/species`

**Test Steps**:
1. Nutzer klickt auf "Art erstellen"
2. Erstellen-Dialog öffnet sich
3. Nutzer gibt im Feld "Wissenschaftlicher Name" den Wert "Phaseolus vulgaris" ein
4. Nutzer gibt im Feld "Gattung" den Wert "Phaseolus" ein
5. Nutzer wählt im Dropdown "Wuchsform" den Wert "Kraut"
6. Nutzer wählt im Dropdown "Wurzeltyp" den Wert "Faserig"
7. Nutzer klickt auf "Erstellen"

**Expected Results**:
- Dialog schließt sich
- Erfolgs-Snackbar erscheint
- "Phaseolus vulgaris" ist in der Species-Liste sichtbar

**Postconditions**:
- Species "Phaseolus vulgaris" ist dauerhaft im System angelegt

**Tags**: [req-001, species, erstellen, happy-path, dialog]

---

## TC-001-026: Species erstellen — Wissenschaftlicher Name leer wird verhindert

**Requirement**: REQ-001 §3 — SpeciesDefinition.scientific_name.min(1)
**Priority**: Critical
**Category**: Formvalidierung
**Preconditions**:
- Erstellen-Dialog für Species ist geöffnet

**Test Steps**:
1. Nutzer lässt das Feld "Wissenschaftlicher Name" leer
2. Nutzer füllt alle anderen Felder korrekt aus
3. Nutzer klickt auf "Erstellen"

**Expected Results**:
- Pflichtfeld-Fehlermeldung erscheint unter "Wissenschaftlicher Name"
- Dialog bleibt geöffnet

**Postconditions**:
- Keine Daueränderung

**Tags**: [req-001, species, formvalidierung, pflichtfeld, scientific-name]

---

## TC-001-027: Species erstellen — Hybrid-Notation "Genus × species" wird akzeptiert

**Requirement**: REQ-001 §3 — SpeciesDefinition.validate_scientific_name (Hybrid-Notation)
**Priority**: High
**Category**: Formvalidierung
**Preconditions**:
- Erstellen-Dialog für Species ist geöffnet

**Test Steps**:
1. Nutzer gibt im Feld "Wissenschaftlicher Name" den Wert "Viola x wittrockiana" ein
2. Nutzer füllt alle weiteren Pflichtfelder aus
3. Nutzer klickt auf "Erstellen"

**Expected Results**:
- Kein Validierungsfehler für das Namenfeld
- Dialog schließt sich, Species wird erstellt

**Test Steps (Unicode-Hybrid)**:
4. Nutzer erstellt eine weitere Species mit dem Namen "Calibrachoa × hybrida"

**Expected Results**:
- Auch die Unicode-Hybridnotation (×) wird akzeptiert und korrekt gespeichert

**Postconditions**:
- Hybrid-Arten sind im System angelegt

**Tags**: [req-001, species, formvalidierung, hybrid-notation, wissenschaftlicher-name]

---

## TC-001-028: Species erstellen — Allelopathie-Wert Grenzwerte

**Requirement**: REQ-001 §3 — SpeciesDefinition.allelopathy_score.min(-1).max(1)
**Priority**: High
**Category**: Formvalidierung
**Preconditions**:
- Erstellen-Dialog für Species ist geöffnet

**Test Steps**:
1. Nutzer gibt im Feld "Allelopathie-Wert" den Wert "-1.1" ein (unter Minimum)
2. Nutzer klickt auf "Erstellen"

**Expected Results**:
- Fehlermeldung erscheint: Wert muss zwischen -1 und 1 liegen
- Dialog bleibt geöffnet

**Test Steps (Fortsetzung)**:
3. Nutzer gibt den Wert "1.1" ein (über Maximum)

**Expected Results**:
- Gleiche Fehlermeldung

**Test Steps (Grenzwerte gültig)**:
4. Nutzer gibt den Wert "-1.0" ein, füllt Pflichtfelder aus und klickt "Erstellen"

**Expected Results**:
- Erfolgreich erstellt (Grenzwert -1.0 ist gültig)

**Postconditions**:
- Keine Daueränderung bei Grenzwert-Verletzungen; Eintrag bei gültigem Wert

**Tags**: [req-001, species, formvalidierung, allelopathie, grenzwert]

---

## TC-001-029: Species erstellen mit Expertise-Level-Filter (REQ-021 Integration)

**Requirement**: REQ-001 §2 — SpeciesCreateDialog ExpertiseFieldWrapper, REQ-021
**Priority**: Medium
**Category**: Dialog
**Preconditions**:
- Nutzer hat Erfahrungsstufe "Einsteiger" eingestellt
- Erstellen-Dialog für Species ist geöffnet

**Test Steps**:
1. Nutzer betrachtet das Formular

**Expected Results**:
- Erweiterte Felder (z.B. "Synonyme", "Taxonomische Autorität", "USDA-Winterhärtezonen") sind ausgeblendet
- "Alle Felder anzeigen"-Toggle ist sichtbar

**Test Steps (Fortsetzung)**:
2. Nutzer klickt auf "Alle Felder anzeigen"

**Expected Results**:
- Alle Felder (incl. Experten-Felder) sind sichtbar

**Postconditions**:
- Keine Daueränderung

**Tags**: [req-001, species, expertise-level, einsteiger, felder-sichtbarkeit, req-021]

---

## Gruppe 6: Pflanzenarten (Species) — Detailansicht

---

## TC-001-030: Species-Detailseite öffnen und Tab "Bearbeiten" anzeigen

**Requirement**: REQ-001 §2 — SpeciesDetailPage, Tab "Bearbeiten"
**Priority**: Critical
**Category**: Detailansicht
**Preconditions**:
- Nutzer ist auf `/stammdaten/species`
- Species "Solanum lycopersicum" ist vorhanden

**Test Steps**:
1. Nutzer klickt in der Liste auf die Zeile "Solanum lycopersicum"

**Expected Results**:
- Browser navigiert zu `/stammdaten/species/{key}`
- Seitenüberschrift zeigt den wissenschaftlichen Namen
- Tab "Bearbeiten" ist aktiv und Bearbeitungsformular ist sichtbar
- Weitere Tabs sind sichtbar: "Anbauperioden", "Sorten", "Lebenszyklus-Konfiguration", "Workflows"
- Felder sind mit den aktuellen Werten vorbelegt

**Postconditions**:
- Keine Daueränderung

**Tags**: [req-001, species, detailansicht, tabs, navigation]

---

## TC-001-031: Species bearbeiten und speichern — Beschreibung ändern

**Requirement**: REQ-001 §2 — Species Edit
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- Nutzer ist auf der Detailseite einer Species, Tab "Bearbeiten"

**Test Steps**:
1. Nutzer ändert das Feld "Beschreibung" auf "Aktualisierte botanische Beschreibung"
2. Nutzer klickt auf "Speichern"

**Expected Results**:
- Erfolgs-Snackbar erscheint
- Feld "Beschreibung" zeigt nach dem Speichern die neue Beschreibung
- Kein Fehlerbanner sichtbar

**Postconditions**:
- Änderung ist dauerhaft gespeichert

**Tags**: [req-001, species, bearbeiten, speichern, happy-path]

---

## TC-001-032: Species — Pflanzeninstanz direkt aus Detailseite erstellen

**Requirement**: REQ-001 §2 — Species Aktionen, SpeciesDetailPage Erstellen-Button
**Priority**: Medium
**Category**: Dialog
**Preconditions**:
- Nutzer ist auf der Detailseite einer Species

**Test Steps**:
1. Nutzer klickt auf den Button "Pflanzeninstanz erstellen" (Add-Icon oben)
2. Dialog "Pflanzeninstanz anlegen" öffnet sich

**Expected Results**:
- Dialog öffnet sich
- Feld "Art" ist bereits mit der aktuellen Species vorbelegt

**Test Steps (Fortsetzung)**:
3. Nutzer füllt Pflichtfelder aus und klickt "Erstellen"

**Expected Results**:
- Dialog schließt sich
- Erfolgs-Snackbar erscheint

**Postconditions**:
- Neue Pflanzeninstanz ist mit dieser Species verknüpft

**Tags**: [req-001, species, pflanzeninstanz, erstellen, dialog]

---

## TC-001-033: Species löschen mit Bestätigungsdialog

**Requirement**: REQ-001 §2 — Species Löschen
**Priority**: Critical
**Category**: Dialog
**Preconditions**:
- Nutzer ist auf der Detailseite einer Species ohne zugeordnete aktive Pflanzeninstanzen
  (z.B. "Phaseolus vulgaris" aus TC-001-025)

**Test Steps**:
1. Nutzer klickt auf den roten Button "Löschen"
2. Bestätigungsdialog erscheint mit dem Namen der Species
3. Nutzer klickt auf "Löschen"

**Expected Results**:
- Dialog schließt sich
- Erfolgs-Snackbar erscheint
- Browser navigiert zurück zu `/stammdaten/species`
- Species ist nicht mehr in der Liste sichtbar

**Postconditions**:
- Species ist aus dem System entfernt

**Tags**: [req-001, species, löschen, confirm-dialog, destructive]

---

## TC-001-034: Species — Favorit auf Detailseite setzen

**Requirement**: REQ-001 §2 — Species Favoriten, SpeciesDetailPage useSowingFavorites
**Priority**: Low
**Category**: Detailansicht
**Preconditions**:
- Nutzer ist auf der Detailseite einer Species die noch kein Favorit ist

**Test Steps**:
1. Nutzer klickt auf den Stern-Button (StarBorderIcon) oben rechts

**Expected Results**:
- Icon wechselt zu gefülltem Stern (StarIcon) mit gelber/warning-Farbe
- Tooltip zeigt Favorit-Info-Text

**Test Steps (Fortsetzung)**:
2. Nutzer klickt erneut auf den Stern

**Expected Results**:
- Icon wechselt zurück zu StarBorderIcon

**Postconditions**:
- Favoritenstatus in localStorage gespeichert

**Tags**: [req-001, species, favoriten, detail]

---

## TC-001-035: Species-Detailseite — Tab "Familie anzeigen" navigiert zur Familiendetailseite

**Requirement**: REQ-001 §2 — belongs_to_family Edge, SpeciesDetailPage Link "Familie anzeigen →"
**Priority**: Medium
**Category**: Navigation
**Preconditions**:
- Nutzer ist auf der Detailseite einer Species die einer Familie zugeordnet ist

**Test Steps**:
1. Nutzer sieht im Formular den Link "Familie anzeigen →" neben dem Familien-Dropdown
2. Nutzer klickt auf "Familie anzeigen →"

**Expected Results**:
- Browser navigiert zur Detailseite der zugehörigen Botanischen Familie (`/stammdaten/botanical-families/{key}`)

**Postconditions**:
- Keine Daueränderung

**Tags**: [req-001, species, navigation, familie-link, belongs-to-family]

---

## Gruppe 7: Pflanzenarten (Species) — Tab "Sorten" (Cultivar)

---

## TC-001-036: Sorten-Tab einer Species zeigt vorhandene Sorten

**Requirement**: REQ-001 §2 — Species → Cultivar has_cultivar, §6 — DoD Sortenvielfalt
**Priority**: Critical
**Category**: Listenansicht
**Preconditions**:
- Nutzer ist auf der Detailseite einer Species
- Species hat mindestens eine Sorte

**Test Steps**:
1. Nutzer klickt auf Tab "Sorten"

**Expected Results**:
- Tab-Inhalt (CultivarListSection) zeigt eine Liste der Sorten
- Jede Zeile zeigt: Sortenname, Züchter, Zuchtjahr, Tage bis Reife
- Button "Sorte erstellen" ist sichtbar

**Postconditions**:
- Keine Daueränderung

**Tags**: [req-001, species, sorten-tab, cultivar, liste]

---

## TC-001-037: Neue Sorte erstellen (Happy Path)

**Requirement**: REQ-001 §2 — Cultivar CRUD
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- Nutzer ist auf dem Tab "Sorten" einer Species-Detailseite

**Test Steps**:
1. Nutzer klickt auf "Sorte erstellen"
2. Dialog öffnet sich
3. Nutzer gibt im Feld "Name" den Wert "San Marzano" ein
4. Nutzer gibt im Feld "Züchter" den Wert "Heirloom" ein
5. Nutzer klickt auf "Erstellen"

**Expected Results**:
- Dialog schließt sich
- Erfolgs-Snackbar erscheint
- "San Marzano" erscheint in der Sortenliste des Tabs

**Postconditions**:
- Sorte "San Marzano" ist mit der Species verknüpft gespeichert

**Tags**: [req-001, cultivar, erstellen, happy-path, dialog]

---

## TC-001-038: Cultivar erstellen — Pflichtfeld "Name" leer wird verhindert

**Requirement**: REQ-001 §3 — CultivarDefinition.name.min(1)
**Priority**: Critical
**Category**: Formvalidierung
**Preconditions**:
- Erstellen-Dialog für Cultivar ist geöffnet

**Test Steps**:
1. Nutzer lässt das Feld "Name" leer
2. Nutzer klickt auf "Erstellen"

**Expected Results**:
- Pflichtfeld-Fehlermeldung erscheint unter "Name"
- Dialog bleibt geöffnet

**Postconditions**:
- Keine Daueränderung

**Tags**: [req-001, cultivar, formvalidierung, pflichtfeld, name]

---

## TC-001-039: Cultivar — Tage bis Reife Grenzwerte (1–365)

**Requirement**: REQ-001 §3 — CultivarDefinition.days_to_maturity.min(1).max(365)
**Priority**: High
**Category**: Formvalidierung
**Preconditions**:
- Erstellen-Dialog für Cultivar ist geöffnet

**Test Steps**:
1. Nutzer gibt im Feld "Tage bis Reife" den Wert "0" ein
2. Nutzer klickt auf "Erstellen"

**Expected Results**:
- Fehlermeldung erscheint: Mindestwert 1

**Test Steps (Fortsetzung)**:
3. Nutzer gibt den Wert "366" ein

**Expected Results**:
- Fehlermeldung erscheint: Maximalwert 365

**Test Steps (Grenzwert gültig)**:
4. Nutzer gibt den Wert "365" ein und klickt "Erstellen"

**Expected Results**:
- Sorte wird erfolgreich erstellt

**Postconditions**:
- Keine Daueränderung bei Grenzwert-Verletzungen

**Tags**: [req-001, cultivar, formvalidierung, days-to-maturity, grenzwert]

---

## Gruppe 8: Cultivar — Autoflower-Validierung

---

## TC-001-040: Autoflower-Cultivar erstellen — vollständige Felder (Happy Path, Szenario 4a)

**Requirement**: REQ-001 §6 — Testszenario 4a, CultivarDefinition.validate_autoflower_fields, §6 — DoD Autoflower-Validierung
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- Nutzer ist auf dem Sorten-Tab einer Cannabis-Species-Detailseite
- Erstellen-Dialog für Cultivar ist geöffnet
- Nutzer hat Expertise-Level "Experte" oder "Alle Felder anzeigen" ist aktiv, damit autoflower-Felder sichtbar sind

**Test Steps**:
1. Nutzer gibt im Feld "Name" den Wert "Northern Lights Auto" ein
2. Nutzer wählt im Dropdown "Lichtreaktion (Cultivar)" den Wert "Autoflower"
3. Nutzer gibt im Feld "Tage bis Blüte-Eintritt" den Wert "25" ein
4. Nutzer gibt im Feld "Gesamtzyklus-Tage" den Wert "75" ein
5. Nutzer gibt als Trait "autoflower" und "compact" ein
6. Nutzer klickt auf "Erstellen"

**Expected Results**:
- Kein Validierungsfehler
- Dialog schließt sich, Sorte wird erstellt
- Sorte erscheint in der Sorten-Liste mit Autoflower-Markierung

**Postconditions**:
- Autoflower-Cultivar ist gespeichert; REQ-003 kann autoflower_days_to_flower für automatischen Phasenübergang verwenden

**Tags**: [req-001, cultivar, autoflower, erstellen, happy-path, szenario-4a]

---

## TC-001-041: Autoflower-Felder ohne "Autoflower"-Typ werden abgelehnt

**Requirement**: REQ-001 §3 — CultivarDefinition.validate_autoflower_fields (autoflower_days_to_flower nur bei photoperiod_type=autoflower)
**Priority**: High
**Category**: Formvalidierung
**Preconditions**:
- Erstellen-Dialog für Cultivar ist geöffnet
- Autoflower-spezifische Felder sind sichtbar (Experten-Modus)

**Test Steps**:
1. Nutzer wählt "Photoperiodisch" als Lichtreaktion (NICHT "Autoflower")
2. Nutzer gibt im Feld "Tage bis Blüte-Eintritt" den Wert "25" ein
3. Nutzer klickt auf "Erstellen"

**Expected Results**:
- Fehlerbenachrichtigung erscheint
- Meldung besagt sinngemäß: "Tage bis Blüte-Eintritt" ist nur bei Autoflower-Typ erlaubt
- Sorte wird NICHT erstellt

**Postconditions**:
- Keine Daueränderung

**Tags**: [req-001, cultivar, formvalidierung, autoflower-felder, photoperiodisch, szenario-4b]

---

## TC-001-042: Autoflower-Validierung — days_to_flower muss kleiner als total_cycle_days sein

**Requirement**: REQ-001 §3 — CultivarDefinition.validate_autoflower_fields (days_to_flower < total_cycle_days)
**Priority**: High
**Category**: Formvalidierung
**Preconditions**:
- Erstellen-Dialog für Cultivar ist geöffnet
- Lichtreaktion "Autoflower" ist gewählt

**Test Steps**:
1. Nutzer gibt im Feld "Tage bis Blüte-Eintritt" den Wert "75" ein
2. Nutzer gibt im Feld "Gesamtzyklus-Tage" den Wert "60" ein (kleiner als days_to_flower)
3. Nutzer klickt auf "Erstellen"

**Expected Results**:
- Fehlerbenachrichtigung erscheint
- Meldung besagt sinngemäß: "Tage bis Blüte-Eintritt" muss kleiner als "Gesamtzyklus-Tage" sein
- Sorte wird NICHT erstellt

**Test Steps (Gleichwert)**:
4. Nutzer gibt beide Felder auf "75" ein und klickt "Erstellen"

**Expected Results**:
- Fehler bleibt: days_to_flower muss KLEINER als total_cycle_days sein (nicht gleich)

**Postconditions**:
- Keine Daueränderung

**Tags**: [req-001, cultivar, formvalidierung, autoflower, days-comparison, grenzwert]

---

## TC-001-043: Cultivar — ungültiger Trait-Wert wird abgelehnt

**Requirement**: REQ-001 §3 — CultivarDefinition.validate_traits
**Priority**: Medium
**Category**: Formvalidierung
**Preconditions**:
- Erstellen-Dialog für Cultivar ist geöffnet

**Test Steps**:
1. Nutzer gibt im Feld "Eigenschaften" einen ungültigen Trait-Wert ein, z.B. "super_rare_custom"
2. Nutzer drückt Enter um den Wert hinzuzufügen
3. Nutzer klickt auf "Erstellen"

**Expected Results**:
- Fehlerbenachrichtigung erscheint
- Meldung enthält sinngemäß "Ungültige Traits"
- Sorte wird NICHT erstellt

**Test Steps (gültige Traits)**:
4. Nutzer gibt "disease_resistant" ein und klickt auf "Erstellen"

**Expected Results**:
- Kein Fehler, Sorte wird erfolgreich erstellt

**Postconditions**:
- Keine Daueränderung bei ungültigen Traits

**Tags**: [req-001, cultivar, formvalidierung, traits, ungültig]

---

## TC-001-044: Cultivar-Detailseite öffnen

**Requirement**: REQ-001 §2 — CultivarDetailPage Route `/stammdaten/species/:speciesKey/cultivars/:cultivarKey`
**Priority**: High
**Category**: Detailansicht
**Preconditions**:
- Nutzer ist auf dem Sorten-Tab einer Species-Detailseite
- Mindestens eine Sorte ist vorhanden

**Test Steps**:
1. Nutzer klickt auf eine Sorte in der Sortenliste

**Expected Results**:
- Browser navigiert zu `/stammdaten/species/{speciesKey}/cultivars/{cultivarKey}`
- Seitenüberschrift zeigt den Sortennamen
- Bearbeitungsformular mit Sortendaten ist sichtbar: Name, Züchter, Zuchtjahr, Traits, Patentstatus, Tage bis Reife, Krankheitsresistenzen

**Postconditions**:
- Keine Daueränderung

**Tags**: [req-001, cultivar, detailseite, navigation, route]

---

## TC-001-045: Cultivar-Detailseite — Sortendaten bearbeiten und speichern

**Requirement**: REQ-001 §2 — Cultivar Edit
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- Nutzer ist auf der Cultivar-Detailseite

**Test Steps**:
1. Nutzer ändert das Feld "Züchter" auf "Updated Breeder GmbH"
2. Nutzer klickt auf "Speichern"

**Expected Results**:
- Erfolgs-Snackbar erscheint
- Feld "Züchter" zeigt nach dem Speichern "Updated Breeder GmbH"

**Postconditions**:
- Änderung ist dauerhaft gespeichert

**Tags**: [req-001, cultivar, bearbeiten, speichern, happy-path]

---

## TC-001-046: Cultivar — Phasen-Bewässerungsüberschreibungen (phaseWateringOverrides)

**Requirement**: REQ-001 §2 — Cultivar.phaseWateringOverrides, CultivarDetailPage Bearbeitungsformular
**Priority**: Medium
**Category**: Detailansicht
**Preconditions**:
- Nutzer ist auf der Cultivar-Detailseite
- Species hat eine LifecycleConfig mit Wachstumsphasen

**Test Steps**:
1. Nutzer scrollt zum Abschnitt "Gießintervall pro Phase"

**Expected Results**:
- Abschnitt "Gießintervall pro Phase" ist sichtbar
- Für jede Wachstumsphase gibt es ein Eingabefeld "Sortenwert (Tage)"
- Leere Felder zeigen den Hinweis an, dass der Art-Standardwert verwendet wird

**Test Steps (Wert eingeben)**:
2. Nutzer gibt für Phase "Vegetatives Wachstum" den Wert "3" in das Sortenfeld ein
3. Nutzer klickt auf "Speichern"

**Expected Results**:
- Erfolgs-Snackbar erscheint
- Phasen-spezifischer Gießintervall ist gespeichert

**Postconditions**:
- Überschreibung ist wirksam

**Tags**: [req-001, cultivar, phasen-giessen, override, bearbeiten]

---

## Gruppe 9: Species — Tab "Lebenszyklus-Konfiguration" (GrowthPhase)

---

## TC-001-047: Lebenszyklus-Tab zeigt LifecycleConfig und GrowthPhases

**Requirement**: REQ-001 §2 — LifecycleConfig + GrowthPhase, consists_of Edge, §6 — DoD Lifecycle-Konfiguration
**Priority**: High
**Category**: Detailansicht
**Preconditions**:
- Nutzer ist auf der Detailseite einer Species die eine LifecycleConfig hat

**Test Steps**:
1. Nutzer klickt auf Tab "Lebenszyklus-Konfiguration"

**Expected Results**:
- Abschnitt mit Lebenszyklus-Typ (einjährig/zweijährig/mehrjährig), Photoperiode und Vernalisation ist sichtbar
- Wachstumsphasen-Tabelle zeigt alle Phasen sortiert nach Sequenz-Reihenfolge
- Jede Phase zeigt: Name, typische Dauer in Tagen, Sequenznummer

**Postconditions**:
- Keine Daueränderung

**Tags**: [req-001, species, lebenszyklus-tab, lifecycle-config, growth-phases]

---

## TC-001-048: Neue Wachstumsphase anlegen

**Requirement**: REQ-001 §2 — GrowthPhase CRUD, consists_of sequence
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- Nutzer ist auf dem Tab "Lebenszyklus-Konfiguration" einer Species-Detailseite

**Test Steps**:
1. Nutzer klickt auf "Phase hinzufügen"
2. Dialog oder Inline-Formular öffnet sich
3. Nutzer gibt im Feld "Name" den Wert "Keimung" ein
4. Nutzer gibt im Feld "Typische Dauer (Tage)" den Wert "7" ein
5. Nutzer klickt auf "Erstellen"

**Expected Results**:
- Dialog/Formular schließt sich
- Phase "Keimung" ist in der Phasen-Tabelle sichtbar mit 7 Tagen Dauer

**Postconditions**:
- Wachstumsphase "Keimung" ist angelegt und mit der LifecycleConfig verknüpft

**Tags**: [req-001, growthphase, erstellen, lifecycle-tab]

---

## TC-001-049: Wachstumsphase — Pflichtfeld "Name" und Mindestdauer 1 Tag

**Requirement**: REQ-001 §3 — GrowthPhase.name.min(1), GrowthPhase.typical_duration_days.min(1)
**Priority**: High
**Category**: Formvalidierung
**Preconditions**:
- Dialog/Formular für neue Wachstumsphase ist geöffnet

**Test Steps**:
1. Nutzer lässt das Feld "Name" leer
2. Nutzer gibt Dauer "0" ein (unter Minimum 1)
3. Nutzer versucht zu speichern

**Expected Results**:
- Pflichtfeld-Fehlermeldung erscheint unter "Name"
- Fehlermeldung erscheint unter "Dauer" (Mindestwert 1)
- Speichern wird blockiert

**Postconditions**:
- Keine Daueränderung

**Tags**: [req-001, growthphase, formvalidierung, pflichtfeld, dauer-minimum]

---

## Gruppe 10: Fruchtfolge-Seite (CropRotationPage)

---

## TC-001-050: Fruchtfolge-Seite öffnen und CRITICAL-Warnung auslösen

**Requirement**: REQ-001 §6 — Testszenario 5, CropRotationValidator CRITICAL
**Priority**: Critical
**Category**: Zustandswechsel
**Preconditions**:
- Nutzer ist angemeldet
- Species Tomate (Solanaceae) und Kartoffel (Solanaceae) sind im System vorhanden

**Test Steps**:
1. Nutzer navigiert zu `/stammdaten/crop-rotation`
2. Nutzer wählt "Solanaceae" als Ausgangsfamilie
3. Nutzer klickt auf "Nachfolger hinzufügen"

**Expected Results**:
- Seite zeigt die Fruchtfolge-Übersicht
- Beim Hinzufügen eines Nachfolgers aus der gleichen Familie (Solanaceae) erscheint CRITICAL-Warnung
- Meldung enthält sinngemäß: "Gleiche Familie — Mindestabstand 3 Jahre"

**Postconditions**:
- Keine Daueränderung

**Tags**: [req-001, fruchtfolge, critical, rotation, familie]

---

## TC-001-051: Fruchtfolge-Warnung WARNING bei gemeinsamem Schädlingsrisiko

**Requirement**: REQ-001 §6 — Testszenario 7, shares_pest_risk-Kante
**Priority**: High
**Category**: Zustandswechsel
**Preconditions**:
- Nutzer ist auf der Fruchtfolge-Seite `/stammdaten/crop-rotation`
- Species Tomate (Solanaceae) und Gurke (Cucurbitaceae) sind vorhanden
- shares_pest_risk zwischen Solanaceae und Cucurbitaceae mit risk_level=medium ist im System

**Test Steps**:
1. Nutzer wählt "Solanaceae" als Ausgangsfamilie
2. Im Bereich Nachfolger-Empfehlungen erscheint "Cucurbitaceae"

**Expected Results**:
- Für Cucurbitaceae wird eine WARNING-Markierung angezeigt (kein CRITICAL, da verschiedene Familien)
- Meldung enthält sinngemäß: "Gemeinsames Schädlingsrisiko: Blattläuse, Weiße Fliege (medium)"

**Postconditions**:
- Keine Daueränderung

**Tags**: [req-001, fruchtfolge, warning, schaedlingsrisiko, shares-pest-risk]

---

## TC-001-052: Fruchtfolge-Empfehlung OK mit Stickstoff-Benefit

**Requirement**: REQ-001 §6 — Testszenario 6, rotation_after-Kante Fabaceae→Solanaceae
**Priority**: High
**Category**: Zustandswechsel
**Preconditions**:
- Nutzer ist auf der Fruchtfolge-Seite
- Familien Brassicaceae und Fabaceae sind im System

**Test Steps**:
1. Nutzer wählt "Brassicaceae" als Ausgangsfamilie
2. Nutzer sieht die Nachfolger-Empfehlungen

**Expected Results**:
- "Fabaceae" erscheint als empfohlener Nachfolger
- Benefit-Begründung enthält sinngemäß "nitrogen_fixation" und einen Wert >= 0.90
- Hinweis auf Stickstoffreduzierungspotenzial ist sichtbar

**Postconditions**:
- Keine Daueränderung

**Tags**: [req-001, fruchtfolge, ok, nitrogen-fixation, rotation-after]

---

## Gruppe 11: Seed-Daten & i18n-Anzeige

---

## TC-001-053: i18n — Deutsche und englische Familiennamen werden korrekt angezeigt

**Requirement**: REQ-001 §6 — DoD i18n-Anzeige, common_name_de/en
**Priority**: High
**Category**: Listenansicht
**Preconditions**:
- Systemsprache ist Deutsch (DE)
- Nutzer ist auf `/stammdaten/botanical-families`

**Test Steps**:
1. Nutzer betrachtet die Spalte "Allgemeinname" in der Familien-Tabelle

**Expected Results**:
- Deutsche Allgemeinnamen werden angezeigt: "Nachtschattengewächse" für Solanaceae, "Kreuzblütler" für Brassicaceae, "Hülsenfrüchtler" für Fabaceae

**Test Steps (Sprachenwechsel)**:
2. Nutzer wechselt die Sprache auf Englisch (EN)
3. Nutzer lädt die Familien-Liste neu

**Expected Results**:
- Englische Allgemeinnamen werden angezeigt: "Nightshade family", "Mustard family", "Legume family"

**Postconditions**:
- Spracheinstellung bleibt EN (falls nicht zurückgesetzt)

**Tags**: [req-001, botanical-family, i18n, deutsch, englisch, common-name]

---

## TC-001-054: Seed-Daten Kontrolle — mindestens 9 Pflanzenfamilien vorhanden

**Requirement**: REQ-001 §2 — Seed-Daten BotanicalFamily, §6 — DoD Erweiterte BotanicalFamily
**Priority**: High
**Category**: Listenansicht
**Preconditions**:
- System hat Seed-Daten eingespielt
- Nutzer ist auf `/stammdaten/botanical-families`

**Test Steps**:
1. Nutzer öffnet die Familienliste

**Expected Results**:
- Mindestens 9 Familien sind sichtbar: Solanaceae, Brassicaceae, Fabaceae, Cucurbitaceae, Apiaceae, Asteraceae, Poaceae, Lamiaceae, Cannabaceae
- Korrekte Nährstoffbedarfs-Werte: Fabaceae="Gering" (light), Cannabaceae="Hoch" (heavy), Solanaceae="Hoch" (heavy)
- Fabaceae hat Stickstofffixierung = aktiviert
- Jede Familie zeigt eine Frosttoleranz-Klasse

**Postconditions**:
- Keine Daueränderung

**Tags**: [req-001, botanical-family, seed-daten, vollständigkeit, liste]

---

## TC-001-055: Zierpflanzen-Seed-Daten — Violaceae Familie und Stiefmütterchen-Species vorhanden

**Requirement**: REQ-001 §2 — Seed-Daten Zierpflanzen-Species, Violaceae
**Priority**: Medium
**Category**: Listenansicht
**Preconditions**:
- System hat Zierpflanzen-Seed-Daten eingespielt

**Test Steps**:
1. Nutzer navigiert zu `/stammdaten/botanical-families`
2. Nutzer sucht nach "Violaceae"

**Expected Results**:
- Familie "Violaceae" mit common_name_de "Veilchengewächse" ist sichtbar
- Nährstoffbedarf: "Gering" (light), Frosttoleranz: "Robust" (hardy)

**Test Steps (Fortsetzung)**:
3. Nutzer navigiert zu `/stammdaten/species`
4. Nutzer sucht nach "Viola x wittrockiana"

**Expected Results**:
- Art "Viola x wittrockiana" ist vorhanden
- Gebräuchlicher Name enthält "Stiefmütterchen"
- Frost-Empfindlichkeit: "hardy"

**Postconditions**:
- Keine Daueränderung

**Tags**: [req-001, zierpflanzen, seed-daten, violaceae, stiefmütterchen]

---

## Gruppe 12: Unsaved-Changes-Guard (cross-cutting)

---

## TC-001-056: Species-Detail — Unsaved-Changes-Guard auf Tab-Wechsel

**Requirement**: REQ-001 §2 — Species Bearbeiten, UnsavedChangesGuard
**Priority**: High
**Category**: Navigation
**Preconditions**:
- Nutzer ist auf Tab "Bearbeiten" einer Species-Detailseite
- Nutzer hat ein Feld geändert (Formular ist "dirty")

**Test Steps**:
1. Nutzer ändert den Wert im Feld "Beschreibung"
2. Nutzer versucht, den Browser-Tab oder eine externe Seite zu öffnen

**Expected Results**:
- Browser-nativer Bestätigungsdialog erscheint: "Sie haben ungespeicherte Änderungen. Möchten Sie die Seite wirklich verlassen?"
- Bei Ablehnen: Nutzer bleibt auf der Seite

**Postconditions**:
- Bei Ablehnen: Änderungen bleiben im Formular erhalten

**Tags**: [req-001, species, unsaved-changes, guard, navigation]

---

## Gruppe 13: Zugangskontrolle & Stammdaten-Scoping

---

## TC-001-057: Nicht angemeldeter Nutzer wird zur Login-Seite weitergeleitet

**Requirement**: REQ-001 §4 — Authentifizierung & Autorisierung, REQ-023
**Priority**: Critical
**Category**: Navigation
**Preconditions**:
- Nutzer ist nicht angemeldet (kein aktiver JWT)

**Test Steps**:
1. Nutzer navigiert direkt zu `/stammdaten/botanical-families`

**Expected Results**:
- Browser leitet auf `/auth/login` oder `/login` weiter
- Kein Inhalt der Familienliste wird angezeigt

**Postconditions**:
- Keine Daueränderung

**Tags**: [req-001, auth, redirect, zugang, req-023]

---

## TC-001-058: Tenant sieht nur für ihn freigeschaltete Species

**Requirement**: REQ-001 §4 — Stammdaten-Scoping, tenant_has_access, §6 — Testszenario 9
**Priority**: Critical
**Category**: Zustandswechsel
**Preconditions**:
- Zwei Tenants existieren: "Gemüsegarten" und "Grow-Op"
- Tenant "Gemüsegarten" hat Zugriff auf Tomate und Basilikum (nicht Cannabis)
- Nutzer ist als Mitglied des Tenants "Gemüsegarten" angemeldet

**Test Steps**:
1. Nutzer navigiert zu `/stammdaten/species` (im Kontext des Tenants "Gemüsegarten")

**Expected Results**:
- Tabelle zeigt Tomate und Basilikum
- Cannabis ist NICHT in der Liste sichtbar

**Postconditions**:
- Keine Daueränderung

**Tags**: [req-001, stammdaten-scoping, tenant_has_access, sichtbarkeit, multi-tenancy]

---

## TC-001-059: Tenant-eigene Species ist nur im eigenen Tenant sichtbar

**Requirement**: REQ-001 §6 — Testszenario 11, DoD Stammdaten-Scoping Tenant-eigene Species
**Priority**: High
**Category**: Zustandswechsel
**Preconditions**:
- Nutzer ist Tenant-Admin von "Züchter"
- Species "Hybrid-X" wurde mit origin='tenant', tenant_key='züchter' angelegt

**Test Steps**:
1. Nutzer (Tenant "Züchter") navigiert zu `/stammdaten/species`

**Expected Results**:
- "Hybrid-X" erscheint in der Liste

**Test Steps (Fortsetzung)**:
2. Nutzer meldet sich als Mitglied eines anderen Tenants an (z.B. "Gemüsegarten")
3. Nutzer navigiert erneut zu `/stammdaten/species`

**Expected Results**:
- "Hybrid-X" ist NICHT in der Liste des anderen Tenants sichtbar

**Postconditions**:
- Keine Daueränderung

**Tags**: [req-001, stammdaten-scoping, tenant-eigene-species, origin-tenant, sichtbarkeit]

---

## TC-001-060: Tenant-Overlay — has_overlay Indikator wird auf Species-Detailseite angezeigt

**Requirement**: REQ-001 §2 — TenantSpeciesConfig Merge-Logik, §6 — DoD Stammdaten-Scoping Merge-Logik, Testszenario 10
**Priority**: High
**Category**: Detailansicht
**Preconditions**:
- Tenant "Profi-Farm" existiert und hat eine TenantSpeciesConfig für die Species "Tomate" mit `custom_phase_durations = {vegetative: 45}`
- Nutzer ist als Mitglied des Tenants "Profi-Farm" angemeldet

**Test Steps**:
1. Nutzer navigiert zur Detailseite von "Solanum lycopersicum" (Tomate)

**Expected Results**:
- Ein visueller Hinweis ist sichtbar, dass ein Tenant-Overlay aktiv ist (z.B. Badge "Tenant-Anpassung", Chip "Overlay aktiv", oder ähnliches)
- Die angezeigten Phasendauern entsprechen den Tenant-Werten (vegetative = 45 Tage) und nicht den globalen Werten (z.B. 30 Tage)
- Nicht überschriebene Felder (scientific_name, family, etc.) zeigen die globalen Werte

**Postconditions**:
- Keine Daueränderung

**Tags**: [req-001, stammdaten-scoping, tenant-overlay, has-overlay, merge-logik, szenario-10]

---

## TC-001-061: Tenant hidden-Flag — ausgeblendete Species erscheint nicht in der Liste

**Requirement**: REQ-001 §2 — TenantSpeciesConfig.hidden, §6 — DoD Stammdaten-Scoping hidden-Flag
**Priority**: High
**Category**: Zustandswechsel
**Preconditions**:
- Tenant "Garten" hat Zugriff auf Species "Cannabis sativa" (tenant_has_access-Kante vorhanden)
- TenantSpeciesConfig für "Cannabis sativa" im Tenant "Garten" ist mit `hidden = true` konfiguriert
- Nutzer ist als Mitglied des Tenants "Garten" angemeldet

**Test Steps**:
1. Nutzer navigiert zu `/stammdaten/species`

**Expected Results**:
- "Cannabis sativa" ist NICHT in der Liste sichtbar, obwohl eine tenant_has_access-Kante existiert
- Die tenant_has_access-Kante wurde NICHT entfernt — die Species ist nur ausgeblendet

**Postconditions**:
- Keine Daueränderung

**Tags**: [req-001, stammdaten-scoping, hidden-flag, tenant-species-config, sichtbarkeit]

---

## TC-001-062: Stammdaten-Promotion — KA-Admin kann Tenant-Species zu globalen Daten promoten

**Requirement**: REQ-001 §6 — Testszenario 12, DoD Stammdaten-Scoping Promotion
**Priority**: High
**Category**: Zustandswechsel
**Preconditions**:
- Tenant-eigene Species "Super-Tomate" (origin: 'tenant', tenant_key: 'züchter') existiert
- Nutzer ist als KA-Admin (Platform-Admin) angemeldet

**Test Steps**:
1. KA-Admin navigiert zur Detailseite von "Super-Tomate"
2. KA-Admin findet und klickt auf eine Option "Zu globalen Stammdaten promoten" (Button oder Menüpunkt)
3. Bestätigungsdialog erscheint
4. KA-Admin bestätigt die Promotion

**Expected Results**:
- Erfolgs-Snackbar erscheint
- Species-Detailseite zeigt keine Tenant-Zugehörigkeit mehr
- "Super-Tomate" ist jetzt global sichtbar (origin: system, tenant_key: null)
- Bestehende Pflanzeninstanzen und Verknüpfungen bleiben intakt (kein Datenverlust)

**Postconditions**:
- "Super-Tomate" ist globale Species und kann per tenant_has_access jedem Tenant zugewiesen werden

**Tags**: [req-001, stammdaten-scoping, promotion, ka-admin, global, szenario-12]

---

## TC-001-063: Platform-Admin kann BotanicalFamily global bearbeiten

**Requirement**: REQ-001 §4 — Auth-Matrix, Platform-Admin hat Schreibzugriff auf globale Stammdaten
**Priority**: High
**Category**: Zustandswechsel
**Preconditions**:
- Nutzer ist als Platform-Admin angemeldet (Membership im Platform-Tenant)
- Familie "Solanaceae" ist vorhanden

**Test Steps**:
1. Platform-Admin navigiert zur Detailseite von "Solanaceae"
2. Platform-Admin ändert das Feld "Beschreibung"
3. Platform-Admin klickt auf "Speichern"

**Expected Results**:
- Erfolgs-Snackbar erscheint
- Änderung ist gespeichert

**Test Steps (Tenant-Mitglied ohne Admin-Rechte)**:
4. Nutzer meldet sich als normales Tenant-Mitglied (kein Platform-Admin) an
5. Nutzer navigiert zur Detailseite von "Solanaceae"

**Expected Results**:
- Speichern-Button ist deaktiviert oder Fehlermeldung erscheint beim Versuch zu speichern
- Kein Schreibzugriff auf globale Stammdaten für normale Tenant-Mitglieder

**Postconditions**:
- Nur die Änderungen des Platform-Admins sind gespeichert

**Tags**: [req-001, auth, platform-admin, schreibzugriff, global-stammdaten]

---

## Gruppe 14: Import-Seite (REQ-012 Verknüpfung)

---

## TC-001-064: Import-Seite für Stammdaten öffnen

**Requirement**: REQ-001 §5 — Abhängigkeiten, Bulk-Import (REQ-012)
**Priority**: Medium
**Category**: Navigation
**Preconditions**:
- Nutzer ist angemeldet

**Test Steps**:
1. Nutzer navigiert zu `/stammdaten/import`

**Expected Results**:
- Import-Seite öffnet sich ohne Fehler
- Upload-Bereich oder Datei-Auswahl ist sichtbar

**Postconditions**:
- Keine Daueränderung

**Tags**: [req-001, import, navigation, req-012]

---

## Gruppe 15: Anbauperioden-Tab (GrowingPeriodsSection)

---

## TC-001-065: Anbauperioden-Tab zeigt Saisonaldaten einer Species

**Requirement**: REQ-001 §2 — Species.direct_sow_months, harvest_months, bloom_months
**Priority**: Medium
**Category**: Detailansicht
**Preconditions**:
- Nutzer ist auf der Detailseite einer Species
- Species hat Anbauperioden-Daten (z.B. direct_sow_months, harvest_months)

**Test Steps**:
1. Nutzer klickt auf Tab "Anbauperioden"

**Expected Results**:
- Tab-Inhalt zeigt GrowingPeriodsSection
- Kalenderdarstellung oder Monatsangaben für Direktsaat, Ernte, Blüte sind sichtbar
- Keine Fehlermeldung ist zu sehen

**Postconditions**:
- Keine Daueränderung

**Tags**: [req-001, species, anbauperioden, tab, saison]

---

## Gruppe 16: Mobile Ansicht (Card-Renderer)

---

## TC-001-066: Botanische Familien-Liste auf Mobilgerät zeigt Card-Ansicht

**Requirement**: REQ-001 §2 — BotanicalFamilyListPage mobileCardRenderer
**Priority**: Medium
**Category**: Listenansicht
**Preconditions**:
- Browser auf Mobilgerät-Breite (< 600px) eingestellt

**Test Steps**:
1. Nutzer navigiert zu `/stammdaten/botanical-families`

**Expected Results**:
- Tabelle wird nicht als Desktop-Tabelle angezeigt
- Stattdessen werden Cards (MobileCard-Komponente) für jede Familie angezeigt
- Jede Card zeigt: Familienname, deutscher Allgemeinname, Chips für Nährstoffbedarf und Frosttoleranz

**Postconditions**:
- Keine Daueränderung

**Tags**: [req-001, botanical-family, mobile, card, responsive]

---

## TC-001-067: Species-Liste auf Mobilgerät zeigt Card-Ansicht

**Requirement**: REQ-001 §2 — SpeciesListPage mobileCardRenderer, §6 — DoD Tablet-Spaltenprioritäten
**Priority**: Medium
**Category**: Listenansicht
**Preconditions**:
- Browser auf Mobilgerät-Breite eingestellt

**Test Steps**:
1. Nutzer navigiert zu `/stammdaten/species`

**Expected Results**:
- Species werden als Cards angezeigt
- Jede Card zeigt: Wissenschaftlicher Name, Allgemeinname, Wuchsform-Chip, Wurzeltyp-Chip

**Postconditions**:
- Keine Daueränderung

**Tags**: [req-001, species, mobile, card, responsive]

---

## Gruppe 17: Edge Cases & Fehlerzustände

---

## TC-001-068: Ungültige URL — Botanische Familie nicht gefunden zeigt Fehlermeldung

**Requirement**: REQ-001 §2 — BotanicalFamily Navigation, ErrorDisplay-Komponente
**Priority**: Medium
**Category**: Fehlermeldung
**Preconditions**:
- Nutzer kennt eine nicht existente Family-ID

**Test Steps**:
1. Nutzer navigiert direkt zu `/stammdaten/botanical-families/nicht-existente-id`

**Expected Results**:
- Seite zeigt eine Fehlermeldung (ErrorDisplay-Komponente, data-testid="error-display") anstelle des Formulars
- "Zurück" oder Retry-Button ist verfügbar
- Fehlermeldung enthält keine internen Systemdetails (kein Stacktrace, keine Datenbankfehlermeldung)

**Postconditions**:
- Keine Daueränderung

**Tags**: [req-001, botanical-family, fehlermeldung, 404, error-display]

---

## TC-001-069: Ungültige URL — Species nicht gefunden zeigt Fehlermeldung

**Requirement**: REQ-001 §2 — Species Navigation, ErrorDisplay-Komponente
**Priority**: Medium
**Category**: Fehlermeldung
**Preconditions**:
- Nutzer kennt eine nicht existente Species-ID

**Test Steps**:
1. Nutzer navigiert direkt zu `/stammdaten/species/nicht-existente-id`

**Expected Results**:
- Seite zeigt eine Fehlermeldung (ErrorDisplay-Komponente) anstelle des Formulars
- "Zurück" oder Retry-Button ist verfügbar

**Postconditions**:
- Keine Daueränderung

**Tags**: [req-001, species, fehlermeldung, 404, error-display]

---

## Gruppe 18: Toxizität & Allergen-Anzeige (User-Safety)

---

## TC-001-070: Toxizitätsdaten einer Species werden auf der Detailseite angezeigt

**Requirement**: REQ-001 §2 — Species.toxicity (ToxicityInfo), §2 — Seed-Daten Species-Toxizität
**Priority**: High
**Category**: Detailansicht
**Preconditions**:
- Nutzer ist auf der Detailseite einer Species mit Toxizitätsdaten
- Z.B. "Monstera deliciosa" (is_toxic_cats=true, is_toxic_dogs=true, severity=moderate)

**Test Steps**:
1. Nutzer öffnet die Detailseite von "Monstera deliciosa"
2. Nutzer scrollt zum Abschnitt Toxizitätsdaten oder Sicherheitshinweise

**Expected Results**:
- Toxizitätsinformationen sind sichtbar: Giftig für Katzen, Giftig für Hunde, Schweregrad "Moderat"
- Giftige Inhaltsstoffe sind aufgelistet (z.B. "Kalziumoxalat-Raphide")
- Betroffene Pflanzenteile sind angegeben (z.B. "Blätter, Stängel")

**Postconditions**:
- Keine Daueränderung

**Tags**: [req-001, species, toxizität, sicherheit, tiergift, detailansicht]

---

## TC-001-071: Hinweis bei fehlenden Toxizitätsdaten

**Requirement**: REQ-001 §2 — Seed-Daten Species-Toxizität, Hinweis bei unbekannten Toxizitätsdaten
**Priority**: Medium
**Category**: Detailansicht
**Preconditions**:
- Nutzer ist auf der Detailseite einer manuell angelegten Species ohne Toxizitätsdaten

**Test Steps**:
1. Nutzer öffnet die Detailseite einer neu erstellten Species (keine Toxizitätsdaten vorhanden)
2. Nutzer navigiert zum Bereich mit Sicherheitshinweisen

**Expected Results**:
- Hinweistext ist sichtbar: "Toxizitätsdaten unbekannt — Vorsicht bei Haustieren und Kleinkindern."
- Kein Fehler-Banner erscheint

**Postconditions**:
- Keine Daueränderung

**Tags**: [req-001, species, toxizität, unbekannt, sicherheitshinweis]

---

## TC-001-072: Allergeninformationen — Latex-Hinweis bei Ficus-Arten

**Requirement**: REQ-001 §2 — Species.allergen_info (AllergenInfo), §2 — Seed-Daten Allergenpotenzial
**Priority**: Medium
**Category**: Detailansicht
**Preconditions**:
- Nutzer ist auf der Detailseite von "Ficus lyrata" (latex_sap=true)

**Test Steps**:
1. Nutzer öffnet die Detailseite von "Ficus lyrata"
2. Nutzer scrollt zu den Allergen-/Sicherheitsinformationen

**Expected Results**:
- Hinweis "Enthält Milchsaft — Vorsicht bei Latexallergie" ist sichtbar
- Allergene Verbindungen sind aufgelistet (z.B. "Latexproteine", "Furocumarine")

**Postconditions**:
- Keine Daueränderung

**Tags**: [req-001, species, allergen, latex, ficus, sicherheitshinweis]

---

## Gruppe 19: Vermehrungsmethoden-Anzeige (REQ-017 Verknüpfung)

---

## TC-001-073: Vermehrungsmethoden einer Species werden auf der Detailseite angezeigt

**Requirement**: REQ-001 §2 — Species.propagation_methods, propagation_difficulty, §2 — Seed-Daten Vermehrungsmethoden
**Priority**: Medium
**Category**: Detailansicht
**Preconditions**:
- Nutzer ist auf der Detailseite einer Species mit Vermehrungsdaten
- Z.B. "Monstera deliciosa" (propagation_methods: ['cutting_stem', 'layering'], propagation_difficulty: 'easy')

**Test Steps**:
1. Nutzer öffnet die Detailseite von "Monstera deliciosa"
2. Nutzer navigiert zur Sektion Vermehrung

**Expected Results**:
- Vermehrungsmethoden sind sichtbar: z.B. "Stecklinge (Stängel)", "Abmoosen"
- Schwierigkeitsgrad "Einfach" ist angezeigt

**Postconditions**:
- Keine Daueränderung

**Tags**: [req-001, species, vermehrung, propagation-methods, detailansicht, req-017]

---

## TC-001-074: Einsteiger-Modus filtert nur "Einfach"-Vermehrungsarten heraus (REQ-021)

**Requirement**: REQ-001 §2 — propagation_difficulty, REQ-021 Einsteiger-Modus
**Priority**: Low
**Category**: Detailansicht
**Preconditions**:
- Nutzer hat Erfahrungsstufe "Einsteiger" eingestellt
- Species-Liste ist geöffnet

**Test Steps**:
1. Nutzer navigiert zu `/stammdaten/species` im Einsteiger-Modus

**Expected Results**:
- Arten mit `propagation_difficulty = 'easy'` (z.B. Monstera, Epipremnum) werden für Vermehrungsempfehlungen bevorzugt angezeigt oder hervorgehoben
- Arten mit `propagation_difficulty = 'difficult'` (z.B. Chamaedorea elegans) sind nicht prominent als Vermehrungskandidaten markiert

**Postconditions**:
- Keine Daueränderung

**Tags**: [req-001, species, vermehrung, einsteiger, propagation-difficulty, req-021]

---

## Gruppe 20: Weitere Validierungs-Edge-Cases

---

## TC-001-075: BotanicalFamily — pH-Felder leer lassen ist erlaubt (optional)

**Requirement**: REQ-001 §3 — PhRange ist optional (soil_ph_preference: Optional[PhRange])
**Priority**: Medium
**Category**: Formvalidierung
**Preconditions**:
- Erstellen-Dialog für Botanische Familie ist geöffnet

**Test Steps**:
1. Nutzer füllt alle Pflichtfelder aus, lässt aber "pH-Minimum" und "pH-Maximum" leer
2. Nutzer klickt auf "Erstellen"

**Expected Results**:
- Kein Validierungsfehler für die pH-Felder
- Dialog schließt sich, Familie wird erfolgreich erstellt ohne pH-Bereich

**Postconditions**:
- Familie ist ohne pH-Präferenz gespeichert

**Tags**: [req-001, botanical-family, formvalidierung, ph-optional, grenzwert]

---

## TC-001-076: Species wissenschaftlicher Name — dreiteilige Namen ohne Hybrid-Symbol werden abgelehnt

**Requirement**: REQ-001 §3 — SpeciesDefinition.validate_scientific_name (drei Teile ohne x/× werden abgelehnt)
**Priority**: Medium
**Category**: Formvalidierung
**Preconditions**:
- Erstellen-Dialog für Species ist geöffnet

**Test Steps**:
1. Nutzer gibt im Feld "Wissenschaftlicher Name" den Wert "Solanum tuberosum var" ein (drei Teile ohne Hybridzeichen)
2. Nutzer klickt auf "Erstellen"

**Expected Results**:
- Fehlermeldung erscheint: Wissenschaftlicher Name muss Binomialnomenklatur (Gattung Art) oder Hybridnotation (Gattung × Art) sein
- Dialog bleibt geöffnet

**Postconditions**:
- Keine Daueränderung

**Tags**: [req-001, species, formvalidierung, scientific-name, binomial, validierung]

---

## TC-001-077: Botanische Familie — Ordnung leer lassen ist erlaubt (optional)

**Requirement**: REQ-001 §3 — BotanicalFamilyDefinition.order Optional
**Priority**: Medium
**Category**: Formvalidierung
**Preconditions**:
- Erstellen-Dialog für Botanische Familie ist geöffnet

**Test Steps**:
1. Nutzer füllt alle Pflichtfelder aus, lässt das Feld "Ordnung" leer
2. Nutzer klickt auf "Erstellen"

**Expected Results**:
- Kein Validierungsfehler für das Ordnungs-Feld
- Dialog schließt sich, Familie wird erfolgreich erstellt

**Postconditions**:
- Familie ohne Ordnung ist gespeichert

**Tags**: [req-001, botanical-family, formvalidierung, order-optional]

---

## TC-001-078: Duplikat-Schutz — Species mit identischem wissenschaftlichen Namen wird abgelehnt

**Requirement**: REQ-001 §6 — DoD Duplikatsprüfung
**Priority**: High
**Category**: Formvalidierung
**Preconditions**:
- Species "Solanum lycopersicum" ist bereits im System vorhanden
- Erstellen-Dialog für Species ist geöffnet

**Test Steps**:
1. Nutzer gibt im Feld "Wissenschaftlicher Name" erneut "Solanum lycopersicum" ein
2. Nutzer füllt alle weiteren Felder aus
3. Nutzer klickt auf "Erstellen"

**Expected Results**:
- Fehlerbenachrichtigung erscheint (vom Server zurückgeliefert)
- Meldung enthält sinngemäß: "Ein Eintrag mit diesem Namen existiert bereits."
- Dialog bleibt geöffnet

**Postconditions**:
- Keine Daueränderung; Duplikat wurde NICHT angelegt

**Tags**: [req-001, species, formvalidierung, duplikat, duplikatsprüfung]

---

## Abdeckungs-Matrix

| Spezifikations-Abschnitt | Beschreibung | Testfälle |
|---|---|---|
| §2 BotanicalFamily Knoten | Listenansicht, CRUD, Formularfelder, pH-Felder | TC-001-001 bis TC-001-018 |
| §2 Species Knoten | Listenansicht, Filter, CRUD, Tabs | TC-001-019 bis TC-001-035 |
| §2 Cultivar Knoten | Sorten-Tab, CRUD, Detailseite, Autoflower, Phasen-Gießen | TC-001-036 bis TC-001-046 |
| §2 LifecycleConfig + GrowthPhase | Lebenszyklus-Tab, Phasen-CRUD | TC-001-047 bis TC-001-049 |
| §2 Fruchtfolge (rotation_after, shares_pest_risk) | CropRotationPage Warnungen | TC-001-050 bis TC-001-052 |
| §2 ToxicityInfo / AllergenInfo | Anzeige auf Detailseite, Hinweise | TC-001-070 bis TC-001-072 |
| §2 propagation_methods | Vermehrungsanzeige | TC-001-073 bis TC-001-074 |
| §2 Seed-Daten Zierpflanzen | Violaceae, Stiefmütterchen-Species | TC-001-055 |
| §3 Validierungen Python | aceae-Endung, ales-Endung, pH-Bereich, Allelopathie, N-Fixing, Scientific-Name-Hybrid, Traits, Duplikat | TC-001-007 bis TC-001-009, TC-001-013, TC-001-017, TC-001-026 bis TC-001-028, TC-001-038 bis TC-001-039, TC-001-040 bis TC-001-043, TC-001-075 bis TC-001-078 |
| §4 Auth & Autorisierung | Redirect unauthenticated, Platform-Admin Schreibzugriff | TC-001-057, TC-001-063 |
| §6 DoD i18n | Deutsch/Englisch Familiennamen | TC-001-053 |
| §6 DoD Seed-Daten | 9 Pflanzenfamilien vollständig | TC-001-054 |
| §6 DoD Stammdaten-Scoping v4.0 | tenant_has_access, Tenant-eigene Species, Overlay, hidden-Flag, Promotion | TC-001-058 bis TC-001-063 |
| §6 DoD Bulk-Import | Import-Seite erreichbar | TC-001-064 |
| §6 Testszenarien 5–7 | Fruchtfolge CRITICAL/WARNING/OK | TC-001-050, TC-001-051, TC-001-052 |
| §6 Testszenarien 9–12 | Tenant-Sichtbarkeit, Overlay, Tenant-eigene, Promotion | TC-001-058 bis TC-001-062 |
| UX-Muster | UnsavedChangesGuard, Mobile Cards | TC-001-014, TC-001-056, TC-001-066, TC-001-067 |
| REQ-021 Erfahrungsstufen | ExpertiseFieldWrapper | TC-001-029, TC-001-074 |
| Fehler/Edge Cases | 404, pH-Optional, Order-Optional | TC-001-068, TC-001-069, TC-001-075, TC-001-077 |
