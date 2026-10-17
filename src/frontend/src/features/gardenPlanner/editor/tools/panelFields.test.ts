import { describe, expect, it } from 'vitest';
import type { Geometry } from '../../model/types';
import { geometryFields, parseDecimal, pointList, setField, setPoint } from './panelFields';

const rect: Geometry = { kind: 'rect', origin: [1, 2], width_m: 3, length_m: 4, rotation_deg: 0 };

describe('parseDecimal', () => {
  it('reads both separators and trims', () => {
    expect(parseDecimal(' 1,25 ')).toBe(1.25);
    expect(parseDecimal('2.5')).toBe(2.5);
    expect(parseDecimal('-0.5')).toBe(-0.5);
  });
  it('refuses text, blanks and thousands separators', () => {
    for (const text of ['', ' ', 'abc', '1,2,3', '1e3', '1 000', '--1'])
      expect(parseDecimal(text)).toBeNull();
  });
});

describe('geometryFields / setField', () => {
  it('offers position, size and rotation of a rectangle', () => {
    expect(geometryFields(rect).map((f) => f.id)).toEqual([
      'x',
      'y',
      'width',
      'length',
      'rotation',
    ]);
  });
  it('changes one field and rounds to the storage precision', () => {
    expect(setField(rect, 'width', 2.00049)).toMatchObject({ width_m: 2 });
    expect(setField(rect, 'x', 7)).toMatchObject({ origin: [7, 2] });
    expect(setField(rect, 'rotation', 370)).toMatchObject({ rotation_deg: 10 });
  });
  it('ignores a field the shape does not have', () => {
    expect(setField(rect, 'radius', 1)).toBe(rect);
  });
  it('has no scalar fields for a polygon, whose points are listed instead', () => {
    const polygon: Geometry = {
      kind: 'polygon',
      points: [
        [0, 0],
        [2, 0],
        [1, 2],
      ],
      rotation_deg: 0,
    };
    expect(geometryFields(polygon)).toEqual([]);
    expect(pointList(polygon)).toHaveLength(3);
    expect(setPoint(polygon, 2, [1, 3])).toMatchObject({
      points: [
        [0, 0],
        [2, 0],
        [1, 3],
      ],
    });
  });
});
