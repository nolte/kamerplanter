/**
 * Wheel zoom without a React render per notch (GP-NFR-034, D-01 WP 9.7). A burst of wheel events (a mouse wheel's
 * notches, a touchpad pinch) moves a *pending* view; the drawing follows it with one CSS transform of the plan layer,
 * and the editor commits the pending view once the wheel has been idle for {@link WHEEL_COMMIT_IDLE_MS}. Culling,
 * level of detail and the sharp redraw happen at that commit. Pure helpers here; the editor owns the timer.
 */
import type { Point } from '../model/types';
import { zoomAround, type ZoomView } from '../model/units';

/** The wheel's quiet time before the pending zoom is committed: longer than the gap between two notches. */
export const WHEEL_COMMIT_IDLE_MS = 120;

export interface LayerTransform {
  scale: number;
  txPx: number;
  tyPx: number;
}

/** The next pending view after one wheel step around `anchorPx` (canvas pixels, y down). */
export function wheelStep(base: ZoomView, nextPxPerM: number, anchorPx: Point, minPxPerM: number): ZoomView {
  return zoomAround(base, nextPxPerM, anchorPx, minPxPerM);
}

/**
 * The screen map from the committed view to the pending one: screen point `p` of the drawing lands at
 * `scale * p + t`. With `transform-origin: 0 0` that is `translate(t) scale(scale)`.
 */
export function layerTransform(committed: ZoomView, pending: ZoomView): LayerTransform {
  const scale = pending.pxPerM / committed.pxPerM;
  return {
    scale,
    txPx: (committed.originM[0] - pending.originM[0]) * pending.pxPerM,
    tyPx: (pending.originM[1] - committed.originM[1]) * pending.pxPerM,
  };
}

export function cssTransform(t: LayerTransform): string {
  return `translate(${t.txPx}px, ${t.tyPx}px) scale(${t.scale})`;
}

/**
 * How to commit a pending view through the editor's callbacks: a zoom to its scale around the fixed point of the
 * screen map (one zoom equals the whole burst), or - when the scale came back to where it was - the pan that remains.
 */
export function commitOf(
  committed: ZoomView,
  pending: ZoomView,
): { kind: 'zoom'; pxPerM: number; anchorPx: Point } | { kind: 'pan'; dxPx: number; dyPx: number } | null {
  const t = layerTransform(committed, pending);
  if (Math.abs(t.scale - 1) < 1e-9) {
    return Math.abs(t.txPx) < 1e-6 && Math.abs(t.tyPx) < 1e-6 ? null : { kind: 'pan', dxPx: t.txPx, dyPx: t.tyPx };
  }
  return { kind: 'zoom', pxPerM: pending.pxPerM, anchorPx: [t.txPx / (1 - t.scale), t.tyPx / (1 - t.scale)] };
}
