import { describe, it, expect, beforeEach, vi } from 'vitest';
import { createTestStore } from '../helpers';

// REQ-045 / REQ-042 — the persistence thunks branch on Light vs Full mode and
// touch localStorage + the preferences API. Mock all three so we can drive both
// branches deterministically without a real backend or storage.
const modeMock = vi.hoisted(() => ({ isLightMode: false }));
vi.mock('@/config/mode', () => ({
  get isLightMode() {
    return modeMock.isLightMode;
  },
}));

const storage = vi.hoisted(() => ({
  writeLocalModuleVisibility: vi.fn(),
  readLocalModuleVisibility: vi.fn(() => ({}) as Record<string, string>),
  clearLocalModuleVisibility: vi.fn(),
  writeLocalDashboardLayout: vi.fn(),
  readLocalDashboardLayout: vi.fn(() => null as unknown),
  clearLocalDashboardLayout: vi.fn(),
}));
vi.mock('@/lib/moduleVisibilityStorage', () => ({
  writeLocalModuleVisibility: storage.writeLocalModuleVisibility,
  readLocalModuleVisibility: storage.readLocalModuleVisibility,
  clearLocalModuleVisibility: storage.clearLocalModuleVisibility,
}));
vi.mock('@/lib/dashboardLayoutStorage', () => ({
  writeLocalDashboardLayout: storage.writeLocalDashboardLayout,
  readLocalDashboardLayout: storage.readLocalDashboardLayout,
  clearLocalDashboardLayout: storage.clearLocalDashboardLayout,
}));

const apiMock = vi.hoisted(() => ({ updatePreferences: vi.fn() }));
vi.mock('@/api/endpoints/userPreferences', () => ({
  updatePreferences: apiMock.updatePreferences,
  getPreferences: vi.fn(),
}));

import {
  saveModuleVisibility,
  saveDashboardLayout,
  migrateLocalModuleVisibility,
  migrateLocalDashboardLayout,
} from '@/store/slices/userPreferencesSlice';

function createStore(preloaded?: unknown) {
  return createTestStore(
    preloaded ? { userPreferences: { preferences: preloaded, loading: false, error: null } } : undefined,
  );
}

beforeEach(() => {
  vi.clearAllMocks();
  modeMock.isLightMode = false;
  storage.readLocalModuleVisibility.mockReturnValue({});
  storage.readLocalDashboardLayout.mockReturnValue(null);
});

describe('saveModuleVisibility thunk body', () => {
  it('writes to localStorage and skips the API in Light mode', async () => {
    modeMock.isLightMode = true;
    const store = createStore({ module_visibility: {} });
    const overrides = { pests: 'enabled' as const };
    await store.dispatch(saveModuleVisibility(overrides));
    expect(storage.writeLocalModuleVisibility).toHaveBeenCalledWith(overrides);
    expect(apiMock.updatePreferences).not.toHaveBeenCalled();
    expect(store.getState().userPreferences.preferences?.module_visibility).toEqual(overrides);
  });

  it('PATCHes the server in Full mode', async () => {
    apiMock.updatePreferences.mockResolvedValue({ module_visibility: { pests: 'enabled' } });
    const store = createStore({ module_visibility: {} });
    await store.dispatch(saveModuleVisibility({ pests: 'enabled' }));
    expect(apiMock.updatePreferences).toHaveBeenCalledWith({ module_visibility: { pests: 'enabled' } });
  });

  it('falls back to an empty object when the server omits module_visibility', async () => {
    apiMock.updatePreferences.mockResolvedValue({});
    const store = createStore({ module_visibility: { a: 'disabled' } });
    await store.dispatch(saveModuleVisibility({ a: 'disabled' }));
    expect(store.getState().userPreferences.preferences?.module_visibility).toEqual({});
  });
});

describe('saveDashboardLayout thunk body', () => {
  const layout = { widgets: [{ id: 'w1' }] } as unknown as Record<string, unknown>;

  it('writes to localStorage and skips the API in Light mode', async () => {
    modeMock.isLightMode = true;
    const store = createStore({ dashboard_layout: null });
    await store.dispatch(saveDashboardLayout(layout as never));
    expect(storage.writeLocalDashboardLayout).toHaveBeenCalledWith(layout);
    expect(apiMock.updatePreferences).not.toHaveBeenCalled();
  });

  it('PATCHes the server and reconciles the sanitized layout in Full mode', async () => {
    apiMock.updatePreferences.mockResolvedValue({ dashboard_layout: { widgets: [] } });
    const store = createStore({ dashboard_layout: null });
    await store.dispatch(saveDashboardLayout(layout as never));
    expect(apiMock.updatePreferences).toHaveBeenCalledWith({ dashboard_layout: layout });
    expect(store.getState().userPreferences.preferences?.dashboard_layout).toEqual({ widgets: [] });
  });

  it('coerces a missing server layout to null', async () => {
    apiMock.updatePreferences.mockResolvedValue({});
    const store = createStore({ dashboard_layout: layout });
    await store.dispatch(saveDashboardLayout(null));
    expect(store.getState().userPreferences.preferences?.dashboard_layout).toBeNull();
  });
});

describe('migrateLocalModuleVisibility thunk body', () => {
  it('returns null in Light mode (nothing to migrate to the server)', async () => {
    modeMock.isLightMode = true;
    const store = createStore({ module_visibility: {} });
    const res = await store.dispatch(migrateLocalModuleVisibility());
    expect(res.payload).toBeNull();
    expect(apiMock.updatePreferences).not.toHaveBeenCalled();
  });

  it('returns null when there are no local overrides', async () => {
    storage.readLocalModuleVisibility.mockReturnValue({});
    const store = createStore({ module_visibility: {} });
    const res = await store.dispatch(migrateLocalModuleVisibility());
    expect(res.payload).toBeNull();
  });

  it('merges local over server overrides, PATCHes, and clears local', async () => {
    storage.readLocalModuleVisibility.mockReturnValue({ pests: 'enabled' });
    apiMock.updatePreferences.mockResolvedValue({ module_visibility: { pests: 'enabled', tanks: 'disabled' } });
    const store = createStore({ module_visibility: { tanks: 'disabled' } });
    await store.dispatch(migrateLocalModuleVisibility());
    expect(apiMock.updatePreferences).toHaveBeenCalledWith({
      module_visibility: { tanks: 'disabled', pests: 'enabled' },
    });
    expect(storage.clearLocalModuleVisibility).toHaveBeenCalled();
  });
});

describe('migrateLocalDashboardLayout thunk body', () => {
  const layout = { widgets: [] } as unknown as Record<string, unknown>;

  it('returns null in Light mode', async () => {
    modeMock.isLightMode = true;
    const store = createStore({ dashboard_layout: null });
    const res = await store.dispatch(migrateLocalDashboardLayout());
    expect(res.payload).toBeNull();
  });

  it('returns null when there is no local layout', async () => {
    storage.readLocalDashboardLayout.mockReturnValue(null);
    const store = createStore({ dashboard_layout: null });
    const res = await store.dispatch(migrateLocalDashboardLayout());
    expect(res.payload).toBeNull();
  });

  it('discards the local layout when the server already has one', async () => {
    storage.readLocalDashboardLayout.mockReturnValue(layout);
    const store = createStore({ dashboard_layout: { widgets: [{ id: 'x' }] } });
    const res = await store.dispatch(migrateLocalDashboardLayout());
    expect(res.payload).toBeNull();
    expect(storage.clearLocalDashboardLayout).toHaveBeenCalled();
    expect(apiMock.updatePreferences).not.toHaveBeenCalled();
  });

  it('PATCHes the local layout when the server has none, then clears local', async () => {
    storage.readLocalDashboardLayout.mockReturnValue(layout);
    apiMock.updatePreferences.mockResolvedValue({ dashboard_layout: layout });
    const store = createStore({ dashboard_layout: null });
    await store.dispatch(migrateLocalDashboardLayout());
    expect(apiMock.updatePreferences).toHaveBeenCalledWith({ dashboard_layout: layout });
    expect(storage.clearLocalDashboardLayout).toHaveBeenCalled();
  });
});
