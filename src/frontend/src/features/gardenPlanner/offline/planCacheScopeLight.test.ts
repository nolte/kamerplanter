import 'fake-indexeddb/auto';
import { configureStore } from '@reduxjs/toolkit';
import { http, HttpResponse } from 'msw';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { planResponse } from '@/test/gardenPlanFixtures';
import { server } from '@/test/mocks/server';
import { PLAN_CACHE_DB_NAME } from '@/pwa/storageWipe';
import type { CacheScope } from './planCache';

/**
 * #3082 shape 2, as the light nightly (TC-053-086) failed: the plan page's read is answered BEFORE the store knows
 * the user and the tenant. Light mode (`KAMERPLANTER_MODE=light`): the tenant-scoped client sends every request to
 * the fixed slug at once, and `ProtectedRoute` renders the plan page without waiting for the profile or the tenant
 * list. Production path as in `planCacheScope.test.ts` (store with the session listener, the real thunks, the real
 * client against msw, `fake-indexeddb`).
 *
 * The mode is read once, when `config/mode` loads, and the test setup has loaded the API client in full mode already;
 * so every module of the path is loaded afresh in light mode ({@link lightApp}).
 */

const SYSTEM_USER = { key: 'user_system', email: 'system@kamerplanter.local', display_name: 'System' };
const LIGHT_TENANT = { key: 'tenant_light', slug: 'mein-garten', name: 'Mein Garten', role: 'lead' };
const SCOPE: CacheScope = { userKey: SYSTEM_USER.key, tenantKey: LIGHT_TENANT.key };
const SITE = 'site_1';

async function lightApp() {
  vi.resetModules();
  vi.doMock('@/config/mode', () => ({ KAMERPLANTER_MODE: 'light', isLightMode: true, isFullMode: false }));
  const [garden, sites, auth, tenants, rootReducer, epoch, listener, cache, offlineData] = await Promise.all([
    import('@/features/gardenPlanner/state/gardenPlanSlice'),
    import('@/store/slices/sitesSlice'),
    import('@/store/slices/authSlice'),
    import('@/store/slices/tenantSlice'),
    import('@/store/rootReducer'),
    import('@/store/sessionEpochMiddleware'),
    import('@/store/sessionListener'),
    import('./planCache'),
    import('@/pwa/offlineData'),
  ]);
  await offlineData.postNamespace(null, null);
  cache.resetPlanCacheForTests();
  const store = configureStore({
    reducer: rootReducer.rootReducer,
    middleware: (getDefaultMiddleware) =>
      getDefaultMiddleware().prepend(epoch.createSessionEpochMiddleware(), listener.sessionListener.middleware),
  });
  /** `AuthProvider` in light mode: the profile, then the tenant list. */
  const bootstrap = () => {
    store.dispatch(auth.fetchProfile.fulfilled(SYSTEM_USER as never, 'profile'));
    store.dispatch(tenants.loadMyTenants.fulfilled([LIGHT_TENANT] as never, 'tenants'));
  };
  return { store, bootstrap, garden, sites, cache };
}

function settle(ms = 50): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

beforeEach(async () => {
  await new Promise<void>((resolve) => {
    const request = indexedDB.deleteDatabase(PLAN_CACHE_DB_NAME);
    request.onsuccess = request.onerror = request.onblocked = () => resolve();
  });
  server.use(
    http.get('/api/v1/t/mein-garten/sites/:site/plan', () => HttpResponse.json(planResponse({ site_key: SITE }))),
    http.get('/api/v1/t/mein-garten/sites', () => HttpResponse.json([{ key: SITE, name: 'Garten', type: 'outdoor' }])),
  );
});

describe('light mode: an answer that arrives before the scope is cached once the scope is known (#3082)', () => {
  it('the plan', async () => {
    const { store, bootstrap, garden, cache } = await lightApp();
    const action = await store.dispatch(garden.loadGardenPlan(SITE));
    expect(garden.loadGardenPlan.fulfilled.match(action)).toBe(true);
    await settle();
    // Answered with nobody known: nothing can be written yet.
    expect(await cache.readCached(cache.planEntry(SCOPE, SITE))).toBeNull();

    bootstrap();

    await expect.poll(() => cache.readCached(cache.planEntry(SCOPE, SITE)), { timeout: 2000 }).not.toBeNull();
  });

  it('the site list (the same thunk shape, sitesSlice)', async () => {
    const { store, bootstrap, sites, cache } = await lightApp();
    const action = await store.dispatch(sites.fetchSites({ all: true }));
    expect(sites.fetchSites.fulfilled.match(action)).toBe(true);
    bootstrap();

    await expect.poll(() => cache.readCached(cache.siteListEntry(SCOPE, 'all')), { timeout: 2000 }).not.toBeNull();
  });
});
