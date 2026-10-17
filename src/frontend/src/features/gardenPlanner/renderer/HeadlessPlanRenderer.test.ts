import { describe, expect, it } from 'vitest';
import { HeadlessPlanRenderer } from './HeadlessPlanRenderer';
import type { PlanModel } from './rendererTestKit';
import {
  NO_SELECTION,
  bed,
  gardenObject,
  normalizePlan,
  options,
  plantedBed,
  planResponse,
  viewportAt,
} from './rendererTestKit';
import type { Point } from '../model/types';

/** Screen point of model point (x, y) for a viewport at origin (0, 10) and 100 px/m. */
const px = (x: number, y: number): Point => [x * 100, (10 - y) * 100];
const VIEW = viewportAt(0, 10, 100);

function render(model: PlanModel, renderer = new HeadlessPlanRenderer()) {
  renderer.render(model, VIEW, NO_SELECTION, options());
  return renderer;
}

const model = (overrides: Parameters<typeof planResponse>[0]) =>
  normalizePlan(planResponse({ plan: null, ...overrides }));

describe('HeadlessPlanRenderer', () => {
  it('keeps the scene of the latest render for assertions', () => {
    const renderer = render(model({ locations: [bed('a', 1, 1)], garden_objects: [] }));
    expect(renderer.lastScene?.shapes.map((s) => s.entry.key)).toEqual(['a']);
  });

  it('refuses to answer before a render', () => {
    const renderer = new HeadlessPlanRenderer();
    expect(() => renderer.hitTest([0, 0])).toThrow(/render\(\)/);
    expect(() => renderer.toModel([0, 0])).toThrow(/render\(\)/);
  });

  it('projects between metres and pixels with y up in the model (GP-NFR-009)', () => {
    const renderer = render(model({ locations: [], garden_objects: [] }));
    expect(renderer.toScreen([2, 7])).toEqual([200, 300]);
    expect(renderer.toModel([200, 300])).toEqual([2, 7]);
    const [x, y] = renderer.toModel(renderer.toScreen([1.234, 5.678]));
    expect(x).toBeCloseTo(1.234, 9);
    expect(y).toBeCloseTo(5.678, 9);
  });

  it('records the drag preview and clears it', () => {
    const renderer = render(model({ locations: [], garden_objects: [] }));
    renderer.setDragOffset('a', 10, -5);
    expect(renderer.dragPreview).toEqual({ key: 'a', dxPx: 10, dyPx: -5 });
    renderer.setDragOffset(null);
    expect(renderer.dragPreview).toBeNull();
  });
});

describe('hit testing (GP-UX-032, GP-UX-033, GP-NFR-065)', () => {
  it('returns null on empty ground and the key on a bed', () => {
    const renderer = render(model({ locations: [bed('a', 1, 1)], garden_objects: [] }));
    expect(renderer.hitTest(px(1.6, 2))).toBe('a');
    expect(renderer.hitTest(px(5, 5))).toBeNull();
    expect(renderer.hitTestAll(px(5, 5))).toEqual([]);
  });

  it('tolerates a few pixels around the edge', () => {
    const renderer = render(model({ locations: [bed('a', 1, 1)], garden_objects: [] }));
    expect(renderer.hitTest([px(1, 2)[0] - 3, px(1, 2)[1]])).toBe('a');
    expect(renderer.hitTest([px(1, 2)[0] - 8, px(1, 2)[1]])).toBeNull();
  });

  it('ranks a plant marker above the bed, the bed above a path, a path above an area', () => {
    const { slots, plants } = plantedBed('bed', 1, 1, 2, 0.5);
    const renderer = render(
      model({
        locations: [bed('bed', 1, 1)],
        garden_objects: [
          gardenObject('lawn', 1.5, 2, {
            object_type: 'lawn',
            props: { object_type: 'lawn' },
            geometry: { kind: 'rect', origin: [0, 0], width_m: 6, length_m: 6, rotation_deg: 0 },
            bbox: [0, 0, 6, 6],
          }),
          gardenObject('path', 1.5, 2, {
            object_type: 'path',
            props: { object_type: 'path' },
            geometry: { kind: 'rect', origin: [0, 1.4], width_m: 6, length_m: 1, rotation_deg: 0 },
            bbox: [0, 1.4, 6, 2.4],
          }),
        ],
        slots,
        plants,
      }),
    );
    // plant 0 sits at (1.1, 1.5)
    expect(renderer.hitTestAll(px(1.1, 1.5))).toEqual(['bed_p0', 'bed', 'path', 'lawn']);
    expect(renderer.hitTest(px(1.1, 1.5))).toBe('bed_p0');
    // the first of the stack is what hitTest returns
    expect(renderer.hitTestAll(px(1.9, 1.9))[0]).toBe(renderer.hitTest(px(1.9, 1.9)));
  });

  it('breaks a tie by z-order, then by the smaller area', () => {
    const big = bed('big', 1, 1, {
      geometry: { kind: 'rect', origin: [1, 1], width_m: 4, length_m: 4, rotation_deg: 0 },
      bbox: [1, 1, 5, 5],
    });
    const small = bed('small', 2, 2); // 1.2 x 2 inside big
    const raised = bed('raised', 3, 3, { z_order: 2 });
    const renderer = render(model({ locations: [big, small, raised], garden_objects: [] }));
    expect(renderer.hitTestAll(px(2.5, 3))).toEqual(['small', 'big']);
    // `raised` has the higher z-order and `small` is also under this point at (3.1, 3.5)
    expect(renderer.hitTestAll(px(3.1, 3.5))).toEqual(['raised', 'small', 'big']);
  });

  it('hits locked objects', () => {
    const renderer = render(
      model({ locations: [bed('locked', 1, 1, { locked: true })], garden_objects: [] }),
    );
    expect(renderer.hitTest(px(1.6, 2))).toBe('locked');
  });

  it('hits a circle and a polyline by their drawn extent', () => {
    const renderer = render(
      model({
        locations: [],
        garden_objects: [
          gardenObject('tree', 5, 5), // radius 1
          gardenObject('fence', 0, 0, {
            object_type: 'fence',
            props: { object_type: 'fence' },
            geometry: {
              kind: 'polyline',
              points: [
                [1, 8],
                [6, 8],
              ],
              width_m: 0.4,
            },
            bbox: [1, 7.8, 6, 8.2],
          }),
        ],
      }),
    );
    expect(renderer.hitTest(px(5.9, 5))).toBe('tree');
    expect(renderer.hitTest(px(7, 5))).toBeNull();
    expect(renderer.hitTest(px(3, 8.15))).toBe('fence');
    expect(renderer.hitTest(px(3, 8.6))).toBeNull();
  });

  it('hits the boundary on its edge only, so an empty click stays empty', () => {
    const renderer = render(
      model({
        plan: {
          boundary: { kind: 'rect', origin: [1, 1], width_m: 8, length_m: 8, rotation_deg: 0 },
          north_angle_deg: 0,
          default_grid_m: 0.1,
          adjacency_factor: 1.5,
          plan_revision: 1,
        },
        locations: [],
        garden_objects: [],
      }),
    );
    expect(renderer.hitTest(px(5, 5))).toBeNull();
    expect(renderer.hitTest(px(1, 5))).toBe('__boundary__');
  });

  it('does not hit markers that are collapsed into a cluster', () => {
    const { slots, plants } = plantedBed('bed', 1, 1, 3, 0.1);
    const dense = model({ locations: [bed('bed', 1, 1)], garden_objects: [], slots, plants });
    const renderer = new HeadlessPlanRenderer();
    renderer.render(dense, viewportAt(0, 10, 50), NO_SELECTION, options()); // 0.1 m = 5 px
    expect(renderer.hitTest([1.1 * 50, (10 - 1.5) * 50])).toBe('bed');
  });
});
