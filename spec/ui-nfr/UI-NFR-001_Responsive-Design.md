---

ID: UI-NFR-001
Titel: Responsive Design & Layout
Kategorie: UI-Verhalten Unterkategorie: Layout, Responsiveness
Technologie: React, TypeScript, MUI, Flutter
Status: Entwurf
Priorität: Hoch
Version: 1.0
Autor: Business Analyst - Agrotech
Datum: 2026-02-26
Tags: [responsive, mobile-first, breakpoints, layout, touch-targets]
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
| R-001 | Die Anwendung MUSS drei Breakpoints definieren: Mobile (≤768px), Tablet (≤1024px), Desktop (>1024px). | MUSS |
| R-002 | Alle Layouts MÜSSEN nach dem Mobile-First-Ansatz entwickelt werden — die mobile Darstellung ist die Basislinie, größere Viewports erweitern das Layout. | MUSS |
| R-003 | Breakpoints SOLLEN über Design-Tokens oder Konfigurationsvariablen zentral definiert werden, nicht hartcodiert in einzelnen Komponenten. | SOLL |

### 2.2 Viewport & Scrolling

| # | Regel | Stufe |
|---|-------|-------|
| R-004 | Jede Seite MUSS ein `<meta name="viewport" content="width=device-width, initial-scale=1">` Tag enthalten (Web). | MUSS |
| R-005 | Es DÜRFEN KEINE horizontalen Scrollbars auf der Hauptseite entstehen — der gesamte Inhalt MUSS innerhalb der Viewport-Breite dargestellt werden. | MUSS |
| R-006 | Horizontales Scrollen DARF nur innerhalb expliziter Scroll-Container (z.B. Tabellen, Code-Blöcke) auftreten. | MUSS |

### 2.3 Grid & Container

| # | Regel | Stufe |
|---|-------|-------|
| R-007 | Layouts MÜSSEN auf einem Fluid-Grid basieren (prozentuale Breiten, nicht fixe Pixel-Werte). | MUSS |
| R-008 | Container MÜSSEN eine Maximalbreite definieren (empfohlen: 1280px für Desktop), um auf sehr breiten Bildschirmen lesbar zu bleiben. | MUSS |
| R-008a | Der Hauptinhaltsbereich MUSS bei ausgeklappter Sidebar direkt (ohne sichtbare Lücke) an die Navigation anschließen — der Content-Bereich DARF NICHT durch doppelte Abstände (z.B. Sidebar-Breite im Flex-Layout plus zusätzliches Margin) von der Navigation abgesetzt werden. | MUSS |
| R-009 | Das Grid SOLL ein 12-Spalten-System verwenden mit konfigurierbarem Gutter (Standard: 16px mobile, 24px Desktop). | SOLL |

### 2.4 Touch-Targets

| # | Regel | Stufe |
|---|-------|-------|
| R-010 | Interaktive Elemente (Buttons, Links, Checkboxen) MÜSSEN eine Mindestgröße von 48×48px für Touch-Targets einhalten. | MUSS |
| R-011 | Der Mindestabstand zwischen zwei Touch-Targets SOLL 8px betragen, um versehentliche Fehleingaben zu vermeiden. | SOLL |
| R-012 | Auf Desktop KANN die Touch-Target-Größe auf 36×36px reduziert werden, sofern die Mausbedienung im Vordergrund steht. | KANN |

### 2.5 Bilder & Medien

| # | Regel | Stufe |
|---|-------|-------|
| R-013 | Bilder MÜSSEN responsive sein (`max-width: 100%; height: auto`) und sich an den verfügbaren Platz anpassen. | MUSS |
| R-014 | Für verschiedene Bildschirmauflösungen SOLLEN `srcset`- oder äquivalente Mechanismen verwendet werden. | SOLL |

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

### 3.3 Desktop Layout (>1024px)

```
┌──────────────────────────────────────────────────┐
│  Logo   Navigation                        👤     │
├────────┬─────────────────────────────────────────┤
│        │                                         │
│  Nav   │  ┌──────┐  ┌──────┐  ┌──────┐          │
│  Item1 │  │Karte1│  │Karte2│  │Karte3│          │  ← Drei Spalten
│  Item2 │  └──────┘  └──────┘  └──────┘          │
│  Item3 │                                         │
│  Item4 │  ┌──────┐  ┌──────┐  ┌──────┐          │
│        │  │Karte4│  │Karte5│  │Karte6│          │
│        │  └──────┘  └──────┘  └──────┘          │
│        │                                         │
└────────┴─────────────────────────────────────────┘
```

---

## 4. Akzeptanzkriterien

### Definition of Done

- [ ] **Breakpoints**
    - [ ] Drei Breakpoints (Mobile, Tablet, Desktop) sind zentral definiert
    - [ ] Layouts passen sich bei Breakpoint-Wechsel korrekt an
    - [ ] Mobile-First-Ansatz: CSS/Styles basieren auf der kleinsten Auflösung
- [ ] **Viewport**
    - [ ] Viewport-Meta-Tag ist auf jeder Seite gesetzt
    - [ ] Keine horizontalen Scrollbars auf der Hauptseite
    - [ ] Inhalte sind auf 320px Viewport-Breite nutzbar
- [ ] **Grid & Container**
    - [ ] Fluid Grid ist implementiert
    - [ ] Container-Maximalbreite ist gesetzt
    - [ ] Gutter-Werte passen sich pro Breakpoint an
- [ ] **Touch-Targets**
    - [ ] Alle interaktiven Elemente erreichen 48×48px Touch-Target-Größe auf Mobile/Tablet
    - [ ] Mindestabstand zwischen Touch-Targets ist eingehalten
- [ ] **Testing**
    - [ ] Layout-Tests auf Viewport-Breiten: 320px, 768px, 1024px, 1440px
    - [ ] Keine Layout-Brüche bei stufenloser Größenänderung des Browserfensters
    - [ ] Manuelle Tests auf mindestens einem realen Mobilgerät und einem Tablet

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

**Version**: 1.0
**Status**: Entwurf
**Letzte Aktualisierung**: 2026-02-26
**Review**: Pending
**Genehmigung**: Pending
