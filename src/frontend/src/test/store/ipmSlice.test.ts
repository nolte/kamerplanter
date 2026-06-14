import { describe, it, expect } from 'vitest';
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
    expect(rejected.error).toBe('Failed to load pests');
  });

  it('fetchPest.fulfilled stores the current pest', () => {
    const state = reducer(baseState, { type: fetchPest.fulfilled.type, payload: { key: 'p1' } });
    expect(state.currentPest).toEqual({ key: 'p1' });
  });

  it('fetchDiseases handles fulfilled and rejected fallback', () => {
    const fulfilled = reducer(baseState, { type: fetchDiseases.fulfilled.type, payload: [{ key: 'd1' }] });
    expect(fulfilled.diseases).toEqual([{ key: 'd1' }]);
    const rejected = reducer(baseState, { type: fetchDiseases.rejected.type, error: {} });
    expect(rejected.error).toBe('Failed to load diseases');
  });

  it('fetchDisease.fulfilled stores the current disease', () => {
    const state = reducer(baseState, { type: fetchDisease.fulfilled.type, payload: { key: 'd1' } });
    expect(state.currentDisease).toEqual({ key: 'd1' });
  });

  it('fetchTreatments handles fulfilled and rejected fallback', () => {
    const fulfilled = reducer(baseState, { type: fetchTreatments.fulfilled.type, payload: [{ key: 't1' }] });
    expect(fulfilled.treatments).toEqual([{ key: 't1' }]);
    const rejected = reducer(baseState, { type: fetchTreatments.rejected.type, error: {} });
    expect(rejected.error).toBe('Failed to load treatments');
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
