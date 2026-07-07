import { screen, waitFor } from '@testing-library/react';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';
import PlantPhaseTimeline from '@/pages/pflanzen/PlantPhaseTimeline';
import type { PhaseHistoryEntry, PlantInstance } from '@/api/types';
import { renderWithProviders } from '../helpers';
import { server } from '../mocks/server';

const plant = {
  key: 'plant-1',
  instance_id: 'TOM-001',
  species_key: 'sp-1',
  plant_name: 'Big Red',
} as unknown as PlantInstance;

const plantNoSpecies = {
  key: 'plant-2',
  instance_id: 'NIL-001',
  species_key: null,
  plant_name: 'No Species',
} as unknown as PlantInstance;

function phaseDefinition(name: string, _order: number) {
  return {
    key: `def-${name}`,
    name,
    display_name: name,
    display_name_de: name,
    description: '',
    description_de: '',
    typical_duration_days: 30,
    stress_tolerance: 'medium',
    watering_interval_days: null,
    illustration: '',
    tags: [],
    is_system: true,
    usage_count: 0,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: null,
  };
}

function sequenceEntry(name: string, order: number) {
  return {
    key: `entry-${name}`,
    phase_sequence_key: 'seq-1',
    phase_definition_key: `def-${name}`,
    sequence_order: order,
    override_duration_days: null,
    effective_duration_days: 30,
    is_terminal: name === 'harvest',
    allows_harvest: name === 'harvest',
    is_recurring: false,
    phase_definition: phaseDefinition(name, order),
    created_at: '2024-01-01T00:00:00Z',
    updated_at: null,
  };
}

const fullSequence = {
  key: 'seq-1',
  name: 'Tomato sequence',
  display_name: 'Tomato',
  display_name_de: 'Tomate',
  description: '',
  description_de: '',
  species_key: 'sp-1',
  cycle_type: 'perennial',
  is_repeating: false,
  cycle_restart_entry_order: null,
  typical_lifespan_years: 3,
  dormancy_required: false,
  vernalization_required: false,
  vernalization_min_days: null,
  photoperiod_type: 'day_neutral',
  critical_day_length_hours: null,
  is_system: true,
  tags: [],
  entries: [
    sequenceEntry('vegetative', 1),
    sequenceEntry('flowering', 2),
    sequenceEntry('harvest', 3),
  ],
  created_at: '2024-01-01T00:00:00Z',
  updated_at: null,
};

// vegetative completed, flowering current, harvest projected -> exercises all
// three status branches of buildTimeline.
const history: PhaseHistoryEntry[] = [
  {
    key: 'h-1',
    phase_name: 'vegetative',
    entered_at: '2024-01-01T00:00:00Z',
    exited_at: '2024-01-31T00:00:00Z',
    actual_duration_days: 30,
    transition_reason: 'time',
    performance_score: null,
  },
  {
    key: 'h-2',
    phase_name: 'flowering',
    entered_at: '2024-02-01T00:00:00Z',
    exited_at: null,
    actual_duration_days: null,
    transition_reason: 'time',
    performance_score: null,
  },
];

const seqUrl = '/api/v1/species/:key/phase-sequence';

describe('PlantPhaseTimeline', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
  });

  it('renders the Kami timeline from a phase sequence and reports the lifecycle', async () => {
    server.use(http.get(seqUrl, () => HttpResponse.json(fullSequence)));
    const onLifecycleLoaded = vi.fn();

    renderWithProviders(
      <PlantPhaseTimeline
        plant={plant}
        history={history}
        speciesName="Solanum lycopersicum"
        onLifecycleLoaded={onLifecycleLoaded}
      />,
    );

    // The timeline list appears once the sequence resolves.
    const list = await screen.findByRole('list', {
      name: i18n.t('pages.plantingRuns.phaseTimeline'),
    });
    expect(list).toBeTruthy();
    // Three sequence entries -> three phase list items.
    expect(screen.getAllByRole('listitem')).toHaveLength(3);

    await waitFor(() => expect(onLifecycleLoaded).toHaveBeenCalled());
    expect(onLifecycleLoaded.mock.calls[0][0]).toMatchObject({
      key: 'seq-1',
      species_key: 'sp-1',
      cycle_type: 'perennial',
      phase_sequence_key: 'seq-1',
    });
  });

  it('shows a loading spinner before the sequence resolves', async () => {
    server.use(http.get(seqUrl, () => HttpResponse.json(fullSequence)));

    renderWithProviders(<PlantPhaseTimeline plant={plant} history={[]} />);

    // Initial synchronous render is in the loading state.
    expect(screen.getByRole('progressbar')).toBeTruthy();
    await screen.findByRole('list');
    expect(screen.queryByRole('progressbar')).toBeNull();
  });

  it('renders nothing and never loads a lifecycle when the plant has no species', async () => {
    const onLifecycleLoaded = vi.fn();
    const { container } = renderWithProviders(
      <PlantPhaseTimeline
        plant={plantNoSpecies}
        history={[]}
        onLifecycleLoaded={onLifecycleLoaded}
      />,
    );

    await waitFor(() =>
      expect(screen.queryByRole('progressbar')).toBeNull(),
    );
    expect(screen.queryByRole('list')).toBeNull();
    expect(container).toBeEmptyDOMElement();
    expect(onLifecycleLoaded).not.toHaveBeenCalled();
  });

  it('falls back to the legacy lifecycle + growth-phase path when no sequence exists', async () => {
    // Sequence endpoint yields null -> component takes the LifecycleConfig branch.
    server.use(http.get(seqUrl, () => HttpResponse.json(null)));
    const onLifecycleLoaded = vi.fn();

    renderWithProviders(
      <PlantPhaseTimeline
        plant={plant}
        history={[]}
        onLifecycleLoaded={onLifecycleLoaded}
      />,
    );

    const list = await screen.findByRole('list');
    expect(list).toBeTruthy();
    // Default growth-phases handler returns vegetative + flowering.
    expect(screen.getAllByRole('listitem')).toHaveLength(2);
    await waitFor(() => expect(onLifecycleLoaded).toHaveBeenCalled());
    expect(onLifecycleLoaded.mock.calls[0][0]).toMatchObject({ key: 'lc-sp-1' });
  });

  it('falls back when the sequence exists but has no entries', async () => {
    server.use(
      http.get(seqUrl, () => HttpResponse.json({ ...fullSequence, entries: [] })),
    );

    renderWithProviders(<PlantPhaseTimeline plant={plant} history={[]} />);

    // Falls through to the legacy path (default handlers) -> 2 phases.
    await screen.findByRole('list');
    expect(screen.getAllByRole('listitem')).toHaveLength(2);
  });

  it('renders nothing when the fallback growth-phase load fails', async () => {
    server.use(
      http.get(seqUrl, () => HttpResponse.json(null)),
      http.get('/api/v1/growth-phases', () =>
        HttpResponse.json({ message: 'boom' }, { status: 500 }),
      ),
    );
    const onLifecycleLoaded = vi.fn();

    const { container } = renderWithProviders(
      <PlantPhaseTimeline
        plant={plant}
        history={[]}
        onLifecycleLoaded={onLifecycleLoaded}
      />,
    );

    // Lifecycle still loads, but with no phases the timeline collapses to null.
    await waitFor(() => expect(onLifecycleLoaded).toHaveBeenCalled());
    await waitFor(() => expect(screen.queryByRole('progressbar')).toBeNull());
    expect(screen.queryByRole('list')).toBeNull();
    expect(container).toBeEmptyDOMElement();
  });
});
