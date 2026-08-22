import type { DiaryAnalysisState, DiaryEntryType } from '@/api/types';

/**
 * REQ-051 §6.2 — the filter state of the tenant-wide diary overview.
 *
 * Kept in its own module so the page, the filter toolbar and the tests agree on
 * one shape instead of three near-copies. Every field maps 1:1 onto a query
 * parameter of `GET /t/{slug}/diary`; nothing here is evaluated in the client.
 * Filtering, sorting and paging happen in one AQL statement server-side, which
 * is what makes the response's `total` the real number of matches rather than
 * "how many of the loaded page survived".
 */
export interface DiaryOverviewFilterState {
  /** Repeatable filter; empty means "every state". */
  analysisStates: DiaryAnalysisState[];
  plantKey: string;
  speciesKey: string;
  entryType: DiaryEntryType | '';
  tag: string;
  /** `YYYY-MM-DD`, inclusive lower bound on `created_at`. */
  from: string;
  /** `YYYY-MM-DD`, inclusive upper bound on `created_at`. */
  to: string;
  /** Free-text search over title and text (AK-17), evaluated server-side. */
  q: string;
  sort: 'created_at' | 'analyzed_at';
}

/** No filter at all, sorted by capture date descending — the §2.5.2 default. */
export const EMPTY_DIARY_FILTERS: DiaryOverviewFilterState = {
  analysisStates: [],
  plantKey: '',
  speciesKey: '',
  entryType: '',
  tag: '',
  from: '',
  to: '',
  q: '',
  sort: 'created_at',
};

/**
 * How many filters narrow the result right now.
 *
 * The sort order is **not** counted: re-ordering shows the same rows, so
 * offering "reset filters" because a user sorted by analysis time would promise
 * to bring back rows that were never gone.
 */
export function activeDiaryFilterCount(state: DiaryOverviewFilterState): number {
  let count = 0;
  if (state.analysisStates.length > 0) count += 1;
  if (state.plantKey) count += 1;
  if (state.speciesKey) count += 1;
  if (state.entryType) count += 1;
  if (state.tag.trim()) count += 1;
  if (state.from) count += 1;
  if (state.to) count += 1;
  if (state.q.trim()) count += 1;
  return count;
}

/** The two shorthand selections §2.5.2 calls the most frequent access of all. */
export type DiaryQuickFilter = 'all' | 'completed' | 'requested';

/**
 * Which shorthand the current state corresponds to, if any.
 *
 * Deliberately exact: a selection of `completed` *plus* `failed` is neither
 * "only with a result" nor "all", so no shorthand is marked as active and the
 * chips do not claim a selection the list does not have.
 */
export function activeQuickFilter(
  states: DiaryAnalysisState[],
): DiaryQuickFilter | null {
  if (states.length === 0) return 'all';
  if (states.length === 1 && states[0] === 'completed') return 'completed';
  if (states.length === 1 && states[0] === 'requested') return 'requested';
  return null;
}
