import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import type { BotanicalFamily } from '@/api/types';
import * as api from '@/api/endpoints/botanicalFamilies';

interface BotanicalFamiliesState {
  items: BotanicalFamily[];
  current: BotanicalFamily | null;
  loading: boolean;
  error: string | null;
}

const initialState: BotanicalFamiliesState = {
  items: [],
  current: null,
  loading: false,
  error: null,
};

export const fetchBotanicalFamilies = createAsyncThunk(
  'botanicalFamilies/fetchAll',
  async ({ offset, limit }: { offset?: number; limit?: number } = {}) => {
    return api.listBotanicalFamilies(offset, limit);
  },
);

export const fetchBotanicalFamily = createAsyncThunk(
  'botanicalFamilies/fetchOne',
  async (key: string) => {
    return api.getBotanicalFamily(key);
  },
);

const botanicalFamiliesSlice = createSlice({
  name: 'botanicalFamilies',
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
      .addCase(fetchBotanicalFamilies.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchBotanicalFamilies.fulfilled, (state, action) => {
        state.loading = false;
        state.items = action.payload;
      })
      .addCase(fetchBotanicalFamilies.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message ?? 'Failed to load botanical families';
      })
      .addCase(fetchBotanicalFamily.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchBotanicalFamily.fulfilled, (state, action) => {
        state.loading = false;
        state.current = action.payload;
      })
      .addCase(fetchBotanicalFamily.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message ?? 'Failed to load botanical family';
      });
  },
});

export const { clearCurrent, clearError } = botanicalFamiliesSlice.actions;
export default botanicalFamiliesSlice.reducer;
