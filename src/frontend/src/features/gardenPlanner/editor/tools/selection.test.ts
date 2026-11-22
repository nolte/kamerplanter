import { describe, expect, it } from 'vitest';
import {
  marqueeSelection,
  nextStackIndex,
  resolveRef,
  selectAll,
  stackRefs,
  toggleRef,
} from './selection';
import { testPlan } from './toolTestKit';
import { BOUNDARY_KEY } from '../../renderer';

describe('resolveRef', () => {
  it('knows locations, objects, plants and slots, but not the boundary', () => {
    const plan = testPlan();
    expect(resolveRef(plan, 'b1')).toEqual({ entity: 'location', key: 'b1' });
    expect(resolveRef(plan, 't1')).toEqual({ entity: 'garden_object', key: 't1' });
    expect(resolveRef(plan, 'p1')).toEqual({ entity: 'plant', key: 'p1' });
    expect(resolveRef(plan, 's1')).toEqual({ entity: 'slot', key: 's1' });
    expect(resolveRef(plan, BOUNDARY_KEY)).toBeNull();
    expect(stackRefs(plan, [BOUNDARY_KEY, 'b1', 'nope']).map((r) => r.key)).toEqual(['b1']);
  });
});

describe('select all and marquee exclude locked objects (GP-FR-156)', () => {
  it('Ctrl+A takes every placed unlocked bed and object', () => {
    const keys = selectAll(testPlan())
      .map((r) => r.key)
      .sort();
    expect(keys).toEqual(['area', 'b1', 'b2', 't1', 'solo'].sort());
    expect(keys).not.toContain('lock');
  });

  it('the marquee takes only what lies completely inside it (GP-UX-037)', () => {
    const plan = testPlan();
    // Frames b1 (3..5) completely and b2 (6..8) only half.
    const picked = marqueeSelection(plan, [2.5, 2.5, 7, 5.5], [], false).map((r) => r.key);
    expect(picked).toEqual(['b1']);
    // The whole area (and everything in it) lies inside a larger frame; the locked bed does not count.
    const big = marqueeSelection(plan, [0, 0, 20, 20], [], false)
      .map((r) => r.key)
      .sort();
    expect(big).toEqual(['area', 'b1', 'b2', 'solo', 't1']);
  });

  it('an additive marquee keeps the current selection', () => {
    const plan = testPlan();
    const keep = [{ entity: 'location' as const, key: 'solo' }];
    const keys = marqueeSelection(plan, [2.5, 2.5, 5.5, 5.5], keep, true).map((r) => r.key);
    expect(keys).toEqual(['solo', 'b1']);
  });
});

describe('toggleRef', () => {
  it('adds and removes', () => {
    const a = { entity: 'location' as const, key: 'a' };
    const b = { entity: 'location' as const, key: 'b' };
    expect(toggleRef([a], b)).toEqual([a, b]);
    expect(toggleRef([a, b], a)).toEqual([b]);
  });
});

describe('nextStackIndex (GP-UX-033)', () => {
  const keys = ['a', 'b', 'c'];
  const stack = { keys, index: 0, pointPx: [100, 100] as [number, number] };

  it('starts at the top for a fresh stack and for a single object', () => {
    expect(nextStackIndex(null, keys, [100, 100], false, null)).toBe(0);
    expect(nextStackIndex(null, ['a'], [100, 100], true, 'a')).toBe(0);
  });

  it('walks down on a repeated click on the same spot and wraps', () => {
    expect(nextStackIndex(stack, keys, [102, 99], false, 'a')).toBe(1);
    expect(nextStackIndex({ ...stack, index: 2 }, keys, [100, 100], false, 'c')).toBe(0);
  });

  it('starts over when the click moved away or the stack changed', () => {
    expect(nextStackIndex(stack, keys, [160, 100], false, 'a')).toBe(0);
    expect(nextStackIndex(stack, ['a', 'x', 'c'], [100, 100], false, 'a')).toBe(0);
  });

  it('Alt+click goes below the selected object even without a stack', () => {
    expect(nextStackIndex(null, keys, [10, 10], true, 'b')).toBe(2);
    expect(nextStackIndex(null, keys, [10, 10], true, null)).toBe(0);
  });
});
