import { describe, expect, it } from 'vitest';
import type { Geometry } from '../../model/types';
import {
  firstViolation,
  inferParentKey,
  violationOfNew,
  ERROR_BED_OVERLAP,
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

describe('V-05 bed overlap, checked live (#2759 question 14)', () => {
  /** The test plan with the server's bed types: `bed` is one, the area type is not. */
  const withBedTypes = () => ({ ...testPlan(), bedTypeKeys: ['bed'] });

  it('flags a bed dragged onto a sibling bed of the same area', () => {
    // b1 (3,3) and b2 (6,3) share the area: b1 moved to (5.5,3) covers half of b2.
    expect(
      firstViolation(withBedTypes(), [
        { entity: 'location', key: 'b1', geometry: rect(5.5, 3, 2, 2) },
      ]),
    ).toBe(ERROR_BED_OVERLAP);
  });

  it('accepts beds that only touch along an edge (the server tolerance)', () => {
    expect(
      firstViolation(withBedTypes(), [
        { entity: 'location', key: 'b1', geometry: rect(4, 3, 2, 2) },
      ]),
    ).toBeNull();
  });

  it('reads the sibling where the same change set moves it', () => {
    // Both move right by 3 m together (a group drag): they keep their gap.
    expect(
      firstViolation(withBedTypes(), [
        { entity: 'location', key: 'b1', geometry: rect(6, 3, 2, 2) },
        { entity: 'location', key: 'b2', geometry: rect(9, 3, 2, 2) },
      ]),
    ).toBeNull();
  });

  it('lets a bed overlap a garden object (a path under a raised bed)', () => {
    // The tree t1 at (9,9) r 0.5 in the same area.
    expect(
      firstViolation(withBedTypes(), [
        { entity: 'location', key: 'b1', geometry: rect(8, 8, 2, 2) },
      ]),
    ).toBeNull();
  });

  it('compares only beds of the same parent', () => {
    // `solo` (14,2) is top level; b1 stays in the area - a shape inside the area cannot reach it anyway, so a new
    // top-level bed on top of solo is the case: it overlaps.
    expect(violationOfNew(withBedTypes(), rect(14.5, 2.5, 1, 1), null, 'bed')).toBe(
      ERROR_BED_OVERLAP,
    );
    // The same shape as a garden object is fine, and so is a new area (not a bed type).
    expect(violationOfNew(withBedTypes(), rect(14.5, 2.5, 1, 1), null)).toBeNull();
    expect(violationOfNew(withBedTypes(), rect(14.5, 2.5, 1, 1), null, 'area')).toBeNull();
  });

  it('is the server-only rule while the plan does not name the bed types', () => {
    expect(
      firstViolation(testPlan(), [{ entity: 'location', key: 'b1', geometry: rect(5.5, 3, 2, 2) }]),
    ).toBeNull();
  });
});
