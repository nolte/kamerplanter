import { screen } from '@testing-library/react';
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

describe('PlantInstanceDetailPage — header action zone (mobile overflow)', () => {
  beforeEach(async () => {
    await i18n.changeLanguage('de');
    setActiveTenantSlug('test-tenant');
  });

  it('keeps the destructive action inside a shrinkable, wrapping action group', async () => {
    seedPlant(makePlant());
    renderWithProviders(<PlantInstanceDetailPage />, { route: '/pflanzen/plant-instances/pi-1' });

    const removeButton = await screen.findByTestId('remove-button', {}, { timeout: 5000 });
    const slot = screen.getByTestId('page-title-actions');
    expect(slot).toContainElement(removeButton);

    // The group the page passes into PageTitle must stay shrinkable: with
    // `flexShrink: 0` it kept its max-content width, its own `flexWrap` never
    // took effect and "Pflanze entfernen" — a destructive action — rendered
    // fully outside a 393px viewport (UI-NFR-001 R-005/R-006).
    const group = slot.firstElementChild as HTMLElement;
    const groupStyle = window.getComputedStyle(group);
    expect(groupStyle.flexShrink).not.toBe('0');
    expect(groupStyle.flexWrap).toBe('wrap');

    // …and the slot that holds it must be shrinkable too (UI-NFR-021 R-023).
    expect(window.getComputedStyle(slot).flexShrink).not.toBe('0');
  });
});
