/**
 * "Days since the last watering" per bed (REQ-053 GP-UX-031, #2466 decision): four classes, worded as a fact
 * ("days since"), never as "needs water" - whether a bed needs water is not something the plan knows.
 */
export type WateredClass = 'd0_1' | 'd2_3' | 'd4_7' | 'd8plus';

export const WATERED_CLASSES: readonly WateredClass[] = ['d0_1', 'd2_3', 'd4_7', 'd8plus'];

const DAY_MS = 86_400_000;

function utcDayStart(instantMs: number): number {
  return Math.floor(instantMs / DAY_MS) * DAY_MS;
}

/** Whole UTC calendar days from the watering to `nowMs` (the same day rule as the backend); never negative. */
export function daysSince(wateredAt: string, nowMs: number): number | null {
  const at = Date.parse(wateredAt);
  if (Number.isNaN(at)) return null;
  return Math.max(0, Math.round((utcDayStart(nowMs) - utcDayStart(at)) / DAY_MS));
}

export function wateredClassOf(days: number): WateredClass {
  if (days <= 1) return 'd0_1';
  if (days <= 3) return 'd2_3';
  if (days <= 7) return 'd4_7';
  return 'd8plus';
}

/** What the renderer draws per bed: the class for the hatching and the number for the label. */
export interface BedWatered {
  days: number;
  wateredClass: WateredClass;
}

/** Beds without a (valid) watering stay out of the map: they get no hatching, and the legend says so. */
export function wateredByBed(
  lastWateredAt: Readonly<Record<string, string | null | undefined>>,
  nowMs: number,
): Record<string, BedWatered> {
  const result: Record<string, BedWatered> = {};
  for (const [key, at] of Object.entries(lastWateredAt)) {
    if (!at) continue;
    const days = daysSince(at, nowMs);
    if (days !== null) result[key] = { days, wateredClass: wateredClassOf(days) };
  }
  return result;
}
