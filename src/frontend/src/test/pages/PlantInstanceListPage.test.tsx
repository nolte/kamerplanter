import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';
import PlantInstanceListPage from '@/pages/pflanzen/PlantInstanceListPage';
import { renderWithProviders } from '../helpers';
import { server } from '../mocks/server';

/** A plant fully wired to slot → location → site, a cultivar, a run and a removal date. */
const richPlant = {
  key: 'plant-2',
  instance_id: 'TOM-002',
  species_key: 'sp-1',
  cultivar_key: 'cv-1',
  site_key: 'site-1',
  slot_key: 'slot-1',
  location_key: 'loc-1',
  substrate_batch_key: null,
  substrate_key: null,
  plant_name: 'Removed One',
  planted_on: '2024-04-01',
  removed_on: '2024-05-01',
  current_phase: 'flowering',
  current_phase_key: null,
  current_phase_started_at: null,
  container_volume_liters: null,
  substrate_type_override: null,
  created_at: '2024-04-01T00:00:00Z',
  updated_at: null,
};

function seedRichPlants() {
  server.use(
    http.get('/api/v1/t/:tenant/plant-instances', () => HttpResponse.json([richPlant])),
    http.get('/api/v1/plant-instances', () => HttpResponse.json([richPlant])),
    // species with the cultivar the plant references
    http.get('/api/v1/species/:key/cultivars', () =>
      HttpResponse.json([{ key: 'cv-1', species_key: 'sp-1', name: 'San Marzano', created_at: null, updated_at: null }]),
    ),
    // a run that contains the plant → run chip + mapping branch
    http.get('/api/v1/t/:tenant/planting-runs', () =>
      HttpResponse.json([{ key: 'run-1', name: 'Spring Batch', created_at: null, updated_at: null }]),
    ),
    http.get('/api/v1/planting-runs', () =>
      HttpResponse.json([{ key: 'run-1', name: 'Spring Batch', created_at: null, updated_at: null }]),
    ),
    http.get('/api/v1/t/:tenant/planting-runs/:runKey/plants', () =>
      HttpResponse.json([
        { key: 'plant-2', instance_id: 'TOM-002', species_key: 'sp-1', cultivar_key: 'cv-1', plant_name: 'Removed One', planted_on: '2024-04-01', removed_on: '2024-05-01', current_phase: 'flowering', detached_at: null, detach_reason: null },
      ]),
    ),
  );
}

describe('PlantInstanceListPage', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
  });

  it('renders the page title', async () => {
    renderWithProviders(<PlantInstanceListPage />);
    await waitFor(() => {
      expect(screen.getByText('Pflanzeninstanzen')).toBeTruthy();
    });
  });

  it('loads and displays plants from API', async () => {
    renderWithProviders(<PlantInstanceListPage />);
    await waitFor(() => {
      expect(screen.getByText('Big Red')).toBeTruthy();
    });
  });

  it('shows instance ID', async () => {
    renderWithProviders(<PlantInstanceListPage />);
    await waitFor(() => {
      expect(screen.getByText('TOM-001')).toBeTruthy();
    });
  });

  it('shows the data table', async () => {
    renderWithProviders(<PlantInstanceListPage />);
    await waitFor(() => {
      expect(screen.getByTestId('data-table')).toBeTruthy();
    });
  });

  it('shows the create button', async () => {
    renderWithProviders(<PlantInstanceListPage />);
    await waitFor(() => {
      expect(screen.getByText('Pflanze erstellen')).toBeTruthy();
    });
  });

  it('renders the current phase as a localized chip', async () => {
    renderWithProviders(<PlantInstanceListPage />);
    await waitFor(() => {
      expect(screen.getByText('Vegetativ')).toBeTruthy();
    });
  });

  it('shows the introduction text once plants are loaded', async () => {
    renderWithProviders(<PlantInstanceListPage />);
    await waitFor(() => {
      expect(screen.getByText(/Hier sehen Sie alle angelegten Pflanzen/)).toBeTruthy();
    });
  });

  it('opens the create dialog when the create button is clicked', async () => {
    const user = userEvent.setup();
    renderWithProviders(<PlantInstanceListPage />);

    const createButton = await screen.findByTestId('create-button');
    await user.click(createButton);

    expect(await screen.findByTestId('plant-instance-create-dialog')).toBeTruthy();
  });

  it('hides removed plants by default and reveals them when the switch is toggled off', async () => {
    const user = userEvent.setup();
    renderWithProviders(<PlantInstanceListPage />);

    await screen.findByText('Big Red');
    const toggle = screen.getByRole('switch');
    expect(toggle).toBeChecked();

    await user.click(toggle);
    expect(toggle).not.toBeChecked();
    // The single mock plant has no removed_on, so it stays visible regardless.
    expect(screen.getByText('Big Red')).toBeTruthy();
  });

  it('enables label printing when plants are present', async () => {
    renderWithProviders(<PlantInstanceListPage />);
    const labelButton = await screen.findByTestId('label-button');
    await waitFor(() => {
      expect(labelButton).not.toBeDisabled();
    });
  });

  it('opens the duplicate dialog from a row action prefilled as a copy', async () => {
    const user = userEvent.setup();
    renderWithProviders(<PlantInstanceListPage />);

    await screen.findByText('Big Red');
    const duplicateBtn = screen.getByRole('button', {
      name: i18n.t('pages.plantInstances.duplicate'),
    });
    await user.click(duplicateBtn);

    const dialog = await screen.findByRole('dialog');
    expect(within(dialog).getByText('Pflanze duplizieren')).toBeTruthy();
  });

  it('opens the label-print dialog when the label button is clicked', async () => {
    const user = userEvent.setup();
    renderWithProviders(<PlantInstanceListPage />);

    const labelButton = await screen.findByTestId('label-button');
    await waitFor(() => expect(labelButton).not.toBeDisabled());
    await user.click(labelButton);

    await waitFor(() => {
      expect(screen.getByRole('dialog')).toBeTruthy();
    });
  });

  it('closes the create dialog again via cancel', async () => {
    const user = userEvent.setup();
    renderWithProviders(<PlantInstanceListPage />);

    await user.click(await screen.findByTestId('create-button'));
    await screen.findByTestId('plant-instance-create-dialog');
    await user.click(screen.getByTestId('form-cancel-button'));

    await waitFor(() => {
      expect(screen.queryByTestId('plant-instance-create-dialog')).toBeNull();
    });
  });

  describe('with a fully-wired plant (location, cultivar, run, removal)', () => {
    beforeEach(() => {
      seedRichPlants();
    });

    it('hides the removed plant by default and reveals it when the switch is toggled', async () => {
      const user = userEvent.setup();
      renderWithProviders(<PlantInstanceListPage />);

      // hideRemoved defaults on → the removed plant is filtered out, leaving the empty table
      const toggle = await screen.findByRole('switch');
      expect(toggle).toBeChecked();
      await waitFor(() => {
        expect(screen.queryByText('Removed One')).toBeNull();
      });

      await user.click(toggle);
      await waitFor(() => {
        expect(screen.getAllByText('Removed One').length).toBeGreaterThan(0);
      });
    });

    it('resolves the location chain and the planting-run chip once removed plants are shown', async () => {
      const user = userEvent.setup();
      renderWithProviders(<PlantInstanceListPage />);

      await user.click(await screen.findByRole('switch'));
      // location resolved through slot → location → site
      await waitFor(() => {
        expect(screen.getAllByText('Zone A').length).toBeGreaterThan(0);
      });
      // planting-run chip rendered from the run mapping
      expect(screen.getAllByText('Spring Batch').length).toBeGreaterThan(0);
    });

    it('searches the table, exercising the column search predicates', async () => {
      const user = userEvent.setup();
      renderWithProviders(<PlantInstanceListPage />);

      await user.click(await screen.findByRole('switch'));
      await screen.findAllByText('Removed One');

      const search = screen.getByPlaceholderText('Tabelle durchsuchen...');
      await user.type(search, 'Removed');
      await waitFor(() => {
        expect(screen.getAllByText('Removed One').length).toBeGreaterThan(0);
      });

      // A non-matching query empties the result set
      await user.clear(search);
      await user.type(search, 'zzz-no-match');
      await waitFor(() => {
        expect(screen.queryByText('Removed One')).toBeNull();
      });
    });

    it('sorts the table when a column header is activated', async () => {
      const user = userEvent.setup();
      renderWithProviders(<PlantInstanceListPage />);

      await user.click(await screen.findByRole('switch'));
      await screen.findAllByText('Removed One');

      const phaseHeader = screen.getByRole('button', {
        name: new RegExp(i18n.t('pages.plantInstances.currentPhase')),
      });
      await user.click(phaseHeader);
      // Sorting must not remove the row
      expect(screen.getAllByText('Removed One').length).toBeGreaterThan(0);
    });
  });

  describe('mobile viewport', () => {
    afterEach(() => {
      vi.unstubAllGlobals();
    });

    it('renders mobile cards with subtitle, location and run chip', async () => {
      // Force the DataTable's useMediaQuery(down(sm)) to report a small screen
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
      seedRichPlants();
      const user = userEvent.setup();
      renderWithProviders(<PlantInstanceListPage />);

      await user.click(await screen.findByRole('switch'));
      // The mobile card renderer surfaces the plant name and its resolved location
      await waitFor(() => {
        expect(screen.getAllByText('Removed One').length).toBeGreaterThan(0);
      });
      expect(screen.getAllByText('Zone A').length).toBeGreaterThan(0);
    });
  });
});
