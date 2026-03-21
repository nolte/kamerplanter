---
req_id: NFR-008
title: Teststrategie & Testprotokoll — Testpyramide, E2E-Tests, Protokollierung
category: Qualitaetssicherung / Teststrategie
test_count: 48
coverage_areas:
  - Testpyramide-Konformitaet (Unit, Integration, API/Contract, E2E)
  - Selenium-Browser-Konfiguration (Chrome-Headless, Firefox-Option)
  - Page-Object-Pattern — Einhaltung und Funktionalitaet
  - Screenshot-Checkpoints (Page-Load, vor/nach Aktion, Failure-Automatik)
  - Testprotokoll-Generierung via --generate-protocol (Format, Ablageort, Inhalt)
  - Protokoll-Metadaten (Datum, Commit-Hash, Branch, Browser, OS)
  - Fehlgeschlagene-Tests-Abschnitt im Protokoll (nodeid, longrepr, Screenshot-Link)
  - Testdaten-Factories (BotanicalFamilyFactory, PlantFactory, LocationFactory)
  - Testdaten-Isolation (Collection-Truncate, kein Test-Seiteneffekt)
  - testcontainers fuer ArangoDB und Redis
  - Lokale Testausfuehrung (Befehle pro Teststufe, --browser CLI-Option)
  - GitIgnore-Konformitaet fuer test-reports/
  - E2E-Kernfunktionen-Abdeckung (Pflanzenverwaltung, Standort, Phasenuebergang, Dashboard, Fehleranzeige)
  - Coverage-Schwellwert >=80% (Backend + Frontend, vgl. NFR-003)
generated: 2026-03-21
version: "1.0"
---

# TC-NFR-008: Teststrategie & Testprotokoll

Dieses Dokument enthaelt End-to-End-Testfaelle aus **NFR-008 Teststrategie & Testprotokoll v1.0**, ausschliesslich aus der Perspektive eines **Entwicklers oder QA-Engineers**, der die Testinfrastruktur selbst ausfuehrt und beobachtet. NFR-008 ist eine Meta-NFR — sie definiert keine fachliche UI-Funktion, sondern die Qualitaetssicherungsinfrastruktur. Die Testfaelle pruefen deshalb:

- Ob die konfigurierten Testwerkzeuge korrekt starten und ausgeben
- Ob das Testprotokoll-Format vollstaendig und korrekt ist
- Ob Page-Objects korrekt kapseln (kein direkter Selenium-Aufruf in Testklassen)
- Ob Screenshots an den vorgeschriebenen Checkpoints entstehen
- Ob die Testdaten-Isolation sicherstellt, dass Tests voneinander unabhaengig sind

**Tester-Perspektive**: Ein QA-Engineer sitzt am Terminal (oder sieht einen CI-Log), fuehrt pytest-Befehle aus und beobachtet, was auf dem Dateisystem und im Terminal erscheint. Kein Nutzer-Browser ist der Testgegenstand — stattdessen ist die **E2E-Testinfrastruktur selbst** das System under Test (SuT).

**Sonderfall E2E-Kernfunktionen** (Gruppe 8): Diese Testfaelle pruefen, ob konkrete E2E-Tests korrekt laufen — hier tritt ein realer Browser auf, und die Testfaelle beschreiben Browser-sichtbare Ergebnisse durch den Selenium-Treiber.

Die UI-Sprache der getesteten Anwendung ist **Deutsch** (Standard-Locale).

---

## 1. Testpyramide — Werkzeuge und Coverage-Ziele

*Abdeckung: NFR-008 §2.1, §2.2, §2.3, §7 (DoD: Testpyramide)*

---

### TC-NFR008-001: Backend-Unit-Tests erzielen mindestens 80 % Line-Coverage

**Requirement**: NFR-008 §2.3 — Unit-Tests MUSS ≥80 % Line-Coverage; vgl. NFR-003
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- Projekt-Repository ist ausgecheckt
- Python-Abhaengigkeiten sind installiert (`pip install -e ".[dev]"`)
- `pytest` und `pytest-cov` sind verfuegbar

**Testschritte**:
1. QA-Engineer oeffnet ein Terminal im Projektverzeichnis
2. QA-Engineer fuehrt aus: `pytest tests/unit/ -v --cov=app --cov-report=term-missing`
3. QA-Engineer wartet, bis alle Tests ausgefuehrt sind

**Erwartete Ergebnisse**:
- Der pytest-Lauf endet ohne Fehler-Exit-Code (Exit 0)
- Die Coverage-Ausgabe zeigt fuer `app` (Backend gesamt) einen Line-Coverage-Wert von **≥80 %**
- Die Zeile `TOTAL` in der Coverage-Tabelle zeigt einen Prozentwert ≥ 80
- Kein Test-Ergebnis zeigt `FAILED` oder `ERROR`

**Postconditions**:
- Coverage-Report liegt im Terminal-Output vor; keine Dateien veraendert

**Tags**: [nfr-008, unit-test, coverage, backend, pytest, nfr-003]

---

### TC-NFR008-002: Frontend-Unit-Tests erzielen mindestens 80 % Line-Coverage

**Requirement**: NFR-008 §2.3 — Unit-Tests MUSS ≥80 % Line-Coverage fuer Frontend; vgl. NFR-003
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- Node.js und npm/pnpm sind installiert (vgl. `.tool-versions` im `src/frontend/`-Verzeichnis)
- Frontend-Abhaengigkeiten sind installiert (`npm install` in `src/frontend/`)
- `vitest` und `@vitest/coverage-v8` sind konfiguriert

**Testschritte**:
1. QA-Engineer oeffnet ein Terminal im Verzeichnis `src/frontend/`
2. QA-Engineer fuehrt aus: `npx vitest run --coverage`
3. QA-Engineer wartet, bis alle Tests ausgefuehrt sind

**Erwartete Ergebnisse**:
- Der Vitest-Lauf endet ohne Fehler-Exit-Code (Exit 0)
- Die Coverage-Ausgabe zeigt fuer den Frontend-Code einen Line-Coverage-Wert von **≥80 %**
- Die Spalte `Stmts` oder `Lines` in der Coverage-Tabelle zeigt ≥ 80 % fuer das Gesamt-Bundle
- Kein Test-Ergebnis zeigt `FAIL`

**Postconditions**:
- Coverage-Report liegt im Terminal-Output vor

**Tags**: [nfr-008, unit-test, coverage, frontend, vitest, nfr-003]

---

### TC-NFR008-003: Unit-Tests sind deterministisch — wiederholte Ausfuehrung liefert identisches Ergebnis

**Requirement**: NFR-008 §2.3 — MUSS: Jeder Unit-Test ist unabhaengig und deterministisch
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- Backend-Unit-Tests sind konfiguriert (siehe TC-NFR008-001)

**Testschritte**:
1. QA-Engineer fuehrt aus: `pytest tests/unit/ -v` (dreimalige Ausfuehrung nacheinander)
2. QA-Engineer notiert die Anzahl bestandener, fehlgeschlagener und uebersprungener Tests pro Lauf

**Erwartete Ergebnisse**:
- Alle drei Laeufe liefern identische Ergebnis-Zaehlungen (gleiche Anzahl passed/failed/skipped)
- Kein Test schlaegt in einem Lauf fehl, der in einem anderen besteht ("Flaky Test")
- Die Ausfuehrungs-Reihenfolge beeinflusst kein Testergebnis

**Postconditions**:
- Keine persistenten Seiteneffekte; Dateisystem und Datenbank unveraendert

**Tags**: [nfr-008, unit-test, determinismus, isolation, pytest]

---

### TC-NFR008-004: Unit-Tests verwenden ausschliesslich Mocks fuer externe Abhaengigkeiten

**Requirement**: NFR-008 §2.3 — MUSS: Unit-Tests verwenden Mocks/Stubs fuer Datenbank-, Netzwerk- und Dateisystem-Zugriffe
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- ArangoDB und Redis sind **nicht** gestartet (Docker-Dienste gestoppt)
- Backend-Unit-Tests sind konfiguriert

**Testschritte**:
1. QA-Engineer stellt sicher, dass ArangoDB und Redis-Container nicht laufen
2. QA-Engineer fuehrt aus: `pytest tests/unit/ -v`

**Erwartete Ergebnisse**:
- Alle Unit-Tests bestehen trotz fehlender Datenbank-Verbindung
- Kein Test zeigt `ConnectionRefusedError`, `ArangoError` oder `RedisConnectionError`
- Die Test-Zusammenfassung zeigt ausschliesslich `passed` oder `skipped` (keine `failed`)

**Postconditions**:
- ArangoDB und Redis bleiben gestoppt; kein unbeabsichtigter Verbindungsversuch

**Tags**: [nfr-008, unit-test, mocking, isolation, backend]

---

## 2. Integrationstests mit testcontainers

*Abdeckung: NFR-008 §2.4, §7 (DoD: Integrationstests)*

---

### TC-NFR008-005: Integrationstests starten ArangoDB-Container via testcontainers

**Requirement**: NFR-008 §2.4 — MUSS: Integrationstests verwenden testcontainers fuer ArangoDB — keine In-Memory-Fakes
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- Docker ist installiert und gestartet
- `testcontainers` Python-Paket ist installiert
- Backend-Integrationstest-Suite ist konfiguriert (`tests/integration/`)

**Testschritte**:
1. QA-Engineer fuehrt aus: `pytest tests/integration/ -v --timeout=60`
2. QA-Engineer beobachtet die Terminalausgabe waehrend des Test-Starts

**Erwartete Ergebnisse**:
- Im Terminal erscheint eine Meldung, dass ein ArangoDB-Container gestartet wird (testcontainers-Log)
- Die Container-ID oder der Port-Mapping-Hinweis ist im Output sichtbar (z. B. `Pulling arangodb:3.11...`)
- Alle Integrationstests bestehen (Exit 0)
- Nach Testende wird der Container automatisch gestoppt und entfernt

**Postconditions**:
- Kein ArangoDB-Container laeuft nach Testende (`docker ps` zeigt keinen Test-Container)

**Tags**: [nfr-008, integration-test, testcontainers, arangodb, docker]

---

### TC-NFR008-006: Integrationstests starten Redis-Container via testcontainers

**Requirement**: NFR-008 §2.4 — MUSS: testcontainers fuer Redis
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- Docker ist installiert und gestartet
- Redis-Integrationstest-Fixtures sind konfiguriert

**Testschritte**:
1. QA-Engineer fuehrt aus: `pytest tests/integration/ -v -k redis --timeout=60`
2. QA-Engineer beobachtet die Container-Start-Meldungen

**Erwartete Ergebnisse**:
- Ein Redis-Container wird gestartet (Log-Eintrag im Terminal sichtbar)
- Alle Redis-Integrationstests bestehen
- Nach Testende wird der Container automatisch gestoppt

**Postconditions**:
- Kein Redis-Container laeuft nach Testende

**Tags**: [nfr-008, integration-test, testcontainers, redis, docker]

---

### TC-NFR008-007: Phasenuebergangs-Integrationstest mit realer ArangoDB

**Requirement**: NFR-008 §2.4 — SOLL: Phasenuebergaenge mit Datenbankpersistenz (REQ-003) abgedeckt
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- Docker ist verfuegbar; `tests/integration/test_phase_transition_persistence.py` existiert
- `sample_plant`-Fixture erzeugt eine Pflanze im Zustand `vegetative`

**Testschritte**:
1. QA-Engineer fuehrt aus: `pytest tests/integration/test_phase_transition_persistence.py -v`

**Erwartete Ergebnisse**:
- `test_transition_vegetative_to_flowering` besteht: Pflanze ist nach der Transition in Phase `flowering` und der Datenbankzustand stimmt ueberein
- `test_backward_transition_rejected` besteht: Transition zurueck nach `germination` wird abgelehnt — kein `PASSED`-Ergebnis ohne Exception

**Postconditions**:
- Testdaten werden in Teardown-Fixture bereinigt (Collection-Truncate)

**Tags**: [nfr-008, integration-test, phasenuebergang, req-003, arangodb]

---

### TC-NFR008-008: Testdaten-Isolation — kein Test hinterlaesst Zustand fuer Folgetest

**Requirement**: NFR-008 §5.3 — MUSS: Jeder Test raeumt seine Daten auf
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- `clean_collections`-Fixture mit `autouse=True` ist in `tests/integration/conftest.py` konfiguriert

**Testschritte**:
1. QA-Engineer fuehrt alle Integrationstests zweimal nacheinander aus: `pytest tests/integration/ -v`
2. QA-Engineer vergleicht die Test-Ergebnisse beider Laeufe

**Erwartete Ergebnisse**:
- Beide Laeufe liefern identische Ergebnisse (gleiche Anzahl passed/failed)
- Kein Test schlaegt im zweiten Lauf fehl, weil ein vorheriger Test Daten-Reste hinterlassen hat
- Bei Einzelausfuehrung eines Integrationstests (Isolation) laeuft dieser genauso durch wie im Gesamtlauf

**Postconditions**:
- Alle Test-Collections sind nach jedem Testlauf leer (keine Testreste)

**Tags**: [nfr-008, integration-test, isolation, cleanup, testdaten]

---

## 3. API-/Contract-Tests

*Abdeckung: NFR-008 §2.5, §7 (DoD: API-/Contract-Tests)*

---

### TC-NFR008-009: Jeder API-Endpunkt hat Happy-Path-Test

**Requirement**: NFR-008 §2.5 — MUSS: Jeder API-Endpunkt hat mindestens einen Happy-Path-Test
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- API-Test-Suite existiert unter `tests/api/`
- FastAPI-TestClient ist konfiguriert

**Testschritte**:
1. QA-Engineer fuehrt aus: `pytest tests/api/ -v --co -q` (nur Test-Sammlung, kein Ausfuehren)
2. QA-Engineer prueft die Liste der gesammelten Tests auf fehlende Endpunkte

**Erwartete Ergebnisse**:
- Fuer jeden in `src/backend/app/api/` definierten Router existiert mindestens eine Testdatei unter `tests/api/`
- Jeder gefundene Test-Dateiname korrespondiert mit einem Router-Modul

**Postconditions**:
- Keine Tests wurden ausgefuehrt; nur Sammlung geprueft

**Tags**: [nfr-008, api-test, contract-test, abdeckung]

---

### TC-NFR008-010: API-Test-Happy-Path fuer botanische Familien gibt paginierte Liste zurueck

**Requirement**: NFR-008 §2.5 — Response-Schema wird gegen Pydantic-Modell validiert
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- `tests/api/test_botanical_families_api.py` existiert mit `test_list_families_returns_paginated`

**Testschritte**:
1. QA-Engineer fuehrt aus: `pytest tests/api/test_botanical_families_api.py::TestBotanicalFamiliesAPI::test_list_families_returns_paginated -v`

**Erwartete Ergebnisse**:
- Test besteht: Antwort enthaelt Felder `items` (Liste) und `total` (Integer)
- Die Laenge von `items` ist kleiner oder gleich dem angeforderten `limit=10`
- Kein Assertion-Fehler bezueglich des Response-Schemas

**Postconditions**:
- Keine Datenbankeintraege erstellt oder geloescht

**Tags**: [nfr-008, api-test, contract-test, pagination, botanical-families]

---

### TC-NFR008-011: API-Error-Path liefert NFR-006-konformes Fehlerformat

**Requirement**: NFR-008 §2.5 — Error-Responses werden gegen NFR-006-Fehlerformat geprueft (error_id, code, message, details)
**Priority**: Critical
**Category**: Fehlermeldung
**Preconditions**:
- `tests/api/test_botanical_families_api.py` existiert mit `test_get_nonexistent_family_returns_404`
- NFR-006-Fehlerformat-Validierung ist implementiert

**Testschritte**:
1. QA-Engineer fuehrt aus: `pytest tests/api/test_botanical_families_api.py::TestBotanicalFamiliesAPI::test_get_nonexistent_family_returns_404 -v`

**Erwartete Ergebnisse**:
- Test besteht: Fehlerobjekt enthaelt die Felder `error_id`, `code` und `message`
- `error_id` folgt dem Format `err_<uuid4>` (kein leerer String, kein Null-Wert)
- `code` ist ein valider Fehlercode (z. B. `ENTITY_NOT_FOUND`)
- Kein Assertion-Fehler bezueglich des NFR-006-Formats

**Postconditions**:
- Keine Datenbankeintraege veraendert

**Tags**: [nfr-008, api-test, contract-test, fehlerformat, nfr-006]

---

### TC-NFR008-012: API-Validierungsfehler bei ungueltigem Schema

**Requirement**: NFR-008 §2.5 — MUSS: API-Tests validieren Response-Schemas gegen Pydantic-Modelle
**Priority**: High
**Category**: Formvalidierung
**Preconditions**:
- `tests/api/test_botanical_families_api.py` mit `test_create_family_validates_schema` ist vorhanden

**Testschritte**:
1. QA-Engineer fuehrt aus: `pytest tests/api/test_botanical_families_api.py::TestBotanicalFamiliesAPI::test_create_family_validates_schema -v`

**Erwartete Ergebnisse**:
- Test besteht: Ungueltige Nutzlast (`{"invalid_field": "value"}`) fuehrt zur Ablehnung
- Die Fehlermeldung im Response entspricht dem NFR-006-Fehlerformat

**Postconditions**:
- Kein Datenbankeintrag wurde erstellt

**Tags**: [nfr-008, api-test, schema-validierung, pydantic, nfr-006]

---

## 4. Selenium-Browser-Konfiguration

*Abdeckung: NFR-008 §3.1, §6.2*

---

### TC-NFR008-013: E2E-Tests starten standardmaessig mit Chrome-Headless

**Requirement**: NFR-008 §3.1 — MUSS: E2E-Tests laufen standardmaessig im Chrome-Headless-Modus
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- Chrome oder Chromium ist installiert
- ChromeDriver ist installiert (oder `chromedriver-autoinstaller` konfiguriert)
- Frontend-Anwendung laeuft auf `http://localhost:5173`
- `tests/e2e/conftest.py` enthaelt `browser`-Fixture mit `--headless=new`

**Testschritte**:
1. QA-Engineer fuehrt aus: `pytest tests/e2e/ -v --browser=chrome`
2. QA-Engineer beobachtet, ob ein sichtbares Chrome-Fenster geoeffnet wird

**Erwartete Ergebnisse**:
- Kein sichtbares Chrome-Fenster oeffnet sich (Headless-Modus aktiv)
- Die E2E-Tests starten und navigieren ohne `WebDriverException`
- Die pytest-Ausgabe zeigt, dass der `browser`-Fixture mit `chrome` initialisiert wurde

**Postconditions**:
- Chrome-Driver wird nach Testende beendet (kein Zombie-Prozess)

**Tags**: [nfr-008, e2e, selenium, chrome, headless]

---

### TC-NFR008-014: E2E-Tests unterstuetzen Firefox als alternativen Browser

**Requirement**: NFR-008 §3.1 — SOLL: Firefox als alternativer Browser unterstuetzt werden
**Priority**: Medium
**Category**: Happy Path
**Preconditions**:
- Firefox und GeckoDriver sind installiert
- Frontend-Anwendung laeuft auf `http://localhost:5173`

**Testschritte**:
1. QA-Engineer fuehrt aus: `pytest tests/e2e/ -v --browser=firefox`
2. QA-Engineer beobachtet, ob die Tests ohne `WebDriverException` starten

**Erwartete Ergebnisse**:
- Kein sichtbares Firefox-Fenster oeffnet sich (Headless-Modus aktiv)
- Die E2E-Tests laufen durch ohne `ValueError: Unsupported browser: firefox`
- Ergebnisse sind vergleichbar mit dem Chrome-Lauf

**Postconditions**:
- GeckoDriver wird nach Testende beendet

**Tags**: [nfr-008, e2e, selenium, firefox, headless]

---

### TC-NFR008-015: Ungueltige Browser-Angabe erzeugt klare Fehlermeldung

**Requirement**: NFR-008 §3.1 — CLI-Option `--browser` mit validen Werten `[chrome, firefox]`
**Priority**: Low
**Category**: Fehlermeldung
**Preconditions**:
- E2E-Test-Suite ist konfiguriert

**Testschritte**:
1. QA-Engineer fuehrt aus: `pytest tests/e2e/ -v --browser=safari`

**Erwartete Ergebnisse**:
- pytest zeigt einen Fehler: `error: argument --browser: invalid choice: 'safari' (choose from 'chrome', 'firefox')`
- Kein Test wird ausgefuehrt
- Exit-Code ist ungleich 0

**Postconditions**:
- Keine Browser-Instanz wurde gestartet

**Tags**: [nfr-008, e2e, cli, fehlermeldung, browser-validierung]

---

### TC-NFR008-016: CLI-Option --base-url steuert Anwendungs-URL der E2E-Tests

**Requirement**: NFR-008 §3.1 — CLI-Option `--base-url` mit Default `http://localhost:5173`
**Priority**: Medium
**Category**: Happy Path
**Preconditions**:
- Frontend-Anwendung laeuft auf einer benutzerdefinierten URL (z. B. `http://localhost:3000`)
- E2E-Test-Suite ist konfiguriert

**Testschritte**:
1. QA-Engineer fuehrt aus: `pytest tests/e2e/ -v --browser=chrome --base-url=http://localhost:3000 -k test_dashboard`

**Erwartete Ergebnisse**:
- Der E2E-Test navigiert zur URL `http://localhost:3000/dashboard` (nicht zum Default `localhost:5173`)
- Kein `ERR_CONNECTION_REFUSED` bei `localhost:5173`
- Test laeuft auf der konfigurierten Basis-URL durch

**Postconditions**:
- Keine Konfigurationsdateien veraendert

**Tags**: [nfr-008, e2e, cli, base-url, konfiguration]

---

## 5. Page-Object-Pattern

*Abdeckung: NFR-008 §3.2, §7 (DoD: Page-Object-Pattern fuer alle Page-Interaktionen)*

---

### TC-NFR008-017: BasePage.navigate() oeffnet korrekte URL

**Requirement**: NFR-008 §3.2 — MUSS: Alle E2E-Tests verwenden das Page-Object-Pattern; BasePage kapselt Navigation
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- `tests/e2e/pages/base_page.py` existiert mit `BasePage`-Klasse und `navigate()`-Methode
- Frontend-Anwendung laeuft auf `http://localhost:5173`

**Testschritte**:
1. QA-Engineer fuehrt einen E2E-Test aus, der `BasePage.navigate("/dashboard")` aufruft
2. QA-Engineer prueft die URL im Driver-Zustand nach dem Navigations-Aufruf

**Erwartete Ergebnisse**:
- `driver.current_url` entspricht `http://localhost:5173/dashboard`
- Kein `driver.get()`-Aufruf ausserhalb einer Page-Object-Methode sichtbar (Code-Review-Kriterium)

**Postconditions**:
- Browser ist auf der Dashboard-Seite

**Tags**: [nfr-008, page-object, base-page, navigation, e2e]

---

### TC-NFR008-018: DashboardPage.open() wartet auf plant-count-Element

**Requirement**: NFR-008 §3.2 — Page Objects kapseln Wait-Bedingungen; `DashboardPage.open()` wartet auf `[data-testid='plant-count']`
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- `tests/e2e/pages/dashboard_page.py` existiert mit `DashboardPage`-Klasse
- Frontend-Anwendung laeuft mit Demo-Daten (mindestens 0 Pflanzen)

**Testschritte**:
1. QA-Engineer fuehrt den E2E-Test `test_dashboard_shows_plant_count` aus
2. QA-Engineer beobachtet, ob `open()` auf das Element `[data-testid='plant-count']` wartet

**Erwartete Ergebnisse**:
- Test besteht ohne `TimeoutException`
- `get_plant_count()` gibt einen ganzzahligen Wert >= 0 zurueck
- Kein direkter `driver.find_element()`-Aufruf ausserhalb der Page-Object-Klasse

**Postconditions**:
- Browser ist auf der Dashboard-Seite; kein Datenbank-Seiteneffekt

**Tags**: [nfr-008, page-object, dashboard-page, data-testid, e2e]

---

### TC-NFR008-019: PlantDetailPage.initiate_phase_transition() oeffnet Bestaetigungsdialog

**Requirement**: NFR-008 §3.2 — PlantDetailPage kapselt Phasenuebergangs-Interaktion
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- `tests/e2e/pages/plant_detail_page.py` existiert mit `PlantDetailPage`-Klasse
- Testpflanze `test-plant-1` ist in Phase `Vegetativ`
- Frontend-Anwendung laeuft mit Demo-Daten

**Testschritte**:
1. QA-Engineer fuehrt aus: `pytest tests/e2e/test_plant_lifecycle.py::TestPlantLifecycleE2E::test_phase_transition_via_ui -v`
2. QA-Engineer beobachtet den Testablauf

**Erwartete Ergebnisse**:
- `initiate_phase_transition()` klickt den Transition-Button und wartet auf `[data-testid='confirm-dialog']`
- `get_current_phase()` gibt `"Vegetativ"` vor und `"Bluete"` nach der Transition zurueck
- Test besteht ohne `TimeoutException` oder `ElementNotInteractableException`

**Postconditions**:
- Testpflanze ist in Phase `Bluete`; Browser zeigt aktualisierte Phase-Anzeige

**Tags**: [nfr-008, page-object, plant-detail, phasenuebergang, e2e, req-003]

---

### TC-NFR008-020: Direkte Selenium-Aufrufe in Testklassen sind nicht erlaubt

**Requirement**: NFR-008 §3.2 — MUSS: Direkte Selenium-Aufrufe (`find_element`, `click`) sind in Testklassen nicht erlaubt
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- Alle E2E-Testdateien unter `tests/e2e/test_*.py` sind vorhanden

**Testschritte**:
1. QA-Engineer fuehrt aus: `grep -rn "find_element\|\.click()\|\.send_keys(" tests/e2e/test_*.py`

**Erwartete Ergebnisse**:
- Das grep-Ergebnis ist **leer** — keine direkten Selenium-Aufrufe in Testklassen-Dateien
- Alle `find_element`-, `click()`- und `send_keys()`-Aufrufe befinden sich ausschliesslich in Page-Object-Dateien unter `tests/e2e/pages/`

**Postconditions**:
- Keine Dateien veraendert

**Tags**: [nfr-008, page-object, code-qualitaet, selenium, architektur]

---

## 6. Screenshot-Checkpoints

*Abdeckung: NFR-008 §3.4, §7 (DoD: Screenshots an definierten Checkpoints)*

---

### TC-NFR008-021: Screenshot-Fixture erzeugt Datei im korrekten Verzeichnis

**Requirement**: NFR-008 §3.4 — MUSS: Screenshot-Fixture fuer einheitliche Benennung; Ablage in `test-reports/{timestamp}/screenshots/`
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- `tests/e2e/conftest.py` enthaelt `screenshot`-Fixture
- Frontend-Anwendung laeuft
- `--generate-protocol`-Flag wird gesetzt

**Testschritte**:
1. QA-Engineer fuehrt aus: `pytest tests/e2e/test_plant_lifecycle.py -v --browser=chrome --generate-protocol`
2. QA-Engineer navigiert im Dateisystem zu `test-reports/`

**Erwartete Ergebnisse**:
- Ein Unterordner mit Zeitstempel-Format `YYYY-MM-DD_HH-MM-SS` wurde erstellt
- Im Unterordner existiert das Verzeichnis `screenshots/`
- Im `screenshots/`-Verzeichnis befinden sich PNG-Dateien mit den definierten Namen (z. B. `001_dashboard-overview.png`)
- Die Dateinamen folgen dem Muster `{name}.png` wie im Fixture-Aufruf angegeben

**Postconditions**:
- Testprotokoll-Verzeichnis wurde angelegt; PNG-Dateien sind vorhanden

**Tags**: [nfr-008, screenshot, fixture, testprotokoll, dateisystem]

---

### TC-NFR008-022: Screenshot wird nach dem Laden jeder neuen Seite aufgenommen

**Requirement**: NFR-008 §3.4 — MUSS: Screenshots nach Page-Load aufnehmen
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- E2E-Test `test_dashboard_shows_plant_count` ruft `screenshot("001_dashboard-overview")` auf
- `--generate-protocol` ist aktiv

**Testschritte**:
1. QA-Engineer fuehrt aus: `pytest tests/e2e/test_plant_lifecycle.py::TestPlantLifecycleE2E::test_dashboard_shows_plant_count -v --generate-protocol`
2. QA-Engineer prueft das `screenshots/`-Verzeichnis nach Testende

**Erwartete Ergebnisse**:
- Die Datei `001_dashboard-overview.png` existiert im Screenshot-Verzeichnis
- Die Datei ist eine gueltige PNG-Datei (nicht leer, groesser als 1 KB)
- Das Bild zeigt die geladene Dashboard-Seite (keine leere oder Fehlerseitenansicht)

**Postconditions**:
- PNG-Datei ist auf dem Dateisystem vorhanden

**Tags**: [nfr-008, screenshot, page-load, checkpoint, e2e]

---

### TC-NFR008-023: Screenshots vor und nach signifikanter Benutzeraktion aufgenommen

**Requirement**: NFR-008 §3.4 — MUSS: Vor und nach signifikanten Benutzeraktionen (z. B. Phasenuebergang)
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- E2E-Test `test_phase_transition_via_ui` ruft Screenshots `002_plant-detail-before-transition`, `003_transition-confirm-dialog` und `004_plant-detail-after-transition` auf
- `--generate-protocol` ist aktiv

**Testschritte**:
1. QA-Engineer fuehrt aus: `pytest tests/e2e/test_plant_lifecycle.py::TestPlantLifecycleE2E::test_phase_transition_via_ui -v --generate-protocol`
2. QA-Engineer prueft das `screenshots/`-Verzeichnis nach Testende

**Erwartete Ergebnisse**:
- Die Dateien `002_plant-detail-before-transition.png`, `003_transition-confirm-dialog.png` und `004_plant-detail-after-transition.png` existieren
- Datei `002` zeigt Phase-Badge "Vegetativ"
- Datei `003` zeigt den geoeffneten Bestaetigungsdialog
- Datei `004` zeigt Phase-Badge "Bluete" (aktualisiert)

**Postconditions**:
- Drei PNG-Dateien auf dem Dateisystem vorhanden

**Tags**: [nfr-008, screenshot, vor-nach-aktion, phasenuebergang, e2e]

---

### TC-NFR008-024: Bei Test-Failure wird automatisch ein Failure-Screenshot erstellt

**Requirement**: NFR-008 §3.4 — MUSS: Automatisch bei Test-Failure
**Priority**: Critical
**Category**: Fehlermeldung
**Preconditions**:
- `pytest_runtest_makereport`-Hook ist in `conftest.py` konfiguriert (setzt `rep_call` am Request-Node)
- Ein E2E-Test schlaegt fehl (z. B. durch eine absichtlich falsche Assertion fuer diesen Qualitaetscheck)
- `--generate-protocol` ist aktiv

**Testschritte**:
1. QA-Engineer modifiziert einen E2E-Test temporaer so, dass er sicher fehlschlaegt (z. B. `assert 1 == 2`)
2. QA-Engineer fuehrt aus: `pytest tests/e2e/ -v --generate-protocol`
3. QA-Engineer prueft das `screenshots/`-Verzeichnis nach Testende

**Erwartete Ergebnisse**:
- Eine Datei mit dem Praefix `FAILURE_` gefolgt vom Testnamen existiert im `screenshots/`-Verzeichnis (z. B. `FAILURE_test_dashboard_shows_plant_count.png`)
- Die Datei ist eine gueltige PNG-Datei (nicht leer)
- Der pytest-Output zeigt den Teststatus als `FAILED`

**Postconditions**:
- Test-Modifikation wird rueckgaengig gemacht; Failure-Screenshot bleibt im Verzeichnis

**Tags**: [nfr-008, screenshot, failure, automatik, hook]

---

## 7. Testprotokoll-Generierung

*Abdeckung: NFR-008 §4.1, §4.2, §4.3, §4.4, §6.3*

---

### TC-NFR008-025: Testprotokoll wird nur mit --generate-protocol erzeugt

**Requirement**: NFR-008 §6.3 — MUSS: Ohne `--generate-protocol` werden keine Protokolle erzeugt
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- `test-reports/`-Verzeichnis ist leer oder nicht vorhanden
- E2E-Tests sind konfiguriert

**Testschritte**:
1. QA-Engineer fuehrt aus: `pytest tests/e2e/ -v --browser=chrome` (ohne `--generate-protocol`)
2. QA-Engineer prueft, ob im `test-reports/`-Verzeichnis neue Dateien entstanden sind

**Erwartete Ergebnisse**:
- Im `test-reports/`-Verzeichnis wurden **keine** neuen Unterordner oder `protokoll.md`-Dateien erstellt
- E2E-Tests laufen normal durch (kein Fehler durch fehlendes Protokoll)
- Terminal-Ausgabe zeigt **keine** Meldung "Testprotokoll generiert: ..."

**Postconditions**:
- `test-reports/`-Verzeichnis bleibt unveraendert

**Tags**: [nfr-008, testprotokoll, generate-protocol, optional]

---

### TC-NFR008-026: Testprotokoll enthaelt korrekte Metadaten (Datum, Commit, Branch)

**Requirement**: NFR-008 §4.3 — MUSS: Metadaten-Tabelle mit Datum, Commit, Branch, OS, Browser, Python, Node.js
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- Git-Repository mit aktuellem Commit vorhanden
- E2E-Tests sind konfiguriert
- `protocol_plugin.py` sammelt `git rev-parse --short HEAD` und `git branch --show-current`

**Testschritte**:
1. QA-Engineer fuehrt aus: `pytest tests/e2e/ -v --browser=chrome --generate-protocol`
2. QA-Engineer oeffnet die erzeugte `test-reports/{timestamp}/protokoll.md`
3. QA-Engineer prueft den Abschnitt `## Metadaten`

**Erwartete Ergebnisse**:
- Feld **Datum** ist mit aktuellem Datum und Uhrzeit im Format `YYYY-MM-DD HH:MM:SS` befuellt
- Feld **Commit** enthaelt einen kurzen Git-Hash (7-10 Zeichen im Format `` `a1b2c3d` ``)
- Feld **Branch** enthaelt den aktuellen Branch-Namen (z. B. `feature/user-notifications`)
- Kein Feld zeigt `None`, leer oder `unknown`

**Postconditions**:
- `protokoll.md` liegt im Zeitstempel-Ordner

**Tags**: [nfr-008, testprotokoll, metadaten, commit-hash, branch]

---

### TC-NFR008-027: Testprotokoll enthaelt Zusammenfassungstabelle mit Testergebnissen

**Requirement**: NFR-008 §4.3 — Zusammenfassung: Gesamt, Bestanden, Fehlgeschlagen, Uebersprungen
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- E2E-Tests mit mindestens einem bestandenen und einem uebersprungenen Test vorhanden
- `--generate-protocol` ist aktiv

**Testschritte**:
1. QA-Engineer fuehrt aus: `pytest tests/e2e/ -v --browser=chrome --generate-protocol`
2. QA-Engineer oeffnet die erzeugte `protokoll.md` und prueft Abschnitt `## Zusammenfassung`

**Erwartete Ergebnisse**:
- Eine Tabelle mit Spalten `Gesamt | Bestanden | Fehlgeschlagen | Uebersprungen` existiert
- Die Summe `Bestanden + Fehlgeschlagen + Uebersprungen` ist gleich `Gesamt`
- Die Zahlen stimmen mit der pytest-Terminalausgabe ueberein (z. B. `5 passed, 1 skipped`)

**Postconditions**:
- `protokoll.md` liegt im Zeitstempel-Ordner

**Tags**: [nfr-008, testprotokoll, zusammenfassung, ergebnisse]

---

### TC-NFR008-028: Fehlgeschlagene Tests erscheinen im Protokoll mit nodeid und Fehlerdetails

**Requirement**: NFR-008 §4.3 — Fehlgeschlagene Tests: Stufe, Datei, Fehler, Ursache, Prioritaet
**Priority**: High
**Category**: Fehlermeldung
**Preconditions**:
- Mindestens ein E2E-Test schlaegt fehl
- `--generate-protocol` ist aktiv

**Testschritte**:
1. QA-Engineer modifiziert einen E2E-Test so, dass er sicher fehlschlaegt
2. QA-Engineer fuehrt aus: `pytest tests/e2e/ -v --browser=chrome --generate-protocol`
3. QA-Engineer oeffnet `protokoll.md` und prueft Abschnitt `## Fehlgeschlagene Tests`

**Erwartete Ergebnisse**:
- Abschnitt `## Fehlgeschlagene Tests` existiert und enthaelt den fehlgeschlagenen Test
- Jeder fehlgeschlagene Test ist mit seinem `nodeid` (Datei + Klassenname + Testname) aufgefuehrt
- Der Fehler-Beschreibungstext (`longrepr`) ist im Codeblock dargestellt
- Der Abschnitt fehlt **komplett**, wenn alle Tests bestanden haben

**Postconditions**:
- Test-Modifikation rueckgaengig machen; `protokoll.md` bleibt vorhanden

**Tags**: [nfr-008, testprotokoll, fehlgeschlagene-tests, longrepr, nodeid]

---

### TC-NFR008-029: Screenshots werden im Protokoll als Tabelle mit Links referenziert

**Requirement**: NFR-008 §4.3 — Screenshots-Abschnitt mit Tabelle: Nr., Dateiname, Markdown-Bildlink
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- E2E-Tests erstellen mindestens einen Screenshot
- `--generate-protocol` ist aktiv

**Testschritte**:
1. QA-Engineer fuehrt aus: `pytest tests/e2e/ -v --browser=chrome --generate-protocol`
2. QA-Engineer oeffnet `protokoll.md` und prueft Abschnitt `## Screenshots`

**Erwartete Ergebnisse**:
- Abschnitt `## Screenshots` existiert und enthaelt eine Tabelle
- Jede Zeile enthaelt: laufende Nummer, Dateiname, Markdown-Bildlink `![name](screenshots/name.png)`
- Alle Bildlinks referenzieren Dateien, die tatsaechlich im `screenshots/`-Unterordner existieren
- Die Sortierung ist aufsteigend nach Dateiname

**Postconditions**:
- `protokoll.md` und alle referenzierten PNG-Dateien sind vorhanden

**Tags**: [nfr-008, testprotokoll, screenshots, markdown, bild-links]

---

### TC-NFR008-030: Testprotokoll-Ordner hat Zeitstempel-Format YYYY-MM-DD_HH-MM-SS

**Requirement**: NFR-008 §4.2 — MUSS: Jeder Testlauf erzeugt Unterordner mit Zeitstempel
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- `test-reports/`-Verzeichnis existiert (oder wird angelegt)
- `--generate-protocol` ist aktiv

**Testschritte**:
1. QA-Engineer fuehrt aus: `pytest tests/e2e/ -v --generate-protocol`
2. QA-Engineer fuehrt aus: `ls test-reports/` und prueft die Unterordner-Namen

**Erwartete Ergebnisse**:
- Mindestens ein Unterordner im Format `YYYY-MM-DD_HH-MM-SS` (z. B. `2026-03-21_14-30-00`) existiert
- Der Ordner-Name entspricht dem Ausfuehrungs-Zeitpunkt des Testlaufs (Datum stimmt ueberein)
- Mehrere Testlaeufe erzeugen separate Unterordner mit unterschiedlichen Zeitstempeln

**Postconditions**:
- Zeitstempel-Ordner sind auf dem Dateisystem vorhanden

**Tags**: [nfr-008, testprotokoll, ablageort, zeitstempel, dateisystem]

---

### TC-NFR008-031: test-reports-Verzeichnis ist in .gitignore eingetragen

**Requirement**: NFR-008 §4.2 — MUSS: `test-reports/` in `.gitignore` eingetragen — Protokolle werden nicht eingecheckt
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- Git-Repository ist vorhanden
- `.gitignore`-Datei im Projekt-Root existiert

**Testschritte**:
1. QA-Engineer fuehrt aus: `grep test-reports .gitignore`
2. QA-Engineer erstellt eine Testdatei in `test-reports/` und fuehrt `git status` aus

**Erwartete Ergebnisse**:
- `.gitignore` enthaelt den Eintrag `test-reports/` oder `test-reports`
- `git status` zeigt die Dateien im `test-reports/`-Verzeichnis **nicht** als untracked an
- `git add .` fuegt keine Protokoll-Dateien zur Staging-Area hinzu

**Postconditions**:
- Testdatei in `test-reports/` wird wieder geloescht

**Tags**: [nfr-008, testprotokoll, gitignore, versionskontrolle]

---

### TC-NFR008-032: Protokoll-Generierung aktiviert sich ausschliesslich via --generate-protocol

**Requirement**: NFR-008 §6.3 — MUSS: Protokoll-Generierung als optionaler Parameter
**Priority**: Medium
**Category**: Happy Path
**Preconditions**:
- `protocol_plugin.py` ist in `tests/e2e/` vorhanden
- `pytest_configure` prueft `config.getoption("--generate-protocol", default=False)`

**Testschritte**:
1. QA-Engineer fuehrt den E2E-Testlauf zweimal aus: einmal ohne, einmal mit `--generate-protocol`
2. QA-Engineer prueft nach dem ersten Lauf (ohne Flag), ob Protokoll-Dateien erstellt wurden

**Erwartete Ergebnisse**:
- Ohne `--generate-protocol`: Kein Protokoll erstellt, kein `ProtocolGenerator` instanziiert
- Mit `--generate-protocol`: Protokoll wird erstellt und Pfad im Terminal ausgegeben
- Die Terminal-Meldung lautet: `Testprotokoll generiert: test-reports/{timestamp}/protokoll.md`

**Postconditions**:
- Protokoll-Verzeichnis nur beim zweiten Lauf angelegt

**Tags**: [nfr-008, testprotokoll, cli, optional-parameter]

---

## 8. E2E-Kernfunktionen — Abdeckung der Pflichtszenarien

*Abdeckung: NFR-008 §3.3, §7 (DoD: Kernfunktionen abgedeckt)*

---

### TC-NFR008-033: E2E-Test — Dashboard laedt und zeigt Pflanzenzahl

**Requirement**: NFR-008 §3.3 — MUSS: Dashboard (REQ-009): Uebersicht laedt, Kennzahlen werden angezeigt
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- Frontend-Anwendung laeuft auf `http://localhost:5173`
- Demo-Nutzer ist eingeloggt (oder Light-Modus ist aktiv)
- Dashboard-Seite existiert und zeigt `[data-testid='plant-count']`

**Testschritte**:
1. QA-Engineer fuehrt aus: `pytest tests/e2e/test_plant_lifecycle.py::TestPlantLifecycleE2E::test_dashboard_shows_plant_count -v`
2. QA-Engineer beobachtet den Browser-Zustand via Screenshot

**Erwartete Ergebnisse**:
- Test besteht: Die Pflanzenzahl (`plant-count`) ist sichtbar und enthaelt einen Integer >= 0
- Kein `TimeoutException` beim Warten auf das Element
- Screenshot `001_dashboard-overview.png` (falls `--generate-protocol` aktiv) zeigt die geladene Seite

**Postconditions**:
- Browser ist auf der Dashboard-Seite; keine Daten veraendert

**Tags**: [nfr-008, e2e, dashboard, pflanzenzahl, req-009]

---

### TC-NFR008-034: E2E-Test — Pflanzendetail zeigt aktuelle Phase

**Requirement**: NFR-008 §3.3 — MUSS: Pflanzenverwaltung (REQ-001): Pflanze anlegen, bearbeiten, Detailansicht
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- Testpflanze `test-plant-1` existiert in Phase `Vegetativ`
- Frontend-Anwendung laeuft
- `PlantDetailPage` ist konfiguriert mit Locator `[data-testid='current-phase']`

**Testschritte**:
1. QA-Engineer fuehrt den E2E-Test fuer Pflanzendetail aus
2. Der Test navigiert zu `/plants/test-plant-1` via `PlantDetailPage.open("test-plant-1")`
3. Der Test liest die aktuelle Phase via `get_current_phase()`

**Erwartete Ergebnisse**:
- Die Seite laedt ohne Fehler
- `current-phase`-Element ist sichtbar und zeigt den Text `"Vegetativ"`
- Screenshot der Detailseite vor der Transition ist aufgenommen (falls `--generate-protocol`)

**Postconditions**:
- Keine Phasenaenderung durchgefuehrt; Pflanze bleibt in `Vegetativ`

**Tags**: [nfr-008, e2e, pflanzendetail, phase, req-001, req-003]

---

### TC-NFR008-035: E2E-Test — Phasenuebergang von Vegetativ nach Bluete durchfuehren

**Requirement**: NFR-008 §3.3 — MUSS: Phasenuebergang (REQ-003): Transition ausloesen, Bestaetigungsdialog, Phase-Anzeige aktualisiert
**Priority**: Critical
**Category**: Zustandswechsel
**Preconditions**:
- Testpflanze `test-plant-1` ist in Phase `Vegetativ`
- Frontend-Anwendung laeuft
- `[data-testid='transition-button']` und `[data-testid='confirm-button']` sind im DOM vorhanden

**Testschritte**:
1. QA-Engineer fuehrt den E2E-Test `test_phase_transition_via_ui` aus
2. Der Test oeffnet Pflanzendetail und klickt Transition-Button via `initiate_phase_transition()`
3. Der Bestaetigungsdialog erscheint (Screenshot `003`)
4. Der Test klickt Bestaetigen via `confirm_transition()`
5. Der Test liest die neue Phase via `get_current_phase()`

**Erwartete Ergebnisse**:
- Bestaetigungsdialog erscheint nach `initiate_phase_transition()` (kein Timeout)
- Nach `confirm_transition()` zeigt `get_current_phase()` den Wert `"Bluete"`
- Alle vier definierten Screenshots sind vorhanden (Page-Load, Before, Dialog, After)
- Test besteht ohne Exception

**Postconditions**:
- Testpflanze ist in Phase `Bluete` (Teardown stellt Ausgangszustand wieder her oder nutzt eigene Test-Pflanze)

**Tags**: [nfr-008, e2e, phasenuebergang, confirm-dialog, req-003, screenshot]

---

### TC-NFR008-036: E2E-Test — Standortverwaltung: Standort anlegen und Kapazitaetsanzeige pruefen

**Requirement**: NFR-008 §3.3 — MUSS: Standortverwaltung (REQ-002): Standort anlegen, Slots konfigurieren, Kapazitaetsanzeige
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- Frontend-Anwendung laeuft
- Standort-Seite existiert
- Testdaten-Fixtures erzeugen einen Teststandort via `LocationFactory`

**Testschritte**:
1. QA-Engineer fuehrt den E2E-Test fuer Standortverwaltung aus
2. Der Test navigiert zur Standort-Liste und klickt "Erstellen"
3. Der Test befuellt das Formular mit Name `Teststandort-E2E` und Slot-Anzahl `5`
4. Der Test klickt "Speichern"
5. Der Test navigiert zur Detailansicht des neuen Standorts

**Erwartete Ergebnisse**:
- Standort erscheint nach dem Speichern in der Liste
- Detailansicht zeigt Kapazitaet 5 Slots
- Kein Fehler-Snackbar erscheint

**Postconditions**:
- Teststandort wird in Teardown geloescht (oder Factory-Isolation greift)

**Tags**: [nfr-008, e2e, standort, slot-kapazitaet, req-002]

---

### TC-NFR008-037: E2E-Test — Fehleranzeige: Validierungsfehler benutzerfreundlich dargestellt

**Requirement**: NFR-008 §3.3 — MUSS: Fehleranzeige (NFR-006): Validierungsfehler werden benutzerfreundlich dargestellt
**Priority**: Critical
**Category**: Fehlermeldung
**Preconditions**:
- Frontend-Anwendung laeuft
- Formular mit Validierungspflichtfeldern ist erreichbar (z. B. Pflanzenerstellungs-Dialog)

**Testschritte**:
1. QA-Engineer fuehrt E2E-Test fuer Fehleranzeige aus
2. Der Test navigiert zur entsprechenden Seite und versucht, ein leeres Pflichtformular abzusenden
3. Der Test prueft, ob eine Fehlermeldung angezeigt wird

**Erwartete Ergebnisse**:
- Fehlermeldung erscheint im UI (Snackbar oder Inline-Fehler) — kein roher Stack-Trace sichtbar
- Die Fehlermeldung ist auf Deutsch und benutzerfreundlich formuliert
- Kein technischer Fehlercode (ArangoDB-Fehlermeldung, Python-Traceback) ist im sichtbaren Bereich

**Postconditions**:
- Kein Datensatz wurde erstellt

**Tags**: [nfr-008, e2e, fehleranzeige, validierungsfehler, nfr-006]

---

## 9. Testdaten-Strategie — Factories und Fixtures

*Abdeckung: NFR-008 §5.1, §5.2, §7 (DoD: Testdaten)*

---

### TC-NFR008-038: BotanicalFamilyFactory.build() erzeugt gueltiges Objekt

**Requirement**: NFR-008 §5.2 — SOLL: Testdaten ueber Factory-Pattern (factory_boy oder manuelle Factories)
**Priority**: Medium
**Category**: Happy Path
**Preconditions**:
- `tests/factories.py` mit `BotanicalFamilyFactory`-Klasse existiert
- `BotanicalFamily`-Modell ist importierbar

**Testschritte**:
1. QA-Engineer fuehrt aus: `python -c "from tests.factories import BotanicalFamilyFactory; f = BotanicalFamilyFactory.build(); print(f.scientific_name)"`

**Erwartete Ergebnisse**:
- Ein `BotanicalFamily`-Objekt wird ohne Exception erstellt
- `scientific_name` ist ein nicht-leerer String (z. B. `"Testaceae-1"`)
- Zwei aufeinanderfolgende `build()`-Aufrufe erzeugen unterschiedliche `scientific_name`-Werte (Counter-Mechanismus)

**Postconditions**:
- Kein Datenbankeintrag erstellt (Factory.build() ist DB-frei)

**Tags**: [nfr-008, testdaten, factory, botanical-family, fixture]

---

### TC-NFR008-039: PlantFactory.build() erzeugt Pflanze mit Standard-Phase "seedling"

**Requirement**: NFR-008 §5.2 — Factory fuer Plant-Testdaten
**Priority**: Medium
**Category**: Happy Path
**Preconditions**:
- `tests/factories.py` mit `PlantFactory`-Klasse existiert

**Testschritte**:
1. QA-Engineer fuehrt aus: `python -c "from tests.factories import PlantFactory; p = PlantFactory.build(); print(p.current_phase)"`

**Erwartete Ergebnisse**:
- Ergebnis ist `"seedling"` (Standard-Phase laut Spec)
- Kein `ValidationError` oder `TypeError` beim Erzeugen
- `PlantFactory.build(current_phase="vegetative")` ueberschreibt den Default korrekt

**Postconditions**:
- Kein Datenbankeintrag erstellt

**Tags**: [nfr-008, testdaten, factory, plant, seedling]

---

### TC-NFR008-040: sample_plant-Fixture stellt Testpflanze mit sample_family-Abhaengigkeit bereit

**Requirement**: NFR-008 §5.1 — MUSS: Fixtures erzeugen keine Seiteneffekte ausserhalb ihres Scopes
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- `tests/conftest.py` enthaelt `sample_family`- und `sample_plant`-Fixtures

**Testschritte**:
1. QA-Engineer fuehrt einen Unittest aus, der `sample_plant` als Fixture-Parameter nutzt
2. QA-Engineer beobachtet, ob `sample_plant.family.scientific_name == "Solanaceae"`

**Erwartete Ergebnisse**:
- `sample_plant.family.scientific_name` ist `"Solanaceae"` (aus `sample_family`)
- `sample_plant.name` ist `"Tomate Roma"` und `current_phase` ist `"vegetative"`
- Die Fixture erzeugt keine Datenbankeintraege (nur In-Memory-Objekte via Factory.build())

**Postconditions**:
- Keine persistenten Seiteneffekte; Fixtures werden nach Testende verworfen

**Tags**: [nfr-008, fixture, sample-plant, solanaceae, scope]

---

## 10. Lokale Testausfuehrung und Dokumentation

*Abdeckung: NFR-008 §6.1, §6.2, §6.3*

---

### TC-NFR008-041: Alle E2E-Befehle sind in der Dokumentation aufgelistet

**Requirement**: NFR-008 §6.2 — Befehle pro Teststufe aufgelistet
**Priority**: Medium
**Category**: Happy Path
**Preconditions**:
- README oder Setup-Dokumentation fuer das Backend-Testverzeichnis existiert

**Testschritte**:
1. QA-Engineer oeffnet die Testdokumentation (README im `tests/`-Verzeichnis oder projektweites README)
2. QA-Engineer sucht nach den E2E-Befehlen laut NFR-008 §6.2

**Erwartete Ergebnisse**:
- Folgende Befehle sind dokumentiert:
  - `pytest tests/unit/ -v --cov=app --cov-report=term-missing`
  - `npx vitest run --coverage`
  - `pytest tests/integration/ -v --timeout=60`
  - `pytest tests/api/ -v`
  - `pytest tests/e2e/ -v --browser=chrome`
  - `pytest tests/e2e/ -v --browser=chrome --generate-protocol`
- Die Dokumentation benennt Docker als Voraussetzung fuer Integrationstests
- Chrome / Chromium + ChromeDriver sind als Voraussetzung fuer E2E-Tests aufgefuehrt

**Postconditions**:
- Kein Dokument veraendert

**Tags**: [nfr-008, dokumentation, testbefehle, voraussetzungen]

---

### TC-NFR008-042: Alle Tests ohne E2E laufen mit einem einzigen Befehl durch

**Requirement**: NFR-008 §6.2 — `pytest tests/unit/ tests/integration/ tests/api/ -v --cov=app`
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- Docker ist gestartet (fuer testcontainers in integration)
- Alle Backend-Abhaengigkeiten sind installiert

**Testschritte**:
1. QA-Engineer fuehrt aus: `pytest tests/unit/ tests/integration/ tests/api/ -v --cov=app`
2. QA-Engineer wartet auf den Abschluss

**Erwartete Ergebnisse**:
- Alle Unit-, Integrations- und API-Tests werden ausgefuehrt
- Exit-Code ist 0 (alle Tests bestehen)
- Die Coverage-Tabelle zeigt Backend-Coverage >= 80 %
- E2E-Tests werden in diesem Lauf **nicht** ausgefuehrt

**Postconditions**:
- Alle testcontainers-Container wurden gestoppt und entfernt

**Tags**: [nfr-008, lokale-ausfuehrung, testbefehl, alle-tests-ohne-e2e]

---

### TC-NFR008-043: protocol_plugin.py gibt Protokoll-Pfad am Ende im Terminal aus

**Requirement**: NFR-008 §4.4 — `pytest_sessionfinish` gibt Pfad des generierten Protokolls aus
**Priority**: Medium
**Category**: Happy Path
**Preconditions**:
- E2E-Testlauf mit `--generate-protocol`

**Testschritte**:
1. QA-Engineer fuehrt aus: `pytest tests/e2e/ -v --generate-protocol`
2. QA-Engineer liest die letzten Zeilen der Terminal-Ausgabe

**Erwartete Ergebnisse**:
- Die Terminal-Ausgabe endet mit einer Zeile: `Testprotokoll generiert: test-reports/YYYY-MM-DD_HH-MM-SS/protokoll.md`
- Der angegebene Pfad existiert auf dem Dateisystem und enthaelt eine gueltige Markdown-Datei
- Die Meldung erscheint **nach** der pytest-Zusammenfassung (als letzter Output)

**Postconditions**:
- Protokoll-Verzeichnis ist auf dem Dateisystem vorhanden

**Tags**: [nfr-008, protocol-plugin, terminal-ausgabe, pfad]

---

## 11. Risiko- und Negativszenarien

*Abdeckung: NFR-008 §8 — Risiken bei Nicht-Einhaltung*

---

### TC-NFR008-044: E2E-Test schlaegt fehl wenn data-testid umbenannt wird

**Requirement**: NFR-008 §8 — Risiko: E2E-Tests ohne Page-Object-Pattern sind fragil; Mitigation: Page-Object kapselt Locatoren
**Priority**: High
**Category**: Fehlermeldung
**Preconditions**:
- `PlantDetailPage` nutzt Locator `[data-testid='transition-button']`
- Der Frontend-Code wird so geaendert, dass der data-testid in `phase-transition-btn` umbenannt wird

**Testschritte**:
1. QA-Engineer benennt `data-testid='transition-button'` im Frontend-Code temporaer um
2. QA-Engineer fuehrt aus: `pytest tests/e2e/test_plant_lifecycle.py::TestPlantLifecycleE2E::test_phase_transition_via_ui -v --generate-protocol`

**Erwartete Ergebnisse**:
- Test schlaegt fehl mit `TimeoutException: Element [data-testid='transition-button'] not found`
- Ein Failure-Screenshot `FAILURE_test_phase_transition_via_ui.png` wird erstellt
- Das Testprotokoll enthaelt den Fehler im Abschnitt `## Fehlgeschlagene Tests` mit nodeid und longrepr
- Die Fehlermeldung zeigt klar, welcher Locator nicht gefunden wurde

**Postconditions**:
- data-testid wird auf den urspruenglichen Wert zurueckgesetzt

**Tags**: [nfr-008, page-object, locator, failure, regression, fragiler-test]

---

### TC-NFR008-045: Integrationstests schlagen fehl ohne Docker

**Requirement**: NFR-008 §8 — Risiko: testcontainers nicht verfuegbar → Mitigation: Docker als Voraussetzung dokumentieren
**Priority**: Medium
**Category**: Fehlermeldung
**Preconditions**:
- Docker ist **nicht** gestartet (Service gestoppt)
- Integrationstests benoetigen ArangoDB via testcontainers

**Testschritte**:
1. QA-Engineer stoppt den Docker-Service
2. QA-Engineer fuehrt aus: `pytest tests/integration/ -v --timeout=30`

**Erwartete Ergebnisse**:
- Tests schlagen fehl mit einer klaren Docker-bezogenen Fehlermeldung (z. B. `DockerException: Error while fetching server API version`)
- Die Fehlermeldung verweist auf den fehlenden Docker-Service
- Keine Testdaten werden in einer echten Datenbank erstellt

**Postconditions**:
- Docker-Service wieder starten

**Tags**: [nfr-008, integration-test, docker, testcontainers, fehlermeldung]

---

### TC-NFR008-046: Testlauf ohne isolierte Fixtures erzeugt nicht-deterministische Ergebnisse

**Requirement**: NFR-008 §8 — Risiko: Fehlende Testdaten-Isolation → Tests beeinflussen sich gegenseitig
**Priority**: High
**Category**: Fehlermeldung
**Preconditions**:
- Zwei Integrationstests existieren: Test A erstellt einen Datensatz, Test B erwartet leere Collection
- `clean_collections`-Fixture ist **deaktiviert** (fuer diesen Risikotest)

**Testschritte**:
1. QA-Engineer fuehrt Test B isoliert aus (besteht)
2. QA-Engineer fuehrt Test A gefolgt von Test B aus (in dieser Reihenfolge)
3. QA-Engineer vergleicht die Ergebnisse beider Szenarien

**Erwartete Ergebnisse**:
- Test B schlaegt beim zweiten Szenario (nach Test A) fehl, da die Collection nicht leer ist
- Dieser Unterschied dokumentiert das Risiko von fehlender Isolation
- Mit aktivierter `clean_collections`-Fixture besteht Test B in beiden Szenarien

**Postconditions**:
- `clean_collections`-Fixture wieder aktivieren; Testdaten bereinigen

**Tags**: [nfr-008, isolation, testdaten, nicht-deterministisch, risiko]

---

### TC-NFR008-047: E2E-Test scheitert wenn Frontend nicht erreichbar ist

**Requirement**: NFR-008 §6.1 — Voraussetzung: laufende Anwendung fuer E2E-Tests
**Priority**: High
**Category**: Fehlermeldung
**Preconditions**:
- Frontend-Anwendung ist **nicht** gestartet

**Testschritte**:
1. QA-Engineer stellt sicher, dass kein Frontend-Server auf Port 5173 laeuft
2. QA-Engineer fuehrt aus: `pytest tests/e2e/ -v --browser=chrome`

**Erwartete Ergebnisse**:
- Tests schlagen fehl mit einer Netzwerk-Fehlermeldung (z. B. `ERR_CONNECTION_REFUSED` oder Selenium-Exception)
- Der Fehler tritt beim ersten Navigations-Versuch auf, nicht erst beim Element-Wait
- Failure-Screenshots (falls `--generate-protocol`) zeigen eine Browser-Fehlerseitenansicht

**Postconditions**:
- Frontend-Server kann danach gestartet werden; keine Testdaten veraendert

**Tags**: [nfr-008, e2e, voraussetzung, frontend-nicht-erreichbar, fehlermeldung]

---

### TC-NFR008-048: Protocol-Plugin generiert kein Protokoll wenn Start-Zeitstempel fehlt

**Requirement**: NFR-008 §4.4 — `ProtocolGenerator.start_time` wird in `pytest_sessionstart` gesetzt
**Priority**: Low
**Category**: Fehlermeldung
**Preconditions**:
- `protocol_plugin.py` ist konfiguriert
- `pytest_sessionstart`-Hook ist implementiert

**Testschritte**:
1. QA-Engineer prueft den Code von `ProtocolGenerator.generate()` auf Robustheit gegen `start_time = None`
2. QA-Engineer fuehrt aus: `pytest tests/e2e/ --generate-protocol` und prueft, ob das Protokoll ein gueltiges Datum enthaelt

**Erwartete Ergebnisse**:
- `pytest_sessionstart` setzt `generator.start_time = datetime.now()` korrekt
- Das Protokoll enthaelt ein gueltiges Datum-Zeitformat, kein `None` oder `NaT`
- Bei ordnungsgemaessem Ablauf kein `AttributeError: 'NoneType' has no attribute 'strftime'`

**Postconditions**:
- Protokoll mit korrektem Zeitstempel ist auf dem Dateisystem vorhanden

**Tags**: [nfr-008, protocol-plugin, start-time, robustheit, fehlerfall]

---

## Abdeckungsmatrix

| NFR-008-Abschnitt | Inhalt | Testfaelle |
|---|---|---|
| §2.1 Testpyramide-Uebersicht | Vier Teststufen definiert | TC-NFR008-001 bis TC-NFR008-004 |
| §2.3 Unit-Tests | >=80 % Coverage, Determinismus, Mocks | TC-NFR008-001, 002, 003, 004 |
| §2.4 Integrationstests | testcontainers, kritische Pfade, Isolation | TC-NFR008-005, 006, 007, 008 |
| §2.5 API-/Contract-Tests | Happy-Path, Error-Path, Schema-Validierung | TC-NFR008-009, 010, 011, 012 |
| §3.1 Browser-Konfiguration | Chrome-Headless, Firefox, CLI-Optionen | TC-NFR008-013, 014, 015, 016 |
| §3.2 Page-Object-Pattern | BasePage, DashboardPage, PlantDetailPage, kein direkter Selenium-Aufruf | TC-NFR008-017, 018, 019, 020 |
| §3.3 Kernfunktionen | Dashboard, Pflanzenverwaltung, Phasenuebergang, Standort, Fehleranzeige | TC-NFR008-033, 034, 035, 036, 037 |
| §3.4 Screenshots | Page-Load, vor/nach Aktion, Fehlerzustand, automatisch bei Failure | TC-NFR008-021, 022, 023, 024 |
| §4.2 Ablageort | `test-reports/`, Zeitstempel-Unterordner, `.gitignore` | TC-NFR008-030, 031 |
| §4.3 Protokoll-Format | Metadaten, Zusammenfassung, Fehlgeschlagene Tests, Screenshots | TC-NFR008-026, 027, 028, 029 |
| §4.4 Protokoll-Generierung | `--generate-protocol`, `pytest_sessionfinish`, Terminal-Ausgabe | TC-NFR008-025, 032, 043, 048 |
| §5.1 Fixtures | sample_plant, sample_family, keine Seiteneffekte | TC-NFR008-040 |
| §5.2 Factory-Pattern | BotanicalFamilyFactory, PlantFactory, LocationFactory | TC-NFR008-038, 039 |
| §5.3 Isolation | clean_collections, kein Test-Zustand-Uebertrag | TC-NFR008-008, 046 |
| §6.1 Voraussetzungen | Docker, Chrome, ChromeDriver | TC-NFR008-041, 047 |
| §6.2 Lokale Befehle | Alle Stufen-Befehle dokumentiert, Gesamt-Befehl | TC-NFR008-041, 042 |
| §6.3 Protokoll-Generierung | Optional, Pfad-Ausgabe | TC-NFR008-043 |
| §7 DoD-Kriterien | Alle Definition-of-Done-Punkte | Verteilt ueber alle Gruppen |
| §8 Risiken | Page-Object-Fragilier-Test, Docker-fehlt, Isolation-fehlt, Frontend-nicht-erreichbar, Plugin-Robustheit | TC-NFR008-044, 045, 046, 047, 048 |
