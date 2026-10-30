/**
 * The irrigation layers in the real plan route (REQ-053 WP 7.6 / 7.7): the registry toggles, the zone layer drawn
 * over its beds, the "last watered" layer worded as days since, the legend, the bed info and the lazy zone panel.
 */
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
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
import { authState, tenantState } from '@/test/helpers';
import { server } from '@/test/mocks/server';
import type { IrrigationZone } from '@/features/gardenPlanner/zones/zoneTypes';

const PLAN_URL = '/api/v1/t/:tenant/sites/:key/plan';
const DAY_MS = 86_400_000;

function usePlanWithZone() {
  const threeDaysAgo = new Date(Date.now() - 3 * DAY_MS).toISOString();
  const body = planResponse({
    locations: [
      bed('loc_a', 2, 2, { name: 'North bed', irrigation_zone_key: 'z1', last_watered_at: threeDaysAgo }),
      bed('loc_b', 6, 2, { name: 'South bed' }),
    ],
    garden_objects: [],
    zones: [
      {
        key: 'z1',
        name: 'Drip line',
        irrigation_type: 'drip',
        color: '#2E7D32',
        location_keys: ['loc_a'],
      },
    ],
  });
  server.use(
    http.get(PLAN_URL, () => HttpResponse.json(body)),
    http.get('/api/v1/t/:tenant/sites/:key/irrigation-zones', () =>
      HttpResponse.json([
        {
          key: 'z1',
          site_key: 'site_1',
          name: 'Drip line',
          irrigation_type: 'drip',
          flow_rate_source: 'manual',
          flow_rate_ha_entity_bound: false,
          color: '#2E7D32',
          location_keys: ['loc_a'],
        },
      ]),
    ),
  );
}

function renderRoute(role?: 'grower' | 'lead') {
  const store = configureStore({
    reducer: rootReducer,
    preloadedState: (role ? { ...tenantState(role), ...authState() } : undefined) as never,
  });
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

describe('irrigation layers in the plan', () => {
  it('start hidden, with a toggle each that names what it shows', async () => {
    usePlanWithZone();
    const { container } = renderRoute();
    const zones = await screen.findByTestId('garden-plan-layer-zones');
    expect(zones).toHaveAttribute('aria-label', 'Show irrigation zones');
    expect(zones).toHaveAttribute('aria-pressed', 'false');
    expect(screen.getByTestId('garden-plan-layer-lastWatered')).toHaveAttribute('aria-label', 'Show last watered');
    expect(container.querySelector('[data-testid="garden-plan-zone-layer"]')).toBeNull();
    expect(screen.queryByTestId('garden-plan-layer-legend')).toBeNull();
  });

  it('draws the zone over its bed, lists it in the legend and remembers the switch', async () => {
    usePlanWithZone();
    const { container } = renderRoute();
    fireEvent.click(await screen.findByTestId('garden-plan-layer-zones'));
    expect(container.querySelector('[data-zone-key="z1"][data-zone-bed="loc_a"]')).not.toBeNull();
    expect(container.querySelector('[data-zone-bed="loc_b"]')).toBeNull();
    expect(screen.getByTestId('garden-plan-legend-zones')).toHaveTextContent('Drip line, Drip irrigation');
    expect(JSON.parse(window.localStorage.getItem('kp_garden_plan_layers') ?? '{}')).toMatchObject({ zones: true });
  });

  it('draws days since the last watering per bed and never claims a need', async () => {
    usePlanWithZone();
    const { container } = renderRoute();
    fireEvent.click(await screen.findByTestId('garden-plan-layer-lastWatered'));
    const layer = container.querySelector('[data-testid="garden-plan-watered-layer"]') as SVGElement;
    expect(layer.querySelector('[data-watered-bed="loc_a"]')?.getAttribute('data-watered-class')).toBe('d2_3');
    expect(layer.querySelector('[data-watered-bed="loc_b"]')).toBeNull();
    const legend = screen.getByTestId('garden-plan-legend-watered');
    expect(legend).toHaveTextContent('0 to 1 day since');
    expect(legend).toHaveTextContent('More than 7 days since');
    expect(legend).toHaveTextContent('No hatching: no watering recorded');
    expect(legend.textContent ?? '').not.toMatch(/needs? water\b(?!\.)/i);
    await expectNoA11yViolations(screen.getByTestId('garden-plan-layer-legend'));
  });

  it('shows the zone and the days since in the info of the selected bed', async () => {
    usePlanWithZone();
    const { container } = renderRoute();
    await screen.findByTestId('garden-plan-canvas');
    const node = container.querySelector('[data-plan-key="loc_a"]') as SVGElement;
    node.focus();
    fireEvent.keyDown(node, { key: 'Enter' });
    expect(await screen.findByTestId('garden-plan-panel-zone')).toHaveTextContent('Irrigation zone: 1. Drip line');
    expect(screen.getByTestId('garden-plan-panel-last-watered')).toHaveTextContent('Last watered: 3 days since');
  });

  it('opens the zone panel as a chunk of its own and lists the zone', async () => {
    usePlanWithZone();
    renderRoute();
    const open = await screen.findByTestId('garden-plan-zones-open');
    expect(open).toHaveAttribute('aria-expanded', 'false');
    await userEvent.setup().click(open);
    expect(open).toHaveAttribute('aria-expanded', 'true');
    const row = await screen.findByTestId('garden-plan-zone-row-z1');
    expect(row).toHaveTextContent('Drip line');
    await waitFor(() => expect(screen.getByTestId('garden-plan-zone-panel')).toBeInTheDocument());
  });

  it('moves the focus into the panel, to its title on a change of view, and back to the button on close', async () => {
    usePlanWithZone();
    server.use(
      http.get('/api/v1/t/:tenant/irrigation-zones/z1/status', () =>
        HttpResponse.json({ consumption_liters_30d: 0, consumption_sources: [], hints: [] }),
      ),
    );
    renderRoute();
    const user = userEvent.setup();
    const open = await screen.findByTestId('garden-plan-zones-open');
    await user.click(open);
    const title = await screen.findByRole('heading', { level: 3, name: 'Irrigation zones' });
    await waitFor(() => expect(title).toHaveFocus());
    // A member without write rights here: the zone opens as its status with a way back to the list.
    await user.click(await screen.findByTestId('garden-plan-zone-row-z1'));
    await screen.findByTestId('garden-plan-zone-status');
    expect(title).toHaveFocus();
    await user.click(screen.getByRole('button', { name: 'Cancel' }));
    await screen.findByTestId('garden-plan-zone-row-z1');
    expect(title).toHaveFocus();
    await user.click(screen.getByTestId('garden-plan-zone-panel-close'));
    await waitFor(() => expect(screen.queryByTestId('garden-plan-zone-panel')).toBeNull());
    expect(open).toHaveFocus();
  });
});

describe('what a zone change reads again', () => {
  /** Counts the plan reads; the zone endpoint answers the current list. */
  function countPlanReads(): { reads: () => number } {
    const threeDaysAgo = new Date(Date.now() - 3 * DAY_MS).toISOString();
    let reads = 0;
    let wateredToday = false;
    const list: IrrigationZone[] = [
      {
        key: 'z1',
        site_key: 'site_1',
        name: 'Drip line',
        irrigation_type: 'drip',
        flow_rate_source: 'manual',
        flow_rate_ha_entity_bound: false,
        color: '#2E7D32',
        location_keys: ['loc_a'],
      },
    ];
    server.use(
      http.get(PLAN_URL, () => {
        reads += 1;
        return HttpResponse.json(
          planResponse({
            locations: [
              bed('loc_a', 2, 2, {
                name: 'North bed',
                irrigation_zone_key: 'z1',
                last_watered_at: wateredToday ? new Date().toISOString() : threeDaysAgo,
              }),
              bed('loc_b', 6, 2, { name: 'South bed' }),
            ],
            garden_objects: [],
            zones: list.map(({ key, name, irrigation_type, color, location_keys }) => ({
              key,
              name,
              irrigation_type,
              color,
              location_keys,
            })),
          }),
        );
      }),
      http.get('/api/v1/t/:tenant/sites/:key/irrigation-zones', () => HttpResponse.json(list)),
      http.get('/api/v1/t/:tenant/irrigation-zones/z1/status', () =>
        HttpResponse.json({ consumption_liters_30d: 0, consumption_sources: [], hints: [] }),
      ),
      http.patch('/api/v1/t/:tenant/irrigation-zones/z1', async ({ request }) => {
        Object.assign(list[0], (await request.json()) as object);
        return HttpResponse.json(list[0]);
      }),
      http.post('/api/v1/t/:tenant/irrigation-zones/z1/log-watering', () => {
        wateredToday = true;
        return HttpResponse.json(
          {
            event_keys: ['e1'],
            shares: [{ location_key: 'loc_a', liters: 5 }],
            allocation: 'by_area',
            performed_at: new Date().toISOString(),
            skipped_location_keys: [],
          },
          { status: 201 },
        );
      }),
    );
    return { reads: () => reads };
  }

  it('reads the zones again after a zone is saved, but not the whole plan', async () => {
    const counter = countPlanReads();
    const { container } = renderRoute('grower');
    const user = userEvent.setup();
    fireEvent.click(await screen.findByTestId('garden-plan-layer-zones'));
    const before = counter.reads();
    await user.click(screen.getByTestId('garden-plan-zones-open'));
    await user.click(await screen.findByTestId('garden-plan-zone-row-z1'));
    await user.clear(screen.getByTestId('garden-plan-zone-name'));
    await user.type(screen.getByTestId('garden-plan-zone-name'), 'Back line');
    await user.click(screen.getByTestId('garden-plan-zone-save'));
    // The legend follows the reloaded zone list ...
    await waitFor(() => expect(screen.getByTestId('garden-plan-legend-zones')).toHaveTextContent('Back line'));
    expect(container.querySelector('[data-zone-key="z1"][data-zone-bed="loc_a"]')).not.toBeNull();
    // ... and the plan was not read again for it: nothing of the plan's last-watered data depends on a zone.
    await new Promise((resolve) => setTimeout(resolve, 50));
    expect(counter.reads()).toBe(before);
  });

  it('reads the last-watered data again after a watering round, so the layer moves on', async () => {
    const counter = countPlanReads();
    const { container } = renderRoute('grower');
    const user = userEvent.setup();
    fireEvent.click(await screen.findByTestId('garden-plan-layer-lastWatered'));
    const layer = () => container.querySelector('[data-watered-bed="loc_a"]');
    expect(layer()?.getAttribute('data-watered-class')).toBe('d2_3');
    const before = counter.reads();
    await user.click(screen.getByTestId('garden-plan-zones-open'));
    await user.click(await screen.findByTestId('garden-plan-zone-row-z1'));
    await user.click(await screen.findByTestId('garden-plan-zone-round-open'));
    await user.type(screen.getByTestId('garden-plan-round-volume'), '5');
    await user.click(screen.getByTestId('garden-plan-round-submit'));
    await screen.findByTestId('garden-plan-round-result');
    await waitFor(() => expect(layer()?.getAttribute('data-watered-class')).toBe('d0_1'));
    expect(counter.reads()).toBe(before + 1);
  });
});
