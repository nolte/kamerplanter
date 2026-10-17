/**
 * `applyOperation` - the pure, invertible reducer of the plan model (REQ-053 GP-NFR-005/006,
 * GP-FR-026, GP-FR-155).
 *
 * Every user action is expressed as `PlanOperation`s of the closed list of GP-API-003. The same
 * operations are applied to the local model (optimistic update) and sent in the batch, so what the
 * user sees is what the server will do. Applying an operation returns the new model **and** its
 * inverse: the operations that undo it once it is saved (GP-FR-155 "after saving, undo produces a
 * counter-operation").
 *
 * Pure: the input model is never mutated and unchanged parts are shared, so one edit copies one map
 * of keys, not the plan (GP-ACC-033 budget: <= 1 ms for a move on a large plan).
 *
 * Mirrors the server's working copy (`GardenPlanService._run_operation`) for the rules a client can
 * decide without the database: unknown references, duplicate temp keys, locked objects. Containment
 * and overlap (V-03/V-05) stay the server's - it is the authority, and a refused batch (422) comes
 * back with the failing `op_index`.
 */
import { areaM2, boundingBox, roundLength } from './geometry';
import { locationSubtree, plantsInLocations, type PlanModel } from './planModel';
import type {
  BoundingBox,
  CreateGardenObjectOp,
  CreateLocationOp,
  DeleteOp,
  GardenObject,
  GardenObjectProps,
  Geometry,
  LocationFieldsPatch,
  PlanEntity,
  PlanLocation,
  PlanOperation,
  PlanSettings,
  SetBoundaryOp,
  UpdateFieldsOp,
  UpdateGeometryOp,
} from './types';

/** A point object (water source, lamp) is drawn as a circle of this radius (§9.5). */
const POINT_OBJECT_RADIUS_M = 0.25;

/** `temp_key` pattern of the closed operation list. */
const TEMP_KEY = /^[A-Za-z0-9_-]{1,40}$/;

/** Plan frame defaults of a site that has no plan yet (`SitePlan`). */
const DEFAULT_GRID_M = 0.1;
const DEFAULT_ADJACENCY_FACTOR = 1.5;

export type PlanOperationErrorCode =
  'reference.not_found' | 'temp_key.duplicate' | 'object.locked' | 'operation.unsupported';

/** An operation the local model refuses; the plan is left untouched. */
export class PlanOperationError extends Error {
  constructor(
    readonly code: PlanOperationErrorCode,
    readonly operation: PlanOperation['op'],
    readonly key?: string,
  ) {
    super(`${operation}: ${code}${key ? ` (${key})` : ''}`);
    this.name = 'PlanOperationError';
  }
}

export interface AppliedOperation {
  plan: PlanModel;
  /**
   * Operations that undo this one, in application order. `null` when the effect cannot be put on
   * the wire (a bed with plants removed, a geometry removed from a placed bed, a field the lean
   * read model does not carry): such a step is undoable only while it is still pending.
   */
  inverse: PlanOperation[] | null;
}

// ── helpers ──────────────────────────────────────────────────────────────────

function geometryOf(entity: PlanEntity, plan: PlanModel, key: string): Geometry | null | undefined {
  return entity === 'location' ? plan.locations[key]?.geometry : plan.gardenObjects[key]?.geometry;
}

function objectBbox(geometry: Geometry): BoundingBox {
  const [minX, minY, maxX, maxY] = boundingBox(geometry);
  if (geometry.kind !== 'point') return [minX, minY, maxX, maxY];
  const r = POINT_OBJECT_RADIUS_M;
  return [
    roundLength(minX - r),
    roundLength(minY - r),
    roundLength(maxX + r),
    roundLength(maxY + r),
  ];
}

function withGeometry(location: PlanLocation, geometry: Geometry): PlanLocation {
  return { ...location, geometry, area_m2: areaM2(geometry), bbox: boundingBox(geometry) };
}

function requireEntity(
  plan: PlanModel,
  op: PlanOperation['op'],
  entity: PlanEntity,
  key: string,
): void {
  const exists = entity === 'location' ? key in plan.locations : key in plan.gardenObjects;
  if (!exists) throw new PlanOperationError('reference.not_found', op, key);
}

function isLocked(plan: PlanModel, entity: PlanEntity, key: string): boolean {
  return (
    (entity === 'location' ? plan.locations[key]?.locked : plan.gardenObjects[key]?.locked) === true
  );
}

function requireFreeTempKey(plan: PlanModel, op: PlanOperation['op'], tempKey: string): void {
  if (tempKey in plan.locations || tempKey in plan.gardenObjects) {
    throw new PlanOperationError('temp_key.duplicate', op, tempKey);
  }
}

function replaceEntry<T>(map: Record<string, T>, key: string, value: T): Record<string, T> {
  return { ...map, [key]: value };
}

function withoutKeys<T>(map: Record<string, T>, keys: ReadonlySet<string>): Record<string, T> {
  const result: Record<string, T> = {};
  for (const [key, value] of Object.entries(map)) {
    if (!keys.has(key)) result[key] = value;
  }
  return result;
}

// ── create ───────────────────────────────────────────────────────────────────

function createLocation(plan: PlanModel, op: CreateLocationOp): AppliedOperation {
  requireFreeTempKey(plan, op.op, op.temp_key);
  const { data } = op;
  const parentKey = data.parent_location_key ?? null;
  let depth = 0;
  if (parentKey !== null) {
    const parent = plan.locations[parentKey];
    if (parent === undefined) throw new PlanOperationError('reference.not_found', op.op, parentKey);
    depth = parent.depth + 1;
  }
  const location: PlanLocation = {
    key: op.temp_key,
    name: data.name,
    location_type_key: data.location_type_key,
    depth,
    geometry: data.geometry,
    area_m2: areaM2(data.geometry),
    bbox: boundingBox(data.geometry),
    bed_status: 'active',
    sun_exposure: data.sun_exposure ?? 'unknown',
    locked: data.locked ?? false,
    z_order: data.z_order ?? 0,
    open_task_count: 0,
    overdue_task_count: 0,
  };
  if (parentKey !== null) location.parent_location_key = parentKey;
  if (data.height_m != null) location.height_m = data.height_m;
  if (data.description != null) location.description = data.description;
  if (data.notes != null) location.notes = data.notes;
  return {
    plan: { ...plan, locations: replaceEntry(plan.locations, op.temp_key, location) },
    inverse: [{ op: 'delete', entity: 'location', key: op.temp_key }],
  };
}

/** `{ ...props, object_type }` - the discriminator inside `props` is the object's `object_type`. */
function objectProps(op: CreateGardenObjectOp): GardenObjectProps {
  const { data } = op;
  const props: Record<string, unknown> = { ...(data.props ?? {}), object_type: data.object_type };
  // The drawn circle is the crown (§9.5): a tree needs no radius twice.
  if (data.object_type === 'tree' && data.geometry.kind === 'circle') {
    props.crown_radius_m = data.geometry.radius_m;
  }
  return props as unknown as GardenObjectProps;
}

function createGardenObject(plan: PlanModel, op: CreateGardenObjectOp): AppliedOperation {
  requireFreeTempKey(plan, op.op, op.temp_key);
  const { data } = op;
  const parentKey = data.parent_location_key ?? null;
  if (parentKey !== null && !(parentKey in plan.locations)) {
    throw new PlanOperationError('reference.not_found', op.op, parentKey);
  }
  const garden: GardenObject = {
    key: op.temp_key,
    site_key: plan.siteKey,
    object_type: data.object_type,
    label: (data.label ?? '').trim(),
    geometry: data.geometry,
    bbox: objectBbox(data.geometry),
    props: objectProps(op),
    off_site: data.off_site ?? false,
    locked: data.locked ?? false,
    z_order: data.z_order ?? 0,
  };
  if (parentKey !== null) garden.parent_location_key = parentKey;
  if (data.notes != null) garden.notes = data.notes;
  return {
    plan: { ...plan, gardenObjects: replaceEntry(plan.gardenObjects, op.temp_key, garden) },
    inverse: [{ op: 'delete', entity: 'garden_object', key: op.temp_key }],
  };
}

// ── update ───────────────────────────────────────────────────────────────────

function updateGeometry(plan: PlanModel, op: UpdateGeometryOp): AppliedOperation {
  requireEntity(plan, op.op, op.entity, op.key);
  if (isLocked(plan, op.entity, op.key))
    throw new PlanOperationError('object.locked', op.op, op.key);
  const previous = geometryOf(op.entity, plan, op.key);
  // A bed taken off the plan has no wire operation: `geometry` cannot be set to null.
  const inverse: PlanOperation[] | null = previous
    ? [{ op: 'update_geometry', entity: op.entity, key: op.key, geometry: previous }]
    : null;
  if (op.entity === 'location') {
    const location = plan.locations[op.key];
    return {
      plan: {
        ...plan,
        locations: replaceEntry(plan.locations, op.key, withGeometry(location, op.geometry)),
      },
      inverse,
    };
  }
  const garden = plan.gardenObjects[op.key];
  const moved: GardenObject = { ...garden, geometry: op.geometry, bbox: objectBbox(op.geometry) };
  return {
    plan: { ...plan, gardenObjects: replaceEntry(plan.gardenObjects, op.key, moved) },
    inverse,
  };
}

function updateLocationFields(
  plan: PlanModel,
  op: Extract<UpdateFieldsOp, { entity: 'location' }>,
): AppliedOperation {
  const location = plan.locations[op.key];
  const patch = op.fields;
  const next: PlanLocation = { ...location };
  const before: LocationFieldsPatch = {};
  let invertible = true;
  if (patch.name !== undefined) {
    before.name = location.name;
    next.name = patch.name;
  }
  if (patch.sun_exposure !== undefined) {
    before.sun_exposure = location.sun_exposure;
    next.sun_exposure = patch.sun_exposure;
  }
  if (patch.height_m !== undefined) {
    before.height_m = location.height_m ?? null;
    if (patch.height_m === null) delete next.height_m;
    else next.height_m = patch.height_m;
  }
  // `description` and `notes` are not in the lean read model: the old value is unknown, so the
  // step has no wire inverse (undo only while it is pending).
  if (patch.description !== undefined) {
    next.description = patch.description;
    invertible = false;
  }
  if (patch.notes !== undefined) {
    next.notes = patch.notes;
    invertible = false;
  }
  return {
    plan: { ...plan, locations: replaceEntry(plan.locations, op.key, next) },
    inverse: invertible
      ? [{ op: 'update_fields', entity: 'location', key: op.key, fields: before }]
      : null,
  };
}

function updateObjectFields(
  plan: PlanModel,
  op: Extract<UpdateFieldsOp, { entity: 'garden_object' }>,
): AppliedOperation {
  const garden = plan.gardenObjects[op.key];
  const patch = op.fields;
  const next: GardenObject = { ...garden };
  const before: Record<string, unknown> = {};
  if (patch.label !== undefined) {
    before.label = garden.label;
    next.label = patch.label.trim();
  }
  if (patch.notes !== undefined) {
    before.notes = garden.notes ?? null;
    if (patch.notes === null) delete next.notes;
    else next.notes = patch.notes;
  }
  if (patch.props !== undefined) {
    before.props = garden.props;
    next.props = {
      ...patch.props,
      object_type: garden.object_type,
    } as unknown as GardenObjectProps;
  }
  if (patch.off_site !== undefined) {
    before.off_site = garden.off_site;
    next.off_site = patch.off_site;
  }
  return {
    plan: { ...plan, gardenObjects: replaceEntry(plan.gardenObjects, op.key, next) },
    inverse: [{ op: 'update_fields', entity: 'garden_object', key: op.key, fields: before }],
  };
}

function updateFields(plan: PlanModel, op: UpdateFieldsOp): AppliedOperation {
  requireEntity(plan, op.op, op.entity, op.key);
  return op.entity === 'location' ? updateLocationFields(plan, op) : updateObjectFields(plan, op);
}

// ── delete ───────────────────────────────────────────────────────────────────

function recreateLocation(location: PlanLocation): PlanOperation | null {
  if (!location.geometry || !TEMP_KEY.test(location.key)) return null;
  const data: CreateLocationOp['data'] = {
    name: location.name,
    location_type_key: location.location_type_key,
    geometry: location.geometry,
    sun_exposure: location.sun_exposure,
    locked: location.locked,
    z_order: location.z_order,
  };
  if (location.parent_location_key) data.parent_location_key = location.parent_location_key;
  if (location.height_m != null) data.height_m = location.height_m;
  if (location.description != null) data.description = location.description;
  if (location.notes != null) data.notes = location.notes;
  return { op: 'create_location', temp_key: location.key, data };
}

function recreateObject(garden: GardenObject): PlanOperation | null {
  if (!TEMP_KEY.test(garden.key)) return null;
  const data: CreateGardenObjectOp['data'] = {
    object_type: garden.object_type,
    label: garden.label,
    geometry: garden.geometry,
    props: garden.props as unknown as Record<string, unknown>,
    off_site: garden.off_site,
    locked: garden.locked,
    z_order: garden.z_order,
  };
  if (garden.parent_location_key) data.parent_location_key = garden.parent_location_key;
  if (garden.notes != null) data.notes = garden.notes;
  return { op: 'create_garden_object', temp_key: garden.key, data };
}

function deleteGardenObject(plan: PlanModel, op: DeleteOp): AppliedOperation {
  const garden = plan.gardenObjects[op.key];
  const recreate = recreateObject(garden);
  return {
    plan: { ...plan, gardenObjects: withoutKeys(plan.gardenObjects, new Set([op.key])) },
    inverse: recreate ? [recreate] : null,
  };
}

/**
 * Deleting a location removes its descendants, the garden objects inside them, their slots and the
 * plants in those slots (the server cascades the same way). A locked bed in the subtree refuses the
 * whole delete (GP-FR-032).
 */
function deleteLocation(plan: PlanModel, op: DeleteOp): AppliedOperation {
  const subtree = locationSubtree(plan, op.key);
  const locationKeys = new Set(subtree);
  const inside = Object.values(plan.gardenObjects).filter(
    (garden) => garden.parent_location_key != null && locationKeys.has(garden.parent_location_key),
  );
  const locked =
    subtree.find((key) => plan.locations[key].locked) ?? inside.find((g) => g.locked)?.key;
  if (locked !== undefined) throw new PlanOperationError('object.locked', op.op, locked);

  const hasPlants = plantsInLocations(plan, locationKeys).length > 0;
  const creates = [
    ...subtree.map((key) => recreateLocation(plan.locations[key])),
    ...inside.map(recreateObject),
  ];
  const invertible = !hasPlants && creates.every((create) => create !== null);

  const removedSlots = new Set(
    Object.values(plan.slots)
      .filter((slot) => locationKeys.has(slot.location_key))
      .map((slot) => slot.key),
  );
  const removedPlants = new Set(
    Object.values(plan.plants)
      .filter((plant) => {
        if (plant.slot_key) return removedSlots.has(plant.slot_key);
        return plant.location_key != null && locationKeys.has(plant.location_key);
      })
      .map((plant) => plant.key),
  );
  return {
    plan: {
      ...plan,
      locations: withoutKeys(plan.locations, locationKeys),
      gardenObjects: withoutKeys(plan.gardenObjects, new Set(inside.map((garden) => garden.key))),
      slots: removedSlots.size ? withoutKeys(plan.slots, removedSlots) : plan.slots,
      plants: removedPlants.size ? withoutKeys(plan.plants, removedPlants) : plan.plants,
    },
    inverse: invertible ? (creates as PlanOperation[]) : null,
  };
}

function deleteEntity(plan: PlanModel, op: DeleteOp): AppliedOperation {
  requireEntity(plan, op.op, op.entity, op.key);
  if (isLocked(plan, op.entity, op.key))
    throw new PlanOperationError('object.locked', op.op, op.key);
  return op.entity === 'garden_object' ? deleteGardenObject(plan, op) : deleteLocation(plan, op);
}

// ── boundary, lock, z-order ──────────────────────────────────────────────────

function setBoundary(plan: PlanModel, op: SetBoundaryOp): AppliedOperation {
  const previous = plan.settings;
  const settings: PlanSettings = {
    north_angle_deg: previous?.north_angle_deg ?? 0,
    default_grid_m: previous?.default_grid_m ?? DEFAULT_GRID_M,
    adjacency_factor: previous?.adjacency_factor ?? DEFAULT_ADJACENCY_FACTOR,
    plan_revision: previous?.plan_revision ?? plan.revision,
    ...(previous ?? {}),
    boundary: op.boundary,
  };
  if (op.north_angle_deg != null) settings.north_angle_deg = op.north_angle_deg;
  if (op.default_grid_m != null) settings.default_grid_m = op.default_grid_m;
  if (op.adjacency_factor != null) settings.adjacency_factor = op.adjacency_factor;
  // A plan that did not exist, or had no outline, cannot be put back by a wire operation.
  const inverse: PlanOperation[] | null = previous?.boundary
    ? [
        {
          op: 'set_boundary',
          boundary: previous.boundary,
          north_angle_deg: previous.north_angle_deg,
          default_grid_m: previous.default_grid_m,
          adjacency_factor: previous.adjacency_factor,
        },
      ]
    : null;
  return { plan: { ...plan, settings }, inverse };
}

function setLocked(
  plan: PlanModel,
  op: Extract<PlanOperation, { op: 'set_locked' }>,
): AppliedOperation {
  requireEntity(plan, op.op, op.entity, op.key);
  const was = isLocked(plan, op.entity, op.key);
  const inverse: PlanOperation[] = [
    { op: 'set_locked', entity: op.entity, key: op.key, locked: was },
  ];
  if (op.entity === 'location') {
    const next = { ...plan.locations[op.key], locked: op.locked };
    return { plan: { ...plan, locations: replaceEntry(plan.locations, op.key, next) }, inverse };
  }
  const next = { ...plan.gardenObjects[op.key], locked: op.locked };
  return {
    plan: { ...plan, gardenObjects: replaceEntry(plan.gardenObjects, op.key, next) },
    inverse,
  };
}

function setZOrder(
  plan: PlanModel,
  op: Extract<PlanOperation, { op: 'set_z_order' }>,
): AppliedOperation {
  requireEntity(plan, op.op, op.entity, op.key);
  const was =
    op.entity === 'location' ? plan.locations[op.key].z_order : plan.gardenObjects[op.key].z_order;
  const inverse: PlanOperation[] = [
    { op: 'set_z_order', entity: op.entity, key: op.key, z_order: was },
  ];
  if (op.entity === 'location') {
    const next = { ...plan.locations[op.key], z_order: op.z_order };
    return { plan: { ...plan, locations: replaceEntry(plan.locations, op.key, next) }, inverse };
  }
  const next = { ...plan.gardenObjects[op.key], z_order: op.z_order };
  return {
    plan: { ...plan, gardenObjects: replaceEntry(plan.gardenObjects, op.key, next) },
    inverse,
  };
}

// ── public API ───────────────────────────────────────────────────────────────

/**
 * Apply one operation to `plan`.
 *
 * @throws PlanOperationError when the model refuses it (unknown key, duplicate temp key, locked).
 */
export function applyOperation(plan: PlanModel, op: PlanOperation): AppliedOperation {
  switch (op.op) {
    case 'create_location':
      return createLocation(plan, op);
    case 'create_garden_object':
      return createGardenObject(plan, op);
    case 'update_geometry':
      return updateGeometry(plan, op);
    case 'update_fields':
      return updateFields(plan, op);
    case 'delete':
      return deleteEntity(plan, op);
    case 'set_boundary':
      return setBoundary(plan, op);
    case 'set_locked':
      return setLocked(plan, op);
    case 'set_z_order':
      return setZOrder(plan, op);
    default:
      throw new PlanOperationError('operation.unsupported', (op as { op: PlanOperation['op'] }).op);
  }
}

/**
 * Apply the operations of one user action in order (GP-FR-155: one action = one undo step). The
 * inverse undoes them in reverse order; it is `null` when any step has none. All or nothing: a
 * refused operation leaves `plan` untouched.
 */
export function applyOperations(plan: PlanModel, ops: readonly PlanOperation[]): AppliedOperation {
  let current = plan;
  const inverses: (PlanOperation[] | null)[] = [];
  for (const op of ops) {
    const applied = applyOperation(current, op);
    current = applied.plan;
    inverses.push(applied.inverse);
  }
  const inverse = inverses.every((entry) => entry !== null)
    ? (inverses as PlanOperation[][]).reverse().flat()
    : null;
  return { plan: current, inverse };
}

/**
 * Rewrite the keys of existing entities in `op` after a save assigned real keys to temp keys
 * (`key_map`). `temp_key` of a create is left alone: it names a new object, not an existing one.
 */
export function remapOperationKeys(
  op: PlanOperation,
  keyMap: Readonly<Record<string, string>>,
): PlanOperation {
  switch (op.op) {
    case 'create_location':
    case 'create_garden_object': {
      const parent = op.data.parent_location_key;
      if (parent == null || keyMap[parent] === undefined) return op;
      return { ...op, data: { ...op.data, parent_location_key: keyMap[parent] } } as PlanOperation;
    }
    case 'update_geometry':
    case 'update_fields':
    case 'delete':
    case 'set_locked':
    case 'set_z_order':
      return keyMap[op.key] === undefined ? op : { ...op, key: keyMap[op.key] };
    default:
      return op;
  }
}
