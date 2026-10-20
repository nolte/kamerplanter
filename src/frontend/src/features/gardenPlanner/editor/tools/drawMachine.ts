/**
 * The draw tools' state machine (REQ-053 GP-FR-001..003, GP-UX-053): rect and circle are dragged
 * out, polygon and polyline are built click by click. Finishing a shape is ONE `commit` with one
 * create operation (one undo step) and hands the editor back to the select tool with the new
 * object selected, ready for its handles. A shape the live validation refuses is not created: the
 * machine reports a notice and, for point-by-point shapes, keeps the points so nothing is lost.
 *
 * The new object's parent is the smallest placed location that holds it completely - the same
 * containment rule the server enforces. The bed type and the object type come from the editor's
 * type choice (WP 2.6); without one the bed type is the one most beds of the plan have and the
 * object is a generic `other`.
 */
import { MIN_DIMENSION_M, roundLength, toShape } from '../../model/geometry';
import { newTempKey } from '../../model/planModel';
import type { GardenObjectType, Geometry, Point, PlanOperation } from '../../model/types';
import type { SelectionRef } from '../../state/gardenPlanSlice';
import {
  dragThresholdPx,
  distancePx,
  EMPTY_OVERLAY,
  type Effect,
  type Overlay,
  type PointerSample,
  type Step,
  type ToolEnv,
} from './machineTypes';
import { defaultProps } from './objectTypes';
import { inferParentKey, violationOfNew } from './validation';

export type DrawShape = 'rect' | 'circle' | 'polygon' | 'polyline';
export type DrawTarget = 'bed' | 'garden_object';

export interface DrawOptions {
  target: DrawTarget;
  shape: DrawShape;
  /** Name of the n-th location of the plan ("Beet 4"); keeps i18n out of the machine. */
  newBedName: (n: number) => string;
  /** `location_type_key` of a new bed; the plan's most common bed type when unset. */
  bedTypeKey?: string;
  /** Type of a new garden object; `other` when unset. */
  objectType?: GardenObjectType;
}

export type DrawState =
  | { kind: 'idle' }
  | {
      kind: 'drag';
      startPx: Point;
      startM: Point;
      currentM: Point;
      currentPx: Point;
      square: boolean;
    }
  | { kind: 'points'; points: Point[]; hoverM: Point | null; pressPx: Point | null }
  /** Touch: the first corner of a rectangle or circle is set; the second tap completes it. */
  | { kind: 'corner'; startPx: Point; startM: Point };

export const INITIAL_DRAW_STATE: DrawState = { kind: 'idle' };

/** A polyline is a stroke: this wide until the panel edits it. */
const DEFAULT_POLYLINE_WIDTH_M = 0.3;
/** Placeholder bed type when the plan has no bed to copy it from (the seeded raised bed). */
const FALLBACK_BED_TYPE_KEY = 'raised_bed';
/** Clicking this close to the first or last point finishes a polygon or polyline. */
const FINISH_RADIUS_PX = 12;

function step(state: DrawState, effects: Effect[] = []): Step<DrawState> {
  return { state, effects };
}

function isPointShape(shape: DrawShape): boolean {
  return shape === 'polygon' || shape === 'polyline';
}

/** The bed type most beds of the plan have. */
export function commonBedTypeKey(plan: ToolEnv['plan']): string {
  const counts = new Map<string, number>();
  for (const location of Object.values(plan.locations)) {
    counts.set(location.location_type_key, (counts.get(location.location_type_key) ?? 0) + 1);
  }
  let best = FALLBACK_BED_TYPE_KEY;
  let bestCount = 0;
  for (const [key, count] of counts) {
    if (count > bestCount) [best, bestCount] = [key, count];
  }
  return best;
}

function bedTypeKey(env: ToolEnv): string {
  return commonBedTypeKey(env.plan);
}

function rectBetween(a: Point, b: Point, square: boolean): Geometry | null {
  let dx = b[0] - a[0];
  let dy = b[1] - a[1];
  if (square) {
    const side = Math.max(Math.abs(dx), Math.abs(dy));
    dx = dx < 0 ? -side : side;
    dy = dy < 0 ? -side : side;
  }
  const width = roundLength(Math.abs(dx));
  const length = roundLength(Math.abs(dy));
  if (width < MIN_DIMENSION_M || length < MIN_DIMENSION_M) return null;
  return {
    kind: 'rect',
    origin: [roundLength(Math.min(a[0], a[0] + dx)), roundLength(Math.min(a[1], a[1] + dy))],
    width_m: width,
    length_m: length,
    rotation_deg: 0,
  };
}

function circleAround(center: Point, edge: Point): Geometry | null {
  const radius = roundLength(Math.hypot(edge[0] - center[0], edge[1] - center[1]));
  if (radius < MIN_DIMENSION_M) return null;
  return {
    kind: 'circle',
    origin: [roundLength(center[0]), roundLength(center[1])],
    radius_m: radius,
  };
}

function dragGeometry(
  drag: Extract<DrawState, { kind: 'drag' }>,
  shape: DrawShape,
): Geometry | null {
  return shape === 'circle'
    ? circleAround(drag.startM, drag.currentM)
    : rectBetween(drag.startM, drag.currentM, drag.square);
}

function pointsGeometry(points: readonly Point[], shape: DrawShape): Geometry {
  return shape === 'polygon'
    ? {
        kind: 'polygon',
        points: points.map((p): Point => [roundLength(p[0]), roundLength(p[1])]),
        rotation_deg: 0,
      }
    : {
        kind: 'polyline',
        points: points.map((p): Point => [roundLength(p[0]), roundLength(p[1])]),
        width_m: DEFAULT_POLYLINE_WIDTH_M,
      };
}

/** The effects of a finished shape, or a notice when the live validation refuses it. */
function create(
  env: ToolEnv,
  opts: DrawOptions,
  geometry: Geometry,
): { effects: Effect[]; ok: boolean } {
  const parentKey = inferParentKey(env.plan, geometry);
  const violation = violationOfNew(env.plan, geometry, parentKey);
  if (violation) return { effects: [{ type: 'notice', code: violation }], ok: false };
  const tempKey = newTempKey();
  let op: PlanOperation;
  let ref: SelectionRef;
  if (opts.target === 'bed') {
    op = {
      op: 'create_location',
      temp_key: tempKey,
      data: {
        name: opts.newBedName(Object.keys(env.plan.locations).length + 1),
        location_type_key: opts.bedTypeKey ?? bedTypeKey(env),
        geometry,
        ...(parentKey ? { parent_location_key: parentKey } : {}),
      },
    };
    ref = { entity: 'location', key: tempKey };
  } else {
    op = {
      op: 'create_garden_object',
      temp_key: tempKey,
      data: {
        object_type: opts.objectType ?? 'other',
        geometry,
        props: defaultProps(opts.objectType ?? 'other'),
        ...(parentKey ? { parent_location_key: parentKey } : {}),
      },
    };
    ref = { entity: 'garden_object', key: tempKey };
  }
  return {
    ok: true,
    effects: [
      { type: 'commit', ops: [op], label: 'draw' },
      { type: 'select', selection: [ref] },
      { type: 'stack', stack: null },
      { type: 'tool', tool: 'select' },
    ],
  };
}

// ── events ───────────────────────────────────────────────────────────────────

export function drawDown(
  state: DrawState,
  sample: PointerSample,
  env: ToolEnv,
  opts: DrawOptions,
): Step<DrawState> {
  const point = env.snapPoint(env.toModel(sample.pointPx), sample.alt, sample.pointerType);
  if (state.kind === 'corner' && !isPointShape(opts.shape)) {
    // The second tap: from here on it is an ordinary drag from the first corner.
    return step({
      kind: 'drag',
      // Where the first corner is on screen now - the view may have been panned since the first tap.
      startPx: env.toScreen(state.startM),
      startM: state.startM,
      currentM: point,
      currentPx: sample.pointPx,
      square: sample.shift,
    });
  }
  if (isPointShape(opts.shape)) {
    const points = state.kind === 'points' ? state.points : [];
    return step({ kind: 'points', points, hoverM: point, pressPx: sample.pointPx });
  }
  return step({
    kind: 'drag',
    startPx: sample.pointPx,
    startM: point,
    currentM: point,
    currentPx: sample.pointPx,
    square: sample.shift,
  });
}

/** `pressed` = a button is down. Without it the pointer only hovers (the rubber band of a polygon). */
export function drawMove(
  state: DrawState,
  sample: PointerSample,
  env: ToolEnv,
  pressed: boolean,
): Step<DrawState> {
  const point = env.snapPoint(env.toModel(sample.pointPx), sample.alt, sample.pointerType);
  if (state.kind === 'drag') {
    return step({ ...state, currentM: point, currentPx: sample.pointPx, square: sample.shift });
  }
  if (state.kind === 'points') {
    const travelled =
      state.pressPx !== null &&
      pressed &&
      distancePx(state.pressPx, sample.pointPx) >= dragThresholdPx(sample.pointerType);
    // A press that turned into a drag is not a click: it adds no point.
    return step({ ...state, hoverM: point, pressPx: travelled ? null : state.pressPx });
  }
  return step(state);
}

export function drawUp(
  state: DrawState,
  sample: PointerSample,
  env: ToolEnv,
  opts: DrawOptions,
): Step<DrawState> {
  if (state.kind === 'drag') {
    const tooShort =
      distancePx(state.startPx, sample.pointPx) < dragThresholdPx(sample.pointerType);
    const geometry = tooShort
      ? null
      : dragGeometry(
          {
            ...state,
            currentM: env.snapPoint(env.toModel(sample.pointPx), sample.alt, sample.pointerType),
            square: sample.shift,
          },
          opts.shape,
        );
    if (geometry === null) {
      // A touch that barely moved is a tap: it sets the first corner, the next tap the second.
      return tooShort && sample.pointerType === 'touch'
        ? step({ kind: 'corner', startPx: state.startPx, startM: state.startM })
        : step(INITIAL_DRAW_STATE);
    }
    const { effects } = create(env, opts, geometry);
    return step(INITIAL_DRAW_STATE, effects);
  }
  if (state.kind === 'corner') return step(state);
  if (state.kind !== 'points' || state.pressPx === null) {
    return step(state.kind === 'points' ? { ...state, pressPx: null } : state);
  }
  const point = env.snapPoint(env.toModel(sample.pointPx), sample.alt, sample.pointerType);
  const { points } = state;
  const polygon = opts.shape === 'polygon';
  const radius = sample.pointerType === 'touch' ? FINISH_RADIUS_PX + 6 : FINISH_RADIUS_PX;
  const near = (target: Point) => distancePx(env.toScreen(target), sample.pointPx) <= radius;
  const enough = points.length >= (polygon ? 3 : 2);
  if (
    points.length > 0 &&
    enough &&
    ((polygon && near(points[0])) || near(points[points.length - 1]))
  ) {
    return drawFinish({ ...state, pressPx: null }, env, opts);
  }
  const last = points[points.length - 1];
  const duplicate =
    last !== undefined && Math.hypot(point[0] - last[0], point[1] - last[1]) < MIN_DIMENSION_M;
  return step({
    kind: 'points',
    points: duplicate ? points : [...points, point],
    hoverM: point,
    pressPx: null,
  });
}

/** Enter, the "done" button or a click on the first/last point. */
export function drawFinish(state: DrawState, env: ToolEnv, opts: DrawOptions): Step<DrawState> {
  if (state.kind !== 'points' || !isPointShape(opts.shape)) return step(state);
  const needed = opts.shape === 'polygon' ? 3 : 2;
  if (state.points.length < needed)
    return step(state, [{ type: 'notice', code: 'draw.too_few_points' }]);
  const { effects, ok } = create(env, opts, pointsGeometry(state.points, opts.shape));
  return step(ok ? INITIAL_DRAW_STATE : state, effects);
}

/** Backspace while drawing takes back the last point. */
export function drawUndoPoint(state: DrawState): DrawState {
  if (state.kind !== 'points') return state;
  const points = state.points.slice(0, -1);
  return points.length === 0 ? INITIAL_DRAW_STATE : { ...state, points };
}

export function pointCount(state: DrawState): number {
  return state.kind === 'points' ? state.points.length : 0;
}

export function drawOverlay(state: DrawState, env: ToolEnv, opts: DrawOptions): Overlay {
  if (state.kind === 'drag') {
    const geometry = dragGeometry(state, opts.shape);
    if (geometry === null) return EMPTY_OVERLAY;
    const invalid = violationOfNew(env.plan, geometry, inferParentKey(env.plan, geometry)) !== null;
    return { shapes: [{ key: 'draft', shape: toShape(geometry), invalid }], marquee: null };
  }
  if (state.kind === 'points' && state.points.length > 0) {
    const vertices = state.hoverM ? [...state.points, state.hoverM] : state.points;
    let invalid = false;
    if (state.points.length >= (opts.shape === 'polygon' ? 3 : 2)) {
      const geometry = pointsGeometry(state.points, opts.shape);
      invalid = violationOfNew(env.plan, geometry, inferParentKey(env.plan, geometry)) !== null;
    }
    return {
      shapes: [
        {
          key: 'draft',
          shape: { kind: 'vertices', vertices, closed: false },
          invalid,
          draft: true,
        },
      ],
      marquee: null,
    };
  }
  return EMPTY_OVERLAY;
}
