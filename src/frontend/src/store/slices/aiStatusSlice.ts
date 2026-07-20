import { createAsyncThunk, createSlice } from '@reduxjs/toolkit';
import type { AiStatus } from '@/api/types';
import { getAiStatus } from '@/api/endpoints/ai';

/**
 * Issue #685 — cluster-wide KI-Assistent availability.
 *
 * Fetched once at app start (analogous to {@link identificationSlice}'s status)
 * so the sidebar can hide the KI-Assistent nav entry and the page can degrade to
 * a "not configured" state when AI features are disabled cluster-wide.
 *
 * `available` starts as `null` (unknown) and is only ever set to `false` when we
 * positively learn the feature is off — the nav entry stays visible while the
 * status is unknown, so a slow/failed probe never hides a working feature.
 */

interface AiStatusState {
  available: boolean | null;
  loading: boolean;
}

const initialState: AiStatusState = {
  available: null,
  loading: false,
};

export const fetchAiStatus = createAsyncThunk<AiStatus>('aiStatus/fetch', async () =>
  getAiStatus(),
);

const aiStatusSlice = createSlice({
  name: 'aiStatus',
  initialState,
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(fetchAiStatus.pending, (state) => {
        state.loading = true;
      })
      .addCase(fetchAiStatus.fulfilled, (state, action) => {
        state.loading = false;
        state.available = action.payload.available;
      })
      .addCase(fetchAiStatus.rejected, (state) => {
        state.loading = false;
        // A failed probe is inconclusive, NOT "feature off": /ai/status is ungated
        // and answers 200 in both flag states, so a rejection only ever stems from
        // a transient fault (network/timeout/5xx/cold-start). Leaving `available`
        // as `null` (unknown) keeps the nav entry visible — only a definitive
        // `fulfilled` payload of `{ available: false }` gates it (fail-open).
      });
  },
});

export default aiStatusSlice.reducer;
