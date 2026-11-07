import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { describe, expect, it } from 'vitest';
import { appShellFiles, isAppShellEntry } from '@/pwa/appShell';

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
    expect(config).toMatch(/appShellFiles\(indexHtml\)/);
  });
});
