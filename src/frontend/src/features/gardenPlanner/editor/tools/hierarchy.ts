/**
 * Parent/child behaviour of the plan (REQ-053 GP-FR-151/153/156): which entities move with an
 * area, and what a delete takes along. Everything is derived from the plan model - nothing is
 * guessed - so the delete dialog's numbers are the numbers `applyOperation` will remove.
 */
import { applyOperations } from '../../model/applyOperation';
import { locationSubtree, plantsInLocations, type PlanModel } from '../../model/planModel';
import type { Geometry, PlanEntity, PlanOperation } from '../../model/types';
import type { SelectionRef } from '../../state/gardenPlanSlice';

/** A location or garden object whose geometry an action changes. */
export interface GeometryEntry {
  entity: PlanEntity;
  key: string;
  geometry: Geometry;
  locked: boolean;
}

export function isPlanEntity(ref: SelectionRef): ref is SelectionRef & { entity: PlanEntity } {
  return ref.entity === 'location' || ref.entity === 'garden_object';
}

export function parentKeyOf(plan: PlanModel, entity: PlanEntity, key: string): string | null {
  const parent =
    entity === 'location'
      ? plan.locations[key]?.parent_location_key
      : plan.gardenObjects[key]?.parent_location_key;
  return parent ?? null;
}

function entryOf(plan: PlanModel, entity: PlanEntity, key: string): GeometryEntry | null {
  const source = entity === 'location' ? plan.locations[key] : plan.gardenObjects[key];
  if (!source?.geometry) return null; // a bed that is not on the plan has nothing to move
  return { entity, key, geometry: source.geometry, locked: source.locked };
}

/** Whether a location above `entity` (any depth) is in `locationKeys`. */
function hasAncestorIn(
  plan: PlanModel,
  entity: PlanEntity,
  key: string,
  locationKeys: ReadonlySet<string>,
): boolean {
  const seen = new Set<string>();
  let parent = parentKeyOf(plan, entity, key);
  while (parent !== null && !seen.has(parent)) {
    if (locationKeys.has(parent)) return true;
    seen.add(parent);
    parent = parentKeyOf(plan, 'location', parent);
  }
  return false;
}

/**
 * The selected locations and garden objects that have no selected location above them: moving or
 * deleting those covers the rest (GP-FR-151 - a child of a selected area is not moved twice).
 */
export function selectionRoots(
  plan: PlanModel,
  selection: readonly SelectionRef[],
): (SelectionRef & { entity: PlanEntity })[] {
  const entities = selection.filter(isPlanEntity);
  const selectedLocations = new Set(
    entities.filter((ref) => ref.entity === 'location').map((ref) => ref.key),
  );
  return entities.filter((ref) => !hasAncestorIn(plan, ref.entity, ref.key, selectedLocations));
}

/** The garden objects inside any of `locationKeys`. */
export function objectsIn(plan: PlanModel, locationKeys: ReadonlySet<string>): string[] {
  return Object.values(plan.gardenObjects)
    .filter(
      (garden) =>
        garden.parent_location_key != null && locationKeys.has(garden.parent_location_key),
    )
    .map((garden) => garden.key);
}

/**
 * What a move or rotation of `selection` changes: the selection roots and everything below an
 * area among them, each exactly once, with the geometry it has now (GP-FR-151).
 */
export function moveTargets(plan: PlanModel, selection: readonly SelectionRef[]): GeometryEntry[] {
  const found = new Map<string, GeometryEntry>();
  const add = (entity: PlanEntity, key: string) => {
    const entry = entryOf(plan, entity, key);
    if (entry && !found.has(`${entity}:${key}`)) found.set(`${entity}:${key}`, entry);
  };
  for (const root of selectionRoots(plan, selection)) {
    add(root.entity, root.key);
    if (root.entity === 'location') {
      const subtree = new Set(locationSubtree(plan, root.key));
      for (const key of subtree) add('location', key);
      for (const key of objectsIn(plan, subtree)) add('garden_object', key);
    }
  }
  return [...found.values()];
}

/** What a delete of the selection takes along (GP-FR-153): counts of the children it removes. */
export interface DeleteImpact {
  /** The selection roots that get a `delete` operation. */
  roots: { entity: PlanEntity; key: string; name: string }[];
  /** Locations below the roots (not the roots themselves). */
  childBeds: number;
  childObjects: number;
  slots: number;
  plants: number;
  /** Open tasks of every deleted location. */
  tasks: number;
  /** Locked entities that stop the delete (GP-FR-032). */
  lockedKeys: string[];
  /** False when the delete cannot be put back by counter-operations after saving (GP-FR-155). */
  reversible: boolean;
  ops: PlanOperation[];
}

export function deleteImpact(plan: PlanModel, selection: readonly SelectionRef[]): DeleteImpact {
  const roots = selectionRoots(plan, selection);
  const rootLocations = roots.filter((ref) => ref.entity === 'location').map((ref) => ref.key);
  const locationKeys = new Set(rootLocations.flatMap((key) => locationSubtree(plan, key)));
  const insideObjects = objectsIn(plan, locationKeys);
  // An object selected on its own is a root; one below a selected area is a child.
  const rootObjects = roots.filter((ref) => ref.entity === 'garden_object').map((ref) => ref.key);

  const lockedKeys = [
    ...[...locationKeys].filter((key) => plan.locations[key]?.locked),
    ...[...new Set([...insideObjects, ...rootObjects])].filter(
      (key) => plan.gardenObjects[key]?.locked,
    ),
  ];
  let tasks = 0;
  for (const key of locationKeys) tasks += plan.locations[key]?.open_task_count ?? 0;

  const ops: PlanOperation[] = roots.map(({ entity, key }) => ({ op: 'delete', entity, key }));
  let reversible = false;
  if (lockedKeys.length === 0 && ops.length > 0) {
    try {
      reversible = applyOperations(plan, ops).inverse !== null;
    } catch {
      reversible = false;
    }
  }
  return {
    roots: roots.map(({ entity, key }) => ({
      entity,
      key,
      name:
        (entity === 'location' ? plan.locations[key]?.name : plan.gardenObjects[key]?.label) ?? '',
    })),
    childBeds: Math.max(0, locationKeys.size - rootLocations.length),
    childObjects: insideObjects.length,
    slots: Object.values(plan.slots).filter((slot) => locationKeys.has(slot.location_key)).length,
    plants: plantsInLocations(plan, locationKeys).length,
    tasks,
    lockedKeys,
    reversible,
    ops,
  };
}
