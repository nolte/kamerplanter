/**
 * The care history of the tenant (REQ-053 GP-FR-107, GP-ACC-057): the last 90 days by default, every bed,
 * the same filters as a bed's history, 50 per page, and the person filter that follows the role (E-16).
 */
import { cleanup, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it } from 'vitest';
import { expectNoA11yViolations } from '@/test/a11y/expectNoA11yViolations';
import { authState, createTestStore, renderWithProviders, tenantState } from '@/test/helpers';
import CareHistoryPage from './CareHistoryPage';
import { careLine, useHistoryBackend } from './historyTestKit';

function renderPage(role: 'viewer' | 'grower' | 'lead' = 'grower') {
  return renderWithProviders(<CareHistoryPage />, {
    store: createTestStore({ ...tenantState(role), ...authState() }),
    route: '/standorte/historie',
  });
}

const DAY = 24 * 3600 * 1000;

afterEach(() => cleanup());

describe('CareHistoryPage', () => {
  it('asks for the last 90 days by default and lists the beds by name', async () => {
    const lines = Array.from({ length: 120 }, (_, index) =>
      careLine(`e${String(index).padStart(3, '0')}`, {
        summary: `Entry ${index}`,
        location_key: index % 2 === 0 ? 'loc_b03' : 'loc_b04',
        performed_at: new Date(Date.now() - index * DAY).toISOString(),
      }),
    );
    const backend = useHistoryBackend({ careEvents: lines });
    const before = Date.now();
    renderPage();

    const list = await screen.findByTestId('care-history-list');
    expect(within(list).getAllByRole('listitem')).toHaveLength(50);
    const first = backend.seen[0];
    expect(first.path).toBe('/care-events');
    expect(first.params.limit).toBe('50');
    expect(first.params.location_key).toBeUndefined();
    const from = Date.parse(first.params.from);
    expect(Math.abs(before - 90 * DAY - from)).toBeLessThan(60_000);
    // the bed name arrives from its own request
    await waitFor(() => expect(within(list).getAllByText('Raised bed 3').length).toBeGreaterThan(0));
    expect(within(list).getAllByText('Herb spiral').length).toBeGreaterThan(0);
  });

  it('pages on with "Load more"', async () => {
    const lines = Array.from({ length: 60 }, (_, index) => careLine(`e${index}`, { summary: `Entry ${index}` }));
    const backend = useHistoryBackend({ careEvents: lines });
    const user = userEvent.setup();
    renderPage();
    await screen.findByTestId('care-history-list');

    await user.click(screen.getByTestId('care-history-more'));

    await waitFor(() => expect(within(screen.getByTestId('care-history-list')).getAllByRole('listitem')).toHaveLength(60));
    expect(backend.seen.map((request) => request.params.offset)).toEqual(['0', '50']);
  });

  it('hides superseded entries until "Show corrections", and lists position corrections like any entry', async () => {
    const backend = useHistoryBackend({
      careEvents: [
        careLine('w1', { summary: 'Watered' }),
        careLine('p1', { category: 'position_corrected', summary: 'Position corrected (BED_001)', plant_keys: ['pl_1'], plant_names: ['TOM-1'] }),
      ],
    });
    const user = userEvent.setup();
    renderPage();

    expect(await screen.findByTestId('care-history-item-care:w1')).toBeInTheDocument();
    // The log lists what the server sends; a full page is never cut down on the client (the page would end up
    // short or empty while the server still has more).
    // The tenant-wide log names the plant from the line itself (#2514), not the slot of the stored summary.
    expect(screen.getByTestId('care-history-item-care:p1')).toHaveTextContent('Position corrected: TOM-1');
    expect(screen.getByTestId('care-history-item-care:p1')).not.toHaveTextContent('BED_001');
    expect(backend.seen[0].params.include_superseded).toBeUndefined();

    await user.click(screen.getByRole('switch', { name: 'Show corrections' }));

    await waitFor(() => expect(backend.seen.some((request) => request.params.include_superseded === 'true')).toBe(true));
  });

  it('filters by bed, then by that bed\'s plants', async () => {
    const backend = useHistoryBackend({
      careEvents: [careLine('w1')],
      plants: [{ plant_key: 'pi_1', instance_id: 'TOM-1' }],
    });
    const user = userEvent.setup();
    renderPage();
    await screen.findByTestId('care-history-list');
    expect(screen.queryByRole('combobox', { name: 'Plant' })).toBeNull();

    await user.click(await screen.findByRole('combobox', { name: 'Bed' }));
    await user.click(await screen.findByRole('option', { name: 'Raised bed 3' }));
    await waitFor(() => expect(backend.seen.some((request) => request.params.location_key === 'loc_b03')).toBe(true));

    await user.click(await screen.findByRole('combobox', { name: 'Plant' }));
    await user.click(await screen.findByRole('option', { name: 'TOM-1' }));
    await waitFor(() => expect(backend.seen.some((request) => request.params.plant_key === 'pi_1')).toBe(true));
  });

  it('"All time" sends a range, because the server answers 90 days when it gets none', async () => {
    const backend = useHistoryBackend({ careEvents: [careLine('w1')] });
    const user = userEvent.setup();
    renderPage();
    await screen.findByTestId('care-history-list');

    await user.click(screen.getByRole('combobox', { name: 'Period' }));
    await user.click(await screen.findByRole('option', { name: 'All time' }));

    await waitFor(() => expect(backend.seen.some((request) => request.params.from?.startsWith('2000-01-01'))).toBe(true));
  });

  it('offers a grower only themselves in the person filter', async () => {
    useHistoryBackend({
      careEvents: [careLine('w1')],
      members: [
        { key: 'mem_1', user_key: 'user-1', display_name: 'Tester' },
        { key: 'mem_2', user_key: 'user-2', display_name: 'Tom' },
      ],
    });
    const user = userEvent.setup();
    renderPage('grower');
    await screen.findByTestId('care-history-list');

    await user.click(screen.getByRole('combobox', { name: 'Person' }));

    expect((await screen.findAllByRole('option')).map((option) => option.textContent)).toEqual(['Everyone', 'Me']);
  });

  it('has no critical accessibility violations', async () => {
    useHistoryBackend({ careEvents: [careLine('w1'), careLine('w2', { category: 'feeding' })] });
    const { container } = renderPage();
    await screen.findByTestId('care-history-list');

    await expectNoA11yViolations(container, { minElements: 30 });
  });
});
