/**
 * Bring to front / send to back (REQ-053 GP-FR-027): one `set_z_order` per entity, to one above
 * the highest or one below the lowest value on the plan. The server accepts -10 000..10 000.
 */
import type { PlanModel } from '../../model/planModel';
import type { PlanOperation } from '../../model/types';
import type { SelectionRef } from '../../state/gardenPlanSlice';
import { isPlanEntity } from './hierarchy';

export const Z_ORDER_MIN = -10_000;
export const Z_ORDER_MAX = 10_000;

export type ZMove = 'front' | 'back';

function zOf(
  plan: PlanModel,
  ref: SelectionRef & { entity: 'location' | 'garden_object' },
): number {
  return (
    (ref.entity === 'location' ? plan.locations[ref.key] : plan.gardenObjects[ref.key])?.z_order ??
    0
  );
}

/** The z values of every placed location and garden object. */
function allZ(plan: PlanModel): number[] {
  return [
    ...Object.values(plan.locations)
      .filter((l) => l.geometry)
      .map((l) => l.z_order),
    ...Object.values(plan.gardenObjects).map((g) => g.z_order),
  ];
}

/**
 * The operations that move `selection` to the front or back, keeping the order inside the
 * selection. Empty when everything is there already (no useless undo step).
 */
export function zOrderOps(
  plan: PlanModel,
  selection: readonly SelectionRef[],
  move: ZMove,
): PlanOperation[] {
  const refs = selection.filter(isPlanEntity);
  if (refs.length === 0) return [];
  const others = allZ(plan);
  const ordered = [...refs].sort((a, b) => zOf(plan, a) - zOf(plan, b));
  const ops: PlanOperation[] = [];
  if (move === 'front') {
    let next = Math.min(Z_ORDER_MAX, Math.max(...others) + 1);
    const top = Math.max(...others);
    const alreadyTop =
      ordered.every((ref) => zOf(plan, ref) === top) &&
      others.filter((z) => z === top).length === ordered.length;
    if (alreadyTop) return [];
    for (const ref of ordered) {
      ops.push({
        op: 'set_z_order',
        entity: ref.entity,
        key: ref.key,
        z_order: Math.min(Z_ORDER_MAX, next),
      });
      next += 1;
    }
  } else {
    let next = Math.max(Z_ORDER_MIN, Math.min(...others) - ordered.length);
    const bottom = Math.min(...others);
    const alreadyBottom =
      ordered.every((ref) => zOf(plan, ref) === bottom) &&
      others.filter((z) => z === bottom).length === ordered.length;
    if (alreadyBottom) return [];
    for (const ref of ordered) {
      ops.push({
        op: 'set_z_order',
        entity: ref.entity,
        key: ref.key,
        z_order: Math.max(Z_ORDER_MIN, next),
      });
      next += 1;
    }
  }
  return ops;
}
