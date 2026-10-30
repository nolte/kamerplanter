/**
 * Snap resolution (REQ-053 GP-FR-012, GP-FR-154): a raw model point becomes the point a tool uses.
 * Priority: object corner -> object edge -> grid. `Alt` (bypass) switches snapping off but the
 * point is still rounded to the storage precision. A moved object snaps with all corners of its
 * bounding box, so its right edge can land on another object's left edge. Pure: the editor
 * supplies the candidates.
 */
import { roundLength, rotatePoint } from '../../model/geometry';
import type { BoundingBox, Point } from '../../model/types';
import { snapToStep } from '../../model/units';

/** Snap tolerance in screen pixels (GP-FR-154). */
export const SNAP_TOLERANCE_PX = { mouse: 10, pen: 24, touch: 24 } as const;
export type SnapPointerType = keyof typeof SNAP_TOLERANCE_PX;

export type SnapKind = 'corner' | 'edge' | 'grid' | 'none';

export interface SnapCandidates {
  corners: readonly Point[];
  edges: readonly (readonly [Point, Point])[];
}

/** A grid frame other than the plan's: a bed's rotated, bed-local raster (slots, GP-FR-154). */
export interface GridFrame {
  origin: Point;
  rotationDeg: number;
}

export interface SnapOptions {
  /** Grid step in metres; the grid snaps only while `gridEnabled`. */
  gridM: number;
  gridEnabled: boolean;
  /** Alt held: no snap, only the storage rounding. */
  bypass: boolean;
  pxPerM: number;
  pointerType?: SnapPointerType;
  /** Corners and edges of other visible objects (`snapCandidates` of the plan index, GP-FR-154). */
  candidates?: SnapCandidates;
  gridFrame?: GridFrame;
}

export interface SnapResult {
  point: Point;
  kind: SnapKind;
  /** The edge the point sits on (`kind = 'edge'`): the marker draws it as a guide line. */
  guide?: readonly [Point, Point];
}

/** What the snap marker draws: where the snapped point lands, of which kind, and the edge as a guide. */
export interface SnapMark {
  point: Point;
  kind: Exclude<SnapKind, 'none'>;
  /** The object edge the point sits on (`kind = 'edge'`), drawn as a solid guide along that edge. */
  guide?: readonly [Point, Point];
}

/** A snap of a whole dragged object: the translation, and where its snapped source point lands. */
export interface MoveSnapResult {
  /** The translation the move applies. */
  delta: Point;
  kind: SnapKind;
  /** The source point after the move - what the marker draws (GP-FR-154), never the pointer. */
  point: Point;
  /** The edge the source sits on (`kind = 'edge'`). */
  guide?: readonly [Point, Point];
}

/** Below this squared length an edge is a point (the `EPSILON` of `pointSegmentDistance`). */
const DEGENERATE_SQ = 1e-9;

function rounded([x, y]: Point): Point {
  return [roundLength(x), roundLength(y)];
}

/** Where on the segment `a`-`b` the point nearest to `(px, py)` lies, as the fraction `t` in `[0, 1]`. */
function segmentParam(px: number, py: number, a: Point, b: Point): number {
  const dx = b[0] - a[0];
  const dy = b[1] - a[1];
  const lengthSq = dx * dx + dy * dy;
  if (lengthSq <= DEGENERATE_SQ) return 0;
  return Math.max(0, Math.min(1, ((px - a[0]) * dx + (py - a[1]) * dy) / lengthSq));
}

function snapToGrid(point: Point, step: number, frame: GridFrame | undefined): Point {
  if (!frame) return [snapToStep(point[0], step), snapToStep(point[1], step)];
  const local = rotatePoint(point, -frame.rotationDeg, frame.origin);
  const snapped: Point = [
    frame.origin[0] + snapToStep(local[0] - frame.origin[0], step),
    frame.origin[1] + snapToStep(local[1] - frame.origin[1], step),
  ];
  return rounded(rotatePoint(snapped, frame.rotationDeg, frame.origin));
}

/**
 * The points of a dragged object that may snap: the four corners of its bounding box (`[min_x, min_y, max_x,
 * max_y]`, counter-clockwise from the lower left) and its anchor when that is none of them (a circle's centre, a
 * polygon's first vertex). Computed once per drag, not per pointer move.
 */
export function moveSources(bbox: BoundingBox, anchorM: Point): Point[] {
  const [x0, y0, x1, y1] = bbox;
  const sources: Point[] = [
    [x0, y0],
    [x1, y0],
    [x1, y1],
    [x0, y1],
  ];
  if (!sources.some(([x, y]) => x === anchorM[0] && y === anchorM[1])) sources.push(anchorM);
  return sources;
}

/**
 * Snap of a move (GP-FR-154): every source point of the dragged object, shifted by `rawDelta`, looks for the object
 * corners within the tolerance, then - if none - for the object edges; across all sources the smallest distance
 * wins. Without an object snap the `reference` (the object's anchor) snaps to the grid, as a single point does, so
 * the object moves in whole grid steps. `Alt` (bypass) only rounds to the storage precision. Pure and free of
 * allocations in the loops: it runs on every pointer move of a drag.
 */
export function resolveMoveSnap(
  sources: readonly Point[],
  reference: Point,
  rawDelta: Point,
  options: SnapOptions,
): MoveSnapResult {
  const [dx, dy] = rawDelta;
  const free = (): MoveSnapResult => {
    const point = rounded([reference[0] + dx, reference[1] + dy]);
    return { delta: [point[0] - reference[0], point[1] - reference[1]], kind: 'none', point };
  };
  if (options.bypass) return free();
  const toleranceM = SNAP_TOLERANCE_PX[options.pointerType ?? 'mouse'] / options.pxPerM;
  const toleranceSq = toleranceM * toleranceM;
  const { candidates } = options;
  if (candidates) {
    const { corners, edges } = candidates;
    let bestSq = toleranceSq;
    let bestSource = -1;
    let bestTarget = -1;
    for (let s = 0; s < sources.length; s += 1) {
      const sx = sources[s][0] + dx;
      const sy = sources[s][1] + dy;
      for (let c = 0; c < corners.length; c += 1) {
        const ex = corners[c][0] - sx;
        const ey = corners[c][1] - sy;
        const distSq = ex * ex + ey * ey;
        if (distSq <= bestSq) {
          bestSq = distSq;
          bestSource = s;
          bestTarget = c;
        }
      }
    }
    if (bestSource >= 0) {
      const point = rounded(corners[bestTarget]);
      const source = sources[bestSource];
      return { delta: [point[0] - source[0], point[1] - source[1]], kind: 'corner', point };
    }
    bestSq = toleranceSq;
    let bestT = 0;
    for (let s = 0; s < sources.length; s += 1) {
      const sx = sources[s][0] + dx;
      const sy = sources[s][1] + dy;
      for (let e = 0; e < edges.length; e += 1) {
        const [a, b] = edges[e];
        const t = segmentParam(sx, sy, a, b);
        const ex = a[0] + t * (b[0] - a[0]) - sx;
        const ey = a[1] + t * (b[1] - a[1]) - sy;
        const distSq = ex * ex + ey * ey;
        if (distSq <= bestSq) {
          bestSq = distSq;
          bestSource = s;
          bestTarget = e;
          bestT = t;
        }
      }
    }
    if (bestSource >= 0) {
      const [a, b] = edges[bestTarget];
      const point = rounded([a[0] + bestT * (b[0] - a[0]), a[1] + bestT * (b[1] - a[1])]);
      const source = sources[bestSource];
      return {
        delta: [point[0] - source[0], point[1] - source[1]],
        kind: 'edge',
        point,
        guide: edges[bestTarget],
      };
    }
  }
  if (options.gridEnabled) {
    const point = snapToGrid([reference[0] + dx, reference[1] + dy], options.gridM, options.gridFrame);
    return { delta: [point[0] - reference[0], point[1] - reference[1]], kind: 'grid', point };
  }
  return free();
}

/** Snap of a single point (drawing, a handle, the template ghost): a move whose only source is the point. */
export function resolveSnap(pointM: Point, options: SnapOptions): SnapResult {
  const { point, kind, guide } = resolveMoveSnap([pointM], pointM, [0, 0], options);
  return guide ? { point, kind, guide } : { point, kind };
}
