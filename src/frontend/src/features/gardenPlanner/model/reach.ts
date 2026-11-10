/**
 * Reach of a bed — TypeScript port of `app/domain/calculators/reach_calculator.py` (REQ-053 GP-FR-166, WP 8.23).
 *
 * The Python module is the reference and carries the full rationale; this port mirrors it rule for rule. Both
 * run against the `reach` cases of `spec/e2e-testcases/fixtures/garden-plan-vectors.json` (§19.6): a vector
 * test per side reads that file, nobody copies the cases.
 *
 * `bed.reach_too_wide` is a hint, never an error. Width: rect `min(width_m, length_m)`, circle diameter,
 * minimum caliper width of a convex polygon; a concave polygon, a polyline, a point or no geometry has none.
 * Manual access from `access_sides`: an opposite pair (N + S, E + W) is `both` (1.2 m), any other non-empty list
 * is `one` (0.6 m), an empty or missing list is `unknown` and takes the one-side threshold. The width is rounded
 * to 0.001 m and must exceed the threshold.
 *
 * Access from paths (#2703, `pathAccess`): a `path` object reaches a bed edge when it meets the strip outward of the
 * edge, `maxDistanceM` deep (default 0.3 m, per site) and shortened by 0.01 m at both ends, so a path past a corner
 * reaches no side. Two reached edges that are antiparallel and span exactly the bed's width are `both`; any reached
 * edge is `one`; none is `none`. A circle (no edges here) is at most `one`. The stronger of both sources wins
 * (`combinedAccess`). The bed summary carries the server's `path_access`, derived by the Python reference; this
 * port runs against the same vectors. Pure: no I/O, no React.
 */

import { isConvex, roundLength, toShape } from './geometry';
import { rawDistanceToRingM, rawEdgeDistanceM } from './geometryDistance';
import type { Geometry, Point } from './types';

/** Reach threshold with access from two opposite sides, metres (confirmed, O-17). */
export const REACH_BOTH_SIDES_M = 1.2;
/** Reach threshold with access from one side, metres (confirmed, O-17); also taken when access is unknown. */
export const REACH_ONE_SIDE_M = 0.6;

/** A path within this edge-to-edge distance of a bed edge makes that side reachable, metres (#2703, default). */
export const PATH_ACCESS_MAX_DISTANCE_M = 0.3;
/** The strip beside a bed edge is shortened by this much at both ends, metres: a corner is no side. */
export const PATH_CORNER_INSET_M = 0.01;

export type ReachAccess = 'both' | 'one' | 'unknown';
/** The access the site's paths give a bed (`path_access` of the bed summary). */
export type PathAccessClass = 'both' | 'one' | 'none';
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
  /** The class the site's paths give the bed; `null`/absent = not known. Joins `accessSides` (the stronger wins). */
  pathAccess?: PathAccessClass | null;
}

export interface PathAccessResult {
  access: PathAccessClass;
  /** Ascending indices of the reached bed edges (edge `i` runs from vertex `i` to `i + 1` of the resolved shape). */
  edges: number[];
}

const ACCESS_RANK: Record<ReachAccess | PathAccessClass, number> = {
  unknown: 0,
  none: 0,
  one: 1,
  both: 2,
};
/** Two unit edge directions are antiparallel when their cross product is below this (numerical noise only). */
const PARALLEL_EPS = 1e-9;

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

function bedRing(geometry: Geometry): Point[] | null {
  if (geometry.kind === 'rect' || (geometry.kind === 'polygon' && isConvex(geometry.points))) {
    const shape = toShape(geometry);
    if (shape.kind === 'vertices' && shape.vertices.length >= 3) return shape.vertices;
  }
  return null;
}

function isCounterClockwise(ring: readonly Point[]): boolean {
  let total = 0;
  for (let i = 0; i < ring.length; i += 1) {
    const [x1, y1] = ring[i];
    const [x2, y2] = ring[(i + 1) % ring.length];
    total += x1 * y2 - x2 * y1;
  }
  return total > 0;
}

function edgeStrip(a: Point, b: Point, outward: Point, depthM: number): Point[] | null {
  const length = Math.hypot(b[0] - a[0], b[1] - a[1]);
  if (length <= 2 * PATH_CORNER_INSET_M) return null;
  const ux = (b[0] - a[0]) / length;
  const uy = (b[1] - a[1]) / length;
  const start: Point = [a[0] + ux * PATH_CORNER_INSET_M, a[1] + uy * PATH_CORNER_INSET_M];
  const end: Point = [b[0] - ux * PATH_CORNER_INSET_M, b[1] - uy * PATH_CORNER_INSET_M];
  if (depthM <= 0) return [start, end];
  const nx = outward[0] * depthM;
  const ny = outward[1] * depthM;
  return [start, end, [end[0] + nx, end[1] + ny], [start[0] + nx, start[1] + ny]];
}

function spanFromEdge(ring: readonly Point[], index: number): number {
  const [ax, ay] = ring[index];
  const [bx, by] = ring[(index + 1) % ring.length];
  const length = Math.hypot(bx - ax, by - ay);
  let span = 0;
  for (const [px, py] of ring) {
    span = Math.max(span, Math.abs((bx - ax) * (py - ay) - (by - ay) * (px - ax)) / length);
  }
  return span;
}

function acrossTheWidth(ring: readonly Point[], i: number, j: number, width: number): boolean {
  const [ax, ay] = ring[i];
  const [bx, by] = ring[(i + 1) % ring.length];
  const [cx, cy] = ring[j];
  const [dx, dy] = ring[(j + 1) % ring.length];
  const lenI = Math.hypot(bx - ax, by - ay);
  const lenJ = Math.hypot(dx - cx, dy - cy);
  const [ux, uy, vx, vy] = [(bx - ax) / lenI, (by - ay) / lenI, (dx - cx) / lenJ, (dy - cy) / lenJ];
  if (Math.abs(ux * vy - uy * vx) > PARALLEL_EPS || ux * vx + uy * vy >= 0) return false;
  return (
    roundLength(spanFromEdge(ring, i)) === width && roundLength(spanFromEdge(ring, j)) === width
  );
}

/** A distance rounded to the storage precision (GP-FR-004) is at most `limitM`. */
function within(distanceM: number, limitM: number): boolean {
  return roundLength(distanceM) <= limitM;
}

/**
 * Which bed edges the `paths` reach and the access class that gives (port of `reach_calculator.path_access`).
 * `paths` are the geometries of the site's `path` objects in the bed's frame. Never throws on data.
 */
export function pathAccess(
  bed: Geometry | null | undefined,
  paths: readonly Geometry[],
  maxDistanceM: number = PATH_ACCESS_MAX_DISTANCE_M,
): PathAccessResult {
  if (!bed || paths.length === 0) return { access: 'none', edges: [] };
  const ring = bedRing(bed);
  if (ring === null) {
    const near = paths.some((path) => within(rawEdgeDistanceM(bed, path), maxDistanceM));
    return { access: near ? 'one' : 'none', edges: [] };
  }
  const ccw = isCounterClockwise(ring);
  const reached: number[] = [];
  for (let i = 0; i < ring.length; i += 1) {
    const a = ring[i];
    const b = ring[(i + 1) % ring.length];
    const length = Math.hypot(b[0] - a[0], b[1] - a[1]);
    if (length === 0) continue;
    // The outward normal: right of the edge for a counter-clockwise ring, left for a clockwise one.
    const dx = (b[0] - a[0]) / length;
    const dy = (b[1] - a[1]) / length;
    const outward: Point = ccw ? [dy, -dx] : [-dy, dx];
    const strip = edgeStrip(a, b, outward, maxDistanceM);
    if (strip !== null && paths.some((path) => within(rawDistanceToRingM(path, strip), 0)))
      reached.push(i);
  }
  if (reached.length === 0) return { access: 'none', edges: [] };
  const rawWidth = bedWidthM(bed);
  const width = rawWidth !== null && Number.isFinite(rawWidth) ? roundLength(rawWidth) : null;
  let both = false;
  if (width !== null) {
    for (let k = 0; k < reached.length && !both; k += 1) {
      for (let m = k + 1; m < reached.length && !both; m += 1) {
        both = acrossTheWidth(ring, reached[k], reached[m], width);
      }
    }
  }
  return { access: both ? 'both' : 'one', edges: reached };
}

/** The stronger of the manual access class and the one derived from paths (port of `combined_access`). */
export function combinedAccess(
  manual: ReachAccess,
  fromPaths: PathAccessClass | null | undefined,
): ReachAccess {
  if (fromPaths && fromPaths !== 'none' && ACCESS_RANK[fromPaths] > ACCESS_RANK[manual])
    return fromPaths;
  return manual;
}

/** Whether `bed.reach_too_wide` applies (port of `reach_calculator.assess`). Never throws on data. */
export function assessReach(
  geometry: Geometry | null | undefined,
  accessSides: readonly string[] | null | undefined,
  {
    bothSidesM = REACH_BOTH_SIDES_M,
    oneSideM = REACH_ONE_SIDE_M,
    pathAccess: fromPaths = null,
  }: ReachThresholds = {},
): ReachResult {
  const access = combinedAccess(reachAccess(accessSides), fromPaths);
  const thresholdM = access === 'both' ? bothSidesM : oneSideM;
  const raw = bedWidthM(geometry);
  if (raw === null || !Number.isFinite(raw)) {
    return { hint: false, reason: 'width_unknown', access, thresholdM, widthM: null };
  }
  const widthM = roundLength(raw);
  if (widthM > thresholdM) return { hint: true, reason: 'too_wide', access, thresholdM, widthM };
  return { hint: false, reason: 'within_reach', access, thresholdM, widthM };
}
