---

ID: UI-NFR-022
Titel: Testbarkeit & eindeutige Identifizierbarkeit (E2E)
Kategorie: UI-Verhalten Unterkategorie: Testbarkeit, E2E-Automatisierung, stabile Selektoren
Technologie: React, TypeScript, MUI, Flutter
Status: Entwurf
Priorität: Hoch
Version: 1.0
Autor: Business Analyst - Agrotech
Datum: 2026-07-12
Tags: [testability, e2e, selenium, data-testid, selektoren, page-object, automation]
Abhängigkeiten: [UI-NFR-002, UI-NFR-005, UI-NFR-008, UI-NFR-017]
Betroffene Module: [Frontend, Mobile]
---

# UI-NFR-022: Testbarkeit & eindeutige Identifizierbarkeit (E2E)

## 1. Business Case

### 1.1 User Story

**Als** E2E-Test-Autor
**möchte ich** jedes relevante UI-Element und jede Seite über einen stabilen, eindeutigen Identifikator ansprechen können
**um** robuste Selenium-Tests zu schreiben, die nicht bei jeder Layout- oder Textänderung brechen.

**Als** Frontend-Entwickler
**möchte ich** eine verbindliche Konvention, welche Elemente einen Test-Identifikator tragen müssen und wie er benannt wird
**um** Testbarkeit konsistent und ohne Nachdenken bei der Implementierung mitzuliefern.

**Als** QA-Verantwortlicher
**möchte ich** dass Test-Identifikatoren als stabiler Vertrag behandelt werden
**um** eine wartbare, verlässliche Test-Suite mit geringer Flakiness zu betreiben.

### 1.2 Geschäftliche Motivation

Die verbindliche Teststrategie (NFR-008) und der Selenium-Teststandard (NFR-008a) schreiben
vor, **wie** Tests Selektoren wählen (Locator-Hierarchie, Page-Object-Pattern). Sie setzen
dabei stabile, eindeutige Identifikatoren im DOM voraus — es fehlt bisher jedoch die
verbindliche **Bereitstellungs**-Anforderung an das Frontend. Diese UI-NFR schließt die Lücke:

1. **Robuste E2E-Tests** — Selektoren, die an fachliche Test-Identifikatoren statt an
   Layout, Position oder übersetzbaren Text gebunden sind, überleben Refactorings und
   i18n-Änderungen.
2. **Geringere Wartungskosten** — Ein stabiler Identifikator-Vertrag verhindert, dass
   Tests reihenweise durch kosmetische UI-Änderungen brechen (Flakiness-Reduktion).
3. **Schnellere Testentwicklung** — Ein vorhersagbares Namensschema erlaubt Test-Autoren,
   Selektoren abzuleiten, ohne den DOM zu inspizieren.
4. **Barrierefreiheit als Nebeneffekt** — Wo Accessibility-Rollen und `aria-label`
   (UI-NFR-002) konsistent gepflegt sind, dienen sie zusätzlich als sekundäre Test-Anker.

---

## 2. Anforderungen

### 2.1 Grundprinzip & Locator-Hierarchie

| # | Regel | Stufe |
|---|-------|-------|
| R-001 | Jedes UI-Element, das ein E2E-Test ansprechen können muss (interaktive Elemente, Seiten-Container, Zustands- und Ergebnisanzeigen), MUSS über einen stabilen, eindeutigen Identifikator adressierbar sein — primär über das Attribut `data-testid`. | MUSS |
| R-002 | Der primäre Test-Identifikator MUSS `data-testid` sein. Die von Tests genutzte Locator-Präzedenz ist in NFR-008a §5.2 normiert (`data-testid` → `#id` → MUI-Klassen → `role` → XPath); dieses Dokument regelt die **Bereitstellung** dieser Identifikatoren durch das Frontend. | MUSS |
| R-003 | Selektoren DÜRFEN NICHT an positionsbasierte Pfade (`nth-child`, XPath-Indizes), an CSS-Utility-Klassen oder an übersetzbaren Anzeigetext gebunden werden müssen — für jedes testrelevante Element MUSS ein von diesen Faktoren unabhängiger Identifikator existieren. | MUSS |
| R-004 | `data-testid` DARF NICHT für Anwendungslogik, Styling oder fachliches Verhalten zweckentfremdet werden — es ist ausschließlich ein Test-Kontrakt. | MUSS |

### 2.2 Seiten-Marker (Page Marker)

| # | Regel | Stufe |
|---|-------|-------|
| R-005 | Jede über eine Route erreichbare Seite MUSS auf ihrem Wurzel-Container einen eindeutigen Seiten-Marker `data-testid="<entity>-<view>-page"` tragen (z.B. `species-list-page`, `species-detail-page`, `species-edit-page`). | MUSS |
| R-006 | Der Seiten-Marker MUSS erst dann im DOM vorhanden sein, wenn die Seite ihren Inhalt darstellt, und pro Seite eindeutig sein (kein Seiten-Marker DARF auf zwei verschiedenen Routen erscheinen). | MUSS |
| R-007 | Der geteilte Ladezustand (Skeleton/Spinner der Seite) MUSS über einen einheitlichen Identifikator `data-testid="loading-skeleton"` erkennbar sein, damit Tests deterministisch auf das Ende des Ladevorgangs warten können (statt fester Wartezeiten). | MUSS |
| R-008 | Der aktive Route-/Navigationszustand SOLL für Navigationselemente identifizierbar sein (vgl. UI-NFR-005), sodass Tests die aktuelle Position verifizieren können. | SOLL |

### 2.3 Bereitstellung auf Elementebene

| # | Regel | Stufe |
|---|-------|-------|
| R-009 | Alle interaktiven Elemente (Buttons, Links mit Aktion, Eingabefelder, Selects, Checkboxen, Toggles, Menü-Einträge, Tabs) MÜSSEN einen `data-testid` tragen. | MUSS |
| R-010 | Formular-Eingabefelder MÜSSEN dem Schema `data-testid="form-field-<name>"` folgen (`<name>` = fachlicher Feldname), konsistent mit dem Formular-Komponenten-Pattern im Frontend-Style-Guide. | MUSS |
| R-011 | Dialoge, Modale und Bestätigungsabfragen MÜSSEN einen `data-testid` tragen (z.B. `confirm-dialog`, `create-dialog`), damit Tests ihren Auf-/Zustand eindeutig prüfen können. | MUSS |
| R-012 | Ergebnis-, Status- und Kennzahlanzeigen, deren Wert ein Test verifiziert (z.B. Zähler, Statusbadges, leere/Fehlerzustände), MÜSSEN einen sprechenden `data-testid` tragen (z.B. `plant-count`, `empty-state`, `error-message`). | MUSS |
| R-013 | Dekorative, rein visuelle Elemente ohne Testrelevanz DÜRFEN keinen `data-testid` tragen — Identifikatoren werden gezielt vergeben, nicht flächendeckend gestreut. | SOLL |

### 2.4 Listen, Tabellen & wiederholte Elemente

| # | Regel | Stufe |
|---|-------|-------|
| R-014 | Wiederholte Elemente (Tabellenzeilen, Karten, Listeneinträge) MÜSSEN pro Eintrag eindeutig adressierbar sein — über einen Identifikator, der einen **stabilen fachlichen Schlüssel** einbettet (z.B. `data-testid="species-row-{slug}"` oder `-{id}`), NICHT über den Zeilen-/Array-Index. | MUSS |
| R-015 | Der Container einer Liste/Tabelle SOLL einen eigenen `data-testid` tragen (z.B. `species-table`), damit Tests „innerhalb dieser Liste"-Abfragen kapseln können. | SOLL |
| R-016 | Zellen mit testrelevantem Inhalt innerhalb einer Zeile SOLLEN über einen zeilen-relativen `data-testid` erreichbar sein (z.B. `data-testid="cell-status"` innerhalb der Zeile), sodass Assertions ohne Spalten-Positionsannahmen möglich sind. | SOLL |

### 2.5 Namenskonvention

| # | Regel | Stufe |
|---|-------|-------|
| R-017 | `data-testid`-Werte MÜSSEN in **kebab-case** und **englisch** notiert werden (konsistent mit NFR-003 „Source-Code englisch"), unabhängig von der DE-kanonischen Doku- und UI-Sprache. | MUSS |
| R-018 | Es gilt folgendes verbindliches Namensschema: <br>• Seiten: `<entity>-<view>-page` (`view` ∈ `list`, `detail`, `edit`, `create`, …) <br>• Formularfelder: `form-field-<name>` <br>• Aktions-Buttons: `<action>-button` bzw. `<entity>-<action>-button` (z.B. `submit-button`, `species-delete-button`) <br>• Dialoge: `<zweck>-dialog` (z.B. `confirm-dialog`) <br>• Listeneinträge: `<entity>-row-<key>` / `<entity>-card-<key>` mit fachlichem Schlüssel <br>• Geteilte Marker: `loading-skeleton`, `empty-state`, `error-message`. | MUSS |
| R-019 | Ein `data-testid`-Wert MUSS innerhalb der aktuell sichtbaren Ansicht eindeutig sein (mehrfach vorkommende Elemente werden per fachlichem Schlüssel disambiguiert, R-014). | MUSS |
| R-020 | Neue oder abweichende Namensmuster SOLLEN in diesem Dokument bzw. im Frontend-Style-Guide ergänzt werden, bevor sie verwendet werden, damit das Schema die einzige Quelle der Wahrheit bleibt. | SOLL |

### 2.6 Stabilität als Vertrag

| # | Regel | Stufe |
|---|-------|-------|
| R-021 | `data-testid`-Werte MÜSSEN als stabiler Schnittstellenvertrag behandelt werden: Sie DÜRFEN NICHT ohne Grund umbenannt oder entfernt werden. Eine Umbenennung MUSS gemeinsam mit der Anpassung der betroffenen Page Objects erfolgen (NFR-008a §5). | MUSS |
| R-022 | `data-testid`-Werte DÜRFEN NICHT aus übersetzbarem Text, aus Laufzeit-Zufallswerten oder aus rein positionsbasierten Ableitungen erzeugt werden — der Wert MUSS deterministisch und über Renders/Locales/Neustarts hinweg identisch sein. | MUSS |
| R-023 | Der Identifikator eines Elements MUSS über die relevanten Zustände (enabled/disabled, loading, error) hinweg stabil bleiben, sofern es dasselbe logische Element bleibt. | MUSS |

### 2.7 Accessibility-Selektoren als sekundäre Anker

| # | Regel | Stufe |
|---|-------|-------|
| R-024 | Die in UI-NFR-002 geforderten `role`- und `aria-label`-Attribute MÜSSEN so konsistent und aussagekräftig sein, dass sie als sekundäre Test-Anker (Locator-Priorität 4 in NFR-008a §5.2) dienen können — insbesondere für Komponenten, deren `data-testid`-Vergabe technisch schwierig ist (z.B. TreeView-Knoten). | MUSS |
| R-025 | Ein aussagekräftiges `aria-label` bzw. eine korrekte `role` ERSETZT NICHT den geforderten `data-testid` bei interaktiven Elementen (R-009); beide werden bereitgestellt, `data-testid` bleibt der primäre Anker. | MUSS |

---

## 3. Wireframe-Beispiele

### 3.1 Seiten-Marker & geteilter Ladezustand

```
  Route: /stammdaten/species
  ┌───────────────────────────────────────────────┐
  │ <div data-testid="species-list-page">          │  ← eindeutiger Seiten-Marker
  │                                                 │
  │   während Laden:                                │
  │   ┌───────────────────────────────────────┐    │
  │   │ data-testid="loading-skeleton"        │    │  ← Tests warten hierauf
  │   └───────────────────────────────────────┘    │
  │                                                 │
  │   nach Laden:  data-testid="species-table"      │
  │   ┌───────────────────────────────────────┐    │
  │   │ species-row-tomato    | cell-status ●  │    │  ← Zeile per fachl. Schlüssel
  │   │ species-row-basil     | cell-status ●  │    │
  │   └───────────────────────────────────────┘    │
  │ </div>                                          │
  └───────────────────────────────────────────────┘
```

### 3.2 Selektor-Bindung: robust vs. fragil

```
  ❌ Fragil (verboten als einzige Option):      ✅ Robust (gefordert):
  ┌────────────────────────────────┐           ┌────────────────────────────────┐
  │ //div[3]/table/tr[2]/td[4]     │           │ [data-testid='species-table']  │
  │ .css-1qx8p3f-MuiButton-root    │           │   [data-testid='species-row-   │
  │ button:contains("Speichern")   │           │     basil'] [data-testid='...']│
  │ (bricht bei Layout/i18n)       │           │ [data-testid='submit-button']  │
  └────────────────────────────────┘           └────────────────────────────────┘
```

### 3.3 Namensschema (Kurzreferenz)

```
  Seite ............. <entity>-<view>-page      z.B. species-detail-page
  Formularfeld ...... form-field-<name>         z.B. form-field-name
  Aktions-Button .... <action>-button           z.B. submit-button
  Dialog ............ <zweck>-dialog             z.B. confirm-dialog
  Listeneintrag ..... <entity>-row-<key>         z.B. species-row-tomato
  Geteilte Marker ... loading-skeleton | empty-state | error-message
```

---

## 4. Akzeptanzkriterien

### Definition of Done

- [ ] **Seiten-Marker**
    - [ ] Jede Route rendert einen eindeutigen `data-testid="<entity>-<view>-page"`
    - [ ] Kein Seiten-Marker erscheint auf zwei verschiedenen Routen
    - [ ] Geteilter `data-testid="loading-skeleton"` ist vorhanden und verschwindet nach dem Laden
- [ ] **Elementebene**
    - [ ] Alle interaktiven Elemente tragen einen `data-testid`
    - [ ] Formularfelder folgen `form-field-<name>`
    - [ ] Dialoge/Modale tragen einen `data-testid`
    - [ ] Testrelevante Ergebnis-/Statusanzeigen tragen einen sprechenden `data-testid`
- [ ] **Listen & Tabellen**
    - [ ] Wiederholte Einträge sind über einen fachlichen Schlüssel (nicht Index) adressierbar
    - [ ] Listen-/Tabellen-Container tragen einen `data-testid`
- [ ] **Namenskonvention & Stabilität**
    - [ ] Alle `data-testid`-Werte sind kebab-case und englisch
    - [ ] Werte folgen dem verbindlichen Namensschema (R-018)
    - [ ] Werte sind deterministisch (nicht aus Text/Zufall/Position abgeleitet)
    - [ ] Umbenennungen erfolgen synchron mit den betroffenen Page Objects
- [ ] **Accessibility-Anker**
    - [ ] `role`/`aria-label` sind konsistent genug für den Fallback-Locator (NFR-008a §5.2 Prio 4)
- [ ] **Testing**
    - [ ] Ein bestehendes Page Object je Seitentyp bindet ausschließlich an `data-testid`/`role` (kein positionsbasierter XPath)
    - [ ] Optionale Lint-/Review-Regel prüft, dass neue interaktive Komponenten einen `data-testid` mitliefern
    - [ ] Ein E2E-Smoke-Test navigiert alle Hauptseiten allein über Seiten-Marker

---

## 5. Risiken bei Nicht-Einhaltung

| Risiko | Auswirkung | Wahrscheinlichkeit | Mitigation |
|---|---|---|---|
| **Fragile Selektoren** | Tests brechen bei jeder Layout-/Textänderung, hohe Flakiness | Hoch | `data-testid`-Bereitstellung als MUSS, Page-Object-Kapselung |
| **Fehlende Seiten-Marker** | Tests können Route nicht deterministisch verifizieren, unsichere Waits | Hoch | Verpflichtender `<entity>-<view>-page`-Marker je Route |
| **Index-basierte Listen-Selektoren** | Falsche Zeile getroffen bei Sortier-/Filteränderung | Mittel | Fachlicher Schlüssel im Identifikator (R-014) |
| **i18n-/textgebundene Selektoren** | Tests brechen bei Sprachwechsel oder Textkorrektur | Hoch | Verbot text-/positionsbasierter Ableitung (R-022) |
| **Uneinheitliche Benennung** | Test-Autoren müssen Selektoren raten/DOM inspizieren | Mittel | Verbindliches, dokumentiertes Namensschema (R-018) |
| **Instabile Identifikatoren** | Umbenennungen brechen Tests unbemerkt | Mittel | `data-testid` als Vertrag, synchrone Page-Object-Pflege (R-021) |

---

**Dokumenten-Ende**

**Version**: 1.0
**Status**: Entwurf
**Letzte Aktualisierung**: 2026-07-12
**Review**: Pending
**Genehmigung**: Pending
