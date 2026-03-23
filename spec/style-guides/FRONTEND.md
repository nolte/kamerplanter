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
| **Prettier** | Code-Formatierung | via `eslint-config-prettier` |
| **Vitest** | Unit-/Komponententests | `vite.config.ts` |

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

### 1.2 TypeScript strict-Modus

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

### 1.3 CI-Pruefung

```bash
npx eslint src/            # Linting
npx tsc --noEmit           # Typpruefung
npx vitest run             # Tests
```

---

## 2. Projektstruktur

```
src/frontend/src/
├── api/                             # API-Schicht (RTK Query / Fetch)
│   └── {feature}Api.ts
├── app/                             # App-Setup
│   ├── store.ts                     # Redux Store
│   └── hooks.ts                     # Typisierte App-Hooks
├── components/                      # Wiederverwendbare UI-Komponenten
│   ├── common/                      # Layout, Navigation, Generics
│   └── {feature}/                   # Feature-spezifische Komponenten
├── features/                        # Redux Slices + Feature-Logik
│   └── {feature}/
│       └── {feature}Slice.ts
├── hooks/                           # Custom Hooks (global)
│   └── use{Feature}.ts
├── i18n/                            # Internationalisierung
│   ├── i18n.ts                      # i18next-Setup
│   └── locales/
│       ├── de/                      # Deutsch (Default)
│       │   └── translation.json
│       └── en/
│           └── translation.json
├── pages/                           # Seitenkomponenten (je Route)
│   └── {Feature}Page.tsx
├── test/                            # Test-Utilities
│   └── helpers.tsx                  # renderWithProviders, Mock-Stores
├── theme/                           # MUI-Theme
│   └── theme.ts
├── types/                           # Geteilte TypeScript-Typen
│   └── {feature}.ts
├── utils/                           # Hilfsfunktionen
│   └── {utility}.ts
├── App.tsx                          # Root-Komponente + Routing
└── main.tsx                         # Entry Point
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
| API | `camelCase` + `Api` Suffix | `speciesApi.ts` |
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

## 10. Formular-Pattern

```tsx
function SpeciesCreateDialog({ open, onClose }: DialogProps) {
  const { t } = useTranslation();
  const [formData, setFormData] = useState<SpeciesCreate>(INITIAL_STATE);
  const [errors, setErrors] = useState<Record<string, string>>({});

  const handleChange = (field: keyof SpeciesCreate) =>
    (e: React.ChangeEvent<HTMLInputElement>) => {
      setFormData((prev) => ({ ...prev, [field]: e.target.value }));
      setErrors((prev) => ({ ...prev, [field]: '' }));  // Fehler bei Eingabe loeschen
    };

  const handleSubmit = async () => {
    const validationErrors = validate(formData);
    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors);
      return;
    }
    await dispatch(createSpecies(formData));
    onClose();
  };

  return (
    <Dialog open={open} onClose={onClose}>
      <DialogTitle>{t('pages.species.createTitle')}</DialogTitle>
      <DialogContent>
        <TextField
          label={t('pages.species.scientificName')}
          value={formData.scientific_name}
          onChange={handleChange('scientific_name')}
          error={!!errors.scientific_name}
          helperText={errors.scientific_name}
          required
          fullWidth
        />
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>{t('common.cancel')}</Button>
        <Button variant="contained" onClick={handleSubmit}>{t('common.save')}</Button>
      </DialogActions>
    </Dialog>
  );
}
```

**Regeln:**
- MUI `Dialog` + `TextField` fuer Formulare
- Lokaler State fuer Formular-Daten
- Fehler-Objekt pro Feld
- Validierung vor Submit
- `fullWidth` auf TextField-Feldern

---

## 11. Error Handling

### 11.1 API-Fehler

```tsx
// In createAsyncThunk — Fehler werden automatisch im Slice behandelt
export const fetchSpecies = createAsyncThunk(
  'species/fetchAll',
  async (params, { rejectWithValue }) => {
    try {
      const response = await api.get('/api/v1/species');
      return response.data;
    } catch (error) {
      return rejectWithValue(extractErrorMessage(error));
    }
  }
);
```

### 11.2 Toast/Snackbar fuer User-Feedback

```tsx
// Zentrale Snackbar-Komponente in Layout
<Snackbar open={!!error} message={error} severity="error" />
```

---

## 12. Tests

### 12.1 Datei-Konvention

```
src/test/helpers.tsx          # renderWithProviders + Mock-Store Setup
src/pages/SpeciesPage.test.tsx # Seiten-Tests (co-located)
src/components/PlantCard.test.tsx # Komponenten-Tests (co-located)
```

### 12.2 Test-Pattern

```tsx
import { describe, it, expect, vi } from 'vitest';
import { renderWithProviders } from '../test/helpers';

describe('PlantCard', () => {
  it('renders plant name', () => {
    const { getByText } = renderWithProviders(
      <PlantCard plant={mockPlant} onSelect={vi.fn()} />
    );
    expect(getByText('Monstera deliciosa')).toBeInTheDocument();
  });

  it('calls onSelect when clicked', async () => {
    const onSelect = vi.fn();
    const { getByRole } = renderWithProviders(
      <PlantCard plant={mockPlant} onSelect={onSelect} />
    );
    await userEvent.click(getByRole('button'));
    expect(onSelect).toHaveBeenCalledWith(mockPlant.key);
  });
});
```

**Regeln:**
- `describe`/`it` Bloecke (vitest)
- `renderWithProviders` aus `test/helpers.tsx` (enthaelt Redux Store + i18n + Theme)
- `vi.fn()` fuer Mocks
- `@testing-library/react` Queries

### 12.3 Test-Helper Setup

```tsx
// test/helpers.tsx — MUSS userPreferences Reducer enthalten
export function renderWithProviders(
  ui: React.ReactElement,
  { preloadedState, ...options }: RenderOptions = {}
) {
  const store = configureStore({
    reducer: {
      species: speciesReducer,
      userPreferences: userPreferencesReducer, // Pflicht fuer useExpertiseLevel
      // ...
    },
    preloadedState,
  });
  return render(<Provider store={store}>{ui}</Provider>, options);
}
```

---

## 13. Expertise-Level System (REQ-021)

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

## 14. Zusammenfassung der Pruefkette

```
Code-Aenderung
    │
    ├─→ eslint              → React Hooks, TS-Regeln, Unused Vars
    ├─→ tsc --noEmit        → Strikte Typpruefung, keine impliziten any
    ├─→ prettier (via lint)  → Einheitliche Formatierung
    └─→ vitest run          → Komponenten- und Unit-Tests
```

Alle vier Tools muessen in CI/CD **fehlerfrei** durchlaufen.
