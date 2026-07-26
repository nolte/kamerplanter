import { cleanup, screen, within } from '@testing-library/react';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';
import type { WateringLog } from '@/api/types';
import { setActiveTenantSlug } from '@/api/client';
import { renderWithProviders } from '../helpers';
import { server } from '../mocks/server';

// Desktop layout: `useMediaQuery(down('sm'))` is false, so `DataTable` renders
// its table. Pinned explicitly so the counterpart to
// `WateringLogListPageMobile.test.tsx` cannot silently drift into card layout.
vi.mock('@mui/material/useMediaQuery', () => ({ default: () => false }));

vi.mock('@/pages/giessprotokoll/WateringLogCreateDialog', () => ({ default: () => null }));

// Import after the mocks so they are picked up.
import WateringLogListPage from '@/pages/giessprotokoll/WateringLogListPage';

const QUERY_TIMEOUT = { timeout: 5000 } as const;

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
    water_source: 'tap',
    performed_by: null,
    notes: null,
    created_at: '2026-07-25T08:30:00Z',
    updated_at: null,
    resolved_plants: [{ key: 'pi-1', name: 'BASIL-0001' }],
    resolved_fertilizers: [{ key: 'f-1', name: 'Grow A', ml_per_liter: 2 }],
    ...overrides,
  } as WateringLog;
}

function seed(logs: WateringLog[]) {
  server.use(
    http.get('/api/v1/t/:tenant/watering-logs', () => HttpResponse.json(logs)),
  );
}

describe('WateringLogListPage — plants column at table width', () => {
  beforeEach(async () => {
    await i18n.changeLanguage('de');
    setActiveTenantSlug('test-tenant');
  });

  afterEach(() => {
    cleanup();
  });

  it('links every plant of the row to its detail page', async () => {
    // The same affordance the card must offer (TC-004-092). Pinned on the
    // desktop side as well, because both layouts now render it through one
    // shared component — a regression there would hit both at once.
    seed([
      makeLog({
        plant_keys: ['pi-1', 'pi-2'],
        resolved_plants: [
          { key: 'pi-1', name: 'BASIL-0001' },
          { key: 'pi-2', name: 'TOM-0002' },
        ],
      }),
    ]);

    renderWithProviders(<WateringLogListPage />, { route: '/giessprotokoll' });

    const cell = (await screen.findAllByTestId('cell-plants', {}, QUERY_TIMEOUT))[0];
    const links = within(cell).getAllByRole('link');

    expect(links.map((a) => a.getAttribute('href'))).toEqual([
      '/pflanzen/plant-instances/pi-1',
      '/pflanzen/plant-instances/pi-2',
    ]);
    expect(within(cell).getByTestId('plant-link-pi-2').textContent).toBe('TOM-0002');
  });

  it('caps the links at three and reports the rest as an overflow chip', async () => {
    seed([
      makeLog({
        plant_keys: ['pi-1', 'pi-2', 'pi-3', 'pi-4'],
        resolved_plants: [
          { key: 'pi-1', name: 'BASIL-0001' },
          { key: 'pi-2', name: 'TOM-0002' },
          { key: 'pi-3', name: 'MINT-0003' },
          { key: 'pi-4', name: 'SAGE-0004' },
        ],
      }),
    ]);

    renderWithProviders(<WateringLogListPage />, { route: '/giessprotokoll' });

    const cell = (await screen.findAllByTestId('cell-plants', {}, QUERY_TIMEOUT))[0];

    expect(within(cell).getAllByRole('link')).toHaveLength(3);
    expect(within(cell).queryByTestId('plant-link-pi-4')).toBeNull();
    expect(cell.textContent).toContain('+1');
  });

  it('renders a dash instead of a link when no plant is attached', async () => {
    seed([makeLog({ plant_keys: [], resolved_plants: [] })]);

    renderWithProviders(<WateringLogListPage />, { route: '/giessprotokoll' });

    const cell = (await screen.findAllByTestId('cell-plants', {}, QUERY_TIMEOUT))[0];

    expect(cell.textContent).toBe('—');
    expect(within(cell).queryAllByRole('link')).toHaveLength(0);
  });
});
