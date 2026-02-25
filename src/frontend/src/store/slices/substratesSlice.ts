import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import type { Substrate } from '@/api/types';
import * as api from '@/api/endpoints/substrates';

interface SubstratesState {
  items: Substrate[];
  current: Substrate | null;
  loading: boolean;
  error: string | null;
}

const initialState: SubstratesState = {
  items: [],
  current: null,
  loading: false,
  error: null,
};

export const fetchSubstrates = createAsyncThunk(
  'substrates/fetchAll',
  async ({ offset, limit }: { offset?: number; limit?: number } = {}) => {
    return api.listSubstrates(offset, limit);
  },
);

export const fetchSubstrate = createAsyncThunk(
  'substrates/fetchOne',
  async (key: string) => {
    return api.getSubstrate(key);
  },
);

const substratesSlice = createSlice({
  name: 'substrates',
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
      .addCase(fetchSubstrates.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchSubstrates.fulfilled, (state, action) => {
        state.loading = false;
        state.items = action.payload;
      })
      .addCase(fetchSubstrates.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message ?? 'Failed to load substrates';
      })
      .addCase(fetchSubstrate.fulfilled, (state, action) => {
        state.current = action.payload;
      });
  },
});

export const { clearCurrent, clearError } = substratesSlice.actions;
export default substratesSlice.reducer;
