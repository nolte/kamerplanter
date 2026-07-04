import { describe, it, expect, vi, beforeEach } from 'vitest';
import { configureStore } from '@reduxjs/toolkit';
import reducer, {
  clearCurrentProfile,
  clearError,
  fetchDashboard,
  fetchProfile,
  confirmCareReminder,
  snoozeCareReminder,
} from '@/store/slices/careRemindersSlice';
import * as careApi from '@/api/endpoints/careReminders';

// Isolated module mock — no real HTTP, no handlers.ts.
vi.mock('@/api/endpoints/careReminders');

const baseState = { dashboard: [], currentProfile: null, loading: false, error: null };

function makeStore() {
  return configureStore({ reducer: { careReminders: reducer } });
}

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
    expect(rejected.error).toBe('errors.loadFailed');
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

describe('careRemindersSlice thunks', () => {
  const mocked = vi.mocked(careApi);

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('fetchDashboard forwards the hemisphere and stores entries', async () => {
    mocked.getDashboard.mockResolvedValue([entryA] as never);
    const store = makeStore();
    await store.dispatch(fetchDashboard('south'));
    expect(mocked.getDashboard).toHaveBeenCalledWith('south');
    expect(store.getState().careReminders.dashboard).toEqual([entryA]);
  });

  it('fetchDashboard surfaces a rejection as the slice error', async () => {
    mocked.getDashboard.mockRejectedValue(new Error('load failed'));
    const store = makeStore();
    await store.dispatch(fetchDashboard());
    expect(store.getState().careReminders.error).toBe('load failed');
  });

  it('fetchProfile forwards its args and stores the profile', async () => {
    mocked.getOrCreateProfile.mockResolvedValue({ key: 'cp1' } as never);
    const store = makeStore();
    await store.dispatch(fetchProfile({ plantKey: 'pl1', speciesName: 'Rosa', botanicalFamily: 'Rosaceae' }));
    expect(mocked.getOrCreateProfile).toHaveBeenCalledWith('pl1', 'Rosa', 'Rosaceae');
    expect(store.getState().careReminders.currentProfile).toEqual({ key: 'cp1' });
  });

  it('confirmCareReminder calls the API and drops the entry', async () => {
    mocked.confirmReminder.mockResolvedValue(entryA as never);
    const store = configureStore({
      reducer: { careReminders: reducer },
      preloadedState: { careReminders: { ...baseState, dashboard: [entryA, entryB] as never } },
    });
    await store.dispatch(confirmCareReminder({ plantKey: 'pl1', reminderType: 'watering' }));
    expect(mocked.confirmReminder).toHaveBeenCalledWith('pl1', 'watering', undefined);
    expect(store.getState().careReminders.dashboard).toEqual([entryB]);
  });

  it('snoozeCareReminder calls the API and drops the entry', async () => {
    mocked.snoozeReminder.mockResolvedValue(entryB as never);
    const store = configureStore({
      reducer: { careReminders: reducer },
      preloadedState: { careReminders: { ...baseState, dashboard: [entryA, entryB] as never } },
    });
    await store.dispatch(snoozeCareReminder({ plantKey: 'pl2', reminderType: 'fertilizing', snoozeDays: 3 }));
    expect(mocked.snoozeReminder).toHaveBeenCalledWith('pl2', 'fertilizing', 3);
    expect(store.getState().careReminders.dashboard).toEqual([entryA]);
  });
});
