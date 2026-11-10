/**
 * Tabs Plan · Liste · Beete of the garden plan route (REQ-053 §17.3, GP-UX-064/065, WP 10.2 #2823):
 * URL state in `?tab=`, history entries, field mode without tabs, no unsaved-changes prompt on a switch,
 * the editor state kept across switches, the bed list following a save (#2813) and a row opening the plan.
 */
import { act, cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import { RouterProvider, createMemoryRouter } from 'react-router-dom';
import { SnackbarProvider } from 'notistack';
import { http, HttpResponse } from 'msw';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import GardenPlanRoute from '@/features/gardenPlanner/routes/GardenPlanRoute';
import { applyAction, setSelection } from '@/features/gardenPlanner/state/gardenPlanSlice';
import { rootReducer } from '@/store/rootReducer';
import { ThemeContextProvider } from '@/theme';
import { expectNoA11yViolations } from '@/test/a11y/expectNoA11yViolations';
import type { GardenPlanResponse } from '@/features/gardenPlanner/model/types';
import { bed, gardenObject, planResponse } from '@/test/gardenPlanFixtures';
import { tenantState } from '@/test/helpers';
import { server } from '@/test/mocks/server';
import { bedListItem } from '@/features/gardenPlanner/bed/bedTestKit';

const PLAN_URL = '/api/v1/t/:tenant/sites/:key/plan';
const BEDS_URL = '/api/v1/t/:tenant/locations';

function usePlan(
  body: GardenPlanResponse = planResponse({
    locations: [bed('loc_a', 2, 2), bed('loc_b', 60, 70)],
    garden_objects: [gardenObject('go_1', 6, 6)],
  }),
) {
  server.use(http.get(PLAN_URL, () => HttpResponse.json(body)));
}

function useBeds(names: Record<string, string> = { loc_a: 'Bed near', loc_b: 'Bed far' }) {
  server.use(
    http.get(BEDS_URL, () =>
      HttpResponse.json(
        Object.entries(names).map(([key, name]) =>
          bedListItem(key, { name, bbox: key === 'loc_b' ? [60, 70, 61.2, 72] : [2, 2, 3.2, 4] }),
        ),
      ),
    ),
  );
}

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

const tab = (name: 'plan' | 'list' | 'beds') => screen.getByTestId(`garden-plan-tab-${name}`);
const editorPanel = () => screen.getByTestId('garden-plan-tabpanel-editor');
const bedsPanel = () => screen.getByTestId('garden-plan-tabpanel-beds');
const tabParam = (router: ReturnType<typeof renderRoute>['router']) =>
  new URLSearchParams(router.state.location.search).get('tab');

function expectTab(name: 'plan' | 'list' | 'beds') {
  for (const other of ['plan', 'list', 'beds'] as const) {
    expect(tab(other)).toHaveAttribute('aria-selected', String(other === name));
  }
  expect(bedsPanel().hidden).toBe(name !== 'beds');
  expect(editorPanel().hidden).toBe(name === 'beds');
}

const MOVE = {
  op: 'update_geometry' as const,
  entity: 'location' as const,
  key: 'loc_a',
  geometry: { kind: 'rect' as const, origin: [3, 3] as [number, number], width_m: 2, length_m: 2, rotation_deg: 0 },
};

beforeEach(() => {
  server.use(
    http.get('/api/v1/tenants/:slug/members', () => HttpResponse.json([])),
    http.get('/api/v1/tenants/:slug/assignments', () => HttpResponse.json([])),
  );
});
afterEach(() => {
  cleanup();
});

describe('garden plan tabs: URL state (GP-UX-064, AC-7, AC-12)', () => {
  it('opens "Plan" without ?tab and with an unknown value', async () => {
    usePlan();
    useBeds();
    const first = renderRoute();
    await screen.findByTestId('garden-plan-canvas');
    expect(screen.getByRole('tablist', { name: 'Garden plan view' })).toBeInTheDocument();
    expectTab('plan');
    first.unmount();

    renderRoute('/standorte/sites/site_1/plan?tab=xyz');
    await screen.findByTestId('garden-plan-canvas');
    expectTab('plan');
  });

  it('opens the tab of a deep link directly: ?tab=beds shows the bed list, ?tab=list the plan as a list', async () => {
    usePlan();
    useBeds();
    const beds = renderRoute('/standorte/sites/site_1/plan?tab=beds');
    expect(await screen.findByText('Bed far')).toBeInTheDocument();
    expectTab('beds');
    expect(screen.getByRole('tabpanel', { name: 'Beds' })).toContainElement(screen.getByTestId('bed-list-section'));
    beds.unmount();

    renderRoute('/standorte/sites/site_1/plan?tab=list');
    expect(await screen.findByTestId('garden-plan-list')).toBeInTheDocument();
    expectTab('list');
    expect(screen.queryByTestId('garden-plan-canvas')).toBeNull();
    // The tab is the one way into the list: the editor's former list switch is gone (WP 10.3).
    expect(screen.queryByTestId('garden-plan-view-list')).toBeNull();
  });

  it('pushes a history entry per switch, so "Back" returns to the previous tab; ?mode stays', async () => {
    usePlan();
    useBeds();
    const { router } = renderRoute('/standorte/sites/site_1/plan?mode=plan');
    await screen.findByTestId('garden-plan-canvas');

    fireEvent.click(tab('beds'));
    await waitFor(() => expect(tabParam(router)).toBe('beds'));
    expect(new URLSearchParams(router.state.location.search).get('mode')).toBe('plan');
    expectTab('beds');

    fireEvent.click(tab('list'));
    await waitFor(() => expect(tabParam(router)).toBe('list'));
    expectTab('list');

    await act(async () => {
      await router.navigate(-1);
    });
    expect(tabParam(router)).toBe('beds');
    expectTab('beds');
    await act(async () => {
      await router.navigate(-1);
    });
    expect(tabParam(router)).toBeNull();
    expectTab('plan');
  });

  it('lets the editor\'s own skip links move the tab, both ways', async () => {
    usePlan();
    useBeds();
    const { router } = renderRoute();
    await screen.findByTestId('garden-plan-canvas');
    fireEvent.click(screen.getByTestId('garden-plan-skip-list'));
    await waitFor(() => expect(tabParam(router)).toBe('list'));
    expect(await screen.findByTestId('garden-plan-list')).toBeInTheDocument();
    expectTab('list');
    fireEvent.click(screen.getByTestId('garden-plan-skip-plan'));
    await waitFor(() => expect(tabParam(router)).toBe('plan'));
    expect(await screen.findByTestId('garden-plan-canvas')).toBeInTheDocument();
  });

  it('shows no tab bar in field mode and ignores ?tab there', async () => {
    usePlan();
    server.use(http.get(BEDS_URL, () => HttpResponse.json([bedListItem('loc_a')])));
    renderRoute('/standorte/sites/site_1/plan?mode=field&tab=beds');
    expect(await screen.findByTestId('garden-plan-field-mode')).toBeInTheDocument();
    expect(await screen.findByTestId('field-bed-list')).toBeInTheDocument();
    expect(screen.queryByTestId('garden-plan-tabs')).toBeNull();
    expect(screen.queryByRole('tablist', { name: 'Garden plan view' })).toBeNull();
    expect(screen.queryByTestId('bed-list-section')).toBeNull();
  });
});

describe('garden plan tabs: nothing is lost on a switch (GP-UX-065, AC-8, AC-16)', () => {
  it('switches with unsaved changes without the prompt, keeps changes, selection and view; leaving still asks', async () => {
    usePlan();
    useBeds();
    const { store, router } = renderRoute();
    await screen.findByTestId('garden-plan-canvas');
    fireEvent.click(screen.getByTestId('garden-plan-zoom-in'));
    const zoom = screen.getByTestId('garden-plan-zoom-level').textContent;
    // State the editor keeps itself, outside the slice: it survives only because the editor stays mounted.
    fireEvent.click(screen.getByTestId('garden-plan-zones-open'));
    expect(screen.getByTestId('garden-plan-zones-open')).toHaveAttribute('aria-expanded', 'true');
    act(() => {
      store.dispatch(applyAction([MOVE]));
      store.dispatch(setSelection([{ entity: 'location', key: 'loc_a' }]));
    });
    expect(screen.getByTestId('garden-plan-save-status')).toHaveTextContent('Unsaved changes (1)');

    for (const next of ['beds', 'plan', 'list', 'plan'] as const) {
      fireEvent.click(tab(next));
      await waitFor(() => expect(tabParam(router)).toBe(next));
      expect(screen.queryByTestId('confirm-dialog')).toBeNull();
      expectTab(next);
    }

    // The editor was never torn down: the change, its undo entry, the selection and the zoom are all still there.
    expect(screen.getByTestId('garden-plan-save-status')).toHaveTextContent('Unsaved changes (1)');
    expect(store.getState().gardenPlan?.past).toHaveLength(1);
    expect(store.getState().gardenPlan?.selection).toEqual([{ entity: 'location', key: 'loc_a' }]);
    expect(screen.getByTestId('garden-plan-zoom-level').textContent).toBe(zoom);
    expect(screen.getByTestId('garden-plan-zones-open')).toHaveAttribute('aria-expanded', 'true');

    // "Back" between tabs does not ask either ...
    await act(async () => {
      await router.navigate(-1);
    });
    expect(tabParam(router)).toBe('list');
    expect(screen.queryByTestId('confirm-dialog')).toBeNull();

    // ... but leaving the route does.
    await act(async () => {
      void router.navigate('/standorte/sites/site_1');
    });
    expect(await screen.findByTestId('confirm-dialog')).toBeInTheDocument();
    expect(router.state.location.pathname).toBe('/standorte/sites/site_1/plan');
  });

  it('still asks before switching to field mode with unsaved changes', async () => {
    usePlan();
    useBeds();
    const { store, router } = renderRoute('/standorte/sites/site_1/plan?tab=beds');
    await screen.findByTestId('garden-plan-canvas');
    act(() => {
      store.dispatch(applyAction([MOVE]));
    });
    fireEvent.click(screen.getByTestId('garden-plan-mode-field'));
    expect(await screen.findByTestId('confirm-dialog')).toBeInTheDocument();
    expect(new URLSearchParams(router.state.location.search).get('mode')).toBeNull();
  });
});

describe('garden plan tabs: the bed list (GP-FR-042, AC-13, #2813)', () => {
  it('shows the saved state: after a save the new bed is in the list without reloading the page', async () => {
    let saved = false;
    let listCalls = 0;
    usePlan();
    server.use(
      http.get(BEDS_URL, () => {
        listCalls += 1;
        const beds = [bedListItem('loc_a', { name: 'Bed near' })];
        if (saved) beds.push(bedListItem('loc_new', { name: 'Bed drawn just now' }));
        return HttpResponse.json(beds);
      }),
      http.post('/api/v1/t/:tenant/sites/:key/plan/batch', () => {
        saved = true;
        return HttpResponse.json({ plan_revision: 43, key_map: {}, updated: ['loc_a'], deleted: [], derived: {} });
      }),
    );
    const { store, router } = renderRoute(undefined, tenantState('grower'));
    await screen.findByTestId('garden-plan-canvas');
    await waitFor(() => expect(listCalls).toBe(1));
    act(() => {
      store.dispatch(applyAction([MOVE]));
    });

    fireEvent.click(screen.getByTestId('garden-plan-save'));
    await waitFor(() => expect(screen.getByTestId('garden-plan-save-status')).toHaveTextContent('Saved'));

    fireEvent.click(tab('beds'));
    await waitFor(() => expect(tabParam(router)).toBe('beds'));
    expect(await screen.findByText('Bed drawn just now')).toBeInTheDocument();
    expect(listCalls).toBe(2);
  });

  it('opens "Plan" with the bed selected and in view when a row is chosen', async () => {
    usePlan();
    useBeds();
    const { store, router } = renderRoute('/standorte/sites/site_1/plan?tab=beds');
    await screen.findByTestId('garden-plan-canvas');
    const fitted = screen.getByTestId('garden-plan-zoom-level').textContent;
    fireEvent.click((await screen.findByText('Bed far')).closest('tr')!);

    await waitFor(() => expect(tabParam(router)).toBe('plan'));
    expectTab('plan');
    expect(store.getState().gardenPlan?.selection).toEqual([{ entity: 'location', key: 'loc_b' }]);
    expect(screen.getByTestId('garden-plan-zoom-level').textContent).not.toBe(fitted);
    // The clicked row is hidden now; the focus moved with the bed onto the plan.
    await waitFor(() => expect(screen.getByTestId('garden-plan-canvas')).toHaveFocus());
  });

  it('stays on "Beete" for a bed that is not drawn yet, and says so', async () => {
    usePlan();
    server.use(
      http.get(BEDS_URL, () =>
        HttpResponse.json([bedListItem('loc_x', { name: 'Stock bed', geometry: null, bbox: null })]),
      ),
    );
    const { router } = renderRoute('/standorte/sites/site_1/plan?tab=beds');
    fireEvent.click((await screen.findByText('Stock bed')).closest('tr')!);
    expect(await screen.findByText('"Stock bed" is not drawn on the garden plan yet.')).toBeInTheDocument();
    expect(tabParam(router)).toBe('beds');
  });
});

describe('garden plan tabs: accessibility', () => {
  it('ties every tab to its panel and has no axe violations on the plan and the beds tab', async () => {
    usePlan();
    useBeds();
    const { container, router } = renderRoute();
    await screen.findByTestId('garden-plan-canvas');
    for (const name of ['plan', 'list', 'beds'] as const) {
      const controlled = tab(name).getAttribute('aria-controls');
      expect(controlled).not.toBeNull();
      expect(document.getElementById(controlled!)).toHaveAttribute('role', 'tabpanel');
    }
    expect(editorPanel()).toHaveAttribute('aria-labelledby', 'garden-plan-tab-plan');
    expect(bedsPanel()).toHaveAttribute('aria-labelledby', 'garden-plan-tab-beds');
    await expectNoA11yViolations(container);

    fireEvent.click(tab('beds'));
    await waitFor(() => expect(tabParam(router)).toBe('beds'));
    await screen.findByText('Bed far');
    await expectNoA11yViolations(container);
  });
});
