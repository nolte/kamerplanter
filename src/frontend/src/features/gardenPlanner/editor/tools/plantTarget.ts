/**
 * What a click of the tool "Pflanze setzen" lands on (REQ-053 GP-UX-071, #2913). The tool puts ONE plant into exactly
 * the free point slot clicked; everything else is told, never guessed: an occupied or reserved spot, a row or zone
 * (sowing lives in the bed), a bed without planting spots, a bed whose spots are too small to hit at this zoom, a miss
 * beside the spots, or no bed at all. Pure: the plan, the keys the renderer found and the zoom.
 */
import { pointInPolygon, pointSegmentDistance } from '../../model/geometry';
import type { PlanModel } from '../../model/planModel';
import type { PlanSlot, Point } from '../../model/types';
import { MARKER_MIN_SPACING_PX, markersVisible } from '../../renderer/lod';
import { isAreaLocation, markerIndex } from '../../renderer/planIndex';

/** The zoom a "zoom in to the spots" goes to: markers this far apart are easy to hit, also with a finger. */
const COMFORT_SPACING_PX = MARKER_MIN_SPACING_PX * 3;

export type PlantTarget =
  /** A free point slot: the dialog opens for it. */
  | { kind: 'free'; bedKey: string; slotKey: string }
  /** Something stands there already; `plantKey` is `null` when only the slot's flag says so. */
  | { kind: 'occupied'; bedKey: string; slotKey: string; plantKey: string | null }
  /** A planned run reserves the spot (GP-FR-074): it stays free for that run. */
  | { kind: 'reserved'; bedKey: string; slotKey: string }
  /** A row or a zone: sown in the bed (SowingDialog), not set plant by plant. */
  | { kind: 'rowSlot'; bedKey: string; slotKey: string }
  /** The bed's planting spots are drawn as one count at this zoom: zoom to `pxPerM` to see and hit them. */
  | { kind: 'zoomIn'; bedKey: string; pxPerM: number }
  /** The bed has planting spots, but the click hit none of them. */
  | { kind: 'missed'; bedKey: string }
  /** A bed without any planting spot: they are laid out on the bed's page. */
  | { kind: 'noSlots'; bedKey: string }
  /** An area, a garden object or empty ground: no bed. */
  | { kind: 'noBed' };

/** A point slot: a position with an origin and no line or surface geometry. */
export function isPointSlot(slot: PlanSlot): boolean {
  return Boolean(slot.plan_geometry?.origin) && !slot.plan_geometry?.kind;
}

/** The plant standing on `slotKey`, if the plan knows one. */
function plantOnSlot(plan: PlanModel, slotKey: string): string | null {
  for (const plant of Object.values(plan.plants)) if (plant.slot_key === slotKey) return plant.key;
  return null;
}

/** What a slot is for the tool: free, occupied (by a plant or by its flag) or reserved by a planned run. */
export function slotState(
  plan: PlanModel,
  slotKey: string,
): { state: 'free' | 'reserved' } | { state: 'occupied'; plantKey: string | null } | { state: 'missing' } {
  const slot = plan.slots[slotKey];
  if (!slot) return { state: 'missing' };
  const plantKey = plantOnSlot(plan, slotKey);
  if (plantKey !== null || slot.currently_occupied === true) return { state: 'occupied', plantKey };
  if (slot.planned_from) return { state: 'reserved' };
  return { state: 'free' };
}

/** The free point slots of a bed, in the order the bed lists them (row, sequence, id). */
export function freePointSlots(plan: PlanModel, bedKey: string): PlanSlot[] {
  return Object.values(plan.slots)
    .filter(
      (slot) => slot.location_key === bedKey && isPointSlot(slot) && slotState(plan, slot.key).state === 'free',
    )
    .sort(
      (a, b) =>
        (a.row_index ?? 0) - (b.row_index ?? 0) ||
        (a.sequence ?? 0) - (b.sequence ?? 0) ||
        a.slot_id.localeCompare(b.slot_id),
    );
}

/** A row (line) or zone (surface) slot of `bedKey` under `pointM`, within `slopM` of a line. */
function rowSlotAt(plan: PlanModel, bedKey: string, pointM: Point, slopM: number): PlanSlot | null {
  for (const slot of Object.values(plan.slots)) {
    const geometry = slot.plan_geometry;
    if (slot.location_key !== bedKey || !geometry?.kind || !geometry.points || geometry.points.length < 2) continue;
    const points = geometry.points;
    if (geometry.kind === 'polygon' && points.length >= 3 && pointInPolygon(pointM, points)) return slot;
    if (geometry.kind === 'polyline') {
      const reach = Math.max((geometry.width_m ?? 0) / 2, slopM);
      for (let i = 0; i + 1 < points.length; i += 1) {
        if (pointSegmentDistance(pointM, points[i], points[i + 1]) <= reach) return slot;
      }
    }
  }
  return null;
}

/** The marker key's slot: a slot key itself, or the slot of the plant drawn there. */
function markerSlot(plan: PlanModel, key: string): { slotKey: string; plantKey: string | null } | null {
  const slot = plan.slots[key];
  if (slot && isPointSlot(slot)) return { slotKey: key, plantKey: null };
  const plant = plan.plants[key];
  if (plant?.slot_key && plan.slots[plant.slot_key]) return { slotKey: plant.slot_key, plantKey: plant.key };
  return null;
}

/**
 * The target of a click at `pointM` (model metres) over `keys` (the renderer's hit stack, topmost first, or for a
 * finger the keys around the touch, nearest first). `maxPxPerM` caps a zoom-in.
 */
export function plantTargetAt(
  plan: PlanModel,
  keys: readonly string[],
  pointM: Point,
  pxPerM: number,
  slopM: number,
  maxPxPerM: number,
): PlantTarget {
  for (const key of keys) {
    const marker = markerSlot(plan, key);
    if (!marker) continue;
    const bedKey = plan.slots[marker.slotKey].location_key;
    const state = slotState(plan, marker.slotKey);
    if (state.state === 'occupied') {
      return { kind: 'occupied', bedKey, slotKey: marker.slotKey, plantKey: state.plantKey ?? marker.plantKey };
    }
    if (state.state === 'reserved') return { kind: 'reserved', bedKey, slotKey: marker.slotKey };
    return { kind: 'free', bedKey, slotKey: marker.slotKey };
  }
  const bedKey = keys.find((key) => {
    const location = plan.locations[key];
    return location !== undefined && !isAreaLocation(location);
  });
  if (bedKey === undefined) return { kind: 'noBed' };
  const row = rowSlotAt(plan, bedKey, pointM, slopM);
  if (row) return { kind: 'rowSlot', bedKey, slotKey: row.key };
  const bed = markerIndex(plan).get(bedKey);
  if (!bed || bed.markers.length === 0) return { kind: 'noSlots', bedKey };
  if (!markersVisible(bed.minSpacingM, pxPerM)) {
    const wanted = Number.isFinite(bed.minSpacingM) ? COMFORT_SPACING_PX / bed.minSpacingM : pxPerM;
    return { kind: 'zoomIn', bedKey, pxPerM: Math.min(Math.max(wanted, pxPerM), maxPxPerM) };
  }
  return { kind: 'missed', bedKey };
}
