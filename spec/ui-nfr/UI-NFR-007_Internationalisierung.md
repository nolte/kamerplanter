---

ID: UI-NFR-007
Titel: Internationalisierung (i18n)
Kategorie: UI-Verhalten Unterkategorie: Internationalisierung, Lokalisierung
Technologie: React, TypeScript, Flutter
Status: Entwurf
Priorität: Mittel
Version: 1.0
Autor: Business Analyst - Agrotech
Datum: 2026-02-26
Tags: [i18n, internationalisierung, lokalisierung, sprache, datumsformat, zahlenformat, pluralisierung]
Abhängigkeiten: []
Betroffene Module: [Frontend, Mobile]
---

# UI-NFR-007: Internationalisierung (i18n)

## 1. Business Case

### 1.1 User Story

**Als** deutschsprachiger Nutzer
**möchte ich** die Anwendung in meiner Muttersprache nutzen können
**um** alle Funktionen ohne Sprachbarriere bedienen zu können.

**Als** englischsprachiger Nutzer
**möchte ich** die Anwendung auf Englisch umschalten können
**um** die Anwendung auch ohne Deutschkenntnisse nutzen zu können.

**Als** Frontend-Entwickler
**möchte ich** alle sichtbaren Texte über i18n-Keys verwalten
**um** neue Sprachen ohne Code-Änderungen hinzufügen zu können.

### 1.2 Geschäftliche Motivation

Internationalisierung von Anfang an einzuplanen ist deutlich günstiger als eine nachträgliche Umstellung:

1. **Marktreichweite** — Deutsch und Englisch als Mindestanforderung, weitere Sprachen können ergänzt werden
2. **Kulturelle Korrektheit** — Datums-, Zeit- und Zahlenformate variieren je nach Region
3. **Wartbarkeit** — Texte an einer zentralen Stelle zu verwalten vereinfacht Korrekturen und Ergänzungen
4. **Zukunftssicherheit** — Weitere Sprachen können ohne Refactoring hinzugefügt werden

---

## 2. Anforderungen

### 2.1 Unterstützte Sprachen

| # | Regel | Stufe |
|---|-------|-------|
| R-001 | Die Anwendung MUSS mindestens Deutsch (de) und Englisch (en) unterstützen. | MUSS |
| R-002 | Deutsch MUSS als Standardsprache voreingestellt sein. | MUSS |
| R-003 | Weitere Sprachen SOLLEN ohne Code-Änderungen hinzufügbar sein (nur neue Übersetzungsdateien). | SOLL |

### 2.2 Text-Externalisierung

| # | Regel | Stufe |
|---|-------|-------|
| R-004 | Alle sichtbaren Texte in der Benutzeroberfläche MÜSSEN über i18n-Keys referenziert werden — keine hartcodierten Strings in Komponenten. | MUSS |
| R-004a | Domänenwerte und Enum-Optionen in Dropdown-/Select-Feldern (z.B. Pflanzenphasen, Substrattypen, Belichtungsarten) MÜSSEN über i18n-Keys übersetzt werden. Die technischen Enum-Werte (z.B. `germination`, `vegetative`) DÜRFEN NICHT als Anzeigetext verwendet werden. | MUSS |
| R-005 | i18n-Keys MÜSSEN hierarchisch organisiert sein (z.B. `common.save`, `errors.notFound`, `pages.dashboard.title`). | MUSS |
| R-005a | Für Domänenwerte SOLL ein einheitlicher Key-Namespace verwendet werden (z.B. `enums.phase.germination`, `enums.substrateType.soil`), damit alle Enum-Übersetzungen zentral auffindbar sind. | SOLL |
| R-006 | Übersetzungsdateien MÜSSEN in einem strukturierten Format vorliegen (JSON oder YAML). | MUSS |
| R-007 | Fehlende Übersetzungen MÜSSEN im Entwicklungsmodus eine Warnung erzeugen und den Key als Fallback anzeigen. | MUSS |

### 2.3 Datums- und Zeitformate

| # | Regel | Stufe |
|---|-------|-------|
| R-008 | Datumsformate MÜSSEN locale-abhängig sein (z.B. DE: `26.02.2026`, EN: `02/26/2026` oder `26 Feb 2026`). | MUSS |
| R-009 | Zeitformate MÜSSEN locale-abhängig sein (z.B. DE: `14:30`, EN: `2:30 PM`). | MUSS |
| R-010 | Relative Zeitangaben SOLLEN verwendet werden, wo sinnvoll (z.B. „vor 5 Minuten", „gestern"). | SOLL |
| R-011 | Die Anwendung MUSS die Zeitzone des Nutzers berücksichtigen und Zeiten in der lokalen Zeitzone anzeigen. | MUSS |

### 2.4 Zahlenformate

| # | Regel | Stufe |
|---|-------|-------|
| R-012 | Zahlenformate MÜSSEN locale-abhängig sein: Dezimaltrennzeichen (DE: Komma, EN: Punkt), Tausendertrennzeichen (DE: Punkt, EN: Komma). | MUSS |
| R-013 | Währungs- und Einheitenformate MÜSSEN locale-abhängig formatiert werden. | MUSS |
| R-014 | Eingabefelder für Zahlen MÜSSEN das locale-spezifische Dezimaltrennzeichen akzeptieren. | MUSS |

### 2.5 Sprachwechsel

| # | Regel | Stufe |
|---|-------|-------|
| R-015 | Der Nutzer MUSS die Sprache über ein UI-Element wechseln können (z.B. Dropdown im Header oder in den Einstellungen). | MUSS |
| R-016 | Der Sprachwechsel MUSS ohne Neuladen der Seite erfolgen (dynamischer Wechsel). | MUSS |
| R-017 | Die gewählte Sprache MUSS persistent gespeichert werden (z.B. LocalStorage, User-Preferences). | MUSS |
| R-018 | Beim ersten Besuch SOLL die Browser-Sprache (`navigator.language`) als Voreinstellung verwendet werden, sofern die Sprache unterstützt wird. | SOLL |

### 2.6 Pluralisierung & dynamische Werte

| # | Regel | Stufe |
|---|-------|-------|
| R-019 | Die i18n-Bibliothek MUSS Pluralisierung unterstützen (z.B. „1 Eintrag" vs. „5 Einträge"). | MUSS |
| R-020 | Dynamische Werte MÜSSEN über Platzhalter in Übersetzungen eingefügt werden (z.B. `{{count}} Einträge gefunden`). | MUSS |
| R-021 | Die Satzstellung DARF NICHT durch String-Konkatenation erzwungen werden — Platzhalter erlauben flexible Wortstellung je Sprache. | MUSS |

### 2.7 RTL-Vorbereitung

| # | Regel | Stufe |
|---|-------|-------|
| R-022 | Das Layout SOLL so strukturiert sein, dass eine spätere RTL-Unterstützung (Right-to-Left für Arabisch, Hebräisch) ohne grundlegendes Refactoring möglich ist. | SOLL |
| R-023 | CSS-Eigenschaften wie `margin-left`/`margin-right` SOLLEN durch logische Eigenschaften (`margin-inline-start`/`margin-inline-end`) ersetzt werden, wo möglich. | SOLL |

---

## 3. Wireframe-Beispiele

### 3.1 Sprachwechsel-Element

```
  Im Header:
  ┌──────────────────────────────────────┐
  │  Logo   Navigation       [DE ▾] 👤  │
  │                            ├──────┤ │
  │                            │ DE ✓ │ │
  │                            │ EN   │ │
  │                            └──────┘ │
  └──────────────────────────────────────┘
```

### 3.2 Locale-abhängige Formate

```
  Deutsch (de):                  Englisch (en):
  ┌─────────────────────┐       ┌─────────────────────┐
  │ Datum: 26.02.2026   │       │ Date: Feb 26, 2026  │
  │ Zeit:  14:30        │       │ Time: 2:30 PM       │
  │ Zahl:  1.234,56     │       │ Number: 1,234.56    │
  │ 3 Einträge gefunden │       │ 3 entries found     │
  └─────────────────────┘       └─────────────────────┘
```

### 3.3 Pluralisierung

```
  0 Einträge gefunden       →  Keine Einträge gefunden
  1 Eintrag gefunden        →  1 Eintrag gefunden
  5 Einträge gefunden       →  5 Einträge gefunden
```

---

## 4. Akzeptanzkriterien

### Definition of Done

- [ ] **Sprachen**
    - [ ] Deutsch und Englisch sind vollständig übersetzt
    - [ ] Deutsch ist die Standardsprache
    - [ ] Sprachwechsel erfolgt ohne Neuladen
    - [ ] Sprachauswahl wird persistent gespeichert
- [ ] **Text-Externalisierung**
    - [ ] Keine hartcodierten Strings in Komponenten
    - [ ] Domänenwerte in Dropdowns/Selects werden über i18n-Keys übersetzt (keine rohen Enum-Werte als Anzeigetext)
    - [ ] Enum-Übersetzungen sind unter einheitlichem `enums.*`-Namespace organisiert
    - [ ] i18n-Keys sind hierarchisch organisiert
    - [ ] Fehlende Übersetzungen erzeugen eine Warnung im Dev-Modus
- [ ] **Formate**
    - [ ] Datumsformate sind locale-abhängig
    - [ ] Zeitformate sind locale-abhängig
    - [ ] Zahlenformate sind locale-abhängig (Dezimal-/Tausendertrennzeichen)
- [ ] **Pluralisierung**
    - [ ] Pluralisierung funktioniert korrekt für alle unterstützten Sprachen
    - [ ] Dynamische Werte werden über Platzhalter eingefügt
    - [ ] Keine String-Konkatenation für Satzbildung
- [ ] **Testing**
    - [ ] Lint-Regel prüft, dass keine hartcodierten Strings in Komponenten vorhanden sind
    - [ ] Automatisierte Tests prüfen Vollständigkeit der Übersetzungsdateien
    - [ ] Visuelle Tests für beide Sprachen (Layout-Brüche durch längere Texte)

---

## 5. Risiken bei Nicht-Einhaltung

| Risiko | Auswirkung | Wahrscheinlichkeit | Mitigation |
|---|---|---|---|
| **Hartcodierte Strings** | Nachträgliche i18n-Umstellung sehr aufwendig | Hoch | Lint-Regeln gegen hardcoded Strings, i18n von Anfang an |
| **Falsche Datums-/Zahlenformate** | Missverständnisse bei Nutzern (z.B. 01/02 = Januar oder Februar?) | Mittel | Intl API / locale-aware Formatierung |
| **Fehlende Pluralisierung** | Grammatisch falsche Texte (z.B. „1 Einträge") | Mittel | i18n-Bibliothek mit Pluralisierungs-Support |
| **Layout-Brüche bei Sprachwechsel** | Längere Texte in anderen Sprachen sprengen das Layout | Mittel | Visuelle Tests mit verschiedenen Sprachen |
| **Inkonsistente Übersetzungen** | Gleiche Begriffe werden unterschiedlich übersetzt | Mittel | Zentrales Glossar, Übersetzungs-Review |

---

**Dokumenten-Ende**

**Version**: 1.0
**Status**: Entwurf
**Letzte Aktualisierung**: 2026-02-26
**Review**: Pending
**Genehmigung**: Pending
