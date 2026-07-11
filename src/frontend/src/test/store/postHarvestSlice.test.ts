import { describe, it, expect, vi, beforeEach } from 'vitest';
import { configureStore } from '@reduxjs/toolkit';
import reducer, {
  clearCurrentDetail,
  clearError,
  fetchPostHarvestBatches,
  fetchPostHarvestBatch,
  advancePostHarvestStage,
  recordDryingProgress,
  recordObservation,
  fetchDryingProgress,
  fetchObservations,
  fetchMoldAlerts,
  startDrying,
} from '@/store/slices/postHarvestSlice';
import * as api from '@/api/endpoints/postHarvest';

vi.mock('@/api/endpoints/postHarvest');

function makeStore() {
  return configureStore({ reducer: { postHarvest: reducer } });
}

const baseState = {
  batches: [],
  currentDetail: null,
  dryingProgress: [],
  observations: [],
  moldAlerts: [],
  loading: false,
  error: null,
};

describe('postHarvestSlice', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('has the empty initial state', () => {
    expect(reducer(undefined, { type: 'unknown' })).toEqual(baseState);
  });

  it('clearCurrentDetail resets detail and child collections', () => {
    const state = reducer(
      {
        ...baseState,
        currentDetail: { batch: { key: 'ph1' } } as never,
        dryingProgress: [{ key: 'dp1' }] as never,
        moldAlerts: [{ key: 'a1' }] as never,
      },
      clearCurrentDetail(),
    );
    expect(state.currentDetail).toBeNull();
    expect(state.dryingProgress).toEqual([]);
    expect(state.moldAlerts).toEqual([]);
  });

  it('clearError resets error', () => {
    const state = reducer({ ...baseState, error: 'boom' }, clearError());
    expect(state.error).toBeNull();
  });

  it('fetchPostHarvestBatches.pending sets loading', () => {
    const state = reducer(baseState, { type: fetchPostHarvestBatches.pending.type });
    expect(state.loading).toBe(true);
  });

  it('fetchPostHarvestBatches.fulfilled stores batches', () => {
    const batches = [{ key: 'ph1' }];
    const state = reducer(baseState, {
      type: fetchPostHarvestBatches.fulfilled.type,
      payload: batches,
    });
    expect(state.batches).toEqual(batches);
    expect(state.loading).toBe(false);
  });

  it('fetchPostHarvestBatches.rejected sets error', () => {
    const state = reducer(baseState, {
      type: fetchPostHarvestBatches.rejected.type,
      error: { message: 'nope' },
    });
    expect(state.error).toBe('nope');
  });

  it('fetchPostHarvestBatch.fulfilled stores detail', () => {
    const detail = { batch: { key: 'ph1' }, latest_drying_progress: null, open_mold_alerts: 0 };
    const state = reducer(baseState, {
      type: fetchPostHarvestBatch.fulfilled.type,
      payload: detail,
    });
    expect(state.currentDetail).toEqual(detail);
  });

  it('advancePostHarvestStage.fulfilled updates the detail batch', () => {
    const start = {
      ...baseState,
      currentDetail: {
        batch: { key: 'ph1', stage: 'drying' },
        latest_drying_progress: null,
        open_mold_alerts: 0,
      },
    } as never;
    const state = reducer(start, {
      type: advancePostHarvestStage.fulfilled.type,
      payload: { key: 'ph1', stage: 'curing' },
    });
    expect(state.currentDetail?.batch.stage).toBe('curing');
  });

  it('recordDryingProgress.fulfilled replaces detail', () => {
    const detail = { batch: { key: 'ph1' }, latest_drying_progress: { key: 'dp1' }, open_mold_alerts: 0 };
    const state = reducer(baseState, {
      type: recordDryingProgress.fulfilled.type,
      payload: detail,
    });
    expect(state.currentDetail).toEqual(detail);
  });

  it('fetchMoldAlerts.fulfilled stores alerts', () => {
    const alerts = [{ key: 'a1', severity: 'critical' }];
    const state = reducer(baseState, {
      type: fetchMoldAlerts.fulfilled.type,
      payload: alerts,
    });
    expect(state.moldAlerts).toEqual(alerts);
  });

  it('recordObservation.fulfilled replaces detail', () => {
    const detail = { batch: { key: 'ph1' }, latest_drying_progress: null, open_mold_alerts: 1 };
    const state = reducer(baseState, {
      type: recordObservation.fulfilled.type,
      payload: detail,
    });
    expect(state.currentDetail).toEqual(detail);
  });

  it('fetchDryingProgress.fulfilled stores progress list', () => {
    const list = [{ key: 'dp1' }];
    const state = reducer(baseState, {
      type: fetchDryingProgress.fulfilled.type,
      payload: list,
    });
    expect(state.dryingProgress).toEqual(list);
  });

  it('fetchObservations.fulfilled stores observation list', () => {
    const list = [{ key: 'obs1' }];
    const state = reducer(baseState, {
      type: fetchObservations.fulfilled.type,
      payload: list,
    });
    expect(state.observations).toEqual(list);
  });

  it('startDrying thunk calls the api', async () => {
    vi.mocked(api.startDrying).mockResolvedValue({ key: 'ph1' } as never);
    const store = makeStore();
    await store.dispatch(startDrying({ harvest_batch_key: 'hb1' }));
    expect(api.startDrying).toHaveBeenCalledWith({ harvest_batch_key: 'hb1' });
  });

  it('recordDryingProgress thunk records then refetches detail', async () => {
    vi.mocked(api.recordDryingProgress).mockResolvedValue({ key: 'dp1' } as never);
    vi.mocked(api.getBatch).mockResolvedValue({
      batch: { key: 'ph1' },
      latest_drying_progress: { key: 'dp1' },
      open_mold_alerts: 0,
    } as never);
    const store = makeStore();
    await store.dispatch(
      recordDryingProgress({ key: 'ph1', payload: { current_weight_g: 180 } }),
    );
    expect(api.recordDryingProgress).toHaveBeenCalledWith('ph1', { current_weight_g: 180 });
    expect(api.getBatch).toHaveBeenCalledWith('ph1');
  });

  it('recordObservation thunk records then refetches detail', async () => {
    vi.mocked(api.recordObservation).mockResolvedValue({ key: 'obs1' } as never);
    vi.mocked(api.getBatch).mockResolvedValue({
      batch: { key: 'ph1' },
      latest_drying_progress: null,
      open_mold_alerts: 1,
    } as never);
    const store = makeStore();
    await store.dispatch(
      recordObservation({ key: 'ph1', payload: { rh_percent: 68 } }),
    );
    expect(api.recordObservation).toHaveBeenCalledWith('ph1', { rh_percent: 68 });
    expect(api.getBatch).toHaveBeenCalledWith('ph1');
  });

  it('fetchMoldAlerts thunk calls the api', async () => {
    vi.mocked(api.getMoldAlerts).mockResolvedValue([]);
    const store = makeStore();
    await store.dispatch(fetchMoldAlerts('ph1'));
    expect(api.getMoldAlerts).toHaveBeenCalledWith('ph1');
  });

  it('fetchPostHarvestBatch thunk calls the api', async () => {
    vi.mocked(api.getBatch).mockResolvedValue({
      batch: { key: 'ph1' },
      latest_drying_progress: null,
      open_mold_alerts: 0,
    } as never);
    const store = makeStore();
    await store.dispatch(fetchPostHarvestBatch('ph1'));
    expect(api.getBatch).toHaveBeenCalledWith('ph1');
  });

  it('fetchPostHarvestBatches thunk calls the api', async () => {
    vi.mocked(api.getBatches).mockResolvedValue([]);
    const store = makeStore();
    await store.dispatch(fetchPostHarvestBatches({}));
    expect(api.getBatches).toHaveBeenCalled();
  });

  it('advancePostHarvestStage thunk calls the api', async () => {
    vi.mocked(api.advanceStage).mockResolvedValue({ key: 'ph1' } as never);
    const store = makeStore();
    await store.dispatch(advancePostHarvestStage({ key: 'ph1', targetStage: 'curing' }));
    expect(api.advanceStage).toHaveBeenCalledWith('ph1', 'curing');
  });
});
