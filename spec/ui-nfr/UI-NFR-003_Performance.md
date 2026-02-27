---

ID: UI-NFR-003
Titel: Ladezeiten & Performance
Kategorie: UI-Verhalten Unterkategorie: Performance, Ladezeiten
Technologie: React, TypeScript, Vite, Flutter
Status: Entwurf
Priorität: Hoch
Version: 1.0
Autor: Business Analyst - Agrotech
Datum: 2026-02-26
Tags: [performance, loading, lazy-loading, bundle-size, core-web-vitals, skeleton]
Abhängigkeiten: []
Betroffene Module: [Frontend, Mobile]
---

# UI-NFR-003: Ladezeiten & Performance

## 1. Business Case

### 1.1 User Story

**Als** Endanwender
**möchte ich** dass die Anwendung innerhalb weniger Sekunden nutzbar ist
**um** nicht durch lange Wartezeiten frustriert zu werden.

**Als** Nutzer mit langsamer Internetverbindung
**möchte ich** dass die Anwendung auch bei eingeschränkter Bandbreite funktioniert
**um** die Anwendung auch unterwegs oder in Gebieten mit schlechter Netzabdeckung nutzen zu können.

**Als** Produktmanager
**möchte ich** dass die Core Web Vitals den empfohlenen Schwellenwerten entsprechen
**um** eine gute Suchmaschinenplatzierung und Nutzerbindung sicherzustellen.

### 1.2 Geschäftliche Motivation

Performance hat direkten Einfluss auf Nutzerzufriedenheit und Konversion:

1. **53% der Nutzer** verlassen eine Seite, die länger als 3 Sekunden lädt (Google-Studie)
2. **Suchmaschinen-Ranking** — Core Web Vitals sind ein Ranking-Faktor
3. **Nutzerbindung** — Schnelle Anwendungen werden häufiger und länger genutzt
4. **Bandbreitenkosten** — Kleinere Bundles reduzieren Traffic-Kosten

---

## 2. Anforderungen

### 2.1 Core Web Vitals

| # | Regel | Stufe |
|---|-------|-------|
| R-001 | First Contentful Paint (FCP) MUSS unter 1.5 Sekunden liegen. | MUSS |
| R-002 | Largest Contentful Paint (LCP) MUSS unter 2.5 Sekunden liegen. | MUSS |
| R-003 | Time to Interactive (TTI) MUSS unter 3.5 Sekunden liegen. | MUSS |
| R-004 | Cumulative Layout Shift (CLS) MUSS unter 0.1 liegen. | MUSS |
| R-005 | Interaction to Next Paint (INP) MUSS unter 200ms liegen. | MUSS |

### 2.2 Ladezustände

| # | Regel | Stufe |
|---|-------|-------|
| R-006 | Für alle asynchronen Ladevorgänge MÜSSEN Skeleton-Screens oder Platzhalter angezeigt werden — keine leeren Seiten. | MUSS |
| R-007 | Skeleton-Screens MÜSSEN die ungefähre Form des geladenen Inhalts widerspiegeln, um Layout-Shifts zu vermeiden. | MUSS |
| R-008 | Ladevorgänge, die länger als 300ms dauern, MÜSSEN einen visuellen Indikator zeigen. | MUSS |
| R-009 | Spinner SOLLEN nur für kurze, fokussierte Aktionen verwendet werden (z.B. Button-Klick), nicht für Seitenübergänge. | SOLL |

### 2.3 Lazy Loading

| # | Regel | Stufe |
|---|-------|-------|
| R-010 | Routen/Seiten MÜSSEN per Code-Splitting lazily geladen werden — nicht alle Seiten im initialen Bundle. | MUSS |
| R-011 | Bilder unterhalb des sichtbaren Bereichs (below the fold) MÜSSEN lazy geladen werden (`loading="lazy"` oder Intersection Observer). | MUSS |
| R-012 | Schwere Komponenten (Charts, Editoren, Karten) SOLLEN per Dynamic Import lazily geladen werden. | SOLL |

### 2.4 Bundle-Size

| # | Regel | Stufe |
|---|-------|-------|
| R-013 | Das initiale JavaScript-Bundle SOLL unter 300KB (gzipped) liegen. Bei Einsatz von MUI + Redux Toolkit + react-i18next ist ein realistischer Zielwert 250–350KB; individuelle Routen MÜSSEN per Code-Splitting lazy-loaded werden. | SOLL |
| R-014 | Das initiale CSS-Bundle SOLL unter 50KB (gzipped) liegen. | SOLL |
| R-015 | Bundle-Size-Budgets MÜSSEN in der CI-Pipeline überwacht werden — ein Überschreiten MUSS den Build fehlschlagen lassen. | MUSS |
| R-016 | Tree-Shaking MUSS aktiviert sein, um ungenutzten Code zu entfernen. | MUSS |

### 2.5 Datenabfragen & Interaktion

| # | Regel | Stufe |
|---|-------|-------|
| R-017 | Sucheingaben MÜSSEN mit Debouncing versehen werden (empfohlen: 300ms Verzögerung). | MUSS |
| R-018 | Listen mit mehr als 50 Einträgen MÜSSEN paginiert oder mit Virtual Scrolling dargestellt werden. | MUSS |
| R-019 | API-Responses SOLLEN clientseitig gecacht werden, wenn die Daten sich selten ändern (Stale-While-Revalidate-Strategie). | SOLL |
| R-020 | Doppelte API-Aufrufe bei schnellen Navigation-Wechseln MÜSSEN durch Request-Deduplizierung oder Abbruch (AbortController) verhindert werden. | MUSS |

### 2.6 Rendering-Stabilität (React Hooks)

| # | Regel | Stufe |
|---|-------|-------|
| R-023 | Custom Hooks, die Objekte oder Arrays zurückgeben, MÜSSEN den Rückgabewert mit `useMemo` stabilisieren, um kaskadierende Referenzinstabilität zu verhindern. | MUSS |
| R-024 | Primitive Rückgabewerte (`string`, `number`, `boolean`) sind von R-023 ausgenommen, da sie per Wert verglichen werden. | INFO |
| R-025 | Wird ein instabiler Hook-Rückgabewert als Dependency in `useCallback`, `useEffect` oder `useMemo` verwendet, MUSS die gesamte Abhängigkeitskette auf Stabilität geprüft werden. | MUSS |

> **Hintergrund:** Ein instabiler Rückgabewert (z.B. `return { success: ..., error: ... }` ohne `useMemo`) erzeugt bei jedem Render eine neue Referenz. Jeder Consumer, der diesen Wert als Dependency nutzt, wird dadurch ebenfalls instabil — mit potentiellen Endlos-Render-Schleifen:
>
> ```
> unstabiler Hook-Return → useCallback neu erstellt → useEffect feuert → setState → Re-Render → ∞
> ```

### 2.7 Caching

| # | Regel | Stufe |
|---|-------|-------|
| R-026 | Statische Assets (JS, CSS, Bilder) MÜSSEN mit Content-Hash im Dateinamen und langen Cache-Headern (≥1 Jahr) ausgeliefert werden. | MUSS |
| R-027 | Die `index.html` MUSS mit `Cache-Control: no-cache` ausgeliefert werden, um stets die aktuelle Version zu laden. | MUSS |

---

## 3. Wireframe-Beispiele

### 3.1 Skeleton-Screen

```
  Ladezustand:                    Geladener Zustand:
  ┌────────────────────┐          ┌────────────────────┐
  │ ████████████       │          │ Seitentitel         │
  ├────────────────────┤          ├────────────────────┤
  │ ░░░░░░░░░░░░░░     │          │ Max Mustermann      │
  │ ░░░░░░░░░░░        │          │ Mitglied seit 2024  │
  │                    │          │                    │
  │ ░░░░░░░░░░░░░░░░░  │          │ Lorem ipsum dolor   │
  │ ░░░░░░░░░░░░░░     │          │ sit amet conse...   │
  │ ░░░░░░░░░          │          │ ctetuer.            │
  └────────────────────┘          └────────────────────┘
```

### 3.2 Pagination vs. Virtual Scrolling

```
  Pagination:                     Virtual Scrolling:
  ┌────────────────────┐          ┌────────────────────┐
  │ Eintrag 1          │          │ Eintrag 47         │
  │ Eintrag 2          │          │ Eintrag 48         │
  │ Eintrag 3          │          │ Eintrag 49         │  ← Nur sichtbare
  │ ...                │          │ Eintrag 50         │     Einträge im DOM
  │ Eintrag 20         │          │ Eintrag 51         │
  ├────────────────────┤          │ Eintrag 52         │
  │ ← 1 2 3 ... 10 →  │          └────────────────────┘
  └────────────────────┘            ↕ Scrollbar
```

---

## 4. Akzeptanzkriterien

### Definition of Done

- [ ] **Core Web Vitals**
    - [ ] FCP < 1.5s auf einem durchschnittlichen Mobilgerät (simuliert: 4G, Moto G4)
    - [ ] LCP < 2.5s gemessen mit Lighthouse
    - [ ] TTI < 3.5s
    - [ ] CLS < 0.1
    - [ ] INP < 200ms
- [ ] **Ladezustände**
    - [ ] Skeleton-Screens für alle seitenweiten Ladevorgänge
    - [ ] Kein FOUC (Flash of Unstyled Content)
    - [ ] Kein Layout-Shift beim Nachladen von Inhalten
- [ ] **Lazy Loading**
    - [ ] Routen werden per Code-Splitting geladen
    - [ ] Bilder unterhalb des Viewports laden lazy
    - [ ] Initiales Bundle enthält nur die aktuelle Route
- [ ] **Bundle-Size**
    - [ ] Initiales JS-Bundle < 200KB gzipped
    - [ ] Bundle-Size-Check in CI-Pipeline integriert
    - [ ] Kein ungenutzter Code im Bundle (Tree-Shaking aktiv)
- [ ] **Rendering-Stabilität**
    - [ ] Alle Custom Hooks mit Objekt-/Array-Rückgabe verwenden `useMemo`
    - [ ] Keine instabilen Referenzketten in `useEffect`-Dependencies
- [ ] **Listen & Suche**
    - [ ] Sucheingaben sind mit Debouncing versehen
    - [ ] Lange Listen verwenden Pagination oder Virtual Scrolling
- [ ] **Testing**
    - [ ] Lighthouse Performance-Score ≥ 90
    - [ ] Bundle-Analyzer-Report wird bei jedem Build generiert
    - [ ] Performance-Regressionstests in CI

---

## 5. Risiken bei Nicht-Einhaltung

| Risiko | Auswirkung | Wahrscheinlichkeit | Mitigation |
|---|---|---|---|
| **Lange Ladezeiten** | Nutzer verlassen die Anwendung | Hoch | Performance-Budgets in CI durchsetzen |
| **Großes initiales Bundle** | Lange TTI, schlechte Mobile-Performance | Hoch | Code-Splitting, Tree-Shaking, Bundle-Budgets |
| **Layout-Shifts** | Frustrierende Benutzererfahrung, Fehleingaben | Mittel | Skeleton-Screens, feste Dimensionen für Medien |
| **Fehlende Ladeindikatoren** | Nutzer denkt, Anwendung ist kaputt | Hoch | Skeleton-Screens für alle Ladezustände |
| **Unkontrolliertes Bundle-Wachstum** | Performance degradiert schleichend | Hoch | Bundle-Size-Budgets mit CI-Gates |

---

**Dokumenten-Ende**

**Version**: 1.0
**Status**: Entwurf
**Letzte Aktualisierung**: 2026-02-26
**Review**: Pending
**Genehmigung**: Pending
