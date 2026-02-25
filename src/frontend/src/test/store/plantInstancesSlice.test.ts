import { describe, it, expect } from 'vitest';
import { configureStore } from '@reduxjs/toolkit';
import reducer, {
  fetchPlantInstances,
  fetchPlantInstance,
  clearCurrent,
  clearError,
} from '@/store/slices/plantInstancesSlice';

function createStore() {
  return configureStore({ reducer: { plantInstances: reducer } });
}

describe('plantInstancesSlice', () => {
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
      { items: [], current: null, loading: false, error: 'err' },
      clearError(),
    );
    expect(state.error).toBeNull();
  });

  it('fetchPlantInstances.pending sets loading', () => {
    const state = reducer(undefined, { type: fetchPlantInstances.pending.type });
    expect(state.loading).toBe(true);
  });

  it('fetchPlantInstances.fulfilled sets items', () => {
    const items = [{ key: 'p1', instance_id: 'TOM-001' }];
    const state = reducer(undefined, {
      type: fetchPlantInstances.fulfilled.type,
      payload: items,
    });
    expect(state.items).toEqual(items);
    expect(state.loading).toBe(false);
  });

  it('fetchPlantInstances.rejected sets error', () => {
    const state = reducer(undefined, {
      type: fetchPlantInstances.rejected.type,
      error: { message: 'Fail' },
    });
    expect(state.error).toBe('Fail');
  });

  it('fetchPlantInstance.fulfilled sets current', () => {
    const plant = { key: 'p1', plant_name: 'Big Red' };
    const state = reducer(undefined, {
      type: fetchPlantInstance.fulfilled.type,
      payload: plant,
    });
    expect(state.current).toEqual(plant);
  });

  it('fetches plant instances via thunk with MSW', async () => {
    const store = createStore();
    await store.dispatch(fetchPlantInstances({}));
    const state = store.getState().plantInstances;
    expect(state.items.length).toBe(1);
    expect(state.items[0].plant_name).toBe('Big Red');
  });
});
