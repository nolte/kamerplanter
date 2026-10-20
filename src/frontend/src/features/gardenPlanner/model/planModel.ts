/**
 * The client-side plan model: the `GET /sites/{key}/plan` response (DTO v1) normalised into maps by
 * key (GP-NFR-005). Locations, garden objects, slots and plants are looked up by key far more often
 * than they are iterated, and a normalised model lets an edit replace one entry and share the rest
 * (structural sharing, which is what keeps `applyOperation` far under 1 ms on a large plan).
 *
 * Plain JSON-serialisable data only - it lives in the Redux store.
 */
import type { PlanZone } from '../zones/zoneTypes';
import {
  PLAN_SCHEMA_VERSION,
  type DerivedGeometry,
  type GardenObject,
  type GardenPlanResponse,
  type Geometry,
  type PlanLocation,
  type PlanPlant,
  type PlanSettings,
  type PlanSlot,
} from './types';

export interface PlanModel {
  schemaVersion: typeof PLAN_SCHEMA_VERSION;
  siteKey: string;
  siteName: string;
  /** The `plan_revision` this copy was loaded or last saved at (the optimistic lock, V-14). */
  revision: number;
  /** `null` = a site without a garden plan yet (§20.2). */
  settings: PlanSettings | null;
  locations: Record<string, PlanLocation>;
  gardenObjects: Record<string, GardenObject>;
  slots: Record<string, PlanSlot>;
  plants: Record<string, PlanPlant>;
  /**
   * The geometry each bed had when `slots` were delivered: the frame their `plan_geometry` is
   * expressed in. `applyOperation` never touches this map or `slots` (GP-ACC-033: copying 3 000 slots
   * per move breaks the 1 ms budget); `planIndex` derives the current plan position of a slot from
   * the bed's current geometry relative to this frame. Absent = every slot is already in the bed's
   * current frame (hand-built models in tests).
   */
  slotFrames?: Record<string, Geometry>;
  /** Irrigation zones of the site as the plan response carries them (WP 7.6). */
  zones: PlanZone[];
}

/** The response carries a DTO version this client does not read. */
export class UnsupportedPlanSchemaError extends Error {
  constructor(readonly schemaVersion: string) {
    super(`Unsupported garden plan schema_version "${schemaVersion}".`);
    this.name = 'UnsupportedPlanSchemaError';
  }
}

function byKey<T extends { key: string }>(items: readonly T[]): Record<string, T> {
  const map: Record<string, T> = {};
  for (const item of items) map[item.key] = item;
  return map;
}

/** The frame of each placed bed at load time - what the server's slot `plan_geometry` is relative to. */
function slotFramesOf(locations: readonly PlanLocation[]): Record<string, Geometry> {
  const frames: Record<string, Geometry> = {};
  for (const location of locations) {
    if (location.geometry) frames[location.key] = location.geometry;
  }
  return frames;
}

/** Normalise a plan response; throws {@link UnsupportedPlanSchemaError} for another `schema_version`. */
export function normalizePlan(response: GardenPlanResponse): PlanModel {
  if (response.schema_version !== PLAN_SCHEMA_VERSION) {
    throw new UnsupportedPlanSchemaError(response.schema_version);
  }
  return {
    schemaVersion: PLAN_SCHEMA_VERSION,
    siteKey: response.site_key,
    siteName: response.site_name,
    revision: response.plan_revision,
    settings: response.plan ?? null,
    locations: byKey(response.locations),
    gardenObjects: byKey(response.garden_objects),
    slots: byKey(response.slots),
    plants: byKey(response.plants),
    slotFrames: slotFramesOf(response.locations),
    zones: response.zones,
  };
}

/**
 * The locations whose `parent_location_key` chain leads to `rootKey`, `rootKey` included, in
 * breadth-first order. A cycle cannot occur on a valid plan, but is cut anyway.
 */
export function locationSubtree(plan: PlanModel, rootKey: string): string[] {
  const children = new Map<string, string[]>();
  for (const location of Object.values(plan.locations)) {
    const parent = location.parent_location_key;
    if (parent) children.set(parent, [...(children.get(parent) ?? []), location.key]);
  }
  const found = [rootKey];
  const seen = new Set(found);
  for (let index = 0; index < found.length; index += 1) {
    for (const child of children.get(found[index]) ?? []) {
      if (!seen.has(child)) {
        seen.add(child);
        found.push(child);
      }
    }
  }
  return found;
}

/** Plants standing in any of `locationKeys` - through a slot or directly on the location. */
export function plantsInLocations(plan: PlanModel, locationKeys: ReadonlySet<string>): PlanPlant[] {
  return Object.values(plan.plants).filter((plant) => {
    if (plant.slot_key) {
      const slot = plan.slots[plant.slot_key];
      return slot !== undefined && locationKeys.has(slot.location_key);
    }
    return plant.location_key != null && locationKeys.has(plant.location_key);
  });
}

let tempKeySequence = 0;

/**
 * A fresh request-local key for a created object (`^[A-Za-z0-9_-]{1,40}$`). Unique within the
 * session; the server answers with the real key in `key_map`.
 */
export function newTempKey(): string {
  tempKeySequence += 1;
  return `tmp${tempKeySequence.toString(36)}${Math.random().toString(36).slice(2, 6)}`;
}

/**
 * Replace the temp keys the server resolved (`key_map`, GP-API-003) by the assigned keys, in the
 * entities and in every reference to them.
 */
export function applyKeyMap(plan: PlanModel, keyMap: Readonly<Record<string, string>>): PlanModel {
  if (Object.keys(keyMap).length === 0) return plan;
  const rename = (key: string): string => keyMap[key] ?? key;
  const withParent = (parent: string | null | undefined) =>
    parent != null ? { parent_location_key: rename(parent) } : {};

  const locations: Record<string, PlanLocation> = {};
  for (const [key, location] of Object.entries(plan.locations)) {
    const next = rename(key);
    const parent = location.parent_location_key;
    const renamed = next !== key || (parent != null && rename(parent) !== parent);
    locations[next] = renamed ? { ...location, key: next, ...withParent(parent) } : location;
  }
  const gardenObjects: Record<string, GardenObject> = {};
  for (const [key, garden] of Object.entries(plan.gardenObjects)) {
    const next = rename(key);
    const parent = garden.parent_location_key;
    const renamed = next !== key || (parent != null && rename(parent) !== parent);
    gardenObjects[next] = renamed ? { ...garden, key: next, ...withParent(parent) } : garden;
  }
  return { ...plan, locations, gardenObjects };
}

/** Take over the values the server derived for created or moved objects (`derived`, GP-FR-006/007). */
export function applyDerived(
  plan: PlanModel,
  derived: Readonly<Record<string, DerivedGeometry>>,
): PlanModel {
  let locations = plan.locations;
  let gardenObjects = plan.gardenObjects;
  for (const [key, values] of Object.entries(derived)) {
    const location = locations[key];
    if (location) {
      locations = {
        ...locations,
        [key]: {
          ...location,
          ...(values.area_m2 != null ? { area_m2: values.area_m2 } : {}),
          ...(values.bbox != null ? { bbox: values.bbox } : {}),
        },
      };
      continue;
    }
    const garden = gardenObjects[key];
    if (garden && values.bbox != null) {
      gardenObjects = { ...gardenObjects, [key]: { ...garden, bbox: values.bbox } };
    }
  }
  return locations === plan.locations && gardenObjects === plan.gardenObjects
    ? plan
    : { ...plan, locations, gardenObjects };
}
