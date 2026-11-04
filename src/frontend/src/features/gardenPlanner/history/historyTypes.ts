/**
 * Wire types of the bed history (REQ-053 WP 4.5). Derived from the served contracts:
 * `app/api/v1/locations/schemas.py` (`BedHistoryItemResponse`, `RotationTimelineResponse`, `BackfillRequest`)
 * and `app/api/v1/care_events/schemas.py` (`CareEventResponse`).
 */

export type HistoryKind = 'care_event' | 'plant_planted' | 'plant_removed' | 'run_started' | 'run_completed';

export type PlanRole = 'main_crop' | 'green_manure' | 'fallow';
export type Season = 'spring' | 'main' | 'autumn';

/** The slice of `CareEventResponse` the lists show. Account keys never reach the client; names do. */
export interface CareEventLine {
  key: string;
  location_key: string;
  plant_keys: string[];
  /** Readable names of `plant_keys` in their order; a plant that is gone is left out (#2514). */
  plant_names: string[];
  category: string;
  /** Stored as written (audit, export); some categories are worded by the client instead (`itemHeadline`). */
  summary: string;
  performed_at: string;
  /** Display name, the third party's label, or `anonymisiert`. */
  performed_by: string | null;
  performed_by_label: string | null;
  created_by_me: boolean;
  trigger: string;
  reason: string | null;
  product_label: string | null;
  quantity: number | null;
  unit: string | null;
  material: string | null;
  observed_outcome: string | null;
  supersedes_key: string | null;
  superseded_by_key: string | null;
  voided_at: string | null;
  void_reason: string | null;
  redacted_at: string | null;
}

/** One line of `GET /locations/{key}/history` (GP-API-038). */
export interface HistoryItem {
  id: string;
  kind: HistoryKind;
  at: string;
  /** The care category, or `planting` / `removal` for a derived plant or run event. */
  category: string;
  care_event: CareEventLine | null;
  plant_key: string | null;
  species_key: string | null;
  plant_name: string | null;
  termination_type: string | null;
  run_key: string | null;
  run_name: string | null;
  run_status: string | null;
}

/** One entry of a year of `GET /locations/{key}/rotation` (GP-API-039). */
export interface RotationPlanting {
  season: Season | null;
  family_key: string | null;
  family_name: string | null;
  species_key: string | null;
  nutrient_demand: string | null;
  plan_role: PlanRole;
  source: 'plant' | 'backfill';
  /** The backfill event; cancel it with `DELETE …/history/backfill/{key}`. */
  care_event_key: string | null;
}

export interface RotationYear {
  year: number;
  plantings: RotationPlanting[];
}

export interface RotationTimeline {
  location_key: string;
  years: number;
  rotation_applicable: boolean;
  not_applicable_reason: string | null;
  rotation_reset_at: string | null;
  timeline: RotationYear[];
}

/** One row of `GET /sites/{key}/rotation-matrix` (GP-FR-135): a bed and one cell per column, oldest year first. */
export interface RotationMatrixBed {
  location_key: string;
  name: string;
  rotation_applicable: boolean;
  not_applicable_reason: string | null;
  rotation_reset_at: string | null;
  cells: RotationYear[];
}

/** `GET /sites/{key}/rotation-matrix` (GP-FR-135): beds x years; a cell is the year of `/locations/{key}/rotation`. */
export interface RotationMatrix {
  site_key: string;
  years: number;
  /** The years, oldest first; the current year is the last. */
  columns: number[];
  /** Beds the matrix reads (at most 500). */
  total: number;
  truncated: boolean;
  offset: number;
  limit: number;
  beds: RotationMatrixBed[];
}

export type SuccessionStatus =
  | 'ok'
  | 'not_applicable'
  | 'no_history'
  | 'demand_unknown'
  | 'no_successor_data'
  | 'no_matching_species';

export type SuccessionTarget = 'heavy_feeder' | 'medium_feeder' | 'light_feeder' | 'restoring';

export interface SuccessionSpecies {
  species_key: string;
  scientific_name: string;
  common_name: string | null;
  nutrient_demand: string | null;
  nitrogen_fixing: boolean | null;
}

export interface SuccessionFamily {
  family_key: string;
  family_name: string | null;
  benefit_score: number | null;
  benefit_reason: string | null;
  pause_years: number | null;
  species: SuccessionSpecies[];
}

export interface SuccessionHeldBack {
  family_key: string;
  family_name: string | null;
  last_year: number;
  pause_years: number;
}

/** `GET /locations/{key}/succession-recommendation` (GP-FR-133): the next step of the feeder cycle. Order only, no amounts. */
export interface SuccessionRecommendation {
  location_key: string;
  rotation_applicable: boolean;
  not_applicable_reason: string | null;
  status: SuccessionStatus;
  previous: {
    year: number;
    step: 'main_crop' | 'restoring';
    nutrient_demand: string | null;
    family_keys: string[];
  } | null;
  target: SuccessionTarget | null;
  families: SuccessionFamily[];
  held_back: SuccessionHeldBack[];
  fallow_option: boolean;
}

/** `POST /locations/{key}/history/backfill` (GP-API-042). */
export interface BackfillBody {
  year: number;
  season?: Season;
  species_key?: string;
  family_key?: string;
  plan_role: PlanRole;
}

export interface BackfillResult {
  care_event_key: string;
  year: number;
}

/** A bed, a plant or a member the filters can name. */
export interface FilterOption {
  key: string;
  label: string;
}
