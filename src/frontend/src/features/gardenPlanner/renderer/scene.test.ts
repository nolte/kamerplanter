import { describe, expect, it } from 'vitest';
import { buildScene } from './scene';
import {
  NO_SELECTION,
  bed,
  gardenObject,
  normalizePlan,
  plantedBed,
  planResponse,
  viewportAt,
} from './rendererTestKit';

function plan(overrides: Parameters<typeof planResponse>[0] = {}) {
  return normalizePlan(planResponse({ plan: null, ...overrides }));
}

const keys = (scene: ReturnType<typeof buildScene>) => scene.shapes.map((s) => s.entry.key);

describe('buildScene - viewport culling (GP-NFR-010)', () => {
  // The view shows x 0..10, y 0..10 at 100 px/m; the cull window is 20 % larger on every side.
  const view = viewportAt(0, 10, 100);

  it('keeps what intersects the viewport and drops what lies beyond the margin', () => {
    const model = plan({
      locations: [bed('inside', 1, 1), bed('far', 30, 30)],
      garden_objects: [],
    });
    expect(keys(buildScene(model, view, NO_SELECTION, {}))).toEqual(['inside']);
  });

  it('keeps an object inside the 20 % margin and drops one just outside it', () => {
    const model = plan({
      locations: [bed('in_margin', 11.5, 1), bed('past_margin', 12.1, 1)],
      garden_objects: [],
    });
    expect(keys(buildScene(model, view, NO_SELECTION, {}))).toEqual(['in_margin']);
  });

  it('never culls the selected or focused object (GP-NFR-069)', () => {
    const model = plan({
      locations: [bed('far', 30, 30), bed('also_far', 40, 40)],
      garden_objects: [],
    });
    const scene = buildScene(
      model,
      view,
      { selectedKeys: new Set(['far']), focusKey: 'also_far' },
      {},
    );
    expect(keys(scene).sort()).toEqual(['also_far', 'far']);
  });

  it('skips a bed that is not placed on the plan', () => {
    const model = plan({
      locations: [bed('placed', 1, 1), bed('unplaced', 1, 1, { geometry: null })],
      garden_objects: [],
    });
    expect(keys(buildScene(model, view, NO_SELECTION, {}))).toEqual(['placed']);
  });
});

describe('buildScene - level of detail (GP-NFR-067)', () => {
  const model = plan({
    locations: [bed('b', 1, 1)], // 1.2 m wide
    garden_objects: [gardenObject('t', 5, 5)], // 2 m wide
  });

  it('prints a bed name from 60 px of on-screen width', () => {
    // 1.2 m: 58.8 px at 49 px/m, exactly 60 px at 50 px/m
    const small = buildScene(model, viewportAt(0, 10, 49), NO_SELECTION, {});
    const large = buildScene(model, viewportAt(0, 10, 50), NO_SELECTION, {});
    expect(small.shapes.find((s) => s.entry.key === 'b')?.showLabel).toBe(false);
    expect(large.shapes.find((s) => s.entry.key === 'b')?.showLabel).toBe(true);
  });

  it('shows a garden object icon from 24 px and never one on a bed', () => {
    // the 2 m tree: 22 px at 11 px/m, 24 px at 12 px/m
    const below = buildScene(model, viewportAt(0, 10, 11), NO_SELECTION, {});
    const at = buildScene(model, viewportAt(0, 10, 12), NO_SELECTION, {});
    expect(below.shapes.find((s) => s.entry.key === 't')?.showIcon).toBe(false);
    expect(at.shapes.find((s) => s.entry.key === 't')?.showIcon).toBe(true);
    expect(at.shapes.find((s) => s.entry.key === 'b')?.showIcon).toBe(false);
  });

  it('prints dimensions for the selection only', () => {
    const scene = buildScene(model, viewportAt(0, 10, 60), { selectedKeys: new Set(['b']) }, {});
    expect(scene.shapes.filter((s) => s.showDimensions).map((s) => s.entry.key)).toEqual(['b']);
  });

  describe('plant markers', () => {
    // 3 plants 0.15 m apart: 9 px at 60 px/m, 10.5 px at 70 px/m
    const { slots, plants } = plantedBed('b', 1, 1, 3, 0.15);
    const planted = plan({ locations: [bed('b', 1, 1)], garden_objects: [], slots, plants });

    it('collapses into one counted cluster below 10 px spacing', () => {
      const scene = buildScene(planted, viewportAt(0, 10, 60), NO_SELECTION, {});
      expect(scene.markers).toEqual([]);
      expect(scene.markerBatches).toEqual([]);
      expect(scene.clusters).toEqual([expect.objectContaining({ locationKey: 'b', count: 3 })]);
    });

    it('shows the markers from 10 px spacing and no cluster, batched into one node per bed', () => {
      const scene = buildScene(planted, viewportAt(0, 10, 70), NO_SELECTION, {});
      expect(scene.markerBatches.map((b) => [b.locationKey, b.markers.map((m) => m.key)])).toEqual([
        ['b', ['b_p0', 'b_p1', 'b_p2']],
      ]);
      expect(scene.markers).toEqual([]);
      expect(scene.clusters).toEqual([]);
    });

    it('treats 0.1 m at 100 px/m as 10 px despite float noise', () => {
      const { slots: s2, plants: p2 } = plantedBed('b', 1, 1, 6, 0.1);
      const noisy = plan({
        locations: [bed('b', 1, 1)],
        garden_objects: [],
        slots: s2,
        plants: p2,
      });
      expect(buildScene(noisy, viewportAt(0, 10, 100), NO_SELECTION, {}).clusters).toEqual([]);
    });

    it('draws a selected marker on its own so the selection stays visible', () => {
      const scene = buildScene(
        planted,
        viewportAt(0, 10, 70),
        { selectedKeys: new Set(['b_p1']) },
        {},
      );
      expect(scene.markers.map((m) => [m.entry.key, m.selected, m.interactive])).toEqual([
        ['b_p1', true, false],
      ]);
      expect(scene.markerBatches[0].markers.map((m) => m.key)).toEqual(['b_p0', 'b_p2']);
    });

    it('draws an empty position as a slot marker', () => {
      const withEmpty = plan({
        locations: [bed('b', 1, 1)],
        garden_objects: [],
        slots: [
          { key: 'free', slot_id: 'B_9', location_key: 'b', plan_geometry: { origin: [1.5, 1.5] } },
        ],
        plants: [],
      });
      const scene = buildScene(withEmpty, viewportAt(0, 10, 70), NO_SELECTION, {});
      expect(scene.markerBatches[0].markers.map((m) => [m.key, m.kind])).toEqual([
        ['free', 'slot'],
      ]);
    });
  });
});

describe('buildScene - order and roving tab stop', () => {
  it('paints boundary, then areas, paths, and beds and objects last; reading order inside a layer', () => {
    const model = plan({
      plan: {
        boundary: { kind: 'rect', origin: [0, 0], width_m: 50, length_m: 50, rotation_deg: 0 },
        north_angle_deg: 0,
        default_grid_m: 0.1,
        adjacency_factor: 1.5,
        plan_revision: 1,
      },
      locations: [bed('south_west', 1, 1), bed('north_east', 8, 8), bed('north_west', 1, 8)],
      garden_objects: [
        gardenObject('lawn', 20, 20, { object_type: 'lawn', props: { object_type: 'lawn' } }),
        gardenObject('path', 22, 22, { object_type: 'path', props: { object_type: 'path' } }),
      ],
    });
    const scene = buildScene(model, viewportAt(0, 30, 20), NO_SELECTION, {});
    expect(keys(scene)).toEqual([
      '__boundary__',
      'lawn',
      'path',
      'north_west',
      'north_east',
      'south_west',
    ]);
  });

  it('puts z-order before reading order', () => {
    const model = plan({
      locations: [
        bed('north', 1, 8),
        bed('south_raised', 1, 1, { z_order: 5 }),
        bed('south', 5, 1),
      ],
      garden_objects: [],
    });
    expect(keys(buildScene(model, viewportAt(0, 12, 50), NO_SELECTION, {}))).toEqual([
      'north',
      'south',
      'south_raised',
    ]);
  });

  const model = plan({ locations: [bed('a', 1, 8), bed('b', 1, 1)], garden_objects: [] });
  const view = viewportAt(0, 12, 50);
  const stops = (selection = NO_SELECTION, entered: string | null = null) =>
    buildScene(model, view, selection, { enteredLocationKey: entered })
      .shapes.filter((s) => s.tabStop)
      .map((s) => s.entry.key);

  it('has exactly one tab stop: focus key, else first selected, else first object', () => {
    expect(stops()).toEqual(['a']);
    expect(stops({ selectedKeys: new Set(['b']) })).toEqual(['b']);
    expect(stops({ selectedKeys: new Set(['b']), focusKey: 'a' })).toEqual(['a']);
  });

  it('moves the tab stop to the plants of the entered bed (GP-NFR-068)', () => {
    const { slots, plants } = plantedBed('b', 1, 1, 3, 0.5);
    const planted = plan({
      locations: [bed('a', 1, 8), bed('b', 1, 1)],
      garden_objects: [],
      slots,
      plants,
    });
    const scene = buildScene(planted, view, NO_SELECTION, { enteredLocationKey: 'b' });
    expect(scene.shapes.some((s) => s.tabStop)).toBe(false);
    expect(scene.markers.filter((m) => m.tabStop).map((m) => m.entry.key)).toEqual(['b_p0']);
    expect(scene.markers.every((m) => m.interactive)).toBe(true);
    expect(scene.tabStopKey).toBe('b_p0');
  });
});
