/**
 * Site fit of a bed — TypeScript port of `app/domain/calculators/site_fit_calculator.py`
 * (REQ-053 GP-FR-160, E-05, GP-ACC-053).
 *
 * The Python module is the reference and carries the full rationale; this port mirrors it rule for
 * rule. Both run against the `site_fit` cases of
 * `spec/e2e-testcases/fixtures/garden-plan-vectors.json` (§19.6): a vector test per side reads that
 * file, nobody copies the cases. The block is generic — a bed feature against a species demand — and
 * REQ-054 reuses it.
 *
 * Pure: no I/O, no React. `shade_tolerance` is the tolerance ("grows down to this step") and never
 * derives the requirement (E-05).
 */

import type { SunExposure } from './types';

/** What a species needs from its bed (`Species.light_requirement`). */
export type LightRequirement = 'full_sun' | 'partial_shade' | 'shade';
/** How far down the sun ladder a species still grows (`Species.shade_tolerance`). */
export type ShadeTolerance = 'full_sun' | 'partial_shade' | 'shade' | 'deep_shade';
export type SiteFit = 'ok' | 'marginal' | 'poor' | 'unknown';
export type SiteFitReason =
  | 'match'
  | 'too_shady'
  | 'tolerated'
  | 'tolerance_unknown'
  | 'too_sunny'
  | 'bed_unknown'
  | 'requirement_unknown';

export interface SiteFitResult {
  fit: SiteFit;
  reason: SiteFitReason;
  /** Steps between the bed and the requirement; negative = the bed is shadier than required. */
  steps: number;
}

/** Position on the ladder; the higher, the sunnier. `unknown` is not on it. A Map: a plain object would answer `constructor`. */
const LADDER: ReadonlyMap<string, number> = new Map([
  ['deep_shade', 0],
  ['shade', 1],
  ['partial_shade', 2],
  ['full_sun', 3],
]);
const REQUIREMENTS: ReadonlySet<string> = new Set(['full_sun', 'partial_shade', 'shade']);

function rank(value: string | null | undefined): number | null {
  if (value === null || value === undefined) return null;
  return LADDER.get(value) ?? null;
}

export function assessSiteFit(
  sunExposure: SunExposure | string | null | undefined,
  lightRequirement: LightRequirement | string | null | undefined,
  shadeTolerance: ShadeTolerance | string | null | undefined,
): SiteFitResult {
  const bed = rank(sunExposure);
  if (bed === null) return { fit: 'unknown', reason: 'bed_unknown', steps: 0 };
  const required =
    lightRequirement && REQUIREMENTS.has(lightRequirement) ? rank(lightRequirement) : null;
  if (required === null) return { fit: 'unknown', reason: 'requirement_unknown', steps: 0 };

  const steps = bed - required;
  if (steps === 0) return { fit: 'ok', reason: 'match', steps };
  if (steps > 0) return { fit: steps === 1 ? 'marginal' : 'poor', reason: 'too_sunny', steps };
  if (steps <= -2) return { fit: 'poor', reason: 'too_shady', steps };
  // Exactly one step shadier: the tolerance decides.
  const tolerance = rank(shadeTolerance);
  if (tolerance === null) return { fit: 'marginal', reason: 'tolerance_unknown', steps };
  if (tolerance <= bed) return { fit: 'marginal', reason: 'tolerated', steps };
  return { fit: 'poor', reason: 'too_shady', steps };
}
