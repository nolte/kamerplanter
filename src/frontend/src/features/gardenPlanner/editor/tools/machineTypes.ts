/**
 * What the tool state machines (`selectMachine`, `drawMachine`, `panMachine`) talk in. A machine is
 * a pure function `(state, pointer event, env) -> { state, effects }`: it never touches the store,
 * the renderer or the DOM, so every gesture - including the aborted ones - is a plain unit test.
 * The hook `useEditorTools` feeds it events and carries out the effects.
 */
import type { PlanModel } from '../../model/planModel';
import type { Point, PlanOperation } from '../../model/types';
import type { PlanTool, SelectionRef, SelectionStack } from '../../state/gardenPlanSlice';
import type { Shape } from '../../model/geometry';

export interface PointerSample {
  /** Canvas pixels, origin top-left. */
  pointPx: Point;
  pointerType: 'mouse' | 'pen' | 'touch';
  shift: boolean;
  /** Alt switches snapping off and makes a click walk down the stack (GP-UX-033, GP-FR-154). */
  alt: boolean;
}

/** The readings the machines need, supplied fresh for every event. */
export interface ToolEnv {
  plan: PlanModel;
  selection: readonly SelectionRef[];
  stack: SelectionStack | null;
  pxPerM: number;
  /** `PlanRenderer.hitTestAll`: keys under a pixel, topmost first. */
  hitTestAll(pointPx: Point): string[];
  toModel(pointPx: Point): Point;
  toScreen(pointM: Point): Point;
  /**
   * The seam for grid and snap (WP 2.5): turns a raw model point into the point the tool uses.
   * `bypass` is Alt. Today it only rounds to the storage precision.
   */
  snapPoint(pointM: Point, bypass: boolean): Point;
  /** Rotation step of the rotate handle: 15, 45 or 90 (GP-FR-008). */
  angleStepDeg: number;
}

export type ActionLabel = 'move' | 'rotate' | 'resize' | 'editPoint' | 'draw' | 'delete';

export type Effect =
  | { type: 'select'; selection: SelectionRef[] }
  | { type: 'stack'; stack: SelectionStack | null }
  | { type: 'commit'; ops: PlanOperation[]; label: ActionLabel }
  | { type: 'pan'; dxPx: number; dyPx: number }
  /** The client refused an edit before it reached the model (`geometry.outside_parent`, `object.locked`, ...). */
  | { type: 'notice'; code: string }
  | { type: 'tool'; tool: PlanTool };

export interface Step<S> {
  state: S;
  effects: Effect[];
}

/** A shape the overlay draws while a gesture is under way. */
export interface OverlayShape {
  key: string;
  shape: Shape;
  /** The live validation failed (GP-UX-053): drawn red. */
  invalid: boolean;
  /** An unfinished outline (polygon being drawn) is not closed. */
  draft?: boolean;
}

export interface Overlay {
  shapes: OverlayShape[];
  /** The marquee in canvas pixels. */
  marquee: { x: number; y: number; width: number; height: number } | null;
}

export const EMPTY_OVERLAY: Overlay = { shapes: [], marquee: null };

/** Pointer travel before a press becomes a drag. */
export function dragThresholdPx(pointerType: PointerSample['pointerType']): number {
  return pointerType === 'touch' ? 8 : 4;
}

export function distancePx(a: Point, b: Point): number {
  return Math.hypot(a[0] - b[0], a[1] - b[1]);
}
