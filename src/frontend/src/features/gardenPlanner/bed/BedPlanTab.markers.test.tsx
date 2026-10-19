/**
 * Plant markers on the bed's plan tab (REQ-053 WP 3.6: GP-FR-067, GP-FR-068/069): phase colour with a ring,
 * a dashed ring for an empty or planned position, and the plant panel with its two actions.
 */
import { cleanup, fireEvent, screen, waitFor } from '@testing-library/react';
import { http, HttpResponse } from 'msw';
import { afterEach, describe, expect, it } from 'vitest';
import { bed, planResponse } from '@/test/gardenPlanFixtures';
import { authState, createTestStore, renderWithProviders, tenantState } from '@/test/helpers';
import { server } from '@/test/mocks/server';
import BedPlanTab from './BedPlanTab';
import { bedSummary } from './bedTestKit';

const BASE = '/api/v1/t/:tenant';

function usePlan() {
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
          plants: [{ key: 'pl_1', instance_id: 'TOM-1', species_key: 'sp_tomato', slot_key: 's1', phase_key: 'ph_veg' }],
        }),
      ),
    ),
    http.get('/api/v1/growth-phases/:key', () =>
      HttpResponse.json({ key: 'ph_veg', name: 'Vegetative', display_name: 'Vegetative' }),
    ),
  );
}

function renderTab(role: 'viewer' | 'grower' | 'lead' = 'grower') {
  return renderWithProviders(<BedPlanTab bed={bedSummary()} planLinkVisible />, {
    store: createTestStore({ ...tenantState(role), ...authState() }),
  });
}

afterEach(() => cleanup());

describe('plant markers', () => {
  it('colours a plant by its phase and rings it; an empty position is dashed and unfilled', async () => {
    usePlan();
    const { container } = renderTab();

    const plant = await waitFor(() => {
      const element = container.querySelector('[data-plan-key="pl_1"] circle');
      expect(element).not.toBeNull();
      return element as SVGCircleElement;
    });
    // The phase name decides the colour once the phase has been read.
    await waitFor(() => expect(plant.getAttribute('fill')).toBe('#43A047'));
    expect(plant.getAttribute('stroke')).not.toBe('none');
    expect(plant.getAttribute('stroke-dasharray')).toBeNull();

    const slot = container.querySelector('[data-plan-key="s2"] circle') as SVGCircleElement;
    expect(slot.getAttribute('fill')).toBe('none');
    expect(slot.getAttribute('stroke-dasharray')).toBe('2 2');
  });

  it('keeps the default plant colour when the phase cannot be read', async () => {
    usePlan();
    server.use(http.get('/api/v1/growth-phases/:key', () => HttpResponse.json({}, { status: 500 })));
    const { container } = renderTab();
    const plant = await waitFor(() => {
      const element = container.querySelector('[data-plan-key="pl_1"] circle');
      expect(element).not.toBeNull();
      return element as SVGCircleElement;
    });
    expect(plant.getAttribute('fill')).not.toBe('#43A047');
    expect(plant.getAttribute('fill')).not.toBe('none');
  });
});

describe('plant panel', () => {
  async function selectPlant(container: HTMLElement) {
    const marker = await waitFor(() => {
      const element = container.querySelector('g[data-plan-key="pl_1"]');
      expect(element).not.toBeNull();
      return element as SVGGElement;
    });
    fireEvent.keyDown(marker, { key: 'Enter' });
  }

  it('offers both actions on the selected plant to someone who may edit', async () => {
    usePlan();
    const { container } = renderTab('grower');
    await selectPlant(container);

    const panel = await screen.findByTestId('bed-plan-plant-panel');
    expect(panel).toHaveTextContent('Plant TOM-1');
    expect(screen.getByTestId('bed-plan-correct')).toBeInTheDocument();
    expect(screen.getByTestId('bed-plan-transplant')).toBeInTheDocument();
  });

  it('shows a viewer the panel without the actions', async () => {
    usePlan();
    const { container } = renderTab('viewer');
    await selectPlant(container);

    expect(await screen.findByTestId('bed-plan-plant-panel')).toBeInTheDocument();
    expect(screen.queryByTestId('bed-plan-correct')).toBeNull();
    expect(screen.queryByTestId('bed-plan-transplant')).toBeNull();
  });

  it('selects again to close the panel', async () => {
    usePlan();
    const { container } = renderTab('grower');
    await selectPlant(container);
    await screen.findByTestId('bed-plan-plant-panel');

    fireEvent.keyDown(container.querySelector('g[data-plan-key="pl_1"]') as Element, { key: 'Enter' });

    await waitFor(() => expect(screen.queryByTestId('bed-plan-plant-panel')).toBeNull());
  });
});
