import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import reducer, {
  switchTenant,
  clearTenants,
  loadMyTenants,
  createOrganization,
} from '@/store/slices/tenantSlice';
import { getActiveTenantSlug } from '@/api/client';

const ACTIVE_TENANT_KEY = 'kp_active_tenant_slug';

const baseState = {
  activeTenant: null,
  myTenants: [],
  isLoading: false,
  error: null,
};

const tenantA = { key: 'ta', slug: 'garten-a', name: 'Garten A', role: 'admin' };
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
    expect(state.error).toBe('Failed to load tenants');
  });

  it('createOrganization.fulfilled replaces the tenant list', () => {
    const state = reducer(undefined, {
      type: createOrganization.fulfilled.type,
      payload: [tenantA, tenantB],
    });
    expect(state.myTenants).toEqual([tenantA, tenantB]);
  });
});
