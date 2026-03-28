---
name: check-test-pyramid
description: "Prueft die Testvollstaendigkeit eines Features oder Moduls auf NFR-008-Konformitaet: Alle 4 Testebenen vorhanden (Unit, Integration, API/Contract, E2E), Coverage-Ziele, Page-Object-Pattern bei Selenium, Screenshot-Checkpoints. Nutze diesen Skill nach Feature-Implementierung oder vor einem Release."
argument-hint: "[REQ-nnn oder Modul-Name, z.B. REQ-013 oder planting_run]"
disable-model-invocation: true
---

# Testpyramiden-Check (NFR-008): $ARGUMENTS

## Schritt 1: Test-Dateien finden

Suche alle relevanten Test-Dateien **parallel**:

1. **Backend Unit-Tests:** Glob `src/backend/tests/test_*.py` — filtere nach `$ARGUMENTS`
2. **Backend Integration-Tests:** Glob `src/backend/tests/integration/test_*.py`
3. **E2E-Tests:** Glob `tests/e2e/test_req*.py` oder `tests/e2e/test_*$ARGUMENTS*.py`
4. **E2E-Page-Objects:** Glob `tests/e2e/pages/*.py`
5. **Frontend-Tests:** Glob `src/frontend/src/**/*.test.tsx` oder `*.spec.tsx`

Lies ausserdem `spec/nfr/NFR-008_Teststrategie-Testprotokoll.md` erste 80 Zeilen.

## Schritt 2: Testpyramiden-Vollstaendigkeit

**Pflicht-Ebenen aus NFR-008 §2.1:**

```
          ┌───────────────┐
          │  E2E-Tests    │   ← Kernfunktionen (Selenium, pytest-selenium)
          ├───────────────┤
          │  API-Tests    │   ← Alle Endpunkte mit TestClient (httpx)
          ├───────────────┤
          │ Integrations- │   ← Kritische Pfade (testcontainers)
          │ tests         │
          ├───────────────┤
          │  Unit-Tests   │   ← Engines, Calculators (≥80% Coverage)
          └───────────────┘
```

Prüfe fuer `$ARGUMENTS` ob alle 4 Ebenen vorhanden sind.

## Schritt 3: Unit-Test-Coverage pruefen

**Prüfe ob folgende Klassen Unit-Tests haben:**

- Alle Engine-Klassen (`*Engine`, `*Calculator`, `*Validator`)
- Alle Service-Klassen (`*Service`) — Mock-basiert
- Frontend-Komponenten (vitest) fuer Dialog/Page-Komponenten

**Coverage-Ziel: ≥80% (NFR-003)**

Fuehre aus:
```bash
cd src/backend && python -m pytest tests/ --tb=no -q --co 2>&1 | grep -c "test session"
```

## Schritt 4: E2E-Test-Qualitaet pruefen (NFR-008 §4)

Falls E2E-Tests vorhanden, prüfe:

**Page-Object-Pattern:**
```python
# ✅ KORREKT — Page-Object kapselt Selektoren
class PlantingRunPage:
    def __init__(self, driver):
        self.driver = driver

    def click_create_button(self):
        self.driver.find_element(By.TEST_ID, "btn-create-run").click()

# ❌ FALSCH — Selektoren direkt im Test
driver.find_element(By.XPATH, "//button[text()='Neuen Durchlauf']").click()
```

**Screenshot-Checkpoints:**
```python
# MUSS an kritischen Stellen vorhanden sein:
driver.save_screenshot(f"screenshots/{test_name}_step_{n}.png")
```

**Testprotokoll-Generierung:**
- Wird `pytest-html` verwendet? (`--html=reports/...`)
- Enthaelt der Report: Datum, Commit-Hash, Screenshots?

## Schritt 5: API-Contract-Tests pruefen

Prüfe ob API-Tests:
- Alle Endpunkte des Moduls abdecken (nicht nur Happy-Path)
- Response-Schema gegen Pydantic-Model validieren
- 4xx/5xx-Fehlerszenarien testen
- Auth-geschuetzte Endpoints ohne Token testen (sollte 401 zurueckgeben)

## Schritt 6: Report ausgeben

```markdown
# Testpyramiden-Review: {Feature/Modul}

## Testebenen-Uebersicht
| Ebene | Vorhanden | Anzahl Tests | Bewertung |
|-------|-----------|-------------|-----------|
| Unit-Tests | ✅/❌ | N | ... |
| Integrationstests | ✅/❌ | N | ... |
| API-Contract-Tests | ✅/❌ | N | ... |
| E2E-Tests (Selenium) | ✅/❌ | N | ... |

## Unit-Test-Details
{Engine-Klassen mit Tests: N/M | Calculator-Klassen: N/M}

## E2E-Test-Qualitaet
{Page-Object-Pattern: ✅/❌ | Screenshots: ✅/❌ | Testprotokoll: ✅/❌}

## API-Contract-Coverage
{Endpunkte mit Tests: N/M | 4xx-Szenarien: ✅/❌ | Auth-Tests: ✅/❌}

## Luecken (priorisiert)
{Nummerierte Liste der fehlenden Test-Cases}

## Bewertung
- ✅ NFR-008-konform / ❌ {N} Luecken identifiziert
```
