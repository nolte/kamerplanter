/**
 * Plant states on the bed's plan tab (REQ-053 WP 3.7: GP-FR-190/191, GP-UX-058/059/060/062,
 * GP-ACC-050/051): the marker channels, the info bubble from the local state - with no request of its own -
 * the label a screen reader gets, Esc, and the legend.
 */
import { cleanup, fireEvent, screen, waitFor, within } from '@testing-library/react';
import { http, HttpResponse } from 'msw';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { expectNoA11yViolations } from '@/test/a11y/expectNoA11yViolations';
import { bed, planResponse } from '@/test/gardenPlanFixtures';
import { authState, createTestStore, renderWithProviders, tenantState } from '@/test/helpers';
import { server } from '@/test/mocks/server';
import BedPlanTab from './BedPlanTab';
import { bedSummary } from './bedTestKit';
import type { PlantStateWire } from '../planting/plantStateApi';

const BASE = '/api/v1/t/:tenant';
const TODAY = new Date().toISOString().slice(0, 10);

function daysFromToday(days: number): string {
  return new Date(Date.now() + days * 86_400_000).toISOString().slice(0, 10);
}

function wire(overrides: Partial<PlantStateWire> = {}): PlantStateWire {
  return {
    plant_key: 'pl_1',
    slot_key: 's1',
    slot_id: 'A1',
    instance_id: 'TOM-1',
    species_key: 'sp_tomato',
    species_name: 'Tomato',
    scientific_name: 'Solanum lycopersicum',
    cultivar_name: 'Roma',
    planted_on: daysFromToday(-70),
    lifecycle: 'active',
    phase: { key: 'ph_flower', name: 'Flowering', elapsed_d: 21, typical_d: 60, fraction: 0.35 },
    last_care: { watering: `${daysFromToday(-3)}T07:00:00Z` },
    next_task: { name: 'Prune suckers', category: 'pruning', due: daysFromToday(-2) },
    attention: [],
    finding_label: 'Aphids',
    harvest: { ready: false },
    inputs: {
      open_tasks: [
        { category: 'pruning', due: daysFromToday(-2) },
        { category: 'watering', due: daysFromToday(-1) },
      ],
      open_findings: 1,
      frost_risk: false,
      harvest_batches: 0,
      phase: { key: 'ph_flower', started_on: daysFromToday(-21), typical_days: 60, allows_harvest: false, is_terminal: false },
    },
    ...overrides,
  };
}

let requests: string[] = [];

function usePlan(states: PlantStateWire[] = [wire()]) {
  server.use(
    http.get(`${BASE}/sites/:key/plan`, () =>
      HttpResponse.json(
        planResponse({
          locations: [bed('loc_b03', 1, 1)],
          garden_objects: [],
          slots: [
            { key: 's1', slot_id: 'A1', location_key: 'loc_b03', plan_geometry: { origin: [1.3, 1.3] } },
            { key: 's2', slot_id: 'A2', location_key: 'loc_b03', plan_geometry: { origin: [1.6, 1.6] } },
          ],
          plants: [{ key: 'pl_1', instance_id: 'TOM-1', species_key: 'sp_tomato', slot_key: 's1', phase_key: 'ph_flower' }],
        }),
      ),
    ),
    http.get('/api/v1/growth-phases/:key', () =>
      HttpResponse.json({ key: 'ph_flower', name: 'Flowering', display_name: 'Flowering' }),
    ),
    http.get(`${BASE}/locations/:key/plant-states`, () => HttpResponse.json(states)),
  );
}

function renderTab() {
  return renderWithProviders(<BedPlanTab bed={bedSummary()} planLinkVisible />, {
    store: createTestStore({ ...tenantState('grower'), ...authState() }),
  });
}

async function marker(container: HTMLElement): Promise<SVGGElement> {
  return waitFor(() => {
    const element = container.querySelector('g[data-plan-key="pl_1"][aria-label*="Tomato"]');
    expect(element).not.toBeNull();
    return element as SVGGElement;
  });
}

beforeEach(() => {
  requests = [];
  server.events.on('request:start', ({ request }) => {
    requests.push(`${request.method} ${new URL(request.url).pathname}`);
  });
});
afterEach(() => {
  server.events.removeAllListeners();
  cleanup();
});

describe('marker channels', () => {
  it('labels the marker with species, phase and what needs attention (GP-UX-062, GP-ACC-050)', async () => {
    usePlan();
    const { container } = renderTab();
    const element = await marker(container);
    // The port ran on the inputs: one open finding, two overdue tasks - problem first, then overdue.
    expect(element.getAttribute('aria-label')).toBe('Tomato, Flowering, Finding: Aphids, 2 tasks overdue');
  });

  it('draws exactly one badge: the most urgent reason (GP-UX-060)', async () => {
    usePlan();
    const { container } = renderTab();
    const element = await marker(container);
    const badges = element.querySelectorAll('[data-plan-badge-reason]');
    expect(badges).toHaveLength(1);
    expect(badges[0].getAttribute('data-plan-badge-reason')).toBe('problem');
    expect(badges[0].getAttribute('data-plan-badge-shape')).toBe('triangle');
  });

  it('draws no badge for a plant with nothing to do and a solid ring for a growing one', async () => {
    usePlan([
      wire({
        inputs: { ...wire().inputs, open_tasks: [], open_findings: 0 },
      }),
    ]);
    const { container } = renderTab();
    const element = await marker(container);
    expect(element.querySelector('[data-plan-badge-reason]')).toBeNull();
    const disc = element.querySelector('circle') as SVGCircleElement;
    expect(disc.getAttribute('data-plan-lifecycle')).toBe('active');
    expect(disc.getAttribute('stroke-dasharray')).toBeNull();
  });

  it('shows a harvesting plant with a second ring', async () => {
    usePlan([
      wire({
        inputs: { ...wire().inputs, open_tasks: [], open_findings: 0, harvest_batches: 1 },
      }),
    ]);
    const { container } = renderTab();
    const element = await marker(container);
    expect(element.querySelectorAll('circle[fill="none"]').length).toBeGreaterThanOrEqual(1);
    expect(element.querySelector('circle')?.getAttribute('data-plan-lifecycle')).toBe('harvesting');
  });

  it('keeps the plain marker when the states cannot be read', async () => {
    usePlan();
    server.use(http.get(`${BASE}/locations/:key/plant-states`, () => HttpResponse.json({}, { status: 500 })));
    const { container } = renderTab();
    const plain = await waitFor(() => {
      const element = container.querySelector('g[data-plan-key="pl_1"]');
      expect(element).not.toBeNull();
      return element as SVGGElement;
    });
    expect(plain.getAttribute('aria-label')).toBe('Plant TOM-1');
    expect(screen.queryByTestId('plant-state-legend')).toBeNull();
  });
});

describe('phase colour', () => {
  it('colours a plant of a phase-sequence species by the phase name the states carry', async () => {
    usePlan([wire({ phase: { key: 'ph_flower', name: 'Flowering', elapsed_d: 21, typical_d: 60, fraction: 0.35 } })]);
    // `/growth-phases/{key}` does not know the entry key of a sequence-driven species.
    server.use(http.get('/api/v1/growth-phases/:key', () => HttpResponse.json({}, { status: 404 })));
    const { container } = renderTab();
    const element = await marker(container);
    await waitFor(() => expect(element.querySelector('circle')?.getAttribute('fill')).toBe('#AB47BC'));
  });
});

describe('plant info (GP-FR-190, GP-ACC-051)', () => {
  it('appears on keyboard focus with the facts of the plant and without any further request', async () => {
    usePlan();
    const { container } = renderTab();
    const element = await marker(container);
    // The bed's own reads are done once the phase colour has arrived; whatever follows is the hover's doing.
    await waitFor(() => expect(element.querySelector('circle')?.getAttribute('fill')).toBe('#AB47BC'));
    const before = requests.length;

    fireEvent.focus(element);

    const bubble = await screen.findByTestId('plant-info-popover');
    expect(bubble).toHaveTextContent('Tomato');
    expect(bubble).toHaveTextContent('Solanum lycopersicum · Roma');
    expect(bubble).toHaveTextContent('Phase: Flowering · 21 of 60 days');
    expect(bubble).toHaveTextContent('Prune suckers');
    expect(bubble).toHaveTextContent('Finding: Aphids');
    expect(bubble).toHaveTextContent('2 tasks overdue');
    expect(within(bubble).getByTestId('plant-info-content').querySelectorAll('li').length).toBeLessThanOrEqual(8);
    // the marker points at the bubble with the same text a screen reader reads
    expect(element.getAttribute('aria-describedby')).toBe(bubble.id);
    // nothing was requested for it: the states came with the bed
    expect(requests.slice(before)).toEqual([]);
    expect(requests.filter((request) => request.includes('plant-states'))).toHaveLength(1);
  });

  it('closes with Esc', async () => {
    usePlan();
    const { container } = renderTab();
    fireEvent.focus(await marker(container));
    await screen.findByTestId('plant-info-popover');

    fireEvent.keyDown(document, { key: 'Escape' });

    await waitFor(() => expect(screen.queryByTestId('plant-info-popover')).toBeNull());
  });

  it('links to the plant detail page', async () => {
    usePlan();
    const { container } = renderTab();
    fireEvent.focus(await marker(container));
    const link = await screen.findByTestId('plant-info-details');
    expect(link.getAttribute('href')).toBe('/pflanzen/plant-instances/pl_1');
  });

  it('has no accessibility violations with the bubble open and the legend shown', async () => {
    usePlan();
    const { container } = renderTab();
    fireEvent.focus(await marker(container));
    await screen.findByTestId('plant-info-popover');
    await expectNoA11yViolations(container);
  });
});

describe('legend (GP-UX-061)', () => {
  it('explains every ring and every badge once states are known', async () => {
    usePlan();
    const { container } = renderTab();
    await marker(container);
    const legend = await screen.findByTestId('plant-state-legend');
    expect(legend.querySelectorAll('li')).toHaveLength(10);
    expect(legend).toHaveTextContent('double ring: harvesting');
    expect(legend).toHaveTextContent('drop: watering due');
  });
});

describe('the clock', () => {
  it('treats a task due today as watering due, not overdue', async () => {
    usePlan([
      wire({
        inputs: {
          ...wire().inputs,
          open_tasks: [{ category: 'watering', due: TODAY }],
          open_findings: 0,
        },
      }),
    ]);
    const { container } = renderTab();
    const element = await waitFor(() => {
      const found = container.querySelector('g[data-plan-key="pl_1"][aria-label*="Watering due"]');
      expect(found).not.toBeNull();
      return found as SVGGElement;
    });
    expect(element.querySelector('[data-plan-badge-reason="water"]')).not.toBeNull();
  });
});
