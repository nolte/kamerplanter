/**
 * Reach of a bed — TypeScript port of `app/domain/calculators/reach_calculator.py` (REQ-053 GP-FR-166, WP 8.23).
 *
 * The Python module is the reference and carries the full rationale; this port mirrors it rule for rule. Both
 * run against the `reach` cases of `spec/e2e-testcases/fixtures/garden-plan-vectors.json` (§19.6): a vector
 * test per side reads that file, nobody copies the cases.
 *
 * `bed.reach_too_wide` is a hint, never an error. Width: rect `min(width_m, length_m)`, circle diameter,
 * minimum caliper width of a convex polygon; a concave polygon, a polyline, a point or no geometry has none.
 * Access from `access_sides` only: an opposite pair (N + S, E + W) is `both` (1.2 m), any other non-empty list
 * is `one` (0.6 m), an empty or missing list is `unknown` and takes the one-side threshold. The width is rounded
 * to 0.001 m and must exceed the threshold. Pure: no I/O, no React.
 */

import { isConvex, roundLength } from './geometry';
import type { Geometry, Point } from './types';

/** Reach threshold with access from two opposite sides, metres (confirmed, O-17). */
export const REACH_BOTH_SIDES_M = 1.2;
/** Reach threshold with access from one side, metres (confirmed, O-17); also taken when access is unknown. */
export const REACH_ONE_SIDE_M = 0.6;
/** The hint code (GP-FR-166). */
export const HINT_REACH_TOO_WIDE = 'bed.reach_too_wide';

export type ReachAccess = 'both' | 'one' | 'unknown';
export type ReachReason = 'too_wide' | 'within_reach' | 'width_unknown';

export interface ReachResult {
  hint: boolean;
  reason: ReachReason;
  access: ReachAccess;
  /** The threshold that was applied, metres. */
  thresholdM: number;
  /** The bed width compared, rounded to 0.001 m; `null` when the shape has none here. */
  widthM: number | null;
}

export interface ReachThresholds {
  bothSidesM?: number;
  oneSideM?: number;
}

const OPPOSITE_PAIRS: readonly (readonly [string, string])[] = [
  ['N', 'S'],
  ['E', 'W'],
];

export function reachAccess(accessSides: readonly string[] | null | undefined): ReachAccess {
  const sides = new Set(accessSides ?? []);
  if (sides.size === 0) return 'unknown';
  return OPPOSITE_PAIRS.some(([a, b]) => sides.has(a) && sides.has(b)) ? 'both' : 'one';
}

function caliperWidth(points: readonly Point[]): number | null {
  const count = points.length;
  let best: number | null = null;
  for (let i = 0; i < count; i += 1) {
    const [ax, ay] = points[i];
    const [bx, by] = points[(i + 1) % count];
    const length = Math.hypot(bx - ax, by - ay);
    if (length === 0) continue;
    let span = 0;
    for (const [px, py] of points) {
      span = Math.max(span, Math.abs((bx - ax) * (py - ay) - (by - ay) * (px - ax)) / length);
    }
    if (best === null || span < best) best = span;
  }
  return best;
}

/** The narrowest extent of the bed, unrounded; `null` for shapes without a width here. */
export function bedWidthM(geometry: Geometry | null | undefined): number | null {
  if (!geometry) return null;
  switch (geometry.kind) {
    case 'rect':
      return Math.min(geometry.width_m, geometry.length_m);
    case 'circle':
      return 2 * geometry.radius_m;
    case 'polygon':
      return isConvex(geometry.points) ? caliperWidth(geometry.points) : null;
    default:
      return null;
  }
}

/** Whether `bed.reach_too_wide` applies (port of `reach_calculator.assess`). Never throws on data. */
export function assessReach(
  geometry: Geometry | null | undefined,
  accessSides: readonly string[] | null | undefined,
  { bothSidesM = REACH_BOTH_SIDES_M, oneSideM = REACH_ONE_SIDE_M }: ReachThresholds = {},
): ReachResult {
  const access = reachAccess(accessSides);
  const thresholdM = access === 'both' ? bothSidesM : oneSideM;
  const raw = bedWidthM(geometry);
  if (raw === null || !Number.isFinite(raw)) {
    return { hint: false, reason: 'width_unknown', access, thresholdM, widthM: null };
  }
  const widthM = roundLength(raw);
  if (widthM > thresholdM) return { hint: true, reason: 'too_wide', access, thresholdM, widthM };
  return { hint: false, reason: 'within_reach', access, thresholdM, widthM };
}
