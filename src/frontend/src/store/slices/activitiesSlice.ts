import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import type { Activity } from '@/api/types';
import * as api from '@/api/endpoints/activities';

interface ActivitiesState {
  items: Activity[];
  current: Activity | null;
  loading: boolean;
  error: string | null;
}

const initialState: ActivitiesState = {
  items: [],
  current: null,
  loading: false,
  error: null,
};

export const fetchActivities = createAsyncThunk(
  'activities/fetchAll',
  async (params?: { category?: string; scope?: 'universal' | 'restricted'; species?: string }) => {
    return api.listActivities(params);
  },
);

export const fetchActivity = createAsyncThunk(
  'activities/fetchOne',
  async (key: string) => {
    return api.getActivity(key);
  },
);

const activitiesSlice = createSlice({
  name: 'activities',
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
      .addCase(fetchActivities.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchActivities.fulfilled, (state, action) => {
        state.loading = false;
        state.items = action.payload;
      })
      .addCase(fetchActivities.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message ?? 'Failed to load activities';
      })
      .addCase(fetchActivity.fulfilled, (state, action) => {
        state.current = action.payload;
      });
  },
});

export const { clearCurrent, clearError } = activitiesSlice.actions;
export default activitiesSlice.reducer;
