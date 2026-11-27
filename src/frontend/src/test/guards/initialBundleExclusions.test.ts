import { describe, expect, it } from 'vitest';

/**
 * #3023 — what must stay out of the initial JS bundle (UI-NFR-003 R-013).
 *
 * The bundle budget (`scripts/check-bundle-budget.mjs`) only measures the sum; it cannot say *why* the entry grew.
 * These source checks pin the individual moves of #3023 so a single static `import` cannot quietly undo one:
 *
 * - the error illustrations (up to 74 KB gzip each) load per status code via `import()`, never statically —
 *   both error pages render inside the eager shell;
 * - the English core translations are a dynamic import, only the German fallback core is static;
 * - the notification drawer, the light-mode take-over dialog and the consent banner are `lazy()` boundaries;
 * - #3018: the static German core carries no page-level namespace (dashboard, settings tabs, print, diagnosis,
 *   AI, …) — those ship with the lazy `pages.json`, as the English ones always did, which made room for the
 *   mobile bottom navigation in the shell.
 *
 * Each detector is exercised against fixtures below in both directions.
 */

const SOURCES = import.meta.glob(['/src/**/*.ts', '/src/**/*.tsx'], {
  query: '?raw',
  import: 'default',
  eager: true,
}) as Record<string, string>;

/** The German catalogue files as written — the i18n bootstrap merges the imported modules into one object. */
const DE_CATALOGUE = import.meta.glob(['/src/i18n/locales/de/core.json', '/src/i18n/locales/de/pages.json'], {
  query: '?raw',
  import: 'default',
  eager: true,
}) as Record<string, string>;

function isProductionSource(path: string): boolean {
  return !/\.(test|spec)\.tsx?$/.test(path) && !path.endsWith('.d.ts') && !path.startsWith('/src/test/');
}

/** Whether `code` imports `module` statically — type-only imports are erased and do not count. */
function importsStatically(code: string, module: RegExp): boolean {
  const pattern = /^\s*(import|export)\s+(type\s+)?(?:[^'"]*?\s+from\s+)?['"]([^'"]+)['"]/gm;
  for (const match of code.matchAll(pattern)) {
    if (match[2]) continue; // `import type` — erased at build time
    if (module.test(match[3])) return true;
  }
  return false;
}

/** Whether `code` loads `module` through a dynamic `import('…')`. */
function importsDynamically(code: string, module: RegExp): boolean {
  for (const match of code.matchAll(/\bimport\(\s*['"]([^'"]+)['"]\s*\)/g)) {
    if (module.test(match[1])) return true;
  }
  return false;
}

const ERROR_ILLUSTRATION = /assets\/illustrations\/errors\/error-\d{3}\.svg$/;
const EN_CORE = /locales\/en\/core\.json$/;

function source(path: string): string {
  const code = SOURCES[path];
  if (code === undefined) throw new Error(`${path} is not in the source glob`);
  return code;
}

describe('initial bundle exclusions (#3023)', () => {
  it('no production module imports an error illustration statically', () => {
    const offenders = Object.entries(SOURCES)
      .filter(([path]) => isProductionSource(path))
      .filter(([, code]) => importsStatically(code, ERROR_ILLUSTRATION))
      .map(([path]) => path);
    expect(offenders).toEqual([]);
  });

  it('ErrorIllustration loads every status illustration through import()', () => {
    const code = source('/src/components/common/ErrorIllustration.tsx');
    for (const status of [400, 401, 403, 404, 408, 429, 500, 502, 503]) {
      expect(importsDynamically(code, new RegExp(`errors/error-${status}\\.svg$`))).toBe(true);
    }
  });

  it('both error pages render the lazy ErrorIllustration', () => {
    for (const page of ['/src/pages/ErrorPage.tsx', '/src/pages/RouterErrorPage.tsx']) {
      expect(importsStatically(source(page), /components\/common\/ErrorIllustration$/)).toBe(true);
    }
  });

  it('the English core translations are code-split, the German fallback core is static', () => {
    const code = source('/src/i18n/i18n.ts');
    expect(importsStatically(code, EN_CORE)).toBe(false);
    expect(importsDynamically(code, EN_CORE)).toBe(true);
    expect(importsStatically(code, /locales\/de\/core\.json$/)).toBe(true);
  });

  it('the static German core holds no page-level namespace (#3018)', () => {
    // These keys are read by lazily loaded pages and dialogs — and one by the eager shell: the breadcrumb of
    // `/diagnose` (`diagnose.title`, `routes/breadcrumbs.ts`). None is read before the app mounts, and `initI18n`
    // awaits `pages.json` before the mount, so every reader finds its key; only if that load fails does the
    // breadcrumb show its key text (`defaultValue`) — like every page string in that case.
    const PAGE_LEVEL = ['dashboard', 'storageSettings', 'print', 'diagnose', 'tankAlerts', 'haPublish', 'ai', 'components'];
    const deCore = JSON.parse(DE_CATALOGUE['/src/i18n/locales/de/core.json']) as Record<string, unknown>;
    const dePages = JSON.parse(DE_CATALOGUE['/src/i18n/locales/de/pages.json']) as Record<string, unknown>;
    expect(PAGE_LEVEL.filter((namespace) => namespace in deCore)).toEqual([]);
    expect(PAGE_LEVEL.filter((namespace) => !(namespace in dePages))).toEqual([]);
  });

  it.each([
    ['/src/components/layout/NotificationBell.tsx', /\.\/NotificationDrawer$/],
    ['/src/layouts/MainLayout.tsx', /components\/tenants\/LightModeTakeoverDialog$/],
    ['/src/components/privacy/AppConsentBanner.tsx', /components\/privacy\/ConsentBanner$/],
  ])('%s loads its shell dialog lazily', (path, module) => {
    const code = source(path);
    expect(importsStatically(code, module)).toBe(false);
    expect(importsDynamically(code, module)).toBe(true);
  });

  describe('detectors', () => {
    it('importsStatically sees default, named, side-effect and re-export imports, not type-only ones', () => {
      expect(importsStatically("import a from '@/assets/illustrations/errors/error-404.svg';", ERROR_ILLUSTRATION)).toBe(
        true,
      );
      expect(importsStatically("import '@/assets/illustrations/errors/error-404.svg';", ERROR_ILLUSTRATION)).toBe(true);
      expect(importsStatically("export { default } from './locales/en/core.json';", EN_CORE)).toBe(true);
      expect(importsStatically("import { x, y } from './locales/en/core.json';", EN_CORE)).toBe(true);
      expect(importsStatically("import type { X } from './locales/en/core.json';", EN_CORE)).toBe(false);
      expect(importsStatically("const m = () => import('./locales/en/core.json');", EN_CORE)).toBe(false);
    });

    it('importsDynamically sees import() and ignores static imports', () => {
      expect(importsDynamically("() => import('./locales/en/core.json')", EN_CORE)).toBe(true);
      expect(importsDynamically("import enCore from './locales/en/core.json';", EN_CORE)).toBe(false);
    });
  });
});
