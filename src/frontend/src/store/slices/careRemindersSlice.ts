import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import type { CareDashboardEntry, CareProfile, ReminderType } from '@/api/types';
import type { ConfirmReminderOptions } from '@/api/endpoints/careReminders';
import * as api from '@/api/endpoints/careReminders';

interface CareRemindersState {
  dashboard: CareDashboardEntry[];
  currentProfile: CareProfile | null;
  loading: boolean;
  error: string | null;
}

const initialState: CareRemindersState = {
  dashboard: [],
  currentProfile: null,
  loading: false,
  error: null,
};

export const fetchDashboard = createAsyncThunk(
  'careReminders/fetchDashboard',
  async (hemisphere?: string) => {
    return api.getDashboard(hemisphere);
  },
);

export const fetchProfile = createAsyncThunk(
  'careReminders/fetchProfile',
  async ({
    plantKey,
    speciesName,
    botanicalFamily,
  }: {
    plantKey: string;
    speciesName?: string;
    botanicalFamily?: string;
  }) => {
    return api.getOrCreateProfile(plantKey, speciesName, botanicalFamily);
  },
);

export const confirmCareReminder = createAsyncThunk(
  'careReminders/confirm',
  async ({
    plantKey,
    reminderType,
    options,
  }: {
    plantKey: string;
    reminderType: ReminderType;
    options?: ConfirmReminderOptions;
  }) => {
    return api.confirmReminder(plantKey, reminderType, options);
  },
);

export const snoozeCareReminder = createAsyncThunk(
  'careReminders/snooze',
  async ({
    plantKey,
    reminderType,
    snoozeDays,
  }: {
    plantKey: string;
    reminderType: ReminderType;
    snoozeDays?: number;
  }) => {
    return api.snoozeReminder(plantKey, reminderType, snoozeDays);
  },
);

const careRemindersSlice = createSlice({
  name: 'careReminders',
  initialState,
  reducers: {
    clearCurrentProfile(state) {
      state.currentProfile = null;
    },
    clearError(state) {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      // Dashboard
      .addCase(fetchDashboard.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchDashboard.fulfilled, (state, action) => {
        state.loading = false;
        state.dashboard = action.payload;
      })
      .addCase(fetchDashboard.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message ?? 'Failed to load care dashboard';
      })
      // Profile
      .addCase(fetchProfile.fulfilled, (state, action) => {
        state.currentProfile = action.payload;
      })
      // Confirm
      .addCase(confirmCareReminder.fulfilled, (state, action) => {
        // Remove the confirmed entry from dashboard
        state.dashboard = state.dashboard.filter(
          (e) =>
            !(
              e.plant_key === action.payload.plant_key &&
              e.reminder_type === action.payload.reminder_type
            ),
        );
      })
      // Snooze
      .addCase(snoozeCareReminder.fulfilled, (state, action) => {
        // Remove the snoozed entry from dashboard
        state.dashboard = state.dashboard.filter(
          (e) =>
            !(
              e.plant_key === action.payload.plant_key &&
              e.reminder_type === action.payload.reminder_type
            ),
        );
      });
  },
});

export const { clearCurrentProfile, clearError } = careRemindersSlice.actions;
export default careRemindersSlice.reducer;
