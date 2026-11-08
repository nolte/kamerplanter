import 'fake-indexeddb/auto';
import { AxiosError, AxiosHeaders } from 'axios';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { ApiError } from '@/api/errors';
import { emptyPlanCache, testPlanCacheDatabase } from '@/test/planCacheTestKit';
import { clearOfflineData } from '@/pwa/offlineData';
import { PLAN_CACHE_DB_NAME } from '@/pwa/storageWipe';
import { storableSheet } from '../field/useBedSheet';
import { careTask } from '../care/careTestKit';
import {
  OfflineCacheMissError,
  PLAN_CACHE_TTL_MS,
  purgeExpiredPlanCache,
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

beforeEach(async () => {
  setOnline(true);
  await emptyPlanCache();
});

afterEach(() => {
  setOnline(true);
  delete (window as { __RUNTIME_CONFIG__?: unknown }).__RUNTIME_CONFIG__;
});

async function databaseNames(): Promise<string[]> {
  return (await indexedDB.databases()).map((database) => database.name ?? '');
}

/** Delete the database as a clean page would find it: no connection, no file. */
async function deleteDatabase(): Promise<void> {
  const { resetPlanCacheForTests } = await import('./planCache');
  resetPlanCacheForTests();
  await new Promise<void>((resolve) => {
    const request = indexedDB.deleteDatabase(PLAN_CACHE_DB_NAME);
    request.onsuccess = () => resolve();
    request.onerror = () => resolve();
    request.onblocked = () => resolve();
  });
}

function settle(ms = 50): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

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
    await writeCached(siteListEntry(ALICE_A, 50), [{ key: 'site_1' }], T0);
    await writeCached(bedListEntry(ALICE_A, 'site_1'), [{ key: 'bed_1' }], T0);
    expect(await readCached(siteListEntry(BOB_A, 50), T0)).toBeNull();
    expect(await readCached(bedListEntry(ALICE_B, 'site_1'), T0)).toBeNull();
    expect((await readCached(siteListEntry(ALICE_A, 50), T0))?.data).toEqual([{ key: 'site_1' }]);
  });

  it('refuses a record whose stored owner does not match its key', async () => {
    await testPlanCacheDatabase().plans.put({
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
    expect((await testPlanCacheDatabase().plans.toArray()).map((record) => record.key)).toEqual([
      'alice:tenant_a:site_2',
    ]);
  });
});

describe('readThrough', () => {
  it('online: answers from the network and writes the cache', async () => {
    const fetcher = vi.fn().mockResolvedValue(PLAN);
    const result = await readThrough(planEntry(ALICE_A, 'site_1'), fetcher, { now: () => T0 });
    expect(result).toEqual({ data: PLAN, cachedAt: null });
    await vi.waitFor(async () => expect(await readCached(planEntry(ALICE_A, 'site_1'), T0)).not.toBeNull());
  });

  it('offline: answers from the cache with its time, without asking the network', async () => {
    await writeCached(planEntry(ALICE_A, 'site_1'), PLAN, T0);
    setOnline(false);
    const fetcher = vi.fn();
    const result = await readThrough(planEntry(ALICE_A, 'site_1'), fetcher, { now: () => T0 + 60_000 });
    expect(result).toEqual({ data: PLAN, cachedAt: T0 });
    expect(fetcher).not.toHaveBeenCalled();
  });

  it('offline miss: fails with OfflineCacheMissError', async () => {
    setOnline(false);
    await expect(readThrough(planEntry(ALICE_A, 'site_1'), vi.fn(), { now: () => T0 })).rejects.toBeInstanceOf(
      OfflineCacheMissError,
    );
  });

  it('offline with an expired record: a miss as well', async () => {
    await writeCached(planEntry(ALICE_A, 'site_1'), PLAN, T0);
    setOnline(false);
    await expect(
      readThrough(planEntry(ALICE_A, 'site_1'), vi.fn(), { now: () => T0 + PLAN_CACHE_TTL_MS + 1 }),
    ).rejects.toBeInstanceOf(OfflineCacheMissError);
  });

  it('a request without an answer falls back to the cache', async () => {
    await writeCached(planEntry(ALICE_A, 'site_1'), PLAN, T0);
    const result = await readThrough(planEntry(ALICE_A, 'site_1'), () => Promise.reject(networkError()), { now: () => T0 });
    expect(result.cachedAt).toBe(T0);
  });

  it('a refusal of the server is never answered from the cache', async () => {
    await writeCached(planEntry(ALICE_A, 'site_1'), PLAN, T0);
    const refusal = new ApiError(
      { error_id: 'e', error_code: 'forbidden', message: 'no', details: [], path: '/', method: 'GET' } as never,
      403,
    );
    await expect(readThrough(planEntry(ALICE_A, 'site_1'), () => Promise.reject(refusal), { now: () => T0 })).rejects.toBe(
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
    await expect(readThrough(planEntry(ALICE_A, 'site_1'), () => Promise.reject(answered), { now: () => T0 })).rejects.toBe(
      answered,
    );
  });
});

describe('keys per include set and page size (#2789 review C1, C7)', () => {
  it('keeps a plan read with plants apart from the plain plan', async () => {
    await writeCached(planEntry(ALICE_A, 'site_1'), { plain: true }, T0);
    await writeCached(planEntry(ALICE_A, 'site_1', ['plants']), { plants: true }, T0);
    expect((await readCached(planEntry(ALICE_A, 'site_1'), T0))?.data).toEqual({ plain: true });
    expect((await readCached(planEntry(ALICE_A, 'site_1', ['plants']), T0))?.data).toEqual({ plants: true });
  });

  it('keeps the site list per page size', async () => {
    await writeCached(siteListEntry(ALICE_A, 200), [{ key: 'many' }], T0);
    expect(await readCached(siteListEntry(ALICE_A, 50), T0)).toBeNull();
    expect(await readCached(siteListEntry(ALICE_A, 200), T0)).not.toBeNull();
  });
});

describe('kill switch (#2789 review S1, G-W9 e)', () => {
  it('reads and writes nothing and never opens the database when caching is off', async () => {
    await deleteDatabase();
    (window as { __RUNTIME_CONFIG__?: unknown }).__RUNTIME_CONFIG__ = { PWA_CACHING_ENABLED: 'false' };
    const result = await readThrough(planEntry(ALICE_A, 'site_1'), () => Promise.resolve(PLAN), { now: () => T0 });
    expect(result).toEqual({ data: PLAN, cachedAt: null });
    await writeCached(planEntry(ALICE_A, 'site_2'), PLAN, T0);
    await purgeExpiredPlanCache(T0);
    await settle();
    expect(await databaseNames()).not.toContain(PLAN_CACHE_DB_NAME);
    // Offline it is a plain network read: no cached answer is served either.
    setOnline(false);
    await expect(
      readThrough(planEntry(ALICE_A, 'site_1'), () => Promise.reject(networkError()), { now: () => T0 }),
    ).rejects.toBeInstanceOf(AxiosError);
  });
});

describe('expired records are deleted, not only skipped (#2789 review L2)', () => {
  it('a read deletes the expired records of every table', async () => {
    // Put directly, so no write purges it first: only the read can.
    await testPlanCacheDatabase().bedSheets.put({
      key: 'alice:tenant_a:loc_1',
      userKey: 'alice',
      tenantKey: 'tenant_a',
      cachedAt: T0,
      data: { tasks: [], plants: [] },
    });
    await readCached(planEntry(ALICE_A, 'site_1'), T0 + PLAN_CACHE_TTL_MS + 1);
    expect(await testPlanCacheDatabase().bedSheets.count()).toBe(0);
  });

  it('the app start deletes what expired while the app was closed', async () => {
    await writeCached(planEntry(ALICE_A, 'site_1'), PLAN, T0);
    await purgeExpiredPlanCache(T0 + PLAN_CACHE_TTL_MS + 1);
    expect(await testPlanCacheDatabase().plans.count()).toBe(0);
  });

  it('the app start does not create a database that is not there', async () => {
    await deleteDatabase();
    await purgeExpiredPlanCache(T0);
    expect(await databaseNames()).not.toContain(PLAN_CACHE_DB_NAME);
  });
});

describe('the bed sheet record (#2789 review L1, C5)', () => {
  const task = careTask('t_1', {
    assigned_to_user_key: 'user-7',
    completion_notes: 'left the gate open',
    photo_refs: ['att_1'],
    difficulty_rating: 4,
  });

  it('keeps no person-related field of a task or a plant', () => {
    const stored = storableSheet({
      tasks: [task],
      plants: [{ plant_key: 'pl_1', cover_photo_ref: 'att_2' } as never],
      complete: true,
    });
    expect(stored?.tasks[0]).toMatchObject({
      key: 't_1',
      name: task.name,
      assigned_to_user_key: null,
      completion_notes: null,
      photo_refs: [],
      difficulty_rating: null,
    });
    expect(stored?.plants?.[0]).toMatchObject({ plant_key: 'pl_1', cover_photo_ref: null });
    expect(stored).not.toHaveProperty('complete');
  });

  it('stores nothing for a partial or aborted answer', () => {
    expect(storableSheet({ tasks: [task], plants: null, complete: false })).toBeUndefined();
    expect(storableSheet({ tasks: [task], plants: [], complete: false })).toBeUndefined();
  });
});

describe('a second tab cannot refill the deleted database (#2789 review S2)', () => {
  /** Another tab of the origin: its own module scope — own Dexie connection, own channel, own generation. */
  async function secondTab() {
    vi.resetModules();
    const cache = await import('./planCache');
    return cache;
  }

  it('the other tab drops its in-flight write and writes nothing new after the clearing', async () => {
    const tabB = await secondTab();
    // Tab B has a read under way (its token is still valid) but no connection yet: only the broadcast
    // can tell it that tab A cleared.
    let answer: (value: unknown) => void = () => undefined;
    const inFlight = tabB.readThrough(tabB.planEntry(ALICE_A, 'site_1'), () => new Promise((resolve) => (answer = resolve)));

    // Tab A (this file's module scope) signs out.
    await clearOfflineData();
    await settle();

    answer(PLAN);
    await inFlight;
    await tabB.writeCached(tabB.planEntry(ALICE_A, 'site_2'), PLAN, Date.now());
    await settle();
    expect(await databaseNames()).not.toContain(PLAN_CACHE_DB_NAME);
  });

  it('a deletion by another connection alone (no broadcast) also retires the tab', async () => {
    const tabB = await secondTab();
    await tabB.writeCached(tabB.planEntry(ALICE_A, 'site_0'), PLAN, Date.now());
    await new Promise<void>((resolve) => {
      const request = indexedDB.deleteDatabase(PLAN_CACHE_DB_NAME);
      request.onsuccess = () => resolve();
      request.onerror = () => resolve();
    });
    await tabB.writeCached(tabB.planEntry(ALICE_A, 'site_2'), PLAN, Date.now());
    await settle();
    expect(await databaseNames()).not.toContain(PLAN_CACHE_DB_NAME);
  });
});
