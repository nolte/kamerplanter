import { describe, expect, it } from 'vitest';
import { applyOperations } from '../../model/applyOperation';
import { deleteImpact, moveTargets, selectionRoots } from './hierarchy';
import { testPlan } from './toolTestKit';

const area = { entity: 'location', key: 'area' } as const;
const b1 = { entity: 'location', key: 'b1' } as const;
const tree = { entity: 'garden_object', key: 't1' } as const;
const solo = { entity: 'location', key: 'solo' } as const;

describe('selectionRoots', () => {
  it('drops a selected child whose area is selected too', () => {
    const roots = selectionRoots(testPlan(), [area, b1, tree, solo]);
    expect(roots.map((ref) => ref.key)).toEqual(['area', 'solo']);
  });

  it('keeps a child on its own, and ignores plants and slots', () => {
    const roots = selectionRoots(testPlan(), [
      b1,
      { entity: 'plant', key: 'p1' },
      { entity: 'slot', key: 's1' },
    ]);
    expect(roots.map((ref) => ref.key)).toEqual(['b1']);
  });
});

describe('moveTargets (GP-FR-151)', () => {
  it('takes every child of a moved area, once each', () => {
    const targets = moveTargets(testPlan(), [area]);
    expect(targets.map((t) => `${t.entity}:${t.key}`).sort()).toEqual([
      'garden_object:t1',
      'location:area',
      'location:b1',
      'location:b2',
    ]);
  });

  it('does not move a child twice when it is selected with its area', () => {
    const targets = moveTargets(testPlan(), [area, b1, solo]);
    expect(targets.filter((t) => t.key === 'b1')).toHaveLength(1);
    expect(targets).toHaveLength(5);
  });

  it('moves a bed on its own without its siblings', () => {
    expect(moveTargets(testPlan(), [b1]).map((t) => t.key)).toEqual(['b1']);
  });

  it('reports locked entries so the caller can refuse the whole move', () => {
    const plan = testPlan();
    const targets = moveTargets(plan, [{ entity: 'location', key: 'lock' }]);
    expect(targets[0].locked).toBe(true);
  });
});

describe('deleteImpact (GP-FR-153)', () => {
  it('counts the children, slots, plants and tasks a bed takes along - from the model', () => {
    const impact = deleteImpact(testPlan(), [b1]);
    expect(impact).toMatchObject({ childBeds: 0, childObjects: 0, slots: 2, plants: 1, tasks: 3 });
    expect(impact.roots.map((r) => r.name)).toEqual(['Bed 1']);
    // A bed with a planted slot cannot be put back once saved (GP-FR-155).
    expect(impact.reversible).toBe(false);
  });

  it('counts everything below an area once, the area itself not as a child', () => {
    const impact = deleteImpact(testPlan(), [area]);
    expect(impact).toMatchObject({ childBeds: 2, childObjects: 1, slots: 2, plants: 1, tasks: 3 });
    expect(impact.ops).toEqual([{ op: 'delete', entity: 'location', key: 'area' }]);
  });

  it('matches what applyOperation really removes', () => {
    const plan = testPlan();
    const impact = deleteImpact(plan, [area]);
    const after = applyOperations(plan, impact.ops).plan;
    const removed = Object.keys(plan.locations).length - Object.keys(after.locations).length - 1; // minus the root
    expect(removed).toBe(impact.childBeds);
    expect(Object.keys(plan.gardenObjects).length - Object.keys(after.gardenObjects).length).toBe(
      impact.childObjects,
    );
    expect(Object.keys(plan.slots).length - Object.keys(after.slots).length).toBe(impact.slots);
    expect(Object.keys(plan.plants).length - Object.keys(after.plants).length).toBe(impact.plants);
  });

  it('is reversible for an empty bed and says so', () => {
    const impact = deleteImpact(testPlan(), [solo]);
    expect(impact).toMatchObject({ childBeds: 0, slots: 0, plants: 0, tasks: 0, reversible: true });
  });

  it('names locked entities and offers no reversibility', () => {
    const impact = deleteImpact(testPlan(), [{ entity: 'location', key: 'lock' }]);
    expect(impact.lockedKeys).toEqual(['lock']);
    expect(impact.reversible).toBe(false);
  });

  it('deletes a selected child on its own and the area root once', () => {
    const impact = deleteImpact(testPlan(), [area, b1]);
    expect(impact.ops).toHaveLength(1);
    expect(impact.roots).toHaveLength(1);
  });
});
