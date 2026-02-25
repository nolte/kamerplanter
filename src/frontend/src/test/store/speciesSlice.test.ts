import { describe, it, expect } from 'vitest';
import { configureStore } from '@reduxjs/toolkit';
import reducer, {
  fetchSpeciesList,
  fetchSpecies,
  clearCurrent,
  clearError,
} from '@/store/slices/speciesSlice';

function createStore() {
  return configureStore({ reducer: { species: reducer } });
}

describe('speciesSlice', () => {
  it('has correct initial state', () => {
    const state = reducer(undefined, { type: 'unknown' });
    expect(state.items).toEqual([]);
    expect(state.total).toBe(0);
    expect(state.offset).toBe(0);
    expect(state.limit).toBe(50);
    expect(state.current).toBeNull();
    expect(state.loading).toBe(false);
    expect(state.error).toBeNull();
  });

  it('clearCurrent resets current', () => {
    const state = reducer(
      { items: [], total: 0, offset: 0, limit: 50, current: { key: 'x' } as never, loading: false, error: null },
      clearCurrent(),
    );
    expect(state.current).toBeNull();
  });

  it('clearError resets error', () => {
    const state = reducer(
      { items: [], total: 0, offset: 0, limit: 50, current: null, loading: false, error: 'err' },
      clearError(),
    );
    expect(state.error).toBeNull();
  });

  it('fetchSpeciesList.pending sets loading', () => {
    const state = reducer(undefined, { type: fetchSpeciesList.pending.type });
    expect(state.loading).toBe(true);
  });

  it('fetchSpeciesList.fulfilled sets items with pagination', () => {
    const payload = { items: [{ key: 's1' }], total: 1, offset: 0, limit: 50 };
    const state = reducer(undefined, {
      type: fetchSpeciesList.fulfilled.type,
      payload,
    });
    expect(state.loading).toBe(false);
    expect(state.items).toEqual([{ key: 's1' }]);
    expect(state.total).toBe(1);
  });

  it('fetchSpeciesList.rejected sets error', () => {
    const state = reducer(undefined, {
      type: fetchSpeciesList.rejected.type,
      error: { message: 'Fail' },
    });
    expect(state.loading).toBe(false);
    expect(state.error).toBe('Fail');
  });

  it('fetches species list via thunk with MSW', async () => {
    const store = createStore();
    await store.dispatch(fetchSpeciesList({}));
    const state = store.getState().species;
    expect(state.items.length).toBe(1);
    expect(state.items[0].scientific_name).toBe('Solanum lycopersicum');
    expect(state.total).toBe(1);
  });

  it('fetchSpecies.fulfilled sets current', () => {
    const species = { key: 's1', scientific_name: 'Test' };
    const state = reducer(undefined, {
      type: fetchSpecies.fulfilled.type,
      payload: species,
    });
    expect(state.current).toEqual(species);
  });
});
