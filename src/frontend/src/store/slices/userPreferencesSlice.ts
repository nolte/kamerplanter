import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import type {
  UserPreference,
  ExperienceLevel,
  ModuleVisibilityState,
} from '@/api/types';
import * as api from '@/api/endpoints/userPreferences';
import { isLightMode } from '@/config/mode';
import {
  readLocalModuleVisibility,
  writeLocalModuleVisibility,
  clearLocalModuleVisibility,
} from '@/lib/moduleVisibilityStorage';
import type { RootState } from '@/store/store';

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
      module_visibility?: Record<string, ModuleVisibilityState>;
    };
  }) => {
    return api.updatePreferences(payload.updates);
  },
);

/**
 * REQ-042 — persist the full override set (set-semantics). In Light mode the
 * overrides live in localStorage; in Full mode they are PATCHed to the server.
 */
export const saveModuleVisibility = createAsyncThunk(
  'userPreferences/saveModuleVisibility',
  async (overrides: Record<string, ModuleVisibilityState>) => {
    if (isLightMode) {
      writeLocalModuleVisibility(overrides);
      return overrides;
    }
    const pref = await api.updatePreferences({ module_visibility: overrides });
    return pref.module_visibility ?? {};
  },
);

/**
 * REQ-042 / REQ-027 — migrate localStorage overrides into the server-side
 * preference after a Light-mode user signs up. Local entries win on conflict.
 */
export const migrateLocalModuleVisibility = createAsyncThunk(
  'userPreferences/migrateLocalModuleVisibility',
  async (_: void, { getState }) => {
    if (isLightMode) return null;
    const local = readLocalModuleVisibility();
    if (Object.keys(local).length === 0) return null;
    const state = getState() as RootState;
    const current = state.userPreferences.preferences?.module_visibility ?? {};
    const merged = { ...current, ...local };
    const pref = await api.updatePreferences({ module_visibility: merged });
    clearLocalModuleVisibility();
    return pref;
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
        // In Light mode localStorage is the source of truth for overrides.
        if (isLightMode && state.preferences) {
          state.preferences.module_visibility = readLocalModuleVisibility();
        }
      })
      .addCase(fetchPreferences.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message ?? 'errors.preferencesLoadFailed';
      })
      // Update
      .addCase(updateUserPreferences.fulfilled, (state, action) => {
        state.preferences = action.payload;
      })
      // REQ-042 module visibility
      .addCase(saveModuleVisibility.fulfilled, (state, action) => {
        if (state.preferences) {
          state.preferences.module_visibility = action.payload;
        }
      })
      .addCase(migrateLocalModuleVisibility.fulfilled, (state, action) => {
        if (action.payload) {
          state.preferences = action.payload;
        }
      });
  },
});

export const { clearError } = userPreferencesSlice.actions;
export default userPreferencesSlice.reducer;
