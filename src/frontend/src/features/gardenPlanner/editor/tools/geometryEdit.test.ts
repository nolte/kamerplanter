import { describe, expect, it } from 'vitest';
import { boundingBox, toShape } from '../../model/geometry';
import type { PolygonGeometry, RectGeometry } from '../../model/types';
import {
  angleBetween,
  effectiveVertices,
  geometryCenter,
  insertVertex,
  moveGeometry,
  moveVertex,
  normalizeAngle,
  removeVertex,
  resizeCircle,
  resizeRect,
  rotationDelta,
  snapAngle,
  translateGeometry,
} from './geometryEdit';

const rect: RectGeometry = {
  kind: 'rect',
  origin: [2, 3],
  width_m: 4,
  length_m: 2,
  rotation_deg: 0,
};
const square: PolygonGeometry = {
  kind: 'polygon',
  points: [
    [0, 0],
    [4, 0],
    [4, 4],
    [0, 4],
  ],
  rotation_deg: 0,
};

describe('angles', () => {
  it('normalises into [0, 360) and snaps to the step', () => {
    expect(normalizeAngle(-90)).toBe(270);
    expect(normalizeAngle(360)).toBe(0);
    expect(normalizeAngle(359.9996)).toBe(0);
    expect(snapAngle(52, 15)).toBe(45);
    expect(snapAngle(40, 45)).toBe(45);
    expect(snapAngle(100, 90)).toBe(90);
  });

  it('measures the turn about a pivot', () => {
    expect(angleBetween([0, 0], [1, 0], [0, 1])).toBeCloseTo(90);
    expect(angleBetween([0, 0], [1, 0], [0, -1])).toBeCloseTo(-90);
  });

  it('snaps the resulting rotation, not the delta, and is free without a step (Alt)', () => {
    const turned = { ...rect, rotation_deg: 10 };
    // Pointer swings 20 degrees: 10 + 20 = 30 is a multiple of 15, so the delta is 20.
    const target: [number, number] = [
      Math.cos((20 * Math.PI) / 180),
      Math.sin((20 * Math.PI) / 180),
    ];
    expect(rotationDelta(turned, [0, 0], [1, 0], target, 15)).toBeCloseTo(20);
    // 10 + 24 = 34 snaps to 30: delta 20 again; to 45 with a 45 step: delta 35.
    const t2: [number, number] = [Math.cos((24 * Math.PI) / 180), Math.sin((24 * Math.PI) / 180)];
    expect(rotationDelta(turned, [0, 0], [1, 0], t2, 15)).toBeCloseTo(20);
    expect(rotationDelta(turned, [0, 0], [1, 0], t2, 45)).toBeCloseTo(35);
    expect(rotationDelta(turned, [0, 0], [1, 0], t2, null)).toBeCloseTo(24);
  });
});

describe('moveGeometry', () => {
  it('translates every kind and rounds to the storage precision', () => {
    expect(translateGeometry(rect, [1.0004, -1])).toMatchObject({ origin: [3, 2] });
    expect(
      translateGeometry({ kind: 'circle', origin: [5, 5], radius_m: 1 }, [1, 1]),
    ).toMatchObject({ origin: [6, 6] });
    expect(translateGeometry({ kind: 'point', origin: [1, 1] }, [2, 2])).toMatchObject({
      origin: [3, 3],
    });
    const poly = translateGeometry(square, [1, 1]) as PolygonGeometry;
    expect(poly.points[0]).toEqual([1, 1]);
    expect(poly.points[2]).toEqual([5, 5]);
    const line = translateGeometry(
      {
        kind: 'polyline',
        points: [
          [0, 0],
          [1, 1],
        ],
        width_m: 0.3,
      },
      [1, 0],
    );
    expect(line).toMatchObject({
      points: [
        [1, 0],
        [2, 1],
      ],
    });
  });

  it('rotates a rect rigidly: the bed frame, and so its slots, turn with it', () => {
    const turned = moveGeometry(rect, {
      translate: [0, 0],
      rotateDeg: 90,
      pivot: geometryCenter(rect),
    }) as RectGeometry;
    expect(turned.rotation_deg).toBe(90);
    // The centre stays where it was.
    const [cx, cy] = geometryCenter(turned);
    expect(cx).toBeCloseTo(4, 2);
    expect(cy).toBeCloseTo(4, 2);
    // Same area, bounding box swapped.
    const [x0, y0, x1, y1] = boundingBox(turned);
    expect(x1 - x0).toBeCloseTo(2, 2);
    expect(y1 - y0).toBeCloseTo(4, 2);
  });

  it('rotates a polygon with a rotation_deg of its own about the same pivot', () => {
    const before = { ...square, rotation_deg: 30 };
    const pivot = geometryCenter(before);
    const after = moveGeometry(before, { translate: [0, 0], rotateDeg: 45, pivot });
    const a = effectiveVertices(after);
    const b = effectiveVertices(before);
    // Each vertex moved by a rotation of 45 degrees about the pivot.
    for (let i = 0; i < a.length; i += 1) {
      const angle = (angleBetween(pivot, b[i], a[i]) + 360) % 360;
      expect(angle).toBeCloseTo(45, 1);
    }
    expect((after as PolygonGeometry).rotation_deg).toBe(75);
  });

  it('rotates a polyline by turning its points', () => {
    const line = {
      kind: 'polyline' as const,
      points: [
        [0, 0],
        [2, 0],
      ] as [number, number][],
      width_m: 0.3,
    };
    const turned = moveGeometry(line, { translate: [0, 0], rotateDeg: 90, pivot: [0, 0] });
    expect(turned).toMatchObject({
      points: [
        [0, 0],
        [0, 2],
      ],
    });
  });
});

describe('resizeRect', () => {
  it('moves one edge and keeps the opposite one', () => {
    const east = resizeRect(rect, 'e', [8, 99], false);
    expect(east).toMatchObject({ origin: [2, 3], width_m: 6, length_m: 2 });
    const west = resizeRect(rect, 'w', [1, 0], false);
    expect(west).toMatchObject({ origin: [1, 3], width_m: 5, length_m: 2 });
    const north = resizeRect(rect, 'n', [0, 7], false);
    expect(north).toMatchObject({ origin: [2, 3], width_m: 4, length_m: 4 });
  });

  it('moves two edges for a corner and mirrors when dragged past the opposite corner', () => {
    expect(resizeRect(rect, 'ne', [7, 6], false)).toMatchObject({ width_m: 5, length_m: 3 });
    const mirrored = resizeRect(rect, 'ne', [0, 1], false);
    expect(mirrored).toMatchObject({ origin: [0, 1], width_m: 2, length_m: 2 });
  });

  it('works in the rect frame when the rect is rotated', () => {
    const turned: RectGeometry = { ...rect, rotation_deg: 90 };
    // Rotated 90 degrees the local x axis points up: the east handle sits above the origin.
    const grown = resizeRect(turned, 'e', [2, 9], false);
    expect(grown.width_m).toBeCloseTo(6, 3);
    expect(grown.length_m).toBe(2);
    expect(grown.origin).toEqual([2, 3]);
  });

  it('keeps the aspect ratio on a corner with Shift', () => {
    const grown = resizeRect(rect, 'ne', [10, 4], true);
    expect(grown.width_m / grown.length_m).toBeCloseTo(2, 3);
    expect(grown.width_m).toBe(8);
  });

  it('never falls below the minimum size', () => {
    expect(resizeRect(rect, 'e', [2, 0], false).width_m).toBe(0.01);
  });
});

describe('resizeCircle', () => {
  it('reaches the pointer and keeps a minimum', () => {
    expect(resizeCircle({ origin: [0, 0], radius_m: 1 }, [3, 4])).toBe(5);
    expect(resizeCircle({ origin: [0, 0], radius_m: 1 }, [0, 0])).toBe(0.01);
  });
});

describe('polygon points (GP-FR-023)', () => {
  it('moves a vertex and keeps the rest', () => {
    const moved = moveVertex(square, 2, [6, 6]) as PolygonGeometry;
    expect(moved.points).toEqual([
      [0, 0],
      [4, 0],
      [6, 6],
      [0, 4],
    ]);
  });

  it('writes vertices back through the stored rotation', () => {
    const turned: PolygonGeometry = { ...square, rotation_deg: 90 };
    const moved = moveVertex(turned, 2, [-5, 7]);
    expect(effectiveVertices(moved)[2][0]).toBeCloseTo(-5, 3);
    expect(effectiveVertices(moved)[2][1]).toBeCloseTo(7, 3);
    // The others stay where they were on the plan.
    expect(effectiveVertices(moved)[1][0]).toBeCloseTo(effectiveVertices(turned)[1][0], 3);
    expect(toShape(moved).kind).toBe('vertices');
  });

  it('inserts a vertex in the middle of an edge, also the closing one, but not past a polyline end', () => {
    const inserted = insertVertex(square, 0) as PolygonGeometry;
    expect(inserted.points).toEqual([
      [0, 0],
      [2, 0],
      [4, 0],
      [4, 4],
      [0, 4],
    ]);
    const closing = insertVertex(square, 3) as PolygonGeometry;
    expect(closing.points).toEqual([
      [0, 0],
      [4, 0],
      [4, 4],
      [0, 4],
      [0, 2],
    ]);
    const line = {
      kind: 'polyline' as const,
      points: [
        [0, 0],
        [2, 0],
      ] as [number, number][],
      width_m: 0.3,
    };
    expect(insertVertex(line, 1)).toBe(line);
  });

  it('deletes a vertex but never below three (polygon) or two (polyline)', () => {
    const triangle: PolygonGeometry = {
      kind: 'polygon',
      points: [
        [0, 0],
        [4, 0],
        [0, 4],
      ],
      rotation_deg: 0,
    };
    expect(removeVertex(triangle, 1)).toBeNull();
    expect((removeVertex(square, 1) as PolygonGeometry).points).toEqual([
      [0, 0],
      [4, 4],
      [0, 4],
    ]);
    const line = {
      kind: 'polyline' as const,
      points: [
        [0, 0],
        [2, 0],
      ] as [number, number][],
      width_m: 0.3,
    };
    expect(removeVertex(line, 0)).toBeNull();
    expect(
      removeVertex(
        {
          ...line,
          points: [
            [0, 0],
            [2, 0],
            [3, 3],
          ],
        },
        0,
      ),
    ).not.toBeNull();
  });
});
