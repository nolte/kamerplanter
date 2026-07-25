import { cleanup, screen, within } from '@testing-library/react';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';
import type { PlantInstance, WateringLog } from '@/api/types';
import { setActiveTenantSlug } from '@/api/client';
import { renderWithProviders } from '../helpers';
import { server } from '../mocks/server';

// Force the mobile breakpoint so the watering-log table renders its MobileCards.
vi.mock('@mui/material/useMediaQuery', () => ({ default: () => true }));

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom');
  return { ...actual, useParams: () => ({ key: 'pi-1' }) };
});

// Stub the interactive dialogs the page mounts; none matter for the card hooks.
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

// Import after the mocks so they are picked up.
import PlantInstanceDetailPage from '@/pages/pflanzen/PlantInstanceDetailPage';

const WATERING_ROUTE = '/pflanzen/plant-instances/pi-1#watering-log';
const QUERY_TIMEOUT = { timeout: 5000 } as const;

const plant = {
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
} as unknown as PlantInstance;

function makeLog(overrides: Partial<WateringLog> = {}): WateringLog {
  return {
    key: 'wl-1',
    logged_at: '2026-07-25T08:30:00Z',
    application_method: 'drench',
    is_supplemental: false,
    volume_liters: 1,
    plant_keys: ['pi-1'],
    slot_keys: [],
    tank_fill_event_key: null,
    nutrient_plan_key: null,
    task_key: null,
    channel_id: null,
    fertilizers_used: [],
    ec_before: null,
    ec_after: null,
    ph_before: null,
    ph_after: null,
    runoff_ec: null,
    runoff_ph: null,
    runoff_volume_liters: null,
    water_source: null,
    performed_by: null,
    notes: null,
    created_at: '2026-07-25T08:30:00Z',
    updated_at: null,
    resolved_plants: [{ key: 'pi-1', name: 'BASIL-0001' }],
    resolved_fertilizers: [],
    ...overrides,
  } as WateringLog;
}

function seed(logs: WateringLog[]) {
  server.use(
    http.get('/api/v1/t/:tenant/plant-instances/:key', () => HttpResponse.json(plant)),
    http.get('/api/v1/plant-instances/:key', () => HttpResponse.json(plant)),
    http.get('/api/v1/t/:tenant/watering-logs/plant/:plantKey', () => HttpResponse.json(logs)),
  );
}

describe('PlantInstanceDetailPage — watering-log cards at mobile width', () => {
  beforeEach(async () => {
    await i18n.changeLanguage('de');
    setActiveTenantSlug('test-tenant');
  });

  afterEach(() => {
    cleanup();
  });

  it('keys every card value by the column id it mirrors', async () => {
    seed([makeLog()]);

    renderWithProviders(<PlantInstanceDetailPage />, { route: WATERING_ROUTE });

    const card = (await screen.findAllByTestId('data-table-row', {}, QUERY_TIMEOUT))[0];

    // Timestamp and application method are the card's title/subtitle: without
    // the title/subtitle hooks neither was addressable by its column id, so a
    // cross-view test could not compare this view against the global log.
    expect(within(card).getByTestId('card-field-loggedAt').textContent).not.toBe('');
    expect(within(card).getByTestId('card-field-applicationMethod').textContent).toBe(
      i18n.t('enums.applicationMethod.drench'),
    );
    expect(within(card).getByTestId('card-field-volume').textContent).toBe('1 L');
  });

  it('renders the supplemental field empty — not absent — for a plain watering', async () => {
    seed([makeLog({ is_supplemental: false })]);

    renderWithProviders(<PlantInstanceDetailPage />, { route: WATERING_ROUTE });

    const card = (await screen.findAllByTestId('data-table-row', {}, QUERY_TIMEOUT))[0];

    // As a conditional chip the column vanished for an ordinary watering, so
    // "the supplemental column must be empty" was unreadable rather than empty.
    expect(within(card).getByTestId('card-field-isSupplemental').textContent).toBe('');
  });

  it('renders the supplemental chip in the keyed field for a supplemental watering', async () => {
    seed([makeLog({ is_supplemental: true })]);

    renderWithProviders(<PlantInstanceDetailPage />, { route: WATERING_ROUTE });

    const card = (await screen.findAllByTestId('data-table-row', {}, QUERY_TIMEOUT))[0];

    expect(within(card).getByTestId('card-field-isSupplemental').textContent).toBe(
      i18n.t('common.yes'),
    );
  });
});
