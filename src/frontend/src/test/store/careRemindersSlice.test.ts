import { describe, it, expect } from 'vitest';
import reducer, {
  clearCurrentProfile,
  clearError,
  fetchDashboard,
  fetchProfile,
  confirmCareReminder,
  snoozeCareReminder,
} from '@/store/slices/careRemindersSlice';

const baseState = { dashboard: [], currentProfile: null, loading: false, error: null };

const entryA = { plant_key: 'pl1', reminder_type: 'watering' };
const entryB = { plant_key: 'pl2', reminder_type: 'fertilizing' };

describe('careRemindersSlice', () => {
  it('has the empty initial state', () => {
    expect(reducer(undefined, { type: 'unknown' })).toEqual(baseState);
  });

  it('clearCurrentProfile resets the profile', () => {
    const state = reducer({ ...baseState, currentProfile: { key: 'cp1' } as never }, clearCurrentProfile());
    expect(state.currentProfile).toBeNull();
  });

  it('clearError resets the error', () => {
    const state = reducer({ ...baseState, error: 'boom' }, clearError());
    expect(state.error).toBeNull();
  });

  it('fetchDashboard handles pending, fulfilled and rejected', () => {
    expect(reducer(baseState, { type: fetchDashboard.pending.type }).loading).toBe(true);
    const fulfilled = reducer(baseState, { type: fetchDashboard.fulfilled.type, payload: [entryA] });
    expect(fulfilled.dashboard).toEqual([entryA]);
    const rejected = reducer(baseState, { type: fetchDashboard.rejected.type, error: {} });
    expect(rejected.error).toBe('Failed to load care dashboard');
  });

  it('fetchProfile.fulfilled stores the current profile', () => {
    const state = reducer(baseState, { type: fetchProfile.fulfilled.type, payload: { key: 'cp1' } });
    expect(state.currentProfile).toEqual({ key: 'cp1' });
  });

  it('confirmCareReminder.fulfilled removes the matching dashboard entry', () => {
    const start = { ...baseState, dashboard: [entryA, entryB] as never };
    const state = reducer(start, { type: confirmCareReminder.fulfilled.type, payload: entryA });
    expect(state.dashboard).toEqual([entryB]);
  });

  it('snoozeCareReminder.fulfilled removes the matching dashboard entry', () => {
    const start = { ...baseState, dashboard: [entryA, entryB] as never };
    const state = reducer(start, { type: snoozeCareReminder.fulfilled.type, payload: entryB });
    expect(state.dashboard).toEqual([entryA]);
  });
});
