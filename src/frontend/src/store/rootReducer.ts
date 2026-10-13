import { combineReducers, type UnknownAction } from '@reduxjs/toolkit';
import { clearAuth, logoutUser } from './slices/authSlice';
import activitiesReducer from './slices/activitiesSlice';
import authReducer from './slices/authSlice';
import uiReducer from './slices/uiSlice';
import botanicalFamiliesReducer from './slices/botanicalFamiliesSlice';
import speciesReducer from './slices/speciesSlice';
import sitesReducer from './slices/sitesSlice';
import substratesReducer from './slices/substratesSlice';
import plantInstancesReducer from './slices/plantInstancesSlice';
import plantingRunsReducer from './slices/plantingRunsSlice';
import successionPlansReducer from './slices/successionPlansSlice';
import tanksReducer from './slices/tanksSlice';
import fertilizersReducer from './slices/fertilizersSlice';
import nutrientPlansReducer from './slices/nutrientPlansSlice';
import feedingEventsReducer from './slices/feedingEventsSlice';
import wateringEventsReducer from './slices/wateringEventsSlice';
import ipmReducer from './slices/ipmSlice';
import harvestReducer from './slices/harvestSlice';
import postHarvestReducer from './slices/postHarvestSlice';
import tasksReducer from './slices/tasksSlice';
import tenantsReducer from './slices/tenantSlice';
import careRemindersReducer from './slices/careRemindersSlice';
import onboardingReducer from './slices/onboardingSlice';
import userPreferencesReducer from './slices/userPreferencesSlice';
import importReducer from './slices/importSlice';
import calendarReducer from './slices/calendarSlice';
import wateringLogsReducer from './slices/wateringLogsSlice';
import identificationReducer from './slices/identificationSlice';
import aiStatusReducer from './slices/aiStatusSlice';
import pestDetectionReducer from './slices/pestDetectionSlice';
import overwinteringProfilesReducer from './slices/overwinteringProfilesSlice';
import seasonReducer from './slices/seasonSlice';
import dashboardReducer from './slices/dashboardSlice';

/** Every slice the application mounts. */
export const appReducer = combineReducers({
  activities: activitiesReducer,
  auth: authReducer,
  ui: uiReducer,
  tenants: tenantsReducer,
  botanicalFamilies: botanicalFamiliesReducer,
  species: speciesReducer,
  sites: sitesReducer,
  substrates: substratesReducer,
  plantInstances: plantInstancesReducer,
  plantingRuns: plantingRunsReducer,
  successionPlans: successionPlansReducer,
  tanks: tanksReducer,
  fertilizers: fertilizersReducer,
  nutrientPlans: nutrientPlansReducer,
  feedingEvents: feedingEventsReducer,
  wateringEvents: wateringEventsReducer,
  ipm: ipmReducer,
  harvest: harvestReducer,
  postHarvest: postHarvestReducer,
  tasks: tasksReducer,
  careReminders: careRemindersReducer,
  onboarding: onboardingReducer,
  userPreferences: userPreferencesReducer,
  import: importReducer,
  calendar: calendarReducer,
  wateringLogs: wateringLogsReducer,
  identification: identificationReducer,
  aiStatus: aiStatusReducer,
  pestDetection: pestDetectionReducer,
  overwinteringProfiles: overwinteringProfilesReducer,
  season: seasonReducer,
  dashboard: dashboardReducer,
});

type AppState = ReturnType<typeof appReducer>;

/**
 * Whether *action* ends the signed-in session in this tab (#2117).
 *
 * A logout (also one whose request failed — the user asked to leave) and
 * `clearAuth`, which the 401 interceptor dispatches when the refresh token is
 * gone (logged out everywhere, session revoked, password changed). A
 * rate-limited refresh is deliberately not one: the session is intact (#1131).
 */
export function isSessionEnd(action: UnknownAction): boolean {
  return logoutUser.fulfilled.match(action) || logoutUser.rejected.match(action) || clearAuth.match(action);
}

/**
 * The application reducer with the session-end reset (#2117, MT-020).
 *
 * On a session end every slice except `auth` restarts from its initial state —
 * the data lists, the tenant list and the active tenant, the preferences, the
 * breadcrumbs (they carry entity names). `auth` handles the same action itself
 * and keeps `initialized`, so the route guards do not fall back to the bootstrap
 * skeleton. The side effects that live outside the store (the persisted tenant
 * slug, the API client's slug, the push subscription) are the listener's, in
 * `sessionListener.ts`. Before this, `createListSlice` lists kept the previous
 * account's items until the next account's own requests replaced them.
 */
export function rootReducer(state: AppState | undefined, action: UnknownAction): AppState {
  if (state !== undefined && isSessionEnd(action)) {
  return appReducer({ auth: state.auth }, action);
  }
  return appReducer(state, action);
}
