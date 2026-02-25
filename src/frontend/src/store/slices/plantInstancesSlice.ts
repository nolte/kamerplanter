import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import type { PlantInstance } from '@/api/types';
import * as api from '@/api/endpoints/plantInstances';

interface PlantInstancesState {
  items: PlantInstance[];
  current: PlantInstance | null;
  loading: boolean;
  error: string | null;
}

const initialState: PlantInstancesState = {
  items: [],
  current: null,
  loading: false,
  error: null,
};

export const fetchPlantInstances = createAsyncThunk(
  'plantInstances/fetchAll',
  async ({ offset, limit }: { offset?: number; limit?: number } = {}) => {
    return api.listPlantInstances(offset, limit);
  },
);

export const fetchPlantInstance = createAsyncThunk(
  'plantInstances/fetchOne',
  async (key: string) => {
    return api.getPlantInstance(key);
  },
);

const plantInstancesSlice = createSlice({
  name: 'plantInstances',
  initialState,
  reducers: {
    clearCurrent(state) {
      state.current = null;
    },
    clearError(state) {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchPlantInstances.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchPlantInstances.fulfilled, (state, action) => {
        state.loading = false;
        state.items = action.payload;
      })
      .addCase(fetchPlantInstances.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message ?? 'Failed to load plant instances';
      })
      .addCase(fetchPlantInstance.fulfilled, (state, action) => {
        state.current = action.payload;
      });
  },
});

export const { clearCurrent, clearError } = plantInstancesSlice.actions;
export default plantInstancesSlice.reducer;
