import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import type { FeedingEvent } from '@/api/types';
import * as api from '@/api/endpoints/feeding-events';

interface FeedingEventsState {
  events: FeedingEvent[];
  currentEvent: FeedingEvent | null;
  loading: boolean;
  error: string | null;
}

const initialState: FeedingEventsState = {
  events: [],
  currentEvent: null,
  loading: false,
  error: null,
};

export const fetchFeedingEvents = createAsyncThunk(
  'feedingEvents/fetchAll',
  async ({
    offset,
    limit,
  }: {
    offset?: number;
    limit?: number;
  } = {}) => {
    return api.listFeedingEvents(offset, limit);
  },
);

export const fetchFeedingEvent = createAsyncThunk(
  'feedingEvents/fetchOne',
  async (key: string) => {
    return api.getFeedingEvent(key);
  },
);

const feedingEventsSlice = createSlice({
  name: 'feedingEvents',
  initialState,
  reducers: {
    clearCurrentEvent(state) {
      state.currentEvent = null;
    },
    clearError(state) {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchFeedingEvents.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchFeedingEvents.fulfilled, (state, action) => {
        state.loading = false;
        state.events = action.payload;
      })
      .addCase(fetchFeedingEvents.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message ?? 'Failed to load feeding events';
      })
      .addCase(fetchFeedingEvent.fulfilled, (state, action) => {
        state.currentEvent = action.payload;
      });
  },
});

export const { clearCurrentEvent, clearError } = feedingEventsSlice.actions;
export default feedingEventsSlice.reducer;
