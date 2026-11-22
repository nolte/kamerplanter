/**
 * Selection rules of the editor (REQ-053 GP-FR-020/156, GP-UX-032/033/037): what a renderer key
 * means, which objects a marquee or "select all" may take, and how a repeated click walks down
 * the stack under the pointer. Pure: no renderer, no store.
 */
import { boundingBox } from '../../model/geometry';
import type { PlanModel } from '../../model/planModel';
import type { BoundingBox } from '../../model/types';
import type { SelectionRef, SelectionStack } from '../../state/gardenPlanSlice';

/** A click or tap counts as "the same spot" within this many pixels (GP-UX-033). */
export const SAME_SPOT_PX = 6;

/** What a renderer key refers to; `null` for the garden boundary and unknown keys. */
export function resolveRef(plan: PlanModel, key: string): SelectionRef | null {
  if (key in plan.locations) return { entity: 'location', key };
  if (key in plan.gardenObjects) return { entity: 'garden_object', key };
  if (key in plan.plants) return { entity: 'plant', key };
  if (key in plan.slots) return { entity: 'slot', key };
  return null;
}

export function sameRef(a: SelectionRef, b: SelectionRef): boolean {
  return a.entity === b.entity && a.key === b.key;
}

export function isSelected(selection: readonly SelectionRef[], ref: SelectionRef): boolean {
  return selection.some((item) => sameRef(item, ref));
}

export function isLockedRef(plan: PlanModel, ref: SelectionRef): boolean {
  if (ref.entity === 'location') return plan.locations[ref.key]?.locked === true;
  if (ref.entity === 'garden_object') return plan.gardenObjects[ref.key]?.locked === true;
  return false;
}

/** Shift+click: add `ref`, or take it out when it is already selected. */
export function toggleRef(selection: readonly SelectionRef[], ref: SelectionRef): SelectionRef[] {
  return isSelected(selection, ref)
    ? selection.filter((item) => !sameRef(item, ref))
    : [...selection, ref];
}

function bboxOf(plan: PlanModel, ref: SelectionRef): BoundingBox | null {
  if (ref.entity === 'location') {
    const location = plan.locations[ref.key];
    if (!location?.geometry) return null;
    return location.bbox ?? boundingBox(location.geometry);
  }
  const garden = plan.gardenObjects[ref.key];
  return garden ? (garden.bbox ?? boundingBox(garden.geometry)) : null;
}

/** Every placed, unlocked location and garden object: "select all" and the marquee draw from it (GP-FR-156). */
function selectable(plan: PlanModel): SelectionRef[] {
  const refs: SelectionRef[] = [];
  for (const location of Object.values(plan.locations)) {
    if (location.geometry && !location.locked) refs.push({ entity: 'location', key: location.key });
  }
  for (const garden of Object.values(plan.gardenObjects)) {
    if (!garden.locked) refs.push({ entity: 'garden_object', key: garden.key });
  }
  return refs;
}

export function selectAll(plan: PlanModel): SelectionRef[] {
  return selectable(plan);
}

/**
 * The marquee takes only objects lying completely inside `rect`; locked objects, the boundary and
 * plants/slots are out (GP-UX-037, GP-FR-156). `additive` keeps the current selection.
 */
export function marqueeSelection(
  plan: PlanModel,
  rect: BoundingBox,
  current: readonly SelectionRef[],
  additive: boolean,
): SelectionRef[] {
  const inside = selectable(plan).filter((ref) => {
    const box = bboxOf(plan, ref);
    return (
      box !== null &&
      box[0] >= rect[0] &&
      box[1] >= rect[1] &&
      box[2] <= rect[2] &&
      box[3] <= rect[3]
    );
  });
  if (!additive) return inside;
  const merged = [...current];
  for (const ref of inside) if (!isSelected(merged, ref)) merged.push(ref);
  return merged;
}

/** The stack under a point as selection refs, topmost first; the boundary is not selectable. */
export function stackRefs(plan: PlanModel, keys: readonly string[]): SelectionRef[] {
  const refs: SelectionRef[] = [];
  for (const key of keys) {
    const ref = resolveRef(plan, key);
    if (ref) refs.push(ref);
  }
  return refs;
}

/**
 * The next stack position for a click at `pointPx` over `keys` (GP-UX-033). A repeated click on
 * the same spot with the same stack goes one down and wraps. Alt+click goes one down from the
 * object that is selected now. Anything else starts at the top. A single object has no stack.
 */
export function nextStackIndex(
  stack: SelectionStack | null,
  keys: readonly string[],
  pointPx: readonly [number, number],
  forceNext: boolean,
  selectedKey: string | null,
): number {
  if (keys.length < 2) return 0;
  if (stack !== null) {
    const near =
      Math.hypot(stack.pointPx[0] - pointPx[0], stack.pointPx[1] - pointPx[1]) <= SAME_SPOT_PX;
    const same =
      stack.keys.length === keys.length && stack.keys.every((key, index) => key === keys[index]);
    if (same && (near || forceNext)) return (stack.index + 1) % keys.length;
  }
  if (forceNext && selectedKey !== null) {
    const at = keys.indexOf(selectedKey);
    if (at >= 0) return (at + 1) % keys.length;
  }
  return 0;
}
