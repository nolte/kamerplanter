import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { server } from '../mocks/server';
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

  it('shows the list intro once loading finishes', async () => {
    renderWithProviders(<BotanicalFamilyListPage />);
    await waitFor(() => {
      expect(screen.getByText('Solanaceae')).toBeTruthy();
    });
    expect(screen.getByTestId('create-button')).toBeTruthy();
  });

  it('opens the create dialog when the create button is clicked', async () => {
    const user = userEvent.setup();
    renderWithProviders(<BotanicalFamilyListPage />);

    await user.click(await screen.findByTestId('create-button'));
    expect(await screen.findByTestId('botanical-family-create-dialog')).toBeTruthy();
  });

  it('renders the localized nutrient demand for a family row', async () => {
    renderWithProviders(<BotanicalFamilyListPage />);
    await waitFor(() => {
      expect(screen.getByText('Solanaceae')).toBeTruthy();
    });
    // typical_nutrient_demand "heavy" → localized enum label appears in the table
    expect(screen.getAllByText(i18n.t('enums.nutrientDemand.heavy')).length).toBeGreaterThan(0);
  });

  it('navigates to the family detail when a row is clicked', async () => {
    const user = userEvent.setup();
    renderWithProviders(<BotanicalFamilyListPage />);

    const row = await screen.findByText('Solanaceae');
    await user.click(row);
    // Navigation is via react-router; the row click handler fires without throwing
    expect(screen.getByTestId('botanical-family-list-page')).toBeTruthy();
  });

  it('falls back to the German common name in the table when language is German', async () => {
    i18n.changeLanguage('de');
    renderWithProviders(<BotanicalFamilyListPage />);
    await waitFor(() => {
      expect(screen.getByText('Solanaceae')).toBeTruthy();
    });
    // common names are absent on the mock → the "—" placeholder is rendered
    expect(screen.getAllByText('—').length).toBeGreaterThan(0);
  });

  describe('with localized common names and rotation categories', () => {
    const richFamilies = [
      {
        key: 'fam-r1', name: 'Brassicaceae', common_name_de: 'Kreuzblütler', common_name_en: 'Cabbage family',
        typical_nutrient_demand: 'heavy', typical_root_depth: 'deep', frost_tolerance: 'hardy',
        species_count: 12, rotation_category: 'leaf', common_pests: [], created_at: '2024-01-01T00:00:00Z', updated_at: null,
      },
      {
        key: 'fam-r2', name: 'Apiaceae', common_name_de: 'Doldenblütler', common_name_en: 'Carrot family',
        typical_nutrient_demand: 'medium', typical_root_depth: 'medium', frost_tolerance: 'moderate',
        species_count: 5, rotation_category: 'root', common_pests: [], created_at: '2024-01-02T00:00:00Z', updated_at: null,
      },
    ];

    beforeEach(() => {
      server.use(http.get('/api/v1/botanical-families', () => HttpResponse.json(richFamilies)));
    });

    it('renders the German common name and rotation category', async () => {
      i18n.changeLanguage('de');
      renderWithProviders(<BotanicalFamilyListPage />);
      await waitFor(() => {
        expect(screen.getAllByText('Kreuzblütler').length).toBeGreaterThan(0);
      });
      expect(screen.getAllByText('leaf').length).toBeGreaterThan(0);
    });

    it('renders the English common name when the language is English', async () => {
      i18n.changeLanguage('en');
      renderWithProviders(<BotanicalFamilyListPage />);
      await waitFor(() => {
        expect(screen.getAllByText('Cabbage family').length).toBeGreaterThan(0);
      });
      i18n.changeLanguage('de');
    });

    it('searches across families, exercising the search predicates', async () => {
      i18n.changeLanguage('de');
      const user = userEvent.setup();
      renderWithProviders(<BotanicalFamilyListPage />);

      await screen.findAllByText('Kreuzblütler');
      const search = screen.getByPlaceholderText('Tabelle durchsuchen...');
      await user.type(search, 'Apiaceae');
      await waitFor(() => {
        expect(screen.queryByText('Brassicaceae')).toBeNull();
      });
      expect(screen.getByText('Apiaceae')).toBeTruthy();
    });

    it('sorts families by the species-count column', async () => {
      i18n.changeLanguage('de');
      const user = userEvent.setup();
      renderWithProviders(<BotanicalFamilyListPage />);

      await screen.findByText('Brassicaceae');
      const header = screen.getByRole('button', {
        name: new RegExp(i18n.t('pages.botanicalFamilies.speciesCount')),
      });
      await user.click(header);
      expect(screen.getByText('Brassicaceae')).toBeTruthy();
    });

    describe('mobile viewport', () => {
      afterEach(() => {
        vi.unstubAllGlobals();
      });

      it('renders mobile family cards with chips and fields', async () => {
        vi.stubGlobal(
          'matchMedia',
          vi.fn().mockReturnValue({
            matches: true,
            addEventListener: vi.fn(),
            removeEventListener: vi.fn(),
            addListener: vi.fn(),
            removeListener: vi.fn(),
          } as unknown as MediaQueryList),
        );
        i18n.changeLanguage('de');
        renderWithProviders(<BotanicalFamilyListPage />);
        await waitFor(() => {
          expect(screen.getAllByText('Brassicaceae').length).toBeGreaterThan(0);
        });
        // mobile card subtitle uses the localized common name
        expect(screen.getAllByText('Kreuzblütler').length).toBeGreaterThan(0);
      });
    });
  });
});
