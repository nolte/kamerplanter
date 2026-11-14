import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import type { InternalAxiosRequestConfig } from 'axios';
import { AxiosHeaders } from 'axios';
import { setActiveTenantSlug } from '@/api/client';
import { listSites, getSite } from '@/api/endpoints/sites';
import { bypassHttpCacheForOfflineReads } from '@/api/offlineReadRequest';
import { getGardenPlan } from '@/features/gardenPlanner/api/gardenPlan';
import { getBedSummary } from '@/features/gardenPlanner/bed/bedApi';

/**
 * SEC-001 (REQ-053 §32.6 Pkt. 13, #2759): the three allowlisted reads answer `Cache-Control: private, no-cache`,
 * which lets the browser's HTTP disk cache store them - a cache no logout can empty from script. Every fetch of them
 * runs with the request cache mode `no-store`: the page's own request (no controlling worker) and the worker's
 * network fetch. Pinned through the production callers and the real tenant client, with `fetch` as the only double.
 */

/** The cache mode a captured `fetch(input, init)` call runs with. */
function cacheModeOf(call: unknown[]): string | undefined {
  const [input, init] = call as [RequestInfo, RequestInit | undefined];
  return init?.cache ?? (input instanceof Request ? input.cache : undefined);
}

function urlOf(call: unknown[]): string {
  const [input] = call as [RequestInfo];
  return typeof input === 'string' ? input : input instanceof Request ? input.url : String(input);
}

describe('the page requests the three offline reads past the HTTP cache', () => {
  let fetchMock: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    setActiveTenantSlug('garten-a');
    fetchMock = vi.fn(
      async () =>
        new Response('[]', { status: 200, headers: { 'content-type': 'application/json' } }),
    );
    vi.stubGlobal('fetch', fetchMock);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    setActiveTenantSlug(null);
  });

  it.each([
    ['sites', () => listSites(), '/api/v1/t/garten-a/sites'],
    ['plan', () => getGardenPlan('site_1'), '/api/v1/t/garten-a/sites/site_1/plan'],
    ['summary', () => getBedSummary('loc_1'), '/api/v1/t/garten-a/locations/loc_1/summary'],
  ])('%s goes through fetch with cache mode no-store', async (_name, call, path) => {
    await call();
    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(new URL(urlOf(fetchMock.mock.calls[0])).pathname).toBe(path);
    expect(cacheModeOf(fetchMock.mock.calls[0])).toBe('no-store');
  });
});

describe('only the allowlisted reads are switched (the interceptor itself)', () => {
  const config = (method: string, url: string): InternalAxiosRequestConfig =>
    ({ method, url, baseURL: '/api/v1', headers: new AxiosHeaders() }) as InternalAxiosRequestConfig;

  it('leaves another read, a write and an unprefixed path alone', () => {
    for (const [method, url] of [
      ['get', '/t/garten-a/sites/site_1'],
      ['post', '/t/garten-a/sites'],
      ['get', '/t/garten-a/sites/site_1/plan/export'],
      ['get', '/sites'],
    ] as const) {
      const out = bypassHttpCacheForOfflineReads(config(method, url));
      expect(out.adapter).toBeUndefined();
      expect(out.fetchOptions).toBeUndefined();
    }
  });

  it('keeps the query out of the path test', () => {
    const out = bypassHttpCacheForOfflineReads(config('get', '/t/garten-a/sites/site_1/plan?include=plants'));
    expect(out.fetchOptions).toMatchObject({ cache: 'no-store' });
  });

  it('a non-allowlisted read keeps the default adapter (no fetch involved)', async () => {
    const fetchMock = vi.fn();
    vi.stubGlobal('fetch', fetchMock);
    setActiveTenantSlug('garten-a');
    try {
      await getSite('site_1').catch(() => undefined);
    } finally {
      vi.unstubAllGlobals();
      setActiveTenantSlug(null);
    }
    expect(fetchMock).not.toHaveBeenCalled();
  });
});

describe('the worker fetches the allowlisted reads with cache mode no-store', () => {
  const source = readFileSync(join(process.cwd(), 'src/sw.ts'), 'utf8');

  it('gives the namespaced NetworkFirst and the fallback NetworkOnly the no-store fetch options', () => {
    const strategy = source.slice(source.indexOf('function apiStrategy('), source.indexOf('const networkOnly ='));
    expect(strategy).toMatch(/new NetworkFirst\(\{[\s\S]*fetchOptions: OFFLINE_READ_FETCH_OPTIONS/);
    expect(source).toMatch(
      /const offlineReadNetworkOnly = new NetworkOnly\(\{ fetchOptions: OFFLINE_READ_FETCH_OPTIONS \}\)/,
    );
    expect(source).toMatch(/if \(killed \|\| !cacheName\) return offlineReadNetworkOnly\.handle\(options\)/);
  });
});
