/**
 * Wire types of the planting dialog (REQ-053 WP 3.6), derived from `app/api/v1/locations/schemas.py`
 * (preview GP-API-016, plantings GP-API-024, validate-planting GP-API-025) and `slots/schemas.py`.
 */
import type { LayoutStrategy, RowDirection } from '../model/layout';
import type { Point, SlotRole } from '../model/types';

/** A slot geometry in the bed frame (§9.2). */
export type BedFrameGeometry =
  | { kind: 'point'; origin: Point }
  | { kind: 'polygon'; points: Point[] };

/** Body of `POST /locations/{key}/planting-layout/preview`: the layout fields of one entry (cm). */
export interface PreviewEntry {
  layout_strategy: LayoutStrategy;
  spacing_cm: number;
  row_spacing_cm?: number | null;
  row_direction?: RowDirection;
  edge_margin_along_cm?: number | null;
  edge_margin_across_cm?: number | null;
  row_assignment?: number[] | null;
  mature_width_cm?: number | null;
  max_count?: number | null;
}

export interface PreviewSlot {
  slot_role: SlotRole;
  geometry: BedFrameGeometry;
  row_index: number | null;
  sequence: number;
  capacity_plants: number;
}

export interface PreviewWarning {
  code: string;
  detail: Record<string, number>;
}

export interface PreviewResponse {
  slots: PreviewSlot[];
  count: number;
  capacity_max: number;
  warnings: PreviewWarning[];
}

export type RotationSeverity = 'OK' | 'INFO' | 'WARNING' | 'CRITICAL';

export interface RotationFinding {
  severity: RotationSeverity;
  code: string;
  message: string;
  family_key?: string | null;
  /** Name of the family; `null` when the catalogue has none. Never show `family_key` in its place. */
  family_name?: string | null;
  species_key?: string | null;
  last_year?: number | null;
  years_since?: number | null;
  pause_years?: number | null;
  pause_source?: 'species' | 'family' | 'default' | null;
  plan_role?: string | null;
}

export interface NeighbourHint {
  severity: RotationSeverity;
  code: string;
  message: string;
  species_key: string;
  slot_keys: string[];
  score?: number | null;
}

/** Answer of `POST /locations/{key}/validate-planting`: hints with a strength, never a blocker (D-09). */
export interface ValidatePlantingResponse {
  location_key: string;
  species_key: string;
  severity: RotationSeverity;
  rotation_applicable: boolean;
  not_applicable_reason?: string | null;
  rotation_window_years: number;
  rotation_reset_at?: string | null;
  rotation: RotationFinding[];
  neighbour_scope: 'slot' | 'bed';
  neighbours: NeighbourHint[];
}

export type PlantingState = 'planned' | 'active' | 'harvested' | 'historical';

/** One line of `GET /locations/{key}/plantings` (§11.3). */
export interface PlantingItem {
  state: PlantingState;
  slot_key?: string | null;
  slot_id?: string | null;
  species_key: string;
  cultivar_key?: string | null;
  plant_key?: string | null;
  instance_id?: string | null;
  run_key?: string | null;
  entry_key?: string | null;
  sequence?: number | null;
  planted_on?: string | null;
  removed_on?: string | null;
  termination_type?: string | null;
  planned_from?: string | null;
  reason?: string | null;
  /** Role of the slot of a planned position (`row`/`zone` can be sown, W-015). */
  slot_role?: SlotRole | null;
  /** Day a planned row or zone was sown (§11.3 "gesät"); `null` when not sown. */
  sown_at?: string | null;
}

/** A slot whose newest plant failed (§11.3 "ausgefallen"): free for a replant of the same crop. */
export interface FailedPlanting {
  slotKey: string;
  slotId: string;
  speciesKey: string;
  cultivarKey: string | null;
  removedOn: string | null;
}

/** `GET /slots/{key}/thinning`: what thinning the sown slot would do (REQ-053 §11.3, W-015). */
export interface ThinningPlan {
  slot_key: string;
  slot_id: string;
  slot_role: SlotRole;
  sown_at: string;
  run_key: string;
  entry_key: string;
  species_key: string;
  cultivar_key?: string | null;
  /** `length` (m) for a row, `area` (m²) for a zone; `null` without a geometry. */
  measure_kind?: 'length' | 'area' | null;
  measure_value?: number | null;
  /** The run's spacing after thinning; `null` when the run has none - the grower enters one (no default). */
  thinning_to_cm?: number | null;
  suggested_count?: number | null;
  max_count: number;
}

/** Body of `POST /slots/{key}/thinning`: a spacing, or the count of seedlings left standing. */
export interface ThinningBody {
  thinning_to_cm?: number | null;
  count?: number | null;
  planted_on?: string | null;
}

export interface ThinningResult {
  plant_keys: string[];
  instance_ids: string[];
  care_event_key: string;
}

export interface QuickPlantingBody {
  species_key: string;
  cultivar_key?: string | null;
  quantity: number;
  planted_on?: string | null;
  name?: string | null;
  id_prefix?: string | null;
  spacing_cm?: number | null;
  row_spacing_cm?: number | null;
  row_direction?: RowDirection | null;
  layout_strategy?: Exclude<LayoutStrategy, 'zone' | 'free'> | null;
  rotation_override_reason?: string | null;
}

export interface QuickPlantingResponse {
  run_key: string;
  entry_key: string;
  slot_keys: string[];
  plant_keys: string[];
  instance_ids: string[];
  warnings: string[];
}

export interface SlotBatchItem {
  slot_id: string;
  slot_role?: SlotRole;
  geometry: BedFrameGeometry;
  capacity_plants?: number;
  row_index?: number | null;
  sequence?: number | null;
  geometry_source?: 'editor' | 'layout' | 'season_copy';
  container_volume_l?: number | null;
  planned_spacing_cm?: number | null;
}

export interface SlotBatchResult {
  created_keys: string[];
  deleted_count: number;
  kept_count: number;
}

/** A slot of a bed as `GET /slots?location_key=` lists it (bed frame). */
export interface SlotRecord {
  key: string;
  slot_id: string;
  location_key: string;
  slot_role?: SlotRole;
  geometry?: BedFrameGeometry | { kind: 'polyline'; points: Point[] } | null;
  archived_at?: string | null;
}
