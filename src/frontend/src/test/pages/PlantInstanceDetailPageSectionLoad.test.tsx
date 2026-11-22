/**
 * #3037 SCR-003 / SCR-008 — the section banner of `PlantInstanceDetailPage`.
 *
 * - A 404 from a "not configured" read (the species' lifecycle) is the empty
 *   case and raises no banner.
 * - A 500 from `getPlantPlan` raises the banner and offers neither the species'
 *   default plan nor the "no plan assigned / assign" call to action; the retry
 *   then shows the plan.
 * - The section retry re-reads the secondary data only: unsaved input on the
 *   edit tab survives it.
 *
 * Harness borrowed from `PlantInstanceDetailPageCatalogueState.test.tsx`.
 */
import { cleanup, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, it, expect, beforeEach, vi } from 'vitest';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';
import type { PlantInstance, Species } from '@/api/types';
import { setActiveTenantSlug } from '@/api/client';

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom');
  return {
    ...actual,
    useParams: () => ({ key: 'pi-1' }),
  };
});

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
import { WAIT_BUDGET } from '../waitBudget';

const ERROR_BODY = { error_id: 'e', error_code: 'X', message: 'boom', details: [] };

function makePlant(): PlantInstance {
  return {
    key: 'pi-1',
    instance_id: 'BASIL-0001',
    species_key: 'sp-basil',
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

function makeSpecies(): Species {
  return {
    key: 'sp-basil',
    scientific_name: 'Ocimum basilicum',
    common_names: [],
    family_key: null,
    family_name: null,
    genus: 'Malus',
    hardiness_zones: [],
    native_habitat: '',
    growth_habit: 'tree',
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
    default_nutrient_plan_key: 'np-default',
    representative_image_url: null,
    representative_image_attribution: null,
    representative_image_license: null,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: null,
  };
}

const PLAN = { key: 'np-1', name: 'Basil Plan', cycle_restart_from_sequence: null };

interface Calls {
  plan: number;
  defaultPlan: number;
  plant: number;
}

/**
 * Serves every read of `load()` successfully; `planResponder` and
 * `lifecycleResponder` replace the two legs under test.
 */
function seed(options: {
  planResponder?: () => Response;
  lifecycleResponder?: () => Response;
} = {}): Calls {
  const calls: Calls = { plan: 0, defaultPlan: 0, plant: 0 };
  const plant = makePlant();
  server.use(
    http.get('*/plant-instances/:key', () => {
      calls.plant += 1;
      return HttpResponse.json(plant);
    }),
    http.get('/api/v1/species/:key', () => HttpResponse.json(makeSpecies())),
    http.get('/api/v1/species/:key/cultivars', () => HttpResponse.json([])),
    http.get('*/plant-instances/:key/planting-runs', () => HttpResponse.json([])),
    http.get('*/plant-instances/:key/phases/current', () =>
      HttpResponse.json(ERROR_BODY, { status: 404 }),
    ),
    http.get('*/plant-instances/:key/phases/history', () => HttpResponse.json([])),
    http.get('*/care-reminders/plants/:key/history', () => HttpResponse.json([])),
    http.get('*/tasks', () => HttpResponse.json([])),
    http.get('*/tasks/plants/:plantKey', () => HttpResponse.json([])),
    http.get('*/watering-logs/plant/:key', () => HttpResponse.json([])),
    http.get('/api/v1/species/:key/lifecycle', options.lifecycleResponder ?? (() =>
      HttpResponse.json({ key: 'lc-basil', species_key: 'sp-basil' }))),
    http.get('*/growth-phases', () => HttpResponse.json([])),
    http.get('*/plant-instances/:key/nutrient-plan', () => {
      calls.plan += 1;
      return options.planResponder ? options.planResponder() : HttpResponse.json(null);
    }),
    http.get('*/nutrient-plans/np-default', () => {
      calls.defaultPlan += 1;
      return HttpResponse.json({ ...PLAN, key: 'np-default', name: 'Default Plan' });
    }),
    http.get('*/nutrient-plans/:key/entries', () => HttpResponse.json([])),
    http.get('*/fertilizers', () => HttpResponse.json([])),
  );
  return calls;
}

describe('PlantInstanceDetailPage — section load banner (#3037)', () => {
  beforeEach(async () => {
    await i18n.changeLanguage('de');
    setActiveTenantSlug('test-tenant');
  });

  afterEach(async () => {
    cleanup();
    await i18n.changeLanguage('en');
  });

  it('raises no banner when the species has no lifecycle (404)', async () => {
    const calls = seed({
      lifecycleResponder: () => HttpResponse.json(ERROR_BODY, { status: 404 }),
    });
    renderWithProviders(<PlantInstanceDetailPage />, { route: '/pflanzen/plant-instances/pi-1' });

    await screen.findByTestId('plant-instance-detail-page', {}, { timeout: WAIT_BUDGET });
    // The plan is the last read of the run; once it is answered the run is over.
    await waitFor(() => expect(calls.defaultPlan).toBe(1), { timeout: WAIT_BUDGET });
    expect(screen.queryByTestId('plant-section-load-error')).toBeNull();
  });

  it('flags a failed plan read, offers no default or assign, and shows the plan after the retry', async () => {
    let failPlan = true;
    const calls = seed({
      planResponder: () =>
        failPlan ? HttpResponse.json(ERROR_BODY, { status: 500 }) : HttpResponse.json(PLAN),
    });
    const user = userEvent.setup();
    renderWithProviders(<PlantInstanceDetailPage />, {
      route: '/pflanzen/plant-instances/pi-1',
    });

    const banner = await screen.findByTestId('plant-section-load-error', {}, { timeout: WAIT_BUDGET });
    expect(banner).toHaveAttribute('role', 'alert');
    // The species default is not offered in place of a failed read.
    expect(calls.defaultPlan).toBe(0);

    await user.click(screen.getByRole('tab', { name: i18n.t('entities.nutrientPlan') }));
    expect(screen.queryByTestId('plant-no-plan-assigned')).toBeNull();
    expect(screen.queryByText(i18n.t('pages.nutrientPlans.noPlanAssigned'))).toBeNull();
    expect(screen.queryByRole('button', { name: i18n.t('pages.nutrientPlans.assignPlan') })).toBeNull();

    failPlan = false;
    await user.click(screen.getByTestId('plant-section-load-error-retry'));

    expect(await screen.findByText('Basil Plan', {}, { timeout: WAIT_BUDGET })).toBeInTheDocument();
    expect(screen.queryByTestId('plant-section-load-error')).toBeNull();
    expect(calls.plan).toBe(2);
  });

  it('keeps unsaved edit-tab input across the section retry', async () => {
    let failPlan = true;
    const calls = seed({
      planResponder: () =>
        failPlan ? HttpResponse.json(ERROR_BODY, { status: 500 }) : HttpResponse.json(null),
    });
    const user = userEvent.setup();
    renderWithProviders(<PlantInstanceDetailPage />, {
      route: '/pflanzen/plant-instances/pi-1#edit',
    });

    await screen.findByTestId('plant-section-load-error', {}, { timeout: WAIT_BUDGET });
    const name = within(screen.getByTestId('form-field-plant_name')).getByRole('textbox');
    await user.clear(name);
    await user.type(name, 'Genovese');

    failPlan = false;
    await user.click(screen.getByTestId('plant-section-load-error-retry'));

    await waitFor(() => expect(calls.plan).toBe(2), { timeout: WAIT_BUDGET });
    await waitFor(() => expect(screen.queryByTestId('plant-section-load-error')).toBeNull());
    expect(within(screen.getByTestId('form-field-plant_name')).getByRole('textbox')).toHaveValue(
      'Genovese',
    );
    // No page skeleton in between: the plant itself was not re-read.
    expect(calls.plant).toBe(1);
  });
});
