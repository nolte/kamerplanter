/**
 * Pure geometry of the garden plan - the TypeScript port of the Python reference
 * `app/domain/calculators/geometry_calculator.py` and the V-01 model rules of
 * `app/domain/models/geometry.py` (REQ-053 GP-FR-004..008, §9.2, §19.6, GP-NFR-012).
 *
 * Python is the reference, this file the port. Both run against
 * `spec/e2e-testcases/fixtures/garden-plan-vectors.json`; when the two disagree the vector file
 * is wrong or one side is - never "fix" a port by editing a vector.
 *
 * No I/O, no geometry library (decision D-04). Conventions: lengths in metres, angles in degrees
 * counter-clockwise about +x. A geometry's anchor is `rect.origin`, `circle.origin`/`point.origin`
 * and the first vertex of a polygon/polyline; rotation pivots about the anchor and
 * `p_plan = anchor + R(rotation_deg) * p_bed`. Stored derived values (area, bbox, centroid) are
 * rounded to 0.001; the predicates work on unrounded floats.
 */
import type { BoundingBox, Geometry, Point } from './types';

// ── V-01 bounds (REQ-053 §20.1, §22.2) ───────────────────────────────────────

export const MIN_DIMENSION_M = 0.01;
export const MAX_DIMENSION_M = 1000.0;
const MIN_COORDINATE_M = 0.0;
const MAX_COORDINATE_M = 1000.0;
const FULL_TURN_DEG = 360.0;
const MIN_POLYGON_POINTS = 3;
const MIN_POLYLINE_POINTS = 2;
const MAX_POINTS = 200;
const LENGTH_DECIMALS = 3;

/** V-03: a child may protrude from its parent by at most 1 cm. */
export const DEFAULT_TOLERANCE_M = 0.01;
/** Numerical noise floor for orientation tests, well below the storage precision. */
const EPSILON = 1e-9;

/** V-02 error code (REQ-053 §22.2). */
export const ERROR_SELF_INTERSECTING = 'geometry.self_intersecting';

/** The coordinate frame a geometry is validated for (§9.2): plan 0..1000, bed -1000..1000. */
export type GeometryFrame = 'plan' | 'bed';

/**
 * Round a length, coordinate or angle to the storage precision (0.001), ties away from zero on the
 * exact binary value (GP-FR-004). `Number.prototype.toFixed` rounds the exact value half up and
 * handles the sign separately, which is the rule Python's
 * `Decimal(value).quantize(Decimal("0.001"), ROUND_HALF_UP)` defines; `Math.round(x * 1000) / 1000`
 * would not agree. `-0` becomes `0`.
 */
export function roundLength(value: number): number {
  return Number(value.toFixed(LENGTH_DECIMALS)) + 0;
}

// ── V-01 parsing ─────────────────────────────────────────────────────────────

type Raw = Record<string, unknown>;

function isRecord(value: unknown): value is Raw {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

/** A strict number: JSON number only (a string or boolean is invalid), finite. */
function isNumber(value: unknown): value is number {
  return typeof value === 'number' && Number.isFinite(value);
}

function hasOnly(raw: Raw, allowed: readonly string[]): boolean {
  return Object.keys(raw).every((key) => allowed.includes(key));
}

function parsePoint(value: unknown, frame: GeometryFrame): Point | null {
  if (!Array.isArray(value) || value.length !== 2) return null;
  const [rawX, rawY] = value as unknown[];
  if (!isNumber(rawX) || !isNumber(rawY)) return null;
  const minimum = frame === 'bed' ? -MAX_COORDINATE_M : MIN_COORDINATE_M;
  const x = roundLength(rawX);
  const y = roundLength(rawY);
  for (const coordinate of [x, y]) {
    if (coordinate < minimum || coordinate > MAX_COORDINATE_M) return null;
  }
  return [x, y];
}

function parseDimension(value: unknown): number | null {
  if (!isNumber(value)) return null;
  const rounded = roundLength(value);
  return rounded >= MIN_DIMENSION_M && rounded <= MAX_DIMENSION_M ? rounded : null;
}

/** V-01 on the input: `0 <= value < 360`; an input that rounds to 360.000 is stored as 0. */
function parseRotation(value: unknown): number | null {
  if (value === undefined) return 0;
  if (!isNumber(value) || value < 0 || value >= FULL_TURN_DEG) return null;
  const rounded = roundLength(value);
  return rounded === FULL_TURN_DEG ? 0 : rounded;
}

function parsePoints(value: unknown, minimum: number, frame: GeometryFrame): Point[] | null {
  if (!Array.isArray(value) || value.length < minimum || value.length > MAX_POINTS) return null;
  const points: Point[] = [];
  for (const item of value as unknown[]) {
    const point = parsePoint(item, frame);
    if (point === null) return null;
    points.push(point);
  }
  return points;
}

/**
 * Validate and normalise a raw mapping as a {@link Geometry} expressed in `frame` (V-01,
 * `geometry.invalid`). Returns the normalised geometry (millimetre precision, `rotation_deg`
 * defaulted) or `null` when the payload violates V-01. Simplicity (V-02) is a domain rule: a
 * self-intersecting polygon parses and {@link validateGeometry} reports it.
 */
export function parseGeometry(raw: unknown, frame: GeometryFrame = 'plan'): Geometry | null {
  if (!isRecord(raw)) return null;
  switch (raw.kind) {
    case 'rect': {
      if (!hasOnly(raw, ['kind', 'origin', 'width_m', 'length_m', 'rotation_deg'])) return null;
      const origin = parsePoint(raw.origin, frame);
      const width = parseDimension(raw.width_m);
      const length = parseDimension(raw.length_m);
      const rotation = parseRotation(raw.rotation_deg);
      if (origin === null || width === null || length === null || rotation === null) return null;
      return { kind: 'rect', origin, width_m: width, length_m: length, rotation_deg: rotation };
    }
    case 'circle': {
      if (!hasOnly(raw, ['kind', 'origin', 'radius_m'])) return null;
      const origin = parsePoint(raw.origin, frame);
      const radius = parseDimension(raw.radius_m);
      if (origin === null || radius === null) return null;
      return { kind: 'circle', origin, radius_m: radius };
    }
    case 'polygon': {
      if (!hasOnly(raw, ['kind', 'points', 'rotation_deg'])) return null;
      const points = parsePoints(raw.points, MIN_POLYGON_POINTS, frame);
      const rotation = parseRotation(raw.rotation_deg);
      if (points === null || rotation === null) return null;
      return { kind: 'polygon', points, rotation_deg: rotation };
    }
    case 'polyline': {
      if (!hasOnly(raw, ['kind', 'points', 'width_m'])) return null;
      const points = parsePoints(raw.points, MIN_POLYLINE_POINTS, frame);
      const width = parseDimension(raw.width_m);
      if (points === null || width === null) return null;
      return { kind: 'polyline', points, width_m: width };
    }
    case 'point': {
      if (!hasOnly(raw, ['kind', 'origin'])) return null;
      const origin = parsePoint(raw.origin, frame);
      return origin === null ? null : { kind: 'point', origin };
    }
    default:
      return null;
  }
}

// ── Resolved shapes ──────────────────────────────────────────────────────────

/**
 * A geometry resolved into vertices. `closed` is true for area shapes (rect, polygon): the edge
 * from the last vertex back to the first is implicit. A polyline has no area and no overlap
 * notion; a point is a one-vertex open shape.
 */
export interface VertexShape {
  kind: 'vertices';
  vertices: Point[];
  closed: boolean;
}

/** A circle resolved into centre and radius; exact, never polygonised. */
export interface CircleShape {
  kind: 'circle';
  center: Point;
  radiusM: number;
}

export type Shape = VertexShape | CircleShape;

// ── Vector helpers ───────────────────────────────────────────────────────────

/** Rotate `point` counter-clockwise by `angleDeg` about `pivot`. */
export function rotatePoint(point: Point, angleDeg: number, pivot: Point = [0, 0]): Point {
  const radians = (angleDeg * Math.PI) / 180;
  const cos = Math.cos(radians);
  const sin = Math.sin(radians);
  const dx = point[0] - pivot[0];
  const dy = point[1] - pivot[1];
  return [pivot[0] + dx * cos - dy * sin, pivot[1] + dx * sin + dy * cos];
}

function distance(a: Point, b: Point): number {
  return Math.hypot(a[0] - b[0], a[1] - b[1]);
}

function roundPoint(point: Point): Point {
  return [roundLength(point[0]), roundLength(point[1])];
}

/** Z component of `(a - o) x (b - o)`: > 0 when `o -> a -> b` turns left. */
function cross(o: Point, a: Point, b: Point): number {
  return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0]);
}

/** Distance from `point` to the segment `a`-`b`. */
export function pointSegmentDistance(point: Point, a: Point, b: Point): number {
  const abx = b[0] - a[0];
  const aby = b[1] - a[1];
  const lengthSq = abx * abx + aby * aby;
  if (lengthSq <= EPSILON) return distance(point, a);
  let t = ((point[0] - a[0]) * abx + (point[1] - a[1]) * aby) / lengthSq;
  t = Math.max(0, Math.min(1, t));
  return distance(point, [a[0] + t * abx, a[1] + t * aby]);
}

/** Signed perpendicular distance of `point` from the line through `a`-`b` (left positive). */
function signedSide(point: Point, a: Point, b: Point): number {
  const length = distance(a, b);
  if (length <= EPSILON) return 0;
  return cross(a, b, point) / length;
}

function edgesOf(vertices: Point[], closed: boolean): [Point, Point][] {
  const count = vertices.length;
  if (count < 2) return [];
  const last = closed ? count : count - 1;
  const edges: [Point, Point][] = [];
  for (let i = 0; i < last; i += 1) edges.push([vertices[i], vertices[(i + 1) % count]]);
  return edges;
}

// ── Anchor, frames and transformation (§9.2) ─────────────────────────────────

/** The pivot of the geometry: origin for rect/circle/point, first vertex otherwise. */
export function anchor(geometry: Geometry): Point {
  return geometry.kind === 'polygon' || geometry.kind === 'polyline'
    ? geometry.points[0]
    : geometry.origin;
}

/** Rotation of the geometry; shapes without a rotation field rotate by 0. */
export function rotationDeg(geometry: Geometry): number {
  return geometry.kind === 'rect' || geometry.kind === 'polygon' ? geometry.rotation_deg : 0;
}

/** Map a point from the bed frame of `bed` into the frame `bed` is expressed in. */
export function transformBedToPlan(point: Point, bed: Geometry): Point {
  const [ax, ay] = anchor(bed);
  const [rx, ry] = rotatePoint(point, rotationDeg(bed));
  return [ax + rx, ay + ry];
}

/** Inverse of {@link transformBedToPlan}. */
export function transformPlanToBed(point: Point, bed: Geometry): Point {
  const [ax, ay] = anchor(bed);
  return rotatePoint([point[0] - ax, point[1] - ay], -rotationDeg(bed));
}

/** Resolve `geometry` in its own local frame: anchor at (0, 0), no rotation (the bed frame). */
export function toLocalShape(geometry: Geometry): Shape {
  switch (geometry.kind) {
    case 'rect': {
      const w = geometry.width_m;
      const l = geometry.length_m;
      return {
        kind: 'vertices',
        vertices: [
          [0, 0],
          [w, 0],
          [w, l],
          [0, l],
        ],
        closed: true,
      };
    }
    case 'circle':
      return { kind: 'circle', center: [0, 0], radiusM: geometry.radius_m };
    case 'point':
      return { kind: 'vertices', vertices: [[0, 0]], closed: false };
    default: {
      const [ax, ay] = geometry.points[0];
      return {
        kind: 'vertices',
        vertices: geometry.points.map(([x, y]): Point => [x - ax, y - ay]),
        closed: geometry.kind === 'polygon',
      };
    }
  }
}

/** Resolve `geometry` in the frame its coordinates are expressed in (rotation applied). */
export function toShape(geometry: Geometry): Shape {
  const local = toLocalShape(geometry);
  if (local.kind === 'circle') {
    return { kind: 'circle', center: anchor(geometry), radiusM: local.radiusM };
  }
  return {
    kind: 'vertices',
    vertices: local.vertices.map((vertex) => transformBedToPlan(vertex, geometry)),
    closed: local.closed,
  };
}

// ── Derived values (GP-FR-006/007) ───────────────────────────────────────────

/** Unsigned area of the closed polygon `points` (shoelace formula), 0 for < 3 points. */
export function shoelaceArea(points: readonly Point[]): number {
  const count = points.length;
  if (count < 3) return 0;
  let total = 0;
  for (let i = 0; i < count; i += 1) {
    const [x1, y1] = points[i];
    const [x2, y2] = points[(i + 1) % count];
    total += x1 * y2 - x2 * y1;
  }
  return Math.abs(total) / 2;
}

/** Area in m2, rounded to 0.001; polylines and points have none (GP-FR-006). */
export function areaM2(geometry: Geometry): number {
  let raw = 0;
  if (geometry.kind === 'rect') raw = geometry.width_m * geometry.length_m;
  else if (geometry.kind === 'circle') raw = Math.PI * geometry.radius_m ** 2;
  else if (geometry.kind === 'polygon') raw = shoelaceArea(geometry.points);
  return roundLength(raw);
}

function shapeBbox(shape: Shape): BoundingBox {
  if (shape.kind === 'circle') {
    const [cx, cy] = shape.center;
    const r = shape.radiusM;
    return [cx - r, cy - r, cx + r, cy + r];
  }
  let minX = Infinity;
  let minY = Infinity;
  let maxX = -Infinity;
  let maxY = -Infinity;
  for (const [x, y] of shape.vertices) {
    if (x < minX) minX = x;
    if (x > maxX) maxX = x;
    if (y < minY) minY = y;
    if (y > maxY) maxY = y;
  }
  return [minX, minY, maxX, maxY];
}

/**
 * Axis-aligned bounding box after rotation, rounded to 0.001 m (GP-FR-007). A polyline's box
 * includes its stroke (`+- width_m / 2`) so that culling and the mini-map see what is drawn.
 */
export function boundingBox(geometry: Geometry): BoundingBox {
  let [minX, minY, maxX, maxY] = shapeBbox(toShape(geometry));
  if (geometry.kind === 'polyline') {
    const half = geometry.width_m / 2;
    minX -= half;
    minY -= half;
    maxX += half;
    maxY += half;
  }
  return [roundLength(minX), roundLength(minY), roundLength(maxX), roundLength(maxY)];
}

/**
 * Centroid after rotation, rounded to 0.001 m. Area shapes use the area centroid, a polyline the
 * mean of its vertices. Computed in the local frame (small numbers) and transformed afterwards.
 */
export function centroid(geometry: Geometry): Point {
  const local = toLocalShape(geometry);
  if (local.kind === 'circle') return roundPoint(anchor(geometry));
  const { vertices } = local;
  const count = vertices.length;
  let localCentroid: Point | null = null;
  if (local.closed) {
    let doubledArea = 0;
    let cx = 0;
    let cy = 0;
    for (let i = 0; i < count; i += 1) {
      const [x1, y1] = vertices[i];
      const [x2, y2] = vertices[(i + 1) % count];
      const crossValue = x1 * y2 - x2 * y1;
      doubledArea += crossValue;
      cx += (x1 + x2) * crossValue;
      cy += (y1 + y2) * crossValue;
    }
    if (Math.abs(doubledArea) > EPSILON) {
      localCentroid = [cx / (3 * doubledArea), cy / (3 * doubledArea)];
    }
  }
  if (localCentroid === null) {
    localCentroid = [
      vertices.reduce((sum, v) => sum + v[0], 0) / count,
      vertices.reduce((sum, v) => sum + v[1], 0) / count,
    ];
  }
  return roundPoint(transformBedToPlan(localCentroid, geometry));
}

// ── Simplicity (V-02) ────────────────────────────────────────────────────────

function onSegment(p: Point, a: Point, b: Point): boolean {
  return (
    Math.min(a[0], b[0]) - EPSILON <= p[0] &&
    p[0] <= Math.max(a[0], b[0]) + EPSILON &&
    Math.min(a[1], b[1]) - EPSILON <= p[1] &&
    p[1] <= Math.max(a[1], b[1]) + EPSILON
  );
}

function orientation(o: Point, a: Point, b: Point): -1 | 0 | 1 {
  const value = cross(o, a, b);
  if (Math.abs(value) <= EPSILON) return 0;
  return value > 0 ? 1 : -1;
}

/** Whether segments `a`-`b` and `c`-`d` share at least one point (touching counts). */
export function segmentsIntersect(a: Point, b: Point, c: Point, d: Point): boolean {
  const o1 = orientation(a, b, c);
  const o2 = orientation(a, b, d);
  const o3 = orientation(c, d, a);
  const o4 = orientation(c, d, b);
  if (o1 !== o2 && o3 !== o4 && o1 !== 0 && o2 !== 0 && o3 !== 0 && o4 !== 0) return true;
  if (o1 === 0 && onSegment(c, a, b)) return true;
  if (o2 === 0 && onSegment(d, a, b)) return true;
  if (o3 === 0 && onSegment(a, c, d)) return true;
  return o4 === 0 && onSegment(b, c, d);
}

/**
 * V-02: the closed polygon `points` has no self-intersection and encloses an area. O(n^2), fine
 * for n <= 200. Non-adjacent edges may not meet at all (a revisited vertex is a self-touch);
 * adjacent edges may not fold back onto each other; every edge has a length; a degenerate
 * (collinear) polygon is not simple.
 */
export function isSimplePolygon(points: readonly Point[]): boolean {
  const count = points.length;
  if (count < 3) return false;
  const edges = edgesOf([...points], true);
  for (const [a, b] of edges) {
    if (distance(a, b) <= EPSILON) return false;
  }
  if (shoelaceArea(points) <= EPSILON) return false;
  for (let i = 0; i < count; i += 1) {
    const [a, b] = edges[i];
    for (let j = i + 1; j < count; j += 1) {
      const [c, d] = edges[j];
      const adjacent = j === i + 1 || (i === 0 && j === count - 1);
      if (adjacent) {
        // The shared vertex is legitimate; folding back onto the previous edge is not.
        const [shared, prevEnd, nextEnd] = j === i + 1 ? [b, a, d] : [a, b, c];
        if (orientation(prevEnd, shared, nextEnd) === 0) {
          const dot =
            (prevEnd[0] - shared[0]) * (nextEnd[0] - shared[0]) +
            (prevEnd[1] - shared[1]) * (nextEnd[1] - shared[1]);
          if (dot > 0) return false;
        }
        continue;
      }
      if (segmentsIntersect(a, b, c, d)) return false;
    }
  }
  return true;
}

/** Domain-level validation codes for `geometry` (empty = valid): today V-02. */
export function validateGeometry(geometry: Geometry): string[] {
  if (geometry.kind === 'polygon' && !isSimplePolygon(geometry.points)) {
    return [ERROR_SELF_INTERSECTING];
  }
  return [];
}

/**
 * Whether the closed *simple* polygon `vertices` is convex (collinear runs allowed). Precondition:
 * the polygon passed V-02.
 */
export function isConvex(vertices: readonly Point[]): boolean {
  const count = vertices.length;
  if (count < 3) return false;
  let sign = 0;
  for (let i = 0; i < count; i += 1) {
    const turn = orientation(vertices[i], vertices[(i + 1) % count], vertices[(i + 2) % count]);
    if (turn === 0) continue;
    if (sign === 0) sign = turn;
    else if (turn !== sign) return false;
  }
  return sign !== 0;
}

// ── Point-in-polygon and signed distance ─────────────────────────────────────

/** Even-odd ray cast; points on the boundary may land on either side (use the distance). */
export function pointInPolygon(point: Point, vertices: readonly Point[]): boolean {
  let inside = false;
  const [px, py] = point;
  const count = vertices.length;
  for (let i = 0; i < count; i += 1) {
    const [x1, y1] = vertices[i];
    const [x2, y2] = vertices[(i + 1) % count];
    if (y1 > py !== y2 > py) {
      const xAt = x1 + ((py - y1) * (x2 - x1)) / (y2 - y1);
      if (px < xAt) inside = !inside;
    }
  }
  return inside;
}

/** Distance from `point` to the polygon boundary: positive inside, negative outside. */
export function signedDistanceToPolygon(point: Point, vertices: readonly Point[]): number {
  let minimum = Infinity;
  for (const [a, b] of edgesOf([...vertices], true)) {
    const d = pointSegmentDistance(point, a, b);
    if (d < minimum) minimum = d;
  }
  return pointInPolygon(point, vertices) ? minimum : -minimum;
}

function signedDistance(point: Point, shape: Shape): number {
  if (shape.kind === 'circle') return shape.radiusM - distance(point, shape.center);
  return signedDistanceToPolygon(point, shape.vertices);
}

/** Whether `a`-`b` and `c`-`d` cross with every end clear of the other line by more than the tolerance. */
function properCrossing(a: Point, b: Point, c: Point, d: Point, toleranceM: number): boolean {
  const sideC = signedSide(c, a, b);
  const sideD = signedSide(d, a, b);
  const sideA = signedSide(a, c, d);
  const sideB = signedSide(b, c, d);
  return (
    sideC * sideD < 0 &&
    sideA * sideB < 0 &&
    Math.min(Math.abs(sideC), Math.abs(sideD), Math.abs(sideA), Math.abs(sideB)) > toleranceM
  );
}

function anyProperCrossing(a: VertexShape, b: VertexShape, toleranceM: number): boolean {
  const edgesB = edgesOf(b.vertices, b.closed);
  for (const [p, q] of edgesOf(a.vertices, a.closed)) {
    for (const [r, s] of edgesB) {
      if (properCrossing(p, q, r, s, toleranceM)) return true;
    }
  }
  return false;
}

/** Positions `t` in [0, 1] along `a`-`b` where it meets `c`-`d` (touching and collinear overlap included). */
function intersectionParameters(a: Point, b: Point, c: Point, d: Point): number[] {
  const abx = b[0] - a[0];
  const aby = b[1] - a[1];
  const cdx = d[0] - c[0];
  const cdy = d[1] - c[1];
  const denominator = abx * cdy - aby * cdx;
  const acx = c[0] - a[0];
  const acy = c[1] - a[1];
  const lengthSq = abx * abx + aby * aby;
  if (lengthSq <= EPSILON) return [];
  if (Math.abs(denominator) <= EPSILON) {
    if (Math.abs(acx * aby - acy * abx) > EPSILON) return []; // parallel but not collinear
    const parameters: number[] = [];
    for (const point of [c, d]) {
      const t = ((point[0] - a[0]) * abx + (point[1] - a[1]) * aby) / lengthSq;
      if (t >= -EPSILON && t <= 1 + EPSILON) parameters.push(Math.min(1, Math.max(0, t)));
    }
    return parameters;
  }
  const t = (acx * cdy - acy * cdx) / denominator;
  const u = (acx * aby - acy * abx) / denominator;
  if (t >= -EPSILON && t <= 1 + EPSILON && u >= -EPSILON && u <= 1 + EPSILON) {
    return [Math.min(1, Math.max(0, t))];
  }
  return [];
}

/**
 * Whether every point of `p`-`q` is at least `margin` inside `parent`. The segment is split at
 * every meeting point with a parent edge; between two consecutive splits it is wholly inside or
 * wholly outside, so the midpoint of each piece decides.
 */
function segmentInsidePolygon(p: Point, q: Point, parent: VertexShape, margin: number): boolean {
  const parameters = [0, 1];
  for (const [c, d] of edgesOf(parent.vertices, true)) {
    parameters.push(...intersectionParameters(p, q, c, d));
  }
  parameters.sort((x, y) => x - y);
  for (let i = 0; i + 1 < parameters.length; i += 1) {
    const start = parameters[i];
    const end = parameters[i + 1];
    if (end - start <= EPSILON) continue;
    const middle = (start + end) / 2;
    const probe: Point = [p[0] + (q[0] - p[0]) * middle, p[1] + (q[1] - p[1]) * middle];
    if (signedDistanceToPolygon(probe, parent.vertices) < margin) return false;
  }
  return true;
}

// ── Containment (V-03 / V-04) ────────────────────────────────────────────────

export interface ContainsOptions {
  /** How far the child may protrude (default 1 cm). */
  toleranceM?: number;
  /** Required distance between child and parent boundary (V-04 slot edge margin). */
  insetM?: number;
}

/**
 * Whether `child` lies completely inside `parent`, at least `insetM` from its edge.
 *
 * V-03 (`geometry.outside_parent`): every child vertex is inside the parent with a 1 cm tolerance.
 * V-04 (`slot.outside_bed`): the edge margin is passed as `insetM` and the parent is the bed in
 * its own frame ({@link toLocalShape}). Beyond the vertex test, every child edge is checked
 * piecewise against a polygon parent and, with an inset, against the parent's vertices. Both
 * shapes are assumed to have passed V-02.
 *
 * @throws Error when `parent` has no area (an open vertex shape).
 */
export function contains(parent: Shape, child: Shape, options: ContainsOptions = {}): boolean {
  const toleranceM = options.toleranceM ?? DEFAULT_TOLERANCE_M;
  const insetM = options.insetM ?? 0;
  if (parent.kind === 'vertices' && !parent.closed) {
    throw new Error('Only an area shape (closed polygon or circle) can contain another geometry.');
  }
  const margin = insetM - toleranceM;
  if (child.kind === 'circle') {
    return signedDistance(child.center, parent) >= child.radiusM + margin;
  }
  if (!child.vertices.every((vertex) => signedDistance(vertex, parent) >= margin)) return false;
  if (parent.kind === 'circle' || child.vertices.length < 2) return true;
  const childEdges = edgesOf(child.vertices, child.closed);
  if (!childEdges.every(([p, q]) => segmentInsidePolygon(p, q, parent, margin))) return false;
  if (margin > 0) {
    return parent.vertices.every((vertex) =>
      childEdges.every(([p, q]) => pointSegmentDistance(vertex, p, q) >= margin),
    );
  }
  return true;
}

// ── Overlap (V-05 / V-06) ────────────────────────────────────────────────────

function bboxesOverlap(a: BoundingBox, b: BoundingBox, toleranceM: number): boolean {
  return (
    a[2] > b[0] + toleranceM &&
    b[2] > a[0] + toleranceM &&
    a[3] > b[1] + toleranceM &&
    b[3] > a[1] + toleranceM
  );
}

function project(vertices: readonly Point[], axis: Point): [number, number] {
  let minimum = Infinity;
  let maximum = -Infinity;
  for (const v of vertices) {
    const dot = v[0] * axis[0] + v[1] * axis[1];
    if (dot < minimum) minimum = dot;
    if (dot > maximum) maximum = dot;
  }
  return [minimum, maximum];
}

/** Separating-axis test for two convex polygons; overlap must exceed the tolerance on every axis. */
function satOverlap(a: VertexShape, b: VertexShape, toleranceM: number): boolean {
  const edges = [...edgesOf(a.vertices, true), ...edgesOf(b.vertices, true)];
  for (const [p, q] of edges) {
    const edgeX = q[0] - p[0];
    const edgeY = q[1] - p[1];
    const length = Math.hypot(edgeX, edgeY);
    if (length <= EPSILON) continue;
    const axis: Point = [-edgeY / length, edgeX / length];
    const [minA, maxA] = project(a.vertices, axis);
    const [minB, maxB] = project(b.vertices, axis);
    if (Math.min(maxA, maxB) - Math.max(minA, minB) <= toleranceM) return false;
  }
  return true;
}

/** The midpoint of every edge, moved `offsetM` into the polygon's interior. */
function inwardEdgeProbes(vertices: readonly Point[], offsetM: number): Point[] {
  const count = vertices.length;
  let signed = 0;
  for (let i = 0; i < count; i += 1) {
    const [x1, y1] = vertices[i];
    const [x2, y2] = vertices[(i + 1) % count];
    signed += x1 * y2 - x2 * y1;
  }
  const orient = signed >= 0 ? 1 : -1; // counter-clockwise: the interior is to the left
  const probes: Point[] = [];
  for (const [p, q] of edgesOf([...vertices], true)) {
    const edgeX = q[0] - p[0];
    const edgeY = q[1] - p[1];
    const length = Math.hypot(edgeX, edgeY);
    if (length <= EPSILON) continue;
    const normalX = (-edgeY / length) * orient;
    const normalY = (edgeX / length) * orient;
    probes.push([(p[0] + q[0]) / 2 + normalX * offsetM, (p[1] + q[1]) / 2 + normalY * offsetM]);
  }
  return probes;
}

/** Whether an inward probe of some `own` edge lies inside `other` as well. */
function probesShareInterior(own: VertexShape, other: VertexShape, toleranceM: number): boolean {
  const half = 0.5 * toleranceM;
  const slack = 1e-6; // below storage precision; lets the identical twin pass the >= test
  for (const probe of inwardEdgeProbes(own.vertices, half)) {
    if (signedDistanceToPolygon(probe, own.vertices) < half - slack) continue;
    if (signedDistanceToPolygon(probe, other.vertices) > half - slack) return true;
  }
  return false;
}

/** General (concave-safe) test: a deep edge crossing, a vertex clearly inside the other, or shared edge interior. */
function edgeOverlap(a: VertexShape, b: VertexShape, toleranceM: number): boolean {
  if (anyProperCrossing(a, b, toleranceM)) return true;
  if (a.vertices.some((v) => signedDistanceToPolygon(v, b.vertices) > toleranceM)) return true;
  if (b.vertices.some((v) => signedDistanceToPolygon(v, a.vertices) > toleranceM)) return true;
  return probesShareInterior(a, b, toleranceM) || probesShareInterior(b, a, toleranceM);
}

export interface OverlapOptions {
  toleranceM?: number;
}

/**
 * Whether two area shapes share more than a sliver (penetration > `toleranceM`): V-05
 * (`bed.overlap`) / V-06 (`slot.overlap`). Bounding-box pre-test, then the separating-axis test for
 * convex polygons or the edge test for concave ones; circles by distance. Shapes without an area
 * (point, polyline) never overlap anything. Both shapes are assumed to have passed V-02.
 */
export function overlaps(a: Shape, b: Shape, options: OverlapOptions = {}): boolean {
  const toleranceM = options.toleranceM ?? DEFAULT_TOLERANCE_M;
  if ((a.kind === 'vertices' && !a.closed) || (b.kind === 'vertices' && !b.closed)) return false;
  if (!bboxesOverlap(shapeBbox(a), shapeBbox(b), toleranceM)) return false;
  if (a.kind === 'circle' && b.kind === 'circle') {
    return distance(a.center, b.center) < a.radiusM + b.radiusM - toleranceM;
  }
  if (a.kind === 'circle') return signedDistance(a.center, b) > toleranceM - a.radiusM;
  if (b.kind === 'circle') return signedDistance(b.center, a) > toleranceM - b.radiusM;
  if (isConvex(a.vertices) && isConvex(b.vertices)) return satOverlap(a, b, toleranceM);
  return edgeOverlap(a, b, toleranceM);
}
