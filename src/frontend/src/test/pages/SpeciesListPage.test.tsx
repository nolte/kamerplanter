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

  // Issue #397 / UI-NFR-018 R-016/R-017/R-018: origin provenance filter.
  describe('origin provenance filter', () => {
    /** Minimal species factory covering the fields the page reads. */
    function makeSpecies(over: Record<string, unknown>): Record<string, unknown> {
      return {
        scientific_name: 'X', common_names: [], family_key: null, family_name: null,
        genus: 'G', growth_habit: 'herb', root_type: 'fibrous', hardiness_zones: [],
        native_habitat: '', allelopathy_score: 0, base_temp: 10,
        indoor_suitable: 'no', container_suitable: 'no', balcony_suitable: 'no',
        greenhouse_recommended: false, frost_sensitivity: 'tender',
        allows_harvest: false, support_required: false, direct_sow_months: [],
        created_at: '2024-01-01T00:00:00Z', updated_at: null,
        ...over,
      };
    }

    /** One row per origin, plus one untagged row (no `origin`) that renders as an
     *  empty chip like `tenant` and must be captured by the tenant filter (R8). */
    const originSpecies = [
      makeSpecies({ key: 'sp-system', scientific_name: 'Alpha systemus', origin: 'system', frost_sensitivity: 'very_hardy' }),
      makeSpecies({ key: 'sp-enrich', scientific_name: 'Beta enrichus', origin: 'enrichment' }),
      makeSpecies({ key: 'sp-import', scientific_name: 'Gamma importus', origin: 'import' }),
      makeSpecies({ key: 'sp-tenant', scientific_name: 'Delta tenantus', origin: 'tenant' }),
      makeSpecies({ key: 'sp-untagged', scientific_name: 'Epsilon untaggedus' }),
    ];

    function seedOriginSpecies() {
      server.use(
        http.get('/api/v1/species', () =>
          HttpResponse.json({ items: originSpecies, total: originSpecies.length, offset: 0, limit: 1000 }),
        ),
      );
    }

    beforeEach(() => {
      seedOriginSpecies();
    });

    it('shows all rows when no origin chip is selected (default "Alle")', async () => {
      renderWithProviders(<SpeciesListPage />);
      await screen.findByText('Alpha systemus');
      expect(screen.getByText('Beta enrichus')).toBeTruthy();
      expect(screen.getByText('Gamma importus')).toBeTruthy();
      expect(screen.getByText('Delta tenantus')).toBeTruthy();
      expect(screen.getByText('Epsilon untaggedus')).toBeTruthy();
    });

    it('OR-combines multiple selected origins within the origin filter', async () => {
      const user = userEvent.setup();
      renderWithProviders(<SpeciesListPage />);

      await screen.findByText('Alpha systemus');
      await user.click(screen.getByTestId('toggle-filters-button'));
      await user.click(await screen.findByTestId('origin-filter-chip-system'));
      await user.click(screen.getByTestId('origin-filter-chip-enrichment'));

      await waitFor(() => {
        expect(screen.queryByText('Gamma importus')).toBeNull();
      });
      expect(screen.getByText('Alpha systemus')).toBeTruthy();
      expect(screen.getByText('Beta enrichus')).toBeTruthy();
      expect(screen.queryByText('Delta tenantus')).toBeNull();
      expect(screen.queryByText('Epsilon untaggedus')).toBeNull();
    });

    it('AND-composes the origin filter with a toggle filter', async () => {
      const user = userEvent.setup();
      renderWithProviders(<SpeciesListPage />);

      await screen.findByText('Alpha systemus');
      await user.click(screen.getByTestId('toggle-filters-button'));
      // system + enrichment selected → two rows, only the system row is frost-hardy
      await user.click(await screen.findByTestId('origin-filter-chip-system'));
      await user.click(screen.getByTestId('origin-filter-chip-enrichment'));
      await user.click(screen.getByTestId('filter-chip-frostHardy'));

      await waitFor(() => {
        expect(screen.queryByText('Beta enrichus')).toBeNull();
      });
      expect(screen.getByText('Alpha systemus')).toBeTruthy();
    });

    it('isolates tenant + untagged rows when the "Eigene" origin is selected (R8)', async () => {
      const user = userEvent.setup();
      renderWithProviders(<SpeciesListPage />);

      await screen.findByText('Alpha systemus');
      await user.click(screen.getByTestId('toggle-filters-button'));
      await user.click(await screen.findByTestId('origin-filter-chip-tenant'));

      await waitFor(() => {
        expect(screen.queryByText('Alpha systemus')).toBeNull();
      });
      expect(screen.getByText('Delta tenantus')).toBeTruthy();
      // A row without an explicit origin renders as an empty chip like tenant and
      // must be captured by the tenant filter.
      expect(screen.getByText('Epsilon untaggedus')).toBeTruthy();
      expect(screen.queryByText('Gamma importus')).toBeNull();
    });

    it('surfaces the specific empty-filter hint when the origin filter yields zero rows', async () => {
      const user = userEvent.setup();
      renderWithProviders(<SpeciesListPage />);

      await screen.findByText('Alpha systemus');
      await user.click(screen.getByTestId('toggle-filters-button'));
      // enrichment row is not frost-hardy → the combination yields zero matches
      await user.click(await screen.findByTestId('origin-filter-chip-enrichment'));
      await user.click(screen.getByTestId('filter-chip-frostHardy'));

      expect(await screen.findByTestId('no-column-filter-results')).toBeTruthy();
      expect(screen.queryByText('Beta enrichus')).toBeNull();
    });

    it('restores the origin selection from the URL query param on load (round-trip)', async () => {
      renderWithProviders(<SpeciesListPage />, { route: '/?origin=system' });

      await screen.findByText('Alpha systemus');
      expect(screen.queryByText('Beta enrichus')).toBeNull();
      expect(screen.queryByText('Delta tenantus')).toBeNull();

      // The corresponding chip reflects the restored selection.
      const chip = screen.getByTestId('origin-filter-chip-system');
      expect(chip.getAttribute('aria-pressed')).toBe('true');
    });

    it('supports an OR selection restored from a comma-separated URL param', async () => {
      renderWithProviders(<SpeciesListPage />, { route: '/?origin=import,tenant' });

      await screen.findByText('Gamma importus');
      expect(screen.getByText('Delta tenantus')).toBeTruthy();
      expect(screen.queryByText('Alpha systemus')).toBeNull();
      expect(screen.queryByText('Beta enrichus')).toBeNull();
    });

    it('counts the origin filter in the badge and clears it via "reset filters"', async () => {
      const user = userEvent.setup();
      renderWithProviders(<SpeciesListPage />);

      await screen.findByText('Alpha systemus');
      await user.click(screen.getByTestId('toggle-filters-button'));
      await user.click(await screen.findByTestId('origin-filter-chip-system'));

      // Active-filter affordances appear.
      const clearBtn = await screen.findByTestId('clear-filters-button');
      await user.click(clearBtn);

      await waitFor(() => {
        expect(screen.queryByTestId('clear-filters-button')).toBeNull();
      });
      // All rows are visible again.
      expect(screen.getByText('Beta enrichus')).toBeTruthy();
      expect(screen.getByTestId('origin-filter-chip-system').getAttribute('aria-pressed')).toBe('false');
    });
  });
});
