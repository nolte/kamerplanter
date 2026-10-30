import { describe, expect, it } from 'vitest';
import { moveSources, resolveMoveSnap, resolveSnap, type SnapOptions } from './snap';

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

describe('resolveMoveSnap: every bbox corner of the dragged object is a source (GP-FR-154)', () => {
  // A 2 x 2 m bed with its anchor (lower-left corner) at (14, 2): sources are its four corners.
  const sources = moveSources([14, 2, 16, 4], [14, 2]);
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

  it('lists the four corners and adds an anchor that is not one of them', () => {
    expect(sources).toEqual([
      [14, 2],
      [16, 2],
      [16, 4],
      [14, 4],
    ]);
    expect(moveSources([0, 0, 2, 2], [1, 1])).toHaveLength(5); // circle: the centre too
  });

  it('right edge to left edge: the right edge of the dragged bed lands on the left edge of another', () => {
    // dragged by (-10.1, 0.5): its right edge is at x 5.9, 0.1 m (10 px) left of b2's left edge x = 6
    const result = resolveMoveSnap(sources, reference, [-10.1, 0.5], { ...BASE, candidates });
    expect(result.kind).toBe('edge');
    expect(result.delta[0]).toBeCloseTo(-10, 6);
    expect(result.delta[1]).toBeCloseTo(0.5, 6);
    // the marker is the snapped source - the upper-right corner on b2's edge - not the pointer
    expect(result.point).toEqual([6, 4.5]);
    expect(result.guide).toEqual([
      [6, 5],
      [6, 3],
    ]);
  });

  it('the anchor alone would have missed it: the old anchor-only snap falls back to the grid', () => {
    expect(resolveSnap([14 - 10.1, 2 + 0.5], { ...BASE, candidates }).kind).toBe('grid');
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
    // right edge 0.15 m (15 px) left of b2's left edge
    const raw: [number, number] = [-10.15, 0.5];
    expect(resolveMoveSnap(sources, reference, raw, { ...BASE, candidates }).kind).toBe('grid');
    expect(
      resolveMoveSnap(sources, reference, raw, { ...BASE, candidates, pointerType: 'touch' }).kind,
    ).toBe('edge');
  });

  it('Alt keeps the raw move, rounded to the storage precision', () => {
    const result = resolveMoveSnap(sources, reference, [-10.1004, 0.5], {
      ...BASE,
      candidates,
      bypass: true,
    });
    expect(result.kind).toBe('none');
    expect(result.point).toEqual([3.9, 2.5]);
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
