import { describe, it, expect } from 'vitest';
import reducer, {
  clearCurrentBatch,
  clearError,
  fetchIndicators,
  fetchBatches,
  fetchBatch,
  fetchQuality,
  fetchYieldMetric,
  fetchObservations,
  fetchReadiness,
} from '@/store/slices/harvestSlice';

const baseState = {
  indicators: [],
  observations: [],
  batches: [],
  currentBatch: null,
  quality: null,
  yieldMetric: null,
  readiness: null,
  loading: false,
  error: null,
};

describe('harvestSlice', () => {
  it('has the empty initial state', () => {
    expect(reducer(undefined, { type: 'unknown' })).toEqual(baseState);
  });

  it('clearCurrentBatch resets batch, quality and yield', () => {
    const state = reducer(
      {
        ...baseState,
        currentBatch: { key: 'b1' } as never,
        quality: { score: 9 } as never,
        yieldMetric: { grams: 100 } as never,
      },
      clearCurrentBatch(),
    );
    expect(state.currentBatch).toBeNull();
    expect(state.quality).toBeNull();
    expect(state.yieldMetric).toBeNull();
  });

  it('clearError resets the error', () => {
    const state = reducer({ ...baseState, error: 'boom' }, clearError());
    expect(state.error).toBeNull();
  });

  it('fetchIndicators.pending sets loading and clears prior error', () => {
    const state = reducer({ ...baseState, error: 'old' }, { type: fetchIndicators.pending.type });
    expect(state.loading).toBe(true);
    expect(state.error).toBeNull();
  });

  it('fetchIndicators.fulfilled stores indicators', () => {
    const indicators = [{ key: 'i1' }];
    const state = reducer(undefined, { type: fetchIndicators.fulfilled.type, payload: indicators });
    expect(state.indicators).toEqual(indicators);
    expect(state.loading).toBe(false);
  });

  it('fetchIndicators.rejected stores the error', () => {
    const state = reducer(undefined, {
      type: fetchIndicators.rejected.type,
      error: { message: 'Indicator fail' },
    });
    expect(state.error).toBe('Indicator fail');
  });

  it('fetchIndicators.rejected falls back to a default message', () => {
    const state = reducer(undefined, { type: fetchIndicators.rejected.type, error: {} });
    expect(state.error).toBe('Failed to load indicators');
  });

  it('fetchBatches.fulfilled stores batches', () => {
    const batches = [{ key: 'b1' }];
    const state = reducer(undefined, { type: fetchBatches.fulfilled.type, payload: batches });
    expect(state.batches).toEqual(batches);
  });

  it('fetchBatches.rejected falls back to a default message', () => {
    const state = reducer(undefined, { type: fetchBatches.rejected.type, error: {} });
    expect(state.error).toBe('Failed to load batches');
  });

  it('fetchBatch.fulfilled stores the current batch', () => {
    const batch = { key: 'b1' };
    const state = reducer(undefined, { type: fetchBatch.fulfilled.type, payload: batch });
    expect(state.currentBatch).toEqual(batch);
  });

  it('fetchQuality.fulfilled stores the quality assessment', () => {
    const quality = { score: 9 };
    const state = reducer(undefined, { type: fetchQuality.fulfilled.type, payload: quality });
    expect(state.quality).toEqual(quality);
  });

  it('fetchYieldMetric.fulfilled stores the yield metric', () => {
    const yieldMetric = { grams: 100 };
    const state = reducer(undefined, { type: fetchYieldMetric.fulfilled.type, payload: yieldMetric });
    expect(state.yieldMetric).toEqual(yieldMetric);
  });

  it('fetchObservations.fulfilled stores observations', () => {
    const observations = [{ key: 'o1' }];
    const state = reducer(undefined, { type: fetchObservations.fulfilled.type, payload: observations });
    expect(state.observations).toEqual(observations);
  });

  it('fetchReadiness.fulfilled stores the readiness assessment', () => {
    const readiness = { ready: true };
    const state = reducer(undefined, { type: fetchReadiness.fulfilled.type, payload: readiness });
    expect(state.readiness).toEqual(readiness);
  });
});
