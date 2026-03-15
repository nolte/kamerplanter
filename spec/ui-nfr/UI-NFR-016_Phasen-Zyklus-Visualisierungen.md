# UI-NFR-016: Phasen- & Zyklus-Visualisierungen

```yaml
ID: UI-NFR-016
Titel: Standardisierte Darstellung von Phasen-Timelines und saisonalen Zyklen
Kategorie: UI-Verhalten
Unterkategorie: Datenvisualisierung, Timeline, Lifecycle
Technologie: React, TypeScript, MUI, SVG
Status: Entwurf
Priorität: Hoch
Version: 1.0
Autor: Business Analyst - Agrotech
Datum: 2026-03-11
Tags: [timeline, phases, seasonal-cycle, gantt, visualization, lifecycle, perennial]
Abhängigkeiten: [REQ-003, REQ-013, REQ-015, UI-NFR-006, UI-NFR-009]
Betroffene Module: [Frontend]
```

## 1. Business Case

### 1.1 User Stories

**Als** Gärtner mit mehrjährigen Pflanzen
**möchte ich** den saisonalen Zyklus meiner Pflanzen auf einen Blick erkennen
**um** zu verstehen, in welcher Phase sich jede Pflanze befindet und was als Nächstes kommt.

**Als** Indoor-Grower
**möchte ich** den linearen Fortschritt meiner Pflanzdurchläufe visuell nachverfolgen
**um** Timing-Probleme frühzeitig zu erkennen und Phasenübergänge zu planen.

**Als** Entwickler
**möchte ich** standardisierte Visualisierungskomponenten für alle Phasen- und Zyklus-Darstellungen verwenden
**um** konsistentes Aussehen und Verhalten über die gesamte Anwendung sicherzustellen.

### 1.2 Geschäftliche Motivation

Die Anwendung visualisiert Pflanzen-Lebenszyklus-Daten an zahlreichen Stellen (Pflanzendetail, Durchlauf-Detail, Kalender, Nährstoffplan). Ohne einheitliche Standards entstehen inkonsistente Darstellungen, die den Nutzer verwirren. Diese UI-NFR definiert das **visuelle Vokabular** für alle phasenbezogenen Darstellungen als verbindliche Referenz.

---

## 2. Visualisierungsvarianten

Das System MUSS folgende Visualisierungsvarianten unterstützen. Jede Variante hat einen definierten Einsatzkontext und standardisierte Darstellungsregeln.

### 2.1 Varianten-Übersicht

| ID | Variante | Einsatzkontext | Datenquelle | Komponente |
|----|----------|---------------|-------------|------------|
| V-001 | Kami-Phase-Timeline | Pflanzendetail-Seite (PlantInstanceDetailPage) | GrowthPhases + PhaseHistory | `PhaseKamiTimeline` |
| V-002 | Vertikaler Phase-Stepper | Durchlauf-Detail-Seite (PlantingRunDetailPage) | SpeciesPhaseTimeline API | `PhaseTimelineStepper` |
| V-003 | Horizontaler Gantt (Monatsansicht) | Kalender-Seite (CalendarPage, Tab "Phasen") | CalendarEvent (phase_transition) | `PhaseTimelineView` |
| V-004 | Saisonübersicht (12-Monats-Karten) | Kalender-Seite (CalendarPage, Tab "Saisonübersicht") | MonthSummary API | `SeasonOverviewView` |
| V-005 | Dünger-Gantt (Phasen × Produkte) | Nährstoffplan-Detail (NutrientPlanDetailPage) | NutrientPlanPhaseEntry | `PhaseGanttChart`, `FertilizerGanttChart` |
| V-006 | Saisonaler Zyklus-Ring | Pflanzendetail (perenniale Pflanzen) | SeasonalCycle + PhaseHistory | _Neu zu implementieren_ |

---

## 3. Gemeinsame Darstellungsregeln

### 3.1 Phasenstatus-Codierung (R-001 bis R-005)

Alle Visualisierungsvarianten MÜSSEN die gleiche visuelle Codierung für den Phasenstatus verwenden:

| # | Regel | Stufe |
|---|-------|-------|
| R-001 | **Abgeschlossene Phasen** (`completed`) MÜSSEN mit voller Farbsättigung und Opazität 1.0 dargestellt werden. | MUSS |
| R-002 | **Aktive Phase** (`current`) MUSS visuell hervorgehoben werden: dickerer Rahmen ODER Leuchteffekt (drop-shadow/glow) ODER Pulsation. Die aktive Phase MUSS ohne Scrollen/Interaktion sofort erkennbar sein. | MUSS |
| R-003 | **Projizierte Phasen** (`projected`) MÜSSEN mit reduzierter Opazität (0.3–0.5) ODER Schraffur/gestricheltem Rahmen dargestellt werden, um den Unterschied zu tatsächlichen Daten klar zu kommunizieren. | MUSS |
| R-004 | **Dormanz-Phasen** (`dormancy`) MÜSSEN farblich vom aktiven Wachstum unterscheidbar sein (kühles Grau/Blaugrau statt Grüntöne). | MUSS |
| R-005 | Wenn eine Phase `is_recurring: true` ist, SOLL dies durch ein dezentes Wiederhol-Symbol (↻) oder Beschriftung signalisiert werden. | SOLL |

### 3.2 Phasenfarbpalette (R-006 bis R-009)

| # | Regel | Stufe |
|---|-------|-------|
| R-006 | Alle Phasen-Visualisierungen MÜSSEN dieselbe Farbpalette verwenden. Die kanonische Zuordnung ist: | MUSS |

```
Phase               Farbe       Hex
─────────────────────────────────────────
germination         Zartgrün    #A5D6A7
seedling            Frühlingsgrün #81C784
vegetative          Sattes Grün #4CAF50
flowering           Pink/Magenta #F48FB1
ripening            Pfirsich    #FFCC80
harvest             Orange      #FFB74D
drying              Warmes Grau #BCAAA4
curing              Mittelbraun #A1887F
flushing            Hellblau    #90CAF9
juvenile            Limettengrün #C5E1A5
climbing            Frühlingsgrün #AED581
mature              Mittelgrün  #66BB6A
dormancy            Kühlgrau    #B0BEC5
senescence          Blassrot    #EF9A9A
establishment       Zartgrün    #A5D6A7
hardening_off       Mintgrün    #B2DFDB
budding             Lavendel    #CE93D8
pre_bloom           Lavendel    #CE93D8
recovery            Türkis      #80CBC4
sprouting           Limettengrün #C5E1A5
tuber_formation     Pfirsich    #FFCC80
corm_ripening       Pfirsich    #FFCC80
```

| # | Regel | Stufe |
|---|-------|-------|
| R-007 | Unbekannte Phasennamen MÜSSEN über einen deterministischen Hash-Algorithmus eine Farbe aus einer Fallback-Palette erhalten, sodass dieselbe Phase immer dieselbe Farbe bekommt. | MUSS |
| R-008 | Die Farbpalette MUSS mit UI-NFR-009 §4.2 (Phasenfarben) konsistent sein. Bei Abweichungen hat diese UI-NFR Vorrang, da sie die vollständige Palette definiert. | MUSS |
| R-009 | Phasenfarben MÜSSEN sowohl im Light- als auch im Dark-Mode ausreichend Kontrast bieten (mind. 3:1 gegen den Hintergrund gemäß WCAG AA für nicht-textuelle Elemente). | MUSS |

### 3.3 Maskottchen-Integration (R-010 bis R-012)

| # | Regel | Stufe |
|---|-------|-------|
| R-010 | Die Kami-Phase-Timeline (V-001) MUSS für jede Phase eine passende Kami-Illustration anzeigen, sofern verfügbar. Fehlende Illustrationen werden durch den farbigen Punkt allein dargestellt. | MUSS |
| R-011 | Kami-Phasen-Illustrationen MÜSSEN im Verzeichnis `assets/brand/illustrations/phases/` als SVG vorliegen und der Namenskonvention `timeline-kami-phase-{phasename}.svg` folgen. | MUSS |
| R-012 | Die Illustration der aktiven Phase SOLL visuell hervorgehoben werden (z.B. Leuchteffekt `drop-shadow(0 0 8px rgba(76, 175, 80, 0.6))`), projizierte Phasen SOLLEN entsättigt dargestellt werden (`grayscale(0.6)`). | SOLL |

### 3.4 Dauer-Anzeige (R-013 bis R-015)

| # | Regel | Stufe |
|---|-------|-------|
| R-013 | Abgeschlossene Phasen MÜSSEN die tatsächliche Dauer in Tagen anzeigen (`actual_duration_days`). | MUSS |
| R-014 | Aktive Phasen MÜSSEN die bisherige Dauer und die typische Dauer im Format `{aktuell}d / {typisch}d` ODER als Progress-Indikator anzeigen. | MUSS |
| R-015 | Projizierte Phasen SOLLEN die typische Dauer in kursiver Schrift anzeigen, um den Unterschied zu tatsächlichen Daten zu verdeutlichen. | SOLL |

### 3.5 Tooltips & Interaktion (R-016 bis R-019)

| # | Regel | Stufe |
|---|-------|-------|
| R-016 | Alle Phasen-Elemente MÜSSEN bei Hover/Touch einen Tooltip mit Phasenname, Start-/Enddatum und Dauer anzeigen. | MUSS |
| R-017 | Tooltips SOLLEN art-spezifische Phasenbeschreibungen anzeigen (`enums.phaseDescriptions.{species_slug}.{phase}`), mit Fallback auf generische Beschreibungen (`enums.phaseDescription.{phase}`). | SOLL |
| R-018 | Klickbare Phasen SOLLEN zur relevanten Detailansicht navigieren (z.B. Pflanze, Durchlauf). | SOLL |
| R-019 | Alle Timeline-Visualisierungen MÜSSEN touch-freundlich sein (Mindest-Tippziel 44×44px gemäß UI-NFR-002). | MUSS |

---

## 4. Varianten-spezifische Anforderungen

### 4.1 V-001: Kami-Phase-Timeline (Horizontale Illustration)

**Einsatz:** Pflanzendetail-Seite, Phasen-Tab

```
  ┌─────────────────────────────────────────────────────────────────────┐
  │  [🌱Kami]──────[🌿Kami]──────[🌸Kami]──────[🍂Kami]──────[💤Kami]  │
  │    ●             ●             ●̣             ○             ○       │
  │  Keimung      Vegetativ     Blüte ←aktiv   Seneszenz    Dormanz    │
  │  14d           42d          Tag 12/35       ~30d         ~90d      │
  │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌ │
  │  ■ abgeschlossen             ■ aktiv         ■ projiziert          │
  └─────────────────────────────────────────────────────────────────────┘
```

| # | Regel | Stufe |
|---|-------|-------|
| R-020 | Die Kami-Timeline MUSS als horizontale Leiste mit verbindenden Linien zwischen den Phasen-Punkten dargestellt werden. | MUSS |
| R-021 | Verbindungslinien zwischen abgeschlossenen Phasen MÜSSEN in der Phasenfarbe gefüllt sein; Linien zu projizierten Phasen MÜSSEN in `action.disabled` dargestellt werden. | MUSS |
| R-022 | Die Kami-Illustrations-Größe MUSS responsiv skalieren: xs: 56px, sm: 72px, md: 88px. | MUSS |
| R-023 | Bei Pflanzen mit zyklischen Phasen (`is_recurring: true`) SOLL die Timeline den aktuellen Zyklus anzeigen, mit einem Hinweis auf die Zyklusnummer (z.B. "Saison 3"). | SOLL |

### 4.2 V-002: Vertikaler Phase-Stepper

**Einsatz:** Durchlauf-Detail-Seite (PlantingRunDetailPage), Phasen-Tab

```
  ┌──────────────────────────────────────────────┐
  │  ✅ Keimung                                  │
  │  │  01.03. – 14.03.2026 (14d)               │
  │  │                                           │
  │  ✅ Sämling                                  │
  │  │  15.03. – 04.04.2026 (21d)               │
  │  │                                           │
  │  ● Vegetativ  ← aktiv                       │
  │  │  05.04. – heute (Tag 12 von ~35d)        │
  │  │  Voraussichtliches Ende: 10.05.2026       │
  │  │                                           │
  │  ○ Blüte                                     │
  │  │  ~35d (projiziert)                        │
  │  │                                           │
  │  ○ Ernte                                     │
  │     ~14d (projiziert)                        │
  └──────────────────────────────────────────────┘
```

| # | Regel | Stufe |
|---|-------|-------|
| R-024 | Der Stepper MUSS MUI `Stepper` mit `orientation="vertical"` verwenden. | MUSS |
| R-025 | Jeder Schritt MUSS ein Custom-StepIcon verwenden: ✅ (completed), 🔵 (current), ⚪ (projected). | MUSS |
| R-026 | Kami-Phasen-Illustrationen SOLLEN neben dem Phasennamen angezeigt werden (32×32px). | SOLL |
| R-027 | Bei mehreren Spezies im Durchlauf MUSS pro Spezies ein separater Stepper mit Spezies-Name und Pflanzenanzahl angezeigt werden. | MUSS |

### 4.3 V-003: Horizontaler Gantt (Monatsansicht)

**Einsatz:** Kalender-Seite, Tab "Phasen-Timeline"

```
  ┌────────────┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┐
  │ März 2026  │ 1│ 2│ 3│ 4│ 5│ 6│ 7│ 8│...                     │
  ├────────────┼──┴──┴──┴──┴──┴──┴──┴──┴─────────────────────────┤
  │ Durchlauf A│                                                  │
  │  Tomate #1 │ ██████████ Vegetativ ██████████│░░░ Blüte ░░░░░ │
  │  Tomate #2 │ ████████ Veg ████████│█████ Blüte █████│░░░░░░░ │
  │ Durchlauf B│                                                  │
  │  Basilikum │ ████ Keim ████│██████████ Vegetativ ██████████│  │
  ├────────────┴──────────────────────────────────────────────────┤
  │  ■ Vegetativ  ■ Blüte  ■ Keimung  │ Heute                   │
  └───────────────────────────────────────────────────────────────┘
```

| # | Regel | Stufe |
|---|-------|-------|
| R-028 | Der Gantt MUSS als CSS-Grid mit einer Spalte pro Tag des Monats dargestellt werden. | MUSS |
| R-029 | Pflanzen MÜSSEN nach Durchlauf gruppiert werden; Durchlauf-Header sind als Zwischenzeilen dargestellt. | MUSS |
| R-030 | Projizierte Phasen MÜSSEN mit diagonaler Schraffur (`repeating-linear-gradient 45deg`) und gestricheltem Rahmen dargestellt werden. | MUSS |
| R-031 | Der aktuelle Tag MUSS durch eine vertikale Markierung (farbiger Hintergrund-Streifen) hervorgehoben werden. | MUSS |
| R-032 | Wochenenden SOLLEN durch dezent abweichende Hintergrundfarbe (`action.hover` mit Opazität 0.3–0.5) erkennbar sein. | SOLL |
| R-033 | Pflanzen-Labels MÜSSEN sticky (links fixiert) sein, damit sie beim horizontalen Scrollen sichtbar bleiben. | MUSS |
| R-034 | Filter für Durchlauf und Pflanze MÜSSEN oberhalb des Gantt angeboten werden (Autocomplete, multiple). | MUSS |
| R-035 | Eine Legende MUSS unter dem Gantt die verwendeten Phasenfarben erklären. | MUSS |

### 4.4 V-004: Saisonübersicht (12-Monats-Karten)

**Einsatz:** Kalender-Seite, Tab "Saisonübersicht"

```
  ┌──────────────────────────────────────────────────────────────┐
  │ Saisonübersicht 2026                                        │
  │ ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐    │
  │ │ Januar    │ │ Februar   │ │ *März*    │ │ April     │    │
  │ │ 🌱 0      │ │ 🌱 2      │ │ 🌱 5      │ │ 🌱 3      │    │
  │ │ 🌾 0      │ │ 🌾 0      │ │ 🌾 0      │ │ 🌾 0      │    │
  │ │ 🌸 0      │ │ 🌸 0      │ │ 🌸 1      │ │ 🌸 4      │    │
  │ │ 📋 3      │ │ 📋 5      │ │ 📋 12     │ │ 📋 8      │    │
  │ └───────────┘ └───────────┘ └───────────┘ └───────────┘    │
  │ ...                                                         │
  └──────────────────────────────────────────────────────────────┘
```

| # | Regel | Stufe |
|---|-------|-------|
| R-036 | Jeder Monat MUSS als MUI `Card` in einem responsiven Grid dargestellt werden (xs: 6, sm: 4, md: 3). | MUSS |
| R-037 | Der aktuelle Monat MUSS visuell hervorgehoben werden (Rahmen in `primary.main`, leicht getönter Hintergrund). | MUSS |
| R-038 | Jede Karte MUSS vier Kennzahlen mit Icon anzeigen: Aussaat (🌱), Ernte (🌾), Blüte (🌸), Aufgaben (📋). | MUSS |
| R-039 | Klick auf eine Monatskarte SOLL zur Monatsansicht des Kalenders navigieren. | SOLL |

### 4.5 V-005: Dünger-Gantt (Phasen × Produkte)

**Einsatz:** Nährstoffplan-Detail, Pflanzeninstanz-Detail (Nährstoffplan-Tab)

```
  ┌──────────────┬──────────┬──────────┬──────────┬──────────┐
  │              │ Keimung  │ Vegetativ│ Blüte    │ Reife    │
  │              │ (14d)    │ (35d)    │ (42d)    │ (14d)    │
  ├──────────────┼──────────┼──────────┼──────────┼──────────┤
  │ Terra Grow   │          │ ████████ │          │          │
  │ Terra Bloom  │          │          │ ████████ │ ████████ │
  │ Power Roots  │ ████████ │ ████     │          │          │
  │ Green Sens.  │          │          │     ████ │ ████████ │
  └──────────────┴──────────┴──────────┴──────────┴──────────┘
```

**Zwei Modi:** Das Dünger-Gantt MUSS abhängig vom Plantyp (`cycle_restart_from_sequence`) in einem von zwei Modi dargestellt werden:

**Modus A — Einjähriger Plan (Samen → Ernte):** Linearer Zeitstrahl von der ersten bis zur letzten Phase. Anwendbar bei `cycle_restart_from_sequence = null`. Stellt den vollständigen Lebenszyklus einer einjährigen Pflanze dar (z.B. Cannabis: Keimung → Sämling → Vegetativ → Blüte → Ernte). Der Zeitstrahl endet nach der letzten Phase.

**Modus B — Saisonaler Zyklus (perennial/wiederkehrend):** Zeitstrahl mit Zyklus-Grenze. Anwendbar bei `cycle_restart_from_sequence ≠ null`. Stellt den wiederkehrenden Jahres-Nährstoffzyklus einer mehrjährigen Pflanze dar (z.B. Monstera: Vegetativ ↔ Dormanz). Die Zyklus-Grenze wird als vertikale Markierungslinie dargestellt. Phasen links davon (einmalige Setup-Phasen) und rechts davon (wiederkehrende Phasen mit ↻-Symbol) sind visuell unterscheidbar.

| # | Regel | Stufe |
|---|-------|-------|
| R-040 | Der Dünger-Gantt MUSS Phasen als Spalten und Düngerprodukte als Zeilen darstellen. | MUSS |
| R-041 | Spaltenbreiten MÜSSEN proportional zur typischen Phasendauer sein. | MUSS |
| R-042 | Phasenspalten-Header MÜSSEN die Phasenfarbe als Hintergrund verwenden. | MUSS |
| R-043 | Dünger-Balken SOLLEN die Dosierung als Tooltip anzeigen (ml/L, g/m²). | SOLL |
| R-043a | Bei saisonalen Plänen (`cycle_restart_from_sequence ≠ null`) MUSS die Zyklus-Grenze als gestrichelte vertikale Linie dargestellt werden, mit dem Hinweis „↻ Zyklus wiederholt ab Phase X". | MUSS |
| R-043b | Einmalige Setup-Phasen (`sequence_order < cycle_restart_from_sequence`) MÜSSEN visuell von wiederkehrenden Phasen unterscheidbar sein (z.B. leicht abweichender Hintergrund, kein ↻-Symbol). | MUSS |
| R-043c | Die Modus-Erkennung (A vs. B) MUSS automatisch erfolgen, ohne manuellen Toggle. | MUSS |

### 4.6 V-006: Saisonaler Zyklus-Ring (Perenniale Pflanzen)

**Einsatz:** Pflanzendetail-Seite, bei perennialen Pflanzen mit `cycle_type: 'perennial'`

Diese Variante visualisiert den **wiederkehrenden Jahres-Zyklus** einer mehrjährigen Pflanze als kreisförmiges Diagramm, um die zyklische Natur (statt linearem Fortschritt) intuitiv darzustellen.

```
  ┌──────────────────────────────────────────────────────────┐
  │  Saison 3 (2026)                                        │
  │                                                          │
  │              Jan   Feb                                   │
  │          Dez ╭─────────╮ Mär                             │
  │         ╱  ░░░DORMANZ░░░  ╲                              │
  │   Nov  │  ░░░░░░░░░░░░░░░  │ Apr                        │
  │        │ Senes ┊    ┊ Austr │                            │
  │   Okt  │ ████  ○    ┊ ████ │ Mai                        │
  │        │ Reife ┊    ┊ Veg  │                            │
  │   Sep  │  █████████████████  │ Jun                       │
  │         ╲  ██████████████  ╱                             │
  │          ╰─────────────╯                                 │
  │           Aug   Jul   Jun                                │
  │                ← BLÜTE                                   │
  │                                                          │
  │  ● Aktuell: Vegetativ (Tag 15 von ~60d)                 │
  │  Saison-Start: 01.03.2026                               │
  │  Reifegrad: Produktiv                                    │
  │  Kältestunden letzte Dormanz: 850h                       │
  └──────────────────────────────────────────────────────────┘
```

| # | Regel | Stufe |
|---|-------|-------|
| R-044 | Der Zyklus-Ring MUSS als kreisförmiges Diagramm (radial chart) dargestellt werden, das den 12-Monats-Zyklus als 360°-Ring abbildet. | MUSS |
| R-045 | Jede Phase MUSS als Bogensegment im Ring dargestellt werden, proportional zu ihrer typischen Dauer. | MUSS |
| R-046 | Die Phasenfarbpalette aus R-006 MUSS verwendet werden. | MUSS |
| R-047 | Die aktive Phase MUSS durch einen hervorgehobenen Marker (Punkt/Pfeil) auf der aktuellen Position im Zyklus markiert werden. | MUSS |
| R-048 | Unter dem Ring MÜSSEN folgende Metadaten angezeigt werden: aktuelle Phase, Tag im Zyklus, Saisonnummer, Reifegrad (`maturity_stage`), Kältestunden der letzten Dormanz. | MUSS |
| R-049 | Der Ring SOLL die Monate als Beschriftung auf der Außenseite anzeigen (Jan–Dez im Uhrzeigersinn, Start oben). | SOLL |
| R-050 | Der Zyklus-Ring SOLL nur bei Pflanzen mit `cycle_type: 'perennial'` und mindestens einer abgeschlossenen Saison angezeigt werden. Bei annuellen Pflanzen MUSS stattdessen die Kami-Phase-Timeline (V-001) verwendet werden. | SOLL |
| R-051 | Ein Dropdown/Tab SOLL den Vergleich zwischen verschiedenen Saisonen ermöglichen (Overlay oder nebeneinander). | SOLL |
| R-052 | Dormanz-Segmente MÜSSEN mit dem Dormanz-Pattern (Schraffur oder dezentes Schneeflocken-Muster) visuell vom aktiven Wachstum unterschieden werden. | MUSS |

---

## 5. Responsive Verhalten (R-053 bis R-057)

| # | Regel | Stufe |
|---|-------|-------|
| R-053 | Auf mobilen Geräten (< 600px) DARF der Gantt (V-003) horizontal scrollbar sein; Pflanzen-Labels MÜSSEN sticky bleiben. | MUSS |
| R-054 | Die Kami-Timeline (V-001) MUSS auf schmalen Viewports automatisch skalieren (kleinere Illustrationen, kompaktere Abstände). Phasennamen DÜRFEN auf Abkürzungen (3 Buchstaben) reduziert werden. | MUSS |
| R-055 | Der Zyklus-Ring (V-006) MUSS eine Mindestgröße von 200×200px haben und auf kleineren Viewports DARF er in eine vertikale Liste der Phasen umschalten (Fallback). | MUSS |
| R-056 | Saisonübersicht-Karten (V-004) MÜSSEN sich von 4 Spalten (Desktop) auf 2 Spalten (Mobil) reduzieren. | MUSS |
| R-057 | Der vertikale Stepper (V-002) SOLL auf mobilen Geräten kompaktere Step-Labels verwenden (Illustration 24×24px statt 32×32px). | SOLL |

---

## 6. Barrierefreiheit (R-058 bis R-061)

| # | Regel | Stufe |
|---|-------|-------|
| R-058 | Alle farbcodierten Phasen MÜSSEN neben der Farbe einen zweiten Unterscheidungskanal bieten (Text-Label, Pattern oder Icon), sodass farbenblinde Nutzer Phasen unterscheiden können (→ UI-NFR-002). | MUSS |
| R-059 | Gantt-Balken und Ring-Segmente MÜSSEN per Tastatur fokussierbar sein und einen Screenreader-Text mit Phasenname, Status und Dauer bereitstellen. | MUSS |
| R-060 | Tooltips MÜSSEN bei Tastatur-Fokus (nicht nur Hover) erscheinen. | MUSS |
| R-061 | Animationen (Glow, Pulsation) MÜSSEN `prefers-reduced-motion` respektieren. | MUSS |

---

## 7. Performance (R-062 bis R-064)

| # | Regel | Stufe |
|---|-------|-------|
| R-062 | Der Gantt (V-003) MUSS bei bis zu 50 Pflanzen-Zeilen × 31 Tagen performant rendern (< 100ms). Bei mehr Zeilen SOLL Virtualisierung eingesetzt werden. | MUSS |
| R-063 | SVG-Illustrationen (Kami-Phasen) MÜSSEN als statische Imports geladen werden (Tree-Shakeable, kein dynamisches Laden pro Phase). | MUSS |
| R-064 | Der Zyklus-Ring (V-006) SOLL als SVG (nicht Canvas) gerendert werden, um Skalierbarkeit und Barrierefreiheit sicherzustellen. | SOLL |

---

## 8. Implementierte Referenzkomponenten

Die folgenden Komponenten implementieren die oben definierten Varianten und dienen als **verbindliche Referenz** für zukünftige Visualisierungen:

| Komponente | Pfad | Variante | Status |
|-----------|------|----------|--------|
| `PhaseKamiTimeline` | `src/frontend/src/pages/durchlaeufe/PhaseKamiTimeline.tsx` | V-001 | Implementiert |
| `PlantPhaseTimeline` | `src/frontend/src/pages/pflanzen/PlantPhaseTimeline.tsx` | V-001 (Wrapper) | Implementiert |
| `PhaseTimelineStepper` | `src/frontend/src/pages/durchlaeufe/PhaseTimelineStepper.tsx` | V-002 | Implementiert |
| `PhaseTimelineView` | `src/frontend/src/pages/kalender/PhaseTimelineView.tsx` | V-003 | Implementiert |
| `SeasonOverviewView` | `src/frontend/src/pages/kalender/SeasonOverviewView.tsx` | V-004 | Implementiert |
| `PhaseGanttChart` | `src/frontend/src/pages/duengung/PhaseGanttChart.tsx` | V-005 | Implementiert |
| `FertilizerGanttChart` | `src/frontend/src/pages/duengung/FertilizerGanttChart.tsx` | V-005 | Implementiert |
| `FertilizerUsageGantt` | `src/frontend/src/pages/duengung/FertilizerUsageGantt.tsx` | V-005 | Implementiert |
| _SeasonalCycleRing_ | — | V-006 | **Noch nicht implementiert** |

---

## 9. Akzeptanzkriterien

### Definition of Done

- [ ] Alle implementierten Varianten (V-001 bis V-005) entsprechen den gemeinsamen Darstellungsregeln (R-001 bis R-019)
- [ ] Die Phasenfarbpalette (R-006) ist zentral definiert und wird von allen Komponenten referenziert (keine Duplikation)
- [ ] Status-Codierung (completed/current/projected) ist visuell konsistent über alle Varianten
- [ ] Kami-Illustrationen sind in allen Phasen-Timelines korrekt eingebunden
- [ ] Tooltips mit Phasendetails funktionieren bei Hover und Tastatur-Fokus
- [ ] Responsive Verhalten ist auf xs/sm/md/lg Viewports getestet
- [ ] Dark-Mode-Kompatibilität ist sichergestellt (Phasenfarben haben ausreichend Kontrast)
- [ ] V-006 (Zyklus-Ring) ist für perenniale Pflanzen spezifiziert und kann implementiert werden

### Testszenarien

**GIVEN** eine perenniale Pflanze (Monstera) in der aktiven Wachstumsphase
**WHEN** der Nutzer die Pflanzendetail-Seite öffnet
**THEN** wird der Zyklus-Ring (V-006) mit aktuellem Monat und aktiver Phase angezeigt; die Dormanz-Phase ist farblich abgegrenzt.

**GIVEN** ein Pflanzdurchlauf mit 5 Pflanzen in verschiedenen Phasen
**WHEN** der Nutzer die Kalender-Seite im Phasen-Tab öffnet
**THEN** zeigt der Gantt (V-003) alle Pflanzen mit korrekten Phasenfarben, sticky Labels und Heute-Markierung.

**GIVEN** eine annuelle Pflanze (Tomate) im Durchlauf
**WHEN** der Nutzer die Pflanzendetail-Seite öffnet
**THEN** wird die Kami-Phase-Timeline (V-001) mit Illustrationen angezeigt; die aktive Phase hat einen Leuchteffekt, projizierte Phasen sind entsättigt.

**GIVEN** Dark-Mode ist aktiviert
**WHEN** der Nutzer eine beliebige Phasen-Visualisierung betrachtet
**THEN** sind alle Phasenfarben gegen den dunklen Hintergrund erkennbar (WCAG AA 3:1 für nicht-textuelle Elemente).

---

## 10. Risiken bei Nicht-Einhaltung

| Risiko | Auswirkung | Wahrscheinlichkeit | Mitigation |
|--------|-----------|---------------------|------------|
| **Inkonsistente Farbpalette** | Nutzer können Phasen nicht über verschiedene Ansichten hinweg wiedererkennen | Hoch | Zentrale Farbpalette als TypeScript-Konstante, nicht inline |
| **Fehlende Status-Unterscheidung** | Nutzer verwechseln projizierte mit tatsächlichen Daten → falsche Entscheidungen | Hoch | Klare visuelle Trennung (Opazität + Schraffur) |
| **Lineare Darstellung für zyklische Pflanzen** | Perenniale Pflanzen wirken wie "abgeschlossen" nach der ersten Saison | Mittel | Zyklus-Ring (V-006) für wiederkehrende Zyklen |
| **Performance bei vielen Pflanzen** | Gantt-Ansicht ruckelt oder friert ein | Mittel | Virtualisierung ab 50 Zeilen, keine DOM-Elemente für leere Zellen |
| **Barrierefreiheits-Mängel** | Farbenblinde Nutzer können Phasen nicht unterscheiden | Mittel | Zweiter Kanal (Text + Pattern) neben Farbe |

---

**Dokumenten-Ende**

**Version**: 1.0
**Status**: Entwurf
**Letzte Aktualisierung**: 2026-03-11
**Review**: Pending
**Genehmigung**: Pending
