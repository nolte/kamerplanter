import { describe, expect, it } from 'vitest';
import { testPlan } from './toolTestKit';
import { addWithDimensions, geometryOfValues, type DimensionValues } from './addDimensions';

const base: DimensionValues = {
  target: 'bed',
  bedTypeKey: 'raised_bed',
  objectType: 'other',
  name: '',
  shape: 'rect',
  x: 14,
  y: 14,
  width: 2,
  length: 1,
  radius: null,
  rotation: 0,
  strokeWidth: null,
  points: [],
};

describe('geometryOfValues', () => {
  it('builds a rectangle and names the first missing field otherwise', () => {
    expect(geometryOfValues(base)).toEqual({
      geometry: { kind: 'rect', origin: [14, 14], width_m: 2, length_m: 1, rotation_deg: 0 },
    });
    expect(geometryOfValues({ ...base, width: null })).toEqual({ missing: 'width' });
  });
  it('builds a polygon from its point list and refuses an unfinished point', () => {
    const polygon = {
      ...base,
      shape: 'polygon' as const,
      points: [
        [0, 0],
        [2, 0],
        [1, 2],
      ] as [number, number][],
    };
    expect(geometryOfValues(polygon)).toMatchObject({ geometry: { kind: 'polygon' } });
    expect(geometryOfValues({ ...polygon, points: [[0, 0], null, [1, 2]] })).toEqual({
      missing: 'point1',
    });
  });
});

describe('addWithDimensions', () => {
  it('creates a bed of the chosen type with the typed name', () => {
    const out = addWithDimensions(testPlan(), { ...base, name: 'Herbs' }, 'Bed 9');
    expect(out.ok).toBe(true);
    if (out.ok) {
      expect(out.ops[0]).toMatchObject({
        op: 'create_location',
        data: { name: 'Herbs', location_type_key: 'raised_bed' },
      });
      expect(out.selection.entity).toBe('location');
    }
  });
  it('falls back to the suggested name for a blank one', () => {
    const out = addWithDimensions(testPlan(), base, 'Bed 9');
    expect(out.ok && out.ops[0]).toMatchObject({ data: { name: 'Bed 9' } });
  });
  it('creates a garden object with the props its type requires', () => {
    const out = addWithDimensions(
      testPlan(),
      { ...base, target: 'garden_object', objectType: 'trellis', shape: 'rect' },
      'x',
    );
    expect(out.ok && out.ops[0]).toMatchObject({
      op: 'create_garden_object',
      data: { object_type: 'trellis', props: { height_m: 1.8 } },
    });
  });
  it('refuses a shape outside the garden boundary with the live-validation code', () => {
    const out = addWithDimensions(testPlan(), { ...base, x: 30 }, 'x');
    expect(out).toEqual({ ok: false, code: 'geometry.outside_parent' });
  });
  it('refuses a missing number as invalid geometry', () => {
    expect(addWithDimensions(testPlan(), { ...base, length: null }, 'x')).toEqual({
      ok: false,
      code: 'geometry.invalid',
    });
  });
});
