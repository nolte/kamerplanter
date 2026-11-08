import 'fake-indexeddb/auto';
import { readdirSync, readFileSync, statSync } from 'node:fs';
import { join, relative } from 'node:path';
import { createElement } from 'react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { configureStore } from '@reduxjs/toolkit';
import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import i18n from 'i18next';

/**
 * REQ-053 WP 9.1 (#2741), guardrail G-W9 (b) / UI-NFR-012 SR-019: a logout and a tenant switch
 * empty the service worker's API cache and IndexedDB completely BEFORE the page reloads (or the new
 * tenant becomes active) — on a shared device the next account must not read the previous one's
 * plans offline.
 *
 * Pinned at both places the issue names, through the production components and the real listener:
 *
 * - logout / forced sign-out: `store/sessionListener.ts`;
 * - tenant switch: `components/layout/TenantSwitcher.tsx` (before `reload()`) and
 *   `components/tenants/LightModeTakeoverDialog.tsx` (before `switchTenant`).
 *
 * The sweep at the end catches a NEW place that dispatches `switchTenant` without clearing first.
 *
 * REQ-053 WP 9.2 (#2742): the plan cache (`features/gardenPlanner/offline`, Dexie) is one of the databases
 * those clearings empty — the real `clearOfflineData` / `clearAllOfflineStorage` and the worker's wipe
 * (`deleteAllDatabases`) run against a real IndexedDB (`fake-indexeddb`) holding a cached plan, and the
 * plan is gone afterwards; a write whose read began before a clearing never lands.
 *
 * #2789 review S3: two more places end a session's offline data — the account erasure
 * (`pages/auth/AccountSettingsPage.tsx`, before its redirect) and a refresh the server refused
 * (`store/sessionListener.ts`, the bootstrap swallows it without `clearAuth`). A refresh that got no
 * answer (offline start) or was rate limited must NOT clear: the offline start reads that cache.
 */

const calls: string[] = [];
let releaseClear: () => void = () => undefined;
let clearGate: Promise<void> = Promise.resolve();

vi.mock('@/pwa/offlineData', () => ({
  clearOfflineData: vi.fn(async () => {
    calls.push('clear:start');
    await clearGate;
    calls.push('clear:done');
  }),
  postNamespace: vi.fn(async (userKey: string | null, tenantKey: string | null) => {
    calls.push(`namespace:${userKey}:${tenantKey}`);
  }),
  repostNamespace: vi.fn(async () => undefined),
  clearAllOfflineStorage: vi.fn(async () => undefined),
  offlineDataGeneration: vi.fn(() => 0),
  onOfflineDataCleared: vi.fn(() => () => undefined),
}));
vi.mock('@/api/endpoints/system', () => ({ getTakeoverStatus: vi.fn(), decideTakeover: vi.fn() }));
vi.mock('@/api/endpoints/auth', async () => ({
  ...(await vi.importActual<typeof import('@/api/endpoints/auth')>('@/api/endpoints/auth')),
  getProfile: vi.fn(),
  listProviders: vi.fn(),
  logout: vi.fn().mockResolvedValue(undefined),
}));
vi.mock('@/api/endpoints/tenants', async () => ({
  ...(await vi.importActual<typeof import('@/api/endpoints/tenants')>('@/api/endpoints/tenants')),
  listMyTenants: vi.fn(),
}));

const offlineData = await import('@/pwa/offlineData');
const { renderWithProviders, createTestStore, authState } = await import('@/test/helpers');

const TENANT_A = { key: 'tenant_a', slug: 'garten-a', name: 'Garten A', tenant_type: 'personal', role: 'lead' };
const TENANT_B = { key: 'tenant_b', slug: 'garten-b', name: 'Garten B', tenant_type: 'organization', role: 'grower' };

function holdClear() {
  clearGate = new Promise<void>((resolve) => {
    releaseClear = resolve;
  });
}

describe('offline data is cleared before a tenant switch reloads (TenantSwitcher)', () => {
  let reload: ReturnType<typeof vi.fn>;
  let originalLocation: Location;

  beforeEach(async () => {
    calls.length = 0;
    vi.mocked(offlineData.clearOfflineData).mockClear();
    await i18n.changeLanguage('de');
    originalLocation = window.location;
    reload = vi.fn(() => calls.push('reload'));
    Object.defineProperty(window, 'location', { configurable: true, value: { ...originalLocation, reload } });
  });

  afterEach(() => {
    Object.defineProperty(window, 'location', { configurable: true, value: originalLocation });
    clearGate = Promise.resolve();
  });

  it('awaits the clear and reloads only after it finished', async () => {
    const { default: TenantSwitcher } = await import('@/components/layout/TenantSwitcher');
    holdClear();
    const store = createTestStore({
      tenants: { activeTenant: TENANT_A, myTenants: [TENANT_A, TENANT_B], isLoading: false, error: null },
    } as never);
    renderWithProviders(createElement(TenantSwitcher), { store });

    await userEvent.click(screen.getByRole('button', { name: /Garten A/ }));
    await userEvent.click(screen.getByTestId('tenant-switcher-item-garten-b'));

    await waitFor(() => expect(offlineData.clearOfflineData).toHaveBeenCalledTimes(1));
    expect(reload).not.toHaveBeenCalled();
    releaseClear();
    await waitFor(() => expect(reload).toHaveBeenCalledTimes(1));
    expect(calls).toEqual(['clear:start', 'clear:done', 'reload']);
  });
});

describe('offline data is cleared before the light-mode take-over switches the tenant', () => {
  beforeEach(async () => {
    calls.length = 0;
    localStorage.clear();
    vi.mocked(offlineData.clearOfflineData).mockClear();
    await i18n.changeLanguage('de');
  });

  it('clears before the taken-over garden becomes active', async () => {
    const systemApi = await import('@/api/endpoints/system');
    const authApi = await import('@/api/endpoints/auth');
    const tenantApi = await import('@/api/endpoints/tenants');
    const { default: LightModeTakeoverDialog } = await import('@/components/tenants/LightModeTakeoverDialog');
    vi.mocked(systemApi.getTakeoverStatus).mockResolvedValue({
      pending: true,
      eligible: true,
      tenant_key: 'tenant_b',
      tenant_name: 'Garten B',
      tenant_slug: 'garten-b',
      resource_counts: { plants: 1, sites: 1, planting_runs: 0, nutrient_plans: 0, tasks: 0 },
    } as never);
    vi.mocked(systemApi.decideTakeover).mockResolvedValue({
      accepted: true,
      tenant_slug: 'garten-b',
      platform_admin_granted: true,
    } as never);
    vi.mocked(authApi.getProfile).mockResolvedValue({ key: 'user-1', display_name: 'T' } as never);
    vi.mocked(authApi.listProviders).mockResolvedValue([{ provider: 'local' }] as never);
    // The first garden is the one `loadMyTenants` picks, so only `switchTenant` can make B active.
    vi.mocked(tenantApi.listMyTenants).mockResolvedValue([TENANT_A, TENANT_B] as never);

    holdClear();
    const store = createTestStore(authState());
    renderWithProviders(createElement(LightModeTakeoverDialog), { store });

    await userEvent.click(await screen.findByTestId('light-mode-takeover-accept'));
    const field = await screen.findByTestId('light-mode-takeover-step-up-password');
    await userEvent.type(field.querySelector('input') as HTMLInputElement, ['pw', 'x', '1'].join('-'));
    await userEvent.click(screen.getByTestId('light-mode-takeover-step-up-confirm'));

    await waitFor(() => expect(offlineData.clearOfflineData).toHaveBeenCalledTimes(1));
    expect(store.getState().tenants.activeTenant?.slug).not.toBe('garten-b');
    releaseClear();
    await waitFor(() => expect(store.getState().tenants.activeTenant?.slug).toBe('garten-b'));
  });
});

describe('offline data is cleared on logout and the namespace follows user and tenant (sessionListener)', () => {
  beforeEach(() => {
    calls.length = 0;
    clearGate = Promise.resolve();
    vi.mocked(offlineData.clearOfflineData).mockClear();
    vi.mocked(offlineData.postNamespace).mockClear();
  });

  async function listenedStore(preloaded: unknown) {
    const { rootReducer } = await import('@/store/rootReducer');
    const { sessionListener } = await import('@/store/sessionListener');
    return configureStore({
      reducer: rootReducer,
      preloadedState: preloaded as never,
      middleware: (getDefault) => getDefault().prepend(sessionListener.middleware),
    });
  }

  it('clears on a forced sign-out (clearAuth) and on a logout', async () => {
    const { clearAuth, logoutUser } = await import('@/store/slices/authSlice');
    const store = await listenedStore(authState());
    store.dispatch(clearAuth());
    await waitFor(() => expect(offlineData.clearOfflineData).toHaveBeenCalledTimes(1));
    await store.dispatch(logoutUser());
    await waitFor(() => expect(offlineData.clearOfflineData).toHaveBeenCalledTimes(2));
  });

  it('posts the user and tenant keys — never a token — when the active tenant changes', async () => {
    const { switchTenant } = await import('@/store/slices/tenantSlice');
    const state = authState() as Record<string, unknown>;
    const auth = state.auth as Record<string, unknown>;
    const store = await listenedStore({
      ...state,
      auth: { ...auth, user: { ...(auth.user as object), key: 'user_1' } },
      tenants: { activeTenant: TENANT_A, myTenants: [TENANT_A, TENANT_B], isLoading: false, error: null },
    });
    store.dispatch(switchTenant('garten-b'));
    await waitFor(() => expect(offlineData.postNamespace).toHaveBeenCalledWith('user_1', 'tenant_b'));
    for (const args of vi.mocked(offlineData.postNamespace).mock.calls) {
      expect(args.join(' ')).not.toMatch(/ey[A-Za-z0-9_-]{8,}\./);
    }
  });
});

describe('sweep: every place that switches the tenant clears first', () => {
  const srcRoot = join(process.cwd(), 'src');

  function sourceFiles(dir: string): string[] {
    return readdirSync(dir).flatMap((name) => {
      const path = join(dir, name);
      if (statSync(path).isDirectory()) return name === 'test' ? [] : sourceFiles(path);
      return /\.(ts|tsx)$/.test(name) && !/\.test\.tsx?$/.test(name) ? [path] : [];
    });
  }

  it('finds no switchTenant dispatch without a preceding await clearOfflineData()', () => {
    const offenders: string[] = [];
    let sites = 0;
    for (const file of sourceFiles(srcRoot)) {
      const text = readFileSync(file, 'utf8');
      for (const match of text.matchAll(/dispatch\(switchTenant\(/g)) {
        sites += 1;
        const before = text.slice(0, match.index);
        const lastClear = before.lastIndexOf('await clearOfflineData()');
        const fnStart = Math.max(before.lastIndexOf('=> {'), before.lastIndexOf('function '));
        if (lastClear === -1 || lastClear < fnStart) {
          // TenantSwitcher clears after the dispatch but before its reload — checked below.
          const after = text.slice(match.index);
          const reload = after.indexOf('window.location.reload()');
          const clear = after.indexOf('await clearOfflineData()');
          if (!(clear !== -1 && reload !== -1 && clear < reload)) offenders.push(relative(srcRoot, file));
        }
      }
    }
    expect(sites).toBeGreaterThanOrEqual(2);
    expect(offenders).toEqual([]);
  });
});

describe('the plan cache database is emptied by the same clearings (WP 9.2)', () => {
  const ALICE = { userKey: 'alice', tenantKey: 'tenant_a' };
  const T0 = Date.now();

  // Each test is a fresh page: a deletion in the previous one retired that page's cache.
  beforeEach(async () => {
    const { emptyPlanCache } = await import('@/test/planCacheTestKit');
    await emptyPlanCache();
  });

  /** A plan, a bed list, a site list, a bed summary and a bed sheet: every table of the plan cache. */
  async function seededPlanCache() {
    const cache = await import('@/features/gardenPlanner/offline/planCache');
    const entries = [
      cache.planEntry(ALICE, 'site_1'),
      cache.bedListEntry(ALICE, 'site_1'),
      cache.siteListEntry(ALICE, 50),
      cache.bedSummaryEntry(ALICE, 'loc_1'),
      cache.bedSheetEntry(ALICE, 'loc_1'),
    ];
    for (const item of entries) {
      await cache.writeCached(item, { cached: item.table }, T0, 0);
      expect(await cache.readCached(item, T0)).not.toBeNull();
    }
    /** What is still readable afterwards, by table. */
    const left = async (): Promise<string[]> => {
      const reads = await Promise.all(entries.map((item) => cache.readCached(item, T0)));
      return entries.filter((_, index) => reads[index] !== null).map((item) => item.table);
    };
    return { left };
  }

  async function databaseNames(): Promise<string[]> {
    return (await indexedDB.databases()).map((database) => database.name ?? '');
  }

  it('lives in the database the wipe knows by name', async () => {
    const { PLAN_CACHE_DB_NAME, APP_DATABASE_NAMES } = await import('@/pwa/storageWipe');
    await seededPlanCache();
    expect(await databaseNames()).toContain(PLAN_CACHE_DB_NAME);
    expect(APP_DATABASE_NAMES).toContain(PLAN_CACHE_DB_NAME);
  });

  it('is empty after a logout or tenant switch (clearOfflineData)', async () => {
    const actual = await vi.importActual<typeof import('@/pwa/offlineData')>('@/pwa/offlineData');
    const { left } = await seededPlanCache();
    await actual.clearOfflineData();
    expect(await left()).toEqual([]);
  });

  it('is empty after the kill switch (clearAllOfflineStorage)', async () => {
    const actual = await vi.importActual<typeof import('@/pwa/offlineData')>('@/pwa/offlineData');
    const { left } = await seededPlanCache();
    await actual.clearAllOfflineStorage();
    expect(await left()).toEqual([]);
  });

  it("is empty after the worker's self-destruct wipe, even where databases() cannot enumerate", async () => {
    const { deleteAllDatabases } = await import('@/pwa/storageWipe');
    const { left } = await seededPlanCache();
    const databases = indexedDB.databases;
    // Firefox before 126: no enumeration. The plan cache must still go, by its name.
    Object.defineProperty(indexedDB, 'databases', { configurable: true, value: undefined });
    try {
      await deleteAllDatabases();
    } finally {
      Object.defineProperty(indexedDB, 'databases', { configurable: true, value: databases });
    }
    expect(await left()).toEqual([]);
  });

  it('drops a write whose read began before a clearing started', async () => {
    const cache = await import('@/features/gardenPlanner/offline/planCache');
    const entry = cache.planEntry(ALICE, 'site_2');
    vi.mocked(offlineData.offlineDataGeneration).mockReturnValue(1);
    try {
      await cache.writeCached(entry, { site_key: 'site_2' }, T0, 0);
    } finally {
      vi.mocked(offlineData.offlineDataGeneration).mockReturnValue(0);
    }
    expect(await cache.readCached(entry, T0)).toBeNull();
  });
});

describe('offline data is cleared on account erasure and on a dead session (#2789 review S3)', () => {
  beforeEach(() => {
    calls.length = 0;
    clearGate = Promise.resolve();
    vi.mocked(offlineData.clearOfflineData).mockClear();
  });

  async function listenedStore() {
    const { rootReducer } = await import('@/store/rootReducer');
    const { sessionListener } = await import('@/store/sessionListener');
    return configureStore({
      reducer: rootReducer,
      preloadedState: authState() as never,
      middleware: (getDefault) => getDefault().prepend(sessionListener.middleware),
    });
  }

  it('clears when the server refuses the refresh, not when it got no answer or was rate limited', async () => {
    const { refreshAccessToken, RATE_LIMITED_REJECTION } = await import('@/store/slices/authSlice');
    const { ApiError } = await import('@/api/errors');
    const { AxiosError } = await import('axios');
    const store = await listenedStore();

    store.dispatch(refreshAccessToken.rejected(new AxiosError('Network Error', 'ERR_NETWORK'), 'r1'));
    store.dispatch(refreshAccessToken.rejected(null, 'r2', undefined, RATE_LIMITED_REJECTION));
    await new Promise((resolve) => setTimeout(resolve, 20));
    expect(offlineData.clearOfflineData).not.toHaveBeenCalled();

    const refused = new ApiError(
      { error_id: 'e', error_code: 'UNAUTHORIZED', message: 'Session expired', details: [], path: '/', method: 'POST' } as never,
      401,
    );
    store.dispatch(refreshAccessToken.rejected(refused, 'r3'));
    await waitFor(() => expect(offlineData.clearOfflineData).toHaveBeenCalledTimes(1));
  });

  it('the account erasure clears before it leaves for the login page', async () => {
    const { http, HttpResponse } = await import('msw');
    const { server } = await import('@/test/mocks/server');
    const authApi = await import('@/api/endpoints/auth');
    const { default: AccountSettingsPage } = await import('@/pages/auth/AccountSettingsPage');
    vi.mocked(authApi.listProviders).mockResolvedValue([
      { key: 'prov-0', provider: 'local', provider_email: 'tester@example.org' },
    ] as never);
    server.use(http.delete('/api/v1/users/me', () => HttpResponse.json({ message: 'ok' })));
    await i18n.changeLanguage('de');
    const originalLocation = window.location;
    let href = `${originalLocation.origin}/account`;
    Object.defineProperty(window, 'location', {
      configurable: true,
      value: {
        ...originalLocation,
        get href() {
          return href;
        },
        set href(value: string) {
          calls.push(`href:${value}`);
          href = value;
        },
      },
    });
    try {
      holdClear();
      renderWithProviders(createElement(AccountSettingsPage), { store: createTestStore(authState()), route: '/account#account' });
      await userEvent.click(await screen.findByTestId('delete-account-btn'));
      const dialog = await screen.findByTestId('delete-account-dialog');
      const email = dialog.querySelector('[data-testid="delete-account-email"] input') as HTMLInputElement;
      await userEvent.type(email, 'tester@example.org');
      await userEvent.type(within(dialog).getByLabelText(/passwort/i), ['my', 'password'].join('-'));
      await userEvent.click(within(dialog).getByTestId('delete-account-confirm'));

      await waitFor(() => expect(offlineData.clearOfflineData).toHaveBeenCalledTimes(1));
      expect(calls).not.toContain('href:/login');
      releaseClear();
      await waitFor(() => expect(calls).toContain('href:/login'));
      expect(calls.indexOf('clear:done')).toBeLessThan(calls.indexOf('href:/login'));
    } finally {
      Object.defineProperty(window, 'location', { configurable: true, value: originalLocation });
    }
  });
});
