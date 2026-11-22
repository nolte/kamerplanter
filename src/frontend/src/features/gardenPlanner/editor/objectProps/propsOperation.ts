/**
 * One edit of an object's props (REQ-053 GP-FR-180, WP 10.6): ONE `update_fields` with the whole props object,
 * through the pending plan model like every panel edit (the server replaces `props`, `garden_plan_service.py`), so
 * it is one undo step and part of the next save. Never a request of its own: that would raise the plan revision
 * outside the editor and turn the next save into a 409 (#2538).
 */
import type { GardenObjectProps, PlanOperation } from '../../model/types';

/** The edit of `current` to `next`, or `null` when nothing changes. */
export function propsOperation(
  objectKey: string,
  current: GardenObjectProps,
  next: GardenObjectProps,
): PlanOperation | null {
  if (JSON.stringify(next) === JSON.stringify(current)) return null;
  return {
    op: 'update_fields',
    entity: 'garden_object',
    key: objectKey,
    fields: { props: next as unknown as Record<string, unknown> },
  };
}
