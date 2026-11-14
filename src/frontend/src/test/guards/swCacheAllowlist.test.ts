import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { describe, expect, it } from 'vitest';
import {
  API_CACHE_ALLOWLIST,
  isAllowlistedApiRequest,
  isCacheableApiResponse,
} from '@/pwa/cachePolicy';

/**
 * REQ-053 WP 9.1 (#2741), guardrail G-W9 (c): the service worker caches only `GET` answers of the
 * allowlisted tenant-scoped read paths (`…/sites`, `…/sites/{key}/plan`,
 * `…/locations/{key}/summary`) — never `/api/v1/auth/*`, `/privacy/*`, `/admin/*` or attachment
 * originals — and never an answer marked `Cache-Control: no-store`.
 *
 * The rule is the ONE predicate the worker calls (`isAllowlistedApiRequest`), so this test reaches
 * it through the same path as production. The second half pins that `src/sw.ts` routes API
 * requests through exactly that predicate and the per-client plugin; the plugin's write rules
 * (`isCacheableApiResponse`, namespace, generation) are exercised in `swApiCachePerClient.test.ts`.
 *
 * UI-NFR-012 R-057 (read allowlist, `no-store` honoured) and R-009 (the allowlisted API reads are the
 * network-first route; every other `/api/` request is network-only).
 */

const ORIGIN = 'https://kamerplanter.example';

function allowed(path: string, method = 'GET', origin = ORIGIN): boolean {
  return isAllowlistedApiRequest(method, new URL(path, origin), ORIGIN);
}

const FORBIDDEN_PATHS = [
  '/api/v1/auth/me',
  '/api/v1/auth/refresh',
  '/api/v1/auth/login',
  '/api/v1/auth',
  '/api/v1/privacy/export',
  '/api/v1/privacy/consents',
  '/api/v1/t/garden/privacy/export',
  '/api/v1/admin/platform/tenants',
  '/api/v1/t/garden/admin/members',
  '/api/v1/t/garden/attachments/att_1',
  '/api/v1/t/garden/attachments/att_1/download',
  '/api/v1/attachments/token/abc',
  '/api/v1/t/garden/sites/site_1/photos',
  '/api/v1/t/garden/locations/loc_1/photos/ph_1',
  // Near misses of the allowlist itself.
  '/api/v1/sites',
  '/api/v1/sites/site_1/plan',
  '/api/v1/t/garden/sites/site_1',
  '/api/v1/t/garden/sites/site_1/plan/render.svg',
  '/api/v1/t/garden/sites/site_1/plan/export',
  '/api/v1/t/garden/locations/loc_1',
  '/api/v1/t/garden/locations/loc_1/summary/extra',
  '/api/v1/t/garden/sites/site_1/plan/../../../../auth/me',
  '/api/v1/t/garden/admin/sites',
  // Fail closed: a garden whose slug is literally `privacy` or `admin` loses offline caching
  // rather than the forbidden-segment rule growing an exception.
  '/api/v1/t/privacy/sites',
  '/api/v1/t/admin/sites',
];

describe('service worker cache allowlist (G-W9 c)', () => {
  it('admits exactly the three allowlisted tenant-scoped reads', () => {
    expect(allowed('/api/v1/t/garden/sites')).toBe(true);
    expect(allowed('/api/v1/t/garden/sites/site_1/plan')).toBe(true);
    expect(allowed('/api/v1/t/garden/sites/site_1/plan?include=plants,tasks')).toBe(true);
    expect(allowed('/api/v1/t/garden/locations/loc_1/summary')).toBe(true);
  });

  it.each(FORBIDDEN_PATHS)('never caches %s', (path) => {
    expect(allowed(path)).toBe(false);
  });

  it.each(['POST', 'PUT', 'PATCH', 'DELETE', 'HEAD'])('never caches a %s', (method) => {
    expect(allowed('/api/v1/t/garden/sites/site_1/plan', method)).toBe(false);
  });

  it('never caches a cross-origin answer, even on an allowlisted path', () => {
    expect(allowed('https://evil.example/api/v1/t/garden/sites', 'GET', 'https://evil.example')).toBe(false);
  });

  it('keeps every allowlist entry anchored and tenant-scoped', () => {
    expect(API_CACHE_ALLOWLIST.length).toBe(3);
    for (const pattern of API_CACHE_ALLOWLIST) {
      expect(pattern.source.startsWith('^\\/api\\/v1\\/t\\/') || pattern.source.startsWith('^/api/v1/t/')).toBe(
        true,
      );
      expect(pattern.source.endsWith('$')).toBe(true);
    }
  });

  it('respects Cache-Control: no-store — the backend default outside the three reads (MT-044)', () => {
    const json = (cacheControl: string | null) => ({
      status: 200,
      type: 'basic',
      headers: new Headers({
        'content-type': 'application/json',
        ...(cacheControl ? { 'cache-control': cacheControl } : {}),
      }),
    });
    expect(isCacheableApiResponse(json('no-store'))).toBe(false);
    expect(isCacheableApiResponse(json('private, no-store'))).toBe(false);
    expect(isCacheableApiResponse(json('NO-STORE'))).toBe(false);
    expect(isCacheableApiResponse(json('private, no-cache'))).toBe(true);
    expect(isCacheableApiResponse(json(null))).toBe(true);
  });

  it('writes only a plain 200 JSON answer', () => {
    const response = (status: number, type: string, contentType: string) => ({
      status,
      type,
      headers: new Headers({ 'content-type': contentType }),
    });
    expect(isCacheableApiResponse(response(200, 'basic', 'application/json'))).toBe(true);
    expect(isCacheableApiResponse(response(206, 'basic', 'application/json'))).toBe(false);
    expect(isCacheableApiResponse(response(401, 'basic', 'application/json'))).toBe(false);
    expect(isCacheableApiResponse(response(200, 'opaque', 'application/json'))).toBe(false);
    expect(isCacheableApiResponse(response(200, 'basic', 'text/html'))).toBe(false);
    expect(
      isCacheableApiResponse({
        status: 200,
        type: 'basic',
        headers: new Headers({ 'content-type': 'application/json', 'set-cookie': 'a=b' }),
      }),
    ).toBe(false);
  });
});

describe('src/sw.ts applies the allowlist on its only API caching path', () => {
  const source = readFileSync(join(process.cwd(), 'src/sw.ts'), 'utf8');

  it('routes API requests through isAllowlistedApiRequest and caches nothing else under /api/', () => {
    // Two `/api/` routes: the allowlisted network-first one and the network-only catch-all.
    expect(source.match(/startsWith\('\/api\/'\)/g)?.length).toBe(2);
    expect(source).toMatch(/startsWith\('\/api\/'\)\s*&&\s*isAllowlistedApiRequest\(/);
    expect(source).toMatch(/new Route\(\(\{ url \}\) => url\.pathname\.startsWith\('\/api\/'\), networkOnly\)/);
  });

  it("answers an allowlisted read only from the requesting client's namespace", () => {
    const route = source.slice(source.indexOf('isAllowlistedApiRequest(request.method'), source.indexOf('router.registerRoute(new Route(({ url }) =>'));
    expect(route).toMatch(/registry\.forClient\(clientIdOf\(options\.event\)\)/);
    expect(route).toMatch(/if \(killed \|\| !cacheName\) return offlineReadNetworkOnly\.handle\(options\)/);
    expect(source).toMatch(/plugins: \[createApiCachePlugin\(cacheName, apiContext\) as WorkboxPlugin\]/);
  });

  it('keeps the static cache-first route off /api/', () => {
    const staticRoute = source.slice(source.indexOf("url.pathname.startsWith('/assets/')") - 200);
    expect(staticRoute).toMatch(/startsWith\('\/assets\/'\) \|\| url\.pathname\.startsWith\('\/icons\/'\)/);
    expect(source).toMatch(/denylist: \[\/\^\\\/api\\\/\//);
  });
});

/**
 * REQ-053 §32.6 Pkt. 13 (#2759): the backend answers exactly the three allowlisted reads with `Cache-Control:
 * private, no-cache` (`OFFLINE_READ_ROUTES` in `src/backend/app/common/cache_control.py`) and every other `/api/v1/`
 * answer with `no-store`. The worker's allowlist and that route list must name the same three paths: an allowlisted
 * path the backend still answers `no-store` is never stored (dead offline cache), a `private, no-cache` route outside
 * the allowlist is network-only.
 */
describe('the allowlist matches the backend routes that answer private, no-cache (#2759)', () => {
  const backend = readFileSync(join(process.cwd(), '../backend/app/common/cache_control.py'), 'utf8');
  const block = backend.slice(backend.indexOf('OFFLINE_READ_ROUTES'), backend.indexOf('def allow_offline_read_cache'));
  const routes = [...block.matchAll(/\(\s*"(\w+)"\s*,\s*"([^"]+)"\s*\)/g)].map(([, method, path]) => ({
    method,
    path,
  }));
  /** A concrete request path of a route template: every `{param}` becomes a plain key. */
  const sample = (template: string) => template.replace(/\{[^}]+\}/g, 'key_1');

  it('reads the three backend routes (the measuring tool finds what it should)', () => {
    expect(routes).toHaveLength(3);
    expect(routes.every((route) => route.method === 'GET')).toBe(true);
  });

  it.each(['sites', 'sites/{key}/plan', 'locations/{key}/summary'])('the backend names …/%s', (tail) => {
    expect(routes.map((route) => route.path)).toContain(`/api/v1/t/{tenant_slug}/${tail}`);
  });

  it('caches every backend private, no-cache route, and an answer with that header is stored', () => {
    for (const route of routes) expect(allowed(sample(route.path), route.method)).toBe(true);
    const answer = {
      status: 200,
      type: 'basic',
      headers: new Headers({ 'content-type': 'application/json', 'cache-control': 'private, no-cache' }),
    };
    expect(isCacheableApiResponse(answer)).toBe(true);
  });

  it('allowlists no path the backend answers no-store', () => {
    for (const pattern of API_CACHE_ALLOWLIST) {
      expect(routes.some((route) => pattern.test(sample(route.path)))).toBe(true);
    }
  });
});
