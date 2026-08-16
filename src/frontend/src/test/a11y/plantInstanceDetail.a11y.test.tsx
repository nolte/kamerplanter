/**
 * Axe pass for `PlantInstanceDetailPage` (#1094).
 *
 * Its own file rather than a case in `topPages.a11y.test.tsx`, because the page
 * reads its target from the route and the `react-router-dom` mock that supplies
 * it is module-scoped — folding it in would hand every other page in that file
 * a `useParams` it did not ask for.
 *
 * This page was deliberately left out of the first backfill, and the reason is
 * the point of this file. It *was* in, and it passed: axe found nothing wrong
 * with the 15 elements of its loading skeleton, because the default MSW handlers
 * do not answer the per-plant requests it makes. A green a11y result over a
 * spinner is worse than no result, since it reads as coverage.
 *
 * So the fixture below is the substance of this test, not scaffolding around it:
 * the page only becomes an accessibility subject once it has rendered a plant.
 * The `minElements` floor is what enforces that — if the seeding ever stops
 * working, this file fails instead of quietly certifying a skeleton again.
 */

import i18n from 'i18next';
import { http, HttpResponse } from 'msw';
import { describe, it, beforeEach, vi } from 'vitest';

import type { PlantInstance } from '@/api/types';

// The page reads its target key from the route.
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom');
  return { ...actual, useParams: () => ({ key: 'pi-a11y' }) };
});

// The interactive dialogs the page mounts are scanned separately in
// dialogs.a11y.test.tsx, where they are actually open. Mounted-but-closed they
// contribute nothing to scan and pull in heavy trees.
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
import { expectNoA11yViolations } from './expectNoA11yViolations';

/** Well above the 15-element skeleton this page renders unseeded. */
const PAGE_MIN_ELEMENTS = 40;

function makePlant(): PlantInstance {
  return {
    key: 'pi-a11y',
    instance_id: 'A11Y-0001',
    species_key: 'sp-a11y',
    cultivar_key: null,
    site_key: null,
    location_key: null,
    slot_key: null,
    substrate_batch_key: null,
    substrate_key: null,
    plant_name: 'Basilikum',
    planted_on: '2026-06-01',
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
    created_at: '2026-06-01T00:00:00Z',
    updated_at: null,
  };
}

describe('Accessibility — PlantInstanceDetailPage', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
    const plant = makePlant();
    server.use(
      http.get('/api/v1/t/:tenant/plant-instances/:key', () => HttpResponse.json(plant)),
      http.get('/api/v1/plant-instances/:key', () => HttpResponse.json(plant)),
      http.get('/api/v1/t/:tenant/tasks/plants/:plantKey', () => HttpResponse.json([])),
      http.get('/api/v1/t/:tenant/tasks', () => HttpResponse.json([])),
    );
  });

  it('has no critical a11y violations once a plant has rendered', async () => {
    const { container } = renderWithProviders(<PlantInstanceDetailPage />);

    await expectNoA11yViolations(container, { minElements: PAGE_MIN_ELEMENTS });
  });
});
