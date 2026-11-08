import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, type RefObject } from 'react';
import { flushSync } from 'react-dom';
import type { Point } from '../model/types';
import { zoomAround, type ZoomView } from '../model/units';
import type { Viewport } from '../renderer';
import { WHEEL_COMMIT_IDLE_MS, commitOf, cssTransform, layerTransform } from './wheelZoom';

/** Ctrl + wheel: the zoom factor per wheel pixel (a 120 px notch zooms by e^0.18). */
export const WHEEL_ZOOM_PER_PX = 0.0015;

/** How long a committed view may wait for the route's render before the layer stops showing it (a refused zoom). */
const RECONCILE_MS = 250;

interface PendingZoomOptions {
  viewport: Viewport;
  onZoom?: (pxPerM: number, anchorPx: Point) => void;
  onPan: (dxPx: number, dyPx: number) => void;
  minPxPerM: number;
  canvasRef: RefObject<HTMLDivElement | null>;
  /** Changes whenever the canvas element is a new one (the list view was shown in between). */
  canvasKey: unknown;
}

export interface PendingZoom {
  /** Callback ref of the plan layer the pending view transforms (renderer, grid and the editor's overlays). */
  attachLayer: (element: HTMLDivElement | null) => void;
  /** Zoom to `pxPerM` around `anchorPx` from the newest view; `defer` waits for the wheel to be idle. */
  zoomTo: (pxPerM: number, anchorPx: Point, defer?: boolean) => void;
  /** The newest view: pending, committed-but-not-drawn, or drawn - what the next step starts from. */
  newestView: () => ZoomView;
}

/**
 * The editor's zoom with one render per gesture (GP-NFR-034). Three views are kept apart:
 *
 * - **drawn**: the viewport the renderer last drew (the route's prop);
 * - **target**: committed through `onZoom`/`onPan`, not drawn yet - the next step must start from it, or a wheel
 *   event between the commit and the render would drop the burst before it;
 * - **pending**: a wheel burst in progress, shown as a CSS transform of the plan layer until it is committed.
 *
 * The layer always shows the newest of them relative to the drawn view; it is reset when the route draws a new view,
 * and also when the route does not (a zoom it refuses or that changes nothing). A pointer press commits a pending
 * burst synchronously first, so hit testing and the overlays never work on a view the screen does not show.
 */
export function usePendingZoom({
  viewport,
  onZoom,
  onPan,
  minPxPerM,
  canvasRef,
  canvasKey,
}: PendingZoomOptions): PendingZoom {
  const layer = useRef<HTMLDivElement | null>(null);
  const drawn = useRef<ZoomView>(viewport);
  const target = useRef<ZoomView | null>(null);
  const pending = useRef<ZoomView | null>(null);
  const timer = useRef<number | null>(null);
  const reconcile = useRef<number | null>(null);
  const latest = useRef({ onZoom, onPan, minPxPerM });
  useEffect(() => {
    latest.current = { onZoom, onPan, minPxPerM };
  });

  const show = useCallback(() => {
    const element = layer.current;
    if (!element) return;
    const shown = pending.current ?? target.current;
    element.style.transform = shown ? cssTransform(layerTransform(drawn.current, shown)) : '';
  }, []);

  // A new drawn view: the committed one has arrived (or another change replaced it).
  useLayoutEffect(() => {
    drawn.current = viewport;
    target.current = null;
    if (reconcile.current !== null) {
      window.clearTimeout(reconcile.current);
      reconcile.current = null;
    }
    show();
  }, [viewport, show]);

  const newestView = useCallback(() => pending.current ?? target.current ?? drawn.current, []);

  const commit = useCallback(
    (sync: boolean) => {
      if (timer.current !== null) {
        window.clearTimeout(timer.current);
        timer.current = null;
      }
      const next = pending.current;
      if (next === null) return;
      pending.current = null;
      const { onZoom: zoom, onPan: pan } = latest.current;
      const step = commitOf(drawn.current, next);
      if (step === null || !zoom) {
        target.current = null;
        show();
        return;
      }
      target.current = next;
      const run = () => (step.kind === 'zoom' ? zoom(step.pxPerM, step.anchorPx) : pan(step.dxPx, step.dyPx));
      if (sync) flushSync(run);
      else run();
      // The route may draw nothing new (a refused or clamped-away zoom): then the layer must not keep the transform.
      if (target.current !== null) {
        if (reconcile.current !== null) window.clearTimeout(reconcile.current);
        reconcile.current = window.setTimeout(() => {
          reconcile.current = null;
          if (target.current !== null) {
            target.current = null;
            show();
          }
        }, RECONCILE_MS);
      }
    },
    [show],
  );

  const zoomTo = useCallback(
    (pxPerM: number, anchorPx: Point, defer = false) => {
      pending.current = zoomAround(newestView(), pxPerM, anchorPx, latest.current.minPxPerM);
      show();
      if (!defer) {
        commit(false);
        return;
      }
      if (timer.current !== null) window.clearTimeout(timer.current);
      timer.current = window.setTimeout(() => commit(false), WHEEL_COMMIT_IDLE_MS);
    },
    [commit, newestView, show],
  );

  useEffect(() => {
    const element = canvasRef.current;
    if (element === null) return undefined;
    const onWheel = (event: WheelEvent) => {
      if (!latest.current.onZoom) return;
      // A plain wheel (or a two-finger touchpad scroll) scrolls the page; zooming needs Ctrl/Cmd
      // (a touchpad pinch arrives as Ctrl + wheel) or the focus on the canvas.
      const focused = element.contains(document.activeElement);
      if (!event.ctrlKey && !event.metaKey && !focused) return;
      event.preventDefault();
      const box = element.getBoundingClientRect();
      const lines = event.deltaMode === 1 ? 16 : 1;
      const base = newestView();
      zoomTo(
        base.pxPerM * Math.exp(-event.deltaY * lines * WHEEL_ZOOM_PER_PX),
        [event.clientX - box.left - element.clientLeft, event.clientY - box.top - element.clientTop],
        true,
      );
    };
    // Before the editor's own press handler (React listens at the root): the press works on the view it sees.
    const onPressCapture = () => {
      if (pending.current !== null) commit(true);
    };
    element.addEventListener('wheel', onWheel, { passive: false });
    element.addEventListener('pointerdown', onPressCapture, { capture: true });
    return () => {
      element.removeEventListener('wheel', onWheel);
      element.removeEventListener('pointerdown', onPressCapture, { capture: true });
      // A burst cut off by a view switch is committed at once rather than lost.
      commit(false);
    };
  }, [canvasRef, canvasKey, commit, newestView, zoomTo]);

  useEffect(
    () => () => {
      if (reconcile.current !== null) window.clearTimeout(reconcile.current);
    },
    [],
  );

  const attachLayer = useCallback(
    (element: HTMLDivElement | null) => {
      layer.current = element;
      show();
    },
    [show],
  );

  return useMemo(() => ({ attachLayer, zoomTo, newestView }), [attachLayer, zoomTo, newestView]);
}
