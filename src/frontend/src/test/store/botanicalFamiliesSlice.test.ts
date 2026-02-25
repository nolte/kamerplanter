import { describe, it, expect } from 'vitest';
import { configureStore } from '@reduxjs/toolkit';
import reducer, {
  fetchBotanicalFamilies,
  fetchBotanicalFamily,
  clearCurrent,
  clearError,
} from '@/store/slices/botanicalFamiliesSlice';

// Uses MSW handlers from test setup
function createStore() {
  return configureStore({ reducer: { botanicalFamilies: reducer } });
}

describe('botanicalFamiliesSlice', () => {
  it('has correct initial state', () => {
    const state = reducer(undefined, { type: 'unknown' });
    expect(state.items).toEqual([]);
    expect(state.current).toBeNull();
    expect(state.loading).toBe(false);
    expect(state.error).toBeNull();
  });

  it('clearCurrent resets current', () => {
    const state = reducer(
      { items: [], current: { key: 'x' } as never, loading: false, error: null },
      clearCurrent(),
    );
    expect(state.current).toBeNull();
  });

  it('clearError resets error', () => {
    const state = reducer(
      { items: [], current: null, loading: false, error: 'some error' },
      clearError(),
    );
    expect(state.error).toBeNull();
  });

  it('fetchBotanicalFamilies.pending sets loading', () => {
    const state = reducer(undefined, { type: fetchBotanicalFamilies.pending.type });
    expect(state.loading).toBe(true);
    expect(state.error).toBeNull();
  });

  it('fetchBotanicalFamilies.fulfilled sets items', () => {
    const families = [{ key: 'f1', name: 'Solanaceae' }];
    const state = reducer(undefined, {
      type: fetchBotanicalFamilies.fulfilled.type,
      payload: families,
    });
    expect(state.loading).toBe(false);
    expect(state.items).toEqual(families);
  });

  it('fetchBotanicalFamilies.rejected sets error', () => {
    const state = reducer(undefined, {
      type: fetchBotanicalFamilies.rejected.type,
      error: { message: 'Network Error' },
    });
    expect(state.loading).toBe(false);
    expect(state.error).toBe('Network Error');
  });

  it('fetches families via thunk with MSW', async () => {
    const store = createStore();
    await store.dispatch(fetchBotanicalFamilies({}));
    const state = store.getState().botanicalFamilies;
    expect(state.items.length).toBe(2);
    expect(state.items[0].name).toBe('Solanaceae');
  });

  it('fetchBotanicalFamily.fulfilled sets current', () => {
    const family = { key: 'f1', name: 'Solanaceae' };
    const state = reducer(undefined, {
      type: fetchBotanicalFamily.fulfilled.type,
      payload: family,
    });
    expect(state.current).toEqual(family);
    expect(state.loading).toBe(false);
  });
});
