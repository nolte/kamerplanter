import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import type { Species } from '@/api/types';
import * as api from '@/api/endpoints/species';

interface SpeciesState {
  items: Species[];
  total: number;
  offset: number;
  limit: number;
  current: Species | null;
  loading: boolean;
  error: string | null;
}

const initialState: SpeciesState = {
  items: [],
  total: 0,
  offset: 0,
  limit: 50,
  current: null,
  loading: false,
  error: null,
};

export const fetchSpeciesList = createAsyncThunk(
  'species/fetchAll',
  async ({ offset = 0, limit = 50 }: { offset?: number; limit?: number } = {}) => {
    return api.listSpecies(offset, limit);
  },
);

export const fetchSpecies = createAsyncThunk('species/fetchOne', async (key: string) => {
  return api.getSpecies(key);
});

const speciesSlice = createSlice({
  name: 'species',
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
      .addCase(fetchSpeciesList.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchSpeciesList.fulfilled, (state, action) => {
        state.loading = false;
        state.items = action.payload.items;
        state.total = action.payload.total;
        state.offset = action.payload.offset;
        state.limit = action.payload.limit;
      })
      .addCase(fetchSpeciesList.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message ?? 'Failed to load species';
      })
      .addCase(fetchSpecies.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchSpecies.fulfilled, (state, action) => {
        state.loading = false;
        state.current = action.payload;
      })
      .addCase(fetchSpecies.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message ?? 'Failed to load species';
      });
  },
});

export const { clearCurrent, clearError } = speciesSlice.actions;
export default speciesSlice.reducer;
