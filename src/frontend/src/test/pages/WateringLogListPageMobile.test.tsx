import { cleanup, screen, within } from '@testing-library/react';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';
import type { WateringLog } from '@/api/types';
import { setActiveTenantSlug } from '@/api/client';
import { renderWithProviders } from '../helpers';
import { server } from '../mocks/server';

// Force the mobile breakpoint so the table renders its MobileCards.
vi.mock('@mui/material/useMediaQuery', () => ({ default: () => true }));

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

describe('WateringLogListPage — card hooks at mobile width', () => {
  beforeEach(async () => {
    await i18n.changeLanguage('de');
    setActiveTenantSlug('test-tenant');
  });

  afterEach(() => {
    cleanup();
  });

  it('keys every card value by the column id it mirrors', async () => {
    seed([makeLog()]);

    renderWithProviders(<WateringLogListPage />, { route: '/giessprotokoll' });

    const card = (await screen.findAllByTestId('data-table-row', {}, QUERY_TIMEOUT))[0];

    // Below the breakpoint there is no <td data-testid="cell-loggedAt"> to read.
    // The timestamp and the plants are the card's title/subtitle, so before the
    // title/subtitle hooks they were unreadable by column id and a cross-view
    // consistency test could not compare them against the other views at all.
    expect(within(card).getByTestId('card-field-loggedAt').textContent).not.toBe('');
    expect(within(card).getByTestId('card-field-plants').textContent).toContain('BASIL-0001');
    expect(within(card).getByTestId('card-field-volume').textContent).toContain('1');
    expect(within(card).getByTestId('card-chip-applicationMethod').textContent).toBe(
      i18n.t('enums.applicationMethod.drench'),
    );
    // Converted in the same pass: a half-keyed chip row silently answers a
    // question about one column with the chip of another.
    expect(within(card).getByTestId('card-chip-waterSource').textContent).toBe(
      i18n.t('enums.waterSource.tap'),
    );
    expect(within(card).getByTestId('card-chip-fertilizers').textContent).toContain('Grow A');
  });

  it('renders every plant as a link to its detail page, like the desktop column', async () => {
    // TC-004-092 (mobile/full-mobile): the plant references were flattened to
    // the card's plain-text subtitle, so a phone user had no way from the
    // watering log to the plant — the card's own click target leads to the
    // *log's* detail page. The spec demands a linked chip in both layouts.
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

    const card = (await screen.findAllByTestId('data-table-row', {}, QUERY_TIMEOUT))[0];
    const plantsGroup = within(card).getByTestId('card-field-plants');

    const links = within(plantsGroup).getAllByRole('link');
    expect(links.map((a) => a.getAttribute('href'))).toEqual([
      '/pflanzen/plant-instances/pi-1',
      '/pflanzen/plant-instances/pi-2',
    ]);
    expect(links.map((a) => a.textContent)).toEqual(['BASIL-0001', 'TOM-0002']);

    // Addressable per plant by its business key, not by chip position.
    expect(within(card).getByTestId('plant-link-pi-1')).toBe(links[0]);
    expect(within(card).getByTestId('plant-link-pi-2')).toBe(links[1]);
  });

  it('keys the plant group as both a card field and a card chip', async () => {
    // The readers resolve `cell-<id>` → `card-field-<id>` → `card-chip-<id>`.
    // The links moved from the subtitle into the chip row, so the chip hook is
    // new — but `card-field-plants` must survive the move, since that is the
    // hook the column-id readers hit first.
    seed([makeLog()]);

    renderWithProviders(<WateringLogListPage />, { route: '/giessprotokoll' });

    const card = (await screen.findAllByTestId('data-table-row', {}, QUERY_TIMEOUT))[0];
    const chipGroup = within(card).getByTestId('card-chip-plants');

    expect(chipGroup).toContainElement(within(card).getByTestId('card-field-plants'));
    expect(within(chipGroup).getByRole('link')).toHaveAttribute(
      'href',
      '/pflanzen/plant-instances/pi-1',
    );
  });

  it('caps the plant links at three and reports the rest as an overflow chip', async () => {
    // Mirrors the desktop column: the card is the narrower layout, so it needs
    // the cap at least as much. Beyond the cap the row click still reaches the
    // log's detail page, which lists every plant.
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

    const card = (await screen.findAllByTestId('data-table-row', {}, QUERY_TIMEOUT))[0];
    const plantsGroup = within(card).getByTestId('card-field-plants');

    expect(within(plantsGroup).getAllByRole('link')).toHaveLength(3);
    expect(within(card).queryByTestId('plant-link-pi-4')).toBeNull();
    expect(plantsGroup.textContent).toContain('+1');
  });

  it('keeps the plant column readable when no plant is attached', async () => {
    // A present-but-empty carrier says "no plant", the same thing the desktop
    // `<td>` says. An absent one is indistinguishable from an unkeyed card and
    // makes the reader raise instead of returning the empty value.
    seed([makeLog({ plant_keys: [], resolved_plants: [] })]);

    renderWithProviders(<WateringLogListPage />, { route: '/giessprotokoll' });

    const card = (await screen.findAllByTestId('data-table-row', {}, QUERY_TIMEOUT))[0];

    expect(within(card).getByTestId('card-field-plants').textContent).toBe('—');
    expect(within(card).queryAllByRole('link')).toHaveLength(0);
  });

  it('drops only the absent chips and keeps the remaining hooks stable', async () => {
    seed([makeLog({ water_source: null, resolved_fertilizers: [] })]);

    renderWithProviders(<WateringLogListPage />, { route: '/giessprotokoll' });

    const card = (await screen.findAllByTestId('data-table-row', {}, QUERY_TIMEOUT))[0];

    expect(within(card).queryByTestId('card-chip-waterSource')).toBeNull();
    expect(within(card).queryByTestId('card-chip-fertilizers')).toBeNull();
    // The unconditional chip keeps its own hook — with a positional read it
    // would have shifted onto whatever chip came first.
    expect(within(card).getByTestId('card-chip-applicationMethod').textContent).toBe(
      i18n.t('enums.applicationMethod.drench'),
    );
  });
});
