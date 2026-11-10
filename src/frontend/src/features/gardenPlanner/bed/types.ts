/**
 * Bed read model (REQ-053 WP 3.5): the bed list row (GP-API-011), the summary that heads the bed view
 * (GP-API-012) and the soil profile (GP-FR-120/121). Derived from `app/api/v1/locations/schemas.py`.
 */
import type {
  BedStatus,
  FrostRisk,
  Geometry,
  PlanSunProfile,
  PlanSunProfilePatch,
  SoilDrainage,
  SunExposure,
  WindExposure,
} from '../model/types';
import type { PathAccessClass } from '../model/reach';

/** Stored heat of a wall or building at a bed (`HeatRetention` of the backend, GP-FR-162). */
export type HeatRetention = 'none' | 'wall' | 'building' | 'unknown';
/** The side of a bed it is tended from (`AccessSide`, GP-FR-168). */
export type AccessSide = 'N' | 'E' | 'S' | 'W';
/**
 * Competition at a bed under or beside woody plants (GP-FR-165, `SiteFlag` of the backend): a note the grower
 * sets by hand. Nothing is computed from it and it never enters `site_fit` (§29).
 */
export type SiteFlag = 'root_competition' | 'allelopathy_risk';

export type { SoilDrainage };

export type GrowingMediumKind =
  | 'native_soil'
  | 'raised_bed_mix'
  | 'potting_mix'
  | 'mineral_substrate'
  | 'other';
export type SoilTexture =
  | 'sand'
  | 'loamy_sand'
  | 'sandy_loam'
  | 'loam'
  | 'silt_loam'
  | 'clay_loam'
  | 'clay'
  | 'unknown';
export type SiteWaterRegime = 'dry' | 'fresh' | 'moist' | 'wet' | 'unknown';
export type SoilCondition = 'compacted' | 'depleted' | 'waterlogged' | 'crusting' | 'stony';
export type PhMethod = 'cacl2' | 'h2o' | 'probe_unknown';
/** How a soil conductivity was measured (`EcMethod`, U-002); `unknown` is comparable with nothing. */
export type EcMethod = 'saturated_paste' | 'ratio_1_2' | 'ratio_1_5' | 'sensor' | 'unknown';

export const GROWING_MEDIUM_KINDS: readonly GrowingMediumKind[] = [
  'native_soil',
  'raised_bed_mix',
  'potting_mix',
  'mineral_substrate',
  'other',
];
export const SOIL_TEXTURES: readonly SoilTexture[] = [
  'sand',
  'loamy_sand',
  'sandy_loam',
  'loam',
  'silt_loam',
  'clay_loam',
  'clay',
  'unknown',
];
export const SOIL_DRAINAGES: readonly SoilDrainage[] = ['poor', 'moderate', 'good', 'unknown'];
export const SITE_WATER_REGIMES: readonly SiteWaterRegime[] = [
  'dry',
  'fresh',
  'moist',
  'wet',
  'unknown',
];
export const SOIL_CONDITIONS: readonly SoilCondition[] = [
  'compacted',
  'depleted',
  'waterlogged',
  'crusting',
  'stony',
];
export const PH_METHODS: readonly PhMethod[] = ['cacl2', 'h2o', 'probe_unknown'];
export const EC_METHODS: readonly EcMethod[] = ['saturated_paste', 'ratio_1_2', 'ratio_1_5', 'sensor', 'unknown'];

/** The v1 soil profile of a bed; everything optional, nothing invented (E-10). */
export interface SoilProfile {
  growing_medium_kind?: GrowingMediumKind | null;
  soil_texture: SoilTexture;
  drainage: SoilDrainage;
  site_water_regime: SiteWaterRegime;
  conditions: SoilCondition[];
  substrate_key?: string | null;
  ph?: number | null;
  ph_method?: PhMethod | null;
  ec_ms_cm?: number | null;
  /** Required by the server as soon as `ec_ms_cm` is set (U-002). */
  ec_method?: EcMethod | null;
  humus_percent?: number | null;
  caco3_percent?: number | null;
  stone_content_class?: 'none' | 'few' | 'many' | 'unknown';
  /** As stated (e.g. by a lab), measured in CaCl2; never derived from the texture (E-10). */
  target_ph?: number | null;
  established_on?: string | null;
  /** Server-owned: the `performed_at` of the newest analysis in the profile; sent back as received. */
  last_analysis_at?: string | null;
  rotation_reset_at?: string | null;
  notes?: string | null;
}

/**
 * The sun profile of a bed (GP-FR-158/159, `Location.site_conditions.sun_profile`). Nothing here is
 * computed (§29): the values are what a person entered. `source` is read-only for this UI.
 */
export interface SunProfile extends PlanSunProfile {
  source?: 'manual' | 'computed';
}

/** What the sun profile editors send: only the keys that changed (the server merges them per key). */
export type SunProfilePatch = PlanSunProfilePatch;

/** The slice of `Location.site_conditions` this UI reads; the other parts are carried untouched. */
export interface SiteConditionsSlice {
  sun_profile?: SunProfile;
  /** The frost risk and the wind load the planting dialog's site hints read (GP-FR-161). */
  microclimate?: { frost_risk?: FrostRisk; cold_air_pocket?: boolean; heat_retention?: HeatRetention };
  wind_exposure?: WindExposure;
  slope_deg?: number | null;
  aspect_deg?: number | null;
  access_sides?: AccessSide[];
  /** Root competition / allelopathy reported at the bed (GP-FR-165); no repeats (the server answers 422). */
  flags?: SiteFlag[];
}

/**
 * What the site-conditions editors send: only the keys that changed, per part (`PATCH /locations/{key}` merges
 * them into the stored value; an unknown key is a 422). A frost-risk change moves the legacy `frost_exposed`
 * with it on the server (#2512), so the client never sends that field.
 */
export interface SiteConditionsPatch {
  microclimate?: { frost_risk?: FrostRisk; cold_air_pocket?: boolean; heat_retention?: HeatRetention };
  wind_exposure?: WindExposure;
  slope_deg?: number | null;
  aspect_deg?: number | null;
  access_sides?: AccessSide[];
  /** Root competition / allelopathy reported at the bed (GP-FR-165); no repeats (the server answers 422). */
  flags?: SiteFlag[];
}

/** One row of `GET /locations?site_key=&is_bed=true` (counters are `null` on a plain listing). */
export interface BedListItem {
  key: string;
  name: string;
  site_key: string;
  parent_location_key?: string | null;
  location_type_key: string;
  area_m2: number;
  geometry?: Geometry | null;
  bbox?: [number, number, number, number] | null;
  bed_status: BedStatus;
  sun_exposure: SunExposure;
  site_conditions?: SiteConditionsSlice | null;
  /** Carried by the location document; only the drainage is read on a listing (GP-FR-161). */
  soil_profile?: SoilProfile | null;
  active_plant_count?: number | null;
  open_task_count?: number | null;
  overdue_task_count?: number | null;
  next_due_at?: string | null;
  /** The bed's cover photo, an attachment id (GP-FR-051); `null` without one. The gallery is `GET .../photos`. */
  cover_photo_ref?: string | null;
  /**
   * GP-FR-167: metres from the bed's edge to the nearest water source of its site, derived on the server
   * (`geometry_distance.nearest_water_source_m`) - the same value in the list, the summary and the CSV. `null` for a
   * location that is no bed (or a plain listing), without a geometry or without a water source.
   */
  nearest_water_source_m?: number | null;
}

/** `GET /locations/{key}/summary`: the location document plus its derived head data. */
/** The nutrient hint of a bed (GP-FR-125, WP 8.10): a state with reason codes, never a number. */
export type NutrientHintState = 'ok' | 'check' | 'likely_deficit' | 'insufficient_data';
export type NutrientHintConfidence = 'low' | 'medium' | 'high';
/** Mirrors `NutrientHintReason` of `app/domain/models/nutrient_hint.py`; additive only. */
export type NutrientHintReason =
  | 'substrate_bed'
  | 'no_current_crop'
  | 'species_not_readable'
  | 'demand_unknown'
  | 'thresholds_without_source'
  | 'no_feeding_recorded'
  | 'feeding_overdue'
  | 'feeding_due'
  | 'fed_recently'
  | 'p_class_low'
  | 'k_class_low'
  | 'content_classes_sufficient'
  | 'demand_partly_unknown'
  | 'preceding_nitrogen_fixer'
  | 'standing_nitrogen_fixer'
  | 'bark_mulch_n_binding'
  | 'p_or_k_class_high'
  | 'check_salt_content';

export interface NutrientHint {
  state: NutrientHintState;
  confidence: NutrientHintConfidence;
  reasons: NutrientHintReason[];
  /** P or K in lab class D/E: compost serves no nutrient supply there, the hint never points to compost or P. */
  compost_and_p_withheld: boolean;
  sources: string[];
  /** The source of the D/E rule (R-006) when it applied. */
  withheld_source?: string | null;
}

export interface BedSummary extends BedListItem {
  is_bed: boolean;
  /**
   * GP-FR-166 (#2703): the access the site's paths give the bed, derived on the server
   * (`reach_calculator.path_access`, within the site's `path_access_max_distance_m`): `both` | `one` | `none`; `null`
   * (or absent, an older backend) for a location that is no bed or has no geometry. Joins `access_sides`.
   */
  path_access?: PathAccessClass | null;
  season_state: string;
  active_plant_count: number;
  species_keys: string[];
  open_task_count: number;
  overdue_task_count: number;
  next_due_at: string | null;
  last_care_at: string | null;
  soil_profile?: SoilProfile | null;
  /** Permanent crop: the rotation check is off whatever `rotation_enabled` says (GP-FR-137). */
  rotation_exempt?: boolean;
  /** The bed's own switch: `null` = default of the bed type, `true` on, `false` off (#2544). */
  rotation_enabled?: boolean | null;
  notes?: string | null;
  description?: string | null;
  /** GP-FR-125: only on a bed; `null` for every other location. */
  nutrient_hint?: NutrientHint | null;
}

/** The document `PATCH /locations/{key}` and `POST /locations/{key}/status` answer with. */
export interface BedPatchResult {
  key: string;
  bed_status: BedStatus;
  soil_profile?: SoilProfile | null;
  plan_revision: number;
}

/** Members and their beds (`location_assignments`, GP-FR-050): who is responsible, not who may write. */
export interface BedAssignee {
  membershipKey: string;
  userKey: string;
  displayName: string;
}
