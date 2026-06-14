import { describe, it, expect } from 'vitest';
import reducer, {
  clearCurrent,
  clearError,
  fetchActivities,
  fetchActivity,
} from '@/store/slices/activitiesSlice';

const baseState = { items: [], current: null, loading: false, error: null };

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
    expect(state.error).toBe('Failed to load activities');
  });

  it('fetchActivity.fulfilled stores the selected activity', () => {
    const activity = { key: 'a1' };
    const state = reducer(undefined, { type: fetchActivity.fulfilled.type, payload: activity });
    expect(state.current).toEqual(activity);
  });
});
