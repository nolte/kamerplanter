/**
 * #3065: when the plant detail page moves to another plant while its Care tab is
 * open, nothing of the previous plant's care profile may render under the new
 * plant — neither its form nor its load error.
 *
 * The page keeps one instance across the key change, and the effect that drops
 * the previous answer runs only *after* the first render under the new key. That
 * render is what this suite watches: the form and the error display are
 * replaced by recorders that note which plant was in the route while they
 * rendered, so a stale render shows up even though the next effect would clear
 * it again before anything can be asserted on the DOM.
 */
import { act, screen, waitFor } from '@testing-library/react';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';
import type { CareProfile, PlantInstance } from '@/api/types';
import { setActiveTenantSlug } from '@/api/client';

let currentKey = 'pi-1';
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom');
  return {
    ...actual,
    useParams: () => ({ key: currentKey }),
  };
});

/** One entry per render: the plant in the route, and the plant the content belongs to. */
const formRenders: Array<{ route: string; profileOf: string }> = [];
const errorRenders: Array<{ route: string; error: string }> = [];

vi.mock('@/pages/pflege/components/CareProfileForm', () => ({
  default: ({ profile }: { profile: CareProfile }) => {
    formRenders.push({ route: currentKey, profileOf: profile.plant_key });
    return <div data-testid="care-profile-form" />;
  },
}));
vi.mock('@/components/common/ErrorDisplay', () => ({
  default: ({ error }: { error: string }) => {
    errorRenders.push({ route: currentKey, error });
    return <div role="alert" data-testid="error-display">{error}</div>;
  },
}));

vi.mock('@/pages/pflege/components/CareConfirmDialog', () => ({ default: () => null }));
vi.mock('@/pages/giessprotokoll/WateringLogCreateDialog', () => ({ default: () => null }));
vi.mock('@/pages/duengung/NutrientPlanAssignDialog', () => ({ default: () => null }));
vi.mock('@/pages/pflanzen/PhaseTransitionDialog', () => ({ default: () => null }));
vi.mock('@/pages/pflanzen/TerminationDialog', () => ({ default: () => null }));
vi.mock('@/pages/pflanzen/PlantTagDialog', () => ({ default: () => null }));
vi.mock('@/components/print/PlantLabelDialog', () => ({ PlantLabelDialog: () => null }));
vi.mock('@/components/pests/PestScanButton', () => ({ default: () => null }));
vi.mock('@/pages/aufgaben/TaskCreateDialog', () => ({ default: () => null }));
vi.mock('@/pages/pflanzen/OverwinteringSection', () => ({ default: () => null }));

import PlantInstanceDetailPage from '@/pages/pflanzen/PlantInstanceDetailPage';
import { renderWithProviders } from '../helpers';
import { server } from '../mocks/server';

const TIMEOUT = { timeout: 10000 } as const;

function makePlant(key: string): PlantInstance {
  return {
    key,
    instance_id: `BASIL-${key}`,
    species_key: 'sp-missing',
    cultivar_key: null,
    site_key: null,
    location_key: null,
    slot_key: null,
    substrate_batch_key: null,
    substrate_key: null,
    plant_name: `Basil ${key}`,
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

function makeProfile(plantKey: string): CareProfile {
  return {
    key: `cp-${plantKey}`,
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
    plant_key: plantKey,
    created_at: '2024-06-01T00:00:00Z',
    updated_at: null,
  };
}

/**
 * Plants answer for any key. The profile of `pi-1` answers as `pi1Profile`
 * says; the profile of `pi-2` is held back, so the new plant's own content can
 * never be what is rendered under it.
 */
function seed(pi1Profile: 'ok' | 'fail') {
  server.use(
    http.get('/api/v1/t/:tenant/plant-instances/:key', ({ params }) =>
      HttpResponse.json(makePlant(String(params.key))),
    ),
    http.get('/api/v1/plant-instances/:key', ({ params }) => HttpResponse.json(makePlant(String(params.key)))),
    http.get('/api/v1/care-reminders/plants/:key/profile', async ({ params }) => {
      const key = String(params.key);
      if (key === 'pi-1') {
        return pi1Profile === 'ok'
          ? HttpResponse.json(makeProfile('pi-1'))
          : HttpResponse.json({ error_code: 'INTERNAL_ERROR' }, { status: 500 });
      }
      await new Promise(() => {});
      return HttpResponse.json(makeProfile(key));
    }),
  );
}

async function moveToSecondPlant(router: { navigate: (to: string) => Promise<void> }) {
  currentKey = 'pi-2';
  await act(async () => {
    await router.navigate('/pflanzen/plant-instances/pi-2#care');
  });
}

describe('PlantInstanceDetailPage — Care tab across a plant change (#3065)', () => {
  beforeEach(async () => {
    await i18n.changeLanguage('de');
    currentKey = 'pi-1';
    formRenders.length = 0;
    errorRenders.length = 0;
    setActiveTenantSlug('test-tenant');
  });

  it('never renders the previous plant\'s form under the new plant', async () => {
    seed('ok');
    const { router } = renderWithProviders(<PlantInstanceDetailPage />, {
      route: '/pflanzen/plant-instances/pi-1#care',
    });
    await screen.findByTestId('care-profile-form', {}, TIMEOUT);

    await moveToSecondPlant(router);

    await waitFor(() => expect(screen.queryByTestId('care-profile-form')).toBeNull(), TIMEOUT);
    expect(formRenders.filter((r) => r.route === 'pi-2')).toEqual([]);
  });

  it('never renders the previous plant\'s load error under the new plant', async () => {
    seed('fail');
    const { router } = renderWithProviders(<PlantInstanceDetailPage />, {
      route: '/pflanzen/plant-instances/pi-1#care',
    });
    await waitFor(() => expect(errorRenders.some((r) => r.route === 'pi-1')).toBe(true), TIMEOUT);

    await moveToSecondPlant(router);

    await waitFor(() => expect(screen.queryByTestId('error-display')).toBeNull(), TIMEOUT);
    expect(errorRenders.filter((r) => r.route === 'pi-2')).toEqual([]);
  });
});
