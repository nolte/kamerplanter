import { describe, expect, it } from 'vitest';
import { bed, planResponse } from '@/test/gardenPlanFixtures';
import { transformPlanToBed } from '../model/geometry';
import { applyOperation } from '../model/applyOperation';
import { normalizePlan } from '../model/planModel';
import { applyUndoPatch, diffPlans } from '../model/undoPatch';
import type { Geometry, PlanOperation } from '../model/types';
import { hitTestAll } from './hitTest';
import { markerIndex } from './planIndex';
import { buildScene } from './scene';
import { largePlacedPlan, NO_SELECTION, plantedBed, viewportAt } from './rendererTestKit';

/**
 * #2381: a slot is bed-local. `applyOperation` keeps `plan.slots` shared (GP-ACC-033), so the plan
 * position the renderers use must follow the bed's geometry - derived in `markerIndex`.
 */
function twoBeds() {
  const { slots, plants } = plantedBed('a', 1, 1, 3, 0.5); // slots at (1.1 + 0.5 i, 1.5)
  return normalizePlan(
    planResponse({
      locations: [bed('a', 1, 1), bed('b', 8, 8)],
      garden_objects: [],
      slots,
      plants,
    }),
  );
}

function moveTo(key: string, origin: [number, number], rotation = 0): PlanOperation {
  return {
    op: 'update_geometry',
    entity: 'location',
    key,
    geometry: { kind: 'rect', origin, width_m: 1.2, length_m: 2, rotation_deg: rotation },
  };
}

function positions(plan: ReturnType<typeof twoBeds>, locationKey = 'a') {
  return markerIndex(plan)
    .get(locationKey)!
    .markers.map((m) => [m.x, m.y]);
}

describe('slot markers follow their bed (#2381)', () => {
  it('keeps the delivered position for an unmoved bed', () => {
    expect(positions(twoBeds())).toEqual([
      [1.1, 1.5],
      [1.6, 1.5],
      [2.1, 1.5],
    ]);
  });

  it('follows a move without touching a slot entry', () => {
    const before = twoBeds();
    const after = applyOperation(before, moveTo('a', [4, 6])).plan;
    expect(after.slots).toBe(before.slots);
    expect(after.plants).toBe(before.plants);
    const moved = positions(after);
    expect(moved[0][0]).toBeCloseTo(4.1);
    expect(moved[0][1]).toBeCloseTo(6.5);
    expect(moved[2][0]).toBeCloseTo(5.1);
    expect(markerIndex(after).get('a')!.bbox[0]).toBeCloseTo(4.1);
    expect(positions(before)[0]).toEqual([1.1, 1.5]);
  });

  it('follows a rotation about the bed anchor', () => {
    const after = applyOperation(twoBeds(), moveTo('a', [1, 1], 90)).plan;
    // bed-local (0.1, 0.5) .. (1.1, 0.5) rotated by 90 deg: (-0.5, 0.1) .. (-0.5, 1.1), plus anchor
    const rotated = positions(after);
    expect(rotated[0][0]).toBeCloseTo(0.5);
    expect(rotated[0][1]).toBeCloseTo(1.1);
    expect(rotated[2][0]).toBeCloseTo(0.5);
    expect(rotated[2][1]).toBeCloseTo(2.1);
  });

  it('keeps spacing and plant count, and reuses the markers of every bed that did not move', () => {
    const before = twoBeds();
    const after = applyOperation(before, moveTo('a', [4, 6], 33)).plan;
    const oldBed = markerIndex(before).get('a')!;
    const newBed = markerIndex(after).get('a')!;
    expect(newBed.plantCount).toBe(oldBed.plantCount);
    expect(newBed.minSpacingM).toBeCloseTo(oldBed.minSpacingM);
    const moveB = applyOperation(before, moveTo('b', [9, 9])).plan;
    expect(markerIndex(moveB).get('a')).toBe(oldBed);
  });

  it('is unaffected by a resize that keeps anchor and rotation', () => {
    const before = twoBeds();
    const resized = applyOperation(before, {
      op: 'update_geometry',
      entity: 'location',
      key: 'a',
      geometry: { kind: 'rect', origin: [1, 1], width_m: 3, length_m: 5, rotation_deg: 0 },
    }).plan;
    expect(markerIndex(resized).get('a')).toBe(markerIndex(before).get('a'));
  });

  it('is restored by undo and re-derived by redo', () => {
    const start = twoBeds();
    const moved = applyOperation(start, moveTo('a', [4, 6])).plan;
    const undone = applyUndoPatch(moved, diffPlans(start, moved));
    expect(positions(undone)).toEqual(positions(start));
    const redone = applyOperation(undone, moveTo('a', [4, 6])).plan;
    expect(positions(redone)[0][0]).toBeCloseTo(4.1);
  });

  it('is used by the hit test', () => {
    const moved = applyOperation(twoBeds(), moveTo('a', [4, 6])).plan;
    const viewport = viewportAt(0, 10, 100);
    // y points up: the first plant moved from (1.1, 1.5) m to (4.1, 6.5) m, i.e. (410, 350) px
    // from the top-left (110, 850) px before
    expect(hitTestAll(moved, viewport, [410, 350])[0]).toBe('a_p0');
    expect(hitTestAll(moved, viewport, [110, 850])).not.toContain('a_p0');
  });

  it('is used by culling and the renderer scene', () => {
    const moved = applyOperation(twoBeds(), moveTo('a', [40, 60])).plan;
    const nearOld = buildScene(moved, viewportAt(0, 4, 100, 400, 400), NO_SELECTION, {});
    expect(nearOld.markerBatches.flatMap((b) => b.markers)).toEqual([]);
    const nearNew = buildScene(moved, viewportAt(39, 62, 100, 400, 400), NO_SELECTION, {});
    expect(nearNew.markerBatches.flatMap((b) => b.markers.map((m) => m.key))).toEqual([
      'a_p0',
      'a_p1',
      'a_p2',
    ]);
    const first = nearNew.markerBatches.flatMap((b) => b.markers)[0];
    expect(first.x).toBeCloseTo(40.1);
    expect(first.y).toBeCloseTo(60.5);
  });

  it('works on the large class: every bed moved keeps all 3 000 slot entries shared', () => {
    const start = largePlacedPlan();
    let plan = start;
    for (let i = 0; i < 150; i += 1) plan = applyOperation(plan, moveTo(`loc_${i}`, [i, 1])).plan;
    expect(plan.slots).toBe(start.slots);
    const first = markerIndex(plan).get('loc_7')!.markers[0];
    const base = markerIndex(start).get('loc_7')!.markers[0];
    // loc_7 started at x = 21, y = 0 and moved to (7, 1): the marker travels with it
    expect(first.x - base.x).toBeCloseTo(7 - 21);
    expect(first.y - base.y).toBeCloseTo(1 - 0);
  });
});

describe('bed-local invariant (#2381)', () => {
  it('keeps every marker at the same bed-local point for a bed loaded rotated, moved and rotated again', () => {
    const loaded: Geometry = {
      kind: 'rect',
      origin: [5, 3],
      width_m: 1.2,
      length_m: 2,
      rotation_deg: 45,
    };
    const { slots, plants } = plantedBed('a', 0, 0, 3, 0.5);
    const plan = normalizePlan(
      planResponse({
        locations: [bed('a', 5, 3, { geometry: loaded })],
        garden_objects: [],
        slots,
        plants,
      }),
    );
    const local = (p: typeof plan, geometry: Geometry) =>
      markerIndex(p)
        .get('a')!
        .markers.map((m) => transformPlanToBed([m.x, m.y], geometry));
    const expected = local(plan, loaded);
    const next: Geometry = { ...loaded, origin: [-2, 9], rotation_deg: 200 };
    const moved = applyOperation(plan, {
      op: 'update_geometry',
      entity: 'location',
      key: 'a',
      geometry: next,
    }).plan;
    local(moved, next).forEach(([x, y], i) => {
      expect(x).toBeCloseTo(expected[i][0], 9);
      expect(y).toBeCloseTo(expected[i][1], 9);
    });
  });

  it('moves with the first vertex of a polygon bed, like the server frame (anchor = points[0])', () => {
    const polygon: Geometry = {
      kind: 'polygon',
      points: [
        [0, 0],
        [4, 0],
        [4, 3],
      ],
      rotation_deg: 0,
    };
    const { slots, plants } = plantedBed('a', 0, 0, 2, 0.5);
    const plan = normalizePlan(
      planResponse({
        locations: [bed('a', 0, 0, { geometry: polygon })],
        garden_objects: [],
        slots,
        plants,
      }),
    );
    const shifted: Geometry = {
      ...polygon,
      points: [
        [1, 2],
        [4, 0],
        [4, 3],
      ],
    };
    const moved = applyOperation(plan, {
      op: 'update_geometry',
      entity: 'location',
      key: 'a',
      geometry: shifted,
    }).plan;
    const before = markerIndex(plan).get('a')!.markers[0];
    const after = markerIndex(moved).get('a')!.markers[0];
    expect(after.x - before.x).toBeCloseTo(1);
    expect(after.y - before.y).toBeCloseTo(2);
  });
});

describe.runIf(process.env.GP_BENCHMARK === '1')(
  'marker derivation after a move (benchmark lane)',
  () => {
    it('derives the moved bed on top of a warm index in well under a frame', () => {
      const start = largePlacedPlan();
      markerIndex(start);
      const samples: number[] = [];
      for (let run = 0; run < 100; run += 1) {
        const plan = applyOperation(start, moveTo(`loc_${run % 150}`, [run, 2], run)).plan;
        const t0 = performance.now();
        markerIndex(plan);
        samples.push(performance.now() - t0);
      }
      samples.sort((a, b) => a - b);
      console.info(`markerIndex after move median ${samples[50].toFixed(4)} ms`);
      expect(samples[50]).toBeLessThanOrEqual(2);
    });
  },
);
