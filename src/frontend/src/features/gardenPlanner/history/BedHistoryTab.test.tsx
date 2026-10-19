/**
 * The history tab of the bed view (REQ-053 GP-FR-102, GP-FR-103, GP-FR-131; GP-ACC-027, GP-ACC-028): the
 * chronological list in pages of 50 with the filters category, period, plant and person, the corrections
 * switch, the planting timeline per year with the family named and colour-coded, and "What stood here in
 * {year}?".
 */
import { cleanup, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { delay, http, HttpResponse } from 'msw';
import { afterEach, describe, expect, it } from 'vitest';
import { expectNoA11yViolations } from '@/test/a11y/expectNoA11yViolations';
import { authState, createTestStore, renderWithProviders, tenantState } from '@/test/helpers';
import { server } from '@/test/mocks/server';
import { bedSummary } from '../bed/bedTestKit';
import BedHistoryTab from './BedHistoryTab';
import { BASE, careItem, FABACEAE, plantedItem, SOLANACEAE, timeline, useHistoryBackend, year } from './historyTestKit';
import type { HistoryItem } from './historyTypes';

const THIS_YEAR = new Date().getFullYear();

function renderTab(role: 'viewer' | 'grower' | 'lead' = 'grower', scopes: readonly string[] = []) {
  return renderWithProviders(<BedHistoryTab bed={bedSummary()} />, {
    store: createTestStore({ ...tenantState(role, scopes), ...authState() }),
    route: '/standorte/locations/loc_b03#history',
  });
}

/** 60 care events over two years, newest first, as the server lists them (GP-ACC-027). */
function sixtyEvents(): HistoryItem[] {
  return Array.from({ length: 60 }, (_, index) => {
    const day = 60 - index;
    const date = new Date(Date.UTC(THIS_YEAR - 1, 0, 1) + day * 12 * 24 * 3600 * 1000);
    return careItem(`e${String(day).padStart(2, '0')}`, {
      category: day % 2 === 0 ? 'watering' : 'feeding',
      summary: `Entry ${String(day).padStart(2, '0')}`,
      performed_at: date.toISOString(),
    });
  });
}

const FIVE_YEARS = [0, 1, 2, 3, 4].map((back) => year(THIS_YEAR - back));

afterEach(() => cleanup());

describe('BedHistoryTab - the list (GP-ACC-027)', () => {
  it('lists the newest 50 entries first and loads the rest on request', async () => {
    const backend = useHistoryBackend({ items: sixtyEvents(), timeline: timeline(FIVE_YEARS) });
    const user = userEvent.setup();
    renderTab();

    const list = await screen.findByTestId('history-list');
    expect(within(list).getAllByRole('listitem')).toHaveLength(50);
    expect(within(list).getAllByRole('listitem')[0]).toHaveTextContent('Entry 60');
    expect(screen.getByText('50 entries shown')).toBeInTheDocument();

    await user.click(screen.getByTestId('history-more'));
    await waitFor(() => expect(within(screen.getByTestId('history-list')).getAllByRole('listitem')).toHaveLength(60));
    expect(screen.queryByTestId('history-more')).toBeNull();
    const history = backend.seen.filter((request) => request.path.endsWith('/history'));
    expect(history.map((request) => request.params.offset)).toEqual(['0', '50']);
    expect(history[0].params.limit).toBe('50');
  });

  it('filters by category and asks the server for it', async () => {
    const backend = useHistoryBackend({ items: sixtyEvents(), timeline: timeline(FIVE_YEARS) });
    const user = userEvent.setup();
    renderTab();
    await screen.findByTestId('history-list');

    await user.click(screen.getByRole('combobox', { name: 'Category' }));
    await user.click(await screen.findByRole('option', { name: 'Watering' }));

    await waitFor(() =>
      expect(backend.seen.some((request) => request.path.endsWith('/history') && request.params.category === 'watering')).toBe(true),
    );
  });

  it('shows planting events next to care events and names the plant', async () => {
    useHistoryBackend({
      items: [
        careItem('w1', { summary: 'Watered the tomatoes', quantity: 2, unit: 'l', performed_by: 'Sabine' }),
        plantedItem('pl_1', 'TOM-1'),
        { ...plantedItem('pl_1', 'TOM-1', '2026-09-30T00:00:00Z'), id: 'plant_removed:pl_1', kind: 'plant_removed', category: 'removal', termination_type: 'harvested' },
      ],
      timeline: timeline(FIVE_YEARS),
    });
    renderTab();

    const care = await screen.findByTestId('history-item-care:w1');
    expect(care).toHaveTextContent('Watered the tomatoes');
    expect(care).toHaveTextContent('2 L');
    expect(care).toHaveTextContent('by Sabine');
    expect(screen.getByTestId('history-item-plant_planted:pl_1')).toHaveTextContent('TOM-1 planted');
    expect(screen.getByTestId('history-item-plant_removed:pl_1')).toHaveTextContent('TOM-1 removed (harvested)');
  });

  it('marks corrected and cancelled entries', async () => {
    useHistoryBackend({
      items: [
        careItem('old', { superseded_by_key: 'new' }),
        careItem('new', { supersedes_key: 'old' }),
        careItem('gone', { voided_at: '2026-06-02T00:00:00Z', void_reason: 'wrong bed' }),
      ],
      timeline: timeline(FIVE_YEARS),
    });
    renderTab();

    expect(await screen.findByTestId('history-item-care:old')).toHaveTextContent('Corrected');
    expect(screen.getByTestId('history-item-care:new')).toHaveTextContent('Correction');
    expect(screen.getByTestId('history-item-care:gone')).toHaveTextContent('Cancelled');
  });

  it('hides corrections by default and shows them on "Show corrections"', async () => {
    const backend = useHistoryBackend({ items: [careItem('a')], timeline: timeline(FIVE_YEARS) });
    const user = userEvent.setup();
    renderTab();
    await screen.findByTestId('history-list');
    const first = backend.seen.find((request) => request.path.endsWith('/history'));
    expect(first?.params.include_corrections).toBeUndefined();

    await user.click(screen.getByRole('switch', { name: 'Show corrections' }));

    await waitFor(() =>
      expect(backend.seen.some((request) => request.path.endsWith('/history') && request.params.include_corrections === 'true')).toBe(true),
    );
  });

  it('says so when nothing is logged, and when a filter hides everything', async () => {
    useHistoryBackend({ items: [], timeline: timeline(FIVE_YEARS) });
    const user = userEvent.setup();
    renderTab();
    expect(await screen.findByText('Nothing logged yet')).toBeInTheDocument();

    await user.click(screen.getByRole('switch', { name: 'Show corrections' }));
    expect(await screen.findByText('No entry matches')).toBeInTheDocument();
    await user.click(screen.getByTestId('history-reset'));
    expect(await screen.findByText('Nothing logged yet')).toBeInTheDocument();
  });

  it('keeps the list and offers a retry when the server fails', async () => {
    useHistoryBackend({ timeline: timeline(FIVE_YEARS) });
    server.use(http.get(`${BASE}/locations/:key/history`, () => HttpResponse.json({ detail: 'down' }, { status: 500 })));
    renderTab();

    expect(await screen.findByRole('button', { name: /retry|try again/i })).toBeInTheDocument();
  });

  it('a custom range that ends before it starts sends nothing and says why', async () => {
    const backend = useHistoryBackend({ items: [careItem('a')], timeline: timeline(FIVE_YEARS) });
    const user = userEvent.setup();
    renderTab();
    await screen.findByTestId('history-list');

    await user.click(screen.getByRole('combobox', { name: 'Period' }));
    await user.click(await screen.findByRole('option', { name: 'Custom range' }));
    await user.type(screen.getByLabelText('From'), '2026-06-10');
    await user.type(screen.getByLabelText('To'), '2026-06-01');

    expect(await screen.findByText('The end lies before the start.')).toBeInTheDocument();
    const withRange = backend.seen.filter((request) => request.params.to !== undefined && request.params.from !== undefined);
    expect(withRange).toHaveLength(0);
  });
});

describe('BedHistoryTab - paging that survives writes and failures', () => {
  it('shows a row once when a write between two pages shifted the window', async () => {
    const items = sixtyEvents();
    // The server answers the second page one row early: the last row of page 1 comes again.
    useHistoryBackend({ items: [], timeline: timeline(FIVE_YEARS) });
    server.use(
      http.get(`${BASE}/locations/:key/history`, ({ request }) => {
        const offset = Number(new URL(request.url).searchParams.get('offset') ?? 0);
        return HttpResponse.json(offset === 0 ? items.slice(0, 50) : items.slice(49, 60));
      }),
    );
    const user = userEvent.setup();
    renderTab();
    await screen.findByTestId('history-list');

    await user.click(screen.getByTestId('history-more'));

    await waitFor(() => expect(within(screen.getByTestId('history-list')).getAllByRole('listitem')).toHaveLength(60));
  });

  it('keeps the button, the focus and the rows when the next page fails, and tries again', async () => {
    const items = sixtyEvents();
    useHistoryBackend({ items: [], timeline: timeline(FIVE_YEARS) });
    let fail = true;
    server.use(
      http.get(`${BASE}/locations/:key/history`, async ({ request }) => {
        const offset = Number(new URL(request.url).searchParams.get('offset') ?? 0);
        if (offset > 0) await delay(150);
        if (offset > 0 && fail) return HttpResponse.json({ detail: 'down' }, { status: 500 });
        return HttpResponse.json(items.slice(offset, offset + 50));
      }),
    );
    const user = userEvent.setup();
    renderTab();
    await screen.findByTestId('history-list');
    const more = screen.getByTestId('history-more');
    more.focus();

    await user.click(more);

    // While the page loads the button is inert but not `disabled`: a disabled button drops the keyboard focus.
    expect(more).toHaveAttribute('aria-disabled', 'true');
    expect(more).not.toBeDisabled();
    expect(await screen.findByRole('button', { name: 'Try again' })).toBe(more);
    expect(more).toHaveFocus();
    expect(within(screen.getByTestId('history-list')).getAllByRole('listitem')).toHaveLength(50);
    fail = false;
    await user.click(more);
    await waitFor(() => expect(within(screen.getByTestId('history-list')).getAllByRole('listitem')).toHaveLength(60));
  });

  it('keeps the rows on screen when a reload after a backfill fails', async () => {
    useHistoryBackend({ items: [careItem('a', { summary: 'Mulched' })], timeline: timeline(FIVE_YEARS) });
    const user = userEvent.setup();
    renderTab();
    await screen.findByTestId('history-item-care:a');
    server.use(http.get(`${BASE}/locations/:key/history`, () => HttpResponse.json({ detail: 'down' }, { status: 500 })));

    await user.click(await screen.findByTestId(`timeline-add-${THIS_YEAR - 1}`));
    const dialog = await screen.findByTestId('backfill-dialog');
    await user.click(within(dialog).getByRole('combobox', { name: /What was it/ }));
    await user.click(await screen.findByRole('option', { name: 'Fallow (nothing grew)' }));
    await user.click(within(dialog).getByTestId('backfill-submit'));

    await waitFor(() => expect(screen.queryByTestId('backfill-dialog')).toBeNull());
    expect(await screen.findByTestId('history-item-care:a')).toHaveTextContent('Mulched');
  });
});

describe('BedHistoryTab - the person filter (E-16, SR-020)', () => {
  it('offers a grower only themselves', async () => {
    useHistoryBackend({
      items: [careItem('a')],
      timeline: timeline(FIVE_YEARS),
      members: [
        { key: 'mem_1', user_key: 'user-1', display_name: 'Tester' },
        { key: 'mem_2', user_key: 'user-2', display_name: 'Tom' },
      ],
    });
    const user = userEvent.setup();
    renderTab('grower');
    await screen.findByTestId('history-list');

    await user.click(screen.getByRole('combobox', { name: 'Person' }));
    const options = await screen.findAllByRole('option');
    expect(options.map((option) => option.textContent)).toEqual(['Everyone', 'Me']);
    expect(screen.getByText('You can filter by yourself; leads see every member.')).toBeInTheDocument();
  });

  it('offers a lead every member and sends the chosen account', async () => {
    const backend = useHistoryBackend({
      items: [careItem('a')],
      timeline: timeline(FIVE_YEARS),
      members: [
        { key: 'mem_1', user_key: 'user-1', display_name: 'Tester' },
        { key: 'mem_2', user_key: 'user-2', display_name: 'Tom' },
      ],
    });
    const user = userEvent.setup();
    renderTab('lead');
    await screen.findByTestId('history-list');

    await user.click(screen.getByRole('combobox', { name: 'Person' }));
    await user.click(await screen.findByRole('option', { name: 'Tom' }));

    await waitFor(() =>
      expect(backend.seen.some((request) => request.params.performed_by === 'user-2')).toBe(true),
    );
  });

  it('offers a member with the management scope every member too', async () => {
    useHistoryBackend({
      items: [],
      timeline: timeline(FIVE_YEARS),
      members: [{ key: 'mem_2', user_key: 'user-2', display_name: 'Tom' }],
    });
    const user = userEvent.setup();
    renderTab('viewer', ['management']);
    await screen.findByText('Nothing logged yet');

    await user.click(screen.getByRole('combobox', { name: 'Person' }));
    expect(await screen.findByRole('option', { name: 'Tom' })).toBeInTheDocument();
  });
});

describe('BedHistoryTab - the planting timeline (GP-FR-103, GP-ACC-028)', () => {
  it('lists at least five years, newest first, with the family named', async () => {
    useHistoryBackend({
      items: [],
      timeline: timeline([
        year(THIS_YEAR, [SOLANACEAE]),
        year(THIS_YEAR - 1, [FABACEAE]),
        year(THIS_YEAR - 2),
        year(THIS_YEAR - 3),
        year(THIS_YEAR - 4),
      ]),
    });
    renderTab();

    const rows = await screen.findAllByTestId(/^timeline-year-/);
    expect(rows.map((row) => row.getAttribute('data-testid'))).toEqual(
      FIVE_YEARS.map((entry) => `timeline-year-${entry.year}`),
    );
    expect(within(rows[0]).getByText(/Solanaceae/)).toBeInTheDocument();
    expect(within(rows[0]).getByText(/Heavy Feeder/)).toBeInTheDocument();
    expect(within(rows[1]).getByText(/Fabaceae/)).toBeInTheDocument();
    expect(within(rows[2]).getByText('Nothing recorded')).toBeInTheDocument();
  });

  it('names a fallow year and a green manure', async () => {
    useHistoryBackend({
      items: [],
      timeline: timeline([
        year(THIS_YEAR, [{ ...SOLANACEAE, plan_role: 'fallow', family_key: null, family_name: null, nutrient_demand: null }]),
        year(THIS_YEAR - 1, [{ ...FABACEAE, plan_role: 'green_manure', nutrient_demand: null }]),
        year(THIS_YEAR - 2),
        year(THIS_YEAR - 3),
        year(THIS_YEAR - 4),
      ]),
    });
    renderTab();

    expect(await screen.findByText('Fallow')).toBeInTheDocument();
    expect(screen.getByText(/Fabaceae · Green manure/)).toBeInTheDocument();
  });

  it('says the check is off for a bed that is exempt, and keeps the history', async () => {
    useHistoryBackend({
      items: [],
      timeline: timeline(FIVE_YEARS, {
        rotation_applicable: false,
        not_applicable_reason: 'rotation.not_applicable.container',
      }),
    });
    renderTab();

    expect(await screen.findByTestId('timeline-not-applicable')).toHaveTextContent(
      'The crop rotation check is off for pots, tents and shelves.',
    );
  });

  it('shows no write controls to a viewer', async () => {
    useHistoryBackend({ items: [], timeline: timeline(FIVE_YEARS) });
    renderTab('viewer');
    await screen.findByTestId('timeline-year-' + THIS_YEAR);

    expect(screen.queryByTestId('timeline-backfill')).toBeNull();
    expect(screen.queryByTestId(`timeline-add-${THIS_YEAR - 1}`)).toBeNull();
  });
});

describe('BedHistoryTab - what stood here in {year}? (GP-API-042)', () => {
  it('records a year from an empty row and offers to take it back', async () => {
    const backend = useHistoryBackend({ items: [], timeline: timeline(FIVE_YEARS) });
    const user = userEvent.setup();
    renderTab();

    await user.click(await screen.findByTestId(`timeline-add-${THIS_YEAR - 1}`));
    const dialog = await screen.findByTestId('backfill-dialog');
    expect(dialog).toHaveTextContent(`What stood here in ${THIS_YEAR - 1}?`);
    await user.click(within(dialog).getByRole('combobox', { name: /Plant family/ }));
    await user.click(await screen.findByRole('option', { name: 'Solanaceae' }));
    await user.click(within(dialog).getByTestId('backfill-submit'));

    await waitFor(() => expect(backend.seen.some((request) => request.method === 'POST')).toBe(true));
    const post = backend.seen.find((request) => request.method === 'POST');
    expect(post?.body).toEqual({ year: THIS_YEAR - 1, plan_role: 'main_crop', family_key: 'fam_sol' });
    expect(await screen.findByText(`Recorded ${THIS_YEAR - 1} for this bed.`)).toBeInTheDocument();
    // the timeline reloads and shows the recorded year with the cancel control
    expect(await screen.findByTestId('timeline-cancel-ce_bf')).toBeInTheDocument();

    await user.click(screen.getByTestId('care-undo'));
    await waitFor(() => expect(backend.seen.some((request) => request.method === 'DELETE')).toBe(true));
    expect(backend.seen.find((request) => request.method === 'DELETE')?.path).toBe(
      '/locations/loc_b03/history/backfill/ce_bf',
    );
  });

  it('refuses an empty family before it asks the server', async () => {
    const backend = useHistoryBackend({ items: [], timeline: timeline(FIVE_YEARS) });
    const user = userEvent.setup();
    renderTab();

    await user.click(await screen.findByTestId('timeline-backfill'));
    const dialog = await screen.findByTestId('backfill-dialog');
    await user.click(within(dialog).getByTestId('backfill-submit'));

    expect(await within(dialog).findByText('Choose a plant family or a species.')).toBeInTheDocument();
    expect(backend.seen.some((request) => request.method === 'POST')).toBe(false);
  });

  it('takes a fallow year without a family', async () => {
    const backend = useHistoryBackend({ items: [], timeline: timeline(FIVE_YEARS) });
    const user = userEvent.setup();
    renderTab();

    await user.click(await screen.findByTestId('timeline-backfill'));
    const dialog = await screen.findByTestId('backfill-dialog');
    await user.click(within(dialog).getByRole('combobox', { name: /What was it/ }));
    await user.click(await screen.findByRole('option', { name: 'Fallow (nothing grew)' }));
    expect(within(dialog).queryByRole('combobox', { name: /Plant family/ })).toBeNull();
    await user.click(within(dialog).getByTestId('backfill-submit'));

    await waitFor(() => expect(backend.seen.some((request) => request.method === 'POST')).toBe(true));
    expect(backend.seen.find((request) => request.method === 'POST')?.body).toEqual({
      year: THIS_YEAR - 1,
      plan_role: 'fallow',
    });
  });

  it('takes a recorded year back after a confirmation', async () => {
    const backend = useHistoryBackend({
      items: [],
      timeline: timeline([
        year(THIS_YEAR, []),
        year(THIS_YEAR - 1, [{ ...SOLANACEAE, source: 'backfill', care_event_key: 'ce_9' }]),
        year(THIS_YEAR - 2),
        year(THIS_YEAR - 3),
        year(THIS_YEAR - 4),
      ]),
    });
    const user = userEvent.setup();
    renderTab();

    await user.click(await screen.findByTestId('timeline-cancel-ce_9'));
    const confirm = await screen.findByTestId('confirm-dialog');
    expect(confirm).toHaveTextContent(`Take back the entry for ${THIS_YEAR - 1}?`);
    await user.click(within(confirm).getByTestId('confirm-dialog-confirm'));

    await waitFor(() => expect(backend.seen.some((request) => request.method === 'DELETE')).toBe(true));
    expect(backend.seen.find((request) => request.method === 'DELETE')?.path).toBe(
      '/locations/loc_b03/history/backfill/ce_9',
    );
  });
});

describe('BedHistoryTab - accessibility', () => {
  it('has no critical violations with the list, the timeline and the filters', async () => {
    useHistoryBackend({
      items: [careItem('a'), plantedItem('pl_1', 'TOM-1')],
      timeline: timeline([year(THIS_YEAR, [SOLANACEAE]), year(THIS_YEAR - 1), year(THIS_YEAR - 2), year(THIS_YEAR - 3), year(THIS_YEAR - 4)]),
    });
    const { container } = renderTab();
    await screen.findByTestId('history-list');
    await screen.findByTestId('timeline-year-' + THIS_YEAR);

    await expectNoA11yViolations(container, { minElements: 40 });
  });

  it('has no critical violations with the backfill dialog open', async () => {
    useHistoryBackend({ items: [], timeline: timeline(FIVE_YEARS) });
    const user = userEvent.setup();
    renderTab();
    await user.click(await screen.findByTestId('timeline-backfill'));
    const dialog = await screen.findByTestId('backfill-dialog');

    await expectNoA11yViolations(dialog, { minElements: 10 });
  });
});

describe('BedHistoryTab - filters on a phone', () => {
  it('folds the filters behind one button with the active count and unfolds them by keyboard', async () => {
    const original = window.matchMedia;
    window.matchMedia = ((query: string) => ({
      matches: query.includes('max-width'),
      media: query,
      onchange: null,
      addEventListener: () => undefined,
      removeEventListener: () => undefined,
      addListener: () => undefined,
      removeListener: () => undefined,
      dispatchEvent: () => false,
    })) as typeof window.matchMedia;
    try {
      useHistoryBackend({ items: [careItem('a')], timeline: timeline(FIVE_YEARS) });
      const user = userEvent.setup();
      renderTab();
      await screen.findByTestId('history-list');

      const toggle = screen.getByTestId('history-filters-toggle');
      expect(toggle).toHaveAttribute('aria-expanded', 'false');
      expect(toggle).toHaveTextContent('Filters');
      expect(screen.queryByRole('combobox', { name: 'Category' })).toBeNull();

      toggle.focus();
      await user.keyboard('{Enter}');
      expect(toggle).toHaveAttribute('aria-expanded', 'true');
      expect(await screen.findByRole('combobox', { name: 'Category' })).toBeVisible();

      await user.click(screen.getByRole('switch', { name: 'Show corrections' }));
      expect(toggle).toHaveTextContent('Filters (1 active)');
    } finally {
      window.matchMedia = original;
    }
  });
});
