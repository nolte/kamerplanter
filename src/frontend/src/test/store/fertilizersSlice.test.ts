import { describe, it, expect } from 'vitest';
import reducer, {
  clearCurrentFertilizer,
  clearError,
  fetchFertilizers,
  fetchFertilizer,
} from '@/store/slices/fertilizersSlice';

const baseState = { fertilizers: [], currentFertilizer: null, loading: false, error: null };

describe('fertilizersSlice', () => {
  it('has the empty initial state', () => {
    expect(reducer(undefined, { type: 'unknown' })).toEqual(baseState);
  });

  it('clearCurrentFertilizer resets the selection', () => {
    const state = reducer({ ...baseState, currentFertilizer: { key: 'f1' } as never }, clearCurrentFertilizer());
    expect(state.currentFertilizer).toBeNull();
  });

  it('clearError resets the error', () => {
    const state = reducer({ ...baseState, error: 'boom' }, clearError());
    expect(state.error).toBeNull();
  });

  it('fetchFertilizers.pending sets loading and clears prior error', () => {
    const state = reducer({ ...baseState, error: 'old' }, { type: fetchFertilizers.pending.type });
    expect(state.loading).toBe(true);
    expect(state.error).toBeNull();
  });

  it('fetchFertilizers.fulfilled stores the fertilizers', () => {
    const fertilizers = [{ key: 'f1' }];
    const state = reducer(undefined, { type: fetchFertilizers.fulfilled.type, payload: fertilizers });
    expect(state.fertilizers).toEqual(fertilizers);
    expect(state.loading).toBe(false);
  });

  it('fetchFertilizers.rejected stores the error', () => {
    const state = reducer(undefined, { type: fetchFertilizers.rejected.type, error: { message: 'fail' } });
    expect(state.error).toBe('fail');
  });

  it('fetchFertilizers.rejected falls back to a default message', () => {
    const state = reducer(undefined, { type: fetchFertilizers.rejected.type, error: {} });
    expect(state.error).toBe('Failed to load fertilizers');
  });

  it('fetchFertilizer.fulfilled stores the selected fertilizer', () => {
    const fertilizer = { key: 'f1' };
    const state = reducer(undefined, { type: fetchFertilizer.fulfilled.type, payload: fertilizer });
    expect(state.currentFertilizer).toEqual(fertilizer);
  });
});
