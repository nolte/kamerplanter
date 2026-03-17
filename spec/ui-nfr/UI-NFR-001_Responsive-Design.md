---

ID: UI-NFR-001
Titel: Responsive Design & Layout
Kategorie: UI-Verhalten Unterkategorie: Layout, Responsiveness
Technologie: React, TypeScript, MUI, Flutter
Status: Entwurf
Priorität: Hoch
Version: 2.0
Autor: Business Analyst - Agrotech
Datum: 2026-03-17
Tags: [responsive, mobile-first, breakpoints, layout, touch-targets, fluid, fullwidth, grid, widescreen]
Abhängigkeiten: []
Betroffene Module: [Frontend, Mobile]
---

# UI-NFR-001: Responsive Design & Layout

## 1. Business Case

### 1.1 User Story

**Als** Endanwender
**möchte ich** die Anwendung auf jedem Gerät (Smartphone, Tablet, Desktop) komfortabel bedienen können
**um** nicht an einen bestimmten Gerätetyp gebunden zu sein und flexibel arbeiten zu können.

**Als** Produktmanager
**möchte ich** dass die Anwendung auf allen gängigen Bildschirmgrößen nutzbar ist
**um** eine maximale Reichweite und Nutzerzufriedenheit zu erzielen.

**Als** Frontend-Entwickler
**möchte ich** klare Breakpoint-Definitionen und Layout-Regeln
**um** konsistente Layouts ohne gerätesspezifische Sonderlösungen zu implementieren.

### 1.2 Geschäftliche Motivation

Eine Anwendung, die nur auf dem Desktop nutzbar ist, schließt einen großen Teil der Nutzer aus — insbesondere in Szenarien, in denen vor Ort (z.B. im Gewächshaus oder auf dem Balkon) mobil gearbeitet wird.

1. **Mobile Nutzung** — Anwender arbeiten häufig unterwegs oder vor Ort mit dem Smartphone
2. **Tablet-Nutzung** — Tablets dienen als Eingabegerät bei der praktischen Arbeit
3. **Desktop-Nutzung** — Planung und Auswertung erfolgen bevorzugt am Desktop
4. **Gerätewechsel** — Nutzer wechseln innerhalb einer Session zwischen Geräten

---

## 2. Anforderungen

### 2.1 Breakpoint-Definitionen

| # | Regel | Stufe |
|---|-------|-------|
| R-001 | Die Anwendung MUSS fünf Breakpoints definieren: Mobile (xs: ≤600px), Tablet (sm: ≤900px), Desktop (md: ≤1200px), Large Desktop (lg: ≤1536px), Extra Large (xl: >1536px). Diese entsprechen den MUI-Standard-Breakpoints. | MUSS |
| R-002 | Alle Layouts MÜSSEN nach dem Mobile-First-Ansatz entwickelt werden — die mobile Darstellung ist die Basislinie, größere Viewports erweitern das Layout. | MUSS |
| R-003 | Breakpoints SOLLEN über Design-Tokens oder Konfigurationsvariablen zentral definiert werden, nicht hartcodiert in einzelnen Komponenten. | SOLL |

**Breakpoint-Referenztabelle:**

| Breakpoint | MUI-Key | Breite | Typische Geräte | Spalten |
|-----------|---------|--------|-----------------|---------|
| Mobile | xs | 0–599px | Smartphone hochkant | 1 (max. 2) |
| Tablet | sm | 600–899px | Smartphone quer, kleines Tablet | 2 |
| Desktop | md | 900–1199px | Tablet quer, kleiner Laptop | 2–3 |
| Large Desktop | lg | 1200–1535px | Laptop, Standard-Monitor | 3–4 |
| Extra Large | xl | ≥1536px | Grosser Monitor, Widescreen, 4K | 4–6 |

### 2.2 Viewport & Scrolling

| # | Regel | Stufe |
|---|-------|-------|
| R-004 | Jede Seite MUSS ein `<meta name="viewport" content="width=device-width, initial-scale=1">` Tag enthalten (Web). | MUSS |
| R-005 | Es DÜRFEN KEINE horizontalen Scrollbars auf der Hauptseite entstehen — der gesamte Inhalt MUSS innerhalb der Viewport-Breite dargestellt werden. | MUSS |
| R-006 | Horizontales Scrollen DARF nur innerhalb expliziter Scroll-Container (z.B. Tabellen, Code-Blöcke) auftreten. | MUSS |

### 2.3 Grid & Container

| # | Regel | Stufe |
|---|-------|-------|
| R-007 | Layouts MÜSSEN auf einem Fluid-Grid basieren (prozentuale Breiten, nicht fixe Pixel-Werte). Die Oberfläche SOLL den gesamten verfügbaren Platz nutzen. | MUSS |
| R-008 | Der Hauptinhalt DARF KEINE starre Maximalbreite (z.B. `maxWidth: 1280px`) verwenden, die auf großen Monitoren ungenutzten Leerraum links und rechts erzeugt. Stattdessen MUSS der Content-Bereich die volle verfügbare Breite (abzüglich Sidebar und Padding) nutzen. | MUSS |
| R-008a | **Ausnahme Fließtext:** Reine Textblöcke (Beschreibungen, Notizen, Dokumentation) SOLLEN eine Maximalbreite von ca. 80ch (≈720px) einhalten, um die Lesbarkeit zu gewährleisten. Dies gilt NICHT für Tabellen, Grids, Formulare oder Karten-Layouts. | SOLL |
| R-009 | Der Hauptinhaltsbereich MUSS bei ausgeklappter Sidebar direkt (ohne sichtbare Lücke) an die Navigation anschließen — der Content-Bereich DARF NICHT durch doppelte Abstände (z.B. Sidebar-Breite im Flex-Layout plus zusätzliches Margin) von der Navigation abgesetzt werden. | MUSS |
| R-010 | Das Grid SOLL ein 12-Spalten-System verwenden mit konfigurierbarem Gutter (Standard: 16px mobile, 24px Desktop). | SOLL |

### 2.4 Dynamische Grid-Layouts für Panels und Karten

| # | Regel | Stufe |
|---|-------|-------|
| R-016 | Panels, Karten und zusammengehörige Informationsblöcke MÜSSEN in einem responsiven Grid-Layout dargestellt werden, das die Spaltenanzahl dynamisch an die verfügbare Breite anpasst. | MUSS |
| R-017 | Die Spaltenanzahl MUSS über MUI Grid `size`-Props pro Breakpoint definiert werden. Empfohlene Konfiguration für Karten-Grids: | MUSS |

**Standard-Grid-Konfiguration für Karten/Panels:**

| Inhalt | xs | sm | md | lg | xl |
|--------|----|----|----|----|-----|
| Dashboard-Karten / KPIs | 12 (1 Spalte) | 6 (2) | 4 (3) | 3 (4) | 2 (6) |
| Detail-Panels (z.B. NPK-Block, Lagerung) | 12 | 12 | 6 (2) | 6 (2) | 4 (3) |
| Formular-Sections | 12 | 12 | 12 | 12 | 12 |
| Listen-Karten (z.B. Pflanzen, Runs) | 12 | 6 (2) | 4 (3) | 3 (4) | 3 (4) |
| Monats-Karten (Saisonübersicht) | 6 (2) | 4 (3) | 3 (4) | 2 (6) | 2 (6) |

| # | Regel | Stufe |
|---|-------|-------|
| R-018 | Auf Extra-Large-Bildschirmen (xl, ≥1536px) SOLLEN Panels nebeneinander dargestellt werden, die auf kleineren Bildschirmen untereinander stehen. Beispiel: NPK-Block und Lagerungsinformationen nebeneinander statt untereinander. | SOLL |
| R-019 | Grid-Layouts MÜSSEN `spacing={2}` (16px) auf Mobile und `spacing={3}` (24px) ab md verwenden. | MUSS |
| R-020 | Einzelne Panels DÜRFEN NICHT breiter als 100% ihres Grid-Containers werden. `overflow: hidden` oder `minWidth: 0` MUSS auf Grid-Items gesetzt werden, wenn der Inhalt (z.B. Tabellen) breiter werden kann. | MUSS |
| R-021 | Tabellen innerhalb von Panels SOLLEN die volle Panel-Breite nutzen und bei Bedarf horizontal scrollbar sein (innerhalb des Panels, nicht der gesamten Seite). | SOLL |

### 2.5 Vollflächige Layouts

| # | Regel | Stufe |
|---|-------|-------|
| R-022 | Der Content-Bereich MUSS als `flex: 1` oder `width: 100%` definiert sein, sodass er den gesamten Platz rechts von der Sidebar einnimmt. | MUSS |
| R-023 | Auf großen Monitoren (lg/xl) SOLLEN Detail-Seiten ihre Sections (z.B. NPK-Hero, Anwendung, Lagerung) in einem 2- oder 3-Spalten-Grid anordnen, anstatt alles untereinander zu stapeln. | SOLL |
| R-024 | Listen-Seiten (Tabellen) MÜSSEN die volle verfügbare Breite nutzen. Tabellen DÜRFEN NICHT in einem schmalen Container zentriert werden, während links und rechts Leerraum entsteht. | MUSS |
| R-025 | Formulare SOLLEN auf großen Bildschirmen (lg/xl) Felder in 2–3 Spalten anordnen (MUI Grid), anstatt jedes Feld über die volle Breite zu strecken. Siehe auch UI-NFR-008 §2.6 Feldgruppen. | SOLL |

### 2.6 Touch-Targets

| # | Regel | Stufe |
|---|-------|-------|
| R-011 | Interaktive Elemente (Buttons, Links, Checkboxen) MÜSSEN eine Mindestgröße von 48×48px für Touch-Targets einhalten. | MUSS |
| R-012 | Der Mindestabstand zwischen zwei Touch-Targets SOLL 8px betragen, um versehentliche Fehleingaben zu vermeiden. | SOLL |
| R-013 | Auf Desktop KANN die Touch-Target-Größe auf 36×36px reduziert werden, sofern die Mausbedienung im Vordergrund steht. | KANN |

### 2.7 Bilder & Medien

| # | Regel | Stufe |
|---|-------|-------|
| R-014 | Bilder MÜSSEN responsive sein (`max-width: 100%; height: auto`) und sich an den verfügbaren Platz anpassen. | MUSS |
| R-015 | Für verschiedene Bildschirmauflösungen SOLLEN `srcset`- oder äquivalente Mechanismen verwendet werden. | SOLL |

---

## 3. Wireframe-Beispiele

### 3.1 Mobile Layout (≤768px)

```
┌──────────────────────┐
│  ☰  App-Titel        │  ← Hamburger-Menü
├──────────────────────┤
│                      │
│  ┌──────────────┐    │
│  │  Karte 1     │    │  ← Volle Breite
│  └──────────────┘    │
│                      │
│  ┌──────────────┐    │
│  │  Karte 2     │    │  ← Volle Breite
│  └──────────────┘    │
│                      │
│  ┌──────────────┐    │
│  │  Karte 3     │    │  ← Volle Breite
│  └──────────────┘    │
│                      │
├──────────────────────┤
│  🏠  📊  ⚙         │  ← Bottom Navigation
└──────────────────────┘
```

### 3.2 Tablet Layout (≤1024px)

```
┌──────────────────────────────────┐
│  Logo   Navigation       👤     │
├──────────────────────────────────┤
│                                  │
│  ┌──────────┐  ┌──────────┐     │
│  │  Karte 1 │  │  Karte 2 │     │  ← Zwei Spalten
│  └──────────┘  └──────────┘     │
│                                  │
│  ┌──────────┐  ┌──────────┐     │
│  │  Karte 3 │  │  Karte 4 │     │
│  └──────────┘  └──────────┘     │
│                                  │
└──────────────────────────────────┘
```

### 3.3 Desktop Layout (md: 900–1199px)

```
┌──────────────────────────────────────────────────┐
│  Logo   Navigation                        👤     │
├────────┬─────────────────────────────────────────┤
│        │                                         │
│  Nav   │  ┌──────┐  ┌──────┐  ┌──────┐          │
│  Item1 │  │Karte1│  │Karte2│  │Karte3│          │  ← 3 Spalten
│  Item2 │  └──────┘  └──────┘  └──────┘          │
│  Item3 │                                         │
│  Item4 │  ┌──────┐  ┌──────┐  ┌──────┐          │
│        │  │Karte4│  │Karte5│  │Karte6│          │
│        │  └──────┘  └──────┘  └──────┘          │
│        │                                         │
└────────┴─────────────────────────────────────────┘
```

### 3.4 Large Desktop Layout (lg: 1200–1535px)

```
┌──────────────────────────────────────────────────────────────────┐
│  Logo   Navigation                                       👤     │
├────────┬─────────────────────────────────────────────────────────┤
│        │                                                         │
│  Nav   │  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐               │
│  Item1 │  │Karte1│  │Karte2│  │Karte3│  │Karte4│               │  ← 4 Spalten
│  Item2 │  └──────┘  └──────┘  └──────┘  └──────┘               │
│  Item3 │                                                         │
│  Item4 │  ┌──────────────────────┐  ┌──────────────────────┐    │
│  Item5 │  │  Detail-Panel 1      │  │  Detail-Panel 2      │    │  ← Panels
│  Item6 │  │  (NPK, EC, pH)       │  │  (Lagerung, Mischen) │    │    nebeneinander
│        │  └──────────────────────┘  └──────────────────────┘    │
│        │                                                         │
└────────┴─────────────────────────────────────────────────────────┘
```

### 3.5 Extra Large Layout (xl: ≥1536px, Widescreen / 4K)

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│  Logo   Navigation                                                       👤     │
├────────┬─────────────────────────────────────────────────────────────────────────┤
│        │                                                                         │
│  Nav   │  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐          │
│  Item1 │  │Karte1│  │Karte2│  │Karte3│  │Karte4│  │Karte5│  │Karte6│          │  ← 6 Spalten
│  Item2 │  └──────┘  └──────┘  └──────┘  └──────┘  └──────┘  └──────┘          │
│  Item3 │                                                                         │
│  Item4 │  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐            │
│  Item5 │  │  Panel 1       │  │  Panel 2       │  │  Panel 3       │            │  ← 3 Panels
│  Item6 │  │  (NPK-Hero)    │  │  (Mischen)     │  │  (Lagerung)    │            │    nebeneinander
│  Item7 │  └────────────────┘  └────────────────┘  └────────────────┘            │
│  Item8 │                                                                         │
│        │  ┌─────────────────────────────────────────────────────────────┐        │
│        │  │  Tabelle (volle Breite, alle Spalten sichtbar)             │        │
│        │  └─────────────────────────────────────────────────────────────┘        │
│        │                                                                         │
└────────┴─────────────────────────────────────────────────────────────────────────┘

  ← Der Content nutzt die VOLLE verfuegbare Breite — kein Leerraum links/rechts →
```

---

## 4. Akzeptanzkriterien

### Definition of Done

- [ ] **Breakpoints**
    - [ ] Fünf Breakpoints (xs, sm, md, lg, xl) sind zentral über MUI-Theme definiert
    - [ ] Layouts passen sich bei Breakpoint-Wechsel korrekt an
    - [ ] Mobile-First-Ansatz: CSS/Styles basieren auf der kleinsten Auflösung
- [ ] **Viewport**
    - [ ] Viewport-Meta-Tag ist auf jeder Seite gesetzt
    - [ ] Keine horizontalen Scrollbars auf der Hauptseite
    - [ ] Inhalte sind auf 320px Viewport-Breite nutzbar
- [ ] **Vollflächiges Layout**
    - [ ] Keine starre `maxWidth` auf dem Content-Container
    - [ ] Content nutzt die volle verfügbare Breite (abzüglich Sidebar + Padding)
    - [ ] Auf 2560px-Monitor: kein ungenutzter Leerraum links/rechts vom Content
- [ ] **Dynamische Grids**
    - [ ] Karten/Panels nutzen MUI Grid mit Breakpoint-spezifischen `size`-Props
    - [ ] Auf xl: mindestens 4 Spalten für Dashboard-Karten
    - [ ] Auf xl: Detail-Panels nebeneinander statt nur untereinander
    - [ ] Tabellen nutzen die volle Panel-/Container-Breite
- [ ] **Touch-Targets**
    - [ ] Alle interaktiven Elemente erreichen 48×48px Touch-Target-Größe auf Mobile/Tablet
    - [ ] Mindestabstand zwischen Touch-Targets ist eingehalten
- [ ] **Testing**
    - [ ] Layout-Tests auf Viewport-Breiten: 320px, 600px, 900px, 1200px, 1536px, 2560px
    - [ ] Keine Layout-Brüche bei stufenloser Größenänderung des Browserfensters
    - [ ] Manuelle Tests auf mindestens einem realen Mobilgerät und einem Tablet
    - [ ] Visueller Check auf einem großen Monitor (≥1536px): Platz wird genutzt, Panels verteilen sich

---

## 5. Risiken bei Nicht-Einhaltung

| Risiko | Auswirkung | Wahrscheinlichkeit | Mitigation |
|---|---|---|---|
| **Nicht nutzbar auf Mobilgeräten** | Nutzer können die Anwendung unterwegs nicht verwenden | Hoch | Mobile-First-Ansatz, kontinuierliches Testing |
| **Horizontale Scrollbars** | Schlechte Benutzererfahrung, Inhalte nicht sichtbar | Mittel | Fluid Grid, Overflow-Checks in CI |
| **Zu kleine Touch-Targets** | Fehleingaben auf Touchscreens, Frustration | Hoch | Lint-Regeln für Mindestgrößen, manuelle Reviews |
| **Inkonsistente Breakpoints** | Unterschiedliches Verhalten zwischen Seiten | Mittel | Zentrale Breakpoint-Definitionen über Tokens |

---

**Dokumenten-Ende**

**Version**: 2.0
**Status**: Entwurf
**Letzte Aktualisierung**: 2026-03-17
**Review**: Pending
**Genehmigung**: Pending
