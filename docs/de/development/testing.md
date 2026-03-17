# Testen

Kamerplanter verfügt über eine umfangreiche Testsuite für Backend und Frontend. Alle Tests müssen grün sein, bevor ein Pull Request gemergt wird.

**Aktueller Stand:** 821 Backend-Tests (pytest), 198 Frontend-Tests (vitest) — alle grün.

---

## Backend-Tests (pytest)

### Voraussetzungen

```bash
cd src/backend
pip install -e ".[dev]"
```

Das installiert alle Produktions- und Entwicklungsabhängigkeiten, einschließlich pytest, pytest-asyncio und pytest-cov.

### Tests ausführen

```bash
# Alle Tests
pytest

# Mit ausführlicher Ausgabe
pytest -v

# Einzelne Testdatei
pytest tests/test_onboarding_engine.py -v

# Einzelnen Test
pytest tests/test_onboarding_engine.py::TestValidateKitApplication::test_valid_application -v

# Tests nach Namenspattern filtern
pytest -k "substrate" -v
```

### Teststruktur

```
src/backend/tests/
├── conftest.py                        # Gemeinsame Fixtures (Species, Site, Substrate, ...)
├── unit/                              # Einheitentests ohne externe Abhängigkeiten
│   ├── domain/
│   │   └── test_calculations.py      # VPD, GDD, EC-Berechnungen
│   └── adapters/
│       └── test_enrichment.py        # GBIF/Perenual Adapter-Logik
├── api/                               # API-Schicht-Tests
│   └── test_error_handling.py
├── integration/                       # Integrationstests (erfordern ArangoDB)
│   └── test_arango_integration.py
├── test_care_reminder_engine.py       # Engine-Tests (direkte Klassen-Instantiierung)
├── test_onboarding_engine.py
├── test_substrate_lifecycle_manager.py
└── test_*.py                          # Weitere Engine-/Service-Tests
```

### pytest-asyncio Konfiguration

pytest-asyncio ist mit `asyncio_mode = "auto"` konfiguriert. Asynchrone Testfunktionen benötigen kein explizites `@pytest.mark.asyncio`-Dekorator:

```python
# Funktioniert ohne explizites Dekorator
async def test_service_creates_species():
    service = SpeciesService(mock_repo)
    result = await service.create(sample_data)
    assert result.scientific_name == "Solanum lycopersicum"
```

### Fixtures (conftest.py)

Die zentrale `conftest.py` stellt typische Datensätze als Fixtures bereit:

```python
def test_substrate_lifecycle(sample_substrate_data):
    substrate = Substrate(**sample_substrate_data)
    manager = SubstrateLifecycleManager()
    result = manager.prepare_for_reuse(substrate)
    assert result.reuse_cycle == 1
```

Verfügbare Fixtures: `sample_species_data`, `sample_site_data`, `sample_location_data`, `sample_substrate_data`.

### Integrationstests

Integrationstests unter `tests/integration/` erfordern eine laufende ArangoDB-Instanz. Sie werden automatisch übersprungen, wenn keine Verbindung besteht:

```python
@pytest.mark.skipif(not ARANGO_AVAILABLE, reason="ArangoDB not available")
class TestArangoSetup:
    ...
```

Um sie gezielt auszuführen:

```bash
# ArangoDB starten (z. B. via Docker Compose)
docker-compose up -d arangodb

# Nur Integrationstests
pytest tests/integration/ -v
```

### Code Coverage

```bash
pytest --cov=app --cov-report=term-missing --cov-report=html
```

Der HTML-Report wird in `htmlcov/` gespeichert und kann im Browser geöffnet werden.

### Neue Tests schreiben

**Engine-Tests** — direkte Klassen-Instantiierung, keine Mocks für Repositories nötig:

```python
class TestNutrientSolutionCalculator:
    calc = NutrientSolutionCalculator()

    def test_ec_net_calculation(self):
        result = self.calc.calculate_ec_net(
            base_water_ec=0.3,
            target_ec=1.8,
        )
        assert result == pytest.approx(1.5, abs=0.01)

    def test_mixing_order_calmag_first(self):
        plan = NutrientPlan(...)
        errors = self.calc.validate_mixing_order(plan)
        assert errors == []
```

**Service-Tests** — Repositories werden gemockt:

```python
class TestSpeciesService:
    async def test_create_species(self):
        mock_repo = AsyncMock(spec=SpeciesRepository)
        mock_repo.create.return_value = Species(key="sp-1", ...)
        service = SpeciesService(mock_repo)
        result = await service.create(CreateSpeciesRequest(...))
        mock_repo.create.assert_called_once()
        assert result.key == "sp-1"
```

---

## Frontend-Tests (vitest)

### Voraussetzungen

```bash
cd src/frontend
npm install
```

Node.js 25.1.0 ist erforderlich (via asdf, `.tool-versions` im Frontend-Verzeichnis).

### Tests ausführen

```bash
# Alle Tests (einmaliger Durchlauf)
npm test

# Watch-Modus (Tests bei Dateiänderungen neu ausführen)
npm run test:watch

# Mit Coverage-Report
npm run test:coverage
```

### Teststruktur

```
src/frontend/src/test/
├── setup.ts                   # Globales Test-Setup (MSW, jest-dom, Cleanup)
├── helpers.tsx                # renderWithProviders, createTestStore
├── mocks/
│   ├── handlers.ts            # MSW Request-Handler (API-Mocks)
│   └── server.ts              # MSW Node-Server
├── components/                # Komponenten-Tests
│   ├── ConfirmDialog.test.tsx
│   ├── DataTable.test.tsx
│   ├── FormTextField.test.tsx
│   └── ...
├── hooks/                     # Hook-Tests (useApiError, useDebounce, ...)
├── pages/                     # Seiten-Komponenten-Tests
├── store/                     # Redux Slice-Tests
├── api/                       # API-Client-Tests
└── a11y/                      # Barrierefreiheits-Tests (vitest-axe)
```

### Test-Infrastruktur (setup.ts)

Das Setup initialisiert vor allen Tests den MSW-Server und setzt einen Tenant-Slug in `localStorage`. Nach jedem Test wird der DOM bereinigt und die MSW-Handler werden zurückgesetzt:

```typescript
beforeAll(() => server.listen({ onUnhandledRequest: 'warn' }));
beforeEach(() => {
  window.localStorage.setItem('kp_active_tenant_slug', 'test-tenant');
});
afterEach(() => {
  cleanup();
  server.resetHandlers();
});
afterAll(() => server.close());
```

### renderWithProviders (helpers.tsx)

Alle Komponenten-Tests verwenden `renderWithProviders` aus `src/test/helpers.tsx`. Diese Funktion wickelt die Komponente in alle erforderlichen Provider ein:

```typescript
import { renderWithProviders } from '@/test/helpers';
import { screen } from '@testing-library/react';
import { SpeciesDetailPage } from '@/pages/stammdaten/SpeciesDetailPage';

test('renders species name', () => {
  renderWithProviders(<SpeciesDetailPage />, { route: '/stammdaten/species/sp-1' });
  expect(screen.getByText('Solanum lycopersicum')).toBeInTheDocument();
});
```

**Enthaltene Provider:** Redux Store, React Router (`createMemoryRouter`), MUI Theme, `SnackbarProvider`.

!!! warning "userPreferences-Reducer erforderlich"
    Komponenten, die `useExpertiseLevel` verwenden, benötigen den `userPreferences`-Reducer im Test-Store. `createTestStore()` schließt ihn bereits ein. Beim manuellen Erstellen eines Test-Stores muss er explizit hinzugefügt werden:
    ```typescript
    configureStore({
      reducer: {
        userPreferences: userPreferencesReducer,
        // ... weitere Reducer
      }
    });
    ```

### API-Mocks mit MSW

API-Aufrufe werden durch [Mock Service Worker (MSW)](https://mswjs.io/) abgefangen. Handler sind in `src/test/mocks/handlers.ts` definiert:

```typescript
import { http, HttpResponse } from 'msw';

export const handlers = [
  http.get('/api/v1/botanical-families', () => {
    return HttpResponse.json(mockFamilies);
  }),

  http.post('/api/v1/t/:tenantSlug/species', async ({ request }) => {
    const body = await request.json();
    return HttpResponse.json({ key: 'sp-new', ...body }, { status: 201 });
  }),
];
```

Für testspezifisches Verhalten können Handler temporär überschrieben werden:

```typescript
test('shows error on API failure', () => {
  server.use(
    http.get('/api/v1/botanical-families', () => {
      return HttpResponse.error();
    })
  );
  renderWithProviders(<BotanicalFamilyList />);
  expect(screen.getByText(/Fehler beim Laden/)).toBeInTheDocument();
});
```

### Barrierefreiheits-Tests (vitest-axe)

Kritische Formulare und Dialogfelder haben automatische Accessibility-Tests:

```typescript
import { axe } from 'vitest-axe';

test('form has no accessibility violations', async () => {
  const { container } = renderWithProviders(<SpeciesCreateDialog open />);
  const results = await axe(container);
  expect(results).toHaveNoViolations();
});
```

### Neue Tests schreiben

**Konventionen für Komponenten-Tests:**

```typescript
import { describe, test, expect } from 'vitest';
import { screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithProviders } from '@/test/helpers';

describe('FormTextField', () => {
  test('displays validation error', async () => {
    const user = userEvent.setup();
    renderWithProviders(
      <FormTextField name="email" label="E-Mail" required />
    );
    await user.click(screen.getByLabelText('E-Mail'));
    await user.tab(); // Fokus verlassen, um Validierung auszulösen
    expect(screen.getByText(/Pflichtfeld/)).toBeInTheDocument();
  });
});
```

**Redux Slice-Tests — ohne React:**

```typescript
import { describe, test, expect } from 'vitest';
import onboardingReducer, { setStep } from '@/store/slices/onboardingSlice';

describe('onboardingSlice', () => {
  test('advances step', () => {
    const initial = { currentStep: 0, completed: false };
    const next = onboardingReducer(initial, setStep(1));
    expect(next.currentStep).toBe(1);
  });
});
```

---

## Gemeinsame Regeln für beide Test-Suites

- Tests laufen in CI bei jedem Push auf `main` und bei jedem Pull Request.
- Neue Features erfordern mindestens einen Unit-Test für die Business-Logik.
- Bug-Fixes erfordern einen Regressionstest, der den Bug reproduziert.
- Kein `.skip` oder `.only` in gemergten Tests ohne Kommentar und Issue-Referenz.

## Siehe auch

- [Code-Standards](code-standards.md)
- [Lokales Setup](local-setup.md)
- [Debugging](debugging.md)
