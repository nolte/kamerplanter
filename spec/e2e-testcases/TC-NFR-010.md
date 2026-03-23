---
req_id: NFR-010
title: UI-Vollständigkeit — Pflegemasken & Listenansichten für alle Entitäten
category: Usability / UI-Vollständigkeit
test_count: 62
coverage_areas:
  - NFR-010 §2.1 CRUD-Operationen
  - NFR-010 §2.2 Create-Dialog
  - NFR-010 §2.3 Read/Detail-Ansicht
  - NFR-010 §2.4 Update/Edit-Formular
  - NFR-010 §2.5 Delete mit Bestätigung
  - NFR-010 §3.1 Tabellarische Übersicht
  - NFR-010 §3.2 Pagination
  - NFR-010 §3.3 Sortierung
  - NFR-010 §3.3a Durchsuchbarkeit
  - NFR-010 §3.3b Spaltenspezifische Filter
  - NFR-010 §3.3c Tablet-Spaltenprioritäten
  - NFR-010 §3.4 Leerzustand
  - NFR-010 §3.5 Ladezustand
  - NFR-010 §3.6 Erstell-Aktion
  - NFR-010 §4.1/4.2 Vollständigkeitsmatrix
  - NFR-010 §5 Eingebettete Entitäten
  - NFR-010 §6.1 UI-Pattern-Konsistenz
  - NFR-010 §6.2 Responsivität
  - NFR-010 §6.3 Barrierefreiheit
  - NFR-010 §7 Akzeptanzkriterien / Testszenarien
generated: 2026-03-21
version: "1.0"
---

# TC-NFR-010: UI-Vollständigkeit — Pflegemasken & Listenansichten

Dieses Dokument enthält alle End-to-End-Testfälle für NFR-010, die aus der
**Perspektive des Nutzers im Browser** formuliert sind. Jeder Testfall beschreibt,
was der Nutzer sieht, klickt, eingibt und als Ergebnis auf dem Bildschirm erwartet.

**Primäre Test-Entitäten** (Vollständigkeitsmatrix NFR-010 §4.2):
BotanicalFamily, Species, Cultivar, Site, Location, Slot, Substrate, Batch,
PlantInstance, GrowthPhase

**Shared-Komponenten** (referenziert in Testfällen):
- `DataTable` → `data-testid="data-table"`, Zeilen: `data-testid="data-table-row"`
- `ConfirmDialog` → `data-testid="confirm-dialog"`, Abbrechen: `data-testid="confirm-dialog-cancel"`, Bestätigen: `data-testid="confirm-dialog-confirm"`
- `EmptyState` → `data-testid="empty-state"`, Aktion: `data-testid="empty-state-action"`
- `LoadingSkeleton` → `data-testid="loading-skeleton"`
- `ErrorDisplay` → `data-testid="error-display"`, Retry: `data-testid="error-retry-button"`
- Formularfelder: `data-testid="form-field-{name}"` (z.B. `form-field-name`)
- `FormActions` Speichern: `data-testid="form-submit-button"`, Abbrechen: `data-testid="form-cancel-button"`
- Suchfeld: `data-testid="table-search-input"`, Trefferzähler: `data-testid="showing-count"`
- Keine-Ergebnisse-Anzeige: `data-testid="no-search-results"`

---

## Gruppe A: Listenansicht — Grundverhalten (DataTable)

### TC-NFR010-001: Listenansicht lädt Daten und zeigt Einleitungstext

**Zusammenfassung**: Nutzer öffnet eine Listenansicht und sieht Seitentitel, Einleitungstext, DataTable und „Hinzufügen"-Button.

**Requirement**: NFR-010 §3.1, §2.2 (Einleitungstexte), §3.6 (Erstell-Aktion)
**Priority**: Critical
**Category**: Listenansicht / Happy Path
**Preconditions**:
- Nutzer ist angemeldet und hat Tenant-Zugriff
- Mindestens ein Datensatz der Entität ist vorhanden
- Test-URL: `/stammdaten/botanical-families`

**Test Steps**:
1. Nutzer navigiert zu `/stammdaten/botanical-families`
2. Nutzer wartet, bis die Seite vollständig geladen ist (Skeleton verschwindet)
3. Nutzer beobachtet Seitenaufbau

**Expected Results**:
- Seitentitel (via `PageTitle`-Komponente) ist sichtbar (z.B. „Botanische Familien")
- Unterhalb des Titels erscheint ein kurzer Einleitungstext (1–2 Sätze, erklärt den Zweck der Liste)
- Die `DataTable`-Komponente (`data-testid="data-table"`) ist sichtbar und enthält Zeilen
- Die Spaltenüberschriften sind auf Deutsch beschriftet
- Ein „Hinzufügen"-Button (FAB oder prominenter Button) ist im Sichtbereich sichtbar
- Das Ladeskelett (`data-testid="loading-skeleton"`) ist nicht mehr sichtbar

**Postconditions**:
- Keine Datenveränderung

**Tags**: [nfr-010, listenansicht, einleitungstext, datatable, stammdaten, botanicalfamily]

---

### TC-NFR010-002: Listenansicht — Ladezustand mit Skeleton

**Zusammenfassung**: Beim ersten Laden der Listenansicht erscheint das Ladeskelett bevor die Daten eintreffen.

**Requirement**: NFR-010 §3.5
**Priority**: High
**Category**: Ladezustand
**Preconditions**:
- Nutzer ist angemeldet
- Netzwerkdrosselung auf „Slow 3G" oder vergleichbar eingestellt (z.B. via Browser DevTools)
- Test-URL: `/stammdaten/botanical-families`

**Test Steps**:
1. Nutzer aktiviert Netzwerkdrosselung im Browser
2. Nutzer navigiert zu `/stammdaten/botanical-families`
3. Nutzer beobachtet die Seite unmittelbar nach dem Navigieren, bevor Daten geladen sind

**Expected Results**:
- `data-testid="loading-skeleton"` ist sichtbar (Tabellen-Skeleton mit mehreren Zeilen-Platzhaltern)
- Es erscheint kein leerer Zustand (`data-testid="empty-state"`) während des Ladens
- Kein Flackern zwischen leerem Zustand und Daten
- Nach vollständigem Laden verschwindet das Skeleton und die Tabelle erscheint

**Postconditions**:
- Netzwerkdrosselung deaktivieren

**Tags**: [nfr-010, listenansicht, ladezustand, loadingskeleton, datatable]

---

### TC-NFR010-003: Listenansicht — Leerzustand mit EmptyState und Erstell-Button

**Zusammenfassung**: Bei leerer Datenmenge zeigt die Tabelle die EmptyState-Komponente mit einem Erstell-Button.

**Requirement**: NFR-010 §3.4, §3.6
**Priority**: Critical
**Category**: Leerzustand
**Preconditions**:
- Nutzer ist angemeldet
- Keine Substrate vorhanden (leere Datenbank für diese Entität)
- Test-URL: `/standorte/substrates`

**Test Steps**:
1. Nutzer navigiert zu `/standorte/substrates`
2. Nutzer wartet, bis die Seite geladen ist

**Expected Results**:
- `data-testid="empty-state"` ist sichtbar
- Die EmptyState-Komponente enthält eine beschreibende Nachricht (z.B. „Noch keine Substrate vorhanden")
- `data-testid="empty-state-action"` (Erstell-Button innerhalb von EmptyState) ist sichtbar und aktiv
- Keine leere Tabelle mit Spalten aber ohne Zeilen sichtbar

**Test Steps (Fortsetzung)**:
3. Nutzer klickt auf `data-testid="empty-state-action"`

**Expected Results (Fortsetzung)**:
- Der Create-Dialog öffnet sich

**Postconditions**:
- Keine Datenveränderung

**Tags**: [nfr-010, listenansicht, leerzustand, emptystate, substrat, standorte]

---

### TC-NFR010-004: Listenansicht — Pagination (Seitengröße und Navigation)

**Zusammenfassung**: Nutzer ändert die Seitengröße und navigiert zwischen Seiten.

**Requirement**: NFR-010 §3.2
**Priority**: High
**Category**: Listenansicht / Pagination
**Preconditions**:
- Nutzer ist angemeldet
- Mindestens 55 PlantInstance-Einträge sind vorhanden
- Test-URL: `/pflanzen` (PlantInstanceListPage)

**Test Steps**:
1. Nutzer navigiert zur Pflanzenliste
2. Nutzer prüft die Standard-Seitengröße
3. Nutzer öffnet das Dropdown „Zeilen pro Seite" (MUI TablePagination)
4. Nutzer wählt „25" aus

**Expected Results**:
- Standard-Seitengröße beim Laden ist 50 Einträge
- Nach Auswahl von 25: Tabelle zeigt maximal 25 Zeilen
- Die Pagination zeigt die Gesamtanzahl an (z.B. „1–25 von 55 Einträgen")
- Der Navigations-Button „Nächste Seite" ist aktiv

**Test Steps (Fortsetzung)**:
5. Nutzer klickt auf „Nächste Seite"

**Expected Results (Fortsetzung)**:
- Die zweite Seite wird geladen (Einträge 26–50 oder 26 bis Ende)
- Die Paginierungsanzeige aktualisiert sich entsprechend (z.B. „26–50 von 55 Einträgen")
- Der Button „Vorherige Seite" ist nun aktiv

**Postconditions**:
- Keine Datenveränderung

**Tags**: [nfr-010, listenansicht, pagination, datatable, pflanzen]

---

### TC-NFR010-005: Listenansicht — Zeilenklick navigiert zur Detail-Ansicht

**Zusammenfassung**: Klick auf eine Tabellenzeile navigiert den Nutzer zur Detail-Seite der Entität.

**Requirement**: NFR-010 §3.1 (onRowClick)
**Priority**: Critical
**Category**: Navigation
**Preconditions**:
- Nutzer ist angemeldet
- Mindestens eine BotanicalFamily mit bekanntem Namen ist vorhanden (z.B. „Solanaceae")
- Test-URL: `/stammdaten/botanical-families`

**Test Steps**:
1. Nutzer navigiert zu `/stammdaten/botanical-families`
2. Nutzer wartet, bis die Tabelle geladen ist
3. Nutzer klickt auf die Zeile mit „Solanaceae" (`data-testid="data-table-row"`)

**Expected Results**:
- Browser navigiert zur Detail-Seite: URL ändert sich auf `/stammdaten/botanical-families/{key}`
- Detail-Seite zeigt den Namen „Solanaceae" im Seitentitel oder Heading
- Breadcrumb zeigt den Navigationspfad (z.B. „Stammdaten > Botanische Familien > Solanaceae")

**Postconditions**:
- Keine Datenveränderung

**Tags**: [nfr-010, listenansicht, navigation, zeilenklick, botanicalfamily, datatable]

---

## Gruppe B: Suche und Sortierung

### TC-NFR010-006: Listenansicht — Volltextsuche mit Debouncing

**Zusammenfassung**: Nutzer gibt einen Suchbegriff ein und die Liste filtert sich nach 300ms Verzögerung.

**Requirement**: NFR-010 §3.3a
**Priority**: High
**Category**: Listenansicht / Suche
**Preconditions**:
- Nutzer ist angemeldet
- Mindestens 5 BotanicalFamily-Einträge vorhanden, darunter „Solanaceae" und „Asteraceae"
- Test-URL: `/stammdaten/botanical-families`

**Test Steps**:
1. Nutzer navigiert zu `/stammdaten/botanical-families`
2. Nutzer klickt in das Suchfeld (`data-testid="table-search-input"`)
3. Nutzer gibt „Solan" ein (Teileingabe)
4. Nutzer wartet weniger als 300ms

**Expected Results**:
- Die Tabelle zeigt noch alle Einträge (Debounce-Verzögerung noch nicht abgelaufen)

**Test Steps (Fortsetzung)**:
5. Nutzer wartet 300ms oder mehr

**Expected Results (Fortsetzung)**:
- Die Tabelle zeigt nur noch Einträge, die „Solan" enthalten (z.B. „Solanaceae")
- `data-testid="showing-count"` zeigt die Trefferzahl an (z.B. „1 von 8 Einträgen")
- `data-testid="search-chip"` mit dem Suchbegriff ist sichtbar
- URL enthält den Query-Parameter `?search=Solan`

**Postconditions**:
- Keine Datenveränderung

**Tags**: [nfr-010, listenansicht, suche, debouncing, url-parameter, datatable, botanicalfamily]

---

### TC-NFR010-007: Listenansicht — Suche zurücksetzen

**Zusammenfassung**: Nutzer löscht den Suchbegriff über das X-Icon und alle Datensätze erscheinen wieder.

**Requirement**: NFR-010 §3.3a (Zurücksetzen-Button)
**Priority**: High
**Category**: Listenansicht / Suche
**Preconditions**:
- Nutzer ist angemeldet
- BotanicalFamily-Listenansicht ist geöffnet
- Aktive Suche mit Begriff „Solan" (Folge-Testfall nach TC-NFR010-006)

**Test Steps**:
1. Nutzer klickt auf das X-Icon im Suchfeld oder löscht den Suchbegriff manuell
2. Nutzer wartet 300ms

**Expected Results**:
- Suchfeld ist leer
- Die Tabelle zeigt alle Einträge (ungefiltert)
- `data-testid="showing-count"` zeigt die Gesamtanzahl oder ist nicht mehr sichtbar
- `data-testid="search-chip"` ist nicht mehr sichtbar
- URL-Query-Parameter `?search=` ist entfernt oder leer

**Postconditions**:
- Keine Datenveränderung

**Tags**: [nfr-010, listenansicht, suche-reset, url-parameter, datatable]

---

### TC-NFR010-008: Listenansicht — Suche ohne Treffer zeigt Keine-Ergebnisse-Meldung

**Zusammenfassung**: Suche nach einem Begriff ohne Treffer zeigt eine spezifische Meldung, nicht die EmptyState-Komponente.

**Requirement**: NFR-010 §3.3a
**Priority**: Medium
**Category**: Listenansicht / Suche / Fehlermeldung
**Preconditions**:
- Nutzer ist angemeldet
- BotanicalFamily-Listenansicht mit mehreren Einträgen ist geöffnet

**Test Steps**:
1. Nutzer gibt in das Suchfeld einen nicht existierenden Begriff ein, z.B. „XXXXXX"
2. Nutzer wartet 300ms

**Expected Results**:
- `data-testid="no-search-results"` ist sichtbar
- Die Meldung lautet sinngemäß: „Keine Ergebnisse für Ihre Suche gefunden" (oder entsprechende i18n-Übersetzung)
- `data-testid="empty-state"` ist NICHT sichtbar (dies ist ein Suchergebnis, kein echter Leerzustand)
- `data-testid="showing-count"` zeigt „0 von N Einträgen"

**Postconditions**:
- Keine Datenveränderung

**Tags**: [nfr-010, listenansicht, suche, keine-treffer, datatable]

---

### TC-NFR010-009: Listenansicht — Spalten sind sortierbar (aufsteigend/absteigend)

**Zusammenfassung**: Klick auf eine Spaltenüberschrift sortiert die Liste, erneuter Klick wechselt die Richtung.

**Requirement**: NFR-010 §3.3
**Priority**: High
**Category**: Listenansicht / Sortierung
**Preconditions**:
- Nutzer ist angemeldet
- Mindestens 5 BotanicalFamily-Einträge vorhanden
- Standard-Sortierung: Name aufsteigend
- Test-URL: `/stammdaten/botanical-families`

**Test Steps**:
1. Nutzer navigiert zu `/stammdaten/botanical-families`
2. Nutzer beobachtet die Spaltenüberschrift „Name" — ein Pfeil nach oben (aufsteigend) ist sichtbar
3. Nutzer klickt auf die Spaltenüberschrift „Name"

**Expected Results**:
- Sortierrichtung wechselt zu absteigend
- Pfeil in der Spaltenüberschrift zeigt nach unten
- Die Einträge sind alphabetisch absteigend sortiert (z.B. „Solanaceae" vor „Apiaceae")
- Sortierzustand wird via MUI `TableSortLabel` visuell angezeigt

**Test Steps (Fortsetzung)**:
4. Nutzer klickt erneut auf „Name"

**Expected Results (Fortsetzung)**:
- Sortierrichtung wechselt zurück zu aufsteigend
- Erster Eintrag ist alphabetisch der erste (z.B. „Apiaceae")

**Postconditions**:
- Keine Datenveränderung

**Tags**: [nfr-010, listenansicht, sortierung, tablesortlabel, botanicalfamily, datatable]

---

### TC-NFR010-010: Listenansicht — URL-Parameter für Suche ist teilbar

**Zusammenfassung**: Eine URL mit `?search=Solan` zeigt beim direkten Aufruf die vorgefilterte Liste.

**Requirement**: NFR-010 §3.3a (URL-Query-Parameter)
**Priority**: Medium
**Category**: Navigation / Suche
**Preconditions**:
- Nutzer ist angemeldet
- Mindestens eine BotanicalFamily mit „Solan" im Namen vorhanden

**Test Steps**:
1. Nutzer ruft direkt die URL `/stammdaten/botanical-families?search=Solan` auf

**Expected Results**:
- Die Seite lädt mit aktivem Suchbegriff „Solan" im Suchfeld
- Tabelle zeigt nur gefilterte Einträge
- `data-testid="showing-count"` zeigt Trefferzahl

**Postconditions**:
- Keine Datenveränderung

**Tags**: [nfr-010, listenansicht, url-parameter, suche, deep-link, botanicalfamily]

---

## Gruppe C: Create-Dialog / Create-Seite

### TC-NFR010-011: Create-Dialog öffnet sich über „Hinzufügen"-Button

**Zusammenfassung**: Nutzer klickt den prominenten Hinzufügen-Button und der Create-Dialog öffnet sich.

**Requirement**: NFR-010 §2.2, §3.6
**Priority**: Critical
**Category**: Dialog / Happy Path
**Preconditions**:
- Nutzer ist angemeldet
- Test-URL: `/stammdaten/botanical-families`

**Test Steps**:
1. Nutzer navigiert zu `/stammdaten/botanical-families`
2. Nutzer klickt auf den „Hinzufügen"-Button (FAB oder Toolbar-Button mit Add-Icon)

**Expected Results**:
- Ein Create-Dialog öffnet sich (Modal)
- Ein Einleitungstext ist sichtbar (z.B. „Legen Sie eine neue Botanische Familie an. Familien gruppieren Pflanzenarten mit ähnlichem Nährstoffbedarf.")
- Pflichtfelder sind mit einem Asterisk `*` im Label gekennzeichnet
- Das erste Pflichtfeld hat den Fokus (Barrierefreiheit: Fokus-Management)
- Der Speichern-Button (`data-testid="form-submit-button"`) ist deaktiviert, da noch keine Eingabe vorgenommen wurde

**Postconditions**:
- Keine Datenveränderung

**Tags**: [nfr-010, create-dialog, einleitungstext, pflichtfelder, fokus, botanicalfamily]

---

### TC-NFR010-012: Create-Dialog — Pflichtfeld-Validierung bei leerem Submit

**Zusammenfassung**: Nutzer klickt Speichern ohne Pflichtfelder zu füllen und sieht Validierungsfehlermeldungen.

**Requirement**: NFR-010 §2.2, §6.1 (Inline-Validierung, Fehlermeldungen unter dem Feld)
**Priority**: Critical
**Category**: Formvalidierung
**Preconditions**:
- Nutzer ist angemeldet
- Create-Dialog für BotanicalFamily ist geöffnet (Folge von TC-NFR010-011)

**Test Steps**:
1. Nutzer lässt alle Felder leer
2. Nutzer klickt den Speichern-Button (`data-testid="form-submit-button"`)

**Expected Results**:
- Validierungsfehlermeldungen erscheinen unter den Pflichtfeldern (helperText, rot eingefärbt)
- Für Feld „Name": Fehlermeldung sichtbar (z.B. „Pflichtfeld" oder „Muss auf '-aceae' enden")
- Für Feld „Typischer Nährstoffbedarf": Fehlermeldung sichtbar
- Für Feld „Typische Wuchsformen" (Mehrfachauswahl): Fehlermeldung sichtbar
- Für Feld „Bestäubungstyp" (Mehrfachauswahl): Fehlermeldung sichtbar
- Der Dialog bleibt geöffnet
- Es wird kein API-Aufruf ausgelöst (keine Spinner-Animation auf dem Submit-Button)

**Postconditions**:
- Keine Datenveränderung

**Tags**: [nfr-010, formvalidierung, pflichtfelder, fehlermeldung, helpertext, zod, botanicalfamily]

---

### TC-NFR010-013: Create-Dialog — Feldspezifische Zod-Validierung (Name-Endung)

**Zusammenfassung**: Nutzer gibt einen Namen ein, der nicht auf „-aceae" endet, und sieht eine feldspezifische Fehlermeldung.

**Requirement**: NFR-010 §2.2, §6.1 (Zod-Schema mit feldspezifischen Fehlermeldungen)
**Priority**: High
**Category**: Formvalidierung
**Preconditions**:
- Nutzer ist angemeldet
- Create-Dialog für BotanicalFamily ist geöffnet

**Test Steps**:
1. Nutzer gibt in das Feld „Name" (`data-testid="form-field-name"`) den Wert „Solanum" ein
2. Nutzer verlässt das Feld (Tab oder Klick außerhalb)

**Expected Results**:
- Fehlermeldung erscheint direkt unter dem Feld: „Muss auf '-aceae' enden"
- Das Feld ist rot umrandet (MUI error state)
- Speichern-Button bleibt deaktiviert

**Test Steps (Fortsetzung)**:
3. Nutzer korrigiert den Wert auf „Solanaceae"
4. Nutzer verlässt das Feld

**Expected Results (Fortsetzung)**:
- Fehlermeldung verschwindet
- Feld zeigt keinen Fehler-State mehr

**Postconditions**:
- Keine Datenveränderung

**Tags**: [nfr-010, formvalidierung, zod, botanicalfamily, name-validierung, blur-validierung]

---

### TC-NFR010-014: Create-Dialog — Erfolgreiche Erstellung mit Snackbar-Feedback

**Zusammenfassung**: Nutzer füllt alle Pflichtfelder korrekt aus, speichert und erhält eine Erfolgsbenachrichtigung.

**Requirement**: NFR-010 §2.2 (Erfolgsrückmeldung via Snackbar)
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- Nutzer ist angemeldet
- Create-Dialog für BotanicalFamily ist geöffnet
- Kein Eintrag „Testaceae" vorhanden

**Test Steps**:
1. Nutzer gibt in „Name" (`data-testid="form-field-name"`) den Wert „Testaceae" ein
2. Nutzer wählt für „Typischer Nährstoffbedarf" (`data-testid="form-field-typical_nutrient_demand"`) den Wert „Mittel" aus
3. Nutzer wählt unter „Typische Wuchsformen" mindestens „Kraut" aus
4. Nutzer wählt unter „Bestäubungstyp" mindestens „Insekten" aus
5. Nutzer klickt „Speichern" (`data-testid="form-submit-button"`)

**Expected Results**:
- Während des API-Calls: Speichern-Button zeigt Ladeindikator (disabled + Spinner)
- Nach erfolgreichem Speichern: Dialog schließt sich
- Eine Erfolgs-Snackbar erscheint (unten mittig), z.B. „Botanische Familie erfolgreich erstellt"
- Die Snackbar blendet sich nach wenigen Sekunden automatisch aus
- Der neue Eintrag „Testaceae" erscheint in der Tabelle

**Postconditions**:
- Datensatz „Testaceae" ist in der Datenbank vorhanden

**Tags**: [nfr-010, create, snackbar, erfolg, botanicalfamily, happy-path]

---

### TC-NFR010-015: Create-Dialog — API-Fehler (Duplikat) wird im Dialog angezeigt

**Zusammenfassung**: Nutzer versucht eine BotanicalFamily mit einem bereits existierenden Namen zu erstellen und sieht eine API-Fehlermeldung.

**Requirement**: NFR-010 §2.2 (Fehlerbehandlung gemäß NFR-006)
**Priority**: High
**Category**: Fehlermeldung
**Preconditions**:
- Nutzer ist angemeldet
- Eintrag „Solanaceae" existiert bereits
- Create-Dialog für BotanicalFamily ist geöffnet

**Test Steps**:
1. Nutzer füllt alle Pflichtfelder aus, gibt als Namen „Solanaceae" ein
2. Nutzer klickt „Speichern" (`data-testid="form-submit-button"`)

**Expected Results**:
- Dialog bleibt geöffnet
- Eine Fehlermeldung erscheint (entweder als Snackbar oder im Dialog), die sinngemäß lautet: „Ein Eintrag mit diesem Namen existiert bereits."
- Das Feld „Name" zeigt ggf. einen Fehler-State

**Postconditions**:
- Keine neuen Datensätze erstellt

**Tags**: [nfr-010, create, api-fehler, duplikat, nfr-006, botanicalfamily]

---

### TC-NFR010-016: Create-Dialog — Abbrechen schließt Dialog ohne Speichern

**Zusammenfassung**: Nutzer öffnet den Create-Dialog, füllt Felder aus und klickt Abbrechen — keine Daten werden gespeichert.

**Requirement**: NFR-010 §2.2, §6.1 (Button-Platzierung: Abbrechen links)
**Priority**: Medium
**Category**: Dialog
**Preconditions**:
- Nutzer ist angemeldet
- Create-Dialog für BotanicalFamily ist geöffnet mit Eingabe „Testfamiliaceae" im Name-Feld

**Test Steps**:
1. Nutzer hat „Testfamiliaceae" im Feld „Name" eingegeben
2. Nutzer klickt den „Abbrechen"-Button (`data-testid="form-cancel-button"`)

**Expected Results**:
- Dialog schließt sich sofort
- Keine Snackbar-Meldung erscheint
- In der Tabelle erscheint kein Eintrag „Testfamiliaceae"
- Fokus kehrt zum auslösenden Element (Hinzufügen-Button) zurück

**Postconditions**:
- Keine Datenveränderung

**Tags**: [nfr-010, create-dialog, abbrechen, fokus-management, botanicalfamily]

---

## Gruppe D: Detail-Ansicht (Read)

### TC-NFR010-017: Detail-Ansicht zeigt alle Felder und Breadcrumb

**Zusammenfassung**: Nutzer öffnet die Detail-Seite einer BotanicalFamily und sieht alle Felder sowie Breadcrumb-Navigation.

**Requirement**: NFR-010 §2.3
**Priority**: Critical
**Category**: Detailansicht / Happy Path
**Preconditions**:
- Nutzer ist angemeldet
- BotanicalFamily „Solanaceae" mit vollständigen Daten existiert
- Test-URL: `/stammdaten/botanical-families/{solanaceae-key}`

**Test Steps**:
1. Nutzer navigiert zur Detail-Seite von „Solanaceae"

**Expected Results**:
- Seitentitel (via `PageTitle`) zeigt „Solanaceae"
- Breadcrumb-Navigation ist sichtbar: „Stammdaten > Botanische Familien > Solanaceae"
- Alle Felder der Entität sind sichtbar und als read-only angezeigt:
  - Name, Deutscher Name, Englischer Name, Ordnung, Beschreibung
  - Typischer Nährstoffbedarf, Stickstoffbindung, Typische Wurzeltiefe
  - Boden-pH min/max, Frosttoleranz, Typische Wuchsformen
  - Häufige Schädlinge, Häufige Krankheiten, Bestäubungstyp
- Eine Aktionsleiste mit „Bearbeiten"- und „Löschen"-Buttons ist sichtbar
- Eingebettete Section mit zugehörigen Arten (Species) ist sichtbar

**Postconditions**:
- Keine Datenveränderung

**Tags**: [nfr-010, detailansicht, breadcrumb, read, botanicalfamily, pagetitle]

---

### TC-NFR010-018: Detail-Ansicht — Ladezustand und Fehlerbehandlung

**Zusammenfassung**: Die Detail-Seite zeigt das Ladeskelett während des API-Calls und bei Fehler die ErrorDisplay-Komponente mit Retry.

**Requirement**: NFR-010 §2.3 (Lade- und Fehlerzustände)
**Priority**: High
**Category**: Detailansicht / Fehlermeldung
**Preconditions**:
- Nutzer ist angemeldet

**Teil A — Ladezustand:**

**Test Steps**:
1. Nutzer aktiviert Netzwerkdrosselung auf „Slow 3G"
2. Nutzer navigiert zur Detail-Seite einer BotanicalFamily

**Expected Results**:
- `data-testid="loading-skeleton"` mit `variant="form"` ist sichtbar
- Seite flackert nicht zwischen leerem Zustand und Inhalt

**Teil B — Fehlerbehandlung bei ungültigem Key:**

**Test Steps**:
3. Nutzer navigiert zu `/stammdaten/botanical-families/ungueltigerkey-9999`

**Expected Results**:
- Browser navigiert zur NotFoundPage (`/404`) oder zeigt `data-testid="error-display"` mit einer Fehlermeldung
- Optional: `data-testid="error-retry-button"` ist sichtbar

**Postconditions**:
- Netzwerkdrosselung deaktivieren; keine Datenveränderung

**Tags**: [nfr-010, detailansicht, ladezustand, fehlerbehandlung, 404, errordisplay, loadingskeleton]

---

### TC-NFR010-019: Breadcrumb-Navigation — Rücknavigation zur Liste

**Zusammenfassung**: Nutzer klickt auf den Breadcrumb-Link zur Listenansicht und navigiert zurück.

**Requirement**: NFR-010 §2.3 (Breadcrumb-Navigation auf allen Seiten Pflicht)
**Priority**: High
**Category**: Navigation
**Preconditions**:
- Nutzer ist auf der Detail-Seite einer BotanicalFamily
- Breadcrumb zeigt: „Stammdaten > Botanische Familien > Solanaceae"

**Test Steps**:
1. Nutzer klickt auf „Botanische Familien" im Breadcrumb

**Expected Results**:
- Browser navigiert zu `/stammdaten/botanical-families`
- Listenansicht wird angezeigt

**Postconditions**:
- Keine Datenveränderung

**Tags**: [nfr-010, navigation, breadcrumb, botanicalfamily]

---

## Gruppe E: Edit-Formular (Update)

### TC-NFR010-020: Edit-Formular öffnet sich mit vorausgefüllten Werten

**Zusammenfassung**: Nutzer klickt „Bearbeiten" auf der Detail-Seite und das Formular ist mit den aktuellen Werten vorbelegt.

**Requirement**: NFR-010 §2.4
**Priority**: Critical
**Category**: Happy Path / Edit
**Preconditions**:
- Nutzer ist angemeldet
- BotanicalFamily „Solanaceae" mit Nährstoffbedarf „Mittel" existiert
- Nutzer befindet sich auf der Detail-Seite von „Solanaceae"

**Test Steps**:
1. Nutzer klickt den „Bearbeiten"-Button in der Aktionsleiste

**Expected Results**:
- Edit-Formular wird geöffnet (entweder Inline-Modus auf der Detail-Seite oder Weiterleitung zur Edit-Seite)
- Ein Einleitungstext erscheint oberhalb des Formulars (z.B. „Bearbeiten Sie die Eigenschaften dieser Botanischen Familie. Änderungen wirken sich auf alle zugeordneten Arten aus.")
- Feld „Name" (`data-testid="form-field-name"`) enthält den aktuellen Wert „Solanaceae"
- Feld „Typischer Nährstoffbedarf" enthält den aktuellen Wert „Mittel"
- Alle anderen Felder sind mit den gespeicherten Werten vorbelegt
- Speichern-Button (`data-testid="form-submit-button"`) ist deaktiviert (keine Änderungen vorgenommen)

**Postconditions**:
- Keine Datenveränderung

**Tags**: [nfr-010, edit, vorausgefuellt, einleitungstext, botanicalfamily, happy-path]

---

### TC-NFR010-021: Edit-Formular — Speichern-Button aktiv nach Änderung

**Zusammenfassung**: Speichern-Button ist deaktiviert bei unverändertem Formular und wird aktiv nach erster Änderung.

**Requirement**: NFR-010 §2.4 (Speichern-Button deaktiviert wenn keine Änderungen)
**Priority**: High
**Category**: Formvalidierung / Zustandswechsel
**Preconditions**:
- Nutzer ist im Edit-Formular für eine BotanicalFamily
- Speichern-Button ist deaktiviert (kein dirty state)

**Test Steps**:
1. Nutzer beobachtet: Speichern-Button (`data-testid="form-submit-button"`) ist deaktiviert
2. Nutzer ändert den Wert im Feld „Typischer Nährstoffbedarf" auf „Schwach"

**Expected Results**:
- Speichern-Button ist nun aktiv (nicht mehr deaktiviert)

**Test Steps (Fortsetzung)**:
3. Nutzer setzt den Wert zurück auf den Originalwert

**Expected Results (Fortsetzung)**:
- Speichern-Button ist wieder deaktiviert (keine Änderungen mehr vorhanden)

**Postconditions**:
- Keine Datenveränderung

**Tags**: [nfr-010, edit, dirty-state, speichern-button, botanicalfamily]

---

### TC-NFR010-022: Edit-Formular — Erfolgreiche Bearbeitung mit Snackbar

**Zusammenfassung**: Nutzer ändert einen Wert und speichert — Erfolgs-Snackbar erscheint und aktualisierter Wert ist sichtbar.

**Requirement**: NFR-010 §2.4 (Erfolgsrückmeldung)
**Priority**: Critical
**Category**: Happy Path / Edit
**Preconditions**:
- Nutzer ist im Edit-Formular für BotanicalFamily „Solanaceae"
- Aktueller Nährstoffbedarf ist „Mittel"

**Test Steps**:
1. Nutzer ändert „Typischer Nährstoffbedarf" auf „Hoch (Starkzehrer)"
2. Nutzer klickt „Speichern" (`data-testid="form-submit-button"`)

**Expected Results**:
- Während des API-Calls: Speichern-Button zeigt Ladeindikator
- Nach erfolgreichem Speichern: Erfolgs-Snackbar erscheint (z.B. „Botanische Familie erfolgreich gespeichert")
- Der angezeigte Wert für Nährstoffbedarf zeigt nun „Hoch" / „Starkzehrer"

**Postconditions**:
- Datensatz „Solanaceae" hat Nährstoffbedarf „Hoch" in der Datenbank

**Tags**: [nfr-010, edit, speichern, snackbar, botanicalfamily, happy-path]

---

### TC-NFR010-023: UnsavedChangesGuard — Warnung bei Navigation mit ungespeicherten Änderungen

**Zusammenfassung**: Nutzer hat Änderungen im Edit-Formular und klickt auf Navigation — eine Warnung erscheint.

**Requirement**: NFR-010 §2.4 (UnsavedChangesGuard)
**Priority**: Critical
**Category**: Zustandswechsel / Navigation
**Preconditions**:
- Nutzer ist im Edit-Formular für ein Substrat
- Nutzer hat den pH-Wert geändert (dirty state aktiv)
- Test-URL: `/standorte/substrates/{key}`

**Test Steps**:
1. Nutzer ändert den pH-Wert im Edit-Formular
2. Nutzer klickt auf einen Breadcrumb-Link (Navigation weg von der Seite)

**Expected Results**:
- Ein Bestätigungsdialog erscheint: „Sie haben ungespeicherte Änderungen. Möchten Sie die Seite wirklich verlassen?"
- Zwei Buttons sind sichtbar: „Abbrechen" und „Verlassen" (oder ähnliche Beschriftung)

**Test Steps (Fortsetzung)**:
3. Nutzer klickt „Abbrechen"

**Expected Results (Fortsetzung)**:
- Dialog schließt sich
- Nutzer bleibt auf der Edit-Seite mit den ungespeicherten Änderungen

**Test Steps (Fortsetzung)**:
4. Nutzer klickt erneut auf den Breadcrumb-Link
5. Nutzer klickt „Verlassen"

**Expected Results (Fortsetzung)**:
- Browser navigiert zur Zielseite (Breadcrumb-Ziel)
- Änderungen sind verworfen

**Postconditions**:
- Keine Datenveränderung (Änderungen wurden verworfen)

**Tags**: [nfr-010, unsavedchangesguard, navigation, warnung, substrat, standorte]

---

### TC-NFR010-024: Edit-Formular — Gleiche Validierungsregeln wie Create

**Zusammenfassung**: Die Validierungsregeln im Edit-Formular sind identisch mit dem Create-Dialog (Zod-Schema).

**Requirement**: NFR-010 §2.4 (Gleiche Validierungsregeln wie beim Create)
**Priority**: High
**Category**: Formvalidierung
**Preconditions**:
- Nutzer ist im Edit-Formular für BotanicalFamily „Solanaceae"

**Test Steps**:
1. Nutzer löscht den Inhalt des Feldes „Name" (`data-testid="form-field-name"`) vollständig
2. Nutzer gibt „Solanum" (ohne „-aceae"-Endung) ein
3. Nutzer verlässt das Feld

**Expected Results**:
- Fehlermeldung erscheint direkt unter dem Feld: „Muss auf '-aceae' enden"
- Speichern-Button ist deaktiviert

**Postconditions**:
- Keine Datenveränderung

**Tags**: [nfr-010, edit, formvalidierung, zod, botanicalfamily]

---

## Gruppe F: Delete mit Bestätigung

### TC-NFR010-025: Delete — ConfirmDialog zeigt Namen der zu löschenden Entität

**Zusammenfassung**: Nutzer klickt „Löschen", ConfirmDialog öffnet sich mit dem Namen der Entität und rotem Bestätigungs-Button.

**Requirement**: NFR-010 §2.5
**Priority**: Critical
**Category**: Dialog / Delete
**Preconditions**:
- Nutzer ist angemeldet
- Nutzer befindet sich auf der Detail-Seite von BotanicalFamily „Testaceae"
- „Testaceae" wird von keiner Species referenziert

**Test Steps**:
1. Nutzer klickt den „Löschen"-Button in der Aktionsleiste

**Expected Results**:
- `data-testid="confirm-dialog"` öffnet sich
- Dialog zeigt den Namen der zu löschenden Entität: „Testaceae" ist im Bestätigungstext sichtbar
- Der Text lautet sinngemäß: „Sind Sie sicher, dass Sie „Testaceae" löschen möchten? Diese Aktion kann nicht rückgängig gemacht werden."
- `data-testid="confirm-dialog-confirm"` (Bestätigungs-Button) ist rot eingefärbt (`destructive={true}`)
- `data-testid="confirm-dialog-cancel"` (Abbrechen-Button) ist sichtbar

**Postconditions**:
- Keine Datenveränderung (Dialog noch nicht bestätigt)

**Tags**: [nfr-010, delete, confirmdialog, destructive, botanicalfamily]

---

### TC-NFR010-026: Delete — Erfolgreiches Löschen mit Rückkehr zur Liste

**Zusammenfassung**: Nutzer bestätigt die Löschung und wird zur Liste zurückgeleitet mit Erfolgsbenachrichtigung.

**Requirement**: NFR-010 §2.5
**Priority**: Critical
**Category**: Happy Path / Delete
**Preconditions**:
- ConfirmDialog für „Testaceae" ist geöffnet (Folge von TC-NFR010-025)
- „Testaceae" wird von keiner Species referenziert

**Test Steps**:
1. Nutzer klickt `data-testid="confirm-dialog-confirm"` (roter Bestätigungs-Button)

**Expected Results**:
- Während des API-Calls: Bestätigungs-Button zeigt Ladeindikator (`loading`-Prop auf ConfirmDialog)
- Nach erfolgreicher Löschung: Dialog schließt sich
- Browser navigiert zurück zur Listenansicht `/stammdaten/botanical-families`
- Erfolgs-Snackbar erscheint: „Botanische Familie erfolgreich gelöscht"
- Eintrag „Testaceae" ist nicht mehr in der Tabelle vorhanden

**Postconditions**:
- Datensatz „Testaceae" ist aus der Datenbank entfernt

**Tags**: [nfr-010, delete, erfolg, rückkehr-liste, snackbar, botanicalfamily, happy-path]

---

### TC-NFR010-027: Delete — Abbrechen schließt Dialog ohne Löschung

**Zusammenfassung**: Nutzer öffnet den Löschen-Dialog und klickt Abbrechen — keine Daten werden gelöscht.

**Requirement**: NFR-010 §2.5
**Priority**: High
**Category**: Dialog
**Preconditions**:
- ConfirmDialog für eine BotanicalFamily ist geöffnet

**Test Steps**:
1. Nutzer klickt `data-testid="confirm-dialog-cancel"`

**Expected Results**:
- Dialog schließt sich
- Nutzer bleibt auf der Detail-Seite
- Keine Snackbar-Meldung erscheint
- Datensatz ist weiterhin vorhanden

**Postconditions**:
- Keine Datenveränderung

**Tags**: [nfr-010, delete, abbrechen, confirmdialog, botanicalfamily]

---

### TC-NFR010-028: Delete — Fehlermeldung bei referenzieller Integrität (HTTP 409)

**Zusammenfassung**: Nutzer versucht eine BotanicalFamily zu löschen, die von einer Species referenziert wird — Fehlermeldung erscheint.

**Requirement**: NFR-010 §2.5, §7 Szenario 5 (Referenzielle Integrität)
**Priority**: High
**Category**: Fehlermeldung / Delete
**Preconditions**:
- Nutzer ist angemeldet
- BotanicalFamily „Solanaceae" existiert und wird von mindestens einer Species referenziert
- Nutzer befindet sich auf der Detail-Seite von „Solanaceae"

**Test Steps**:
1. Nutzer klickt „Löschen"-Button
2. Nutzer bestätigt mit `data-testid="confirm-dialog-confirm"`

**Expected Results**:
- API gibt einen Fehler zurück (Konflikt wegen referenzieller Integrität)
- Fehlermeldung erscheint (Snackbar oder inline im Dialog), sinngemäß: „'Solanaceae' kann nicht gelöscht werden, da sie von Pflanzenarten referenziert wird."
- ConfirmDialog bleibt geöffnet (oder schließt sich mit Fehlermeldung)
- Datensatz „Solanaceae" ist weiterhin in der Liste vorhanden

**Postconditions**:
- Keine Datenveränderung

**Tags**: [nfr-010, delete, fehlermeldung, referenzielle-integritaet, nfr-006, botanicalfamily]

---

## Gruppe G: Vollständiger CRUD-Zyklus (NFR-010 §7 Szenario 1)

### TC-NFR010-029: Vollständiger CRUD-Zyklus für BotanicalFamily

**Zusammenfassung**: End-to-End-Test des vollständigen Create → Read → Update → Delete-Zyklus für BotanicalFamily gemäß NFR-010 §7 Szenario 1.

**Requirement**: NFR-010 §7 Szenario 1
**Priority**: Critical
**Category**: Happy Path / End-to-End
**Preconditions**:
- Nutzer ist angemeldet
- Kein Eintrag „Zyklustestaceae" vorhanden

**Test Steps**:
1. Nutzer navigiert zu `/stammdaten/botanical-families`
2. Nutzer klickt „Hinzufügen"
3. Nutzer füllt aus: Name=„Zyklustestaceae", Nährstoffbedarf=„Mittel", Wuchsformen=[„Kraut"], Bestäubungstyp=[„Insekten"]
4. Nutzer klickt „Speichern"

**Expected Results nach Schritt 4**:
- Erfolgs-Snackbar erscheint
- „Zyklustestaceae" ist in der Liste sichtbar

**Test Steps (Fortsetzung)**:
5. Nutzer klickt auf Zeile „Zyklustestaceae" in der Tabelle
6. Nutzer beobachtet Detail-Ansicht

**Expected Results nach Schritt 6**:
- Alle eingegebenen Felder sind korrekt angezeigt
- Breadcrumb zeigt korrekten Pfad

**Test Steps (Fortsetzung)**:
7. Nutzer klickt „Bearbeiten"
8. Nutzer ändert Nährstoffbedarf auf „Hoch (Starkzehrer)"
9. Nutzer klickt „Speichern"

**Expected Results nach Schritt 9**:
- Erfolgs-Snackbar erscheint
- Detailansicht zeigt neuen Wert „Hoch"

**Test Steps (Fortsetzung)**:
10. Nutzer klickt „Löschen"
11. Dialog zeigt „Zyklustestaceae" im Bestätigungstext
12. Nutzer bestätigt Löschung

**Expected Results nach Schritt 12**:
- Nutzer wird zur Listenansicht weitergeleitet
- Erfolgs-Snackbar erscheint
- „Zyklustestaceae" ist nicht mehr in der Liste

**Postconditions**:
- Datensatz „Zyklustestaceae" ist vollständig entfernt

**Tags**: [nfr-010, crud-zyklus, e2e, botanicalfamily, happy-path, szenario-1]

---

## Gruppe H: Eingebettete Entitäten (NFR-010 §5)

### TC-NFR010-030: Cultivar in Species-Detail — Vollständiger CRUD-Zyklus (NFR-010 §7 Szenario 2)

**Zusammenfassung**: Eingebettete Entität Cultivar bietet in der Species-Detail-Section vollständigen CRUD via Dialoge.

**Requirement**: NFR-010 §5, §7 Szenario 2
**Priority**: Critical
**Category**: Happy Path / Eingebettete Entität
**Preconditions**:
- Nutzer ist angemeldet
- Species „Solanum lycopersicum" (Tomate) existiert
- Nutzer befindet sich auf der Detail-Seite der Species

**Test Steps**:
1. Nutzer navigiert zu `/stammdaten/species/{tomato-key}`
2. Nutzer scrollt zur „Sorten"-Section (CultivarListSection)
3. Nutzer klickt „Sorte hinzufügen" in der Section

**Expected Results**:
- Create-Dialog für Cultivar öffnet sich (Modal)
- Einleitungstext erklärt, was eine Sorte ist

**Test Steps (Fortsetzung)**:
4. Nutzer gibt Name=„Cherry Roma" ein und füllt Pflichtfelder aus
5. Nutzer klickt „Speichern"

**Expected Results nach Schritt 5**:
- Dialog schließt sich
- Erfolgs-Snackbar erscheint
- „Cherry Roma" erscheint in der CultivarListSection-Tabelle

**Test Steps (Fortsetzung)**:
6. Nutzer klickt auf „Cherry Roma" in der Section-Tabelle

**Expected Results nach Schritt 6**:
- Detail-Dialog oder Inline-Anzeige zeigt alle Felder der Sorte

**Test Steps (Fortsetzung)**:
7. Nutzer klickt „Bearbeiten" (Edit-Dialog öffnet sich)
8. Nutzer ändert einen Wert (z.B. Tage bis Reife)
9. Nutzer klickt „Speichern"

**Expected Results nach Schritt 9**:
- Erfolgs-Snackbar erscheint
- Aktualisierter Wert ist in der Section sichtbar

**Test Steps (Fortsetzung)**:
10. Nutzer klickt „Löschen" für „Cherry Roma"
11. ConfirmDialog erscheint mit Namen „Cherry Roma"
12. Nutzer bestätigt

**Expected Results nach Schritt 12**:
- „Cherry Roma" ist aus der CultivarListSection entfernt
- Erfolgs-Snackbar erscheint
- Nutzer bleibt auf der Species-Detail-Seite (keine separate Navigation)

**Postconditions**:
- Cultivar „Cherry Roma" ist gelöscht

**Tags**: [nfr-010, eingebettete-entitaet, cultivar, species, crud-zyklus, szenario-2]

---

### TC-NFR010-031: GrowthPhase in PlantInstance-Detail — Create und Delete

**Zusammenfassung**: Eingebettete GrowthPhase-Entität in PlantInstance-Detail bietet Create und Delete via Dialoge.

**Requirement**: NFR-010 §5.2, §5.3
**Priority**: High
**Category**: Eingebettete Entität
**Preconditions**:
- Nutzer ist angemeldet
- PlantInstance mit einer Species existiert
- Nutzer befindet sich auf der Detail-Seite der PlantInstance

**Test Steps**:
1. Nutzer scrollt zur „Wachstumsphasen"-Section (GrowthPhaseListSection)
2. Nutzer klickt „Phase hinzufügen"

**Expected Results**:
- Create-Dialog für GrowthPhase öffnet sich
- Pflichtfelder sind gekennzeichnet

**Test Steps (Fortsetzung)**:
3. Nutzer gibt einen Phasennamen ein und füllt Pflichtfelder aus
4. Nutzer klickt „Speichern"

**Expected Results**:
- Neue Phase erscheint in der GrowthPhase-Tabelle innerhalb der Section
- Erfolgs-Snackbar erscheint

**Test Steps (Fortsetzung)**:
5. Nutzer klickt „Löschen" für die neue Phase
6. ConfirmDialog öffnet sich
7. Nutzer bestätigt Löschung

**Expected Results**:
- Phase wird aus der Section entfernt
- Nutzer bleibt auf der PlantInstance-Detail-Seite

**Postconditions**:
- Die neu erstellte Phase ist gelöscht

**Tags**: [nfr-010, eingebettete-entitaet, growthphase, plantinstance, crud]

---

### TC-NFR010-032: Location in Site-Detail — CRUD via Section (LocationListSection)

**Zusammenfassung**: Eingebettete Location-Entität in SiteDetailPage bietet vollständigen CRUD über die LocationListSection.

**Requirement**: NFR-010 §5.2
**Priority**: High
**Category**: Eingebettete Entität
**Preconditions**:
- Nutzer ist angemeldet
- Site „Gewächshaus West" existiert
- Nutzer befindet sich auf der Detail-Seite der Site

**Test Steps**:
1. Nutzer scrollt zur „Standorte"-Section (LocationListSection) in der Site-Detail-Seite
2. Nutzer klickt „Standort hinzufügen"
3. Nutzer füllt Name und Pflichtfelder aus
4. Nutzer klickt „Speichern"

**Expected Results**:
- Neuer Standort erscheint in der LocationListSection
- Erfolgs-Snackbar erscheint

**Test Steps (Fortsetzung)**:
5. Nutzer klickt auf den neuen Standort-Eintrag in der Section
6. Browser navigiert zur LocationDetailPage (`/standorte/locations/{key}`)

**Expected Results**:
- LocationDetailPage wird angezeigt mit Breadcrumb: „Standorte > Gewächshaus West > {Standortname}"

**Postconditions**:
- Neuer Location-Datensatz ist vorhanden

**Tags**: [nfr-010, eingebettete-entitaet, location, site, standorte, crud]

---

## Gruppe I: Konsistenz der Shared-Komponenten (NFR-010 §6.1)

### TC-NFR010-033: Einheitliche FormActions — Button-Reihenfolge in allen Formularen

**Zusammenfassung**: In allen Create- und Edit-Formularen befindet sich der primäre Aktions-Button rechts und Abbrechen links.

**Requirement**: NFR-010 §6.1 (Button-Platzierung)
**Priority**: Medium
**Category**: Konsistenz / UI-Pattern
**Preconditions**:
- Nutzer ist angemeldet

**Test Steps**:
1. Nutzer öffnet Create-Dialog für BotanicalFamily
2. Nutzer beobachtet Anordnung der Buttons in der FormActions-Leiste
3. Nutzer schließt den Dialog und öffnet Edit-Formular für eine Species
4. Nutzer beobachtet erneut die Button-Anordnung

**Expected Results**:
- In beiden Formularen: „Abbrechen" (`data-testid="form-cancel-button"`) befindet sich links
- In beiden Formularen: „Speichern" (`data-testid="form-submit-button"`) befindet sich rechts
- Muster ist konsistent zwischen Create-Dialog (Modal) und Edit-Seite

**Postconditions**:
- Keine Datenveränderung

**Tags**: [nfr-010, konsistenz, formactions, button-reihenfolge]

---

### TC-NFR010-034: Einheitliche Validierungsdarstellung — Fehlermeldungen unter dem Feld

**Zusammenfassung**: In allen Formularen erscheinen Validierungsfehler direkt unter dem betroffenen Feld, rot eingefärbt.

**Requirement**: NFR-010 §6.1 (Fehlermeldungen unter dem Feld, rot eingefärbt)
**Priority**: High
**Category**: Konsistenz / Formvalidierung
**Preconditions**:
- Nutzer ist angemeldet
- Create-Dialog für Substrate ist geöffnet (URL: `/standorte/substrates`)

**Test Steps**:
1. Nutzer lässt den Pflichtfeld „Name" leer
2. Nutzer klickt auf „Speichern"

**Expected Results**:
- Fehlermeldung erscheint direkt unterhalb von `data-testid="form-field-name"` (als helperText des MUI TextField)
- Text ist rot eingefärbt (MUI error color)
- Kein Popup, kein Toast — nur Inline-Fehlermeldung

**Postconditions**:
- Keine Datenveränderung

**Tags**: [nfr-010, konsistenz, formvalidierung, helpertext, fehlermeldung, substrat]

---

### TC-NFR010-035: Numerische Felder akzeptieren Dezimalwerte

**Zusammenfassung**: Numerische Felder (pH, EC) akzeptieren beliebige Dezimalwerte ohne Einschränkung durch step=1.

**Requirement**: NFR-010 §6.1 (FormNumberField — step="any" als Default)
**Priority**: High
**Category**: Formvalidierung / Konsistenz
**Preconditions**:
- Nutzer ist angemeldet
- Create- oder Edit-Formular für BotanicalFamily ist geöffnet (enthält pH-Felder)

**Test Steps**:
1. Nutzer navigiert zum Feld „Boden-pH min" (`data-testid="form-field-soil_ph_min"`)
2. Nutzer gibt den Wert „6.2" ein
3. Nutzer verlässt das Feld

**Expected Results**:
- Kein Validierungsfehler für den Wert „6.2" (Dezimaltrennzeichen wird akzeptiert)
- Feld zeigt den Wert „6.2" korrekt an

**Test Steps (Fortsetzung)**:
4. Nutzer gibt den Wert „2.9" ein (unterhalb des Minimums von 3.0)

**Expected Results (Fortsetzung)**:
- Fehlermeldung erscheint (Wert muss zwischen 3 und 9 liegen)
- Pfeiltasten-Navigation im Feld macht sinnvolle Schritte (kein Sprung um 1.0 auf Feldern die Dezimalwerte erwarten)

**Postconditions**:
- Keine Datenveränderung

**Tags**: [nfr-010, numerische-felder, dezimalwerte, step-any, formnumberfield, botanicalfamily]

---

### TC-NFR010-036: Erfolgs-Snackbar erscheint unten-mittig und blendet sich automatisch aus

**Zusammenfassung**: Nach jeder erfolgreichen Aktion (Create/Update/Delete) erscheint die Snackbar unten mittig und verschwindet automatisch.

**Requirement**: NFR-010 §6.1 (Erfolgsmeldungen als Snackbar, unten-mittig, automatisch ausblendend)
**Priority**: Medium
**Category**: Konsistenz / Feedback
**Preconditions**:
- Nutzer ist angemeldet
- Create-Dialog für eine neue BotanicalFamily wurde erfolgreich gespeichert

**Test Steps**:
1. Nutzer erstellt eine neue BotanicalFamily (Pflichtfelder ausgefüllt, Speichern geklickt)
2. Nutzer beobachtet die Snackbar

**Expected Results**:
- Snackbar erscheint in der unteren Mitte des Bildschirms (nicht oben, nicht in einer Ecke)
- Snackbar zeigt grüne/erfolg-farbige Hintergrundfarbe
- Snackbar blendet sich nach 3–6 Sekunden automatisch aus (kein manuelles Schließen erforderlich)

**Postconditions**:
- Neuer Datensatz ist erstellt

**Tags**: [nfr-010, snackbar, konsistenz, feedback, position]

---

## Gruppe J: Responsivität und Barrierefreiheit (NFR-010 §6.2/§6.3)

### TC-NFR010-037: Alle Masken und Listen sind auf Desktop vollständig nutzbar (≥1024px)

**Zusammenfassung**: Auf einem Desktop-Viewport (≥1024px) sind alle CRUD-Operationen für BotanicalFamily vollständig zugänglich.

**Requirement**: NFR-010 §6.2 (Desktop-Pflicht ≥1024px)
**Priority**: High
**Category**: Responsivität
**Preconditions**:
- Browser-Viewport ist auf 1280px × 800px gesetzt
- Nutzer ist angemeldet

**Test Steps**:
1. Nutzer navigiert zu `/stammdaten/botanical-families`
2. Nutzer prüft: Sind alle Tabellenspalten sichtbar?
3. Nutzer öffnet Create-Dialog
4. Nutzer prüft: Sind alle Formularfelder zugänglich und ohne horizontales Scrolling?
5. Nutzer navigiert zur Detail-Seite
6. Nutzer prüft: Sind Breadcrumb und Aktionsleiste vollständig sichtbar?

**Expected Results**:
- Alle Tabellenspalten sind auf 1280px Viewport sichtbar
- Create-Dialog ist vollständig ohne Scrolling nutzbar (oder mit vernünftigem internem Scroll)
- Breadcrumb und alle Action-Buttons sind ohne horizontales Scrolling erreichbar
- Kein UI-Element ist abgeschnitten oder überlappt

**Postconditions**:
- Keine Datenveränderung

**Tags**: [nfr-010, responsivitaet, desktop, 1280px, botanicalfamily]

---

### TC-NFR010-038: Tablet-Spaltenprioritäten — weniger wichtige Spalten werden ausgeblendet (≤1024px)

**Zusammenfassung**: Auf Tablet-Viewport (≤1024px) werden über `hideBelowBreakpoint="md"` definierte Spalten automatisch ausgeblendet.

**Requirement**: NFR-010 §3.3c
**Priority**: Medium
**Category**: Responsivität / Tablet
**Preconditions**:
- Browser-Viewport ist auf 900px × 768px gesetzt (Tablet-Breite)
- Nutzer ist angemeldet
- Entität mit definierten `hideBelowBreakpoint="md"`-Spalten: z.B. PestListPage (`/t/{slug}/pflanzenschutz/pests`)

**Test Steps**:
1. Nutzer öffnet die PestListPage im 900px-Viewport
2. Nutzer beobachtet welche Spalten sichtbar sind

**Expected Results**:
- Maximal 3–4 Primärspalten sind sichtbar (z.B. Name, Typ)
- Sekundärspalten mit `hideBelowBreakpoint="md"` (z.B. Lebenszyklus-Tage, Erkennungsschwierigkeit) sind ausgeblendet
- Die primären Spalten sind lesbar und nicht gequetscht
- Mobile-Card-Ansicht ist optional aktiv (falls `mobileBreakpoint="sm"` und Viewport unter 600px)

**Postconditions**:
- Keine Datenveränderung

**Tags**: [nfr-010, tablet, responsivitaet, spaltenpriorität, hideBelowBreakpoint, pflanzenschutz]

---

### TC-NFR010-039: Barrierefreiheit — Fokus-Management bei Dialog-Öffnung und -Schließung

**Requirement**: NFR-010 §6.3
**Priority**: High
**Category**: Barrierefreiheit / Dialog
**Preconditions**:
- Nutzer ist angemeldet
- BotanicalFamily-Listenansicht ist geöffnet
- Nutzer verwendet Tastaturnavigation (Tab)

**Test Steps**:
1. Nutzer navigiert mit Tab zur Schaltfläche „Hinzufügen"
2. Nutzer drückt Enter (Dialog öffnet sich)
3. Nutzer beobachtet, wo der Fokus liegt

**Expected Results**:
- Dialog öffnet sich
- Fokus ist automatisch auf dem ersten Formularfeld (z.B. Name-Eingabefeld)
- Nutzer kann mit Tab durch alle Formularfelder navigieren

**Test Steps (Fortsetzung)**:
4. Nutzer drückt Escape oder Tab/Enter zu „Abbrechen"
5. Nutzer bestätigt Schließen

**Expected Results (Fortsetzung)**:
- Dialog schließt sich
- Fokus kehrt zum auslösenden Element zurück (Hinzufügen-Button)

**Postconditions**:
- Keine Datenveränderung

**Tags**: [nfr-010, barrierefreiheit, fokus-management, dialog, tastaturnavigation]

---

### TC-NFR010-040: Barrierefreiheit — data-testid-Attribute auf interaktiven Elementen

**Zusammenfassung**: Alle interaktiven Elemente in Formularen und Tabellen haben `data-testid`-Attribute für Testbarkeit.

**Requirement**: NFR-010 §6.3 (`data-testid`-Attribute auf allen interaktiven Elementen)
**Priority**: Medium
**Category**: Barrierefreiheit / Testbarkeit
**Preconditions**:
- Browser DevTools sind geöffnet
- Nutzer ist auf der BotanicalFamily-Listenansicht

**Test Steps**:
1. Nutzer öffnet DevTools und inspiziert die DataTable-Komponente
2. Nutzer inspiziert das Suchfeld
3. Nutzer öffnet Create-Dialog und inspiziert die Formularfelder

**Expected Results**:
- `data-testid="data-table"` ist auf der Tabelle vorhanden
- `data-testid="table-search-input"` ist auf dem Suchfeld vorhanden
- `data-testid="data-table-row"` ist auf jeder Zeile vorhanden
- `data-testid="form-field-name"` ist auf dem Name-Eingabefeld vorhanden
- `data-testid="form-submit-button"` ist auf dem Speichern-Button vorhanden
- `data-testid="form-cancel-button"` ist auf dem Abbrechen-Button vorhanden

**Postconditions**:
- Keine Datenveränderung

**Tags**: [nfr-010, barrierefreiheit, data-testid, testbarkeit, selenium, datatable]

---

## Gruppe K: Vollständigkeitsmatrix — Fehlende Operationen (NFR-010 §4.2)

### TC-NFR010-041: BotanicalFamily — Edit-Funktion ist implementiert (fehlend in Ist-Zustand)

**Zusammenfassung**: Die BotanicalFamily-Detail-Seite verfügt über ein vollständig funktionsfähiges Edit-Formular (war in §4.1 als fehlend markiert).

**Requirement**: NFR-010 §4.2 (BotanicalFamily: Update als fehlende Operation)
**Priority**: Critical
**Category**: Vollständigkeitsmatrix / Happy Path
**Preconditions**:
- Nutzer ist angemeldet
- BotanicalFamily „Solanaceae" existiert
- Test-URL: `/stammdaten/botanical-families/{solanaceae-key}`

**Test Steps**:
1. Nutzer navigiert zur Detail-Seite von „Solanaceae"
2. Nutzer prüft die Aktionsleiste auf einen „Bearbeiten"-Button

**Expected Results**:
- Ein „Bearbeiten"-Button ist sichtbar (die Funktion ist implementiert)
- Klick auf „Bearbeiten" öffnet ein Edit-Formular mit vorausgefüllten Werten
- Das Formular ermöglicht das Ändern aller Felder

**Tags**: [nfr-010, vollständigkeitsmatrix, botanicalfamily, edit, fehlende-operation]

---

### TC-NFR010-042: Cultivar — Read (Detail-Ansicht) ist implementiert

**Zusammenfassung**: Cultivar-Einträge in der Species-Detail-Seite bieten eine Detail-Anzeige (war in §4.1 als fehlend markiert).

**Requirement**: NFR-010 §4.2 (Cultivar: Read als fehlende Operation)
**Priority**: Critical
**Category**: Vollständigkeitsmatrix / Detailansicht
**Preconditions**:
- Nutzer ist angemeldet
- Species mit mindestens einem Cultivar existiert
- Nutzer ist auf der Species-Detail-Seite

**Test Steps**:
1. Nutzer scrollt zur „Sorten"-Section
2. Nutzer klickt auf einen Cultivar-Eintrag in der Section-Tabelle

**Expected Results**:
- Detail-Ansicht des Cultivars öffnet sich (Detail-Dialog, Inline-Anzeige oder Navigation zu `/stammdaten/species/{key}/cultivars/{cultivarKey}`)
- Alle Felder des Cultivars sind sichtbar (Name, Tage bis Reife etc.)

**Tags**: [nfr-010, vollständigkeitsmatrix, cultivar, read, eingebettete-entitaet]

---

### TC-NFR010-043: Cultivar — Edit-Funktion ist implementiert

**Zusammenfassung**: Cultivar-Einträge in der Species-Detail-Section bieten eine Edit-Funktion (war in §4.1 als fehlend markiert).

**Requirement**: NFR-010 §4.2 (Cultivar: Update als fehlende Operation)
**Priority**: Critical
**Category**: Vollständigkeitsmatrix / Edit
**Preconditions**:
- Nutzer ist angemeldet
- Cultivar ist in der Species-Detail-Seite sichtbar

**Test Steps**:
1. Nutzer klickt auf einen Cultivar in der Section
2. Nutzer klickt auf „Bearbeiten" in der Cultivar-Anzeige

**Expected Results**:
- Edit-Dialog öffnet sich mit vorausgefüllten Cultivar-Werten
- Nutzer kann Felder ändern und speichern
- Nach Speichern erscheint Erfolgs-Snackbar

**Tags**: [nfr-010, vollständigkeitsmatrix, cultivar, edit, fehlende-operation]

---

### TC-NFR010-044: Slot — Edit und Delete sind implementiert

**Zusammenfassung**: Slot-Einträge in der Location-Detail-Seite bieten Edit- und Delete-Funktion (beide in §4.1 als fehlend markiert).

**Requirement**: NFR-010 §4.2 (Slot: Update und Delete als fehlende Operationen)
**Priority**: Critical
**Category**: Vollständigkeitsmatrix
**Preconditions**:
- Nutzer ist angemeldet
- Location mit mindestens einem Slot existiert
- Nutzer ist auf der Location-Detail-Seite (`/standorte/locations/{key}`)

**Test Steps**:
1. Nutzer scrollt zur Slot-Section
2. Nutzer klickt auf einen Slot-Eintrag

**Expected Results (Edit)**:
- Ein „Bearbeiten"-Button oder Edit-Icon ist sichtbar
- Klick öffnet Edit-Dialog mit vorausgefüllten Werten
- Speichern aktualisiert den Slot

**Expected Results (Delete)**:
- Ein „Löschen"-Button oder Delete-Icon ist sichtbar
- Klick öffnet ConfirmDialog
- Bestätigung löscht den Slot aus der Section

**Tags**: [nfr-010, vollständigkeitsmatrix, slot, edit, delete, fehlende-operation, location]

---

### TC-NFR010-045: Substrate — Edit und Delete sind implementiert

**Zusammenfassung**: Substrate-Einträge haben Edit- und Delete-Funktion (beide in §4.1 als fehlend markiert).

**Requirement**: NFR-010 §4.2 (Substrate: Update und Delete als fehlende Operationen)
**Priority**: Critical
**Category**: Vollständigkeitsmatrix
**Preconditions**:
- Nutzer ist angemeldet
- Mindestens ein Substrate-Eintrag existiert
- Nutzer ist auf der Substrate-Detail-Seite (`/standorte/substrates/{key}`)

**Test Steps**:
1. Nutzer navigiert zur Substrate-Detail-Seite
2. Nutzer prüft die Aktionsleiste auf „Bearbeiten"- und „Löschen"-Buttons

**Expected Results**:
- „Bearbeiten"-Button öffnet Edit-Formular mit vorausgefüllten Werten
- „Löschen"-Button öffnet ConfirmDialog
- Beide Funktionen sind vollständig implementiert

**Tags**: [nfr-010, vollständigkeitsmatrix, substrat, edit, delete, fehlende-operation]

---

### TC-NFR010-046: Batch — List-Ansicht ist implementiert

**Zusammenfassung**: Batch-Einträge haben eine Listenansicht (war in §4.1 als fehlend markiert — Liste und Update und Delete fehlen).

**Requirement**: NFR-010 §4.2 (Batch: List/Update/Delete als fehlende Operationen)
**Priority**: Critical
**Category**: Vollständigkeitsmatrix / Listenansicht
**Preconditions**:
- Nutzer ist angemeldet
- Substrate mit mindestens einem Batch existiert

**Test Steps**:
1. Nutzer navigiert zur Substrate-Detail-Seite (`/standorte/substrates/{key}`)
2. Nutzer scrollt zur Batch-Section oder navigiert zur Batch-Listenansicht

**Expected Results**:
- Eine Tabellen-/Listenansicht für Batches ist vorhanden
- Batches sind aufgelistet
- Ein „Hinzufügen"-Button für neue Batches ist sichtbar

**Tags**: [nfr-010, vollständigkeitsmatrix, batch, listenansicht, substrat, fehlende-operation]

---

### TC-NFR010-047: PlantInstance — Edit-Funktion ist implementiert

**Zusammenfassung**: PlantInstance-Einträge haben eine Edit-Funktion (war in §4.1 als fehlend markiert).

**Requirement**: NFR-010 §4.2 (PlantInstance: Update als fehlende Operation)
**Priority**: Critical
**Category**: Vollständigkeitsmatrix / Edit
**Preconditions**:
- Nutzer ist angemeldet
- Mindestens eine PlantInstance existiert
- Nutzer ist auf der PlantInstance-Detail-Seite

**Test Steps**:
1. Nutzer navigiert zur PlantInstance-Detail-Seite
2. Nutzer prüft Aktionsleiste auf „Bearbeiten"-Button

**Expected Results**:
- „Bearbeiten"-Button öffnet Edit-Formular mit vorausgefüllten Werten
- Formular enthält UnsavedChangesGuard

**Tags**: [nfr-010, vollständigkeitsmatrix, plantinstance, edit, fehlende-operation]

---

### TC-NFR010-048: GrowthPhase — Delete-Funktion ist implementiert

**Zusammenfassung**: GrowthPhase-Einträge in der PlantInstance-Section haben eine Delete-Funktion (war in §4.1 als fehlend markiert).

**Requirement**: NFR-010 §4.2 (GrowthPhase: Delete als fehlende Operation)
**Priority**: Critical
**Category**: Vollständigkeitsmatrix / Delete
**Preconditions**:
- Nutzer ist angemeldet
- PlantInstance mit mindestens einer GrowthPhase existiert
- Nutzer ist auf der PlantInstance-Detail-Seite

**Test Steps**:
1. Nutzer scrollt zur GrowthPhase-Section
2. Nutzer klickt auf Delete-Icon einer Phase
3. ConfirmDialog öffnet sich
4. Nutzer bestätigt

**Expected Results**:
- ConfirmDialog zeigt Phasennamen
- Phase wird aus der Section entfernt
- Erfolgs-Snackbar erscheint

**Tags**: [nfr-010, vollständigkeitsmatrix, growthphase, delete, fehlende-operation, plantinstance]

---

## Gruppe L: Einleitungstexte (NFR-010 §2.2, §2.4, §3.1)

### TC-NFR010-049: Alle Listenansichten haben Einleitungstext

**Zusammenfassung**: Überprüfung, dass alle getesteten Listenansichten einen Einleitungstext unterhalb des Seitentitels aufweisen.

**Requirement**: NFR-010 §3.1 (Einleitungstext als Pflicht)
**Priority**: High
**Category**: Konsistenz / Einleitungstext
**Preconditions**:
- Nutzer ist angemeldet

**Test Steps**:
1. Nutzer navigiert zu `/stammdaten/botanical-families`
2. Nutzer beobachtet Bereich unterhalb des Seitentitels
3. Nutzer wiederholt für: `/stammdaten/species`, `/standorte/substrates`, `/standorte/sites`, `/pflanzen`

**Expected Results**:
- Auf allen 5 Listenseiten erscheint ein Einleitungstext (1–2 Sätze) unterhalb des Seitentitels
- Text erklärt in einfacher Sprache, welche Datensätze die Liste enthält und wofür sie verwendet werden
- Text ist auf Deutsch (Standard-Sprache)

**Tags**: [nfr-010, einleitungstext, listenansicht, konsistenz, i18n]

---

### TC-NFR010-050: Alle Create-Dialoge haben Einleitungstext

**Zusammenfassung**: Alle Create-Dialoge haben einen erklärenden Einleitungstext oberhalb des Formulars.

**Requirement**: NFR-010 §2.2 (Einleitungstext als MUSS)
**Priority**: High
**Category**: Konsistenz / Einleitungstext
**Preconditions**:
- Nutzer ist angemeldet

**Test Steps**:
1. Nutzer öffnet Create-Dialog für BotanicalFamily
2. Nutzer beobachtet Bereich oberhalb des ersten Formularfelds
3. Nutzer wiederholt für Create-Dialoge von: Species, Substrate, Site, Cultivar (in Species-Section)

**Expected Results**:
- Alle 5 Create-Dialoge haben einen Einleitungstext
- Text erklärt, was angelegt wird und welche Auswirkungen das Erstellen hat
- Text ist in einfacher Sprache ohne technischen Jargon

**Tags**: [nfr-010, einleitungstext, create-dialog, konsistenz]

---

### TC-NFR010-051: Alle Edit-Formulare haben Einleitungstext

**Zusammenfassung**: Alle Edit-Formulare haben einen erklärenden Einleitungstext oberhalb des Formulars.

**Requirement**: NFR-010 §2.4 (Einleitungstext als MUSS)
**Priority**: High
**Category**: Konsistenz / Einleitungstext
**Preconditions**:
- Nutzer ist angemeldet

**Test Steps**:
1. Nutzer öffnet Edit-Formular für eine BotanicalFamily
2. Nutzer beobachtet Bereich oberhalb des ersten Formularfelds
3. Nutzer wiederholt für: Species, Substrate, Site

**Expected Results**:
- Alle 4 Edit-Formulare haben einen Einleitungstext
- Text erklärt, welchen Datensatz der Nutzer bearbeitet und worauf er achten sollte
- Text nennt Konsequenzen von Änderungen (z.B. „Änderungen wirken sich auf alle zugeordneten Arten aus")

**Tags**: [nfr-010, einleitungstext, edit, konsistenz]

---

## Gruppe M: i18n — Internationale Darstellung

### TC-NFR010-052: Sprachenwechsel — Spaltenüberschriften und Enum-Werte wechseln auf Englisch

**Zusammenfassung**: Nach Wechsel zur englischen Sprache zeigen Listen und Formulare englische Beschriftungen.

**Requirement**: NFR-010 §3.1 (i18n-konforme Spaltenüberschriften), §6.1 (i18n DE/EN)
**Priority**: Medium
**Category**: i18n
**Preconditions**:
- Nutzer ist angemeldet
- Sprache ist auf Deutsch gesetzt

**Test Steps**:
1. Nutzer navigiert zu `/stammdaten/botanical-families`
2. Nutzer beobachtet Spaltenüberschriften (auf Deutsch)
3. Nutzer wechselt die Sprache auf Englisch (über Sprachumschalter in der Navigation oder Account-Einstellungen)

**Expected Results**:
- Spaltenüberschriften wechseln auf Englisch (z.B. „Name", „Common Name", „Nutrient Demand")
- Enum-Werte in Zellen wechseln auf Englisch (z.B. „heavy" statt „Hoch")
- Einleitungstext über der Tabelle ist auf Englisch
- Seitentitel ist auf Englisch

**Test Steps (Fortsetzung)**:
4. Nutzer öffnet Create-Dialog

**Expected Results (Fortsetzung)**:
- Feldlabels sind auf Englisch
- Fehlermeldungen bei Validierung sind auf Englisch

**Postconditions**:
- Sprache auf Deutsch zurücksetzen

**Tags**: [nfr-010, i18n, sprachenwechsel, englisch, botanicalfamily, enum-uebersetzung]

---

## Gruppe N: Spezifische Entitäten — Routen und CRUD-Vollständigkeit

### TC-NFR010-053: Species — Vollständigkeit aller CRUD-Operationen

**Zusammenfassung**: Species ist in §4.1 als vollständig markiert — Verifikation aller 5 CRUD-Operationen.

**Requirement**: NFR-010 §4.1 (Species: vollständig)
**Priority**: High
**Category**: Vollständigkeitsmatrix / Species
**Preconditions**:
- Nutzer ist angemeldet
- Species „Solanum lycopersicum" existiert

**Test Steps**:
1. Nutzer navigiert zu `/stammdaten/species`
2. Nutzer prüft: Listenansicht mit DataTable vorhanden?
3. Nutzer klickt „Hinzufügen" → Create-Dialog öffnet sich
4. Nutzer navigiert zur Species-Detail-Seite
5. Nutzer prüft: Detail-Ansicht zeigt alle Felder? Breadcrumb vorhanden?
6. Nutzer klickt „Bearbeiten" → Edit-Formular mit Vorausfüllung
7. Nutzer klickt „Löschen" → ConfirmDialog mit Species-Namen

**Expected Results**:
- Alle 5 CRUD-Operationen (List, Create, Read, Update, Delete) sind zugänglich und funktionsfähig
- Kein Schritt schlägt mit 404 oder fehlendem UI-Element fehl

**Tags**: [nfr-010, vollständigkeitsmatrix, species, crud, happy-path]

---

### TC-NFR010-054: Site — Vollständigkeit aller CRUD-Operationen

**Requirement**: NFR-010 §4.1 (Site: vollständig)
**Priority**: High
**Category**: Vollständigkeitsmatrix / Site
**Preconditions**:
- Nutzer ist angemeldet; Site „Gewächshaus West" existiert

**Test Steps**:
1. Nutzer navigiert zu `/standorte/sites`
2. Nutzer klickt auf Site-Eintrag → Detail-Seite mit Breadcrumb
3. Nutzer klickt „Bearbeiten" → Edit-Formular
4. Nutzer klickt „Löschen" → ConfirmDialog

**Expected Results**:
- Alle 5 CRUD-Operationen zugänglich und funktionsfähig

**Tags**: [nfr-010, vollständigkeitsmatrix, site, crud, standorte]

---

### TC-NFR010-055: Location — Vollständigkeit aller CRUD-Operationen (eingebettet in Site)

**Requirement**: NFR-010 §4.1/§4.2 (Location: vollständig, eingebettet in Site-Detail)
**Priority**: High
**Category**: Vollständigkeitsmatrix / Location
**Preconditions**:
- Nutzer ist angemeldet; Site mit Location existiert

**Test Steps**:
1. Nutzer öffnet Site-Detail-Seite
2. Nutzer prüft LocationListSection: Listenansicht vorhanden
3. Nutzer klickt „Standort hinzufügen" → Create-Dialog
4. Nutzer klickt auf Location-Eintrag → navigiert zu LocationDetailPage
5. Nutzer klickt „Bearbeiten" auf LocationDetailPage
6. Nutzer klickt „Löschen" → ConfirmDialog

**Expected Results**:
- Alle 5 CRUD-Operationen zugänglich

**Tags**: [nfr-010, vollständigkeitsmatrix, location, crud, site]

---

## Gruppe O: Hinweistexte (helperText) in Formularen

### TC-NFR010-056: Formularfelder zeigen Hinweistexte für fachlich komplexe Felder

**Zusammenfassung**: Formularfelder mit nicht-selbsterklärendem Zweck haben Hinweistexte (helperText) unterhalb des Feldes.

**Requirement**: NFR-010 §2.2 (Hinweistexte für Felder, die Erklärung benötigen)
**Priority**: Medium
**Category**: Konsistenz / Barrierefreiheit
**Preconditions**:
- Nutzer ist angemeldet
- Create-Dialog für BotanicalFamily ist geöffnet

**Test Steps**:
1. Nutzer beobachtet das Feld „Boden-pH min"
2. Nutzer beobachtet das Feld „Name" (mit aceae-Constraint)

**Expected Results**:
- Feld „Name" zeigt einen Hinweistext unterhalb: z.B. „Muss auf '-aceae' enden (z.B. Solanaceae)"
- Feld „Boden-pH min" zeigt einen Hinweistext: z.B. „Gültige Werte: 3.0 – 9.0. Leer lassen wenn unbekannt."
- Hinweistexte sind in normalem Grau (kein Fehler-State), deutlich lesbarer Text

**Postconditions**:
- Keine Datenveränderung

**Tags**: [nfr-010, helpertext, hinweistexte, formular, botanicalfamily, konsistenz]

---

## Gruppe P: REQ-021-Kompatibilität (Erfahrungsstufen)

### TC-NFR010-057: Einsteiger-Modus — Auto-gesetzten Felder zeigen „Automatisch gesetzt"-Badge

**Zusammenfassung**: Im Einsteiger-Modus werden Felder mit Defaults befüllt und zeigen in der Detailansicht ein „Automatisch gesetzt"-Badge.

**Requirement**: NFR-010 §2.1 (Hinweis zur Kompatibilität mit REQ-021), REQ-021
**Priority**: Medium
**Category**: REQ-021-Kompatibilität / Detailansicht
**Preconditions**:
- Nutzer ist angemeldet im Einsteiger-Modus (ExperienceLevel = beginner)
- Nutzer hat einen Datensatz erstellt, bei dem Felder mit Defaults automatisch gesetzt wurden

**Test Steps**:
1. Nutzer navigiert zur Detail-Seite eines im Einsteiger-Modus erstellten Datensatzes
2. Nutzer beobachtet Felder, die automatisch mit Defaults befüllt wurden

**Expected Results**:
- Felder mit automatisch gesetzten Defaults zeigen ein „Automatisch gesetzt"-Badge (oder ähnliche visuelle Kennzeichnung)
- Der Nutzer erkennt, welche Werte er manuell prüfen sollte

**Postconditions**:
- Keine Datenveränderung

**Tags**: [nfr-010, req-021, einsteiger, auto-badge, detailansicht, erfahrungsstufen]

---

### TC-NFR010-058: Einsteiger-Modus — Alle Felder via ShowAllFieldsToggle erreichbar

**Zusammenfassung**: Auch im Einsteiger-Modus sind alle Felder über den „Mehr anzeigen"-Toggle zugänglich.

**Requirement**: NFR-010 §2.1 (ShowAllFieldsToggle, REQ-021-Konformität)
**Priority**: Medium
**Category**: REQ-021-Kompatibilität
**Preconditions**:
- Nutzer ist angemeldet im Einsteiger-Modus
- Create-Dialog oder Edit-Formular für Species ist geöffnet

**Test Steps**:
1. Nutzer beobachtet: Im Einsteiger-Modus sind nur die Basis-Felder sichtbar
2. Nutzer klickt auf den „Mehr anzeigen"-Toggle (`ShowAllFieldsToggle`)

**Expected Results**:
- Zusätzliche Felder werden eingeblendet (die im Einsteiger-Modus ausgeblendet waren)
- Alle Felder des Zod-Schemas sind nun zugänglich
- Toggle zeigt „Weniger anzeigen"

**Postconditions**:
- Keine Datenveränderung

**Tags**: [nfr-010, req-021, showallfieldstoggle, einsteiger, alle-felder]

---

## Gruppe Q: Spezifische Szenarien aus NFR-010 §7

### TC-NFR010-059: Szenario 3 — Leere Substrate-Liste mit EmptyState und Erstell-Aktion

**Zusammenfassung**: Vollständige Umsetzung von NFR-010 §7 Szenario 3: Leere Liste → EmptyState → Create-Dialog.

**Requirement**: NFR-010 §7 Szenario 3
**Priority**: High
**Category**: Happy Path / Leerzustand
**Preconditions**:
- Nutzer ist angemeldet
- Keine Substrate vorhanden

**Test Steps**:
1. Nutzer navigiert zu `/standorte/substrates`
2. Nutzer beobachtet EmptyState
3. Nutzer klickt `data-testid="empty-state-action"` (Erstellen-Button in EmptyState)

**Expected Results**:
- EmptyState zeigt beschreibende Nachricht (z.B. „Noch keine Substrate angelegt")
- `data-testid="empty-state-action"` öffnet den Create-Dialog für Substrate
- Create-Dialog enthält Einleitungstext und Pflichtfelder

**Postconditions**:
- Keine Datenveränderung

**Tags**: [nfr-010, szenario-3, leerzustand, emptystate, substrat, create-dialog]

---

### TC-NFR010-060: Szenario 4 — UnsavedChangesGuard bei Substrat-Bearbeitung

**Zusammenfassung**: Vollständige Umsetzung von NFR-010 §7 Szenario 4: Bearbeitung → Navigation → Guard-Dialog → Verbleib → Verlassen.

**Requirement**: NFR-010 §7 Szenario 4
**Priority**: Critical
**Category**: Navigation / UnsavedChangesGuard
**Preconditions**:
- Nutzer ist angemeldet
- Nutzer befindet sich im Edit-Formular für ein Substrat
- Nutzer hat den pH-Wert geändert (dirty state)

**Test Steps**:
1. Nutzer hat pH-Wert geändert (Formular ist „dirty")
2. Nutzer klickt auf Breadcrumb-Link zur Substrat-Liste
3. `UnsavedChangesGuard`-Dialog erscheint
4. Nutzer klickt „Abbrechen"

**Expected Results nach Schritt 4**:
- Nutzer bleibt auf der Edit-Seite
- Die Änderung ist noch im Formular vorhanden

**Test Steps (Fortsetzung)**:
5. Nutzer klickt erneut auf Breadcrumb-Link
6. Dialog erscheint erneut
7. Nutzer klickt „Verlassen" (oder äquivalenten Bestätigungs-Button)

**Expected Results nach Schritt 7**:
- Browser navigiert zur Substrat-Liste
- Änderungen sind verworfen

**Postconditions**:
- Keine Datenveränderung (Änderungen wurden verworfen)

**Tags**: [nfr-010, szenario-4, unsavedchangesguard, substrat, navigation]

---

### TC-NFR010-061: Szenario 5 — Delete mit referenzieller Integrität (BotanicalFamily → Species)

**Zusammenfassung**: Vollständige Umsetzung von NFR-010 §7 Szenario 5: Löschversuch einer referenzierten Entität führt zu Fehlermeldung, Dialog bleibt offen.

**Requirement**: NFR-010 §7 Szenario 5, §2.5 (Fehlermeldung bei referenzieller Integrität)
**Priority**: High
**Category**: Fehlermeldung / Delete
**Preconditions**:
- BotanicalFamily „Solanaceae" wird von mindestens einer Species referenziert
- Nutzer ist auf der Detail-Seite von „Solanaceae"

**Test Steps**:
1. Nutzer klickt „Löschen"
2. ConfirmDialog öffnet sich mit „Solanaceae"
3. Nutzer bestätigt mit `data-testid="confirm-dialog-confirm"`

**Expected Results**:
- API gibt Konflikt-Fehler zurück
- Fehlermeldung erscheint (im Dialog oder als Snackbar): „'Solanaceae' kann nicht gelöscht werden, da sie von Pflanzenarten referenziert wird." (oder äquivalente Meldung)
- Dialog bleibt geöffnet (Nutzer kann abbrechen)
- `data-testid="confirm-dialog-cancel"` ist sichtbar und aktiv

**Test Steps (Fortsetzung)**:
4. Nutzer klickt `data-testid="confirm-dialog-cancel"`

**Expected Results (Fortsetzung)**:
- Dialog schließt sich
- Nutzer verbleibt auf der Detail-Seite
- „Solanaceae" ist weiterhin vorhanden

**Postconditions**:
- Keine Datenveränderung

**Tags**: [nfr-010, szenario-5, delete, referenzielle-integritaet, confirmdialog, nfr-006, botanicalfamily]

---

### TC-NFR010-062: Alle Entitäten der Vollständigkeitsmatrix haben Listenansicht mit DataTable

**Zusammenfassung**: Überprüfung, dass alle Entitäten aus NFR-010 §4.2 eine eigenständige oder eingebettete Listenansicht mit DataTable haben.

**Requirement**: NFR-010 §3.1, §4.2
**Priority**: Critical
**Category**: Vollständigkeitsmatrix / Listenansicht
**Preconditions**:
- Nutzer ist angemeldet
- Testdaten für alle Entitäten sind vorhanden

**Test Steps**:
1. Nutzer navigiert zu `/stammdaten/botanical-families` → prüft `data-testid="data-table"`
2. Nutzer navigiert zu `/stammdaten/species` → prüft `data-testid="data-table"`
3. Nutzer öffnet Species-Detail → prüft CultivarListSection enthält `data-testid="data-table"` (oder äquivalente Tabellenstruktur)
4. Nutzer navigiert zu `/standorte/sites` → prüft `data-testid="data-table"`
5. Nutzer öffnet Site-Detail → prüft LocationListSection enthält Tabelle
6. Nutzer öffnet Location-Detail → prüft Slot-Section enthält Tabelle
7. Nutzer navigiert zu `/standorte/substrates` → prüft `data-testid="data-table"`
8. Nutzer öffnet Substrate-Detail → prüft Batch-Section enthält Tabelle
9. Nutzer navigiert zu PlantInstance-Liste → prüft `data-testid="data-table"`
10. Nutzer öffnet PlantInstance-Detail → prüft GrowthPhase-Section enthält Tabelle

**Expected Results**:
- Alle 10 Entitäten (eigenständig oder eingebettet) haben eine Listenansicht
- Alle eigenständigen Listenansichten verwenden `data-testid="data-table"`
- Eingebettete Sections haben eine tabellarische Darstellung (kann vereinfachtes Layout sein)
- Keine Entität hat nur eine Detailansicht ohne Listenzugang

**Postconditions**:
- Keine Datenveränderung

**Tags**: [nfr-010, vollständigkeitsmatrix, alle-entitäten, listenansicht, datatable, abschlussprüfung]

---

## Abdeckungsmatrix

| NFR-010 Abschnitt | Testfall-IDs |
|---|---|
| §2.1 CRUD-Operationen (Vollständigkeit) | TC-NFR010-041 bis TC-NFR010-048, TC-NFR010-062 |
| §2.2 Create-Dialog (Einleitungstext, Validierung, Snackbar) | TC-NFR010-011 bis TC-NFR010-016, TC-NFR010-050 |
| §2.3 Read/Detail-Ansicht (Breadcrumb, Felder, Lade-/Fehlerzustand) | TC-NFR010-017, TC-NFR010-018, TC-NFR010-019 |
| §2.4 Edit-Formular (Vorausfüllung, UnsavedChangesGuard, Snackbar) | TC-NFR010-020 bis TC-NFR010-024, TC-NFR010-051 |
| §2.5 Delete mit ConfirmDialog | TC-NFR010-025 bis TC-NFR010-028 |
| §3.1 Tabellarische Übersicht (Einleitungstext, Zeilenklick) | TC-NFR010-001, TC-NFR010-005, TC-NFR010-049, TC-NFR010-062 |
| §3.2 Pagination | TC-NFR010-004 |
| §3.3 Sortierung (TableSortLabel) | TC-NFR010-009 |
| §3.3a Durchsuchbarkeit (Debouncing, URL-Parameter) | TC-NFR010-006 bis TC-NFR010-008, TC-NFR010-010 |
| §3.3b Spaltenspezifische Filter | (Verweis auf UI-NFR-010 §7.2; Basis-Testfälle in TC-REQ-006/010) |
| §3.3c Tablet-Spaltenprioritäten | TC-NFR010-038 |
| §3.4 Leerzustand (EmptyState) | TC-NFR010-003, TC-NFR010-059 |
| §3.5 Ladezustand (LoadingSkeleton) | TC-NFR010-002, TC-NFR010-018 |
| §3.6 Erstell-Aktion (Hinzufügen-Button) | TC-NFR010-011 |
| §4.2 Vollständigkeitsmatrix (fehlende Operationen) | TC-NFR010-041 bis TC-NFR010-048 |
| §5 Eingebettete Entitäten (Cultivar, Location, Slot, GrowthPhase) | TC-NFR010-030 bis TC-NFR010-032 |
| §6.1 Konsistenz (Button-Reihenfolge, Fehlermeldungen, Numerik) | TC-NFR010-033 bis TC-NFR010-036 |
| §6.2 Responsivität (Desktop ≥1024px, Tablet ≤1024px) | TC-NFR010-037, TC-NFR010-038 |
| §6.3 Barrierefreiheit (Fokus, Labels, data-testid) | TC-NFR010-039, TC-NFR010-040 |
| §7 Akzeptanzszenarien 1–5 | TC-NFR010-029, TC-NFR010-030, TC-NFR010-059, TC-NFR010-060, TC-NFR010-061 |
| REQ-021-Kompatibilität (Einsteiger-Modus) | TC-NFR010-057, TC-NFR010-058 |
| i18n (DE/EN) | TC-NFR010-052 |

**Gesamtanzahl Testfälle**: 62

**Kritische Testfälle** (Priority=Critical): TC-NFR010-001, 003, 005, 011, 012, 014, 017, 020, 022, 023, 025, 026, 029, 030, 039, 041, 042, 043, 044, 045, 047, 048, 060, 062

**Implementierungsstatus der getesteten Ist-Zustand-Lücken** (NFR-010 §4.1 → §4.2):
- BotanicalFamily Edit: TC-NFR010-041 (war fehlend)
- Cultivar Read + Edit: TC-NFR010-042, TC-NFR010-043 (war fehlend)
- Slot Edit + Delete: TC-NFR010-044 (war fehlend)
- Substrate Edit + Delete: TC-NFR010-045 (war fehlend)
- Batch List + Edit + Delete: TC-NFR010-046 (war fehlend)
- PlantInstance Edit: TC-NFR010-047 (war fehlend)
- GrowthPhase Delete: TC-NFR010-048 (war fehlend)
