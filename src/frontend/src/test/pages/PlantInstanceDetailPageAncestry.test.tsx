import { screen, waitFor } from '@testing-library/react';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';
import type { PlantInstance } from '@/api/types';
import { setActiveTenantSlug } from '@/api/client';

// The detail page reads its target key from the route via useParams. Provide a
// stable key without depending on a matched route path; keep the rest of
// react-router-dom (RouterLink, RouterProvider) real so navigation links render.
let currentKey = 'pup-1';
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom');
  return {
    ...actual,
    useParams: () => ({ key: currentKey }),
  };
});

// The detail page mounts several interactive dialogs unconditionally (they read
// redux slices the shared test store does not preload). None are relevant to the
// clonal-continuation ancestry link (R6), so stub them to null to keep the test
// focused and independent of unrelated feature state.
vi.mock('@/pages/pflege/components/CareConfirmDialog', () => ({ default: () => null }));
vi.mock('@/pages/pflege/components/CareProfileEditDialog', () => ({ default: () => null }));
vi.mock('@/pages/giessprotokoll/WateringLogCreateDialog', () => ({ default: () => null }));
vi.mock('@/pages/duengung/NutrientPlanAssignDialog', () => ({ default: () => null }));
vi.mock('@/pages/pflanzen/PhaseTransitionDialog', () => ({ default: () => null }));
vi.mock('@/pages/pflanzen/TerminationDialog', () => ({ default: () => null }));
vi.mock('@/pages/pflanzen/PlantTagDialog', () => ({ default: () => null }));
vi.mock('@/components/print/PlantLabelDialog', () => ({ PlantLabelDialog: () => null }));
vi.mock('@/components/pests/PestScanButton', () => ({ default: () => null }));

import PlantInstanceDetailPage from '@/pages/pflanzen/PlantInstanceDetailPage';
import { renderWithProviders } from '../helpers';
import { server } from '../mocks/server';

function makePlant(overrides: Partial<PlantInstance> = {}): PlantInstance {
  return {
    key: 'pup-1',
    instance_id: 'AGA-PUP-001',
    // A species key with no master-data record: getSpecies 404s and the
    // species-dependent info card stays unrendered, keeping the test focused
    // on the ancestry link.
    species_key: 'sp-missing',
    cultivar_key: null,
    site_key: null,
    location_key: null,
    slot_key: null,
    substrate_batch_key: null,
    substrate_key: null,
    plant_name: 'Agave pup',
    planted_on: '2024-06-01',
    removed_on: null,
    termination_type: null,
    termination_cause: null,
    current_phase: 'seedling',
    current_phase_key: null,
    current_phase_started_at: null,
    container_volume_liters: null,
    substrate_type_override: null,
    species: null,
    cultivar: null,
    mother_key: null,
    created_at: '2024-06-01T00:00:00Z',
    updated_at: null,
    ...overrides,
  };
}

/** Seed the tenant-scoped instance endpoint with a pup + its mother. */
function seedInstances(pup: PlantInstance, mother?: PlantInstance) {
  const createHandler = (pattern: string) => {
    return http.get(pattern, ({ params }) => {
      if (params.key === pup.key) return HttpResponse.json(pup);
      if (mother && params.key === mother.key) return HttpResponse.json(mother);
      return HttpResponse.json(
        { error_id: 'e', error_code: 'ENTITY_NOT_FOUND', message: 'Not found', details: [], timestamp: '', path: '', method: '' },
        { status: 404 },
      );
    });
  };
  // Register handlers for both scoped and non-scoped endpoints to ensure they're
  // matched before the global defaults in handlers.ts
  server.use(
    createHandler('/api/v1/t/:tenant/plant-instances/:key'),
    createHandler('/api/v1/plant-instances/:key'),
  );
}

describe('PlantInstanceDetailPage — clonal-continuation ancestry link (D10 / R6)', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
    currentKey = 'pup-1';
    setActiveTenantSlug('test-tenant');
  });

  it('renders a "Kindel von" link to the mother, labelled with the mother instance_id', async () => {
    const mother = makePlant({ key: 'mother-1', instance_id: 'AGA-MOTHER-042', plant_name: 'Agave mother' });
    const pup = makePlant({ key: 'pup-1', mother_key: 'mother-1' });
    seedInstances(pup, mother);

    renderWithProviders(<PlantInstanceDetailPage />);

    // The ancestry label uses the detail-page namespace key.
    await screen.findByText(i18n.t('pages.plantInstances.descendedFrom'));

    const link = await screen.findByTestId('ancestry-mother-link');
    // Human-readable mother instance_id, not the raw key.
    await waitFor(() => expect(link.textContent).toContain('AGA-MOTHER-042'));
    expect(link.getAttribute('href')).toBe('/pflanzen/plant-instances/mother-1');
  });

  it('falls back to the raw mother key when the mother instance cannot be loaded', async () => {
    const pup = makePlant({ key: 'pup-1', mother_key: 'mother-gone' });
    seedInstances(pup); // no mother handler → 404

    renderWithProviders(<PlantInstanceDetailPage />);

    const link = await screen.findByTestId('ancestry-mother-link');
    expect(link.getAttribute('href')).toBe('/pflanzen/plant-instances/mother-gone');
    await waitFor(() => expect(link.textContent).toContain('mother-gone'));
  });

  it('shows no ancestry link when the plant has no mother_key', async () => {
    const pup = makePlant({ key: 'pup-1', mother_key: null });
    seedInstances(pup);

    renderWithProviders(<PlantInstanceDetailPage />);

    // Wait for the info card to render, then assert the ancestry block is absent.
    await screen.findByTestId('plant-info-card');
    expect(screen.queryByTestId('ancestry-mother')).toBeNull();
    expect(screen.queryByText(i18n.t('pages.plantInstances.descendedFrom'))).toBeNull();
  });
});
