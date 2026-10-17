/**
 * Dimension text of a shape (REQ-053 GP-FR-014): width, length (or radius) and area of what is
 * selected, drawn or resized. Pure: the editor turns the numbers into text with the length unit
 * and the language.
 */
import { shoelaceArea, type Shape } from '../model/geometry';
import type { Point } from '../model/types';

export type Dimensions =
  | { kind: 'rect'; widthM: number; lengthM: number; areaM2: number }
  | { kind: 'circle'; diameterM: number; areaM2: number }
  | { kind: 'polygon'; widthM: number; lengthM: number; areaM2: number }
  | { kind: 'line'; lengthM: number };

const RIGHT_ANGLE_TOLERANCE = 1e-6;

function dist(a: Point, b: Point): number {
  return Math.hypot(b[0] - a[0], b[1] - a[1]);
}

function isRectangle(v: readonly Point[]): boolean {
  if (v.length !== 4) return false;
  for (let i = 0; i < 4; i += 1) {
    const o = v[i];
    const a = v[(i + 1) % 4];
    const b = v[(i + 3) % 4];
    const dot = (a[0] - o[0]) * (b[0] - o[0]) + (a[1] - o[1]) * (b[1] - o[1]);
    const scale = dist(o, a) * dist(o, b);
    if (scale === 0 || Math.abs(dot) / scale > RIGHT_ANGLE_TOLERANCE) return false;
  }
  return true;
}

/** `null` for a point or an empty shape: nothing to measure. */
export function dimensionsOfShape(shape: Shape): Dimensions | null {
  if (shape.kind === 'circle') {
    return {
      kind: 'circle',
      diameterM: 2 * shape.radiusM,
      areaM2: Math.PI * shape.radiusM * shape.radiusM,
    };
  }
  const { vertices } = shape;
  if (vertices.length < 2) return null;
  if (!shape.closed) {
    let length = 0;
    for (let i = 1; i < vertices.length; i += 1) length += dist(vertices[i - 1], vertices[i]);
    return { kind: 'line', lengthM: length };
  }
  if (isRectangle(vertices)) {
    return {
      kind: 'rect',
      widthM: dist(vertices[0], vertices[1]),
      lengthM: dist(vertices[1], vertices[2]),
      areaM2: shoelaceArea(vertices),
    };
  }
  const xs = vertices.map((vertex) => vertex[0]);
  const ys = vertices.map((vertex) => vertex[1]);
  return {
    kind: 'polygon',
    widthM: Math.max(...xs) - Math.min(...xs),
    lengthM: Math.max(...ys) - Math.min(...ys),
    areaM2: shoelaceArea(vertices),
  };
}

/** The model-space point above the shape's middle: where the label sits. */
export function labelAnchor(shape: Shape): Point {
  if (shape.kind === 'circle') return [shape.center[0], shape.center[1] + shape.radiusM];
  const xs = shape.vertices.map((vertex) => vertex[0]);
  const ys = shape.vertices.map((vertex) => vertex[1]);
  return [(Math.min(...xs) + Math.max(...xs)) / 2, Math.max(...ys)];
}
