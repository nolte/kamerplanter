/**
 * #1628 acceptance for `PlantInstanceDetailPage.tsx:234`: the edit tab's
 * substrate picker reports a failed catalogue load instead of offering an empty,
 * operable list. Harness borrowed from `PlantInstanceDetailPageHeader.test.tsx`.
 */
import { cleanup, screen, within } from '@testing-library/react';
import { afterEach, describe, it, expect, beforeEach, vi } from 'vitest';
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

// Stub the interactive dialogs the page mounts; none matter for the edit tab.
vi.mock('@/pages/pflege/components/CareConfirmDialog', () => ({ default: () => null }));
vi.mock('@/pages/pflege/components/CareProfileEditDialog', () => ({ default: () => null }));
vi.mock('@/pages/giessprotokoll/WateringLogCreateDialog', () => ({ default: () => null }));
vi.mock('@/pages/duengung/NutrientPlanAssignDialog', () => ({ default: () => null }));
vi.mock('@/pages/pflanzen/PhaseTransitionDialog', () => ({ default: () => null }));
vi.mock('@/pages/pflanzen/TerminationDialog', () => ({ default: () => null }));
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

function seedPlant(plant: PlantInstance) {
  server.use(
    http.get('/api/v1/t/:tenant/plant-instances/:key', () => HttpResponse.json(plant)),
    http.get('/api/v1/plant-instances/:key', () => HttpResponse.json(plant)),
    http.get('/api/v1/t/:tenant/tasks/plants/:plantKey', () => HttpResponse.json([])),
    http.get('/api/v1/t/:tenant/tasks', () => HttpResponse.json([])),
  );
}

describe('PlantInstanceDetailPage — failed substrate catalogue (#1628)', () => {
  beforeEach(async () => {
    await i18n.changeLanguage('de');
    setActiveTenantSlug('test-tenant');
  });

  afterEach(async () => {
    cleanup();
    await i18n.changeLanguage('en');
  });

  it('shows the failure at the substrate picker and locks the picker', async () => {
    seedPlant(makePlant());
    server.use(http.get('*/substrates', () => new HttpResponse(null, { status: 500 })));
    renderWithProviders(<PlantInstanceDetailPage />, {
      route: '/pflanzen/plant-instances/pi-1#edit',
    });

    const element = await screen.findByTestId('catalogue-load-error-substrates', {}, { timeout: 5000 });
    expect(within(element).getByRole('alert')).toBeTruthy();
    expect(
      within(screen.getByTestId('form-field-substrate_key'))
        .getByRole('combobox')
        .hasAttribute('disabled'),
    ).toBe(true);
  });
});
