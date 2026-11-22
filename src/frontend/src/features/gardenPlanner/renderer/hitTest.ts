/**
 * Hit testing for both renderers (GP-NFR-009, GP-NFR-065). Priority (GP-UX-032), topmost first:
 * plant/slot marker, bed or garden object, path, area, boundary; inside a class the higher
 * z-order, then the smaller area. Locked objects are hit too (they only cannot be moved).
 */
import { pointInPolygon, pointSegmentDistance } from '../model/geometry';
import type { PlanModel } from '../model/planModel';
import type { Point } from '../model/types';
import { HIT_SLOP_PX, MARKER_HIT_RADIUS_PX, markersVisible } from './lod';
import { markerIndex, shapeEntries, type ShapeEntry } from './planIndex';
import type { Viewport } from './types';
import { toModel } from './viewport';

interface Candidate {
  key: string;
  rank: number;
  zOrder: number;
  area: number;
}

function minEdgeDistance(point: Point, vertices: readonly Point[], closed: boolean): number {
  let best = Infinity;
  const last = closed ? vertices.length : vertices.length - 1;
  for (let i = 0; i < last; i += 1) {
    const d = pointSegmentDistance(point, vertices[i], vertices[(i + 1) % vertices.length]);
    if (d < best) best = d;
  }
  return best;
}

function hitsShape(entry: ShapeEntry, point: Point, slopM: number, pointRadiusM: number): boolean {
  const { shape, geometry } = entry;
  if (
    point[0] < entry.bbox[0] - slopM ||
    point[0] > entry.bbox[2] + slopM ||
    point[1] < entry.bbox[1] - slopM ||
    point[1] > entry.bbox[3] + slopM
  ) {
    return false;
  }
  if (shape.kind === 'circle') {
    return (
      Math.hypot(point[0] - shape.center[0], point[1] - shape.center[1]) <= shape.radiusM + slopM
    );
  }
  const { vertices, closed } = shape;
  if (!closed) {
    if (vertices.length === 1) {
      return Math.hypot(point[0] - vertices[0][0], point[1] - vertices[0][1]) <= pointRadiusM;
    }
    const halfStroke = geometry.kind === 'polyline' ? geometry.width_m / 2 : 0;
    return minEdgeDistance(point, vertices, false) <= Math.max(halfStroke, slopM);
  }
  // The garden boundary encloses everything: only its edge is a target, so an empty click stays empty.
  if (entry.kind === 'boundary') return minEdgeDistance(point, vertices, true) <= slopM;
  return pointInPolygon(point, vertices) || minEdgeDistance(point, vertices, true) <= slopM;
}

/** Keys under `pointPx`, topmost first. */
export function hitTestAll(model: PlanModel, viewport: Viewport, pointPx: Point): string[] {
  const point = toModel(viewport, pointPx);
  const slopM = HIT_SLOP_PX / viewport.pxPerM;
  const markerRadiusM = MARKER_HIT_RADIUS_PX / viewport.pxPerM;
  const found: Candidate[] = [];

  for (const bed of markerIndex(model).values()) {
    if (!markersVisible(bed.minSpacingM, viewport.pxPerM)) continue;
    const [minX, minY, maxX, maxY] = bed.bbox;
    if (
      point[0] < minX - markerRadiusM ||
      point[0] > maxX + markerRadiusM ||
      point[1] < minY - markerRadiusM ||
      point[1] > maxY + markerRadiusM
    ) {
      continue;
    }
    for (const marker of bed.markers) {
      if (Math.hypot(point[0] - marker.x, point[1] - marker.y) <= markerRadiusM) {
        found.push({ key: marker.key, rank: 0, zOrder: 0, area: 0 });
      }
    }
  }
  for (const entry of shapeEntries(model)) {
    if (hitsShape(entry, point, slopM, markerRadiusM)) {
      found.push({
        key: entry.key,
        rank: entry.layer,
        zOrder: entry.zOrder,
        area: entry.bboxAreaM2,
      });
    }
  }
  found.sort(
    (a, b) =>
      a.rank - b.rank ||
      b.zOrder - a.zOrder ||
      a.area - b.area ||
      (a.key < b.key ? -1 : a.key > b.key ? 1 : 0),
  );
  return found.map((candidate) => candidate.key);
}
