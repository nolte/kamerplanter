/**
 * Wires the tool state machines to the canvas (REQ-053 WP 2.4): turns pointer and key events into
 * machine events, carries out their effects (select, commit, pan, notice) through callbacks, and
 * exposes what the overlay draws. The editor reaches the renderer only through the `PlanRenderer`
 * interface (GP-NFR-009): hit tests, coordinate conversion and the drag preview.
 *
 * One pointer drives a gesture at a time (a second finger is ignored here; pinch is WP 2.5/2.6).
 * Mouse, pen and touch are the same events (Pointer Events).
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
import { roundLength } from '../../model/geometry';
import type { PlanModel } from '../../model/planModel';
import type { PlanOperation, Point } from '../../model/types';
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
import { insertVertex, removeVertex } from './geometryEdit';
import { computeHandles, type HandleSet } from './handles';
import { isPlanEntity } from './hierarchy';
import {
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
  selectCancel,
  selectDown,
  selectMove,
  selectOverlay,
  selectUp,
  type SelectState,
  type VertexSelection,
} from './selectMachine';
import { selectAll } from './selection';
import { firstViolation } from './validation';

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
}

export interface EditorTools {
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
  /** The select gesture or a draw is under way. */
  busy: boolean;
  cancel: () => void;
  finishDraw: () => void;
  deleteVertex: () => void;
  insertVertexAfter: () => void;
}

const defaultSnap: ToolEnv['snapPoint'] = ([x, y]) => [roundLength(x), roundLength(y)];

function toolKind(tool: PlanTool): 'select' | 'draw' | 'pan' {
  if (tool === 'pan') return 'pan';
  if (tool === 'bed' || tool === 'garden_object') return 'draw';
  return 'select';
}

function sampleOf(event: ReactPointerEvent<HTMLElement>): PointerSample {
  const element = event.currentTarget;
  const box = element.getBoundingClientRect();
  return {
    pointPx: [
      event.clientX - box.left - element.clientLeft,
      event.clientY - box.top - element.clientTop,
    ],
    pointerType:
      event.pointerType === 'touch' || event.pointerType === 'pen' ? event.pointerType : 'mouse',
    shift: event.shiftKey,
    alt: event.altKey,
  };
}

type EnvSource = Pick<
  EditorToolsOptions,
  'plan' | 'viewport' | 'selection' | 'stack' | 'renderer' | 'angleStepDeg' | 'snapPoint'
>;

function envOf(o: EnvSource): ToolEnv {
  return {
    plan: o.plan,
    selection: o.selection,
    stack: o.stack,
    pxPerM: o.viewport.pxPerM,
    hitTestAll: (pointPx: Point) => o.renderer.hitTestAll(pointPx),
    toModel: (pointPx: Point) => o.renderer.toModel(pointPx),
    toScreen: (pointM: Point) => o.renderer.toScreen(pointM),
    snapPoint: o.snapPoint ?? defaultSnap,
    angleStepDeg: o.angleStepDeg,
  };
}

function drawOptionsOf(o: EditorToolsOptions): DrawOptions {
  return {
    target: o.tool === 'garden_object' ? 'garden_object' : 'bed',
    shape: o.drawShape,
    newBedName: o.newBedName,
  };
}

interface Machines {
  select: SelectState;
  draw: DrawState;
  pan: PanState;
  /** Which machine owns the gesture in progress. */
  active: 'select' | 'draw' | 'pan' | null;
  pointerId: number | null;
  /** The tool and shape these states belong to: a switch discards them (see `useEditorTools`). */
  forTool: string;
}

const INITIAL_MACHINES: Omit<Machines, 'forTool'> = {
  select: INITIAL_SELECT_STATE,
  draw: INITIAL_DRAW_STATE,
  pan: INITIAL_PAN_STATE,
  active: null,
  pointerId: null,
};

const toolId = (o: Pick<EditorToolsOptions, 'tool' | 'drawShape'>) => `${o.tool}:${o.drawShape}`;

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
      live.current = { ...current(), ...patch };
      setMachines(live.current);
    },
    [current],
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
  }, [tool, drawShape]);

  const onPointerDown = useCallback(
    (event: ReactPointerEvent<HTMLElement>) => {
      if (event.button !== 0 && event.button !== 1) return;
      const m = current();
      if (m.pointerId !== null) return; // one pointer at a time
      const o = latest.current;
      o.onNotice(null);
      const sample = sampleOf(event);
      const env = envOf(o);
      const kind = event.button === 1 ? 'pan' : toolKind(o.tool);
      try {
        event.currentTarget.setPointerCapture?.(event.pointerId);
      } catch {
        // a synthetic or already released pointer: the gesture still works inside the canvas
      }
      if (kind === 'pan') {
        update({ active: kind, pointerId: event.pointerId, pan: panDown(m.pan, sample).state });
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
    [apply, current, syncPreview, update],
  );

  const onPointerMove = useCallback(
    (event: ReactPointerEvent<HTMLElement>) => {
      const m = current();
      const o = latest.current;
      if (m.pointerId !== null && event.pointerId !== m.pointerId) return;
      const sample = sampleOf(event);
      const env = envOf(o);
      if (m.active === 'pan') {
        const step = panMove(m.pan, sample);
        update({ pan: step.state });
        apply(step.effects);
      } else if (m.active === 'draw') {
        update({ draw: drawMove(m.draw, sample, env, true).state });
      } else if (m.active === 'select') {
        const step = selectMove(m.select, sample, env);
        update({ select: step.state });
        apply(step.effects);
        syncPreview();
      } else if (toolKind(o.tool) === 'draw' && m.draw.kind === 'points') {
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
      const sample = sampleOf(event);
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
      } else if (m.active === 'select') {
        const step = selectUp(m.select, sample, env);
        update({ active: null, pointerId: null, select: step.state });
        apply(step.effects);
      }
    },
    [apply, current, update],
  );

  const onPointerCancel = useCallback(() => {
    const m = current();
    update({
      select: selectCancel(m.select),
      draw: m.draw.kind === 'drag' ? INITIAL_DRAW_STATE : m.draw,
      pan: INITIAL_PAN_STATE,
      active: null,
      pointerId: null,
    });
    latest.current.renderer.setDragOffset(null);
  }, [current, update]);

  /** Escape: the innermost thing under way ends first - a draft, a gesture, a picked point, the selection, the tool. */
  const cancel = useCallback(() => {
    const m = current();
    const o = latest.current;
    if (m.draw.kind !== 'idle') update({ draw: INITIAL_DRAW_STATE, active: null, pointerId: null });
    else if (isGestureActive(m.select))
      update({ select: selectCancel(m.select), active: null, pointerId: null });
    else if (m.select.vertex !== null) update({ select: clearVertex(m.select) });
    else if (o.selection.length > 0) {
      o.onSelect([]);
      o.onStack(null);
    } else if (o.tool !== 'select') o.onTool('select');
    o.renderer.setDragOffset(null);
  }, [current, update]);

  const finishDraw = useCallback(() => {
    const o = latest.current;
    const step = drawFinish(current().draw, envOf(o), drawOptionsOf(o));
    update({ draw: step.state });
    apply(step.effects);
  }, [apply, current, update]);

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

  const deleteVertex = useCallback(() => {
    const o = latest.current;
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
  }, [current, pickedVertex, update]);

  const insertVertexAfter = useCallback(() => {
    const o = latest.current;
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
  }, [current, pickedVertex, update]);

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
        if (pickedVertex() !== null) {
          event.preventDefault();
          deleteVertex();
        } else if (o.selection.some(isPlanEntity)) {
          event.preventDefault();
          o.onRequestDelete();
        }
      }
    },
    [cancel, current, deleteVertex, finishDraw, pickedVertex, update],
  );

  const kind = toolKind(options.tool);
  const { plan, viewport, selection, renderer, stack, angleStepDeg, snapPoint, newBedName } =
    options;
  const { select: selectState, draw: drawState } = machines;

  const overlay = useMemo<Overlay>(() => {
    if (kind === 'select') return selectOverlay(selectState);
    if (kind !== 'draw') return EMPTY_OVERLAY;
    return drawOverlay(
      drawState,
      envOf({ plan, viewport, selection, renderer, stack, angleStepDeg, snapPoint }),
      { target: tool === 'garden_object' ? 'garden_object' : 'bed', shape: drawShape, newBedName },
    );
  }, [
    kind,
    selectState,
    drawState,
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
  ]);

  // Handles follow the live draft of a handle drag, and are hidden while a move or marquee runs.
  const handles = useMemo<HandleSet | null>(() => {
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
  }, [kind, selection, selectState, plan, viewport.pxPerM]);

  const vertex =
    selection.length === 1 && selectState.vertex?.key === selection[0].key
      ? selectState.vertex
      : null;
  const draftPoints = pointCount(drawState);
  const busy = isGestureActive(selectState) || drawState.kind !== 'idle';

  return useMemo(
    () => ({
      containerProps: { onPointerDown, onPointerMove, onPointerUp, onPointerCancel, onKeyDown },
      overlay,
      handles,
      vertex,
      draftPoints,
      busy,
      cancel,
      finishDraw,
      deleteVertex,
      insertVertexAfter,
    }),
    [
      onPointerDown,
      onPointerMove,
      onPointerUp,
      onPointerCancel,
      onKeyDown,
      overlay,
      handles,
      vertex,
      draftPoints,
      busy,
      cancel,
      finishDraw,
      deleteVertex,
      insertVertexAfter,
    ],
  );
}
