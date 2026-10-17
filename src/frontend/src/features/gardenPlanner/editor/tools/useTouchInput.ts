/**
 * The touch layer of the editor (REQ-053 GP-UX-034/037/040/041): wraps the pointer handlers of
 * `useEditorTools` and applies the binding gesture table for fingers. Mouse and pen pass straight
 * through. For touch:
 *
 * | Gesture                              | Result                                                    |
 * |--------------------------------------|-----------------------------------------------------------|
 * | tap on an object                     | select it (the panel / sheet opens)                       |
 * | tap on several plant markers         | list "plants nearby", never a guessed single hit          |
 * | drag from an object, < 500 ms        | pan the plan                                              |
 * | press an object for 500 ms, then drag | move it (progress ring, vibration where available)       |
 * | drag on empty ground                 | pan - or a marquee in multi-select mode                   |
 * | drag on a handle                     | edit the handle at once (the handle itself is the target) |
 * | two fingers                          | pan with the midpoint, zoom with the spread               |
 *
 * A second finger within 50 ms of the first and a palm-sized contact patch are ignored (wet
 * fingers, GP-UX-041). Drawing tools and the pan tool take the finger as it is.
 */
import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type PointerEvent as ReactPointerEvent,
} from 'react';
import type { PlanModel } from '../../model/planModel';
import type { Point } from '../../model/types';
import type { PlanRenderer } from '../../renderer';
import type { PlanTool } from '../../state/gardenPlanSlice';
import type { EditorTools } from './useEditorTools';
import type { HandleSet } from './handles';
import { handleAt } from './handles';
import {
  isPhantomTouch,
  keysNearPoint,
  LONG_PRESS_MS,
  TOUCH_PAN_THRESHOLD_PX,
  twoFingerStep,
} from './touchGestures';

export type PointerKind = 'mouse' | 'pen' | 'touch';

export interface TouchInputOptions {
  tool: PlanTool;
  multiSelect: boolean;
  plan: PlanModel;
  renderer: PlanRenderer;
  handles: HandleSet | null;
  base: EditorTools['containerProps'];
  onPan: (dxPx: number, dyPx: number) => void;
  /** Pinch: `factor` > 1 zooms in about `centerPx`. Optional until the viewport can zoom (WP 2.5). */
  onZoom?: (factor: number, centerPx: Point) => void;
  /** A tap on two or more plant markers: the keys under the finger. */
  onPlantsNearby: (keys: string[], pointPx: Point) => void;
}

/** The long-press progress ring (GP-UX-040). */
export interface PressRing {
  pointPx: Point;
  /** The hold time is over: the next drag moves the object. */
  armed: boolean;
}

export interface TouchInput {
  containerProps: EditorTools['containerProps'] & {
    onContextMenu: (event: React.MouseEvent<HTMLElement>) => void;
  };
  ring: PressRing | null;
  /** The pointer type of the last pointer-down, for the context menu (mouse/pen only). */
  lastPointerType: () => PointerKind;
}

type Mode = 'forward' | 'undecided' | 'armed' | 'pan' | 'plants';

interface Single {
  id: number;
  mode: Mode;
  downPx: Point;
  lastPx: Point;
  plantKeys: string[];
}

function pixelOf(event: ReactPointerEvent<HTMLElement>): Point {
  const element = event.currentTarget;
  const box = element.getBoundingClientRect();
  return [
    event.clientX - box.left - element.clientLeft,
    event.clientY - box.top - element.clientTop,
  ];
}

function kindOf(event: ReactPointerEvent<HTMLElement>): PointerKind {
  return event.pointerType === 'touch' || event.pointerType === 'pen' ? event.pointerType : 'mouse';
}

export function useTouchInput(options: TouchInputOptions): TouchInput {
  const latest = useRef(options);
  useEffect(() => {
    latest.current = options;
  });
  const touches = useRef(new Map<number, Point>());
  const ignored = useRef(new Set<number>());
  const firstDownAt = useRef<number | null>(null);
  const single = useRef<Single | null>(null);
  const multi = useRef<{ ids: [number, number]; prev: [Point, Point] } | null>(null);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const lastKind = useRef<PointerKind>('mouse');
  const [ring, setRing] = useState<PressRing | null>(null);

  const stopTimer = useCallback(() => {
    if (timer.current !== null) clearTimeout(timer.current);
    timer.current = null;
  }, []);
  useEffect(() => stopTimer, [stopTimer]);

  const reset = useCallback(() => {
    stopTimer();
    single.current = null;
    multi.current = null;
    setRing(null);
  }, [stopTimer]);

  const onPointerDown = useCallback(
    (event: ReactPointerEvent<HTMLElement>) => {
      const o = latest.current;
      lastKind.current = kindOf(event);
      if (event.pointerType !== 'touch') {
        o.base.onPointerDown(event);
        return;
      }
      if (event.isPrimary) {
        // A primary pointer means no other touch is down: forget a finger whose end was never seen.
        if (single.current) o.base.onPointerCancel(event);
        touches.current.clear();
        ignored.current.clear();
        firstDownAt.current = null;
        reset();
      }
      const contact = {
        timeStamp: event.timeStamp,
        width: event.width,
        height: event.height,
      };
      if (isPhantomTouch(contact, firstDownAt.current, touches.current.size)) {
        ignored.current.add(event.pointerId);
        return;
      }
      const point = pixelOf(event);
      touches.current.set(event.pointerId, point);
      if (touches.current.size === 1) firstDownAt.current = event.timeStamp;

      if (touches.current.size === 2) {
        // A second finger ends whatever one finger began and starts the pan/zoom.
        if (single.current) o.base.onPointerCancel(event);
        stopTimer();
        setRing(null);
        const entries = [...touches.current.entries()];
        single.current = null;
        multi.current = {
          ids: [entries[0][0], entries[1][0]],
          prev: [entries[0][1], entries[1][1]],
        };
        return;
      }
      if (touches.current.size > 2) return;

      const next: Single = {
        id: event.pointerId,
        mode: 'forward',
        downPx: point,
        lastPx: point,
        plantKeys: [],
      };
      single.current = next;
      if (o.tool !== 'select') {
        o.base.onPointerDown(event);
        return;
      }
      const onHandle =
        o.handles !== null &&
        handleAt(o.handles.handles, (p: Point) => o.renderer.toScreen(p), point) !== null;
      if (onHandle) {
        o.base.onPointerDown(event); // a handle is its own 48 px target: no long-press
        return;
      }
      const hits = o.renderer.hitTestAll(point);
      const isMarker = (key: string) => key in o.plan.plants || key in o.plan.slots;
      const plantKeys = keysNearPoint((p) => o.renderer.hitTestAll(p), point).filter(isMarker);
      if (plantKeys.length >= 2) {
        // Dense markers: a tap lists them, it never guesses one (GP-UX-034).
        next.mode = 'plants';
        next.plantKeys = plantKeys;
        return;
      }
      if (hits.length === 0 && o.multiSelect) {
        o.base.onPointerDown(event); // marquee, only in multi-select mode (GP-UX-037)
        return;
      }
      next.mode = 'undecided';
      o.base.onPointerDown(event); // the press selects; moving it is decided below
      if (hits.length > 0) {
        setRing({ pointPx: point, armed: false });
        timer.current = setTimeout(() => {
          timer.current = null;
          const current = single.current;
          if (current && current.id === next.id && current.mode === 'undecided') {
            current.mode = 'armed';
            setRing({ pointPx: current.downPx, armed: true });
            if (typeof navigator !== 'undefined') navigator.vibrate?.(30);
          }
        }, LONG_PRESS_MS);
      }
    },
    [reset, stopTimer],
  );

  const onPointerMove = useCallback((event: ReactPointerEvent<HTMLElement>) => {
    const o = latest.current;
    if (event.pointerType !== 'touch') {
      o.base.onPointerMove(event);
      return;
    }
    if (ignored.current.has(event.pointerId) || !touches.current.has(event.pointerId)) return;
    const point = pixelOf(event);
    touches.current.set(event.pointerId, point);
    const pair = multi.current;
    if (pair) {
      const a = touches.current.get(pair.ids[0]);
      const b = touches.current.get(pair.ids[1]);
      if (!a || !b) return;
      const step = twoFingerStep(pair.prev, [a, b]);
      pair.prev = [a, b];
      if (step.pan[0] !== 0 || step.pan[1] !== 0) o.onPan(step.pan[0], step.pan[1]);
      if (step.zoom !== 1) o.onZoom?.(step.zoom, step.center);
      return;
    }
    const current = single.current;
    if (!current || current.id !== event.pointerId) return;
    if (current.mode === 'forward' || current.mode === 'armed') {
      o.base.onPointerMove(event);
      return;
    }
    if (current.mode === 'undecided' || current.mode === 'plants') {
      const travelled = Math.hypot(point[0] - current.downPx[0], point[1] - current.downPx[1]);
      if (travelled < TOUCH_PAN_THRESHOLD_PX) return;
      // Moved before the hold time was over: the finger pans (GP-UX-040).
      if (current.mode === 'undecided') o.base.onPointerCancel(event);
      current.mode = 'pan';
      if (timer.current !== null) {
        clearTimeout(timer.current);
        timer.current = null;
      }
      setRing(null);
    }
    if (current.mode === 'pan') {
      o.onPan(point[0] - current.lastPx[0], point[1] - current.lastPx[1]);
      current.lastPx = point;
    }
  }, []);

  const finish = useCallback(
    (event: ReactPointerEvent<HTMLElement>, cancelled: boolean) => {
      const o = latest.current;
      if (event.pointerType !== 'touch') {
        if (cancelled) o.base.onPointerCancel(event);
        else o.base.onPointerUp(event);
        return;
      }
      touches.current.delete(event.pointerId);
      if (touches.current.size === 0) firstDownAt.current = null;
      if (ignored.current.delete(event.pointerId)) return;
      if (multi.current) {
        // The pair is over once one finger lifts; the other one does nothing until it lifts too.
        multi.current = null;
        return;
      }
      const current = single.current;
      if (!current || current.id !== event.pointerId) return;
      const mode = current.mode;
      reset();
      if (cancelled) {
        o.base.onPointerCancel(event);
      } else if (mode === 'plants') {
        o.onPlantsNearby(current.plantKeys, current.downPx);
      } else if (mode !== 'pan') {
        o.base.onPointerUp(event);
      }
    },
    [reset],
  );

  const onPointerUp = useCallback(
    (event: ReactPointerEvent<HTMLElement>) => finish(event, false),
    [finish],
  );
  const onPointerCancel = useCallback(
    (event: ReactPointerEvent<HTMLElement>) => finish(event, true),
    [finish],
  );
  const onContextMenu = useCallback((event: React.MouseEvent<HTMLElement>) => {
    // The long-press of a finger is the move gesture, not a menu: keep the browser's out of the way.
    if (lastKind.current === 'touch') event.preventDefault();
  }, []);
  const lastPointerType = useCallback(() => lastKind.current, []);

  const base = options.base;
  const containerProps = useMemo(
    () => ({
      onPointerDown,
      onPointerMove,
      onPointerUp,
      onPointerCancel,
      onKeyDown: base.onKeyDown,
      onContextMenu,
    }),
    [base.onKeyDown, onContextMenu, onPointerCancel, onPointerDown, onPointerMove, onPointerUp],
  );
  return useMemo(
    () => ({ containerProps, ring, lastPointerType }),
    [containerProps, ring, lastPointerType],
  );
}
