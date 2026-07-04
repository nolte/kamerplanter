import { describe, it, expect, vi, beforeEach } from 'vitest';
import { configureStore } from '@reduxjs/toolkit';
import reducer, {
  clearCurrentPest,
  clearCurrentDisease,
  clearCurrentTreatment,
  clearError,
  fetchPests,
  fetchPest,
  fetchDiseases,
  fetchDisease,
  fetchTreatments,
  fetchTreatment,
  fetchInspections,
  fetchApplications,
  fetchKarenzPeriods,
} from '@/store/slices/ipmSlice';
import * as ipmApi from '@/api/endpoints/ipm';

// Isolated module mock — no real HTTP, no handlers.ts.
vi.mock('@/api/endpoints/ipm');

function makeIpmStore() {
  return configureStore({ reducer: { ipm: reducer } });
}

const baseState = {
  pests: [],
  diseases: [],
  treatments: [],
  inspections: [],
  applications: [],
  karenzPeriods: [],
  currentPest: null,
  currentDisease: null,
  currentTreatment: null,
  loading: false,
  error: null,
};

describe('ipmSlice', () => {
  it('has the empty initial state', () => {
    expect(reducer(undefined, { type: 'unknown' })).toEqual(baseState);
  });

  it('clearCurrentPest, clearCurrentDisease and clearCurrentTreatment reset their selections', () => {
    const populated = {
      ...baseState,
      currentPest: { key: 'p' } as never,
      currentDisease: { key: 'd' } as never,
      currentTreatment: { key: 't' } as never,
    };
    expect(reducer(populated, clearCurrentPest()).currentPest).toBeNull();
    expect(reducer(populated, clearCurrentDisease()).currentDisease).toBeNull();
    expect(reducer(populated, clearCurrentTreatment()).currentTreatment).toBeNull();
  });

  it('clearError resets the error', () => {
    const state = reducer({ ...baseState, error: 'boom' }, clearError());
    expect(state.error).toBeNull();
  });

  it('fetchPests handles pending, fulfilled and rejected', () => {
    expect(reducer(baseState, { type: fetchPests.pending.type }).loading).toBe(true);
    const fulfilled = reducer(baseState, { type: fetchPests.fulfilled.type, payload: [{ key: 'p1' }] });
    expect(fulfilled.pests).toEqual([{ key: 'p1' }]);
    const rejected = reducer(baseState, { type: fetchPests.rejected.type, error: {} });
    expect(rejected.error).toBe('errors.loadFailed');
  });

  it('fetchPest.fulfilled stores the current pest', () => {
    const state = reducer(baseState, { type: fetchPest.fulfilled.type, payload: { key: 'p1' } });
    expect(state.currentPest).toEqual({ key: 'p1' });
  });

  it('fetchDiseases handles fulfilled and rejected fallback', () => {
    const fulfilled = reducer(baseState, { type: fetchDiseases.fulfilled.type, payload: [{ key: 'd1' }] });
    expect(fulfilled.diseases).toEqual([{ key: 'd1' }]);
    const rejected = reducer(baseState, { type: fetchDiseases.rejected.type, error: {} });
    expect(rejected.error).toBe('errors.loadFailed');
  });

  it('fetchDisease.fulfilled stores the current disease', () => {
    const state = reducer(baseState, { type: fetchDisease.fulfilled.type, payload: { key: 'd1' } });
    expect(state.currentDisease).toEqual({ key: 'd1' });
  });

  it('fetchTreatments handles fulfilled and rejected fallback', () => {
    const fulfilled = reducer(baseState, { type: fetchTreatments.fulfilled.type, payload: [{ key: 't1' }] });
    expect(fulfilled.treatments).toEqual([{ key: 't1' }]);
    const rejected = reducer(baseState, { type: fetchTreatments.rejected.type, error: {} });
    expect(rejected.error).toBe('errors.loadFailed');
  });

  it('fetchTreatment.fulfilled stores the current treatment', () => {
    const state = reducer(baseState, { type: fetchTreatment.fulfilled.type, payload: { key: 't1' } });
    expect(state.currentTreatment).toEqual({ key: 't1' });
  });

  it('fetchInspections.fulfilled stores inspections', () => {
    const state = reducer(baseState, { type: fetchInspections.fulfilled.type, payload: [{ key: 'i1' }] });
    expect(state.inspections).toEqual([{ key: 'i1' }]);
  });

  it('fetchApplications.fulfilled stores applications', () => {
    const state = reducer(baseState, { type: fetchApplications.fulfilled.type, payload: [{ key: 'a1' }] });
    expect(state.applications).toEqual([{ key: 'a1' }]);
  });

  it('fetchKarenzPeriods.fulfilled stores karenz periods', () => {
    const state = reducer(baseState, { type: fetchKarenzPeriods.fulfilled.type, payload: [{ key: 'k1' }] });
    expect(state.karenzPeriods).toEqual([{ key: 'k1' }]);
  });
});

describe('ipmSlice thunks', () => {
  const mocked = vi.mocked(ipmApi);

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('fetchPests forwards paging and stores pests', async () => {
    mocked.listPests.mockResolvedValue([{ key: 'p1' }] as never);
    const store = makeIpmStore();
    await store.dispatch(fetchPests({ offset: 0, limit: 10 }));
    expect(mocked.listPests).toHaveBeenCalledWith(0, 10);
    expect(store.getState().ipm.pests).toEqual([{ key: 'p1' }]);
  });

  it('fetchPests surfaces a rejection as the slice error', async () => {
    mocked.listPests.mockRejectedValue(new Error('load failed'));
    const store = makeIpmStore();
    await store.dispatch(fetchPests({}));
    expect(store.getState().ipm.error).toBe('load failed');
  });

  it('fetchPest stores the current pest', async () => {
    mocked.getPest.mockResolvedValue({ key: 'p9' } as never);
    const store = makeIpmStore();
    await store.dispatch(fetchPest('p9'));
    expect(mocked.getPest).toHaveBeenCalledWith('p9');
    expect(store.getState().ipm.currentPest).toEqual({ key: 'p9' });
  });

  it('fetchDiseases stores diseases', async () => {
    mocked.listDiseases.mockResolvedValue([{ key: 'd1' }] as never);
    const store = makeIpmStore();
    await store.dispatch(fetchDiseases({}));
    expect(store.getState().ipm.diseases).toEqual([{ key: 'd1' }]);
  });

  it('fetchDisease stores the current disease', async () => {
    mocked.getDisease.mockResolvedValue({ key: 'd9' } as never);
    const store = makeIpmStore();
    await store.dispatch(fetchDisease('d9'));
    expect(mocked.getDisease).toHaveBeenCalledWith('d9');
    expect(store.getState().ipm.currentDisease).toEqual({ key: 'd9' });
  });

  it('fetchTreatments stores treatments', async () => {
    mocked.listTreatments.mockResolvedValue([{ key: 't1' }] as never);
    const store = makeIpmStore();
    await store.dispatch(fetchTreatments({}));
    expect(store.getState().ipm.treatments).toEqual([{ key: 't1' }]);
  });

  it('fetchTreatment stores the current treatment', async () => {
    mocked.getTreatment.mockResolvedValue({ key: 't9' } as never);
    const store = makeIpmStore();
    await store.dispatch(fetchTreatment('t9'));
    expect(mocked.getTreatment).toHaveBeenCalledWith('t9');
    expect(store.getState().ipm.currentTreatment).toEqual({ key: 't9' });
  });

  it('fetchInspections forwards its args and stores inspections', async () => {
    mocked.getInspections.mockResolvedValue([{ key: 'in1' }] as never);
    const store = makeIpmStore();
    await store.dispatch(fetchInspections({ plantKey: 'pl1', offset: 0, limit: 5 }));
    expect(mocked.getInspections).toHaveBeenCalledWith('pl1', 0, 5);
    expect(store.getState().ipm.inspections).toEqual([{ key: 'in1' }]);
  });

  it('fetchApplications forwards its args and stores applications', async () => {
    mocked.getTreatmentApplications.mockResolvedValue([{ key: 'ta1' }] as never);
    const store = makeIpmStore();
    await store.dispatch(fetchApplications({ plantKey: 'pl1', offset: 0, limit: 5 }));
    expect(mocked.getTreatmentApplications).toHaveBeenCalledWith('pl1', 0, 5);
    expect(store.getState().ipm.applications).toEqual([{ key: 'ta1' }]);
  });

  it('fetchKarenzPeriods stores karenz periods', async () => {
    mocked.getKarenzPeriods.mockResolvedValue([{ key: 'k1' }] as never);
    const store = makeIpmStore();
    await store.dispatch(fetchKarenzPeriods('pl1'));
    expect(mocked.getKarenzPeriods).toHaveBeenCalledWith('pl1');
    expect(store.getState().ipm.karenzPeriods).toEqual([{ key: 'k1' }]);
  });
});
