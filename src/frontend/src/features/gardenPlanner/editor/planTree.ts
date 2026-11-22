/**
 * The plan as a tree for the list view (REQ-053 GP-NFR-023): garden -> area -> bed -> object,
 * derived from the same model the canvas draws. Pure.
 *
 * The plan carries no "is a bed" flag for a location (the location type does, but the read model
 * leaves it out), so a location that has locations below it is an *area* and a leaf is a *bed*.
 */
import type { PlanModel } from '../model/planModel';
import type { GardenObjectType } from '../model/types';
import type { SelectionRef } from '../state/gardenPlanSlice';

export type TreeLevel = 'area' | 'bed' | 'object';

export interface TreeRow {
  /** The renderer key; also what `data-list-key` carries. */
  key: string;
  ref: SelectionRef & { entity: 'location' | 'garden_object' };
  level: TreeLevel;
  /** 1 = directly below the garden. */
  depth: number;
  name: string;
  objectType: GardenObjectType | null;
  locked: boolean;
  placed: boolean;
}

const byName = (a: { name: string }, b: { name: string }) => a.name.localeCompare(b.name);

/** Rows in reading order: an area, then what is inside it, then the next area. */
export function buildTree(
  plan: PlanModel,
  objectName: (type: GardenObjectType) => string,
): TreeRow[] {
  const locations = Object.values(plan.locations);
  const childrenOf = new Map<string | null, typeof locations>();
  for (const location of locations) {
    const parent =
      location.parent_location_key && location.parent_location_key in plan.locations
        ? location.parent_location_key
        : null;
    childrenOf.set(parent, [...(childrenOf.get(parent) ?? []), location]);
  }
  const objectsOf = new Map<string | null, TreeRow[]>();
  for (const object of Object.values(plan.gardenObjects)) {
    const parent =
      object.parent_location_key && object.parent_location_key in plan.locations
        ? object.parent_location_key
        : null;
    const row: TreeRow = {
      key: object.key,
      ref: { entity: 'garden_object', key: object.key },
      level: 'object',
      depth: 0,
      name: object.label || objectName(object.object_type),
      objectType: object.object_type,
      locked: object.locked,
      placed: true,
    };
    objectsOf.set(parent, [...(objectsOf.get(parent) ?? []), row]);
  }

  const rows: TreeRow[] = [];
  const seen = new Set<string>();
  const walk = (parent: string | null, depth: number) => {
    for (const location of [...(childrenOf.get(parent) ?? [])].sort(byName)) {
      if (seen.has(location.key)) continue; // a cycle cannot occur on a valid plan, but is cut
      seen.add(location.key);
      rows.push({
        key: location.key,
        ref: { entity: 'location', key: location.key },
        level: childrenOf.has(location.key) ? 'area' : 'bed',
        depth,
        name: location.name,
        objectType: null,
        locked: location.locked,
        placed: Boolean(location.geometry),
      });
      walk(location.key, depth + 1);
    }
    for (const row of [...(objectsOf.get(parent) ?? [])].sort(byName)) rows.push({ ...row, depth });
  };
  walk(null, 1);
  return rows;
}

/**
 * Where the focus goes when the rows `removedRoots` leave the list (with everything below them):
 * the next row that stays, else the previous one, else `null` (GP-NFR-070 - never to the body).
 */
export function neighbourKey(
  rows: readonly TreeRow[],
  removedRoots: ReadonlySet<string>,
): string | null {
  const gone = new Set<string>();
  rows.forEach((row, index) => {
    if (!removedRoots.has(row.key)) return;
    gone.add(row.key);
    for (let next = index + 1; next < rows.length && rows[next].depth > row.depth; next += 1)
      gone.add(rows[next].key);
  });
  const first = rows.findIndex((row) => gone.has(row.key));
  if (first < 0) return null;
  const after = rows.slice(first + 1).find((row) => !gone.has(row.key));
  if (after) return after.key;
  const before = [...rows.slice(0, first)].reverse().find((row) => !gone.has(row.key));
  return before?.key ?? null;
}
