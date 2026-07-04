import { createAsyncThunk } from '@reduxjs/toolkit';
import type { ActionReducerMapBuilder } from '@reduxjs/toolkit';
import { createListSlice, type ListState } from '@/store/createListSlice';
import type {
  OverwinteringProfile,
  WinterHardinessOverview,
} from '@/api/types';
import * as api from '@/api/endpoints/overwinteringProfiles';

/**
 * REQ-022 — dashboard winter-hardiness overview thunk. Kept separate from the
 * list slice because the widget aggregates counts (not the paginated list).
 */
export const fetchHardinessOverview = createAsyncThunk(
  'overwinteringProfiles/fetchHardinessOverview',
  async () => api.getHardinessOverview(),
);

/** Extra state carried alongside the generic list state. */
export interface OverwinteringProfilesExtraState {
  overview: WinterHardinessOverview | null;
  overviewLoading: boolean;
  overviewError: string | null;
}

type OverwinteringProfilesState = ListState<OverwinteringProfile> &
  OverwinteringProfilesExtraState;

function overviewCases(
  builder: ActionReducerMapBuilder<ListState<OverwinteringProfile>>,
): void {
  // The generic ListState is extended with overview fields via preloaded state
  // and the extraCases hook; cast to the widened state to mutate them.
  builder
    .addCase(fetchHardinessOverview.pending, (state) => {
      const s = state as OverwinteringProfilesState;
      s.overviewLoading = true;
      s.overviewError = null;
    })
    .addCase(fetchHardinessOverview.fulfilled, (state, action) => {
      const s = state as OverwinteringProfilesState;
      s.overviewLoading = false;
      s.overview = action.payload;
    })
    .addCase(fetchHardinessOverview.rejected, (state, action) => {
      const s = state as OverwinteringProfilesState;
      s.overviewLoading = false;
      s.overviewError = action.error.message ?? 'errors.loadFailed';
    });
}

const { slice, reducer, fetchList, fetchOne, actions } =
  createListSlice<OverwinteringProfile>({
    name: 'overwinteringProfiles',
    list: (offset, limit) => api.listOverwinteringProfiles(offset, limit),
    getOne: (key) => api.getOverwinteringProfile(key),
    extraCases: overviewCases,
  });

// Seed the extra fields onto the generic list initial state so they always
// exist before the reducer mutates them (the extraCases below mutate the draft
// in place, which requires the fields to be present up-front).
const initialExtra: OverwinteringProfilesExtraState = {
  overview: null,
  overviewLoading: false,
  overviewError: null,
};

const genericInitial = reducer(undefined, {
  type: 'overwinteringProfiles/@@seed',
}) as ListState<OverwinteringProfile>;

const initialState: OverwinteringProfilesState = {
  ...genericInitial,
  ...initialExtra,
};

/** Reducer that starts from the widened (list + overview) initial state. */
function reducerWithExtra(
  state: OverwinteringProfilesState = initialState,
  action: Parameters<typeof reducer>[1],
): OverwinteringProfilesState {
  return reducer(state, action) as OverwinteringProfilesState;
}

export const fetchOverwinteringProfiles = fetchList;
export const fetchOverwinteringProfile = fetchOne!;
export const { clearCurrent, clearError } = actions;
export { slice };
export default reducerWithExtra;
