/**
 * The bed list (REQ-053 GP-FR-042/050, GP-API-011): counters, the row click, the status filter and
 * "My beds".
 */
import { cleanup, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { expectNoA11yViolations } from '@/test/a11y/expectNoA11yViolations';
import { authState, createTestStore, renderWithProviders, tenantState } from '@/test/helpers';
import { server } from '@/test/mocks/server';
import BedListSection from './BedListSection';
import { bedListItem } from './bedTestKit';

const BEDS = [
  bedListItem('bed_1', { name: 'Tomato bed', active_plant_count: 6, open_task_count: 3, overdue_task_count: 1, next_due_at: '2026-06-18T00:00:00Z' }),
  bedListItem('bed_2', { name: 'Herb spiral', active_plant_count: 0, open_task_count: 0 }),
  bedListItem('bed_3', { name: 'Old frame', bed_status: 'retired' }),
];

function useBackend(beds = BEDS, seen: URLSearchParams[] = []) {
  server.use(
    http.get('/api/v1/t/:tenant/locations', ({ request }) => {
      seen.push(new URL(request.url).searchParams);
      return HttpResponse.json(beds);
    }),
    http.get('/api/v1/location-types', () =>
      HttpResponse.json([{ key: 'raised_bed', name: 'Hochbeet', name_en: 'Raised bed' }]),
    ),
    http.get('/api/v1/tenants/:slug/members', () =>
      HttpResponse.json([
        { key: 'mem_me', user_key: 'user-1', display_name: 'Tester' },
        { key: 'mem_other', user_key: 'user-2', display_name: 'Alex' },
      ]),
    ),
    http.get('/api/v1/tenants/:slug/assignments', () =>
      HttpResponse.json([
        { key: 'a1', membership_key: 'mem_me', location_key: 'bed_1', tenant_key: 't' },
        { key: 'a2', membership_key: 'mem_other', location_key: 'bed_2', tenant_key: 't' },
      ]),
    ),
  );
}

function renderList(onSelectBed = vi.fn()) {
  const store = createTestStore({ ...tenantState('grower'), ...authState() });
  const view = renderWithProviders(
    <BedListSection siteKey="site_1" reloadToken="r1" onSelectBed={onSelectBed} />,
    { store },
  );
  return { onSelectBed, ...view };
}

afterEach(() => cleanup());

describe('BedListSection', () => {
  it('asks for the beds of the site and shows the counters (GP-API-011)', async () => {
    const seen: URLSearchParams[] = [];
    useBackend(BEDS, seen);
    renderList();
    const row = (await screen.findByText('Tomato bed')).closest('tr')!;
    expect(seen[0].get('site_key')).toBe('site_1');
    expect(seen[0].get('is_bed')).toBe('true');
    expect(within(row).getByText('3 (1 overdue)')).toBeInTheDocument();
    expect(within(row).getByText('6')).toBeInTheDocument();
    expect(within(row).getByText('Active')).toBeInTheDocument();
    await waitFor(() => expect(within(row).getByText('Tester')).toBeInTheDocument());
    await waitFor(() => expect(within(row).getByText('Raised bed')).toBeInTheDocument());
  });

  it('hides retired beds by default and shows them on request', async () => {
    useBackend();
    const user = userEvent.setup();
    renderList();
    await screen.findByText('Tomato bed');
    expect(screen.queryByText('Old frame')).toBeNull();
    await user.click(within(screen.getByTestId('bed-list-status-filter').parentElement!).getByRole('combobox'));
    await user.click(await screen.findByRole('option', { name: 'All' }));
    expect(await screen.findByText('Old frame')).toBeInTheDocument();
  });

  it('selects the bed on a row click and on Enter (GP-ACC-016), but the name link only navigates', async () => {
    useBackend();
    const user = userEvent.setup();
    const { onSelectBed } = renderList();
    const row = (await screen.findByText('Herb spiral')).closest('tr')!;
    await user.click(within(row).getByText('Active'));
    expect(onSelectBed).toHaveBeenCalledWith(expect.objectContaining({ key: 'bed_2' }));
    onSelectBed.mockClear();
    row.focus();
    await user.keyboard('{Enter}');
    expect(onSelectBed).toHaveBeenCalledTimes(1);
    onSelectBed.mockClear();
    const link = screen.getByTestId('bed-list-link-bed_1');
    expect(link).toHaveAttribute('href', '/standorte/locations/bed_1');
    await user.click(link);
    expect(onSelectBed).not.toHaveBeenCalled();
  });

  it('narrows the list to the beds assigned to me (GP-FR-050)', async () => {
    useBackend();
    const user = userEvent.setup();
    renderList();
    await screen.findByText('Tomato bed');
    const toggle = screen.getByTestId('bed-list-only-mine');
    await waitFor(() => expect(toggle).toBeEnabled());
    await user.click(toggle);
    expect(screen.getByText('Tomato bed')).toBeInTheDocument();
    expect(screen.queryByText('Herb spiral')).toBeNull();
  });

  it('shows an empty state and an error with retry', async () => {
    useBackend([]);
    renderList();
    expect(await screen.findByText('No beds yet')).toBeInTheDocument();
    cleanup();
    server.use(http.get('/api/v1/t/:tenant/locations', () => HttpResponse.json({ message: 'boom' }, { status: 500 })));
    renderList();
    expect(await screen.findByTestId('error-display')).toBeInTheDocument();
  });

  it('has no critical accessibility violations', async () => {
    useBackend();
    const { container } = renderList();
    await screen.findByText('Tomato bed');
    await expectNoA11yViolations(container);
  });
});
