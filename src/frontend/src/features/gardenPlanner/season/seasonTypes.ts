/**
 * Wire types of "new season from the previous year" (REQ-053 GP-FR-171, WP 7.16), derived from
 * `app/api/v1/garden_plan/schemas.py` (`PlanSeasonRequest`, `PlanSeasonResponse`).
 */

export type SeasonBedStatus =
  'copied' | 'skipped_active_plants' | 'skipped_retired' | 'skipped_slot_quota' | 'nothing_to_copy';

/** The new season is bounded like the server's: 2001 up to next year. */
export const MIN_SEASON_YEAR = 2001;

export interface SeasonRequest {
  year: number;
  dry_run: boolean;
  /** The `plan_revision` the check saw; another stored revision is a 409. */
  expected_revision?: number | null;
}

export interface SeasonBedOutcome {
  location_key: string;
  status: SeasonBedStatus;
  slots: number;
  slots_outside_bed: number;
}

export interface SeasonReport {
  year: number;
  source_year: number;
  dry_run: boolean;
  applied: boolean;
  plan_revision: number | null;
  beds_copied: number;
  beds_skipped: number;
  slots_to_create: number;
  beds: SeasonBedOutcome[];
}
