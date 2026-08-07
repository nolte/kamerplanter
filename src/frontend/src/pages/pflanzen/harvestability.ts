import type { CurrentPhaseResponse, GrowthPhase } from '@/api/types';

/**
 * The only species field harvestability depends on, declared structurally so a
 * full {@link import('@/api/types').Species} can be passed straight in.
 *
 * `allows_harvest` is typed as a required `boolean` on `Species`, but the wire
 * is a tri-state: the backend model defaults it to `True`
 * (`app/domain/models/species.py`), and a record written before the field
 * existed — or projected by an older API — can arrive without it. Admitting
 * `undefined`/`null` here is what makes that third state *decidable* instead of
 * accidental (see {@link plantCanBeHarvested}).
 */
export interface HarvestabilitySpecies {
  allows_harvest?: boolean | null;
}

/**
 * Can this plant ever be harvested at all? (REQ-007, issue #963)
 *
 * The plant-instance detail page used to answer this question twice, with two
 * different answers: the estimated-harvest-date row declined to predict a date
 * for a *Dracaena reflexa*, while the harvest-readiness panel 930 lines below it
 * offered to assess that same never-arriving harvest's ripeness — trichomes and
 * Brix on a houseplant. This predicate is the single answer both displays now
 * ask for, so the two can no longer contradict each other about the same plant.
 *
 * **Deliberately fail-open.** An unknown answer renders the harvest UI:
 *
 * - `allows_harvest` defaults to `True` on the domain model, so a species that
 *   was imported (REQ-012) or enriched (REQ-011) without a curated value *means*
 *   "harvestable", not "unknown". Treating an absent field as `false` would
 *   invent a suppression the data never asked for.
 * - The two errors are not equally expensive. Showing a readiness panel on an
 *   ornamental is noise. Hiding it on a real crop removes the only route in the
 *   application to record a ripeness observation — `ObservationCreateDialog` is
 *   reachable from nowhere else (#818) — so a fail-closed guard would silently
 *   amputate a feature rather than merely clutter a page.
 * - There is no flicker to trade against: `PlantInstanceDetailPage` gates its
 *   whole body on a page-level `loading` flag, and its loader awaits the species
 *   request before clearing it. By the time either call site renders, `species`
 *   is resolved or definitively absent — never "still in flight". A `null`
 *   species here therefore means "this plant has no species record", not "wait".
 *
 * The species axis alone decides it. The phase-level axes (`has_harvest_phase`,
 * `GrowthPhase.allows_harvest`) are *not* consulted, on purpose: a crop whose
 * lifecycle is incomplete or unassigned would otherwise lose its readiness panel,
 * and a ripeness assessment — unlike a harvest *date* — needs no phase durations
 * to be meaningful. See {@link harvestDateIsPredictable} for why the date estimate
 * asks strictly more.
 */
export function plantCanBeHarvested(species: HarvestabilitySpecies | null | undefined): boolean {
  return species?.allows_harvest !== false;
}

/** Inputs of {@link harvestDateIsPredictable}. */
export interface HarvestDatePredictabilityInput {
  species: HarvestabilitySpecies | null;
  currentPhase: Pick<CurrentPhaseResponse, 'cycle_type' | 'has_harvest_phase'> | null;
  growthPhases: Pick<GrowthPhase, 'allows_harvest'>[];
}

/**
 * Can a *single terminal harvest date* be predicted for this plant?
 *
 * A strictly narrower question than {@link plantCanBeHarvested}, and it stays a
 * separate predicate rather than being harmonised into one: the two displays
 * genuinely differ. A perennial fruit tree *is* harvestable — its readiness is
 * worth assessing every season — but it has no single date to count down to,
 * because its cycle restarts. Likewise a tomato whose lifecycle phases have not
 * been configured yet can have its ripeness observed, but nothing to add up into
 * a date.
 *
 * So this predicate is `plantCanBeHarvested()` **plus** the conditions that only
 * a date needs:
 *
 * - perennial cycle → recurring harvests, no single endpoint;
 * - no harvest phase in the plant's phase sequence → nothing to aim at;
 * - no growth phase that allows harvest → no duration sum to project from.
 *
 * Sharing the species axis is the point: a future change to what "harvestable"
 * means lands on both displays at once, which is exactly what #963 was about.
 */
export function harvestDateIsPredictable({
  species,
  currentPhase,
  growthPhases,
}: HarvestDatePredictabilityInput): boolean {
  if (!plantCanBeHarvested(species)) return false;
  // Perennials have recurring cycles — no single harvest endpoint.
  if (currentPhase?.cycle_type === 'perennial') return false;
  // No harvest phase configured — nothing to estimate.
  if (currentPhase?.has_harvest_phase === false) return false;
  return growthPhases.some((gp) => gp.allows_harvest);
}
