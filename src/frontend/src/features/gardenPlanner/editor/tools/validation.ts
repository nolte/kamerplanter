/**
 * Live validation while drawing and dragging (REQ-053 GP-UX-053). It mirrors the server's
 * `check_entity` for the rules a client can decide without the database: V-01 (bounds), V-02
 * (simple polygon), V-03 (containment in the nearest placed ancestor, else the garden
 * boundary) and V-05 (two beds of one parent location do not overlap; operator decision of 2026-11-14 on #2759,
 * question 14). V-05 needs the `is_bed` flag of a location's type: the plan carries it as `bedTypeKeys`; a plan
 * without them (cached before the server sent them) leaves V-05 to the server. A bed overlapping a garden object or
 * an area is allowed (a path under a raised bed). The server is the authority; this only draws the red outline early.
 */
import { contains, overlaps, parseGeometry, toShape, validateGeometry } from '../../model/geometry';
import type { PlanModel } from '../../model/planModel';
import type { Geometry, PlanEntity } from '../../model/types';

export const ERROR_INVALID = 'geometry.invalid';
export const ERROR_OUTSIDE_PARENT = 'geometry.outside_parent';
/** V-05: the server's `bed.overlap`. */
export const ERROR_BED_OVERLAP = 'bed.overlap';

/** The key a not-yet-created shape is checked under; no stored or temp key looks like it. */
const NEW_ENTITY_KEY = '__new__';

export interface DraftChange {
  entity: PlanEntity;
  key: string;
  geometry: Geometry;
}

/** A shape that does not exist yet: the parent it would be created under and, for a location, its type. */
export interface NewEntity {
  parentKey: string | null;
  /** The type of a new location; absent = a garden object (never a bed). */
  locationTypeKey?: string;
}

/** Whether locations of `typeKey` are beds by the plan's `bedTypeKeys`; `null` = the plan does not say (no V-05). */
function isBedType(plan: PlanModel, typeKey: string | undefined): boolean | null {
  if (!plan.bedTypeKeys) return null;
  return typeKey !== undefined && plan.bedTypeKeys.includes(typeKey);
}

/**
 * V-05 for one bed: whether `geometry` overlaps another placed bed with the same parent. `overrides` hold the shapes
 * the change set gives the other beds; `selfKey` is skipped (a bed never overlaps itself).
 */
function overlapsSiblingBed(
  plan: PlanModel,
  selfKey: string,
  geometry: Geometry,
  parentKey: string | null,
  overrides: ReadonlyMap<string, Geometry>,
): boolean {
  const shape = toShape(geometry);
  for (const other of Object.values(plan.locations)) {
    if (other.key === selfKey || (other.parent_location_key ?? null) !== parentKey) continue;
    if (isBedType(plan, other.location_type_key) !== true) continue;
    const otherGeometry = overrides.get(`location:${other.key}`) ?? other.geometry;
    if (!otherGeometry) continue;
    if (overlaps(shape, toShape(otherGeometry))) return true;
  }
  return false;
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
  newEntity?: NewEntity,
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
    // V-05, after V-02/V-03 like the server: a shape without a defined interior would answer noise.
    if (change.entity !== 'location') continue;
    const typeKey = source
      ? plan.locations[change.key]?.location_type_key
      : newEntity?.locationTypeKey;
    if (isBedType(plan, typeKey) !== true) continue;
    if (overlapsSiblingBed(plan, change.key, change.geometry, parentKey ?? null, overrides)) {
      return ERROR_BED_OVERLAP;
    }
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

export const ERROR_BOUNDARY_SHRINKS = 'boundary.shrinks_below_objects';

/** Whether a location of the plan bounds `parentKey`'s subtree: some ancestor of it has a geometry. */
function hasPlacedAncestor(plan: PlanModel, parentKey: string | null | undefined): boolean {
  const seen = new Set<string>();
  let current = parentKey ?? null;
  while (current !== null && !seen.has(current)) {
    seen.add(current);
    const location = plan.locations[current];
    if (location?.geometry) return true;
    current = location?.parent_location_key ?? null;
  }
  return false;
}

/**
 * A new garden boundary (GP-FR-019, UC-01): V-01/V-02 on its own shape, then V-03 from the other side - mirroring the
 * server's V-19 (`boundary_violations`): every placed bed and garden object the boundary bounds directly (no placed
 * ancestor, not `off_site`) must lie inside it, 1 cm tolerance. `null` = fine. Nothing is clipped: a refusal keeps the
 * stored boundary, the user moves the objects first.
 */
export function boundaryViolation(plan: PlanModel, boundary: Geometry): string | null {
  if (boundary.kind !== 'rect' && boundary.kind !== 'polygon') return ERROR_INVALID;
  if (parseGeometry(boundary, 'plan') === null) return ERROR_INVALID;
  const simple = validateGeometry(boundary);
  if (simple.length > 0) return simple[0];
  const outline = toShape(boundary);
  for (const location of Object.values(plan.locations)) {
    if (!location.geometry || hasPlacedAncestor(plan, location.parent_location_key)) continue;
    if (!contains(outline, toShape(location.geometry))) return ERROR_BOUNDARY_SHRINKS;
  }
  for (const garden of Object.values(plan.gardenObjects)) {
    if (!garden.geometry || garden.off_site || hasPlacedAncestor(plan, garden.parent_location_key)) continue;
    if (!contains(outline, toShape(garden.geometry))) return ERROR_BOUNDARY_SHRINKS;
  }
  return null;
}

/**
 * For a brand-new shape: the V-01..V-03 verdict, with the parent it would be created under - and V-05 when it is a
 * location of a bed type (`locationTypeKey`).
 */
export function violationOfNew(
  plan: PlanModel,
  geometry: Geometry,
  parentKey: string | null,
  locationTypeKey?: string,
): string | null {
  const draft: DraftChange = {
    entity: locationTypeKey === undefined ? 'garden_object' : 'location',
    key: NEW_ENTITY_KEY,
    geometry,
  };
  return firstViolation(plan, [draft], { parentKey, locationTypeKey });
}

/**
 * The smallest placed location that holds `geometry` completely: the parent a new shape gets. `areasOnly`: only area
 * locations qualify - a new area never lies in a bed (REQ-053 GP-UX-071, #2913).
 */
export function inferParentKey(plan: PlanModel, geometry: Geometry, areasOnly = false): string | null {
  const shape = toShape(geometry);
  let best: { key: string; area: number } | null = null;
  for (const location of Object.values(plan.locations)) {
    if (!location.geometry) continue;
    if (areasOnly && location.is_area !== true) continue;
    const parent = toShape(location.geometry);
    if (parent.kind === 'vertices' && !parent.closed) continue;
    if (!contains(parent, shape)) continue;
    if (best === null || location.area_m2 < best.area)
      best = { key: location.key, area: location.area_m2 };
  }
  return best?.key ?? null;
}
