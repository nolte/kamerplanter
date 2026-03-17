---

ID: UI-NFR-008
Titel: Formulare & Eingabeverhalten
Kategorie: UI-Verhalten Unterkategorie: Formulare, Eingaben, Validierung
Technologie: React, TypeScript, MUI, Flutter
Status: Entwurf
Priorität: Hoch
Version: 1.2
Autor: Business Analyst - Agrotech
Datum: 2026-03-17
Tags: [formulare, forms, validierung, dirty-state, autofokus, tab-order, submit, double-submit, fremdschlüssel, autocomplete, dropdown]
Abhängigkeiten: [UI-NFR-002, UI-NFR-004, UI-NFR-006, UI-NFR-007]
Betroffene Module: [Frontend, Mobile]
---

# UI-NFR-008: Formulare & Eingabeverhalten

> **Verwandtes Dokument:** NFR-010 (UI-Pflegemasken & Listenansichten) definiert die Formular-Anforderungen pro Entität (Create/Edit-Dialoge, Shared-Komponenten, Zod-Validierung). Dieses Dokument definiert das allgemeine Formularverhalten.

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
| R-018 | Nach erfolgreichem Submit MUSS eine Bestätigungsmeldung angezeigt werden (Snackbar oder Inline-Meldung). | MUSS |
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
| R-037 | Komplexe Formulare mit mehr als 6 Feldern MÜSSEN in klar voneinander abgegrenzte Panels (MUI `Card` oder `Paper` mit Titel) aufgeteilt werden. Jedes Panel gruppiert thematisch zusammengehörige Felder (z.B. „Grunddaten", „Nährstoffprofil", „Umgebungsbedingungen"). | MUSS |
| R-038 | Jedes Panel MUSS eine eigene Überschrift (Typography variant `h6` oder `subtitle1`) und optional einen kurzen Einleitungstext besitzen, der den Zweck der Feldgruppe beschreibt. | MUSS |
| R-039 | Panels MÜSSEN durch visuellen Abstand (`spacing.lg` = 24px) und/oder Rahmen/Elevation (`elevation.1`) klar voneinander getrennt sein — ein einzelnes langes Formular ohne visuelle Unterteilung ist NICHT akzeptabel. | MUSS |
| R-040 | Die Panel-Reihenfolge MUSS der fachlichen Priorität folgen: Pflichtfelder und häufig genutzte Felder in den oberen Panels, optionale und Experten-Felder in den unteren Panels. | MUSS |
| R-041 | Panels, die nur für höhere Erfahrungsstufen (REQ-021) sichtbare Felder enthalten, SOLLEN als Ganzes ein-/ausgeblendet werden, statt leere Panels anzuzeigen. | SOLL |

### 2.7 Kontextuelle Hilfetext-Icons

| # | Regel | Stufe |
|---|-------|-------|
| R-042 | Jedes Eingabefeld, dessen Zweck nicht auf den ersten Blick offensichtlich ist, MUSS ein Info-Icon (ℹ️ / `HelpOutlineIcon`) rechts neben dem Feldlabel besitzen, das bei Interaktion einen erklärenden Hilfetext anzeigt. | MUSS |
| R-043 | Das Info-Icon MUSS als `InputAdornment` (MUI `endAdornment`) oder direkt neben dem Label platziert werden — konsistent über alle Formulare hinweg. | MUSS |
| R-044 | Bei Hover (Desktop, 300ms Delay) oder Tap (Mobile/Touch) auf das Info-Icon MUSS ein Tooltip mit dem Hilfetext erscheinen. Der Tooltip MUSS bei Mausverlassen bzw. Tap außerhalb wieder schließen. | MUSS |
| R-045 | Hilfetexte MÜSSEN als i18n-Schlüssel verwaltet werden (`fields.<fieldName>.help`) und in DE + EN vorliegen. | MUSS |
| R-046 | Für Felder mit Fachbegriffen (VPD, EC, PPFD etc.) MUSS die `HelpTooltip`-Komponente aus UI-NFR-011 verwendet werden, die zusätzlich Glossar-Verlinkung und erfahrungsstufenabhängige Darstellung bietet. Für allgemeine Felder ohne Fachbegriff genügt ein einfacher MUI `Tooltip` mit dem i18n-Hilfetext. | MUSS |
| R-047 | Das Info-Icon MUSS per Tastatur fokussierbar sein (`tabIndex={0}`) und den Tooltip bei Enter/Space öffnen (WCAG 2.1 Level AA). | MUSS |
| R-048 | Das Info-Icon SOLL dezent gestaltet sein (Farbe: `text.secondary`, Größe: 18px), um den visuellen Fluss des Formulars nicht zu stören, aber dennoch als interaktives Element erkennbar bleiben. | SOLL |

#### Wireframe: Feld mit Info-Icon

```
  Name *                              Beschreibung (optional)
  ┌───────────────────────────── ⓘ┐   ┌───────────────────────────── ⓘ┐
  │ Basilikum                     │   │                               │
  └───────────────────────────────┘   └───────────────────────────────┘
                                        ↑ Info-Icon (endAdornment)
  Bei Hover/Tap auf ⓘ:
  ┌─────────────────────────────────┐
  │ Der botanische oder umgangs-    │
  │ sprachliche Name der Pflanze.   │
  └─────────────────────────────────┘
```

#### Wireframe: Panel-Aufteilung mit Info-Icons

```
┌──────────────────────────────────────────────┐
│                                              │
│  Neue Art anlegen                            │
│                                              │
│  ┌─ Grunddaten ───────────────────────────┐  │
│  │                                        │  │
│  │  Name *                            ⓘ  │  │
│  │  ┌──────────────────────────────────┐  │  │
│  │  │                                  │  │  │
│  │  └──────────────────────────────────┘  │  │
│  │                                        │  │
│  │  Botanische Familie *              ⓘ  │  │
│  │  ┌──────────────────────────── ▾┐     │  │
│  │  │ Bitte wählen...              │     │  │
│  │  └──────────────────────────────┘     │  │
│  │                                        │  │
│  └────────────────────────────────────────┘  │
│                                              │  ← spacing.lg (24px)
│  ┌─ Nährstoffprofil ─────────────────────┐  │
│  │  Definiert den typischen Nährstoff-    │  │
│  │  bedarf dieser Art.                    │  │
│  │                                        │  │
│  │  EC-Zielwert (mS/cm)              ⓘ  │  │  ← HelpTooltip (Fachbegriff)
│  │  ┌──────────────────────────────────┐  │  │
│  │  │ 1.2                              │  │  │
│  │  └──────────────────────────────────┘  │  │
│  │                                        │  │
│  │  pH-Bereich                        ⓘ  │  │
│  │  ┌──────────┐  ┌──────────┐           │  │
│  │  │ 5.5      │  │ 6.5      │           │  │
│  │  └──────────┘  └──────────┘           │  │
│  │   Min            Max                   │  │
│  │                                        │  │
│  └────────────────────────────────────────┘  │
│                                              │
│  * Pflichtfeld                               │
│                                              │
│           [Abbrechen]  [Speichern]           │
│                                              │
└──────────────────────────────────────────────┘
```

### 2.8 Sonderzeichen, Einheiten & Unicode in UI-Strings

| # | Regel | Stufe |
|---|-------|-------|
| R-049 | Sonderzeichen in UI-Strings (Labels, Suffixe, Hilfetexte, Platzhalter) MÜSSEN als direkte UTF-8-Zeichen geschrieben werden, NICHT als Unicode-Escapes (`\u00B0`, `\u2014` etc.). | MUSS |
| R-050 | Einheiten-Suffixe in numerischen Feldern (z.B. `°C`, `mS/cm`, `ml/L`, `€/L`, `%`, `m²`) MÜSSEN als direkte UTF-8-Zeichen im `suffix`-Prop angegeben werden. | MUSS |
| R-051 | Sonderzeichen in Template-Literals und JSX-Attributen MÜSSEN ebenfalls als direkte UTF-8-Zeichen geschrieben werden — auch wenn Unicode-Escapes zur Compile-Zeit korrekt aufgelöst werden, können sie bei Hot-Reload, SSR oder Bundler-Konfigurationsänderungen als Rohtext durchrutschen. | MUSS |
| R-052 | Häufig verwendete Sonderzeichen und ihre korrekte Schreibweise: | — |

**Referenztabelle:**

| Zeichen | Beschreibung | Korrekt | Verboten |
|---------|-------------|---------|----------|
| ° | Grad-Zeichen | `suffix="°C"` | `suffix="\u00B0C"` |
| — | Gedankenstrich (Em-Dash) | `'—'` | `'\u2014'` |
| – | Halbgeviertstrich (En-Dash) | `'–'` | `'\u2013'` |
| € | Euro-Zeichen | `'€/L'` | `'\u20AC/L'` |
| ≥ | Grösser-gleich | `'≥'` | `'\u2265'` |
| ≤ | Kleiner-gleich | `'≤'` | `'\u2264'` |
| ² | Hochgestellt 2 | `'m²'` | `'m\u00B2'` |
| ℹ | Info-Symbol | `'ℹ'` | `'\u2139'` |

> **Begründung:** Unicode-Escapes in JSX/TypeScript werden zwar zur Compile-Zeit korrekt aufgelöst, sind aber (a) schwer lesbar im Code-Review, (b) fehleranfällig bei Copy-Paste und (c) in Edge-Cases (Hot-Module-Replacement, SSR-Hydration-Mismatch) als Rohtext sichtbar. Direkte UTF-8-Zeichen sind in modernen Editoren und Toolchains problemlos und eindeutig.

### 2.9 Formular-Reset

| # | Regel | Stufe |
|---|-------|-------|
| R-027 | Ein „Abbrechen"-Button MUSS das Formular auf den letzten gespeicherten Zustand zurücksetzen. | MUSS |
| R-028 | Ein „Zurücksetzen"-Button KANN angeboten werden, um das Formular auf die Standardwerte zurückzusetzen. | KANN |
| R-029 | Der Reset SOLL einen Bestätigungsdialog zeigen, wenn der Dirty-State aktiv ist. | SOLL |

### 2.10 Fremdschlüssel-Felder & Referenzauswahl

| # | Regel | Stufe |
|---|-------|-------|
| R-030 | Felder, die auf eine andere Entität verweisen (Fremdschlüssel), MÜSSEN als Auswahl-Komponente (Dropdown, Autocomplete) dargestellt werden — der Nutzer DARF NICHT gezwungen sein, einen Schlüssel oder Namen manuell einzutippen. | MUSS |
| R-031 | Die Auswahl-Komponente MUSS die verfügbaren Optionen dynamisch aus der API laden. | MUSS |
| R-032 | Bei mehr als 20 Optionen MUSS eine durchsuchbare Auswahl (Autocomplete mit Filterfunktion) verwendet werden. Bei ≤ 20 Optionen KANN ein einfaches Dropdown (Select) verwendet werden. | MUSS |
| R-033 | Während die Optionen geladen werden, MUSS ein Ladezustand angezeigt werden (z.B. Skeleton oder Spinner im Dropdown). | MUSS |
| R-034 | Wenn die API keine Optionen liefert (leere Liste), MUSS ein Hinweistext angezeigt werden (z.B. „Keine Einträge vorhanden — bitte zuerst anlegen"). | MUSS |
| R-035 | Bei Bearbeitungsformularen MUSS der aktuell zugewiesene Wert vorausgewählt sein. | MUSS |
| R-036 | Wenn ein referenzierter Datensatz zwischenzeitlich gelöscht wurde, SOLL das Feld den Nutzer darauf hinweisen und eine Neuauswahl erzwingen. | SOLL |

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

### 3.2 Fremdschlüssel-Feld (Autocomplete)

```
  Autocomplete (> 20 Optionen):       Dropdown (≤ 20 Optionen):
  ┌────────────────────────────┐      ┌────────────────────────── ▾┐
  │ 🔍 Ros...                 │      │ Solanaceae                  │
  ├────────────────────────────┤      ├─────────────────────────────┤
  │  Rosaceae                  │      │ Solanaceae               ✓  │
  │  Rosmarinus                │      │ Fabaceae                    │
  │  Roscovitine               │      │ Poaceae                     │
  └────────────────────────────┘      └─────────────────────────────┘

  Leere Optionsliste:                 Ladezustand:
  ┌────────────────────────────┐      ┌────────────────────────────┐
  │ 🔍                        │      │ ⏳ Wird geladen...         │
  ├────────────────────────────┤      └────────────────────────────┘
  │  Keine Einträge vorhanden  │
  │  — bitte zuerst anlegen.   │
  └────────────────────────────┘
```

### 3.4 Double-Submit-Schutz

```
  Normaler Zustand:           Ladezustand:
  ┌──────────────────┐       ┌──────────────────┐
  │    Speichern     │       │ ⏳ Wird gespei-  │  ← Deaktiviert
  └──────────────────┘       │    chert...      │
                              └──────────────────┘
```

### 3.5 Dirty-State-Warnung

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
- [ ] **Feldgruppen & Panel-Aufteilung**
    - [ ] Zusammengehörige Felder sind mit `<fieldset>` und `<legend>` gruppiert
    - [ ] Pflichtfelder sind gekennzeichnet
    - [ ] Komplexe Formulare (>6 Felder) sind in separate Panels (Card/Paper) aufgeteilt
    - [ ] Jedes Panel hat eine Überschrift und optional einen Einleitungstext
    - [ ] Panels sind durch visuellen Abstand (24px) klar getrennt
    - [ ] Panel-Reihenfolge folgt der fachlichen Priorität (Pflichtfelder oben)
- [ ] **Kontextuelle Hilfetext-Icons**
    - [ ] Nicht-offensichtliche Felder haben ein Info-Icon (ⓘ) neben dem Label
    - [ ] Info-Icon zeigt Tooltip mit Hilfetext bei Hover/Tap
    - [ ] Hilfetexte sind als i18n-Schlüssel verwaltet (DE + EN)
    - [ ] Fachbegriff-Felder verwenden `HelpTooltip` aus UI-NFR-011
    - [ ] Info-Icon ist per Tastatur fokussierbar (WCAG 2.1 Level AA)
- [ ] **Fremdschlüssel-Felder**
    - [ ] Alle Fremdschlüssel-Felder nutzen Dropdown oder Autocomplete — kein manuelles Eintippen
    - [ ] Optionen werden dynamisch aus der API geladen
    - [ ] Autocomplete bei > 20 Optionen
    - [ ] Ladezustand während des Ladens der Optionen
    - [ ] Hinweistext bei leerer Optionsliste
    - [ ] Bestehender Wert ist bei Bearbeitung vorausgewählt
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
| **Freitext-Eingabe statt Auswahl bei Fremdschlüsseln** | Tippfehler, ungültige Referenzen, inkonsistente Daten | Hoch | Auswahl-Komponenten (Dropdown/Autocomplete) als verpflichtendes Pattern für alle FK-Felder |

---

**Dokumenten-Ende**

**Version**: 1.2
**Status**: Entwurf
**Letzte Aktualisierung**: 2026-03-17
**Review**: Pending
**Genehmigung**: Pending
