---

ID: UI-NFR-005
Titel: Navigation & Routing
Kategorie: UI-Verhalten Unterkategorie: Navigation, Routing, URL-Design
Technologie: React, TypeScript, React Router, Flutter
Status: Entwurf
Priorität: Hoch
Version: 1.0
Autor: Business Analyst - Agrotech
Datum: 2026-02-26
Tags: [navigation, routing, breadcrumb, deep-linking, browser-history, url-design]
Abhängigkeiten: [UI-NFR-001]
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
| R-010 | Die Hauptnavigation MUSS auf allen Seiten persistent sichtbar sein (Desktop: Sidebar oder Top-Navigation, Mobile: Bottom-Navigation oder Hamburger-Menü). | MUSS |
| R-011 | Der aktuell aktive Menüpunkt MUSS visuell hervorgehoben sein (z.B. farbliche Markierung, fetter Text, Indikator-Leiste). | MUSS |
| R-012 | Die Navigation MUSS maximal zwei Hierarchieebenen direkt zugänglich machen — tiefere Ebenen über Breadcrumbs oder Sub-Navigation. | MUSS |
| R-013 | Die Navigationsstruktur MUSS konsistent bleiben — die Reihenfolge und Gruppierung der Menüpunkte DARF NICHT kontextabhängig wechseln. | MUSS |

### 2.4 Breadcrumb-Navigation

| # | Regel | Stufe |
|---|-------|-------|
| R-014 | Seiten mit mehr als einer Hierarchieebene MÜSSEN Breadcrumbs anzeigen. | MUSS |
| R-015 | Jede Breadcrumb-Stufe MUSS ein klickbarer Link zur entsprechenden Ebene sein. | MUSS |
| R-016 | Die aktuelle Seite MUSS als letzte Breadcrumb-Stufe angezeigt werden, aber NICHT klickbar sein. | MUSS |
| R-017 | Breadcrumbs MÜSSEN semantisch korrekt als `<nav aria-label="Breadcrumb">` mit einer geordneten Liste markiert werden. | MUSS |

### 2.5 Fehlerseiten

| # | Regel | Stufe |
|---|-------|-------|
| R-018 | Ungültige URLs MÜSSEN eine 404-Fehlerseite anzeigen mit Navigation zur Startseite und Suchfunktion. | MUSS |
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

### 3.2 Mobile-Navigation

```
┌──────────────────────┐
│  ☰  Seitentitel      │  ← Hamburger-Menü
├──────────────────────┤
│                      │
│  Dashboard > Detail  │  ← Breadcrumbs
│                      │
│  Inhalt              │
│                      │
│                      │
├──────────────────────┤
│  🏠   📋   📊   ⚙  │  ← Bottom Navigation
│  ↑ aktiv             │
└──────────────────────┘
```

### 3.3 404-Fehlerseite

```
┌──────────────────────────────────────┐
│  Logo   Navigation              👤  │
├──────────────────────────────────────┤
│                                      │
│              🔍                      │
│                                      │
│     Seite nicht gefunden (404)       │
│                                      │
│  Die angeforderte Seite existiert    │
│  nicht oder wurde verschoben.        │
│                                      │
│  [ Zur Startseite ]  [ Suche ]       │
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
- [ ] **Breadcrumbs**
    - [ ] Breadcrumbs sind auf allen Seiten mit Hierarchie vorhanden
    - [ ] Alle Stufen sind klickbar (außer aktuelle Seite)
    - [ ] Semantisch korrekt als `<nav>` ausgezeichnet
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
| **Fehlende Breadcrumbs** | Orientierungsverlust bei tiefen Hierarchien | Mittel | Breadcrumbs als Standard-Komponente |
| **Generische 404-Seite** | Unprofessioneller Eindruck, keine Hilfe für den Nutzer | Niedrig | Eigene 404-Seite im Design-System |
| **Fehlende Seitentitel** | Screenreader-Nutzer wissen nicht, wo sie sind; Lesezeichen unbrauchbar | Mittel | Titel-Setzen als Teil der Route-Definition |

---

**Dokumenten-Ende**

**Version**: 1.0
**Status**: Entwurf
**Letzte Aktualisierung**: 2026-02-26
**Review**: Pending
**Genehmigung**: Pending
