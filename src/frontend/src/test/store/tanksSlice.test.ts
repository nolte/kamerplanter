import { describe, it, expect } from 'vitest';
import reducer, {
  clearCurrentTank,
  clearError,
  fetchTanks,
  fetchTank,
} from '@/store/slices/tanksSlice';

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
