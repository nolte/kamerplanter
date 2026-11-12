/**
 * Editing the garden boundary / flat outline (REQ-053 UC-01, GP-FR-019/022/023/032, #2890): the handles of the
 * boundary while the boundary mode is on. The boundary is not a selectable object (GP-UX-032 puts it last in the hit
 * order, GP-UX-037 keeps it out of every selection), so it gets its own small machine instead of a selection: a press
 * on one of its handles reshapes it exactly like a bed's handle (corner, edge, rotate, polygon point, "+" on an edge),
 * a press anywhere else is not this machine's - the editor pans then.
 *
 * Releasing commits ONE `set_boundary` (one undo step, GP-FR-155) that keeps the north angle. The live check is the
 * server's V-19 seen from the boundary (`boundaryViolation`): a shape that would leave a bed or object outside is
 * drawn red and, released, reported as a notice - the stored boundary stays, nothing is clipped.
 */
import { toShape } from '../../model/geometry';
import type { Geometry, Point, PlanOperation } from '../../model/types';
import { insertVertex, moveGeometry } from './geometryEdit';
import { computeHandles, handleAt, type Handle, type HandleSet } from './handles';
import {
  distancePx,
  dragThresholdPx,
  EMPTY_OVERLAY,
  type Effect,
  type Overlay,
  type PointerSample,
  type Step,
  type ToolEnv,
} from './machineTypes';
import { reshapeByHandle, rotationOfHandle } from './selectMachine';
import { boundaryViolation } from './validation';

export type BoundaryState =
  | {
      kind: 'idle';
      /** The polygon point picked by a click on its handle: "Punkt löschen" acts on it (GP-FR-023). */
      vertex: number | null;
    }
  | {
      kind: 'handle';
      vertex: number | null;
      handle: Handle;
      start: Geometry;
      downPx: Point;
      downModel: Point;
      draft: Geometry;
      violation: string | null;
      dragged: boolean;
      /** A "+" handle inserted a vertex into `start` already. */
      inserted: boolean;
    };

export const INITIAL_BOUNDARY_STATE: BoundaryState = { kind: 'idle', vertex: null };

/** The boundary of the plan, or `null` (then the mode draws one). */
export function planBoundary(env: Pick<ToolEnv, 'plan'>): Geometry | null {
  return env.plan.settings?.boundary ?? null;
}

/** The set_boundary of a new outline; the north angle stays what it is (UC-01: north is set on its own). */
export function setBoundaryOp(env: Pick<ToolEnv, 'plan'>, boundary: Geometry): PlanOperation {
  const northAngle = env.plan.settings?.north_angle_deg;
  return { op: 'set_boundary', boundary, ...(northAngle != null ? { north_angle_deg: northAngle } : {}) };
}

/** The handles the boundary shows: of the shape being dragged while a handle moves, else of the stored one. */
export function boundaryHandles(state: BoundaryState, env: Pick<ToolEnv, 'plan' | 'pxPerM'>): HandleSet | null {
  const boundary = planBoundary(env);
  if (boundary === null) return null;
  const shown = state.kind === 'handle' && state.dragged ? state.draft : boundary;
  return computeHandles(shown, env.pxPerM);
}

/**
 * A press: on a boundary handle it starts that handle's drag; elsewhere it returns `null` - the press is not the
 * boundary's (the editor pans with it).
 */
export function boundaryDown(state: BoundaryState, sample: PointerSample, env: ToolEnv): Step<BoundaryState> | null {
  const boundary = planBoundary(env);
  if (boundary === null) return null;
  const handle = handleAt(computeHandles(boundary, env.pxPerM).handles, env.toScreen, sample.pointPx);
  if (handle === null) return null;
  let start = boundary;
  let active = handle;
  let inserted = false;
  if (handle.kind === 'midpoint' && handle.index !== undefined) {
    // The "+" handle puts a new point on the edge; from here on the new point is dragged.
    start = insertVertex(start, handle.index, handle.pointM);
    active = { id: `v${handle.index + 1}`, kind: 'vertex', pointM: handle.pointM, index: handle.index + 1 };
    inserted = true;
  }
  return {
    state: {
      kind: 'handle',
      vertex: state.vertex,
      handle: active,
      start,
      downPx: sample.pointPx,
      downModel: env.toModel(sample.pointPx),
      draft: start,
      violation: null,
      dragged: false,
      inserted,
    },
    effects: [],
  };
}

export function boundaryMove(state: BoundaryState, sample: PointerSample, env: ToolEnv): BoundaryState {
  if (state.kind !== 'handle') return state;
  const dragged = state.dragged || distancePx(state.downPx, sample.pointPx) >= dragThresholdPx(sample.pointerType);
  if (!dragged) return state;
  let draft: Geometry;
  if (state.handle.kind === 'rotate') {
    const { pivot, rotateDeg } = rotationOfHandle(state.start, state.downModel, sample, env);
    draft = moveGeometry(state.start, { translate: [0, 0], rotateDeg, pivot });
  } else {
    const pointer = env.snapPoint(env.toModel(sample.pointPx), sample.alt, sample.pointerType);
    draft = reshapeByHandle(state.start, state.handle, pointer, sample.shift);
  }
  return { ...state, dragged, draft, violation: boundaryViolation(env.plan, draft) };
}

export function boundaryUp(state: BoundaryState, env: ToolEnv): Step<BoundaryState> {
  if (state.kind !== 'handle') return { state, effects: [] };
  const { handle } = state;
  if (!state.dragged && !state.inserted) {
    // A click on a polygon point picks it; a click on another handle keeps the pick.
    const vertex = handle.kind === 'vertex' && handle.index !== undefined ? handle.index : state.vertex;
    return { state: { kind: 'idle', vertex }, effects: [] };
  }
  if (state.violation) {
    return { state: { kind: 'idle', vertex: state.vertex }, effects: [{ type: 'notice', code: state.violation }] };
  }
  const vertex = handle.kind === 'vertex' && handle.index !== undefined ? handle.index : null;
  const effects: Effect[] = [{ type: 'commit', ops: [setBoundaryOp(env, state.draft)], label: 'editBoundary' }];
  return { state: { kind: 'idle', vertex }, effects };
}

/** Escape: the drag ends, nothing was committed. */
export function boundaryCancel(state: BoundaryState): BoundaryState {
  return state.kind === 'handle' ? { kind: 'idle', vertex: state.vertex } : state;
}

export function boundaryGestureActive(state: BoundaryState): boolean {
  return state.kind === 'handle';
}

/** The outline being dragged, red while the live check refuses it (GP-UX-053). */
export function boundaryOverlay(state: BoundaryState): Overlay {
  if (state.kind !== 'handle' || !state.dragged) return EMPTY_OVERLAY;
  return {
    shapes: [{ key: 'boundary', shape: toShape(state.draft), invalid: state.violation !== null }],
    marquee: null,
  };
}
