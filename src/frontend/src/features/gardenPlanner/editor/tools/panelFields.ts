/**
 * The numeric fields of the properties panel (REQ-053 GP-UX-054, GP-FR-024): which fields a
 * geometry offers, how a typed value is read, and how one changed field becomes the geometry that
 * is checked and committed. Pure - the panel keeps the draft text, this module decides what it means.
 * Coordinates are model metres, x to the right and y up (§9.2); rotation is mathematical, degrees
 * counter-clockwise.
 */
import { MAX_DIMENSION_M, MIN_DIMENSION_M, roundLength } from '../../model/geometry';
import type { Geometry, Point } from '../../model/types';
import { effectiveVertices, moveVertex, normalizeAngle } from './geometryEdit';

export type FieldId = 'x' | 'y' | 'width' | 'length' | 'radius' | 'rotation' | 'strokeWidth';

export interface GeometryField {
  id: FieldId;
  value: number;
  /** Unit shown after the value. */
  unit: 'm' | 'deg';
  min: number;
  max: number;
}

const COORD_MAX = 1000;

/** Read a typed number: both decimal separators, surrounding blanks; `null` for anything else. */
export function parseDecimal(text: string): number | null {
  const normalized = text.trim().replace(',', '.');
  if (normalized === '' || !/^[+-]?(\d+\.?\d*|\.\d+)$/.test(normalized)) return null;
  const value = Number(normalized);
  return Number.isFinite(value) ? value : null;
}

/** The fields of `geometry` in display order. Polygons and polylines edit their points elsewhere. */
export function geometryFields(geometry: Geometry): GeometryField[] {
  const dim = (id: FieldId, value: number): GeometryField => ({
    id,
    value,
    unit: 'm',
    min: MIN_DIMENSION_M,
    max: MAX_DIMENSION_M,
  });
  const coord = (id: 'x' | 'y', value: number): GeometryField => ({
    id,
    value,
    unit: 'm',
    min: -COORD_MAX,
    max: COORD_MAX,
  });
  switch (geometry.kind) {
    case 'rect':
      return [
        coord('x', geometry.origin[0]),
        coord('y', geometry.origin[1]),
        dim('width', geometry.width_m),
        dim('length', geometry.length_m),
        { id: 'rotation', value: geometry.rotation_deg, unit: 'deg', min: 0, max: 360 },
      ];
    case 'circle':
      return [
        coord('x', geometry.origin[0]),
        coord('y', geometry.origin[1]),
        dim('radius', geometry.radius_m),
      ];
    case 'point':
      return [coord('x', geometry.origin[0]), coord('y', geometry.origin[1])];
    case 'polyline':
      return [dim('strokeWidth', geometry.width_m)];
    default:
      return [];
  }
}

/** `geometry` with field `id` set to `value`; the same object when the field does not apply. */
export function setField(geometry: Geometry, id: FieldId, value: number): Geometry {
  const v = roundLength(value);
  switch (geometry.kind) {
    case 'rect':
      if (id === 'x') return { ...geometry, origin: [v, geometry.origin[1]] };
      if (id === 'y') return { ...geometry, origin: [geometry.origin[0], v] };
      if (id === 'width') return { ...geometry, width_m: v };
      if (id === 'length') return { ...geometry, length_m: v };
      if (id === 'rotation') return { ...geometry, rotation_deg: roundLength(normalizeAngle(v)) };
      return geometry;
    case 'circle':
      if (id === 'x') return { ...geometry, origin: [v, geometry.origin[1]] };
      if (id === 'y') return { ...geometry, origin: [geometry.origin[0], v] };
      if (id === 'radius') return { ...geometry, radius_m: v };
      return geometry;
    case 'point':
      if (id === 'x') return { ...geometry, origin: [v, geometry.origin[1]] };
      if (id === 'y') return { ...geometry, origin: [geometry.origin[0], v] };
      return geometry;
    case 'polyline':
      return id === 'strokeWidth' ? { ...geometry, width_m: v } : geometry;
    default:
      return geometry;
  }
}

/** The points of a polygon or polyline as the plan shows them (rotation applied). */
export function pointList(geometry: Geometry): Point[] {
  return geometry.kind === 'polygon' || geometry.kind === 'polyline'
    ? effectiveVertices(geometry)
    : [];
}

/** `geometry` with point `index` moved to `to`. */
export function setPoint(geometry: Geometry, index: number, to: Point): Geometry {
  return moveVertex(geometry, index, [roundLength(to[0]), roundLength(to[1])]);
}

/** Whether two geometries are the same to the storage precision (a blur without a change commits nothing). */
export function sameGeometry(a: Geometry, b: Geometry): boolean {
  return JSON.stringify(a) === JSON.stringify(b);
}
