import { describe, it, expect, vi, beforeEach } from 'vitest';
import { configureStore } from '@reduxjs/toolkit';
import reducer, {
  clearCurrentTank,
  clearError,
  fetchTanks,
  fetchTank,
} from '@/store/slices/tanksSlice';
import * as tanksApi from '@/api/endpoints/tanks';

// Isolated module mock — no real HTTP, no handlers.ts.
vi.mock('@/api/endpoints/tanks');

function makeStore() {
  return configureStore({ reducer: { tanks: reducer } });
}

const baseState = {
  tanks: [],
  currentTank: null,
  loading: false,
  error: null,
};

describe('tanksSlice', () => {
  it('has the empty initial state', () => {
    const state = reducer(undefined, { type: 'unknown' });
    expect(state).toEqual(baseState);
  });

  it('clearCurrentTank resets the selected tank', () => {
    const state = reducer(
      { ...baseState, currentTank: { key: 't1' } as never },
      clearCurrentTank(),
    );
    expect(state.currentTank).toBeNull();
  });

  it('clearError resets the error', () => {
    const state = reducer({ ...baseState, error: 'boom' }, clearError());
    expect(state.error).toBeNull();
  });

  it('fetchTanks.pending sets loading and clears prior error', () => {
    const state = reducer({ ...baseState, error: 'old' }, { type: fetchTanks.pending.type });
    expect(state.loading).toBe(true);
    expect(state.error).toBeNull();
  });

  it('fetchTanks.fulfilled stores the tanks and stops loading', () => {
    const tanks = [{ key: 't1', name: 'Tank A' }];
    const state = reducer(undefined, { type: fetchTanks.fulfilled.type, payload: tanks });
    expect(state.tanks).toEqual(tanks);
    expect(state.loading).toBe(false);
  });

  it('fetchTanks.rejected stores the error', () => {
    const state = reducer(undefined, {
      type: fetchTanks.rejected.type,
      error: { message: 'Tank fail' },
    });
    expect(state.loading).toBe(false);
    expect(state.error).toBe('Tank fail');
  });

  it('fetchTanks.rejected falls back to a default message when none is given', () => {
    const state = reducer(undefined, { type: fetchTanks.rejected.type, error: {} });
    expect(state.error).toBe('Failed to load tanks');
  });

  it('fetchTank.fulfilled stores the selected tank', () => {
    const tank = { key: 't1', name: 'Tank A' };
    const state = reducer(undefined, { type: fetchTank.fulfilled.type, payload: tank });
    expect(state.currentTank).toEqual(tank);
  });
});

describe('tanksSlice thunks', () => {
  const mocked = vi.mocked(tanksApi);

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('fetchTanks forwards paging/filter args and stores the tanks', async () => {
    mocked.listTanks.mockResolvedValue([{ key: 't1' }] as never);
    const store = makeStore();
    await store.dispatch(fetchTanks({ offset: 0, limit: 20, tankType: 'reservoir' }));
    expect(mocked.listTanks).toHaveBeenCalledWith(0, 20, 'reservoir');
    expect(store.getState().tanks.tanks).toEqual([{ key: 't1' }]);
  });

  it('fetchTanks surfaces a rejection as the slice error', async () => {
    mocked.listTanks.mockRejectedValue(new Error('load failed'));
    const store = makeStore();
    await store.dispatch(fetchTanks({}));
    expect(store.getState().tanks.error).toBe('load failed');
  });

  it('fetchTank calls getTank and stores the selection', async () => {
    mocked.getTank.mockResolvedValue({ key: 't9' } as never);
    const store = makeStore();
    await store.dispatch(fetchTank('t9'));
    expect(mocked.getTank).toHaveBeenCalledWith('t9');
    expect(store.getState().tanks.currentTank).toEqual({ key: 't9' });
  });
});
