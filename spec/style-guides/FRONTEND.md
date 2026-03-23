# Frontend Style Guide — React / TypeScript / MUI

> Verbindlicher Style Guide fuer den Kamerplanter Frontend-Code.
> Wird durch **ESLint** (Linting), **TypeScript strict** (Typsicherheit), **Prettier** (Formatierung) und **Vitest** (Tests) automatisch geprueft.

**Scope:** `src/frontend/`

---

## 1. Statische Analyse & Tooling

| Tool | Zweck | Config |
|------|-------|--------|
| **ESLint** | Linting (JS/TS Regeln + React Hooks) | `eslint.config.js` |
| **TypeScript** | Statische Typanalyse (strict) | `tsconfig.json` |
| **Prettier** | Code-Formatierung | `.prettierrc` + `eslint-config-prettier` |
| **Vitest** | Unit-/Komponententests | `vitest.config.ts` |

### 1.1 ESLint-Konfiguration

```javascript
// eslint.config.js (Flat Config)
export default tseslint.config(
  { ignores: ['dist', 'public'] },
  js.configs.recommended,
  ...tseslint.configs.recommended,
  {
    files: ['**/*.{ts,tsx}'],
    plugins: { 'react-hooks': reactHooks },
    rules: {
      ...reactHooks.configs.recommended.rules,
      '@typescript-eslint/no-unused-vars': ['error', { argsIgnorePattern: '^_' }],
    },
  },
  prettier,  // Deaktiviert Formatierungsregeln (Prettier uebernimmt)
);
```

**Regeln:**
- `react-hooks/rules-of-hooks` — Hook-Aufrufe nur in Komponenten/Hooks
- `react-hooks/exhaustive-deps` — Vollstaendige Dependency-Arrays
- `@typescript-eslint/no-unused-vars` — Unbenutzte Variablen (ausser `_`-Praefix)

### 1.2 Prettier-Konfiguration

```json
{
  "singleQuote": true,
  "semi": true,
  "tabWidth": 2,
  "trailingComma": "all",
  "printWidth": 100
}
```

### 1.3 TypeScript strict-Modus

```json
{
  "compilerOptions": {
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "forceConsistentCasingInFileNames": true
  }
}
```

### 1.4 CI-Pruefung

```bash
npx eslint src/            # Linting
npx tsc --noEmit           # Typpruefung
npx vitest run             # Tests
```

---

## 2. Projektstruktur

```
src/frontend/src/
├── api/                             # API-Schicht
│   ├── client.ts                    # Axios-Client + Tenant-Interceptor
│   ├── endpoints/                   # API-Funktionen pro Feature
│   │   ├── species.ts
│   │   ├── sites.ts
│   │   └── ...                      # 24 Endpoint-Module
│   ├── errors.ts                    # ApiError-Klasse, parseApiError()
│   ├── types.ts                     # Alle TypeScript-Interfaces (API DTOs)
│   └── index.ts                     # Barrel Export
├── auth/                            # Authentifizierung
│   ├── AuthProvider.tsx             # JWT-Refresh + 401-Interceptor
│   ├── ProtectedRoute.tsx           # Auth-Guard (Light-Modus Bypass)
│   └── PublicOnlyRoute.tsx          # Guard fuer Login/Register
├── components/                      # Wiederverwendbare UI-Komponenten
│   ├── common/                      # ErrorDisplay, LoadingSkeleton, etc.
│   ├── form/                        # FormTextField, FormSelectField, etc.
│   ├── layout/                      # Breadcrumbs, Sidebar, TenantSwitcher
│   └── {feature}/                   # Feature-spezifische Komponenten
├── config/
│   └── mode.ts                      # isLightMode Check
├── hooks/                           # Custom Hooks (21 Stueck)
│   ├── useExpertiseLevel.ts
│   ├── useNotification.ts           # notistack-Wrapper
│   ├── useApiError.ts               # API-Fehlerbehandlung
│   └── ...
├── i18n/                            # Internationalisierung
│   ├── i18n.ts                      # i18next-Setup (DE Default)
│   └── locales/
│       ├── de/translation.json      # Deutsch (Default)
│       └── en/translation.json      # Englisch
├── layouts/
│   ├── MainLayout.tsx               # AppBar + Sidebar + <Outlet/>
│   └── Sidebar.tsx                  # Navigation (Expertise-Level Tiering)
├── pages/                           # Seitenkomponenten (je Route)
│   ├── DashboardPage.tsx
│   ├── auth/                        # Login, Register, AccountSettings
│   ├── stammdaten/                  # Species, Cultivar, Family (11 Seiten)
│   ├── standorte/                   # Site, Location, Substrate, Tank
│   ├── pflanzen/                    # PlantInstance, Calculations
│   ├── durchlaeufe/                 # PlantingRun
│   ├── duengung/                    # Fertilizer, NutrientPlan
│   ├── pflanzenschutz/              # IPM, Pest, Disease, Treatment
│   ├── ernte/                       # Harvest
│   ├── aufgaben/                    # Tasks
│   ├── kalender/                    # Calendar
│   ├── pflege/                      # Care Reminders
│   ├── tenants/                     # Tenant-Verwaltung
│   └── onboarding/                  # Wizard (5 Schritte)
├── routes/
│   ├── AppRoutes.tsx                # Router-Definition (Lazy Routes)
│   └── breadcrumbs.ts               # Breadcrumb-Pfad-Mappings
├── store/
│   ├── store.ts                     # configureStore() mit 22 Reducern
│   ├── hooks.ts                     # useAppDispatch, useAppSelector
│   └── slices/                      # 22 Redux Toolkit Slices
│       └── speciesSlice.ts
├── test/                            # Test-Utilities
│   ├── helpers.tsx                  # renderWithProviders
│   ├── setup.ts                     # vitest + MSW Setup
│   └── mocks/
│       ├── server.ts                # MSW setupServer
│       └── handlers.ts              # MSW Request-Handler
├── theme/
│   ├── theme.ts                     # createTheme (Light/Dark)
│   ├── palette.ts                   # lightPalette, darkPalette
│   ├── typography.ts                # Font-Stacks
│   ├── tokens.ts                    # Breakpoints, Spacing, Radii
│   └── ThemeContext.tsx             # Theme-Provider + useThemeMode
├── validation/
│   └── schemas.ts                   # Zod-Schemas (Formularvalidierung)
├── utils/                           # Hilfsfunktionen
├── App.tsx                          # Redux Provider + Theme + Router + i18n
└── main.tsx                         # Entry Point (React.StrictMode)
```

### 2.1 Path-Alias

```json
// tsconfig.json
{
  "compilerOptions": {
    "paths": { "@/*": ["src/*"] }
  }
}
```

**Alle Imports** verwenden den `@/` Alias statt relativer Pfade:

```typescript
// RICHTIG
import { useAppDispatch } from '@/store/hooks';
import type { Species } from '@/api/types';

// FALSCH
import { useAppDispatch } from '../../../store/hooks';
```

---

## 3. Namenskonventionen

### 3.1 Dateien

| Typ | Konvention | Beispiel |
|-----|-----------|----------|
| Seiten | `PascalCase` + `Page` Suffix | `SpeciesPage.tsx` |
| Komponenten | `PascalCase` | `PlantCard.tsx`, `CareProfileEditDialog.tsx` |
| Hooks | `camelCase` mit `use` Praefix | `useExpertiseLevel.ts` |
| Redux Slices | `camelCase` + `Slice` Suffix | `speciesSlice.ts` |
| API Endpoints | `camelCase` | `species.ts` (in `api/endpoints/`) |
| Typen | `camelCase` | `species.ts` |
| Utils | `camelCase` | `formatDate.ts` |
| Tests | `{dateiname}.test.tsx` | `PlantCard.test.tsx` |

### 3.2 Komponenten & Funktionen

| Element | Konvention | Beispiel |
|---------|-----------|----------|
| Komponenten | `PascalCase` | `SpeciesListPage`, `CareProfileEditDialog` |
| Hooks | `use` Praefix | `useExpertiseLevel`, `useAppDispatch` |
| Event-Handler | `handle` Praefix | `handleSubmit`, `handlePhaseChange` |
| Boolean Props | `is`/`has`/`show` Praefix | `isLoading`, `hasError`, `showDialog` |
| Callback Props | `on` Praefix | `onClose`, `onSave`, `onChange` |
| Constants | `UPPER_SNAKE_CASE` | `DEFAULT_PAGE_SIZE`, `API_BASE_URL` |

### 3.3 i18n-Keys

```
pages.<section>.<key>           # Seitentexte
enums.<enumName>.<value>        # Enum-Uebersetzungen
common.<key>                    # Globale Labels (save, cancel, delete)
validation.<key>                # Validierungsmeldungen
```

Beispiel: `pages.nutrientCalc.title`, `enums.phaseType.flowering`

---

## 4. Komponenten-Pattern

### 4.1 Funktionale Komponenten (ausschliesslich)

```tsx
// Named Export (bevorzugt fuer nicht-Seiten)
export function PlantCard({ plant, onSelect }: PlantCardProps) {
  const { t } = useTranslation();
  // ...
  return <Card>...</Card>;
}

// Default Export NUR fuer Seiten (React.lazy Kompatibilitaet)
export default function SpeciesPage() {
  // ...
}
```

**Regeln:**
- **Keine** Class Components
- **Named Exports** fuer Komponenten und Hooks
- **Default Exports** nur fuer Seiten-Komponenten (Lazy Loading)
- Keine `React.FC` — direkt `function` mit Props-Parameter

### 4.2 Props-Typisierung

```tsx
// Interface fuer Props (nicht type)
interface PlantCardProps {
  plant: PlantInstance;
  onSelect: (key: string) => void;
  isCompact?: boolean;
}

export function PlantCard({ plant, onSelect, isCompact = false }: PlantCardProps) {
  // Destructuring mit Defaults direkt im Parameter
}
```

- `interface` fuer Props (erweiterbar, bessere Fehlermeldungen)
- `type` fuer Unions, Utility Types, generische Typen
- Optionale Props mit `?` und Default im Destructuring

---

## 5. State Management (Redux Toolkit)

### 5.1 Slice-Struktur

```typescript
// features/species/speciesSlice.ts
import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';

interface SpeciesState {
  items: Species[];
  total: number;
  loading: boolean;
  error: string | null;
}

const initialState: SpeciesState = {
  items: [],
  total: 0,
  loading: false,
  error: null,
};

export const fetchSpecies = createAsyncThunk(
  'species/fetchAll',
  async ({ offset, limit }: { offset: number; limit: number }) => {
    const response = await api.get(`/api/v1/species?offset=${offset}&limit=${limit}`);
    return response.data;
  }
);

const speciesSlice = createSlice({
  name: 'species',
  initialState,
  reducers: {
    clearError(state) {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchSpecies.pending, (state) => { state.loading = true; })
      .addCase(fetchSpecies.fulfilled, (state, action) => {
        state.loading = false;
        state.items = action.payload.items;
        state.total = action.payload.total;
      })
      .addCase(fetchSpecies.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message ?? 'Unknown error';
      });
  },
});

export const { clearError } = speciesSlice.actions;
export default speciesSlice.reducer;
```

### 5.2 Typisierte Hooks

```typescript
// app/hooks.ts
import { useDispatch, useSelector } from 'react-redux';
import type { RootState, AppDispatch } from './store';

export const useAppDispatch = useDispatch.withTypes<AppDispatch>();
export const useAppSelector = useSelector.withTypes<RootState>();
```

- **Immer** `useAppDispatch` / `useAppSelector` statt `useDispatch` / `useSelector`

---

## 6. Custom Hooks

### 6.1 Referenz-Stabilisierung (Pflicht)

```tsx
// RICHTIG: useMemo fuer Objekte/Arrays
export function usePlantFilters() {
  const [filters, setFilters] = useState<Filters>({});

  return useMemo(() => ({
    filters,
    setFilters,
    activeCount: Object.keys(filters).length,
  }), [filters]);
}

// FALSCH: Instabiles Objekt bei jedem Render
export function usePlantFilters() {
  const [filters, setFilters] = useState<Filters>({});
  return { filters, setFilters }; // Neues Objekt bei jedem Render!
}
```

**Regeln:**
- Hooks die Objekte oder Arrays zurueckgeben: **`useMemo`** Pflicht
- Primitive Rueckgaben (`string`, `number`, `boolean`): kein `useMemo` noetig
- Callbacks in Hooks: `useCallback` verwenden

### 6.2 Hook-Benennung

```typescript
// Datei: hooks/useExpertiseLevel.ts
export function useExpertiseLevel(): ExpertiseLevelResult {
  // ...
}
```

- Dateiname = Hook-Name
- Return-Type immer explizit deklarieren

---

## 7. MUI-Verwendung

### 7.1 Theme

```typescript
// theme/theme.ts — Zentral, NICHT in Komponenten ueberschreiben
import { createTheme } from '@mui/material/styles';

export const lightTheme = createTheme({
  palette: {
    mode: 'light',
    primary: { main: '#2e7d32' },    // Kamerplanter Green
    // ...
  },
});

export const darkTheme = createTheme({
  palette: {
    mode: 'dark',
    // ...
  },
});
```

### 7.2 Styling-Hierarchie

1. **Theme** (global) — Farben, Typografie, Spacing
2. **`sx` Prop** (bevorzugt) — Komponentenspezifisches Styling
3. **`styled()`** (selten) — Nur fuer komplexe, wiederverwendbare Styled Components

```tsx
// RICHTIG: sx Prop fuer einmaliges Styling
<Box sx={{ display: 'flex', gap: 2, mb: 3 }}>

// RICHTIG: styled() fuer wiederverwendbare Komponenten
const StyledCard = styled(Card)(({ theme }) => ({
  borderLeft: `4px solid ${theme.palette.primary.main}`,
}));

// FALSCH: Inline style-Attribute
<Box style={{ display: 'flex', gap: '16px' }}>
```

---

## 8. Routing

```tsx
// App.tsx — react-router-dom v7
import { BrowserRouter, Routes, Route } from 'react-router-dom';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<DashboardPage />} />
          <Route path="species" element={<SpeciesPage />} />
          <Route path="species/:key" element={<SpeciesDetailPage />} />
          <Route path="t/:tenantSlug/*" element={<TenantRoutes />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
```

- Tenant-scoped Routen: `/t/:tenantSlug/...`
- Detailseiten: `/:key`
- Layout als Parent-Route mit `<Outlet />`

---

## 9. Internationalisierung (i18n)

```tsx
import { useTranslation } from 'react-i18next';

function SpeciesPage() {
  const { t } = useTranslation();

  return (
    <Typography variant="h4">{t('pages.species.title')}</Typography>
  );
}
```

**Regeln:**
- **Deutsch** ist Default-Sprache (`fallbackLng: 'de'`)
- **Keine** hartcodierten Strings in Komponenten (ausser technische Labels)
- Namespace: eine `translation.json` pro Sprache
- Enum-Uebersetzungen: `t(`enums.${enumName}.${value}`)`

---

## 10. API-Schicht

### 10.1 Axios-Client

```typescript
// api/client.ts — Zwei Clients: global + tenant-scoped
import axios from 'axios';

// Globale Endpunkte (/api/v1/species, /api/v1/auth/...)
export const client = axios.create({
  baseURL: '/api/v1',
  headers: { 'Content-Type': 'application/json' },
});

// Tenant-scoped Endpunkte (/api/v1/t/{slug}/...)
export const tenantClient = axios.create({
  baseURL: '/api/v1',
  headers: { 'Content-Type': 'application/json' },
});

// Interceptor: Tenant-Slug automatisch voranstellen
tenantClient.interceptors.request.use((config) => {
  const slug = getActiveTenantSlug();
  if (slug && config.url && !config.url.startsWith('/t/')) {
    config.url = `/t/${slug}${config.url}`;
  }
  return config;
});
```

### 10.2 Endpoint-Funktionen

```typescript
// api/endpoints/species.ts
import { client } from '@/api/client';
import type { Species, SpeciesCreate, PaginatedResponse } from '@/api/types';

export async function listSpecies(offset = 0, limit = 50) {
  const { data } = await client.get<PaginatedResponse<Species>>('/species', {
    params: { offset, limit },
  });
  return data;
}

export async function updateSpecies(key: string, payload: SpeciesCreate) {
  const { data } = await client.put<Species>(`/species/${key}`, payload);
  return data;
}
```

**Regeln:**
- Async-Funktionen, Generic `<ReturnType>` auf Axios-Call
- `{ data }` Destructuring aus Response
- `client` fuer globale, `tenantClient` fuer tenant-scoped Endpunkte
- Typen aus `@/api/types` importieren

### 10.3 Fehlerbehandlung

```typescript
// api/errors.ts
export class ApiError extends Error {
  errorId: string;
  errorCode: string;
  statusCode: number;
}

export function parseApiError(error: unknown): string {
  if (isApiError(error)) return error.message;
  if (error instanceof Error) return error.message;
  return 'An unknown error occurred.';
}

// In Komponenten: useApiError Hook
const { handleError } = useApiError();
try {
  await updateSpecies(key, data);
} catch (err) {
  handleError(err);  // Zeigt Toast + loggt
}
```

---

## 11. Formular-Pattern (react-hook-form + Zod)

### 11.1 Schema-Definition

```typescript
// validation/schemas.ts
import { z } from 'zod';

export const speciesSchema = z.object({
  scientific_name: z.string().min(1, 'Required'),
  family_key: z.string().nullable(),
  growth_habit: z.enum(['herb', 'shrub', 'tree']),
});

export type SpeciesFormData = z.infer<typeof speciesSchema>;
```

### 11.2 Formular-Komponente

```tsx
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { speciesSchema, type SpeciesFormData } from '@/validation/schemas';
import { FormTextField, FormSelectField, FormActions } from '@/components/form';

export default function SpeciesForm({ species, onSave }: SpeciesFormProps) {
  const { t } = useTranslation();
  const {
    control,
    handleSubmit,
    reset,
    formState: { isDirty },
  } = useForm<SpeciesFormData>({
    resolver: zodResolver(speciesSchema),
    defaultValues: { scientific_name: species?.scientific_name ?? '' },
  });

  const onSubmit = async (data: SpeciesFormData) => {
    await onSave(data);
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <FormTextField name="scientific_name" control={control} label={t('labels.species.scientificName')} required />
      <FormSelectField name="growth_habit" control={control} label={t('labels.species.growthHabit')} options={[...]} />
      <FormActions isDirty={isDirty} onReset={() => reset()} />
    </form>
  );
}
```

### 11.3 Formular-Feld-Komponenten

Wiederverwendbare Wrapper um MUI + react-hook-form `Controller`:

| Komponente | MUI-Basis | Zweck |
|-----------|-----------|-------|
| `FormTextField` | TextField | Text-/Zahleneingabe |
| `FormSelectField` | Select | Dropdown-Auswahl |
| `FormNumberField` | TextField (type=number) | Numerische Eingabe |
| `FormDateField` | DatePicker | Datumsauswahl |
| `FormMultiSelectField` | Autocomplete | Mehrfachauswahl |
| `FormChipInput` | ChipInput | String-Array Eingabe |
| `FormSwitchField` | Switch | Boolean-Toggle |
| `FormActions` | Button-Gruppe | Speichern/Zuruecksetzen |

```tsx
// Internes Pattern jeder Form-Komponente
<Controller
  name={name}
  control={control}
  render={({ field, fieldState: { error } }) => (
    <TextField
      {...field}
      value={field.value ?? ''}
      error={!!error}
      helperText={error?.message ?? helperText}
      fullWidth
      sx={{ mb: 2 }}
      data-testid={`form-field-${name}`}
    />
  )}
/>
```

**Regeln:**
- Zod-Schema definiert Validierung (nicht manuell im Handler)
- `zodResolver` verbindet Schema mit react-hook-form
- `FormActions` zeigt Speichern-Button nur wenn `isDirty`
- `UnsavedChangesGuard` warnt bei Navigation mit ungespeicherten Aenderungen
- `data-testid` auf allen interaktiven Elementen

---

## 12. Error Handling

### 12.1 Toast-Benachrichtigungen (notistack)

```tsx
import { useNotification } from '@/hooks/useNotification';

function SpeciesForm() {
  const { success, error } = useNotification();

  const handleSave = async () => {
    try {
      await updateSpecies(key, data);
      success(t('common.saved'));
    } catch (err) {
      error(parseApiError(err));
    }
  };
}
```

**Auto-Hide Zeiten:**
- Success: 5s
- Error: kein Auto-Hide (manuell schliessen)
- Warning: 8s
- Max 3 Toasts gleichzeitig (unten rechts)

---

## 13. Tests

### 13.1 Datei-Konvention

```
src/test/helpers.tsx              # renderWithProviders + Mock-Store Setup
src/test/setup.ts                 # vitest + MSW Setup, jest-dom Matchers
src/test/mocks/server.ts          # MSW setupServer
src/test/mocks/handlers.ts        # MSW Request-Handler
src/test/components/*.test.tsx    # Komponenten-Tests
src/test/pages/*.test.tsx         # Seiten-Tests
src/test/hooks/*.test.tsx         # Hook-Tests
src/test/a11y/*.test.tsx          # Accessibility-Tests
```

### 13.2 Test-Pattern

```tsx
import { describe, it, expect, vi } from 'vitest';
import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithProviders } from '@/test/helpers';

describe('PlantCard', () => {
  it('renders plant name', () => {
    renderWithProviders(<PlantCard plant={mockPlant} onSelect={vi.fn()} />);
    expect(screen.getByText('Monstera deliciosa')).toBeInTheDocument();
  });

  it('calls onSelect when clicked', async () => {
    const user = userEvent.setup();
    const onSelect = vi.fn();
    renderWithProviders(<PlantCard plant={mockPlant} onSelect={onSelect} />);
    await user.click(screen.getByRole('button'));
    expect(onSelect).toHaveBeenCalledWith(mockPlant.key);
  });
});
```

**Regeln:**
- `describe`/`it` Bloecke (vitest)
- `renderWithProviders` aus `@/test/helpers` (enthaelt Redux Store + i18n + Theme + Router)
- `vi.fn()` fuer Mocks
- `screen` Queries bevorzugt: `getByRole`, `getByLabelText` (nicht `getByText`)
- `userEvent.setup()` fuer Interaktionen

### 13.3 API-Mocking (MSW)

```typescript
// test/mocks/handlers.ts
import { http, HttpResponse } from 'msw';

export const handlers = [
  http.get('/api/v1/species', () =>
    HttpResponse.json({ items: [mockSpecies], total: 1, offset: 0, limit: 50 }),
  ),
  http.post('/api/v1/species', async ({ request }) => {
    const body = await request.json();
    return HttpResponse.json({ key: 'new-key', ...body }, { status: 201 });
  }),
];
```

- MSW faengt HTTP-Requests ab (kein Backend noetig)
- Handlers in `test/mocks/handlers.ts`
- Auto-Reset zwischen Tests (`server.resetHandlers()`)

### 13.4 Test-Helper Setup

```tsx
// test/helpers.tsx — MUSS userPreferences Reducer enthalten
export function renderWithProviders(
  ui: React.ReactElement,
  { store = createTestStore(), route = '/' } = {},
) {
  const router = createMemoryRouter([{ path: '*', element: ui }], {
    initialEntries: [route],
  });
  return {
    store,
    ...render(
      <Provider store={store}>
        <ThemeContextProvider>
          <SnackbarProvider>
            <RouterProvider router={router} />
          </SnackbarProvider>
        </ThemeContextProvider>
      </Provider>,
    ),
  };
}
```

### 13.5 Accessibility-Tests (vitest-axe)

```tsx
import { axe } from 'vitest-axe';

it('has no critical a11y violations', async () => {
  const { container } = renderWithProviders(<DashboardPage />);
  const results = await axe(container);
  expect(results.violations.filter(v => v.impact === 'critical')).toEqual([]);
});
```

### 13.6 Coverage-Schwellen

```typescript
// vitest.config.ts
coverage: {
  provider: 'v8',
  thresholds: { statements: 80, branches: 80, functions: 80, lines: 80 },
}
```

---

## 14. Accessibility (a11y)

- **vitest-axe**: Automatisierte a11y-Pruefung (keine kritischen Violations)
- **data-testid**: Auf allen interaktiven Elementen
- **Role-Based Queries** in Tests: `getByRole('button')`, `getByLabelText()` bevorzugt
- **ARIA-Attribute**: `role`, `aria-label`, `aria-describedby` auf komplexen Komponenten
- **Keyboard-Navigation**: Alle Dialoge/Menues per Tastatur bedienbar
- **Farbkontrast**: MUI-Paletten WCAG AA konform

---

## 15. Expertise-Level System (REQ-021)

```tsx
import { ExpertiseFieldWrapper } from '../components/common/ExpertiseFieldWrapper';
import { fieldConfigs } from '../config/fieldConfigs';

// Felder deklarativ ein-/ausblenden
<ExpertiseFieldWrapper config={fieldConfigs.species.frostSensitivity}>
  <TextField label={t('pages.species.frostSensitivity')} ... />
</ExpertiseFieldWrapper>
```

- Feldkonfiguration in `fieldConfigs.ts` (deklarativ)
- `ExpertiseFieldWrapper` blendet Felder nach Level ein/aus
- `ShowAllFieldsToggle` fuer temporaere Anzeige aller Felder

---

## 16. Node-Version & Build

**`.tool-versions`**: `nodejs 25.1.0` (asdf)

```bash
npm run dev         # Vite Dev-Server (Port 5173, API-Proxy → localhost:8000)
npm run build       # tsc -b && vite build → dist/
npm run lint        # ESLint
npm run format      # Prettier
npm run test        # vitest run
```

---

## 17. Zusammenfassung der Pruefkette

```
Code-Aenderung
    │
    ├─→ eslint              → React Hooks, TS-Regeln, Unused Vars
    ├─→ tsc --noEmit        → Strikte Typpruefung, keine impliziten any
    ├─→ prettier (via lint)  → Einheitliche Formatierung
    └─→ vitest run          → Komponenten- und Unit-Tests
```

Alle vier Tools muessen in CI/CD **fehlerfrei** durchlaufen.
