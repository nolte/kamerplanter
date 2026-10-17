/**
 * Duplicate with offset (REQ-053 GP-FR-025): copies geometry and base fields of the selected
 * locations and garden objects - and everything inside a selected area - shifted by one grid step.
 * Plants and tasks are never copied. Slots cannot be: the closed plan operation list has no
 * `create_slot`, so a copied bed starts without positions (the panel offers to lay them out).
 * Every copy gets a fresh temp key; one duplicate is one `PlanOperation` batch = one undo step.
 */
import { locationSubtree, newTempKey, type PlanModel } from '../../model/planModel';
import type {
  CreateGardenObjectData,
  CreateLocationData,
  GardenObject,
  PlanLocation,
  PlanOperation,
  Point,
} from '../../model/types';
import type { SelectionRef } from '../../state/gardenPlanSlice';
import { translateGeometry } from './geometryEdit';
import { objectsIn, selectionRoots } from './hierarchy';
import { violationOfNew } from './validation';

/** Offset directions tried in turn: down-right first, then the other diagonals and axes. */
const DIRECTIONS: readonly Point[] = [
  [1, -1],
  [1, 1],
  [-1, -1],
  [-1, 1],
  [1, 0],
  [0, 1],
  [-1, 0],
  [0, -1],
];

export interface DuplicateResult {
  ops: PlanOperation[];
  /** The copies of the selection roots, to select afterwards. */
  selection: SelectionRef[];
}

export type DuplicateOutcome =
  | { ok: true; value: DuplicateResult }
  | { ok: false; code: 'nothing' | 'geometry.outside_parent' | 'geometry.invalid' };

function locationData(
  location: PlanLocation,
  geometry: NonNullable<PlanLocation['geometry']>,
  parent: string | null,
  copyName: string,
): CreateLocationData {
  const data: CreateLocationData = {
    name: copyName,
    location_type_key: location.location_type_key,
    geometry,
    sun_exposure: location.sun_exposure,
    z_order: location.z_order,
  };
  if (parent) data.parent_location_key = parent;
  if (location.height_m != null) data.height_m = location.height_m;
  if (location.description != null) data.description = location.description;
  if (location.notes != null) data.notes = location.notes;
  return data;
}

function objectData(
  garden: GardenObject,
  geometry: GardenObject['geometry'],
  parent: string | null,
): CreateGardenObjectData {
  const data: CreateGardenObjectData = {
    object_type: garden.object_type,
    label: garden.label,
    geometry,
    props: garden.props as unknown as Record<string, unknown>,
    off_site: garden.off_site,
    z_order: garden.z_order,
  };
  if (parent) data.parent_location_key = parent;
  if (garden.notes != null) data.notes = garden.notes;
  return data;
}

/**
 * The operations that duplicate `selection`, shifted by `stepM` metres in the first direction
 * where the copies stay inside their parent (the live validation of GP-UX-053).
 * `copyName(name)` builds the name of a copied bed ("Beet 1 (Kopie)"); i18n stays with the caller.
 */
export function duplicateSelection(
  plan: PlanModel,
  selection: readonly SelectionRef[],
  stepM: number,
  copyName: (name: string) => string,
): DuplicateOutcome {
  const roots = selectionRoots(plan, selection).filter((ref) => {
    const source =
      ref.entity === 'location' ? plan.locations[ref.key] : plan.gardenObjects[ref.key];
    return source?.geometry != null;
  });
  if (roots.length === 0) return { ok: false, code: 'nothing' };

  const locationKeys = new Set(
    roots.filter((r) => r.entity === 'location').flatMap((r) => locationSubtree(plan, r.key)),
  );
  const insideObjects = objectsIn(plan, locationKeys);
  const rootObjectKeys = roots.filter((r) => r.entity === 'garden_object').map((r) => r.key);

  let sawOutside = false;
  for (const [dx, dy] of DIRECTIONS) {
    const delta: Point = [dx * stepM, dy * stepM];
    // Keys of the copies, so children point at their copied parent.
    const copyOf = new Map<string, string>();
    for (const key of locationKeys) copyOf.set(key, newTempKey());
    const ops: PlanOperation[] = [];
    let violation: string | null = null;
    const rootCopies: SelectionRef[] = [];
    // Parents first: `locationSubtree` is breadth-first per root.
    const orderedLocations = roots
      .filter((r) => r.entity === 'location')
      .flatMap((r) => locationSubtree(plan, r.key));
    for (const key of orderedLocations) {
      const location = plan.locations[key];
      if (!location.geometry) continue;
      const geometry = translateGeometry(location.geometry, delta);
      const isRoot = roots.some((r) => r.entity === 'location' && r.key === key);
      const parent = isRoot
        ? (location.parent_location_key ?? null)
        : (copyOf.get(location.parent_location_key ?? '') ?? null);
      const tempKey = copyOf.get(key)!;
      ops.push({
        op: 'create_location',
        temp_key: tempKey,
        data: locationData(
          location,
          geometry,
          parent,
          isRoot ? copyName(location.name) : location.name,
        ),
      });
      if (isRoot) {
        // A root copy shares the parent of its original; its subtree moves rigidly with it.
        violation ??= violationOfNew(plan, geometry, parent);
        rootCopies.push({ entity: 'location', key: tempKey });
      }
    }
    for (const key of [
      ...rootObjectKeys,
      ...insideObjects.filter((k) => !rootObjectKeys.includes(k)),
    ]) {
      const garden = plan.gardenObjects[key];
      const isRoot = rootObjectKeys.includes(key);
      const geometry = translateGeometry(garden.geometry, delta);
      const parent = isRoot
        ? (garden.parent_location_key ?? null)
        : (copyOf.get(garden.parent_location_key ?? '') ?? null);
      const tempKey = newTempKey();
      ops.push({
        op: 'create_garden_object',
        temp_key: tempKey,
        data: objectData(garden, geometry, parent),
      });
      if (isRoot) {
        if (!garden.off_site) violation ??= violationOfNew(plan, geometry, parent);
        rootCopies.push({ entity: 'garden_object', key: tempKey });
      }
    }
    if (violation === null) return { ok: true, value: { ops, selection: rootCopies } };
    sawOutside ||= violation === 'geometry.outside_parent';
  }
  return { ok: false, code: sawOutside ? 'geometry.outside_parent' : 'geometry.invalid' };
}
