import { describe, expect, it } from 'vitest';
import { applyOperations } from '../../model/applyOperation';
import { bed, planResponse } from '@/test/gardenPlanFixtures';
import { normalizePlan } from '../../model/planModel';
import type { Geometry } from '../../model/types';
import { testPlan } from './toolTestKit';
import {
  duplicateSelection,
  multiCopyName,
  multiDuplicate,
  type MultiDuplicateOptions,
} from './duplicate';

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

describe('multiDuplicate (GP-FR-025 SHOULD, GP-NFR-017)', () => {
  const rect: Geometry = { kind: 'rect', origin: [1, 1], width_m: 2, length_m: 1, rotation_deg: 0 };
  const community = (extra: number = 0) =>
    normalizePlan(
      planResponse({
        plan: {
          boundary: { kind: 'rect', origin: [0, 0], width_m: 200, length_m: 50, rotation_deg: 0 },
          north_angle_deg: 0,
          default_grid_m: 0.1,
          adjacency_factor: 1.5,
          plan_revision: 1,
        },
        locations: [
          bed('plot', 1, 1, { geometry: rect, area_m2: 2, bbox: [1, 1, 3, 2], name: 'Plot' }),
          ...Array.from({ length: extra }, (_, i) =>
            bed(`x${i}`, 100, 10, {
              geometry: { ...rect, origin: [100, 10] },
              area_m2: 2,
              bbox: [100, 10, 102, 11],
            }),
          ),
        ],
      }),
    );
  const options: MultiDuplicateOptions = {
    count: 30,
    direction: 'right',
    spacingM: 0.5,
    scheme: 'Parzelle {n}',
    startNumber: 1,
  };

  it('makes 30 parcels in a row with the naming scheme in one batch', () => {
    const plan = community();
    const out = multiDuplicate(plan, [{ entity: 'location', key: 'plot' }], options);
    if (!out.ok) throw new Error(out.code);
    expect(out.value.ops).toHaveLength(30);
    expect(out.value.selection).toHaveLength(30);
    const names = out.value.ops.map((op) => (op.op === 'create_location' ? op.data.name : ''));
    expect(names[0]).toBe('Parzelle 1');
    expect(names[29]).toBe('Parzelle 30');
    expect(new Set(names).size).toBe(30);
    // pitch = width 2 + spacing 0.5: the k-th copy starts at 1 + 2.5 k
    const origins = out.value.ops.map((op) =>
      op.op === 'create_location' && op.data.geometry?.kind === 'rect'
        ? op.data.geometry.origin
        : null,
    );
    expect(origins[0]).toEqual([3.5, 1]);
    expect(origins[29]).toEqual([76, 1]);
    const applied = applyOperations(plan, out.value.ops).plan;
    expect(Object.keys(applied.locations)).toHaveLength(31);
  });

  it('goes left, up and down by the height of the selection', () => {
    const plan = community();
    const sel = [{ entity: 'location' as const, key: 'plot' }];
    const up = multiDuplicate(plan, sel, { ...options, count: 2, direction: 'up', spacingM: 1 });
    if (!up.ok) throw new Error(up.code);
    expect(
      up.value.ops.map((op) =>
        op.op === 'create_location' && op.data.geometry?.kind === 'rect'
          ? op.data.geometry.origin
          : null,
      ),
    ).toEqual([
      [1, 3],
      [1, 5],
    ]);
    const left = multiDuplicate(plan, sel, {
      ...options,
      count: 1,
      direction: 'left',
      spacingM: 0,
    });
    // the plot starts at x = 1: a copy 2 m to the left would have negative coordinates (V-01)
    expect(left).toMatchObject({ ok: false, code: 'geometry.invalid', failedCopy: 1 });
  });

  it('starts at the given number and appends one when the scheme has no {n}', () => {
    expect(multiCopyName('Parzelle {n}', 12)).toBe('Parzelle 12');
    expect(multiCopyName('Plot', 3)).toBe('Plot 3');
    expect(multiCopyName('{n}. Beet', 3)).toBe('3. Beet');
  });

  it('keeps the name of the original when the scheme is empty', () => {
    const out = multiDuplicate(community(), [{ entity: 'location', key: 'plot' }], {
      ...options,
      count: 2,
      scheme: '  ',
    });
    if (!out.ok) throw new Error(out.code);
    expect(out.value.ops.map((op) => (op.op === 'create_location' ? op.data.name : ''))).toEqual([
      'Plot',
      'Plot',
    ]);
  });

  it('checks the quota of the site (500) up front and builds nothing', () => {
    const plan = community(480); // 481 beds: 30 more would be 511
    expect(multiDuplicate(plan, [{ entity: 'location', key: 'plot' }], options)).toEqual({
      ok: false,
      code: 'plan.quota_exceeded',
    });
    const room = 500 - Object.keys(plan.locations).length - Object.keys(plan.gardenObjects).length;
    const sel = [{ entity: 'location' as const, key: 'plot' }];
    expect(multiDuplicate(plan, sel, { ...options, count: room }).ok).toBe(true);
    expect(multiDuplicate(plan, sel, { ...options, count: room + 1 })).toEqual({
      ok: false,
      code: 'plan.quota_exceeded',
    });
  });

  it('refuses the whole run when one copy would leave the garden, nothing half done', () => {
    const out = multiDuplicate(community(), [{ entity: 'location', key: 'plot' }], {
      ...options,
      count: 100,
    });
    expect(out).toMatchObject({ ok: false, code: 'geometry.outside_parent' });
    if (!out.ok) expect(out.failedCopy).toBeGreaterThan(1);
  });

  it('counts the operations already waiting for the save against the batch limit', () => {
    const sel = [{ entity: 'location' as const, key: 'plot' }];
    expect(multiDuplicate(community(), sel, { ...options, count: 30, pendingCount: 471 })).toEqual({
      ok: false,
      code: 'multi.too_many',
    });
    expect(multiDuplicate(community(), sel, { ...options, count: 30, pendingCount: 470 }).ok).toBe(true);
  });

  it('rejects numbers that make no sense', () => {
    const sel = [{ entity: 'location' as const, key: 'plot' }];
    const bad = (patch: object) => multiDuplicate(community(), sel, { ...options, ...patch });
    expect(bad({ count: 0 })).toEqual({ ok: false, code: 'multi.invalid' });
    expect(bad({ count: 101 })).toEqual({ ok: false, code: 'multi.invalid' });
    expect(bad({ count: 2.5 })).toEqual({ ok: false, code: 'multi.invalid' });
    expect(bad({ spacingM: -1 })).toEqual({ ok: false, code: 'multi.invalid' });
    expect(multiDuplicate(community(), [], options)).toEqual({ ok: false, code: 'nothing' });
  });

  it('does not copy slots, plants or tasks of the bed', () => {
    const plan = testPlan();
    const out = multiDuplicate(plan, [{ entity: 'location', key: 'b1' }], {
      count: 2,
      direction: 'up',
      spacingM: 0.2,
      scheme: 'N {n}',
      startNumber: 1,
    });
    if (!out.ok) throw new Error(out.code);
    const applied = applyOperations(plan, out.value.ops).plan;
    expect(Object.keys(applied.slots)).toHaveLength(Object.keys(plan.slots).length);
    expect(Object.keys(applied.plants)).toHaveLength(Object.keys(plan.plants).length);
  });
});
