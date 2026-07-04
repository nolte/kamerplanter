import { describe, it, expect, vi, beforeEach } from 'vitest';
import { configureStore } from '@reduxjs/toolkit';
import reducer, {
  clearCurrentFertilizer,
  clearError,
  fetchFertilizers,
  fetchFertilizer,
} from '@/store/slices/fertilizersSlice';
import * as fertApi from '@/api/endpoints/fertilizers';

// Isolated module mock — no real HTTP, no handlers.ts.
vi.mock('@/api/endpoints/fertilizers');

const baseState = { fertilizers: [], currentFertilizer: null, loading: false, error: null };

function makeStore() {
  return configureStore({ reducer: { fertilizers: reducer } });
}

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
    expect(state.error).toBe('errors.loadFailed');
  });

  it('fetchFertilizer.fulfilled stores the selected fertilizer', () => {
    const fertilizer = { key: 'f1' };
    const state = reducer(undefined, { type: fetchFertilizer.fulfilled.type, payload: fertilizer });
    expect(state.currentFertilizer).toEqual(fertilizer);
  });
});

describe('fertilizersSlice thunks', () => {
  const mocked = vi.mocked(fertApi);

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('fetchFertilizers calls the API without filters when none are given', async () => {
    mocked.fetchFertilizers.mockResolvedValue([{ key: 'f1' }] as never);
    const store = makeStore();
    await store.dispatch(fetchFertilizers({}));
    expect(mocked.fetchFertilizers).toHaveBeenCalledWith(undefined, undefined, undefined);
    expect(store.getState().fertilizers.fertilizers).toEqual([{ key: 'f1' }]);
  });

  it('fetchFertilizers builds a filter map from the provided options', async () => {
    mocked.fetchFertilizers.mockResolvedValue([] as never);
    const store = makeStore();
    await store.dispatch(
      fetchFertilizers({
        offset: 10,
        limit: 5,
        fertilizerType: 'mineral',
        brand: 'Acme',
        tankSafe: true,
        isOrganic: false,
      }),
    );
    expect(mocked.fetchFertilizers).toHaveBeenCalledWith(10, 5, {
      fertilizer_type: 'mineral',
      brand: 'Acme',
      tank_safe: 'true',
      is_organic: 'false',
    });
  });

  it('fetchFertilizers surfaces a rejection as the slice error', async () => {
    mocked.fetchFertilizers.mockRejectedValue(new Error('load failed'));
    const store = makeStore();
    await store.dispatch(fetchFertilizers({}));
    expect(store.getState().fertilizers.error).toBe('load failed');
  });

  it('fetchFertilizer calls the API and stores the selection', async () => {
    mocked.fetchFertilizer.mockResolvedValue({ key: 'f9' } as never);
    const store = makeStore();
    await store.dispatch(fetchFertilizer('f9'));
    expect(mocked.fetchFertilizer).toHaveBeenCalledWith('f9');
    expect(store.getState().fertilizers.currentFertilizer).toEqual({ key: 'f9' });
  });
});
