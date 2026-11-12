/**
 * Wording helpers for a feeding event's dose (REQ-053 W-007, #2903). A feeding from the REQ-004 form is a volume
 * of nutrient solution; a top dress logged in the care log or by a bed task (compost, horn shavings, a dry
 * fertiliser) has no volume and carries its dose as material, amount and unit. Pure: the detail page, the list
 * and their tests share them.
 */
import type { TFunction } from 'i18next';
import type { FeedingEvent } from '@/api/types';
import { formatQuantity } from '@/features/gardenPlanner/history/historyFormat';

const AREA_UNITS = new Set(['l_per_m2', 'g_per_m2']);

/** A solid dose spread on the soil: no volume, no EC/pH, no run-off. */
export function isTopDress(event: Pick<FeedingEvent, 'application_method'>): boolean {
  return event.application_method === 'top_dress';
}

/** The plants of the dose: every plant a bed dose names, else the one `plant_key` (empty for a whole bed). */
export function feedingPlantKeys(event: Pick<FeedingEvent, 'plant_key' | 'plant_keys'>): string[] {
  const keys = event.plant_keys ?? [];
  if (keys.length > 0) return [...keys];
  return event.plant_key ? [event.plant_key] : [];
}

/** The material in the reader's language; a free-text material is shown as typed. */
export function materialLabel(t: TFunction, material: string | null | undefined): string {
  if (!material) return '';
  return t(`enums.careMaterial.${material}`, { defaultValue: material });
}

/**
 * `2 Liter`, `150 Gramm pro m² (375 Gramm gesamt)`; empty when the event names no amount. The total is the bed's
 * (dose × area) and is only shown for a dose per m².
 */
export function formatFeedingDose(
  t: TFunction,
  event: Pick<FeedingEvent, 'dose_quantity' | 'dose_unit' | 'quantity_total' | 'quantity_total_unit'>,
): string {
  const dose = formatQuantity(t, { quantity: event.dose_quantity ?? null, unit: event.dose_unit ?? null });
  if (dose === '') return '';
  if (event.dose_unit && AREA_UNITS.has(event.dose_unit) && event.quantity_total != null) {
    const total = formatQuantity(t, { quantity: event.quantity_total, unit: event.quantity_total_unit ?? null });
    return t('pages.feedingEvents.doseWithTotal', { dose, total });
  }
  return dose;
}

/**
 * Whether the liquid-feeding fields (volume, EC, pH, run-off) mean something for this event: always for a
 * solution; for a top dress only when one of them was recorded after all (a value is never hidden).
 */
export function showsLiquidFields(event: FeedingEvent): boolean {
  if (!isTopDress(event)) return true;
  return (
    event.volume_applied_liters > 0 ||
    [
      event.measured_ec_before,
      event.measured_ec_after,
      event.measured_ph_before,
      event.measured_ph_after,
      event.runoff_ec,
      event.runoff_ph,
      event.runoff_volume_liters,
    ].some((value) => value != null)
  );
}

/**
 * The amount column of a feeding: the litres of a solution; without a volume (a top dress, or millilitres of a
 * concentrate whose water is unknown) the dose as logged - never "0 L".
 */
export function formatFeedingAmount(t: TFunction, event: FeedingEvent): string {
  if (event.volume_applied_liters > 0) return `${event.volume_applied_liters} L`;
  return formatFeedingDose(t, event) || '—';
}
