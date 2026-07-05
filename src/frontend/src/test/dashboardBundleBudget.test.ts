import { describe, it, expect } from 'vitest';
// Vite `?raw` imports the module source as a string (no node:fs needed).
import readonlyGridSrc from '@/components/dashboard/DashboardReadonlyGrid.tsx?raw';
import dashboardPageSrc from '@/pages/DashboardPage.tsx?raw';
import editGridSrc from '@/components/dashboard/DashboardEditGrid.tsx?raw';

/**
 * REQ-045 §3.9 / UI-NFR-003 R-028 (K-001) — the read-only rendering path of the
 * most-visited page must NOT statically pull in react-grid-layout. The DnD
 * library may only be a static import of the lazily-loaded edit grid. This
 * source-level guard fails fast if a future refactor reintroduces the library
 * into the read-only path.
 */
// Match the quoted module specifier prefix, so any entrypoint (the main entry,
// the `/legacy` compat subpath, or `/css/*` styles) is caught, while prose
// mentions of the library in doc comments do not trip the guard.
const SPECIFIER = "'react-grid-layout";

describe('dashboard route bundle budget', () => {
  it('read-only grid does not import react-grid-layout', () => {
    expect(readonlyGridSrc).not.toContain(SPECIFIER);
  });

  it('DashboardPage does not statically import react-grid-layout (edit grid is lazy)', () => {
    expect(dashboardPageSrc).not.toContain(SPECIFIER);
    expect(dashboardPageSrc).toContain('lazy(() => import');
  });

  it('the edit grid is the sole static importer of react-grid-layout', () => {
    expect(editGridSrc).toContain(`from ${SPECIFIER}`);
  });
});
