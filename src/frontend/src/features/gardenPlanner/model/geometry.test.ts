import { describe, expect, it } from 'vitest';
import {
  areaM2,
  boundingBox,
  contains,
  parseGeometry,
  roundLength,
  toLocalShape,
  toShape,
  transformBedToPlan,
  transformPlanToBed,
} from './geometry';

/** Rules of the port that the shared vector file cannot pin from one side only. */
describe('roundLength (GP-FR-004)', () => {
  it('rounds the exact binary value, ties away from zero', () => {
    expect(roundLength(2.0625)).toBe(2.063); // an exact binary tie
    expect(roundLength(-2.0625)).toBe(-2.063); // away from zero, not toward +infinity
    expect(roundLength(1.0005)).toBe(1); // binary-below the tie
    expect(roundLength(0.0045)).toBe(0.004);
  });

  it('stores negative zero as zero', () => {
    expect(Object.is(roundLength(-0.0004), 0)).toBe(true);
    expect(Object.is(roundLength(-0), 0)).toBe(true);
  });
});

describe('parseGeometry (V-01)', () => {
  it('rejects what is not an object, has an unknown key or a wrong kind', () => {
    expect(parseGeometry(null)).toBeNull();
    expect(parseGeometry([])).toBeNull();
    expect(parseGeometry({ kind: 'point', origin: [1, 1], extra: 1 })).toBeNull();
    expect(parseGeometry({ origin: [1, 1] })).toBeNull();
  });

  it('rejects non-finite numbers and malformed points', () => {
    expect(parseGeometry({ kind: 'point', origin: [Number.NaN, 1] })).toBeNull();
    expect(parseGeometry({ kind: 'point', origin: [Infinity, 1] })).toBeNull();
    expect(parseGeometry({ kind: 'point', origin: [1, 1, 1] })).toBeNull();
  });

  it('caps polygons at 200 points', () => {
    const ring = (n: number) => Array.from({ length: n }, (_, i) => [i % 100, Math.floor(i / 100)]);
    expect(parseGeometry({ kind: 'polygon', points: ring(200) })).not.toBeNull();
    expect(parseGeometry({ kind: 'polygon', points: ring(201) })).toBeNull();
  });

  it('defaults rotation_deg and is a pure function of its input', () => {
    const raw = { kind: 'rect', origin: [1, 2], width_m: 3, length_m: 4 };
    expect(parseGeometry(raw)).toEqual({ ...raw, rotation_deg: 0 });
    expect(raw).not.toHaveProperty('rotation_deg');
  });
});

describe('derived values', () => {
  it('area and bbox of the §20.1 rotated rectangle', () => {
    const geometry = parseGeometry({
      kind: 'rect',
      origin: [1, 1],
      width_m: 2,
      length_m: 1,
      rotation_deg: 90,
    })!;
    expect(areaM2(geometry)).toBe(2);
    expect(boundingBox(geometry)).toEqual([0, 1, 1, 3]);
  });

  it('bed and plan frame are inverse transforms of each other', () => {
    const bed = parseGeometry({
      kind: 'rect',
      origin: [4, 5],
      width_m: 2,
      length_m: 1,
      rotation_deg: 33,
    })!;
    const [px, py] = transformBedToPlan([0.7, 0.4], bed);
    const [bx, by] = transformPlanToBed([px, py], bed);
    expect(bx).toBeCloseTo(0.7, 9);
    expect(by).toBeCloseTo(0.4, 9);
  });

  it('refuses a parent without an area', () => {
    const line = toShape(
      parseGeometry({
        kind: 'polyline',
        points: [
          [0, 0],
          [1, 1],
        ],
        width_m: 0.1,
      })!,
    );
    expect(() => contains(line, line)).toThrow(/area shape/);
    expect(toLocalShape(parseGeometry({ kind: 'point', origin: [3, 3] })!)).toEqual({
      kind: 'vertices',
      vertices: [[0, 0]],
      closed: false,
    });
  });
});
