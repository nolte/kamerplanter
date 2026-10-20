import { describe, expect, it } from 'vitest';
import { resolveSnap, type SnapOptions } from './snap';

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
