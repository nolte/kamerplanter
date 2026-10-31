import { describe, expect, it } from 'vitest';
import { centroid, pointInPolygon } from './geometry';
import {
  centredRoom,
  labelAnchor,
  labelLength,
  MAX_START_CELLS_PER_AXIS,
  poleOfInaccessibility,
  truncateLabel,
} from './labelAnchor';
import type { Point } from './types';

/** Edge cases of the port the shared vectors (`labelAnchor.vectors.test.ts`) do not need to carry. */
const L_SHAPE: Point[] = [
  [0, 0],
  [4, 0],
  [4, 1],
  [1, 1],
  [1, 4],
  [0, 4],
];

describe('poleOfInaccessibility', () => {
  it('finds the pole of an L-shape inside it, where the centroid lies in the notch', () => {
    const pole = poleOfInaccessibility(L_SHAPE);
    expect(pointInPolygon(pole, L_SHAPE)).toBe(true);
    // analytic: (t, t) with t = sqrt2 / (1 + sqrt2) = 0.586
    expect(pole[0]).toBeCloseTo(0.586, 2);
    expect(pole[1]).toBeCloseTo(0.586, 2);
    const geometryCentroid = centroid({ kind: 'polygon', points: L_SHAPE, rotation_deg: 0 });
    expect(pointInPolygon(geometryCentroid, L_SHAPE)).toBe(false);
  });

  it('falls back to the first vertex for a polygon without area', () => {
    expect(
      poleOfInaccessibility([
        [1, 1],
        [2, 1],
        [3, 1],
      ]),
    ).toEqual([1, 1]);
  });
});

describe('poleOfInaccessibility - bounded work (SCR-001)', () => {
  const slivers: [string, Point[]][] = [
    [
      'rect 1000 x 0.001 m',
      [
        [0, 0],
        [1000, 0],
        [1000, 0.001],
        [0, 0.001],
      ],
    ],
    [
      'triangle 1000 x 0.002 m',
      [
        [0, 0],
        [1000, 0],
        [0, 0.002],
      ],
    ],
    [
      'upright 0.001 x 1000 m',
      [
        [0, 0],
        [0.001, 0],
        [0.001, 1000],
        [0, 1000],
      ],
    ],
  ];

  it.each(slivers)('searches a %s sliver within the time budget, inside the shape', (_name, vertices) => {
    // the textbook start grid held a million cells for the first one
    const started = performance.now();
    const pole = poleOfInaccessibility(vertices);
    expect(performance.now() - started).toBeLessThan(250);
    expect(pointInPolygon(pole, vertices)).toBe(true);
  });

  it('keeps the textbook start grid up to the cap: a 64:1 strip finds its mid-line', () => {
    const length = MAX_START_CELLS_PER_AXIS * 0.3;
    const pole = poleOfInaccessibility([
      [0, 0],
      [length, 0],
      [length, 0.3],
      [0, 0.3],
    ]);
    expect(Math.abs(pole[1] - 0.15)).toBeLessThanOrEqual(0.01);
  });

  it.each([NaN, Infinity, -Infinity])('falls back to the first vertex for a vertex coordinate %s', (bad) => {
    expect(
      poleOfInaccessibility([
        [1, 2],
        [4, 2],
        [bad, 4],
        [1, 4],
      ]),
    ).toEqual([1, 2]);
  });
});

describe('centredRoom', () => {
  it('is symmetric about the point', () => {
    expect(centredRoom(L_SHAPE, [1, 0.5])).toBeCloseTo(2);
  });

  it('is null for a point outside the shape', () => {
    expect(centredRoom(L_SHAPE, [3, 3])).toBeNull();
  });

  it('meets a vertex on the line once', () => {
    expect(centredRoom(L_SHAPE, [0.5, 1])).toBeCloseTo(1);
  });
});

describe('labelAnchor', () => {
  it('turns a rect with its rotation and measures the room on the page', () => {
    const anchor = labelAnchor({ kind: 'rect', origin: [5, 5], width_m: 4, length_m: 1, rotation_deg: 90 });
    expect(anchor.point[0]).toBeCloseTo(4.5, 3);
    expect(anchor.point[1]).toBeCloseTo(7, 3);
    expect(anchor.widthM).toBeCloseTo(1, 3);
  });

  it('is deterministic (GP-FR-003)', () => {
    const geometry = { kind: 'polygon', points: L_SHAPE, rotation_deg: 0 } as const;
    expect(labelAnchor(geometry)).toEqual(labelAnchor(geometry));
  });
});

describe('truncateLabel', () => {
  it('keeps a name that fits', () => {
    expect(truncateLabel('Beet 1', 6)).toBe('Beet 1');
  });

  it('cuts with an ellipsis and drops the space before it', () => {
    expect(truncateLabel('Beet am Zaun', 6)).toBe('Beet…');
    expect(truncateLabel('Kräuterspirale', 6)).toBe('Kräut…');
  });

  it('counts code points, never splitting a character outside the BMP (SCR-004)', () => {
    expect(labelLength('🌱🌱🌱🌱 Beet')).toBe(9);
    expect(truncateLabel('🌱🌱🌱🌱 Beet', 6)).toBe('🌱🌱🌱🌱…');
    expect(truncateLabel('𝔅𝔢𝔢𝔱 𝟏', 6)).toBe('𝔅𝔢𝔢𝔱 𝟏');
    expect(truncateLabel('🍅🍅🍅🍅🍅🍅', 4)).not.toMatch(/[\uD800-\uDBFF](?![\uDC00-\uDFFF])/);
  });

  it('collapses runs of whitespace like the PDF writer', () => {
    expect(truncateLabel('  Beet \n  Nord  ', 20)).toBe('Beet Nord');
  });
});
