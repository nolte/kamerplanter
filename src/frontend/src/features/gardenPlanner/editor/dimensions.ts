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

/** The model-space point below the shape's middle: where the label goes when there is no room above. */
export function labelAnchorBelow(shape: Shape): Point {
  if (shape.kind === 'circle') return [shape.center[0], shape.center[1] - shape.radiusM];
  const xs = shape.vertices.map((vertex) => vertex[0]);
  const ys = shape.vertices.map((vertex) => vertex[1]);
  return [(Math.min(...xs) + Math.max(...xs)) / 2, Math.min(...ys)];
}

/** Room between the edge (or a handle) and the dimension text, in screen pixels. */
export const DIMENSION_GAP_PX = 6;
/** Clearance kept around a handle's visible square, in screen pixels. */
const HANDLE_CLEARANCE_PX = 2;
/** Average glyph width of the (semi-bold) dimension text as a share of its font size. */
const DIMENSION_GLYPH_EM = 0.62;
/** Below the baseline the text reaches this share of its font size. */
const DESCENT_EM = 0.25;

export interface DimensionPlacementInput {
  /** Screen point centred on the shape's top edge, and on its bottom edge. */
  topPx: Point;
  bottomPx: Point;
  text: string;
  fontPx: number;
  /** Screen centres of the visible handles, each `handleSizePx` square. */
  handlesPx: readonly Point[];
  handleSizePx: number;
  /** Canvas height: the text must stay on it. */
  heightPx: number;
}

type Box = readonly [number, number, number, number];

function overlaps(a: Box, b: Box): boolean {
  return a[0] < b[2] && b[0] < a[2] && a[1] < b[3] && b[1] < a[3];
}

/**
 * Where the dimension text goes (GP-UX-047): outside the shape, centred over its top edge, and clear of every handle -
 * a handle in the way pushes the text further out, past it. When the text would leave the top of the canvas it moves
 * below the bottom edge by the same rule. Returns the text's centre x and its baseline y, in screen pixels.
 */
export function placeDimensionLabel(input: DimensionPlacementInput): Point {
  const { topPx, bottomPx, text, fontPx, handlesPx, handleSizePx, heightPx } = input;
  const halfWidth = (text.length * fontPx * DIMENSION_GLYPH_EM) / 2;
  const descent = fontPx * DESCENT_EM;
  const half = handleSizePx / 2 + HANDLE_CLEARANCE_PX;
  const handles: Box[] = handlesPx.map(([x, y]) => [x - half, y - half, x + half, y + half]);
  const textBox = (x: number, baseline: number): Box => [x - halfWidth, baseline - fontPx, x + halfWidth, baseline + descent];

  // Each pass clears at least one more handle, so as many passes as handles always settle.
  const settle = (x: number, start: number, direction: -1 | 1): number => {
    let baseline = start;
    for (let pass = 0; pass <= handles.length; pass += 1) {
      const box = textBox(x, baseline);
      const blocking = handles.filter((handle) => overlaps(box, handle));
      if (blocking.length === 0) return baseline;
      baseline =
        direction < 0
          ? Math.min(...blocking.map((handle) => handle[1])) - DIMENSION_GAP_PX / 2 - descent
          : Math.max(...blocking.map((handle) => handle[3])) + DIMENSION_GAP_PX / 2 + fontPx;
    }
    return baseline;
  };

  const above = settle(topPx[0], topPx[1] - DIMENSION_GAP_PX, -1);
  if (above - fontPx >= 0) return [topPx[0], above];
  const below = settle(bottomPx[0], bottomPx[1] + DIMENSION_GAP_PX + fontPx, 1);
  if (below + descent <= heightPx) return [bottomPx[0], below];
  // Neither side has room (a shape taller than the canvas): keep the text on screen at the top.
  return [topPx[0], fontPx + 2];
}
