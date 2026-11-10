import { act, cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import { RouterProvider, createMemoryRouter } from 'react-router-dom';
import { SnackbarProvider } from 'notistack';
import { http, HttpResponse } from 'msw';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import GardenPlanRoute from '@/features/gardenPlanner/routes/GardenPlanRoute';
import ModuleGuard from '@/components/common/ModuleGuard';
import { applyAction, loadGardenPlan } from '@/features/gardenPlanner/state/gardenPlanSlice';
import { installRecordingCanvas, uninstallRecordingCanvas } from '@/features/gardenPlanner/renderer/konvaTestCanvas';
import { rootReducer } from '@/store/rootReducer';
import { ThemeContextProvider } from '@/theme';
import { expectNoA11yViolations } from '@/test/a11y/expectNoA11yViolations';
import type { GardenPlanResponse } from '@/features/gardenPlanner/model/types';
import { bed, gardenObject, planResponse } from '@/test/gardenPlanFixtures';
import { createStoreWithModuleOverrides, renderWithProviders, tenantState } from '@/test/helpers';
import { server } from '@/test/mocks/server';
import { bedListItem } from '@/features/gardenPlanner/bed/bedTestKit';

const PLAN_URL = '/api/v1/t/:tenant/sites/:key/plan';

function usePlan(body: GardenPlanResponse = planResponse({ locations: [bed('loc_a', 2, 2)], garden_objects: [gardenObject('go_1', 6, 6)] })) {
  server.use(http.get(PLAN_URL, () => HttpResponse.json(body)));
}

/** A store with the real root reducer, so the lazily injected slice is exercised for real. */
function renderRoute(route = '/standorte/sites/site_1/plan', preloadedState?: Record<string, unknown>) {
  const store = configureStore({ reducer: rootReducer, preloadedState: preloadedState as never });
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

// The bed list asks for the tenant's members and assignments. Unanswered, MSW passes them through; a 403 from
// whatever listens on the test origin is then read as a stale tenant and clears the active slug - mid-way through a
// later test of this file, whose next tenant-scoped request (a write) waits for a slug that never comes back.
beforeEach(() => {
  server.use(
    http.get('/api/v1/tenants/:slug/members', () => HttpResponse.json([])),
    http.get('/api/v1/tenants/:slug/assignments', () => HttpResponse.json([])),
  );
});
afterEach(() => cleanup());

describe('GardenPlanRoute', () => {
  it('shows a loading skeleton, then the plan drawn by the SVG renderer', async () => {
    usePlan();
    const { container } = renderRoute();
    expect(screen.getByTestId('garden-plan-page')).toBeInTheDocument();
    expect(await screen.findByTestId('garden-plan-canvas')).toBeInTheDocument();
    // The site name is the title; the drawing is an SVG with the bed and the object in it.
    expect(screen.getByRole('heading', { name: 'Vegetable garden' })).toBeInTheDocument();
    expect(container.querySelector('svg')).not.toBeNull();
    expect(container.querySelector('[data-plan-key="loc_a"]')).not.toBeNull();
    expect(container.querySelector('[data-plan-key="go_1"]')).not.toBeNull();
    // The scrollable drawing is a named, keyboard-focusable region.
    expect(screen.getByRole('region', { name: 'Garden plan' })).toHaveAttribute('tabindex', '0');
  });

  it('mounts the editor: the tool bar, and a pan drag moves the view of the drawing', async () => {
    usePlan();
    const { container } = renderRoute();
    const canvas = await screen.findByTestId('garden-plan-canvas');
    expect(screen.getByRole('toolbar', { name: 'Garden plan tools' })).toBeInTheDocument();
    const viewBox = () => container.querySelector('svg[data-testid="garden-plan-svg"]')!.getAttribute('viewBox');
    const before = viewBox();
    fireEvent.click(screen.getByTestId('garden-plan-tool-pan'));
    fireEvent.pointerDown(canvas, { pointerId: 1, pointerType: 'mouse', button: 0, clientX: 100, clientY: 100 });
    fireEvent.pointerMove(canvas, { pointerId: 1, pointerType: 'mouse', button: 0, clientX: 160, clientY: 130 });
    fireEvent.pointerUp(canvas, { pointerId: 1, pointerType: 'mouse', button: 0, clientX: 160, clientY: 130 });
    const after = viewBox();
    expect(after).not.toBe(before);
    // The view moved, the plan did not: nothing is pending.
    expect(screen.queryByTestId('garden-plan-notice')).toBeNull();
  });

  it('zooms with the buttons, keeps the pan, and "fit" returns to the fitted view (WP 2.5)', async () => {
    usePlan();
    renderRoute();
    await screen.findByTestId('garden-plan-canvas');
    const level = () => screen.getByTestId('garden-plan-zoom-level').textContent;
    const fitted = level();
    fireEvent.click(screen.getByTestId('garden-plan-zoom-in'));
    expect(level()).not.toBe(fitted);
    expect(screen.getByTestId('garden-plan-scale-bar')).toBeInTheDocument();
    fireEvent.click(screen.getByTestId('garden-plan-zoom-fit'));
    expect(level()).toBe(fitted);
    // The fitted view is the lowest zoom (GP-FR-150).
    expect(screen.getByTestId('garden-plan-zoom-out')).toBeDisabled();
  });

  it('selects the bed and brings its bounding box into view when a row of the bed list is chosen (GP-ACC-016)', async () => {
    usePlan(
      planResponse({
        locations: [bed('loc_a', 2, 2), bed('loc_b', 60, 70), bed('loc_c', 80, 10)],
        garden_objects: [],
      }),
    );
    server.use(
      http.get('/api/v1/t/:tenant/locations', () =>
        HttpResponse.json([
          bedListItem('loc_a', { name: 'Bed near', bbox: [2, 2, 3.2, 4] }),
          bedListItem('loc_b', { name: 'Bed far', bbox: [60, 70, 61.2, 72] }),
          bedListItem('loc_c', { name: 'Bed east', bbox: [80, 10, 81.2, 12] }),
        ]),
      ),
    );
    // The bed list is the tab "Beete" (GP-UX-064); a row opens the plan again.
    const { store, container } = renderRoute('/standorte/sites/site_1/plan?tab=beds');
    await screen.findByTestId('garden-plan-canvas');
    const level = () => screen.getByTestId('garden-plan-zoom-level').textContent;
    const fitted = level();
    const row = (await screen.findByText('Bed far')).closest('tr')!;
    fireEvent.click(row);

    // Selected on the plan ...
    expect(store.getState().gardenPlan?.selection).toEqual([{ entity: 'location', key: 'loc_b' }]);
    // ... and zoomed in on: the whole bounding box lies inside the visible part of the drawing.
    expect(level()).not.toBe(fitted);
    const [x, y, width, height] = container
      .querySelector('svg[data-testid="garden-plan-svg"]')!
      .getAttribute('viewBox')!
      .split(/\s+/)
      .map(Number);
    // The viewBox is in metres with y negated (user unit = 1 m); the view is the bed, not the 100 m plan.
    expect(width).toBeLessThan(30);
    for (const [mx, my] of [[60, 70], [61.2, 72]]) {
      expect(mx).toBeGreaterThanOrEqual(x);
      expect(mx).toBeLessThanOrEqual(x + width);
      expect(-my).toBeGreaterThanOrEqual(y);
      expect(-my).toBeLessThanOrEqual(y + height);
    }
  });

  it('does not select a bed that is not drawn yet, and says so', async () => {
    usePlan(planResponse({ locations: [bed('loc_a', 2, 2)], garden_objects: [] }));
    server.use(
      http.get('/api/v1/t/:tenant/locations', () =>
        HttpResponse.json([bedListItem('loc_x', { name: 'Stock bed', geometry: null, bbox: null })]),
      ),
    );
    const { store } = renderRoute('/standorte/sites/site_1/plan?tab=beds');
    await screen.findByTestId('garden-plan-canvas');
    fireEvent.click((await screen.findByText('Stock bed')).closest('tr')!);
    expect(await screen.findByText('"Stock bed" is not drawn on the garden plan yet.')).toBeInTheDocument();
    expect(store.getState().gardenPlan?.selection).toEqual([]);
  });

  it('asks before leaving with unsaved changes and lets the user stay (GP-NFR-005)', async () => {
    usePlan();
    const { store, router } = renderRoute();
    await screen.findByTestId('garden-plan-canvas');
    // Nothing pending: the back link leaves without a question.
    expect(screen.getByTestId('garden-plan-save-status')).toHaveTextContent('Saved');

    act(() => {
      store.dispatch(
        applyAction([
          {
            op: 'update_geometry',
            entity: 'location',
            key: 'loc_a',
            geometry: { kind: 'rect', origin: [3, 3], width_m: 2, length_m: 2, rotation_deg: 0 },
          },
        ]),
      );
    });
    expect(screen.getByTestId('garden-plan-save-status')).toHaveTextContent('Unsaved changes (1)');
    const unload = new Event('beforeunload', { cancelable: true });
    window.dispatchEvent(unload);
    expect(unload.defaultPrevented).toBe(true);

    await act(async () => {
      void router.navigate('/standorte/sites/site_1');
    });
    expect(await screen.findByTestId('confirm-dialog')).toBeInTheDocument();
    expect(router.state.location.pathname).toBe('/standorte/sites/site_1/plan');
    fireEvent.click(screen.getByTestId('confirm-dialog-cancel'));
    await waitFor(() => expect(screen.queryByTestId('confirm-dialog')).toBeNull());
    expect(screen.getByTestId('garden-plan-save-status')).toHaveTextContent('Unsaved changes (1)');
  });

  it('explains the empty state of a site without a plan', async () => {
    usePlan(planResponse({ plan: null, locations: [], garden_objects: [], slots: [], plants: [] }));
    renderRoute();
    expect(await screen.findByTestId('garden-plan-empty')).toBeInTheDocument();
    expect(screen.getByText(/No plan has been created for this site yet/)).toBeInTheDocument();
    expect(screen.queryByTestId('garden-plan-canvas')).toBeNull();
  });

  describe('empty plan: the first bed (GP-UX-049, #2617)', () => {
    const emptyPlan = () => planResponse({ plan: null, locations: [], garden_objects: [], slots: [], plants: [] });
    const set = (id: string, value: string) => fireEvent.change(screen.getByTestId(id), { target: { value } });

    it('offers a grower the one next step, and it opens the editor with "add with dimensions"', async () => {
      usePlan(emptyPlan());
      renderRoute(undefined, tenantState('grower'));
      await screen.findByTestId('garden-plan-empty');
      // The description names the next step; the action is a named, touch-sized button.
      expect(screen.getByText(/As the next step, add the first bed with its dimensions/)).toBeInTheDocument();
      const action = screen.getByRole('button', { name: 'Add the first bed' });
      expect(action).toHaveAttribute('data-testid', 'garden-plan-empty-add-bed');
      expect(screen.queryByTestId('garden-plan-canvas')).toBeNull();

      fireEvent.click(action);
      expect(await screen.findByTestId('garden-plan-canvas')).toBeInTheDocument();
      expect(screen.getByTestId('garden-plan-editor')).toBeInTheDocument();
      expect(await screen.findByRole('dialog', { name: 'Add with dimensions' })).toBeInTheDocument();
      expect(screen.queryByTestId('garden-plan-empty')).toBeNull();
    });

    it('keeps the editor once the first bed is created through the dialog', async () => {
      usePlan(emptyPlan());
      const { store, container } = renderRoute(undefined, tenantState('lead'));
      fireEvent.click(await screen.findByTestId('garden-plan-empty-add-bed'));
      await screen.findByTestId('garden-plan-add-dialog');
      set('garden-plan-add-name', 'First bed');
      set('garden-plan-add-x', '4');
      set('garden-plan-add-y', '4');
      set('garden-plan-add-width', '1,2');
      set('garden-plan-add-length', '2');
      fireEvent.click(screen.getByTestId('garden-plan-add-submit'));
      await waitFor(() => expect(screen.queryByTestId('garden-plan-add-dialog')).toBeNull());

      const locations = Object.values(store.getState().gardenPlan!.plan!.locations);
      expect(locations).toHaveLength(1);
      expect(locations[0]).toMatchObject({ name: 'First bed', geometry: { kind: 'rect', origin: [4, 4] } });
      // The plan is no longer empty and the editor stays: the new bed is drawn, the empty state does not return.
      expect(screen.getByTestId('garden-plan-canvas')).toBeInTheDocument();
      expect(container.querySelector(`[data-plan-key="${locations[0].key}"]`)).not.toBeNull();
      expect(screen.queryByTestId('garden-plan-empty')).toBeNull();
    });

    it('shows a viewer the empty state without the action', async () => {
      usePlan(emptyPlan());
      renderRoute(undefined, tenantState('viewer'));
      await screen.findByTestId('garden-plan-empty');
      expect(screen.getByText(/Members with the grower or lead role create the beds/)).toBeInTheDocument();
      expect(screen.queryByTestId('garden-plan-empty-add-bed')).toBeNull();
      expect(screen.queryByRole('button', { name: 'Add the first bed' })).toBeNull();
      expect(screen.queryByTestId('garden-plan-canvas')).toBeNull();
    });
  });

  it('reloads the plan after a CSV bed list and selects the new beds for arranging (GP-FR-174)', async () => {
    let imported = false;
    server.use(
      http.get(PLAN_URL, () =>
        HttpResponse.json(
          planResponse({
            locations: imported ? [bed('loc_a', 2, 2), bed('loc_new', 10, 10)] : [bed('loc_a', 2, 2)],
            garden_objects: [],
          }),
        ),
      ),
      http.post('/api/v1/t/:tenant/sites/:key/beds/import-csv', ({ request }) => {
        const dryRun = new URL(request.url).searchParams.get('dry_run') === 'true';
        imported = !dryRun;
        return HttpResponse.json({
          dry_run: dryRun,
          rows_total: 1,
          rows: [
            {
              line: 2,
              name: 'New bed',
              location_type_key: 'raised_bed',
              width_m: 1.2,
              length_m: 2,
              origin: [10, 10],
              sun_exposure: 'full_sun',
              soil_texture: null,
              irrigation_zone_key: null,
              location_key: dryRun ? null : 'loc_new',
            },
          ],
          rows_valid: 1,
          rows_skipped: 0,
          errors: [],
          errors_total: 0,
          warnings: [],
          warnings_total: 0,
          ignored_columns: [],
          ignored_columns_total: 0,
          applied: !dryRun,
          plan_revision: dryRun ? 4 : 5,
        });
      }),
    );
    const { store } = renderRoute(undefined, tenantState('lead'));
    await screen.findByTestId('garden-plan-canvas');
    // With the editor on screen export and import are entries of the header bar's overflow (WP 10.3).
    fireEvent.click(screen.getByTestId('garden-plan-overflow'));
    fireEvent.click(await screen.findByTestId('garden-plan-io-csv'));
    const user = userEvent.setup();
    await user.upload(
      await screen.findByTestId('plan-csv-file'),
      new File(['Name;Typ;Breite_m;Länge_m\r\nNew bed;Hochbeet;1,2;2\r\n'], 'beds.csv', { type: 'text/csv' }),
    );
    await screen.findByTestId('plan-csv-report');
    fireEvent.click(await screen.findByTestId('plan-csv-apply'));
    await screen.findByTestId('plan-csv-done');

    await waitFor(() =>
      expect(store.getState().gardenPlan?.selection).toEqual([{ entity: 'location', key: 'loc_new' }]),
    );
    expect(store.getState().gardenPlan?.plan?.locations.loc_new).toBeDefined();
  });

  it('decides the renderer afresh when the same site loads again: a plan grown past 3 000 objects goes to Konva (D-01)', async () => {
    installRecordingCanvas();
    try {
      let big = false;
      server.use(
        http.get(PLAN_URL, () =>
          HttpResponse.json(
            planResponse({
              locations: [bed('loc_a', 2, 2)],
              garden_objects: [],
              plants: [],
              slots: big
                ? Array.from({ length: 3000 }, (_, i) => ({
                    key: `s${i}`,
                    slot_id: `S${i}`,
                    location_key: 'loc_a',
                    plan_geometry: { origin: [2.1 + (i % 10) * 0.1, 2.1 + Math.floor(i / 10) * 0.005] as [number, number] },
                  }))
                : [],
            }),
          ),
        ),
      );
      const { store } = renderRoute();
      await screen.findByTestId('garden-plan-canvas');
      expect(screen.queryByTestId('garden-plan-konva')).toBeNull(); // the small plan: SVG
      // An import into the same site, a reload after a conflict: the page stays mounted, the plan loads again.
      big = true;
      await act(async () => {
        await store.dispatch(loadGardenPlan('site_1'));
      });
      expect(await screen.findByTestId('garden-plan-konva', undefined, { timeout: 5000 })).toBeInTheDocument();
    } finally {
      uninstallRecordingCanvas();
    }
  });

  it('shows the existing error display for a site of another tenant (404) and retries', async () => {
    server.use(
      http.get(PLAN_URL, () =>
        HttpResponse.json(
          { error_id: 'e1', error_code: 'NOT_FOUND', message: 'Site not found.', details: [], timestamp: '', path: '', method: '' },
          { status: 404 },
        ),
      ),
    );
    renderRoute('/standorte/sites/foreign/plan');
    expect(await screen.findByTestId('error-display')).toBeInTheDocument();
    expect(screen.queryByTestId('garden-plan-canvas')).toBeNull();

    usePlan();
    screen.getByTestId('error-retry-button').click();
    expect(await screen.findByTestId('garden-plan-canvas')).toBeInTheDocument();
  });

  it('opens field mode with ?mode=field: no editor, the bed list first (GP-UX-020)', async () => {
    usePlan();
    server.use(http.get('/api/v1/t/:tenant/locations', () => HttpResponse.json([bedListItem('loc_a')])));
    renderRoute('/standorte/sites/site_1/plan?mode=field');
    expect(await screen.findByTestId('garden-plan-field-mode')).toBeInTheDocument();
    expect(await screen.findByTestId('field-bed-list')).toBeInTheDocument();
    expect(screen.queryByTestId('garden-plan-canvas')).toBeNull();
    expect(screen.getByTestId('garden-plan-mode-planning')).toHaveAttribute(
      'href',
      '/standorte/sites/site_1/plan?mode=plan',
    );
  });

  it('opens field mode by default on a phone (xs) and planning mode with ?mode=plan', async () => {
    const original = window.matchMedia;
    // Every max-width query matches: the xs breakpoint (< 600 px) is active.
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
      usePlan();
      server.use(http.get('/api/v1/t/:tenant/locations', () => HttpResponse.json([bedListItem('loc_a')])));
      renderRoute();
      expect(await screen.findByTestId('garden-plan-field-mode')).toBeInTheDocument();
      cleanup();
      renderRoute('/standorte/sites/site_1/plan?mode=plan');
      expect(await screen.findByTestId('garden-plan-canvas')).toBeInTheDocument();
      expect(screen.queryByTestId('garden-plan-field-mode')).toBeNull();
    } finally {
      window.matchMedia = original;
    }
  });

  it('opens planning mode on a wide screen and offers the switch to field mode', async () => {
    usePlan();
    const { router } = renderRoute();
    await screen.findByTestId('garden-plan-canvas');
    expect(screen.queryByTestId('garden-plan-field-mode')).toBeNull();
    fireEvent.click(screen.getByTestId('garden-plan-mode-field'));
    await waitFor(() => expect(router.state.location.search).toBe('?mode=field'));
    expect(await screen.findByTestId('garden-plan-field-mode')).toBeInTheDocument();
  });

  it('links back to the site and forgets the plan when it is left', async () => {
    usePlan();
    const { store, router } = renderRoute();
    await screen.findByTestId('garden-plan-canvas');
    expect(store.getState().gardenPlan?.plan?.siteKey).toBe('site_1');

    screen.getByTestId('garden-plan-back-link').click();
    await waitFor(() => expect(screen.getByTestId('site-detail-stub')).toBeInTheDocument());
    expect(router.state.location.pathname).toBe('/standorte/sites/site_1');
    expect(store.getState().gardenPlan?.plan).toBeNull();
  });

  it('has no accessibility violations (loaded and empty)', async () => {
    usePlan();
    const loaded = renderRoute();
    await screen.findByTestId('garden-plan-canvas');
    await expectNoA11yViolations(loaded.container);
    loaded.unmount();

    usePlan(planResponse({ plan: null, locations: [], garden_objects: [], slots: [], plants: [] }));
    const empty = renderRoute();
    await screen.findByTestId('garden-plan-empty');
    await expectNoA11yViolations(empty.container);
    empty.unmount();

    // The empty state with its action (a grower, #2617).
    const emptyWithAction = renderRoute(undefined, tenantState('grower'));
    await screen.findByTestId('garden-plan-empty-add-bed');
    await expectNoA11yViolations(emptyWithAction.container);
  });
});

describe('garden plan module visibility (REQ-042 §4.3)', () => {
  const guarded = (
    <ModuleGuard moduleKey="garden_planner">
      <div data-testid="plan-content" />
    </ModuleGuard>
  );

  it('shows the route content while the module is on (also at the beginner level)', () => {
    renderWithProviders(guarded, {
      store: createStoreWithModuleOverrides('beginner', {}),
      route: '/standorte/sites/site_1/plan',
    });
    expect(screen.getByTestId('plan-content')).toBeInTheDocument();
  });

  it('shows the reactivation hint when the module is switched off, although the path lies under the core locations module', () => {
    renderWithProviders(guarded, {
      store: createStoreWithModuleOverrides('expert', { garden_planner: 'disabled' }),
      route: '/standorte/sites/site_1/plan',
    });
    expect(screen.getByTestId('module-guard-hint')).toBeInTheDocument();
    expect(screen.queryByTestId('plan-content')).toBeNull();
  });
});
