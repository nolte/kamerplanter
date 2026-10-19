import { cleanup, fireEvent, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { expectNoA11yViolations } from '@/test/a11y/expectNoA11yViolations';
import { renderWithProviders } from '@/test/helpers';
import PlantInfoSheet from './PlantInfoSheet';
import type { PlantStateView } from './usePlantStates';

/** On touch the plant info is a bottom sheet with the cover photo and a way to the details (GP-UX-040). */
const view = {
  plant_key: 'pl_1',
  slot_id: 'A1',
  instance_id: 'TOM-1',
  species_key: 'sp',
  species_name: 'Tomato',
  scientific_name: 'Solanum lycopersicum',
  planted_on: '2026-04-01',
  lifecycle: 'active',
  phase: { key: 'ph', name: 'Flowering', elapsed_d: 21, typical_d: 60, fraction: 0.35 },
  last_care: {},
  attention: [{ reason: 'overdue', count: 2 }],
  harvest: { ready: false },
  cover_photo_ref: 'att1',
  inputs: { open_tasks: [], open_findings: 0, frost_risk: false, harvest_batches: 0, phase: null },
  visual: {
    lifecycle: 'active',
    phase_key: 'ph',
    phase_progress: { elapsed_d: 21, typical_d: 60, fraction: 0.35, next_phase_eta: null },
    attention: [{ reason: 'overdue', count: 2 }],
    harvest_ready: false,
    harvest_ready_from: null,
  },
} as unknown as PlantStateView;

afterEach(() => cleanup());

describe('PlantInfoSheet', () => {
  it('shows the facts, the details link and closes', async () => {
    const onClose = vi.fn();
    renderWithProviders(<PlantInfoSheet view={view} onClose={onClose} />);

    const sheet = await screen.findByRole('region', { name: 'Plant Tomato' });
    expect(sheet).toHaveTextContent('Tomato');
    expect(sheet).toHaveTextContent('2 tasks overdue');
    expect(screen.getByRole('link', { name: 'Details' })).toHaveAttribute('href', '/pflanzen/plant-instances/pl_1');

    fireEvent.click(screen.getByRole('button', { name: 'Close' }));
    expect(onClose).toHaveBeenCalled();
  });

  it('renders nothing without a plant', () => {
    renderWithProviders(<PlantInfoSheet view={null} onClose={() => undefined} />);
    expect(screen.queryByRole('region')).toBeNull();
  });

  it('has no accessibility violations', async () => {
    const { baseElement } = renderWithProviders(<PlantInfoSheet view={view} onClose={() => undefined} />);
    await screen.findByRole('region', { name: 'Plant Tomato' });
    await expectNoA11yViolations(baseElement);
  });
});
