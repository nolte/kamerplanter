import { configureStore } from '@reduxjs/toolkit';
import activitiesReducer from './slices/activitiesSlice';
import authReducer from './slices/authSlice';
import uiReducer from './slices/uiSlice';
import botanicalFamiliesReducer from './slices/botanicalFamiliesSlice';
import speciesReducer from './slices/speciesSlice';
import sitesReducer from './slices/sitesSlice';
import substratesReducer from './slices/substratesSlice';
import plantInstancesReducer from './slices/plantInstancesSlice';
import plantingRunsReducer from './slices/plantingRunsSlice';
import tanksReducer from './slices/tanksSlice';
import fertilizersReducer from './slices/fertilizersSlice';
import nutrientPlansReducer from './slices/nutrientPlansSlice';
import feedingEventsReducer from './slices/feedingEventsSlice';
import wateringEventsReducer from './slices/wateringEventsSlice';
import ipmReducer from './slices/ipmSlice';
import harvestReducer from './slices/harvestSlice';
import tasksReducer from './slices/tasksSlice';
import tenantsReducer from './slices/tenantSlice';
import careRemindersReducer from './slices/careRemindersSlice';
import onboardingReducer from './slices/onboardingSlice';
import userPreferencesReducer from './slices/userPreferencesSlice';
import importReducer from './slices/importSlice';
import calendarReducer from './slices/calendarSlice';
import wateringLogsReducer from './slices/wateringLogsSlice';

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
    tanks: tanksReducer,
    fertilizers: fertilizersReducer,
    nutrientPlans: nutrientPlansReducer,
    feedingEvents: feedingEventsReducer,
    wateringEvents: wateringEventsReducer,
    ipm: ipmReducer,
    harvest: harvestReducer,
    tasks: tasksReducer,
    careReminders: careRemindersReducer,
    onboarding: onboardingReducer,
    userPreferences: userPreferencesReducer,
    import: importReducer,
    calendar: calendarReducer,
    wateringLogs: wateringLogsReducer,
  },
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
