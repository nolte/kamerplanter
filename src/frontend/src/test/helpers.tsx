import { type ReactElement } from 'react';
import { render } from '@testing-library/react';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
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

export function createTestStore() {
  return configureStore({
    reducer: {
      ui: uiReducer,
      botanicalFamilies: botanicalFamiliesReducer,
      species: speciesReducer,
      sites: sitesReducer,
      substrates: substratesReducer,
      plantInstances: plantInstancesReducer,
      userPreferences: userPreferencesReducer,
    },
  });
}

export type TestStore = ReturnType<typeof createTestStore>;

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
