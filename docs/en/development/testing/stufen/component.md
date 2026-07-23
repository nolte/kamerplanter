# Component Tests

Component tests verify **React components in the rendered DOM** — with all required providers, but against a mocked API. They check what the user sees and does (clicks, input, validation) without starting a real browser. That places them between the unit and E2E levels.

## What this level verifies

- **Rendering & interaction:** that forms, dialogs, and pages display correctly and react to user actions.
- **Accessibility:** critical forms and dialogs are checked for accessibility violations with `vitest-axe`.

## Tested areas at a glance

| Area | Tested elements | Extent |
|------|-----------------|--------|
| Components | forms, dialogs, and widgets per area: admin, dashboard, diagnosis, pests, tanks, identification, glossary, layout, privacy, AI | extensive |
| Pages | page components incl. routing and data loading | extensive |
| Accessibility | critical forms/dialogs (`vitest-axe`) | focused |

## Tooling & location

| | Value |
|---|---|
| Tooling | vitest + Testing Library, `userEvent`, `vitest-axe` |
| Location | `src/frontend/src/test/components/`, `…/pages/`, `…/a11y/` |
| API | intercepted via [Mock Service Worker (MSW)](https://mswjs.io/) |

All component tests render via `renderWithProviders` from `src/test/helpers.tsx` — this wraps the component with the Redux store, React Router, MUI theme, and `SnackbarProvider`.

!!! warning "userPreferences reducer required"
    Components that use `useExpertiseLevel` need the `userPreferences` reducer in the test store. `createTestStore()` includes it; a manually built store must add it explicitly.

## Running

```bash
cd src/frontend
npm test                 # single run
npm run test:watch       # watch mode
npm run test:coverage    # with coverage report
```

Patterns and MSW details in the [testing concept → Frontend Tests](../index.md#frontend-tests-vitest).

## Conventions

- Never assemble providers manually — always use `renderWithProviders`.
- Mock API responses via MSW handlers; override test-specific behavior temporarily with `server.use(…)`.
- Every new or changed component needs a component test; critical forms additionally an a11y test.
