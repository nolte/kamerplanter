/**
 * Bed read model (REQ-053 WP 3.5): the bed list row (GP-API-011), the summary that heads the bed view
 * (GP-API-012) and the soil profile (GP-FR-120/121). Derived from `app/api/v1/locations/schemas.py`.
 */
import type { BedStatus, Geometry, SunExposure, SunWindow } from '../model/types';

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
export type SoilDrainage = 'poor' | 'moderate' | 'good' | 'unknown';
export type SiteWaterRegime = 'dry' | 'fresh' | 'moist' | 'wet' | 'unknown';
export type SoilCondition = 'compacted' | 'depleted' | 'waterlogged' | 'crusting' | 'stony';
export type PhMethod = 'cacl2' | 'h2o' | 'probe_unknown';

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
  humus_percent?: number | null;
  notes?: string | null;
}

/**
 * The sun profile of a bed (GP-FR-158/159, `Location.site_conditions.sun_profile`). Nothing here is
 * computed (§29): the values are what a person entered. `source` is read-only for this UI.
 */
export interface SunProfile {
  sun_window?: SunWindow;
  direct_sun_hours_summer?: number | null;
  foliage_shade_in_summer?: boolean;
  source?: 'manual' | 'computed';
}

/** What the sun profile editors send: only the keys that changed (the server merges them per key). */
export type SunProfilePatch = Pick<SunProfile, 'sun_window' | 'direct_sun_hours_summer' | 'foliage_shade_in_summer'>;

/** The slice of `Location.site_conditions` this UI reads; the other parts are carried untouched. */
export interface SiteConditionsSlice {
  sun_profile?: SunProfile;
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
  active_plant_count?: number | null;
  open_task_count?: number | null;
  overdue_task_count?: number | null;
  next_due_at?: string | null;
}

/** `GET /locations/{key}/summary`: the location document plus its derived head data. */
export interface BedSummary extends BedListItem {
  is_bed: boolean;
  season_state: string;
  active_plant_count: number;
  species_keys: string[];
  open_task_count: number;
  overdue_task_count: number;
  next_due_at: string | null;
  last_care_at: string | null;
  soil_profile?: SoilProfile | null;
  notes?: string | null;
  description?: string | null;
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
