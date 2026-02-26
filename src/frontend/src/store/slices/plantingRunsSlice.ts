import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import type { PlantingRun } from '@/api/types';
import * as api from '@/api/endpoints/plantingRuns';

interface PlantingRunsState {
  runs: PlantingRun[];
  currentRun: PlantingRun | null;
  loading: boolean;
  error: string | null;
}

const initialState: PlantingRunsState = {
  runs: [],
  currentRun: null,
  loading: false,
  error: null,
};

export const fetchPlantingRuns = createAsyncThunk(
  'plantingRuns/fetchAll',
  async ({
    offset,
    limit,
    status,
    runType,
  }: {
    offset?: number;
    limit?: number;
    status?: string;
    runType?: string;
  } = {}) => {
    return api.listPlantingRuns(offset, limit, status, runType);
  },
);

export const fetchPlantingRun = createAsyncThunk(
  'plantingRuns/fetchOne',
  async (key: string) => {
    return api.getPlantingRun(key);
  },
);

const plantingRunsSlice = createSlice({
  name: 'plantingRuns',
  initialState,
  reducers: {
    clearCurrentRun(state) {
      state.currentRun = null;
    },
    clearError(state) {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchPlantingRuns.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchPlantingRuns.fulfilled, (state, action) => {
        state.loading = false;
        state.runs = action.payload;
      })
      .addCase(fetchPlantingRuns.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message ?? 'Failed to load planting runs';
      })
      .addCase(fetchPlantingRun.fulfilled, (state, action) => {
        state.currentRun = action.payload;
      });
  },
});

export const { clearCurrentRun, clearError } = plantingRunsSlice.actions;
export default plantingRunsSlice.reducer;
