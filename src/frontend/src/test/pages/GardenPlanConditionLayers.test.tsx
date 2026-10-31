/**
 * The site-condition layers in the real plan route (REQ-053 GP-FR-169, #2487): a toggle each that starts off,
 * the overlay drawn only over beds that carry a value, the legend section and the stored switch.
 */
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import { RouterProvider, createMemoryRouter } from 'react-router-dom';
import { SnackbarProvider } from 'notistack';
import { http, HttpResponse } from 'msw';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import GardenPlanRoute from '@/features/gardenPlanner/routes/GardenPlanRoute';
import { rootReducer } from '@/store/rootReducer';
import { ThemeContextProvider } from '@/theme';
import { expectNoA11yViolations } from '@/test/a11y/expectNoA11yViolations';
import { bed, planResponse } from '@/test/gardenPlanFixtures';
import { server } from '@/test/mocks/server';

const PLAN_URL = '/api/v1/t/:tenant/sites/:key/plan';

function usePlanWithConditions() {
  const body = planResponse({
    locations: [
      bed('loc_a', 2, 2, {
        name: 'North bed',
        site_conditions: { sun_profile: { sun_window: 'morning' }, microclimate: { frost_risk: 'high' } },
        soil_profile: { drainage: 'poor' },
      }),
      bed('loc_b', 6, 2, { name: 'South bed' }),
    ],
    garden_objects: [],
  });
  server.use(http.get(PLAN_URL, () => HttpResponse.json(body)));
}

function renderRoute() {
  const store = configureStore({ reducer: rootReducer });
  const router = createMemoryRouter(
    [{ path: 'standorte/sites/:key/plan', element: <GardenPlanRoute /> }],
    { initialEntries: ['/standorte/sites/site_1/plan?mode=plan'] },
  );
  return render(
    <Provider store={store}>
      <ThemeContextProvider>
        <SnackbarProvider>
          <RouterProvider router={router} />
        </SnackbarProvider>
      </ThemeContextProvider>
    </Provider>,
  );
}

beforeEach(() => window.localStorage.clear());
afterEach(() => {
  cleanup();
  window.localStorage.clear();
});

const CASES = [
  { id: 'sun', label: 'Show sun window', value: 'morning', legend: 'Morning' },
  { id: 'moisture', label: 'Show drainage', value: 'poor', legend: 'Poor' },
  { id: 'frost', label: 'Show frost risk', value: 'high', legend: 'High' },
] as const;

describe('site-condition layers in the plan', () => {
  it('start hidden, with a toggle each that names what it shows', async () => {
    usePlanWithConditions();
    const { container } = renderRoute();
    for (const { id, label } of CASES) {
      const toggle = await screen.findByTestId(`garden-plan-layer-${id}`);
      expect(toggle).toHaveAttribute('aria-label', label);
      expect(toggle).toHaveAttribute('aria-pressed', 'false');
      expect(container.querySelector(`[data-testid="garden-plan-${id}-layer"]`)).toBeNull();
    }
    expect(screen.queryByTestId('garden-plan-layer-legend')).toBeNull();
  });

  it.each(CASES)('$id: draws the bed with a value, skips the other, adds the legend and stores the switch', async ({
    id,
    value,
    legend,
  }) => {
    usePlanWithConditions();
    const { container } = renderRoute();
    fireEvent.click(await screen.findByTestId(`garden-plan-layer-${id}`));
    const layer = container.querySelector(`[data-testid="garden-plan-${id}-layer"]`) as SVGElement;
    expect(layer.querySelector('[data-condition-bed="loc_a"]')?.getAttribute('data-condition-value')).toBe(value);
    expect(layer.querySelector('[data-condition-bed="loc_b"]')).toBeNull();
    expect(screen.getByTestId(`garden-plan-legend-${id}`)).toHaveTextContent(legend);
    expect(JSON.parse(window.localStorage.getItem('kp_garden_plan_layers') ?? '{}')).toMatchObject({ [id]: true });
    await expectNoA11yViolations(screen.getByTestId('garden-plan-layer-legend'));
  });

  it('has no accessibility violations in the layer group of the view bar', async () => {
    usePlanWithConditions();
    renderRoute();
    const toggle = await screen.findByTestId('garden-plan-layer-frost');
    fireEvent.click(toggle);
    expect(toggle).toHaveAttribute('aria-pressed', 'true');
    await expectNoA11yViolations(toggle.parentElement as HTMLElement);
  });
});
