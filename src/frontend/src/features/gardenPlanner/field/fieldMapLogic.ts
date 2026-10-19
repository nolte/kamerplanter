/**
 * Which bed a tap on the field map means (REQ-053 §18.1 step 2): the whole bed is the target; a tap on a
 * plant or slot means its bed; a tap next to a bed too small to hit (< 48 px on screen) still finds it
 * within half the minimum target. And whether a remembered view still shows the plan. Pure.
 */
import { boundingBox } from '../model/geometry';
import type { PlanModel } from '../model/planModel';
import type { BoundingBox, Point } from '../model/types';
import { MAX_PX_PER_M } from '../model/units';
import type { FieldViewport } from './fieldPrefs';

/** The smallest on-screen size a bed may have as a target (§18.1 step 2). */
export const MIN_BED_TARGET_PX = 48;

/** The bed a hit key belongs to: the bed itself, the bed of a plant or of a slot. */
export function bedOfKey(plan: PlanModel, key: string, bedKeys: ReadonlySet<string>): string | null {
  if (bedKeys.has(key)) return key;
  const plant = plan.plants[key];
  // A plant names its bed directly or through its slot.
  const plantBed = plant ? (plant.location_key ?? (plant.slot_key ? plan.slots[plant.slot_key]?.location_key : null) ?? null) : null;
  if (plantBed && bedKeys.has(plantBed)) return plantBed;
  const slotBed = plan.slots[key]?.location_key ?? null;
  if (slotBed && bedKeys.has(slotBed)) return slotBed;
  return null;
}

/**
 * The bed whose bounding box lies closest to `pointM`, if within `toleranceM`. Ties go to the smaller bed,
 * which is the one a near miss most likely aimed at.
 */
export function nearestBed(
  plan: PlanModel,
  bedKeys: ReadonlySet<string>,
  pointM: Point,
  toleranceM: number,
): string | null {
  let best: { key: string; distance: number; area: number } | null = null;
  for (const key of bedKeys) {
    const location = plan.locations[key];
    if (!location?.geometry) continue;
    const [x0, y0, x1, y1] = location.bbox ?? boundingBox(location.geometry);
    const dx = Math.max(x0 - pointM[0], 0, pointM[0] - x1);
    const dy = Math.max(y0 - pointM[1], 0, pointM[1] - y1);
    const distance = Math.hypot(dx, dy);
    if (distance > toleranceM) continue;
    const area = (x1 - x0) * (y1 - y0);
    if (!best || distance < best.distance || (distance === best.distance && area < best.area)) {
      best = { key, distance, area };
    }
  }
  return best?.key ?? null;
}

/**
 * A remembered view must still show a fair part of the plan: the share of the drawing (or of the canvas,
 * when the plan is larger than it) that has to stay in sight. Below it the map would look empty.
 */
export const MIN_VISIBLE_SHARE = 0.25;

/**
 * The remembered view, made to fit the canvas it is restored onto (GP-UX-030), or `null` for "fit the
 * whole plan". The zoom is clamped to `[minPxPerM, MAX_PX_PER_M]`; the view is dropped when the plan has
 * moved out of sight - another device, a turned phone, a plan that shrank - so the map never opens empty.
 * `widthPx` × `heightPx` is the canvas of the current container; `bounds` the box of everything drawn.
 */
export function restoreFieldView(
  view: FieldViewport | null,
  bounds: BoundingBox,
  widthPx: number,
  heightPx: number,
  minPxPerM: number,
): FieldViewport | null {
  if (view === null || widthPx <= 0 || heightPx <= 0) return null;
  const { pxPerM: stored, originM } = view;
  if (!Number.isFinite(stored) || !Number.isFinite(originM[0]) || !Number.isFinite(originM[1])) return null;
  const pxPerM = Math.min(MAX_PX_PER_M, Math.max(stored, minPxPerM));
  const visible: BoundingBox = [originM[0], originM[1] - heightPx / pxPerM, originM[0] + widthPx / pxPerM, originM[1]];
  // Degenerate plans (a single line) still count with a minimum size, as in `fitViewport`.
  const [minX, minY, maxX, maxY] = bounds;
  const sizeX = Math.max(maxX - minX, 0.1);
  const sizeY = Math.max(maxY - minY, 0.1);
  const overlapX = Math.min(visible[2], minX + sizeX) - Math.max(visible[0], minX);
  const overlapY = Math.min(visible[3], minY + sizeY) - Math.max(visible[1], minY);
  if (overlapX <= 0 || overlapY <= 0) return null;
  const visibleArea = (visible[2] - visible[0]) * (visible[3] - visible[1]);
  const needed = Math.min(sizeX * sizeY, visibleArea) * MIN_VISIBLE_SHARE;
  return overlapX * overlapY >= needed ? { pxPerM, originM } : null;
}
