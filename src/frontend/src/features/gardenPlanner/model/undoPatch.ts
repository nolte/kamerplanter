/**
 * Entity-level undo records (GP-FR-155).
 *
 * While an action is still unsaved its undo is exact: the previous value of every entity it touched
 * is restored and its operations leave `pending`. A patch holds only the touched entries (the
 * previous value, `null` = it did not exist), never a copy of the plan, so fifty undo steps of a
 * large plan stay small and the Redux dev-mode invariant checks stay cheap.
 */
import type { PlanModel } from './planModel';
import type { PlanSettings } from './types';

type EntityMap = 'locations' | 'gardenObjects' | 'slots' | 'plants';
const ENTITY_MAPS: readonly EntityMap[] = ['locations', 'gardenObjects', 'slots', 'plants'];

export type UndoPatch = {
  [K in EntityMap]?: Record<string, PlanModel[K][string] | null>;
} & {
  /** Present when the settings changed; the value is the previous settings (`null` = no plan). */
  settings?: { previous: PlanSettings | null };
};

/** What must be written back to `after` to get `before` again. */
export function diffPlans(before: PlanModel, after: PlanModel): UndoPatch {
  const patch: UndoPatch = {};
  for (const name of ENTITY_MAPS) {
    const was = before[name] as Record<string, unknown>;
    const now = after[name] as Record<string, unknown>;
    if (was === now) continue; // untouched maps are shared: the common case costs nothing
    const changed: Record<string, unknown> = {};
    for (const key of Object.keys(now)) {
      if (was[key] !== now[key]) changed[key] = was[key] ?? null;
    }
    for (const key of Object.keys(was)) {
      if (!(key in now)) changed[key] = was[key];
    }
    if (Object.keys(changed).length > 0) (patch as Record<string, unknown>)[name] = changed;
  }
  if (before.settings !== after.settings) patch.settings = { previous: before.settings };
  return patch;
}

/** Restore the entries of `patch` on `plan`. */
export function applyUndoPatch(plan: PlanModel, patch: UndoPatch): PlanModel {
  const next: PlanModel = { ...plan };
  for (const name of ENTITY_MAPS) {
    const changes = patch[name] as Record<string, unknown> | undefined;
    if (!changes) continue;
    const map: Record<string, unknown> = { ...plan[name] };
    for (const [key, previous] of Object.entries(changes)) {
      if (previous === null) delete map[key];
      else map[key] = previous;
    }
    (next as unknown as Record<string, unknown>)[name] = map;
  }
  if (patch.settings) next.settings = patch.settings.previous;
  return next;
}
