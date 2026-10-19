/**
 * Planting layout of a bed — TypeScript port of
 * `app/domain/calculators/planting_layout_calculator.py` (REQ-053 GP-FR-060/062/063/073).
 *
 * The Python module is the reference and carries the full rationale (axes, inset rule, strategies,
 * upper bound); this port mirrors it operation for operation so both sides produce the same
 * points. Both run against `spec/e2e-testcases/fixtures/garden-plan-vectors.json` (GP-ACC-017/018/043,
 * §19.6). The server answer wins on any difference (GP-FR-063): this port feeds the instant preview
 * of the planting dialog, the preview endpoint confirms it.
 *
 * Pure: no I/O, no React. Positions are in the **bed frame** (anchor at (0, 0), no rotation, §9.2),
 * rounded to the storage precision of 0.001 m.
 */

import {
  areaM2,
  roundLength,
  shoelaceArea,
  signedDistanceToPolygon,
  toLocalShape,
  type Shape,
  type VertexShape,
} from './geometry';
import type { Geometry, Point } from './types';

export type LayoutStrategy = 'grid' | 'rows' | 'triangular' | 'zone' | 'free';
export type RowDirection = 'along_length' | 'along_width';

/** GP-FR-062 / V-22: positions one layout (and one slot batch) may carry. */
export const MAX_LAYOUT_POSITIONS = 2000;
/** Candidates the grid walk may visit (5x the position cap). */
export const MAX_LAYOUT_CANDIDATES = 10_000;
/** GP-FR-060: `spacing_cm` / `row_spacing_cm` bounds (centimetres). */
export const MIN_SPACING_CM = 5;
export const MAX_SPACING_CM = 1500;
/** GP-FR-062: `spacing < mature_width x 0.7` is worth a warning. */
export const MATURE_WIDTH_FACTOR = 0.7;
/** Row factor of a staggered layout (`slot_capacity_calculator.TRIANGULAR_ROW_FACTOR`). */
export const TRIANGULAR_ROW_FACTOR = 0.866;

const EPSILON = 1e-9;
const COUNT_EPSILON = 1e-6;
export const SPACING_TOLERANCE_M = 0.002;
const CIRCLE_ZONE_VERTICES = 32;

export const CODE_TOO_MANY_POSITIONS = 'layout.too_many_positions';
export const CODE_BED_NOT_AN_AREA = 'layout.bed_not_an_area';
export const CODE_ROW_SPACING_REQUIRED = 'layout.row_spacing_required';
export const CODE_SPACING_OUT_OF_RANGE = 'layout.spacing_out_of_range';
export const WARNING_SPACING_BELOW_MATURE_WIDTH = 'layout.spacing_below_mature_width';
export const WARNING_NO_POSITION_FITS = 'layout.no_position_fits';
export const WARNING_SPACING_BELOW_MINIMUM = 'planting.spacing_below_minimum';
export const WARNING_ZONE_INSET_NOT_APPLIED = 'layout.zone_inset_not_applied';

/** The layout-relevant fields of a planting-run entry (GP-FR-060), in centimetres. */
export interface EntryLayout {
  layout_strategy: LayoutStrategy;
  spacing_cm: number;
  row_spacing_cm?: number | null;
  row_direction?: RowDirection | null;
  edge_margin_along_cm?: number | null;
  edge_margin_across_cm?: number | null;
  /** Row indices (0-based) this entry occupies when rows alternate between entries (GP-FR-070). */
  row_assignment?: number[] | null;
  /** Steckbrief `mature_width_cm` (lower bound) - only used for the warning. */
  mature_width_cm?: number | null;
}

export interface LayoutSlot {
  slot_role: 'position' | 'zone';
  /** `[x, y]` of a position; `null` for a zone. */
  point: Point | null;
  /** Outline of a zone, closed implicitly; `null` for a position. */
  outline: Point[] | null;
  row_index: number | null;
  /** 1-based rank in layout order (row by row). */
  sequence: number;
  capacity_plants: number;
}

export interface LayoutWarning {
  code: string;
  detail: Record<string, number>;
}

export interface LayoutResult {
  slots: LayoutSlot[];
  /** Plants the slots hold (positions: one each; zone: its capacity); after `maxCount`. */
  count: number;
  /** The most this entry could place in the bed before `maxCount` truncates (GP-FR-073). */
  capacity_max: number;
  warnings: LayoutWarning[];
}

/** A refusal the server publishes under the same dotted `code` (422). */
export class LayoutError extends Error {
  readonly code: string;

  readonly estimated: number | null;

  constructor(code: string, message: string, estimated: number | null = null) {
    super(message);
    this.name = 'LayoutError';
    this.code = code;
    this.estimated = estimated;
  }
}

// ── Parameters ───────────────────────────────────────────────────────────────

function rowSpacingM(entry: EntryLayout): number {
  const spacing = entry.spacing_cm / 100;
  const strategy = entry.layout_strategy;
  if (strategy === 'rows') return (entry.row_spacing_cm ?? 0) / 100;
  if (strategy === 'triangular') return spacing * TRIANGULAR_ROW_FACTOR;
  if (strategy === 'zone' && entry.row_spacing_cm) return entry.row_spacing_cm / 100;
  return spacing;
}

function validate(entry: EntryLayout): void {
  if (!(entry.spacing_cm >= MIN_SPACING_CM && entry.spacing_cm <= MAX_SPACING_CM)) {
    throw new LayoutError(
      CODE_SPACING_OUT_OF_RANGE,
      `spacing_cm must lie within ${MIN_SPACING_CM}..${MAX_SPACING_CM}.`,
    );
  }
  if (entry.layout_strategy === 'rows') {
    const rowSpacing = entry.row_spacing_cm;
    if (rowSpacing === null || rowSpacing === undefined) {
      throw new LayoutError(CODE_ROW_SPACING_REQUIRED, 'The rows layout needs a row_spacing_cm.');
    }
    if (!(rowSpacing >= MIN_SPACING_CM && rowSpacing <= MAX_SPACING_CM)) {
      throw new LayoutError(
        CODE_SPACING_OUT_OF_RANGE,
        `row_spacing_cm must lie within ${MIN_SPACING_CM}..${MAX_SPACING_CM}.`,
      );
    }
  }
}

/** `[along, across]` edge margins in metres; the defaults are half a spacing (GP-FR-060). */
function marginsM(entry: EntryLayout, rowSpacing: number): [number, number] {
  const zone = entry.layout_strategy === 'zone';
  const defaultAlong = zone ? 0 : entry.spacing_cm / 200;
  const defaultAcross = zone ? 0 : rowSpacing / 2;
  const along =
    entry.edge_margin_along_cm === null || entry.edge_margin_along_cm === undefined
      ? defaultAlong
      : entry.edge_margin_along_cm / 100;
  const across =
    entry.edge_margin_across_cm === null || entry.edge_margin_across_cm === undefined
      ? defaultAcross
      : entry.edge_margin_across_cm / 100;
  return [along, across];
}

/** `area / (spacing x row_spacing)` - the pre-estimate of GP-FR-062; no point is generated. */
export function estimatePositions(bed: Geometry, entry: EntryLayout): number {
  validate(entry);
  const area = areaM2(bed);
  const cell = (entry.spacing_cm / 100) * rowSpacingM(entry);
  if (area <= 0 || cell <= 0) return 0;
  return Math.floor(area / cell + COUNT_EPSILON);
}

// ── Geometry of the bed frame ────────────────────────────────────────────────

type Box = [number, number, number, number];

function shapeBox(shape: Shape): Box {
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

/** Whether the segment `a-b` meets the box (Liang-Barsky); a degenerate side has no interior. */
function segmentHitsBox(
  a: Point,
  b: Point,
  x0: number,
  x1: number,
  y0: number,
  y1: number,
): boolean {
  const dx = b[0] - a[0];
  const dy = b[1] - a[1];
  if ((x0 === x1 && dx === 0) || (y0 === y1 && dy === 0)) return false;
  let t0 = 0;
  let t1 = 1;
  const clips: [number, number][] = [
    [-dx, a[0] - x0],
    [dx, x1 - a[0]],
    [-dy, a[1] - y0],
    [dy, y1 - a[1]],
  ];
  for (const [p, q] of clips) {
    if (p === 0) {
      if (q < 0) return false;
    } else {
      const r = q / p;
      if (p < 0) {
        if (r > t1) return false;
        t0 = Math.max(t0, r);
      } else {
        if (r < t0) return false;
        t1 = Math.min(t1, r);
      }
    }
  }
  return t0 <= t1;
}

/** Whether the box of half-extents `(halfX, halfY)` around `(x, y)` lies inside `shape`. */
function boxFits(shape: Shape, x: number, y: number, halfX: number, halfY: number): boolean {
  if (shape.kind === 'circle') {
    const [cx, cy] = shape.center;
    const reach = Math.hypot(Math.abs(x - cx) + halfX, Math.abs(y - cy) + halfY);
    return reach <= shape.radiusM + EPSILON;
  }
  const { vertices } = shape;
  if (signedDistanceToPolygon([x, y], vertices) < -EPSILON) return false;
  if (halfX <= 0 && halfY <= 0) return true;
  const hx = Math.max(halfX - EPSILON, 0);
  const hy = Math.max(halfY - EPSILON, 0);
  const count = vertices.length;
  for (let i = 0; i < count; i += 1) {
    if (segmentHitsBox(vertices[i], vertices[(i + 1) % count], x - hx, x + hx, y - hy, y + hy)) {
      return false;
    }
  }
  return true;
}

/** Smallest distance between two of `points` (`null` for fewer than two); O(n) via a cell hash. */
function closestPairM(points: Point[], cellM: number): number | null {
  const cells = new Map<string, Point[]>();
  const cellOf = (point: Point): [number, number] => [
    Math.floor(point[0] / cellM),
    Math.floor(point[1] / cellM),
  ];
  for (const point of points) {
    const [cx, cy] = cellOf(point);
    const id = `${cx},${cy}`;
    const bucket = cells.get(id);
    if (bucket) bucket.push(point);
    else cells.set(id, [point]);
  }
  let best: number | null = null;
  for (const members of cells.values()) {
    const [cx, cy] = cellOf(members[0]);
    for (let dx = -1; dx <= 1; dx += 1) {
      for (let dy = -1; dy <= 1; dy += 1) {
        const others = cells.get(`${cx + dx},${cy + dy}`) ?? [];
        for (const other of others) {
          for (const point of members) {
            if (point !== other) {
              const distance = Math.hypot(point[0] - other[0], point[1] - other[1]);
              if (best === null || distance < best) best = distance;
            }
          }
        }
      }
    }
  }
  return best;
}

function roundPoint(x: number, y: number): Point {
  return [roundLength(x), roundLength(y)];
}

function tooMany(estimated: number): LayoutError {
  return new LayoutError(
    CODE_TOO_MANY_POSITIONS,
    `A layout holds at most ${MAX_LAYOUT_POSITIONS} positions; this one would need about ${estimated}.`,
    estimated,
  );
}

function matureWidthWarnings(entry: EntryLayout): LayoutWarning[] {
  const width = entry.mature_width_cm;
  if (
    width !== null &&
    width !== undefined &&
    width > 0 &&
    entry.spacing_cm < width * MATURE_WIDTH_FACTOR
  ) {
    return [
      {
        code: WARNING_SPACING_BELOW_MATURE_WIDTH,
        detail: { spacing_cm: entry.spacing_cm, mature_width_cm: width },
      },
    ];
  }
  return [];
}

interface Axes {
  rowsAlongX: boolean;
  box: Box;
}

function axesOf(shape: Shape, entry: EntryLayout): Axes {
  const box = shapeBox(shape);
  const [xMin, yMin, xMax, yMax] = box;
  const longerIsX = xMax - xMin >= yMax - yMin;
  const rowsAlongX = ((entry.row_direction ?? 'along_length') === 'along_length') === longerIsX;
  return { rowsAlongX, box };
}

// ── Layout ───────────────────────────────────────────────────────────────────

/** The positions of `entry` in the bed frame of `bed` (GP-FR-062). */
export function computeLayout(
  bed: Geometry,
  entry: EntryLayout,
  maxCount: number | null = null,
): LayoutResult {
  const estimated = estimatePositions(bed, entry); // validates the entry
  const warnings = matureWidthWarnings(entry);
  const shape = toLocalShape(bed);
  if (shape.kind === 'vertices' && !shape.closed) {
    throw new LayoutError(
      CODE_BED_NOT_AN_AREA,
      'A planting layout needs a bed that encloses an area (rect, circle or polygon).',
    );
  }
  if (entry.layout_strategy === 'free') {
    return { slots: [], count: 0, capacity_max: estimated, warnings };
  }
  if (entry.layout_strategy === 'zone') return zoneLayout(shape, entry, maxCount, warnings);
  // An entry that takes only some rows (GP-FR-070) holds a fraction of the area estimate, so it is
  // bounded by the candidate walk and the count of the real result instead.
  if (estimated > MAX_LAYOUT_POSITIONS && !entry.row_assignment) throw tooMany(estimated);
  return pointLayout(shape, entry, maxCount, warnings);
}

function pointLayout(
  shape: Shape,
  entry: EntryLayout,
  maxCount: number | null,
  warnings: LayoutWarning[],
): LayoutResult {
  const spacing = entry.spacing_cm / 100;
  const rowSpacing = rowSpacingM(entry);
  const [marginAlong, marginAcross] = marginsM(entry, rowSpacing);
  const { rowsAlongX, box } = axesOf(shape, entry);
  const [xMin, yMin, xMax, yMax] = box;
  const [uMin, uMax, vMin, vMax] = rowsAlongX ? [xMin, xMax, yMin, yMax] : [yMin, yMax, xMin, xMax];
  const [halfX, halfY] = rowsAlongX ? [marginAlong, marginAcross] : [marginAcross, marginAlong];

  const uSpan = uMax - uMin - 2 * marginAlong;
  const vSpan = vMax - vMin - 2 * marginAcross;
  const shift = entry.layout_strategy === 'triangular' ? spacing / 2 : 0;
  const candidates =
    (Math.floor(uSpan / spacing + EPSILON) + 1) * (Math.floor(vSpan / rowSpacing + EPSILON) + 1);
  if (uSpan >= -EPSILON && vSpan >= -EPSILON && candidates > MAX_LAYOUT_CANDIDATES) {
    throw tooMany(candidates);
  }

  const wantedRows = entry.row_assignment ? new Set(entry.row_assignment) : null;
  const points: { row: number; point: Point }[] = [];
  let row = 0;
  let v = vMin + marginAcross;
  while (v <= vMax - marginAcross + EPSILON) {
    if (wantedRows === null || wantedRows.has(row)) {
      const offset = row % 2 === 1 ? shift : 0;
      let step = 0;
      let u = uMin + marginAlong + offset;
      while (u <= uMax - marginAlong + EPSILON) {
        const [x, y] = rowsAlongX ? [u, v] : [v, u];
        if (boxFits(shape, x, y, halfX, halfY)) {
          points.push({ row, point: roundPoint(x, y) });
          if (points.length > MAX_LAYOUT_POSITIONS) throw tooMany(points.length);
        }
        step += 1;
        u = uMin + marginAlong + offset + step * spacing;
      }
    }
    row += 1;
    v = vMin + marginAcross + row * rowSpacing;
  }

  const capacityMax = points.length;
  const resultWarnings = [...warnings];
  const closest = closestPairM(
    points.map((entryPoint) => entryPoint.point),
    spacing,
  );
  if (closest !== null && closest < spacing - SPACING_TOLERANCE_M) {
    resultWarnings.push({
      code: WARNING_SPACING_BELOW_MINIMUM,
      detail: { spacing_cm: entry.spacing_cm, closest_cm: Math.round(closest * 1000) / 10 },
    });
  }
  const kept = maxCount === null ? points : points.slice(0, Math.max(maxCount, 0));
  const slots: LayoutSlot[] = kept.map(({ row: rowIndex, point }, index) => ({
    slot_role: 'position',
    point,
    outline: null,
    row_index: rowIndex,
    sequence: index + 1,
    capacity_plants: 1,
  }));
  if (capacityMax === 0) resultWarnings.push({ code: WARNING_NO_POSITION_FITS, detail: {} });
  return { slots, count: slots.length, capacity_max: capacityMax, warnings: resultWarnings };
}

function isAxisAlignedRect(vertices: Point[], box: Box): boolean {
  const [xMin, yMin, xMax, yMax] = box;
  const corners = new Set([
    `${xMin},${yMin}`,
    `${xMax},${yMin}`,
    `${xMax},${yMax}`,
    `${xMin},${yMax}`,
  ]);
  const own = new Set(vertices.map(([x, y]) => `${x},${y}`));
  return vertices.length === 4 && own.size === 4 && [...own].every((corner) => corners.has(corner));
}

/** The outline of a zone slot and whether the requested margins were applied to it. */
function zoneOutline(shape: Shape, marginX: number, marginY: number): [Point[], number, boolean] {
  const insets = marginX > 0 || marginY > 0;
  if (shape.kind === 'circle') {
    const [cx, cy] = shape.center;
    const outline: Point[] = [];
    for (let i = 0; i < CIRCLE_ZONE_VERTICES; i += 1) {
      const angle = (2 * Math.PI * i) / CIRCLE_ZONE_VERTICES;
      outline.push([cx + shape.radiusM * Math.cos(angle), cy + shape.radiusM * Math.sin(angle)]);
    }
    return [outline, Math.PI * shape.radiusM ** 2, !insets];
  }
  const vertexShape: VertexShape = shape;
  const box = shapeBox(shape);
  if (isAxisAlignedRect(vertexShape.vertices, box)) {
    const [xMin, yMin, xMax, yMax] = box;
    const loX = xMin + marginX;
    const hiX = xMax - marginX;
    const loY = yMin + marginY;
    const hiY = yMax - marginY;
    if (hiX <= loX || hiY <= loY) return [[], 0, true];
    return [
      [
        [loX, loY],
        [hiX, loY],
        [hiX, hiY],
        [loX, hiY],
      ],
      (hiX - loX) * (hiY - loY),
      true,
    ];
  }
  return [vertexShape.vertices, shoelaceArea(vertexShape.vertices), !insets];
}

function zoneLayout(
  shape: Shape,
  entry: EntryLayout,
  maxCount: number | null,
  warnings: LayoutWarning[],
): LayoutResult {
  const rowSpacing = rowSpacingM(entry);
  const [marginAlong, marginAcross] = marginsM(entry, rowSpacing);
  const { rowsAlongX } = axesOf(shape, entry);
  const [marginX, marginY] = rowsAlongX ? [marginAlong, marginAcross] : [marginAcross, marginAlong];

  const [outline, zoneArea, applied] = zoneOutline(shape, marginX, marginY);
  const resultWarnings = [...warnings];
  if (!applied) resultWarnings.push({ code: WARNING_ZONE_INSET_NOT_APPLIED, detail: {} });
  const cell = (entry.spacing_cm / 100) * rowSpacing;
  const capacityMax = cell > 0 ? Math.floor(zoneArea / cell + COUNT_EPSILON) : 0;
  if (capacityMax === 0) {
    resultWarnings.push({ code: WARNING_NO_POSITION_FITS, detail: {} });
    return { slots: [], count: 0, capacity_max: 0, warnings: resultWarnings };
  }
  const count = maxCount === null ? capacityMax : Math.max(Math.min(maxCount, capacityMax), 0);
  if (count === 0) {
    return { slots: [], count: 0, capacity_max: capacityMax, warnings: resultWarnings };
  }
  const slot: LayoutSlot = {
    slot_role: 'zone',
    point: null,
    outline: outline.map(([x, y]) => roundPoint(x, y)),
    row_index: null,
    sequence: 1,
    capacity_plants: count,
  };
  return { slots: [slot], count, capacity_max: capacityMax, warnings: resultWarnings };
}
