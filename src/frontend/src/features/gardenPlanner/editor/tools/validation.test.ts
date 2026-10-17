import { describe, expect, it } from 'vitest';
import type { Geometry } from '../../model/types';
import {
  firstViolation,
  inferParentKey,
  violationOfNew,
  ERROR_INVALID,
  ERROR_OUTSIDE_PARENT,
} from './validation';
import { testPlan } from './toolTestKit';

const rect = (x: number, y: number, w: number, l: number): Geometry => ({
  kind: 'rect',
  origin: [x, y],
  width_m: w,
  length_m: l,
  rotation_deg: 0,
});

describe('firstViolation (GP-UX-053)', () => {
  it('accepts a bed that stays inside its area', () => {
    expect(
      firstViolation(testPlan(), [{ entity: 'location', key: 'b1', geometry: rect(4, 4, 2, 2) }]),
    ).toBeNull();
  });

  it('flags a bed pushed out of its area (V-03)', () => {
    const result = firstViolation(testPlan(), [
      { entity: 'location', key: 'b1', geometry: rect(11, 3, 2, 2) },
    ]);
    expect(result).toBe(ERROR_OUTSIDE_PARENT);
  });

  it('checks a parentless bed against the garden boundary', () => {
    const plan = testPlan();
    expect(
      firstViolation(plan, [{ entity: 'location', key: 'solo', geometry: rect(19.5, 2, 2, 2) }]),
    ).toBe(ERROR_OUTSIDE_PARENT);
    expect(
      firstViolation(plan, [{ entity: 'location', key: 'solo', geometry: rect(18, 2, 2, 2) }]),
    ).toBeNull();
  });

  it('flags the children a resized area no longer holds', () => {
    const shrunk = [{ entity: 'location' as const, key: 'area', geometry: rect(2, 2, 3, 3) }];
    expect(firstViolation(testPlan(), shrunk)).toBe(ERROR_OUTSIDE_PARENT);
  });

  it('lets an area move with its children (they move in the same change)', () => {
    const plan = testPlan();
    const moved = [
      { entity: 'location' as const, key: 'area', geometry: rect(8, 8, 10, 10) },
      { entity: 'location' as const, key: 'b1', geometry: rect(9, 9, 2, 2) },
      { entity: 'location' as const, key: 'b2', geometry: rect(12, 9, 2, 2) },
      {
        entity: 'garden_object' as const,
        key: 't1',
        geometry: { kind: 'circle' as const, origin: [15, 15] as [number, number], radius_m: 0.5 },
      },
    ];
    expect(firstViolation(plan, moved)).toBeNull();
    // Moving only the area strands its children.
    expect(firstViolation(plan, [moved[0]])).toBe(ERROR_OUTSIDE_PARENT);
  });

  it('flags a self-intersecting polygon (V-02) and out-of-range geometry (V-01)', () => {
    const bow: Geometry = {
      kind: 'polygon',
      points: [
        [3, 3],
        [5, 5],
        [5, 3],
        [3, 5],
      ],
      rotation_deg: 0,
    };
    expect(firstViolation(testPlan(), [{ entity: 'location', key: 'b1', geometry: bow }])).toBe(
      'geometry.self_intersecting',
    );
    expect(
      firstViolation(testPlan(), [{ entity: 'location', key: 'b1', geometry: rect(3, 3, 0, 2) }]),
    ).toBe(ERROR_INVALID);
    expect(
      firstViolation(testPlan(), [
        { entity: 'location', key: 'solo', geometry: rect(-1, 2, 2, 2) },
      ]),
    ).toBe(ERROR_INVALID);
  });

  it('skips containment for off-site garden objects', () => {
    const plan = testPlan();
    const off = {
      ...plan,
      gardenObjects: {
        ...plan.gardenObjects,
        t1: { ...plan.gardenObjects.t1, off_site: true, parent_location_key: null },
      },
    };
    const far = {
      entity: 'garden_object' as const,
      key: 't1',
      geometry: { kind: 'circle' as const, origin: [50, 50] as [number, number], radius_m: 1 },
    };
    expect(firstViolation(off, [far])).toBeNull();
  });
});

describe('new shapes', () => {
  it('finds the smallest placed location that holds a shape as its parent', () => {
    const plan = testPlan();
    expect(inferParentKey(plan, rect(3.5, 3.5, 1, 1))).toBe('b1');
    expect(inferParentKey(plan, rect(9, 6, 1, 1))).toBe('area');
    expect(inferParentKey(plan, rect(16, 14, 1, 1))).toBeNull();
  });

  it('judges a new shape under the parent it would get', () => {
    const plan = testPlan();
    expect(violationOfNew(plan, rect(9, 6, 1, 1), 'area')).toBeNull();
    expect(violationOfNew(plan, rect(15, 15, 6, 1), null)).toBe(ERROR_OUTSIDE_PARENT);
  });
});
