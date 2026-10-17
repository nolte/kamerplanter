/**
 * Moving the selection without a pointer (REQ-053 GP-NFR-023, GP-ACC-008): the arrow keys and the
 * list view's buttons and number fields all end in the same operations a drag produces - the
 * selection roots and everything below an area, each shifted once, checked by the same live
 * validation. Pure: no store, no renderer.
 */
import { boundingBox, roundLength } from '../../model/geometry';
import type { PlanModel } from '../../model/planModel';
import type { PlanOperation, Point } from '../../model/types';
import type { SelectionRef } from '../../state/gardenPlanSlice';
import { translateGeometry } from './geometryEdit';
import { moveTargets } from './hierarchy';
import { firstViolation } from './validation';

export type MoveResult = { ok: true; ops: PlanOperation[] } | { ok: false; notice: string };

export const NOT_MOVABLE = 'object.not_movable';
export const LOCKED = 'object.locked';

/** The operations that shift `selection` by `delta` metres, or the notice code that says why not. */
export function moveOperations(
  plan: PlanModel,
  selection: readonly SelectionRef[],
  delta: Point,
): MoveResult {
  const targets = moveTargets(plan, selection);
  if (targets.length === 0) return { ok: false, notice: NOT_MOVABLE };
  if (targets.some((entry) => entry.locked)) return { ok: false, notice: LOCKED };
  const draft = targets.map((entry) => ({
    entity: entry.entity,
    key: entry.key,
    geometry: translateGeometry(entry.geometry, delta),
  }));
  const violation = firstViolation(plan, draft);
  if (violation) return { ok: false, notice: violation };
  return {
    ok: true,
    ops: draft.map(({ entity, key, geometry }) => ({
      op: 'update_geometry',
      entity,
      key,
      geometry,
    })),
  };
}

/**
 * Where an entity "is" for a reader: the lower-left corner of its bounding box, in metres. The
 * list view shows it, the move-to fields edit it and the live region announces it.
 */
export function positionOf(plan: PlanModel, ref: SelectionRef): Point | null {
  const source =
    ref.entity === 'location'
      ? plan.locations[ref.key]
      : ref.entity === 'garden_object'
        ? plan.gardenObjects[ref.key]
        : undefined;
  const geometry = source && 'geometry' in source ? source.geometry : null;
  if (!geometry) return null;
  const box = source?.bbox ?? boundingBox(geometry);
  return [roundLength(box[0]), roundLength(box[1])];
}
