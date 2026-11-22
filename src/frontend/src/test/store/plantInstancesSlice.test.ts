import { describe, it, expect } from 'vitest';
import { configureStore } from '@reduxjs/toolkit';
import reducer, {
  fetchAllPlantInstances,
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
      {
        items: [],
        total: 0,
        offset: 0,
        limit: 50,
        current: { key: 'x' } as never,
        loading: false,
        error: null,
      },
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
    expect(state.error).toBe('errors.loadFailed');
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

  describe('fetchAllPlantInstances', () => {
    const plants = [{ key: 'a' }, { key: 'b' }] as never[];
    const meta = { requestId: 'r1', requestStatus: 'pending', arg: undefined };

    function afterPages() {
      let state = reducer(undefined, { type: fetchAllPlantInstances.pending.type, meta });
      state = reducer(state, {
        type: 'plantInstances/pageLoaded',
        payload: { requestId: 'r1', items: plants, first: true, done: true },
      });
      return state;
    }

    it('keeps the items the pages already delivered, so effects keyed on them do not re-run', () => {
      const loaded = afterPages();
      const done = reducer(loaded, {
        type: fetchAllPlantInstances.fulfilled.type,
        meta,
        payload: [...plants],
      });
      expect(done.items).toBe(loaded.items);
      expect(done.loading).toBe(false);
    });

    it('takes the payload when the pages did not deliver the complete set', () => {
      const loaded = afterPages();
      const complete = [...plants, { key: 'c' }] as never[];
      const done = reducer(loaded, {
        type: fetchAllPlantInstances.fulfilled.type,
        meta,
        payload: complete,
      });
      expect(done.items.map((p) => p.key)).toEqual(['a', 'b', 'c']);
    });
  });
});
