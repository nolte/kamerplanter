import { describe, expect, it } from 'vitest';
import { applyOperations } from '../../model/applyOperation';
import { moveOperations, positionOf } from './keyboardMove';
import { testPlan } from './toolTestKit';

const ref = (key: string, entity: 'location' | 'garden_object' = 'location') => ({ entity, key });

describe('moveOperations', () => {
  it('shifts a bed and the result applies to the plan', () => {
    const plan = testPlan();
    const result = moveOperations(plan, [ref('solo')], [0.3, 0]);
    expect(result.ok).toBe(true);
    if (!result.ok) return;
    const moved = applyOperations(plan, result.ops).plan;
    expect(positionOf(moved, ref('solo'))).toEqual([14.3, 2]);
  });

  it('moves what lies inside an area with it, each once (GP-FR-151)', () => {
    const plan = testPlan();
    const result = moveOperations(plan, [ref('area'), ref('b1')], [1, 0]);
    expect(result.ok && result.ops.map((op) => ('key' in op ? op.key : '')).sort()).toEqual([
      'area',
      'b1',
      'b2',
      't1',
    ]);
  });

  it('refuses a locked object, a plant and a move out of the garden', () => {
    const plan = testPlan();
    expect(moveOperations(plan, [ref('lock')], [1, 0])).toEqual({
      ok: false,
      notice: 'object.locked',
    });
    expect(moveOperations(plan, [{ entity: 'plant', key: 'p1' }], [1, 0])).toEqual({
      ok: false,
      notice: 'object.not_movable',
    });
    const outside = moveOperations(plan, [ref('solo')], [100, 0]);
    expect(outside.ok).toBe(false);
  });
});

describe('positionOf', () => {
  it('is the lower-left corner of the bounding box', () => {
    const plan = testPlan();
    expect(positionOf(plan, ref('b1'))).toEqual([3, 3]);
    expect(positionOf(plan, ref('t1', 'garden_object'))).toEqual([8.5, 8.5]);
    expect(positionOf(plan, { entity: 'plant', key: 'p1' })).toBeNull();
  });
});
