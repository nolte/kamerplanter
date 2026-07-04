import { describe, it, expect, vi, beforeEach } from 'vitest';
import { configureStore } from '@reduxjs/toolkit';
import reducer, {
  clearCurrent,
  clearError,
  fetchActivities,
  fetchActivity,
} from '@/store/slices/activitiesSlice';
import * as activitiesApi from '@/api/endpoints/activities';

// Isolated module mock — no real HTTP, no handlers.ts.
vi.mock('@/api/endpoints/activities');

const baseState = { items: [], current: null, loading: false, error: null };

function makeStore() {
  return configureStore({ reducer: { activities: reducer } });
}

describe('activitiesSlice', () => {
  it('has the empty initial state', () => {
    expect(reducer(undefined, { type: 'unknown' })).toEqual(baseState);
  });

  it('clearCurrent resets the selection', () => {
    const state = reducer({ ...baseState, current: { key: 'a1' } as never }, clearCurrent());
    expect(state.current).toBeNull();
  });

  it('clearError resets the error', () => {
    const state = reducer({ ...baseState, error: 'boom' }, clearError());
    expect(state.error).toBeNull();
  });

  it('fetchActivities.pending sets loading and clears prior error', () => {
    const state = reducer({ ...baseState, error: 'old' }, { type: fetchActivities.pending.type });
    expect(state.loading).toBe(true);
    expect(state.error).toBeNull();
  });

  it('fetchActivities.fulfilled stores the items', () => {
    const items = [{ key: 'a1' }];
    const state = reducer(undefined, { type: fetchActivities.fulfilled.type, payload: items });
    expect(state.items).toEqual(items);
    expect(state.loading).toBe(false);
  });

  it('fetchActivities.rejected stores the error', () => {
    const state = reducer(undefined, { type: fetchActivities.rejected.type, error: { message: 'fail' } });
    expect(state.error).toBe('fail');
  });

  it('fetchActivities.rejected falls back to a default message', () => {
    const state = reducer(undefined, { type: fetchActivities.rejected.type, error: {} });
    expect(state.error).toBe('errors.loadFailed');
  });

  it('fetchActivity.fulfilled stores the selected activity', () => {
    const activity = { key: 'a1' };
    const state = reducer(undefined, { type: fetchActivity.fulfilled.type, payload: activity });
    expect(state.current).toEqual(activity);
  });
});

describe('activitiesSlice thunks', () => {
  const mocked = vi.mocked(activitiesApi);

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('fetchActivities calls listActivities and stores the items', async () => {
    mocked.listActivities.mockResolvedValue([{ key: 'a1' }] as never);
    const store = makeStore();
    const params = { category: 'watering' };
    await store.dispatch(fetchActivities(params));
    expect(mocked.listActivities).toHaveBeenCalledWith(params);
    expect(store.getState().activities.items).toEqual([{ key: 'a1' }]);
  });

  it('fetchActivities surfaces a rejection as the slice error', async () => {
    mocked.listActivities.mockRejectedValue(new Error('load failed'));
    const store = makeStore();
    await store.dispatch(fetchActivities());
    expect(store.getState().activities.error).toBe('load failed');
  });

  it('fetchActivity calls getActivity and stores the selection', async () => {
    mocked.getActivity.mockResolvedValue({ key: 'a9' } as never);
    const store = makeStore();
    await store.dispatch(fetchActivity('a9'));
    expect(mocked.getActivity).toHaveBeenCalledWith('a9');
    expect(store.getState().activities.current).toEqual({ key: 'a9' });
  });
});
