import { describe, expect, it } from 'vitest';
import { toShape } from '../../model/geometry';
import type { Geometry, Point } from '../../model/types';
import { moveSources, resolveMoveSnap, resolveSnap, type SnapCandidates, type SnapOptions } from './snap';

const BASE: SnapOptions = { gridM: 0.1, gridEnabled: true, bypass: false, pxPerM: 100 };

describe('resolveSnap', () => {
  it('snaps to the grid (GP-ACC-006: 23 cm -> 20 cm)', () => {
    expect(resolveSnap([0.23, 1.04], BASE)).toEqual({ point: [0.2, 1], kind: 'grid' });
  });
  it('Alt keeps the exact value, rounded to the storage precision', () => {
    expect(resolveSnap([0.2304, 1.04], { ...BASE, bypass: true })).toEqual({
      point: [0.23, 1.04],
      kind: 'none',
    });
  });
  it('switched off grid keeps the value', () => {
    expect(resolveSnap([0.23, 0], { ...BASE, gridEnabled: false })).toEqual({
      point: [0.23, 0],
      kind: 'none',
    });
  });
  it('snaps to a bed-local, rotated raster (slots)', () => {
    const result = resolveSnap([1.02, 2.51], {
      ...BASE,
      gridM: 0.5,
      gridFrame: { origin: [1, 2], rotationDeg: 90 },
    });
    // rotated by 90 degrees the local x axis is +y: (1.02, 2.51) is local (0.51, -0.02) -> (0.5, 0)
    expect(result.kind).toBe('grid');
    expect(result.point[0]).toBeCloseTo(1, 3);
    expect(result.point[1]).toBeCloseTo(2.5, 3);
  });

  describe('priority corner > edge > grid (GP-FR-154)', () => {
    const candidates = {
      corners: [[2, 2]] as [number, number][],
      edges: [[[0, 0.5], [4, 0.5]]] as [[number, number], [number, number]][],
    };
    it('a corner within 10 px wins over an edge and the grid', () => {
      // 8 px = 0.08 m from the corner at 100 px/m
      expect(resolveSnap([2.05, 2.06], { ...BASE, candidates })).toEqual({
        point: [2, 2],
        kind: 'corner',
      });
    });
    it('an edge within tolerance wins over the grid', () => {
      const result = resolveSnap([1.234, 0.55], { ...BASE, candidates });
      expect(result).toEqual({
        point: [1.234, 0.5],
        kind: 'edge',
        guide: [
          [0, 0.5],
          [4, 0.5],
        ],
      });
    });
    it('falls back to the grid outside the tolerance', () => {
      expect(resolveSnap([1.234, 1.04], { ...BASE, candidates })).toEqual({
        point: [1.2, 1],
        kind: 'grid',
      });
    });
    it('the tolerance is 10 px for the mouse and 24 px for touch and pen, in screen space', () => {
      const near: [number, number] = [2.15, 2];
      expect(resolveSnap(near, { ...BASE, candidates }).kind).toBe('grid');
      expect(resolveSnap(near, { ...BASE, candidates, pointerType: 'touch' }).kind).toBe('corner');
      expect(resolveSnap(near, { ...BASE, candidates, pointerType: 'pen' }).kind).toBe('corner');
      // zoomed out the same pixels span more metres
      expect(resolveSnap([2.15, 2], { ...BASE, candidates, pxPerM: 50 }).kind).toBe('corner');
    });
    it('Alt switches the object snap off too', () => {
      expect(resolveSnap([2.05, 2.06], { ...BASE, candidates, bypass: true }).kind).toBe('none');
    });
    it('the nearest of several corners wins', () => {
      const two = { corners: [[2, 2], [2.04, 2]] as [number, number][], edges: [] };
      expect(resolveSnap([2.035, 2], { ...BASE, candidates: two }).point).toEqual([2.04, 2]);
    });
  });
});

describe('resolveMoveSnap: every corner of the dragged object is a source (GP-FR-154)', () => {
  // A 2 x 2 m bed with its anchor (lower-left corner) at (14, 2): sources are its four corners.
  const bed: Geometry = { kind: 'rect', origin: [14, 2], width_m: 2, length_m: 2, rotation_deg: 0 };
  const sources = moveSources(bed);
  const reference: [number, number] = [14, 2];
  // b2 of the editor fixture: x 6..8, y 3..5
  const candidates = {
    corners: [
      [6, 3],
      [8, 3],
      [8, 5],
      [6, 5],
    ] as [number, number][],
    edges: [
      [[6, 3], [8, 3]],
      [[8, 3], [8, 5]],
      [[8, 5], [6, 5]],
      [[6, 5], [6, 3]],
    ] as [[number, number], [number, number]][],
  };

  it('an axis-aligned rectangle snaps with its four corners, the anchor first', () => {
    expect(sources).toEqual([
      [14, 2],
      [16, 2],
      [16, 4],
      [14, 4],
    ]);
  });

  it('left edge to right edge: the moved bed ends beside the other one, free of any overlap', () => {
    // dragged by (-5.9, 0.5): its left edge is at x 8.1, 0.1 m (10 px) right of b2's right edge x = 8; the end
    // state 8..10 x 2.5..4.5 only touches b2 - two overlapping beds would be an unsavable plan (V-05)
    const result = resolveMoveSnap(sources, reference, [-5.9, 0.5], { ...BASE, candidates });
    expect(result.kind).toBe('edge');
    expect(result.delta[0]).toBeCloseTo(-6, 6);
    expect(result.delta[1]).toBeCloseTo(0.5, 6);
    // the marker is the snapped source - the upper-left corner on b2's edge - not the pointer
    expect(result.point).toEqual([8, 4.5]);
    expect(result.guide).toEqual([
      [8, 3],
      [8, 5],
    ]);
  });

  it('the anchor alone would have missed it: the old anchor-only snap falls back to the grid', () => {
    expect(resolveSnap([14 - 5.9, 2 + 0.5], { ...BASE, candidates }).kind).toBe('grid');
  });

  it('a corner of any source wins over an edge, and the nearest pair wins among corners', () => {
    // upper-left corner (14, 4) -> (8.05, 2.96): 0.064 m from b2's corner (8, 3); lower-left (8.05, 0.96) is far
    const result = resolveMoveSnap(sources, reference, [-5.95, -1.04], { ...BASE, candidates });
    expect(result.kind).toBe('corner');
    expect(result.point).toEqual([8, 3]);
    expect(result.delta[0]).toBeCloseTo(-6, 6);
    expect(result.delta[1]).toBeCloseTo(-1, 6);
  });

  it('falls back to the grid on the anchor, as before', () => {
    const result = resolveMoveSnap(sources, reference, [-1.234, 0.06], { ...BASE, candidates });
    expect(result).toMatchObject({ kind: 'grid', point: [12.8, 2.1] });
    expect(result.delta[0]).toBeCloseTo(-1.2, 6);
    expect(result.delta[1]).toBeCloseTo(0.1, 6);
  });

  it('keeps the tolerances: 10 px for the mouse, 24 px for touch', () => {
    // left edge 0.15 m (15 px) right of b2's right edge
    const raw: [number, number] = [-5.85, 0.5];
    expect(resolveMoveSnap(sources, reference, raw, { ...BASE, candidates }).kind).toBe('grid');
    expect(
      resolveMoveSnap(sources, reference, raw, { ...BASE, candidates, pointerType: 'touch' }).kind,
    ).toBe('edge');
  });

  it('Alt keeps the raw move, rounded to the storage precision', () => {
    const result = resolveMoveSnap(sources, reference, [-5.9004, 0.5], {
      ...BASE,
      candidates,
      bypass: true,
    });
    expect(result.kind).toBe('none');
    expect(result.point).toEqual([8.1, 2.5]);
  });

  it('every result is within the tolerance of its source (property over a sweep)', () => {
    const toleranceM = 10 / BASE.pxPerM;
    for (let i = 0; i < 200; i += 1) {
      const raw: [number, number] = [-12 + (i % 20) * 0.37, -2 + Math.floor(i / 20) * 0.53];
      const result = resolveMoveSnap(sources, reference, raw, { ...BASE, candidates });
      if (result.kind !== 'corner' && result.kind !== 'edge') continue;
      const moved = Math.hypot(result.delta[0] - raw[0], result.delta[1] - raw[1]);
      expect(moved).toBeLessThanOrEqual(toleranceM + 1e-9);
    }
  });
});

describe('moveSources: the points of the real shape, never phantom bbox corners (GP-FR-154)', () => {
  const target: Point = [5, 5];
  const single: SnapCandidates = { corners: [target], edges: [] };
  /** Distance from the target to the nearest point of the moved shape's outline or centre. */
  function gapToShape(geometry: Geometry, delta: Point): number {
    const shape = toShape(geometry);
    if (shape.kind === 'circle') {
      const d = Math.hypot(target[0] - shape.center[0] - delta[0], target[1] - shape.center[1] - delta[1]);
      return Math.min(d, Math.abs(d - shape.radiusM));
    }
    return Math.min(
      ...shape.vertices.map(([x, y]) => Math.hypot(target[0] - x - delta[0], target[1] - y - delta[1])),
    );
  }
  /** Every 'corner' snap over a sweep of drags lands a real point of the shape on the target (<= 1 mm). */
  function expectOnlyRealCorners(geometry: Geometry): number {
    const sources = moveSources(geometry);
    const shape = toShape(geometry);
    const ref: Point = shape.kind === 'circle' ? shape.center : shape.vertices[0];
    let corners = 0;
    for (let i = 0; i < 4000; i += 1) {
      const raw: Point = [-2 + (i % 80) * 0.11, -2 + Math.floor(i / 80) * 0.19];
      const result = resolveMoveSnap(sources, ref, raw, { ...BASE, candidates: single });
      if (result.kind !== 'corner') continue;
      corners += 1;
      expect(result.point).toEqual(target);
      expect(gapToShape(geometry, result.delta)).toBeLessThanOrEqual(0.001);
    }
    return corners;
  }

  it('a rectangle rotated by 45 degrees snaps with its rotated vertices', () => {
    const rect: Geometry = { kind: 'rect', origin: [0, 0], width_m: 2, length_m: 2, rotation_deg: 45 };
    const sources = moveSources(rect);
    expect(sources).toHaveLength(4);
    const vertices = (toShape(rect) as { vertices: Point[] }).vertices;
    sources.forEach((source, i) => {
      expect(source[0]).toBeCloseTo(vertices[i][0], 9);
      expect(source[1]).toBeCloseTo(vertices[i][1], 9);
    });
    // the right vertex (1.414, 1.414) dragged to 3 cm / 2 cm beside the target corner: it lands on it
    const result = resolveMoveSnap(sources, [0, 0], [5 - Math.SQRT2 + 0.03, 5 - Math.SQRT2 + 0.02], {
      ...BASE,
      candidates: single,
    });
    expect(result.kind).toBe('corner');
    expect(result.point).toEqual(target);
    expect(gapToShape(rect, result.delta)).toBeLessThanOrEqual(0.001);
    // the upper-right corner of its bounding box (1.414, 2.828) is no point of the bed: it does not snap
    const phantom = resolveMoveSnap(sources, [0, 0], [5 - Math.SQRT2 + 0.03, 5 - 2 * Math.SQRT2 + 0.02], {
      ...BASE,
      candidates: single,
    });
    expect(phantom.kind).toBe('grid');
    expect(expectOnlyRealCorners(rect)).toBeGreaterThan(0);
  });

  it('a circle snaps with its centre and its four cardinal points, not the corners of its box', () => {
    const circle: Geometry = { kind: 'circle', origin: [0, 0], radius_m: 1 };
    expect(moveSources(circle)).toEqual([
      [0, 0],
      [1, 0],
      [0, 1],
      [-1, 0],
      [0, -1],
    ]);
    // the box corner (1, 1) would land on the target with a gap of r * (sqrt 2 - 1) to the circle
    const phantom = resolveMoveSnap(moveSources(circle), [0, 0], [4.03, 4.02], {
      ...BASE,
      candidates: single,
    });
    expect(phantom.kind).not.toBe('corner');
    const east = resolveMoveSnap(moveSources(circle), [0, 0], [4.03, 5.02], { ...BASE, candidates: single });
    expect(east).toMatchObject({ kind: 'corner', point: target });
    expect(gapToShape(circle, east.delta)).toBeLessThanOrEqual(0.001);
    expect(expectOnlyRealCorners(circle)).toBeGreaterThan(0);
  });

  it('a rotated polygon and a polyline snap with their vertices', () => {
    const polygon: Geometry = {
      kind: 'polygon',
      points: [
        [1, 1],
        [3, 1],
        [2, 3],
      ],
      rotation_deg: 30,
    };
    const vertices = (toShape(polygon) as { vertices: Point[] }).vertices;
    const sources = moveSources(polygon);
    expect(sources).toHaveLength(3);
    expect(sources[0]).toEqual([1, 1]);
    sources.forEach((source, i) => {
      expect(source[0]).toBeCloseTo(vertices[i][0], 9);
      expect(source[1]).toBeCloseTo(vertices[i][1], 9);
    });
    expect(expectOnlyRealCorners(polygon)).toBeGreaterThan(0);
    const line: Geometry = {
      kind: 'polyline',
      points: [
        [0, 0],
        [2, 1],
        [4, 0],
      ],
      width_m: 0.3,
    };
    expect(moveSources(line)).toEqual([
      [0, 0],
      [2, 1],
      [4, 0],
    ]);
    expect(expectOnlyRealCorners(line)).toBeGreaterThan(0);
  });
});

describe('resolveMoveSnap: a corner within tolerance beats a nearer edge (GP-FR-154)', () => {
  // the source sits exactly ON an edge (distance 0) while a corner is 0.08 m (8 px) away
  const candidates: SnapCandidates = {
    corners: [[2, 1.08]],
    edges: [
      [
        [0, 1],
        [4, 1],
      ],
    ],
  };

  it('one source: the corner wins although the edge is nearer', () => {
    const result = resolveMoveSnap([[2, 1]], [2, 1], [0, 0], { ...BASE, candidates });
    expect(result).toMatchObject({ kind: 'corner', point: [2, 1.08] });
  });

  it('several sources: a corner of one source beats an edge that another source already touches', () => {
    // source 0 lies on the edge, source 1 is 0.08 m from the corner (the order must not matter either)
    const shifted: Point[] = [
      [1, 1],
      [2, 1.16],
    ];
    for (const list of [shifted, [...shifted].reverse()]) {
      const result = resolveMoveSnap(list, list[0], [0, 0], { ...BASE, candidates });
      expect(result.kind).toBe('corner');
      expect(result.point).toEqual([2, 1.08]);
      expect(result.delta[0]).toBeCloseTo(0, 9);
      expect(result.delta[1]).toBeCloseTo(-0.08, 9);
    }
  });
});
