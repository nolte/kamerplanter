import { createAsyncThunk, createSlice } from '@reduxjs/toolkit';

import * as api from '@/api/endpoints/nutrient-plans';
import type { NutrientPlan } from '@/api/types';

interface NutrientPlansState {
  plans: NutrientPlan[];
  currentPlan: NutrientPlan | null;
  loading: boolean;
  error: string | null;
}

const initialState: NutrientPlansState = {
  plans: [],
  currentPlan: null,
  loading: false,
  error: null,
};

export const fetchNutrientPlans = createAsyncThunk(
  'nutrientPlans/fetchAll',
  async ({
    offset,
    limit,
    isTemplate,
  }: {
    offset?: number;
    limit?: number;
    isTemplate?: boolean;
  } = {}) => {
    return api.fetchNutrientPlans(
      offset,
      limit,
      isTemplate !== undefined ? { is_template: String(isTemplate) } : undefined,
    );
  },
);

export const fetchNutrientPlan = createAsyncThunk(
  'nutrientPlans/fetchOne',
  async (key: string) => {
    return api.fetchNutrientPlan(key);
  },
);

const nutrientPlansSlice = createSlice({
  name: 'nutrientPlans',
  initialState,
  reducers: {
    clearCurrentPlan(state) {
      state.currentPlan = null;
    },
    clearError(state) {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchNutrientPlans.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchNutrientPlans.fulfilled, (state, action) => {
        state.loading = false;
        state.plans = action.payload;
      })
      .addCase(fetchNutrientPlans.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message ?? 'Failed to load nutrient plans';
      })
      .addCase(fetchNutrientPlan.fulfilled, (state, action) => {
        state.currentPlan = action.payload;
      });
  },
});

export const { clearCurrentPlan, clearError } = nutrientPlansSlice.actions;
export default nutrientPlansSlice.reducer;
