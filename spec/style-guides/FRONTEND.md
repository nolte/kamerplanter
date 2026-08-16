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
  details: ApiErrorDetail[];   // { field, reason, code } je Verletzung
}
```

**Regel: Server-Fehlertexte werden NIE roh angezeigt.** `message` und
`details[].reason` kommen aus dem Backend und sind **englisch** (NFR-003 haelt
Source und API-Meldungen englisch, die UI ist uebersetzt). Angezeigt wird
ausschliesslich ein ueber den **stabilen Code** aufgeloester Text:

- Top-Level: `error_code` → `errors.<error_code>` (NFR-017 R-118)
- Feldfehler: `details[].code` → `errors.<code>`, gesetzt am Feld, das
  `details[].field` benennt (`body.`-Praefix abgeschnitten)

```typescript
export function parseApiError(error: unknown, t: TFunction): string {
  if (isApiError(error)) {
    // Der Code ist der Vertrag, `message` ist nur der englische Rohtext.
    return t(`errors.${error.errorCode}`, { defaultValue: t('errors.generic') });
  }
  if (error instanceof Error) return t('errors.network');
  return t('errors.unknown');
}

// Feldfehler: Code -> i18n-Key, nie `reason` durchreichen
for (const v of getFieldViolations(err)) {
  const formField = SERVER_TO_FORM_FIELD[v.field];
  const key = `errors.${v.code}`;
  if (formField && i18n.exists(key)) {
    setError(formField, { message: t(key) });   // RICHTIG
  }
  // FALSCH: setError(formField, { message: v.reason }) — englischer Satz im deutschen Formular
}
```

Der **Fallback ist ein uebersetzter generischer Text**, kein englischer
Rohstring: Ein Code ohne Uebersetzung faellt auf `errors.generic` zurueck und
bleibt im generischen Validierungs-Toast sichtbar (der Dialog bleibt offen) —
sichtbar-degradiert schlaegt falsch-uebersetzt. Belege: #1015, #1016.

```typescript
// In Komponenten: useApiError Hook
const { handleError } = useApiError();
try {
  await updateSpecies(key, data);
} catch (err) {
  handleError(err);  // loest Code -> i18n auf, zeigt Toast + loggt
}
```

Ein Feld, das eine Servermeldung tragen soll, braucht eine sichtbare
Fehlerflaeche und den `form-field-<name>`-Hook — Details in §11.2a.

---

## 11. Formular-Pattern (react-hook-form + Zod)

### 11.0 `<Form>` statt `<form>` — `noValidate` ist nicht verhandelbar

**Regel:** Jedes Formular rendert `<Form>` aus `@/components/form/Form`. Ein
rohes `<form>`-Element oder ein `component="form"` ist verboten.

`<Form>` setzt `noValidate` **nach** dem Prop-Spread, damit keine Aufrufstelle es
abschalten kann. Ohne `noValidate` fuehrt der Browser seine eigene
Constraint-Validierung aus und bricht das Absenden ab, **bevor** das
`submit`-Event feuert. Die Folge ist keine Kosmetik:

1. `handleSubmit` laeuft nie → **Zod laeuft nie**, jede Cross-Field- und
   Domaenenregel im Schema wird still uebersprungen.
2. Kein `helperText` rendert → die uebersetzten Feldmeldungen erscheinen nicht.
3. Der Nutzer sieht stattdessen eine native Bubble in der **Browser**-Locale —
   eine deutsche App zeigt eine englische Meldung.

Unsere `Form*Field`-Wrapper reichen `required` direkt an den MUI-Input durch, wo
es als natives Attribut auf dem DOM-Knoten landet: **jedes** aus ihnen gebaute
Formular ist ohne `noValidate` betroffen. Das war #825 — 55 von 84
formulartragenden Dateien hatten das Richtige nicht opt-in gewaehlt.

**Durchsetzung (normativ, nicht nur Lint-Detail).** `eslint.config.js` fuehrt
drei `no-restricted-syntax`-Selektoren, die zusammen die Regel schliessen. Sie
gehoeren zur Spec, nicht nur zur Werkzeugkonfiguration — wer die Lint-Regel
entfernt, entfernt die Regel:

| Selektor | Was er verbietet |
|----------|------------------|
| `JSXOpeningElement[name.name='form']:not(:has(JSXAttribute[name.name='noValidate']))` | rohes `<form>` ohne `noValidate` |
| `JSXOpeningElement:has(JSXAttribute[name.name='component'][value.value='form']):not(:has(JSXAttribute[name.name='noValidate']))` | `component="form"` ohne `noValidate` |
| `JSXAttribute[name.name='noValidate'][value.expression.value=false]` | `noValidate={false}` — sieht aus wie Konformitaet, ist der defekte Zustand |

Der dritte Selektor existiert, weil die ersten beiden nur die *Anwesenheit* des
Attributs pruefen. Ein Guard, dessen Aufgabe es ist, den schlechten Zustand
unerreichbar zu machen, darf kein Opt-out haben, das sich wie Erfuellung liest.

!!! warning "Kein Unit-Test kann das pruefen"
    jsdom implementiert die native Constraint-Validierung nicht. Ein
    Verhaltenstest („leeres Pflichtfeld absenden, Zod-Meldung erwarten") ist
    **mit und ohne** `noValidate` gruen — er sieht aus, als bewache er die
    Regel, und tut es nicht (#822 hat einen solchen Test deshalb verworfen).
    Die wirksamen Verteidigungen sind die drei Lint-Selektoren und E2E in einem
    echten Browser.

**Migrationsfalle:** `<Form>` *entfernt* die native Validierung. Fuer ein
RHF+Zod-Formular ist genau das der Zweck. Fuer ein reines `useState`-Formular
ohne Schema war `required` die einzige Bremse — dort den Submit-Button auf die
gefuellten Felder gaten (`disabled={isLoading || !email || !password}`). Die
Lint-Regel sieht hier ein konformes `<Form>` und kann die Klasse nicht fangen.

### 11.1 Schema-Definition

**Regel: Zod-Meldungen MUESSEN i18n-Keys sein, niemals fertige Prosa.** Ein
Literal wie `'Required'` ist in einer deutschen App eine englische
Fehlermeldung — dieselbe Klasse wie die native Browser-Bubble aus §11.0, nur
selbst verursacht. Das Schema traegt den **stabilen Key**, aufgeloest wird er
beim Rendern.

```typescript
// validation/schemas.ts
import { z } from 'zod';

// RICHTIG — die Meldung ist ein i18n-Key
export const speciesSchema = z.object({
  scientific_name: z.string().min(1, 'validation.required'),
  family_key: z.string().nullable(),
  growth_habit: z.enum(['herb', 'shrub', 'tree'], { error: 'validation.invalidOption' }),
  allelopathy_score: z.number().min(-1, 'validation.min').max(1, 'validation.max'),
});

// FALSCH — englische Prosa, die ungefiltert im deutschen Formular landet
export const speciesSchemaWrong = z.object({
  scientific_name: z.string().min(1, 'Required'),
});

export type SpeciesFormData = z.infer<typeof speciesSchema>;
```

Damit ein Key nicht roh im Formular erscheint, loest die **Feld-Wrapper-Schicht**
ihn auf — die Stelle, an der `fieldState.error.message` in `helperText` wandert
(`FormTextField` und Geschwister). Ein Key ohne Uebersetzung faellt auf einen
generischen Text zurueck, nie auf den rohen Key.

Fuer Zod-**eigene** Meldungen (Typfehler, `invalid_type`, die kein Aufrufer
explizit setzt) wird ein globaler Fehler-Adapter einmal beim App-Start
registriert, statt jede Regel einzeln zu beschriften:

```typescript
// validation/zodI18n.ts — einmalig in main.tsx importiert
import { z } from 'zod';
import i18n from '@/i18n';

// zod 4: z.config({ customError }); in zod 3 hiess dieselbe Stelle z.setErrorMap.
z.config({
  customError: (issue) => ({
    message: i18n.t(`validation.zod.${issue.code}`, {
      defaultValue: i18n.t('validation.invalid'),
      ...issue,
    }),
  }),
});
```

!!! note "Bestand"
    Die vorhandenen Schemas in `src/frontend/src/validation/` tragen noch
    englische Literale (`'Name is required'`), und die `Form*Field`-Wrapper
    reichen `error.message` heute unuebersetzt durch. Die Umstellung laeuft als
    eigene Massnahme (P4.1 der Issue-Muster-Analyse); fuer **neuen oder
    angefassten** Code gilt die Regel oben ab sofort — wie bei §5.3 im
    Backend-Guide waechst die Abdeckung mit der normalen Arbeit am Feature.

### 11.2 Formular-Komponente

```tsx
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { speciesSchema, type SpeciesFormData } from '@/validation/schemas';
import Form from '@/components/form/Form';
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
    <Form onSubmit={handleSubmit(onSubmit)}>
      <FormTextField name="scientific_name" control={control} label={t('labels.species.scientificName')} required />
      <FormSelectField name="growth_habit" control={control} label={t('labels.species.growthHabit')} options={[...]} />
      <FormActions isDirty={isDirty} onReset={() => reset()} />
    </Form>
  );
}
```

`<Form>` statt `<form>` ist Pflicht — siehe §11.0.

### 11.2a Feldübergreifende Domänenregeln gehören **nicht** ins Zod-Schema

**Einzelfeld-Constraints spiegeln, feldübergreifende Regeln nicht.**

| Art der Regel | Beispiel | Gehört ins Zod-Schema? |
|---|---|---|
| Einzelfeld-Constraint (Wertebereich, Pflichtfeld, Enum) | `volume_liters > 0`, `ph <= 14` | **Ja** — steht ohnehin als `min`/`max` am Input, der Nutzer darf sie vor dem Absenden sehen, und „strenger als der Server" kann bei einem Zahlenbereich niemanden aussperren. |
| Feldübergreifende Domänenregel | „mindestens `slot_keys` **oder** `plant_keys`" | **Nein** — der Server prüft sie und antwortet mit 422 samt Feldangabe; die Antwort wird an den beteiligten Feldern angezeigt. |

Begründung (#970):

1. **Nichts kann die beiden Kopien vergleichen.** Backend-seitig funktioniert der Schutz gegen genau diese Klasse, weil beide Seiten Python sind und dieselbe Funktion aufrufen (`find_watering_log_violations` + `TestRequestSchemaAndDomainModelAgree`). Eine TypeScript-Kopie liegt ausserhalb dieser Reichweite — die Drift fände ein Nutzer, nicht die CI.
2. **Die beiden Drift-Richtungen scheitern unterschiedlich, und nur eine ist tragbar.** Eine veraltete Client-Kopie, die *strenger* ist als die Domäne, blockiert eine Eingabe, die der Server akzeptiert hätte: Der Nutzer kann etwas Erlaubtes nicht tun und hat keinen Ausweg. Wer nur die Serverantwort rendert, kann höchstens *hinterherhinken* — eine unbekannte Regel fällt auf den generischen Validierungs-Toast zurück, der Dialog bleibt offen. Sichtbar-degradiert schlägt falsch-blockierend.
3. **Eine Meldung ist keine Regel.** Der Client muss ohnehin einen übersetzten Text vorhalten, weil `reason` aus dem Backend englisch ist (NFR-003). Über den stabilen `code` der Verletzung gekoppelt ist eine veraltete Meldung *falscher Text*; ein veraltetes Prädikat wäre eine *falsche Entscheidung*.

**Umsetzung (#1015):** `useFieldViolations()` (`@/hooks/useFieldViolations`) baut aus einer `code → i18n-Key`-Map einen Handler, den `handleError(err, handler)` je Verletzung aufruft: er übersetzt über den stabilen `code` und setzt `setError()` nur, wenn der Code gemappt ist — sonst überspringt er die Verletzung, und sie fällt auf den generischen Toast aus `handleError()` zurück. **Der englische `reason` wird nie an ein Feld geschrieben.** Der `FieldViolationHandler`-Vertrag von `useApiError` nimmt `{ field, reason, code }`; das frühere `(name, message) => void`-Muster (das den englischen `reason` durchreichte) ist damit ein **Typfehler**, die Fehlerklasse also strukturell geschlossen. Referenz: `OverwinteringProfileDialog.tsx`, `HarvestCreateDialog.tsx`. Ein Dialog ohne gemappten Code übergibt keinen Handler und bleibt beim Toast.

Zod-Default-Meldungen (`z.number().gt(0)` u. a.) liefern sonst englischen Text in eine deutsche UI (#1016). Eine globale Error-Map (`@/validation/zodErrorMap`, via `z.config`) übersetzt sie über `validation.*` (DE-kanonisch + EN-Spiegel); eine neue blanke Constraint kann damit keinen englischen Default mehr ausliefern, Inline-Meldungen am Schema gewinnen weiterhin. Einzelne Constraints daher **nicht** mit Inline-Meldungen zupflastern — die Map trägt sie.

Ein Feld, das eine Servermeldung tragen soll, braucht eine sichtbare Fehlerfläche und den `form-field-<name>`-Hook. Die `Form*Field`-Wrapper bringen beides mit; ein direkt eingesetztes MUI-Control (z. B. `Autocomplete`) nicht — dort `fieldState.error` selbst verdrahten und in ein `<Box data-testid="form-field-<name>">` wickeln. Ohne das verschluckt der Mapping-Schritt die Verletzung lautlos.

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
- `data-testid` auf allen interaktiven Elementen (verbindliches Namensschema und Stabilitaetsvertrag: UI-NFR-022)

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

**Was hier wirklich durchgesetzt wird (#1096).** Genau eine a11y-Pruefung
blockiert: dieser vitest-axe-Lauf, im required Check `lint-test-build (22)`. Die
Lighthouse-a11y-Assertion (`categories:accessibility >= 0.98`, error) ist echt,
aber ihr Job ist **advisory** und sie sieht nur den statisch gebauten SPA-Shell —
keine Seite hinter dem Login. Eine E2E-axe-Journey gegen die komponierte
Anwendung existiert nicht (#1095, offen). Die vollstaendige Aufstellung samt der
Regeln, die **niemand** misst (Tastaturnavigation, Fokus-Indikator, Kontraste,
200%-Zoom), steht in der Definition of Done von UI-NFR-002; dieser Abschnitt
beschreibt nur den einen Lauf, der blockiert.

Benutze **immer** den gemeinsamen Helfer, nie `axe()` direkt (#1094):

```tsx
import { expectNoA11yViolations } from '@/test/a11y/expectNoA11yViolations';

it('has no critical a11y violations', async () => {
  const { container } = renderWithProviders(<DashboardPage />);
  await expectNoA11yViolations(container, { minElements: 20 });
});
```

Der Helfer trifft drei Entscheidungen, die vorher jede Datei neu raten musste:

- **`critical` laesst den Test scheitern**, nicht „gar keine Violations". In jsdom meldet axe an isoliert gerenderten Komponenten Kontrast- und Landmark-Befunde, die Artefakte des Tests sind und nicht des Bauteils; ein Helfer, der daran scheitert, wird abgeschaltet statt repariert. `minImpact` verschaerft pro Aufruf.
- **Grosszuegiger Timeout.** `axe()` ist ein vollstaendiger DOM-Durchlauf und ueberschreitet unter Volllast den 1-Sekunden-Default von `waitFor` (unabhaengig von `testTimeout`). Last darf das Urteil nicht faellen.
- **`minElements` ist bei Seiten Pflicht.** Eine Seite, die nur ihr Ladeskelett zeigt, besteht *jeden* axe-Test. Gemessen: zwei der vier in #1094 nachgezogenen Seiten standen bei 15 Elementen und waren gruen. Ohne diesen Boden zertifiziert der Test einen Spinner.

Neue **Seiten**-Tests bekommen den axe-Durchlauf per Default — trage die Seite in `src/test/a11y/topPages.a11y.test.tsx` ein. Bleibt eine Seite im Ladezustand haengen, weil die Default-MSW-Handler ihre Anfragen nicht beantworten, dann **gehoert sie nicht mit abgesenktem Boden hinein**, sondern braucht ihre Fixture oder bleibt vorerst draussen (dokumentiert). Der abgesenkte Boden macht die ganze Datei wertlos: dann besteht jede Seite im Ladezustand.

„Per Default" ist dabei nicht als Zusage gemeint, sondern wird gemessen:
`src/test/a11y/pageCoverage.test.tsx` zaehlt alle `*Page.tsx` auf und verlangt
fuer jede entweder einen axe-Durchlauf oder einen Eintrag im Register
`PAGES_OWING_AN_AXE_PASS`. Eine neue Seite kann die Pruefung damit nicht
stillschweigend ueberspringen — sie faellt auf, und wer sie zurueckstellt, muss
das hinschreiben. Das Register faellt ausserdem, sobald ein Eintrag ueberfluessig
geworden ist, damit es nicht zur Liste dessen wird, was frueher einmal fehlte.

Bei **Dialogen** ist der Container `document.body`, nicht das Render-Ergebnis:
MUI rendert in ein Portal, das Fragment aus `render` bleibt leer, und ein Scan
darueber besteht, waehrend er nichts ansieht. Ein Dialog ist zugleich die
Oberflaeche, an der a11y am haertesten scheitert — er uebernimmt die Seite, also
laesst ein fehlender Name oder eine fehlende Beschriftung Tastatur- und
Screenreader-Nutzung ohne Ausweg. Siehe `src/test/a11y/dialogs.a11y.test.tsx`.

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
