import { describe, expect, it } from 'vitest';
import { testPlan } from './toolTestKit';
import { zOrderOps } from './zOrder';

describe('zOrderOps', () => {
  it('brings a bed one above the highest value on the plan', () => {
    const ops = zOrderOps(testPlan(), [{ entity: 'location', key: 'solo' }], 'front');
    expect(ops).toEqual([{ op: 'set_z_order', entity: 'location', key: 'solo', z_order: 2 }]);
  });
  it('sends a bed below the lowest value', () => {
    const ops = zOrderOps(testPlan(), [{ entity: 'location', key: 'b1' }], 'back');
    expect(ops).toEqual([{ op: 'set_z_order', entity: 'location', key: 'b1', z_order: -1 }]);
  });
  it('keeps the order inside a multi-selection', () => {
    const ops = zOrderOps(
      testPlan(),
      [
        { entity: 'location', key: 'b2' },
        { entity: 'location', key: 'solo' },
      ],
      'front',
    );
    expect(ops.map((op) => (op as { key: string }).key)).toEqual(['solo', 'b2']);
    expect(ops.map((op) => (op as { z_order: number }).z_order)).toEqual([2, 3]);
  });
  it('does nothing for a plant or when the bed is on top already', () => {
    expect(zOrderOps(testPlan(), [{ entity: 'plant', key: 'p1' }], 'front')).toEqual([]);
    // b1 and b2 share the top value 1, so neither is strictly in front.
    expect(zOrderOps(testPlan(), [{ entity: 'location', key: 'b1' }], 'front')).toHaveLength(1);
  });
});
