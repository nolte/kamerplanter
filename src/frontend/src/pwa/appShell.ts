/**
 * What the service worker precaches (REQ-053 WP 9.1, #2741, review findings 8 and F1): the app
 * shell — `index.html`, the entry chunk and every chunk/stylesheet `index.html` loads eagerly (the
 * set the bundle budget counts as "initial") — PLUS what the first paint needs before the worker
 * controls the page: the code-split translation bundles of every supported locale (`main.tsx`
 * awaits them before mounting) and the start routes (`/dashboard`, the manifest's `start_url`,
 * and `/login`) with their static imports. Those load by dynamic import on the very first visit,
 * before the new worker controls the page, so they would never reach the runtime cache and an
 * offline start would show raw translation keys. Every other lazy route chunk is cached on first use
 * by the worker's cache-first `/assets/` route.
 *
 * Resolved from the build's own chunk graph (`dist/.vite/manifest.json`), never from hashes.
 * Pure string/object handling: imported by `vite.config.ts` (Node) as a `manifestTransforms` step.
 */

/** Source modules whose chunks (and static imports) the first paint needs, besides the entry. */
export const START_ROUTE_SOURCES: readonly string[] = ['src/pages/DashboardPage.tsx', 'src/pages/auth/LoginPage.tsx'];

/** The code-split translation bundles: `src/i18n/locales/<lang>/<namespace>.json`, every language. */
export const LOCALE_BUNDLE_SOURCE = /^src\/i18n\/locales\/[a-z]{2}\/[A-Za-z0-9_-]+\.json$/;

/** One chunk of Vite's build manifest (the fields this reads). */
export interface ViteManifestChunk {
  file: string;
  imports?: string[];
  css?: string[];
}

/**
 * The files the first paint needs from the build manifest: every locale bundle chunk and every start
 * route chunk, each with its static imports (transitively) and stylesheets. Missing sources are
 * reported, so a renamed start route fails the build instead of silently dropping out.
 */
export function firstPaintFiles(
  manifest: Record<string, ViteManifestChunk>,
  startSources: readonly string[] = START_ROUTE_SOURCES,
): { files: Set<string>; missing: string[] } {
  const files = new Set<string>();
  const seen = new Set<string>();
  const visit = (key: string) => {
    if (seen.has(key)) return;
    seen.add(key);
    const chunk = manifest[key];
    if (!chunk) return;
    files.add(chunk.file);
    chunk.css?.forEach((css) => files.add(css));
    chunk.imports?.forEach(visit);
  };
  const localeSources = Object.keys(manifest).filter((key) => LOCALE_BUNDLE_SOURCE.test(key));
  const missing = startSources.filter((source) => !manifest[source]);
  if (localeSources.length === 0) missing.push('src/i18n/locales/*/*.json');
  [...localeSources, ...startSources].forEach(visit);
  return { files, missing };
}

/** The dist-relative files `index.html` loads eagerly (module script, modulepreload, stylesheet). */
export function appShellFiles(indexHtml: string): Set<string> {
  const files = new Set<string>(['index.html']);
  const patterns = [
    /<script[^>]+type="module"[^>]+src="([^"]+)"/g,
    /<link[^>]+rel="modulepreload"[^>]+href="([^"]+)"/g,
    /<link[^>]+rel="stylesheet"[^>]+href="([^"]+)"/g,
  ];
  for (const pattern of patterns) {
    for (const match of indexHtml.matchAll(pattern)) files.add(match[1].replace(/^\//, ''));
  }
  return files;
}

/** Whether one precache-manifest URL belongs to the app shell. */
export function isAppShellEntry(url: string, shell: ReadonlySet<string>): boolean {
  return shell.has(url) || url === 'manifest.json' || /^icons\/[^/]+\.png$/.test(url);
}
