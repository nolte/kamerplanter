import { describe, expect, it } from 'vitest';
import { applyOperations } from '../../model/applyOperation';
import { testPlan } from './toolTestKit';
import { duplicateSelection } from './duplicate';

const name = (n: string) => `${n} (copy)`;

describe('duplicateSelection', () => {
  it('copies a bed with its base fields, shifted by the step, and names the copy', () => {
    const plan = testPlan();
    const out = duplicateSelection(plan, [{ entity: 'location', key: 'solo' }], 0.5, name);
    expect(out.ok).toBe(true);
    if (!out.ok) return;
    const [op] = out.value.ops;
    expect(op).toMatchObject({
      op: 'create_location',
      data: { name: 'Solo (copy)', location_type_key: 'bed', geometry: { origin: [14.5, 1.5] } },
    });
    expect(out.value.selection).toEqual([
      { entity: 'location', key: (op as { temp_key: string }).temp_key },
    ]);
  });

  it('never copies slots, plants or tasks of a bed', () => {
    const plan = testPlan();
    const out = duplicateSelection(plan, [{ entity: 'location', key: 'b1' }], 0.1, name);
    if (!out.ok) throw new Error('expected a copy');
    const applied = applyOperations(plan, out.value.ops).plan;
    expect(Object.keys(applied.slots)).toHaveLength(Object.keys(plan.slots).length);
    expect(Object.keys(applied.plants)).toHaveLength(Object.keys(plan.plants).length);
    const copy = applied.locations[out.value.selection[0].key];
    expect(copy.open_task_count).toBe(0);
  });

  it('takes everything inside a selected area along, under the copied area', () => {
    const plan = testPlan();
    const out = duplicateSelection(plan, [{ entity: 'location', key: 'area' }], 0.1, name);
    if (!out.ok) throw new Error('expected a copy');
    // area + b1 + b2 + the tree
    expect(out.value.ops).toHaveLength(4);
    const applied = applyOperations(plan, out.value.ops).plan;
    const rootKey = out.value.selection[0].key;
    const children = Object.values(applied.locations).filter(
      (l) => l.parent_location_key === rootKey,
    );
    expect(children.map((c) => c.name).sort()).toEqual(['Bed 1', 'Bed 2']);
  });

  it('tries the other directions when the first would leave the parent', () => {
    const plan = testPlan();
    // b2 sits at (6,3)..(8,5) in the area (2,2)..(12,12): a step of 3.9 m right-down leaves it at the bottom.
    const out = duplicateSelection(plan, [{ entity: 'location', key: 'b2' }], 3.9, name);
    expect(out.ok).toBe(true);
    if (out.ok) {
      const geometry = (out.value.ops[0] as { data: { geometry: { origin: number[] } } }).data
        .geometry;
      expect(geometry.origin).not.toEqual([9.9, -0.9]);
    }
  });

  it('refuses when no direction fits', () => {
    const plan = testPlan();
    const out = duplicateSelection(plan, [{ entity: 'location', key: 'b2' }], 9, name);
    expect(out).toEqual({ ok: false, code: 'geometry.outside_parent' });
  });

  it('has nothing to copy for a plant or an empty selection', () => {
    const plan = testPlan();
    expect(duplicateSelection(plan, [], 0.1, name)).toEqual({ ok: false, code: 'nothing' });
    expect(duplicateSelection(plan, [{ entity: 'plant', key: 'p1' }], 0.1, name)).toEqual({
      ok: false,
      code: 'nothing',
    });
  });

  it('does not mark a copy of a locked bed as locked', () => {
    const plan = testPlan();
    const out = duplicateSelection(plan, [{ entity: 'location', key: 'lock' }], 0.2, name);
    if (!out.ok) throw new Error('expected a copy');
    const applied = applyOperations(plan, out.value.ops).plan;
    expect(applied.locations[out.value.selection[0].key].locked).toBe(false);
  });
});
