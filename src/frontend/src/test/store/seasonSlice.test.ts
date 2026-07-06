import { describe, it, expect, vi, beforeEach } from 'vitest';
import { configureStore } from '@reduxjs/toolkit';
import reducer, {
  clearCurrentProfile,
  fetchSeasonOverview,
  fetchOverwintering,
  fetchOverwinteringStatus,
  overrideOverwintering,
  resetOverwintering,
} from '@/store/slices/seasonSlice';
import * as api from '@/api/endpoints/season';
import { ApiError } from '@/api/errors';
import type { OverwinteringProfile, SeasonState } from '@/api/types';

// Isolated module mock — no real HTTP, no handlers.ts.
vi.mock('@/api/endpoints/season');

function makeStore() {
  return configureStore({ reducer: { season: reducer } });
}

const state1: SeasonState = {
  site_key: 'site-1',
  season_state_id: 'ss-1',
  phase: 'pre_winter',
  trigger_tier: 'live',
  trigger_reason_i18n_key: 'pages.season.trigger.frostForecast',
  season_year: 2026,
  entered_phase_at: null,
  last_min_temp_c: 3.2,
  forecast_first_frost_date: '2026-11-10',
  estimated_first_frost_md: null,
  estimated_last_frost_md: null,
  evaluated_at: null,
};

const profile = {
  key: 'ow-1',
  plant_key: 'plant-1',
  hardiness_rating: 'needs_protection',
  winter_action: 'fleece',
  winter_action_month: 10,
  user_overridden: false,
  auto_generated: true,
  derived_path: 'A',
} as unknown as OverwinteringProfile;

describe('seasonSlice reducers', () => {
  it('starts from an empty state', () => {
    const state = reducer(undefined, { type: 'unknown' });
    expect(state.overview).toEqual([]);
    expect(state.overviewLoading).toBe(false);
    expect(state.currentProfile).toBeNull();
    expect(state.requestedPlantKey).toBeNull();
  });

  it('fetchSeasonOverview transitions pending → fulfilled', () => {
    const pending = reducer(undefined, { type: fetchSeasonOverview.pending.type });
    expect(pending.overviewLoading).toBe(true);
    const done = reducer(pending, {
      type: fetchSeasonOverview.fulfilled.type,
      payload: [state1],
    });
    expect(done.overviewLoading).toBe(false);
    expect(done.overview).toEqual([state1]);
  });

  it('fetchSeasonOverview.rejected records a localised error key', () => {
    const state = reducer(undefined, {
      type: fetchSeasonOverview.rejected.type,
      error: { message: 'raw backend nope' },
    });
    expect(state.overviewError).toBe('errors.loadFailed');
  });

  it('fetchOverwintering pending → fulfilled stores the current profile', () => {
    const pending = reducer(undefined, fetchOverwintering.pending('req-1', 'plant-1'));
    expect(pending.profileLoading).toBe(true);
    expect(pending.requestedPlantKey).toBe('plant-1');
    const done = reducer(
      pending,
      fetchOverwintering.fulfilled(profile, 'req-1', 'plant-1'),
    );
    expect(done.currentProfile).toEqual(profile);
    expect(done.profileLoading).toBe(false);
  });

  it('pending clears the previous plant profile so the loader guard wins (F1)', () => {
    let state = reducer(undefined, fetchOverwintering.pending('reqA', 'plant-A'));
    state = reducer(state, fetchOverwintering.fulfilled(profile, 'reqA', 'plant-A'));
    expect(state.currentProfile).not.toBeNull();
    // Navigating to another plant must immediately drop A's profile — otherwise
    // the `!currentProfile` skeleton guard never fires and A stays on screen.
    state = reducer(state, fetchOverwintering.pending('reqB', 'plant-B'));
    expect(state.currentProfile).toBeNull();
    expect(state.profileLoading).toBe(true);
    expect(state.requestedPlantKey).toBe('plant-B');
  });

  it('discards a stale profile response after navigating to another plant (F1)', () => {
    // Request for plant A starts, then the user navigates to plant B: A's
    // section unmounts (clearCurrentProfile) and B's mounts and requests.
    let state = reducer(undefined, fetchOverwintering.pending('reqA', 'plant-A'));
    state = reducer(state, clearCurrentProfile());
    state = reducer(state, fetchOverwintering.pending('reqB', 'plant-B'));

    // A's slow response finally arrives — it must NOT leak onto B's page.
    const profileA = { ...profile, key: 'ow-A', plant_key: 'plant-A' };
    state = reducer(
      state,
      fetchOverwintering.fulfilled(profileA, 'reqA', 'plant-A'),
    );
    expect(state.currentProfile).toBeNull();
    expect(state.requestedPlantKey).toBe('plant-B');

    // B's own response applies normally.
    const profileB = { ...profile, key: 'ow-B', plant_key: 'plant-B' };
    state = reducer(
      state,
      fetchOverwintering.fulfilled(profileB, 'reqB', 'plant-B'),
    );
    expect(state.currentProfile).toEqual(profileB);
  });

  it('fetchOverwintering.rejected stores a localised key, not the raw message', () => {
    let state = reducer(undefined, fetchOverwintering.pending('req-1', 'plant-1'));
    state = reducer(
      state,
      fetchOverwintering.rejected(new Error('raw backend boom'), 'req-1', 'plant-1'),
    );
    expect(state.profileError).toBe('errors.loadFailed');
  });

  it('discards a stale rejection after navigating away (F1)', () => {
    let state = reducer(undefined, fetchOverwintering.pending('reqA', 'plant-A'));
    state = reducer(state, fetchOverwintering.pending('reqB', 'plant-B'));
    // A's late failure must not raise an error banner on B's page.
    state = reducer(
      state,
      fetchOverwintering.rejected(new Error('boom'), 'reqA', 'plant-A'),
    );
    expect(state.profileError).toBeNull();
    expect(state.profileLoading).toBe(true);
  });

  it('override and reset replace the current profile', () => {
    let state = reducer(undefined, fetchOverwintering.pending('req-1', 'plant-1'));
    state = reducer(state, fetchOverwintering.fulfilled(profile, 'req-1', 'plant-1'));

    const overridden = { ...profile, user_overridden: true };
    const afterOverride = reducer(
      state,
      overrideOverwintering.fulfilled(overridden, 'req-2', {
        plantKey: 'plant-1',
        patch: { winter_watering: 'minimal' },
      }),
    );
    expect(afterOverride.currentProfile?.user_overridden).toBe(true);

    const afterReset = reducer(
      afterOverride,
      resetOverwintering.fulfilled(profile, 'req-3', 'plant-1'),
    );
    expect(afterReset.currentProfile?.user_overridden).toBe(false);
  });

  it('ignores an override that resolves after navigating to another plant (F1)', () => {
    let state = reducer(undefined, fetchOverwintering.pending('reqA', 'plant-A'));
    state = reducer(state, fetchOverwintering.fulfilled(profile, 'reqA', 'plant-A'));
    state = reducer(state, fetchOverwintering.pending('reqB', 'plant-B'));

    const overridden = { ...profile, key: 'ow-A', user_overridden: true };
    state = reducer(
      state,
      overrideOverwintering.fulfilled(overridden, 'reqX', {
        plantKey: 'plant-A',
        patch: { winter_watering: 'minimal' },
      }),
    );
    // B is the active plant now — A's mutation must not overwrite the slice.
    expect(state.currentProfile).toBeNull();
    expect(state.requestedPlantKey).toBe('plant-B');
  });

  it('clearCurrentProfile empties the profile and the request marker', () => {
    let state = reducer(undefined, fetchOverwintering.pending('req-1', 'plant-1'));
    state = reducer(state, fetchOverwintering.fulfilled(profile, 'req-1', 'plant-1'));
    const cleared = reducer(state, clearCurrentProfile());
    expect(cleared.currentProfile).toBeNull();
    expect(cleared.requestedPlantKey).toBeNull();
    expect(cleared.currentStatus).toBeNull();
  });

  it('starts with no hardiness status', () => {
    const state = reducer(undefined, { type: 'unknown' });
    expect(state.currentStatus).toBeNull();
    expect(state.statusLoading).toBe(false);
  });

  it('fetchOverwinteringStatus pending → fulfilled stores the status', () => {
    let state = reducer(undefined, fetchOverwintering.pending('req-1', 'plant-1'));
    state = reducer(state, fetchOverwinteringStatus.pending('req-2', 'plant-1'));
    expect(state.statusLoading).toBe(true);
    const status = {
      has_profile: false,
      hardiness_light: 'yellow',
      will_materialize: true,
      site_overwinterable: true,
    } as const;
    state = reducer(state, fetchOverwinteringStatus.fulfilled(status, 'req-2', 'plant-1'));
    expect(state.statusLoading).toBe(false);
    expect(state.currentStatus).toEqual(status);
  });

  it('discards a stale status response after navigating to another plant', () => {
    let state = reducer(undefined, fetchOverwintering.pending('reqA', 'plant-A'));
    state = reducer(state, fetchOverwinteringStatus.pending('reqA2', 'plant-A'));
    // User navigates to B before A's status resolves.
    state = reducer(state, fetchOverwintering.pending('reqB', 'plant-B'));
    const staleStatus = {
      has_profile: false,
      hardiness_light: 'green',
      will_materialize: false,
      site_overwinterable: true,
    } as const;
    state = reducer(state, fetchOverwinteringStatus.fulfilled(staleStatus, 'reqA2', 'plant-A'));
    expect(state.currentStatus).toBeNull();
  });

  it('a new profile fetch resets a previous plant\'s status', () => {
    let state = reducer(undefined, fetchOverwintering.pending('reqA', 'plant-A'));
    const status = {
      has_profile: false,
      hardiness_light: 'green',
      will_materialize: false,
      site_overwinterable: true,
    } as const;
    state = reducer(state, fetchOverwinteringStatus.fulfilled(status, 'reqA2', 'plant-A'));
    expect(state.currentStatus).toEqual(status);
    state = reducer(state, fetchOverwintering.pending('reqB', 'plant-B'));
    expect(state.currentStatus).toBeNull();
  });
});

describe('seasonSlice thunks', () => {
  const mocked = vi.mocked(api);

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('fetchSeasonOverview unwraps the states array', async () => {
    mocked.getSeasonOverview.mockResolvedValue({ states: [state1] } as never);
    const store = makeStore();
    await store.dispatch(fetchSeasonOverview());
    expect(mocked.getSeasonOverview).toHaveBeenCalledTimes(1);
    expect(store.getState().season.overview).toEqual([state1]);
  });

  it('overrideOverwintering forwards the patch and stores the result', async () => {
    const overridden = { ...profile, user_overridden: true };
    mocked.getPlantOverwintering.mockResolvedValue(profile as never);
    mocked.overridePlantOverwintering.mockResolvedValue(overridden as never);
    const store = makeStore();
    // The section always reads the profile first — that read sets the "current
    // plant" the override guard checks against.
    await store.dispatch(fetchOverwintering('plant-1'));
    await store.dispatch(
      overrideOverwintering({ plantKey: 'plant-1', patch: { winter_watering: 'minimal' } }),
    );
    expect(mocked.overridePlantOverwintering).toHaveBeenCalledWith('plant-1', {
      winter_watering: 'minimal',
    });
    expect(store.getState().season.currentProfile?.user_overridden).toBe(true);
  });

  it('resetOverwintering calls the reset endpoint', async () => {
    mocked.getPlantOverwintering.mockResolvedValue(profile as never);
    mocked.resetPlantOverwintering.mockResolvedValue(profile as never);
    const store = makeStore();
    await store.dispatch(fetchOverwintering('plant-1'));
    await store.dispatch(resetOverwintering('plant-1'));
    expect(mocked.resetPlantOverwintering).toHaveBeenCalledWith('plant-1');
    expect(store.getState().season.currentProfile).toEqual(profile);
  });

  it('fetchOverwintering treats a 404 as "no profile" (winter-hardy plant), not an error', async () => {
    mocked.getPlantOverwintering.mockRejectedValue(
      new ApiError(
        {
          error_id: 'err-1',
          error_code: 'ENTITY_NOT_FOUND',
          message: 'not found',
          details: [],
          timestamp: new Date().toISOString(),
          path: '/plants/plant-1/overwintering',
          method: 'GET',
        },
        404,
      ),
    );
    const store = makeStore();
    await store.dispatch(fetchOverwintering('plant-1'));
    expect(store.getState().season.currentProfile).toBeNull();
    expect(store.getState().season.profileError).toBeNull();
  });

  it('fetchOverwintering surfaces a real server error instead of masquerading as "no profile"', async () => {
    mocked.getPlantOverwintering.mockRejectedValue(
      new ApiError(
        {
          error_id: 'err-2',
          error_code: 'INTERNAL_ERROR',
          message: 'boom',
          details: [],
          timestamp: new Date().toISOString(),
          path: '/plants/plant-1/overwintering',
          method: 'GET',
        },
        500,
      ),
    );
    const store = makeStore();
    await store.dispatch(fetchOverwintering('plant-1'));
    expect(store.getState().season.currentProfile).toBeNull();
    expect(store.getState().season.profileError).toBeTruthy();
  });
});
