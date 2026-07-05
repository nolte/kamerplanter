import { describe, it, expect, vi, beforeEach } from 'vitest';
import { configureStore } from '@reduxjs/toolkit';
import reducer, {
  clearCurrentProfile,
  fetchSeasonOverview,
  fetchSeasonState,
  fetchOverwintering,
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
    expect(state.siteStates).toEqual({});
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

  it('fetchSeasonOverview.rejected records the error', () => {
    const state = reducer(undefined, {
      type: fetchSeasonOverview.rejected.type,
      error: { message: 'nope' },
    });
    expect(state.overviewError).toBe('nope');
  });

  it('fetchSeasonState.fulfilled keys the state by site_key', () => {
    const state = reducer(undefined, {
      type: fetchSeasonState.fulfilled.type,
      payload: state1,
    });
    expect(state.siteStates['site-1']).toEqual(state1);
  });

  it('fetchOverwintering.fulfilled stores the current profile', () => {
    const state = reducer(undefined, {
      type: fetchOverwintering.fulfilled.type,
      payload: profile,
    });
    expect(state.currentProfile).toEqual(profile);
    expect(state.profileLoading).toBe(false);
  });

  it('override and reset replace the current profile', () => {
    const overridden = { ...profile, user_overridden: true };
    const afterOverride = reducer(undefined, {
      type: overrideOverwintering.fulfilled.type,
      payload: overridden,
    });
    expect(afterOverride.currentProfile?.user_overridden).toBe(true);

    const afterReset = reducer(afterOverride, {
      type: resetOverwintering.fulfilled.type,
      payload: profile,
    });
    expect(afterReset.currentProfile?.user_overridden).toBe(false);
  });

  it('clearCurrentProfile empties the profile', () => {
    const seeded = reducer(undefined, {
      type: fetchOverwintering.fulfilled.type,
      payload: profile,
    });
    const cleared = reducer(seeded, clearCurrentProfile());
    expect(cleared.currentProfile).toBeNull();
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
    mocked.overridePlantOverwintering.mockResolvedValue(overridden as never);
    const store = makeStore();
    await store.dispatch(
      overrideOverwintering({ plantKey: 'plant-1', patch: { winter_watering: 'minimal' } }),
    );
    expect(mocked.overridePlantOverwintering).toHaveBeenCalledWith('plant-1', {
      winter_watering: 'minimal',
    });
    expect(store.getState().season.currentProfile?.user_overridden).toBe(true);
  });

  it('resetOverwintering calls the reset endpoint', async () => {
    mocked.resetPlantOverwintering.mockResolvedValue(profile as never);
    const store = makeStore();
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
