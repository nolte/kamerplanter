import { describe, expect, it } from 'vitest';
import { applyOperations } from '../../model/applyOperation';
import { normalizePlan } from '../../model/planModel';
import { bed, planResponse } from '@/test/gardenPlanFixtures';
import type { Geometry } from '../../model/types';
import type { SelectionRef } from '../../state/gardenPlanSlice';
import { alignAvailability, alignSelection, distributeSelection } from './align';
import { testPlan } from './toolTestKit';

const rect = (x: number, y: number, w: number, l: number): Geometry => ({
  kind: 'rect',
  origin: [x, y],
  width_m: w,
  length_m: l,
  rotation_deg: 0,
});

function row() {
  const make = (key: string, x: number, y: number, w: number, l: number, extra = {}) =>
    bed(key, x, y, {
      geometry: rect(x, y, w, l),
      area_m2: w * l,
      bbox: [x, y, x + w, y + l],
      ...extra,
    });
  return normalizePlan(
    planResponse({
      plan: {
        boundary: { kind: 'rect', origin: [0, 0], width_m: 30, length_m: 30, rotation_deg: 0 },
        north_angle_deg: 0,
        default_grid_m: 0.1,
        adjacency_factor: 1.5,
        plan_revision: 1,
      },
      locations: [
        make('a', 1, 1, 2, 2),
        make('b', 5, 4, 3, 1),
        make('c', 12, 8, 2, 2),
        make('d', 20, 2, 1, 1, { locked: true }),
      ],
    }),
  );
}
const sel = (...keys: string[]): SelectionRef[] =>
  keys.map((key) => ({ entity: 'location', key }));
const originOf = (ops: { key: string; geometry: Geometry }[], key: string) => {
  const g = ops.find((op) => op.key === key)?.geometry;
  return g?.kind === 'rect' ? g.origin : undefined;
};

describe('alignSelection (GP-FR-029)', () => {
  it('aligns the left edges to the leftmost object in one batch', () => {
    const out = alignSelection(row(), sel('a', 'b', 'c'), 'left');
    if (!out.ok) throw new Error(out.code);
    const ops = out.ops as { key: string; geometry: Geometry }[];
    expect(out.ops.every((op) => op.op === 'update_geometry')).toBe(true);
    expect(originOf(ops, 'b')).toEqual([1, 4]);
    expect(originOf(ops, 'c')).toEqual([1, 8]);
    expect(ops.find((op) => op.key === 'a')).toBeUndefined(); // already there: no operation
  });

  it('aligns the right edges', () => {
    const out = alignSelection(row(), sel('a', 'b', 'c'), 'right');
    if (!out.ok) throw new Error(out.code);
    const ops = out.ops as { key: string; geometry: Geometry }[];
    expect(originOf(ops, 'a')).toEqual([12, 1]);
    expect(originOf(ops, 'b')).toEqual([11, 4]);
  });

  it('aligns the top (largest y) and bottom edges', () => {
    const top = alignSelection(row(), sel('a', 'b', 'c'), 'top');
    const bottom = alignSelection(row(), sel('a', 'b', 'c'), 'bottom');
    if (!top.ok || !bottom.ok) throw new Error('expected moves');
    expect(originOf(top.ops as never, 'a')).toEqual([1, 8]);
    expect(originOf(bottom.ops as never, 'c')).toEqual([12, 1]);
  });

  it('centres on the middle of the selection, horizontally and vertically', () => {
    const h = alignSelection(row(), sel('a', 'b', 'c'), 'centerH');
    const v = alignSelection(row(), sel('a', 'b', 'c'), 'centerV');
    if (!h.ok || !v.ok) throw new Error('expected moves');
    // span x 1..14, middle 7.5: b (5..8, middle 6.5) moves +1
    expect(originOf(h.ops as never, 'b')).toEqual([6, 4]);
    // span y 1..10, middle 5.5: a (1..3, middle 2) moves +3.5
    expect(originOf(v.ops as never, 'a')).toEqual([1, 4.5]);
  });

  it('leaves a locked object out, as a mover and as a reference', () => {
    const out = alignSelection(row(), sel('a', 'b', 'd'), 'right');
    if (!out.ok) throw new Error(out.code);
    // d (x 20..21) would have been the reference; without it the right edge is b's at 8
    expect(originOf(out.ops as never, 'a')).toEqual([6, 1]);
    expect((out.ops as { key: string }[]).some((op) => op.key === 'd')).toBe(false);
  });

  it('refuses with nothing to do when fewer than two can move', () => {
    expect(alignSelection(row(), sel('a'), 'left')).toEqual({ ok: false, code: 'nothing' });
    expect(alignSelection(row(), sel('a', 'd'), 'left')).toEqual({ ok: false, code: 'object.locked' });
  });

  it('refuses a result that leaves the garden', () => {
    const plan = row();
    plan.settings = {
      ...plan.settings!,
      boundary: { kind: 'rect', origin: [0, 0], width_m: 13, length_m: 30, rotation_deg: 0 },
    };
    // c (x 12..14) already sticks out of a 13 m wide garden, so moving a to its right edge cannot fit either
    const refused = alignSelection(plan, sel('a', 'c'), 'right');
    expect(refused).toEqual({ ok: false, code: 'geometry.outside_parent' });
  });

  it('applies to the model as one batch', () => {
    const plan = row();
    const out = alignSelection(plan, sel('a', 'b', 'c'), 'left');
    if (!out.ok) throw new Error(out.code);
    const applied = applyOperations(plan, out.ops).plan;
    expect(applied.locations.b.geometry).toMatchObject({ origin: [1, 4] });
  });

  it('moves the content of a selected area with it, once', () => {
    const plan = testPlan();
    const out = alignSelection(plan, sel('area', 'b1', 'solo'), 'left');
    if (!out.ok) throw new Error(out.code);
    const keys = (out.ops as { key: string }[]).map((op) => op.key).sort();
    expect(new Set(keys).size).toBe(keys.length);
    expect(keys).not.toContain('area'); // area (x 2) is already the leftmost
  });
});

describe('distributeSelection (GP-FR-029)', () => {
  it('makes the horizontal gaps equal and keeps the outer objects', () => {
    const out = distributeSelection(row(), sel('a', 'b', 'c'), 'horizontal');
    if (!out.ok) throw new Error(out.code);
    const ops = out.ops as { key: string; geometry: Geometry }[];
    // widths 2+3+2 = 7 in 1..14 -> gap 3: a 1..3, b 6..9, c 12..14
    expect(originOf(ops, 'b')).toEqual([6, 4]);
    expect(ops.find((op) => op.key === 'a')).toBeUndefined();
    expect(ops.find((op) => op.key === 'c')).toBeUndefined();
  });

  it('distributes vertically', () => {
    const out = distributeSelection(row(), sel('a', 'b', 'c'), 'vertical');
    if (!out.ok) throw new Error(out.code);
    // heights 2+1+2 = 5 in 1..10 -> gap 2: a 1..3, b 5..6, c 8..10
    expect(originOf(out.ops as never, 'b')).toEqual([5, 5]);
  });

  it('needs three movable objects', () => {
    expect(distributeSelection(row(), sel('a', 'b'), 'horizontal')).toEqual({
      ok: false,
      code: 'nothing',
    });
    expect(distributeSelection(row(), sel('a', 'b', 'd'), 'horizontal')).toEqual({
      ok: false,
      code: 'object.locked',
    });
  });

  it('reports what the selection allows', () => {
    expect(alignAvailability(row(), sel('a', 'b', 'c'))).toEqual({ align: true, distribute: true });
    expect(alignAvailability(row(), sel('a', 'b', 'd'))).toEqual({ align: true, distribute: false });
    expect(alignAvailability(row(), [])).toEqual({ align: false, distribute: false });
  });
});
