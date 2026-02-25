import { describe, it, expect } from 'vitest';
import { configureStore } from '@reduxjs/toolkit';
import reducer, {
  fetchSubstrates,
  fetchSubstrate,
  clearCurrent,
  clearError,
} from '@/store/slices/substratesSlice';

function createStore() {
  return configureStore({ reducer: { substrates: reducer } });
}

describe('substratesSlice', () => {
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

  it('fetchSubstrates.pending sets loading', () => {
    const state = reducer(undefined, { type: fetchSubstrates.pending.type });
    expect(state.loading).toBe(true);
  });

  it('fetchSubstrates.fulfilled sets items', () => {
    const items = [{ key: 'sub1', type: 'soil' }];
    const state = reducer(undefined, {
      type: fetchSubstrates.fulfilled.type,
      payload: items,
    });
    expect(state.items).toEqual(items);
    expect(state.loading).toBe(false);
  });

  it('fetchSubstrates.rejected sets error', () => {
    const state = reducer(undefined, {
      type: fetchSubstrates.rejected.type,
      error: { message: 'Fail' },
    });
    expect(state.error).toBe('Fail');
  });

  it('fetchSubstrate.fulfilled sets current', () => {
    const substrate = { key: 'sub1', type: 'coco' };
    const state = reducer(undefined, {
      type: fetchSubstrate.fulfilled.type,
      payload: substrate,
    });
    expect(state.current).toEqual(substrate);
  });

  it('fetches substrates via thunk with MSW', async () => {
    const store = createStore();
    await store.dispatch(fetchSubstrates({}));
    const state = store.getState().substrates;
    expect(state.items).toEqual([]);
    expect(state.loading).toBe(false);
  });
});
