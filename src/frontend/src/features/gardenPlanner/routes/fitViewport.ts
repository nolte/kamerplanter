import { boundingBox } from '../model/geometry';
import type { PlanModel } from '../model/planModel';
import type { BoundingBox } from '../model/types';
import type { Viewport } from '../renderer/types';

/** Free space around the drawing, as a share of its larger side. */
const MARGIN_RATIO = 0.05;
/** Never zoom in past this: a single small bed must not fill the screen with huge strokes. */
const MAX_PX_PER_M = 200;
/** Never zoom out past this; a 1 km garden is still drawn (the editor adds pan and zoom in WP 2.4). */
const MIN_PX_PER_M = 0.5;

/**
 * The model-space box (metres, `[minX, minY, maxX, maxY]`) around everything the plan draws: the
 * garden boundary, every placed bed and every garden object. `null` = nothing to draw. Beds without
 * a geometry (stock data, REQ-053 GP-ACC-035) are not placed and do not count.
 */
export function planContentBounds(plan: PlanModel): BoundingBox | null {
  const boxes: BoundingBox[] = [];
  const boundary = plan.settings?.boundary;
  if (boundary) boxes.push(boundingBox(boundary));
  for (const location of Object.values(plan.locations)) {
    if (location.geometry) boxes.push(location.bbox ?? boundingBox(location.geometry));
  }
  for (const object of Object.values(plan.gardenObjects)) {
    boxes.push(object.bbox ?? boundingBox(object.geometry));
  }
  if (boxes.length === 0) return null;
  return boxes.reduce<BoundingBox>(
    (acc, [x0, y0, x1, y1]) => [
      Math.min(acc[0], x0),
      Math.min(acc[1], y0),
      Math.max(acc[2], x1),
      Math.max(acc[3], y1),
    ],
    [Infinity, Infinity, -Infinity, -Infinity],
  );
}

/**
 * A viewport that shows `bounds` completely in `widthPx` x at most `maxHeightPx`. Screen y points
 * down and model y up, so the origin is the top-left corner `(minX, maxY)` (see {@link Viewport}).
 * The drawing is centred horizontally by the container; the height follows the aspect ratio.
 */
export function fitViewport(bounds: BoundingBox, widthPx: number, maxHeightPx: number): Viewport {
  const [minX, minY, maxX, maxY] = bounds;
  const sizeX = Math.max(maxX - minX, 0.1);
  const sizeY = Math.max(maxY - minY, 0.1);
  const margin = Math.max(sizeX, sizeY) * MARGIN_RATIO;
  const contentW = sizeX + 2 * margin;
  const contentH = sizeY + 2 * margin;
  const fit = Math.min(widthPx / contentW, maxHeightPx / contentH);
  const pxPerM = Math.min(MAX_PX_PER_M, Math.max(MIN_PX_PER_M, fit));
  return {
    originM: [minX - margin, maxY + margin],
    pxPerM,
    widthPx: Math.round(contentW * pxPerM),
    heightPx: Math.round(contentH * pxPerM),
  };
}
