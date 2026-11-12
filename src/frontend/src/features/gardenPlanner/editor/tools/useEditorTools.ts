/**
 * Wires the tool state machines to the canvas (REQ-053 WP 2.4): turns pointer and key events into
 * machine events, carries out their effects (select, commit, pan, notice) through callbacks, and
 * exposes what the overlay draws. The editor reaches the renderer only through the `PlanRenderer`
 * interface (GP-NFR-009): hit tests, coordinate conversion and the drag preview.
 *
 * One pointer drives a gesture at a time (a second finger is ignored here; pinch is WP 2.5/2.6).
 * Mouse, pen and touch are the same events (Pointer Events).
 *
 * A press pans instead of using the tool (GP-FR-010) when it is the middle button, or the primary button of a mouse or
 * pen while Space is held on the canvas. Both are a temporary override: the tool in the store never changes.
 */
import {
  useCallback,
  useEffect,
  useMemo,
  useState,
  useRef,
  type KeyboardEvent as ReactKeyboardEvent,
  type PointerEvent as ReactPointerEvent,
} from 'react';
import { isPanModifierTarget } from '../keyTargets';
import { roundLength } from '../../model/geometry';
import type { PlanModel } from '../../model/planModel';
import type { GardenObjectType, PlanOperation, Point } from '../../model/types';
import type { PlanRenderer, Viewport } from '../../renderer';
import type { PlanTool, SelectionRef, SelectionStack } from '../../state/gardenPlanSlice';
import {
  drawDown,
  drawFinish,
  drawMove,
  drawOverlay,
  drawUndoPoint,
  drawUp,
  INITIAL_DRAW_STATE,
  pointCount,
  type DrawOptions,
  type DrawShape,
  type DrawState,
} from './drawMachine';
import {
  boundaryCancel,
  boundaryDown,
  boundaryGestureActive,
  boundaryHandles,
  boundaryMove,
  boundaryOverlay,
  boundaryUp,
  INITIAL_BOUNDARY_STATE,
  setBoundaryOp,
  type BoundaryState,
} from './boundaryMachine';
import { BOUNDARY_KEY } from '../../renderer/planIndex';
import { insertVertex, removeVertex } from './geometryEdit';
import { computeHandles, type HandleSet } from './handles';
import { isPlanEntity } from './hierarchy';
import {
  anchorSnapMove,
  EMPTY_OVERLAY,
  type ActionLabel,
  type Effect,
  type Overlay,
  type PointerSample,
  type ToolEnv,
} from './machineTypes';
import { INITIAL_PAN_STATE, panDown, panMove, panUp, type PanState } from './panMachine';
import {
  clearVertex,
  dragPreview,
  INITIAL_SELECT_STATE,
  isGestureActive,
  moveSnapMark,
  selectCancel,
  selectDown,
  selectMove,
  selectOverlay,
  selectUp,
  type SelectState,
  type VertexSelection,
} from './selectMachine';
import { selectAll } from './selection';
import type { SnapMark } from './snap';
import { boundaryViolation, firstViolation } from './validation';

export interface EditorToolsOptions {
  tool: PlanTool;
  drawShape: DrawShape;
  angleStepDeg: number;
  plan: PlanModel;
  viewport: Viewport;
  renderer: PlanRenderer;
  selection: SelectionRef[];
  stack: SelectionStack | null;
  newBedName: (n: number) => string;
  onSelect: (selection: SelectionRef[]) => void;
  onStack: (stack: SelectionStack | null) => void;
  onCommit: (ops: PlanOperation[], label: ActionLabel) => void;
  onPan: (dxPx: number, dyPx: number) => void;
  onTool: (tool: PlanTool) => void;
  /** A refusal to tell the user about, or `null` to clear the last one. */
  onNotice: (code: string | null) => void;
  /** Delete was asked for (key or button): the editor shows the confirmation. */
  onRequestDelete: () => void;
  /** Grid and snap hook (WP 2.5); defaults to rounding to the storage precision. */
  snapPoint?: ToolEnv['snapPoint'];
  /** Snap of a moved object by all its corners (GP-FR-154); defaults to the anchor through `snapPoint`. */
  snapMove?: ToolEnv['snapMove'];
  /** Every click adds to the selection, like Shift (the touch "multi-select" toggle, GP-UX-037). */
  additive?: boolean;
  /** The type choice for the next drawn bed / garden object (WP 2.6). */
  bedTypeKey?: string;
  objectType?: GardenObjectType;
}

/**
 * The select state of a move gesture between React commits (GP-NFR-011, GP-NFR-033): a pointer move that only shifts
 * the moved selection is published here instead of re-rendering the editor. `get()` is `null` while no move is in
 * flight past its first frame; then the committed `overlay` / `moveSnap` are current.
 */
export interface LiveMoveStore {
  subscribe: (listener: () => void) => () => void;
  get: () => SelectState | null;
}

function createLiveMoveStore(): LiveMoveStore & { set: (state: SelectState | null) => void } {
  let value: SelectState | null = null;
  const listeners = new Set<() => void>();
  return {
    subscribe: (listener) => {
      listeners.add(listener);
      return () => listeners.delete(listener);
    },
    get: () => value,
    set: (next) => {
      if (next === value) return;
      value = next;
      for (const listener of listeners) listener();
    },
  };
}

/**
 * A step that only moves the selection: same tool, pointer, machines and vertex, a press or a move before and a move
 * after. Nothing the editor renders besides the ghost, the size labels, the move's snap marker and the (then hidden)
 * handles depends on it - all of them are drawn by the live layer.
 */
function isMoveOnly(committed: Machines, next: Machines): boolean {
  return (
    committed.forTool === next.forTool &&
    committed.active === 'select' &&
    next.active === 'select' &&
    committed.pointerId === next.pointerId &&
    committed.draw === next.draw &&
    committed.pan === next.pan &&
    committed.boundary === next.boundary &&
    committed.select.vertex === next.select.vertex &&
    // The press that turns into a move is live too: the editor renders at the press and at the release only.
    (committed.select.gesture.kind === 'move' || committed.select.gesture.kind === 'press') &&
    next.select.gesture.kind === 'move'
  );
}

export interface EditorTools {
  /** The live state of a move gesture (see {@link LiveMoveStore}); the ghost layer subscribes to it. */
  liveMove: LiveMoveStore;
  /** A pointer holds a gesture right now (press, move, draw, pan): the view must not move under it. */
  isPointerDown: () => boolean;
  /**
   * Space is held on the canvas (GP-FR-010): a primary-button press of a mouse or pen pans, whatever the tool. The
   * canvas shows the grab cursor meanwhile.
   */
  panModifier: boolean;
  containerProps: {
    onPointerDown: (event: ReactPointerEvent<HTMLElement>) => void;
    onPointerMove: (event: ReactPointerEvent<HTMLElement>) => void;
    onPointerUp: (event: ReactPointerEvent<HTMLElement>) => void;
    onPointerCancel: (event: ReactPointerEvent<HTMLElement>) => void;
    onKeyDown: (event: ReactKeyboardEvent<HTMLElement>) => void;
  };
  overlay: Overlay;
  /** The handles of the selected object; `null` when nothing editable is selected. */
  handles: HandleSet | null;
  vertex: VertexSelection | null;
  /** Points placed so far by a polygon/polyline being drawn. */
  draftPoints: number;
  /**
   * A handle of the selected object is being dragged past the threshold: the dragged point is the pointer's
   * snapped point, so the pointer's snap marker is right (GP-FR-154). A press, a marquee or a move is not.
   */
  handleDragging: boolean;
  /** A move of the selection is under way: its snap marker is `moveSnap`, not the pointer's. */
  moving: boolean;
  /** Where the snapped source of the moved object lands (GP-FR-154); `null` without a snap. */
  moveSnap: SnapMark | null;
  cancel: () => void;
  finishDraw: () => void;
  /** Touch: set a polygon/line point or a rectangle/circle corner at a canvas pixel. */
  placePointAt: (pointPx: Point) => void;
  /** Touch: take the last drawn point back. */
  undoPoint: () => void;
  deleteVertex: () => void;
  insertVertexAfter: () => void;
}

const defaultSnap: ToolEnv['snapPoint'] = ([x, y]) => [roundLength(x), roundLength(y)];

type ToolKind = 'select' | 'draw' | 'pan' | 'boundary';

/** The boundary mode draws while the plan has no boundary and edits it once there is one (#2890). */
function toolKind(tool: PlanTool, plan: PlanModel): ToolKind {
  if (tool === 'pan') return 'pan';
  if (tool === 'bed' || tool === 'garden_object') return 'draw';
  if (tool === 'boundary') return plan.settings?.boundary ? 'boundary' : 'draw';
  return 'select';
}

function drawTargetOf(tool: PlanTool): DrawOptions['target'] {
  if (tool === 'garden_object') return 'garden_object';
  return tool === 'boundary' ? 'boundary' : 'bed';
}

/** Where the canvas content starts in client pixels (inside its border). */
function canvasOrigin(element: HTMLElement): Point {
  const box = element.getBoundingClientRect();
  return [box.left + element.clientLeft, box.top + element.clientTop];
}

/**
 * The canvas origin a gesture works with: read at the press and then re-read only when something scrolls. A layout
 * shift while the pointer is down (a notice or a sheet that opens on the selection) is not followed on its own - the
 * gesture must not jump by it - but a scroll is: the pointer then really points at another part of the plan.
 *
 * At a scroll the canvas's position on screen is measured, not the scroll offsets summed: what counts is where the
 * canvas is, and a scroll offset can change while the canvas stays put - scroll anchoring that answers a layout shift
 * above the canvas, or a canvas inside a sticky or fixed box while the page scrolls under it. The canvas is measured
 * once per scroll event, never per pointer move, so a move forces no layout (GP-NFR-033).
 */
class PressOrigin {
  point: Point;
  private readonly element: HTMLElement;

  constructor(element: HTMLElement) {
    this.element = element;
    this.point = canvasOrigin(element);
  }

  readonly onScroll = (): void => {
    this.point = canvasOrigin(this.element);
  };
}

/** The pointer in canvas pixels, from the gesture's origin when one is under way (see {@link PressOrigin}). */
function sampleOf(event: ReactPointerEvent<HTMLElement>, additive = false, origin?: Point): PointerSample {
  const [left, top] = origin ?? canvasOrigin(event.currentTarget);
  return {
    pointPx: [event.clientX - left, event.clientY - top],
    pointerType:
      event.pointerType === 'touch' || event.pointerType === 'pen' ? event.pointerType : 'mouse',
    shift: event.shiftKey || additive,
    alt: event.altKey,
  };
}

type EnvSource = Pick<
  EditorToolsOptions,
  'plan' | 'viewport' | 'selection' | 'stack' | 'renderer' | 'angleStepDeg' | 'snapPoint'
> &
  Partial<Pick<EditorToolsOptions, 'snapMove'>>;

function envOf(o: EnvSource): ToolEnv {
  const snapPoint = o.snapPoint ?? defaultSnap;
  return {
    plan: o.plan,
    selection: o.selection,
    stack: o.stack,
    pxPerM: o.viewport.pxPerM,
    hitTestAll: (pointPx: Point) => o.renderer.hitTestAll(pointPx),
    toModel: (pointPx: Point) => o.renderer.toModel(pointPx),
    toScreen: (pointM: Point) => o.renderer.toScreen(pointM),
    snapPoint,
    snapMove: o.snapMove ?? anchorSnapMove(snapPoint),
    angleStepDeg: o.angleStepDeg,
  };
}

function drawOptionsOf(o: EditorToolsOptions): DrawOptions {
  return {
    target: drawTargetOf(o.tool),
    shape: o.drawShape,
    newBedName: o.newBedName,
    bedTypeKey: o.bedTypeKey,
    objectType: o.objectType,
  };
}

interface Machines {
  select: SelectState;
  draw: DrawState;
  pan: PanState;
  boundary: BoundaryState;
  /** Which machine owns the gesture in progress. */
  active: 'select' | 'draw' | 'pan' | 'boundary' | null;
  pointerId: number | null;
  /** The tool and shape these states belong to: a switch discards them (see `useEditorTools`). */
  forTool: string;
}

const INITIAL_MACHINES: Omit<Machines, 'forTool'> = {
  select: INITIAL_SELECT_STATE,
  draw: INITIAL_DRAW_STATE,
  pan: INITIAL_PAN_STATE,
  boundary: INITIAL_BOUNDARY_STATE,
  active: null,
  pointerId: null,
};

/** The boundary mode switching from drawing to editing (or back, by an undo) is a switch too. */
const toolId = (o: Pick<EditorToolsOptions, 'tool' | 'drawShape' | 'plan'>) =>
  `${o.tool}:${o.drawShape}:${toolKind(o.tool, o.plan)}`;

export function useEditorTools(options: EditorToolsOptions): EditorTools {
  // Handlers read the newest options and machine states from refs; the same states are mirrored
  // into React state so the overlay renders from them.
  const latest = useRef(options);
  useEffect(() => {
    latest.current = options;
  });
  const [stored, setMachines] = useState<Machines>({
    ...INITIAL_MACHINES,
    forTool: toolId(options),
  });
  const live = useRef<Machines>(stored);
  // The canvas origin at the press of the gesture in progress (see `sampleOf`).
  const pressOrigin = useRef<PressOrigin | null>(null);
  const endPress = useCallback(() => {
    const origin = pressOrigin.current;
    if (origin) window.removeEventListener('scroll', origin.onScroll, { capture: true });
    pressOrigin.current = null;
  }, []);
  useEffect(() => endPress, [endPress]);
  // Space as the pan modifier (GP-FR-010): held from its keydown on the canvas until its keyup anywhere or until the
  // window loses the focus (the keyup then never arrives). `spaceUsed`: a press panned while it was held.
  const [panModifier, setPanModifier] = useState(false);
  const spaceHeld = useRef(false);
  const spaceUsed = useRef(false);
  const spaceListeners = useRef<(() => void) | null>(null);
  const releaseSpace = useCallback(() => {
    spaceListeners.current?.();
    spaceListeners.current = null;
    spaceHeld.current = false;
    setPanModifier(false);
  }, []);
  const holdSpace = useCallback(() => {
    spaceHeld.current = true;
    spaceUsed.current = false;
    setPanModifier(true);
    const onKeyUp = (event: KeyboardEvent) => {
      if (event.key !== ' ') return;
      // A Space that panned is no activation: a focused plan object leaves a handled release alone.
      if (spaceUsed.current) event.preventDefault();
      releaseSpace();
    };
    // Capture: the release is seen before the element it happens on, and also where the canvas has no focus anymore.
    window.addEventListener('keyup', onKeyUp, { capture: true });
    window.addEventListener('blur', releaseSpace);
    spaceListeners.current = () => {
      window.removeEventListener('keyup', onKeyUp, { capture: true });
      window.removeEventListener('blur', releaseSpace);
    };
  }, [releaseSpace]);
  useEffect(() => () => spaceListeners.current?.(), []);
  // What was last handed to React: a move-only step is compared against it, not against the live state.
  const committed = useRef<Machines>(stored);
  const liveMove = useMemo(() => createLiveMoveStore(), []);
  /**
   * The machine states for the tool that is active now. A tool or shape switch ends whatever was
   * under way (a half-drawn polygon, a drag): states recorded for another tool count as initial.
   */
  const current = useCallback((): Machines => {
    const id = toolId(latest.current);
    return live.current.forTool === id ? live.current : { ...INITIAL_MACHINES, forTool: id };
  }, []);
  const update = useCallback(
    (patch: Partial<Machines>) => {
      const next = { ...current(), ...patch };
      live.current = next;
      if (isMoveOnly(committed.current, next)) {
        liveMove.set(next.select);
        return;
      }
      committed.current = next;
      liveMove.set(null);
      setMachines(next);
    },
    [current, liveMove],
  );
  const machines =
    stored.forTool === toolId(options) ? stored : { ...INITIAL_MACHINES, forTool: toolId(options) };

  const apply = useCallback((effects: Effect[]) => {
    const o = latest.current;
    for (const effect of effects) {
      switch (effect.type) {
        case 'select':
          o.onSelect(effect.selection);
          break;
        case 'stack':
          o.onStack(effect.stack);
          break;
        case 'commit':
          o.onCommit(effect.ops, effect.label);
          break;
        case 'pan':
          o.onPan(effect.dxPx, effect.dyPx);
          break;
        case 'notice':
          o.onNotice(effect.code);
          break;
        case 'tool':
          o.onTool(effect.tool);
          break;
      }
    }
  }, []);

  /** The renderer's drag preview follows the move gesture (GP-NFR-011), nothing else. */
  const syncPreview = useCallback(() => {
    const o = latest.current;
    const preview = dragPreview(current().select, o.viewport.pxPerM);
    if (preview) o.renderer.setDragOffset(preview.key, preview.dxPx, preview.dyPx);
    else o.renderer.setDragOffset(null);
  }, [current]);

  // A tool switch also ends the renderer's drag preview.
  const { tool, drawShape } = options;
  useEffect(() => {
    latest.current.renderer.setDragOffset(null);
    // A move cut off by the switch leaves no ghost behind in the live layer.
    liveMove.set(null);
  }, [tool, drawShape, liveMove]);

  const onPointerDown = useCallback(
    (event: ReactPointerEvent<HTMLElement>) => {
      if (event.button !== 0 && event.button !== 1) return;
      const m = current();
      if (m.pointerId !== null) return; // one pointer at a time
      const o = latest.current;
      o.onNotice(null);
      endPress();
      const origin = new PressOrigin(event.currentTarget);
      pressOrigin.current = origin;
      window.addEventListener('scroll', origin.onScroll, { capture: true, passive: true });
      const sample = sampleOf(event, o.additive, origin.point);
      const env = envOf(o);
      // The middle button and Space + primary button pan in every tool; a finger keeps its own gestures.
      const spacePan = spaceHeld.current && event.button === 0 && event.pointerType !== 'touch';
      if (spacePan) spaceUsed.current = true;
      let kind: ToolKind = event.button === 1 || spacePan ? 'pan' : toolKind(o.tool, o.plan);
      // In the boundary mode a press on a boundary handle reshapes it; any other press pans the view (#2890).
      const boundaryStep = kind === 'boundary' ? boundaryDown(m.boundary, sample, env) : null;
      if (kind === 'boundary' && boundaryStep === null) kind = 'pan';
      try {
        event.currentTarget.setPointerCapture?.(event.pointerId);
      } catch {
        // a synthetic or already released pointer: the gesture still works inside the canvas
      }
      if (kind === 'pan') {
        update({ active: kind, pointerId: event.pointerId, pan: panDown(m.pan, sample).state });
      } else if (kind === 'boundary' && boundaryStep) {
        update({ active: kind, pointerId: event.pointerId, boundary: boundaryStep.state });
        apply(boundaryStep.effects);
      } else if (kind === 'draw') {
        const step = drawDown(m.draw, sample, env, drawOptionsOf(o));
        update({ active: kind, pointerId: event.pointerId, draw: step.state });
        apply(step.effects);
      } else {
        const step = selectDown(m.select, sample, env);
        update({ active: kind, pointerId: event.pointerId, select: step.state });
        apply(step.effects);
      }
      syncPreview();
    },
    [apply, current, endPress, syncPreview, update],
  );

  const onPointerMove = useCallback(
    (event: ReactPointerEvent<HTMLElement>) => {
      const m = current();
      const o = latest.current;
      if (m.pointerId !== null && event.pointerId !== m.pointerId) return;
      const sample = sampleOf(event, o.additive, m.pointerId !== null ? pressOrigin.current?.point : undefined);
      const env = envOf(o);
      if (m.active === 'pan') {
        const step = panMove(m.pan, sample);
        update({ pan: step.state });
        apply(step.effects);
      } else if (m.active === 'draw') {
        update({ draw: drawMove(m.draw, sample, env, true).state });
      } else if (m.active === 'boundary') {
        update({ boundary: boundaryMove(m.boundary, sample, env) });
      } else if (m.active === 'select') {
        const step = selectMove(m.select, sample, env);
        update({ select: step.state });
        apply(step.effects);
        syncPreview();
      } else if (toolKind(o.tool, o.plan) === 'draw' && m.draw.kind === 'points') {
        update({ draw: drawMove(m.draw, sample, env, false).state }); // the rubber band follows the hover
      }
    },
    [apply, current, syncPreview, update],
  );

  const onPointerUp = useCallback(
    (event: ReactPointerEvent<HTMLElement>) => {
      const m = current();
      const o = latest.current;
      if (m.pointerId === null || event.pointerId !== m.pointerId) return;
      const sample = sampleOf(event, o.additive, pressOrigin.current?.point);
      endPress();
      const env = envOf(o);
      try {
        event.currentTarget.releasePointerCapture?.(event.pointerId);
      } catch {
        // see onPointerDown
      }
      // The preview ends before the model changes, so the node never jumps twice.
      o.renderer.setDragOffset(null);
      if (m.active === 'pan') {
        update({ active: null, pointerId: null, pan: panUp().state });
      } else if (m.active === 'draw') {
        const step = drawUp(m.draw, sample, env, drawOptionsOf(o));
        update({ active: null, pointerId: null, draw: step.state });
        apply(step.effects);
      } else if (m.active === 'boundary') {
        const step = boundaryUp(boundaryMove(m.boundary, sample, env), env);
        update({ active: null, pointerId: null, boundary: step.state });
        apply(step.effects);
      } else if (m.active === 'select') {
        const step = selectUp(m.select, sample, env);
        update({ active: null, pointerId: null, select: step.state });
        apply(step.effects);
      }
    },
    [apply, current, endPress, update],
  );

  const onPointerCancel = useCallback(() => {
    const m = current();
    update({
      select: selectCancel(m.select),
      draw: m.draw.kind === 'drag' ? INITIAL_DRAW_STATE : m.draw,
      boundary: boundaryCancel(m.boundary),
      pan: INITIAL_PAN_STATE,
      active: null,
      pointerId: null,
    });
    endPress();
    latest.current.renderer.setDragOffset(null);
  }, [current, endPress, update]);

  /** Escape: the innermost thing under way ends first - a draft, a gesture, a picked point, the selection, the tool. */
  const cancel = useCallback(() => {
    const m = current();
    const o = latest.current;
    if (m.draw.kind !== 'idle') {
      update({ draw: INITIAL_DRAW_STATE, active: null, pointerId: null });
      endPress(); // the release no longer reaches the gesture: its press origin and scroll listener end here
    } else if (boundaryGestureActive(m.boundary)) {
      update({ boundary: boundaryCancel(m.boundary), active: null, pointerId: null });
      endPress();
    } else if (m.boundary.vertex !== null) {
      update({ boundary: { kind: 'idle', vertex: null } });
    } else if (isGestureActive(m.select)) {
      update({ select: selectCancel(m.select), active: null, pointerId: null });
      endPress();
    } else if (m.select.vertex !== null) update({ select: clearVertex(m.select) });
    else if (o.selection.length > 0) {
      o.onSelect([]);
      o.onStack(null);
    } else if (o.tool !== 'select') o.onTool('select');
    o.renderer.setDragOffset(null);
  }, [current, endPress, update]);

  const finishDraw = useCallback(() => {
    const o = latest.current;
    const step = drawFinish(current().draw, envOf(o), drawOptionsOf(o));
    update({ draw: step.state });
    apply(step.effects);
  }, [apply, current, update]);

  const placePointAt = useCallback(
    (pointPx: Point) => {
      const o = latest.current;
      if (toolKind(o.tool, o.plan) !== 'draw') return;
      const sample: PointerSample = { pointPx, pointerType: 'touch', shift: false, alt: false };
      const env = envOf(o);
      const drawOptions = drawOptionsOf(o);
      const down = drawDown(current().draw, sample, env, drawOptions);
      const up = drawUp(down.state, sample, env, drawOptions);
      update({ draw: up.state });
      apply(up.effects);
    },
    [apply, current, update],
  );

  const undoPoint = useCallback(() => {
    update({ draw: drawUndoPoint(current().draw) });
  }, [current, update]);

  /** The geometry and index of the picked polygon point, if it is still there. */
  const pickedVertex = useCallback(() => {
    const o = latest.current;
    const picked = current().select.vertex;
    if (picked === null || o.selection.length !== 1 || o.selection[0].key !== picked.key)
      return null;
    const ref = o.selection[0];
    if (!isPlanEntity(ref)) return null;
    const geometry = (
      ref.entity === 'location' ? o.plan.locations[ref.key] : o.plan.gardenObjects[ref.key]
    )?.geometry;
    return geometry ? { ref, geometry, index: picked.index } : null;
  }, [current]);

  /** The picked point of the boundary in the boundary mode (#2890), if it is still there. */
  const pickedBoundaryVertex = useCallback(() => {
    const o = latest.current;
    const m = current();
    const boundary = o.plan.settings?.boundary ?? null;
    if (toolKind(o.tool, o.plan) !== 'boundary' || boundary === null || m.boundary.vertex === null) return null;
    return { geometry: boundary, index: m.boundary.vertex };
  }, [current]);

  /** "Punkt löschen" / "Punkt einfügen" on the boundary: one `set_boundary`, checked like a handle drag. */
  const editBoundaryVertex = useCallback(
    (mode: 'delete' | 'insert') => {
      const o = latest.current;
      const picked = pickedBoundaryVertex();
      if (picked === null) return;
      const next =
        mode === 'delete'
          ? removeVertex(picked.geometry, picked.index)
          : insertVertex(picked.geometry, picked.index);
      if (next === null) {
        o.onNotice('geometry.too_few_points');
        return;
      }
      if (next === picked.geometry) return;
      const violation = boundaryViolation(o.plan, next);
      if (violation) {
        o.onNotice(violation);
        return;
      }
      o.onCommit([setBoundaryOp(o, next)], 'editBoundary');
      update({ boundary: { kind: 'idle', vertex: mode === 'delete' ? null : picked.index + 1 } });
    },
    [pickedBoundaryVertex, update],
  );

  const deleteVertex = useCallback(() => {
    const o = latest.current;
    if (pickedBoundaryVertex() !== null) {
      editBoundaryVertex('delete');
      return;
    }
    const picked = pickedVertex();
    if (picked === null) return;
    const next = removeVertex(picked.geometry, picked.index);
    if (next === null) {
      o.onNotice('geometry.too_few_points');
      return;
    }
    const draft = { entity: picked.ref.entity, key: picked.ref.key, geometry: next };
    const violation = firstViolation(o.plan, [draft]);
    if (violation) {
      o.onNotice(violation);
      return;
    }
    o.onCommit([{ op: 'update_geometry', ...draft }], 'editPoint');
    update({ select: clearVertex(current().select) });
  }, [current, editBoundaryVertex, pickedBoundaryVertex, pickedVertex, update]);

  const insertVertexAfter = useCallback(() => {
    const o = latest.current;
    if (pickedBoundaryVertex() !== null) {
      editBoundaryVertex('insert');
      return;
    }
    const picked = pickedVertex();
    if (picked === null) return;
    const next = insertVertex(picked.geometry, picked.index);
    if (next === picked.geometry) return;
    o.onCommit(
      [{ op: 'update_geometry', entity: picked.ref.entity, key: picked.ref.key, geometry: next }],
      'editPoint',
    );
    update({
      select: { ...current().select, vertex: { key: picked.ref.key, index: picked.index + 1 } },
    });
  }, [current, editBoundaryVertex, pickedBoundaryVertex, pickedVertex, update]);

  const onKeyDown = useCallback(
    (event: ReactKeyboardEvent<HTMLElement>) => {
      const o = latest.current;
      const m = current();
      // Keys typed into a field inside the canvas region belong to the field.
      if (
        event.target instanceof HTMLElement &&
        /^(INPUT|TEXTAREA|SELECT)$/.test(event.target.tagName)
      )
        return;
      if (event.key === ' ' && !event.ctrlKey && !event.metaKey && !event.altKey) {
        // Space on a control (a zoom button, a menu item) or in a contenteditable stays theirs.
        if (!isPanModifierTarget(event.target, event.currentTarget)) return;
        event.preventDefault(); // the page must not scroll - on the key repeat neither
        if (!spaceHeld.current) holdSpace();
        return;
      }
      if (event.key === 'Escape') {
        cancel();
      } else if (event.key === 'Enter' && m.draw.kind === 'points') {
        event.preventDefault();
        finishDraw();
      } else if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'a') {
        event.preventDefault();
        o.onSelect(selectAll(o.plan));
        o.onStack(null);
      } else if (event.key === 'Backspace' && m.draw.kind === 'points') {
        event.preventDefault();
        update({ draw: drawUndoPoint(m.draw) });
      } else if (event.key === 'Delete' || event.key === 'Backspace') {
        if (pickedVertex() !== null || pickedBoundaryVertex() !== null) {
          event.preventDefault();
          deleteVertex();
        } else if (o.selection.some(isPlanEntity)) {
          event.preventDefault();
          o.onRequestDelete();
        }
      }
    },
    [cancel, current, deleteVertex, finishDraw, holdSpace, pickedBoundaryVertex, pickedVertex, update],
  );

  const isPointerDown = useCallback(() => current().pointerId !== null, [current]);

  const kind = toolKind(options.tool, options.plan);
  const {
    plan,
    viewport,
    selection,
    renderer,
    stack,
    angleStepDeg,
    snapPoint,
    newBedName,
    bedTypeKey,
    objectType,
  } = options;
  const { select: selectState, draw: drawState, boundary: boundaryState } = machines;

  const overlay = useMemo<Overlay>(() => {
    if (kind === 'select') return selectOverlay(selectState);
    if (kind === 'boundary') return boundaryOverlay(boundaryState);
    if (kind !== 'draw') return EMPTY_OVERLAY;
    return drawOverlay(
      drawState,
      envOf({ plan, viewport, selection, renderer, stack, angleStepDeg, snapPoint }),
      {
        target: drawTargetOf(tool),
        shape: drawShape,
        newBedName,
        bedTypeKey,
        objectType,
      },
    );
  }, [
    kind,
    selectState,
    drawState,
    boundaryState,
    plan,
    viewport,
    selection,
    renderer,
    stack,
    angleStepDeg,
    snapPoint,
    tool,
    drawShape,
    newBedName,
    bedTypeKey,
    objectType,
  ]);

  // Handles follow the live draft of a handle drag, and are hidden while a move or marquee runs.
  const handles = useMemo<HandleSet | null>(() => {
    // The unlocked boundary shows its own handles (#2890); nothing is selected meanwhile.
    if (kind === 'boundary') return boundaryHandles(boundaryState, { plan, pxPerM: viewport.pxPerM });
    if (kind !== 'select' || selection.length !== 1) return null;
    const ref = selection[0];
    const gesture = selectState.gesture;
    if (!isPlanEntity(ref) || gesture.kind === 'move' || gesture.kind === 'marquee') return null;
    const source =
      ref.entity === 'location' ? plan.locations[ref.key] : plan.gardenObjects[ref.key];
    if (!source || source.locked) return null;
    let geometry = source.geometry ?? null;
    if (gesture.kind === 'handle' && gesture.dragged) {
      geometry = gesture.draft.find((entry) => entry.key === ref.key)?.geometry ?? geometry;
    }
    return geometry ? computeHandles(geometry, viewport.pxPerM) : null;
  }, [kind, selection, selectState, boundaryState, plan, viewport.pxPerM]);

  const boundaryVertex = boundaryState.vertex;
  const vertex = useMemo<VertexSelection | null>(() => {
    if (kind === 'boundary') return boundaryVertex === null ? null : { key: BOUNDARY_KEY, index: boundaryVertex };
    return selection.length === 1 && selectState.vertex?.key === selection[0].key ? selectState.vertex : null;
  }, [kind, boundaryVertex, selection, selectState.vertex]);
  const draftPoints = pointCount(drawState);
  const handleDragging =
    (kind === 'select' && selectState.gesture.kind === 'handle' && selectState.gesture.dragged) ||
    (kind === 'boundary' && boundaryState.kind === 'handle' && boundaryState.dragged);
  const moving = kind === 'select' && selectState.gesture.kind === 'move';
  const moveSnap = useMemo(
    () => (kind === 'select' ? moveSnapMark(selectState) : null),
    [kind, selectState],
  );

  return useMemo(
    () => ({
      liveMove,
      isPointerDown,
      panModifier,
      containerProps: { onPointerDown, onPointerMove, onPointerUp, onPointerCancel, onKeyDown },
      overlay,
      handles,
      vertex,
      draftPoints,
      handleDragging,
      moving,
      moveSnap,
      cancel,
      finishDraw,
      placePointAt,
      undoPoint,
      deleteVertex,
      insertVertexAfter,
    }),
    [
      liveMove,
      isPointerDown,
      panModifier,
      onPointerDown,
      onPointerMove,
      onPointerUp,
      onPointerCancel,
      onKeyDown,
      overlay,
      handles,
      vertex,
      draftPoints,
      handleDragging,
      moving,
      moveSnap,
      cancel,
      finishDraw,
      placePointAt,
      undoPoint,
      deleteVertex,
      insertVertexAfter,
    ],
  );
}
