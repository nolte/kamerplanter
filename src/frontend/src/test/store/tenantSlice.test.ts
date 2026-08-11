import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { configureStore } from '@reduxjs/toolkit';
import reducer, {
  switchTenant,
  clearActiveTenant,
  clearTenants,
  loadMyTenants,
  createOrganization,
} from '@/store/slices/tenantSlice';
import { getActiveTenantSlug } from '@/api/client';
import * as tenantApi from '@/api/endpoints/tenants';

// Isolated module mock — no real HTTP, no handlers.ts.
vi.mock('@/api/endpoints/tenants');

const ACTIVE_TENANT_KEY = 'kp_active_tenant_slug';

const baseState = {
  activeTenant: null,
  myTenants: [],
  isLoading: false,
  error: null,
};

const tenantA = { key: 'ta', slug: 'garten-a', name: 'Garten A', role: 'lead' };
const tenantB = { key: 'tb', slug: 'garten-b', name: 'Garten B', role: 'grower' };

function stubLocalStorage(initial: Record<string, string> = {}) {
  const store = new Map(Object.entries(initial));
  vi.stubGlobal('localStorage', {
    getItem: (k: string) => (store.has(k) ? store.get(k)! : null),
    setItem: (k: string, v: string) => void store.set(k, v),
    removeItem: (k: string) => void store.delete(k),
    clear: () => store.clear(),
  });
  return store;
}

describe('tenantSlice', () => {
  beforeEach(() => {
    stubLocalStorage();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('has the empty initial state', () => {
    expect(reducer(undefined, { type: 'unknown' })).toEqual(baseState);
  });

  it('switchTenant activates a known tenant and persists its slug', () => {
    const store = stubLocalStorage();
    const populated = { ...baseState, myTenants: [tenantA, tenantB] as never };
    const state = reducer(populated, switchTenant('garten-b'));
    expect(state.activeTenant).toEqual(tenantB);
    expect(store.get(ACTIVE_TENANT_KEY)).toBe('garten-b');
    expect(getActiveTenantSlug()).toBe('garten-b');
  });

  it('switchTenant ignores an unknown slug', () => {
    const populated = { ...baseState, myTenants: [tenantA] as never, activeTenant: tenantA as never };
    const state = reducer(populated, switchTenant('does-not-exist'));
    expect(state.activeTenant).toEqual(tenantA);
  });

  it('clearActiveTenant drops the active tenant and its persisted slug but keeps the list', () => {
    // #1091 A-4: stale-slug recovery. The list is about to be reloaded, so it
    // must survive — wiping it would make the tenant switcher disappear.
    const store = stubLocalStorage({ [ACTIVE_TENANT_KEY]: 'garten-a' });
    const populated = {
      ...baseState,
      myTenants: [tenantA, tenantB] as never,
      activeTenant: tenantA as never,
    };
    const state = reducer(populated, clearActiveTenant());
    expect(state.activeTenant).toBeNull();
    expect(state.myTenants).toEqual([tenantA, tenantB]);
    expect(store.has(ACTIVE_TENANT_KEY)).toBe(false);
    expect(getActiveTenantSlug()).toBeNull();
  });

  it('heals the persisted slug after recovery: a revoked tenant is replaced by a surviving one', () => {
    // #1091 A-4 AC 4, second half. Clearing alone would leave the user without a
    // tenant; the reload that follows must re-persist a slug that still resolves,
    // otherwise the next session starts on the same dead one.
    const store = stubLocalStorage({ [ACTIVE_TENANT_KEY]: 'garten-a' });
    const cleared = reducer(
      { ...baseState, myTenants: [tenantA, tenantB] as never, activeTenant: tenantA as never },
      clearActiveTenant(),
    );
    expect(store.has(ACTIVE_TENANT_KEY)).toBe(false);

    const reloaded = reducer(cleared, {
      type: loadMyTenants.fulfilled.type,
      payload: [tenantB], // membership in garten-a was revoked
    });
    expect(reloaded.activeTenant).toEqual(tenantB);
    expect(store.get(ACTIVE_TENANT_KEY)).toBe('garten-b');
    expect(getActiveTenantSlug()).toBe('garten-b');
  });

  it('clearTenants wipes the tenant state and persisted slug', () => {
    const store = stubLocalStorage({ [ACTIVE_TENANT_KEY]: 'garten-a' });
    const populated = { ...baseState, myTenants: [tenantA] as never, activeTenant: tenantA as never };
    const state = reducer(populated, clearTenants());
    expect(state.activeTenant).toBeNull();
    expect(state.myTenants).toEqual([]);
    expect(store.has(ACTIVE_TENANT_KEY)).toBe(false);
    expect(getActiveTenantSlug()).toBeNull();
  });

  it('loadMyTenants.pending sets loading and clears prior error', () => {
    const state = reducer({ ...baseState, error: 'old' }, { type: loadMyTenants.pending.type });
    expect(state.isLoading).toBe(true);
    expect(state.error).toBeNull();
  });

  it('loadMyTenants.fulfilled defaults to the first tenant when none is persisted', () => {
    stubLocalStorage();
    const state = reducer(undefined, {
      type: loadMyTenants.fulfilled.type,
      payload: [tenantA, tenantB],
    });
    expect(state.activeTenant).toEqual(tenantA);
    expect(state.isLoading).toBe(false);
  });

  it('loadMyTenants.fulfilled restores the persisted tenant when it still exists', () => {
    stubLocalStorage({ [ACTIVE_TENANT_KEY]: 'garten-b' });
    const state = reducer(undefined, {
      type: loadMyTenants.fulfilled.type,
      payload: [tenantA, tenantB],
    });
    expect(state.activeTenant).toEqual(tenantB);
  });

  it('loadMyTenants.fulfilled sets active tenant to null for an empty list', () => {
    stubLocalStorage();
    const state = reducer(undefined, { type: loadMyTenants.fulfilled.type, payload: [] });
    expect(state.activeTenant).toBeNull();
  });

  it('loadMyTenants.rejected falls back to a default message', () => {
    const state = reducer(undefined, { type: loadMyTenants.rejected.type, error: {} });
    expect(state.error).toBe('errors.tenantsLoadFailed');
  });

  it('createOrganization.fulfilled replaces the tenant list', () => {
    const state = reducer(undefined, {
      type: createOrganization.fulfilled.type,
      payload: [tenantA, tenantB],
    });
    expect(state.myTenants).toEqual([tenantA, tenantB]);
  });
});

describe('tenantSlice thunks', () => {
  const mocked = vi.mocked(tenantApi);

  beforeEach(() => {
    stubLocalStorage();
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('loadMyTenants calls the API and stores the tenants', async () => {
    mocked.listMyTenants.mockResolvedValue([tenantA, tenantB] as never);
    const store = configureStore({ reducer: { tenants: reducer } });
    await store.dispatch(loadMyTenants());
    expect(mocked.listMyTenants).toHaveBeenCalled();
    expect(store.getState().tenants.myTenants).toEqual([tenantA, tenantB]);
  });

  it('loadMyTenants surfaces a rejection as the slice error', async () => {
    mocked.listMyTenants.mockRejectedValue(new Error('load failed'));
    const store = configureStore({ reducer: { tenants: reducer } });
    await store.dispatch(loadMyTenants());
    expect(store.getState().tenants.error).toBe('load failed');
  });

  it('createOrganization creates and then reloads the tenant list', async () => {
    mocked.createOrganization.mockResolvedValue({ key: 'tc' } as never);
    mocked.listMyTenants.mockResolvedValue([tenantA] as never);
    const store = configureStore({ reducer: { tenants: reducer } });
    const payload = { name: 'New Org', slug: 'new-org' } as never;
    await store.dispatch(createOrganization(payload));
    expect(mocked.createOrganization).toHaveBeenCalledWith(payload);
    expect(mocked.listMyTenants).toHaveBeenCalled();
    expect(store.getState().tenants.myTenants).toEqual([tenantA]);
  });
});
