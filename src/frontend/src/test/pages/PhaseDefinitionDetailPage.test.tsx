import { cleanup, screen, waitFor, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';
import { renderWithProviders } from '../helpers';
import { server } from '../mocks/server';
import type {
  PhaseDefinition,
  PhaseSequence,
  PlantInstanceInPhase,
  PlantInstancesInPhase,
  PhaseDefinitionSpecies,
} from '@/api/types';

const mockNavigate = vi.fn();
vi.mock('react-router-dom', async (orig) => {
  const actual = await orig<typeof import('react-router-dom')>();
  return { ...actual, useParams: () => ({ key: 'def-1' }), useNavigate: () => mockNavigate };
});

import PhaseDefinitionDetailPage from '@/pages/phasen/PhaseDefinitionDetailPage';

const DEF_URL = '/api/v1/phase-definitions/:key';
const SEQ_URL = '/api/v1/phase-definitions/:key/sequences';
const PLANTS_URL = '/api/v1/t/:tenant/plant-instances/by-phase-definition/:key';
const SPECIES_URL = '/api/v1/phase-definitions/:key/species';

function makeDefinition(overrides: Partial<PhaseDefinition> = {}): PhaseDefinition {
  return {
    key: 'def-1',
    name: 'vegetative',
    display_name: 'Vegetative',
    display_name_de: 'Vegetativ',
    description: 'Vegetative growth phase.',
    description_de: 'Vegetative Wachstumsphase.',
    typical_duration_days: 28,
    stress_tolerance: 'medium',
    watering_interval_days: 3,
    illustration: '',
    tags: ['indoor'],
    is_system: false,
    usage_count: 0,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: null,
    ...overrides,
  };
}

function makeSequence(overrides: Partial<PhaseSequence> = {}): PhaseSequence {
  return {
    key: 'seq-1',
    name: 'tomato-cycle',
    display_name: 'Tomato Cycle',
    display_name_de: 'Tomaten-Zyklus',
    description: '',
    description_de: '',
    species_key: 'sp-1',
    cycle_type: 'annual',
    is_repeating: true,
    cycle_restart_entry_order: null,
    typical_lifespan_years: null,
    dormancy_required: false,
    vernalization_required: false,
    vernalization_min_days: null,
    photoperiod_type: 'day_neutral',
    critical_day_length_hours: null,
    is_system: false,
    tags: [],
    entries: [],
    created_at: '2024-01-01T00:00:00Z',
    updated_at: null,
    ...overrides,
  };
}

function makePlantInstanceInPhase(overrides: Partial<PlantInstanceInPhase> = {}): PlantInstanceInPhase {
  return {
    key: 'pi-1',
    instance_id: 'PLANT-001',
    plant_name: 'Tomato #1',
    species_key: 'sp-1',
    species_scientific_name: 'Solanum lycopersicum',
    species_common_names: ['Tomate', 'Tomato'],
    location_key: 'loc-1',
    location_name: 'Greenhouse A',
    slot_key: 'slot-1',
    slot_label: 'Row 1, Pos 3',
    current_phase_key: 'def-1',
    current_phase_started_at: '2024-01-10T12:00:00Z',
    ...overrides,
  };
}

function makePhaseDefinitionSpecies(overrides: Partial<PhaseDefinitionSpecies> = {}): PhaseDefinitionSpecies {
  return {
    key: 'sp-1',
    scientific_name: 'Solanum lycopersicum',
    common_names: ['Tomate', 'Tomato'],
    typical_duration_days: 28,
    illustration: 'phases/vegetative.svg',
    ...overrides,
  };
}

function useDefinition(
  def: PhaseDefinition,
  sequences: PhaseSequence[] = [],
  plants: PlantInstancesInPhase = { total: 0, items: [] },
  species: PhaseDefinitionSpecies[] = []
) {
  server.use(
    http.get(DEF_URL, () => HttpResponse.json(def)),
    http.get(SEQ_URL, () => HttpResponse.json(sequences)),
    http.get(PLANTS_URL, () => HttpResponse.json(plants)),
    http.get(SPECIES_URL, () => HttpResponse.json(species)),
  );
}

describe('PhaseDefinitionDetailPage', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
    mockNavigate.mockClear();
  });

  afterEach(() => {
    // Unmount before resetting the language: the file's afterEach runs before
    // testing-library's auto-cleanup (LIFO), so an i18n reset here would
    // otherwise re-render every still-mounted useTranslation() consumer
    // outside act(). Unmounting first makes the reset touch nothing.
    cleanup();
    i18n.changeLanguage('en');
  });

  it('renders the loaded definition detail', async () => {
    useDefinition(makeDefinition());
    renderWithProviders(<PhaseDefinitionDetailPage />, {
      route: '/phasen/definitionen/def-1',
    });

    expect(await screen.findByTestId('phase-definition-detail-page')).toBeInTheDocument();
    expect(screen.getByTestId('delete-definition-button')).toBeInTheDocument();
  });

  it('renders the sequences-using-definition table and its properties (EN, no watering, no tags)', async () => {
    await i18n.changeLanguage('en');
    useDefinition(
      makeDefinition({
        watering_interval_days: null,
        tags: [],
        illustration: 'phases/vegetative.svg',
      }),
      [makeSequence()],
    );
    renderWithProviders(<PhaseDefinitionDetailPage />, {
      route: '/phasen/definitionen/def-1',
    });

    expect(await screen.findByTestId('sequence-row-seq-1')).toBeInTheDocument();
    // Sequence display name (EN) rendered as a link
    expect(screen.getByText('Tomato Cycle')).toBeInTheDocument();
    // repeating icon has an accessible label
    expect(
      screen.getAllByLabelText(i18n.t('pages.phaseSequences.isRepeating')).length,
    ).toBeGreaterThan(0);
    // The illustration image hides itself on load error (onError handler).
    const img = screen.getByAltText('Vegetative') as HTMLImageElement;
    fireEvent.error(img);
    expect(img.style.display).toBe('none');
  });

  it('renders even when the used-in sequences request fails', async () => {
    server.use(
      http.get(DEF_URL, () => HttpResponse.json(makeDefinition())),
      http.get(SEQ_URL, () => new HttpResponse(null, { status: 500 })),
    );
    renderWithProviders(<PhaseDefinitionDetailPage />, {
      route: '/phasen/definitionen/def-1',
    });

    expect(await screen.findByTestId('phase-definition-detail-page')).toBeInTheDocument();
    expect(
      screen.getByText(i18n.t('pages.phaseSequences.noSequencesUsingDefinition')),
    ).toBeInTheDocument();
  });

  it('renders placeholder dashes for a sparse definition and a non-repeating sequence', async () => {
    useDefinition(
      makeDefinition({
        display_name: '',
        display_name_de: '',
        description: '',
        description_de: '',
        watering_interval_days: 5,
        tags: [],
        illustration: '',
      }),
      [makeSequence({ is_repeating: false, display_name: '', display_name_de: '' })],
    );
    renderWithProviders(<PhaseDefinitionDetailPage />, {
      route: '/phasen/definitionen/def-1',
    });

    // Title + sequence link fall back to the raw name.
    expect(await screen.findByTestId('phase-definition-detail-page')).toBeInTheDocument();
    expect(screen.getAllByText('vegetative').length).toBeGreaterThan(0);
    // Non-repeating sequence renders a dash in the repeating column.
    expect(screen.getByText('tomato-cycle')).toBeInTheDocument();
    // Empty display-name / description rows render an em dash.
    expect(screen.getAllByText('—').length).toBeGreaterThan(0);
  });

  it('opens and closes the edit dialog', async () => {
    useDefinition(makeDefinition());
    const user = userEvent.setup();
    renderWithProviders(<PhaseDefinitionDetailPage />, {
      route: '/phasen/definitionen/def-1',
    });

    await user.click(await screen.findByTestId('edit-definition-button'));
    expect(await screen.findByRole('dialog')).toBeInTheDocument();
    await user.keyboard('{Escape}');
    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument());
  });

  it('closes the delete confirmation on cancel without deleting', async () => {
    let deleteCalled = false;
    useDefinition(makeDefinition());
    server.use(
      http.delete(DEF_URL, () => {
        deleteCalled = true;
        return new HttpResponse(null, { status: 204 });
      }),
    );
    const user = userEvent.setup();
    renderWithProviders(<PhaseDefinitionDetailPage />, {
      route: '/phasen/definitionen/def-1',
    });

    await user.click(await screen.findByTestId('delete-definition-button'));
    await user.click(await screen.findByTestId('confirm-dialog-cancel'));

    await waitFor(() =>
      expect(screen.queryByTestId('confirm-dialog')).not.toBeInTheDocument(),
    );
    expect(deleteCalled).toBe(false);
  });

  it('navigates back to the list via the back button', async () => {
    useDefinition(makeDefinition());
    const user = userEvent.setup();
    renderWithProviders(<PhaseDefinitionDetailPage />, {
      route: '/phasen/definitionen/def-1',
    });

    await user.click(await screen.findByTestId('back-button'));
    expect(mockNavigate).toHaveBeenCalledWith('/phasen/definitionen');
  });

  it('deletes the definition and navigates back to the list', async () => {
    let deletedKey: string | null = null;
    useDefinition(makeDefinition());
    server.use(
      http.delete(DEF_URL, ({ params }) => {
        deletedKey = params.key as string;
        return new HttpResponse(null, { status: 204 });
      }),
    );
    const user = userEvent.setup();
    renderWithProviders(<PhaseDefinitionDetailPage />, {
      route: '/phasen/definitionen/def-1',
    });

    await user.click(await screen.findByTestId('delete-definition-button'));
    await user.click(await screen.findByTestId('confirm-dialog-confirm'));

    await waitFor(() => expect(deletedKey).toBe('def-1'));
    await waitFor(() =>
      expect(mockNavigate).toHaveBeenCalledWith('/phasen/definitionen'),
    );
  });

  it('shows the pending state on the confirm dialog while the delete is in flight', async () => {
    let resolveDelete: (() => void) | null = null;
    useDefinition(makeDefinition());
    server.use(
      http.delete(
        DEF_URL,
        () =>
          new Promise<Response>((resolve) => {
            resolveDelete = () => resolve(new HttpResponse(null, { status: 204 }));
          }),
      ),
    );
    const user = userEvent.setup();
    renderWithProviders(<PhaseDefinitionDetailPage />, {
      route: '/phasen/definitionen/def-1',
    });

    await user.click(await screen.findByTestId('delete-definition-button'));
    await user.click(await screen.findByTestId('confirm-dialog-confirm'));

    await waitFor(() =>
      expect(screen.getByTestId('confirm-dialog-confirm')).toHaveAttribute('aria-busy', 'true'),
    );
    expect(screen.getByTestId('confirm-dialog-live-region')).toHaveTextContent(
      i18n.t('common.processing'),
    );

    resolveDelete!();
    await waitFor(() => expect(mockNavigate).toHaveBeenCalledWith('/phasen/definitionen'));
  });

  it('surfaces an error and stays on the page when the delete fails', async () => {
    useDefinition(makeDefinition());
    server.use(http.delete(DEF_URL, () => new HttpResponse(null, { status: 500 })));
    const user = userEvent.setup();
    renderWithProviders(<PhaseDefinitionDetailPage />, {
      route: '/phasen/definitionen/def-1',
    });

    await user.click(await screen.findByTestId('delete-definition-button'));
    await user.click(await screen.findByTestId('confirm-dialog-confirm'));

    expect(await screen.findByText(i18n.t('errors.server'))).toBeInTheDocument();
    expect(mockNavigate).not.toHaveBeenCalledWith('/phasen/definitionen');
  });

  it('disables delete for an in-use definition', async () => {
    useDefinition(makeDefinition({ usage_count: 5 }));
    renderWithProviders(<PhaseDefinitionDetailPage />, {
      route: '/phasen/definitionen/def-1',
    });

    expect(await screen.findByTestId('delete-definition-button')).toBeDisabled();
    expect(screen.getByTestId('edit-definition-button')).not.toBeDisabled();
  });

  it('disables edit and delete for a system definition', async () => {
    useDefinition(makeDefinition({ is_system: true }));
    renderWithProviders(<PhaseDefinitionDetailPage />, {
      route: '/phasen/definitionen/def-1',
    });

    expect(await screen.findByTestId('delete-definition-button')).toBeDisabled();
    expect(screen.getByTestId('edit-definition-button')).toBeDisabled();
  });

  it('renders an error state with retry when the definition cannot be loaded', async () => {
    let calls = 0;
    server.use(
      http.get(DEF_URL, () => {
        calls += 1;
        if (calls === 1) return new HttpResponse(null, { status: 404 });
        return HttpResponse.json(makeDefinition());
      }),
      http.get(SEQ_URL, () => HttpResponse.json([])),
    );
    const user = userEvent.setup();
    renderWithProviders(<PhaseDefinitionDetailPage />, {
      route: '/phasen/definitionen/def-1',
    });

    expect((await screen.findAllByText(i18n.t('errors.notFound'))).length).toBeGreaterThan(0);
    await user.click(screen.getByRole('button', { name: i18n.t('common.retry') }));
    expect(await screen.findByTestId('phase-definition-detail-page')).toBeInTheDocument();
  });

  describe('FIX-01: Plants and Species in Phase (R1–R10)', () => {
    it('renders plants in phase section with count chip and table', async () => {
      const plants: PlantInstancesInPhase = {
        total: 2,
        items: [
          makePlantInstanceInPhase({ key: 'pi-1', instance_id: 'PLANT-001', plant_name: 'Tomato #1' }),
          makePlantInstanceInPhase({ key: 'pi-2', instance_id: 'PLANT-002', plant_name: 'Tomato #2' }),
        ],
      };
      useDefinition(makeDefinition(), [], plants);

      renderWithProviders(<PhaseDefinitionDetailPage />, {
        route: '/phasen/definitionen/def-1',
      });

      expect(await screen.findByTestId('phase-definition-plants-card')).toBeInTheDocument();
      expect(screen.getByTestId('plants-in-phase-count')).toHaveTextContent('2');
      expect(screen.getByText('Tomato #1')).toBeInTheDocument();
      expect(screen.getByText('Tomato #2')).toBeInTheDocument();
    });

    it('renders empty state when no plants in phase', async () => {
      useDefinition(makeDefinition(), [], { total: 0, items: [] });

      renderWithProviders(<PhaseDefinitionDetailPage />, {
        route: '/phasen/definitionen/def-1',
      });

      expect(await screen.findByTestId('phase-definition-plants-card')).toBeInTheDocument();
      expect(screen.getByTestId('plants-in-phase-count')).toHaveTextContent('0');
      expect(screen.getByText(i18n.t('pages.phaseSequences.noPlantsInPhase'))).toBeInTheDocument();
    });

    it('navigates to plant detail when clicking a plant row (FIX-01 R2)', async () => {
      const plants: PlantInstancesInPhase = {
        total: 1,
        items: [makePlantInstanceInPhase({ key: 'pi-42' })],
      };
      useDefinition(makeDefinition(), [], plants);
      const user = userEvent.setup();

      renderWithProviders(<PhaseDefinitionDetailPage />, {
        route: '/phasen/definitionen/def-1',
      });

      const plantLink = await screen.findByTestId('plant-in-phase-row-pi-42');
      await user.click(plantLink);

      expect(mockNavigate).toHaveBeenCalledWith('/pflanzen/plant-instances/pi-42');
    });

    it('displays plant location and slot in the table', async () => {
      const plants: PlantInstancesInPhase = {
        total: 1,
        items: [
          makePlantInstanceInPhase({
            location_name: 'Greenhouse A',
            slot_label: 'Row 2',
          }),
        ],
      };
      useDefinition(makeDefinition(), [], plants);

      renderWithProviders(<PhaseDefinitionDetailPage />, {
        route: '/phasen/definitionen/def-1',
      });

      expect(await screen.findByText(/Greenhouse A · Row 2/)).toBeInTheDocument();
    });

    it('displays phase started date and calculated days in phase', async () => {
      const now = new Date();
      const tenDaysAgo = new Date(now.getTime() - 10 * 24 * 60 * 60 * 1000).toISOString();
      const plants: PlantInstancesInPhase = {
        total: 1,
        items: [
          makePlantInstanceInPhase({
            current_phase_started_at: tenDaysAgo,
          }),
        ],
      };
      useDefinition(makeDefinition(), [], plants);

      renderWithProviders(<PhaseDefinitionDetailPage />, {
        route: '/phasen/definitionen/def-1',
      });

      await screen.findByTestId('phase-definition-plants-card');
      // The page should display "10 days" (or similar i18n'd value)
      expect(screen.getByText(/10\s*(Tage|days)/i)).toBeInTheDocument();
    });

    it('renders species in phase section with table', async () => {
      const species: PhaseDefinitionSpecies[] = [
        makePhaseDefinitionSpecies({ key: 'sp-1', scientific_name: 'Solanum lycopersicum' }),
        makePhaseDefinitionSpecies({
          key: 'sp-2',
          scientific_name: 'Capsicum annuum',
          common_names: ['Pepper', 'Paprika'],
        }),
      ];
      useDefinition(makeDefinition(), [], { total: 0, items: [] }, species);

      renderWithProviders(<PhaseDefinitionDetailPage />, {
        route: '/phasen/definitionen/def-1',
      });

      expect(await screen.findByTestId('phase-definition-species-card')).toBeInTheDocument();
      expect(screen.getByText('Solanum lycopersicum')).toBeInTheDocument();
      expect(screen.getByText('Capsicum annuum')).toBeInTheDocument();
    });

    it('renders empty state when no species in phase', async () => {
      useDefinition(makeDefinition(), [], { total: 0, items: [] }, []);

      renderWithProviders(<PhaseDefinitionDetailPage />, {
        route: '/phasen/definitionen/def-1',
      });

      expect(await screen.findByTestId('phase-definition-species-card')).toBeInTheDocument();
      expect(screen.getByText(i18n.t('pages.phaseSequences.noSpeciesInPhase'))).toBeInTheDocument();
    });

    it('navigates to species detail when clicking a species row (FIX-01 R5/R9)', async () => {
      const species: PhaseDefinitionSpecies[] = [
        makePhaseDefinitionSpecies({ key: 'sp-tomato', scientific_name: 'Solanum lycopersicum' }),
      ];
      useDefinition(makeDefinition(), [], { total: 0, items: [] }, species);
      const user = userEvent.setup();

      renderWithProviders(<PhaseDefinitionDetailPage />, {
        route: '/phasen/definitionen/def-1',
      });

      const speciesLink = await screen.findByTestId('species-in-phase-row-sp-tomato');
      await user.click(speciesLink);

      expect(mockNavigate).toHaveBeenCalledWith('/stammdaten/species/sp-tomato');
    });

    it('displays typical duration for each species in the phase', async () => {
      const species: PhaseDefinitionSpecies[] = [
        makePhaseDefinitionSpecies({ key: 'sp-1', typical_duration_days: 28 }),
        makePhaseDefinitionSpecies({ key: 'sp-2', typical_duration_days: 42 }),
      ];
      useDefinition(makeDefinition(), [], { total: 0, items: [] }, species);

      renderWithProviders(<PhaseDefinitionDetailPage />, {
        route: '/phasen/definitionen/def-1',
      });

      await screen.findByTestId('phase-definition-species-card');
      // Both durations should appear in the table (use getAllByText to find all occurrences)
      const allDurations = screen.getAllByText(/\d+\s*(Tage|days)/i);
      const durationTexts = allDurations.map((el) => el.textContent);
      expect(durationTexts.join(' ')).toMatch(/28/);
      expect(durationTexts.join(' ')).toMatch(/42/);
    });

    it('gracefully handles missing plants-in-phase data (light mode scenario)', async () => {
      // When the tenant context is absent (light mode), the page should degrade gracefully
      server.use(
        http.get(DEF_URL, () => HttpResponse.json(makeDefinition())),
        http.get(SEQ_URL, () => HttpResponse.json([])),
        http.get(PLANTS_URL, () => new HttpResponse(null, { status: 403 })),
        http.get(SPECIES_URL, () => HttpResponse.json([])),
      );

      renderWithProviders(<PhaseDefinitionDetailPage />, {
        route: '/phasen/definitionen/def-1',
      });

      expect(await screen.findByTestId('phase-definition-detail-page')).toBeInTheDocument();
      expect(screen.getByTestId('plants-in-phase-count')).toHaveTextContent('0');
    });

    it('displays common names for species in the phase', async () => {
      const species: PhaseDefinitionSpecies[] = [
        makePhaseDefinitionSpecies({
          key: 'sp-1',
          common_names: ['Tomate', 'Tomato', 'Pomodoro'],
        }),
      ];
      useDefinition(makeDefinition(), [], { total: 0, items: [] }, species);

      renderWithProviders(<PhaseDefinitionDetailPage />, {
        route: '/phasen/definitionen/def-1',
      });

      await screen.findByTestId('phase-definition-species-card');
      expect(screen.getByText(/Tomate.*Tomato.*Pomodoro/)).toBeInTheDocument();
    });
  });
});
