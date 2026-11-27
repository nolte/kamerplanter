import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';
import type { PlantInstance } from '@/api/types';
import { setActiveTenantSlug } from '@/api/client';

// The detail page reads its target key from the route via useParams.
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom');
  return {
    ...actual,
    useParams: () => ({ key: 'pi-1' }),
  };
});

// Stub the interactive dialogs the page mounts; none matter for the header.
vi.mock('@/pages/pflege/components/CareConfirmDialog', () => ({ default: () => null }));
vi.mock('@/pages/pflege/components/CareProfileEditDialog', () => ({ default: () => null }));
vi.mock('@/pages/giessprotokoll/WateringLogCreateDialog', () => ({ default: () => null }));
vi.mock('@/pages/duengung/NutrientPlanAssignDialog', () => ({ default: () => null }));
vi.mock('@/pages/pflanzen/PhaseTransitionDialog', () => ({ default: () => null }));
// The real dialog is tested on its own (TerminationDialog.test.tsx). Here a stub stays rendered after `open` turns
// false - the real one is still on screen while it animates out - so the test can confirm a second time the way a
// double click during the exit animation does, and read the loading flag the page hands it. No timing involved.
vi.mock('@/pages/pflanzen/TerminationDialog', () => ({
  default: ({ loading, onConfirm }: { loading: boolean; onConfirm: (body: object) => void }) => (
    <button
      type="button"
      data-testid="stub-termination-confirm"
      data-loading={String(loading)}
      onClick={() => onConfirm({ termination_type: 'died', termination_cause: 'frost' })}
    >
      confirm
    </button>
  ),
}));
vi.mock('@/pages/pflanzen/PlantTagDialog', () => ({ default: () => null }));
vi.mock('@/components/print/PlantLabelDialog', () => ({ PlantLabelDialog: () => null }));
vi.mock('@/components/pests/PestScanButton', () => ({ default: () => null }));
vi.mock('@/pages/aufgaben/TaskCreateDialog', () => ({ default: () => null }));

import PlantInstanceDetailPage from '@/pages/pflanzen/PlantInstanceDetailPage';
import { renderWithProviders } from '../helpers';
import { server } from '../mocks/server';

function makePlant(): PlantInstance {
  return {
    key: 'pi-1',
    instance_id: 'BASIL-0001',
    species_key: 'sp-missing',
    cultivar_key: null,
    site_key: null,
    location_key: null,
    slot_key: null,
    substrate_batch_key: null,
    substrate_key: null,
    plant_name: 'Basil',
    planted_on: '2024-06-01',
    removed_on: null,
    termination_type: null,
    termination_cause: null,
    current_phase: 'vegetative',
    current_phase_key: null,
    current_phase_started_at: null,
    container_volume_liters: null,
    substrate_type_override: null,
    species: null,
    cultivar: null,
    mother_key: null,
    created_at: '2024-06-01T00:00:00Z',
    updated_at: null,
  };
}

describe('PlantInstanceDetailPage — removing a plant (#2888 F-19)', () => {
  beforeEach(async () => {
    await i18n.changeLanguage('de');
    setActiveTenantSlug('test-tenant');
  });

  it('sends one remove even if the confirm is clicked again after it succeeded', async () => {
    const plant = makePlant();
    let posts = 0;
    server.use(
      http.get('/api/v1/t/:tenant/plant-instances/:key', () => HttpResponse.json(plant)),
      http.get('/api/v1/t/:tenant/tasks/plants/:plantKey', () => HttpResponse.json([])),
      http.get('/api/v1/t/:tenant/tasks', () => HttpResponse.json([])),
      http.post('/api/v1/t/:tenant/plant-instances/:key/remove', () => {
        posts += 1;
        return HttpResponse.json({ ...plant, removed_on: '2026-11-27', termination_type: 'died', termination_cause: 'frost' });
      }),
    );
    const user = userEvent.setup();
    renderWithProviders(<PlantInstanceDetailPage />, { route: '/pflanzen/plant-instances/pi-1' });

    await user.click(await screen.findByTestId('remove-button', {}, { timeout: 5000 }));
    const confirm = screen.getByTestId('stub-termination-confirm');
    expect(confirm.dataset.loading).toBe('false');
    await user.click(confirm);
    await waitFor(() => expect(posts).toBe(1));
    // After the success the confirm stays blocked while the dialog is still on screen …
    await waitFor(() => expect(screen.getByTestId('stub-termination-confirm').dataset.loading).toBe('true'));
    // … and a second confirm sends nothing.
    await user.click(screen.getByTestId('stub-termination-confirm'));
    await new Promise((resolve) => setTimeout(resolve, 0));
    expect(posts).toBe(1);
  });
});
