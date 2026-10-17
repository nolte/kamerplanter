/**
 * The select tool's state machine (REQ-053 GP-FR-020/021/022/023/151/156, GP-UX-032/033/037/048).
 *
 * One press can become: a click (select, Shift toggles, repeated click / Alt+click walks the
 * stack), a move of the selection with everything below an area (GP-FR-151), a marquee on empty
 * ground, or a handle drag (resize, radius, rotate, polygon points). Releasing commits ONE
 * `commit` effect - all operations of the gesture - so a drag is one undo step (GP-FR-155).
 * A gesture the live validation rejects commits nothing and reports a notice (snap-back,
 * GP-UX-053). Escape cancels at any point before the release and changes nothing.
 */
import { anchor, toShape } from '../../model/geometry';
import type { Geometry, Point, PlanEntity, PlanOperation } from '../../model/types';
import type { SelectionRef } from '../../state/gardenPlanSlice';
import { computeHandles, handleAt, type Handle } from './handles';
import {
  geometryCenter,
  insertVertex,
  moveGeometry,
  moveVertex,
  resizeCircle,
  resizeRect,
  rotationDelta,
  translateGeometry,
  type RectHandleId,
} from './geometryEdit';
import { isPlanEntity, moveTargets, type GeometryEntry } from './hierarchy';
import {
  dragThresholdPx,
  distancePx,
  EMPTY_OVERLAY,
  type ActionLabel,
  type Effect,
  type Overlay,
  type PointerSample,
  type Step,
  type ToolEnv,
} from './machineTypes';
import {
  isLockedRef,
  isSelected,
  marqueeSelection,
  nextStackIndex,
  sameRef,
  stackRefs,
  toggleRef,
} from './selection';
import { firstViolation, type DraftChange } from './validation';

export interface VertexSelection {
  key: string;
  index: number;
}

type Gesture =
  | { kind: 'idle' }
  | {
      kind: 'press';
      downPx: Point;
      downModel: Point;
      target: SelectionRef;
      hitKeys: string[];
      hits: SelectionRef[];
      shift: boolean;
      alt: boolean;
      wasSelected: boolean;
      /** The selection once this press has been applied. */
      selection: SelectionRef[];
      /** A refused drag has already said why. */
      refused: boolean;
    }
  | {
      kind: 'move';
      downModel: Point;
      targets: GeometryEntry[];
      primary: GeometryEntry;
      delta: Point;
      violation: string | null;
    }
  | { kind: 'marquee'; downPx: Point; currentPx: Point; additive: boolean }
  | {
      kind: 'handle';
      handle: Handle;
      subject: { entity: PlanEntity; key: string };
      start: Geometry;
      targets: GeometryEntry[];
      downPx: Point;
      downModel: Point;
      draft: DraftChange[];
      violation: string | null;
      /** The pointer travelled far enough to count as a drag. */
      dragged: boolean;
      /** A "+" handle inserted a vertex into `start` already. */
      inserted: boolean;
    };

export interface SelectState {
  gesture: Gesture;
  /** The polygon point picked by a click on its handle: "Punkt löschen" acts on it (GP-FR-023). */
  vertex: VertexSelection | null;
}

export const INITIAL_SELECT_STATE: SelectState = { gesture: { kind: 'idle' }, vertex: null };

const MIN_MOVE_M = 0.0005;

function step(state: SelectState, effects: Effect[] = []): Step<SelectState> {
  return { state, effects };
}

function select(selection: SelectionRef[]): Effect {
  return { type: 'select', selection };
}

/** The one selected, placed, unlocked location or garden object - the only thing that shows handles. */
function editableSubject(
  env: ToolEnv,
): { ref: SelectionRef & { entity: PlanEntity }; geometry: Geometry } | null {
  if (env.selection.length !== 1) return null;
  const ref = env.selection[0];
  if (!isPlanEntity(ref) || isLockedRef(env.plan, ref)) return null;
  const source =
    ref.entity === 'location' ? env.plan.locations[ref.key] : env.plan.gardenObjects[ref.key];
  return source?.geometry ? { ref, geometry: source.geometry } : null;
}

function operationsOf(draft: readonly DraftChange[]): PlanOperation[] {
  return draft.map(({ entity, key, geometry }) => ({
    op: 'update_geometry',
    entity,
    key,
    geometry,
  }));
}

// ── pointer down ─────────────────────────────────────────────────────────────

export function selectDown(
  state: SelectState,
  sample: PointerSample,
  env: ToolEnv,
): Step<SelectState> {
  const { pointPx } = sample;
  const downModel = env.toModel(pointPx);
  const subject = editableSubject(env);
  if (subject) {
    const set = computeHandles(subject.geometry, env.pxPerM);
    const handle = handleAt(set.handles, env.toScreen, pointPx);
    if (handle) return startHandle(state, handle, subject, pointPx, downModel, env);
  }

  const hitKeys = env.hitTestAll(pointPx);
  const hits = stackRefs(env.plan, hitKeys);
  const keys = hits.map((ref) => ref.key);
  let target: SelectionRef | null = hits[0] ?? null;
  const { stack } = env;
  if (stack && distancePx(stack.pointPx, pointPx) <= 6 && stack.keys.length === keys.length) {
    // A press on the spot of the last stack click acts on the object that click chose.
    const current = hits.find((ref) => ref.key === stack.keys[stack.index]);
    if (current && isSelected(env.selection, current)) target = current;
  }

  if (target === null) {
    return step({
      gesture: { kind: 'marquee', downPx: pointPx, currentPx: pointPx, additive: sample.shift },
      vertex: null,
    });
  }
  const wasSelected = isSelected(env.selection, target);
  let selection = [...env.selection];
  const effects: Effect[] = [];
  if (!wasSelected) {
    selection = sample.shift ? [...env.selection, target] : [target];
    // Alt+click walks the stack from what is selected now, so it does not pick the top on press;
    // a drag started with Alt still moves the pressed object and picks it then.
    if (!sample.alt) effects.push(select(selection));
  }
  return step(
    {
      gesture: {
        kind: 'press',
        downPx: pointPx,
        downModel,
        target,
        hitKeys: keys,
        hits,
        shift: sample.shift,
        alt: sample.alt,
        wasSelected,
        selection,
        refused: false,
      },
      vertex: null,
    },
    effects,
  );
}

function startHandle(
  state: SelectState,
  handle: Handle,
  subject: { ref: SelectionRef & { entity: PlanEntity }; geometry: Geometry },
  downPx: Point,
  downModel: Point,
  env: ToolEnv,
): Step<SelectState> {
  const { ref } = subject;
  let start = subject.geometry;
  let active = handle;
  let inserted = false;
  if (handle.kind === 'midpoint' && handle.index !== undefined) {
    // The "+" handle puts a new vertex on the edge; from here on the new vertex is dragged.
    start = insertVertex(start, handle.index, handle.pointM);
    active = {
      id: `v${handle.index + 1}`,
      kind: 'vertex',
      pointM: handle.pointM,
      index: handle.index + 1,
    };
    inserted = true;
  }
  return step({
    gesture: {
      kind: 'handle',
      handle: active,
      subject: { entity: ref.entity, key: ref.key },
      start,
      targets: handle.kind === 'rotate' ? moveTargets(env.plan, [ref]) : [],
      downPx,
      downModel,
      draft: [{ entity: ref.entity, key: ref.key, geometry: start }],
      violation: null,
      dragged: false,
      inserted,
    },
    vertex: state.vertex,
  });
}

// ── pointer move ─────────────────────────────────────────────────────────────

export function selectMove(
  state: SelectState,
  sample: PointerSample,
  env: ToolEnv,
): Step<SelectState> {
  const { gesture } = state;
  const { pointPx } = sample;
  switch (gesture.kind) {
    case 'press':
      return pressMoved(state, gesture, sample, env);
    case 'move':
      return step({ ...state, gesture: movedTo(gesture, sample, env) });
    case 'marquee':
      return step({ ...state, gesture: { ...gesture, currentPx: pointPx } });
    case 'handle':
      return step({ ...state, gesture: handleMovedTo(gesture, sample, env) });
    default:
      return step(state);
  }
}

function pressMoved(
  state: SelectState,
  press: Extract<Gesture, { kind: 'press' }>,
  sample: PointerSample,
  env: ToolEnv,
): Step<SelectState> {
  if (distancePx(press.downPx, sample.pointPx) < dragThresholdPx(sample.pointerType))
    return step(state);
  // Plants and slot markers are selectable, not movable.
  const targets = moveTargets(env.plan, press.selection);
  if (targets.length === 0 || press.refused) return step(state);
  if (targets.some((entry) => entry.locked)) {
    // GP-UX-032: a locked object is hit but not moved; one locked child holds the whole group back.
    return step({ ...state, gesture: { ...press, refused: true } }, [
      { type: 'notice', code: 'object.locked' },
    ]);
  }
  const primary =
    targets.find(
      (entry) => entry.key === press.target.key && entry.entity === press.target.entity,
    ) ?? targets[0];
  const effects: Effect[] =
    press.alt && !press.wasSelected
      ? [select(press.selection), { type: 'stack', stack: null }]
      : [];
  const moving: Extract<Gesture, { kind: 'move' }> = {
    kind: 'move',
    downModel: press.downModel,
    targets,
    primary,
    delta: [0, 0],
    violation: null,
  };
  return step({ ...state, gesture: movedTo(moving, sample, env) }, effects);
}

function movedTo(
  move: Extract<Gesture, { kind: 'move' }>,
  sample: PointerSample,
  env: ToolEnv,
): Extract<Gesture, { kind: 'move' }> {
  const now = env.toModel(sample.pointPx);
  const raw: Point = [now[0] - move.downModel[0], now[1] - move.downModel[1]];
  const start = anchor(move.primary.geometry);
  const snapped = env.snapPoint([start[0] + raw[0], start[1] + raw[1]], sample.alt);
  const delta: Point = [snapped[0] - start[0], snapped[1] - start[1]];
  const draft = move.targets.map((entry) => ({
    entity: entry.entity,
    key: entry.key,
    geometry: translateGeometry(entry.geometry, delta),
  }));
  return { ...move, delta, violation: firstViolation(env.plan, draft) };
}

function handleMovedTo(
  handle: Extract<Gesture, { kind: 'handle' }>,
  sample: PointerSample,
  env: ToolEnv,
): Extract<Gesture, { kind: 'handle' }> {
  const dragged =
    handle.dragged ||
    distancePx(handle.downPx, sample.pointPx) >= dragThresholdPx(sample.pointerType);
  if (!dragged) return handle;
  const pointer = env.snapPoint(env.toModel(sample.pointPx), sample.alt);
  const { start } = handle;
  let draft: DraftChange[] = [{ ...handle.subject, geometry: start }];
  switch (handle.handle.kind) {
    case 'corner':
    case 'edge':
      if (start.kind === 'rect') {
        draft = [
          {
            ...handle.subject,
            geometry: resizeRect(start, handle.handle.id as RectHandleId, pointer, sample.shift),
          },
        ];
      }
      break;
    case 'radius':
      if (start.kind === 'circle') {
        draft = [
          { ...handle.subject, geometry: { ...start, radius_m: resizeCircle(start, pointer) } },
        ];
      }
      break;
    case 'vertex':
      draft = [
        { ...handle.subject, geometry: moveVertex(start, handle.handle.index ?? 0, pointer) },
      ];
      break;
    case 'rotate': {
      const pivot = geometryCenter(start);
      const rawPointer = env.toModel(sample.pointPx);
      const step = sample.alt ? null : env.angleStepDeg;
      const rotateDeg = rotationDelta(start, pivot, handle.downModel, rawPointer, step);
      draft = handle.targets.map((entry) => ({
        entity: entry.entity,
        key: entry.key,
        geometry: moveGeometry(entry.geometry, { translate: [0, 0], rotateDeg, pivot }),
      }));
      break;
    }
    default:
      break;
  }
  return { ...handle, dragged, draft, violation: firstViolation(env.plan, draft) };
}

// ── pointer up ───────────────────────────────────────────────────────────────

const HANDLE_LABEL: Record<Handle['kind'], ActionLabel> = {
  corner: 'resize',
  edge: 'resize',
  radius: 'resize',
  rotate: 'rotate',
  vertex: 'editPoint',
  midpoint: 'editPoint',
};

export function selectUp(
  state: SelectState,
  sample: PointerSample,
  env: ToolEnv,
): Step<SelectState> {
  const { gesture } = state;
  const idle: SelectState = { ...state, gesture: { kind: 'idle' } };
  switch (gesture.kind) {
    case 'press':
      return clicked(idle, gesture, sample, env);
    case 'move': {
      if (Math.hypot(gesture.delta[0], gesture.delta[1]) < MIN_MOVE_M) return step(idle);
      if (gesture.violation) return step(idle, [{ type: 'notice', code: gesture.violation }]);
      const draft = gesture.targets.map((entry) => ({
        entity: entry.entity,
        key: entry.key,
        geometry: translateGeometry(entry.geometry, gesture.delta),
      }));
      return step(idle, [{ type: 'commit', ops: operationsOf(draft), label: 'move' }]);
    }
    case 'marquee': {
      if (distancePx(gesture.downPx, gesture.currentPx) < dragThresholdPx(sample.pointerType)) {
        // A click on empty ground: nothing is picked, so nothing stays selected (Shift keeps it).
        return step(
          { ...idle, vertex: null },
          gesture.additive ? [] : [select([]), { type: 'stack', stack: null }],
        );
      }
      const a = env.toModel(gesture.downPx);
      const b = env.toModel(gesture.currentPx);
      const picked = marqueeSelection(
        env.plan,
        [Math.min(a[0], b[0]), Math.min(a[1], b[1]), Math.max(a[0], b[0]), Math.max(a[1], b[1])],
        env.selection,
        gesture.additive,
      );
      return step({ ...idle, vertex: null }, [select(picked), { type: 'stack', stack: null }]);
    }
    case 'handle':
      return handleReleased(idle, gesture);
    default:
      return step(idle);
  }
}

function clicked(
  idle: SelectState,
  press: Extract<Gesture, { kind: 'press' }>,
  sample: PointerSample,
  env: ToolEnv,
): Step<SelectState> {
  if (distancePx(press.downPx, sample.pointPx) >= dragThresholdPx(sample.pointerType))
    return step(idle);
  if (press.shift && !press.alt) {
    // Shift+click toggles; a press that already added the object leaves it in.
    return step(idle, press.wasSelected ? [select(toggleRef(env.selection, press.target))] : []);
  }
  const selected = env.selection.length === 1 ? env.selection[0] : null;
  const index = nextStackIndex(
    env.stack,
    press.hits.map((ref) => ref.key),
    press.downPx as [number, number],
    press.alt,
    selected && press.hits.some((ref) => sameRef(ref, selected)) ? selected.key : null,
  );
  const chosen = press.hits[index] ?? press.target;
  const stack =
    press.hits.length > 1
      ? { keys: press.hits.map((ref) => ref.key), index, pointPx: press.downPx as [number, number] }
      : null;
  return step(idle, [select([chosen]), { type: 'stack', stack }]);
}

function handleReleased(
  idle: SelectState,
  handle: Extract<Gesture, { kind: 'handle' }>,
): Step<SelectState> {
  const { subject } = handle;
  if (!handle.dragged && !handle.inserted) {
    // A click on a polygon point picks it; on any other handle it does nothing.
    const picked =
      handle.handle.kind === 'vertex' && handle.handle.index !== undefined
        ? { key: subject.key, index: handle.handle.index }
        : idle.vertex;
    return step({ ...idle, vertex: picked });
  }
  if (handle.violation) {
    return step({ ...idle, vertex: idle.vertex }, [{ type: 'notice', code: handle.violation }]);
  }
  const vertex =
    handle.handle.kind === 'vertex' && handle.handle.index !== undefined
      ? { key: subject.key, index: handle.handle.index }
      : null;
  return step({ ...idle, vertex }, [
    { type: 'commit', ops: operationsOf(handle.draft), label: HANDLE_LABEL[handle.handle.kind] },
  ]);
}

// ── cancel, keys, overlay ────────────────────────────────────────────────────

/** Escape: drop the gesture in progress; nothing was committed, so nothing is undone. */
export function selectCancel(state: SelectState): SelectState {
  return { ...state, gesture: { kind: 'idle' } };
}

export function isGestureActive(state: SelectState): boolean {
  return state.gesture.kind !== 'idle';
}

export function clearVertex(state: SelectState): SelectState {
  return state.vertex === null ? state : { ...state, vertex: null };
}

/** What the overlay draws for the gesture: ghost outlines of the moved/resized shapes and the marquee. */
export function selectOverlay(state: SelectState): Overlay {
  const { gesture } = state;
  if (gesture.kind === 'marquee') {
    const [x0, y0] = gesture.downPx;
    const [x1, y1] = gesture.currentPx;
    if (distancePx(gesture.downPx, gesture.currentPx) < 3) return EMPTY_OVERLAY;
    return {
      shapes: [],
      marquee: {
        x: Math.min(x0, x1),
        y: Math.min(y0, y1),
        width: Math.abs(x1 - x0),
        height: Math.abs(y1 - y0),
      },
    };
  }
  return { marquee: null, ...ghostShapes(gesture) };
}

function ghostShapes(gesture: Gesture): Pick<Overlay, 'shapes'> {
  if (gesture.kind === 'move') {
    return {
      shapes: gesture.targets.map((entry) => ({
        key: `${entry.entity}:${entry.key}`,
        shape: toShape(translateGeometry(entry.geometry, gesture.delta)),
        invalid: gesture.violation !== null,
      })),
    };
  }
  if (gesture.kind === 'handle' && gesture.dragged) {
    return {
      shapes: gesture.draft.map((entry) => ({
        key: `${entry.entity}:${entry.key}`,
        shape: toShape(entry.geometry),
        invalid: gesture.violation !== null,
      })),
    };
  }
  return { shapes: [] };
}

/** The move preview offset for the renderer (`setDragOffset`): the primary object, in pixels. */
export function dragPreview(
  state: SelectState,
  pxPerM: number,
): { key: string; dxPx: number; dyPx: number } | null {
  const { gesture } = state;
  if (gesture.kind !== 'move') return null;
  return {
    key: gesture.primary.key,
    dxPx: gesture.delta[0] * pxPerM,
    dyPx: -gesture.delta[1] * pxPerM,
  };
}
