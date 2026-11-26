/**
 * UI-NFR-019 R-024 — the predefined values a kiosk quick-select offers for the measurements
 * logged most often. The values follow the wireframe of §3.2 (EC) and the common target band of
 * a nutrient solution (pH); the free "Manuell" entry stays beside them for everything else (R-026).
 *
 * Temperature and humidity are named by R-024 too, but no form a kiosk session reaches asks for
 * them today — a preset without a field would only be dead code.
 */
export interface QuickSelectPreset {
  values: readonly number[];
  /** Decimal places the tiles show, so `2` reads "2,0" next to "2,5". */
  fractionDigits: number;
}

/** EC of a nutrient solution or runoff, in mS/cm. */
export const EC_QUICK_SELECT: QuickSelectPreset = { values: [1.0, 1.5, 2.0, 2.5, 3.0], fractionDigits: 1 };

/** pH of a nutrient solution or runoff. */
export const PH_QUICK_SELECT: QuickSelectPreset = { values: [5.5, 5.8, 6.0, 6.2, 6.5], fractionDigits: 1 };
