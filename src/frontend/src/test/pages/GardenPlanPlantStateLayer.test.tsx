/**
 * The plant-state layer in the real plan route (REQ-053 GP-UX-061, #2488): a toggle that starts off, the state
 * channels on the overview once it is on, the dependent filter "only plants that need attention" with its stored
 * choice, the legend section, and no request for plant states while the layer is off.
 */
import { act, cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import { RouterProvider, createMemoryRouter } from 'react-router-dom';
import { SnackbarProvider } from 'notistack';
import { http, HttpResponse } from 'msw';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import GardenPlanRoute from '@/features/gardenPlanner/routes/GardenPlanRoute';
import { refreshGardenPlan, selectGardenPlanState } from '@/features/gardenPlanner/state/gardenPlanSlice';
import type { PlantStateWire } from '@/features/gardenPlanner/planting/plantStateApi';
import { forgetMissingPhaseKeys } from '@/features/gardenPlanner/planting/phaseColors';
import { rootReducer } from '@/store/rootReducer';
import { ThemeContextProvider } from '@/theme';
import { expectNoA11yViolations } from '@/test/a11y/expectNoA11yViolations';
import { bed, planResponse } from '@/test/gardenPlanFixtures';
import { authState, tenantState } from '@/test/helpers';
import { server } from '@/test/mocks/server';

const BASE = '/api/v1/t/:tenant';
const TODAY = new Date().toISOString().slice(0, 10);

function wire(plantKey: string, overdue: boolean): PlantStateWire {
  return {
    plant_key: plantKey,
    instance_id: plantKey.toUpperCase(),
    species_key: 'sp_tomato',
    species_name: 'Tomato',
    planted_on: TODAY,
    lifecycle: 'active',
    phase: { key: 'ph_flower', name: 'flowering', elapsed_d: 3 },
    last_care: {},
    attention: [],
    harvest: { ready: false },
    inputs: {
      open_tasks: overdue ? [{ category: 'pruning', due: '2020-01-01' }] : [],
      open_findings: 0,
      frost_risk: false,
      harvest_batches: 0,
      phase: { key: 'ph_flower', started_on: TODAY, typical_days: 30, allows_harvest: false, is_terminal: false },
    },
  };
}

let stateRequests: string[] = [];
let phaseRequests: string[] = [];

interface PlanFixture {
  /** Distance of the three plants in metres: 0.4 m reaches marker LOD at the fit zoom, 0.01 m stays a cluster. */
  spacingM?: number;
  /** The phase key of the plants; `ph_seq` stands for a phase-sequence entry `/growth-phases/{key}` answers 404 for. */
  phaseKey?: string;
}

function usePlanWithPlants({ spacingM = 0.4, phaseKey = 'ph_flower' }: PlanFixture = {}) {
  const slots = [0, 1, 2].map((i) => ({
    key: `s${i}`,
    slot_id: `A${i}`,
    location_key: 'loc_a',
    plan_geometry: { origin: [2.2 + i * spacingM, 3] as [number, number] },
  }));
  const plants = [0, 1, 2].map((i) => ({
    key: `pl_${i}`,
    instance_id: `TOM-${i}`,
    species_key: 'sp_tomato',
    slot_key: `s${i}`,
    phase_key: phaseKey,
  }));
  const body = planResponse({
    // No site outline: the route fits the view to the bed, which puts its 0.4 m spacing at marker LOD.
    plan: null,
    locations: [bed('loc_a', 2, 2, { name: 'North bed' })],
    garden_objects: [],
    slots,
    plants,
  });
  server.use(
    http.get(`${BASE}/sites/:key/plan`, () => HttpResponse.json(body)),
    http.get('/api/v1/growth-phases/:key', ({ params }) => {
      phaseRequests.push(String(params.key));
      if (params.key === 'ph_seq') {
        return HttpResponse.json(
          { error_id: 'e1', error_code: 'NOT_FOUND', message: 'Not found', details: [], path: '', method: 'GET' },
          { status: 404 },
        );
      }
      return HttpResponse.json({ key: 'ph_flower', name: 'flowering', display_name: 'Flowering' });
    }),
    http.get(`${BASE}/locations/:key/plant-states`, ({ params }) => {
      stateRequests.push(String(params.key));
      return HttpResponse.json([wire('pl_0', true), wire('pl_1', false), wire('pl_2', false)]);
    }),
  );
}

let store = configureStore({ reducer: rootReducer });

function renderRoute(role?: 'grower') {
  store = configureStore({
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

const layerMarkers = (container: HTMLElement) =>
  [...container.querySelectorAll('g[data-plan-state-layer="true"]')].map((node) => node.getAttribute('data-plan-key'));

beforeEach(() => {
  window.localStorage.clear();
  stateRequests = [];
  phaseRequests = [];
  forgetMissingPhaseKeys();
});
afterEach(() => {
  cleanup();
  window.localStorage.clear();
});

describe('plant-state layer in the plan', () => {
  it('starts hidden with a named toggle, a disabled filter and no plant-state request', async () => {
    usePlanWithPlants();
    const { container } = renderRoute();
    const toggle = await screen.findByTestId('garden-plan-layer-plantState');
    expect(toggle).toHaveAttribute('aria-label', 'Show plant state');
    expect(toggle).toHaveAttribute('aria-pressed', 'false');
    const filter = screen.getByTestId('garden-plan-attention-filter');
    expect(filter).toHaveAttribute('aria-label', 'Only show plants that need attention');
    // disabled by aria-disabled: still in the tab order, and its reason is announced as its description
    expect(filter).toHaveAttribute('aria-disabled', 'true');
    expect(filter).not.toBeDisabled();
    expect(filter.tabIndex).toBe(0);
    filter.focus();
    expect(filter).toHaveFocus();
    expect(filter).toHaveAccessibleDescription(
      'Switch on the "Plant state" layer first, then you can filter by what needs attention.',
    );
    // a click while disabled changes nothing
    fireEvent.click(filter);
    expect(filter).toHaveAttribute('aria-pressed', 'false');
    expect(window.localStorage.getItem('kp_garden_plan_attention_filter')).toBeNull();
    await expectNoA11yViolations(screen.getByTestId('garden-plan-view-bar'));
    expect(layerMarkers(container)).toEqual([]);
    expect(screen.queryByTestId('garden-plan-legend-plantState')).toBeNull();
    expect(stateRequests).toEqual([]);
  });

  it('draws the states of the bed at marker LOD, adds the legend and stores the switch', async () => {
    usePlanWithPlants();
    const { container } = renderRoute();
    fireEvent.click(await screen.findByTestId('garden-plan-layer-plantState'));
    await waitFor(() => expect(layerMarkers(container)).toEqual(['pl_0', 'pl_1', 'pl_2']));
    expect(stateRequests).toEqual(['loc_a']);
    expect(container.querySelector('g[data-plan-key="pl_0"] [data-plan-badge-reason="overdue"]')).not.toBeNull();
    // phase colour of "flowering" on the disc
    await waitFor(() =>
      expect(container.querySelector('g[data-plan-key="pl_1"] [data-plan-lifecycle]')?.getAttribute('fill')).toBe('#AB47BC'),
    );
    const legend = screen.getByTestId('garden-plan-legend-plantState');
    expect(legend).toHaveTextContent('Plant state');
    await waitFor(() => expect(legend).toHaveTextContent('Flowering'));
    expect(JSON.parse(window.localStorage.getItem('kp_garden_plan_layers') ?? '{}')).toMatchObject({ plantState: true });
    await expectNoA11yViolations(screen.getByTestId('garden-plan-layer-legend'));
  });

  it('filters to the plants that need attention, remembers the choice and is accessible', async () => {
    usePlanWithPlants();
    const { container } = renderRoute();
    fireEvent.click(await screen.findByTestId('garden-plan-layer-plantState'));
    await waitFor(() => expect(layerMarkers(container)).toHaveLength(3));
    const filter = screen.getByTestId('garden-plan-attention-filter');
    expect(filter).not.toHaveAttribute('aria-disabled');
    fireEvent.click(filter);
    expect(filter).toHaveAttribute('aria-pressed', 'true');
    expect(layerMarkers(container)).toEqual(['pl_0']);
    expect(window.localStorage.getItem('kp_garden_plan_attention_filter')).toBe('true');
    await expectNoA11yViolations(screen.getByTestId('garden-plan-view-bar'));

    // a later visit keeps both choices
    cleanup();
    renderRoute();
    const again = await screen.findByTestId('garden-plan-attention-filter');
    expect(again).not.toHaveAttribute('aria-disabled');
    expect(again).toHaveAttribute('aria-pressed', 'true');
  });

  it('reads no plant state and no growth phase for a zoomed-out plan with the layer on', async () => {
    usePlanWithPlants({ spacingM: 0.01 });
    const { container } = renderRoute();
    fireEvent.click(await screen.findByTestId('garden-plan-layer-plantState'));
    await screen.findByTestId('garden-plan-legend-plantState');
    expect(container.querySelector('[data-plan-cluster="loc_a"]')).not.toBeNull();
    await new Promise((resolve) => setTimeout(resolve, 50));
    expect(stateRequests).toEqual([]);
    expect(phaseRequests).toEqual([]);
  });

  it('asks a phase key that answered 404 only once per session, even after the plan is opened again', async () => {
    usePlanWithPlants({ phaseKey: 'ph_seq' });
    const { container } = renderRoute();
    fireEvent.click(await screen.findByTestId('garden-plan-layer-plantState'));
    await waitFor(() => expect(layerMarkers(container)).toHaveLength(3));
    await waitFor(() => expect(phaseRequests).toEqual(['ph_seq']));
    cleanup();
    const again = renderRoute();
    await waitFor(() => expect(layerMarkers(again.container)).toHaveLength(3));
    await new Promise((resolve) => setTimeout(resolve, 50));
    expect(stateRequests).toEqual(['loc_a', 'loc_a']);
    expect(phaseRequests).toEqual(['ph_seq']);
  });

  it('reads the loaded states again after the plan was saved or reloaded (a new revision)', async () => {
    usePlanWithPlants();
    const { container } = renderRoute();
    fireEvent.click(await screen.findByTestId('garden-plan-layer-plantState'));
    await waitFor(() => expect(layerMarkers(container)).toHaveLength(3));
    expect(stateRequests).toEqual(['loc_a']);
    const plan = selectGardenPlanState(store.getState()).plan;
    if (!plan) throw new Error('plan not loaded');
    act(() => {
      store.dispatch(refreshGardenPlan.fulfilled({ ...plan, revision: plan.revision + 1 }, 'r2', plan.siteKey));
    });
    await waitFor(() => expect(stateRequests).toEqual(['loc_a', 'loc_a']));
    await waitFor(() => expect(layerMarkers(container)).toHaveLength(3));
  });

  it('reads the loaded states again after a zone was saved in the zone panel, and not the plan', async () => {
    usePlanWithPlants();
    let planReads = 0;
    const zone = {
      key: 'z1',
      site_key: 'site_1',
      name: 'Drip line',
      irrigation_type: 'drip',
      flow_rate_source: 'manual',
      flow_rate_ha_entity_bound: false,
      color: '#2E7D32',
      location_keys: ['loc_a'],
    };
    server.use(
      // Counts every plan read and falls through to the plan of usePlanWithPlants.
      http.get(`${BASE}/sites/:key/plan`, () => {
        planReads += 1;
        return undefined;
      }),
      http.get(`${BASE}/sites/:key/irrigation-zones`, () => HttpResponse.json([zone])),
      http.get(`${BASE}/irrigation-zones/z1/status`, () =>
        HttpResponse.json({ consumption_liters_30d: 0, consumption_sources: [], hints: [] }),
      ),
      http.patch(`${BASE}/irrigation-zones/z1`, async ({ request }) => {
        Object.assign(zone, (await request.json()) as object);
        return HttpResponse.json(zone);
      }),
    );
    const { container } = renderRoute('grower');
    fireEvent.click(await screen.findByTestId('garden-plan-layer-plantState'));
    await waitFor(() => expect(layerMarkers(container)).toHaveLength(3));
    expect(stateRequests).toEqual(['loc_a']);
    const readsBefore = planReads;
    expect(readsBefore).toBeGreaterThan(0);
    const user = userEvent.setup();
    await user.click(screen.getByTestId('garden-plan-zones-open'));
    await user.click(await screen.findByTestId('garden-plan-zone-row-z1'));
    await user.clear(await screen.findByTestId('garden-plan-zone-name'));
    await user.type(screen.getByTestId('garden-plan-zone-name'), 'Back line');
    await user.click(screen.getByTestId('garden-plan-zone-save'));
    await waitFor(() => expect(stateRequests).toEqual(['loc_a', 'loc_a']));
    await waitFor(() => expect(screen.getByRole('heading', { name: 'Zone Back line' })).toBeInTheDocument());
    expect(planReads).toBe(readsBefore);
  });
});
