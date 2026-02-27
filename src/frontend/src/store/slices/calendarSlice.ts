import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import type { CalendarEvent, CalendarFeed } from '@/api/types';
import * as api from '@/api/endpoints/calendar';

interface CalendarState {
  events: CalendarEvent[];
  feeds: CalendarFeed[];
  loading: boolean;
  feedsLoading: boolean;
  error: string | null;
}

const initialState: CalendarState = {
  events: [],
  feeds: [],
  loading: false,
  feedsLoading: false,
  error: null,
};

export const fetchCalendarEvents = createAsyncThunk(
  'calendar/fetchEvents',
  async ({
    start,
    end,
    category,
    tenantKey,
  }: {
    start: string;
    end: string;
    category?: string;
    tenantKey?: string;
  }) => {
    return api.getCalendarEvents(start, end, category, tenantKey);
  },
);

export const fetchCalendarFeeds = createAsyncThunk(
  'calendar/fetchFeeds',
  async ({ userKey, tenantKey }: { userKey?: string; tenantKey?: string } = {}) => {
    return api.listCalendarFeeds(userKey, tenantKey);
  },
);

export const createCalendarFeed = createAsyncThunk(
  'calendar/createFeed',
  async ({ name, filters }: { name: string; filters: { categories: string[]; site_key: string | null } }) => {
    return api.createCalendarFeed(name, filters);
  },
);

export const deleteCalendarFeed = createAsyncThunk(
  'calendar/deleteFeed',
  async (key: string) => {
    await api.deleteCalendarFeed(key);
    return key;
  },
);

export const regenerateCalendarFeedToken = createAsyncThunk(
  'calendar/regenerateToken',
  async (key: string) => {
    return api.regenerateCalendarFeedToken(key);
  },
);

const calendarSlice = createSlice({
  name: 'calendar',
  initialState,
  reducers: {
    clearError(state) {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      // Events
      .addCase(fetchCalendarEvents.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchCalendarEvents.fulfilled, (state, action) => {
        state.loading = false;
        state.events = action.payload.events;
      })
      .addCase(fetchCalendarEvents.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message ?? 'Failed to load calendar events';
      })
      // Feeds
      .addCase(fetchCalendarFeeds.pending, (state) => {
        state.feedsLoading = true;
      })
      .addCase(fetchCalendarFeeds.fulfilled, (state, action) => {
        state.feedsLoading = false;
        state.feeds = action.payload;
      })
      .addCase(fetchCalendarFeeds.rejected, (state, action) => {
        state.feedsLoading = false;
        state.error = action.error.message ?? 'Failed to load feeds';
      })
      // Create feed
      .addCase(createCalendarFeed.fulfilled, (state, action) => {
        state.feeds.push(action.payload);
      })
      // Delete feed
      .addCase(deleteCalendarFeed.fulfilled, (state, action) => {
        state.feeds = state.feeds.filter((f) => f.key !== action.payload);
      })
      // Regenerate token
      .addCase(regenerateCalendarFeedToken.fulfilled, (state, action) => {
        const index = state.feeds.findIndex((f) => f.key === action.payload.key);
        if (index >= 0) {
          state.feeds[index] = action.payload;
        }
      });
  },
});

export const { clearError } = calendarSlice.actions;
export default calendarSlice.reducer;
