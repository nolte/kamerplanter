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
        // Treat an unreachable probe as "unavailable" — a 404/network error means
        // the feature is off (the guarded routes 404 when the flag is off).
        state.available = false;
      });
  },
});

export default aiStatusSlice.reducer;
