import { describe, it, expect, beforeEach, vi } from 'vitest';
import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import i18n from 'i18next';
import { http, HttpResponse } from 'msw';
import { server } from '@/test/mocks/server';
import {
  createStoreWithModuleOverrides,
  createTestStore,
  renderWithProviders,
  type TestStore,
} from '@/test/helpers';
import ModuleGuard from '@/components/common/ModuleGuard';
import { findModuleByPath, moduleCatalog } from '@/config/moduleCatalog';
import DiaryOverviewPage from '@/pages/tagebuch/DiaryOverviewPage';
import type {
  DiaryAnalysisState,
  DiaryOverviewItem,
  PlantDiaryEntry,
  TenantRole,
} from '@/api/types';

/**
 * REQ-050 §2.5.2 — the tenant-wide diary overview.
 *
 * Covers AK-15 (all plants, descending, with every column), AK-16 (five states
 * told apart, `completed` highlighted with a summary preview), AK-17 (state
 * filter including the two shorthands, the remaining filters and the free-text
 * search), AK-19 (a foreign row shows the state but offers no control),
 * AK-27/AK-29 (no progress indication for `requested`, an explicit refresh) and
 * AK-31 (the page hangs off the `diary` module and can be switched off).
 *
 * Every filter assertion checks the **request** the page issued, not the rows
 * left on screen. The endpoint filters, sorts and pages server-side, so a test
 * that only counted visible rows would still pass if the page had quietly
 * narrowed the loaded page locally — which is exactly the bug that makes `total`
 * and the row count disagree.
 */

const TENANT = 'test-tenant';
const OVERVIEW_URL = `/api/v1/t/${TENANT}/diary`;
const PLANTS_URL = `/api/v1/t/${TENANT}/plant-instances`;
const ENTRY_URL = `/api/v1/t/${TENANT}/plant-instances/:plantKey/diary/:entryKey`;
const THUMBNAIL_URL = `/api/v1/t/${TENANT}/attachments/:id/thumbnails/:px`;

function row(overrides: Partial<DiaryOverviewItem> = {}): DiaryOverviewItem {
  return {
    key: 'e1',
    created_at: '2026-08-03T18:22:11Z',
    entry_type: 'observation',
    title: 'Braune Flecken unten',
    excerpt: 'Seit dem Umtopfen hängen die unteren Blätter.',
    tags: ['blatt'],
    plant_key: 'p1',
    plant_name: 'Tomate Beet 2 #05',
    instance_id: 'HOCHBEETA_TOM_05',
    species_name: 'Solanum lycopersicum',
    photo_count: 0,
    preview_photo_id: null,
    analysis_state: 'none',
    analysis_summary: null,
    analysis_error: null,
    analysis_claimed_at: null,
    analyzed_at: null,
    can_request_analysis: true,
    ...overrides,
  };
}

function entry(overrides: Partial<PlantDiaryEntry> = {}): PlantDiaryEntry {
  return {
    key: 'e1',
    plant_key: 'p1',
    entry_type: 'observation',
    title: 'Braune Flecken unten',
    text: 'Seit dem Umtopfen hängen die unteren Blätter.',
    photo_refs: [],
    tags: ['blatt'],
    measurements: null,
    created_by: 'u1',
    created_at: '2026-08-03T18:22:11Z',
    updated_at: '2026-08-03T18:22:11Z',
    analysis_state: 'none',
    analysis_requested_at: null,
    analysis_requested_by: null,
    analysis_claimed_at: null,
    analysis_claimed_by: null,
    analysis_lease_expires_at: null,
    analysis: null,
    analysis_error: null,
    // REQ-013 §2.3a — the fixture defaults to an entry written before the
    // environment snapshot existed, which is the shape most tests here care
    // about; the snapshot tests override it.
    environment: [],
    environment_captured_at: null,
    environment_status: 'not_attempted',
    can_request_analysis: true,
    ...overrides,
  };
}

/** Every request the page made against the overview endpoint, as a URL. */
interface OverviewSpy {
  urls: URL[];
  last: () => URL;
}

/**
 * Register the overview endpoint and record what it was asked for.
 *
 * `listAllPlantInstances` pages until a short page comes back, so an empty
 * plant list answers the dropdown in one request and never loops.
 */
function mockOverview(items: DiaryOverviewItem[], total = items.length): OverviewSpy {
  const spy: OverviewSpy = {
    urls: [],
    last: () => spy.urls[spy.urls.length - 1],
  };
  server.use(
    http.get(OVERVIEW_URL, ({ request }) => {
      spy.urls.push(new URL(request.url));
      return HttpResponse.json({ items, total, limit: 50, offset: 0 });
    }),
    http.get(PLANTS_URL, () => HttpResponse.json([])),
    http.get(THUMBNAIL_URL, () =>
      HttpResponse.arrayBuffer(new Uint8Array([1, 2, 3]).buffer, {
        headers: { 'Content-Type': 'image/webp' },
      }),
    ),
  );
  return spy;
}

function storeWithRole(role: TenantRole): TestStore {
  return createTestStore({
    tenants: {
      activeTenant: {
        key: 't1',
        name: 'Test',
        slug: TENANT,
        tenant_type: 'community',
        description: null,
        avatar_url: null,
        owner_key: 'u1',
        max_members: 5,
        created_at: null,
        updated_at: null,
        role,
      },
      myTenants: [],
      isLoading: false,
      error: null,
    },
  });
}

/** Structured error envelope, exactly as the backend's handlers emit it. */
function apiError(status: number, code: string) {
  return HttpResponse.json(
    {
      error_id: 'e-1',
      error_code: code,
      message: code,
      details: [],
      path: OVERVIEW_URL,
      method: 'POST',
    },
    { status },
  );
}

describe('DiaryOverviewPage (REQ-050 §2.5.2)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    i18n.changeLanguage('de');
  });

  // ── AK-15 ───────────────────────────────────────────────────────────────
  describe('the list itself (AK-15)', () => {
    it('lists the entries of all plants in the order the server sent them', async () => {
      // Two different plants: the point of this page is that they appear
      // together, which no per-plant diary tab can show.
      mockOverview([
        row({ key: 'e1', title: 'Neuester Eintrag', plant_key: 'p1', plant_name: 'Tomate' }),
        row({
          key: 'e2',
          title: 'Älterer Eintrag',
          plant_key: 'p2',
          plant_name: 'Basilikum',
          created_at: '2026-07-01T09:00:00Z',
        }),
      ]);

      renderWithProviders(<DiaryOverviewPage />, { store: storeWithRole('grower') });

      const rows = await screen.findAllByTestId('data-table-row');
      expect(rows).toHaveLength(2);
      expect(within(rows[0]).getByTestId('diary-entry-title')).toHaveTextContent(
        'Neuester Eintrag',
      );
      expect(within(rows[1]).getByTestId('diary-entry-title')).toHaveTextContent(
        'Älterer Eintrag',
      );
      // Two plants, two distinct links — this is the tenant-wide view.
      expect(screen.getByTestId('diary-plant-link-p1')).toBeInTheDocument();
      expect(screen.getByTestId('diary-plant-link-p2')).toBeInTheDocument();
    });

    it('asks for the newest first without being told to', async () => {
      const spy = mockOverview([]);
      renderWithProviders(<DiaryOverviewPage />, { store: storeWithRole('grower') });

      await waitFor(() => expect(spy.urls).toHaveLength(1));
      // §2.5.2: sorting is by capture date, descending, by default. The
      // direction is not a parameter — the endpoint is always descending.
      expect(spy.last().searchParams.get('sort')).toBe('created_at');
    });

    it('renders every column §2.5.2 requires, per row', async () => {
      mockOverview([
        row({
          key: 'e1',
          title: 'Braune Flecken unten',
          entry_type: 'problem',
          photo_count: 2,
          preview_photo_id: 'att-1',
        }),
      ]);

      renderWithProviders(<DiaryOverviewPage />, { store: storeWithRole('grower') });

      const tableRow = await screen.findByTestId('data-table-row');
      // Date, plant (linked), species, type, title/excerpt, photos, analysis.
      expect(within(tableRow).getByTestId('cell-createdAt')).toHaveTextContent('2026');
      expect(within(tableRow).getByTestId('diary-plant-link-p1')).toHaveAttribute(
        'href',
        '/pflanzen/plant-instances/p1',
      );
      expect(within(tableRow).getByTestId('cell-species')).toHaveTextContent(
        'Solanum lycopersicum',
      );
      expect(within(tableRow).getByTestId('diary-entry-type')).toHaveTextContent('Problem');
      expect(within(tableRow).getByTestId('diary-entry-title')).toHaveTextContent(
        'Braune Flecken unten',
      );
      // The photo count with a thumbnail of the first photo.
      const photos = within(tableRow).getByTestId('diary-photo-count');
      expect(photos).toHaveAttribute('data-count', '2');
      expect(await within(photos).findByTestId('diary-photo-preview')).toBeInTheDocument();
      expect(within(tableRow).getByTestId('diary-analysis-cell')).toBeInTheDocument();
    });

    it('renders a row whose created_at is null instead of failing over it', async () => {
      // §2.5.2 makes `created_at` nullable on purpose: one legacy document
      // without a timestamp must not take the whole page down.
      mockOverview([row({ key: 'e1', created_at: null })]);
      renderWithProviders(<DiaryOverviewPage />, { store: storeWithRole('grower') });

      const tableRow = await screen.findByTestId('data-table-row');
      expect(within(tableRow).getByTestId('cell-createdAt')).toHaveTextContent('—');
    });

    it('shows the true match count across all pages, not the loaded page size', async () => {
      mockOverview([row({ key: 'e1' })], 137);
      renderWithProviders(<DiaryOverviewPage />, { store: storeWithRole('grower') });

      await screen.findByTestId('data-table-row');
      expect(await screen.findByText(/137/)).toBeInTheDocument();
    });
  });

  // ── AK-16 ───────────────────────────────────────────────────────────────
  describe('the analysis column (AK-16)', () => {
    it('tells all five states apart visibly', async () => {
      const states: DiaryAnalysisState[] = [
        'none',
        'requested',
        'in_progress',
        'completed',
        'failed',
      ];
      mockOverview(
        states.map((state, index) =>
          row({
            key: `e${index}`,
            analysis_state: state,
            analysis_summary: state === 'completed' ? 'Vermutlich Staunässe.' : null,
            analysis_error: state === 'failed' ? 'Modell nicht erreichbar' : null,
          }),
        ),
      );

      renderWithProviders(<DiaryOverviewPage />, { store: storeWithRole('grower') });

      const cells = await screen.findAllByTestId('diary-analysis-cell');
      expect(cells.map((c) => c.getAttribute('data-state'))).toEqual(states);

      // Each state carries its own wording, so the column is not "result
      // yes/no" with four indistinguishable nos.
      const badges = screen.getAllByTestId('diary-analysis-state');
      const labels = badges.map((b) => b.textContent);
      expect(new Set(labels).size).toBe(5);
    });

    it('highlights completed and previews its summary in one line', async () => {
      mockOverview([
        row({
          key: 'e1',
          analysis_state: 'completed',
          analysis_summary: 'Vermutlich Staunässe nach dem Umtopfen, kein Pilzbefall erkennbar.',
          analyzed_at: '2026-08-04T07:14:52Z',
        }),
        row({ key: 'e2', analysis_state: 'none' }),
      ]);

      renderWithProviders(<DiaryOverviewPage />, { store: storeWithRole('grower') });

      const cells = await screen.findAllByTestId('diary-analysis-cell');
      expect(cells[0]).toHaveAttribute('data-highlighted', 'true');
      expect(cells[1]).toHaveAttribute('data-highlighted', 'false');

      const preview = within(cells[0]).getByTestId('diary-analysis-summary-preview');
      expect(preview).toHaveTextContent('Vermutlich Staunässe nach dem Umtopfen');
      // A preview, not the result: the findings never travel with the row
      // (AK-18), so nothing here may pretend to be the full verdict.
      expect(screen.queryByTestId('diary-analysis-findings')).not.toBeInTheDocument();
    });

    it('names the moment an agent claimed the entry, as a fixed point in time', async () => {
      // §2.5.2 asks the `in_progress` row for "wird analysiert" *with* the
      // moment of claiming. `analyzed_at` is the completion of a run and would
      // be the wrong timestamp here — the server sends the claim separately.
      mockOverview([
        row({
          key: 'e1',
          analysis_state: 'in_progress',
          analysis_claimed_at: '2026-08-04T07:10:00Z',
        }),
      ]);

      renderWithProviders(<DiaryOverviewPage />, { store: storeWithRole('grower') });

      const cell = await screen.findByTestId('diary-analysis-cell');
      expect(within(cell).getByTestId('diary-analysis-state')).toHaveTextContent(
        /Wird analysiert/i,
      );
      const claimed = within(cell).getByTestId('diary-analysis-claimed-at');
      expect(claimed).toHaveTextContent('04.08.2026');

      // A fact, not a forecast: no bar, no spinner, and no "läuft seit …"
      // counting up — an elapsed time reads as progress towards an end nobody
      // here can promise (§3, AK-27, AK-29).
      expect(screen.queryByRole('progressbar')).not.toBeInTheDocument();
      expect(document.querySelector('.MuiLinearProgress-root')).toBeNull();
      expect(document.querySelector('.MuiCircularProgress-root')).toBeNull();
      expect(document.querySelector('.MuiSkeleton-root')).toBeNull();
      expect(cell.textContent).not.toMatch(/seit|noch|verbleib|Minute|%/i);
    });

    it('keeps the running hint legible when no claim time came with the row', async () => {
      // A row whose lease ran out reads as `requested` and carries no claim
      // time at all; a live one may still lack it on a partially written
      // document. Neither is an error state for this cell.
      mockOverview([
        row({ key: 'e1', analysis_state: 'in_progress', analysis_claimed_at: null }),
      ]);

      renderWithProviders(<DiaryOverviewPage />, { store: storeWithRole('grower') });

      const cell = await screen.findByTestId('diary-analysis-cell');
      expect(within(cell).getByTestId('diary-analysis-running-hint')).toHaveTextContent(
        /Agent/i,
      );
      expect(within(cell).queryByTestId('diary-analysis-claimed-at')).not.toBeInTheDocument();
      // No placeholder dash where a timestamp would be — the sentence stands
      // on its own instead of pointing at a hole.
      expect(cell.textContent).not.toContain('—');
    });

    it('shows no claim time on a waiting row', async () => {
      // The server suppresses `analysis_claimed_at` on a row it renders as
      // `requested`, and the cell asks for it only in `in_progress` — so even a
      // client fed a contradictory row cannot print "übernommen am …" next to
      // "wartet auf Analyse".
      mockOverview([
        row({
          key: 'e1',
          analysis_state: 'requested',
          analysis_claimed_at: '2026-08-04T07:10:00Z',
        }),
      ]);

      renderWithProviders(<DiaryOverviewPage />, { store: storeWithRole('grower') });

      const cell = await screen.findByTestId('diary-analysis-cell');
      expect(within(cell).getByTestId('diary-analysis-waiting-hint')).toBeInTheDocument();
      expect(within(cell).queryByTestId('diary-analysis-claimed-at')).not.toBeInTheDocument();
    });

    it('names the reported cause of a failure and offers re-marking', async () => {
      mockOverview([
        row({
          key: 'e1',
          analysis_state: 'failed',
          analysis_error: 'Das Modell hat keine Antwort geliefert.',
        }),
      ]);

      renderWithProviders(<DiaryOverviewPage />, { store: storeWithRole('grower') });

      expect(await screen.findByTestId('diary-analysis-error-preview')).toHaveTextContent(
        'Das Modell hat keine Antwort geliefert.',
      );
      expect(screen.getByTestId('diary-request-analysis')).toHaveTextContent(
        'Erneut analysieren',
      );
    });

    it('marks an entry and renders the state the server answered with', async () => {
      const user = userEvent.setup();
      mockOverview([row({ key: 'e1', analysis_state: 'none' })]);
      server.use(
        http.post(`${ENTRY_URL}/request-analysis`, () =>
          HttpResponse.json(entry({ key: 'e1', analysis_state: 'requested' })),
        ),
      );

      renderWithProviders(<DiaryOverviewPage />, { store: storeWithRole('grower') });

      await user.click(await screen.findByTestId('diary-request-analysis'));

      await waitFor(() =>
        expect(screen.getByTestId('diary-analysis-cell')).toHaveAttribute(
          'data-state',
          'requested',
        ),
      );
      // `requested` is not a state the machine lets a user leave forwards, so
      // no marking control remains on the row.
      expect(screen.queryByTestId('diary-request-analysis')).not.toBeInTheDocument();
    });

    it('reports a refused marking in words and leaves the state alone (AK-18a)', async () => {
      const user = userEvent.setup();
      // The row said `true` and the server still refuses — the flag is a
      // display aid, the endpoint re-evaluates §7.2 on its own.
      mockOverview([row({ key: 'e1', can_request_analysis: true })]);
      server.use(
        http.post(`${ENTRY_URL}/request-analysis`, () => apiError(403, 'PERMISSION_DENIED')),
      );

      renderWithProviders(<DiaryOverviewPage />, { store: storeWithRole('grower') });

      await user.click(await screen.findByTestId('diary-request-analysis'));

      expect(await screen.findByText(/nicht zur Analyse markieren/)).toBeInTheDocument();
      expect(screen.getByTestId('diary-analysis-cell')).toHaveAttribute('data-state', 'none');
    });
  });

  // ── AK-17 ───────────────────────────────────────────────────────────────
  describe('filters and search (AK-17)', () => {
    it('reaches "only with a result" in a single click, with no panel to open', async () => {
      const user = userEvent.setup();
      const spy = mockOverview([]);
      renderWithProviders(<DiaryOverviewPage />, { store: storeWithRole('grower') });

      await waitFor(() => expect(spy.urls).toHaveLength(1));
      // Visible immediately — not behind a "more filters" toggle.
      const chip = screen.getByTestId('diary-quick-filter-completed');
      await user.click(chip);

      await waitFor(() =>
        expect(spy.last().searchParams.getAll('analysis_state')).toEqual(['completed']),
      );
      expect(chip).toHaveAttribute('aria-pressed', 'true');
    });

    it('reaches "only waiting" in a single click', async () => {
      const user = userEvent.setup();
      const spy = mockOverview([]);
      renderWithProviders(<DiaryOverviewPage />, { store: storeWithRole('grower') });

      await waitFor(() => expect(spy.urls).toHaveLength(1));
      await user.click(screen.getByTestId('diary-quick-filter-requested'));

      await waitFor(() =>
        expect(spy.last().searchParams.getAll('analysis_state')).toEqual(['requested']),
      );
    });

    it('goes back to every state via the "all" shorthand', async () => {
      const user = userEvent.setup();
      const spy = mockOverview([]);
      renderWithProviders(<DiaryOverviewPage />, { store: storeWithRole('grower') });

      await waitFor(() => expect(spy.urls).toHaveLength(1));
      await user.click(screen.getByTestId('diary-quick-filter-completed'));
      await waitFor(() => expect(spy.urls).toHaveLength(2));

      await user.click(screen.getByTestId('diary-quick-filter-all'));
      await waitFor(() =>
        expect(spy.last().searchParams.getAll('analysis_state')).toEqual([]),
      );
    });

    it('sends several states as repeated parameters, not as one array key', async () => {
      const user = userEvent.setup();
      const spy = mockOverview([]);
      renderWithProviders(<DiaryOverviewPage />, { store: storeWithRole('grower') });
      await waitFor(() => expect(spy.urls).toHaveLength(1));

      const select = within(screen.getByTestId('diary-filter-analysis-state')).getByRole(
        'combobox',
      );
      await user.click(select);
      await user.click(await screen.findByTestId('diary-filter-analysis-state-option-failed'));
      await user.click(
        await screen.findByTestId('diary-filter-analysis-state-option-in_progress'),
      );

      await waitFor(() =>
        expect(spy.last().searchParams.getAll('analysis_state')).toEqual([
          'failed',
          'in_progress',
        ]),
      );
      // axios would serialise the array as `analysis_state[]=` by default, and
      // FastAPI would then see no filter at all.
      expect(spy.last().search).not.toContain('analysis_state[]');
    });

    it('filters by entry type', async () => {
      const user = userEvent.setup();
      const spy = mockOverview([]);
      renderWithProviders(<DiaryOverviewPage />, { store: storeWithRole('grower') });
      await waitFor(() => expect(spy.urls).toHaveLength(1));

      await user.click(
        within(screen.getByTestId('diary-filter-entry-type')).getByRole('combobox'),
      );
      await user.click(await screen.findByTestId('diary-filter-entry-type-option-problem'));

      await waitFor(() => expect(spy.last().searchParams.get('entry_type')).toBe('problem'));
    });

    it('filters by tag and by period', async () => {
      const user = userEvent.setup();
      const spy = mockOverview([]);
      renderWithProviders(<DiaryOverviewPage />, { store: storeWithRole('grower') });
      await waitFor(() => expect(spy.urls).toHaveLength(1));

      await user.type(within(screen.getByTestId('diary-filter-tag')).getByRole('textbox'), 'blatt');
      await waitFor(() => expect(spy.last().searchParams.get('tag')).toBe('blatt'));

      const from = screen.getByTestId('diary-filter-from').querySelector('input')!;
      await user.type(from, '2026-08-01');
      await waitFor(() => expect(spy.last().searchParams.get('from')).toBe('2026-08-01'));
    });

    it('sends the free-text search to the server, not to the loaded page', async () => {
      const user = userEvent.setup();
      const spy = mockOverview([row({ key: 'e1' })]);
      renderWithProviders(<DiaryOverviewPage />, { store: storeWithRole('grower') });
      await waitFor(() => expect(spy.urls).toHaveLength(1));

      await user.type(
        within(screen.getByTestId('diary-search-input')).getByRole('textbox'),
        'Flecken',
      );

      // The search covers title *and* text of every entry (AK-17) — filtering
      // the 50 rows in memory would silently miss everything on page two.
      await waitFor(() => expect(spy.last().searchParams.get('q')).toBe('Flecken'));
    });

    it('switches the sort field to the analysis time', async () => {
      const user = userEvent.setup();
      const spy = mockOverview([]);
      renderWithProviders(<DiaryOverviewPage />, { store: storeWithRole('grower') });
      await waitFor(() => expect(spy.urls).toHaveLength(1));

      await user.click(within(screen.getByTestId('diary-filter-sort')).getByRole('combobox'));
      await user.click(await screen.findByRole('option', { name: /Analyse-Zeitpunkt/ }));

      await waitFor(() => expect(spy.last().searchParams.get('sort')).toBe('analyzed_at'));
    });

    it('offers a reset that clears the filters and says so instead of "create one"', async () => {
      const user = userEvent.setup();
      // A filtered result with no matches: entries exist, they just do not
      // match — so the "record your first entry" empty state would be a lie,
      // and this page cannot create entries anyway (§2.5.1).
      const spy = mockOverview([]);
      renderWithProviders(<DiaryOverviewPage />, { store: storeWithRole('grower') });
      await waitFor(() => expect(spy.urls).toHaveLength(1));

      await user.click(screen.getByTestId('diary-quick-filter-completed'));
      expect(await screen.findByTestId('no-column-filter-results')).toBeInTheDocument();

      await user.click(screen.getByTestId('diary-reset-filters'));
      await waitFor(() =>
        expect(spy.last().searchParams.getAll('analysis_state')).toEqual([]),
      );
      expect(await screen.findByTestId('empty-state')).toBeInTheDocument();
    });
  });

  // ── AK-19 ───────────────────────────────────────────────────────────────
  describe('other members’ entries (AK-19)', () => {
    it('shows a foreign row’s state but offers no control', async () => {
      mockOverview([
        row({ key: 'mine', analysis_state: 'none', can_request_analysis: true }),
        row({ key: 'theirs', analysis_state: 'requested', can_request_analysis: false }),
      ]);

      renderWithProviders(<DiaryOverviewPage />, { store: storeWithRole('grower') });

      const cells = await screen.findAllByTestId('diary-analysis-cell');
      // The foreign row is present and its state is legible…
      expect(cells[1]).toHaveAttribute('data-state', 'requested');
      expect(within(cells[1]).getByTestId('diary-analysis-state')).toHaveAttribute(
        'data-state',
        'requested',
      );
      // …but it carries no switch, while the own row does.
      expect(within(cells[1]).queryByTestId('diary-request-analysis')).not.toBeInTheDocument();
      expect(within(cells[0]).getByTestId('diary-request-analysis')).toBeInTheDocument();
    });

    it('hides the control on a foreign row even in a state that could be marked', async () => {
      // `completed` + `can_request_analysis: false`: the state would allow a
      // re-run, the server's §7.2 verdict does not. The verdict wins, and the
      // client does not re-derive it from authorship or role.
      mockOverview([
        row({
          key: 'theirs',
          analysis_state: 'completed',
          analysis_summary: 'Alles unauffällig.',
          can_request_analysis: false,
        }),
      ]);

      renderWithProviders(<DiaryOverviewPage />, { store: storeWithRole('viewer') });

      const cell = await screen.findByTestId('diary-analysis-cell');
      expect(within(cell).getByTestId('diary-analysis-summary-preview')).toBeInTheDocument();
      expect(within(cell).queryByTestId('diary-request-analysis')).not.toBeInTheDocument();
    });
  });

  // ── AK-27 / AK-29 ───────────────────────────────────────────────────────
  describe('waiting and refreshing (AK-27, AK-29)', () => {
    it('states that a requested entry is waiting, with no progress indication', async () => {
      mockOverview([row({ key: 'e1', analysis_state: 'requested' })]);

      renderWithProviders(<DiaryOverviewPage />, { store: storeWithRole('grower') });

      const cell = await screen.findByTestId('diary-analysis-cell');
      expect(cell).toHaveAttribute('data-state', 'requested');
      expect(within(cell).getByTestId('diary-analysis-state')).toHaveTextContent(
        /Wartet auf Analyse/i,
      );
      expect(within(cell).getByTestId('diary-analysis-waiting-hint')).toBeInTheDocument();

      // The absence check is the point: the analysing agent runs outside this
      // installation, so a bar — or a spinner, or a shimmering skeleton that
      // reads like one — would assert a duration nobody can promise (§3).
      expect(screen.queryByRole('progressbar')).not.toBeInTheDocument();
      expect(document.querySelector('.MuiLinearProgress-root')).toBeNull();
      expect(document.querySelector('.MuiCircularProgress-root')).toBeNull();
      expect(document.querySelector('.MuiSkeleton-root')).toBeNull();
    });

    it('re-reads the state on demand and does not poll for it', async () => {
      const user = userEvent.setup();
      const spy = mockOverview([row({ key: 'e1', analysis_state: 'requested' })]);

      renderWithProviders(<DiaryOverviewPage />, { store: storeWithRole('grower') });

      // One read when the view opens (§2.5.4).
      await waitFor(() => expect(spy.urls).toHaveLength(1));

      // No server-to-client channel exists, so nothing arrives by itself —
      // and nothing may quietly poll for it either.
      await new Promise((resolve) => setTimeout(resolve, 600));
      expect(spy.urls).toHaveLength(1);

      await user.click(screen.getByTestId('diary-overview-refresh'));
      await waitFor(() => expect(spy.urls).toHaveLength(2));
    });
  });

  // ── the row click ───────────────────────────────────────────────────────
  describe('opening an entry', () => {
    it('opens the full entry with its analysis result on a row click', async () => {
      const user = userEvent.setup();
      mockOverview([
        row({
          key: 'e1',
          analysis_state: 'completed',
          analysis_summary: 'Vermutlich Staunässe.',
        }),
      ]);
      server.use(
        http.get(ENTRY_URL, () =>
          HttpResponse.json(
            entry({
              key: 'e1',
              analysis_state: 'completed',
              analysis: {
                summary: 'Vermutlich Staunässe.',
                findings: [
                  {
                    label: 'Staunässe',
                    confidence: 0.72,
                    rationale: 'Substrat riecht sauer, untere Blätter hängen.',
                  },
                ],
                recommended_actions: ['Weniger gießen'],
                disclaimer: 'Hypothese eines Sprachmodells.',
                model: 'demo-model',
                recipe_version: '1.0.0',
                analyzed_at: '2026-08-04T07:14:52Z',
                analyzed_photo_ids: [],
              },
            }),
          ),
        ),
      );

      renderWithProviders(<DiaryOverviewPage />, { store: storeWithRole('grower') });

      await user.click(await screen.findByTestId('data-table-row'));

      const dialog = await screen.findByTestId('diary-entry-detail-dialog');
      // Only the single read carries the findings and the disclaimer — the row
      // never does (AK-18, AK-20).
      expect(await within(dialog).findByTestId('diary-analysis-result')).toBeInTheDocument();
      expect(within(dialog).getByTestId('diary-analysis-disclaimer')).toBeInTheDocument();
      expect(within(dialog).getByTestId('diary-detail-open-plant')).toHaveAttribute(
        'href',
        '/pflanzen/plant-instances/p1',
      );
    });

    it('does not open the entry when the plant link is followed', async () => {
      const user = userEvent.setup();
      mockOverview([row({ key: 'e1' })]);
      renderWithProviders(<DiaryOverviewPage />, { store: storeWithRole('grower') });

      await user.click(await screen.findByTestId('diary-plant-link-p1'));
      expect(screen.queryByTestId('diary-entry-detail-dialog')).not.toBeInTheDocument();
    });
  });

  // ── AK-31 ───────────────────────────────────────────────────────────────
  describe('module registration (AK-31)', () => {
    it('is owned by a non-core module named diary', () => {
      const owner = findModuleByPath('/tagebuch');
      expect(owner?.key).toBe('diary');
      // `core: true` would be exactly the nav entry a user cannot get rid of,
      // which is what AK-31 rules out.
      expect(owner?.core).toBe(false);
      expect(moduleCatalog.diary.category).toBe('care_planning');
      expect(moduleCatalog.diary.defaultLevel).toBe('beginner');
      expect(moduleCatalog.diary.requiresSmartHome).toBe(false);
    });

    it('renders for a beginner without any override', async () => {
      mockOverview([row({ key: 'e1' })]);
      renderWithProviders(
        <ModuleGuard>
          <DiaryOverviewPage />
        </ModuleGuard>,
        { store: createStoreWithModuleOverrides('beginner', {}), route: '/tagebuch' },
      );

      expect(await screen.findByTestId('diary-overview-page')).toBeInTheDocument();
      expect(screen.queryByTestId('module-guard-hint')).not.toBeInTheDocument();
    });

    it('disappears behind the reactivation hint when the module is switched off', async () => {
      const spy = mockOverview([row({ key: 'e1' })]);
      renderWithProviders(
        <ModuleGuard>
          <DiaryOverviewPage />
        </ModuleGuard>,
        {
          store: createStoreWithModuleOverrides('expert', { diary: 'disabled' }),
          route: '/tagebuch',
        },
      );

      expect(await screen.findByTestId('module-guard-hint')).toBeInTheDocument();
      expect(screen.queryByTestId('diary-overview-page')).not.toBeInTheDocument();
      // Not merely hidden: the page never mounted, so it never asked either.
      expect(spy.urls).toHaveLength(0);
    });
  });
});
