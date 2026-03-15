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
    brand,
    tankSafe,
    isOrganic,
  }: {
    offset?: number;
    limit?: number;
    fertilizerType?: string;
    brand?: string;
    tankSafe?: boolean;
    isOrganic?: boolean;
  } = {}) => {
    const filters: Record<string, string> = {};
    if (fertilizerType) filters.fertilizer_type = fertilizerType;
    if (brand) filters.brand = brand;
    if (tankSafe !== undefined) filters.tank_safe = String(tankSafe);
    if (isOrganic !== undefined) filters.is_organic = String(isOrganic);
    return api.fetchFertilizers(offset, limit, Object.keys(filters).length > 0 ? filters : undefined);
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
