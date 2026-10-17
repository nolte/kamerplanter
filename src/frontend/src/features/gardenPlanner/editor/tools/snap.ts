/**
 * Snap resolution (REQ-053 GP-FR-012, GP-FR-154): a raw model point becomes the point a tool uses.
 * Priority: object corner -> object edge -> grid. `Alt` (bypass) switches snapping off but the
 * point is still rounded to the storage precision. Pure: the editor supplies the candidates.
 */
import { pointSegmentDistance, roundLength, rotatePoint } from '../../model/geometry';
import type { Point } from '../../model/types';
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
  /** Corners and edges of other objects. Object snap is SHOULD (MVP: not supplied). */
  candidates?: SnapCandidates;
  gridFrame?: GridFrame;
}

export interface SnapResult {
  point: Point;
  kind: SnapKind;
}

function rounded([x, y]: Point): Point {
  return [roundLength(x), roundLength(y)];
}

function nearestOnSegment(point: Point, a: Point, b: Point): Point {
  const dx = b[0] - a[0];
  const dy = b[1] - a[1];
  const lengthSq = dx * dx + dy * dy;
  if (lengthSq === 0) return a;
  const t = Math.max(0, Math.min(1, ((point[0] - a[0]) * dx + (point[1] - a[1]) * dy) / lengthSq));
  return [a[0] + t * dx, a[1] + t * dy];
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

export function resolveSnap(pointM: Point, options: SnapOptions): SnapResult {
  if (options.bypass) return { point: rounded(pointM), kind: 'none' };
  const toleranceM = SNAP_TOLERANCE_PX[options.pointerType ?? 'mouse'] / options.pxPerM;
  const { candidates } = options;
  if (candidates) {
    let best: Point | null = null;
    let bestDistance = toleranceM;
    for (const corner of candidates.corners) {
      const distance = Math.hypot(corner[0] - pointM[0], corner[1] - pointM[1]);
      if (distance <= bestDistance) {
        best = corner;
        bestDistance = distance;
      }
    }
    if (best) return { point: rounded(best), kind: 'corner' };
    bestDistance = toleranceM;
    for (const [a, b] of candidates.edges) {
      const distance = pointSegmentDistance(pointM, a, b);
      if (distance <= bestDistance) {
        best = nearestOnSegment(pointM, a, b);
        bestDistance = distance;
      }
    }
    if (best) return { point: rounded(best), kind: 'edge' };
  }
  if (options.gridEnabled) {
    return { point: snapToGrid(pointM, options.gridM, options.gridFrame), kind: 'grid' };
  }
  return { point: rounded(pointM), kind: 'none' };
}
