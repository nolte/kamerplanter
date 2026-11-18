/**
 * #3014 (audit 2026-11, A-04): a detail page reloads when its route key changes.
 * Two answers in flight, the one for the previous key arriving last, must not
 * overwrite the entity that is now selected.
 *
 * Each case mounts the page under a real `/detail/:key` route, navigates from
 * key `a` to key `b` inside the same page instance, releases `b`'s answer first
 * and `a`'s afterwards, and asserts the title still names `b`.
 */
import type { ReactElement } from 'react';
import { act, render, screen, waitFor } from '@testing-library/react';
import { Provider } from 'react-redux';
import { createMemoryRouter, RouterProvider } from 'react-router-dom';
import { SnackbarProvider } from 'notistack';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';
import { ThemeContextProvider } from '@/theme';
import * as favoritesApi from '@/api/endpoints/favorites';
import { createStoreWithSmartHome, type TestStore } from '../helpers';
import { server } from '../mocks/server';

import TankDetailPage from '@/pages/standorte/TankDetailPage';
import LocationDetailPage from '@/pages/standorte/LocationDetailPage';
import SubstrateDetailPage from '@/pages/standorte/SubstrateDetailPage';
import SiteDetailPage from '@/pages/standorte/SiteDetailPage';
import FertilizerDetailPage from '@/pages/duengung/FertilizerDetailPage';
import TaskDetailPage from '@/pages/aufgaben/TaskDetailPage';
import HarvestBatchDetailPage from '@/pages/ernte/HarvestBatchDetailPage';
import PlantingRunDetailPage from '@/pages/durchlaeufe/PlantingRunDetailPage';
import PlantInstanceDetailPage from '@/pages/pflanzen/PlantInstanceDetailPage';

vi.mock('@/api/endpoints/favorites');

// Dialogs the plant detail page mounts unconditionally read slices this store
// does not preload; none take part in the load under test.
vi.mock('@/pages/pflege/components/CareConfirmDialog', () => ({ default: () => null }));
vi.mock('@/pages/pflege/components/CareProfileEditDialog', () => ({ default: () => null }));
vi.mock('@/pages/giessprotokoll/WateringLogCreateDialog', () => ({ default: () => null }));
vi.mock('@/pages/duengung/NutrientPlanAssignDialog', () => ({ default: () => null }));
vi.mock('@/pages/pflanzen/PhaseTransitionDialog', () => ({ default: () => null }));
vi.mock('@/pages/pflanzen/TerminationDialog', () => ({ default: () => null }));
vi.mock('@/pages/pflanzen/PlantTagDialog', () => ({ default: () => null }));
vi.mock('@/components/print/PlantLabelDialog', () => ({ PlantLabelDialog: () => null }));
vi.mock('@/components/pests/PestScanButton', () => ({ default: () => null }));

const T = '/api/v1/t/:tenant';
const TIMEOUT = { timeout: 20000 } as const;

/** A GET handler whose answer per key is held back until the test releases it. */
interface GatedEndpoint {
  requested: string[];
  release: (key: string) => void;
}

function gatedEndpoint(
  patterns: string | string[],
  entityFor: (key: string) => Record<string, unknown> | Record<string, unknown>[],
): GatedEndpoint {
  const releases = new Map<string, () => void>();
  const gates = new Map<string, Promise<void>>();
  const gateFor = (key: string) => {
    let gate = gates.get(key);
    if (!gate) {
      gate = new Promise<void>((resolve) => releases.set(key, resolve));
      gates.set(key, gate);
    }
    return gate;
  };
  const requested: string[] = [];
  server.use(
    ...[patterns].flat().map((pattern) =>
      http.get(pattern, async ({ params }) => {
        const key = String(params.key);
        requested.push(key);
        await gateFor(key);
        return HttpResponse.json(entityFor(key));
      }),
    ),
  );
  return {
    requested,
    release: (key) => {
      gateFor(key);
      releases.get(key)!();
    },
  };
}

function renderAtKey(ui: ReactElement, store: TestStore) {
  const router = createMemoryRouter([{ path: '/detail/:key', element: ui }], {
    initialEntries: ['/detail/a'],
  });
  render(
    <Provider store={store}>
      <ThemeContextProvider>
        <SnackbarProvider>
          <RouterProvider router={router} />
        </SnackbarProvider>
      </ThemeContextProvider>
    </Provider>,
  );
  return router;
}

/** Lets a released answer travel through MSW, axios and the page's awaits. */
async function settle() {
  await act(async () => {
    await new Promise((resolve) => setTimeout(resolve, 150));
  });
}

/**
 * Navigates a→b, answers b, then answers a late; the title must keep naming b.
 * `titleOf` is the text the page title shows for a key.
 */
async function expectLatestKeyWins(ui: ReactElement, gate: GatedEndpoint, titleOf: (key: string) => string) {
  const router = renderAtKey(ui, createStoreWithSmartHome());
  await waitFor(() => expect(gate.requested).toContain('a'), TIMEOUT);

  await act(async () => {
    await router.navigate('/detail/b');
  });
  await waitFor(() => expect(gate.requested).toContain('b'), TIMEOUT);

  gate.release('b');
  await waitFor(() => expect(screen.getByTestId('page-title').textContent).toContain(titleOf('b')), TIMEOUT);

  gate.release('a');
  await settle();

  expect(screen.getByTestId('page-title').textContent).toContain(titleOf('b'));
  expect(screen.getByTestId('page-title').textContent).not.toContain(titleOf('a'));
}

const ts = { created_at: '2024-01-01T00:00:00Z', updated_at: null };

describe('detail pages keep the current entity when an older answer arrives last (#3014)', () => {
  beforeEach(async () => {
    await i18n.changeLanguage('de');
    vi.mocked(favoritesApi.listFavorites).mockResolvedValue([]);
    vi.mocked(favoritesApi.addFavorite).mockResolvedValue({} as never);
    vi.mocked(favoritesApi.removeFavorite).mockResolvedValue(undefined);
    const storage = new Map<string, string>();
    vi.stubGlobal('localStorage', {
      getItem: (k: string) => storage.get(k) ?? null,
      setItem: (k: string, v: string) => void storage.set(k, v),
      removeItem: (k: string) => void storage.delete(k),
      clear: () => storage.clear(),
    });
  });

  it('TankDetailPage', async () => {
    server.use(
      http.get(`${T}/tanks/:key/states/latest`, () => HttpResponse.json(null)),
      http.get(`${T}/tanks/:key/states`, () => HttpResponse.json([])),
      http.get(`${T}/tanks/:key/alerts`, () => HttpResponse.json([])),
      http.get(`${T}/tanks/:key/maintenance/due`, () => HttpResponse.json([])),
      http.get(`${T}/tanks/:key/maintenance`, () => HttpResponse.json([])),
      http.get(`${T}/tanks/:key/schedules`, () => HttpResponse.json([])),
      http.get(`${T}/tanks/:key/fills`, () => HttpResponse.json([])),
      http.get(`${T}/tanks/:key/sensors`, () => HttpResponse.json([])),
      http.get(`${T}/tanks/:key/live-state`, () => HttpResponse.json({ available: false })),
      http.get(`${T}/observations/status`, () => HttpResponse.json({ available: false })),
      http.get(`${T}/ha/*`, () => HttpResponse.json({ published: false, available: false })),
    );
    const gate = gatedEndpoint(`${T}/tanks/:key`, (key) => ({
      key,
      name: `Tank ${key.toUpperCase()}`,
      tank_type: 'nutrient',
      volume_liters: 50,
      material: 'plastic',
      has_lid: true,
      has_air_pump: false,
      has_circulation_pump: false,
      has_heater: false,
      is_light_proof: false,
      has_uv_sterilizer: false,
      has_ozone_generator: false,
      installed_on: null,
      location_key: null,
      notes: null,
      ...ts,
    }));
    await expectLatestKeyWins(<TankDetailPage />, gate, (key) => `Tank ${key.toUpperCase()}`);
  });

  it('LocationDetailPage (child-location links reuse the page instance)', async () => {
    server.use(
      http.get(`${T}/locations/:key/bed-summary`, () => HttpResponse.json({}, { status: 404 })),
      http.get(`${T}/locations/:key/slots`, () => HttpResponse.json([])),
      http.get(`${T}/locations/:key/children`, () => HttpResponse.json([])),
      http.get(`${T}/locations/:key/sensors`, () => HttpResponse.json([])),
    );
    const gate = gatedEndpoint(`${T}/locations/:key`, (key) => ({
      key,
      site_key: 'site-1',
      name: `Zone ${key.toUpperCase()}`,
      location_type_key: 'lt-bed',
      parent_location_key: null,
      depth: 0,
      path: `Zone ${key.toUpperCase()}`,
      area_m2: 5,
      light_type: 'led',
      irrigation_system: 'drip',
      lights_on: '06:00',
      lights_off: '00:00',
      use_dynamic_sunrise: false,
      tank_key: null,
      ...ts,
    }));
    await expectLatestKeyWins(<LocationDetailPage />, gate, (key) => `Zone ${key.toUpperCase()}`);
  });

  it('SubstrateDetailPage', async () => {
    server.use(http.get('/api/v1/substrates/:key/batches', () => HttpResponse.json([])));
    const gate = gatedEndpoint('/api/v1/substrates/:key', (key) => ({
      key,
      type: 'coco',
      brand: 'CocoBrand',
      name_de: `Kokos ${key.toUpperCase()}`,
      name_en: `Coco ${key.toUpperCase()}`,
      is_mix: false,
      mix_components: [],
      ph_base: 6.0,
      ec_base_ms: 0.4,
      water_retention: 'medium',
      air_porosity_percent: 30,
      composition: {},
      additives: [],
      is_amendment: false,
      buffer_capacity: 'medium',
      reusable: true,
      max_reuse_cycles: 3,
      water_holding_capacity_percent: null,
      easily_available_water_percent: null,
      cec_meq_per_100cm3: null,
      particle_size_mm: null,
      bulk_density_g_per_l: null,
      irrigation_strategy: null,
      ...ts,
    }));
    await expectLatestKeyWins(<SubstrateDetailPage />, gate, (key) => `Kokos ${key.toUpperCase()}`);
  });

  it('SiteDetailPage', async () => {
    server.use(http.get(`${T}/sites/:key/sensors`, () => HttpResponse.json([])));
    const gate = gatedEndpoint(`${T}/sites/:key`, (key) => ({
      key,
      name: `Garden ${key.toUpperCase()}`,
      type: 'indoor',
      gps_coordinates: null,
      climate_zone: '7b',
      total_area_m2: 20,
      timezone: 'Europe/Berlin',
      water_config: null,
      ...ts,
    }));
    await expectLatestKeyWins(<SiteDetailPage />, gate, (key) => `Garden ${key.toUpperCase()}`);
  });

  it('FertilizerDetailPage', async () => {
    for (const base of [`${T}/fertilizers/:key`, '/api/v1/fertilizers/:key']) {
      server.use(
        http.get(`${base}/stocks`, () => HttpResponse.json([])),
        http.get(`${base}/nutrient-plans`, () => HttpResponse.json([])),
        http.get(`${base}/incompatibilities`, () => HttpResponse.json([])),
      );
    }
    const fertilizer = (key: string) => ({
      key,
      product_name: `Base ${key.toUpperCase()}`,
      brand: 'GrowCo',
      fertilizer_type: 'base',
      is_organic: false,
      tank_safe: true,
      recommended_application: 'fertigation',
      npk_ratio: [3, 1, 2],
      ec_contribution_per_ml: 0.4,
      ec_contribution_uncertain: false,
      max_dose_ml_per_liter: 5,
      mixing_priority: 3,
      ph_effect: 'neutral',
      bioavailability: 'immediate',
      shelf_life_days: null,
      storage_temp_min: null,
      storage_temp_max: null,
      application_rate_g_per_m2: null,
      application_rate_l_per_m2: null,
      dilution_ratio: null,
      nutrient_release_speed: null,
      notes: null,
      ...ts,
    });
    const gate = gatedEndpoint([`${T}/fertilizers/:key`, '/api/v1/fertilizers/:key'], fertilizer);
    await expectLatestKeyWins(<FertilizerDetailPage />, gate, (key) => `Base ${key.toUpperCase()}`);
  });

  it('TaskDetailPage', async () => {
    server.use(
      http.get(`${T}/tasks/:key/comments`, () => HttpResponse.json([])),
      http.get(`${T}/tasks/:key/history`, () => HttpResponse.json([])),
    );
    const gate = gatedEndpoint(`${T}/tasks/:key`, (key) => ({
      key,
      name: `Water ${key.toUpperCase()}`,
      name_de: `Giessen ${key.toUpperCase()}`,
      instruction: '',
      instruction_de: '',
      category: 'maintenance',
      entity_key: null,
      entity_type: null,
      due_date: null,
      scheduled_time: null,
      status: 'pending',
      priority: 'medium',
      skill_level: 'beginner',
      stress_level: 'none',
      estimated_duration_minutes: null,
      actual_duration_minutes: null,
      requires_photo: false,
      photo_refs: [],
      timer_duration_seconds: null,
      timer_label: null,
      completion_notes: null,
      difficulty_rating: null,
      quality_rating: null,
      tags: [],
      checklist: [],
      assigned_to_user_key: null,
      recurrence_rule: null,
      recurrence_end_date: null,
      origin: 'user',
      source: '',
      source_run_ref: null,
      external_ref: null,
      parent_recurring_task_key: null,
      trigger_phase: null,
      trigger_phase_override: null,
      reopened_at: null,
      reopened_from_status: null,
      started_at: null,
      completed_at: null,
      activity_key: null,
      template_key: null,
      workflow_execution_key: null,
      watering_event_key: null,
      ...ts,
    }));
    await expectLatestKeyWins(<TaskDetailPage />, gate, (key) => `Giessen ${key.toUpperCase()}`);
  });

  it('HarvestBatchDetailPage', async () => {
    server.use(
      http.get(`${T}/harvest/batches/:key/quality`, () => HttpResponse.json(null)),
      http.get(`${T}/harvest/batches/:key/yield`, () => HttpResponse.json(null)),
      http.get(`${T}/plant-instances/:key`, () => HttpResponse.json({}, { status: 404 })),
    );
    const gate = gatedEndpoint(`${T}/harvest/batches/:key`, (key) => ({
      key,
      batch_id: `HB-${key.toUpperCase()}`,
      plant_key: 'plant-1',
      harvest_date: '2024-06-01',
      harvest_type: 'final',
      wet_weight_g: 100,
      estimated_dry_weight_g: null,
      actual_dry_weight_g: null,
      quality_grade: null,
      harvester: '',
      notes: null,
      ...ts,
    }));
    await expectLatestKeyWins(<HarvestBatchDetailPage />, gate, (key) => `HB-${key.toUpperCase()}`);
  });

  it('PlantingRunDetailPage', async () => {
    server.use(
      http.get(`${T}/planting-runs/:key/entries`, () => HttpResponse.json([])),
      http.get(`${T}/planting-runs/:key/plants`, () => HttpResponse.json([])),
      http.get(`${T}/planting-runs/:key/nutrient-plan`, () => HttpResponse.json({ plan: null })),
      http.get(`${T}/planting-runs/:key/watering-schedule`, () => HttpResponse.json(null)),
      http.get(`${T}/planting-runs/:key/phase-timeline`, () => HttpResponse.json([])),
    );
    const gate = gatedEndpoint(`${T}/planting-runs/:key`, (key) => ({
      key,
      name: `Run ${key.toUpperCase()}`,
      run_type: 'monoculture',
      status: 'planned',
      planned_quantity: 3,
      actual_quantity: 0,
      current_phase_key: null,
      current_phase_started_at: null,
      lifecycle_config_key: null,
      location_key: null,
      substrate_batch_key: null,
      planned_start_date: null,
      started_at: null,
      completed_at: null,
      source_plant_key: null,
      notes: null,
      ...ts,
    }));
    await expectLatestKeyWins(<PlantingRunDetailPage />, gate, (key) => `Run ${key.toUpperCase()}`);
  });

  it('PlantInstanceDetailPage', async () => {
    stubPlantSecondaryReads();
    const gate = gatedEndpoint([`${T}/plant-instances/:key`, '/api/v1/plant-instances/:key'], plantFor);
    await expectLatestKeyWins(<PlantInstanceDetailPage />, gate, (key) => `Plant ${key.toUpperCase()}`);
  });

  it('PlantInstanceDetailPage — a fire-and-forget read of the previous plant lands late', async () => {
    stubPlantSecondaryReads();
    server.use(
      http.get(`${T}/plant-instances/:key`, ({ params }) => HttpResponse.json(plantFor(String(params.key)))),
    );
    const runs = gatedEndpoint(`${T}/plant-instances/:key/planting-runs`, (key) => [
      { key: `run-${key}`, name: `Run ${key.toUpperCase()}`, status: 'active' },
    ]);
    const router = renderAtKey(<PlantInstanceDetailPage />, createStoreWithSmartHome());
    await waitFor(() => expect(runs.requested).toContain('a'), TIMEOUT);
    await waitFor(() => expect(screen.getByTestId('page-title').textContent).toContain('Plant A'), TIMEOUT);

    await act(async () => {
      await router.navigate('/detail/b');
    });
    await waitFor(() => expect(runs.requested).toContain('b'), TIMEOUT);
    await waitFor(() => expect(screen.getByTestId('page-title').textContent).toContain('Plant B'), TIMEOUT);

    runs.release('b');
    await screen.findByText('Run B', {}, TIMEOUT);
    runs.release('a');
    await settle();

    expect(screen.getByText('Run B')).toBeTruthy();
    expect(screen.queryByText('Run A')).toBeNull();
  });
});

function stubPlantSecondaryReads() {
  // Every secondary read answers at once: an unhandled request passes through to
  // the network and, once the connection pool is used up, stalls the load.
  const notFound = () => HttpResponse.json({}, { status: 404 });
  server.use(
    http.get(`${T}/plant-instances/:key/*`, notFound),
    http.get('/api/v1/plant-instances/:key/*', notFound),
    http.get('/api/v1/care-reminders/*', notFound),
    http.get('/api/v1/tasks', () => HttpResponse.json([])),
    http.get('/api/v1/watering-logs/*', () => HttpResponse.json([])),
  );
}

function plantFor(key: string): Record<string, unknown> {
  return {
    key,
    instance_id: `PLT-${key.toUpperCase()}`,
    species_key: 'sp-missing',
    cultivar_key: null,
    site_key: null,
    location_key: null,
    slot_key: null,
    substrate_batch_key: null,
    substrate_key: null,
    plant_name: `Plant ${key.toUpperCase()}`,
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
    ...ts,
  };
}
