/**
 * The state of the "record soil analysis" dialog and its translation into the care-event body (REQ-053 §15.1,
 * GP-FR-122). Pure, so the rules are pinned without rendering. A value is sent exactly as typed, with the unit and
 * method the user chose - nothing is converted between methods or units (U-002/U-003).
 */
import { parseQuantity, performedAtProblem, toLocalInput } from '../care/careForm';
import {
  CONTENT_CLASS_PARAMETERS,
  SOIL_CONTENT_CLASSES,
  SOIL_EXTRACTION_METHODS,
  UNITS_BY_PARAMETER,
  type SoilAnalysisBody,
  type SoilAnalysisSource,
  type SoilContentClass,
  type SoilExtractionMethod,
  type SoilMeasurementBody,
  type SoilParameter,
} from './soilAnalysisTypes';
import { EC_METHODS, PH_METHODS, type EcMethod, type PhMethod } from './types';

/** At most this many values in one analysis (`measurements` max 50 on the server; a lab sheet has far fewer). */
export const MAX_ROWS = 20;
const MAX_DEPTH_CM = 1000;

/** The physical range of a parameter; a value outside is a typing error. */
const RANGES: Readonly<Record<SoilParameter, readonly [number, number]>> = {
  ph: [0, 14],
  ec: [0, Number.POSITIVE_INFINITY],
  humus: [0, 100],
  caco3: [0, 100],
  moisture: [0, 100],
  n_min: [0, Number.POSITIVE_INFINITY],
  p: [0, Number.POSITIVE_INFINITY],
  k: [0, Number.POSITIVE_INFINITY],
  mg: [0, Number.POSITIVE_INFINITY],
};

export interface MeasurementRow {
  id: number;
  parameter: SoilParameter;
  value: string;
  unit: string;
  /** `ph_method` (pH), `ec_method` (EC) or the extraction; `''` = not given (only allowed for the extraction). */
  method: string;
  /** A content class the lab stated; only kept for P, K, Mg by CAL from a lab. */
  contentClass: string;
}

export interface SoilAnalysisFormState {
  /** `datetime-local` value (local time). */
  performedAt: string;
  source: SoilAnalysisSource;
  /** Sampling depth in cm, the same for every value of the analysis; `''` = not given. */
  depth: string;
  rows: MeasurementRow[];
}

export type RowError = Partial<Record<'value' | 'method', 'required' | 'number' | 'range'>>;

export interface SoilAnalysisErrors {
  performedAt?: 'future' | 'tooOld' | 'invalid';
  depth?: 'range';
  rows: Record<number, RowError>;
}

/** The method choices of a parameter: pH and EC their own lists, the rest the extraction. */
export function methodsFor(parameter: SoilParameter): readonly string[] {
  if (parameter === 'ph') return PH_METHODS;
  if (parameter === 'ec') return EC_METHODS;
  return SOIL_EXTRACTION_METHODS;
}

/** pH and EC are unreadable without their method (a conductivity is refused by the server without one). */
export function methodRequired(parameter: SoilParameter): boolean {
  return parameter === 'ph' || parameter === 'ec';
}

/** The i18n enum group of a parameter's methods. */
export function methodEnumGroup(parameter: SoilParameter): 'phMethod' | 'ecMethod' | 'soilExtractionMethod' {
  if (parameter === 'ph') return 'phMethod';
  if (parameter === 'ec') return 'ecMethod';
  return 'soilExtractionMethod';
}

/** Whether a content class may be given for this row: a lab value of P, K or Mg by CAL. */
export function contentClassAllowed(row: MeasurementRow, source: SoilAnalysisSource): boolean {
  return source === 'lab' && row.method === 'cal' && CONTENT_CLASS_PARAMETERS.includes(row.parameter);
}

export function emptyRow(id: number, parameter: SoilParameter = 'ph'): MeasurementRow {
  return { id, parameter, value: '', unit: UNITS_BY_PARAMETER[parameter][0], method: '', contentClass: '' };
}

/** A row switched to another parameter: its unit and method lists change, so both start over. */
export function withParameter(row: MeasurementRow, parameter: SoilParameter): MeasurementRow {
  return { ...row, parameter, unit: UNITS_BY_PARAMETER[parameter][0], method: '', contentClass: '' };
}

export function emptySoilAnalysisForm(now: Date = new Date()): SoilAnalysisFormState {
  return { performedAt: toLocalInput(now), source: 'lab', depth: '', rows: [emptyRow(1)] };
}

function rowError(row: MeasurementRow): RowError {
  const error: RowError = {};
  if (row.value.trim() === '') error.value = 'required';
  else {
    const value = parseQuantity(row.value);
    const [low, high] = RANGES[row.parameter];
    if (value === null) error.value = 'number';
    else if (value < low || value > high) error.value = 'range';
  }
  if (methodRequired(row.parameter) && !methodsFor(row.parameter).includes(row.method)) error.method = 'required';
  return error;
}

/** Field problems as i18n keys; `hasErrors` says whether the form may be sent. */
export function validateSoilAnalysis(state: SoilAnalysisFormState, now: Date): SoilAnalysisErrors {
  const errors: SoilAnalysisErrors = { rows: {} };
  const problem = performedAtProblem(state.performedAt, now);
  if (problem) errors.performedAt = problem;
  if (state.depth.trim() !== '') {
    const depth = parseQuantity(state.depth);
    if (depth === null || depth < 0 || depth > MAX_DEPTH_CM) errors.depth = 'range';
  }
  for (const row of state.rows) {
    const error = rowError(row);
    if (Object.keys(error).length > 0) errors.rows[row.id] = error;
  }
  return errors;
}

export function hasErrors(errors: SoilAnalysisErrors): boolean {
  return errors.performedAt !== undefined || errors.depth !== undefined || Object.keys(errors.rows).length > 0;
}

function measurementOf(row: MeasurementRow, source: SoilAnalysisSource, depth: number | null): SoilMeasurementBody {
  const body: SoilMeasurementBody = {
    parameter: row.parameter,
    value: parseQuantity(row.value) ?? 0,
    unit: row.unit,
    source,
  };
  if (depth !== null) body.sample_depth_cm = depth;
  if (row.parameter === 'ph') body.ph_method = row.method as PhMethod;
  else if (row.parameter === 'ec') body.ec_method = row.method as EcMethod;
  else if ((SOIL_EXTRACTION_METHODS as readonly string[]).includes(row.method)) {
    body.extraction_method = row.method as SoilExtractionMethod;
  }
  if (contentClassAllowed(row, source) && (SOIL_CONTENT_CLASSES as readonly string[]).includes(row.contentClass)) {
    body.content_class = row.contentClass as SoilContentClass;
  }
  return body;
}

/** The care-event body of a valid form; `summary` is the line the history shows. */
export function buildSoilAnalysisBody(
  bedKey: string,
  state: SoilAnalysisFormState,
  summary: string,
): SoilAnalysisBody {
  const depth = state.depth.trim() === '' ? null : parseQuantity(state.depth);
  return {
    location_key: bedKey,
    category: 'soil_analysis',
    summary,
    performed_at: new Date(state.performedAt).toISOString(),
    measurements: state.rows.map((row) => measurementOf(row, state.source, depth)),
  };
}
