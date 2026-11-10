/**
 * Edge-to-edge distance between two plan geometries — TypeScript port of
 * `app/domain/calculators/geometry_distance.py` (REQ-053 GP-FR-167, WP 9.12).
 *
 * The Python module is the reference and carries the full rationale; this port mirrors it rule for rule. Both run
 * against the `edge_distance` and `nearest_water_source` cases of
 * `spec/e2e-testcases/fixtures/garden-plan-vectors.json` (§19.6).
 *
 * The measure is outline to outline, not centre to centre; touching, overlapping or nested shapes are 0 apart.
 * Each geometry is a core plus an inflation: rect/polygon the closed ring (0), point the point (0), circle its centre
 * (the radius), polyline the open centre line (half the stroke). Distance = max(0, core distance - both
 * inflations). Exact, rounded to 0.001 m. Pure: no I/O, no React.
 */

import { pointInPolygon, roundLength, segmentsIntersect, toShape } from './geometry';
import type { GardenObjectType, Geometry, Point } from './types';

/** Below this squared length a segment is a point (the Python reference uses the same floor). */
const DEGENERATE_SQ = 1e-18;

interface Core {
  vertices: Point[];
  closed: boolean;
  inflationM: number;
}

function coreOf(geometry: Geometry): Core {
  const shape = toShape(geometry);
  if (shape.kind === 'circle') return { vertices: [shape.center], closed: false, inflationM: shape.radiusM };
  const inflationM = geometry.kind === 'polyline' ? geometry.width_m / 2 : 0;
  return { vertices: shape.vertices, closed: shape.closed, inflationM };
}

function segmentsOf(core: Core): [Point, Point][] {
  const { vertices } = core;
  const count = vertices.length;
  if (count === 1) return [[vertices[0], vertices[0]]];
  const last = core.closed ? count : count - 1;
  const segments: [Point, Point][] = [];
  for (let i = 0; i < last; i += 1) segments.push([vertices[i], vertices[(i + 1) % count]]);
  return segments;
}

function pointSegmentDistance(point: Point, a: Point, b: Point): number {
  const abx = b[0] - a[0];
  const aby = b[1] - a[1];
  const lengthSq = abx * abx + aby * aby;
  if (lengthSq <= DEGENERATE_SQ) return Math.hypot(point[0] - a[0], point[1] - a[1]);
  const t = Math.max(0, Math.min(1, ((point[0] - a[0]) * abx + (point[1] - a[1]) * aby) / lengthSq));
  return Math.hypot(point[0] - (a[0] + t * abx), point[1] - (a[1] + t * aby));
}

function segmentDistance(a: Point, b: Point, c: Point, d: Point): number {
  if (segmentsIntersect(a, b, c, d)) return 0;
  return Math.min(
    pointSegmentDistance(a, c, d),
    pointSegmentDistance(b, c, d),
    pointSegmentDistance(c, a, b),
    pointSegmentDistance(d, a, b),
  );
}

function containsVertex(outer: Core, inner: Core): boolean {
  return outer.closed && outer.vertices.length >= 3 && pointInPolygon(inner.vertices[0], outer.vertices);
}

function coreDistance(a: Core, b: Core): number {
  if (containsVertex(a, b) || containsVertex(b, a)) return 0;
  let best = Number.POSITIVE_INFINITY;
  const segmentsB = segmentsOf(b);
  for (const [p, q] of segmentsOf(a)) {
    for (const [r, s] of segmentsB) {
      const value = segmentDistance(p, q, r, s);
      if (value === 0) return 0;
      if (value < best) best = value;
    }
  }
  return best;
}

/** {@link edgeDistanceM} unrounded - for a caller that compares or sums before it shows. */
export function rawEdgeDistanceM(a: Geometry, b: Geometry): number {
  const coreA = coreOf(a);
  const coreB = coreOf(b);
  return Math.max(0, coreDistance(coreA, coreB) - coreA.inflationM - coreB.inflationM);
}

/**
 * {@link rawEdgeDistanceM} from `geometry` to a vertex ring in the same frame, unrounded (port of
 * `geometry_distance.raw_distance_to_ring_m`): the ring is a derived area, no stored geometry (the strip beside a
 * bed edge a path must reach, `reach.ts`). Three or more vertices take part like a polygon; two are a segment.
 */
export function rawDistanceToRingM(geometry: Geometry, ring: readonly Point[]): number {
  const core = coreOf(geometry);
  const other: Core = { vertices: [...ring], closed: ring.length >= 3, inflationM: 0 };
  return Math.max(0, coreDistance(core, other) - core.inflationM);
}

/** The shortest outline-to-outline distance of `a` and `b` in metres (same frame), rounded to 0.001 m. */
export function edgeDistanceM(a: Geometry, b: Geometry): number {
  return roundLength(rawEdgeDistanceM(a, b));
}

/**
 * Whether GP-FR-167 measures to a garden object: class `water_source` and not `off_site` scenery (mirrors
 * `geometry_distance.is_water_source`; vector operation `is_water_source`).
 */
export function isWaterSource(objectType: GardenObjectType | string, offSite: boolean): boolean {
  return objectType === 'water_source' && !offSite;
}

/**
 * The distance from the bed's edge to the nearest of `sources` (GP-FR-167), rounded to 0.001 m; `null` without a
 * bed geometry or without a source. Which objects are sources is the caller's decision.
 */
export function nearestWaterSourceM(
  bed: Geometry | null | undefined,
  sources: readonly Geometry[],
): number | null {
  if (!bed) return null;
  let best: number | null = null;
  for (const source of sources) {
    const value = rawEdgeDistanceM(bed, source);
    if (best === null || value < best) best = value;
  }
  return best === null ? null : roundLength(best);
}
