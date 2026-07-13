import { screen, waitFor, fireEvent } from '@testing-library/react';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';
import type { PlantInstance, CareProfile } from '@/api/types';
import { setActiveTenantSlug } from '@/api/client';

// The detail page reads its target key from the route via useParams. Provide a
// stable key without depending on a matched route path.
let currentKey = 'pi-1';
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom');
  return {
    ...actual,
    useParams: () => ({ key: currentKey }),
  };
});

// Stub the interactive dialogs the page mounts (they read redux slices the shared
// test store does not preload); none are relevant to the Care-tab behaviour. The
// Care-profile form itself is intentionally NOT mocked — it now renders inline.
vi.mock('@/pages/pflege/components/CareConfirmDialog', () => ({ default: () => null }));
vi.mock('@/pages/giessprotokoll/WateringLogCreateDialog', () => ({ default: () => null }));
vi.mock('@/pages/duengung/NutrientPlanAssignDialog', () => ({ default: () => null }));
vi.mock('@/pages/pflanzen/PhaseTransitionDialog', () => ({ default: () => null }));
vi.mock('@/pages/pflanzen/TerminationDialog', () => ({ default: () => null }));
vi.mock('@/pages/pflanzen/PlantTagDialog', () => ({ default: () => null }));
vi.mock('@/components/print/PlantLabelDialog', () => ({ PlantLabelDialog: () => null }));
vi.mock('@/components/pests/PestScanButton', () => ({ default: () => null }));
vi.mock('@/pages/aufgaben/TaskCreateDialog', () => ({ default: () => null }));
// The overwintering section fires its own tenant-scoped reads; not under test here.
vi.mock('@/pages/pflanzen/OverwinteringSection', () => ({ default: () => null }));

import PlantInstanceDetailPage from '@/pages/pflanzen/PlantInstanceDetailPage';
import { renderWithProviders } from '../helpers';
import { server } from '../mocks/server';

const CARE_ROUTE = '/pflanzen/plant-instances/pi-1#care';

function makePlant(overrides: Partial<PlantInstance> = {}): PlantInstance {
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
    ...overrides,
  };
}

function makeCareProfile(overrides: Partial<CareProfile> = {}): CareProfile {
  return {
    key: 'cp-1',
    care_style: 'tropical',
    watering_interval_days: 7,
    winter_watering_multiplier: 1.0,
    watering_method: 'top_water',
    water_quality_hint: null,
    fertilizing_interval_days: 14,
    fertilizing_active_months: [3, 4, 5, 6, 7, 8, 9],
    repotting_interval_months: 12,
    pest_check_interval_days: 7,
    location_check_enabled: false,
    location_check_months: [],
    humidity_check_enabled: false,
    humidity_check_interval_days: 3,
    adaptive_learning_enabled: false,
    auto_create_watering_task: true,
    auto_create_fertilizing_task: true,
    auto_create_repotting_task: false,
    auto_create_pest_check_task: false,
    watering_interval_learned: null,
    fertilizing_interval_learned: null,
    notes: null,
    auto_generated: true,
    plant_key: 'pi-1',
    created_at: '2024-06-01T00:00:00Z',
    updated_at: null,
    ...overrides,
  };
}

function seedPlant(plant: PlantInstance) {
  server.use(
    http.get('/api/v1/t/:tenant/plant-instances/:key', ({ params }) =>
      params.key === plant.key
        ? HttpResponse.json(plant)
        : HttpResponse.json({ error_code: 'ENTITY_NOT_FOUND', message: 'Not found' }, { status: 404 }),
    ),
    http.get('/api/v1/plant-instances/:key', ({ params }) =>
      params.key === plant.key
        ? HttpResponse.json(plant)
        : HttpResponse.json({ error_code: 'ENTITY_NOT_FOUND', message: 'Not found' }, { status: 404 }),
    ),
  );
}

function seedCareProfile(getProfile: () => CareProfile) {
  server.use(
    http.get('/api/v1/care-reminders/plants/:key/profile', () =>
      HttpResponse.json(getProfile()),
    ),
  );
}

const QUERY_TIMEOUT = { timeout: 5000 } as const;

describe('PlantInstanceDetailPage — Care tab (#577)', () => {
  beforeEach(async () => {
    await i18n.changeLanguage('de');
    currentKey = 'pi-1';
    setActiveTenantSlug('test-tenant');
  });

  it('edits the care profile inline with no modal dialog', async () => {
    seedPlant(makePlant());
    seedCareProfile(() => makeCareProfile());

    renderWithProviders(<PlantInstanceDetailPage />, { route: CARE_ROUTE });

    // The editable form is rendered directly on the tab...
    await screen.findByTestId('care-profile-form', {}, QUERY_TIMEOUT);
    expect(screen.getByTestId('care-style-select')).toBeTruthy();
    expect(screen.getByTestId('save-profile-button')).toBeTruthy();
    expect(screen.getByTestId('reset-profile-button')).toBeTruthy();

    // ...and the former modal is gone: no dialog, no separate open-edit button.
    expect(screen.queryByTestId('care-profile-edit-dialog')).toBeNull();
    expect(screen.queryByTestId('cancel-button')).toBeNull();
  });

  it('persists an inline save and refreshes the profile state', async () => {
    seedPlant(makePlant());
    let current = makeCareProfile();
    seedCareProfile(() => current);
    let patchedBody: unknown = null;
    server.use(
      http.patch('/api/v1/care-reminders/plants/:key/profile', async ({ request }) => {
        patchedBody = await request.json();
        current = makeCareProfile({ care_style: 'succulent' });
        return HttpResponse.json(current);
      }),
    );

    renderWithProviders(<PlantInstanceDetailPage />, { route: CARE_ROUTE });

    await screen.findByTestId('care-profile-form', {}, QUERY_TIMEOUT);
    fireEvent.click(screen.getByTestId('save-profile-button'));

    await waitFor(() => expect(patchedBody).not.toBeNull(), QUERY_TIMEOUT);
    // onUpdated refreshes careProfile: the new style surfaces both in the
    // section-header chip and in the (re-seeded) inline care-style select. Before
    // the save the style was 'tropical', so 'Sukkulente' appeared zero times.
    await waitFor(
      () => expect(screen.getAllByText(i18n.t('enums.careStyle.succulent')).length).toBeGreaterThan(0),
      QUERY_TIMEOUT,
    );
  });
});
