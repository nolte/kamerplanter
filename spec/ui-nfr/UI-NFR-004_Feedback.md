---

ID: UI-NFR-004
Titel: Fehleranzeige & Benutzer-Feedback
Kategorie: UI-Verhalten Unterkategorie: Feedback, Fehleranzeige, Notifications
Technologie: React, TypeScript, MUI, Flutter
Status: Entwurf
Priorität: Hoch
Version: 1.0
Autor: Business Analyst - Agrotech
Datum: 2026-02-26
Tags: [feedback, notifications, snackbar, error-states, empty-states, loading, validation]
Abhängigkeiten: [UI-NFR-002, UI-NFR-003, UI-NFR-006]
Betroffene Module: [Frontend, Mobile]
---

# UI-NFR-004: Fehleranzeige & Benutzer-Feedback

> **Verwandtes Dokument:** NFR-010 (UI-Pflegemasken & Listenansichten) definiert, **was** pro Entität vorhanden sein muss. Dieses Dokument definiert, **wie** Feedback visuell dargestellt wird.

## 1. Business Case

### 1.1 User Story

**Als** Endanwender
**möchte ich** bei jeder Aktion ein klares visuelles Feedback erhalten
**um** zu wissen, ob meine Aktion erfolgreich war, fehlgeschlagen ist oder noch verarbeitet wird.

**Als** Endanwender
**möchte ich** bei Fehlern verständliche Meldungen mit Handlungsoptionen sehen
**um** den Fehler selbstständig beheben oder dem Support melden zu können.

**Als** Frontend-Entwickler
**möchte ich** einheitliche Feedback-Patterns für alle Anwendungsteile
**um** konsistentes Verhalten ohne individuelle Implementierungen zu gewährleisten.

### 1.2 Geschäftliche Motivation

Fehlende oder unklare Rückmeldungen sind eine der häufigsten Ursachen für Nutzerfrust:

1. **Vertrauen** — Nutzer müssen wissen, dass ihre Aktionen verarbeitet wurden
2. **Fehlerreduktion** — Klare Validierung verhindert fehlerhafte Eingaben
3. **Selbstbedienung** — Verständliche Fehlermeldungen reduzieren Support-Anfragen
4. **Datenverlust vermeiden** — Bestätigungsdialoge schützen vor versehentlichem Löschen

---

## 2. Anforderungen

### 2.1 Snackbar-Notifications

| # | Regel | Stufe |
|---|-------|-------|
| R-001 | Erfolgreiche Aktionen MÜSSEN per Snackbar bestätigt werden (z.B. „Gespeichert", „Gelöscht"). | MUSS |
| R-002 | Snackbars MÜSSEN vier Schweregrade unterstützen: Erfolg, Info, Warnung, Fehler — jeweils visuell unterscheidbar (Farbe + Icon). | MUSS |
| R-003 | Erfolgs- und Info-Snackbars MÜSSEN nach 5 Sekunden automatisch verschwinden (Auto-Dismiss). | MUSS |
| R-004 | Fehler-Snackbars DÜRFEN NICHT automatisch verschwinden — der Nutzer MUSS sie manuell schließen. | MUSS |
| R-005 | Warnungs-Snackbars SOLLEN nach 8 Sekunden automatisch verschwinden, können aber manuell geschlossen werden. | SOLL |
| R-006 | Maximal drei Snackbars SOLLEN gleichzeitig sichtbar sein — weitere werden in eine Warteschlange gestellt. | SOLL |
| R-007 | Snackbars MÜSSEN per Tastatur schließbar sein und ARIA-Live-Regions verwenden. | MUSS |

### 2.2 Visuelle Darstellung von Validierungsfehlern

> **Hinweis:** Die Validierungszeitpunkte (On-Blur, On-Submit) und das grundlegende Formularverhalten werden in **UI-NFR-008 §2.1** definiert. Diese Sektion regelt die visuelle Darstellung der Validierungsergebnisse.

| # | Regel | Stufe |
|---|-------|-------|
| R-008 | Fehlerhafte Felder MÜSSEN visuell markiert werden (roter Rahmen + Fehlermeldung unterhalb des Feldes). | MUSS |
| R-009 | Die Fehlermeldung MUSS beschreiben, was falsch ist und wie der Fehler behoben werden kann. | MUSS |
| R-010 | Bei Submit-Fehlern MUSS der Fokus auf das erste fehlerhafte Feld gesetzt werden. | MUSS |
| R-011 | Erfolgreich validierte Felder KÖNNEN mit einem grünen Häkchen markiert werden. | KANN |

### 2.3 Leerzustände

| # | Regel | Stufe |
|---|-------|-------|
| R-012 | Leere Listen oder Bereiche MÜSSEN einen Leerzustand mit erklärendem Text und einer Handlungsaufforderung anzeigen. | MUSS |
| R-013 | Leerzustände SOLLEN ein illustratives Element (Icon oder Illustration) enthalten. | SOLL |
| R-014 | Leerzustände MÜSSEN einen primären Call-to-Action-Button enthalten, der den Nutzer zur nächsten logischen Aktion führt. | MUSS |

### 2.4 Fehlerzustände

| # | Regel | Stufe |
|---|-------|-------|
| R-015 | Netzwerk-Fehler MÜSSEN eine Fehlermeldung mit „Erneut versuchen"-Option anzeigen. | MUSS |
| R-016 | HTTP 404 (Nicht gefunden) MUSS eine dedizierte Fehlerseite mit Navigation zurück zur Startseite anzeigen. | MUSS |
| R-017 | HTTP 500 (Serverfehler) MUSS eine Fehlerseite mit Referenz-ID und Support-Kontaktmöglichkeit anzeigen. | MUSS |
| R-018 | Timeout-Fehler MÜSSEN unterschieden werden von Server-Fehlern und eine Retry-Option anbieten. | MUSS |
| R-019 | Bei Authentifizierungsfehlern (401/403) MUSS der Nutzer zur Login-Seite weitergeleitet oder eine Zugriffsverweigerung angezeigt werden. | MUSS |

### 2.5 Ladeindikatoren

> **Hinweis:** Der Double-Submit-Schutz (Button-Deaktivierung während Anfrage) wird in **UI-NFR-008 §2.4** definiert. Diese Sektion regelt die allgemeine Darstellung von Ladezuständen.

| # | Regel | Stufe |
|---|-------|-------|
| R-020 | Jede asynchrone Aktion MUSS einen visuellen Ladeindikator zeigen (Spinner, Progress-Bar, Skeleton). | MUSS |
| R-021 | Fortschrittsanzeigen SOLLEN für längere Operationen (>3s) verwendet werden, wenn der Fortschritt bekannt ist. | SOLL |

### 2.6 Bestätigungsdialoge

| # | Regel | Stufe |
|---|-------|-------|
| R-022 | Destruktive Aktionen (Löschen, Überschreiben, unwiderrufliche Änderungen) MÜSSEN einen Bestätigungsdialog anzeigen. | MUSS |
| R-023 | Der Bestätigungsdialog MUSS die Konsequenz der Aktion klar beschreiben. | MUSS |
| R-024 | Der destruktive Button im Dialog MUSS visuell als gefährlich erkennbar sein (z.B. rot). | MUSS |
| R-025 | Der Abbrechen-Button MUSS die Standard-Aktion sein (Fokus auf „Abbrechen", nicht auf „Löschen"). | MUSS |

---

## 3. Wireframe-Beispiele

### 3.1 Snackbar-Notifications

```
                                    ┌──────────────────────────┐
                                    │ ✓ Erfolgreich gespeichert│  ← Erfolg (grün)
                                    │                    [✕]   │
                                    └──────────────────────────┘

                                    ┌──────────────────────────┐
                                    │ ✗ Speichern fehlgeschla- │  ← Fehler (rot)
                                    │   gen. Erneut versuchen? │     Kein Auto-Dismiss
                                    │           [Retry]  [✕]   │
                                    └──────────────────────────┘
```

### 3.2 Leerzustand

```
┌──────────────────────────────────────┐
│                                      │
│              📋                       │
│                                      │
│     Noch keine Einträge vorhanden    │
│                                      │
│  Erstellen Sie Ihren ersten Eintrag  │
│  um loszulegen.                      │
│                                      │
│       [ + Neuen Eintrag erstellen ]  │
│                                      │
└──────────────────────────────────────┘
```

### 3.3 Inline-Validierung

```
  ┌──────────────────────────────────┐
  │ Name *                           │
  │ ┌──────────────────────────────┐ │
  │ │                              │ │  ← Roter Rahmen
  │ └──────────────────────────────┘ │
  │ ✗ Name ist ein Pflichtfeld.      │  ← Fehlermeldung (rot)
  │                                  │
  │ E-Mail *                         │
  │ ┌──────────────────────────────┐ │
  │ │ max@beispiel.de              │ │  ← Grüner Rahmen
  │ └──────────────────────────────┘ │
  │ ✓ Gültige E-Mail-Adresse        │  ← Erfolgsmeldung (grün)
  └──────────────────────────────────┘
```

### 3.4 Bestätigungsdialog

```
┌──────────────────────────────────────┐
│                                      │
│  Eintrag löschen?                    │
│                                      │
│  Möchten Sie den Eintrag „Beispiel"  │
│  wirklich löschen? Diese Aktion      │
│  kann nicht rückgängig gemacht        │
│  werden.                             │
│                                      │
│         [Abbrechen]  [Löschen]       │
│          ↑ Fokus      ↑ Rot          │
│                                      │
└──────────────────────────────────────┘
```

### 3.5 Netzwerk-Fehler

```
┌──────────────────────────────────────┐
│                                      │
│              ⚡                       │
│                                      │
│     Keine Verbindung zum Server      │
│                                      │
│  Bitte überprüfen Sie Ihre Internet- │
│  verbindung und versuchen Sie es     │
│  erneut.                             │
│                                      │
│        [ Erneut versuchen ]          │
│                                      │
└──────────────────────────────────────┘
```

---

## 4. Akzeptanzkriterien

### Definition of Done

- [ ] **Snackbar-Notifications**
    - [ ] Vier Schweregrade sind implementiert (Erfolg, Info, Warnung, Fehler)
    - [ ] Auto-Dismiss funktioniert korrekt je nach Schweregrad
    - [ ] Fehler-Snackbars bleiben sichtbar bis manuell geschlossen
    - [ ] Snackbars verwenden ARIA-Live-Regions
    - [ ] Maximal drei Snackbars gleichzeitig sichtbar
- [ ] **Visuelle Validierungsdarstellung** (Validierungszeitpunkte siehe UI-NFR-008)
    - [ ] Fehlerhafte Felder sind visuell markiert (roter Rahmen + Fehlermeldung)
    - [ ] Fehlermeldungen sind verständlich und handlungsorientiert
    - [ ] Fokus springt zum ersten fehlerhaften Feld bei Submit
- [ ] **Leerzustände**
    - [ ] Alle Listen/Bereiche haben Leerzustände
    - [ ] Leerzustände enthalten Call-to-Action
- [ ] **Fehlerzustände**
    - [ ] 404-Seite ist vorhanden
    - [ ] 500-Seite ist vorhanden mit Referenz-ID
    - [ ] Netzwerk-Fehler zeigen Retry-Option
    - [ ] Auth-Fehler leiten korrekt weiter
- [ ] **Ladeindikatoren**
    - [ ] Alle asynchronen Aktionen zeigen Ladezustand
    - [ ] Buttons sind während asynchroner Aktionen deaktiviert
- [ ] **Bestätigungsdialoge**
    - [ ] Alle destruktiven Aktionen haben Bestätigungsdialog
    - [ ] Fokus liegt standardmäßig auf „Abbrechen"

---

## 5. Risiken bei Nicht-Einhaltung

| Risiko | Auswirkung | Wahrscheinlichkeit | Mitigation |
|---|---|---|---|
| **Fehlende Rückmeldung** | Nutzer weiß nicht, ob Aktion erfolgreich war | Hoch | Snackbar-System als zentrale Komponente |
| **Kryptische Fehlermeldungen** | Nutzer kann Fehler nicht selbst beheben | Hoch | Verständliche, handlungsorientierte Meldungen |
| **Versehentliches Löschen** | Datenverlust durch fehlende Bestätigung | Mittel | Bestätigungsdialoge für destruktive Aktionen |
| **Leere Seiten ohne Erklärung** | Nutzer denkt, Anwendung ist kaputt | Mittel | Leerzustände mit Call-to-Action |
| **Doppelklick-Probleme** | Doppelte Einträge oder Aktionen | Hoch | Button-Deaktivierung während Verarbeitung |

---

**Dokumenten-Ende**

**Version**: 1.0
**Status**: Entwurf
**Letzte Aktualisierung**: 2026-02-26
**Review**: Pending
**Genehmigung**: Pending
