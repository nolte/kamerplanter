/**
 * Pure geometry edits behind the editor tools (REQ-053 GP-FR-021/022/023, GP-FR-008). Every
 * function takes a geometry and returns a new one; nothing here knows the plan, the renderer or
 * the pointer. All outputs are rounded to the storage precision (0.001 m, GP-FR-004).
 *
 * Conventions follow `model/geometry.ts`: lengths in metres, angles counter-clockwise about +x,
 * rotation pivots about the anchor (`rect.origin`, `circle.origin`, first vertex).
 */
import {
  anchor,
  centroid,
  MIN_DIMENSION_M,
  rotatePoint,
  rotationDeg,
  roundLength,
  toShape,
} from '../../model/geometry';
import type { Geometry, Point, RectGeometry } from '../../model/types';

const FULL_TURN_DEG = 360;

function roundPoint([x, y]: Point): Point {
  return [roundLength(x), roundLength(y)];
}

/** An angle in `[0, 360)`, rounded to 0.001 (a value that rounds to 360 is 0). */
export function normalizeAngle(deg: number): number {
  const wrapped = ((deg % FULL_TURN_DEG) + FULL_TURN_DEG) % FULL_TURN_DEG;
  const rounded = roundLength(wrapped);
  return rounded >= FULL_TURN_DEG ? 0 : rounded;
}

/** Snap an angle to the nearest multiple of `stepDeg` (GP-FR-008: 15 / 45 / 90). */
export function snapAngle(deg: number, stepDeg: number): number {
  return Math.round(deg / stepDeg) * stepDeg;
}

/** A rigid motion: rotate by `rotateDeg` about `pivot`, then translate. */
export interface RigidMotion {
  translate: Point;
  rotateDeg: number;
  pivot: Point;
}

/**
 * Apply a rigid motion to a whole geometry. The geometry's own frame moves with it, so a bed
 * keeps every slot (slots live in the bed frame, §9.2): moving or turning a bed is one update.
 */
export function moveGeometry(geometry: Geometry, motion: RigidMotion): Geometry {
  const start = anchor(geometry);
  const turned = rotatePoint(start, motion.rotateDeg, motion.pivot);
  const next: Point = [turned[0] + motion.translate[0], turned[1] + motion.translate[1]];
  switch (geometry.kind) {
    case 'point':
    case 'circle':
      return { ...geometry, origin: roundPoint(next) };
    case 'rect':
      return {
        ...geometry,
        origin: roundPoint(next),
        rotation_deg: normalizeAngle(geometry.rotation_deg + motion.rotateDeg),
      };
    case 'polygon': {
      // Stored points are pre-rotation; the frame (anchor + rotation) carries the motion.
      const shift: Point = [next[0] - start[0], next[1] - start[1]];
      return {
        ...geometry,
        points: geometry.points.map(([x, y]): Point => roundPoint([x + shift[0], y + shift[1]])),
        rotation_deg: normalizeAngle(geometry.rotation_deg + motion.rotateDeg),
      };
    }
    case 'polyline':
      return {
        ...geometry,
        points: geometry.points.map((point): Point => {
          const [x, y] = rotatePoint(point, motion.rotateDeg, motion.pivot);
          return roundPoint([x + motion.translate[0], y + motion.translate[1]]);
        }),
      };
  }
}

export function translateGeometry(geometry: Geometry, delta: Point): Geometry {
  return moveGeometry(geometry, { translate: delta, rotateDeg: 0, pivot: [0, 0] });
}

/** The point a rotation turns about: the visual middle of the shape. */
export function geometryCenter(geometry: Geometry): Point {
  if (geometry.kind === 'rect') {
    return rotatePoint(
      [geometry.origin[0] + geometry.width_m / 2, geometry.origin[1] + geometry.length_m / 2],
      geometry.rotation_deg,
      geometry.origin,
    );
  }
  if (geometry.kind === 'circle' || geometry.kind === 'point') return geometry.origin;
  return centroid(geometry);
}

/** The change of angle (degrees, counter-clockwise) when the pointer moves from `from` to `to` about `pivot`. */
export function angleBetween(pivot: Point, from: Point, to: Point): number {
  const a0 = Math.atan2(from[1] - pivot[1], from[0] - pivot[0]);
  const a1 = Math.atan2(to[1] - pivot[1], to[0] - pivot[0]);
  return ((a1 - a0) * 180) / Math.PI;
}

/**
 * The rotation delta of a rotate-handle drag. With `stepDeg` the resulting absolute rotation
 * snaps to a multiple of it (angle snap, GP-FR-154); without, the turn is free (Alt).
 */
export function rotationDelta(
  geometry: Geometry,
  pivot: Point,
  startPointer: Point,
  pointer: Point,
  stepDeg: number | null,
): number {
  const raw = angleBetween(pivot, startPointer, pointer);
  if (stepDeg === null) return raw;
  const base = rotationDeg(geometry);
  return snapAngle(base + raw, stepDeg) - base;
}

// ── Rect: eight handles ──────────────────────────────────────────────────────

/** Handle names are positions in the rect's own frame (before rotation): n = +length side. */
export type RectHandleId = 'n' | 'ne' | 'e' | 'se' | 's' | 'sw' | 'w' | 'nw';

export const RECT_HANDLE_IDS: readonly RectHandleId[] = [
  'nw',
  'n',
  'ne',
  'e',
  'se',
  's',
  'sw',
  'w',
];

/** Where a rect handle sits, in the rect's local frame. */
export function rectHandleLocal(id: RectHandleId, width: number, length: number): Point {
  const x = id.includes('e') ? width : id.includes('w') ? 0 : width / 2;
  const y = id.includes('n') ? length : id.includes('s') ? 0 : length / 2;
  return [x, y];
}

/**
 * Drag a rect handle to `pointer` (plan frame). An edge handle moves one edge, a corner handle two;
 * the opposite edges stay put (dragging past them mirrors the rect). `keepAspect` (Shift) holds the
 * width:length ratio on a corner handle (GP-FR-022).
 */
export function resizeRect(
  rect: RectGeometry,
  handle: RectHandleId,
  pointer: Point,
  keepAspect: boolean,
): RectGeometry {
  const [lx, ly] = rotatePoint(pointer, -rect.rotation_deg, rect.origin);
  const local: Point = [lx - rect.origin[0], ly - rect.origin[1]];
  let x0 = 0;
  let x1 = rect.width_m;
  let y0 = 0;
  let y1 = rect.length_m;
  const dragsEast = handle.includes('e');
  const dragsWest = handle.includes('w');
  const dragsNorth = handle.includes('n');
  const dragsSouth = handle.includes('s');

  if (keepAspect && handle.length === 2) {
    const fixedX = dragsEast ? 0 : rect.width_m;
    const fixedY = dragsNorth ? 0 : rect.length_m;
    const dx = local[0] - fixedX;
    const dy = local[1] - fixedY;
    const scale = Math.max(Math.abs(dx) / rect.width_m, Math.abs(dy) / rect.length_m);
    const width = rect.width_m * scale;
    const length = rect.length_m * scale;
    const movedX = fixedX + (dx < 0 ? -width : width);
    const movedY = fixedY + (dy < 0 ? -length : length);
    [x0, x1] = [Math.min(fixedX, movedX), Math.max(fixedX, movedX)];
    [y0, y1] = [Math.min(fixedY, movedY), Math.max(fixedY, movedY)];
  } else {
    if (dragsEast) x1 = local[0];
    if (dragsWest) x0 = local[0];
    if (dragsNorth) y1 = local[1];
    if (dragsSouth) y0 = local[1];
    [x0, x1] = [Math.min(x0, x1), Math.max(x0, x1)];
    [y0, y1] = [Math.min(y0, y1), Math.max(y0, y1)];
  }
  const width = Math.max(MIN_DIMENSION_M, x1 - x0);
  const length = Math.max(MIN_DIMENSION_M, y1 - y0);
  const origin = rotatePoint(
    [rect.origin[0] + x0, rect.origin[1] + y0],
    rect.rotation_deg,
    rect.origin,
  );
  return {
    ...rect,
    origin: roundPoint(origin),
    width_m: roundLength(width),
    length_m: roundLength(length),
  };
}

/** The radius handle: the circle reaches the pointer (never below the minimum size). */
export function resizeCircle(circle: { origin: Point; radius_m: number }, pointer: Point): number {
  const radius = Math.hypot(pointer[0] - circle.origin[0], pointer[1] - circle.origin[1]);
  return roundLength(Math.max(MIN_DIMENSION_M, radius));
}

// ── Polygon / polyline vertices (GP-FR-023) ──────────────────────────────────

/** The vertices as they appear on the plan (rotation applied). */
export function effectiveVertices(geometry: Geometry): Point[] {
  const shape = toShape(geometry);
  return shape.kind === 'vertices' ? shape.vertices : [];
}

/**
 * Write plan-frame vertices back into a polygon or polyline. The first vertex stays the anchor and
 * the stored rotation is kept, so the pre-rotation points are the inverse-rotated vertices.
 */
export function withVertices(geometry: Geometry, vertices: readonly Point[]): Geometry {
  if (geometry.kind === 'polyline') {
    return { ...geometry, points: vertices.map(roundPoint) };
  }
  if (geometry.kind !== 'polygon') return geometry;
  const pivot = vertices[0];
  return {
    ...geometry,
    points: vertices.map((vertex): Point =>
      roundPoint(rotatePoint(vertex, -geometry.rotation_deg, pivot)),
    ),
  };
}

export function moveVertex(geometry: Geometry, index: number, to: Point): Geometry {
  const vertices = effectiveVertices(geometry);
  if (index < 0 || index >= vertices.length) return geometry;
  return withVertices(
    geometry,
    vertices.map((vertex, i) => (i === index ? to : vertex)),
  );
}

/** The vertex index `index + 1` is a new vertex at `at` (default: the middle of the edge). */
export function insertVertex(geometry: Geometry, index: number, at?: Point): Geometry {
  const vertices = effectiveVertices(geometry);
  const closed = geometry.kind === 'polygon';
  const last = closed ? vertices.length : vertices.length - 1;
  if (index < 0 || index >= last) return geometry;
  const from = vertices[index];
  const to = vertices[(index + 1) % vertices.length];
  const point: Point = at ?? [(from[0] + to[0]) / 2, (from[1] + to[1]) / 2];
  return withVertices(geometry, [
    ...vertices.slice(0, index + 1),
    point,
    ...vertices.slice(index + 1),
  ]);
}

/** Fewest vertices that keep the shape valid: polygon 3, polyline 2 (GP-FR-023). */
export function minVertices(geometry: Geometry): number {
  return geometry.kind === 'polygon' ? 3 : 2;
}

/** `null` when the geometry would fall below the minimum. */
export function removeVertex(geometry: Geometry, index: number): Geometry | null {
  const vertices = effectiveVertices(geometry);
  if (vertices.length <= minVertices(geometry) || index < 0 || index >= vertices.length)
    return null;
  return withVertices(
    geometry,
    vertices.filter((_, i) => i !== index),
  );
}
