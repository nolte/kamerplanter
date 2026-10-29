import type { PlanUnderlay, UnderlayCalibration } from '../model/types';

/**
 * The maths of the underlay (REQ-053 GP-FR-033), kept apart from the UI so it can be tested on its own.
 *
 * The picture is calibrated by two points in pixels and the real distance between them: that fixes the scale
 * (metres per pixel). The server refuses what cannot be computed with (non-finite numbers, two points less than
 * a pixel apart, a non-positive distance); the same rules run here so the form says so before it asks.
 */

/** Two calibration points closer than this are one point (the server's `MIN_UNDERLAY_POINT_GAP_PX`). */
export const MIN_POINT_GAP_PX = 1;
/** The longest real distance a calibration may state, in metres (the server's `MAX_UNDERLAY_DISTANCE_M`). */
export const MAX_DISTANCE_M = 2000;
export const MIN_OPACITY = 0.05;

export type Point = readonly [number, number];

export function pixelDistance(p1: Point, p2: Point): number {
  return Math.hypot(p2[0] - p1[0], p2[1] - p1[1]);
}

/** Pixels per metre between the two points, or `null` while the input cannot give a scale. */
export function pixelsPerMetre(calibration: {
  p1_px: Point;
  p2_px: Point;
  distance_m: number;
}): number | null {
  const pixels = pixelDistance(calibration.p1_px, calibration.p2_px);
  const { distance_m: metres } = calibration;
  if (!Number.isFinite(pixels) || !Number.isFinite(metres)) return null;
  if (pixels < MIN_POINT_GAP_PX || metres <= 0 || metres > MAX_DISTANCE_M) return null;
  return pixels / metres;
}

/** Metres per pixel of a stored calibration; `null` for one that gives no scale. */
export function metresPerPixel(calibration: UnderlayCalibration): number | null {
  const perMetre = pixelsPerMetre(calibration);
  return perMetre === null ? null : 1 / perMetre;
}

/** The SVG transform that lays the picture (in pixels) onto the plan frame, whose y axis points down in the SVG. */
export function underlayTransform(underlay: PlanUnderlay): string | null {
  const scale = metresPerPixel(underlay.calibration);
  if (scale === null) return null;
  const [ox, oy] = underlay.origin;
  // translate to the plan position of pixel (0, 0); the plan turns counter-clockwise, the SVG clockwise.
  return `translate(${round(ox)} ${round(-oy)}) rotate(${round(-underlay.rotation_deg)}) scale(${round(scale, 8)})`;
}

/** A pointer position inside the displayed picture as a pixel of the picture itself. */
export function toImagePoint(
  client: Point,
  box: { left: number; top: number; width: number; height: number },
  natural: { width: number; height: number },
): [number, number] | null {
  if (box.width <= 0 || box.height <= 0) return null;
  const x = ((client[0] - box.left) / box.width) * natural.width;
  const y = ((client[1] - box.top) / box.height) * natural.height;
  if (x < 0 || y < 0 || x > natural.width || y > natural.height) return null;
  return [round(x, 1), round(y, 1)];
}

export function clampOpacity(value: number): number {
  if (!Number.isFinite(value)) return 0.5;
  return Math.min(1, Math.max(MIN_OPACITY, value));
}

function round(value: number, digits = 4): number {
  const factor = 10 ** digits;
  return Math.round(value * factor) / factor;
}
