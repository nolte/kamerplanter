import { describe, it, expect, vi, beforeEach } from 'vitest';
import { configureStore } from '@reduxjs/toolkit';
import reducer, {
  clearCurrentPlan,
  clearError,
  fetchSuccessionPlans,
  fetchSuccessionPlan,
} from '@/store/slices/successionPlansSlice';
import * as successionApi from '@/api/endpoints/successionPlans';

// Isolated module mock — no real HTTP, no handlers.ts.
vi.mock('@/api/endpoints/successionPlans');

const baseState = { plans: [], currentPlan: null, loading: false, error: null };

function makeStore() {
  return configureStore({ reducer: { successionPlans: reducer } });
}

describe('successionPlansSlice', () => {
  it('has the empty initial state', () => {
    expect(reducer(undefined, { type: 'unknown' })).toEqual(baseState);
  });

  it('clearCurrentPlan resets the selection', () => {
    const state = reducer(
      { ...baseState, currentPlan: { key: 'sp1' } as never },
      clearCurrentPlan(),
    );
    expect(state.currentPlan).toBeNull();
  });

  it('clearError resets the error', () => {
    const state = reducer({ ...baseState, error: 'boom' }, clearError());
    expect(state.error).toBeNull();
  });

  it('fetchSuccessionPlans.pending sets loading and clears prior error', () => {
    const state = reducer(
      { ...baseState, error: 'old' },
      { type: fetchSuccessionPlans.pending.type },
    );
    expect(state.loading).toBe(true);
    expect(state.error).toBeNull();
  });

  it('fetchSuccessionPlans.fulfilled stores the plans', () => {
    const plans = [{ key: 'sp1' }];
    const state = reducer(undefined, {
      type: fetchSuccessionPlans.fulfilled.type,
      payload: plans,
    });
    expect(state.plans).toEqual(plans);
    expect(state.loading).toBe(false);
  });

  it('fetchSuccessionPlans.rejected stores the error', () => {
    const state = reducer(undefined, {
      type: fetchSuccessionPlans.rejected.type,
      error: { message: 'fail' },
    });
    expect(state.error).toBe('fail');
  });

  it('fetchSuccessionPlans.rejected falls back to a default message', () => {
    const state = reducer(undefined, {
      type: fetchSuccessionPlans.rejected.type,
      error: {},
    });
    expect(state.error).toBe('errors.loadFailed');
  });

  it('fetchSuccessionPlan.fulfilled stores the selected plan', () => {
    const plan = { key: 'sp1' };
    const state = reducer(undefined, {
      type: fetchSuccessionPlan.fulfilled.type,
      payload: plan,
    });
    expect(state.currentPlan).toEqual(plan);
  });
});

describe('successionPlansSlice thunks', () => {
  const mocked = vi.mocked(successionApi);

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('fetchSuccessionPlans forwards paging args and stores the plans', async () => {
    mocked.listSuccessionPlans.mockResolvedValue([{ key: 'sp1' }] as never);
    const store = makeStore();
    await store.dispatch(fetchSuccessionPlans({ offset: 5, limit: 10 }));
    expect(mocked.listSuccessionPlans).toHaveBeenCalledWith(5, 10);
    expect(store.getState().successionPlans.plans).toEqual([{ key: 'sp1' }]);
  });

  it('fetchSuccessionPlans surfaces a rejection as the slice error', async () => {
    mocked.listSuccessionPlans.mockRejectedValue(new Error('load failed'));
    const store = makeStore();
    await store.dispatch(fetchSuccessionPlans({}));
    expect(store.getState().successionPlans.error).toBe('load failed');
  });

  it('fetchSuccessionPlan calls getSuccessionPlan and stores the selection', async () => {
    mocked.getSuccessionPlan.mockResolvedValue({ key: 'sp9' } as never);
    const store = makeStore();
    await store.dispatch(fetchSuccessionPlan('sp9'));
    expect(mocked.getSuccessionPlan).toHaveBeenCalledWith('sp9');
    expect(store.getState().successionPlans.currentPlan).toEqual({ key: 'sp9' });
  });
});
