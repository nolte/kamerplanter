/**
 * Area doses of the bed care dialog (REQ-053 GP-FR-123, WP 8.9, review acceptance "area dosing").
 *
 * The TypeScript port of `domain/calculators/area_dose_calculator.py`; both run against the operations
 * `area_dose`, `nitrogen_approximation` and `unit_identity` of `garden-plan-vectors.json`.
 *
 * - `areaDoseTotal`: a rate per m² times the bed area. The stored total keeps 3 places (the server
 *   computes it again); the dialog shows whole grams and litres to 0.1. Any other unit, no quantity or a
 *   bed without area has no total (`null`), never a silent 0.
 * - `nitrogenApproximation`: the product's N % on the label times a rate in g/m², as g N/m² (0.1) and
 *   kg N/ha (whole). An approximation, shown as such; no threshold and no seasonal warning (R-004).
 * - `gPerM2ToKgPerHa`, `lPerM2ToMm`: 1 g/m² = 10 kg/ha, 1 L/m² = 1 mm.
 *
 * Rounding is half up on the exact binary value (`toFixed`), the rule of the Python `Decimal` quantisation.
 * Pure. A rate is never derived here from a soil analysis or a feeder class.
 */
import type { CareUnit } from '../care/careTypes';

const AREA_UNITS: ReadonlySet<string> = new Set(['g_per_m2', 'l_per_m2']);
const TOTAL_DECIMALS = 3;
const DISPLAY_DECIMALS = { g: 0, l: 1 } as const;
/** A rate pre-filled from the data sheet and g N/m² are shown to 0.1. */
const RATE_DECIMALS = 1;
const KG_PER_HA_PER_G_PER_M2 = 10;
const MM_PER_L_PER_M2 = 1;

export type TotalUnit = keyof typeof DISPLAY_DECIMALS;

export interface AreaDoseTotal {
  /** Rounded to 0.001, as the server stores it. */
  quantityTotal: number;
  quantityTotalUnit: TotalUnit;
  /** Whole grams or litres to 0.1, as the dialog shows it. */
  displayTotal: number;
}

export interface NitrogenApproximation {
  gNPerM2: number;
  kgNPerHa: number;
}

/** `value` rounded to `decimals` places, ties away from zero on the exact binary value; `-0` becomes `0`. */
export function roundHalfUp(value: number, decimals: number): number {
  return Number(value.toFixed(decimals)) + 0;
}

/** Whether `unit` is a dose per m² of the bed. */
export function isAreaUnit(
  unit: string | null | undefined,
): unit is Extract<CareUnit, 'g_per_m2' | 'l_per_m2'> {
  return unit != null && AREA_UNITS.has(unit);
}

/** A bed area the total can be computed for: finite and above 0. */
export function hasArea(areaM2: number | null | undefined): areaM2 is number {
  return areaM2 != null && Number.isFinite(areaM2) && areaM2 > 0;
}

/** A rate from the product data sheet as the rate field takes it (0.1). */
export function roundRate(rate: number): number {
  return roundHalfUp(rate, RATE_DECIMALS);
}

/** `quantity × areaM2` for an area unit; `null` for any other unit, no quantity or a bed without area. */
export function areaDoseTotal(
  quantity: number | null,
  unit: string | null,
  areaM2: number | null | undefined,
): AreaDoseTotal | null {
  if (quantity === null || !Number.isFinite(quantity) || !isAreaUnit(unit) || !hasArea(areaM2))
    return null;
  const totalUnit: TotalUnit = unit === 'l_per_m2' ? 'l' : 'g';
  const quantityTotal = roundHalfUp(quantity * areaM2, TOTAL_DECIMALS);
  return {
    quantityTotal,
    quantityTotalUnit: totalUnit,
    displayTotal: roundHalfUp(quantityTotal, DISPLAY_DECIMALS[totalUnit]),
  };
}

/** 1 g/m² = 10 kg/ha (unrounded). */
export function gPerM2ToKgPerHa(rateGPerM2: number): number {
  return rateGPerM2 * KG_PER_HA_PER_G_PER_M2;
}

/** 1 L/m² = 1 mm layer (unrounded). */
export function lPerM2ToMm(rateLPerM2: number): number {
  return rateLPerM2 * MM_PER_L_PER_M2;
}

/**
 * `{ gNPerM2, kgNPerHa }` from a rate in g/m² and the N % on the label; `null` without both. N 0 % is
 * the catalogue's "not stated", so a missing label never reads as "no nitrogen".
 */
export function nitrogenApproximation(
  rateGPerM2: number | null,
  nPercent: number | null | undefined,
): NitrogenApproximation | null {
  if (rateGPerM2 === null || !Number.isFinite(rateGPerM2) || rateGPerM2 <= 0) return null;
  if (nPercent == null || !Number.isFinite(nPercent) || nPercent <= 0 || nPercent > 100)
    return null;
  const gNPerM2 = (rateGPerM2 * nPercent) / 100;
  return {
    gNPerM2: roundHalfUp(gNPerM2, RATE_DECIMALS),
    kgNPerHa: roundHalfUp(gPerM2ToKgPerHa(gNPerM2), 0),
  };
}
