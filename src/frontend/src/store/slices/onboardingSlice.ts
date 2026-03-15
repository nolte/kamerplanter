import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import type { OnboardingState, StarterKit, ExperienceLevel } from '@/api/types';
import * as onboardingApi from '@/api/endpoints/onboarding';
import * as starterKitsApi from '@/api/endpoints/starterKits';

interface OnboardingSliceState {
  state: OnboardingState | null;
  kits: StarterKit[];
  loading: boolean;
  error: string | null;
}

const initialState: OnboardingSliceState = {
  state: null,
  kits: [],
  loading: false,
  error: null,
};

export const fetchOnboardingState = createAsyncThunk(
  'onboarding/fetchState',
  async (userKey?: string) => {
    return onboardingApi.getState(userKey);
  },
);

export const fetchStarterKits = createAsyncThunk(
  'onboarding/fetchKits',
  async (difficulty?: string) => {
    return starterKitsApi.listKits(difficulty);
  },
);

export const completeOnboarding = createAsyncThunk(
  'onboarding/complete',
  async (payload: {
    kit_id?: string;
    experience_level?: ExperienceLevel;
    site_name?: string;
    plant_count?: number;
    has_ro_system?: boolean;
    tap_water_ec_ms?: number;
    tap_water_ph?: number;
  }) => {
    return onboardingApi.complete(payload);
  },
);

export const skipOnboarding = createAsyncThunk('onboarding/skip', async () => {
  return onboardingApi.skip();
});

const onboardingSlice = createSlice({
  name: 'onboarding',
  initialState,
  reducers: {
    clearError(state) {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      // Fetch state
      .addCase(fetchOnboardingState.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchOnboardingState.fulfilled, (state, action) => {
        state.loading = false;
        state.state = action.payload;
      })
      .addCase(fetchOnboardingState.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message ?? 'Failed to load onboarding state';
      })
      // Fetch kits
      .addCase(fetchStarterKits.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchStarterKits.fulfilled, (state, action) => {
        state.loading = false;
        state.kits = action.payload;
      })
      .addCase(fetchStarterKits.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message ?? 'Failed to load starter kits';
      })
      // Complete
      .addCase(completeOnboarding.fulfilled, (state) => {
        if (state.state) {
          state.state.completed = true;
        }
      })
      // Skip
      .addCase(skipOnboarding.fulfilled, (state, action) => {
        state.state = action.payload;
      });
  },
});

export const { clearError } = onboardingSlice.actions;
export default onboardingSlice.reducer;
