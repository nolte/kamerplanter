---

ID: UI-NFR-010
Titel: Tabellen & Datenansichten
Kategorie: UI-Verhalten Unterkategorie: Tabellen, Listen, Datenvisualisierung
Technologie: React, TypeScript, MUI, Flutter
Status: Entwurf
Priorität: Hoch
Version: 1.1
Autor: Business Analyst - Agrotech
Datum: 2026-03-18
Tags: [tabellen, tables, sortierung, filter, suche, pagination, responsive, selektion, barrierefreiheit]
Abhängigkeiten: [UI-NFR-001, UI-NFR-002, UI-NFR-003, UI-NFR-004, UI-NFR-005, UI-NFR-006, UI-NFR-007]
Betroffene Module: [Frontend, Mobile]
---

# UI-NFR-010: Tabellen & Datenansichten

> **Verwandtes Dokument:** NFR-010 (UI-Pflegemasken & Listenansichten) definiert, **welche** Entitäten Listenansichten benötigen und welche Spalten/Aktionen pro Entität vorhanden sein müssen. Dieses Dokument definiert das allgemeine **Verhalten** aller Tabellen.

## 1. Business Case

### 1.1 User Story

**Als** Endanwender
**möchte ich** tabellarische Daten effizient durchsuchen, sortieren und filtern können
**um** relevante Einträge schnell zu finden und fundierte Entscheidungen zu treffen.

**Als** Endanwender
**möchte ich** Tabellen auf jedem Gerät komfortabel nutzen können
**um** auch unterwegs oder am Tablet auf meine Daten zugreifen zu können.

**Als** Frontend-Entwickler
**möchte ich** eine zentrale, wiederverwendbare Tabellenkomponente mit konsistentem Verhalten
**um** Tabellenfunktionalität nicht in jeder Ansicht neu implementieren zu müssen.

### 1.2 Geschäftliche Motivation

Tabellen sind die primäre Darstellungsform für Sammlungsdaten in der Anwendung (Pflanzen, Standorte, Familien, Aufgaben, Ernten). Schlechte Tabellen kosten Zeit und führen zu Fehlern:

1. **Auffindbarkeit** — Ohne Suche und Filter muss der Nutzer manuell scrollen, um Einträge zu finden
2. **Orientierung** — Ohne Sortierung fehlt jede logische Ordnung der Daten
3. **Effizienz** — Ohne Massenaktionen müssen Operationen einzeln ausgeführt werden
4. **Zugänglichkeit** — Ohne korrekte ARIA-Attribute sind Tabellen für Screenreader unbrauchbar
5. **Mobilfähigkeit** — Ohne responsive Anpassung sind Tabellen auf kleinen Bildschirmen unlesbar

---

## 2. Anforderungen

### 2.1 Sortierung

| # | Regel | Stufe |
|---|-------|-------|
| R-001 | Jede Datenspalte MUSS per Klick auf den Spaltenheader sortierbar sein, sofern der Datentyp eine sinnvolle Sortierung erlaubt. | MUSS |
| R-002 | Spaltenheader MÜSSEN die aktuelle Sortierrichtung visuell anzeigen (Pfeil aufwärts/abwärts). | MUSS |
| R-003 | Ein erneuter Klick auf den gleichen Header MUSS die Sortierrichtung umkehren (aufsteigend ↔ absteigend). | MUSS |
| R-004 | Die Standard-Sortierung SOLL kontextuell sinnvoll sein (z.B. alphabetisch nach Name, chronologisch nach Datum). | SOLL |
| R-005 | Spaltenheader MÜSSEN durch `cursor: pointer` und Hover-Effekt als interaktiv erkennbar sein. | MUSS |

### 2.2 Suche & Filter

| # | Regel | Stufe |
|---|-------|-------|
| R-006 | Über jeder Tabelle MUSS ein globales Suchfeld angeboten werden, das über alle sichtbaren Spalten sucht. | MUSS |
| R-007 | Die Suche MUSS mit Debouncing (≥ 300ms) implementiert sein, um unnötige API-Aufrufe zu vermeiden (vgl. UI-NFR-003). | MUSS |
| R-008 | Spaltenspezifische Filter KÖNNEN zusätzlich angeboten werden (z.B. Dropdown-Filter für Status oder Phase). | KANN |
| R-009 | Aktive Filter MÜSSEN visuell hervorgehoben sein (z.B. Chip mit Löschen-Button). | MUSS |
| R-010 | Ein „Alle Filter zurücksetzen"-Button MUSS vorhanden sein, wenn mindestens ein Filter aktiv ist. | MUSS |

### 2.3 Pagination & Ergebnisanzeige

| # | Regel | Stufe |
|---|-------|-------|
| R-011 | Tabellen mit mehr als 50 Einträgen MÜSSEN paginiert werden. | MUSS |
| R-012 | Die Anzahl der Einträge pro Seite MUSS vom Nutzer einstellbar sein (Optionen: 10, 25, 50, 100). | MUSS |
| R-013 | Die aktuelle Position MUSS angezeigt werden: „Zeigt 1–50 von 234 Einträgen". | MUSS |
| R-014 | Die gewählte Seitengröße SOLL im `localStorage` persistiert werden, damit sie beim nächsten Besuch erhalten bleibt. | SOLL |
| R-015 | Beim Wechsel von Filtern oder Sortierung MUSS die Pagination auf Seite 1 zurückgesetzt werden. | MUSS |

### 2.4 URL-Persistenz

| # | Regel | Stufe |
|---|-------|-------|
| R-016 | Sortierung, Filterkriterien und aktuelle Seite MÜSSEN als URL-Query-Parameter abgebildet werden (vgl. UI-NFR-005 R-003). | MUSS |
| R-017 | Beim Laden einer URL mit Query-Parametern MUSS die Tabelle den entsprechenden Zustand wiederherstellen. | MUSS |
| R-018 | Gefilterte und sortierte Ansichten MÜSSEN über die URL teilbar und als Lesezeichen speicherbar sein. | MUSS |

### 2.5 Responsive Verhalten

| # | Regel | Stufe |
|---|-------|-------|
| R-019 | Auf Desktop (>1024px) MUSS die vollständige Tabelle mit allen Spalten dargestellt werden. | MUSS |
| R-020 | Auf Tablet (≤1024px) SOLLEN weniger wichtige Spalten ausgeblendet werden. Die Priorität der Spalten MUSS pro Tabelle definiert sein. | SOLL |
| R-021 | Auf Mobile (≤768px) MUSS die Tabelle als Kartenansicht (Card-Layout) oder als verkürzte Tabelle mit horizontalem Scroll dargestellt werden. | MUSS |
| R-022 | Horizontales Scrollen in Tabellen MUSS durch einen visuellen Hinweis erkennbar sein (Schatten am Rand oder Scroll-Indikator). | MUSS |

### 2.6 Sticky Header

| # | Regel | Stufe |
|---|-------|-------|
| R-023 | Der Tabellenkopf (Header-Zeile) MUSS beim vertikalen Scrollen fixiert bleiben (`position: sticky`). | MUSS |
| R-024 | Der fixierte Header MUSS durch einen Schatten oder eine Linie visuell vom Tabelleninhalt abgegrenzt sein. | MUSS |

### 2.7 Zeilen-Selektion & Massenaktionen

| # | Regel | Stufe |
|---|-------|-------|
| R-025 | Tabellen KÖNNEN eine Checkbox-Spalte zur Mehrfachauswahl von Zeilen anbieten. | KANN |
| R-026 | Wenn Mehrfachauswahl aktiviert ist, MUSS eine „Alle auswählen"-Checkbox im Header vorhanden sein. | MUSS |
| R-027 | Bei aktiver Selektion MUSS eine Aktionsleiste (Toolbar) erscheinen mit der Anzahl ausgewählter Einträge und verfügbaren Massenaktionen. | MUSS |
| R-028 | Destruktive Massenaktionen (z.B. „Alle löschen") MÜSSEN einen Bestätigungsdialog auslösen. | MUSS |

### 2.8 Lade- & Leerzustände

| # | Regel | Stufe |
|---|-------|-------|
| R-029 | Während die Daten geladen werden, MUSS ein Skeleton angezeigt werden (keine leere Tabelle, kein Spinner). | MUSS |
| R-030 | Wenn keine Daten vorhanden sind, MUSS ein leerer Zustand mit erklärendem Text und optionaler Aktion angezeigt werden (z.B. „Noch keine Pflanzen vorhanden. [Jetzt anlegen]"). | MUSS |
| R-031 | Wenn eine Suche/ein Filter keine Ergebnisse liefert, MUSS ein spezifischer Hinweis erscheinen (z.B. „Keine Ergebnisse für ‚xyz'. [Filter zurücksetzen]") — nicht der allgemeine Leerzustand. | MUSS |

### 2.9 Tastaturnavigation & Barrierefreiheit

| # | Regel | Stufe |
|---|-------|-------|
| R-032 | Tabellen MÜSSEN mit korrekten ARIA-Attributen versehen sein: `role="table"`, `role="row"`, `role="columnheader"`, `role="cell"`. | MUSS |
| R-033 | Die aktive Sortierrichtung MUSS über `aria-sort="ascending"` bzw. `aria-sort="descending"` kommuniziert werden. | MUSS |
| R-034 | Sortierbare Spaltenheader MÜSSEN per Tastatur (Tab + Enter/Leertaste) bedienbar sein. | MUSS |
| R-035 | Klickbare Tabellenzeilen MÜSSEN einen sichtbaren Fokus-Indikator haben (`outline` oder `box-shadow`). | MUSS |
| R-036 | Die Tabelle SOLL ein `<caption>`-Element oder `aria-label` besitzen, das den Inhalt der Tabelle beschreibt. | SOLL |

### 2.10 Visuelle Konsistenz

| # | Regel | Stufe |
|---|-------|-------|
| R-037 | Alle Tabellen MÜSSEN die zentrale `DataTable`-Komponente verwenden — keine individuellen Tabellenimplementierungen. | MUSS |
| R-038 | Zeilen MÜSSEN einen Hover-Effekt haben, wenn sie klickbar sind. | MUSS |
| R-039 | Gerade und ungerade Zeilen KÖNNEN durch alternierende Hintergrundfarben (Zebra-Streifen) unterschieden werden. | KANN |
| R-040 | Zahlenwerte SOLLEN rechtsbündig, Textwerte linksbündig ausgerichtet sein. | SOLL |

---

## 3. Wireframe-Beispiele

### 3.1 Vollständige Tabelle (Desktop)

```
┌──────────────────────────────────────────────────────────────────┐
│                                                                  │
│  Pflanzen-Instanzen                            [🔍 Suche...]    │
│                                                                  │
│  Aktive Filter: [Phase: Vegetativ ✕]  [Standort: GH-1 ✕]       │
│                                       [Alle Filter zurücksetzen] │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ ☐ │ Name ▲        │ Sorte        │ Phase      │ Standort │  │  ← Sticky Header
│  ├────────────────────────────────────────────────────────────┤  │
│  │ ☐ │ Pflanze-001   │ Sativa X     │ Vegetativ  │ GH-1     │  │
│  │ ☐ │ Pflanze-002   │ Indica Y     │ Vegetativ  │ GH-1     │  │
│  │ ☐ │ Pflanze-003   │ Hybrid Z     │ Vegetativ  │ GH-1     │  │
│  │   │ ...           │ ...          │ ...        │ ...      │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  Zeigt 1–50 von 234 Einträgen        Zeilen pro Seite: [50 ▾]  │
│                                  [◀ Zurück]  1  2  3  [Weiter ▶]│
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### 3.2 Massenaktionen-Toolbar

```
┌──────────────────────────────────────────────────────────────────┐
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  ✓ 3 ausgewählt     [Phase ändern]  [Exportieren]  [🗑️]  │  │
│  └────────────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ ☑ │ Pflanze-001   │ Sativa X     │ Vegetativ  │ GH-1     │  │
│  │ ☐ │ Pflanze-002   │ Indica Y     │ Vegetativ  │ GH-1     │  │
│  │ ☑ │ Pflanze-003   │ Hybrid Z     │ Vegetativ  │ GH-1     │  │
│  │ ☑ │ Pflanze-004   │ Sativa A     │ Vegetativ  │ GH-2     │  │
│  └────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

### 3.3 Mobile Kartenansicht (≤768px)

```
┌──────────────────────┐
│ [🔍 Suche...]        │
│ [Filter ▾]           │
│                      │
│ ┌──────────────────┐ │
│ │ Pflanze-001      │ │
│ │ Sorte: Sativa X  │ │
│ │ Phase: Vegetativ │ │
│ │ Standort: GH-1   │ │
│ └──────────────────┘ │
│                      │
│ ┌──────────────────┐ │
│ │ Pflanze-002      │ │
│ │ Sorte: Indica Y  │ │
│ │ Phase: Vegetativ │ │
│ │ Standort: GH-1   │ │
│ └──────────────────┘ │
│                      │
│ Zeigt 1–10 von 234  │
│   [◀]  1  2  3  [▶] │
└──────────────────────┘
```

### 3.4 Leerzustand vs. keine Suchergebnisse

```
  Leerzustand (keine Daten):           Keine Suchergebnisse:
  ┌────────────────────────────┐       ┌────────────────────────────┐
  │                            │       │ [🔍 Tomate ]              │
  │     📋                     │       │                            │
  │                            │       │     🔍                     │
  │  Noch keine Pflanzen       │       │                            │
  │  vorhanden.                │       │  Keine Ergebnisse für      │
  │                            │       │  „Tomate".                 │
  │  [Jetzt anlegen]           │       │                            │
  │                            │       │  [Filter zurücksetzen]     │
  └────────────────────────────┘       └────────────────────────────┘
```

### 3.5 Sortier-Indikator

```
  Nicht sortiert:    Aufsteigend:     Absteigend:
  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
  │ Name    ↕    │  │ Name    ▲    │  │ Name    ▼    │
  └──────────────┘  └──────────────┘  └──────────────┘
```

---

## 4. URL-Schema

Tabellenansichten bilden ihren Zustand in der URL ab. Beispiel:

```
/pflanzen/plant-instances?sort=name&order=asc&search=sativa&phase=vegetativ&page=2&pageSize=25
```

| Parameter | Beschreibung | Beispiel |
|---|---|---|
| `sort` | Sortier-Spalte | `name`, `created_at`, `phase` |
| `order` | Sortierrichtung | `asc`, `desc` |
| `search` | Globaler Suchbegriff | `sativa` |
| `page` | Aktuelle Seite (1-basiert) | `1`, `2`, `3` |
| `pageSize` | Einträge pro Seite | `10`, `25`, `50`, `100` |
| `<feldname>` | Spaltenspezifischer Filter | `phase=vegetativ` |

---

## 5. Akzeptanzkriterien

### Definition of Done

- [ ] **Sortierung**
    - [ ] Alle Datenspalten sind per Klick auf den Header sortierbar
    - [ ] Sortierrichtung wird visuell angezeigt (Pfeil)
    - [ ] Erneuter Klick kehrt die Richtung um
    - [ ] Header haben `cursor: pointer` und Hover-Effekt
- [ ] **Suche & Filter**
    - [ ] Globales Suchfeld über der Tabelle
    - [ ] Suche mit Debouncing (≥ 300ms)
    - [ ] Aktive Filter sind als Chips dargestellt mit Löschen-Button
    - [ ] „Alle Filter zurücksetzen"-Button bei aktiven Filtern
- [ ] **Pagination**
    - [ ] Tabellen mit > 50 Einträgen sind paginiert
    - [ ] Seitengröße einstellbar (10, 25, 50, 100)
    - [ ] Position wird angezeigt: „Zeigt X–Y von Z Einträgen"
    - [ ] Seitengröße wird im `localStorage` persistiert
    - [ ] Filter-/Sortierwechsel setzt Pagination auf Seite 1 zurück
- [ ] **URL-Persistenz**
    - [ ] Sortierung, Filter und Seite sind in der URL abgebildet
    - [ ] Laden einer URL mit Query-Parametern stellt Zustand wieder her
    - [ ] Ansichten sind über URL teilbar
- [ ] **Responsive**
    - [ ] Desktop: vollständige Tabelle
    - [ ] Tablet: weniger wichtige Spalten ausgeblendet
    - [ ] Mobile: Kartenansicht oder horizontaler Scroll mit Indikator
- [ ] **Sticky Header**
    - [ ] Header bleibt beim Scrollen fixiert
    - [ ] Visueller Schatten trennt Header vom Inhalt
- [ ] **Lade- & Leerzustände**
    - [ ] Skeleton während des Ladens
    - [ ] Leerzustand mit Hinweistext und Aktion
    - [ ] Keine-Ergebnisse-Zustand unterscheidet sich vom allgemeinen Leerzustand
- [ ] **Barrierefreiheit**
    - [ ] ARIA-Attribute: `role`, `aria-sort`, `aria-label`/`<caption>`
    - [ ] Sortierbare Header per Tastatur bedienbar (Tab + Enter)
    - [ ] Sichtbarer Fokus-Indikator auf klickbaren Zeilen
- [ ] **Testing**
    - [ ] Unit-Tests für Sortier-, Filter- und Pagination-Logik
    - [ ] E2E-Tests für Sortierung, Suche und Seitennavigation
    - [ ] Responsive Tests auf Mobile, Tablet und Desktop
    - [ ] Tastaturnavigation getestet

---

## 6. Risiken bei Nicht-Einhaltung

| Risiko | Auswirkung | Wahrscheinlichkeit | Mitigation |
|---|---|---|---|
| **Fehlende Sortierung** | Nutzer kann Daten nicht ordnen, findet Einträge nicht | Hoch | Sortierung als Standard-Feature der DataTable-Komponente |
| **Fehlende Suche/Filter** | Nutzer muss manuell durch alle Seiten scrollen | Hoch | Globales Suchfeld als Pflichtbestandteil jeder Tabellenansicht |
| **Keine URL-Persistenz** | Gefilterte Ansichten gehen beim Seitenwechsel verloren, nicht teilbar | Mittel | Query-Parameter als Teil der DataTable-Logik |
| **Nicht-responsive Tabellen** | Tabellen sind auf Mobile/Tablet unbrauchbar | Hoch | Mobile-First-Entwicklung, Card-Layout als Fallback |
| **Fehlende ARIA-Attribute** | Screenreader können Tabellendaten nicht interpretieren | Mittel | ARIA-Attribute als Teil der zentralen Komponente, a11y-Tests |
| **Individuelle Tabellenimplementierungen** | Inkonsistentes Verhalten, höherer Wartungsaufwand | Hoch | DataTable als einzige erlaubte Tabellenkomponente (R-037) |
| **Fehlender Keine-Ergebnisse-Hinweis** | Nutzer denkt fälschlicherweise, es gibt keine Daten | Mittel | Unterschiedliche Leerzustände für „keine Daten" vs. „keine Treffer" |

---

## 7. Domänenspezifische Filter-Matrix

<!-- Quelle: Tabellen-Analyse-Report 2026-03-18 (L-001) -->

R-008 definiert spaltenspezifische Filter als KANN-Anforderung. Dieser Abschnitt konkretisiert, **welche** Filter für **welche** Entität bereitgestellt werden SOLLEN, um die häufigsten Nutzer-Fragen direkt über die Listenansicht beantwortbar zu machen. Filter werden als Chip-Gruppe oberhalb der Tabelle (unterhalb des Suchfelds) dargestellt.

### 7.1 Filter-Darstellung

| # | Regel | Stufe |
|---|-------|-------|
| R-041 | Spaltenspezifische Filter SOLLEN als MUI `Chip`-Gruppe mit Dropdown-Auswahl dargestellt werden. | SOLL |
| R-042 | Enum-basierte Filter (Status, Phase, Typ) SOLLEN als Single-Select-Chip-Gruppe dargestellt werden — ein Klick auf den aktiven Chip deaktiviert den Filter. | SOLL |
| R-043 | Zeitraum-Filter SOLLEN als Datums-Range-Picker (Von/Bis) dargestellt werden. | SOLL |
| R-044 | Alle aktiven Filter MÜSSEN als URL-Query-Parameter abgebildet werden (vgl. §4). | MUSS |
| R-045 | Filter-Werte SOLLEN über die i18n-Schlüssel `enums.<enumName>.<value>` lokalisiert werden (vgl. UI-NFR-007). | SOLL |

### 7.2 Filter pro Entität

| Entität | REQ | Filter | Typ | URL-Parameter | Stufe |
|---------|-----|--------|-----|---------------|-------|
| **PlantInstance** | REQ-003 | Wachstumsphase | Enum-Chip (`germination`, `seedling`, `vegetative`, `flowering`, `harvest`, `drying`, `curing`) | `phase` | SOLL |
| PlantInstance | REQ-003 | Standort (Site) | Dropdown (Referenz) | `site_key` | SOLL |
| PlantInstance | REQ-003 | Pflanzdurchlauf (Run) | Dropdown (Referenz) | `run_key` | KANN |
| **Task** | REQ-006 | Status | Enum-Chip (`pending`, `in_progress`, `completed`, `skipped`, `dormant`) | `status` | SOLL |
| Task | REQ-006 | Zuweisung | Toggle „Meine Aufgaben" / „Alle Aufgaben" | `assigned_to=me` | SOLL |
| Task | REQ-006 | Priorität | Enum-Chip (`low`, `medium`, `high`, `critical`) | `priority` | KANN |
| Task | REQ-006 | Kategorie | Enum-Chip (`watering`, `feeding`, `training`, `inspection`, `harvest`, `maintenance`, `seasonal`, `phenological`) | `category` | KANN |
| Task | REQ-006 | Fälligkeitszeitraum | Datums-Range | `due_from`, `due_to` | KANN |
| Task | REQ-006 | Tags | Chip-Autocomplete (Freitext) | `tag` | KANN |
| **HarvestBatch** | REQ-007 | Erntezeitraum | Datums-Range | `harvested_from`, `harvested_to` | SOLL |
| HarvestBatch | REQ-007 | Qualitätsgrad | Enum-Chip (`A+`, `A`, `B`, `C`) | `grade` | KANN |
| HarvestBatch | REQ-007 | Erntetyp | Enum-Chip (`full`, `partial`, `continuous`) | `harvest_type` | KANN |
| **Pest** | REQ-010 | Befallstyp | Enum-Chip (`insect`, `mite`, `fungus`, `bacteria`, `virus`, `nematode`) | `pest_type` | SOLL |
| **Disease** | REQ-010 | Krankheitstyp | Enum-Chip (`fungal`, `bacterial`, `viral`, `physiological`, `nutrient_deficiency`) | `disease_type` | SOLL |
| **Treatment** | REQ-010 | Behandlungsmethode | Enum-Chip (`cultural`, `biological`, `chemical`) | `method` | SOLL |
| Treatment | REQ-010 | Karenz-Status | Toggle „Aktive Karenz" / „Alle" | `karenz_active=true` | SOLL |
| **FeedingEvent** | REQ-004 | Zeitraum | Datums-Range | `date_from`, `date_to` | SOLL |
| FeedingEvent | REQ-004 | Pflanzdurchlauf (Run) | Dropdown (Referenz) | `run_key` | KANN |
| **Fertilizer** | REQ-004 | Dünger-Typ | Enum-Chip (`base`, `supplement`, `booster`, `biological`, `ph_adjuster`, `organic`) | `fertilizer_type` | SOLL |
| Fertilizer | REQ-004 | Bio-Zertifizierung | Toggle „Nur Bio" | `is_organic=true` | KANN |
| Fertilizer | REQ-004 | Tank-Sicherheit | Toggle „Nur tanksicher" | `tank_safe=true` | KANN |
| **NutrientPlan** | REQ-004 | Substrattyp | Enum-Chip | `substrate_type` | KANN |
| NutrientPlan | REQ-004 | Vorlage | Toggle „Nur Vorlagen" | `is_template=true` | KANN |
| **PlantingRun** | REQ-013 | Status | Enum-Chip (`planned`, `active`, `harvesting`, `completed`, `cancelled`) | `status` | SOLL |
| PlantingRun | REQ-013 | Standort (Site) | Dropdown (Referenz) | `site_key` | KANN |
| **Tank** | REQ-014 | Standort (Site) | Dropdown (Referenz) | `site_key` | KANN |
| **TankFillEvent** | REQ-014 | Zeitraum | Datums-Range | `date_from`, `date_to` | SOLL |
| TankFillEvent | REQ-014 | Befüllungstyp | Enum-Chip (`full_change`, `top_up`, `additive_only`) | `fill_type` | KANN |
| **WateringEvent** | REQ-014 | Zeitraum | Datums-Range | `date_from`, `date_to` | SOLL |
| **Substrate** | REQ-019 | Substrattyp | Enum-Chip (13 Werte, vgl. REQ-019) | `substrate_type` | SOLL |
| **Species** | REQ-001 | Botanische Familie | Dropdown (Referenz) | `family_key` | KANN |
| **ImportJob** | REQ-012 | Import-Status | Enum-Chip (`pending`, `validated`, `imported`, `failed`) | `status` | SOLL |
| **Membership** | REQ-024 | Rolle | Enum-Chip (`admin`, `grower`, `viewer`) | `role` | KANN |
| **WorkflowTemplate** | REQ-006 | Kategorie | Enum-Chip | `category` | KANN |

### 7.3 CSV-Import-Vorschautabelle (REQ-012 Sonderfall)

<!-- Quelle: Tabellen-Analyse-Report 2026-03-18 (L-004) -->

Die Import-Vorschautabelle hat besondere Anforderungen, die über die Standard-DataTable hinausgehen:

| # | Regel | Stufe |
|---|-------|-------|
| R-046 | Jede Zeile MUSS einen visuellen Validierungsstatus anzeigen: grün (valid), rot (invalid), gelb (duplicate). | MUSS |
| R-047 | Fehlerhafte Felder innerhalb einer Zeile SOLLEN farblich hervorgehoben werden (roter Rand). | SOLL |
| R-048 | Ein Zeilen-Status-Filter SOLL bereitgestellt werden: „Nur Fehler anzeigen" / „Nur Duplikate" / „Alle". | SOLL |
| R-049 | Einzelne Zeilen SOLLEN über eine Checkbox vom Import ausschließbar sein („Zeile überspringen"). | SOLL |
| R-050 | Oberhalb der Vorschautabelle MUSS eine Zusammenfassung angezeigt werden: „X gültig, Y fehlerhaft, Z Duplikate". | MUSS |

---

## 8. Tablet-Spaltenprioritäten

<!-- Quelle: Tabellen-Analyse-Report 2026-03-18 (L-003) -->

R-020 fordert, dass auf Tablet (≤1024px) weniger wichtige Spalten ausgeblendet werden. Dieser Abschnitt definiert die Spaltenprioritäten pro Listenansicht. Spalten mit `hideBelowBreakpoint: 'md'` werden auf Tablet ausgeblendet, Spalten mit `hideBelowBreakpoint: 'lg'` nur auf großen Tablets.

| # | Regel | Stufe |
|---|-------|-------|
| R-051 | Jede ListPage MUSS für jede Spalte eine Priorität definieren: **primär** (immer sichtbar), **sekundär** (ab `md` ausblenden) oder **tertiär** (ab `lg` ausblenden). | SOLL |
| R-052 | Primärspalten MÜSSEN den Datensatz eindeutig identifizierbar und die Kernfrage der Listenansicht beantwortbar machen (max. 3–4 Spalten). | MUSS |

### 8.1 Spaltenprioritäten pro Listenansicht

| ListPage | Primär (immer sichtbar) | Sekundär (`hideBelowBreakpoint: 'md'`) | Tertiär (`hideBelowBreakpoint: 'lg'`) |
|----------|------------------------|----------------------------------------|---------------------------------------|
| **PlantInstance** | Name, Sorte, Phase | Standort, Pflanzdatum | Instanz-ID, Entfernt-am |
| **Task** | Name, Status, Fälligkeit | Priorität, Zugewiesen an | Kategorie, Erstellt-am |
| **HarvestBatch** | Batch-ID, Datum, Gewicht | Qualität, Erntetyp | Pflanzen-Key |
| **PlantingRun** | Name, Status, Anzahl Pflanzen | Species, Standort | Start-/Enddatum |
| **FertilizerList** | Name, Typ, Hersteller | NPK-Verhältnis | EC-Beitrag, Tank-Sicherheit |
| **FeedingEvent** | Datum, Run/Pflanze, EC-Ist | EC-Soll, pH | Notizen |
| **TankList** | Name, Standort, Volumen | EC, pH | Letzte Befüllung |
| **PestList** | Deutscher Name, Typ | Wissenschaftl. Name | Wirtspflanzen |
| **DiseaseList** | Deutscher Name, Typ | Wissenschaftl. Name | Symptome |
| **TreatmentList** | Name, Methode, Wirkstoff | Karenzzeit | Hersteller |
| **SubstrateList** | Name, Typ, pH | EC, Standort | Erstellt-am |
| **SpeciesList** | Deutscher Name, Familie | Wissenschaftl. Name | Nährstoffbedarf |
| **WorkflowTemplate** | Name, Kategorie | Beschreibung | Erstellt-am |
| **WateringEvent** | Datum, Tank, Volumen | pH, EC | Notizen |
| **ImportJob** | Dateiname, Status, Datum | Gültige/Fehlerhafte Zeilen | — |
| **Membership** | Nutzername, Rolle | E-Mail | Beitrittsdatum |

---

## 9. Daten-Export

<!-- Quelle: Tabellen-Analyse-Report 2026-03-18 (L-005) -->

### 9.1 Allgemeine Export-Regeln

| # | Regel | Stufe |
|---|-------|-------|
| R-053 | Listenansichten KÖNNEN einen Export-Button anbieten, der die aktuell gefilterte/sortierte Ansicht als Datei herunterlädt. | KANN |
| R-054 | Unterstützte Exportformate SOLLEN mindestens CSV umfassen. PDF ist optional. | SOLL |
| R-055 | Der Export MUSS die aktuell aktiven Filter und die aktuelle Sortierung berücksichtigen — nicht die Gesamtdatenmenge. | MUSS |
| R-056 | Der Export-Button SOLL in der Toolbar neben dem Suchfeld platziert werden (Icon: Download). | SOLL |
| R-057 | Bei aktiver Zeilen-Selektion (§2.7) SOLL der Export nur die selektierten Zeilen exportieren. | SOLL |

### 9.2 Compliance-relevante Exporte (Priorität)

Folgende Exporte haben fachlichen Compliance-Bezug und SOLLEN priorisiert implementiert werden:

| Entität | REQ | Exportformat | Begründung |
|---------|-----|-------------|------------|
| HarvestBatch | REQ-007 | CSV + PDF | CanG-Dokumentation: Erntemengen, Qualität, Rückverfolgbarkeit |
| TreatmentApplication | REQ-010 | CSV + PDF | Pflanzenschutz-Protokoll mit Karenzzeiten |
| FeedingEvent | REQ-004 | CSV | Düngeprotokoll (EC/pH-Verlauf) |

---

## 10. Akzeptanzkriterien — Ergänzungen

Die folgenden Akzeptanzkriterien ergänzen §5:

- [ ] **Domänenspezifische Filter (§7)**
    - [ ] PlantInstance-Listenansicht bietet Phase-Filter als Chip-Gruppe
    - [ ] Task-Listenansicht bietet Status-Filter und „Meine Aufgaben"-Toggle
    - [ ] Alle SOLL-Filter aus §7.2 sind implementiert
    - [ ] Filter-Werte sind URL-persistiert und teilbar
    - [ ] Filter-Werte sind i18n-lokalisiert (DE/EN)
- [ ] **Tablet-Spaltenprioritäten (§8)**
    - [ ] Alle ListPages definieren `hideBelowBreakpoint` für sekundäre/tertiäre Spalten
    - [ ] Auf Tablet (≤1024px) sind max. 3–4 Primärspalten sichtbar
- [ ] **Import-Vorschautabelle (§7.3)**
    - [ ] Zeilenweiser Validierungsstatus (grün/rot/gelb) ist sichtbar
    - [ ] Status-Filter und Zusammenfassung sind vorhanden
- [ ] **Export (§9)**
    - [ ] Compliance-relevante Exporte (HarvestBatch, TreatmentApplication) sind als CSV/PDF verfügbar

---

**Dokumenten-Ende**

**Version**: 1.1
**Status**: Entwurf
**Letzte Aktualisierung**: 2026-03-18
**Review**: Pending
**Genehmigung**: Pending
