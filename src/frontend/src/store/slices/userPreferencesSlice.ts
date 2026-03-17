import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import type { UserPreference, ExperienceLevel } from '@/api/types';
import * as api from '@/api/endpoints/userPreferences';

interface UserPreferencesState {
  preferences: UserPreference | null;
  loading: boolean;
  error: string | null;
}

const initialState: UserPreferencesState = {
  preferences: null,
  loading: false,
  error: null,
};

export const fetchPreferences = createAsyncThunk(
  'userPreferences/fetch',
  async () => {
    return api.getPreferences();
  },
);

export const updateUserPreferences = createAsyncThunk(
  'userPreferences/update',
  async (payload: {
    updates: {
      experience_level?: ExperienceLevel;
      locale?: string;
      theme?: string;
      onboarding_completed?: boolean;
      watering_can_liters?: number;
      smart_home_enabled?: boolean;
    };
  }) => {
    return api.updatePreferences(payload.updates);
  },
);

const userPreferencesSlice = createSlice({
  name: 'userPreferences',
  initialState,
  reducers: {
    clearError(state) {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      // Fetch
      .addCase(fetchPreferences.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchPreferences.fulfilled, (state, action) => {
        state.loading = false;
        state.preferences = action.payload;
      })
      .addCase(fetchPreferences.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message ?? 'Failed to load preferences';
      })
      // Update
      .addCase(updateUserPreferences.fulfilled, (state, action) => {
        state.preferences = action.payload;
      });
  },
});

export const { clearError } = userPreferencesSlice.actions;
export default userPreferencesSlice.reducer;
