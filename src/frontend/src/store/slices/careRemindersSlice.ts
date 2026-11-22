import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import type { CareDashboardEntry, CareProfile, ReminderType } from '@/api/types';
import type { ConfirmReminderOptions } from '@/api/endpoints/careReminders';
import * as api from '@/api/endpoints/careReminders';
import { errorKey } from '@/api/errors';

interface CareRemindersState {
  dashboard: CareDashboardEntry[];
  currentProfile: CareProfile | null;
  loading: boolean;
  /**
   * True once a dashboard query has settled at least once, either way.
   *
   * A consumer that gates its first paint on "everything has answered" cannot
   * express that through `loading` alone: `loading === false` is also the state
   * before anything was ever asked, and before the entries that decide the
   * layout exist. Hosts of the dashboard reload it on interaction, so the
   * distinction is the difference between a first paint and a refetch.
   */
  dashboardLoaded: boolean;
  error: string | null;
  /**
   * `requestId` of the profile read whose answer the slice still accepts (#3065).
   *
   * `currentProfile` is shared by every host that edits a profile. Without the
   * marker, opening the editor for plant B rendered whatever profile was in the
   * store — plant A's — and a late answer for A could still overwrite B's. Hosts
   * render the form only when `currentProfile.plant_key` is the plant they asked
   * for; the slice discards every answer but the latest request's.
   *
   * The request, not the plant: closing and reopening the editor for the *same*
   * plant leaves two reads for it in flight, and the first one landing after
   * the second would hand the form a new profile object and re-seed it over the
   * user's edits.
   */
  profileRequestId: string | null;
  /** Localised error key of the last failed profile read, `null` otherwise. */
  profileError: string | null;
}

const initialState: CareRemindersState = {
  dashboard: [],
  currentProfile: null,
  loading: false,
  dashboardLoaded: false,
  error: null,
  profileRequestId: null,
  profileError: null,
};

export const fetchDashboard = createAsyncThunk(
  'careReminders/fetchDashboard',
  async (hemisphere?: string) => {
    return api.getDashboard(hemisphere);
  },
);

export const fetchProfile = createAsyncThunk(
  'careReminders/fetchProfile',
  async ({ plantKey }: { plantKey: string }) => {
    return api.getOrCreateProfile(plantKey);
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
      state.profileError = null;
      // Drop the request marker so an answer arriving after the host closed its
      // editor can no longer write into the shared slice.
      state.profileRequestId = null;
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
        state.dashboardLoaded = true;
        state.dashboard = action.payload;
      })
      .addCase(fetchDashboard.rejected, (state, action) => {
        state.loading = false;
        state.dashboardLoaded = true;
        state.error = errorKey(action.error, 'errors.loadFailed');
      })
      // Profile
      .addCase(fetchProfile.pending, (state, action) => {
        state.profileRequestId = action.meta.requestId;
        // Never keep another plant's profile on screen while this one loads.
        state.currentProfile = null;
        state.profileError = null;
      })
      .addCase(fetchProfile.fulfilled, (state, action) => {
        // Discard every answer but the latest request's.
        if (action.meta.requestId !== state.profileRequestId) return;
        state.currentProfile = action.payload;
      })
      .addCase(fetchProfile.rejected, (state, action) => {
        if (action.meta.requestId !== state.profileRequestId) return;
        state.profileError = errorKey(action.error, 'errors.loadFailed');
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
