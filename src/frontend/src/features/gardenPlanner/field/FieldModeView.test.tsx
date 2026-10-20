/**
 * Field mode (REQ-053 WP 5.1, §18): the list first and the geometry after it, the bed sheet, "Done" in two
 * taps (GP-ACC-029), the one-tap chip with its undo (GP-ACC-048), the offline lock, the read-only viewer,
 * the map tab, the 10 cm stepper, the device memory and the axe pass.
 */
import { configureStore } from '@reduxjs/toolkit';
import { act, cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { Provider } from 'react-redux';
import { RouterProvider, createMemoryRouter } from 'react-router-dom';
import { SnackbarProvider } from 'notistack';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import GardenPlanRoute from '@/features/gardenPlanner/routes/GardenPlanRoute';
import { expectNoA11yViolations } from '@/test/a11y/expectNoA11yViolations';
import { bed, planResponse } from '@/test/gardenPlanFixtures';
import { authState, tenantState } from '@/test/helpers';
import { rootReducer } from '@/store/rootReducer';
import { server } from '@/test/mocks/server';
import { ThemeContextProvider } from '@/theme';
import { KIOSK_TOUCH_TARGET } from '@/kiosk/kioskTheme';
import { bedListItem } from '../bed/bedTestKit';
import type { BedListItem } from '../bed/types';
import { BASE, careTask, useCareBackend } from '../care/careTestKit';
import type { CareTask } from '../care/careTypes';
import { normalizePlan } from '../model/planModel';
import type { PlantStateWire } from '../planting/plantStateApi';
import { fitViewport, planContentBounds } from '../routes/fitViewport';
import { FIELD_PREFS_KEY, readFieldPrefs } from './fieldPrefs';

const PAST = '2020-01-01T00:00:00Z';
const FUTURE = '2099-01-01T00:00:00Z';
const TODAY = `${new Date().toISOString().slice(0, 10)}T12:00:00Z`;

const BEDS: BedListItem[] = [
  bedListItem('loc_b', { name: 'Herb spiral', overdue_task_count: 0, next_due_at: FUTURE }),
  bedListItem('loc_a', { name: 'Raised bed 1', overdue_task_count: 1, open_task_count: 2 }),
  bedListItem('loc_c', { name: 'Allotment', overdue_task_count: 0, next_due_at: TODAY }),
];

function plantState(key: string, overrides: Partial<PlantStateWire> = {}): PlantStateWire {
  return {
    plant_key: key,
    slot_key: `slot_${key}`,
    instance_id: key.toUpperCase(),
    species_key: 'sp_tomato',
    species_name: 'Tomato',
    planted_on: '2026-05-01',
    lifecycle: 'active',
    phase: { key: 'ph_flower', name: 'Flowering', elapsed_d: 10 },
    last_care: {},
    attention: [],
    harvest: { ready: false },
    inputs: { open_tasks: [], open_findings: 0, frost_risk: false, harvest_batches: 0 },
    ...overrides,
  };
}

interface Backend {
  requests: string[];
  releaseList: () => void;
  releaseAssignments: () => void;
  /** From now on the bed list answers with a server error (a failed reload). */
  failList: () => void;
}

function useFieldBackend({
  beds = BEDS,
  tasks = [careTask('t_water', { name: 'Water the bed', category: 'watering', entity_key: 'loc_a', due_date: PAST })],
  plants = [plantState('pl_1'), plantState('pl_2')],
  holdList = false,
  holdAssignments = false,
}: {
  beds?: BedListItem[];
  tasks?: CareTask[];
  plants?: PlantStateWire[];
  holdList?: boolean;
  holdAssignments?: boolean;
} = {}) {
  const care = useCareBackend(tasks);
  const list = { fails: false };
  const backend: Backend = {
    requests: [],
    releaseList: () => undefined,
    releaseAssignments: () => undefined,
    failList: () => {
      list.fails = true;
    },
  };
  const gate = holdList
    ? new Promise<void>((resolve) => {
        backend.releaseList = resolve;
      })
    : Promise.resolve();
  const assignmentGate = holdAssignments
    ? new Promise<void>((resolve) => {
        backend.releaseAssignments = resolve;
      })
    : Promise.resolve();
  server.use(
    http.get(`${BASE}/locations`, async () => {
      backend.requests.push('list');
      await gate;
      if (list.fails) return HttpResponse.json({ detail: 'Internal error' }, { status: 500 });
      return HttpResponse.json(beds);
    }),
    http.get(`${BASE}/sites/:key/plan`, () => {
      backend.requests.push('plan');
      return HttpResponse.json(
        planResponse({
          locations: [bed('loc_a', 1, 1), bed('loc_b', 4, 1), bed('loc_c', 8, 1)],
          garden_objects: [],
          slots: [],
          plants: [],
        }),
      );
    }),
    http.get(`${BASE}/locations/:key/plant-states`, () => HttpResponse.json(plants)),
    http.get('/api/v1/tenants/:slug/members', () =>
      HttpResponse.json([{ key: 'm_1', user_key: 'user-1', display_name: 'Tester' }]),
    ),
    http.get('/api/v1/tenants/:slug/assignments', async () => {
      await assignmentGate;
      return HttpResponse.json([{ key: 'as_1', membership_key: 'm_1', location_key: 'loc_b' }]);
    }),
  );
  return { ...care, backend };
}

function renderField(role: 'viewer' | 'grower' | 'lead' = 'grower', route = '/standorte/sites/site_1/plan?mode=field') {
  // The real root reducer: the plan slice is injected into it lazily, as in the app.
  const store = configureStore({ reducer: rootReducer, preloadedState: { ...tenantState(role), ...authState() } as never });
  const router = createMemoryRouter(
    [
      { path: 'standorte/sites/:key/plan', element: <GardenPlanRoute /> },
      { path: 'standorte/sites/:key', element: <div data-testid="site-detail-stub" /> },
    ],
    { initialEntries: [route] },
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
  return { store, router, ...view };
}

function setOnline(value: boolean) {
  Object.defineProperty(window.navigator, 'onLine', { configurable: true, get: () => value });
  act(() => {
    window.dispatchEvent(new Event(value ? 'online' : 'offline'));
  });
}

async function openBed(name: string) {
  const list = await screen.findByTestId('field-bed-list');
  fireEvent.click(within(list).getByText(name).closest('button')!);
  return screen.findByTestId('field-bed-sheet');
}

beforeEach(() => localStorage.clear());
afterEach(() => {
  setOnline(true);
  cleanup();
});

describe('field mode entry', () => {
  it('loads the bed list first and the plan geometry only after it answered (GP-UX-030)', async () => {
    const { backend } = useFieldBackend({ holdList: true });
    renderField();
    expect(await screen.findByTestId('garden-plan-field-mode')).toBeInTheDocument();
    await waitFor(() => expect(backend.requests).toEqual(['list']));
    act(() => backend.releaseList());
    await screen.findByTestId('field-bed-list');
    await waitFor(() => expect(backend.requests).toEqual(['list', 'plan']));
    // No editor in field mode: no tool bar, no import/export.
    expect(screen.queryByRole('toolbar', { name: 'Garden plan tools' })).toBeNull();
    expect(screen.queryByTestId('garden-plan-io-menu')).toBeNull();
  });

  it('lists my beds first, then by what is due, and says overdue in words', async () => {
    useFieldBackend();
    renderField();
    const list = await screen.findByTestId('field-bed-list');
    const rows = within(list).getAllByRole('button');
    expect(rows.map((row) => row.getAttribute('data-testid'))).toEqual([
      'field-bed-row-loc_b',
      'field-bed-row-loc_a',
      'field-bed-row-loc_c',
    ]);
    expect(await screen.findByTestId('field-bed-mine-loc_b')).toHaveTextContent('Mine');
    expect(screen.getByTestId('field-bed-overdue-loc_a')).toHaveTextContent('1 task overdue');
    expect(screen.getByTestId('field-bed-due-loc_c')).toHaveTextContent('Due today');
    expect(rows[0]).toHaveStyle({ minHeight: `${KIOSK_TOUCH_TARGET}px` });
  });

  it('waits for the assignments before it shows the list, so the order never changes under a tap', async () => {
    const { backend } = useFieldBackend({ holdAssignments: true });
    renderField();
    await waitFor(() => expect(backend.requests).toContain('list'));
    // The beds have answered, the assignments not yet: still loading, no rows to hit.
    expect(await screen.findByRole('status', { name: 'Loading beds' })).toBeInTheDocument();
    expect(screen.queryByTestId('field-bed-list')).toBeNull();
    act(() => backend.releaseAssignments());
    const list = await screen.findByTestId('field-bed-list');
    // The first order shown is already the final one: my bed (loc_b) first.
    expect(within(list).getAllByRole('button').map((row) => row.getAttribute('data-testid'))).toEqual([
      'field-bed-row-loc_b',
      'field-bed-row-loc_a',
      'field-bed-row-loc_c',
    ]);
  });

  it('switches to planning mode with a link that keeps the page', async () => {
    useFieldBackend();
    const { router } = renderField();
    await screen.findByTestId('field-bed-list');
    fireEvent.click(screen.getByTestId('garden-plan-mode-planning'));
    await waitFor(() => expect(router.state.location.search).toBe('?mode=plan'));
    expect(await screen.findByTestId('garden-plan-mode-field')).toBeInTheDocument();
  });
});

describe('bed sheet', () => {
  it('completes a task in two taps after the bed was chosen and offers undo (GP-ACC-029, GP-FR-149)', async () => {
    const { seen } = useFieldBackend();
    const user = userEvent.setup();
    renderField();
    const sheet = await openBed('Raised bed 1');
    const done = await within(sheet).findByTestId('field-done-t_water');
    expect(within(sheet).getByTestId('field-tasks-overdue')).toContainElement(done);
    expect(done).toHaveStyle({ minHeight: `${KIOSK_TOUCH_TARGET}px`, minWidth: `${KIOSK_TOUCH_TARGET}px` });

    await user.click(done); // tap 1
    const dialog = await screen.findByTestId('care-complete-dialog');
    const finish = within(dialog).getByTestId('care-complete-submit');
    expect(finish).toHaveTextContent('Finish');
    await user.click(finish); // tap 2

    await waitFor(() => expect(seen.filter((entry) => entry.url === '/tasks/t_water/complete')).toHaveLength(1));
    // Without any input the completion carries no fields: a watering care line without a quantity.
    expect(seen.find((entry) => entry.url === '/tasks/t_water/complete')?.body).toEqual({});
    const undo = await screen.findByTestId('care-undo');
    await user.click(undo);
    await waitFor(() =>
      expect(seen.find((entry) => entry.url === '/tasks/t_water/reopen')?.body).toEqual({ undo: true }),
    );
  });

  it('ignores a double tap on "Done" and keeps it locked while the answer is pending', async () => {
    const { seen } = useFieldBackend();
    let release: () => void = () => undefined;
    server.use(
      http.post(`${BASE}/tasks/:key/complete`, async () => {
        seen.push({ url: '/tasks/t_water/complete', body: {} });
        await new Promise<void>((resolve) => {
          release = resolve;
        });
        return HttpResponse.json({ status: 'completed' });
      }),
    );
    renderField();
    const sheet = await openBed('Raised bed 1');
    const done = await within(sheet).findByTestId('field-done-t_water');
    fireEvent.click(done);
    const finish = within(await screen.findByTestId('care-complete-dialog')).getByTestId('care-complete-submit');
    fireEvent.click(finish);
    fireEvent.click(finish);
    await waitFor(() => expect(within(sheet).getByTestId('field-done-t_water')).toBeDisabled());
    expect(seen.filter((entry) => entry.url === '/tasks/t_water/complete')).toHaveLength(1);
    act(() => release());
    await waitFor(() => expect(screen.queryByTestId('care-complete-dialog')).toBeNull());
  });

  it('logs weeding with one chip tap and voids it with the undo (GP-ACC-048)', async () => {
    const { seen } = useFieldBackend();
    const user = userEvent.setup();
    renderField();
    const sheet = await openBed('Raised bed 1');
    const chip = within(sheet).getByTestId('field-chip-weeding');
    expect(chip).toHaveTextContent('Weeded/Mulched');
    await user.click(chip);
    await waitFor(() => expect(seen.some((entry) => entry.url === '/care-events')).toBe(true));
    const body = seen.find((entry) => entry.url === '/care-events')?.body as Record<string, unknown>;
    expect(body).toMatchObject({ location_key: 'loc_a', category: 'weeding' });
    expect(body).not.toHaveProperty('trigger');
    await user.click(await screen.findByTestId('care-undo'));
    await waitFor(() =>
      expect(seen.find((entry) => entry.url === '/care-events/ce_1/void')?.body).toEqual({ reason: 'undo' }),
    );
  });

  it('keeps the list, the open sheet and the undo when a reload of the list fails', async () => {
    const { backend } = useFieldBackend();
    const user = userEvent.setup();
    renderField();
    const sheet = await openBed('Raised bed 1');
    backend.failList();
    const reloads = backend.requests.filter((entry) => entry === 'list').length;
    await user.click(within(sheet).getByTestId('field-chip-weeding'));
    await waitFor(() => expect(backend.requests.filter((entry) => entry === 'list').length).toBe(reloads + 1));
    expect(await screen.findByTestId('field-list-reload-failed', {}, { timeout: 3000 })).toHaveTextContent(
      'The beds could not be refreshed',
    );
    // Nothing was taken down: the sheet, its undo and the rows behind it stay.
    expect(screen.getByTestId('field-bed-sheet')).toBeInTheDocument();
    expect(screen.getByTestId('care-undo')).toBeInTheDocument();
    expect(screen.getByTestId('field-bed-row-loc_a')).toBeInTheDocument();
    expect(screen.queryByTestId('error-display')).toBeNull();
  });

  it('opens the short harvest form from its chip and logs a harvest', async () => {
    const { seen } = useFieldBackend();
    const user = userEvent.setup();
    renderField();
    const sheet = await openBed('Raised bed 1');
    await user.click(within(sheet).getByTestId('field-chip-harvest'));
    const dialog = await screen.findByTestId('care-log-dialog');
    // The category is fixed: no category list.
    expect(within(dialog).queryByTestId('care-log-category')).toBeNull();
    await user.click(within(dialog).getByTestId('care-log-submit'));
    await waitFor(() =>
      expect(seen.find((entry) => entry.url === '/care-events')?.body).toMatchObject({ category: 'harvest' }),
    );
  });

  it('opens the planting dialog with "already planted" on from the "Planted" chip', async () => {
    useFieldBackend();
    server.use(http.get('/api/v1/species', () => HttpResponse.json({ items: [], total: 0 })));
    const user = userEvent.setup();
    renderField();
    const sheet = await openBed('Raised bed 1');
    await user.click(within(sheet).getByTestId('field-chip-planted'));
    const dialog = await screen.findByTestId('planting-dialog');
    // The dialog's own controls are kiosk targets in the field (GP-UX-020).
    expect(within(dialog).getByTestId('planting-submit')).toHaveStyle({
      minHeight: `${KIOSK_TOUCH_TARGET}px`,
      minWidth: `${KIOSK_TOUCH_TARGET}px`,
    });
  });

  it('opens the photo dialog with kiosk touch targets (GP-UX-020)', async () => {
    useFieldBackend();
    const user = userEvent.setup();
    renderField();
    const sheet = await openBed('Raised bed 1');
    const group = await within(sheet).findByTestId('field-plant-group-sp-tomato--none--ph-flower');
    await user.click(within(group).getByTestId('field-plant-group-toggle-sp-tomato--none--ph-flower'));
    await user.click(within(group).getByTestId('field-plant-photo-pl_1'));
    const dialog = await screen.findByTestId('plant-photo-upload-dialog');
    for (const id of ['plant-photo-upload-cancel', 'plant-photo-upload-confirm']) {
      expect(within(dialog).getByTestId(id)).toHaveStyle({ minHeight: `${KIOSK_TOUCH_TARGET}px` });
    }
    expect(within(dialog).getByTestId('plant-photo-upload-close')).toHaveStyle({ width: `${KIOSK_TOUCH_TARGET}px` });
  });

  it('shows plants by species, count and phase and moves a plant by 10 cm with the stepper', async () => {
    const { backend } = useFieldBackend();
    let patched: unknown = null;
    server.use(
      http.patch(`${BASE}/slots/:key`, async ({ request }) => {
        patched = await request.json();
        return new HttpResponse(null, { status: 204 });
      }),
      http.get(`${BASE}/slots/:key`, () =>
        HttpResponse.json({
          key: 'slot_pl_1',
          slot_id: 'A1',
          location_key: 'loc_a',
          geometry: { kind: 'point', origin: [0.5, 0.5] },
        }),
      ),
      http.get(`${BASE}/slots`, () => HttpResponse.json([])),
    );
    const user = userEvent.setup();
    renderField();
    const sheet = await openBed('Raised bed 1');
    const group = await within(sheet).findByTestId('field-plant-group-sp-tomato--none--ph-flower');
    expect(group).toHaveTextContent('Tomato · 2');
    expect(group).toHaveTextContent('Phase: Flowering');
    await user.click(within(group).getByTestId('field-plant-group-toggle-sp-tomato--none--ph-flower'));
    await user.click(within(group).getByTestId('field-plant-correct-pl_1'));
    const dialog = await screen.findByTestId('position-dialog');
    const y = await within(dialog).findByTestId('position-y');
    expect(y).toHaveValue('50');
    await user.click(within(dialog).getByTestId('position-up'));
    expect(y).toHaveValue('60');
    expect(within(dialog).getByTestId('position-up')).toHaveStyle({ width: `${KIOSK_TOUCH_TARGET}px` });
    // The 10 cm step is already coarse: no ±5 cm buttons in the field.
    expect(within(dialog).queryByTestId('position-big-left')).toBeNull();
    expect(within(dialog).queryByTestId('position-big-right')).toBeNull();

    // Saving reloads the plan, so the map draws the plant where it now stands.
    await waitFor(() => expect(backend.requests).toContain('plan'));
    const plansBefore = backend.requests.filter((entry) => entry === 'plan').length;
    await user.click(within(dialog).getByTestId('position-save'));
    await waitFor(() => expect(patched).toEqual({ geometry: { kind: 'point', origin: [0.5, 0.6] } }));
    await waitFor(() => expect(backend.requests.filter((entry) => entry === 'plan').length).toBe(plansBefore + 1));
  });

  it('locks "Done" and the chips and says so while offline (GP-UX-024, D-23)', async () => {
    const { seen } = useFieldBackend();
    renderField();
    const sheet = await openBed('Raised bed 1');
    const done = await within(sheet).findByTestId('field-done-t_water');
    setOnline(false);
    expect(await screen.findByTestId('field-offline')).toBeInTheDocument();
    expect(within(sheet).getByTestId('field-sheet-offline')).toBeInTheDocument();
    expect(done).toBeDisabled();
    expect(within(sheet).getByTestId('field-chip-watering')).toBeDisabled();
    fireEvent.click(done);
    expect(screen.queryByTestId('care-complete-dialog')).toBeNull();
    expect(seen).toHaveLength(0);
    setOnline(true);
    await waitFor(() => expect(within(sheet).getByTestId('field-done-t_water')).toBeEnabled());
  });

  it('shows a viewer the tasks and plants without any write control', async () => {
    useFieldBackend();
    renderField('viewer');
    const sheet = await openBed('Raised bed 1');
    expect(await within(sheet).findByTestId('field-task-t_water')).toBeInTheDocument();
    expect(within(sheet).queryByTestId('field-done-t_water')).toBeNull();
    expect(within(sheet).queryByTestId('field-quick-protocol')).toBeNull();
  });

  it('closes with its 64 px close button', async () => {
    useFieldBackend();
    renderField();
    await openBed('Raised bed 1');
    fireEvent.click(screen.getByTestId('field-sheet-close'));
    await waitFor(() => expect(screen.queryByTestId('field-bed-sheet')).toBeNull());
  });
});

describe('map tab and device memory', () => {
  it('draws the plan without tools, opens a bed from the map and remembers the tab', async () => {
    useFieldBackend();
    const user = userEvent.setup();
    const { container, unmount } = renderField();
    await screen.findByTestId('field-bed-list');
    await user.click(screen.getByTestId('field-tab-map'));
    expect(await screen.findByTestId('field-map-canvas')).toBeInTheDocument();
    expect(screen.queryByTestId('garden-plan-tool-pan')).toBeNull();
    await user.click(screen.getByTestId('field-map-zoom-in'));
    await user.click(screen.getByTestId('field-map-fit'));

    const node = container.querySelector('[data-plan-key="loc_a"]') as HTMLElement;
    fireEvent.keyDown(node, { key: 'Enter' });
    const sheet = await screen.findByTestId('field-bed-sheet');
    expect(within(sheet).getByRole('heading', { level: 2 })).toHaveTextContent('Raised bed 1');

    expect(readFieldPrefs('user-1')).toMatchObject({ tenantSlug: 'testgarten', siteKey: 'site_1', tab: 'map' });
    expect(Object.keys(readFieldPrefs('user-1')?.viewports ?? {})).toEqual(['site_1']);
    unmount();

    renderField();
    // The tab and the view come back from the device memory.
    await waitFor(() => expect(screen.getByTestId('field-tab-map')).toHaveAttribute('aria-selected', 'true'));
    expect(await screen.findByTestId('field-map-canvas')).toBeInTheDocument();
    expect(localStorage.getItem(FIELD_PREFS_KEY)).not.toBeNull();
  });

  it('comes back to the view the user left when switching tabs, not the one from the start', async () => {
    useFieldBackend();
    const user = userEvent.setup();
    renderField();
    await screen.findByTestId('field-bed-list');
    await user.click(screen.getByTestId('field-tab-map'));
    await screen.findByTestId('field-map-canvas');
    // At "whole plan" zooming out is not possible; one step in makes it possible.
    expect(screen.getByTestId('field-map-zoom-out')).toBeDisabled();
    await user.click(screen.getByTestId('field-map-zoom-in'));
    expect(screen.getByTestId('field-map-zoom-out')).toBeEnabled();

    await user.click(screen.getByTestId('field-tab-list'));
    await user.click(screen.getByTestId('field-tab-map'));
    await screen.findByTestId('field-map-canvas');
    expect(screen.getByTestId('field-map-zoom-out')).toBeEnabled();

    await user.click(screen.getByTestId('field-map-fit'));
    await user.click(screen.getByTestId('field-tab-list'));
    await user.click(screen.getByTestId('field-tab-map'));
    await screen.findByTestId('field-map-canvas');
    expect(screen.getByTestId('field-map-zoom-out')).toBeDisabled();
  });

  it('restores a remembered view that still shows the plan and drops one that would show nothing', async () => {
    const plan = normalizePlan(planResponse({ locations: [bed('loc_a', 1, 1), bed('loc_b', 4, 1), bed('loc_c', 8, 1)] }));
    const fit = fitViewport(planContentBounds(plan)!, 636, Math.max(240, window.innerHeight * 0.6));
    const remember = (originM: [number, number]) =>
      localStorage.setItem(
        FIELD_PREFS_KEY,
        JSON.stringify({
          userKey: 'user-1',
          tenantSlug: 'testgarten',
          siteKey: 'site_1',
          tab: 'map',
          viewports: { site_1: { pxPerM: fit.pxPerM * 2, originM } },
        }),
      );

    useFieldBackend();
    remember(fit.originM);
    const first = renderField();
    await screen.findByTestId('field-map-canvas');
    // Zoomed in on the plan: the remembered view holds.
    expect(screen.getByTestId('field-map-zoom-out')).toBeEnabled();
    first.unmount();

    // A view far away from every bed (another device, a turned phone) is not applied: the whole plan.
    remember([500, -500]);
    renderField();
    await screen.findByTestId('field-map-canvas');
    expect(screen.getByTestId('field-map-zoom-out')).toBeDisabled();
  });

  it('opens the bed that is tapped, or the one next to a tap that missed a small bed', async () => {
    useFieldBackend();
    const user = userEvent.setup();
    renderField();
    await screen.findByTestId('field-bed-list');
    await user.click(screen.getByTestId('field-tab-map'));
    const canvas = await screen.findByTestId('field-map-canvas');
    // The same fit FieldMap computes (jsdom: 640 px fallback width minus the frame, no layout offsets).
    const plan = normalizePlan(planResponse({ locations: [bed('loc_a', 1, 1), bed('loc_b', 4, 1), bed('loc_c', 8, 1)] }));
    const view = fitViewport(planContentBounds(plan)!, 636, Math.max(240, window.innerHeight * 0.6));
    const tap = (x: number, y: number) =>
      fireEvent.click(canvas, {
        clientX: (x - view.originM[0]) * view.pxPerM,
        clientY: (view.originM[1] - y) * view.pxPerM,
      });

    tap(1.6, 2); // inside "Raised bed 1"
    expect(within(await screen.findByTestId('field-bed-sheet')).getByRole('heading', { level: 2 })).toHaveTextContent(
      'Raised bed 1',
    );
    fireEvent.click(screen.getByTestId('field-sheet-close'));
    await waitFor(() => expect(screen.queryByTestId('field-bed-sheet')).toBeNull());
    // The tap zoomed onto the bed; back to the whole plan, where the coordinates above hold.
    fireEvent.click(screen.getByTestId('field-map-fit'));

    tap(6.5, 2); // between beds, closer to "Herb spiral" (x 4…5.2) than to "Allotment" (x 8…)
    expect(within(await screen.findByTestId('field-bed-sheet')).getByRole('heading', { level: 2 })).toHaveTextContent(
      'Herb spiral',
    );
  });
});

describe('field mode accessibility', () => {
  it('has no critical violations in the list and in the open sheet', async () => {
    useFieldBackend();
    const { container } = renderField();
    await screen.findByTestId('field-bed-list');
    await expectNoA11yViolations(container, { minElements: 20 });
    await openBed('Raised bed 1');
    await screen.findByTestId('field-done-t_water');
    await expectNoA11yViolations(document.body, { minElements: 40 });
  });
});

describe('sun window in the bed sheet (REQ-053 GP-FR-158/159, GP-UX-057, WP 7.20)', () => {
  const SUN_BEDS: BedListItem[] = [
    bedListItem('loc_a', {
      name: 'Raised bed 1',
      site_conditions: { sun_profile: { sun_window: 'morning', foliage_shade_in_summer: false } },
    }),
  ];

  function useSunPatch() {
    const bodies: unknown[] = [];
    server.use(
      http.patch(`${BASE}/locations/:key`, async ({ request }) => {
        bodies.push(await request.json());
        return HttpResponse.json({ key: 'loc_a', bed_status: 'active', plan_revision: 5 });
      }),
    );
    return bodies;
  }

  it('shows the stored window and keeps the chips and the switch at 64 px', async () => {
    useFieldBackend({ beds: SUN_BEDS });
    renderField();
    const sheet = await openBed('Raised bed 1');
    const section = await within(sheet).findByTestId('field-mode-sun-section');

    expect(await within(section).findByRole('radio', { name: 'Morning' })).toBeChecked();
    for (const option of ['morning', 'midday', 'afternoon', 'all_day', 'mixed', 'unknown']) {
      expect(within(section).getByTestId(`field-mode-sun-profile-window-${option}`)).toHaveStyle({
        minHeight: `${KIOSK_TOUCH_TARGET}px`,
        minWidth: `${KIOSK_TOUCH_TARGET}px`,
      });
    }
    expect(within(section).getByRole('switch', { name: 'Leaf shade in summer' }).closest('label')).toHaveStyle({
      minHeight: `${KIOSK_TOUCH_TARGET}px`,
    });
  });

  it('stores a tapped chip and the leaf-shade switch at once, one changed key per request', async () => {
    useFieldBackend({ beds: SUN_BEDS });
    const bodies = useSunPatch();
    const user = userEvent.setup();
    renderField();
    const sheet = await openBed('Raised bed 1');

    await user.click(await within(sheet).findByRole('radio', { name: 'Afternoon' }));
    await waitFor(() => expect(bodies).toHaveLength(1));
    expect(bodies[0]).toEqual({ site_conditions: { sun_profile: { sun_window: 'afternoon' } } });

    await waitFor(() => expect(within(sheet).getByRole('switch', { name: 'Leaf shade in summer' })).toBeEnabled());
    await user.click(within(sheet).getByRole('switch', { name: 'Leaf shade in summer' }));
    await waitFor(() => expect(bodies).toHaveLength(2));
    expect(bodies[1]).toEqual({ site_conditions: { sun_profile: { foliage_shade_in_summer: true } } });
  });

  it('keeps focus on the chip group after a save so the arrow keys can go on', async () => {
    useFieldBackend({ beds: SUN_BEDS });
    const bodies = useSunPatch();
    const user = userEvent.setup();
    renderField();
    const sheet = await openBed('Raised bed 1');
    const morning = await within(sheet).findByRole('radio', { name: 'Morning' });

    morning.focus();
    await user.keyboard('{ArrowRight}');

    await waitFor(() => expect(bodies).toHaveLength(1));
    expect(bodies[0]).toEqual({ site_conditions: { sun_profile: { sun_window: 'midday' } } });
    // The static test backend still answers "morning" after the reload; what counts here is the focus.
    expect(document.activeElement).toBe(within(sheet).getByRole('radio', { name: 'Midday' }));
    await user.keyboard('{ArrowRight}');
    await waitFor(() => expect(bodies).toHaveLength(2));
    expect(bodies[1]).toEqual({ site_conditions: { sun_profile: { sun_window: 'afternoon' } } });
  });

  it('stores hours typed and a chip tapped right after as two requests, none is lost', async () => {
    useFieldBackend({ beds: SUN_BEDS });
    const bodies: unknown[] = [];
    let release: () => void = () => undefined;
    const gate = new Promise<void>((resolve) => {
      release = resolve;
    });
    server.use(
      http.patch(`${BASE}/locations/:key`, async ({ request }) => {
        bodies.push(await request.json());
        if (bodies.length === 1) await gate; // the first save is still running when the chip is tapped
        return HttpResponse.json({ key: 'loc_a', bed_status: 'active', plan_revision: 5 });
      }),
    );
    const user = userEvent.setup();
    renderField();
    const sheet = await openBed('Raised bed 1');
    const hours = await within(sheet).findByRole('textbox', { name: 'Hours of direct sun in summer (optional)' });

    await user.type(hours, '6');
    await user.click(within(sheet).getByRole('radio', { name: 'All day' })); // blur saves the hours first
    await waitFor(() => expect(bodies).toHaveLength(1));
    expect(within(sheet).getByRole('radio', { name: 'All day' })).toBeChecked();
    act(() => release());

    await waitFor(() => expect(bodies).toHaveLength(2));
    expect(bodies[0]).toEqual({ site_conditions: { sun_profile: { direct_sun_hours_summer: 6 } } });
    expect(bodies[1]).toEqual({ site_conditions: { sun_profile: { sun_window: 'all_day' } } });
  });

  it('puts the chip back when the server refuses the change (422)', async () => {
    useFieldBackend({ beds: SUN_BEDS });
    let refused = 0;
    server.use(
      http.patch(`${BASE}/locations/:key`, () => {
        refused += 1;
        return HttpResponse.json({ detail: 'refused' }, { status: 422 });
      }),
    );
    const user = userEvent.setup();
    renderField();
    const sheet = await openBed('Raised bed 1');

    await user.click(await within(sheet).findByRole('radio', { name: 'Afternoon' }));

    await waitFor(() => expect(refused).toBe(1));
    await waitFor(() => expect(within(sheet).getByRole('radio', { name: 'Morning' })).toBeChecked());
    expect(within(sheet).getByRole('radio', { name: 'Afternoon' })).not.toBeChecked();
    expect(screen.getByTestId('field-bed-sheet')).toBeInTheDocument();
  });

  it('puts the switch back when the network fails', async () => {
    useFieldBackend({ beds: SUN_BEDS });
    server.use(http.patch(`${BASE}/locations/:key`, () => HttpResponse.error()));
    const user = userEvent.setup();
    renderField();
    const sheet = await openBed('Raised bed 1');
    const toggle = await within(sheet).findByRole('switch', { name: 'Leaf shade in summer' });

    await user.click(toggle);

    await waitFor(() => expect(toggle).not.toBeChecked());
    expect(screen.getByTestId('field-bed-sheet')).toBeInTheDocument();
  });

  it('stores the summer sun hours from the sheet', async () => {
    useFieldBackend({ beds: SUN_BEDS });
    const bodies = useSunPatch();
    const user = userEvent.setup();
    renderField();
    const sheet = await openBed('Raised bed 1');
    const hours = await within(sheet).findByRole('textbox', { name: 'Hours of direct sun in summer (optional)' });

    await user.type(hours, '7{Enter}');

    await waitFor(() => expect(bodies).toHaveLength(1));
    expect(bodies[0]).toEqual({ site_conditions: { sun_profile: { direct_sun_hours_summer: 7 } } });
  });

  it('shows a viewer the values and takes no input', async () => {
    useFieldBackend({ beds: SUN_BEDS });
    const bodies = useSunPatch();
    renderField('viewer');
    const sheet = await openBed('Raised bed 1');

    const chip = await within(sheet).findByRole('radio', { name: 'Morning' });
    expect(chip).toBeChecked();
    expect(chip).toBeDisabled();
    expect(within(sheet).getByRole('switch', { name: 'Leaf shade in summer' })).toBeDisabled();
    expect(bodies).toHaveLength(0);
  });

  it('locks the controls while offline instead of losing the entry', async () => {
    useFieldBackend({ beds: SUN_BEDS });
    renderField();
    const sheet = await openBed('Raised bed 1');
    const chip = await within(sheet).findByRole('radio', { name: 'Midday' });
    expect(chip).toBeEnabled();

    setOnline(false);

    expect(chip).toBeDisabled();
  });

  it('has no accessibility violations in the sheet', async () => {
    useFieldBackend({ beds: SUN_BEDS });
    renderField();
    const sheet = await openBed('Raised bed 1');
    await within(sheet).findByRole('radio', { name: 'Morning' });

    await expectNoA11yViolations(sheet);
  });
});
