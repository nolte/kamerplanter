import { createAsyncThunk, createSlice } from '@reduxjs/toolkit';

import * as api from '@/api/endpoints/fertilizers';
import type { Fertilizer } from '@/api/types';

interface FertilizersState {
  fertilizers: Fertilizer[];
  currentFertilizer: Fertilizer | null;
  loading: boolean;
  error: string | null;
}

const initialState: FertilizersState = {
  fertilizers: [],
  currentFertilizer: null,
  loading: false,
  error: null,
};

export const fetchFertilizers = createAsyncThunk(
  'fertilizers/fetchAll',
  async ({
    offset,
    limit,
    fertilizerType,
  }: {
    offset?: number;
    limit?: number;
    fertilizerType?: string;
  } = {}) => {
    return api.fetchFertilizers(offset, limit, fertilizerType ? { fertilizer_type: fertilizerType } : undefined);
  },
);

export const fetchFertilizer = createAsyncThunk(
  'fertilizers/fetchOne',
  async (key: string) => {
    return api.fetchFertilizer(key);
  },
);

const fertilizersSlice = createSlice({
  name: 'fertilizers',
  initialState,
  reducers: {
    clearCurrentFertilizer(state) {
      state.currentFertilizer = null;
    },
    clearError(state) {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchFertilizers.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchFertilizers.fulfilled, (state, action) => {
        state.loading = false;
        state.fertilizers = action.payload;
      })
      .addCase(fetchFertilizers.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message ?? 'Failed to load fertilizers';
      })
      .addCase(fetchFertilizer.fulfilled, (state, action) => {
        state.currentFertilizer = action.payload;
      });
  },
});

export const { clearCurrentFertilizer, clearError } = fertilizersSlice.actions;
export default fertilizersSlice.reducer;
