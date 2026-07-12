/**
 * Phase reference profiles mirrored from the backend resource-profile generator
 * (`app/domain/engines/resource_profile_generator.py`). Kept purely as UI-side
 * presets/prefills for the calculators — the actual computation stays server-side
 * (`POST /calculations/*`). Values are intentionally identical to the backend so
 * dropdown presets match what the server would classify a VPD/DLI against.
 */

/** Growth phases the backend VPD classifier and resource generator recognise. */
export const PHASE_KEYS = [
  'seedling',
  'vegetative',
  'flowering',
  'flushing',
  'ripening',
  'dormancy',
] as const;

export type PhaseKey = (typeof PHASE_KEYS)[number];

export interface PhaseProfile {
  /** Lower bound of the phase's optimal VPD band (kPa). */
  vpdMin: number;
  /** Upper bound of the phase's optimal VPD band (kPa). */
  vpdMax: number;
  /** Reference light intensity (PPFD, µmol/m²/s). */
  ppfd: number;
  /** Reference photoperiod length (hours). */
  photoperiodHours: number;
}

export const PHASE_PROFILES: Record<PhaseKey, PhaseProfile> = {
  seedling: { vpdMin: 0.4, vpdMax: 0.8, ppfd: 200, photoperiodHours: 18 },
  vegetative: { vpdMin: 0.8, vpdMax: 1.2, ppfd: 400, photoperiodHours: 18 },
  flowering: { vpdMin: 1.0, vpdMax: 1.5, ppfd: 600, photoperiodHours: 12 },
  flushing: { vpdMin: 0.8, vpdMax: 1.2, ppfd: 400, photoperiodHours: 12 },
  ripening: { vpdMin: 1.2, vpdMax: 1.6, ppfd: 500, photoperiodHours: 12 },
  dormancy: { vpdMin: 0.4, vpdMax: 0.8, ppfd: 400, photoperiodHours: 18 },
};

/** Discrete PPFD presets surfaced as quick-select buttons in the photoperiod card. */
export const PPFD_PRESETS = [200, 400, 600] as const;

/**
 * Per-crop base-temperature presets for GDD. Distinct i18n keys keep them
 * selectable even where two crops share the same numeric base (10 °C).
 */
export interface BaseTempPreset {
  /** i18n suffix under `pages.calculations.gddBasePresets.*`. */
  key: string;
  /** Base temperature in °C. */
  value: number;
}

export const GDD_BASE_TEMP_PRESETS: readonly BaseTempPreset[] = [
  { key: 'coolSeason', value: 4 },
  { key: 'lettuce', value: 5 },
  { key: 'tomato', value: 10 },
  { key: 'maize', value: 10 },
  { key: 'warmSeason', value: 15 },
] as const;

/** Typical row spacings (cm) offered as slot-capacity quick picks. */
export const SPACING_PRESETS = [10, 15, 20, 25, 30, 40, 50, 60] as const;
