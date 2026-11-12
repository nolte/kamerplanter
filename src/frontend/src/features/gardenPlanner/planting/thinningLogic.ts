/**
 * How many plants a sown row or zone holds after thinning (REQ-053 §11.3, W-015) — the TypeScript port of
 * `app/domain/calculators/thinning_calculator.py::thinning_count`, for the live count in the thinning dialog. The
 * server computes the stored count itself; the two must agree (`thinningLogic.test.ts` runs the same cases).
 *
 * - Row: `floor(length / spacing)` plants, one every `spacing` along the line.
 * - Zone with a row spacing (band or row sowing, #2862): `floor(area / (rowSpacing × spacing))` plants.
 * - Zone without one (broadcast): `floor(area / spacing²)` plants, the square-grid estimate.
 * - At least one seedling stays standing.
 *
 * No default spacing or row spacing (E-10): without a spacing there is no count, the grower enters it; the row
 * spacing comes from the run or the species profile (the server's plan) or the grower.
 */
import type { FailedPlanting, PlantingItem } from './plantingTypes';

/** Decimals a quotient is rounded to before the floor (1.0 m / 10 cm is 10 plants, not 9). */
const FLOOR_DECIMALS = 6;
/** The widest spacing a sown crop is thinned to (cm, `MAX_THINNING_SPACING_CM` of the server). */
export const MAX_THINNING_SPACING_CM = 200;
/** The row-spacing bounds of the layout (cm, GP-FR-060: `MIN_ROW_SPACING_CM`/`MAX_SPACING_CM` of the server). */
export const MIN_THINNING_ROW_SPACING_CM = 5;
export const MAX_THINNING_ROW_SPACING_CM = 1500;

/** The rule a count follows: along a row, rows × in-row spacing, or the square-grid estimate of a zone. */
export type ThinningFormula = 'along_row' | 'rows' | 'square_grid';

export function thinningFormula(kind: 'length' | 'area', rowSpacingCm: number | null = null): ThinningFormula {
  if (kind === 'length') return 'along_row';
  return rowSpacingCm !== null ? 'rows' : 'square_grid';
}

/** The area one plant takes in a zone (m²): row spacing × spacing, else the square of the spacing. */
function cellM2(spacingCm: number, rowSpacingCm: number | null): number {
  const spacingM = spacingCm / 100;
  return rowSpacingCm !== null ? spacingM * (rowSpacingCm / 100) : spacingM * spacingM;
}
/**
 * A slot is offered for a replant only when its plant died. A senesced plant ended its natural life (an annual at the
 * end of its season): that is no failure to make good (agrobiology review of WP 10.9).
 */
const REPLANT_TERMINATIONS: ReadonlySet<string> = new Set(['died']);

/** Whether a single spacing is longer than the row, or one plant's cell larger than the zone: then one seedling stays. */
export function spacingExceedsSlot(
  kind: 'length' | 'area',
  value: number,
  spacingCm: number,
  rowSpacingCm: number | null = null,
): boolean {
  return kind === 'length' ? spacingCm / 100 > value : cellM2(spacingCm, rowSpacingCm) > value;
}

export function thinningCount(
  kind: 'length' | 'area',
  value: number,
  spacingCm: number,
  rowSpacingCm: number | null = null,
): number | null {
  if (!(spacingCm > 0) || !(value > 0)) return null;
  if (rowSpacingCm !== null && !(rowSpacingCm > 0)) return null;
  const perPlant = kind === 'length' ? spacingCm / 100 : cellM2(spacingCm, rowSpacingCm);
  const raw = Number((value / perPlant).toFixed(FLOOR_DECIMALS));
  return Math.max(1, Math.floor(raw));
}

/** A decimal typed with a comma or a point; `null` when empty or not a number. */
export function parseDecimal(text: string): number | null {
  const trimmed = text.trim().replace(',', '.');
  if (trimmed === '') return null;
  const parsed = Number(trimmed);
  return Number.isFinite(parsed) ? parsed : null;
}

/** A planned position that can be sown: a row or a zone, not yet sown. */
export function isSowable(item: PlantingItem): boolean {
  return item.state === 'planned' && !item.sown_at && (item.slot_role === 'row' || item.slot_role === 'zone');
}

/**
 * The failed slots of a bed (§11.3 "ausgefallen"): a slot whose newest plant died and in which nothing
 * stands or is planned now — the slot is free for a replant. One line per slot, the newest failure.
 */
export function failedSlots(items: readonly PlantingItem[]): FailedPlanting[] {
  const busy = new Set(
    items
      .filter((item) => item.state === 'active' || item.state === 'planned')
      .map((item) => item.slot_key)
      .filter((key): key is string => Boolean(key)),
  );
  const newest = new Map<string, PlantingItem>();
  for (const item of items) {
    if (!item.slot_key || busy.has(item.slot_key)) continue;
    if (item.state !== 'historical' && item.state !== 'harvested') continue;
    const current = newest.get(item.slot_key);
    if (!current || (item.removed_on ?? '') > (current.removed_on ?? '')) newest.set(item.slot_key, item);
  }
  return [...newest.values()]
    .filter((item) => item.termination_type != null && REPLANT_TERMINATIONS.has(item.termination_type))
    .map((item) => ({
      slotKey: item.slot_key as string,
      slotId: item.slot_id ?? '',
      speciesKey: item.species_key,
      cultivarKey: item.cultivar_key ?? null,
      removedOn: item.removed_on ?? null,
    }))
    .sort((a, b) => a.slotId.localeCompare(b.slotId));
}
