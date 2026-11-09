/**
 * The rotation matrix of a site (REQ-053 GP-FR-135, WP 8.13): table semantics, the family carried by code and
 * pattern next to the colour, the feeder class as text, the year dialog behind a past cell, paging with a stable
 * look-back, marked beds and the reading rights per role.
 */
import { cleanup, render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { Provider } from 'react-redux';
import { SnackbarProvider } from 'notistack';
import { RouterProvider, createMemoryRouter } from 'react-router-dom';
import { afterEach, describe, expect, it } from 'vitest';
import { expectNoA11yViolations } from '@/test/a11y/expectNoA11yViolations';
import { authState, createTestStore, tenantState } from '@/test/helpers';
import { server } from '@/test/mocks/server';
import { ThemeContextProvider } from '@/theme';
import { BASE, FABACEAE, SOLANACEAE, useHistoryBackend } from './historyTestKit';
import type { RotationMatrix, RotationMatrixBed, RotationYear } from './historyTypes';
import RotationMatrixPage from './RotationMatrixPage';

const THIS_YEAR = new Date().getFullYear();
const COLUMNS = [0, 1, 2, 3, 4].map((back) => THIS_YEAR - 4 + back);

function cells(filled: Record<number, RotationYear['plantings']> = {}): RotationYear[] {
  return COLUMNS.map((year) => ({ year, plantings: filled[year] ?? [] }));
}

function bed(key: string, name: string, overrides: Partial<RotationMatrixBed> = {}): RotationMatrixBed {
  return {
    location_key: key,
    name,
    rotation_applicable: true,
    not_applicable_reason: null,
    rotation_reset_at: null,
    cells: cells({ [THIS_YEAR - 2]: [SOLANACEAE], [THIS_YEAR - 1]: [FABACEAE] }),
    ...overrides,
  };
}

interface Seen {
  params: Record<string, string>;
}

function useMatrix(beds: RotationMatrixBed[], options: { total?: number; fail?: boolean } = {}) {
  const seen: Seen[] = [];
  server.use(
    http.get(`${BASE}/sites/:key/rotation-matrix`, ({ request }) => {
      const params = Object.fromEntries(new URL(request.url).searchParams);
      seen.push({ params });
      if (options.fail) return HttpResponse.json({ detail: 'boom' }, { status: 500 });
      const offset = Number(params.offset ?? 0);
      const limit = Number(params.limit ?? 50);
      const body: RotationMatrix = {
        site_key: 'site_1',
        years: Number(params.years ?? 5),
        columns: COLUMNS,
        total: options.total ?? beds.length,
        truncated: false,
        offset,
        limit,
        beds: beds.slice(offset, offset + limit),
      };
      return HttpResponse.json(body);
    }),
  );
  return { seen };
}

function renderPage(role: 'viewer' | 'grower' | 'lead' = 'grower') {
  const store = createTestStore({ ...tenantState(role), ...authState() });
  const router = createMemoryRouter(
    [
      { path: 'standorte/sites/:key/rotation-matrix', element: <RotationMatrixPage /> },
      { path: 'standorte/sites/:key', element: <div data-testid="site-stub" /> },
      { path: 'standorte/locations/:key', element: <div data-testid="bed-stub" /> },
    ],
    { initialEntries: ['/standorte/sites/site_1/rotation-matrix'] },
  );
  return {
    router,
    ...render(
      <Provider store={store}>
        <ThemeContextProvider>
          <SnackbarProvider>
            <RouterProvider router={router} />
          </SnackbarProvider>
        </ThemeContextProvider>
      </Provider>,
    ),
  };
}

afterEach(() => cleanup());

describe('RotationMatrixPage - table semantics and marks', () => {
  it('is a table with a column header per year and a row header per bed', async () => {
    useMatrix([bed('loc_a', 'Raised bed 1'), bed('loc_b', 'Herb spiral')]);
    renderPage();

    const table = await screen.findByTestId('rotation-matrix-table');
    expect(within(table).getAllByRole('columnheader').map((cell) => cell.textContent)).toEqual([
      'Bed',
      ...COLUMNS.map(String),
    ]);
    expect(within(table).getAllByRole('rowheader').map((cell) => cell.textContent)).toEqual([
      'Raised bed 1',
      'Herb spiral',
    ]);
    // the scroll region is a labelled, focusable region (keyboard users can scroll it)
    const region = screen.getByRole('region', { name: /Crop rotation matrix/ });
    expect(region).toHaveAttribute('tabindex', '0');
  });

  it('marks a family by code and pattern, not by colour alone, and shows the feeder class as text', async () => {
    useMatrix([bed('loc_a', 'Raised bed 1')]);
    renderPage();

    const cell = await screen.findByTestId(`matrix-cell-loc_a-${THIS_YEAR - 2}`);
    expect(within(cell).getByText('So')).toBeInTheDocument(); // the code of Solanaceae
    expect(within(cell).getByText(/Heavy feeder/i)).toBeInTheDocument();
    const legend = screen.getByTestId('matrix-legend');
    expect(within(legend).getByText('Solanaceae', { exact: false })).toBeInTheDocument();
    expect(within(legend).getByText('Fabaceae', { exact: false })).toBeInTheDocument();
    // two families, two different patterns
    const swatches = legend.querySelectorAll<HTMLElement>('[data-testid^="matrix-swatch-"]');
    expect(new Set([...swatches].map((swatch) => swatch.style.backgroundImage || getComputedStyle(swatch).backgroundImage)).size).toBe(2);
  });

  it('links a bed name to the bed and an empty year shows a dash', async () => {
    useMatrix([bed('loc_a', 'Raised bed 1')]);
    const { router } = renderPage();
    const user = userEvent.setup();

    expect(await screen.findByTestId(`matrix-cell-loc_a-${COLUMNS[0]}`)).toHaveTextContent('–');
    await user.click(screen.getByTestId('matrix-bed-link-loc_a'));
    await waitFor(() => expect(router.state.location.pathname).toBe('/standorte/locations/loc_a'));
  });

  it('marks a bed the rotation check is off for and still shows its history', async () => {
    useMatrix([
      bed('loc_a', 'Hedge', { rotation_applicable: false, not_applicable_reason: 'rotation.not_applicable.rotation_exempt' }),
      bed('loc_b', 'Raised bed 1'),
    ]);
    renderPage();

    expect(await screen.findByTestId('matrix-off-loc_a')).toHaveTextContent('Exempt from the rotation check');
    expect(screen.queryByTestId('matrix-off-loc_b')).toBeNull();
    expect(screen.getByTestId(`matrix-cell-loc_a-${THIS_YEAR - 2}`)).toHaveTextContent('So');
  });

  it('says so when a site has no beds', async () => {
    useMatrix([]);
    renderPage();
    expect(await screen.findByTestId('matrix-empty')).toBeInTheDocument();
    expect(screen.queryByTestId('rotation-matrix-table')).toBeNull();
  });

  it('keeps every hidden text inside the scroll container, so the table scrolls there and not the page (#2764)', async () => {
    // Beds with empty years: each empty cell carries a visually hidden "nothing recorded".
    useMatrix([bed('loc_a', 'Raised bed 1', { cells: cells() }), bed('loc_b', 'Herb spiral')]);
    renderPage();

    const region = await screen.findByTestId('matrix-scroll');
    expect(getComputedStyle(region).position).toBe('relative');
    const hidden = [...region.querySelectorAll<HTMLElement>('*')].filter(
      (element) => getComputedStyle(element).position === 'absolute',
    );
    expect(hidden.length).toBeGreaterThan(0);
    for (const element of hidden) {
      // A positioned ancestor inside the container clips it; with none, the page grows by its offset (3596 px).
      let anchor: HTMLElement | null = element.parentElement;
      while (anchor && anchor !== region && getComputedStyle(anchor).position === 'static') anchor = anchor.parentElement;
      expect(anchor === region || region.contains(anchor)).toBe(true);
      // One pixel, never a share of the containing block (`sx={{ width: 1 }}` is 100 %).
      expect(getComputedStyle(element).width).toBe('1px');
    }
  });

  it('has no critical accessibility violation', async () => {
    useMatrix([bed('loc_a', 'Raised bed 1'), bed('loc_b', 'Herb spiral')]);
    const { container } = renderPage();
    await screen.findByTestId('rotation-matrix-table');
    await expectNoA11yViolations(container);
  });
});

describe('RotationMatrixPage - rights and the year dialog (GP-API-042)', () => {
  it('lets a viewer read but gives no past cell a button', async () => {
    useMatrix([bed('loc_a', 'Raised bed 1')]);
    renderPage('viewer');

    await screen.findByTestId('rotation-matrix-table');
    expect(screen.queryByTestId(`matrix-cell-button-loc_a-${THIS_YEAR - 1}`)).toBeNull();
    expect(screen.queryByTestId('matrix-edit-hint')).toBeNull();
  });

  it('opens "What stood here?" for a past cell of a grower, never for the current year', async () => {
    useMatrix([bed('loc_a', 'Raised bed 1')]);
    useHistoryBackend();
    const user = userEvent.setup();
    renderPage('grower');

    expect(await screen.findByTestId(`matrix-cell-loc_a-${THIS_YEAR}`)).toBeInTheDocument();
    expect(screen.queryByTestId(`matrix-cell-button-loc_a-${THIS_YEAR}`)).toBeNull();
    const button = screen.getByTestId(`matrix-cell-button-loc_a-${THIS_YEAR - 3}`);
    expect(button).toHaveAccessibleName(/Raised bed 1, \d{4}: nothing recorded\. What stood here\?/);
    await user.click(button);

    const dialog = await screen.findByTestId('backfill-dialog');
    expect(dialog).toHaveTextContent(`What stood here in ${THIS_YEAR - 3}?`);
  });

  it('records the year for that bed, reloads the matrix and offers to take it back', async () => {
    const matrixSeen = useMatrix([bed('loc_a', 'Raised bed 1')]);
    const backend = useHistoryBackend();
    const user = userEvent.setup();
    renderPage('grower');

    await user.click(await screen.findByTestId(`matrix-cell-button-loc_a-${THIS_YEAR - 3}`));
    const dialog = await screen.findByTestId('backfill-dialog');
    await user.click(within(dialog).getByRole('combobox', { name: /Plant family/ }));
    await user.click(await screen.findByRole('option', { name: 'Solanaceae' }));
    await user.click(within(dialog).getByTestId('backfill-submit'));

    await waitFor(() => expect(backend.seen.some((request) => request.method === 'POST')).toBe(true));
    const post = backend.seen.find((request) => request.method === 'POST');
    expect(post?.path).toBe('/locations/loc_a/history/backfill');
    expect(post?.body).toEqual({ year: THIS_YEAR - 3, plan_role: 'main_crop', family_key: 'fam_sol' });
    await waitFor(() => expect(matrixSeen.seen.length).toBeGreaterThanOrEqual(2)); // reloaded
    expect(await screen.findByText(`Recorded ${THIS_YEAR - 3} for this bed.`)).toBeInTheDocument();

    await user.click(screen.getByTestId('care-undo'));
    await waitFor(() => expect(backend.seen.some((request) => request.method === 'DELETE')).toBe(true));
  });
});

describe('RotationMatrixPage - paging', () => {
  it('loads the next beds with the look-back of the first answer and appends them', async () => {
    const all = Array.from({ length: 3 }, (_, index) => bed(`loc_${index}`, `Bed ${index}`));
    const backend = useMatrix(all, { total: 3 });
    // a page of one bed at a time: the page size is the server's limit
    server.use(
      http.get(`${BASE}/sites/:key/rotation-matrix`, ({ request }) => {
        const params = Object.fromEntries(new URL(request.url).searchParams);
        backend.seen.push({ params });
        const offset = Number(params.offset ?? 0);
        return HttpResponse.json({
          site_key: 'site_1',
          years: 7,
          columns: COLUMNS,
          total: 3,
          truncated: false,
          offset,
          limit: 1,
          beds: all.slice(offset, offset + 1),
        });
      }),
    );
    const user = userEvent.setup();
    renderPage();

    expect(await screen.findByTestId('matrix-count')).toHaveTextContent('1 of 3 beds');
    await user.click(screen.getByTestId('matrix-more'));
    await waitFor(() => expect(screen.getByTestId('matrix-count')).toHaveTextContent('2 of 3 beds'));

    expect(backend.seen[1].params.offset).toBe('1');
    expect(backend.seen[1].params.years).toBe('7'); // the columns stay aligned
    expect(screen.getAllByRole('rowheader')).toHaveLength(2);
  });

  it('keeps a bed of a later page on screen after a year was filled in for it', async () => {
    const all = [bed('loc_0', 'Bed 0'), bed('loc_1', 'Bed 1')];
    const seen: Seen[] = [];
    server.use(
      http.get(`${BASE}/sites/:key/rotation-matrix`, ({ request }) => {
        const params = Object.fromEntries(new URL(request.url).searchParams);
        seen.push({ params });
        const offset = Number(params.offset ?? 0);
        return HttpResponse.json({
          site_key: 'site_1',
          years: 7,
          columns: COLUMNS,
          total: 2,
          truncated: false,
          offset,
          limit: 1,
          beds: all.slice(offset, offset + 1),
        });
      }),
    );
    useHistoryBackend();
    const user = userEvent.setup();
    renderPage('grower');

    await user.click(await screen.findByTestId('matrix-more'));
    await waitFor(() => expect(screen.getAllByRole('rowheader')).toHaveLength(2));
    await user.click(screen.getByTestId(`matrix-cell-button-loc_1-${THIS_YEAR - 3}`));
    const dialog = await screen.findByTestId('backfill-dialog');
    await user.click(within(dialog).getByRole('combobox', { name: /Plant family/ }));
    await user.click(await screen.findByRole('option', { name: 'Solanaceae' }));
    const before = seen.length;
    await user.click(within(dialog).getByTestId('backfill-submit'));

    await waitFor(() => expect(seen.length).toBeGreaterThan(before));
    await screen.findByText(`Recorded ${THIS_YEAR - 3} for this bed.`);
    await waitFor(() => expect(screen.getAllByRole('rowheader')).toHaveLength(2));
    // the refresh asked for the first page with the look-back of the first answer, then for the second page
    const refresh = seen.slice(before);
    expect(refresh.map((request) => request.params.offset)).toEqual(['0', '1']);
    expect(refresh[0].params.years).toBe('7');
  });

  it('says the matrix was cut at 500 beds', async () => {
    server.use(
      http.get(`${BASE}/sites/:key/rotation-matrix`, () =>
        HttpResponse.json({
          site_key: 'site_1',
          years: 5,
          columns: COLUMNS,
          total: 500,
          truncated: true,
          offset: 0,
          limit: 50,
          beds: [bed('loc_a', 'Bed')],
        }),
      ),
    );
    renderPage();
    expect(await screen.findByTestId('matrix-truncated')).toHaveTextContent('at most 500 beds');
  });
});

describe('RotationMatrixPage - failure', () => {
  it('shows the error with a retry instead of an empty table', async () => {
    useMatrix([], { fail: true });
    renderPage();
    expect(await screen.findByTestId('error-display')).toBeInTheDocument();
    expect(screen.queryByTestId('rotation-matrix-table')).toBeNull();
  });
});
