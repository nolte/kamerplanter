import { describe, it, expect } from 'vitest';
import {
  plantCanBeHarvested,
  harvestDateIsPredictable,
  type HarvestabilitySpecies,
} from '@/pages/pflanzen/harvestability';

/**
 * Unit tests for the shared harvestability predicates (issue #963).
 *
 * These pin the *decisions* — above all the fail-open answer to an unknown
 * `allows_harvest` — independently of any component, so a future refactor of the
 * plant-detail page cannot quietly flip them. The two call sites are exercised
 * through the real page in
 * `PlantInstanceDetailPageHarvestReadiness.test.tsx`.
 */

/** `allows_harvest` absent — the shape an un-curated / pre-flag record arrives in. */
const UNKNOWN: HarvestabilitySpecies = {};

const HARVEST_PHASE = [{ allows_harvest: false }, { allows_harvest: true }];

describe('plantCanBeHarvested (REQ-007 / #963)', () => {
  it('says yes for a species curated as harvestable', () => {
    expect(plantCanBeHarvested({ allows_harvest: true })).toBe(true);
  });

  it('says no for a species curated as not harvestable (the Dracaena case)', () => {
    expect(plantCanBeHarvested({ allows_harvest: false })).toBe(false);
  });

  // The fail-open decision, pinned. `allows_harvest` defaults to True on the
  // domain model, so an absent value means "harvestable", not "unknown" — and
  // hiding the panel on a real crop would remove the only route to record a
  // ripeness observation (#818). Do not "harden" this to `=== true`.
  it('fails open for a species whose allows_harvest was never set', () => {
    expect(plantCanBeHarvested(UNKNOWN)).toBe(true);
  });

  it('fails open for a null value on the wire', () => {
    expect(plantCanBeHarvested({ allows_harvest: null })).toBe(true);
  });

  it('fails open when there is no species record at all', () => {
    expect(plantCanBeHarvested(null)).toBe(true);
    expect(plantCanBeHarvested(undefined)).toBe(true);
  });
});

describe('harvestDateIsPredictable (REQ-007 / #963)', () => {
  it('predicts a date for an annual crop with a harvest phase', () => {
    expect(
      harvestDateIsPredictable({
        species: { allows_harvest: true },
        currentPhase: { cycle_type: 'annual', has_harvest_phase: true },
        growthPhases: HARVEST_PHASE,
      }),
    ).toBe(true);
  });

  // The shared axis: whatever the phases say, a species that yields nothing gets
  // no harvest date — the same answer the readiness panel now gives.
  it('refuses a date for a non-harvestable species even when a phase allows harvest', () => {
    expect(
      harvestDateIsPredictable({
        species: { allows_harvest: false },
        currentPhase: { cycle_type: 'annual', has_harvest_phase: true },
        growthPhases: HARVEST_PHASE,
      }),
    ).toBe(false);
  });

  it('fails open on an unknown species, exactly like the readiness guard', () => {
    expect(
      harvestDateIsPredictable({
        species: UNKNOWN,
        currentPhase: { cycle_type: 'annual', has_harvest_phase: true },
        growthPhases: HARVEST_PHASE,
      }),
    ).toBe(true);
    expect(
      harvestDateIsPredictable({
        species: null,
        currentPhase: null,
        growthPhases: HARVEST_PHASE,
      }),
    ).toBe(true);
  });

  // The date-only axes. These are why this stays a second predicate: a perennial
  // fruit tree is harvestable (readiness panel stays) but has no single date.
  it('refuses a date for a perennial, which plantCanBeHarvested still allows', () => {
    const species = { allows_harvest: true };
    expect(
      harvestDateIsPredictable({
        species,
        currentPhase: { cycle_type: 'perennial', has_harvest_phase: true },
        growthPhases: HARVEST_PHASE,
      }),
    ).toBe(false);
    expect(plantCanBeHarvested(species)).toBe(true);
  });

  it('refuses a date when the phase sequence has no harvest phase', () => {
    expect(
      harvestDateIsPredictable({
        species: { allows_harvest: true },
        currentPhase: { cycle_type: 'annual', has_harvest_phase: false },
        growthPhases: HARVEST_PHASE,
      }),
    ).toBe(false);
  });

  it('refuses a date when no growth phase allows harvest', () => {
    expect(
      harvestDateIsPredictable({
        species: { allows_harvest: true },
        currentPhase: { cycle_type: 'annual', has_harvest_phase: true },
        growthPhases: [{ allows_harvest: false }],
      }),
    ).toBe(false);
  });

  it('refuses a date when the lifecycle has no phases at all', () => {
    expect(
      harvestDateIsPredictable({
        species: { allows_harvest: true },
        currentPhase: null,
        growthPhases: [],
      }),
    ).toBe(false);
  });
});
