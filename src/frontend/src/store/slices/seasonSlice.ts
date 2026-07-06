import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import type {
  OverwinteringOverride,
  OverwinteringProfile,
  PlantOverwinteringStatus,
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
  /** Overwintering profile of the plant instance currently in view. */
  currentProfile: OverwinteringProfile | null;
  profileLoading: boolean;
  profileError: string | null;
  /**
   * Winter-hardiness status of the plant currently in view (loaded lazily only
   * when there is no profile). Lets the empty state tell "genuinely winter-hardy"
   * (green) apart from "profile is materialised in autumn" (yellow/red) instead
   * of always showing the misleading winter-hardy hint.
   */
  currentStatus: PlantOverwinteringStatus | null;
  statusLoading: boolean;
  /**
   * Plant key of the most recently requested profile read. Used to discard
   * stale in-flight responses when the user navigates plant A → B before A's
   * request resolves — otherwise A's profile would leak onto B's detail page
   * (the slice is shared across all `OverwinteringSection` mounts).
   */
  requestedPlantKey: string | null;
}

const initialState: SeasonSliceState = {
  overview: [],
  overviewLoading: false,
  overviewError: null,
  currentProfile: null,
  profileLoading: false,
  profileError: null,
  currentStatus: null,
  statusLoading: false,
  requestedPlantKey: null,
};

export const fetchSeasonOverview = createAsyncThunk(
  'season/fetchOverview',
  async () => (await api.getSeasonOverview()).states,
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

export const fetchOverwinteringStatus = createAsyncThunk(
  'season/fetchOverwinteringStatus',
  async (plantKey: string): Promise<PlantOverwinteringStatus> =>
    api.getPlantOverwinteringStatus(plantKey),
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
      state.currentStatus = null;
      state.statusLoading = false;
      // Drop the pending request marker so a late response arriving after the
      // section unmounted can no longer write into the shared slice.
      state.requestedPlantKey = null;
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
      .addCase(fetchSeasonOverview.rejected, (state) => {
        state.overviewLoading = false;
        state.overviewError = 'errors.loadFailed';
      })
      // Profile read
      .addCase(fetchOverwintering.pending, (state, action) => {
        state.profileLoading = true;
        state.profileError = null;
        state.requestedPlantKey = action.meta.arg;
        // Never keep a previous plant's profile visible while the new one loads:
        // the loading skeleton must win (its guard is `!currentProfile`).
        state.currentProfile = null;
        // A stale status from the previous plant must never leak into the new
        // plant's empty state — it is re-fetched lazily if this plant has none.
        state.currentStatus = null;
        state.statusLoading = false;
      })
      .addCase(fetchOverwintering.fulfilled, (state, action) => {
        // Discard responses for a plant the user already navigated away from.
        if (action.meta.arg !== state.requestedPlantKey) return;
        state.profileLoading = false;
        state.currentProfile = action.payload;
      })
      .addCase(fetchOverwintering.rejected, (state, action) => {
        if (action.meta.arg !== state.requestedPlantKey) return;
        state.profileLoading = false;
        // Surface a localised key (FE-L5), never the raw backend/technical
        // message — ErrorDisplay resolves `errors.*` keys to the active locale.
        state.profileError = 'errors.loadFailed';
      })
      // Status read (lazy, only when the profile read yielded no profile).
      .addCase(fetchOverwinteringStatus.pending, (state, action) => {
        state.requestedPlantKey = action.meta.arg;
        state.statusLoading = true;
      })
      .addCase(fetchOverwinteringStatus.fulfilled, (state, action) => {
        if (action.meta.arg !== state.requestedPlantKey) return;
        state.statusLoading = false;
        state.currentStatus = action.payload;
      })
      .addCase(fetchOverwinteringStatus.rejected, (state, action) => {
        if (action.meta.arg !== state.requestedPlantKey) return;
        state.statusLoading = false;
        // Store an explicit "unknown" status (not null) so the empty state leaves
        // the skeleton and shows the neutral pending hint — never a false
        // "winter-hardy" all-clear and never an endless skeleton. `site_overwinterable`
        // stays `true` here so the (safe) pending hint wins over the indoor hint: on a
        // failed read we do not know the site type and must not claim "no overwintering
        // needed" (the indoor hint only fires on an explicit `false` from the backend).
        state.currentStatus = {
          has_profile: false,
          hardiness_light: null,
          will_materialize: false,
          site_overwinterable: true,
        };
      })
      // Profile mutations — both replace the current profile, but only if the
      // user is still viewing the same plant (guards a slow PATCH/POST that
      // resolves after navigation).
      .addCase(overrideOverwintering.fulfilled, (state, action) => {
        if (action.meta.arg.plantKey !== state.requestedPlantKey) return;
        state.currentProfile = action.payload;
        // A profile now exists — drop any stale empty-state status.
        state.currentStatus = null;
      })
      .addCase(resetOverwintering.fulfilled, (state, action) => {
        if (action.meta.arg !== state.requestedPlantKey) return;
        state.currentProfile = action.payload;
        state.currentStatus = null;
      });
  },
});

export const { clearCurrentProfile } = seasonSlice.actions;
export default seasonSlice.reducer;
