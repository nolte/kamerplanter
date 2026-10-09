import { describe, expect, it } from 'vitest';

/**
 * #2159 — no third-party tracker SDK may load in the browser outside the
 * consent gate (UI-NFR-013 CI-001/CI-002).
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
  /\b(?:sentry-cdn\.com|ingest\.sentry\.io|googletagmanager\.com|google-analytics\.com|plausible\.io|static\.hotjar\.com|cdn\.mxpnl\.com|cdn\.segment\.com|cdn\.logrocket|js\.datadoghq|eu\.posthog\.com|us\.posthog\.com|matomo\.cloud)\b/;

/** The one module permitted to load a tracker; its gate is tested behaviourally. */
const GATED_LOADER = '/src/observability/errorTracking.ts';

/** Tracker dependencies the manifest may carry; adding one means adding its gate here. */
const KNOWN_TRACKER_DEPENDENCIES = ['@sentry/react'];

const APP_SOURCES = import.meta.glob(
  ['/src/**/*.ts', '/src/**/*.tsx', '!/src/test/**', '!/src/**/*.test.ts', '!/src/**/*.test.tsx'],
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

  it('the gated loader has no static value import of the SDK', () => {
    const source = APP_SOURCES[GATED_LOADER]!;
    // `typeof import('…')` and `import type` are erased at build time; a value
    // import would put the SDK in the initial bundle and run it before consent.
    const staticImports = source
      .split('\n')
      .filter((line) => /^\s*(?:import|export)\b(?!\s+type\b)/.test(line))
      .filter((line) => trackerReferences(line).length > 0);
    expect(staticImports).toEqual([]);
    expect(source).toContain("await import('@sentry/react')");
  });

  it('the gated loader reaches the SDK only through the consent check', () => {
    const source = APP_SOURCES[GATED_LOADER]!;
    const callSites = source
      .split('\n')
      .filter(
        (line) =>
          /\bstartErrorTracking\(/.test(line) && !/function\s+startErrorTracking/.test(line),
      );
    expect(callSites).toEqual(["  if (hasConsent('error_tracking')) return startErrorTracking();"]);
  });

  it('the manifest carries no tracker dependency without a gate', () => {
    const manifest = JSON.parse(MANIFEST) as {
      dependencies?: Record<string, string>;
      optionalDependencies?: Record<string, string>;
    };
    const declared = Object.keys({
      ...manifest.dependencies,
      ...manifest.optionalDependencies,
    });
    expect(declared.filter((name) => TRACKER_PACKAGE.test(name))).toEqual(
      KNOWN_TRACKER_DEPENDENCIES,
    );
  });
});
