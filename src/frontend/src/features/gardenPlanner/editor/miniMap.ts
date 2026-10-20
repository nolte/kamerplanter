/**
 * The mini-map (REQ-053 GP-UX-014, §9.6): when it shows and where a click on it takes the view. Pure.
 *
 * It appears only when the plan is larger than what the viewport shows - the site extent exceeds four times the
 * viewport (areas, in metres) - because on a plan that fits the screen it would show the screen again.
 */
import type { BoundingBox, Point } from '../model/types';
import type { Viewport } from '../renderer';

/** The side of the square mini-map in pixels (GP-UX-014). */
export const MINI_MAP_PX = 120;

/** The extent must exceed this many viewports (by area) for the mini-map to show (§9.6). */
export const MINI_MAP_MIN_RATIO = 4;

/** The part of the plan the viewport shows, `[min_x, min_y, max_x, max_y]` in metres. */
export function viewportBox(viewport: Viewport): BoundingBox {
  const width = viewport.widthPx / viewport.pxPerM;
  const height = viewport.heightPx / viewport.pxPerM;
  // Screen y points down and model y up: the origin is the top-left corner (see `Viewport`).
  return [
    viewport.originM[0],
    viewport.originM[1] - height,
    viewport.originM[0] + width,
    viewport.originM[1],
  ];
}

const area = (box: BoundingBox): number => (box[2] - box[0]) * (box[3] - box[1]);

/** Whether the mini-map is shown for a site of `extent` seen through `viewport`. */
export function miniMapVisible(extent: BoundingBox | null, viewport: Viewport): boolean {
  if (extent === null || viewport.pxPerM <= 0) return false;
  const seen = area(viewportBox(viewport));
  return seen > 0 && area(extent) > MINI_MAP_MIN_RATIO * seen;
}

export interface MiniMapScale {
  /** Pixels per metre of the mini-map. */
  scale: number;
  /** Where the extent starts inside the square (the shorter side is centred). */
  offsetPx: Point;
}

/** The fit of `extent` into the square of {@link MINI_MAP_PX}. */
export function miniMapScale(extent: BoundingBox): MiniMapScale {
  const width = Math.max(extent[2] - extent[0], 1e-6);
  const height = Math.max(extent[3] - extent[1], 1e-6);
  const scale = MINI_MAP_PX / Math.max(width, height);
  return {
    scale,
    offsetPx: [(MINI_MAP_PX - width * scale) / 2, (MINI_MAP_PX - height * scale) / 2],
  };
}

/** Model point -> pixel in the mini-map (y flipped). */
export function toMiniMap(point: Point, extent: BoundingBox, fit: MiniMapScale): Point {
  return [
    fit.offsetPx[0] + (point[0] - extent[0]) * fit.scale,
    fit.offsetPx[1] + (extent[3] - point[1]) * fit.scale,
  ];
}

/** Pixel in the mini-map -> model point, clamped to the extent. */
export function fromMiniMap(pixel: Point, extent: BoundingBox, fit: MiniMapScale): Point {
  const x = extent[0] + (pixel[0] - fit.offsetPx[0]) / fit.scale;
  const y = extent[3] - (pixel[1] - fit.offsetPx[1]) / fit.scale;
  return [Math.min(Math.max(x, extent[0]), extent[2]), Math.min(Math.max(y, extent[1]), extent[3])];
}

/**
 * The pan (in canvas pixels, the unit of `onPan`) that centres `viewport` on `target`. Dragging the plan by
 * `(dx, dy)` moves the origin by `(-dx / px, +dy / px)`, so the sign is the other way round.
 */
export function panToCentre(viewport: Viewport, target: Point): Point {
  const box = viewportBox(viewport);
  const centre: Point = [(box[0] + box[2]) / 2, (box[1] + box[3]) / 2];
  return [-(target[0] - centre[0]) * viewport.pxPerM, (target[1] - centre[1]) * viewport.pxPerM];
}
