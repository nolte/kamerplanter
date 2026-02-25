---

ID: UI-NFR-008
Titel: Formulare & Eingabeverhalten
Kategorie: UI-Verhalten Unterkategorie: Formulare, Eingaben, Validierung
Technologie: React, TypeScript, MUI, Flutter
Status: Entwurf
Priorität: Hoch
Version: 1.0
Autor: Business Analyst - Agrotech
Datum: 2026-02-26
Tags: [formulare, forms, validierung, dirty-state, autofokus, tab-order, submit, double-submit]
Abhängigkeiten: [UI-NFR-002, UI-NFR-004]
Betroffene Module: [Frontend, Mobile]
---

# UI-NFR-008: Formulare & Eingabeverhalten

## 1. Business Case

### 1.1 User Story

**Als** Endanwender
**möchte ich** Formulare effizient und fehlerfrei ausfüllen können
**um** Daten schnell und korrekt zu erfassen.

**Als** Endanwender
**möchte ich** gewarnt werden, wenn ich eine Seite mit ungespeicherten Änderungen verlasse
**um** keinen Datenverlust durch versehentliches Navigieren zu erleiden.

**Als** Frontend-Entwickler
**möchte ich** einheitliche Formular-Patterns für alle Eingabemasken
**um** konsistentes Verhalten ohne individuelle Implementierungen sicherzustellen.

### 1.2 Geschäftliche Motivation

Formulare sind die primäre Datenerfassungsmethode in der Anwendung. Schlechte Formulare kosten Zeit und verursachen Fehler:

1. **Effizienz** — Schnelle Dateneingabe durch sinnvolle Defaults, Autofokus und Tab-Navigation
2. **Fehlerprävention** — Echtzeit-Validierung verhindert fehlerhafte Eingaben bevor sie abgesendet werden
3. **Datenschutz** — Dirty-State-Warnung verhindert versehentlichen Datenverlust
4. **Datenqualität** — Konsistente Validierung stellt sicher, dass nur korrekte Daten erfasst werden

---

## 2. Anforderungen

### 2.1 Validierung

| # | Regel | Stufe |
|---|-------|-------|
| R-001 | Formularfelder MÜSSEN bei Verlust des Fokus (On-Blur) validiert werden. | MUSS |
| R-002 | Beim Absenden (On-Submit) MUSS das gesamte Formular validiert werden, auch wenn einzelne Felder nicht berührt wurden. | MUSS |
| R-003 | Die Frontend-Validierung MUSS als Ergänzung zur Backend-Validierung dienen — die Frontend-Validierung allein ist NICHT ausreichend. | MUSS |
| R-004 | Backend-Validierungsfehler MÜSSEN inline am betroffenen Feld angezeigt werden, sofern ein Feldbezug vorhanden ist. | MUSS |
| R-005 | Validierungsregeln SOLLEN zentral definiert werden (z.B. als Schema), nicht in einzelnen Formular-Komponenten dupliziert. | SOLL |

### 2.2 Dirty-State & ungespeicherte Änderungen

| # | Regel | Stufe |
|---|-------|-------|
| R-006 | Das Formular MUSS einen Dirty-State tracken — ob der Nutzer Eingaben verändert hat, die noch nicht gespeichert wurden. | MUSS |
| R-007 | Beim Verlassen einer Seite mit ungespeicherten Änderungen MUSS ein Bestätigungsdialog erscheinen: „Ungespeicherte Änderungen gehen verloren. Möchten Sie die Seite wirklich verlassen?" | MUSS |
| R-008 | Die Dirty-State-Warnung MUSS auch bei Browser-Navigation (Zurück-Taste, Tab schließen) ausgelöst werden. | MUSS |
| R-009 | Nach erfolgreichem Speichern MUSS der Dirty-State zurückgesetzt werden. | MUSS |

### 2.3 Autofokus & Tab-Reihenfolge

| # | Regel | Stufe |
|---|-------|-------|
| R-010 | Beim Öffnen eines Formulars MUSS der Fokus automatisch auf das erste bearbeitbare Eingabefeld gesetzt werden. | MUSS |
| R-011 | Die Tab-Reihenfolge MUSS der visuellen und logischen Reihenfolge der Felder entsprechen (von oben nach unten, von links nach rechts). | MUSS |
| R-012 | Deaktivierte oder schreibgeschützte Felder SOLLEN bei Tab übersprungen werden. | SOLL |
| R-013 | In Modalen mit Formularen MUSS der Fokus innerhalb des Modals gefangen bleiben (Focus-Trap). | MUSS |

### 2.4 Submit-Verhalten

| # | Regel | Stufe |
|---|-------|-------|
| R-014 | Formulare MÜSSEN per Enter-Taste abgesendet werden können (in einzeiligen Eingabefeldern). | MUSS |
| R-015 | In mehrzeiligen Textfeldern (Textarea) DARF Enter NICHT das Formular absenden — Enter fügt eine neue Zeile ein. | MUSS |
| R-016 | Der Submit-Button MUSS während einer laufenden Anfrage deaktiviert sein (Double-Submit-Schutz). | MUSS |
| R-017 | Während der Anfrage MUSS der Submit-Button einen Ladezustand anzeigen (Spinner oder Text „Wird gespeichert…"). | MUSS |
| R-018 | Nach erfolgreichem Submit MUSS eine Bestätigungsmeldung angezeigt werden (Toast oder Inline-Meldung). | MUSS |
| R-019 | Nach fehlgeschlagenem Submit MÜSSEN die eingegebenen Daten erhalten bleiben — das Formular DARF NICHT zurückgesetzt werden. | MUSS |

### 2.5 Sinnvolle Defaults & Vorauswahlen

| # | Regel | Stufe |
|---|-------|-------|
| R-020 | Felder SOLLEN sinnvolle Standardwerte haben, wo die häufigste Auswahl vorhersagbar ist. | SOLL |
| R-021 | Datumsfelder SOLLEN standardmäßig das heutige Datum vorauswählen, sofern kontextuell sinnvoll. | SOLL |
| R-022 | Dropdown-Felder mit nur einer Option SOLLEN diese automatisch vorauswählen. | SOLL |

### 2.6 Feldgruppen & Struktur

| # | Regel | Stufe |
|---|-------|-------|
| R-023 | Zusammengehörige Felder MÜSSEN visuell und semantisch gruppiert werden (`<fieldset>` mit `<legend>`). | MUSS |
| R-024 | Feldgruppen MÜSSEN einen beschreibenden Titel haben. | MUSS |
| R-025 | Pflichtfelder MÜSSEN als solche gekennzeichnet sein (z.B. mit `*` und Erklärungstext „* Pflichtfeld"). | MUSS |
| R-026 | Optionale Felder KÖNNEN mit dem Hinweis „(optional)" gekennzeichnet werden. | KANN |

### 2.7 Formular-Reset

| # | Regel | Stufe |
|---|-------|-------|
| R-027 | Ein „Abbrechen"-Button MUSS das Formular auf den letzten gespeicherten Zustand zurücksetzen. | MUSS |
| R-028 | Ein „Zurücksetzen"-Button KANN angeboten werden, um das Formular auf die Standardwerte zurückzusetzen. | KANN |
| R-029 | Der Reset SOLL einen Bestätigungsdialog zeigen, wenn der Dirty-State aktiv ist. | SOLL |

---

## 3. Wireframe-Beispiele

### 3.1 Formular mit Validierung und Feldgruppen

```
┌──────────────────────────────────────┐
│                                      │
│  Neuen Eintrag erstellen             │
│                                      │
│  ┌ Grunddaten ─────────────────────┐ │
│  │                                 │ │
│  │  Name *                         │ │
│  │  ┌───────────────────────────┐  │ │
│  │  │ [Autofokus]               │  │ │  ← Fokus hier
│  │  └───────────────────────────┘  │ │
│  │                                 │ │
│  │  Beschreibung (optional)        │ │
│  │  ┌───────────────────────────┐  │ │
│  │  │                           │  │ │
│  │  │                           │  │ │
│  │  └───────────────────────────┘  │ │
│  │                                 │ │
│  └─────────────────────────────────┘ │
│                                      │
│  ┌ Einstellungen ──────────────────┐ │
│  │                                 │ │
│  │  Kategorie *                    │ │
│  │  ┌───────────────────────── ▾┐  │ │
│  │  │ Bitte wählen...            │  │ │
│  │  └────────────────────────────┘  │ │
│  │                                 │ │
│  │  Datum *                        │ │
│  │  ┌────────────────────────────┐ │ │
│  │  │ 26.02.2026                 │ │ │  ← Default: heute
│  │  └────────────────────────────┘ │ │
│  │                                 │ │
│  └─────────────────────────────────┘ │
│                                      │
│  * Pflichtfeld                       │
│                                      │
│         [Abbrechen]  [Speichern]     │
│                                      │
└──────────────────────────────────────┘
```

### 3.2 Double-Submit-Schutz

```
  Normaler Zustand:           Ladezustand:
  ┌──────────────────┐       ┌──────────────────┐
  │    Speichern     │       │ ⏳ Wird gespei-  │  ← Deaktiviert
  └──────────────────┘       │    chert...      │
                              └──────────────────┘
```

### 3.3 Dirty-State-Warnung

```
┌──────────────────────────────────────┐
│                                      │
│  Ungespeicherte Änderungen           │
│                                      │
│  Sie haben ungespeicherte Änderun-   │
│  gen auf dieser Seite. Möchten Sie   │
│  die Seite wirklich verlassen?       │
│                                      │
│  Ihre Änderungen gehen dabei         │
│  verloren.                           │
│                                      │
│      [Auf Seite bleiben]  [Verlassen]│
│       ↑ Fokus                        │
│                                      │
└──────────────────────────────────────┘
```

---

## 4. Akzeptanzkriterien

### Definition of Done

- [ ] **Validierung**
    - [ ] On-Blur-Validierung auf allen Formularen
    - [ ] On-Submit-Validierung auf allen Formularen
    - [ ] Backend-Validierungsfehler werden inline angezeigt
    - [ ] Validierungsregeln sind zentral definiert
- [ ] **Dirty-State**
    - [ ] Dirty-State wird korrekt getrackt
    - [ ] Bestätigungsdialog bei Seitenverlassen mit ungespeicherten Änderungen
    - [ ] Dirty-State wird nach Speichern zurückgesetzt
    - [ ] Browser-Navigation (Zurück, Tab schließen) löst Warnung aus
- [ ] **Autofokus & Tab-Reihenfolge**
    - [ ] Autofokus auf erstes Eingabefeld in allen Formularen
    - [ ] Tab-Reihenfolge entspricht visueller Reihenfolge
    - [ ] Focus-Trap in Modalen
- [ ] **Submit-Verhalten**
    - [ ] Enter-Taste sendet Formular ab (einzeilige Felder)
    - [ ] Double-Submit-Schutz ist implementiert
    - [ ] Ladezustand am Submit-Button
    - [ ] Bestätigungsmeldung nach erfolgreichem Submit
    - [ ] Formulardaten bleiben bei fehlgeschlagenem Submit erhalten
- [ ] **Feldgruppen**
    - [ ] Zusammengehörige Felder sind mit `<fieldset>` und `<legend>` gruppiert
    - [ ] Pflichtfelder sind gekennzeichnet
- [ ] **Testing**
    - [ ] Alle Formulare haben Unit-Tests für Validierungsregeln
    - [ ] E2E-Tests für kritische Formulare (Submit, Validierung, Dirty-State)
    - [ ] Tastatur-Navigation durch alle Formulare getestet

---

## 5. Risiken bei Nicht-Einhaltung

| Risiko | Auswirkung | Wahrscheinlichkeit | Mitigation |
|---|---|---|---|
| **Datenverlust durch fehlende Dirty-State-Warnung** | Nutzer verliert eingegebene Daten | Hoch | Dirty-State als Standard-Pattern in allen Formularen |
| **Doppelte Einträge durch Double-Submit** | Dateninkonsistenz, Verwirrung | Hoch | Submit-Button-Deaktivierung als zentrale Komponente |
| **Schlechte Tab-Reihenfolge** | Nutzer mit Tastatur können Formular nicht effizient ausfüllen | Mittel | Tab-Reihenfolge als Teil der Barrierefreiheits-Tests |
| **Inkonsistente Validierung** | Unterschiedliches Verhalten zwischen Formularen | Hoch | Zentrale Validierungsregeln, wiederverwendbare Formular-Komponenten |
| **Fehlende Pflichtfeld-Kennzeichnung** | Nutzer weiß nicht, welche Felder ausgefüllt werden müssen | Mittel | Standard-Pattern für Pflichtfelder im Design-System |

---

**Dokumenten-Ende**

**Version**: 1.0
**Status**: Entwurf
**Letzte Aktualisierung**: 2026-02-26
**Review**: Pending
**Genehmigung**: Pending
