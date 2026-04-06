---
ID: NFR-008a
Titel: E2E-Selenium-Teststandard — Verbindliche Konventionen fuer Selenium-E2E-Tests
Kategorie: Qualitaetssicherung
Unterkategorie: E2E-Testing, Selenium, Testarchitektur
Fokus: Beides (Zierpflanze & Nutzpflanze)
Technologie: pytest, Selenium WebDriver, Chrome Headless, Page-Object-Pattern
Status: Verbindlich
Prioritaet: Hoch
Version: 1.0
Autor: QA-Engineering
Datum: 2026-04-02
Tags: [e2e, selenium, test-standard, page-object, screenshots, testprotokoll, tc-ids, markers]
Abhaengigkeiten: [NFR-008]
Betroffene Module: [tests/e2e]
---

# NFR-008a: E2E-Selenium-Teststandard

## Abgrenzung

| Dokument | Fokus |
|----------|-------|
| **NFR-008** | Uebergreifende Teststrategie, Testpyramide, Protokoll-Format |
| **NFR-008a (dieses Dokument)** | Verbindliche Konventionen fuer jeden einzelnen Selenium-E2E-Test |

NFR-008 definiert das *Was* (Teststufen, Protokoll-Format, Screenshot-Checkpoints). NFR-008a definiert das *Wie* — die konkreten Code-Konventionen, die jeder E2E-Test einhalten MUSS.

Dieses Dokument ist die **primaere Referenz** fuer:
- `.claude/agents/selenium-test-generator.md` — beim Erzeugen neuer Tests
- `.claude/agents/selenium-test-reviewer.md` — beim Pruefen bestehender Tests
- `.claude/agents/e2e-result-reviewer.md` — beim Reviewen von Testergebnissen

---

## 1. Verzeichnisstruktur

```
tests/e2e/
  conftest.py                    # Session-Fixtures, CLI-Optionen, Seed-Daten
  protocol_plugin.py             # Testprotokoll-Generator
  requirements.txt               # Selenium + Abhaengigkeiten
  pages/
    __init__.py                  # Re-Export aller Page Objects
    base_page.py                 # BasePage mit gemeinsamen Helfern
    <entity>_<view>_page.py      # Ein Page Object pro Seite
  test_req<NNN>_<thema>.py       # Tests gruppiert nach REQ-Nummer
```

### Datei-Benennung

| Element | Pattern | Beispiel |
|---------|---------|----------|
| Testdatei | `test_req<NNN>_<thema>.py` | `test_req001_species.py` |
| Page Object | `<entity>_<view>_page.py` | `species_list_page.py`, `site_detail_page.py` |
| Testklasse | `Test<Entity><View>` | `TestSpeciesListPage`, `TestSiteDetailPage` |
| Testmethode | `test_<aktion>` | `test_display_species_in_data_table` |

---

## 2. Test-Datei-Aufbau (MUSS)

Jede Testdatei MUSS diesen Aufbau haben:

```python
"""E2E tests for REQ-<NNN> — <Titel>.

Spec-TC Mapping (test TC -> spec/e2e-testcases/TC-REQ-<NNN>.md):
  TC-REQ-<NNN>-<XXX>  ->  TC-<NNN>-<YYY>  <Spec-Beschreibung>
  TC-REQ-<NNN>-<XXX>  ->  TC-<NNN>-<YYY>  <Spec-Beschreibung>
  ...
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import pytest
from selenium.webdriver.remote.webdriver import WebDriver

from .pages import <PageObject1>, <PageObject2>


@pytest.fixture
def <page>(browser: WebDriver, base_url: str) -> <PageObject>:
    return <PageObject>(browser, base_url)


class Test<Entity><View>:
    """<Kurzbeschreibung> (Spec: TC-<NNN>-<A>, TC-<NNN>-<B>)."""

    @pytest.mark.smoke
    @pytest.mark.core_crud
    def test_<aktion>(
        self, <page>: <PageObject>, screenshot: Callable[..., Path]
    ) -> None:
        """TC-REQ-<NNN>-<XXX>: <Englische Beschreibung>.

        Spec: TC-<NNN>-<YYY> -- <Deutsche Spec-Beschreibung>.
        """
        ...
```

### 2.1 Modul-Docstring (MUSS)

- Erste Zeile: `"""E2E tests for REQ-<NNN> — <Titel>."""`
- Danach: **Spec-TC Mapping** als Kommentarblock — mappt jede Test-TC-ID auf die zugehoerige Spec-TC-ID aus `spec/e2e-testcases/TC-REQ-<NNN>.md`
- Zweck: Rueckverfolgbarkeit zwischen Test und Spezifikation

### 2.2 Test-Docstring (MUSS)

Jeder Test MUSS einen Docstring mit:

1. **TC-ID** als erste Zeile: `TC-REQ-<NNN>-<XXX>: <Englische Beschreibung>.`
2. **Spec-Referenz** als zweiter Absatz: `Spec: TC-<NNN>-<YYY> -- <Deutsche Spec-Beschreibung>.`

```python
def test_display_species_in_data_table(self, ...):
    """TC-REQ-001-029: Display species in a paginated data table.

    Spec: TC-001-019 -- Species-Liste laden und Grundspalten pruefen.
    """
```

Die TC-IDs im Test (TC-REQ-<NNN>-<XXX>) und in der Spec (TC-<NNN>-<YYY>) duerfen unterschiedliche Nummern haben — das Mapping im Modul-Docstring stellt die Verbindung her.

### 2.3 Klassen-Docstring (MUSS)

Jede Testklasse MUSS einen Docstring mit Spec-Referenz haben:

```python
class TestSpeciesListPage:
    """Species list display and navigation (Spec: TC-001-019, TC-001-030)."""
```

---

## 3. Pytest-Marker (MUSS)

Jeder Test MUSS mindestens einen Marker tragen. Verfuegbare Marker:

| Marker | Bedeutung | Verwendung |
|--------|-----------|------------|
| `@pytest.mark.smoke` | Rauchtest — die absoluten Basics | Seite laedt, Titel sichtbar, kein Crash |
| `@pytest.mark.core_crud` | Kern-CRUD-Operationen | Erstellen, Anzeigen, Bearbeiten, Loeschen |
| `@pytest.mark.requires_auth` | Nur im Full-Mode (mit Auth) | Login, Register, Passwort-Reset |

Testlauf-Varianten:
```bash
pytest tests/e2e/ -m smoke            # Nur Smoke-Tests (~30s)
pytest tests/e2e/ -m core_crud        # CRUD-Kerntests (~5min)
pytest tests/e2e/                     # Alle Tests
```

---

## 4. Screenshot-Konventionen (MUSS)

### 4.1 Screenshot-Fixture

Tests verwenden die `screenshot` Fixture (Typ `Callable[..., Path]`):

```python
def test_example(self, page: SomePage, screenshot: Callable[..., Path]) -> None:
    page.open()
    screenshot("TC-REQ-001-029_species-list-loaded",
               "Species list page after initial load")
```

**Parameter:**
1. `name` (str): Screenshot-Dateiname — Pattern: `TC-REQ-<NNN>-<XXX>_<beschreibung>`
2. `description` (str): Menschenlesbare Beschreibung fuer das Testprotokoll

### 4.2 Pflicht-Checkpoints

| Checkpoint | Wann | Beispiel |
|------------|------|---------|
| **Page Load** | Nach jeder Navigation / `.open()` | `"TC-REQ-001-029_species-list-loaded"` |
| **Before Action** | Vor signifikanter Benutzeraktion | `"TC-REQ-001-031_before-row-click"` |
| **After Action** | Nach signifikanter Benutzeraktion | `"TC-REQ-001-031_after-row-click"` |
| **Error State** | Bei sichtbaren Fehlern/Validierung | `"TC-REQ-001-035_validation-error"` |
| **Failure** | Automatisch bei Test-Failure | `"FAILURE_test_method_name"` (via Hook) |

### 4.3 Benennung

```
TC-REQ-<NNN>-<XXX>_<kebab-case-beschreibung>.png
```

- Prefix MUSS die TC-ID sein
- Suffix MUSS den sichtbaren Zustand beschreiben
- Trennung mit Unterstrich `_`

Gute Beispiele:
- `TC-REQ-002-005_create-dialog-open.png`
- `TC-REQ-001-039_field-modified.png`
- `TC-REQ-002-016_before-edit.png`

Schlechte Beispiele:
- `screenshot1.png` (kein Kontext)
- `test.png` (nichtssagend)
- `TC-REQ-001-029.png` (keine Zustandsbeschreibung)

---

## 5. Page-Object-Pattern (MUSS)

### 5.1 Alle Page Objects erben von `BasePage`

```python
class SpeciesListPage(BasePage):
    PATH = "/stammdaten/species"
    PAGE = (By.CSS_SELECTOR, "[data-testid='species-list-page']")
    ...
```

### 5.2 Locator-Hierarchie

Locators in dieser Praezerenz-Reihenfolge verwenden:

1. `[data-testid='...']` (bevorzugt)
2. `#id` (wenn data-testid nicht verfuegbar)
3. CSS-Selektoren auf MUI-Klassen (`.MuiButton-root`)
4. `[role='...']` (fuer ARIA-Elemente wie TreeView)
5. XPath (nur als letztes Mittel, nie positionsbasiert)

**VERBOTEN** in Tests (nur in Page Objects erlaubt):
- `driver.find_element()`
- `driver.find_elements()`
- `By.XPATH` mit positionsbasierten Pfaden (`//div[3]/span[2]`)

### 5.3 Kein `time.sleep()` in Tests

| Verboten | Erlaubt |
|----------|---------|
| `time.sleep(3)` | `page.wait_for_loading_complete()` |
| `time.sleep(0.5)` nach Klick | `page.wait_for_element_visible(locator)` |
| `time.sleep(1)` fuer Animation | `page.wait_for_url_contains(fragment)` |

`time.sleep()` ist **ausschliesslich in Page Objects** erlaubt, und nur fuer:
- MUI-Animationen (max. `0.3s`)
- Debounce-Wartezeiten (max. `0.5s`)
- MUSS mit Kommentar begruendet sein

### 5.4 BasePage Pflicht-Methoden

Jedes Page Object erbt diese Methoden von `BasePage`:

| Methode | Zweck |
|---------|-------|
| `navigate(path)` | URL-Navigation relativ zur Base-URL |
| `wait_for_element(locator)` | Warten auf DOM-Praesenz (15s Timeout) |
| `wait_for_element_visible(locator)` | Warten auf Sichtbarkeit |
| `wait_for_element_clickable(locator)` | Warten auf Klickbarkeit |
| `wait_for_loading_complete()` | Warten bis LoadingSkeleton verschwindet |
| `wait_for_url_contains(fragment)` | Warten auf URL-Aenderung |
| `scroll_and_click(element)` | Scrollen + Klick (JS-Fallback) |
| `clear_and_fill(element, value)` | React-kompatibles Feld-Clearing + Eingabe |
| `expand_all_fields()` | REQ-021 "Alle Felder anzeigen"-Toggle klicken |

### 5.5 Page Object Pflicht-Struktur

```python
class <Entity><View>Page(BasePage):
    """Interact with <Seite> (``<route>``)."""

    PATH = "<route>"

    # ── Page markers ──
    PAGE = (By.CSS_SELECTOR, "[data-testid='<page-testid>']")
    LOADING_SKELETON = (By.CSS_SELECTOR, "[data-testid='loading-skeleton']")

    # ── Locators (gruppiert nach Funktion) ──
    FORM_NAME = (By.CSS_SELECTOR, "[data-testid='form-field-name'] input")
    ...

    def open(self, key: str | None = None) -> "<Entity><View>Page":
        """Navigieren und auf Seiteninhalt warten."""
        self.navigate(f"{self.PATH}/{key}" if key else self.PATH)
        self.wait_for_element(self.PAGE)
        self.wait_for_loading_complete()
        return self

    # ── Page state ──
    def get_title(self) -> str: ...
    def get_row_count(self) -> int: ...

    # ── Interactions ──
    def click_create(self) -> None: ...
    def click_row(self, index: int) -> None: ...
    def submit_form(self) -> None: ...
```

---

## 6. Assertions (MUSS)

### 6.1 Beschreibende Fehlermeldungen

Jede Assertion MUSS eine Fehlermeldung mit TC-ID haben:

```python
# GUT:
assert "/stammdaten/species/" in driver.current_url, (
    f"TC-REQ-001-031 FAIL: Expected URL to contain '/stammdaten/species/', "
    f"got '{driver.current_url}'"
)

# SCHLECHT:
assert "/stammdaten/species/" in driver.current_url
```

### 6.2 Keine leeren Assertions

```python
# VERBOTEN:
assert True
assert page is not None

# KORREKT:
assert row_count >= 1, "TC-REQ-001-029 FAIL: Expected at least 1 species row"
```

---

## 7. Testdaten / Seed-Fixture (MUSS)

### 7.1 Idempotente Seed-Daten

Die `e2e_seed_data` Fixture (conftest.py, scope=session) MUSS:

1. **Idempotent** sein — pruefen ob Daten bereits existieren bevor sie angelegt werden
2. **Unterscheidbare Namen** verwenden — keine generischen "E2E-Test"-Namen
3. **Realistische Werte** setzen — Klimazone, Flaeche, Zeitzone etc. befuellen
4. **Mehrere Entitaeten** anlegen fuer Listentests (min. 2 Sites, 2 Locations)

### 7.2 Test-spezifische Daten

Tests die eigene Daten erstellen (z.B. Delete-Tests) MUSS:
1. Eindeutige Namen mit `uuid.uuid4().hex[:6]` Suffix verwenden
2. Nach dem Erstellen die Existenz verifizieren bevor der naechste Schritt laeuft
3. Suchfunktion nutzen wenn Pagination die neue Entitaet verbergen koennte

```python
# GUT:
unique = uuid.uuid4().hex[:6]
species_list.fill_scientific_name(f"Deletus testii{unique}")

# SCHLECHT:
species_list.fill_scientific_name("Test")
```

---

## 8. Precondition-Handling (MUSS)

### 8.1 Fehlende Testdaten -> pytest.skip

Wenn Testdaten nicht verfuegbar sind, MUSS `pytest.skip()` mit beschreibender Nachricht verwendet werden:

```python
if species_list.get_row_count() == 0:
    pytest.skip("No species in database")
```

### 8.2 Kein stilles Ueberspringen

```python
# VERBOTEN — Test tut nichts wenn Precondition fehlt:
if row_count == 0:
    return

# KORREKT — expliziter Skip mit Grund:
if row_count == 0:
    pytest.skip("No data available for this test")
```

---

## 9. Testprotokoll-Integration (MUSS)

### 9.1 Jeder Test erzeugt Protokoll-Daten

Die `protocol_plugin.py` sammelt automatisch:
- Testname, TC-ID, Ergebnis (PASS/FAIL/SKIP), Dauer
- Screenshot-Referenzen mit Beschreibungen
- Fehlerdetails bei FAIL

### 9.2 Protokoll-Ausgabe

Bei `--generate-protocol` wird `protokoll.md` erzeugt mit:
- Metadaten (Datum, Commit, Branch, Browser)
- Zusammenfassung (Bestanden/Fehlgeschlagen/Uebersprungen)
- Abgedeckte REQ-Nummern
- Detail-Ergebnisse pro Testklasse
- Screenshot-Galerie mit Beschreibungen

### 9.3 REQ-Abdeckungs-Tracking

Das Protokoll MUSS pro REQ auflisten wie viele Tests zugeordnet sind:

```markdown
| REQ | Tests |
|-----|-------|
| REQ-001 | 9 |
| REQ-002 | 10 |
```

---

## 10. Checkliste fuer neue E2E-Tests

Bevor ein neuer E2E-Test als fertig gilt, MUSS er folgende Kriterien erfuellen:

- [ ] Dateiname folgt `test_req<NNN>_<thema>.py` Pattern
- [ ] Modul-Docstring mit Spec-TC Mapping vorhanden
- [ ] Jeder Test hat TC-ID + Spec-Referenz im Docstring
- [ ] Jede Testklasse hat Spec-Referenz im Docstring
- [ ] Mindestens ein Pytest-Marker (`smoke`, `core_crud`, `requires_auth`)
- [ ] Screenshots an allen Pflicht-Checkpoints (Page Load, Before/After Action)
- [ ] Screenshot-Namen folgen `TC-REQ-<NNN>-<XXX>_<beschreibung>` Pattern
- [ ] Alle UI-Interaktionen ueber Page Objects (kein `find_element` im Test)
- [ ] Kein `time.sleep()` im Test (nur in Page Objects, begruendet)
- [ ] Alle Assertions haben beschreibende Fehlermeldungen mit TC-ID
- [ ] Test-spezifische Daten verwenden UUID-Suffixe
- [ ] Fehlende Preconditions fuehren zu `pytest.skip()` mit Beschreibung
- [ ] `python -m pytest --collect-only` zeigt den Test als sammelbar

---

## 11. Anti-Patterns (VERBOTEN)

| Anti-Pattern | Korrekte Alternative |
|-------------|---------------------|
| `time.sleep(N)` im Test | `wait_for_element()` / `wait_for_loading_complete()` |
| `driver.find_element()` im Test | Page-Object-Methode |
| `By.XPATH, "//div[3]/span[2]"` | `[data-testid='...']` |
| `assert True` | Beschreibende Assertion mit Pruefwert |
| Test ohne Screenshot | Min. 1 Screenshot pro Test |
| Test ohne TC-ID | `TC-REQ-<NNN>-<XXX>` im Docstring |
| Test ohne Marker | `@pytest.mark.smoke` oder `@pytest.mark.core_crud` |
| Generischer Testdaten-Name | UUID-Suffix: `f"Testus {uuid.uuid4().hex[:6]}"` |
| Stilles `return` bei fehlenden Daten | `pytest.skip("Reason")` |
| Screenshot ohne Beschreibung | Immer 2. Parameter mit Description |

---

## 12. Referenz-Implementierung

Die folgenden Dateien sind die **Referenz-Implementierung** (Gen-3-Standard) und dienen als Vorlage:

| Datei | Zeigt |
|-------|-------|
| `tests/e2e/conftest.py` | Session-Fixtures, CLI-Optionen, Seed-Daten, Marker-Registrierung |
| `tests/e2e/pages/base_page.py` | BasePage mit allen Pflicht-Methoden |
| `tests/e2e/pages/species_list_page.py` | Page Object fuer Listenseite |
| `tests/e2e/pages/site_detail_page.py` | Page Object fuer Detailseite (inkl. TreeView) |
| `tests/e2e/test_req001_species.py` | Referenz-Test mit TC-Mapping, Markern, Screenshots |
| `tests/e2e/test_req001_cultivar.py` | Referenz-Test fuer Sub-Entity (Cultivar in Species) |
| `tests/e2e/test_req002_standorte.py` | Referenz-Test fuer mehrstufige Hierarchie |
| `tests/e2e/protocol_plugin.py` | Testprotokoll-Generator (NFR-008 §4.4) |
