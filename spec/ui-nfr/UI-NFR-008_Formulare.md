---

ID: UI-NFR-008
Titel: Formulare & Eingabeverhalten
Kategorie: UI-Verhalten Unterkategorie: Formulare, Eingaben, Validierung
Technologie: React, TypeScript, MUI, Flutter
Status: Entwurf
Priorität: Hoch
Version: 1.3
Autor: Business Analyst - Agrotech
Datum: 2026-04-25
Tags: [formulare, forms, validierung, dirty-state, autofokus, tab-order, submit, double-submit, fremdschlüssel, autocomplete, dropdown, layout, panel-grid, content-density]
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
| R-004 | Backend-Validierungsfehler MÜSSEN inline am betroffenen Feld angezeigt werden, sofern ein Feldbezug vorhanden ist. Gemappt wird aus dem Fehler-Envelope: `details[].field` (ohne `body.`-Präfix) bestimmt **welches** Feld, `details[].code` bestimmt **welcher Text** — aufgelöst über den i18n-Key `errors.<code>`. Der Server-`reason` ist ein englischer Entwicklertext und DARF NICHT als Feldmeldung gerendert werden (NFR-017 R-118a, Beleg #1015). Trifft eines von beidem nicht (unbekanntes Feld oder fehlender Katalog-Key), bleibt es bei der generischen, lokalisierten Meldung — der Fehler verschwindet nie stillschweigend (UI-NFR-004 R-014a). | MUSS |
| R-005 | Validierungsregeln SOLLEN zentral definiert werden (z.B. als Schema), nicht in einzelnen Formular-Komponenten dupliziert. | SOLL |
| R-005a | Meldungstexte der Client-Validierung MÜSSEN i18n-Keys sein, keine fremdsprachigen Literale im Schema (`spec/style-guides/FRONTEND.md` §11.1, NFR-017 R-118b). | MUSS |

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
| R-048a | Die Erklärungspflicht aus R-042 gilt ausdrücklich **auch für Schalter, Umschalter und Checkboxen** (`Switch`, `Checkbox`, `FormSwitchField`). Ein Schalter ist der erklärungsbedürftigste Feldtyp im Formular: Sein Label benennt eine Option, aber nicht, **was beim Einschalten passiert** und was der ausgeschaltete Zustand bedeutet. Jeder Schalter, dessen Wirkung nicht aus dem Label allein hervorgeht, MUSS einen Hilfetext tragen — als Beschreibungszeile unter dem Label oder über das Info-Icon. Beleg: #633. | MUSS |

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

### 2.11 Inhaltsdichte & Mehrspalten-Layout

> **Motivation:** Detail- und Edit-Seiten mit vielen kleinen Form-Panels nebeneinander wirken auf grossen Viewports „leer", wenn das gesamte Formular auf eine schmale Lesespalte begrenzt ist. Gleichzeitig muss langer Fliesstext (Beschreibungen, Notizen) eine Lese-Breite behalten, die nicht ueberschreitet, was Augen ohne Sakkaden komfortabel lesen koennen. Diese Regeln definieren das Spannungsfeld – und lassen dem Implementierer bewusst Spielraum bei der konkreten Card-Anordnung pro Seite.

#### Container- und Spaltenbreiten

| # | Regel | Stufe |
|---|-------|-------|
| R-053 | Der aeussere Form-Container von Detail-/Edit-Seiten MUSS auf `md+` mindestens `1280px` `maxWidth` zulassen, damit kompakte Panels horizontal nebeneinander Platz finden. Ein pauschales `maxWidth: 900` ist NICHT akzeptabel. | MUSS |
| R-054 | Felder mit Fliesstext (Beschreibungen, Notizen, Multiline-Textareas mit `minRows >= 4`) MUESSEN eine eigene `maxWidth` von `760px` (entspricht ~70-80 Zeichen pro Zeile) erhalten, unabhaengig von der Container-Breite. Diese Lesbarkeits-Bremse gilt auch dann, wenn die Card selbst breiter ist. | MUSS |
| R-055 | Mehrzeilige Eingaben in der gleichen Sprachgruppe (z.B. `description_en` + `description_de`) MUESSEN vertikal untereinander gestapelt werden, NIEMALS in einer 50/50-`FormRow` mit Fliesstext. Kurze Felder (Name, Slug) DUERFEN dagegen weiter nebeneinander stehen. | MUSS |

#### Panel-Verteilung auf grossen Viewports

| # | Regel | Stufe |
|---|-------|-------|
| R-056 | Form-Panels (`Card`/`Paper` aus R-037) DUERFEN auf `md+` in einem 2- oder 3-spaltigen CSS-Grid angeordnet werden, sofern jedes betroffene Panel die Bedingungen aus R-057 erfuellt. Die konkrete Spaltenzahl und Anordnung waehlt der Implementierer pro Seite. | KANN |
| R-057 | Ein Panel ist „kompakt" und damit grid-faehig, wenn es **alle** der folgenden Bedingungen erfuellt: (a) keine Multiline-Textfelder mit `minRows >= 4`, (b) keine `Autocomplete`-Felder mit erwartet langer Optionsliste, (c) maximal sechs aktive Form-Felder, (d) keine eingebetteten Tabellen oder Listen mit dynamischer Hoehe. | MUSS |
| R-058 | Panels mit Fliesstext-Feldern (Beschreibungen) oder freier Listen-Komponente (`Autocomplete`, dynamischem `FormChipInput` mit erwartet vielen Eintraegen) MUESSEN auf voller Container-Breite einspaltig stehen — sie duerfen NICHT in das Mehrspalten-Grid einsortiert werden. | MUSS |
| R-059 | Auf `xs`-Viewports MUESSEN ALLE Panels einspaltig untereinander stehen (das Grid kollabiert auf `gridTemplateColumns: '1fr'`). Auf `sm` SOLL maximal zweispaltig gerastert werden, auf `md+` sind drei Spalten zulaessig. | MUSS |
| R-060 | Innerhalb eines Panels MUSS die bisherige `FormRow` (zwei Spalten ab `md`, eine Spalte auf `xs`) weiterhin verwendet werden, um zusammengehoerige Kurzfelder (z.B. Min/Max, Wert/Einheit, Name-EN/Name-DE) nebeneinander zu zeigen. | MUSS |

#### Implementierer-Freiheit

| # | Regel | Stufe |
|---|-------|-------|
| R-061 | Welche kompakten Panels konkret in welcher Spalte stehen, ist eine Implementierer-Entscheidung pro Seite. Die Spec gibt nur die Spielregeln vor (R-053 bis R-060). Es gibt KEINE pauschale Vorgabe wie „Klassifizierung links, Ausfuehrung rechts". | MUSS |
| R-062 | Die fachliche Reihenfolge (R-040: Pflichtfelder oben, optionale unten) MUSS auch im Mehrspalten-Layout erkennbar bleiben. Lese-Reihenfolge in CSS-Grid ist links-nach-rechts, dann zeilenweise — Panels mit hoher Prioritaet stehen also oben links. | MUSS |
| R-063 | Wechselt eine Seite vom Einspalten- in ein Mehrspalten-Layout, MUSS der Implementierer die Tab-Reihenfolge (R-011) gegenpruefen — die DOM-Reihenfolge muss der visuellen Lese-Reihenfolge entsprechen. | MUSS |
| R-064 | Sticky-FormActions oder andere Navigations-Hilfen sind KEINE Pflicht aus dieser Sektion und KOENNEN seitenweise abgewogen werden. | KANN |

#### Wireframe: Detail-Seite mit Mehrspalten-Layout (md+)

```
┌─────────────────────────────────────────────────────────────────────┐
│  Titel-Header  ☆                                       [Aktion]    │
│  [Chip] [Chip]  Meta-Info                                           │
│  ────────────────────────────────────────────────────────────────   │
│                                                                     │
│  ┌─ Identifikation (full-width Panel, Fliesstext-Felder) ───────┐  │
│  │  Name (EN)              │  Name (DE)                          │  │
│  │  ┌────────────────────┐ │ ┌────────────────────┐              │  │
│  │  └────────────────────┘ │ └────────────────────┘              │  │
│  │                                                               │  │
│  │  Beschreibung (EN)        ← maxWidth 760, auto-grow          │  │
│  │  ┌────────────────────────────────────────────┐               │  │
│  │  │ Mehrzeiliger Fliesstext bis 14 Zeilen…    │               │  │
│  │  └────────────────────────────────────────────┘               │  │
│  │  Beschreibung (DE)                                            │  │
│  │  ┌────────────────────────────────────────────┐               │  │
│  │  └────────────────────────────────────────────┘               │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌─ Klassifizierung (kompakt) ──┐ ┌─ Ausfuehrung (kompakt) ─────┐  │
│  │  Kategorie  │  Skill         │ │  Dauer  │  Foto-Pflicht     │  │
│  │  Stress     │  Recovery-Days │ │  Werkzeuge (Chip-Input)     │  │
│  └───────────────────────────────┘ └─────────────────────────────┘  │
│                                                                     │
│  ┌─ Geltungsbereich (Autocomplete, einspaltig) ──────────────────┐  │
│  │  ⓘ Diese Tatigkeit ist auf 3 Arten beschrankt.                │  │
│  │  Kompatible Arten  [Apium ⓧ] [Sellerie ⓧ] [Celeriac ⓧ]      │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌─ Erweitert (kompakt) ────────────────────────────────────────┐  │
│  │  Verbotene Phasen        │  Eingeschraenkte Sub-Phasen        │  │
│  │  Tags                    │  Sortierreihenfolge                │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                     │
│       [Abbrechen]  [Speichern]                                      │
└─────────────────────────────────────────────────────────────────────┘
```

#### Wireframe: Master-Detail-Variante (md+)

Alternative zur reinen Spalten-Verteilung: Eine Hauptspalte in Lesebreite (`READING_COL_MAX = 760 px`) traegt das Identifikations-Panel mit Fliesstext, daneben steht eine schmalere „Detail"-Spalte mit gestapelten kompakten Panels. Tradeoff: ausgewogener Visual Balance ohne abgehackt wirkende Lese-Spalte, aber Tab-Reihenfolge springt nach dem letzten Fliesstext-Feld in die rechte obere Ecke.

```
┌─────────────────────────────────────────────────────────────────────┐
│  Titel-Header  ☆                                       [Aktion]    │
│  ────────────────────────────────────────────────────────────────   │
│                                                                     │
│  ┌─ Identifikation (760 px) ────────┐ ┌─ Klassifizierung ────────┐  │
│  │  Name (EN) │ Name (DE)            │ │  Kategorie │ Skill        │  │
│  │  Beschreibung (EN)                │ │  Stress    │ Recovery     │  │
│  │  ┌────────────────────────────┐  │ └───────────────────────────┘  │
│  │  │ Mehrzeiliger Fliesstext   │  │ ┌─ Ausfuehrung ─────────────┐  │
│  │  └────────────────────────────┘  │ │  Dauer │ Foto-Pflicht     │  │
│  │  Beschreibung (DE)                │ │  Werkzeuge                │  │
│  │  ┌────────────────────────────┐  │ └───────────────────────────┘  │
│  │  └────────────────────────────┘  │                                │
│  └───────────────────────────────────┘                                │
│                                                                     │
│  ┌─ Geltungsbereich (full-width, R-058) ───────────────────────────┐ │
│  └──────────────────────────────────────────────────────────────────┘ │
│                                                                     │
│  ┌─ Erweitert (full-width) ────────────────────────────────────────┐ │
│  └──────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

```tsx
// Master-Detail: gridTemplateColumns: { md: `minmax(0, ${READING_COL_MAX}px) 1fr` }
// Linke Spalte: Identifikation (Card)
// Rechte Spalte: <Box flex column gap={PANEL_GAP}> mit Klassifizierung + Ausfuehrung
// Darunter (ausserhalb des Master-Detail-Grids): Scope und Advanced full-width
```

R-063 erinnert: bei Master-Detail springt der Fokus nach dem letzten Fliesstext-Feld in die rechte obere Ecke (`Klassifizierung > Kategorie`). Das ist akzeptabel, solange die DOM-Reihenfolge der visuellen Lese-Reihenfolge folgt (links-Spalte komplett vor rechts-Spalte komplett).

#### Anti-Pattern-Beispiele

| Anti-Pattern | Warum verboten | Korrektur |
|--------------|----------------|-----------|
| Komplette Form auf `maxWidth: 900` | Verschwendet auf grossen Bildschirmen 600-800 px Whitespace neben den Cards | R-053: Container `maxWidth: 1280` + selektives R-054 fuer Fliesstext |
| `description_en` + `description_de` in `FormRow` (50/50) mit `rows={3}` | Lange Beschreibung ist in halbierter Spalte praktisch unlesbar (~30 Zeichen pro Zeile, internes Scrollen) | R-055: vertikal stapeln + R-054: maxWidth 760 + auto-grow (`minRows`/`maxRows`) |
| Drei kompakte Cards (je 2 Felder) untereinander auf 1920×1080-Display | Erzwingt Scrollen, obwohl alle drei nebeneinander passen | R-056: 3-spaltiges Grid auf `md+` |
| Identification + Beschreibung in 2-Spalten-Grid neben Klassifizierung | Verletzt R-058 (Fliesstext-Panel im Grid) | R-058: Identification bleibt full-width, Klassifizierung steht in eigener Grid-Reihe |

### 2.9 Formular-Reset

| # | Regel | Stufe |
|---|-------|-------|
| R-027 | Ein „Abbrechen"-Button MUSS das Formular auf den letzten gespeicherten Zustand zurücksetzen. | MUSS |
| R-028 | Ein „Zurücksetzen"-Button KANN angeboten werden, um das Formular auf die Standardwerte zurückzusetzen. | KANN |
| R-029 | Der Reset SOLL einen Bestätigungsdialog zeigen, wenn der Dirty-State aktiv ist. | SOLL |

### 2.10 Felder mit geschlossener Wertemenge (Referenzen, Enums, Monate)

| # | Regel | Stufe |
|---|-------|-------|
| R-030 | Felder mit **geschlossener Wertemenge** MÜSSEN als Auswahl-Komponente (Dropdown, Autocomplete, Chip-Auswahl) dargestellt werden — der Nutzer DARF NICHT gezwungen sein, einen Schlüssel, Code oder Namen manuell einzutippen. Das gilt für Verweise auf andere Entitäten (Fremdschlüssel) **und für Enum-Felder gleichermaßen**: dass ein Enum keine Zieltabelle hat, aus der Optionen geladen werden könnten, ändert nichts daran, dass die zulässigen Werte bekannt und endlich sind. Ein Freitextfeld für einen Enum-Wert erzwingt Raten und produziert 422-Antworten für Tippfehler (Beleg: #610). Die Optionen kommen aus dem TypeScript-Union-Typ bzw. dem OpenAPI-Schema, die Beschriftungen aus `enums.<enumName>.<value>` (UI-NFR-007). | MUSS |
| R-030a | **Monatsfelder MÜSSEN als benannte Monats-Auswahl gerendert werden** — Eingabe und Anzeige über den Monatsnamen („März"), nicht über die Zahl. Eine Zahl DARF höchstens als Zusatzinformation danebenstehen; sie ist nie die primäre Darstellung und nie das Eingabeformat. Das gilt für alle Monatsfelder in Formularen, Listen und Detailansichten (`direct_sow_months`, `harvest_months`, `bloom_months`, `pruning_months`, `propagation_configs[].months`, …), nicht nur für die Anbauzeitachse (verallgemeinert UI-NFR-020 R-043). Ein Formular, das „3, 4, 9" verlangt, ist für Endnutzer nicht bedienbar. Belege: #613, #683. | MUSS |
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
- [ ] **Inhaltsdichte & Mehrspalten-Layout (Sektion 2.11)**
    - [ ] Form-Container nutzt `maxWidth >= 1280` auf `md+` (kein pauschales `900`)
    - [ ] Multiline-Fließtext-Felder sind auf `maxWidth: 760` gecappt (Lese-Spalte)
    - [ ] Sprachgruppen mit Multiline-Textareas (EN+DE-Beschreibung) sind vertikal gestapelt, nicht in `FormRow`
    - [ ] Kompakte Panels (R-057) auf `md+` in 2- oder 3-spaltigem Grid platziert
    - [ ] Panels mit Fließtext oder freier Listen-Komponente bleiben einspaltig (R-058)
    - [ ] Auf `xs` kollabiert das Panel-Grid auf eine Spalte (R-059)
    - [ ] Tab-Reihenfolge entspricht visueller Lese-Reihenfolge auch im Mehrspalten-Layout (R-063)
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

**Version**: 1.3
**Status**: Entwurf
**Letzte Aktualisierung**: 2026-04-25
**Changelog**:
- 1.3 (2026-04-25): Sektion 2.11 „Inhaltsdichte & Mehrspalten-Layout" ergänzt (R-053–R-064): Container-Breite, Lese-Spalten-Limit für Fließtext, optionales 2-/3-Spalten-Grid für kompakte Panels, Implementierer-Freiheit bei der konkreten Card-Anordnung pro Seite. Master-Detail-Wireframe als zweite zulässige Layout-Variante zu R-061 ergänzt.
- 1.2 (2026-03-17): Vorherige Fassung.
**Review**: Pending
**Genehmigung**: Pending
