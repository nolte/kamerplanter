# Kamerplanter Frontend

React/TypeScript single-page application for plant lifecycle management.

## Tech Stack

| Technology | Version | Purpose |
|---|---|---|
| React | 19 | UI framework |
| TypeScript | 5.9 | Type safety (strict mode) |
| MUI | 7 | Component library |
| Redux Toolkit | 2.5 | State management |
| react-router-dom | 7 | Client-side routing |
| react-hook-form + zod | 7.56 / 3.25 | Form handling & validation |
| react-i18next | 16 | Internationalization (DE/EN) |
| Vite | 6.4 | Build tooling & dev server |
| Vitest | 3 | Unit testing |
| Axios | 1.9 | HTTP client |
| dayjs | 1.11 | Date handling |

## Getting Started

```bash
# Install dependencies
npm ci

# Start dev server (port 5173)
npm run dev

# API proxy: /api -> http://127.0.0.1:8000
# Override with VITE_BACKEND_URL env variable
```

## Scripts

| Command | Description |
|---|---|
| `npm run dev` | Start Vite dev server |
| `npm run build` | TypeScript check + production build |
| `npm run lint` | ESLint check |
| `npm run format` | Prettier formatting |
| `npm run test` | Run Vitest tests |
| `npm run test:watch` | Watch mode |
| `npm run test:coverage` | Coverage report |

## Project Structure

```
src/
  api/endpoints/        # Axios API client functions per domain
  assets/               # Static assets (brand, illustrations)
  auth/                 # AuthProvider, route guards
  components/
    common/             # DataTable, EmptyState, ErrorDisplay, PhotoUpload, TaskTimer
    form/               # FormTextField, FormNumberField, FormSelectField, FormRow,
                        #   LocationTreeSelect, SubstrateSelectField
    layout/             # Breadcrumbs, Sidebar
    water/              # Water source/mixing components
  config/               # fieldConfigs.ts (expertise-level field visibility)
  hooks/                # useTabUrl, useCountdownTimer, useLocalFavorites,
                        #   useRunNutrientData, useSowingFavorites,
                        #   useWateringVolumeSuggestion, useExpertiseLevel
  pages/
    admin/              # AdminSettingsPage
    aufgaben/           # Task queue, workflow templates, activity plans
    auth/               # Login, Register, Password reset, Account settings
    duengung/           # Fertilizers, nutrient plans, feeding events, Gantt charts
    durchlaeufe/        # Planting runs, phase timelines, watering calendar
    ernte/              # Harvest batches, observations
    giessprotokoll/     # Watering logs (create, detail, list)
    kalender/           # Calendar, sowing calendar, season overview, phase timeline
    onboarding/         # OnboardingWizard (5-step)
    pflanzen/           # Plant instances, growth phases, profiles, phase transitions
    pflanzenschutz/     # IPM: pests, diseases, treatments
    pflege/             # Care dashboard, care profile editing, care confirmation
    stammdaten/         # Species, cultivars, botanical families, activities,
                        #   companion planting, crop rotation
    standorte/          # Sites, locations, substrates, tanks, slots,
                        #   watering events, sensors, maintenance
    tenants/            # Tenant settings
  routes/               # AppRoutes.tsx (lazy-loaded routes)
  store/slices/         # 20+ Redux slices
  test/                 # Test helpers & test files
  theme/                # MUI theme (light/dark)
  utils/                # weekCalculation, etc.
```

## Architecture

- **State**: Redux Toolkit with one slice per domain. Async operations via `createAsyncThunk`.
- **Routing**: `react-router-dom` v7 with `createBrowserRouter`, lazy-loaded pages, `ProtectedRoute`/`PublicOnlyRoute` guards.
- **Forms**: `react-hook-form` + `zod` schemas. Reusable form components (`FormTextField`, `FormNumberField`, `FormSelectField`).
- **i18n**: German (default) and English. Keys follow `pages.<section>.<key>` pattern. Enum translations: `enums.<enumName>.<value>`.
- **Expertise levels**: `fieldConfigs.ts` controls field visibility per experience level (beginner/intermediate/expert). `ExpertiseFieldWrapper` hides advanced fields. Navigation items tiered in Sidebar.
- **API**: Axios client with `/api` proxy to backend. Endpoint files grouped by domain in `api/endpoints/`.

## Conventions

- Custom hooks returning objects/arrays must wrap return values with `useMemo` to stabilize references.
- TypeScript strict mode enabled (`noUnusedLocals`, `noUnusedParameters`).
- Path alias: `@/` maps to `src/`.
