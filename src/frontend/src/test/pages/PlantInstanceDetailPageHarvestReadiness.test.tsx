import { screen, waitFor } from '@testing-library/react';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';
import type { PlantInstance, ReadinessAssessment } from '@/api/types';
import { setActiveTenantSlug } from '@/api/client';

// The detail page reads its target key from the route via useParams. Provide a
// stable key without depending on a matched route path; keep the rest of
// react-router-dom real so the info tab's navigation links still render.
let currentKey = 'plant-1';
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom');
  return {
    ...actual,
    useParams: () => ({ key: currentKey }),
  };
});

// The detail page mounts several interactive dialogs unconditionally; none are
// relevant to the harvest-readiness section, so stub them out to keep the test
// focused (same set the sibling detail-page tests stub).
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

const QUERY_TIMEOUT = { timeout: 5000 } as const;

function makePlant(overrides: Partial<PlantInstance> = {}): PlantInstance {
  return {
    key: 'plant-1',
    instance_id: 'TOM-001',
    // A species key with no master-data record keeps the species card (and its
    // extra requests) out of the way; irrelevant to the readiness section.
    species_key: 'sp-missing',
    cultivar_key: null,
    site_key: null,
    location_key: null,
    slot_key: null,
    substrate_batch_key: null,
    substrate_key: null,
    plant_name: 'Tomate',
    planted_on: '2024-06-01',
    removed_on: null,
    termination_type: null,
    termination_cause: null,
    current_phase: 'flowering',
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

function seedPlant(plant: PlantInstance) {
  const handler = (pattern: string) =>
    http.get(pattern, ({ params }) =>
      params.key === plant.key
        ? HttpResponse.json(plant)
        : HttpResponse.json(
            { error_id: 'e', error_code: 'ENTITY_NOT_FOUND', message: 'Not found', details: [], timestamp: '', path: '', method: '' },
            { status: 404 },
          ),
    );
  server.use(
    handler('/api/v1/t/:tenant/plant-instances/:key'),
    handler('/api/v1/plant-instances/:key'),
  );
}

/** Records every plant key the readiness endpoint is asked about. */
function seedReadiness(
  responder: (plantKey: string) => Response,
  requested: string[] = [],
): string[] {
  server.use(
    http.get('/api/v1/t/:tenant/harvest/plants/:plantKey/readiness', ({ params }) => {
      requested.push(String(params.plantKey));
      return responder(String(params.plantKey));
    }),
  );
  return requested;
}

function makeReadiness(overrides: Partial<ReadinessAssessment> = {}): ReadinessAssessment {
  return {
    overall_score: 92,
    recommendation: 'optimal',
    estimated_days: 1,
    indicators: [
      { indicator_key: 'trichome', stage: 'peak', score: 100, reliability: 0.9, weighted_contribution: 90 },
    ],
    ...overrides,
  };
}

describe('PlantInstanceDetailPage — harvest readiness wiring (REQ-007 §3 / §6 DoD)', () => {
  beforeEach(async () => {
    await i18n.changeLanguage('de');
    currentKey = 'plant-1';
    setActiveTenantSlug('test-tenant');
  });

  it('requests the readiness assessment for the open plant and renders the card on the info tab', async () => {
    seedPlant(makePlant());
    const requested = seedReadiness(() => HttpResponse.json(makeReadiness()));

    renderWithProviders(<PlantInstanceDetailPage />);

    // The section lives on the default (info) tab — no tab switch needed, which
    // is what the E2E page object assumes.
    const card = await screen.findByTestId('harvest-readiness-card', {}, QUERY_TIMEOUT);
    expect(card).toBeInTheDocument();
    await waitFor(() => expect(requested).toEqual(['plant-1']), QUERY_TIMEOUT);
    expect(screen.getByText('92')).toBeInTheDocument();
    expect(screen.getByText(i18n.t('enums.readinessRecommendation.optimal'))).toBeInTheDocument();
  });

  it('renders the no-data explanation for a plant without ripeness observations', async () => {
    seedPlant(makePlant());
    seedReadiness(() =>
      HttpResponse.json({ overall_score: 0, recommendation: 'immature', estimated_days: null, indicators: [] }),
    );

    renderWithProviders(<PlantInstanceDetailPage />);

    expect(await screen.findByTestId('harvest-readiness-empty', {}, QUERY_TIMEOUT)).toBeInTheDocument();
    expect(screen.getByText(i18n.t('pages.harvest.readinessNoData'))).toBeInTheDocument();
    expect(screen.queryByTestId('harvest-readiness-card')).toBeNull();
  });

  it('renders the readiness error state when the assessment cannot be loaded', async () => {
    seedPlant(makePlant());
    seedReadiness(() =>
      HttpResponse.json(
        { error_id: 'e', error_code: 'INTERNAL_ERROR', message: 'internal error', details: [], timestamp: '', path: '', method: '' },
        { status: 500 },
      ),
    );

    renderWithProviders(<PlantInstanceDetailPage />);

    expect(await screen.findByTestId('harvest-readiness-error', {}, QUERY_TIMEOUT)).toBeInTheDocument();
    // The rest of the info tab must stay usable — a failing sub-request never
    // takes the whole detail page down.
    expect(screen.getByTestId('plant-info-card')).toBeInTheDocument();
    expect(screen.queryByTestId('harvest-readiness-card')).toBeNull();
  });

  it('omits the readiness section once the plant has been removed', async () => {
    seedPlant(makePlant({ removed_on: '2024-09-01', termination_type: 'harvested' }));
    const requested = seedReadiness(() => HttpResponse.json(makeReadiness()));

    renderWithProviders(<PlantInstanceDetailPage />);

    await screen.findByTestId('plant-info-card', {}, QUERY_TIMEOUT);
    expect(screen.queryByTestId('harvest-readiness-section')).toBeNull();
    expect(requested).toEqual([]);
  });
});
