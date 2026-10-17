/**
 * Pure rules of the touch input (REQ-053 GP-UX-040/041/052): the phantom-touch filter for wet
 * fingers and palms, the two-finger pan/zoom step, and the pan that keeps a selected object above
 * the bottom sheet. No DOM, no timers - the hook `useTouchInput` feeds the numbers.
 */
import type { Point } from '../../model/types';

/** A second finger this soon after the first is a wet-finger ghost (GP-UX-041). */
export const PHANTOM_WINDOW_MS = 50;
/** A contact patch wider or taller than this (CSS px) is a palm, not a fingertip. */
export const PHANTOM_CONTACT_PX = 64;
/** Hold time before a touch press on an object becomes a move (GP-UX-040). */
export const LONG_PRESS_MS = 500;
/** Travel (px) that turns an undecided touch press into a pan. */
export const TOUCH_PAN_THRESHOLD_PX = 8;

export interface TouchContact {
  timeStamp: number;
  width?: number;
  height?: number;
}

/**
 * Whether a new touch must be ignored. `firstDownAt` is the `timeStamp` of the earliest touch that
 * is still down (`null` when none is), `active` the number of accepted touches down now.
 */
export function isPhantomTouch(
  contact: TouchContact,
  firstDownAt: number | null,
  active: number,
): boolean {
  if ((contact.width ?? 0) > PHANTOM_CONTACT_PX || (contact.height ?? 0) > PHANTOM_CONTACT_PX) {
    return true;
  }
  return active >= 1 && firstDownAt !== null && contact.timeStamp - firstDownAt < PHANTOM_WINDOW_MS;
}

export function centroidOf(a: Point, b: Point): Point {
  return [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2];
}

export interface TwoFingerStep {
  /** Movement of the midpoint in pixels. */
  pan: Point;
  /** Ratio of the new finger distance to the old one (> 1 = spread = zoom in). */
  zoom: number;
  /** The new midpoint: the fixed point of the zoom. */
  center: Point;
}

/** What two fingers moving from `before` to `after` mean (pan with the midpoint, zoom with the spread). */
export function twoFingerStep(before: [Point, Point], after: [Point, Point]): TwoFingerStep {
  const [b0, b1] = before;
  const [a0, a1] = after;
  const oldDistance = Math.hypot(b0[0] - b1[0], b0[1] - b1[1]);
  const newDistance = Math.hypot(a0[0] - a1[0], a0[1] - a1[1]);
  const oldCenter = centroidOf(b0, b1);
  const center = centroidOf(a0, a1);
  return {
    pan: [center[0] - oldCenter[0], center[1] - oldCenter[1]],
    zoom: oldDistance > 0 && newDistance > 0 ? newDistance / oldDistance : 1,
    center,
  };
}

/**
 * The vertical pan (px, positive = drag the plan down) that brings an object whose screen box is
 * `topPx..bottomPx` into the free area `0..visibleHeightPx` above a sheet, keeping `marginPx`.
 * 0 when it is visible already or cannot fit (the top edge wins then).
 */
export function panIntoView(
  topPx: number,
  bottomPx: number,
  visibleHeightPx: number,
  marginPx = 16,
): number {
  const fits = bottomPx - topPx + 2 * marginPx <= visibleHeightPx;
  if (!fits)
    return bottomPx > visibleHeightPx - marginPx || topPx < marginPx ? marginPx - topPx : 0;
  if (bottomPx + marginPx > visibleHeightPx) return visibleHeightPx - marginPx - bottomPx;
  if (topPx < marginPx) return marginPx - topPx;
  return 0;
}

/** Probe radii (px) and counts used to find markers near a fingertip. */
const NEARBY_RINGS: readonly (readonly [number, number])[] = [
  [12, 6],
  [24, 12],
];

/**
 * The keys `hit` finds at `pointPx` and around it, within about a fingertip (24 px): a finger is
 * not a pixel, so two markers closer than the touch target both count as "under the finger"
 * (GP-UX-034). Order: the exact point first, then rings outwards; each key once.
 */
export function keysNearPoint(hit: (pointPx: Point) => string[], pointPx: Point): string[] {
  const found: string[] = [...hit(pointPx)];
  for (const [radius, count] of NEARBY_RINGS) {
    for (let i = 0; i < count; i += 1) {
      const angle = (2 * Math.PI * i) / count;
      for (const key of hit([
        pointPx[0] + radius * Math.cos(angle),
        pointPx[1] + radius * Math.sin(angle),
      ])) {
        if (!found.includes(key)) found.push(key);
      }
    }
  }
  return found;
}
