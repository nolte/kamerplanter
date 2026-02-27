import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import type { Tank } from '@/api/types';
import * as api from '@/api/endpoints/tanks';

interface TanksState {
  tanks: Tank[];
  currentTank: Tank | null;
  loading: boolean;
  error: string | null;
}

const initialState: TanksState = {
  tanks: [],
  currentTank: null,
  loading: false,
  error: null,
};

export const fetchTanks = createAsyncThunk(
  'tanks/fetchAll',
  async ({
    offset,
    limit,
    tankType,
  }: {
    offset?: number;
    limit?: number;
    tankType?: string;
  } = {}) => {
    return api.listTanks(offset, limit, tankType);
  },
);

export const fetchTank = createAsyncThunk(
  'tanks/fetchOne',
  async (key: string) => {
    return api.getTank(key);
  },
);

const tanksSlice = createSlice({
  name: 'tanks',
  initialState,
  reducers: {
    clearCurrentTank(state) {
      state.currentTank = null;
    },
    clearError(state) {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchTanks.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchTanks.fulfilled, (state, action) => {
        state.loading = false;
        state.tanks = action.payload;
      })
      .addCase(fetchTanks.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message ?? 'Failed to load tanks';
      })
      .addCase(fetchTank.fulfilled, (state, action) => {
        state.currentTank = action.payload;
      });
  },
});

export const { clearCurrentTank, clearError } = tanksSlice.actions;
export default tanksSlice.reducer;
