/**
 * The measure tool's state machine (REQ-053 GP-UX-071, #2913): a distance on the plan, click by click. The first
 * click sets the start, the pointer drags a live line with its length, every further click fixes a point of a
 * polyline; Enter, the touch bar's "Finish", a double click or a click on the last point ends the measurement. A
 * finished measurement stays until Esc clears it, the next click starts a new one or the tool changes.
 *
 * Transient: the machine has no effects - nothing reaches the plan, no operation, no undo step. Points snap like a
 * drawn point (`env.snapPoint`: grid and object snap, Alt bypasses).
 */
import { MIN_DIMENSION_M } from '../../model/geometry';
import type { Point } from '../../model/types';
import { dragThresholdPx, distancePx, type PointerSample, type ToolEnv } from './machineTypes';

export type MeasureState =
  | { kind: 'idle' }
  /** Being measured: the fixed points, where the pointer hovers, and the press that may become a click. */
  | { kind: 'open'; points: Point[]; hoverM: Point | null; pressPx: Point | null }
  /** Finished: shown until cleared; a click starts the next measurement. */
  | { kind: 'done'; points: Point[]; pressPx: Point | null };

export const INITIAL_MEASURE_STATE: MeasureState = { kind: 'idle' };

/** Clicking this close to the last point (two or more set) finishes - the second click of a double click does. */
const FINISH_RADIUS_PX = 12;

/** What the overlay and the status text show of a measurement. */
export interface MeasureView {
  /** The drawn path in model metres: the fixed points and, while open, the hovered point. */
  pathM: Point[];
  /** The length of each segment of `pathM`, in metres. */
  segmentsM: number[];
  /** The length of `pathM`. */
  totalM: number;
  /** The fixed points only (no hover): what the status text announces. */
  fixedPoints: number;
  fixedTotalM: number;
  done: boolean;
}

function snapped(sample: PointerSample, env: ToolEnv): Point {
  return env.snapPoint(env.toModel(sample.pointPx), sample.alt, sample.pointerType);
}

/** The lengths of the segments of a polyline and their sum. */
export function polylineLengths(points: readonly Point[]): { segmentsM: number[]; totalM: number } {
  const segmentsM: number[] = [];
  for (let i = 1; i < points.length; i += 1) {
    segmentsM.push(Math.hypot(points[i][0] - points[i - 1][0], points[i][1] - points[i - 1][1]));
  }
  return { segmentsM, totalM: segmentsM.reduce((sum, length) => sum + length, 0) };
}

export function measureDown(state: MeasureState, sample: PointerSample, env: ToolEnv): MeasureState {
  if (state.kind === 'done') return { ...state, pressPx: sample.pointPx };
  const points = state.kind === 'open' ? state.points : [];
  return { kind: 'open', points, hoverM: snapped(sample, env), pressPx: sample.pointPx };
}

/** `pressed` = a button is down. Without it the pointer only hovers: the live line follows it. */
export function measureMove(
  state: MeasureState,
  sample: PointerSample,
  env: ToolEnv,
  pressed: boolean,
): MeasureState {
  if (state.kind === 'idle') return state;
  // A press that turned into a drag is not a click: it sets no point.
  const travelled =
    state.pressPx !== null &&
    pressed &&
    distancePx(state.pressPx, sample.pointPx) >= dragThresholdPx(sample.pointerType);
  const pressPx = travelled ? null : state.pressPx;
  if (state.kind === 'done') return pressPx === state.pressPx ? state : { ...state, pressPx };
  return { ...state, hoverM: snapped(sample, env), pressPx };
}

export function measureUp(state: MeasureState, sample: PointerSample, env: ToolEnv): MeasureState {
  if (state.kind === 'idle') return state;
  if (state.pressPx === null) return state;
  const point = snapped(sample, env);
  // A click after a finished measurement starts the next one.
  if (state.kind === 'done') return { kind: 'open', points: [point], hoverM: point, pressPx: null };
  const { points } = state;
  const last = points[points.length - 1];
  const radius = sample.pointerType === 'touch' ? FINISH_RADIUS_PX + 6 : FINISH_RADIUS_PX;
  if (last !== undefined && points.length >= 2 && distancePx(env.toScreen(last), sample.pointPx) <= radius) {
    return measureFinish({ ...state, pressPx: null });
  }
  const duplicate = last !== undefined && Math.hypot(point[0] - last[0], point[1] - last[1]) < MIN_DIMENSION_M;
  return { kind: 'open', points: duplicate ? points : [...points, point], hoverM: point, pressPx: null };
}

/** Enter, "Finish" or a click on the last point: from two points on the measurement is complete. */
export function measureFinish(state: MeasureState): MeasureState {
  if (state.kind !== 'open' || state.points.length < 2) return state;
  return { kind: 'done', points: state.points, pressPx: null };
}

/** Backspace or the touch bar's "Undo": the last point goes; a finished measurement opens again. */
export function measureUndoPoint(state: MeasureState): MeasureState {
  if (state.kind === 'idle') return state;
  const points = state.points.slice(0, -1);
  if (points.length === 0) return INITIAL_MEASURE_STATE;
  return { kind: 'open', points, hoverM: null, pressPx: null };
}

/** A pointer cancel ends the press, never the measurement. */
export function measureRelease(state: MeasureState): MeasureState {
  return state.kind === 'idle' || state.pressPx === null ? state : { ...state, pressPx: null };
}

export function measurePointCount(state: MeasureState): number {
  return state.kind === 'idle' ? 0 : state.points.length;
}

/** The measurement can be finished now (two fixed points, not finished yet). */
export function measureFinishable(state: MeasureState): boolean {
  return state.kind === 'open' && state.points.length >= 2;
}

export function measureView(state: MeasureState): MeasureView | null {
  if (state.kind === 'idle' || state.points.length === 0) return null;
  const hover = state.kind === 'open' ? state.hoverM : null;
  const last = state.points[state.points.length - 1];
  const pathM = hover && (hover[0] !== last[0] || hover[1] !== last[1]) ? [...state.points, hover] : state.points;
  const path = polylineLengths(pathM);
  return {
    pathM,
    segmentsM: path.segmentsM,
    totalM: path.totalM,
    fixedPoints: state.points.length,
    fixedTotalM: polylineLengths(state.points).totalM,
    done: state.kind === 'done',
  };
}
