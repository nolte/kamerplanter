import { describe, expect, it } from 'vitest';
import type { Geometry } from '../../model/types';
import { formatDecimal } from '../../model/units';
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

describe('formatDecimal (#2905, UI-NFR-007 R-014)', () => {
  it('writes the separator of the language, without grouping or rounding', () => {
    expect(formatDecimal(0.9, 'de')).toBe('0,9');
    expect(formatDecimal(0.9, 'en')).toBe('0.9');
    expect(formatDecimal(-1234.5678, 'de')).toBe('-1234,5678');
    expect(formatDecimal(1234.5678, 'en-US')).toBe('1234.5678');
    expect(formatDecimal(3, 'de')).toBe('3');
  });
  it('writes a missing or unset value as an empty text', () => {
    expect(formatDecimal(null, 'de')).toBe('');
    expect(formatDecimal(undefined, 'en')).toBe('');
    expect(formatDecimal(Number.NaN, 'de')).toBe('');
  });
  it('round-trips through parseDecimal without drift', () => {
    for (const language of ['de', 'en'])
      for (const value of [0.1, 0.3, 0.1 + 0.2, 1.005, -0.5, 12.345, 999.999])
        expect(parseDecimal(formatDecimal(value, language))).toBe(value);
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
