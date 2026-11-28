import { describe, expect, it } from 'vitest';
import routesSource from '@/routes/AppRoutes.tsx?raw';
import { FRONTEND_PARAM_ROUTES, maskPath } from '@/observability/errorTrackingScrub';

/**
 * UI-NFR-013 v1.4 CI-006 (#3025 F-6) — every parameter of a frontend route is
 * masked before an error report leaves the browser.
 *
 * The masking matches the route patterns in `FRONTEND_PARAM_ROUTES`. A new route
 * with a parameter in `AppRoutes.tsx` that is missing there would ship its key
 * (or token) whenever it has no digit — so this reads the routes themselves.
 * Every `path="…"` with a parameter counts — a commented-out one too, which only
 * errs on the safe side (a pattern masked that no route uses).
 *
 * Exempt: `settings/:group?` — a fixed set of tab names, no record or person.
 */
const EXEMPT = new Set(['settings/:group?']);

function parameterisedRoutes(source: string): string[] {
  const found = new Set<string>();
  for (const match of source.matchAll(/\bpath="([^"]*:[^"]*)"/g)) found.add(match[1]!);
  return [...found].filter((route) => !EXEMPT.has(route));
}

/** A realistic value without digits — the shape the generic key rule would miss. */
function fill(route: string): string {
  return `/${route.replace(/:[A-Za-z]+\??/g, 'hochbeet-sued')}`;
}

describe('the tracker masks every frontend route parameter (CI-006)', () => {
  const routes = parameterisedRoutes(routesSource);

  it('finds the routes (non-vacuity)', () => {
    expect(routes.length).toBeGreaterThan(20);
    expect(routes).toContain('pflanzen/plant-instances/:key');
  });

  it.each(parameterisedRoutes(routesSource))('%s', (route) => {
    expect(FRONTEND_PARAM_ROUTES).toContain(route);
    const masked = maskPath(fill(route));
    expect(masked).not.toContain('hochbeet-sued');
    expect(masked).toBe(`/${route}`);
  });

  it('the detector finds every path attribute with a parameter', () => {
    expect(parameterisedRoutes('// path="x/:key"\n<Route path="a/:key" />')).toEqual([
      'x/:key',
      'a/:key',
    ]);
  });
});
