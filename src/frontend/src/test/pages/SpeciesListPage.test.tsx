import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';
import SpeciesListPage from '@/pages/stammdaten/SpeciesListPage';
import { renderWithProviders } from '../helpers';
import { server } from '../mocks/server';

const thisMonth = new Date().getMonth() + 1;

/** Two species spanning the various toggle-filter predicates. */
const filterableSpecies = [
  {
    key: 'sp-indoor', scientific_name: 'Ocimum basilicum', common_names: ['Basil'], family_key: 'fam-1', family_name: 'Lamiaceae',
    genus: 'Ocimum', growth_habit: 'herb', root_type: 'fibrous', hardiness_zones: [], native_habitat: '', allelopathy_score: 0, base_temp: 10,
    indoor_suitable: 'yes', container_suitable: 'yes', balcony_suitable: 'yes', greenhouse_recommended: true,
    frost_sensitivity: 'tender', allows_harvest: true, support_required: false, direct_sow_months: [thisMonth],
    created_at: '2024-01-01T00:00:00Z', updated_at: null,
  },
  {
    key: 'sp-hardy', scientific_name: 'Malus domestica', common_names: ['Apple'], family_key: 'fam-2', family_name: 'Rosaceae',
    genus: 'Malus', growth_habit: 'tree', root_type: 'taproot', hardiness_zones: [], native_habitat: '', allelopathy_score: 0, base_temp: 5,
    indoor_suitable: 'no', container_suitable: 'no', balcony_suitable: 'no', greenhouse_recommended: false,
    frost_sensitivity: 'very_hardy', allows_harvest: false, support_required: true, direct_sow_months: [],
    created_at: '2024-01-02T00:00:00Z', updated_at: null,
  },
];

function seedFilterableSpecies() {
  server.use(
    http.get('/api/v1/species', () =>
      HttpResponse.json({ items: filterableSpecies, total: filterableSpecies.length, offset: 0, limit: 1000 }),
    ),
  );
}

describe('SpeciesListPage', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
  });

  it('renders the page title', async () => {
    renderWithProviders(<SpeciesListPage />);
    await waitFor(() => {
      expect(screen.getByText('Arten')).toBeTruthy();
    });
  });

  it('loads and displays species from API', async () => {
    renderWithProviders(<SpeciesListPage />);
    await waitFor(() => {
      expect(screen.getByText('Solanum lycopersicum')).toBeTruthy();
    });
  });

  it('shows the create button', async () => {
    renderWithProviders(<SpeciesListPage />);
    await waitFor(() => {
      expect(screen.getByText('Art erstellen')).toBeTruthy();
    });
  });

  it('displays species common names', async () => {
    renderWithProviders(<SpeciesListPage />);
    await waitFor(() => {
      expect(screen.getByText('Tomato')).toBeTruthy();
    });
  });

  it('toggles the filter panel open and closed', async () => {
    const user = userEvent.setup();
    renderWithProviders(<SpeciesListPage />);

    await screen.findByText('Solanum lycopersicum');
    const toggleBtn = screen.getByTestId('toggle-filters-button');
    await user.click(toggleBtn);
    expect(await screen.findByTestId('species-filter-panel')).toBeTruthy();
  });

  it('activates a toggle filter, shows the result count, and clears it again', async () => {
    const user = userEvent.setup();
    renderWithProviders(<SpeciesListPage />);

    await screen.findByText('Solanum lycopersicum');
    await user.click(screen.getByTestId('toggle-filters-button'));

    // Activating a restrictive filter (frost-hardy) hides the single non-hardy mock species
    await user.click(await screen.findByTestId('filter-chip-frostHardy'));
    expect(await screen.findByTestId('clear-filters-button')).toBeTruthy();

    await user.click(screen.getByTestId('clear-filters-button'));
    await waitFor(() => {
      expect(screen.queryByTestId('clear-filters-button')).toBeNull();
    });
    // Species list is visible again
    expect(screen.getByText('Solanum lycopersicum')).toBeTruthy();
  });

  it('filters by growth habit via the select', async () => {
    const user = userEvent.setup();
    renderWithProviders(<SpeciesListPage />);

    await screen.findByText('Solanum lycopersicum');
    await user.click(screen.getByTestId('toggle-filters-button'));

    const habitSelect = within(await screen.findByTestId('filter-growth-habit')).getByRole('combobox');
    await user.click(habitSelect);
    // The mock tomato has growth_habit "herb" → selecting "herb" keeps it visible
    await user.click(await screen.findByRole('option', { name: i18n.t('enums.growthHabit.herb') }));

    await waitFor(() => {
      expect(screen.getByText('Solanum lycopersicum')).toBeTruthy();
    });
  });

  it('opens the create dialog when the create button is clicked', async () => {
    const user = userEvent.setup();
    renderWithProviders(<SpeciesListPage />);

    await user.click(await screen.findByTestId('create-button'));
    expect(await screen.findByTestId('species-create-dialog')).toBeTruthy();
  });

  describe('toggle-filter predicates', () => {
    beforeEach(() => {
      seedFilterableSpecies();
    });

    it('narrows the list to indoor-suitable species', async () => {
      const user = userEvent.setup();
      renderWithProviders(<SpeciesListPage />);

      await screen.findByText('Ocimum basilicum');
      await user.click(screen.getByTestId('toggle-filters-button'));
      await user.click(await screen.findByTestId('filter-chip-indoor'));

      await waitFor(() => {
        expect(screen.getByText('Ocimum basilicum')).toBeTruthy();
      });
      expect(screen.queryByText('Malus domestica')).toBeNull();
    });

    it('narrows the list to frost-hardy species', async () => {
      const user = userEvent.setup();
      renderWithProviders(<SpeciesListPage />);

      await screen.findByText('Malus domestica');
      await user.click(screen.getByTestId('toggle-filters-button'));
      await user.click(await screen.findByTestId('filter-chip-frostHardy'));

      await waitFor(() => {
        expect(screen.getByText('Malus domestica')).toBeTruthy();
      });
      expect(screen.queryByText('Ocimum basilicum')).toBeNull();
    });

    it('applies the sow-now, harvestable and support-needed predicates', async () => {
      const user = userEvent.setup();
      renderWithProviders(<SpeciesListPage />);

      await screen.findByText('Ocimum basilicum');
      await user.click(screen.getByTestId('toggle-filters-button'));

      // sowNow + harvestable both match only the basil (sown this month, harvestable)
      await user.click(await screen.findByTestId('filter-chip-sowNow'));
      await user.click(screen.getByTestId('filter-chip-harvestable'));
      await waitFor(() => {
        expect(screen.queryByText('Malus domestica')).toBeNull();
      });
      expect(screen.getByText('Ocimum basilicum')).toBeTruthy();

      // Clearing brings everything back
      await user.click(screen.getByTestId('clear-filters-button'));
      await waitFor(() => {
        expect(screen.getByText('Malus domestica')).toBeTruthy();
      });
    });

    it('filters by family via the URL query parameter', async () => {
      renderWithProviders(<SpeciesListPage />, { route: '/?family=fam-2' });

      await waitFor(() => {
        expect(screen.getByText('Malus domestica')).toBeTruthy();
      });
      expect(screen.queryByText('Ocimum basilicum')).toBeNull();
    });

    it('searches the table, exercising the column search predicates', async () => {
      const user = userEvent.setup();
      renderWithProviders(<SpeciesListPage />);

      await screen.findByText('Ocimum basilicum');
      const search = screen.getByPlaceholderText('Tabelle durchsuchen...');
      await user.type(search, 'Malus');
      // The DataTable search is debounced; waitFor's default 1000ms poll window
      // overruns under full-suite + v8-coverage load. Give it explicit headroom
      // so system load, not correctness, decides the outcome.
      await waitFor(() => {
        expect(screen.queryByText('Ocimum basilicum')).toBeNull();
      }, { timeout: 5000 });
      expect(screen.getByText('Malus domestica')).toBeTruthy();
    });

    it('sorts the table by the active-plants column', async () => {
      const user = userEvent.setup();
      renderWithProviders(<SpeciesListPage />);

      await screen.findByText('Ocimum basilicum');
      const header = screen.getByRole('button', {
        name: new RegExp(i18n.t('pages.species.activePlants')),
      });
      await user.click(header);
      expect(screen.getByText('Ocimum basilicum')).toBeTruthy();
    });

    describe('mobile viewport', () => {
      afterEach(() => {
        vi.unstubAllGlobals();
      });

      it('renders mobile species cards', async () => {
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
        renderWithProviders(<SpeciesListPage />);
        await waitFor(() => {
          expect(screen.getAllByText('Ocimum basilicum').length).toBeGreaterThan(0);
        });
      });
    });
  });
});
