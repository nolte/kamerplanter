import { describe, it, expect, vi, beforeEach } from 'vitest';
import { configureStore } from '@reduxjs/toolkit';
import reducer, {
  clearCurrentRun,
  clearError,
  fetchPlantingRuns,
  fetchPlantingRun,
} from '@/store/slices/plantingRunsSlice';
import * as runsApi from '@/api/endpoints/plantingRuns';

// Isolated module mock — no real HTTP, no handlers.ts.
vi.mock('@/api/endpoints/plantingRuns');

const baseState = { runs: [], currentRun: null, loading: false, error: null };

function makeStore() {
  return configureStore({ reducer: { plantingRuns: reducer } });
}

describe('plantingRunsSlice', () => {
  it('has the empty initial state', () => {
    expect(reducer(undefined, { type: 'unknown' })).toEqual(baseState);
  });

  it('clearCurrentRun resets the selection', () => {
    const state = reducer({ ...baseState, currentRun: { key: 'r1' } as never }, clearCurrentRun());
    expect(state.currentRun).toBeNull();
  });

  it('clearError resets the error', () => {
    const state = reducer({ ...baseState, error: 'boom' }, clearError());
    expect(state.error).toBeNull();
  });

  it('fetchPlantingRuns.pending sets loading and clears prior error', () => {
    const state = reducer({ ...baseState, error: 'old' }, { type: fetchPlantingRuns.pending.type });
    expect(state.loading).toBe(true);
    expect(state.error).toBeNull();
  });

  it('fetchPlantingRuns.fulfilled stores the runs', () => {
    const runs = [{ key: 'r1' }];
    const state = reducer(undefined, { type: fetchPlantingRuns.fulfilled.type, payload: runs });
    expect(state.runs).toEqual(runs);
    expect(state.loading).toBe(false);
  });

  it('fetchPlantingRuns.rejected stores the error', () => {
    const state = reducer(undefined, { type: fetchPlantingRuns.rejected.type, error: { message: 'fail' } });
    expect(state.error).toBe('fail');
  });

  it('fetchPlantingRuns.rejected falls back to a default message', () => {
    const state = reducer(undefined, { type: fetchPlantingRuns.rejected.type, error: {} });
    expect(state.error).toBe('Failed to load planting runs');
  });

  it('fetchPlantingRun.fulfilled stores the selected run', () => {
    const run = { key: 'r1' };
    const state = reducer(undefined, { type: fetchPlantingRun.fulfilled.type, payload: run });
    expect(state.currentRun).toEqual(run);
  });
});

describe('plantingRunsSlice thunks', () => {
  const mocked = vi.mocked(runsApi);

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('fetchPlantingRuns forwards paging/filter args and stores the runs', async () => {
    mocked.listPlantingRuns.mockResolvedValue([{ key: 'r1' }] as never);
    const store = makeStore();
    await store.dispatch(fetchPlantingRuns({ offset: 5, limit: 10, status: 'active', runType: 'seed' }));
    expect(mocked.listPlantingRuns).toHaveBeenCalledWith(5, 10, 'active', 'seed');
    expect(store.getState().plantingRuns.runs).toEqual([{ key: 'r1' }]);
  });

  it('fetchPlantingRuns surfaces a rejection as the slice error', async () => {
    mocked.listPlantingRuns.mockRejectedValue(new Error('load failed'));
    const store = makeStore();
    await store.dispatch(fetchPlantingRuns({}));
    expect(store.getState().plantingRuns.error).toBe('load failed');
  });

  it('fetchPlantingRun calls getPlantingRun and stores the selection', async () => {
    mocked.getPlantingRun.mockResolvedValue({ key: 'r9' } as never);
    const store = makeStore();
    await store.dispatch(fetchPlantingRun('r9'));
    expect(mocked.getPlantingRun).toHaveBeenCalledWith('r9');
    expect(store.getState().plantingRuns.currentRun).toEqual({ key: 'r9' });
  });
});
