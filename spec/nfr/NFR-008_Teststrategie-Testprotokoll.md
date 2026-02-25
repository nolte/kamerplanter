---

ID: NFR-008
Titel: Teststrategie & Testprotokoll — Testpyramide, E2E-Tests, Protokollierung
Kategorie: Qualitätssicherung Unterkategorie: Teststrategie, E2E-Testing, Testdokumentation Fokus: Beides (Zierpflanze & Nutzpflanze)
Technologie: pytest, vitest, Selenium WebDriver, testcontainers, httpx, factory_boy
Status: Entwurf
Priorität: Hoch
Version: 1.0
Autor: Business Analyst - Agrotech
Datum: 2026-02-26
Tags: [testing, test-strategy, test-pyramid, e2e, selenium, test-protocol, quality-assurance, screenshots]
Abhängigkeiten: [NFR-001, NFR-003, NFR-006, NFR-007]
Betroffene Module: [ALL]
---

# NFR-008: Teststrategie & Testprotokoll

## Abgrenzung zu bestehenden NFRs

| NFR | Fokus | Definiert |
|---|---|---|
| NFR-001 (Abschnitt 9) | Codebeispiele für Backend/Frontend-Tests | **Wie** Tests aussehen |
| NFR-003 | Tooling (pytest, vitest, coverage 80%) | **Werkzeuge & Schwellwerte** |
| NFR-006 (Abschnitt 8) | Integrationstests für Fehlerformat | **Spezifische Testanforderung** |
| NFR-007 (Abschnitt 6) | Smoke-Tests, Post-Deployment-Checks | **Betriebstests** |
| **NFR-008 (dieses Dokument)** | Testpyramide, E2E-Strategie, Testprotokoll | **Gesamtstrategie & Dokumentation** |

NFR-008 definiert die **übergreifende Teststrategie** und das **Testprotokoll-Format**. Werkzeuge und Schwellwerte aus NFR-003 gelten weiterhin; dieses Dokument ergänzt sie um Teststufen-Definitionen, E2E-Architektur und eine formale Protokollierung zur Nachverfolgung von UI-Veränderungen.

---

## 1. Business Case

### 1.1 User Stories

**Als** Entwickler
**möchte ich** eine klar definierte Testpyramide mit Werkzeugen und Regeln pro Teststufe
**um** bei jeder Änderung gezielt die passenden Tests auszuführen und Regressionsfehler frühzeitig zu erkennen.

**Als** QA-Engineer
**möchte ich** automatisierte E2E-Tests mit Screenshots an definierten Checkpoints
**um** visuell nachvollziehen zu können, ob die Benutzeroberfläche wie erwartet funktioniert und sich über die Zeit verändert.

**Als** Produktmanager
**möchte ich** Testprotokolle als lebende Dokumentation des Anwendungszustands
**um** bei Reviews und Audits den aktuellen Funktionsumfang und dessen Qualität belegen zu können.

**Als** Auditor
**möchte ich** datierte Testprotokolle mit Commit-Hash und Screenshot-Referenzen
**um** nachweisen zu können, welche Funktionalität zu welchem Zeitpunkt geprüft und verifiziert wurde.

### 1.2 Geschäftliche Motivation

Ohne zentrale Teststrategie:

1. **Lückenhafte Testabdeckung** — Ohne definierte Teststufen werden Integrationsszenarien und E2E-Flows übersehen
2. **Keine Nachvollziehbarkeit** — Ohne Protokollierung ist nicht belegbar, was wann getestet wurde
3. **Regressionsfehler** — Ohne systematische E2E-Tests werden UI-Brüche erst nach Deployment entdeckt
4. **Inkonsistente Testqualität** — Ohne Architekturvorgaben (Page-Object-Pattern) entstehen fragile, unwartbare Tests
5. **Fehlende Dokumentation** — Testprotokolle mit Screenshots dokumentieren den Anwendungszustand über die Entwicklungszeit hinweg

### 1.3 Fachliche Beschreibung

Praktisches Beispiel:

> **Szenario**: Ein Entwickler ändert die Phasenübergangs-Logik (REQ-003) und den zugehörigen UI-Dialog.
> **Ohne NFR-008**: Unit-Tests laufen grün, aber der E2E-Flow "Pflanze von Vegetativ nach Blüte überführen" ist visuell gebrochen. Es existiert kein Referenz-Screenshot.
> **Mit NFR-008**: Der E2E-Test erkennt den Fehler, erstellt Screenshots und ein Testprotokoll. Der Entwickler vergleicht den neuen Screenshot mit früheren Protokollen und erkennt die unbeabsichtigte Änderung sofort.

---

## 2. Testpyramide & Teststufen

### 2.1 Übersicht

```
          ┌───────────────┐
          │  E2E-Tests    │   ← Wenige, gezielte Selenium-Tests
          │  (Selenium)   │     Kernfunktionen validieren
          ├───────────────┤
          │  API-/Contract│   ← Alle Endpunkte, Schema-Validation
          │  Tests        │
          ├───────────────┤
          │ Integrations- │   ← Kritische Pfade mit realen
          │ tests         │     Abhängigkeiten (Testcontainers)
          ├───────────────┤
          │  Unit-Tests   │   ← Breite Basis, schnell, isoliert
          │               │     ≥80% Coverage
          └───────────────┘
```

### 2.2 Teststufen im Detail

| Stufe | Werkzeuge | Coverage-Ziel | Ausführung |
|---|---|---|---|
| **Unit-Tests** | pytest (Backend), vitest (Frontend) | ≥80% (vgl. NFR-003) | Lokal + CI |
| **Integrationstests** | pytest + testcontainers (ArangoDB, Redis), vitest + MSW | Kritische Pfade | Lokal + CI |
| **API-/Contract-Tests** | pytest + httpx (TestClient), Pydantic-Schema-Validation | Alle Endpunkte | Lokal + CI |
| **E2E-Tests (Selenium)** | Selenium WebDriver, pytest-selenium, pytest-html | Kernfunktionen | Lokal |

### 2.3 Stufe 1: Unit-Tests

**Scope**: Einzelne Funktionen, Klassen und Module isoliert von externen Abhängigkeiten.

**MUSS**: Unit-Tests erreichen ≥80% Line-Coverage für Backend und Frontend (vgl. NFR-003).
**MUSS**: Unit-Tests verwenden Mocks/Stubs für Datenbank-, Netzwerk- und Dateisystem-Zugriffe.
**MUSS**: Jeder Unit-Test ist unabhängig und deterministisch — keine Reihenfolge-Abhängigkeiten.

**Backend-Beispiel** (vgl. NFR-001 Abschnitt 9 für weitere Beispiele):

```python
# tests/unit/services/test_vpd_calculator.py
import pytest
from app.calculators.vpd_calculator import calculate_vpd


class TestVPDCalculator:
    """Tests für die VPD-Berechnung (Tetens-Formel)."""

    def test_vpd_vegetative_optimal(self):
        """VPD im vegetativen Bereich (0.8–1.5 kPa)."""
        vpd = calculate_vpd(temperature=25.0, humidity=60.0)
        assert 0.8 <= vpd <= 1.5

    def test_vpd_zero_humidity(self):
        """100% Luftfeuchtigkeit → VPD = 0."""
        vpd = calculate_vpd(temperature=25.0, humidity=100.0)
        assert vpd == pytest.approx(0.0, abs=0.01)

    def test_vpd_negative_temperature(self):
        """Negative Temperatur → gültiger VPD-Wert."""
        vpd = calculate_vpd(temperature=-5.0, humidity=80.0)
        assert vpd >= 0.0
```

**Frontend-Beispiel**:

```typescript
// src/__tests__/utils/gdd-calculator.test.ts
import { describe, it, expect } from "vitest";
import { calculateGDD } from "@/utils/gdd-calculator";

describe("GDD Calculator", () => {
  it("calculates growing degree days correctly", () => {
    const gdd = calculateGDD({ tempMax: 30, tempMin: 20, baseTemp: 10 });
    expect(gdd).toBe(15);
  });

  it("returns zero when average is below base temperature", () => {
    const gdd = calculateGDD({ tempMax: 8, tempMin: 4, baseTemp: 10 });
    expect(gdd).toBe(0);
  });
});
```

### 2.4 Stufe 2: Integrationstests

**Scope**: Zusammenspiel mehrerer Komponenten mit realen Abhängigkeiten (Datenbank, Cache).

**MUSS**: Integrationstests verwenden testcontainers für ArangoDB und Redis — keine In-Memory-Fakes.
**MUSS**: Jeder Integrationstest räumt seine Testdaten nach Ausführung auf (vgl. Abschnitt 5).
**SOLL**: Integrationstests decken mindestens folgende kritische Pfade ab:
- Phasenübergänge mit Datenbankpersistenz (REQ-003)
- Companion-Planting-Graph-Queries (REQ-001)
- Standort-Slot-Kapazitätsberechnung (REQ-002)
- Fehlerformat-Validierung (NFR-006)

**Beispiel**:

```python
# tests/integration/test_phase_transition_persistence.py
import pytest
from testcontainers.arangodb import ArangoDbContainer

from app.services.phase_transition_service import PhaseTransitionService
from app.repositories.plant_repository import PlantRepository


@pytest.fixture(scope="module")
def arangodb():
    with ArangoDbContainer("arangodb:3.11") as container:
        yield container.get_connection_url()


class TestPhaseTransitionPersistence:
    """Phasenübergang mit realer ArangoDB."""

    async def test_transition_vegetative_to_flowering(self, arangodb, sample_plant):
        repo = PlantRepository(connection_url=arangodb)
        service = PhaseTransitionService(repository=repo)

        result = await service.transition(
            plant_id=sample_plant.id,
            target_phase="flowering",
        )

        assert result.current_phase == "flowering"
        persisted = await repo.get(sample_plant.id)
        assert persisted.current_phase == "flowering"

    async def test_backward_transition_rejected(self, arangodb, sample_plant):
        """Rückwärts-Transition ist nicht erlaubt."""
        repo = PlantRepository(connection_url=arangodb)
        service = PhaseTransitionService(repository=repo)

        with pytest.raises(InvalidTransitionError):
            await service.transition(
                plant_id=sample_plant.id,
                target_phase="germination",
            )
```

### 2.5 Stufe 3: API-/Contract-Tests

**Scope**: HTTP-Endpunkte über den FastAPI-TestClient, Schema-Validierung der Responses.

**MUSS**: Jeder API-Endpunkt hat mindestens einen Happy-Path- und einen Error-Path-Test.
**MUSS**: API-Tests validieren Response-Schemas gegen die Pydantic-Modelle.
**MUSS**: Error-Responses werden gegen das NFR-006-Fehlerformat geprüft (error_id, code, message, details).

**Beispiel**:

```python
# tests/api/test_botanical_families_api.py
import pytest
from httpx import AsyncClient

from app.main import app


@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


class TestBotanicalFamiliesAPI:
    """Contract-Tests für /api/v1/botanical-families."""

    async def test_list_families_returns_paginated(self, client):
        response = await client.get("/api/v1/botanical-families?limit=10")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert len(data["items"]) <= 10

    async def test_get_nonexistent_family_returns_404(self, client):
        response = await client.get("/api/v1/botanical-families/nonexistent-id")
        assert response.status_code == 404
        error = response.json()
        # NFR-006: Fehlerformat-Validierung
        assert "error_id" in error
        assert "code" in error
        assert "message" in error

    async def test_create_family_validates_schema(self, client):
        response = await client.post(
            "/api/v1/botanical-families",
            json={"invalid_field": "value"},
        )
        assert response.status_code == 422
```

### 2.6 Stufe 4: E2E-Tests (Selenium)

Vollständig spezifiziert in Abschnitt 3.

---

## 3. E2E-Tests mit Selenium

### 3.1 Browser-Konfiguration

**MUSS**: E2E-Tests laufen standardmäßig im Chrome-Headless-Modus.
**SOLL**: Firefox als alternativer Browser unterstützt werden.

```python
# tests/e2e/conftest.py
import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions


@pytest.fixture(scope="session")
def browser(request):
    """Browser-Fixture mit konfigurierbarem Typ."""
    browser_name = request.config.getoption("--browser", default="chrome")

    if browser_name == "chrome":
        options = ChromeOptions()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")
        driver = webdriver.Chrome(options=options)
    elif browser_name == "firefox":
        options = webdriver.FirefoxOptions()
        options.add_argument("--headless")
        driver = webdriver.Firefox(options=options)
    else:
        raise ValueError(f"Unsupported browser: {browser_name}")

    driver.implicitly_wait(10)
    yield driver
    driver.quit()
```

**MUSS**: CLI-Optionen für Browser-Auswahl:

```python
# tests/e2e/conftest.py (Ergänzung)
def pytest_addoption(parser):
    parser.addoption(
        "--browser",
        action="store",
        default="chrome",
        choices=["chrome", "firefox"],
        help="Browser für E2E-Tests (default: chrome)",
    )
    parser.addoption(
        "--base-url",
        action="store",
        default="http://localhost:3000",
        help="Base-URL der Anwendung (default: http://localhost:3000)",
    )
    parser.addoption(
        "--generate-protocol",
        action="store_true",
        default=False,
        help="Testprotokoll mit Screenshots generieren",
    )
```

### 3.2 Page-Object-Pattern

**MUSS**: Alle E2E-Tests verwenden das Page-Object-Pattern. Direkte Selenium-Aufrufe (`find_element`, `click`) sind in Testklassen nicht erlaubt.

**Begründung**: Page Objects kapseln UI-Selektoren und Interaktionen. Bei UI-Änderungen muss nur das Page Object angepasst werden, nicht jeder einzelne Test.

```python
# tests/e2e/pages/base_page.py
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class BasePage:
    """Basisklasse für alle Page Objects."""

    def __init__(self, driver: WebDriver, base_url: str):
        self.driver = driver
        self.base_url = base_url
        self.wait = WebDriverWait(driver, timeout=15)

    def navigate(self, path: str = "") -> None:
        self.driver.get(f"{self.base_url}{path}")

    def wait_for_element(self, locator):
        return self.wait.until(EC.presence_of_element_located(locator))

    def take_screenshot(self, name: str, output_dir: str) -> str:
        """Screenshot aufnehmen und Pfad zurückgeben."""
        filepath = f"{output_dir}/{name}.png"
        self.driver.save_screenshot(filepath)
        return filepath
```

```python
# tests/e2e/pages/dashboard_page.py
from selenium.webdriver.common.by import By

from tests.e2e.pages.base_page import BasePage


class DashboardPage(BasePage):
    """Page Object für das Dashboard."""

    # Locators
    PLANT_COUNT = (By.CSS_SELECTOR, "[data-testid='plant-count']")
    LOCATION_LIST = (By.CSS_SELECTOR, "[data-testid='location-list']")
    ALERT_BANNER = (By.CSS_SELECTOR, "[data-testid='alert-banner']")

    def open(self) -> "DashboardPage":
        self.navigate("/dashboard")
        self.wait_for_element(self.PLANT_COUNT)
        return self

    def get_plant_count(self) -> int:
        element = self.wait_for_element(self.PLANT_COUNT)
        return int(element.text)

    def get_location_names(self) -> list[str]:
        elements = self.driver.find_elements(*self.LOCATION_LIST)
        return [el.text for el in elements]
```

```python
# tests/e2e/pages/plant_detail_page.py
from selenium.webdriver.common.by import By

from tests.e2e.pages.base_page import BasePage


class PlantDetailPage(BasePage):
    """Page Object für die Pflanzendetailansicht."""

    # Locators
    PLANT_NAME = (By.CSS_SELECTOR, "[data-testid='plant-name']")
    CURRENT_PHASE = (By.CSS_SELECTOR, "[data-testid='current-phase']")
    TRANSITION_BUTTON = (By.CSS_SELECTOR, "[data-testid='transition-button']")
    CONFIRM_DIALOG = (By.CSS_SELECTOR, "[data-testid='confirm-dialog']")
    CONFIRM_BUTTON = (By.CSS_SELECTOR, "[data-testid='confirm-button']")

    def open(self, plant_id: str) -> "PlantDetailPage":
        self.navigate(f"/plants/{plant_id}")
        self.wait_for_element(self.PLANT_NAME)
        return self

    def get_current_phase(self) -> str:
        element = self.wait_for_element(self.CURRENT_PHASE)
        return element.text

    def initiate_phase_transition(self) -> None:
        button = self.wait_for_element(self.TRANSITION_BUTTON)
        button.click()
        self.wait_for_element(self.CONFIRM_DIALOG)

    def confirm_transition(self) -> None:
        button = self.wait_for_element(self.CONFIRM_BUTTON)
        button.click()
```

### 3.3 Zu testende Kernfunktionen

**MUSS**: E2E-Tests decken mindestens folgende Kernfunktionen ab:

| Kernfunktion | REQ-Referenz | Beschreibung |
|---|---|---|
| **Pflanzenverwaltung** | REQ-001 | Pflanze anlegen, bearbeiten, Detailansicht |
| **Standortverwaltung** | REQ-002 | Standort anlegen, Slots konfigurieren, Kapazitätsanzeige |
| **Phasenübergang** | REQ-003 | Transition auslösen, Bestätigungsdialog, Phase-Anzeige aktualisiert |
| **Dashboard** | REQ-009 | Übersicht lädt, Kennzahlen werden angezeigt |
| **Fehleranzeige** | NFR-006 | Validierungsfehler werden benutzerfreundlich dargestellt |

**SOLL**: E2E-Tests für weitere Kernfunktionen (Düngung, Ernte, IPM) werden ergänzt, sobald die zugehörigen REQs implementiert sind.

**Beispiel**:

```python
# tests/e2e/test_plant_lifecycle.py
import pytest

from tests.e2e.pages.dashboard_page import DashboardPage
from tests.e2e.pages.plant_detail_page import PlantDetailPage


class TestPlantLifecycleE2E:
    """E2E-Test: Pflanzen-Lebenszyklus über die UI."""

    def test_dashboard_shows_plant_count(self, browser, base_url, screenshot):
        dashboard = DashboardPage(browser, base_url).open()
        screenshot("001_dashboard-overview")

        count = dashboard.get_plant_count()
        assert count >= 0

    def test_phase_transition_via_ui(self, browser, base_url, screenshot):
        detail = PlantDetailPage(browser, base_url).open(plant_id="test-plant-1")
        screenshot("002_plant-detail-before-transition")

        assert detail.get_current_phase() == "Vegetativ"

        detail.initiate_phase_transition()
        screenshot("003_transition-confirm-dialog")

        detail.confirm_transition()
        screenshot("004_plant-detail-after-transition")

        assert detail.get_current_phase() == "Blüte"
```

### 3.4 Screenshot-Aufnahme

**MUSS**: Screenshots werden an folgenden Checkpoints aufgenommen:
1. Nach dem Laden einer neuen Seite (Page Load)
2. Vor und nach signifikanten Benutzeraktionen (z.B. Phasenübergang)
3. Bei Fehlerzuständen (Validierungsfehler, Serverfehler)
4. Automatisch bei Test-Failure

**MUSS**: Screenshot-Fixture für einheitliche Benennung:

```python
# tests/e2e/conftest.py (Ergänzung)
import os
from datetime import datetime


@pytest.fixture
def screenshot(browser, request):
    """Fixture für benannte Screenshots."""
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    output_dir = f"test-reports/{timestamp}/screenshots"
    os.makedirs(output_dir, exist_ok=True)

    def _capture(name: str) -> str:
        filepath = f"{output_dir}/{name}.png"
        browser.save_screenshot(filepath)
        return filepath

    yield _capture

    # Automatisch Screenshot bei Test-Failure
    if request.node.rep_call and request.node.rep_call.failed:
        _capture(f"FAILURE_{request.node.name}")
```

**MUSS**: Failure-Screenshot-Hook:

```python
# tests/e2e/conftest.py (Ergänzung)
@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Testergebnis am Request-Node verfügbar machen."""
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)
```

---

## 4. Testprotokoll

### 4.1 Zweck

Testprotokolle dienen als **lebende Entwicklungsdokumentation**:

- **Nachvollziehbarkeit**: Welche Funktionalität wurde zu welchem Zeitpunkt (Commit) geprüft?
- **UI-Veränderungsverfolgung**: Screenshots dokumentieren den visuellen Zustand der Anwendung über die Entwicklungszeit
- **Audit-Fähigkeit**: Datierte Protokolle mit Commit-Hash belegen den Qualitätsstatus
- **Regressionserkennung**: Vergleich früherer Protokolle mit aktuellen Ergebnissen

### 4.2 Ablageort

**MUSS**: Testprotokolle werden im Verzeichnis `test-reports/` abgelegt.
**MUSS**: Das Verzeichnis `test-reports/` ist in `.gitignore` eingetragen — Protokolle werden **nicht** eingecheckt.
**MUSS**: Jeder Testlauf erzeugt einen Unterordner mit Zeitstempel.

```
test-reports/
├── 2026-02-26_14-30-00/
│   ├── protokoll.md
│   └── screenshots/
│       ├── 001_dashboard-overview.png
│       ├── 002_plant-detail-before-transition.png
│       ├── 003_transition-confirm-dialog.png
│       ├── 004_plant-detail-after-transition.png
│       └── FAILURE_test_validation_error.png
├── 2026-02-27_09-15-00/
│   ├── protokoll.md
│   └── screenshots/
│       └── ...
└── .gitkeep  ← (optional) damit das Verzeichnis im Repo existiert
```

### 4.3 Protokoll-Format

**MUSS**: Jedes Testprotokoll ist eine Markdown-Datei mit folgendem Aufbau:

```markdown
# Testprotokoll — [DATUM]

## Metadaten

| Feld | Wert |
|---|---|
| **Datum** | 2026-02-26 14:30:00 |
| **Commit** | `a1b2c3d` (main) |
| **Branch** | main |
| **Ausführender** | max.mustermann |
| **Betriebssystem** | Ubuntu 22.04 |
| **Browser** | Chrome 121.0 (headless) |
| **Python** | 3.12.1 |
| **Node.js** | 20.11.0 |

## Zusammenfassung

| Stufe | Gesamt | Bestanden | Fehlgeschlagen | Übersprungen |
|---|---|---|---|---|
| Unit-Tests (Backend) | 142 | 140 | 1 | 1 |
| Unit-Tests (Frontend) | 87 | 87 | 0 | 0 |
| Integrationstests | 23 | 23 | 0 | 0 |
| API-/Contract-Tests | 45 | 44 | 1 | 0 |
| E2E-Tests | 12 | 11 | 1 | 0 |
| **Gesamt** | **309** | **305** | **3** | **1** |

## Coverage

| Modul | Line Coverage | Branch Coverage | Ziel (NFR-003) |
|---|---|---|---|
| Backend gesamt | 83.2% | 71.4% | ≥80% ✅ |
| Frontend gesamt | 81.7% | 68.9% | ≥80% ✅ |

## Fehlgeschlagene Tests

### ❌ test_create_family_validates_schema
- **Stufe**: API-/Contract-Test
- **Datei**: `tests/api/test_botanical_families_api.py:45`
- **Fehler**: `AssertionError: expected 422, got 400`
- **Ursache**: Schema-Validation liefert 400 statt 422 nach FastAPI-Update
- **Priorität**: Mittel

### ❌ test_phase_transition_via_ui
- **Stufe**: E2E-Test
- **Datei**: `tests/e2e/test_plant_lifecycle.py:28`
- **Fehler**: `TimeoutException: Element [data-testid='transition-button'] not found`
- **Screenshot**: [FAILURE_test_phase_transition_via_ui](screenshots/FAILURE_test_phase_transition_via_ui.png)
- **Ursache**: Button-Testid wurde umbenannt
- **Priorität**: Hoch

## Screenshots (E2E)

| Nr. | Beschreibung | Screenshot |
|---|---|---|
| 001 | Dashboard-Übersicht | ![001](screenshots/001_dashboard-overview.png) |
| 002 | Pflanzendetail vor Transition | ![002](screenshots/002_plant-detail-before-transition.png) |
| 003 | Bestätigungsdialog | ![003](screenshots/003_transition-confirm-dialog.png) |
| 004 | Pflanzendetail nach Transition | ![004](screenshots/004_plant-detail-after-transition.png) |

## Anmerkungen

- [Freitext für manuelle Beobachtungen, bekannte Probleme etc.]
```

### 4.4 Automatische Protokoll-Generierung

**MUSS**: Testprotokolle werden durch einen pytest-Hook automatisch generiert, wenn `--generate-protocol` übergeben wird.

```python
# tests/e2e/protocol_plugin.py
"""pytest-Plugin zur automatischen Testprotokoll-Generierung."""
import os
import subprocess
from datetime import datetime

import pytest


class ProtocolGenerator:
    """Sammelt Testergebnisse und erzeugt ein Markdown-Protokoll."""

    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        self.results: list[dict] = []
        self.start_time: datetime | None = None

    def add_result(self, nodeid: str, outcome: str, duration: float, longrepr: str = ""):
        self.results.append({
            "nodeid": nodeid,
            "outcome": outcome,
            "duration": duration,
            "longrepr": longrepr,
        })

    def generate(self) -> str:
        """Erzeugt die protokoll.md-Datei."""
        os.makedirs(self.output_dir, exist_ok=True)
        filepath = os.path.join(self.output_dir, "protokoll.md")

        commit = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True,
        ).stdout.strip()

        branch = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True, text=True,
        ).stdout.strip()

        passed = sum(1 for r in self.results if r["outcome"] == "passed")
        failed = sum(1 for r in self.results if r["outcome"] == "failed")
        skipped = sum(1 for r in self.results if r["outcome"] == "skipped")
        total = len(self.results)

        with open(filepath, "w") as f:
            f.write(f"# Testprotokoll — {self.start_time:%Y-%m-%d %H:%M:%S}\n\n")
            f.write("## Metadaten\n\n")
            f.write("| Feld | Wert |\n|---|---|\n")
            f.write(f"| **Datum** | {self.start_time:%Y-%m-%d %H:%M:%S} |\n")
            f.write(f"| **Commit** | `{commit}` ({branch}) |\n")
            f.write(f"| **Branch** | {branch} |\n\n")
            f.write("## Zusammenfassung\n\n")
            f.write("| Gesamt | Bestanden | Fehlgeschlagen | Übersprungen |\n")
            f.write("|---|---|---|---|\n")
            f.write(f"| {total} | {passed} | {failed} | {skipped} |\n\n")

            if failed > 0:
                f.write("## Fehlgeschlagene Tests\n\n")
                for r in self.results:
                    if r["outcome"] == "failed":
                        f.write(f"### {r['nodeid']}\n\n")
                        f.write(f"```\n{r['longrepr']}\n```\n\n")

            # Screenshot-Referenzen
            screenshot_dir = os.path.join(self.output_dir, "screenshots")
            if os.path.isdir(screenshot_dir):
                screenshots = sorted(os.listdir(screenshot_dir))
                if screenshots:
                    f.write("## Screenshots\n\n")
                    f.write("| Nr. | Datei |\n|---|---|\n")
                    for i, s in enumerate(screenshots, 1):
                        f.write(f"| {i:03d} | ![{s}](screenshots/{s}) |\n")
                    f.write("\n")

        return filepath


def pytest_configure(config):
    if config.getoption("--generate-protocol", default=False):
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        output_dir = f"test-reports/{timestamp}"
        generator = ProtocolGenerator(output_dir)
        config._protocol_generator = generator


def pytest_sessionstart(session):
    generator = getattr(session.config, "_protocol_generator", None)
    if generator:
        generator.start_time = datetime.now()


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    if rep.when == "call":
        generator = getattr(item.config, "_protocol_generator", None)
        if generator:
            generator.add_result(
                nodeid=rep.nodeid,
                outcome=rep.outcome,
                duration=rep.duration,
                longrepr=str(rep.longrepr) if rep.failed else "",
            )


def pytest_sessionfinish(session, exitstatus):
    generator = getattr(session.config, "_protocol_generator", None)
    if generator:
        filepath = generator.generate()
        print(f"\nTestprotokoll generiert: {filepath}")
```

---

## 5. Testdaten-Strategie

### 5.1 Fixtures

**MUSS**: Reproduzierbare Testdaten werden über pytest-Fixtures (Backend) bzw. Test-Utilities (Frontend) bereitgestellt.
**MUSS**: Fixtures erzeugen keine Seiteneffekte außerhalb ihres Scopes.

```python
# tests/conftest.py
import pytest

from tests.factories import BotanicalFamilyFactory, PlantFactory, LocationFactory


@pytest.fixture
def sample_family():
    return BotanicalFamilyFactory.build(
        scientific_name="Solanaceae",
        common_name="Nachtschattengewächse",
    )


@pytest.fixture
def sample_plant(sample_family):
    return PlantFactory.build(
        name="Tomate Roma",
        family=sample_family,
        current_phase="vegetative",
    )


@pytest.fixture
def sample_location():
    return LocationFactory.build(
        name="Gewächshaus Nord",
        slot_count=20,
    )
```

### 5.2 Factory-Pattern

**SOLL**: Testdaten werden über das Factory-Pattern erzeugt (factory_boy oder manuelle Factories).

```python
# tests/factories.py
from app.models.botanical_family import BotanicalFamily
from app.models.plant import Plant
from app.models.location import Location


class BotanicalFamilyFactory:
    """Factory für BotanicalFamily-Testdaten."""

    _counter = 0

    @classmethod
    def build(cls, **overrides) -> BotanicalFamily:
        cls._counter += 1
        defaults = {
            "scientific_name": f"Testaceae-{cls._counter}",
            "common_name": f"Testfamilie {cls._counter}",
        }
        defaults.update(overrides)
        return BotanicalFamily(**defaults)


class PlantFactory:
    """Factory für Plant-Testdaten."""

    _counter = 0

    @classmethod
    def build(cls, **overrides) -> Plant:
        cls._counter += 1
        defaults = {
            "name": f"Testpflanze-{cls._counter}",
            "current_phase": "seedling",
        }
        defaults.update(overrides)
        return Plant(**defaults)


class LocationFactory:
    """Factory für Location-Testdaten."""

    _counter = 0

    @classmethod
    def build(cls, **overrides) -> Location:
        cls._counter += 1
        defaults = {
            "name": f"Teststandort-{cls._counter}",
            "slot_count": 10,
        }
        defaults.update(overrides)
        return Location(**defaults)
```

### 5.3 Isolation

**MUSS**: Jeder Test räumt seine Daten auf — kein Test hinterlässt Zustand, der andere Tests beeinflusst.
**MUSS**: Integrationstests mit testcontainers verwenden entweder:
- **Transaktion-Rollback** pro Test (bevorzugt), oder
- **Collection-Truncate** in einer Teardown-Fixture

```python
# tests/integration/conftest.py
import pytest


@pytest.fixture(autouse=True)
async def clean_collections(arangodb_client):
    """Bereinigt alle Test-Collections nach jedem Test."""
    yield
    for collection_name in arangodb_client.collections():
        if not collection_name.startswith("_"):  # System-Collections auslassen
            arangodb_client.collection(collection_name).truncate()
```

---

## 6. Lokale Testausführung

### 6.1 Voraussetzungen

| Abhängigkeit | Zweck | Installation |
|---|---|---|
| Docker | testcontainers (ArangoDB, Redis) | [docs.docker.com](https://docs.docker.com/get-docker/) |
| Chrome / Chromium | Selenium E2E-Tests | Paketmanager oder [chrome.google.com](https://www.google.com/chrome/) |
| ChromeDriver | Selenium WebDriver für Chrome | `pip install chromedriver-autoinstaller` oder manuell |
| Firefox + GeckoDriver | Alternativer Browser (optional) | Paketmanager |

### 6.2 Befehle pro Teststufe

```bash
# Unit-Tests Backend
pytest tests/unit/ -v --cov=app --cov-report=term-missing

# Unit-Tests Frontend
npx vitest run --coverage

# Integrationstests (erfordert Docker)
pytest tests/integration/ -v --timeout=60

# API-/Contract-Tests
pytest tests/api/ -v

# E2E-Tests (erfordert laufende Anwendung + Chrome)
pytest tests/e2e/ -v --browser=chrome

# E2E-Tests MIT Testprotokoll-Generierung
pytest tests/e2e/ -v --browser=chrome --generate-protocol

# Alle Tests (außer E2E)
pytest tests/unit/ tests/integration/ tests/api/ -v --cov=app

# Alle Tests inkl. E2E mit Protokoll
pytest tests/ -v --browser=chrome --generate-protocol
```

### 6.3 Protokoll-Generierung

**MUSS**: Die Protokoll-Generierung wird über den CLI-Parameter `--generate-protocol` aktiviert.
**MUSS**: Ohne diesen Parameter werden keine Protokolle erzeugt — Tests laufen normal.

```bash
# Protokoll erzeugen
pytest tests/e2e/ --generate-protocol

# Ergebnis:
# test-reports/2026-02-26_14-30-00/
# ├── protokoll.md
# └── screenshots/
#     ├── 001_dashboard-overview.png
#     └── ...
```

---

## 7. Akzeptanzkriterien

### Definition of Done

- [ ] **Testpyramide**
    - [ ] Vier Teststufen (Unit, Integration, API/Contract, E2E) sind definiert und dokumentiert
    - [ ] Werkzeuge und Coverage-Ziele pro Stufe sind festgelegt
    - [ ] Mindestens ein Codebeispiel pro Stufe vorhanden
- [ ] **Unit-Tests**
    - [ ] ≥80% Line-Coverage für Backend und Frontend (vgl. NFR-003)
    - [ ] Alle Unit-Tests sind deterministisch und unabhängig
    - [ ] Mocks/Stubs für externe Abhängigkeiten
- [ ] **Integrationstests**
    - [ ] testcontainers für ArangoDB und Redis konfiguriert
    - [ ] Kritische Pfade (Phasenübergänge, Graph-Queries, Slot-Kapazität) abgedeckt
    - [ ] Testdaten-Isolation (Cleanup nach jedem Test)
- [ ] **API-/Contract-Tests**
    - [ ] Jeder Endpunkt hat Happy-Path- und Error-Path-Test
    - [ ] Response-Schemas werden gegen Pydantic-Modelle validiert
    - [ ] Error-Responses entsprechen NFR-006-Format
- [ ] **E2E-Tests (Selenium)**
    - [ ] Chrome-Headless als Standard-Browser konfiguriert
    - [ ] Page-Object-Pattern für alle Page-Interaktionen
    - [ ] Alle Kernfunktionen (Pflanzenverwaltung, Standorte, Phasenübergänge, Dashboard) abgedeckt
    - [ ] Screenshots an definierten Checkpoints
    - [ ] Automatischer Failure-Screenshot
- [ ] **Testprotokoll**
    - [ ] Ablageort `test-reports/` in `.gitignore`
    - [ ] Zeitstempel-basierte Unterordner-Struktur
    - [ ] Markdown-Protokoll mit Metadaten, Zusammenfassung, Fehlern, Screenshots
    - [ ] Automatische Generierung via `--generate-protocol`
- [ ] **Testdaten**
    - [ ] Factory-Pattern für reproduzierbare Testdaten
    - [ ] Isolation: Jeder Test räumt seine Daten auf
- [ ] **Lokale Ausführung**
    - [ ] Voraussetzungen dokumentiert
    - [ ] Befehle pro Teststufe aufgelistet
    - [ ] Protokoll-Generierung als optionaler Parameter

---

## 8. Risiken bei Nicht-Einhaltung

| Risiko | Auswirkung | Wahrscheinlichkeit | Mitigation |
|---|---|---|---|
| **Keine definierte Testpyramide** | Übergewicht an E2E-Tests (langsam, fragil) oder nur Unit-Tests (fehlende Integration) | Hoch | Klare Teststufen mit Scope-Definition und Coverage-Zielen |
| **E2E-Tests ohne Page-Object-Pattern** | Fragile Tests, die bei jeder UI-Änderung brechen; hoher Wartungsaufwand | Hoch | Page-Object-Pattern als MUSS-Vorgabe, Codebeispiele als Vorlage |
| **Fehlende Testdaten-Isolation** | Tests beeinflussen sich gegenseitig; nicht-deterministische Ergebnisse | Mittel | Cleanup-Fixtures, Transaktion-Rollback, Collection-Truncate |
| **Keine Testprotokolle** | Fehlende Nachvollziehbarkeit, kein Audit-Trail, UI-Veränderungen unbemerkt | Mittel | Automatische Protokoll-Generierung, Screenshot-Checkpoints |
| **Testcontainers nicht verfügbar** | Integrationstests können lokal nicht ausgeführt werden | Niedrig | Docker als Voraussetzung dokumentieren, CI als Fallback |
| **Selenium-Abhängigkeit auf Browser-Version** | E2E-Tests brechen bei Browser-Updates | Mittel | chromedriver-autoinstaller, versionierte Browser in CI |
| **Protokoll-Inflation** | Zu viele Protokolle verbrauchen Speicherplatz | Niedrig | Lokale Ablage, regelmäßige manuelle Bereinigung, nicht eingecheckt |

---

**Dokumenten-Ende**

**Version**: 1.0
**Status**: Entwurf
**Letzte Aktualisierung**: 2026-02-26
**Review**: Pending
**Genehmigung**: Pending
