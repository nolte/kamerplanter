import { describe, it, expect, vi, beforeEach } from 'vitest';
import { configureStore } from '@reduxjs/toolkit';
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
import * as harvestApi from '@/api/endpoints/harvest';

// Isolated module mock — no real HTTP, no handlers.ts.
vi.mock('@/api/endpoints/harvest');

function makeHarvestStore() {
  return configureStore({ reducer: { harvest: reducer } });
}

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
    expect(state.error).toBe('errors.loadFailed');
  });

  it('fetchBatches.fulfilled stores batches', () => {
    const batches = [{ key: 'b1' }];
    const state = reducer(undefined, { type: fetchBatches.fulfilled.type, payload: batches });
    expect(state.batches).toEqual(batches);
  });

  it('fetchBatches.rejected falls back to a default message', () => {
    const state = reducer(undefined, { type: fetchBatches.rejected.type, error: {} });
    expect(state.error).toBe('errors.loadFailed');
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

describe('harvestSlice thunks', () => {
  const mocked = vi.mocked(harvestApi);

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('fetchIndicators forwards paging and stores indicators', async () => {
    mocked.getIndicators.mockResolvedValue([{ key: 'i1' }] as never);
    const store = makeHarvestStore();
    await store.dispatch(fetchIndicators({ offset: 0, limit: 10 }));
    expect(mocked.getIndicators).toHaveBeenCalledWith(0, 10);
    expect(store.getState().harvest.indicators).toEqual([{ key: 'i1' }]);
  });

  it('fetchBatches forwards paging and stores batches', async () => {
    mocked.getBatches.mockResolvedValue([{ key: 'b1' }] as never);
    const store = makeHarvestStore();
    await store.dispatch(fetchBatches({}));
    expect(mocked.getBatches).toHaveBeenCalledWith(undefined, undefined);
    expect(store.getState().harvest.batches).toEqual([{ key: 'b1' }]);
  });

  it('fetchBatches surfaces a rejection as the slice error', async () => {
    mocked.getBatches.mockRejectedValue(new Error('load failed'));
    const store = makeHarvestStore();
    await store.dispatch(fetchBatches({}));
    expect(store.getState().harvest.error).toBe('load failed');
  });

  it('fetchBatch stores the current batch', async () => {
    mocked.getBatch.mockResolvedValue({ key: 'b9' } as never);
    const store = makeHarvestStore();
    await store.dispatch(fetchBatch('b9'));
    expect(mocked.getBatch).toHaveBeenCalledWith('b9');
    expect(store.getState().harvest.currentBatch).toEqual({ key: 'b9' });
  });

  it('fetchQuality stores the quality assessment', async () => {
    mocked.getQuality.mockResolvedValue({ score: 9 } as never);
    const store = makeHarvestStore();
    await store.dispatch(fetchQuality('b9'));
    expect(mocked.getQuality).toHaveBeenCalledWith('b9');
    expect(store.getState().harvest.quality).toEqual({ score: 9 });
  });

  it('fetchYieldMetric stores the yield metric', async () => {
    mocked.getYield.mockResolvedValue({ grams: 100 } as never);
    const store = makeHarvestStore();
    await store.dispatch(fetchYieldMetric('b9'));
    expect(mocked.getYield).toHaveBeenCalledWith('b9');
    expect(store.getState().harvest.yieldMetric).toEqual({ grams: 100 });
  });

  it('fetchObservations forwards its args and stores observations', async () => {
    mocked.getObservations.mockResolvedValue([{ key: 'o1' }] as never);
    const store = makeHarvestStore();
    await store.dispatch(fetchObservations({ plantKey: 'pl1', offset: 0, limit: 5 }));
    expect(mocked.getObservations).toHaveBeenCalledWith('pl1', 0, 5);
    expect(store.getState().harvest.observations).toEqual([{ key: 'o1' }]);
  });

  it('fetchReadiness stores the assessment', async () => {
    mocked.assessReadiness.mockResolvedValue({ ready: true } as never);
    const store = makeHarvestStore();
    await store.dispatch(fetchReadiness('pl1'));
    expect(mocked.assessReadiness).toHaveBeenCalledWith('pl1');
    expect(store.getState().harvest.readiness).toEqual({ ready: true });
  });
});
