/**
 * Where an object's name sits on the plan, and how wide it may run (REQ-053 GP-UX-047, GP-FR-003; #2490) - the
 * TypeScript port of `app/domain/calculators/label_anchor_calculator.py`. Both run against the `label_anchor` cases of
 * `spec/e2e-testcases/fixtures/garden-plan-vectors.json`, so the editor and the PDF put a name on the same point.
 * Python is the reference: when the two disagree, fix the port, never the vector.
 *
 * - rect, circle: the centre; a circle's room is its diameter.
 * - polygon: the pole of inaccessibility (the inner point farthest from every edge, Agafonkin's polylabel search to
 *   within {@link POLE_PRECISION_M}, seeded with the area centroid), searched in the local frame and transformed
 *   afterwards. Cells leave the queue in a total order - highest potential, then lowest x, then lowest y, then
 *   insertion - so ties resolve as in the reference.
 * - polyline: the point at half its length; room = bounding-box width (stroke included).
 * - point: the point itself; room 0.
 *
 * The room of a centred, horizontal label is twice the shorter reach along the horizontal chord through the anchor.
 * Point and room are rounded to 0.001 m. Arithmetic is written as in the reference (no `Math.hypot`), so the search
 * sees the same floats.
 */
import { anchor, boundingBox, roundLength, toLocalShape, toShape, transformBedToPlan } from './geometry';
import type { Geometry, Point } from './types';

/** The pole search stops once no cell can beat the best point by more than this (1 cm). */
export const POLE_PRECISION_M = 0.01;
const DEGENERATE_M = 1e-9;

export interface LabelAnchor {
  /** The label centre, plan frame, metres. */
  point: Point;
  /** The widest horizontal text centred on `point` that stays inside the shape, metres. */
  widthM: number;
}

// ── Pole of inaccessibility ──────────────────────────────────────────────────

function segmentDistanceSq(px: number, py: number, a: Point, b: Point): number {
  let x = a[0];
  let y = a[1];
  let dx = b[0] - x;
  let dy = b[1] - y;
  if (dx !== 0 || dy !== 0) {
    const t = ((px - x) * dx + (py - y) * dy) / (dx * dx + dy * dy);
    if (t > 1) {
      x = b[0];
      y = b[1];
    } else if (t > 0) {
      x += dx * t;
      y += dy * t;
    }
  }
  dx = px - x;
  dy = py - y;
  return dx * dx + dy * dy;
}

/** Distance to the boundary: positive inside, negative outside (even-odd rule). */
function signedDistance(px: number, py: number, vertices: readonly Point[]): number {
  let inside = false;
  let bestSq = Infinity;
  const count = vertices.length;
  for (let i = 0, j = count - 1; i < count; j = i, i += 1) {
    const a = vertices[i];
    const b = vertices[j];
    if (a[1] > py !== b[1] > py && px < ((b[0] - a[0]) * (py - a[1])) / (b[1] - a[1]) + a[0]) {
      inside = !inside;
    }
    bestSq = Math.min(bestSq, segmentDistanceSq(px, py, a, b));
  }
  const distance = Math.sqrt(bestSq);
  return inside ? distance : -distance;
}

interface Cell {
  x: number;
  y: number;
  half: number;
  distance: number;
  potential: number;
  order: number;
}

/** `a` leaves the queue before `b`: higher potential, then lower x, then lower y, then pushed earlier. */
function before(a: Cell, b: Cell): boolean {
  if (a.potential !== b.potential) return a.potential > b.potential;
  if (a.x !== b.x) return a.x < b.x;
  if (a.y !== b.y) return a.y < b.y;
  return a.order < b.order;
}

/** A binary heap ordered by {@link before}. */
class CellQueue {
  private readonly items: Cell[] = [];

  get size(): number {
    return this.items.length;
  }

  push(cell: Cell): void {
    const { items } = this;
    items.push(cell);
    let index = items.length - 1;
    while (index > 0) {
      const parent = (index - 1) >> 1;
      if (!before(items[index], items[parent])) break;
      [items[index], items[parent]] = [items[parent], items[index]];
      index = parent;
    }
  }

  pop(): Cell {
    const { items } = this;
    const top = items[0];
    const last = items.pop() as Cell;
    if (items.length > 0) {
      items[0] = last;
      let index = 0;
      for (;;) {
        const left = 2 * index + 1;
        const right = left + 1;
        let first = index;
        if (left < items.length && before(items[left], items[first])) first = left;
        if (right < items.length && before(items[right], items[first])) first = right;
        if (first === index) break;
        [items[index], items[first]] = [items[first], items[index]];
        index = first;
      }
    }
    return top;
  }
}

function areaCentroid(vertices: readonly Point[]): Point {
  let doubled = 0;
  let cx = 0;
  let cy = 0;
  const count = vertices.length;
  for (let i = 0, j = count - 1; i < count; j = i, i += 1) {
    const [ax, ay] = vertices[i];
    const [bx, by] = vertices[j];
    const crossValue = ax * by - bx * ay;
    cx += (ax + bx) * crossValue;
    cy += (ay + by) * crossValue;
    doubled += crossValue;
  }
  if (doubled === 0) return vertices[0];
  return [cx / (3 * doubled), cy / (3 * doubled)];
}

/** The inner point of the simple polygon farthest from its boundary, to within `precisionM`; unrounded. */
export function poleOfInaccessibility(vertices: readonly Point[], precisionM = POLE_PRECISION_M): Point {
  let minX = Infinity;
  let minY = Infinity;
  let maxX = -Infinity;
  let maxY = -Infinity;
  for (const [x, y] of vertices) {
    minX = Math.min(minX, x);
    minY = Math.min(minY, y);
    maxX = Math.max(maxX, x);
    maxY = Math.max(maxY, y);
  }
  const width = maxX - minX;
  const height = maxY - minY;
  const cellSize = Math.min(width, height);
  if (cellSize <= DEGENERATE_M) return vertices[0];
  const queue = new CellQueue();
  let pushed = 0;
  const cell = (x: number, y: number, half: number): Cell => {
    const distance = signedDistance(x, y, vertices);
    return { x, y, half, distance, potential: distance + half * Math.sqrt(2), order: 0 };
  };
  const push = (item: Cell): void => {
    item.order = pushed;
    pushed += 1;
    queue.push(item);
  };

  const half = cellSize / 2;
  for (let x = minX; x < maxX; x += cellSize) {
    for (let y = minY; y < maxY; y += cellSize) push(cell(x + half, y + half, half));
  }
  const centre = areaCentroid(vertices);
  let best = cell(centre[0], centre[1], 0);
  const boxCentre = cell(minX + width / 2, minY + height / 2, 0);
  if (boxCentre.distance > best.distance) best = boxCentre;

  while (queue.size > 0) {
    const current = queue.pop();
    if (current.distance > best.distance) best = current;
    if (current.potential - best.distance <= precisionM) continue;
    const h = current.half / 2;
    push(cell(current.x - h, current.y - h, h));
    push(cell(current.x + h, current.y - h, h));
    push(cell(current.x - h, current.y + h, h));
    push(cell(current.x + h, current.y + h, h));
  }
  return [best.x, best.y];
}

// ── Horizontal room ──────────────────────────────────────────────────────────

/**
 * Width of the widest horizontal text centred on `point` inside the polygon: twice the shorter reach along the chord
 * `y = point_y` that contains it (edges half-open in y). `null` when the point lies in no inside stretch.
 */
export function centredRoom(vertices: readonly Point[], point: Point): number | null {
  const [px, py] = point;
  const crossings: number[] = [];
  const count = vertices.length;
  for (let i = 0, j = count - 1; i < count; j = i, i += 1) {
    const a = vertices[i];
    const b = vertices[j];
    if (a[1] > py !== b[1] > py) crossings.push(a[0] + ((py - a[1]) * (b[0] - a[0])) / (b[1] - a[1]));
  }
  crossings.sort((m, n) => m - n);
  for (let k = 0; k + 1 < crossings.length; k += 2) {
    const left = crossings[k];
    const right = crossings[k + 1];
    if (left <= px && px <= right) return 2 * Math.min(px - left, right - px);
  }
  return null;
}

// ── Label anchor ─────────────────────────────────────────────────────────────

function segmentLength(a: Point, b: Point): number {
  const dx = b[0] - a[0];
  const dy = b[1] - a[1];
  return Math.sqrt(dx * dx + dy * dy);
}

function polylineMidpoint(vertices: readonly Point[]): Point {
  const lengths: number[] = [];
  for (let i = 1; i < vertices.length; i += 1) lengths.push(segmentLength(vertices[i - 1], vertices[i]));
  let remaining = lengths.reduce((sum, length) => sum + length, 0) / 2;
  for (let i = 0; i < lengths.length; i += 1) {
    const length = lengths[i];
    if (length > 0 && remaining <= length) {
      const t = remaining / length;
      const a = vertices[i];
      const b = vertices[i + 1];
      return [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t];
    }
    remaining -= length;
  }
  return vertices[0];
}

function rounded(point: Point, widthM: number): LabelAnchor {
  return { point: [roundLength(point[0]), roundLength(point[1])], widthM: roundLength(widthM) };
}

/** The label centre of `geometry` (plan frame) and the horizontal room for its text (GP-UX-047). */
export function labelAnchor(geometry: Geometry): LabelAnchor {
  if (geometry.kind === 'point') return rounded(geometry.origin, 0);
  if (geometry.kind === 'circle') return rounded(anchor(geometry), 2 * geometry.radius_m);
  const shape = toShape(geometry);
  if (shape.kind === 'circle') return rounded(shape.center, 2 * shape.radiusM);
  if (geometry.kind === 'polyline') {
    const [minX, , maxX] = boundingBox(geometry);
    return rounded(polylineMidpoint(shape.vertices), maxX - minX);
  }
  let localPoint: Point;
  if (geometry.kind === 'rect') {
    localPoint = [geometry.width_m / 2, geometry.length_m / 2];
  } else {
    const local = toLocalShape(geometry);
    localPoint = local.kind === 'vertices' ? poleOfInaccessibility(local.vertices) : [0, 0];
  }
  const point = transformBedToPlan(localPoint, geometry);
  let room = centredRoom(shape.vertices, point);
  if (room === null) {
    const [minX, , maxX] = boundingBox(geometry);
    room = maxX - minX;
  }
  return rounded(point, room);
}

/**
 * Shorten `text` to `maxChars` with an ellipsis (GP-UX-047): whitespace runs collapse to one space, and the cut
 * drops trailing spaces before the "…" - the rule of the PDF writer (`plan_svg_engine._truncate`).
 */
export function truncateLabel(text: string, maxChars: number): string {
  const cleaned = text.split(/\s+/).filter(Boolean).join(' ');
  if (cleaned.length <= maxChars) return cleaned;
  return `${cleaned.slice(0, Math.max(1, maxChars - 1)).trimEnd()}…`;
}
