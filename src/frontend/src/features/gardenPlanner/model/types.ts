/**
 * Garden plan DTO v1 (REQ-053 §20.1, §21.1, §21.3; `schema_version: "1"`).
 *
 * Derived from the backend schemas, not guessed:
 * `app/api/v1/garden_plan/schemas.py`, `app/domain/models/{geometry,garden_plan,garden_object}.py`,
 * `app/api/v1/garden_objects/schemas.py`. Where the backend leaves a field out of the wire at its
 * default (`response_model_exclude_none`, GP-NFR-031) the field is optional here.
 *
 * Lengths are metres, angles degrees counter-clockwise about +x (§9.2).
 */

import type { PlanZone } from '../zones/zoneTypes';

/** The only plan DTO version this client reads (GP-API-001 `schema_version`). */
export const PLAN_SCHEMA_VERSION = '1';

/** Operations per batch (V-17, GP-API-003). */
export const MAX_BATCH_OPERATIONS = 500;

/** Locations plus garden objects per site (GP-NFR-017, SR-004); beyond it the server answers 422 `plan.quota_exceeded`. */
export const MAX_PLAN_OBJECTS_PER_SITE = 500;

/** `[x, y]` in metres. */
export type Point = [number, number];

/** `[min_x, min_y, max_x, max_y]` in the frame of the geometry (GP-FR-007). */
export type BoundingBox = [number, number, number, number];

// ── Geometry (§20.1) ─────────────────────────────────────────────────────────

export type GeometryKind = 'rect' | 'circle' | 'polygon' | 'polyline' | 'point';

/** `origin` is the lower-left corner before rotation; the rotation pivots about it. */
export interface RectGeometry {
  kind: 'rect';
  origin: Point;
  width_m: number;
  length_m: number;
  rotation_deg: number;
}

/** `origin` is the centre. A circle has no rotation. */
export interface CircleGeometry {
  kind: 'circle';
  origin: Point;
  radius_m: number;
}

/** 3..200 vertices, the closing edge is implicit; the first vertex is the anchor. */
export interface PolygonGeometry {
  kind: 'polygon';
  points: Point[];
  rotation_deg: number;
}

/** 2..200 vertices with a stroke width. */
export interface PolylineGeometry {
  kind: 'polyline';
  points: Point[];
  width_m: number;
}

export interface PointGeometry {
  kind: 'point';
  origin: Point;
}

export type Geometry =
  RectGeometry | CircleGeometry | PolygonGeometry | PolylineGeometry | PointGeometry;

// ── Enums of the read model ──────────────────────────────────────────────────

export type BedStatus = 'planned' | 'active' | 'retired';
export type SunExposure = 'full_sun' | 'partial_shade' | 'shade' | 'deep_shade' | 'unknown';

/** When the direct sun reaches a bed (GP-FR-158, `SunWindow` of the backend). */
export type SunWindow = 'morning' | 'midday' | 'afternoon' | 'all_day' | 'mixed' | 'unknown';
/** Frost risk of one bed (GP-FR-162, `FrostRisk` of the backend). */
export type FrostRisk = 'low' | 'normal' | 'high' | 'unknown';
/** How well a bed drains (§15.1, `SoilDrainage` of the backend). */
export type SoilDrainage = 'poor' | 'moderate' | 'good' | 'unknown';
export type SlotRole = 'position' | 'row' | 'zone';

export type GardenObjectType =
  | 'path'
  | 'lawn'
  | 'tree'
  | 'shrub'
  | 'building'
  | 'wall'
  | 'fence'
  | 'trellis'
  | 'water_source'
  | 'compost'
  | 'storage'
  | 'other'
  | 'window'
  | 'door'
  | 'furniture'
  | 'lamp';

export type PathSurface = 'gravel' | 'paving' | 'bark' | 'grass' | 'other';
export type FoliageType = 'deciduous' | 'evergreen';
export type ObstacleOpacity = 'opaque' | 'semi' | 'open';
export type WaterSourceKind = 'tap' | 'rain_barrel' | 'well' | 'pond' | 'cistern' | 'hose_reel';
export type WindowGlazing = 'single' | 'double' | 'unknown';
export type LampKind = 'grow_light' | 'ceiling' | 'floor';

// ── Garden object props (§9.5, §9.8, §20.4) ──────────────────────────────────

export interface PathProps {
  object_type: 'path';
  surface?: PathSurface | null;
}
export interface LawnProps {
  object_type: 'lawn';
}
export interface TreeProps {
  object_type: 'tree';
  species_label?: string | null;
  crown_radius_m: number;
  height_m?: number | null;
  crown_base_height_m?: number | null;
  foliage?: FoliageType | null;
}
export interface ShrubProps {
  object_type: 'shrub';
  height_m?: number | null;
  opacity?: ObstacleOpacity | null;
}
export interface BuildingProps {
  object_type: 'building';
  height_m?: number | null;
  ridge_height_m?: number | null;
}
export interface WallProps {
  object_type: 'wall';
  height_m?: number | null;
  opacity?: ObstacleOpacity | null;
}
export interface FenceProps {
  object_type: 'fence';
  height_m?: number | null;
  opacity?: ObstacleOpacity | null;
}
export interface TrellisProps {
  object_type: 'trellis';
  height_m: number;
}
export interface WaterSourceProps {
  object_type: 'water_source';
  water_source_kind: WaterSourceKind;
  capacity_liters?: number | null;
  last_refilled_at?: string | null;
}
export interface CompostProps {
  object_type: 'compost';
}
export interface StorageProps {
  object_type: 'storage';
}
export interface OtherProps {
  object_type: 'other';
}
export interface WindowProps {
  object_type: 'window';
  sill_height_m?: number | null;
  glazing?: WindowGlazing | null;
}
export interface DoorProps {
  object_type: 'door';
  swing?: string | null;
}
export interface FurnitureProps {
  object_type: 'furniture';
}
export interface LampProps {
  object_type: 'lamp';
  kind: LampKind;
  height_m: number;
  ppfd_ref?: number | null;
}

export type GardenObjectProps =
  | PathProps
  | LawnProps
  | TreeProps
  | ShrubProps
  | BuildingProps
  | WallProps
  | FenceProps
  | TrellisProps
  | WaterSourceProps
  | CompostProps
  | StorageProps
  | OtherProps
  | WindowProps
  | DoorProps
  | FurnitureProps
  | LampProps;

// ── Read model (GP-API-001) ──────────────────────────────────────────────────

/**
 * The sun profile of a bed as the plan carries it (GP-FR-158/159, #2538). The server leaves out what is
 * unknown: an absent `sun_window` is `unknown`, absent hours are "not entered", an absent leaf shade is `false`.
 */
export interface PlanSunProfile {
  sun_window?: SunWindow;
  direct_sun_hours_summer?: number | null;
  foliage_shade_in_summer?: boolean;
}

/** The lean slice of `Location.site_conditions` on the plan: sun profile and frost risk, unknowns absent. */
export interface PlanSiteConditions {
  sun_profile?: PlanSunProfile;
  /** Read only on the plan path: the frost risk is edited on the bed page (`PATCH /locations`). */
  microclimate?: { frost_risk?: FrostRisk };
}

/** The drainage of a bed for the moisture layer; the rest of the soil profile is the bed page's. */
export interface PlanSoilProfile {
  drainage?: SoilDrainage;
}

/** The sun-profile keys `update_fields` may change; only the keys sent are merged by the server. */
export type PlanSunProfilePatch = Pick<PlanSunProfile, 'sun_window' | 'direct_sun_hours_summer' | 'foliage_shade_in_summer'>;

/** A location as the map draws it: geometry, status and counters, no soil profile or notes. */
export interface PlanLocation {
  key: string;
  name: string;
  parent_location_key?: string | null;
  location_type_key: string;
  depth: number;
  /** `null`/absent = not placed on the plan. */
  geometry?: Geometry | null;
  area_m2: number;
  bbox?: BoundingBox | null;
  height_m?: number | null;
  bed_status: BedStatus;
  sun_exposure: SunExposure;
  /** Absent = nothing known (#2538). */
  site_conditions?: PlanSiteConditions | null;
  /** Absent = drainage unknown (#2538). */
  soil_profile?: PlanSoilProfile | null;
  irrigation_zone_key?: string | null;
  locked: boolean;
  z_order: number;
  season_state?: string | null;
  open_task_count: number;
  overdue_task_count: number;
  /** Newest watering of the bed within a year (ISO instant); absent = none. Shown as "days since", never as a need. */
  last_watered_at?: string | null;
  /**
   * Not part of the lean read model: present only after an `update_fields` of this client set them
   * (the single-bed endpoints, GP-API-012, carry them).
   */
  description?: string | null;
  notes?: string | null;
}

export interface GardenObject {
  key: string;
  site_key: string;
  parent_location_key?: string | null;
  object_type: GardenObjectType;
  label: string;
  geometry: Geometry;
  bbox?: BoundingBox | null;
  props: GardenObjectProps;
  off_site: boolean;
  locked: boolean;
  z_order: number;
  notes?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
}

/** A slot geometry in the plan frame, as compact as the wire allows: a point is `{origin}`. */
export interface PlanSlotGeometry {
  /** Absent for a point (the common case). */
  kind?: 'polyline' | 'polygon' | null;
  origin?: Point | null;
  points?: Point[] | null;
  width_m?: number | null;
}

/** Absent `slot_role` = position, absent `capacity_plants` = 1, absent `currently_occupied` = false. */
export interface PlanSlot {
  key: string;
  slot_id: string;
  location_key: string;
  slot_role?: SlotRole | null;
  capacity_plants?: number | null;
  currently_occupied?: boolean | null;
  row_index?: number | null;
  sequence?: number | null;
  plan_geometry?: PlanSlotGeometry | null;
}

export interface PlanPlant {
  key: string;
  instance_id: string;
  species_key: string;
  phase_key?: string | null;
  slot_key?: string | null;
  /** Only for a plant without a slot. */
  location_key?: string | null;
}

/** Two points of the underlay picture (pixels) and the real distance between them (metres): the scale (GP-FR-033). */
export interface UnderlayCalibration {
  p1_px: [number, number];
  p2_px: [number, number];
  distance_m: number;
}

/**
 * The background picture of the plan to trace over (GP-FR-033). `origin` is the plan position (metres) of the
 * picture's top-left pixel, `rotation_deg` turns it counter-clockwise about that pixel. Never part of the export.
 */
export interface PlanUnderlay {
  attachment_key: string;
  calibration: UnderlayCalibration;
  origin: [number, number];
  rotation_deg: number;
  opacity: number;
}

export interface PlanSettings {
  boundary?: Geometry | null;
  north_angle_deg: number;
  default_grid_m: number;
  adjacency_factor: number;
  plan_revision: number;
  plan_updated_at?: string | null;
  /** Display name, never the account key (§22.1). */
  plan_updated_by_name?: string | null;
  /** The background picture to trace over; one per site, the same for every member (GP-FR-033). */
  underlay?: PlanUnderlay | null;
}

export interface GardenPlanResponse {
  schema_version: string;
  site_key: string;
  site_name: string;
  plan_revision: number;
  /** Absent = a site without a garden plan (§20.2). */
  plan?: PlanSettings | null;
  locations: PlanLocation[];
  garden_objects: GardenObject[];
  slots: PlanSlot[];
  plants: PlanPlant[];
  zones: PlanZone[];
}

// ── Plan operations (GP-API-003, closed list) ────────────────────────────────

/** Request-local name of an object created in the same batch; matches `^[A-Za-z0-9_-]{1,40}$`. */
export type TempKey = string;

export type PlanEntity = 'location' | 'garden_object';

export interface CreateLocationData {
  name: string;
  location_type_key: string;
  parent_location_key?: string | null;
  geometry: Geometry;
  height_m?: number | null;
  description?: string | null;
  notes?: string | null;
  sun_exposure?: SunExposure;
  locked?: boolean;
  z_order?: number;
}

export interface CreateGardenObjectData {
  object_type: GardenObjectType;
  label?: string;
  geometry: Geometry;
  /** The discriminator inside may be omitted; the object's `object_type` is it. */
  props?: Record<string, unknown>;
  parent_location_key?: string | null;
  off_site?: boolean;
  locked?: boolean;
  z_order?: number;
  notes?: string | null;
}

/** What `update_fields` may change on a location (structure and geometry have their own operations). */
export interface LocationFieldsPatch {
  name?: string;
  description?: string | null;
  notes?: string | null;
  sun_exposure?: SunExposure;
  height_m?: number | null;
  /** The sun profile only (#2538); the server merges the keys sent and refuses any other part. */
  site_conditions?: { sun_profile?: PlanSunProfilePatch };
}

export interface GardenObjectFieldsPatch {
  label?: string;
  notes?: string | null;
  props?: Record<string, unknown>;
  off_site?: boolean;
}

export interface CreateLocationOp {
  op: 'create_location';
  temp_key: TempKey;
  data: CreateLocationData;
}
export interface CreateGardenObjectOp {
  op: 'create_garden_object';
  temp_key: TempKey;
  data: CreateGardenObjectData;
}
export interface UpdateGeometryOp {
  op: 'update_geometry';
  entity: PlanEntity;
  key: string;
  geometry: Geometry;
}
export interface UpdateLocationFieldsOp {
  op: 'update_fields';
  entity: 'location';
  key: string;
  fields: LocationFieldsPatch;
}
export interface UpdateGardenObjectFieldsOp {
  op: 'update_fields';
  entity: 'garden_object';
  key: string;
  fields: GardenObjectFieldsPatch;
}
export type UpdateFieldsOp = UpdateLocationFieldsOp | UpdateGardenObjectFieldsOp;
export interface DeleteOp {
  op: 'delete';
  entity: PlanEntity;
  key: string;
}
export interface SetBoundaryOp {
  op: 'set_boundary';
  boundary: Geometry;
  north_angle_deg?: number | null;
  default_grid_m?: number | null;
  adjacency_factor?: number | null;
}
export interface SetLockedOp {
  op: 'set_locked';
  entity: PlanEntity;
  key: string;
  locked: boolean;
}
export interface SetZOrderOp {
  op: 'set_z_order';
  entity: PlanEntity;
  key: string;
  z_order: number;
}

export type PlanOperation =
  | CreateLocationOp
  | CreateGardenObjectOp
  | UpdateGeometryOp
  | UpdateFieldsOp
  | DeleteOp
  | SetBoundaryOp
  | SetLockedOp
  | SetZOrderOp;

export type PlanOperationName = PlanOperation['op'];

// ── Batch, boundary and audit (GP-API-002/003/008) ───────────────────────────

export interface PlanBatchRequest {
  expected_revision: number;
  operations: PlanOperation[];
}

export interface DerivedGeometry {
  area_m2?: number | null;
  bbox?: BoundingBox | null;
}

export interface PlanBatchResponse {
  plan_revision: number;
  /** `temp_key` → assigned key. */
  key_map: Record<string, string>;
  updated: string[];
  deleted: string[];
  derived: Record<string, DerivedGeometry>;
}

export interface PlanBoundaryRequest {
  boundary: Geometry;
  north_angle_deg?: number | null;
  default_grid_m?: number | null;
  adjacency_factor?: number | null;
  /** Omitted on the first save of a plan. */
  expected_revision?: number | null;
}

export interface PlanBoundaryResponse {
  plan_revision: number;
  total_area_m2: number;
  boundary?: Geometry | null;
}

export interface PlanAuditEntry {
  revision: number;
  op: string;
  entity: string;
  key: string;
  summary: string;
  at: string;
  changed_by_name?: string | null;
}

// ── Bed templates (§20.12, §21.7; WP 7.8 / 7.9) ──────────────────────────────

/**
 * A bed template as `GET /bed-templates` answers it. `default_geometry` is in the bed frame: the anchor of
 * the shape (lower-left corner of a rectangle, centre of a circle, first vertex of a polygon) sits at the
 * origin. `is_system` marks a global template (the standard sizes of GP-FR-045), which a tenant cannot change.
 */
export interface BedTemplate {
  key: string;
  name: string;
  location_type_key: string;
  default_geometry: Geometry;
  height_m?: number | null;
  recurring_task_templates: string[];
  is_system: boolean;
}

/** `POST /bed-templates`: what "Save as template" sends. */
export interface BedTemplateInput {
  name: string;
  location_type_key: string;
  default_geometry: Geometry;
  height_m?: number;
}

/** `POST /sites/{key}/plan/place-template` (GP-API, §21.7). */
export interface PlaceTemplateRequest {
  template_key: string;
  origin: Point;
  rotation_deg: number;
  expected_revision: number;
}
