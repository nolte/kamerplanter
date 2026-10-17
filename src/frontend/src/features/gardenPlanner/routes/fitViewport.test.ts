import { describe, expect, it } from 'vitest';
import { bed, gardenObject, planResponse } from '@/test/gardenPlanFixtures';
import { normalizePlan } from '../model/planModel';
import { fitViewport, planContentBounds } from './fitViewport';

describe('planContentBounds', () => {
  it('is the box around the boundary, the beds and the garden objects', () => {
    const plan = normalizePlan(
      planResponse({
        plan: {
          boundary: { kind: 'rect', origin: [0, 0], width_m: 10, length_m: 8, rotation_deg: 0 },
          north_angle_deg: 0,
          default_grid_m: 0.1,
          adjacency_factor: 1.5,
          plan_revision: 1,
        },
        locations: [bed('loc_a', 12, 1)],
        garden_objects: [gardenObject('go_1', -2, 9)],
      }),
    );
    const [minX, minY, maxX, maxY] = planContentBounds(plan) ?? [];
    expect(minX).toBeLessThanOrEqual(-2);
    expect(minY).toBe(0);
    expect(maxX).toBeCloseTo(13.2, 5);
    expect(maxY).toBeGreaterThanOrEqual(9);
  });

  it('is null for a plan with nothing placed', () => {
    const plan = normalizePlan(
      planResponse({ plan: null, locations: [], garden_objects: [], slots: [], plants: [] }),
    );
    expect(planContentBounds(plan)).toBeNull();
  });

  it('ignores a bed without a geometry (stock data)', () => {
    const plan = normalizePlan(
      planResponse({
        plan: null,
        locations: [bed('loc_a', 1, 1, { geometry: null, bbox: null })],
        garden_objects: [],
      }),
    );
    expect(planContentBounds(plan)).toBeNull();
  });
});

describe('fitViewport', () => {
  it('shows the whole box, top-left at (minX, maxY) with a margin', () => {
    const viewport = fitViewport([0, 0, 10, 5], 600, 1000);
    const [ox, oy] = viewport.originM;
    expect(ox).toBeLessThan(0);
    expect(oy).toBeGreaterThan(5);
    // 10 m plus margin on both sides fill the width.
    expect(viewport.widthPx).toBeLessThanOrEqual(600);
    expect(viewport.pxPerM * (10 + 2 * 0.5)).toBeCloseTo(viewport.widthPx, 0);
  });

  it('is limited by the height when the drawing is tall', () => {
    const viewport = fitViewport([0, 0, 2, 20], 600, 300);
    expect(viewport.heightPx).toBeLessThanOrEqual(300);
    expect(viewport.widthPx).toBeLessThan(600);
  });

  it('does not zoom into a tiny drawing beyond the cap', () => {
    expect(fitViewport([0, 0, 0.2, 0.2], 600, 600).pxPerM).toBe(200);
  });

  it('survives a degenerate box', () => {
    const viewport = fitViewport([3, 3, 3, 3], 600, 600);
    expect(Number.isFinite(viewport.pxPerM)).toBe(true);
    expect(viewport.widthPx).toBeGreaterThan(0);
  });
});
