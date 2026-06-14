import { describe, it, expect } from 'vitest';
import reducer, {
  clearCurrentRun,
  clearError,
  fetchPlantingRuns,
  fetchPlantingRun,
} from '@/store/slices/plantingRunsSlice';

const baseState = { runs: [], currentRun: null, loading: false, error: null };

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
