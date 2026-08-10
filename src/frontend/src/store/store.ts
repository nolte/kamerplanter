import { configureStore } from '@reduxjs/toolkit';
import { setActiveTenantRejectedHandler } from '../api/client';
import { clearActiveTenant, loadMyTenants } from './slices/tenantSlice';
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

export const store = configureStore({
  reducer: {
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
  },
});

/**
 * Stale-slug recovery, wired where the store exists (#1091 A-4).
 *
 * The API client detects that the backend refuses the persisted active tenant
 * (a membership was revoked, the organisation was deleted) but cannot repair it
 * on its own: it owns no state beyond the in-memory slug, and it must not import
 * the store — every slice imports the client, so the reverse edge would be a
 * cycle. This is the composition root, the one place that legitimately knows
 * both, so the behaviour is registered here.
 *
 * Clearing first and reloading second matters: `loadMyTenants.fulfilled` re-picks
 * an existing tenant and re-persists `kp_active_tenant_slug`, so the user lands
 * on a working scope instead of a permanently 403-ing catalogue. The returned
 * dispatch promise is what the client uses to collapse a page-load's worth of
 * simultaneous 403s into a single reload.
 *
 * Not a cache invalidation: switching tenants deliberately goes through
 * `TenantSwitcher`, which does a full `window.location.reload()`.
 */
setActiveTenantRejectedHandler(() => {
  store.dispatch(clearActiveTenant());
  return store.dispatch(loadMyTenants());
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
