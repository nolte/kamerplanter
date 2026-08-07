import { screen, waitFor } from '@testing-library/react';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';
import type { PlantInstance, ReadinessAssessment, Species } from '@/api/types';
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

/** Type-complete Species mock for the species-card / harvestability paths. */
function makeSpecies(overrides: Partial<Species> = {}): Species {
  return {
    key: 'sp-1',
    scientific_name: 'Solanum lycopersicum',
    common_names: ['Tomate'],
    family_key: null,
    family_name: null,
    genus: 'Solanum',
    hardiness_zones: [],
    native_habitat: '',
    growth_habit: 'herb',
    root_type: 'fibrous',
    allelopathy_score: 0,
    base_temp: 10,
    synonyms: [],
    taxonomic_authority: '',
    taxonomic_status: '',
    description: '',
    sowing_indoor_weeks_before_last_frost: null,
    sowing_outdoor_after_last_frost_days: null,
    direct_sow_months: [],
    harvest_months: [],
    bloom_months: [],
    harvest_from_year: null,
    bloom_from_year: null,
    frost_sensitivity: null,
    plant_category: null,
    harvest_pattern: null,
    harvested_part: null,
    climacteric: null,
    propagation_configs: [],
    allows_harvest: true,
    growing_periods: [],
    container_suitable: null,
    recommended_container_volume_l: null,
    min_container_depth_cm: null,
    mature_height_cm: null,
    mature_width_cm: null,
    spacing_cm: null,
    indoor_suitable: null,
    balcony_suitable: null,
    greenhouse_recommended: false,
    support_required: false,
    watering_guide: null,
    default_nutrient_plan_key: null,
    representative_image_url: null,
    representative_image_attribution: null,
    representative_image_license: null,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: null,
    ...overrides,
  };
}

/**
 * Serve one species record, plus a lifecycle whose phase sequence *does* contain
 * a harvest phase. The lifecycle matters: it makes the estimated-harvest-date row
 * renderable, so a suppression observed there can only come from the species
 * axis — which is the second call site of the shared predicate (#963).
 *
 * `payload` is deliberately typed as a *partial* species so a test can serve a
 * record with `allows_harvest` absent entirely — the tri-state the wire allows
 * even though the frontend type declares the field as required.
 */
function seedSpecies(payload: Partial<Species> & { key: string }) {
  server.use(
    http.get('/api/v1/species/:key', ({ params }) =>
      params.key === payload.key
        ? HttpResponse.json(payload)
        : HttpResponse.json(
            { error_id: 'e', error_code: 'ENTITY_NOT_FOUND', message: 'Not found', details: [], timestamp: '', path: '', method: '' },
            { status: 404 },
          ),
    ),
    http.get('/api/v1/species/:key/lifecycle', ({ params }) =>
      HttpResponse.json({
        key: `lc-${params.key}`,
        species_key: params.key,
        cycle_type: 'annual',
        cultivation_cycle_type: null,
        flowering_strategy: null,
        typical_lifespan_years: null,
        dormancy_required: false,
        vernalization_required: false,
        vernalization_min_days: null,
        photoperiod_type: 'day_neutral',
        critical_day_length_hours: null,
        phase_sequence_key: null,
        grown_as_annual: false,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: null,
      }),
    ),
    http.get('/api/v1/growth-phases', () =>
      HttpResponse.json([
        {
          key: 'gp-veg', name: 'vegetative', display_name: 'Vegetativ', description: '',
          lifecycle_key: 'lc-sp-1', typical_duration_days: 30, sequence_order: 1,
          is_terminal: false, allows_harvest: false, stress_tolerance: 'medium',
          watering_interval_days: null, created_at: '2024-01-01T00:00:00Z', updated_at: null,
        },
        {
          key: 'gp-harvest', name: 'harvest', display_name: 'Ernte', description: '',
          lifecycle_key: 'lc-sp-1', typical_duration_days: 60, sequence_order: 2,
          is_terminal: true, allows_harvest: true, stress_tolerance: 'low',
          watering_interval_days: null, created_at: '2024-01-01T00:00:00Z', updated_at: null,
        },
      ]),
    ),
  );
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

/**
 * Issue #963 — the readiness panel used to ask only "not removed yet?", so an
 * ornamental such as *Dracaena reflexa* was offered a trichome/Brix observation
 * it can never have. The page already declined to predict a harvest *date* for
 * that same plant, so the two displays contradicted each other. Both now consult
 * the shared `plantCanBeHarvested` predicate, and these tests hold them together:
 * every species variant is asserted against the readiness panel *and* the
 * estimated-harvest row, so a future change cannot fix one call site while
 * silently breaking the other.
 */
describe('PlantInstanceDetailPage — harvestability guard (#963)', () => {
  beforeEach(async () => {
    await i18n.changeLanguage('de');
    currentKey = 'plant-1';
    setActiveTenantSlug('test-tenant');
  });

  it('renders no readiness panel for a species that cannot be harvested', async () => {
    seedPlant(makePlant({ species_key: 'sp-1' }));
    seedSpecies(makeSpecies({ allows_harvest: false }));
    seedReadiness(() => HttpResponse.json(makeReadiness()));

    renderWithProviders(<PlantInstanceDetailPage />);

    // Wait for the species card: it only renders once the species resolved, so
    // reaching it proves the guard ran with the loaded (non-harvestable) record
    // rather than with a still-null one.
    await screen.findByTestId('species-card', {}, QUERY_TIMEOUT);
    expect(screen.queryByTestId('harvest-readiness-section')).toBeNull();
    expect(screen.queryByTestId('harvest-readiness-empty')).toBeNull();
    expect(screen.queryByTestId('record-observation-button')).toBeNull();
  });

  // The second call site, asserted separately so each display fails on its own
  // and neither can be fixed while the other silently regresses. The seeded
  // lifecycle *does* contain a harvest phase, so the phase-level conditions all
  // pass — only the shared species axis can suppress this row.
  it('makes no harvest-date promise for a species that cannot be harvested', async () => {
    seedPlant(makePlant({ species_key: 'sp-1' }));
    seedSpecies(makeSpecies({ allows_harvest: false }));
    seedReadiness(() => HttpResponse.json(makeReadiness()));

    renderWithProviders(<PlantInstanceDetailPage />);

    await screen.findByTestId('species-card', {}, QUERY_TIMEOUT);
    expect(screen.queryByTestId('estimated-harvest')).toBeNull();
  });

  // No flicker, and no wasted request. `HarvestReadinessSection` dispatches on
  // mount, so a panel that rendered and then vanished would leave a readiness
  // call behind — an empty request log is the machine-checkable form of "the
  // section was never mounted at any point".
  it('never fires the readiness request for a non-harvestable plant', async () => {
    seedPlant(makePlant({ species_key: 'sp-1' }));
    seedSpecies(makeSpecies({ allows_harvest: false }));
    const requested = seedReadiness(() => HttpResponse.json(makeReadiness()));

    renderWithProviders(<PlantInstanceDetailPage />);

    await screen.findByTestId('species-card', {}, QUERY_TIMEOUT);
    // Give any late effect a chance to fire before declaring the log empty.
    await waitFor(() => expect(screen.getByTestId('plant-info-card')).toBeInTheDocument(), QUERY_TIMEOUT);
    expect(requested).toEqual([]);
  });

  it('renders both harvest displays for a species that can be harvested', async () => {
    seedPlant(makePlant({ species_key: 'sp-1' }));
    seedSpecies(makeSpecies({ allows_harvest: true }));
    const requested = seedReadiness(() => HttpResponse.json(makeReadiness()));

    renderWithProviders(<PlantInstanceDetailPage />);

    expect(await screen.findByTestId('harvest-readiness-card', {}, QUERY_TIMEOUT)).toBeInTheDocument();
    await waitFor(() => expect(requested).toEqual(['plant-1']), QUERY_TIMEOUT);
    expect(screen.getByTestId('estimated-harvest')).toBeInTheDocument();
  });

  // The tri-state decision, pinned at the page level: an absent `allows_harvest`
  // renders the harvest UI. `allows_harvest` defaults to True on the domain
  // model, and suppressing the panel on a real crop would remove the only route
  // to record a ripeness observation (#818). Do not flip this to fail-closed.
  it('falls open when the species record carries no allows_harvest field', async () => {
    seedPlant(makePlant({ species_key: 'sp-1' }));
    const withoutFlag: Partial<Species> & { key: string } = { ...makeSpecies() };
    delete withoutFlag.allows_harvest;
    seedSpecies(withoutFlag);
    const requested = seedReadiness(() => HttpResponse.json(makeReadiness()));

    renderWithProviders(<PlantInstanceDetailPage />);

    expect(await screen.findByTestId('harvest-readiness-card', {}, QUERY_TIMEOUT)).toBeInTheDocument();
    await waitFor(() => expect(requested).toEqual(['plant-1']), QUERY_TIMEOUT);
    expect(screen.getByTestId('estimated-harvest')).toBeInTheDocument();
  });

  // A species that cannot be loaded at all must not cost the user the panel
  // either — the same fail-open answer, reached through `species === null`.
  it('falls open when the species record cannot be loaded', async () => {
    seedPlant(makePlant({ species_key: 'sp-missing' }));
    const requested = seedReadiness(() => HttpResponse.json(makeReadiness()));

    renderWithProviders(<PlantInstanceDetailPage />);

    expect(await screen.findByTestId('harvest-readiness-card', {}, QUERY_TIMEOUT)).toBeInTheDocument();
    await waitFor(() => expect(requested).toEqual(['plant-1']), QUERY_TIMEOUT);
    expect(screen.queryByTestId('species-card')).toBeNull();
  });
});
