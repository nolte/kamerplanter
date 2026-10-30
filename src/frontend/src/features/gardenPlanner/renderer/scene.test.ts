import { describe, expect, it } from 'vitest';
import { buildScene, markerLodBedKeys } from './scene';
import type { PlantMarkerState, RenderOptions } from './types';
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

describe('buildScene - plant-state layer (GP-UX-061, #2488)', () => {
  // 'near' has 0.5 m spacing: 15 px at 30 px/m (markers); 'dense' has 0.2 m: 6 px (one cluster).
  const near = plantedBed('near', 1, 1, 4, 0.5);
  const dense = plantedBed('dense', 5, 1, 4, 0.2);
  const model = plan({
    locations: [bed('near', 1, 1), bed('dense', 5, 1)],
    garden_objects: [],
    slots: [...near.slots, ...dense.slots, { key: 'near_empty', slot_id: 'NE', location_key: 'near', plan_geometry: { origin: [1.1, 2.5] } }],
    plants: [...near.plants, ...dense.plants],
  });
  const view = viewportAt(0, 10, 30);

  function stated(badge: PlantMarkerState['badge'] = null): PlantMarkerState {
    return { lifecycle: 'active', badge, initial: 'T', progress: null, ariaLabel: 'Tomato' };
  }
  const states: Record<string, PlantMarkerState> = {
    near_p0: stated('water'),
    near_p1: stated(),
    near_p2: stated('harvest'),
    dense_p0: stated('water'),
    dense_p1: stated('problem'),
    dense_p2: stated(),
    dense_p3: stated(),
  };
  const layer = (attentionOnly: boolean): Pick<RenderOptions, 'plantStateLayer'> => ({
    plantStateLayer: { states, attentionOnly },
  });

  it('names exactly the placed beds with plants at marker LOD as the ones to read', () => {
    expect(markerLodBedKeys(model, view)).toEqual(['near']);
    // zoomed in far enough, the dense bed reaches marker LOD too; out of the cull window, nothing
    expect(markerLodBedKeys(model, viewportAt(0, 10, 50)).sort()).toEqual(['dense', 'near']);
    expect(markerLodBedKeys(model, viewportAt(100, 100, 30))).toEqual([]);
  });

  it('draws the stated plants of a bed at marker LOD on their own, decorative, with their state', () => {
    const scene = buildScene(model, view, NO_SELECTION, layer(false));
    const own = scene.markers.map((m) => [m.entry.key, m.layerState?.badge ?? null, m.interactive]);
    expect(own).toEqual([
      ['near_p0', 'water', false],
      ['near_p1', null, false],
      ['near_p2', 'harvest', false],
    ]);
    // the plant without a known state and the empty slot stay in the cheap batch
    const batch = scene.markerBatches.find((b) => b.locationKey === 'near');
    expect(batch?.markers.map((m) => m.key)).toEqual(['near_p3', 'near_empty']);
    // the layer adds no tab stop: the focus stays on the objects
    expect(scene.markers.some((m) => m.tabStop)).toBe(false);
    expect(scene.shapes.some((s) => s.tabStop)).toBe(true);
  });

  it('keeps the plain batches without the layer (the default view is unchanged)', () => {
    const scene = buildScene(model, view, NO_SELECTION, {});
    expect(scene.markers).toEqual([]);
    expect(scene.markerBatches.find((b) => b.locationKey === 'near')?.markers).toHaveLength(5);
    expect(scene.clusters[0]).toMatchObject({ locationKey: 'dense', count: 4, attention: null, topBadge: null });
  });

  it('counts the badged plants of a cluster with the top reason by priority (problem before water)', () => {
    const [cluster] = buildScene(model, view, NO_SELECTION, layer(false)).clusters;
    expect(cluster).toMatchObject({ locationKey: 'dense', count: 4, attention: 2, topBadge: 'problem' });
  });

  it('with "only plants that need attention" keeps only badged markers, and a selected one', () => {
    const scene = buildScene(model, view, { selectedKeys: new Set(['near_p1']) }, layer(true));
    expect(scene.markers.map((m) => m.entry.key)).toEqual(['near_p0', 'near_p1', 'near_p2']);
    expect(scene.markers.find((m) => m.entry.key === 'near_p1')?.selected).toBe(true);
    expect(scene.markerBatches.find((b) => b.locationKey === 'near')).toBeUndefined();
    const unselected = buildScene(model, view, NO_SELECTION, layer(true));
    expect(unselected.markers.map((m) => m.entry.key)).toEqual(['near_p0', 'near_p2']);
  });

  it('with the filter a cluster counts only badged plants, hides at zero and keeps its count while unknown', () => {
    const [counted] = buildScene(model, view, NO_SELECTION, layer(true)).clusters;
    expect(counted).toMatchObject({ locationKey: 'dense', count: 2, attention: 2, topBadge: 'problem' });
    const calm = { dense_p0: stated(), dense_p1: stated() };
    expect(
      buildScene(model, view, NO_SELECTION, { plantStateLayer: { states: calm, attentionOnly: true } }).clusters,
    ).toEqual([]);
    const unknown = buildScene(model, view, NO_SELECTION, { plantStateLayer: { states: {}, attentionOnly: true } });
    expect(unknown.clusters[0]).toMatchObject({ locationKey: 'dense', count: 4, attention: null });
    // likewise at marker LOD: a bed not read yet keeps its plain markers instead of going blank while it loads
    expect(unknown.markerBatches.find((b) => b.locationKey === 'near')?.markers).toHaveLength(5);
  });

  it('leaves the entered bed to the bed-view states and keeps its markers interactive', () => {
    const scene = buildScene(model, viewportAt(0, 10, 50), NO_SELECTION, {
      enteredLocationKey: 'near',
      ...layer(true),
    });
    const nearMarkers = scene.markers.filter((m) => m.entry.locationKey === 'near');
    expect(nearMarkers).toHaveLength(5);
    expect(nearMarkers.every((m) => m.interactive && m.layerState === undefined)).toBe(true);
  });
});
