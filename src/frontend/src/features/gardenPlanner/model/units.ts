/**
 * Units, grid steps, zoom levels and the scale bar of the garden plan editor (REQ-053 WP 2.5).
 * Pure functions only: lengths are stored in metres (GP-FR-004), everything here is a view
 * concern - which step the grid lines use, how far one zoom button goes, how long the scale bar is.
 */
import { roundLength } from './geometry';
import type { Point } from './types';

// ── length display (GP-FR-004) ───────────────────────────────────────────────

export type LengthUnit = 'm' | 'cm';

/** The user's choice is a view setting: it never changes a stored value. */
export function formatLength(valueM: number, unit: LengthUnit, locale?: string): string {
  if (unit === 'cm') {
    const cm = Math.round(valueM * 1000) / 10; // storage precision is 1 mm = 0.1 cm
    return `${new Intl.NumberFormat(locale, { maximumFractionDigits: 1 }).format(cm)} cm`;
  }
  const format = new Intl.NumberFormat(locale, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  return `${format.format(roundLength(valueM))} m`;
}

export function formatArea(valueM2: number, locale?: string): string {
  const format = new Intl.NumberFormat(locale, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  return `${format.format(roundLength(valueM2))} m²`;
}

export function isLengthUnit(value: unknown): value is LengthUnit {
  return value === 'm' || value === 'cm';
}

// ── grid (GP-FR-011) ─────────────────────────────────────────────────────────

/** The grid steps in metres: 1 cm, 5 cm, 10 cm, 25 cm, 50 cm, 1 m. */
export const GRID_STEPS_M = [0.01, 0.05, 0.1, 0.25, 0.5, 1] as const;
export const DEFAULT_GRID_STEP_M = 0.1;
/** Grid lines closer than this on screen are not drawn (the next coarser step is). */
export const MIN_GRID_LINE_PX = 8;

/** The step of the list closest to `valueM` (a stored `default_grid_m` may be any number). */
export function nearestGridStep(valueM: number | null | undefined): number {
  if (valueM == null || !Number.isFinite(valueM) || valueM <= 0) return DEFAULT_GRID_STEP_M;
  return GRID_STEPS_M.reduce((best, step) =>
    Math.abs(step - valueM) < Math.abs(best - valueM) ? step : best,
  );
}

/** "1 cm", "25 cm", "1 m" - the label of a grid step in the header. */
export function gridStepLabel(stepM: number, locale?: string): string {
  const format = new Intl.NumberFormat(locale);
  return stepM < 1 ? `${format.format(Math.round(stepM * 100))} cm` : `${format.format(stepM)} m`;
}

/**
 * The step whose lines are drawn: the chosen one while its lines are at least 8 px apart, else the
 * next coarser one of the list, beyond 1 m whole metres in a 1-2-5 sequence. The snap raster
 * is not affected - it stays at the chosen step (GP-FR-011).
 */
export function displayGridStep(chosenM: number, pxPerM: number): number {
  const coarser = [...GRID_STEPS_M.filter((step) => step >= chosenM - 1e-9)];
  for (const step of coarser) if (step * pxPerM >= MIN_GRID_LINE_PX) return step;
  // Beyond 1 m: 2, 5, 10, 20, 50, ... metres.
  for (let decade = 1; ; decade *= 10) {
    for (const mantissa of [2, 5, 10]) {
      const step = mantissa * decade;
      if (step * pxPerM >= MIN_GRID_LINE_PX) return step;
    }
  }
}

/** The nearest multiple of `stepM`, rounded to the storage precision (no 0.30000000000000004). */
export function snapToStep(value: number, stepM: number): number {
  // The quotient is first cleaned of float noise: 0.35 / 0.1 is 3.4999999999999996, not 3.5.
  const steps = Math.round(Math.round((value / stepM) * 1e6) / 1e6);
  return roundLength(steps * stepM);
}

// ── zoom (GP-FR-009, GP-FR-150) ──────────────────────────────────────────────

/** 100 % = 100 px/m (GP-FR-150). */
export const PX_PER_M_AT_100 = 100;
/** The fixed levels of the buttons and keys, in percent (GP-FR-009). */
export const ZOOM_LEVELS_PERCENT = [25, 50, 100, 200, 400] as const;
/** The highest zoom shows 1 cm with at least 8 px (GP-FR-150). */
export const MAX_PX_PER_M = MIN_GRID_LINE_PX / 0.01;

export function pxPerMToPercent(pxPerM: number): number {
  return Math.round((pxPerM / PX_PER_M_AT_100) * 100);
}

export function clampZoom(pxPerM: number, minPxPerM: number): number {
  return Math.min(MAX_PX_PER_M, Math.max(Math.min(minPxPerM, MAX_PX_PER_M), pxPerM));
}

/**
 * One button or key step: the next fixed level above (`direction` 1) or below (-1) the current
 * zoom. The lowest level is the fit zoom and the highest the 1 cm = 8 px limit, so on a huge
 * plan the small levels collapse into the fit (GP-FR-150).
 */
export function stepZoom(pxPerM: number, direction: 1 | -1, minPxPerM: number): number {
  const levels = ZOOM_LEVELS_PERCENT.map((percent) => (percent * PX_PER_M_AT_100) / 100);
  const eps = 1e-6;
  const next =
    direction > 0
      ? (levels.find((level) => level > pxPerM + eps) ?? MAX_PX_PER_M)
      : ([...levels].reverse().find((level) => level < pxPerM - eps) ?? minPxPerM);
  return clampZoom(next, minPxPerM);
}

export interface ZoomView {
  originM: Point;
  pxPerM: number;
}

/**
 * Zoom to `nextPxPerM` such that the model point under `anchorPx` (canvas pixels, y down) stays
 * under it - the pointer for the wheel, the canvas centre for the buttons.
 */
export function zoomAround(
  view: ZoomView,
  nextPxPerM: number,
  anchorPx: Point,
  minPxPerM: number,
): ZoomView {
  const pxPerM = clampZoom(nextPxPerM, minPxPerM);
  const modelX = view.originM[0] + anchorPx[0] / view.pxPerM;
  const modelY = view.originM[1] - anchorPx[1] / view.pxPerM;
  return {
    pxPerM,
    originM: [modelX - anchorPx[0] / pxPerM, modelY + anchorPx[1] / pxPerM],
  };
}

// ── scale bar (GP-FR-009) ────────────────────────────────────────────────────

/** Lengths the bar may have: 1 m, 5 m, 10 m and their decimal neighbours. */
const SCALE_BAR_LENGTHS_M = [0.01, 0.05, 0.1, 0.5, 1, 5, 10, 50, 100, 500, 1000] as const;
export const SCALE_BAR_MAX_PX = 160;

/** The longest nice length that fits into 160 px; at the lowest zoom the shortest one is used. */
export function scaleBarLengthM(pxPerM: number): number {
  const fitting = SCALE_BAR_LENGTHS_M.filter((length) => length * pxPerM <= SCALE_BAR_MAX_PX);
  return fitting.length > 0 ? fitting[fitting.length - 1] : SCALE_BAR_LENGTHS_M[0];
}

/** "1 m", "50 cm", "5 m" - the label of the bar. */
export function scaleBarLabel(lengthM: number, locale?: string): string {
  return lengthM < 1
    ? `${new Intl.NumberFormat(locale).format(Math.round(lengthM * 100))} cm`
    : `${new Intl.NumberFormat(locale).format(lengthM)} m`;
}
