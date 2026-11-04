/**
 * "Export CSV" of the care history (REQ-053 GP-FR-104, WP 8.4): the button asks for the entries the filters on screen
 * list (a bed adds its key), as a file; the Excel variant sends the semicolon; a refusal says why in the reader's
 * language.
 */
import { cleanup, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { expectNoA11yViolations } from '@/test/a11y/expectNoA11yViolations';
import { authState, createTestStore, renderWithProviders, tenantState } from '@/test/helpers';
import { server } from '@/test/mocks/server';
import { bedSummary } from '../bed/bedTestKit';
import BedHistoryTab from './BedHistoryTab';
import CareHistoryPage from './CareHistoryPage';
import { BASE, careItem, timeline, useHistoryBackend, year } from './historyTestKit';

const CSV = '﻿performed_at,category\r\n2026-06-01T08:00:00+00:00,watering\r\n';

interface Seen {
  params: Record<string, string>;
}

/** Answers `format=csv` with a file (and records the query); everything else stays the history backend's. */
function csvBackend(refusal?: { status: number; body: Record<string, unknown> }): Seen[] {
  const seen: Seen[] = [];
  server.use(
    http.get(`${BASE}/care-events`, ({ request }) => {
      const params = Object.fromEntries(new URL(request.url).searchParams.entries());
      if (params.format !== 'csv') return HttpResponse.json([]);
      seen.push({ params });
      if (refusal) return HttpResponse.json(refusal.body, { status: refusal.status });
      return new HttpResponse(CSV, { headers: { 'Content-Type': 'text/csv; charset=utf-8' } });
    }),
  );
  return seen;
}

function renderTab() {
  return renderWithProviders(<BedHistoryTab bed={bedSummary()} />, {
    store: createTestStore({ ...tenantState('viewer'), ...authState() }),
    route: '/standorte/locations/loc_b03#history',
  });
}

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe('HistoryExportButton', () => {
  it('downloads the bed history as CSV with the bed and the filters on screen', async () => {
    useHistoryBackend({
      items: [careItem('e1')],
      timeline: timeline([year(new Date().getFullYear() - 1)]),
    });
    const seen = csvBackend();
    const click = vi
      .spyOn(HTMLAnchorElement.prototype, 'click')
      .mockImplementation(() => undefined);
    const user = userEvent.setup();
    renderTab();
    await screen.findByTestId('history-list');

    await user.click(screen.getByRole('combobox', { name: 'Category' }));
    await user.click(await screen.findByRole('option', { name: 'Watering' }));
    await user.click(screen.getByTestId('history-export'));
    await user.click(await screen.findByTestId('history-export-comma'));

    await waitFor(() => expect(seen).toHaveLength(1));
    expect(seen[0].params).toMatchObject({
      format: 'csv',
      delimiter: 'comma',
      location_key: 'loc_b03',
      category: 'watering',
    });
    expect(seen[0].params.offset).toBeUndefined();
    await waitFor(() => expect(click).toHaveBeenCalledTimes(1));
  });

  it('sends the semicolon for the Excel variant', async () => {
    useHistoryBackend({ items: [careItem('e1')], timeline: timeline([]) });
    const seen = csvBackend();
    vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => undefined);
    const user = userEvent.setup();
    renderTab();
    await screen.findByTestId('history-list');

    await user.click(screen.getByTestId('history-export'));
    await user.click(await screen.findByTestId('history-export-semicolon'));

    await waitFor(() => expect(seen).toHaveLength(1));
    expect(seen[0].params.delimiter).toBe('semicolon');
  });

  it('is offered to a viewer too (reads are open to every member)', async () => {
    useHistoryBackend({ items: [], timeline: timeline([]) });
    renderTab();

    expect(await screen.findByTestId('history-export')).toBeEnabled();
  });

  it('says why a file over the row limit is refused and saves nothing', async () => {
    useHistoryBackend({ items: [careItem('e1')], timeline: timeline([]) });
    csvBackend({
      status: 422,
      body: {
        error_id: 'err_1',
        error_code: 'export.too_many_rows',
        message: 'The export would have more than 50000 rows',
        details: [{ field: 'request', reason: 'too many', code: 'export.too_many_rows' }],
        path: '/care-events',
        method: 'GET',
      },
    });
    const click = vi
      .spyOn(HTMLAnchorElement.prototype, 'click')
      .mockImplementation(() => undefined);
    const user = userEvent.setup();
    renderTab();
    await screen.findByTestId('history-list');

    await user.click(screen.getByTestId('history-export'));
    await user.click(await screen.findByTestId('history-export-comma'));

    expect(await screen.findByText(/more than 50,000 entries/)).toBeInTheDocument();
    expect(click).not.toHaveBeenCalled();
  });

  it('says to wait when the export budget is used up (the limiter answers without an error envelope)', async () => {
    useHistoryBackend({ items: [careItem('e1')], timeline: timeline([]) });
    server.use(
      http.get(`${BASE}/care-events`, ({ request }) =>
        new URL(request.url).searchParams.get('format') === 'csv'
          ? HttpResponse.json({ error: 'Rate limit exceeded: 10 per 1 minute' }, { status: 429 })
          : HttpResponse.json([]),
      ),
    );
    const click = vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => undefined);
    const user = userEvent.setup();
    renderTab();
    await screen.findByTestId('history-list');

    await user.click(screen.getByTestId('history-export'));
    await user.click(await screen.findByTestId('history-export-comma'));

    expect(await screen.findByText(/several exports a moment ago/)).toBeInTheDocument();
    expect(click).not.toHaveBeenCalled();
  });

  it('has no accessibility violations with the menu open', async () => {
    useHistoryBackend({ items: [], timeline: timeline([]) });
    const user = userEvent.setup();
    const { container } = renderTab();
    await user.click(await screen.findByTestId('history-export'));
    await screen.findByTestId('history-export-comma');

    await expectNoA11yViolations(container);
  });
});

describe('CareHistoryPage - export', () => {
  it('exports the tenant-wide log under the page filters and without a bed', async () => {
    useHistoryBackend({ careEvents: [] });
    const seen = csvBackend();
    vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => undefined);
    const user = userEvent.setup();
    renderWithProviders(<CareHistoryPage />, {
      store: createTestStore({ ...tenantState('grower'), ...authState() }),
      route: '/standorte/historie',
    });

    await user.click(await screen.findByTestId('care-history-export'));
    await user.click(await screen.findByTestId('care-history-export-comma'));

    await waitFor(() => expect(seen).toHaveLength(1));
    expect(seen[0].params.location_key).toBeUndefined();
    expect(seen[0].params.from).toBeDefined(); // the 90-day window the page shows
    expect(seen[0].params.format).toBe('csv');
  });
});
