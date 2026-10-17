/**
 * Live validation while drawing and dragging (REQ-053 GP-UX-053). It mirrors the server's
 * `check_entity` for the rules a client can decide without the database: V-01 (bounds), V-02
 * (simple polygon) and V-03 (containment in the nearest placed ancestor, else the garden
 * boundary). Bed overlap (V-05) needs the location type's `is_bed` flag the plan does not carry,
 * so it stays the server's. The server is the authority; this only draws the red outline early.
 */
import { contains, parseGeometry, toShape, validateGeometry } from '../../model/geometry';
import type { PlanModel } from '../../model/planModel';
import type { Geometry, PlanEntity } from '../../model/types';

export const ERROR_INVALID = 'geometry.invalid';
export const ERROR_OUTSIDE_PARENT = 'geometry.outside_parent';

export interface DraftChange {
  entity: PlanEntity;
  key: string;
  geometry: Geometry;
}

/** The geometry of the nearest ancestor location that is placed, else the boundary, else none. */
function enclosingGeometry(
  plan: PlanModel,
  parentKey: string | null | undefined,
  overrides: ReadonlyMap<string, Geometry>,
): Geometry | null {
  const seen = new Set<string>();
  let current = parentKey ?? null;
  while (current !== null && !seen.has(current)) {
    seen.add(current);
    const geometry = overrides.get(`location:${current}`) ?? plan.locations[current]?.geometry;
    if (geometry) return geometry;
    current = plan.locations[current]?.parent_location_key ?? null;
  }
  return plan.settings?.boundary ?? null;
}

/**
 * The first rule the change set breaks, as a server error code, or `null`. Besides each changed
 * entity, the children of a changed location are checked against its new shape (the server checks
 * them too: a moved or resized area drags its descendants, GP-FR-151).
 */
export function firstViolation(
  plan: PlanModel,
  changes: readonly DraftChange[],
  newEntity?: { parentKey: string | null },
): string | null {
  const overrides = new Map(changes.map((c) => [`${c.entity}:${c.key}`, c.geometry]));
  const checked = new Set<string>();

  const check = (
    id: string,
    geometry: Geometry,
    parentKey: string | null | undefined,
    offSite: boolean,
  ): string | null => {
    if (checked.has(id)) return null;
    checked.add(id);
    if (parseGeometry(geometry, 'plan') === null) return ERROR_INVALID;
    const simple = validateGeometry(geometry);
    if (simple.length > 0) return simple[0];
    const enclosing = enclosingGeometry(plan, parentKey, overrides);
    if (enclosing && !offSite && !contains(toShape(enclosing), toShape(geometry))) {
      return ERROR_OUTSIDE_PARENT;
    }
    return null;
  };

  for (const change of changes) {
    const source =
      change.entity === 'location' ? plan.locations[change.key] : plan.gardenObjects[change.key];
    const parentKey = source ? source.parent_location_key : (newEntity?.parentKey ?? null);
    const offSite =
      change.entity === 'garden_object' && plan.gardenObjects[change.key]?.off_site === true;
    const own = check(`${change.entity}:${change.key}`, change.geometry, parentKey, offSite);
    if (own) return own;
  }
  const changedLocations = new Set(
    changes.filter((c) => c.entity === 'location').map((c) => c.key),
  );
  if (changedLocations.size > 0) {
    for (const location of Object.values(plan.locations)) {
      if (!location.geometry || !location.parent_location_key) continue;
      if (!changedLocations.has(location.parent_location_key)) continue;
      const geometry = overrides.get(`location:${location.key}`) ?? location.geometry;
      const result = check(
        `location:${location.key}`,
        geometry,
        location.parent_location_key,
        false,
      );
      if (result) return result;
    }
    for (const garden of Object.values(plan.gardenObjects)) {
      if (!garden.parent_location_key || !changedLocations.has(garden.parent_location_key))
        continue;
      const geometry = overrides.get(`garden_object:${garden.key}`) ?? garden.geometry;
      const result = check(
        `garden_object:${garden.key}`,
        geometry,
        garden.parent_location_key,
        garden.off_site,
      );
      if (result) return result;
    }
  }
  return null;
}

/** For a brand-new shape: the V-01..V-03 verdict, with the parent it would be created under. */
export function violationOfNew(
  plan: PlanModel,
  geometry: Geometry,
  parentKey: string | null,
): string | null {
  const draft: DraftChange = { entity: 'garden_object', key: '__new__', geometry };
  return firstViolation(plan, [draft], { parentKey });
}

/** The smallest placed location that holds `geometry` completely: the parent a new shape gets. */
export function inferParentKey(plan: PlanModel, geometry: Geometry): string | null {
  const shape = toShape(geometry);
  let best: { key: string; area: number } | null = null;
  for (const location of Object.values(plan.locations)) {
    if (!location.geometry) continue;
    const parent = toShape(location.geometry);
    if (parent.kind === 'vertices' && !parent.closed) continue;
    if (!contains(parent, shape)) continue;
    if (best === null || location.area_m2 < best.area)
      best = { key: location.key, area: location.area_m2 };
  }
  return best?.key ?? null;
}
