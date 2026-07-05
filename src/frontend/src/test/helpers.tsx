import { type ReactElement } from 'react';
import { render } from '@testing-library/react';
import { Provider } from 'react-redux';
import { combineReducers, configureStore } from '@reduxjs/toolkit';
import { createMemoryRouter, RouterProvider } from 'react-router-dom';
import { SnackbarProvider } from 'notistack';
import { ThemeContextProvider } from '@/theme';
import uiReducer from '@/store/slices/uiSlice';
import botanicalFamiliesReducer from '@/store/slices/botanicalFamiliesSlice';
import speciesReducer from '@/store/slices/speciesSlice';
import sitesReducer from '@/store/slices/sitesSlice';
import substratesReducer from '@/store/slices/substratesSlice';
import plantInstancesReducer from '@/store/slices/plantInstancesSlice';
import userPreferencesReducer from '@/store/slices/userPreferencesSlice';
import authReducer from '@/store/slices/authSlice';
import identificationReducer from '@/store/slices/identificationSlice';
import pestDetectionReducer from '@/store/slices/pestDetectionSlice';
import ipmReducer from '@/store/slices/ipmSlice';
import tenantsReducer from '@/store/slices/tenantSlice';
import successionPlansReducer from '@/store/slices/successionPlansSlice';
import overwinteringProfilesReducer from '@/store/slices/overwinteringProfilesSlice';
import seasonReducer from '@/store/slices/seasonSlice';
import dashboardReducer from '@/store/slices/dashboardSlice';
import plantingRunsReducer from '@/store/slices/plantingRunsSlice';

const rootReducer = combineReducers({
  ui: uiReducer,
  botanicalFamilies: botanicalFamiliesReducer,
  species: speciesReducer,
  sites: sitesReducer,
  substrates: substratesReducer,
  plantInstances: plantInstancesReducer,
  userPreferences: userPreferencesReducer,
  auth: authReducer,
  identification: identificationReducer,
  pestDetection: pestDetectionReducer,
  ipm: ipmReducer,
  tenants: tenantsReducer,
  successionPlans: successionPlansReducer,
  overwinteringProfiles: overwinteringProfilesReducer,
  season: seasonReducer,
  dashboard: dashboardReducer,
  plantingRuns: plantingRunsReducer,
});

// Loosely-typed preloaded state: only the slices a given test cares about need
// to be supplied. configureStore fills the rest from each reducer's initial state.
type PreloadedState = Record<string, unknown>;

export function createTestStore(preloadedState?: PreloadedState) {
  return configureStore({
    reducer: rootReducer,
    preloadedState: preloadedState as never,
  });
}

export type TestStore = ReturnType<typeof createTestStore>;

type ExpertiseLevel = 'beginner' | 'intermediate' | 'expert';

/**
 * Store seeded with a loaded user-preference experience level. Components that
 * gate fields behind {@link useExpertiseLevel} (ExpertiseFieldWrapper) show the
 * intermediate/expert fields only when a preference is actually loaded.
 */
export function createStoreWithExpertise(level: ExpertiseLevel): TestStore {
  return createTestStore({
    userPreferences: {
      preferences: {
        key: 'pref-1',
        user_key: 'user-1',
        experience_level: level,
        onboarding_completed: true,
        locale: 'de',
        theme: 'light',
        watering_can_liters: 5,
        smart_home_enabled: false,
        module_visibility: {},
      },
      loading: false,
      error: null,
    },
  });
}

type ModuleVisibilityState = 'enabled' | 'disabled';

/**
 * Store seeded with a loaded experience level plus REQ-042 module-visibility
 * overrides — for components/hooks that combine both signals.
 */
export function createStoreWithModuleOverrides(
  level: ExpertiseLevel,
  overrides: Record<string, ModuleVisibilityState>,
): TestStore {
  return createTestStore({
    userPreferences: {
      preferences: {
        key: 'pref-1',
        user_key: 'user-1',
        experience_level: level,
        onboarding_completed: true,
        locale: 'de',
        theme: 'light',
        watering_can_liters: 5,
        smart_home_enabled: false,
        module_visibility: overrides,
      },
      loading: false,
      error: null,
    },
  });
}

export function renderWithProviders(
  ui: ReactElement,
  { store = createTestStore(), route = '/' }: { store?: TestStore; route?: string } = {},
) {
  const router = createMemoryRouter(
    [{ path: '*', element: ui }],
    { initialEntries: [route] },
  );
  return {
    store,
    ...render(
      <Provider store={store}>
        <ThemeContextProvider>
          <SnackbarProvider>
            <RouterProvider router={router} />
          </SnackbarProvider>
        </ThemeContextProvider>
      </Provider>,
    ),
  };
}
