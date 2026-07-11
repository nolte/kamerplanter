#!/usr/bin/env node
// UI-NFR-003 R-013/R-014/R-015/R-028 — bundle-size budget gate.
//
// Fails the build (non-zero exit) when the initial payload of the app grows
// past the configured gzip budgets. "Initial JS" is the entry module plus every
// chunk the browser eagerly loads for it (the `<script type="module">` and all
// `<link rel="modulepreload">` hrefs Vite injects into `dist/index.html`).
// Route- and interaction-level chunks are dynamically imported and therefore
// excluded — exactly the payload that decides First Contentful Paint.
//
// The `/dashboard` route chunk gets its own budget (R-028): the most-visited
// page must not regress even though it is lazily loaded.
//
// Run: `node scripts/check-bundle-budget.mjs` (after `vite build`).

import { gzipSync } from 'node:zlib';
import { readFileSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const frontendRoot = join(dirname(fileURLToPath(import.meta.url)), '..');
const distDir = join(frontendRoot, 'dist');
const budgetPath = join(frontendRoot, 'bundle-budget.json');

/** Gzip-compressed size of a dist-relative asset, in bytes. */
function gzipBytes(assetPath) {
  const raw = readFileSync(join(distDir, assetPath));
  return gzipSync(raw, { level: 9 }).length;
}

/** Extract the asset hrefs referenced from `dist/index.html` by tag type. */
function parseIndexHtml() {
  const html = readFileSync(join(distDir, 'index.html'), 'utf8');
  const js = new Set();
  const css = new Set();

  const scriptRe = /<script[^>]+type="module"[^>]+src="([^"]+)"/g;
  const preloadRe = /<link[^>]+rel="modulepreload"[^>]+href="([^"]+)"/g;
  const styleRe = /<link[^>]+rel="stylesheet"[^>]+href="([^"]+)"/g;

  for (const re of [scriptRe, preloadRe]) {
    let m;
    while ((m = re.exec(html)) !== null) js.add(m[1].replace(/^\//, ''));
  }
  let m;
  while ((m = styleRe.exec(html)) !== null) css.add(m[1].replace(/^\//, ''));

  return { js: [...js], css: [...css] };
}

/** Resolve the emitted chunk file for a source module via the Vite manifest. */
function resolveManifestChunk(sourceKey) {
  // Vite 8 / rolldown emits the manifest at dist/.vite/manifest.json.
  const manifest = JSON.parse(
    readFileSync(join(distDir, '.vite', 'manifest.json'), 'utf8'),
  );
  const entry = manifest[sourceKey];
  if (!entry) return null;
  const files = [entry.file];
  for (const cssFile of entry.css ?? []) files.push(cssFile);
  return files;
}

export function kib(bytes) {
  return `${(bytes / 1024).toFixed(1)} KB`;
}

/**
 * Pure budget evaluation — no I/O, so it can be unit-tested. Takes the measured
 * gzip byte counts plus the parsed budget config and returns the per-check
 * results and an overall `failed` flag (true iff an `error`-severity check is
 * over budget).
 *
 * @param {{ initialJsBytes: number, initialCssBytes: number,
 *   dashboardBytes: number | null, budget: object }} input
 */
export function evaluateBudget({ initialJsBytes, initialCssBytes, dashboardBytes, budget }) {
  const checks = [
    {
      label: 'Initial JS (gzip)',
      requirement: 'R-013/R-015',
      actual: initialJsBytes,
      budget: budget.initialJsGzipKb * 1024,
      severity: 'error',
    },
    {
      label: 'Initial CSS (gzip)',
      requirement: 'R-014',
      actual: initialCssBytes,
      budget: budget.initialCssGzipKb * 1024,
      severity: budget.cssSeverity ?? 'error',
    },
  ];

  if (dashboardBytes !== null && dashboardBytes !== undefined) {
    checks.push({
      label: '/dashboard route chunk (gzip)',
      requirement: 'R-028',
      actual: dashboardBytes,
      budget: budget.routeChunks.dashboard.gzipKb * 1024,
      severity: 'error',
    });
  }

  let failed = false;
  for (const c of checks) {
    c.over = c.actual > c.budget;
    c.status = c.over ? (c.severity === 'error' ? 'FAIL' : 'WARN') : 'PASS';
    if (c.over && c.severity === 'error') failed = true;
  }
  return { checks, failed };
}

function main() {
  const budget = JSON.parse(readFileSync(budgetPath, 'utf8'));
  const { js, css } = parseIndexHtml();

  const initialJsBytes = js.reduce((sum, f) => sum + gzipBytes(f), 0);
  const initialCssBytes = css.reduce((sum, f) => sum + gzipBytes(f), 0);

  const dashboardFiles = resolveManifestChunk(budget.routeChunks.dashboard.source);
  const dashboardBytes = dashboardFiles
    ? dashboardFiles.reduce((sum, f) => sum + gzipBytes(f), 0)
    : null;

  const { checks, failed } = evaluateBudget({
    initialJsBytes,
    initialCssBytes,
    dashboardBytes,
    budget,
  });

  console.log('UI-NFR-003 bundle-size budget report');
  console.log('====================================');
  for (const c of checks) {
    const pct = ((c.actual / c.budget) * 100).toFixed(0);
    console.log(
      `[${c.status}] ${c.label} (${c.requirement}): ${kib(c.actual)} / ${kib(c.budget)} (${pct}%)`,
    );
  }
  console.log('====================================');
  console.log(`Initial JS chunks counted: ${js.length}`);

  if (failed) {
    console.error(
      '\nBundle budget exceeded. Reduce the initial payload (code-split, ' +
        'lazy-load, tree-shake) or, if the growth is justified, raise the ' +
        'budget in bundle-budget.json and document the measured value.',
    );
    process.exit(1);
  }
  console.log('\nAll bundle budgets within limits.');
}

// Only run the CLI when invoked directly (not when imported by unit tests).
if (process.argv[1] && process.argv[1] === fileURLToPath(import.meta.url)) {
  main();
}
