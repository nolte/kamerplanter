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
    expect(cluster).toMatchObject({ locationKey: 'dense', count: 4, shownCount: 4, attention: 2, topBadge: 'problem' });
  });

  it('with "only plants that need attention" keeps badged markers, a selected one and plants not known yet', () => {
    const scene = buildScene(model, view, { selectedKeys: new Set(['near_p1']) }, layer(true));
    expect(scene.markers.map((m) => m.entry.key)).toEqual(['near_p0', 'near_p1', 'near_p2']);
    expect(scene.markers.find((m) => m.entry.key === 'near_p1')?.selected).toBe(true);
    // per plant: near_p3 has no known state yet and keeps its plain marker; the empty slot goes
    expect(scene.markerBatches.find((b) => b.locationKey === 'near')?.markers.map((m) => m.key)).toEqual(['near_p3']);
    const unselected = buildScene(model, view, NO_SELECTION, layer(true));
    expect(unselected.markers.map((m) => m.entry.key)).toEqual(['near_p0', 'near_p2']);
  });

  it('with the filter a cluster keeps the total, draws the kept plants and hides only when all are known and calm', () => {
    const [counted] = buildScene(model, view, NO_SELECTION, layer(true)).clusters;
    expect(counted).toMatchObject({ locationKey: 'dense', count: 4, shownCount: 2, attention: 2, topBadge: 'problem' });
    const allCalm = { dense_p0: stated(), dense_p1: stated(), dense_p2: stated(), dense_p3: stated() };
    expect(
      buildScene(model, view, NO_SELECTION, { plantStateLayer: { states: allCalm, attentionOnly: true } }).clusters,
    ).toEqual([]);
    // partly known: the two plants without a state are "unknown", not "calm" - the cluster stays and shows them
    const partlyCalm = { dense_p0: stated(), dense_p1: stated() };
    const [partly] = buildScene(model, view, NO_SELECTION, {
      plantStateLayer: { states: partlyCalm, attentionOnly: true },
    }).clusters;
    expect(partly).toMatchObject({ locationKey: 'dense', count: 4, shownCount: 2, attention: 0 });
    const unknown = buildScene(model, view, NO_SELECTION, { plantStateLayer: { states: {}, attentionOnly: true } });
    expect(unknown.clusters[0]).toMatchObject({ locationKey: 'dense', count: 4, shownCount: 4, attention: null });
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

describe('buildScene - label placement (GP-UX-047, #2490)', () => {
  // An L-shaped bed (concave): its area centroid (4.236, 3.236) lies in the notch, outside the bed.
  const lShape = bed('l', 2, 2, {
    name: 'Winkelbeet',
    geometry: {
      kind: 'polygon',
      points: [
        [2, 2],
        [8, 2],
        [8, 3.2],
        [3.2, 3.2],
        [3.2, 6],
        [2, 6],
      ],
      rotation_deg: 0,
    },
    bbox: [2, 2, 8, 6],
    area_m2: 10.56,
  });
  const labelOf = (scene: ReturnType<typeof buildScene>, key: string) =>
    scene.shapes.find((shape) => shape.entry.key === key)?.label ?? null;

  it('puts the name of an L-shaped bed at its pole of inaccessibility, not at the centroid', () => {
    const scene = buildScene(plan({ locations: [lShape], garden_objects: [] }), viewportAt(0, 10, 100), NO_SELECTION, {});
    expect(labelOf(scene, 'l')).toEqual({ text: 'Winkelbeet', x: 2.703, y: 2.703 });
  });

  it('shortens a name with an ellipsis to the room at the anchor', () => {
    // room 1.406 m at 50 px/m = 70 px: 9 characters of 7.2 px (the 6 m box would hold 41)
    const named = { ...lShape, name: 'Staudenbeet am Gartenzaun' };
    const scene = buildScene(plan({ locations: [named], garden_objects: [] }), viewportAt(0, 10, 50), NO_SELECTION, {});
    expect(labelOf(scene, 'l')?.text).toBe('Staudenb…');
  });

  it('shortens with the field-mode font to fewer characters (16 px)', () => {
    const named = { ...lShape, name: 'Staudenbeet am Gartenzaun' };
    const scene = buildScene(plan({ locations: [named], garden_objects: [] }), viewportAt(0, 10, 50), NO_SELECTION, {
      fieldMode: true,
    });
    // 70 px / 9.6 px = 7 characters
    expect(labelOf(scene, 'l')?.text).toBe('Staude…');
  });

  it('gives an overlapping name to the larger object; the smaller keeps its LOD gate for the overlays', () => {
    // A 1.2 x 2 m bed whose centre sits 6 cm from the centre of a 4 x 4 m area around it.
    const area = bed('area', 0, 0, {
      name: 'Gemüsegarten',
      geometry: { kind: 'rect', origin: [0, 0], width_m: 4, length_m: 4, rotation_deg: 0 },
      bbox: [0, 0, 4, 4],
      area_m2: 16,
      location_type_key: 'area',
    });
    const inner = bed('inner', 1.4, 1.06, { name: 'Beet' });
    const scene = buildScene(plan({ locations: [inner, area], garden_objects: [] }), viewportAt(-1, 6, 100), NO_SELECTION, {});
    expect(labelOf(scene, 'area')?.text).toBe('Gemüsegarten');
    expect(labelOf(scene, 'inner')).toBeNull();
    expect(scene.shapes.find((shape) => shape.entry.key === 'inner')?.showLabel).toBe(true);
  });

  it('keeps both names when they do not meet', () => {
    const scene = buildScene(
      plan({ locations: [bed('a', 1, 1), bed('b', 4, 1)], garden_objects: [] }),
      viewportAt(0, 10, 100),
      NO_SELECTION,
      {},
    );
    expect(labelOf(scene, 'a')?.text).toBe('Bed a');
    expect(labelOf(scene, 'b')?.text).toBe('Bed b');
  });

  it('draws no name below 60 px of on-screen width (GP-NFR-067)', () => {
    const scene = buildScene(plan({ locations: [bed('b', 1, 1)], garden_objects: [] }), viewportAt(0, 10, 49), NO_SELECTION, {});
    expect(labelOf(scene, 'b')).toBeNull();
  });

  it('places the plant cluster a line above the name, never on it', () => {
    const { slots, plants } = plantedBed('b', 1, 1, 6, 0.1);
    const model = plan({ locations: [bed('b', 1, 1)], garden_objects: [], slots, plants });
    const scene = buildScene(model, viewportAt(0, 10, 99), NO_SELECTION, {});
    const label = labelOf(scene, 'b');
    const cluster = scene.clusters[0];
    expect(label).not.toBeNull();
    expect(cluster.x).toBe(label?.x);
    expect((cluster.y - (label?.y ?? 0)) * 99).toBeCloseTo(18, 5); // 1.5 x 12 px
  });

  it('centres the cluster on the label anchor when the name is not drawn', () => {
    const { slots, plants } = plantedBed('b', 1, 1, 6, 0.1);
    const model = plan({ locations: [bed('b', 1, 1)], garden_objects: [], slots, plants });
    const scene = buildScene(model, viewportAt(0, 10, 45), NO_SELECTION, {});
    expect(labelOf(scene, 'b')).toBeNull();
    expect([scene.clusters[0].x, scene.clusters[0].y]).toEqual([1.6, 2]);
  });

  it('leaves the dimensions of the selection to the overlay when the caller draws them', () => {
    const model = plan({ locations: [bed('b', 1, 1)], garden_objects: [] });
    const selection = { selectedKeys: new Set(['b']) };
    expect(buildScene(model, viewportAt(0, 10, 60), selection, {}).shapes[0].showDimensions).toBe(true);
    expect(
      buildScene(model, viewportAt(0, 10, 60), selection, { dimensionsOnOverlay: true }).shapes[0].showDimensions,
    ).toBe(false);
  });

  it('is deterministic for the same data and viewport (GP-FR-003)', () => {
    const model = plan({ locations: [lShape, bed('a', 1, 7), bed('b', 4, 7)], garden_objects: [gardenObject('t', 6, 8)] });
    const view = viewportAt(0, 10, 80);
    const first = buildScene(model, view, NO_SELECTION, {}).shapes.map((shape) => shape.label);
    const second = buildScene(model, view, NO_SELECTION, {}).shapes.map((shape) => shape.label);
    expect(second).toEqual(first);
  });
});
