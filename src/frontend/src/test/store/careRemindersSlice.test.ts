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

const baseState = {
  dashboard: [],
  currentProfile: null,
  loading: false,
  dashboardLoaded: false,
  error: null,
  profileRequestId: null,
  profileError: null,
};

function makeStore() {
  return configureStore({ reducer: { careReminders: reducer } });
}

const entryA = { plant_key: 'pl1', reminder_type: 'watering' };
const entryB = { plant_key: 'pl2', reminder_type: 'fertilizing' };

describe('careRemindersSlice', () => {
  it('has the empty initial state', () => {
    expect(reducer(undefined, { type: 'unknown' })).toEqual(baseState);
  });

  it('fetchDashboard latches dashboardLoaded on either outcome', () => {
    // A host gating its first paint on "everything has answered" cannot read
    // that off `loading`: false is also the state before anything was asked.
    const settled = reducer(undefined, { type: fetchDashboard.fulfilled.type, payload: [] });
    expect(settled.dashboardLoaded).toBe(true);
    const failed = reducer(undefined, { type: fetchDashboard.rejected.type, error: {} });
    expect(failed.dashboardLoaded).toBe(true);
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

  /** A `fetchProfile` lifecycle action as RTK dispatches it: the arg and the request it belongs to. */
  function profileAction(phase: 'pending' | 'fulfilled' | 'rejected', plantKey: string, requestId: string, payload?: unknown) {
    return {
      type: fetchProfile[phase].type,
      payload,
      error: phase === 'rejected' ? {} : undefined,
      meta: { arg: { plantKey }, requestId },
    };
  }

  it('fetchProfile.fulfilled stores the current profile', () => {
    const asked = reducer(baseState, profileAction('pending', 'pl1', 'r1'));
    const state = reducer(asked, profileAction('fulfilled', 'pl1', 'r1', { key: 'cp1' }));
    expect(state.currentProfile).toEqual({ key: 'cp1' });
  });

  // #3065: the slice is shared by every profile editor. Asking for plant B must
  // drop plant A's profile at once, and A's late answer must not replace B's.
  it('fetchProfile.pending drops the previous profile and a late answer of an earlier request is discarded', () => {
    const loadedA = { ...baseState, currentProfile: { key: 'cpA', plant_key: 'plA' } as never, profileRequestId: 'rA' };
    const askedB = reducer(loadedA, profileAction('pending', 'plB', 'rB'));
    expect(askedB.currentProfile).toBeNull();
    expect(askedB.profileRequestId).toBe('rB');

    expect(reducer(askedB, profileAction('fulfilled', 'plA', 'rA', { key: 'cpA' })).currentProfile).toBeNull();
    expect(reducer(askedB, profileAction('rejected', 'plA', 'rA')).profileError).toBeNull();
  });

  // Same plant, two reads: close and reopen the editor for A while the first
  // read is still in flight. A plant-key guard lets the first answer through.
  it('drops the late answer of an earlier request for the same plant after a clear', () => {
    let state = reducer(baseState, profileAction('pending', 'plA', 'r1'));
    state = reducer(state, clearCurrentProfile());
    state = reducer(state, profileAction('pending', 'plA', 'r2'));
    state = reducer(state, profileAction('fulfilled', 'plA', 'r2', { key: 'cpA-2' }));
    state = reducer(state, profileAction('fulfilled', 'plA', 'r1', { key: 'cpA-1' }));
    expect(state.currentProfile).toEqual({ key: 'cpA-2' });
  });

  it('fetchProfile.rejected for the current request sets the profile error', () => {
    const asked = reducer(baseState, profileAction('pending', 'pl1', 'r1'));
    const state = reducer(asked, profileAction('rejected', 'pl1', 'r1'));
    expect(state.profileError).toBe('errors.loadFailed');
    expect(state.currentProfile).toBeNull();
  });

  it('clearCurrentProfile drops the request marker so a late answer cannot land', () => {
    const asked = reducer(baseState, profileAction('pending', 'pl1', 'r1'));
    const cleared = reducer(asked, clearCurrentProfile());
    expect(cleared.profileRequestId).toBeNull();
    expect(reducer(cleared, profileAction('fulfilled', 'pl1', 'r1', { key: 'cp1' })).currentProfile).toBeNull();
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
    expect(store.getState().careReminders.error).toBe('errors.loadFailed');
  });

  it('fetchProfile forwards its args and stores the profile', async () => {
    mocked.getOrCreateProfile.mockResolvedValue({ key: 'cp1' } as never);
    const store = makeStore();
    await store.dispatch(fetchProfile({ plantKey: 'pl1' }));
    expect(mocked.getOrCreateProfile).toHaveBeenCalledWith('pl1');
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
