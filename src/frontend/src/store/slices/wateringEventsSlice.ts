import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import type { WateringEvent, WateringStats } from '@/api/types';
import * as api from '@/api/endpoints/watering-events';

interface WateringEventsState {
  events: WateringEvent[];
  stats: WateringStats | null;
  loading: boolean;
  error: string | null;
}

const initialState: WateringEventsState = {
  events: [],
  stats: null,
  loading: false,
  error: null,
};

export const fetchWateringEvents = createAsyncThunk(
  'wateringEvents/fetchAll',
  async ({
    offset,
    limit,
  }: {
    offset?: number;
    limit?: number;
  } = {}) => {
    return api.listWateringEvents(offset, limit);
  },
);

export const fetchLocationWateringEvents = createAsyncThunk(
  'wateringEvents/fetchByLocation',
  async ({
    locationKey,
    offset,
    limit,
  }: {
    locationKey: string;
    offset?: number;
    limit?: number;
  }) => {
    return api.getLocationWateringEvents(locationKey, offset, limit);
  },
);

export const fetchLocationWateringStats = createAsyncThunk(
  'wateringEvents/fetchStats',
  async (locationKey: string) => {
    return api.getLocationWateringStats(locationKey);
  },
);

const wateringEventsSlice = createSlice({
  name: 'wateringEvents',
  initialState,
  reducers: {
    clearError(state) {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchWateringEvents.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchWateringEvents.fulfilled, (state, action) => {
        state.loading = false;
        state.events = action.payload;
      })
      .addCase(fetchWateringEvents.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message ?? 'Failed to load watering events';
      })
      .addCase(fetchLocationWateringEvents.fulfilled, (state, action) => {
        state.events = action.payload;
      })
      .addCase(fetchLocationWateringStats.fulfilled, (state, action) => {
        state.stats = action.payload;
      });
  },
});

export const { clearError } = wateringEventsSlice.actions;
export default wateringEventsSlice.reducer;
