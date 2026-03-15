import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import type { WateringLog } from '@/api/types';
import * as api from '@/api/endpoints/watering-logs';

interface WateringLogsState {
  logs: WateringLog[];
  currentLog: WateringLog | null;
  loading: boolean;
  error: string | null;
}

const initialState: WateringLogsState = {
  logs: [],
  currentLog: null,
  loading: false,
  error: null,
};

export const fetchWateringLogs = createAsyncThunk(
  'wateringLogs/fetchAll',
  async ({
    offset,
    limit,
  }: {
    offset?: number;
    limit?: number;
  } = {}) => {
    return api.listWateringLogs(offset, limit);
  },
);

export const fetchWateringLog = createAsyncThunk(
  'wateringLogs/fetchOne',
  async (key: string) => {
    return api.getWateringLog(key);
  },
);

const wateringLogsSlice = createSlice({
  name: 'wateringLogs',
  initialState,
  reducers: {
    clearCurrentLog(state) {
      state.currentLog = null;
    },
    clearError(state) {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchWateringLogs.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchWateringLogs.fulfilled, (state, action) => {
        state.loading = false;
        state.logs = action.payload;
      })
      .addCase(fetchWateringLogs.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message ?? 'Failed to load watering logs';
      })
      .addCase(fetchWateringLog.fulfilled, (state, action) => {
        state.currentLog = action.payload;
      });
  },
});

export const { clearCurrentLog, clearError } = wateringLogsSlice.actions;
export default wateringLogsSlice.reducer;
