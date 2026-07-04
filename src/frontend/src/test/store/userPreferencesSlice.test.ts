import { describe, it, expect } from 'vitest';
import { configureStore } from '@reduxjs/toolkit';
import reducer, {
  clearError,
  fetchPreferences,
  updateUserPreferences,
} from '@/store/slices/userPreferencesSlice';

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
});
