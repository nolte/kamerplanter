/**
 * A bed template on the plan (REQ-053 §21.7, GP-FR-044; WP 7.10): the TypeScript port of
 * `domain/calculators/template_placement_calculator.py` (Python is the reference), used for the ghost under the
 * pointer; the server places the bed itself. Plus the way back: the bed-frame geometry of a bed that becomes a
 * template ("Save as template").
 *
 * A template's `default_geometry` is in the bed frame: its anchor - the lower-left corner of a rectangle, the
 * centre of a circle, the first vertex of a polygon - is the origin of its own frame. Placing it puts that
 * anchor at `origin` and turns the shape by `rotationDeg` on top of its own rotation. A circle has no rotation.
 */
import { roundLength } from '../model/geometry';
import type { Geometry, Point } from '../model/types';

const FULL_TURN_DEG = 360;

/** The template's own rotation plus the requested one, folded into `[0, 360)`. */
function turned(own: number, extra: number): number {
  const value = roundLength((own + extra) % FULL_TURN_DEG);
  return value >= FULL_TURN_DEG ? 0 : value;
}

/** `geometry` with its anchor at `origin`, turned by `rotationDeg` about that anchor; `null` for a non-bed shape. */
export function placeGeometry(
  geometry: Geometry,
  origin: Point,
  rotationDeg: number,
): Geometry | null {
  switch (geometry.kind) {
    case 'rect':
      return {
        kind: 'rect',
        origin: [origin[0], origin[1]],
        width_m: geometry.width_m,
        length_m: geometry.length_m,
        rotation_deg: turned(geometry.rotation_deg, rotationDeg),
      };
    case 'circle':
      return { kind: 'circle', origin: [origin[0], origin[1]], radius_m: geometry.radius_m };
    case 'polygon': {
      const [ax, ay] = geometry.points[0];
      return {
        kind: 'polygon',
        points: geometry.points.map(([x, y]): Point => [origin[0] + x - ax, origin[1] + y - ay]),
        rotation_deg: turned(geometry.rotation_deg, rotationDeg),
      };
    }
    default:
      return null;
  }
}

/** The bed-frame geometry of a bed: the same shape with its anchor moved to the origin (`null` for a non-bed shape). */
export function bedFrameGeometry(geometry: Geometry): Geometry | null {
  switch (geometry.kind) {
    case 'rect':
      return { ...geometry, origin: [0, 0] };
    case 'circle':
      return { ...geometry, origin: [0, 0] };
    case 'polygon': {
      const [ax, ay] = geometry.points[0];
      return {
        ...geometry,
        points: geometry.points.map(([x, y]): Point => [roundLength(x - ax), roundLength(y - ay)]),
      };
    }
    default:
      return null;
  }
}
