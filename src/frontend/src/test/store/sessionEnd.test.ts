/**
 * #2117 (MT-020) — the end of a session leaves nothing of the account behind in the tab.
 *
 * Measured before the change: `logoutUser.fulfilled` and `clearAuth` reset only
 * `auth`. Every data slice kept the previous account's items (the list slices do
 * not clear on `.pending`), `kp_active_tenant_slug` stayed in localStorage and in
 * the API client, and the Web-Push subscription stayed registered for the
 * previous account — on a shared device the next person saw the first one's
 * plants until their own lists arrived, and the device received both accounts'
 * pushes.
 *
 * Runs against the application's real store (fresh module per test), so the
 * reducer map under test is the one `App` mounts — not a copy.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

const ACTIVE_TENANT_KEY = 'kp_active_tenant_slug';

vi.mock('@/api/endpoints/auth', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/api/endpoints/auth')>();
  return { ...actual, logout: vi.fn().mockResolvedValue(undefined) };
});
vi.mock('@/api/endpoints/notifications', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/api/endpoints/notifications')>();
  return { ...actual, unsubscribePwa: vi.fn().mockResolvedValue(undefined) };
});

interface PushDouble {
  endpoint: string;
  unsubscribe: ReturnType<typeof vi.fn>;
}

function installPush(): PushDouble {
  const subscription: PushDouble = {
    endpoint: 'https://push.example.org/device-1',
    unsubscribe: vi.fn().mockResolvedValue(true),
  };
  const registration = { pushManager: { getSubscription: vi.fn().mockResolvedValue(subscription) } };
  Object.defineProperty(navigator, 'serviceWorker', {
    configurable: true,
    value: { getRegistration: vi.fn().mockResolvedValue(registration), ready: Promise.resolve(registration) },
  });
  Object.defineProperty(window, 'PushManager', { configurable: true, value: function PushManager() {} });
  Object.defineProperty(window, 'Notification', {
    configurable: true,
    value: Object.assign(function Notification() {}, { permission: 'granted' }),
  });
  return subscription;
}

function removePush() {
  for (const target of [navigator, window] as object[]) {
    for (const name of ['serviceWorker', 'PushManager', 'Notification']) {
      if (Object.getOwnPropertyDescriptor(target, name)?.configurable) {
        delete (target as Record<string, unknown>)[name];
      }
    }
  }
}

async function freshStore() {
  vi.resetModules();
  const storeModule = await import('@/store/store');
  const auth = await import('@/store/slices/authSlice');
  const tenants = await import('@/store/slices/tenantSlice');
  const sites = await import('@/store/slices/sitesSlice');
  const prefs = await import('@/store/slices/userPreferencesSlice');
  const ui = await import('@/store/slices/uiSlice');
  const client = await import('@/api/client');
  const authApi = await import('@/api/endpoints/auth');
  const notificationsApi = await import('@/api/endpoints/notifications');
  return { store: storeModule.store, auth, tenants, sites, prefs, ui, client, authApi, notificationsApi };
}

type World = Awaited<ReturnType<typeof freshStore>>;

/** Put the first account's data into the slices a shared-device leak is about. */
function fillAsAccountA(w: World) {
  const { store } = w;
  store.dispatch(w.auth.setAccessToken('jwt-of-a'));
  store.dispatch({
    type: w.tenants.loadMyTenants.fulfilled.type,
    payload: [{ key: 't-a', slug: 'garten-von-a', name: 'Garten von A', role: 'lead', tenant_type: 'personal' }],
  });
  store.dispatch(w.tenants.switchTenant('garten-von-a'));
  store.dispatch({
    type: w.sites.fetchSites.fulfilled.type,
    payload: { items: [{ key: 's-a', name: 'Balkon von A' }], total: 1, offset: 0, limit: 50 },
  });
  store.dispatch({ type: w.prefs.fetchPreferences.fulfilled.type, payload: { experience_level: 'expert' } });
  store.dispatch(w.ui.setBreadcrumbs([{ label: 'Tomate von A' }]));
  localStorage.setItem(ACTIVE_TENANT_KEY, 'garten-von-a');
}

function withoutAuth(state: Record<string, unknown>) {
  return Object.fromEntries(Object.entries(state).filter(([slice]) => slice !== 'auth'));
}

describe('the end of a session (#2117)', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  afterEach(() => {
    removePush();
    vi.clearAllMocks();
  });

  it.each(['logout', 'forced'] as const)('returns every slice to its initial state (%s)', async (how) => {
    const w = await freshStore();
    const pristine = withoutAuth(w.store.getState() as unknown as Record<string, unknown>);
    fillAsAccountA(w);
    expect(withoutAuth(w.store.getState() as unknown as Record<string, unknown>)).not.toEqual(pristine);

    if (how === 'logout') await w.store.dispatch(w.auth.logoutUser());
    else w.store.dispatch(w.auth.clearAuth());

    expect(withoutAuth(w.store.getState() as unknown as Record<string, unknown>)).toEqual(pristine);
    expect(w.store.getState().auth.isAuthenticated).toBe(false);
    expect(w.store.getState().auth.initialized).toBe(true);
  });

  it.each(['logout', 'forced'] as const)('forgets the active tenant slug (%s)', async (how) => {
    const w = await freshStore();
    fillAsAccountA(w);
    expect(w.client.getActiveTenantSlug()).toBe('garten-von-a');

    if (how === 'logout') await w.store.dispatch(w.auth.logoutUser());
    else w.store.dispatch(w.auth.clearAuth());

    expect(localStorage.getItem(ACTIVE_TENANT_KEY)).toBeNull();
    expect(w.client.getActiveTenantSlug()).toBeNull();
  });

  it('a failed logout request still ends the session in the tab', async () => {
    const w = await freshStore();
    fillAsAccountA(w);
    vi.mocked(w.authApi.logout).mockRejectedValueOnce(new Error('offline'));

    await w.store.dispatch(w.auth.logoutUser());

    expect(w.store.getState().sites).toEqual((await import('@/store/slices/sitesSlice')).default(undefined, { type: '' }));
    expect(localStorage.getItem(ACTIVE_TENANT_KEY)).toBeNull();
  });

  it('logout drops the push subscription on the server first, then in the browser', async () => {
    const subscription = installPush();
    const w = await freshStore();
    fillAsAccountA(w);
    const order: string[] = [];
    vi.mocked(w.notificationsApi.unsubscribePwa).mockImplementation(async () => {
      order.push('server');
      return undefined as never;
    });
    subscription.unsubscribe.mockImplementation(async () => {
      order.push('browser');
      return true;
    });
    vi.mocked(w.authApi.logout).mockImplementation(async () => {
      order.push('logout');
    });

    await w.store.dispatch(w.auth.logoutUser());

    expect(w.notificationsApi.unsubscribePwa).toHaveBeenCalledWith('https://push.example.org/device-1');
    // While the access token still works, and before the session is gone.
    expect(order.slice(0, 2)).toEqual(['server', 'browser']);
    expect(order).toContain('logout');
  });

  it('a forced sign-out drops the browser subscription (no token left to tell the server)', async () => {
    const subscription = installPush();
    const w = await freshStore();
    fillAsAccountA(w);

    w.store.dispatch(w.auth.clearAuth());
    await vi.waitFor(() => expect(subscription.unsubscribe).toHaveBeenCalled());

    expect(w.notificationsApi.unsubscribePwa).not.toHaveBeenCalled();
  });

  it('a rate-limited refresh is not the end of a session', async () => {
    const w = await freshStore();
    fillAsAccountA(w);
    const before = w.store.getState().sites;

    w.store.dispatch({
      type: w.auth.refreshAccessToken.rejected.type,
      payload: w.auth.RATE_LIMITED_REJECTION,
      meta: { rejectedWithValue: true },
      error: {},
    });

    expect(w.store.getState().sites).toBe(before);
    expect(localStorage.getItem(ACTIVE_TENANT_KEY)).toBe('garten-von-a');
  });
});

describe('a logout never waits on push for long (#2117)', () => {
  afterEach(() => {
    removePush();
    vi.useRealTimers();
    vi.clearAllMocks();
  });

  it('signs out even when the backend never answers the unsubscribe', async () => {
    const subscription = installPush();
    const w = await freshStore();
    fillAsAccountA(w);
    vi.mocked(w.notificationsApi.unsubscribePwa).mockReturnValue(new Promise(() => undefined));
    vi.useFakeTimers();

    const done = w.store.dispatch(w.auth.logoutUser());
    await vi.advanceTimersByTimeAsync(3_000);
    await done;

    expect(subscription.unsubscribe).toHaveBeenCalled();
    expect(w.authApi.logout).toHaveBeenCalled();
    expect(w.store.getState().auth.isAuthenticated).toBe(false);
  });
});
