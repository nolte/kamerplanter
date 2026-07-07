import { describe, it, expect } from 'vitest';
import { configureStore } from '@reduxjs/toolkit';
import reducer, {
  clearError,
  fetchPreferences,
  updateUserPreferences,
  saveModuleVisibility,
  saveDashboardLayout,
  migrateLocalModuleVisibility,
  migrateLocalDashboardLayout,
} from '@/store/slices/userPreferencesSlice';
import type { UserPreference, DashboardLayout } from '@/api/types';

const prefWith = (over: Partial<UserPreference> = {}): UserPreference =>
  ({ experience_level: 'intermediate', ...over }) as UserPreference;

const stateWith = (pref: UserPreference | null) => ({
  preferences: pref,
  loading: false,
  error: null,
});

function createStore() {
  return configureStore({ reducer: { userPreferences: reducer } });
}

describe('userPreferencesSlice', () => {
  it('has the empty initial state', () => {
    const state = reducer(undefined, { type: 'unknown' });
    expect(state.preferences).toBeNull();
    expect(state.loading).toBe(false);
    expect(state.error).toBeNull();
  });

  it('clearError removes a stored error message', () => {
    const withError = { preferences: null, loading: false, error: 'Boom' };
    const state = reducer(withError, clearError());
    expect(state.error).toBeNull();
  });

  it('fetchPreferences.pending sets loading and clears prior error', () => {
    const withError = { preferences: null, loading: false, error: 'old' };
    const state = reducer(withError, { type: fetchPreferences.pending.type });
    expect(state.loading).toBe(true);
    expect(state.error).toBeNull();
  });

  it('fetchPreferences.fulfilled stores the preferences and stops loading', () => {
    const prefs = { experience_level: 'expert', locale: 'de', theme: 'dark' };
    const state = reducer(undefined, {
      type: fetchPreferences.fulfilled.type,
      payload: prefs,
    });
    expect(state.preferences).toEqual(prefs);
    expect(state.loading).toBe(false);
  });

  it('fetchPreferences.rejected stores the error message', () => {
    const state = reducer(undefined, {
      type: fetchPreferences.rejected.type,
      error: { message: 'Network down' },
    });
    expect(state.loading).toBe(false);
    expect(state.error).toBe('Network down');
  });

  it('fetchPreferences.rejected falls back to a default message when none is given', () => {
    const state = reducer(undefined, {
      type: fetchPreferences.rejected.type,
      error: {},
    });
    expect(state.error).toBe('errors.preferencesLoadFailed');
  });

  it('updateUserPreferences.fulfilled replaces the stored preferences', () => {
    const existing = { preferences: { theme: 'light' } as never, loading: false, error: null };
    const updated = { experience_level: 'beginner', theme: 'dark' };
    const state = reducer(existing, {
      type: updateUserPreferences.fulfilled.type,
      payload: updated,
    });
    expect(state.preferences).toEqual(updated);
  });

  it('updates state through the store when dispatching the update action', () => {
    const store = createStore();
    store.dispatch({
      type: updateUserPreferences.fulfilled.type,
      payload: { theme: 'dark' },
    });
    expect(store.getState().userPreferences.preferences).toEqual({ theme: 'dark' });
  });

  it('loads preferences via the fetchPreferences thunk against the mocked API', async () => {
    const store = createStore();
    await store.dispatch(fetchPreferences());
    const state = store.getState().userPreferences;
    expect(state.preferences?.experience_level).toBe('intermediate');
    expect(state.loading).toBe(false);
  });

  it('persists changes via the updateUserPreferences thunk', async () => {
    const store = createStore();
    await store.dispatch(updateUserPreferences({ updates: { theme: 'dark' } }));
    expect(store.getState().userPreferences.preferences?.theme).toBe('dark');
  });

  // REQ-042 module visibility
  describe('saveModuleVisibility.fulfilled', () => {
    it('replaces the module_visibility override set', () => {
      const start = stateWith(prefWith({ module_visibility: {} }));
      const overrides = { pests: 'enabled' as const };
      const next = reducer(start, {
        type: saveModuleVisibility.fulfilled.type,
        payload: overrides,
      });
      expect(next.preferences?.module_visibility).toEqual(overrides);
    });

    it('is a no-op when no preferences are loaded yet', () => {
      const next = reducer(stateWith(null), {
        type: saveModuleVisibility.fulfilled.type,
        payload: { pests: 'enabled' },
      });
      expect(next.preferences).toBeNull();
    });
  });

  describe('migrateLocalModuleVisibility.fulfilled', () => {
    it('adopts the migrated server preference', () => {
      const migrated = prefWith({ module_visibility: { pests: 'disabled' } });
      const next = reducer(stateWith(null), {
        type: migrateLocalModuleVisibility.fulfilled.type,
        payload: migrated,
      });
      expect(next.preferences).toEqual(migrated);
    });

    it('keeps existing preferences when the migration yields null', () => {
      const existing = prefWith({ theme: 'dark' });
      const next = reducer(stateWith(existing), {
        type: migrateLocalModuleVisibility.fulfilled.type,
        payload: null,
      });
      expect(next.preferences).toEqual(existing);
    });
  });

  // REQ-045 dashboard layout
  describe('saveDashboardLayout', () => {
    const layout = { widgets: [{ id: 'w1' }] } as unknown as DashboardLayout;

    it('optimistically applies the arg layout on pending', () => {
      const next = reducer(stateWith(prefWith()), {
        type: saveDashboardLayout.pending.type,
        meta: { arg: layout },
      });
      expect(next.preferences?.dashboard_layout).toEqual(layout);
    });

    it('reconciles with the server-sanitized layout on fulfilled', () => {
      const sanitized = { widgets: [] } as unknown as DashboardLayout;
      const next = reducer(stateWith(prefWith({ dashboard_layout: layout })), {
        type: saveDashboardLayout.fulfilled.type,
        payload: sanitized,
      });
      expect(next.preferences?.dashboard_layout).toEqual(sanitized);
    });

    it('pending is a no-op without loaded preferences', () => {
      const next = reducer(stateWith(null), {
        type: saveDashboardLayout.pending.type,
        meta: { arg: layout },
      });
      expect(next.preferences).toBeNull();
    });
  });

  describe('migrateLocalDashboardLayout.fulfilled', () => {
    it('adopts the migrated preference when present', () => {
      const migrated = prefWith({ dashboard_layout: { widgets: [] } as unknown as DashboardLayout });
      const next = reducer(stateWith(null), {
        type: migrateLocalDashboardLayout.fulfilled.type,
        payload: migrated,
      });
      expect(next.preferences).toEqual(migrated);
    });

    it('is a no-op when the migration yields null', () => {
      const existing = prefWith();
      const next = reducer(stateWith(existing), {
        type: migrateLocalDashboardLayout.fulfilled.type,
        payload: null,
      });
      expect(next.preferences).toEqual(existing);
    });
  });
});
