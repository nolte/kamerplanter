import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import type {
  OverwinteringOverride,
  OverwinteringProfile,
  SeasonState,
} from '@/api/types';
import * as api from '@/api/endpoints/season';
import { isApiError } from '@/api/errors';

/**
 * REQ-047 §4.1–§4.3 — season & overwintering-automation state.
 *
 * Holds the aggregated season overview (dashboard widget / spring assistant),
 * an optional single-site state, and the currently viewed overwintering profile
 * of a plant instance (detail-page override section). Kept as a dedicated slice
 * because these reads span sites and plants and are consumed by several views.
 */
export interface SeasonSliceState {
  /** Season states of all outdoor/greenhouse sites (season/overview). */
  overview: SeasonState[];
  overviewLoading: boolean;
  overviewError: string | null;
  /** Optional per-site state keyed by site_key. */
  siteStates: Record<string, SeasonState>;
  /** Overwintering profile of the plant instance currently in view. */
  currentProfile: OverwinteringProfile | null;
  profileLoading: boolean;
  profileError: string | null;
}

const initialState: SeasonSliceState = {
  overview: [],
  overviewLoading: false,
  overviewError: null,
  siteStates: {},
  currentProfile: null,
  profileLoading: false,
  profileError: null,
};

export const fetchSeasonOverview = createAsyncThunk(
  'season/fetchOverview',
  async () => (await api.getSeasonOverview()).states,
);

export const fetchSeasonState = createAsyncThunk(
  'season/fetchState',
  async (siteKey: string) => api.getSiteSeasonState(siteKey),
);

export const fetchOverwintering = createAsyncThunk(
  'season/fetchOverwintering',
  async (plantKey: string): Promise<OverwinteringProfile | null> => {
    try {
      return await api.getPlantOverwintering(plantKey);
    } catch (err) {
      // REQ-047 §4.3/§4.4 — 404 is the domain-legitimate "no profile" signal
      // (winter-hardy plant, or not yet materialised), not a failure. A real
      // failure (500, network) must still reject so the UI never confuses
      // "couldn't load" with "this plant needs no winter protection".
      if (isApiError(err) && err.statusCode === 404) return null;
      throw err;
    }
  },
);

export const overrideOverwintering = createAsyncThunk(
  'season/overrideOverwintering',
  async ({ plantKey, patch }: { plantKey: string; patch: OverwinteringOverride }) =>
    api.overridePlantOverwintering(plantKey, patch),
);

export const resetOverwintering = createAsyncThunk(
  'season/resetOverwintering',
  async (plantKey: string) => api.resetPlantOverwintering(plantKey),
);

const seasonSlice = createSlice({
  name: 'season',
  initialState,
  reducers: {
    clearCurrentProfile(state) {
      state.currentProfile = null;
      state.profileError = null;
    },
  },
  extraReducers: (builder) => {
    builder
      // Overview
      .addCase(fetchSeasonOverview.pending, (state) => {
        state.overviewLoading = true;
        state.overviewError = null;
      })
      .addCase(fetchSeasonOverview.fulfilled, (state, action) => {
        state.overviewLoading = false;
        state.overview = action.payload;
      })
      .addCase(fetchSeasonOverview.rejected, (state, action) => {
        state.overviewLoading = false;
        state.overviewError = action.error.message ?? 'errors.loadFailed';
      })
      // Single site
      .addCase(fetchSeasonState.fulfilled, (state, action) => {
        state.siteStates[action.payload.site_key] = action.payload;
      })
      // Profile read
      .addCase(fetchOverwintering.pending, (state) => {
        state.profileLoading = true;
        state.profileError = null;
      })
      .addCase(fetchOverwintering.fulfilled, (state, action) => {
        state.profileLoading = false;
        state.currentProfile = action.payload;
      })
      .addCase(fetchOverwintering.rejected, (state, action) => {
        state.profileLoading = false;
        state.profileError = action.error.message ?? 'errors.loadFailed';
      })
      // Profile mutations — both replace the current profile
      .addCase(overrideOverwintering.fulfilled, (state, action) => {
        state.currentProfile = action.payload;
      })
      .addCase(resetOverwintering.fulfilled, (state, action) => {
        state.currentProfile = action.payload;
      });
  },
});

export const { clearCurrentProfile } = seasonSlice.actions;
export default seasonSlice.reducer;
