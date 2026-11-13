/**
 * REQ-053 WP 9.2 (#2742), GP-UX-024 part 1 — the views that read the plan cache when offline, through
 * the production components and a real IndexedDB (`fake-indexeddb`):
 *
 * - planning mode: an online load writes the cache; offline the plan is read from it, drawn read-only
 *   with the "Stand von hh:mm" banner, and the geometry tools are locked with a hint (no editor, no
 *   import/export); a site never loaded online shows the empty state with a hint;
 * - field mode: bed list and map from the cache with the banner; a miss is an empty state, not an error;
 * - bed view (plan tab): cached plan with the banner, plant moves locked; miss as empty state.
 *
 * The site list is covered in `src/test/pages/SiteListPageOffline.test.tsx` (features never import pages).
 */
import 'fake-indexeddb/auto';
import { configureStore } from '@reduxjs/toolkit';
import { act, cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { http, HttpResponse } from 'msw';
import { Provider } from 'react-redux';
import { RouterProvider, createMemoryRouter } from 'react-router-dom';
import { SnackbarProvider } from 'notistack';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import GardenPlanRoute from '@/features/gardenPlanner/routes/GardenPlanRoute';
import { rootReducer } from '@/store/rootReducer';
import { bed, planResponse } from '@/test/gardenPlanFixtures';
import { authState, createTestStore, renderWithProviders, tenantState } from '@/test/helpers';
import { server } from '@/test/mocks/server';
import { emptyPlanCache } from '@/test/planCacheTestKit';
import { ThemeContextProvider } from '@/theme';
import BedPlanTab from '../bed/BedPlanTab';
import BedView from '../bed/BedView';
import { bedListItem, bedSummary } from '../bed/bedTestKit';
import { careTask } from '../care/careTestKit';
import { applyAction, selectGardenPlanState } from '../state/gardenPlanSlice';
// A bed sheet is seeded with `complete: true`: `storedProjection('bedSheets')` stores only a complete answer.
import { bedListEntry, bedSheetEntry, planEntry, readCached, writeCached, type CacheScope } from './planCache';
import { requestLanguage } from '@/api/client';

const BASE = '/api/v1/t/:tenant';
/** `authState()` signs in `user-1`, `tenantState()` makes `tenant-1` active. */
const SCOPE: CacheScope = { userKey: 'user-1', tenantKey: 'tenant-1' };
const OTHER_TENANT: CacheScope = { userKey: 'user-1', tenantKey: 'tenant-2' };
const CACHED_AT = Date.now() - 5 * 60 * 1000;
/** The bed sheet's cache entry in the language the sheet reads in (the key carries it, #2902). */
const sheetEntry = () => bedSheetEntry(SCOPE, 'loc_b03', requestLanguage());

const PLAN = planResponse({
  locations: [bed('loc_b03', 1, 1), bed('loc_b04', 4, 1)],
  garden_objects: [],
  slots: [{ key: 's1', slot_id: 'A1', location_key: 'loc_b03', plan_geometry: { origin: [1.3, 1.3] } }],
  plants: [{ key: 'pl_1', instance_id: 'TOM-1', species_key: 'sp_tomato', slot_key: 's1' }],
});
const BEDS = [bedListItem('loc_b03', { name: 'Raised bed 3' }), bedListItem('loc_b04', { name: 'Herb spiral' })];

function stamp(at: number): string {
  return new Intl.DateTimeFormat('en', { hour: '2-digit', minute: '2-digit' }).format(new Date(at));
}

function setOnline(value: boolean) {
  Object.defineProperty(window.navigator, 'onLine', { configurable: true, get: () => value });
  act(() => {
    window.dispatchEvent(new Event(value ? 'online' : 'offline'));
  });
}

let requests: string[];
/** Reads of the assignments (bed list, field mode): not offline data, counted apart. */
let assignmentReads = 0;

/** The server; offline nothing of it may be needed for the plan, the bed list or the site list. */
function useBackend() {
  requests = [];
  assignmentReads = 0;
  server.use(
    http.get(`${BASE}/sites/:key/plan`, () => {
      requests.push('plan');
      return HttpResponse.json(PLAN);
    }),
    http.get(`${BASE}/locations`, () => {
      requests.push('beds');
      return HttpResponse.json(BEDS);
    }),
    http.get(`${BASE}/locations/:key/plant-states`, () => HttpResponse.json([])),
    http.get(`${BASE}/tasks/queue`, () => {
      requests.push('sheet');
      return HttpResponse.json([careTask('t_live', { name: 'Live task', entity_key: 'loc_b03' })]);
    }),
    http.get('/api/v1/tenants/:slug/members', () => HttpResponse.json([])),
    http.get('/api/v1/tenants/:slug/assignments', () => {
      assignmentReads += 1;
      return HttpResponse.json([]);
    }),
    http.get('/api/v1/growth-phases/:key', () => HttpResponse.json({ key: 'ph', name: 'Vegetative' })),
  );
}

function renderPlan(mode: 'plan' | 'field', role: 'viewer' | 'grower' | 'lead' = 'lead') {
  const store = configureStore({ reducer: rootReducer, preloadedState: { ...tenantState(role), ...authState() } as never });
  const router = createMemoryRouter(
    [{ path: 'standorte/sites/:key/plan', element: <GardenPlanRoute /> }],
    { initialEntries: [`/standorte/sites/site_1/plan?mode=${mode}`] },
  );
  const view = render(
    <Provider store={store}>
      <ThemeContextProvider>
        <SnackbarProvider>
          <RouterProvider router={router} />
        </SnackbarProvider>
      </ThemeContextProvider>
    </Provider>,
  );
  return { ...view, store };
}

/** `navigator.onLine` turns true without the `online` event: only a click can read again. */
function setOnlineSilently(value: boolean) {
  Object.defineProperty(window.navigator, 'onLine', { configurable: true, get: () => value });
}

beforeEach(async () => {
  localStorage.clear();
  await emptyPlanCache();
  useBackend();
});

afterEach(() => {
  // Unmount first: a view coming back online would read from the server again and write the cache.
  cleanup();
  setOnline(true);
});

describe('planning mode', () => {
  it('writes the plan into the cache after an online load, and reads it from there offline', async () => {
    renderPlan('plan');
    expect(await screen.findByRole('toolbar', { name: 'Garden plan tools' })).toBeInTheDocument();
    await waitFor(async () => expect(await readCached(planEntry(SCOPE, 'site_1'))).not.toBeNull());
    expect(screen.queryByTestId('offline-cached-banner')).toBeNull();
    cleanup();

    setOnline(false);
    requests.length = 0;
    renderPlan('plan');
    expect(await screen.findByTestId('garden-plan-read-only')).toBeInTheDocument();
    expect(screen.getByTestId('offline-cached-banner')).toHaveTextContent(/as of \d{2}:\d{2}/);
    expect(requests).toEqual([]);
  });

  it('shows "as of hh:mm" and locks the geometry tools with a hint, not an error', async () => {
    await writeCached(planEntry(SCOPE, 'site_1'), PLAN, CACHED_AT);
    setOnline(false);
    renderPlan('plan');

    const banner = await screen.findByTestId('offline-cached-banner');
    expect(banner).toHaveTextContent(stamp(CACHED_AT));
    expect(screen.getByTestId('garden-plan-geometry-locked')).toHaveTextContent('Drawing, moving and transplanting are locked');
    // No editor: no tool bar, no import/export, no "add the first bed"; and no error.
    expect(screen.queryByRole('toolbar', { name: 'Garden plan tools' })).toBeNull();
    expect(screen.queryByTestId('garden-plan-io-menu')).toBeNull();
    expect(screen.queryByTestId('error-display')).toBeNull();
    expect(screen.getByTestId('garden-plan-read-only').querySelector('svg')).not.toBeNull();
  });

  it('also stays read-only when the browser believes it is online but the request got no answer', async () => {
    await writeCached(planEntry(SCOPE, 'site_1'), PLAN, CACHED_AT);
    server.use(http.get(`${BASE}/sites/:key/plan`, () => HttpResponse.error()));
    renderPlan('plan');
    expect(await screen.findByTestId('garden-plan-read-only')).toBeInTheDocument();
    expect(screen.getByTestId('offline-cached-banner')).toHaveTextContent(stamp(CACHED_AT));
    expect(screen.queryByRole('toolbar', { name: 'Garden plan tools' })).toBeNull();
  });

  it('reads the plan from the server again once the connection is back, and unlocks the editor', async () => {
    await writeCached(planEntry(SCOPE, 'site_1'), PLAN, CACHED_AT);
    setOnline(false);
    renderPlan('plan');
    await screen.findByTestId('garden-plan-read-only');
    expect(requests).toEqual([]);
    setOnline(true);
    expect(await screen.findByRole('toolbar', { name: 'Garden plan tools' })).toBeInTheDocument();
    // The plan once; the bed list below the editor is back as well.
    expect(requests.filter((request) => request === 'plan')).toEqual(['plan']);
    expect(screen.queryByTestId('offline-cached-banner')).toBeNull();
  });

  it('a cache miss offline is an empty state with a hint', async () => {
    // Another tenant's plan of the same site key is no hit for this one.
    await writeCached(planEntry(OTHER_TENANT, 'site_1'), PLAN, CACHED_AT);
    setOnline(false);
    renderPlan('plan');
    const miss = await screen.findByTestId('garden-plan-offline-miss');
    expect(within(miss).getByText('This plan is not available offline')).toBeInTheDocument();
    expect(miss).toHaveTextContent('Open the page once with a connection');
    expect(screen.queryByTestId('error-display')).toBeNull();
    expect(screen.queryByTestId('offline-cached-banner')).toBeNull();
  });
});

describe('planning mode: a short outage (#2789 review C6, C2)', () => {
  it('keeps the editor mounted, locks it with a hint and refuses edits until the connection is back', async () => {
    const { store } = renderPlan('plan');
    const toolbar = await screen.findByRole('toolbar', { name: 'Garden plan tools' });
    setOnline(false);
    // Same editor, still there: tool, selection and unsaved edits survive.
    expect(screen.getByRole('toolbar', { name: 'Garden plan tools' })).toBe(toolbar);
    expect(await screen.findByTestId('garden-plan-geometry-locked')).toBeInTheDocument();
    expect(screen.queryByTestId('garden-plan-read-only')).toBeNull();
    act(() => {
      store.dispatch(applyAction([{ op: 'delete', entity: 'location', key: 'loc_b04' }]));
    });
    const state = selectGardenPlanState(store.getState() as never);
    expect(state.editError).toBe('plan.offline');
    expect(state.pending).toEqual([]);
    setOnline(true);
    await waitFor(() => expect(screen.queryByTestId('garden-plan-geometry-locked')).toBeNull());
    act(() => {
      store.dispatch(applyAction([{ op: 'delete', entity: 'location', key: 'loc_b04' }]));
    });
    expect(selectGardenPlanState(store.getState() as never).pending).toHaveLength(1);
  });

  it('reads a missed plan once the connection is back', async () => {
    setOnline(false);
    renderPlan('plan');
    await screen.findByTestId('garden-plan-offline-miss');
    setOnline(true);
    expect(await screen.findByRole('toolbar', { name: 'Garden plan tools' })).toBeInTheDocument();
    // The bed list below the editor is back too; let its reads finish inside this test.
    await waitFor(() => expect(assignmentReads).toBeGreaterThan(0));
  });

  it('offers "try again" on a miss', async () => {
    setOnline(false);
    renderPlan('plan');
    const miss = await screen.findByTestId('garden-plan-offline-miss');
    setOnlineSilently(true);
    fireEvent.click(within(miss).getByTestId('empty-state-action'));
    expect(await screen.findByRole('toolbar', { name: 'Garden plan tools' })).toBeInTheDocument();
    await waitFor(() => expect(assignmentReads).toBeGreaterThan(0));
  });
});

describe('field mode', () => {
  it('reads the bed list and the map from the cache with the banner', async () => {
    await writeCached(bedListEntry(SCOPE, 'site_1'), BEDS, CACHED_AT);
    await writeCached(planEntry(SCOPE, 'site_1'), PLAN, CACHED_AT + 60_000);
    setOnline(false);
    renderPlan('field');

    const list = await screen.findByTestId('field-bed-list');
    expect(within(list).getByText('Herb spiral')).toBeInTheDocument();
    // The older of the two states is the one the banner names.
    expect(screen.getByTestId('offline-cached-banner')).toHaveTextContent(stamp(CACHED_AT));
    fireEvent.click(screen.getByTestId('field-tab-map'));
    expect(await screen.findByTestId('field-map')).toBeInTheDocument();
    expect(requests).toEqual([]);
  });

  it('reads list and plan from the server again once the connection is back', async () => {
    await writeCached(bedListEntry(SCOPE, 'site_1'), BEDS, CACHED_AT);
    await writeCached(planEntry(SCOPE, 'site_1'), PLAN, CACHED_AT);
    setOnline(false);
    renderPlan('field');
    await screen.findByTestId('offline-cached-banner');
    setOnline(true);
    await waitFor(() => expect([...requests].sort()).toEqual(['beds', 'plan']));
    await waitFor(() => expect(screen.queryByTestId('offline-cached-banner')).toBeNull());
  });

  it('a cache miss offline is an empty state with a hint on both tabs', async () => {
    setOnline(false);
    renderPlan('field');
    const miss = await screen.findByTestId('field-list-offline-miss');
    expect(miss).toHaveTextContent('The beds are not available offline');
    expect(screen.queryByTestId('error-display')).toBeNull();
    fireEvent.click(screen.getByTestId('field-tab-map'));
    expect(await screen.findByTestId('field-map-offline-miss')).toHaveTextContent('This plan is not available offline');
  });

  it('writes the bed list into the cache after an online read', async () => {
    renderPlan('field');
    await screen.findByTestId('field-bed-list');
    await waitFor(async () => expect((await readCached(bedListEntry(SCOPE, 'site_1')))?.data).toEqual(BEDS));
  });
});

describe('bed view (plan tab)', () => {
  function renderTab() {
    return renderWithProviders(<BedPlanTab bed={bedSummary()} planLinkVisible />, {
      store: createTestStore({ ...tenantState('grower'), ...authState() }),
    });
  }

  it('reads the cached plan offline and locks moving a plant with a hint', async () => {
    // The tab reads the plan with its plants: its own record, not the plain plan's (#2789 review C1).
    await writeCached(planEntry(SCOPE, 'site_1'), { ...PLAN, plants: [] }, CACHED_AT);
    await writeCached(planEntry(SCOPE, 'site_1', ['plants']), PLAN, CACHED_AT);
    setOnline(false);
    const { container } = renderTab();

    expect(await screen.findByTestId('offline-cached-banner')).toHaveTextContent(stamp(CACHED_AT));
    const marker = await waitFor(() => {
      const element = container.querySelector('g[data-plan-key="pl_1"]');
      expect(element).not.toBeNull();
      return element as SVGGElement;
    });
    fireEvent.keyDown(marker, { key: 'Enter' });
    await screen.findByTestId('bed-plan-plant-panel');
    expect(screen.getByTestId('bed-plan-correct')).toBeDisabled();
    expect(screen.getByTestId('bed-plan-transplant')).toBeDisabled();
    expect(screen.getByTestId('bed-plan-geometry-locked')).toHaveTextContent('locked');
    expect(requests).toEqual([]);
  });

  it('reads the plan again once the connection is back: banner gone, moves unlocked', async () => {
    await writeCached(planEntry(SCOPE, 'site_1', ['plants']), PLAN, CACHED_AT);
    setOnline(false);
    renderTab();
    await screen.findByTestId('offline-cached-banner');
    setOnline(true);
    await waitFor(() => expect(screen.queryByTestId('offline-cached-banner')).toBeNull());
    expect(requests).toContain('plan');
  });

  it('a cache miss offline is an empty state, not an error', async () => {
    setOnline(false);
    renderTab();
    expect(await screen.findByTestId('bed-plan-offline-miss')).toHaveTextContent('This plan is not available offline');
    expect(screen.queryByTestId('error-display')).toBeNull();
  });
});

describe('field-mode bed sheet', () => {
  async function openBed(name: string) {
    const list = await screen.findByTestId('field-bed-list');
    fireEvent.click(within(list).getByText(name).closest('button')!);
    return screen.findByTestId('field-bed-sheet');
  }

  it('reads tasks and plants from the cache offline, with the banner and every write but the buffered note locked', async () => {
    await writeCached(bedListEntry(SCOPE, 'site_1'), BEDS, CACHED_AT);
    await writeCached(planEntry(SCOPE, 'site_1'), PLAN, CACHED_AT);
    await writeCached(
      sheetEntry(),
      { tasks: [careTask('t_cached', { name: 'Cached task', entity_key: 'loc_b03' })], plants: [], complete: true },
      CACHED_AT,
    );
    setOnline(false);
    renderPlan('field', 'grower');
    const sheet = await openBed('Raised bed 3');
    expect(await within(sheet).findByTestId('field-sheet-cached-banner')).toHaveTextContent(stamp(CACHED_AT));
    expect(within(sheet).getByText('Cached task')).toBeInTheDocument();
    // WP 9.4: offline the note goes into the write buffer; every other chip needs the server.
    for (const chip of within(sheet).getAllByRole('button').filter((b) => b.dataset.testid?.startsWith('field-chip-'))) {
      if (chip.dataset.testid === 'field-chip-note') expect(chip).toBeEnabled();
      else expect(chip).toBeDisabled();
    }
    expect(requests).toEqual([]);
  });

  it('lie-fi: online with a cached sheet, "Done" and the note are BUFFERED, never sent directly; the read is retried', async () => {
    const { emptyWriteQueue } = await import('@/test/writeQueueTestKit');
    const { listEntries } = await import('./queue');
    await emptyWriteQueue();
    await writeCached(
      sheetEntry(),
      { tasks: [careTask('t_cached', { name: 'Cached task', entity_key: 'loc_b03' })], plants: [], complete: true },
      CACHED_AT,
    );
    let reads = 0;
    let releaseRetry: () => void = () => undefined;
    const completes: unknown[] = [];
    server.use(
      http.get(`${BASE}/tasks/queue`, async () => {
        reads += 1;
        // Read 1: the sheet; read 2: the existing re-read once a cached sheet shows (WP 9.2); read 3: the retry.
        if (reads === 3) {
          await new Promise<void>((resolve) => {
            releaseRetry = resolve;
          });
        }
        return HttpResponse.error();
      }),
      http.post(`${BASE}/tasks/:key/complete`, async ({ request }) => {
        completes.push(await request.json());
        return HttpResponse.json({});
      }),
    );
    renderPlan('field', 'grower');
    const sheet = await openBed('Raised bed 3');
    await within(sheet).findByTestId('field-sheet-cached-banner');
    // The browser says online, the read got no answer: the buffered actions work, the server-only ones wait.
    await waitFor(() => {
      expect(within(sheet).getByTestId('field-done-t_cached')).toBeEnabled();
      expect(within(sheet).getByTestId('field-chip-note')).toBeEnabled();
      expect(within(sheet).getByTestId('field-chip-watering')).toBeDisabled();
    });

    // No online/offline flip ever comes: the sheet retries the read by itself (2 s first) and locks meanwhile.
    await waitFor(() => expect(reads).toBe(3), { timeout: 5000 });
    await waitFor(() => expect(within(sheet).getByTestId('field-done-t_cached')).toBeDisabled());
    act(() => releaseRetry());
    await waitFor(() => expect(within(sheet).getByTestId('field-done-t_cached')).toBeEnabled());

    fireEvent.click(within(sheet).getByTestId('field-done-t_cached'));
    fireEvent.click(within(await screen.findByTestId('care-complete-dialog')).getByTestId('care-complete-submit'));
    await within(sheet).findByTestId('field-done-queued-t_cached');
    expect(completes).toEqual([]); // nothing went to the server against the snapshot
    const [entry] = await listEntries(SCOPE);
    expect(entry.write).toMatchObject({ kind: 'complete', taskKey: 't_cached' });
  });

  it('a cache miss offline is an empty state, not an error', async () => {
    await writeCached(bedListEntry(SCOPE, 'site_1'), BEDS, CACHED_AT);
    setOnline(false);
    renderPlan('field');
    const sheet = await openBed('Raised bed 3');
    expect(await within(sheet).findByTestId('field-sheet-offline-miss')).toHaveTextContent('This bed is not available offline');
    expect(within(sheet).queryByTestId('error-display')).toBeNull();
  });

  it('writes the sheet into the cache after an online read, without the person-related fields', async () => {
    server.use(
      http.get(`${BASE}/tasks/queue`, () =>
        HttpResponse.json([
          careTask('t_live', {
            name: 'Live task',
            entity_key: 'loc_b03',
            assigned_to_user_key: 'user-7',
            completion_notes: 'note',
            photo_refs: ['att_1'],
          }),
        ]),
      ),
    );
    renderPlan('field');
    const sheet = await openBed('Raised bed 3');
    await within(sheet).findByText('Live task');
    await waitFor(async () =>
      expect((await readCached<{ tasks: Record<string, unknown>[] }>(sheetEntry()))?.data.tasks[0]).toMatchObject(
        { name: 'Live task', assigned_to_user_key: null, completion_notes: null, photo_refs: [] },
      ),
    );
  });

  it('never writes a partial sheet over a good one (plant states failed)', async () => {
    await writeCached(sheetEntry(), { tasks: [], plants: [{ plant_key: 'pl_good' }], complete: true }, CACHED_AT);
    server.use(http.get(`${BASE}/locations/:key/plant-states`, () => HttpResponse.json({}, { status: 500 })));
    renderPlan('field');
    const sheet = await openBed('Raised bed 3');
    await within(sheet).findByText('Live task');
    await new Promise((resolve) => setTimeout(resolve, 100));
    expect((await readCached<{ plants: { plant_key: string }[] }>(sheetEntry()))?.data.plants).toEqual([
      { plant_key: 'pl_good', cover_photo_ref: null },
    ]);
  });

  it('reads a cached sheet again once the connection is back, and unlocks the writes', async () => {
    await writeCached(bedListEntry(SCOPE, 'site_1'), BEDS, CACHED_AT);
    await writeCached(planEntry(SCOPE, 'site_1'), PLAN, CACHED_AT);
    await writeCached(
      sheetEntry(),
      { tasks: [careTask('t_cached', { name: 'Cached task', entity_key: 'loc_b03' })], plants: [], complete: true },
      CACHED_AT,
    );
    setOnline(false);
    renderPlan('field', 'grower');
    const sheet = await openBed('Raised bed 3');
    await within(sheet).findByTestId('field-sheet-cached-banner');
    setOnline(true);
    expect(await within(sheet).findByText('Live task')).toBeInTheDocument();
    expect(within(sheet).queryByTestId('field-sheet-cached-banner')).toBeNull();
    const chips = within(sheet).getAllByRole('button').filter((b) => b.dataset.testid?.startsWith('field-chip-'));
    expect(chips.some((chip) => !chip.hasAttribute('disabled'))).toBe(true);
  });

  it('reads a missed sheet once the connection is back', async () => {
    await writeCached(bedListEntry(SCOPE, 'site_1'), BEDS, CACHED_AT);
    setOnline(false);
    renderPlan('field');
    const sheet = await openBed('Raised bed 3');
    await within(sheet).findByTestId('field-sheet-offline-miss');
    setOnline(true);
    expect(await within(sheet).findByText('Live task')).toBeInTheDocument();
  });
});

describe('bed view with a cached summary', () => {
  it('shows the banner and locks every edit of the bed with a hint', async () => {
    renderWithProviders(
      <BedView summary={bedSummary()} cachedAt={CACHED_AT} details={<div />} onReload={() => undefined} />,
      { store: createTestStore({ ...tenantState('lead'), ...authState() }), route: '/standorte/locations/loc_b03#soil' },
    );
    expect(await screen.findByTestId('bed-view-cached-banner')).toHaveTextContent(stamp(CACHED_AT));
    expect(screen.getByTestId('bed-view-edits-locked')).toBeInTheDocument();
    expect(screen.queryByTestId('bed-status-change-button')).toBeNull();
    expect(screen.queryByTestId('bed-sun-change-button')).toBeNull();
    expect(screen.queryByTestId('bed-site-change-button')).toBeNull();
  });

  it('offers the edits when the summary is live and the browser online', async () => {
    renderWithProviders(<BedView summary={bedSummary()} details={<div />} onReload={() => undefined} />, {
      store: createTestStore({ ...tenantState('lead'), ...authState() }),
      route: '/standorte/locations/loc_b03#soil',
    });
    expect(await screen.findByTestId('bed-status-change-button')).toBeInTheDocument();
    expect(screen.queryByTestId('bed-view-edits-locked')).toBeNull();
  });
});
