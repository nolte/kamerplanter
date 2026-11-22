/**
 * The form of "What stood here in {year}?" (REQ-053 GP-FR-131, GP-API-042) as pure functions: the
 * years on offer, the body to send and what is still missing. The server validates again; this
 * only spares the round trip for the obvious cases.
 */
import type { BackfillBody, PlanRole, RotationYear, Season } from './historyTypes';

/** The server accepts `current year - 10 .. current year - 1`. */
export const BACKFILL_YEARS_BACK = 10;

export interface BackfillForm {
  year: number;
  season: Season | '';
  planRole: PlanRole;
  speciesKey: string;
  familyKey: string;
}

export type BackfillError = 'family' | 'year';

/** Years on offer, newest first. */
export function backfillYears(now: Date): number[] {
  const current = now.getFullYear();
  return Array.from({ length: BACKFILL_YEARS_BACK }, (_, index) => current - 1 - index);
}

/** The newest year with nothing recorded, else last year: where the grower most likely starts. */
export function firstEmptyYear(timeline: readonly RotationYear[], now: Date): number {
  const years = backfillYears(now);
  const recorded = new Set(timeline.filter((entry) => entry.plantings.length > 0).map((entry) => entry.year));
  return years.find((year) => !recorded.has(year)) ?? years[0];
}

export function emptyBackfillForm(year: number): BackfillForm {
  return { year, season: '', planRole: 'main_crop', speciesKey: '', familyKey: '' };
}

/**
 * What the form still lacks. A species names its family, a fallow year needs neither; anything else
 * needs a family (GP-API-042).
 */
export function backfillErrors(form: BackfillForm, now: Date): Partial<Record<'family' | 'year', BackfillError>> {
  const errors: Partial<Record<'family' | 'year', BackfillError>> = {};
  if (!backfillYears(now).includes(form.year)) errors.year = 'year';
  if (form.planRole !== 'fallow' && !form.speciesKey && !form.familyKey) errors.family = 'family';
  return errors;
}

/** The body: a fallow year names neither species nor family; a species stands for its family. */
export function buildBackfillBody(form: BackfillForm, speciesFamilyKey: string | null): BackfillBody {
  const body: BackfillBody = { year: form.year, plan_role: form.planRole };
  if (form.season) body.season = form.season;
  if (form.planRole === 'fallow') return body;
  if (form.speciesKey) body.species_key = form.speciesKey;
  const family = form.familyKey || speciesFamilyKey;
  if (family) body.family_key = family;
  return body;
}
