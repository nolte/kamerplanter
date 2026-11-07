/**
 * What the service worker precaches (REQ-053 WP 9.1, #2741, review finding 8): the app shell only —
 * `index.html`, the entry chunk and every chunk/stylesheet `index.html` loads eagerly (the same set
 * the bundle budget counts as "initial"), the icons and the manifest. Lazy route chunks are NOT
 * precached; the worker's cache-first `/assets/` route keeps each one after its first use, so a
 * first visit no longer downloads every route of the app.
 *
 * Pure string handling: imported by `vite.config.ts` (Node) as a Workbox `manifestTransforms` step.
 */

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
