import { describe, expect, it } from 'vitest';

/**
 * #2159 — no third-party tracker SDK may load in the browser outside the
 * consent gate (UI-NFR-013 CI-001/CI-002).
 *
 * These are regression fences, not the proof of the gate: the proof is the
 * behaviour in `observability/errorTracking.test.ts`. The fences keep a second
 * tracker or a bypassing import from appearing without anyone noticing.
 *
 * The defect this guards against was not a wrong gate but a *missing* one:
 * `initErrorTracking` loaded Sentry on a DSN alone and nothing read the consent
 * banner. The behavioural tests in `observability/errorTracking.test.ts` pin the
 * gate of the one SDK that exists; this guard pins that there is no second one.
 *
 * The predicate is a string-literal match, not an import parse, so every way to
 * pull a module in is covered by one rule: `import … from`, side-effect
 * `import '…'`, `import('…')`, template-literal `import(\`…\`)`, `export * from`
 * and `require`. Script-tag and CDN loading is covered by matching the known
 * tracker hosts in the same sources plus `index.html` and `public/`. A new
 * tracker *dependency* is caught at the manifest, before any code imports it.
 *
 * Known limit: an SDK loaded from a host not in {@link TRACKER_HOSTS} through a
 * runtime-built URL. The manifest check closes the npm route; a hand-rolled
 * beacon is a code-review matter, not a pattern.
 */

/** Package-name shapes of browser tracking / analytics / error-reporting SDKs. */
const TRACKER_PACKAGE =
  /^(?:@sentry(?:-internal)?\/|@posthog\/|posthog-js$|mixpanel|@amplitude\/|amplitude-js$|@datadog\/browser|logrocket|@bugsnag\/|rollbar$|@newrelic\/|@honeybadger-io\/|trackjs$|@elastic\/apm-rum|@grafana\/faro|react-ga4?$|react-gtm|@analytics\/|analytics$|plausible|@vercel\/(?:analytics|speed-insights)|hotjar|@hotjar\/|matomo|@microsoft\/applicationinsights|@segment\/|@highlight-run\/|@openreplay\/|@fullstory\/|smartlook|@growthbook\/|@statsig\/|launchdarkly)/;

/** Hosts a tracker is loaded from or reports to when wired in as a script tag. */
const TRACKER_HOSTS =
  /\b(?:sentry-cdn\.com|ingest\.sentry\.io|googletagmanager\.com|google-analytics\.com|plausible\.io|static\.hotjar\.com|cdn\.mxpnl\.com|cdn\.segment\.com|cdn\.logrocket|js\.datadoghq|eu\.posthog\.com|us\.posthog\.com|matomo\.cloud|app\.glitchtip\.com)\b/;

/** The one module permitted to load a tracker; its gate is tested behaviourally. */
const GATED_LOADER = '/src/observability/errorTracking.ts';

/** Tracker dependencies the manifest may carry; adding one means adding its gate here. */
const KNOWN_TRACKER_DEPENDENCIES = ['@sentry/react'];

const APP_SOURCES = import.meta.glob(
  ['/src/**/*.{ts,tsx,js,jsx,mjs}', '!/src/test/**', '!/src/**/*.test.{ts,tsx,js,jsx}'],
  { query: '?raw', import: 'default', eager: true },
) as Record<string, string>;

const SHELL_SOURCES = import.meta.glob(['/index.html', '/public/**/*.js', '/public/**/*.html'], {
  query: '?raw',
  import: 'default',
  eager: true,
}) as Record<string, string>;

const MANIFEST = Object.values(
  import.meta.glob('/package.json', { query: '?raw', import: 'default', eager: true }) as Record<
    string,
    string
  >,
)[0]!;

/** Every quoted module specifier in a source, whatever syntax carries it. */
function quotedSpecifiers(source: string): string[] {
  return [...source.matchAll(/['"`]([@\w][\w@./-]*)['"`]/g)].map((m) => m[1]!);
}

/**
 * Static *value* imports/re-exports of a tracker package, matched on the whole
 * source so a multi-line import clause is seen too. `import type` is erased at
 * build time and excluded; `typeof import('…')` is not an import statement.
 */
function staticTrackerImports(source: string): string[] {
  const statements =
    /^\s*(?:import|export)\b(?!\s+type\b)[^;]*?\bfrom\s*['"]([^'"]+)['"]|^\s*import\s*['"]([^'"]+)['"]/gm;
  return [...source.matchAll(statements)]
    .map((m) => (m[1] ?? m[2])!)
    .filter((spec) => TRACKER_PACKAGE.test(spec));
}

/** Runtime `import('…')` of a tracker package (not the type-level `typeof import`). */
function dynamicTrackerImports(source: string): string[] {
  return [...source.matchAll(/(?<!typeof\s+)\bimport\s*\(\s*['"`]([^'"`]+)['"`]\s*\)/g)]
    .map((m) => m[1]!)
    .filter((spec) => TRACKER_PACKAGE.test(spec));
}

/**
 * The condition text guarding each call of `name(`: everything between the
 * previous statement boundary (`;`, `{`, `}`) and the call. Whitespace- and
 * line-break-tolerant, so a reformat does not break the fence.
 */
function guardsOfCalls(source: string, name: string): string[] {
  const calls = [...source.matchAll(new RegExp(`\\b${name}\\s*\\(`, 'g'))].filter(
    (m) => !/function\s+$/.test(source.slice(Math.max(0, m.index - 20), m.index)),
  );
  return calls.map((m) => {
    const before = source.slice(0, m.index);
    const boundary = Math.max(
      before.lastIndexOf(';'),
      before.lastIndexOf('{'),
      before.lastIndexOf('}'),
    );
    return before.slice(boundary + 1);
  });
}

function trackerReferences(source: string): string[] {
  const packages = quotedSpecifiers(source).filter((spec) => TRACKER_PACKAGE.test(spec));
  const hosts = [...source.matchAll(new RegExp(TRACKER_HOSTS.source, 'g'))].map((m) => m[0]);
  return [...packages, ...hosts];
}

describe('tracker SDKs stay behind the consent gate (#2159)', () => {
  it('reads a non-trivial source set (the glob is not silently empty)', () => {
    expect(Object.keys(APP_SOURCES).length).toBeGreaterThan(100);
    expect(Object.keys(APP_SOURCES)).toContain(GATED_LOADER);
    expect(Object.keys(SHELL_SOURCES)).toContain('/index.html');
  });

  it('the predicate recognises every loading syntax it claims to', () => {
    const writings = [
      "import * as Sentry from '@sentry/react';",
      "import '@sentry/browser';",
      "const m = await import('posthog-js');",
      'const m = await import(`@datadog/browser-rum`);',
      "export * from '@grafana/faro-web-sdk';",
      "require('logrocket')",
      '<script src="https://www.googletagmanager.com/gtag/js"></script>',
    ];
    for (const writing of writings) {
      expect(trackerReferences(writing), writing).not.toEqual([]);
    }
    expect(trackerReferences("import { useState } from 'react';")).toEqual([]);
  });

  it('only the gated loader references a tracker SDK', () => {
    const offenders = Object.entries({ ...APP_SOURCES, ...SHELL_SOURCES })
      .filter(([path]) => path !== GATED_LOADER)
      .map(([path, source]) => [path, trackerReferences(source)] as const)
      .filter(([, refs]) => refs.length > 0);
    expect(offenders).toEqual([]);
  });

  it('the static-import predicate sees multi-line clauses and skips type-only ones', () => {
    expect(staticTrackerImports('import {\n  init,\n} from "@sentry/react";')).toEqual([
      '@sentry/react',
    ]);
    expect(staticTrackerImports("import '@sentry/browser';")).toEqual(['@sentry/browser']);
    expect(staticTrackerImports("export * from '@sentry/react';")).toEqual(['@sentry/react']);
    expect(staticTrackerImports("import type { Event } from '@sentry/react';")).toEqual([]);
    expect(staticTrackerImports("type M = typeof import('@sentry/react');")).toEqual([]);
    expect(dynamicTrackerImports("type M = typeof import('@sentry/react');")).toEqual([]);
    expect(dynamicTrackerImports("await import(\n  '@sentry/react'\n)")).toEqual(['@sentry/react']);
  });

  it('no app source imports a tracker statically', () => {
    const offenders = Object.entries(APP_SOURCES)
      .map(([path, source]) => [path, staticTrackerImports(source)] as const)
      .filter(([, specs]) => specs.length > 0);
    expect(offenders).toEqual([]);
  });

  it('the gated loader has exactly one runtime import of the SDK', () => {
    expect(dynamicTrackerImports(APP_SOURCES[GATED_LOADER]!)).toEqual(['@sentry/react']);
  });

  it('the gated loader starts the SDK only behind the consent check', () => {
    const source = APP_SOURCES[GATED_LOADER]!;
    const guards = guardsOfCalls(source, 'startErrorTracking');
    expect(guards).toHaveLength(1);
    expect(guards[0]).toMatch(/\bif\s*\(\s*trackingPermitted\s*\(\s*\)\s*\)\s*return\s*$/);
    // …and the predicate is the consent read, minus Light mode.
    const predicate = /function\s+trackingPermitted\s*\(\s*\)[^{]*\{([^}]*)\}/.exec(source)?.[1];
    expect(predicate).toMatch(/!\s*isLightMode\s*&&\s*hasConsent\(\s*['"]error_tracking['"]\s*\)/);
  });

  it('the manifest carries no tracker dependency without a gate', () => {
    const manifest = JSON.parse(MANIFEST) as Record<string, Record<string, string> | undefined>;
    const declared = Object.keys({
      ...manifest.dependencies,
      ...manifest.devDependencies,
      ...manifest.peerDependencies,
      ...manifest.optionalDependencies,
    });
    expect(declared.filter((name) => TRACKER_PACKAGE.test(name))).toEqual(
      KNOWN_TRACKER_DEPENDENCIES,
    );
  });
});
