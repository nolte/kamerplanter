/**
 * Soil analyses (REQ-053 §15.1, GP-FR-122): the measurement a `soil_analysis` care event carries and the series
 * `GET /locations/{key}/soil-analyses` answers. Derived from `app/domain/models/care_event.py` (`Measurement`) and
 * `app/api/v1/locations/schemas.py` (`SoilAnalysesResponse`).
 */
import type { EcMethod, PhMethod } from './types';

/** The parameters a soil measurement may carry (`Measurement.parameter`). */
export type SoilParameter = 'ph' | 'ec' | 'n_min' | 'p' | 'k' | 'mg' | 'humus' | 'caco3' | 'moisture';
export const SOIL_PARAMETERS: readonly SoilParameter[] = [
  'ph',
  'ec',
  'humus',
  'caco3',
  'n_min',
  'p',
  'k',
  'mg',
  'moisture',
];

/** Where a value comes from (§15.1). */
export type SoilAnalysisSource = 'lab' | 'test_kit' | 'sensor';
export const SOIL_ANALYSIS_SOURCES: readonly SoilAnalysisSource[] = ['lab', 'test_kit', 'sensor'];

/** The extraction of a nutrient value (§15.1); pH and EC carry their own method instead. */
export type SoilExtractionMethod = 'cal' | 'ammonium_acetate' | 'saturated_paste' | 'quick_test' | 'sensor';
export const SOIL_EXTRACTION_METHODS: readonly SoilExtractionMethod[] = [
  'cal',
  'ammonium_acetate',
  'saturated_paste',
  'quick_test',
  'sensor',
];

/** A CAL content class, only taken over from a lab result for P, K or Mg - never computed. */
export type SoilContentClass = 'A' | 'B' | 'C' | 'D' | 'E';
export const SOIL_CONTENT_CLASSES: readonly SoilContentClass[] = ['A', 'B', 'C', 'D', 'E'];
export const CONTENT_CLASS_PARAMETERS: readonly SoilParameter[] = ['p', 'k', 'mg'];

/**
 * The units offered per parameter. pH, EC (`mS/cm` = `dS/m`), humus and lime in the profile's own unit, so the
 * server can take the value into the profile; nothing is converted (U-002/U-003).
 */
export const UNITS_BY_PARAMETER: Readonly<Record<SoilParameter, readonly string[]>> = {
  ph: ['pH'],
  ec: ['mS/cm', 'dS/m'],
  humus: ['%'],
  caco3: ['%'],
  n_min: ['kg_n_per_ha'],
  p: ['mg_per_100g', 'mg_per_l'],
  k: ['mg_per_100g', 'mg_per_l'],
  mg: ['mg_per_100g', 'mg_per_l'],
  moisture: ['%'],
};

/** One measurement on the wire (`Measurement`, `extra="forbid"`). */
export interface SoilMeasurementBody {
  parameter: SoilParameter;
  value: number;
  unit: string;
  source: SoilAnalysisSource;
  sample_depth_cm?: number;
  extraction_method?: SoilExtractionMethod;
  ph_method?: PhMethod;
  ec_method?: EcMethod;
  content_class?: SoilContentClass;
}

/** `POST /care-events` for a soil analysis. */
export interface SoilAnalysisBody {
  location_key: string;
  category: 'soil_analysis';
  summary: string;
  performed_at: string;
  measurements: SoilMeasurementBody[];
}

export interface SoilAnalysisPoint {
  performed_at: string;
  value: number;
  unit: string;
  source: string;
  sample_depth_cm: number | null;
  content_class: string | null;
  event_key: string;
}

export interface SoilAnalysisSeries {
  parameter: string;
  /** `ec_method` of a conductivity, `ph_method` of a pH, else the extraction; `unknown` is its own method. */
  method: string;
  points: SoilAnalysisPoint[];
}

export interface SoilMethodChange {
  parameter: string;
  at: string;
  from_method: string;
  to_method: string;
}

export type LimingStatus = 'likely' | 'not_indicated' | 'not_assessable';
export type LimingReason =
  | 'below_target'
  | 'at_or_above_target'
  | 'no_ph'
  | 'not_native_soil'
  | 'ph_method_not_cacl2'
  | 'texture_unknown'
  | 'no_target_ph';

/** "Liming likely", derived by the server from method + texture + stated target pH - never an amount. */
export interface LimingHint {
  status: LimingStatus;
  reason: LimingReason;
}

export interface SoilAnalysesResponse {
  location_key: string;
  series: SoilAnalysisSeries[];
  method_changes: SoilMethodChange[];
  analyses: number;
  truncated: boolean;
  liming_hint: LimingHint;
}

/** The parameters the history chart shows (GP-FR-122). */
export const CHART_PARAMETERS = ['ph', 'ec', 'humus'] as const;
export type ChartParameter = (typeof CHART_PARAMETERS)[number];
