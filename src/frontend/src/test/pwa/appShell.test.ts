import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { describe, expect, it } from 'vitest';
import { existsSync, readdirSync } from 'node:fs';
import {
  START_ROUTE_SOURCES,
  appShellFiles,
  firstPaintFiles,
  isAppShellEntry,
  type ViteManifestChunk,
} from '@/pwa/appShell';

/**
 * Precache scope (REQ-053 WP 9.1, #2786 review finding 8): only the app shell is precached —
 * index.html and what it loads eagerly, icons, manifest. Lazy route chunks come cache-first from the
 * worker's /assets/ route on first use.
 */

const INDEX = `<!doctype html><html><head>
<script type="module" crossorigin src="/assets/index-AAA.js"></script>
<link rel="modulepreload" crossorigin href="/assets/vendor-react-BBB.js">
<link rel="modulepreload" crossorigin href="/assets/vendor-mui-CCC.js">
<link rel="stylesheet" crossorigin href="/assets/index-DDD.css">
</head><body><script src="/runtime-config.js"></script></body></html>`;

describe('appShellFiles', () => {
  const shell = appShellFiles(INDEX);

  it('takes index.html, the entry, its modulepreloads and stylesheets', () => {
    expect([...shell].sort()).toEqual(
      ['assets/index-AAA.js', 'assets/index-DDD.css', 'assets/vendor-mui-CCC.js', 'assets/vendor-react-BBB.js', 'index.html'].sort(),
    );
  });

  it('keeps lazy route chunks, illustrations and runtime-config.js out of the precache', () => {
    expect(isAppShellEntry('assets/GardenPlanRoute-EEE.js', shell)).toBe(false);
    expect(isAppShellEntry('assets/error-503-FFF.svg', shell)).toBe(false);
    expect(isAppShellEntry('runtime-config.js', shell)).toBe(false);
    expect(isAppShellEntry('icons/icon-192.png', shell)).toBe(true);
    expect(isAppShellEntry('manifest.json', shell)).toBe(true);
  });

  it('is the transform the build applies to the precache manifest', () => {
    const config = readFileSync(join(process.cwd(), 'vite.config.ts'), 'utf8');
    expect(config).toMatch(/manifestTransforms: \[/);
    expect(config).toMatch(/entries\.filter\(\(entry\) => isAppShellEntry\(entry\.url, shell\)\)/);
    expect(config).toMatch(/appShellFiles\(readFileSync\(indexPath, 'utf8'\)\)/);
    expect(config).toMatch(/firstPaintFiles\(chunkGraph\)/);
    expect(config).toMatch(/firstPaint\.files\.forEach\(\(file\) => shell\.add\(file\)\)/);
    expect(config).toMatch(/if \(firstPaint\.missing\.length > 0\) \{\s*throw/);
  });
});

/**
 * #2786 review F1: the first paint loads the translation bundles and the start route by dynamic
 * import BEFORE the new worker controls the page, so they never reach the runtime cache. They must
 * be in the precache, resolved from the build's chunk graph.
 */
describe('firstPaintFiles — locale bundles and start routes', () => {
  const GRAPH: Record<string, ViteManifestChunk> = {
    'index.html': { file: 'assets/index-AAA.js', imports: ['_vendor-react.js'] },
    '_vendor-react.js': { file: 'assets/vendor-react-BBB.js' },
    'src/i18n/locales/de/pages.json': { file: 'assets/pages-DE.js' },
    'src/i18n/locales/de/enums.json': { file: 'assets/enums-DE.js' },
    'src/i18n/locales/de/glossary.json': { file: 'assets/glossary-DE.js' },
    'src/i18n/locales/en/pages.json': { file: 'assets/pages-EN.js' },
    'src/i18n/locales/en/enums.json': { file: 'assets/enums-EN.js' },
    'src/i18n/locales/en/glossary.json': { file: 'assets/glossary-EN.js' },
    'src/pages/DashboardPage.tsx': {
      file: 'assets/DashboardPage-CCC.js',
      imports: ['_widgets.js', '_vendor-react.js'],
      css: ['assets/DashboardPage-CCC.css'],
    },
    '_widgets.js': { file: 'assets/widgets-DDD.js', imports: ['_deep.js'] },
    '_deep.js': { file: 'assets/deep-EEE.js' },
    'src/pages/auth/LoginPage.tsx': { file: 'assets/LoginPage-FFF.js' },
    'src/pages/PlantDetailPage.tsx': { file: 'assets/PlantDetailPage-GGG.js' },
  };

  it('takes every locale bundle of every language', () => {
    const { files, missing } = firstPaintFiles(GRAPH);
    expect(missing).toEqual([]);
    for (const lang of ['DE', 'EN']) {
      for (const ns of ['pages', 'enums', 'glossary']) expect(files.has(`assets/${ns}-${lang}.js`)).toBe(true);
    }
  });

  it('takes the start routes with their transitive static imports and stylesheets', () => {
    const { files } = firstPaintFiles(GRAPH);
    for (const file of [
      'assets/DashboardPage-CCC.js',
      'assets/DashboardPage-CCC.css',
      'assets/widgets-DDD.js',
      'assets/deep-EEE.js',
      'assets/LoginPage-FFF.js',
    ]) {
      expect(files.has(file)).toBe(true);
    }
    expect(files.has('assets/PlantDetailPage-GGG.js')).toBe(false);
  });

  it('reports a start route or the locale bundles missing from the build, instead of dropping them', () => {
    expect(firstPaintFiles({}, ['src/pages/Gone.tsx']).missing).toEqual([
      'src/pages/Gone.tsx',
      'src/i18n/locales/*/*.json',
    ]);
  });

  it('names start routes and locales that exist in the source tree', () => {
    for (const source of START_ROUTE_SOURCES) expect(existsSync(join(process.cwd(), source))).toBe(true);
    const languages = readdirSync(join(process.cwd(), 'src/i18n/locales'));
    expect(languages.sort()).toEqual(['de', 'en']);
    const i18nSource = readFileSync(join(process.cwd(), 'src/i18n/i18n.ts'), 'utf8');
    for (const lang of languages) {
      expect(i18nSource).toContain(`import('./locales/${lang}/pages.json')`);
    }
  });
});
