import { render, screen, waitFor } from '@testing-library/react';
import { describe, it, expect, beforeEach } from 'vitest';
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
import BotanicalFamilyListPage from '@/pages/stammdaten/BotanicalFamilyListPage';
import i18n from 'i18next';

function createTestStore() {
  return configureStore({
    reducer: {
      ui: uiReducer,
      botanicalFamilies: botanicalFamiliesReducer,
      species: speciesReducer,
      sites: sitesReducer,
      substrates: substratesReducer,
      plantInstances: plantInstancesReducer,
    },
  });
}

function renderWithProviders(ui: React.ReactElement) {
  const testStore = createTestStore();
  const router = createMemoryRouter(
    [{ path: '*', element: ui }],
    { initialEntries: ['/'] },
  );
  return render(
    <Provider store={testStore}>
      <ThemeContextProvider>
        <SnackbarProvider>
          <RouterProvider router={router} />
        </SnackbarProvider>
      </ThemeContextProvider>
    </Provider>,
  );
}

describe('BotanicalFamilyListPage', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
  });

  it('renders the page title', async () => {
    renderWithProviders(<BotanicalFamilyListPage />);
    await waitFor(() => {
      expect(screen.getByText('Botanische Familien')).toBeTruthy();
    });
  });

  it('loads and displays families from API', async () => {
    renderWithProviders(<BotanicalFamilyListPage />);
    await waitFor(() => {
      expect(screen.getByText('Solanaceae')).toBeTruthy();
      expect(screen.getByText('Fabaceae')).toBeTruthy();
    });
  });

  it('shows the create button', async () => {
    renderWithProviders(<BotanicalFamilyListPage />);
    await waitFor(() => {
      expect(screen.getByText('Familie erstellen')).toBeTruthy();
    });
  });
});
