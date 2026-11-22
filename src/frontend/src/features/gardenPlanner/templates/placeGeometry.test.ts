import { describe, expect, it } from 'vitest';
import { boundingBox } from '../model/geometry';
import type { Geometry } from '../model/types';
import { bedFrameGeometry, originForCentre, placeGeometry } from './placeGeometry';

describe('placeGeometry (port of template_placement_calculator.py)', () => {
  it('puts the anchor of a rectangle at the origin and adds the requested turn', () => {
    expect(
      placeGeometry(
        { kind: 'rect', origin: [0, 0], width_m: 2, length_m: 1, rotation_deg: 30 },
        [4, 1],
        90,
      ),
    ).toEqual({ kind: 'rect', origin: [4, 1], width_m: 2, length_m: 1, rotation_deg: 120 });
  });

  it('folds the turn into [0, 360)', () => {
    const placed = placeGeometry(
      { kind: 'rect', origin: [0, 0], width_m: 1, length_m: 1, rotation_deg: 270 },
      [0, 0],
      180,
    );
    expect(placed).toMatchObject({ rotation_deg: 90 });
    const full = placeGeometry(
      { kind: 'rect', origin: [0, 0], width_m: 1, length_m: 1, rotation_deg: 0 },
      [0, 0],
      0,
    );
    expect(full).toMatchObject({ rotation_deg: 0 });
  });

  it('moves a circle by its centre and ignores the turn', () => {
    expect(placeGeometry({ kind: 'circle', origin: [0, 0], radius_m: 0.2 }, [3, 2], 90)).toEqual({
      kind: 'circle',
      origin: [3, 2],
      radius_m: 0.2,
    });
  });

  it('keeps the vertices of a polygon relative to its first vertex', () => {
    expect(
      placeGeometry(
        {
          kind: 'polygon',
          points: [
            [0, 0],
            [2, 0],
            [2, 1],
          ],
          rotation_deg: 0,
        },
        [1, 1],
        45,
      ),
    ).toEqual({
      kind: 'polygon',
      points: [
        [1, 1],
        [3, 1],
        [3, 2],
      ],
      rotation_deg: 45,
    });
  });

  it('refuses a shape that is no bed', () => {
    expect(placeGeometry({ kind: 'point', origin: [0, 0] }, [1, 1], 0)).toBeNull();
    expect(
      bedFrameGeometry({
        kind: 'polyline',
        points: [
          [0, 0],
          [1, 1],
        ],
        width_m: 0.1,
      }),
    ).toBeNull();
  });
});

describe('bedFrameGeometry', () => {
  it('moves the anchor to the origin and keeps the rotation', () => {
    expect(
      bedFrameGeometry({ kind: 'rect', origin: [5, 6], width_m: 2, length_m: 1, rotation_deg: 30 }),
    ).toEqual({ kind: 'rect', origin: [0, 0], width_m: 2, length_m: 1, rotation_deg: 30 });
    expect(bedFrameGeometry({ kind: 'circle', origin: [5, 6], radius_m: 1 })).toEqual({
      kind: 'circle',
      origin: [0, 0],
      radius_m: 1,
    });
  });

  it('makes the first vertex of a polygon the origin', () => {
    expect(
      bedFrameGeometry({
        kind: 'polygon',
        points: [
          [4, 4],
          [6, 4],
          [6, 5],
        ],
        rotation_deg: 0,
      }),
    ).toEqual({
      kind: 'polygon',
      points: [
        [0, 0],
        [2, 0],
        [2, 1],
      ],
      rotation_deg: 0,
    });
  });

  it('round-trips through placeGeometry', () => {
    const bed: Geometry = {
      kind: 'rect',
      origin: [5, 6],
      width_m: 2,
      length_m: 1,
      rotation_deg: 0,
    };
    const frame = bedFrameGeometry(bed)!;
    expect(placeGeometry(frame, [5, 6], 0)).toEqual(bed);
  });
});

describe('originForCentre (#2536)', () => {
  const rect: Geometry = { kind: 'rect', origin: [0, 0], width_m: 2, length_m: 1, rotation_deg: 0 };

  it('puts the middle of a rectangle, not its corner, on the target', () => {
    expect(originForCentre(rect, 0, [10, 10])).toEqual([9, 9.5]);
  });

  it('follows the turn: a 2 x 1 m rect turned by 90 degrees spans x -1..0, y 0..2 about its anchor', () => {
    const origin = originForCentre(rect, 90, [10, 10])!;
    expect(origin).toEqual([10.5, 9]);
    const placed = placeGeometry(rect, origin, 90)!;
    const [x0, y0, x1, y1] = boundingBox(placed);
    expect([(x0 + x1) / 2, (y0 + y1) / 2]).toEqual([10, 10]);
  });

  it('keeps a circle on its centre and centres a polygon by its box', () => {
    expect(originForCentre({ kind: 'circle', origin: [0, 0], radius_m: 0.5 }, 90, [3, 4])).toEqual([3, 4]);
    const polygon: Geometry = {
      kind: 'polygon',
      points: [
        [0, 0],
        [4, 0],
        [4, 2],
      ],
      rotation_deg: 0,
    };
    expect(originForCentre(polygon, 0, [10, 10])).toEqual([8, 9]);
  });

  it('has nothing to centre for a non-bed shape', () => {
    expect(originForCentre({ kind: 'point', origin: [0, 0] }, 0, [1, 1])).toBeNull();
  });
});
