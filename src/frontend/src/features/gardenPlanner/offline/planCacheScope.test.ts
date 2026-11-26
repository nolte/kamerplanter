import 'fake-indexeddb/auto';
import { configureStore } from '@reduxjs/toolkit';
import { http, HttpResponse } from 'msw';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { setActiveTenantSlug } from '@/api/client';
import { loadGardenPlan } from '@/features/gardenPlanner/state/gardenPlanSlice';
import { planResponse } from '@/test/gardenPlanFixtures';
import { server } from '@/test/mocks/server';
import { postNamespace } from '@/pwa/offlineData';
import { PLAN_CACHE_DB_NAME } from '@/pwa/storageWipe';
import { rootReducer } from '@/store/rootReducer';
import { createSessionEpochMiddleware } from '@/store/sessionEpochMiddleware';
import { sessionListener } from '@/store/sessionListener';
import { fetchProfile, logoutUser } from '@/store/slices/authSlice';
import { clearActiveTenant, loadMyTenants } from '@/store/slices/tenantSlice';
import { planEntry, readCached, resetPlanCacheForTests, type CacheScope } from './planCache';

/**
 * #3082 shape 2 (full mode) — the plan read takes its cache scope when the answer is in, not at dispatch.
 *
 * The production path: the store with the real root reducer, the session epoch guard and the session listener
 * (which posts the namespace and runs the clearings), the real `loadGardenPlan` thunk, the real tenant-scoped API
 * client (msw answers) and a real IndexedDB (`fake-indexeddb`). In full mode a tenant-scoped request waits for the
 * tenant slug, which `loadMyTenants` sets together with the active tenant; the profile comes before it.
 */

const USER = { key: 'user_u', email: 'u@example.com', display_name: 'U' };
const NEXT_USER = { key: 'user_v', email: 'v@example.com', display_name: 'V' };
const TENANT_A = { key: 'tenant_a', slug: 'garten-a', name: 'A', role: 'lead' };
const TENANT_B = { key: 'tenant_b', slug: 'garten-b', name: 'B', role: 'lead' };
const IN_A: CacheScope = { userKey: USER.key, tenantKey: TENANT_A.key };
const IN_B: CacheScope = { userKey: USER.key, tenantKey: TENANT_B.key };
const SITE = 'site_1';

function productionStore() {
  return configureStore({
    reducer: rootReducer,
    middleware: (getDefaultMiddleware) =>
      getDefaultMiddleware().prepend(createSessionEpochMiddleware(), sessionListener.middleware),
  });
}
type Store = ReturnType<typeof productionStore>;

/** The profile and the tenant list arrive (what `AuthProvider` dispatches during the bootstrap). */
function bootstrap(store: Store, tenants = [TENANT_A]): void {
  store.dispatch(fetchProfile.fulfilled(USER as never, 'profile'));
  store.dispatch(loadMyTenants.fulfilled(tenants as never, 'tenants'));
}

/** The plan endpoint, answering only once `release` is called; `slugs` lists the tenants it was asked in. */
function gatedPlan() {
  const slugs: string[] = [];
  let release: () => void = () => undefined;
  const gate = new Promise<void>((resolve) => (release = resolve));
  server.use(
    http.get('/api/v1/t/:slug/sites/:site/plan', async ({ params }) => {
      slugs.push(String(params.slug));
      await gate;
      return HttpResponse.json(planResponse({ site_key: SITE }));
    }),
  );
  return { slugs, release: () => release() };
}

function settle(ms = 50): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function databaseNames(): Promise<string[]> {
  return (await indexedDB.databases()).map((database) => database.name ?? '');
}

beforeEach(async () => {
  setActiveTenantSlug(null);
  localStorage.clear();
  await postNamespace(null, null);
  resetPlanCacheForTests();
  await new Promise<void>((resolve) => {
    const request = indexedDB.deleteDatabase(PLAN_CACHE_DB_NAME);
    request.onsuccess = request.onerror = request.onblocked = () => resolve();
  });
});

afterEach(() => {
  setActiveTenantSlug(null);
  localStorage.clear();
});

describe('the plan read caches in the scope known when the answer is in (#3082)', () => {
  it('a plan loaded before the profile and the tenant are known is cached once they are', async () => {
    const store = productionStore();
    const plan = gatedPlan();
    // The plan page mounts first: nobody signed in yet in the store, no tenant, no slug.
    const load = store.dispatch(loadGardenPlan(SITE));
    await settle();
    bootstrap(store);
    await settle();
    plan.release();
    const action = await load;

    expect(loadGardenPlan.fulfilled.match(action)).toBe(true);
    expect(plan.slugs).toEqual([TENANT_A.slug]);
    await expect.poll(() => readCached(planEntry(IN_A, SITE)), { timeout: 2000 }).not.toBeNull();
  });

  it('a tenant switch between request and answer writes nothing (the clearing moved the generation)', async () => {
    const store = productionStore();
    bootstrap(store);
    const plan = gatedPlan();
    const load = store.dispatch(loadGardenPlan(SITE));
    await settle();
    // `TenantSwitcher`: clear the offline data, then the other tenant is the active one.
    const { clearOfflineData } = await import('@/pwa/offlineData');
    await clearOfflineData();
    store.dispatch(clearActiveTenant());
    store.dispatch(loadMyTenants.fulfilled([TENANT_B] as never, 'tenants-b'));
    plan.release();
    await load;
    await settle(100);

    expect(await readCached(planEntry(IN_B, SITE))).toBeNull();
    expect(await readCached(planEntry(IN_A, SITE))).toBeNull();
  });

  it('a tenant re-picked without a clearing drops an answer read before any scope was known', async () => {
    const store = productionStore();
    const plan = gatedPlan();
    const load = store.dispatch(loadGardenPlan(SITE));
    await settle();
    bootstrap(store);
    // The request went out in tenant A; then the server refused A elsewhere and the store re-picked B
    // (`setActiveTenantRejectedHandler`: clearActiveTenant + loadMyTenants) — no clearing of the offline data.
    await expect.poll(() => plan.slugs).toEqual([TENANT_A.slug]);
    store.dispatch(clearActiveTenant());
    store.dispatch(loadMyTenants.fulfilled([TENANT_B] as never, 'tenants-b'));
    plan.release();
    await load;
    await settle(100);

    expect(await readCached(planEntry(IN_B, SITE))).toBeNull();
  });

  it('a logout between request and answer writes nothing, also not once the next account signs in', async () => {
    const store = productionStore();
    bootstrap(store);
    const plan = gatedPlan();
    const load = store.dispatch(loadGardenPlan(SITE));
    await settle();
    store.dispatch(logoutUser.fulfilled(undefined as never, 'logout'));
    await settle();
    plan.release();
    await load;
    await settle(100);
    expect(await databaseNames()).not.toContain(PLAN_CACHE_DB_NAME);

    // The next person on the device signs in: the answer of the previous session stays unwritten.
    store.dispatch(fetchProfile.fulfilled(NEXT_USER as never, 'profile-next'));
    store.dispatch(loadMyTenants.fulfilled([TENANT_A] as never, 'tenants-next'));
    await settle(100);
    expect(await readCached(planEntry({ userKey: NEXT_USER.key, tenantKey: TENANT_A.key }, SITE))).toBeNull();
    expect(await readCached(planEntry(IN_A, SITE))).toBeNull();
  });
});
