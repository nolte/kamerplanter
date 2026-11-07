import 'fake-indexeddb/auto';
import { AxiosError, AxiosHeaders } from 'axios';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { ApiError } from '@/api/errors';
import {
  OfflineCacheMissError,
  PLAN_CACHE_TTL_MS,
  bedListEntry,
  planEntry,
  readCached,
  readThrough,
  scopeFromState,
  siteCacheKey,
  siteListEntry,
  writeCached,
  type CacheScope,
} from './planCache';

/**
 * REQ-053 WP 9.2 (#2742), GP-UX-024 part 1 — the plan cache against a real IndexedDB
 * (`fake-indexeddb`): the 15-minute TTL (R-012), the key per user AND tenant (G-W9 a, no cross
 * read), the miss, and the read-through rule (network first, cache only without a connection).
 */

const ALICE_A: CacheScope = { userKey: 'alice', tenantKey: 'tenant_a' };
const ALICE_B: CacheScope = { userKey: 'alice', tenantKey: 'tenant_b' };
const BOB_A: CacheScope = { userKey: 'bob', tenantKey: 'tenant_a' };
const T0 = Date.UTC(2026, 10, 7, 12, 0, 0);
const PLAN = { site: { key: 'site_1', name: 'Garten' }, locations: [] };

function networkError(): AxiosError {
  return new AxiosError('Network Error', 'ERR_NETWORK');
}

function setOnline(value: boolean) {
  Object.defineProperty(navigator, 'onLine', { configurable: true, get: () => value });
}

async function wipe() {
  const { planCacheDatabase } = await import('./db');
  const db = planCacheDatabase();
  await Promise.all([db.plans.clear(), db.bedLists.clear(), db.siteLists.clear()]);
}

beforeEach(async () => {
  setOnline(true);
  await wipe();
});

afterEach(() => {
  setOnline(true);
});

describe('key', () => {
  it('is {user_key}:{tenant_key}:{site_key}', () => {
    expect(siteCacheKey(ALICE_A, 'site_1')).toBe('alice:tenant_a:site_1');
  });

  it('encodes a colon inside a key so two scopes cannot collide', () => {
    const left = siteCacheKey({ userKey: 'a:b', tenantKey: 'c' }, 's');
    const right = siteCacheKey({ userKey: 'a', tenantKey: 'b:c' }, 's');
    expect(left).not.toBe(right);
  });

  it('takes the scope from the signed-in user and the active tenant only', () => {
    expect(scopeFromState({ auth: { user: { key: 'alice' } }, tenants: { activeTenant: { key: 'tenant_a' } } })).toEqual(
      ALICE_A,
    );
    expect(scopeFromState({ auth: { user: null }, tenants: { activeTenant: { key: 'tenant_a' } } })).toBeNull();
    expect(scopeFromState({ auth: { user: { key: 'alice' } }, tenants: { activeTenant: null } })).toBeNull();
  });
});

describe('scope per user and tenant (no cross read)', () => {
  it('returns a plan only to the user and tenant that loaded it', async () => {
    await writeCached(planEntry(ALICE_A, 'site_1'), PLAN, T0);
    expect(await readCached(planEntry(ALICE_A, 'site_1'), T0 + 1000)).toEqual({ data: PLAN, cachedAt: T0 });
    expect(await readCached(planEntry(ALICE_B, 'site_1'), T0 + 1000)).toBeNull();
    expect(await readCached(planEntry(BOB_A, 'site_1'), T0 + 1000)).toBeNull();
  });

  it('keeps the site list and the bed list per scope as well', async () => {
    await writeCached(siteListEntry(ALICE_A), [{ key: 'site_1' }], T0);
    await writeCached(bedListEntry(ALICE_A, 'site_1'), [{ key: 'bed_1' }], T0);
    expect(await readCached(siteListEntry(BOB_A), T0)).toBeNull();
    expect(await readCached(bedListEntry(ALICE_B, 'site_1'), T0)).toBeNull();
    expect((await readCached(siteListEntry(ALICE_A), T0))?.data).toEqual([{ key: 'site_1' }]);
  });

  it('refuses a record whose stored owner does not match its key', async () => {
    const { planCacheDatabase } = await import('./db');
    await planCacheDatabase().plans.put({
      key: siteCacheKey(ALICE_A, 'site_1'),
      userKey: 'bob',
      tenantKey: 'tenant_a',
      cachedAt: T0,
      data: PLAN,
    });
    expect(await readCached(planEntry(ALICE_A, 'site_1'), T0)).toBeNull();
  });
});

describe('TTL 15 min (R-012)', () => {
  it('serves a record up to 15 minutes old and never an older one', async () => {
    await writeCached(planEntry(ALICE_A, 'site_1'), PLAN, T0);
    expect(await readCached(planEntry(ALICE_A, 'site_1'), T0 + PLAN_CACHE_TTL_MS)).not.toBeNull();
    expect(await readCached(planEntry(ALICE_A, 'site_1'), T0 + PLAN_CACHE_TTL_MS + 1)).toBeNull();
  });

  it('deletes expired records on the next write', async () => {
    await writeCached(planEntry(ALICE_A, 'site_1'), PLAN, T0);
    await writeCached(planEntry(ALICE_A, 'site_2'), PLAN, T0 + PLAN_CACHE_TTL_MS + 1);
    const { planCacheDatabase } = await import('./db');
    expect((await planCacheDatabase().plans.toArray()).map((record) => record.key)).toEqual([
      'alice:tenant_a:site_2',
    ]);
  });
});

describe('readThrough', () => {
  it('online: answers from the network and writes the cache', async () => {
    const fetcher = vi.fn().mockResolvedValue(PLAN);
    const result = await readThrough(planEntry(ALICE_A, 'site_1'), fetcher, () => T0);
    expect(result).toEqual({ data: PLAN, cachedAt: null });
    await vi.waitFor(async () => expect(await readCached(planEntry(ALICE_A, 'site_1'), T0)).not.toBeNull());
  });

  it('offline: answers from the cache with its time, without asking the network', async () => {
    await writeCached(planEntry(ALICE_A, 'site_1'), PLAN, T0);
    setOnline(false);
    const fetcher = vi.fn();
    const result = await readThrough(planEntry(ALICE_A, 'site_1'), fetcher, () => T0 + 60_000);
    expect(result).toEqual({ data: PLAN, cachedAt: T0 });
    expect(fetcher).not.toHaveBeenCalled();
  });

  it('offline miss: fails with OfflineCacheMissError', async () => {
    setOnline(false);
    await expect(readThrough(planEntry(ALICE_A, 'site_1'), vi.fn(), () => T0)).rejects.toBeInstanceOf(
      OfflineCacheMissError,
    );
  });

  it('offline with an expired record: a miss as well', async () => {
    await writeCached(planEntry(ALICE_A, 'site_1'), PLAN, T0);
    setOnline(false);
    await expect(
      readThrough(planEntry(ALICE_A, 'site_1'), vi.fn(), () => T0 + PLAN_CACHE_TTL_MS + 1),
    ).rejects.toBeInstanceOf(OfflineCacheMissError);
  });

  it('a request without an answer falls back to the cache', async () => {
    await writeCached(planEntry(ALICE_A, 'site_1'), PLAN, T0);
    const result = await readThrough(planEntry(ALICE_A, 'site_1'), () => Promise.reject(networkError()), () => T0);
    expect(result.cachedAt).toBe(T0);
  });

  it('a refusal of the server is never answered from the cache', async () => {
    await writeCached(planEntry(ALICE_A, 'site_1'), PLAN, T0);
    const refusal = new ApiError(
      { error_id: 'e', error_code: 'forbidden', message: 'no', details: [], path: '/', method: 'GET' } as never,
      403,
    );
    await expect(readThrough(planEntry(ALICE_A, 'site_1'), () => Promise.reject(refusal), () => T0)).rejects.toBe(
      refusal,
    );
  });

  it('without a scope nothing is cached or read', async () => {
    setOnline(false);
    const fetcher = vi.fn().mockRejectedValue(networkError());
    await expect(readThrough(null, fetcher)).rejects.toBeInstanceOf(AxiosError);
  });

  it('an axios error with an answer is a refusal, not a missing connection', async () => {
    await writeCached(planEntry(ALICE_A, 'site_1'), PLAN, T0);
    const answered = new AxiosError('Bad', 'ERR_BAD_RESPONSE', undefined, undefined, {
      status: 500,
      statusText: 'x',
      headers: {},
      config: { headers: new AxiosHeaders() },
      data: null,
    });
    await expect(readThrough(planEntry(ALICE_A, 'site_1'), () => Promise.reject(answered), () => T0)).rejects.toBe(
      answered,
    );
  });
});
