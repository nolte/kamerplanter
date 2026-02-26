---

ID: UI-NFR-010
Titel: Tabellen & Datenansichten
Kategorie: UI-Verhalten Unterkategorie: Tabellen, Listen, Datenvisualisierung
Technologie: React, TypeScript, MUI, Flutter
Status: Entwurf
Priorität: Hoch
Version: 1.0
Autor: Business Analyst - Agrotech
Datum: 2026-02-26
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

**Dokumenten-Ende**

**Version**: 1.0
**Status**: Entwurf
**Letzte Aktualisierung**: 2026-02-26
**Review**: Pending
**Genehmigung**: Pending
