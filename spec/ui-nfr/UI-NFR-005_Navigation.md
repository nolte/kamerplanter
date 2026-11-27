---

ID: UI-NFR-005
Titel: Navigation & Routing
Kategorie: UI-Verhalten Unterkategorie: Navigation, Routing, URL-Design
Technologie: React, TypeScript, React Router, Flutter
Status: Entwurf
Priorität: Hoch
Version: 1.6
Autor: Business Analyst - Agrotech
Datum: 2026-02-28
Tags: [navigation, routing, breadcrumb, deep-linking, browser-history, url-design]
Abhängigkeiten: [UI-NFR-001, UI-NFR-002]
Betroffene Module: [Frontend, Mobile]
---

# UI-NFR-005: Navigation & Routing

## 1. Business Case

### 1.1 User Story

**Als** Endanwender
**möchte ich** jede Ansicht direkt per URL aufrufen und als Lesezeichen speichern können
**um** schnell zu häufig genutzten Bereichen zurückzukehren.

**Als** Endanwender
**möchte ich** dass die Zurück- und Vorwärts-Tasten im Browser wie erwartet funktionieren
**um** mich intuitiv in der Anwendung bewegen zu können.

**Als** Endanwender
**möchte ich** jederzeit wissen, wo ich mich in der Anwendung befinde
**um** die Orientierung nicht zu verlieren.

### 1.2 Geschäftliche Motivation

Navigation ist die Grundlage jeder Anwendung. Fehlerhafte oder unvorhersehbare Navigation führt zu Orientierungsverlust und Frustration:

1. **Deep-Linking** — Links auf bestimmte Seiten können geteilt, als Lesezeichen gespeichert oder aus externen Systemen aufgerufen werden
2. **Browser-Erwartungen** — Nutzer erwarten, dass Zurück/Vorwärts funktioniert
3. **Auffindbarkeit** — Klare Hierarchien und Breadcrumbs helfen bei der Orientierung
4. **Support** — Nutzer können die URL einer problematischen Seite an den Support senden

---

## 2. Anforderungen

### 2.1 Deep-Linking & URL-Design

| # | Regel | Stufe |
|---|-------|-------|
| R-001 | Jede eigenständige Ansicht MUSS über eine eindeutige URL erreichbar sein (Deep-Linking). | MUSS |
| R-002 | URLs MÜSSEN lesbar und beschreibend sein (z.B. `/einstellungen/profil` statt `/page?id=42`). | MUSS |
| R-003 | Filter- und Suchparameter SOLLEN in der URL als Query-Parameter abgebildet werden, damit gefilterte Ansichten teilbar sind. | SOLL |
| R-004 | URLs MÜSSEN stabil sein — Änderungen an der URL-Struktur erfordern Weiterleitungen (301) von alten auf neue URLs. | MUSS |

> **Ausnahme zu R-004 — Tab-Fragmente der Einstellungsseite (F-11, #2935):** Die frühere Einstellungsseite adressierte ihre Tabs über das URL-Fragment (`/settings#<tab>`). Ein Fragment erreicht den Server nicht, eine 301-Weiterleitung ist dafür technisch unmöglich; eine clientseitige Umschlüsselung der alten Tab-Namen hat der Betreiber am 2026-11-17 abgelehnt. Alte Lesezeichen öffnen deshalb `/settings`: auf dem Desktop die erste sichtbare Einstellungsgruppe, auf dem Smartphone die Gruppenliste (Betreiberentscheidung 2026-11-23); alle Links innerhalb der App zeigen auf die neue Form `/settings/<gruppe>#<abschnitt>`. Für Pfade gilt R-018 unverändert: eine unbekannte Gruppe (`/settings/<unbekannt>`) zeigt die 404-Seite.

### 2.2 Browser-History

| # | Regel | Stufe |
|---|-------|-------|
| R-005 | Navigation zwischen Seiten MUSS korrekte Browser-History-Einträge erzeugen. | MUSS |
| R-006 | Die Zurück-Taste MUSS den Nutzer zur vorherigen Ansicht zurückbringen. | MUSS |
| R-007 | Die Vorwärts-Taste MUSS nach dem Zurückgehen wieder vorwärts navigieren. | MUSS |
| R-008 | Modale Dialoge DÜRFEN KEINE Browser-History-Einträge erzeugen (sie werden per Escape oder Klick geschlossen, nicht per Zurück-Taste). | MUSS |
| R-009 | Formular-Submissions SOLLEN `history.replaceState` verwenden, um doppelte Einträge bei Seitenaktualisierung zu vermeiden. | SOLL |

### 2.3 Hauptnavigation

| # | Regel | Stufe |
|---|-------|-------|
| R-010 | Die Hauptnavigation MUSS auf allen Seiten persistent sichtbar sein (Desktop: Sidebar, Mobile: Bottom-Navigation). | MUSS |
| R-011 | Der aktuell aktive Menüpunkt MUSS visuell hervorgehoben sein (z.B. farbliche Markierung, fetter Text, Indikator-Leiste). | MUSS |
| R-012 | Die Navigation MUSS maximal zwei Hierarchieebenen direkt zugänglich machen — tiefere Ebenen über Breadcrumbs oder Sub-Navigation. | MUSS |
| R-013 | Die Navigationsstruktur MUSS konsistent bleiben — die Reihenfolge und Gruppierung der Menüpunkte DARF NICHT kontextabhängig wechseln. | MUSS |
| R-013a | Alle Navigations-Links (Sidebar, Breadcrumbs, In-Content-Links) MÜSSEN als native `<a>`-Elemente gerendert werden (z.B. via react-router-dom `<Link>` bzw. MUI `component={Link}`), damit Standard-Browser-Interaktionen funktionieren: Ctrl+Klick / Cmd+Klick (neuer Tab), Mittelklick (neuer Tab), Rechtsklick → „Link in neuem Tab öffnen". `onClick` + `navigate()` ohne zugrunde liegendes `<a>`-Element ist NICHT zulässig. | MUSS |

<!-- Quelle: Frontend-Design-Review K-001 (Massentauglichkeit 2026-02-28) -->
### 2.3.1 Bottom-Navigation (Mobile)

**Begründung:** Im Gewächshaus oder am Balkon ist die Daumen-Zone am unteren Bildschirmrand die einzige ergonomisch erreichbare Zone bei Einhand-Bedienung eines Smartphones. Der Hamburger-Toggle oben links ist die am schlechtesten erreichbare Zone — insbesondere mit nassen oder erdigen Händen. Eine Bottom-Navigation ersetzt das Hamburger-Menü auf Mobile vollständig und macht die wichtigsten Bereiche per Daumen-Tap erreichbar.

| # | Regel | Stufe |
|---|-------|-------|
| R-023 | Auf Viewports < 768px (unterhalb des Breakpoints `md`) MUSS eine fixierte Bottom-Navigation (`MuiBottomNavigation`) angezeigt werden. Die Desktop-Sidebar MUSS auf diesem Breakpoint ausgeblendet sein. | MUSS |
| R-024 | Die Bottom-Navigation MUSS für **alle Erfahrungsstufen gleich** sein: vier feste Ziele plus „Mehr“. Sie ist NICHT erfahrungsstufenabhängig (Betreiberentscheidung 2026-11-22, #3018; ersetzt die Stufen-Tabs aus Version 1.3 — siehe Hinweis unter der Tabelle). | MUSS |
| R-025 | Die vier festen Ziele sind in dieser Reihenfolge: Start (Dashboard), Pflanzen (Instanzen-Liste), Aufgaben (Task-Queue), Kalender. | MUSS |
| R-026 | Der fünfte Eintrag „Mehr“ MUSS die Seitenleiste als Drawer öffnen. Sie enthält alle weiteren Bereiche in derselben Auswahl wie die Desktop-Sidebar (Erfahrungsstufe und Modul-Sichtbarkeit wirken dort, nicht in der Bottom-Navigation). „Mehr“ ist kein Navigationsziel und wird nicht als aktiver Tab hervorgehoben. | MUSS |
| R-027 | Touch-Targets in der Bottom-Navigation MÜSSEN mindestens 48×48px betragen, empfohlen 56×48px. | MUSS |
| R-028 | Die Bottom-Navigation MUSS den aktuell aktiven Tab visuell hervorheben (Icon-Farbe + Label). | MUSS |
| R-029 | Doppel-Tap auf den aktiven Tab SOLL zum Seitenanfang scrollen (Scroll-to-Top). | SOLL |
| R-030 | Die Bottom-Navigation DARF NICHT bei Scroll-Down ausgeblendet werden — sie MUSS permanent fixiert bleiben (`position: fixed; bottom: 0`). | MUSS |
| R-031 | Der Seiteninhalt MUSS ausreichend Bottom-Padding erhalten, damit der letzte Inhalt nicht von der Bottom-Navigation verdeckt wird (mindestens Höhe der Navigation + 8px). | MUSS |

!!! note "Abweichung von Version 1.3 (Betreiberentscheidung 2026-11-22, #3018)"
    Bis Version 1.3 verlangten R-024 bis R-026 eigene Tabs je Erfahrungsstufe (Einsteiger: Start, Pflanzen, Aufgaben, Einstellungen; Fortgeschritten: vier Tabs plus Overflow; Experte: Start, Pflanzen, Aufgaben, Düngung, Mehr). Der Betreiber hat am 2026-11-22 entschieden, dass die Bottom-Navigation für alle Stufen dieselben vier Ziele plus „Mehr“ zeigt: Die Leiste bleibt beim Wechsel der Stufe an ihrem Platz, und jeder weitere Bereich ist über „Mehr“ erreichbar. Die Einstellungen und die Düngung liegen damit hinter „Mehr“.

!!! note "Beabsichtigt — nicht „reparieren“ (Review #3018)"
    - Die vier festen Ziele ignorieren Erfahrungsstufe **und** Modul-Sichtbarkeit (R-024, R-026). Ist das Modul eines Ziels ausgeblendet, führt der Tap trotzdem auf die Seite, und dort erscheint der Hinweis zum Wiedereinblenden des Moduls (`ModuleGuard`); das Ziel verschwindet nicht aus der Leiste.
    - Die Leiste erscheint auf jeder Seite der Hauptoberfläche (R-010), auch im Onboarding-Assistenten. Sie fehlt nur dort, wo die Oberfläche keine Navigation hat: Anmelde- und Registrierungsseiten sowie der Kiosk-Modus, dessen eigene Leiste sie nicht verdoppelt.

### 2.4 Breadcrumb-Navigation

| # | Regel | Stufe |
|---|-------|-------|
| R-014 | **Alle** Seiten MÜSSEN eine Breadcrumb-Navigation anzeigen — unabhängig von der Hierarchieebene. Top-Level-Seiten (z.B. Dashboard, Listen) zeigen eine einstufige Breadcrumb mit dem Seitennamen. | MUSS |
| R-015 | Jede Breadcrumb-Stufe MUSS ein klickbarer Link zur entsprechenden Ebene sein. | MUSS |
| R-016 | Die aktuelle Seite MUSS als letzte Breadcrumb-Stufe angezeigt werden, aber NICHT klickbar sein. | MUSS |
| R-017 | Breadcrumbs MÜSSEN semantisch korrekt als `<nav aria-label="Breadcrumb">` mit einer geordneten Liste markiert werden. | MUSS |
| R-017a | Die Breadcrumb-Komponente (`Breadcrumbs.tsx`) MUSS als zentraler Layout-Bestandteil in das Seitenlayout eingebunden sein, sodass neue Seiten automatisch eine Breadcrumb erhalten. | MUSS |

### 2.5 Fehlerseiten

| # | Regel | Stufe |
|---|-------|-------|
| R-018 | Ungültige URLs MÜSSEN eine 404-Fehlerseite anzeigen mit Navigation zur Startseite. Eine Suchfunktion gehört nicht dazu: Die Anwendung hat keine globale Suche (Betreiberentscheidung 2026-11-27, #3150). | MUSS |
| R-019 | Die 404-Seite MUSS dem Design-System der Anwendung entsprechen (keine generische Browser-Fehlerseite). | MUSS |

### 2.6 Seitentitel

| # | Regel | Stufe |
|---|-------|-------|
| R-020 | Jede Route MUSS einen dynamischen Seitentitel (`<title>`) setzen, der die aktuelle Ansicht beschreibt. | MUSS |
| R-021 | Der Seitentitel MUSS dem Muster folgen: `Seitenname — App-Name` (z.B. „Einstellungen — Kamerplanter"). | MUSS |
| R-022 | Seitentitel MÜSSEN für Screenreader über `document.title` zugänglich sein. | MUSS |

---

## 3. Wireframe-Beispiele

### 3.1 Desktop-Navigation mit Breadcrumbs

**Top-Level-Seite (einstufige Breadcrumb):**
```
┌──────────────────────────────────────────────────┐
│  Logo   Dashboard   Listen   Einstellungen  👤  │
│         ↑ aktiv (hervorgehoben)                  │
├──────────────────────────────────────────────────┤
│                                                  │
│  Dashboard                                       │  ← Breadcrumb (1 Stufe, nicht klickbar)
│                                                  │
│  Dashboard — Inhalt                              │
│                                                  │
└──────────────────────────────────────────────────┘
```

**Detail-Seite (mehrstufige Breadcrumb):**
```
┌──────────────────────────────────────────────────┐
│  Logo   Dashboard   Listen   Einstellungen  👤  │
│                      ↑ aktiv (hervorgehoben)     │
├──────────────────────────────────────────────────┤
│                                                  │
│  Dashboard > Listen > Detailansicht              │  ← Breadcrumbs
│                ↑ klickbar   ↑ nicht klickbar     │
│                                                  │
│  Detailansicht — Inhalt                          │
│                                                  │
└──────────────────────────────────────────────────┘
```

<!-- Quelle: Frontend-Design-Review K-001 (Massentauglichkeit 2026-02-28) -->
### 3.2 Mobile-Navigation (Bottom-Navigation, R-023 bis R-031)

**Alle Erfahrungsstufen (4 Ziele + „Mehr“):**
```
┌──────────────────────────────────────┐
│  Kamerplanter          Seitentitel   │  ← AppBar (kein Hamburger)
├──────────────────────────────────────┤
│                                      │
│  Dashboard > Detail                  │  ← Breadcrumbs
│                                      │
│  Inhalt                              │
│                                      │
│                                      │
│                   padding-bottom: 64px│
├──────────────────────────────────────┤
│  🏠     🌱      ✅      📅     ⋯   │  ← Bottom Navigation (fixiert)
│  Start Pflanzen Aufg.  Kalender Mehr │
│  ↑ aktiv                 Mehr → Drawer│
│       min. 48×48px Touch-Target      │
└──────────────────────────────────────┘
```

### 3.3 404-Fehlerseite

```
┌──────────────────────────────────────┐
│  Logo   Navigation              👤  │
├──────────────────────────────────────┤
│                                      │
│              ❓                      │
│                                      │
│     Seite nicht gefunden (404)       │
│                                      │
│  Die angeforderte Seite existiert    │
│  nicht oder wurde verschoben.        │
│                                      │
│        [ Zur Startseite ]            │
│                                      │
└──────────────────────────────────────┘
```

---

## 4. Akzeptanzkriterien

### Definition of Done

- [ ] **Deep-Linking**
    - [ ] Jede Ansicht hat eine eindeutige, lesbare URL
    - [ ] URLs können als Lesezeichen gespeichert und geteilt werden
    - [ ] Filter und Suchparameter sind in der URL abgebildet
- [ ] **Browser-History**
    - [ ] Zurück-Taste funktioniert auf allen Seiten korrekt
    - [ ] Vorwärts-Taste funktioniert nach Zurücknavigation
    - [ ] Modale erzeugen keine History-Einträge
- [ ] **Hauptnavigation**
    - [ ] Navigation ist auf allen Seiten sichtbar
    - [ ] Aktiver Menüpunkt ist hervorgehoben
    - [ ] Navigationsstruktur ist konsistent
    - [ ] Alle Navigations-Links rendern native `<a>`-Elemente (Ctrl+Klick, Mittelklick, Rechtsklick → neuer Tab funktionieren)
- [ ] **Bottom-Navigation (Mobile)**
    - [ ] Bottom-Navigation ist auf Viewports < 768px sichtbar und fixiert
    - [ ] Desktop-Sidebar ist auf < 768px ausgeblendet
    - [ ] Alle Erfahrungsstufen: dieselben 4 Ziele (Start, Pflanzen, Aufgaben, Kalender) plus „Mehr“
    - [ ] „Mehr“ öffnet die Seitenleiste als Drawer und ist nie der aktive Tab
    - [ ] Touch-Targets ≥ 48×48px
    - [ ] Aktiver Tab visuell hervorgehoben
    - [ ] Seiteninhalt hat ausreichend Bottom-Padding
- [ ] **Breadcrumbs**
    - [ ] Breadcrumbs sind auf **allen** Seiten vorhanden (inkl. Top-Level-Seiten)
    - [ ] Top-Level-Seiten zeigen einstufige Breadcrumb (nur Seitenname)
    - [ ] Alle Stufen sind klickbar (außer aktuelle Seite)
    - [ ] Semantisch korrekt als `<nav>` ausgezeichnet
    - [ ] Breadcrumb-Komponente ist zentral im Layout eingebunden
- [ ] **Fehlerseiten**
    - [ ] 404-Seite ist vorhanden und gestaltet
    - [ ] 404-Seite bietet Navigation zur Startseite
- [ ] **Seitentitel**
    - [ ] Jede Route setzt einen dynamischen `<title>`
    - [ ] Titel folgen dem Muster „Seitenname — App-Name"
- [ ] **Testing**
    - [ ] Manuelle Tests der Zurück/Vorwärts-Navigation
    - [ ] Automatisierte Tests für alle Routen (Smoke-Tests)
    - [ ] Deep-Link-Tests: Direktaufruf aller URLs prüfen

---

## 5. Risiken bei Nicht-Einhaltung

| Risiko | Auswirkung | Wahrscheinlichkeit | Mitigation |
|---|---|---|---|
| **Fehlende Deep-Links** | Seiten können nicht geteilt oder als Lesezeichen gespeichert werden | Hoch | URL-Design als Teil des Feature-Designs |
| **Kaputte Zurück-Taste** | Nutzer verliert Orientierung, unerwartetes Verhalten | Hoch | Browser-History-Tests bei jedem Feature |
| **Fehlende Breadcrumbs** | Orientierungsverlust und inkonsistentes Erscheinungsbild | Hoch | Breadcrumbs zentral im Layout eingebunden, automatisch auf allen Seiten |
| **Generische 404-Seite** | Unprofessioneller Eindruck, keine Hilfe für den Nutzer | Niedrig | Eigene 404-Seite im Design-System |
| **Fehlende Seitentitel** | Screenreader-Nutzer wissen nicht, wo sie sind; Lesezeichen unbrauchbar | Mittel | Titel-Setzen als Teil der Route-Definition |

---

**Dokumenten-Ende**

**Version**: 1.6
**Status**: Entwurf
**Letzte Aktualisierung**: 2026-11-27
**Changelog**:
- 1.6 (2026-11-27): R-018 verlangt auf der 404-Seite keine Suchfunktion mehr; die Anwendung hat keine globale Suche, und eine Suche nur für die Fehlerseite steht in keinem Verhältnis (Betreiberentscheidung 2026-11-27, #3150). Wireframe in §3.3 angepasst.
- 1.5 (2026-11-27): Wortlaut korrigiert: R-023 und die Checkliste nennen „< 768px“ statt „≤ 768px“ — der Breakpoint `md` liegt bei 768px, bei genau 768px gilt wie für die Seitenleiste das Desktop-Layout. Hinweis ergänzt, dass die festen Ziele Modul-Sichtbarkeit ignorieren und die Leiste auch im Onboarding erscheint (Review #3018). Inhaltlich keine neue Anforderung.
- 1.4 (2026-11-26): R-024 bis R-026 auf vier feste Ziele plus „Mehr“ für alle Erfahrungsstufen umgestellt (Betreiberentscheidung 2026-11-22, #3018).
- 1.3 (2026-02-28): Vorherige Fassung.
**Review**: Pending
**Genehmigung**: Pending
