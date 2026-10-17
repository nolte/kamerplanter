import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import { RouterProvider, createMemoryRouter } from 'react-router-dom';
import { SnackbarProvider } from 'notistack';
import { http, HttpResponse } from 'msw';
import { afterEach, describe, expect, it } from 'vitest';
import GardenPlanRoute from '@/features/gardenPlanner/routes/GardenPlanRoute';
import ModuleGuard from '@/components/common/ModuleGuard';
import { rootReducer } from '@/store/rootReducer';
import { ThemeContextProvider } from '@/theme';
import { expectNoA11yViolations } from '@/test/a11y/expectNoA11yViolations';
import type { GardenPlanResponse } from '@/features/gardenPlanner/model/types';
import { bed, gardenObject, planResponse } from '@/test/gardenPlanFixtures';
import { createStoreWithModuleOverrides, renderWithProviders } from '@/test/helpers';
import { server } from '@/test/mocks/server';

const PLAN_URL = '/api/v1/t/:tenant/sites/:key/plan';

function usePlan(body: GardenPlanResponse = planResponse({ locations: [bed('loc_a', 2, 2)], garden_objects: [gardenObject('go_1', 6, 6)] })) {
  server.use(http.get(PLAN_URL, () => HttpResponse.json(body)));
}

/** A store with the real root reducer, so the lazily injected slice is exercised for real. */
function renderRoute(route = '/standorte/sites/site_1/plan') {
  const store = configureStore({ reducer: rootReducer });
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

  it('explains the empty state of a site without a plan', async () => {
    usePlan(planResponse({ plan: null, locations: [], garden_objects: [], slots: [], plants: [] }));
    renderRoute();
    expect(await screen.findByTestId('garden-plan-empty')).toBeInTheDocument();
    expect(screen.getByText(/No plan has been created for this site yet/)).toBeInTheDocument();
    expect(screen.queryByTestId('garden-plan-canvas')).toBeNull();
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

  it('recognises ?mode=field as a placeholder without changing the plan', async () => {
    usePlan();
    renderRoute('/standorte/sites/site_1/plan?mode=field');
    expect(await screen.findByTestId('garden-plan-field-mode-hint')).toBeInTheDocument();
    expect(await screen.findByTestId('garden-plan-canvas')).toBeInTheDocument();
  });

  it('does not show the field-mode hint on the normal route', async () => {
    usePlan();
    renderRoute();
    await screen.findByTestId('garden-plan-canvas');
    expect(screen.queryByTestId('garden-plan-field-mode-hint')).toBeNull();
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
