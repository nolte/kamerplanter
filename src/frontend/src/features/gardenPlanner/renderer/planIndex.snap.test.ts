import { describe, expect, it } from 'vitest';
import { testPlan } from '../editor/tools/toolTestKit';
import { resolveSnap } from '../editor/tools/snap';
import { snapCandidates } from './planIndex';

describe('snapCandidates (GP-FR-154)', () => {
  const plan = testPlan();

  it('lists the corners and closed edges of every placed bed and the boundary', () => {
    const { corners, edges } = snapCandidates(plan, new Set(['area', 'b1', 'b2', 'lock', 't1']));
    // solo (14,2) 2x2 and the 20x20 boundary: 4 corners + 4 edges each
    expect(corners).toHaveLength(8);
    expect(edges).toHaveLength(8);
    expect(corners).toContainEqual([14, 2]);
    expect(corners).toContainEqual([16, 4]);
    expect(corners).toContainEqual([0, 0]);
  });

  it('leaves out the excluded objects, so a moved bed does not snap to itself', () => {
    const all = snapCandidates(plan);
    const without = snapCandidates(plan, new Set(['solo']));
    expect(all.corners.length - without.corners.length).toBe(4);
    expect(without.corners).not.toContainEqual([14, 2]);
  });

  it('gives a circle its four quadrant points and no edges', () => {
    const { corners } = snapCandidates(plan);
    expect(corners).toContainEqual([9.5, 9]);
    expect(corners).toContainEqual([9, 8.5]);
  });

  it('feeds resolveSnap: a corner within tolerance wins over the grid', () => {
    const candidates = snapCandidates(plan);
    const result = resolveSnap([14.05, 2.04], {
      gridM: 0.5,
      gridEnabled: true,
      bypass: false,
      pxPerM: 100,
      candidates,
    });
    expect(result).toEqual({ point: [14, 2], kind: 'corner' });
  });

  it('is cached per shape entry: an unchanged plan answers equal lists', () => {
    expect(snapCandidates(plan)).toEqual(snapCandidates(plan));
  });
});
