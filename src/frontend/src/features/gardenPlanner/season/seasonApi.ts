import { tenantClient } from '@/api/client';
import { getRotationTimeline } from '../history/historyApi';
import type { SeasonReport, SeasonRequest } from './seasonTypes';

/** GP-FR-171: check (`dry_run`) or write last year's slot places as free slots; the same report either way. */
export async function startNewSeason(
  siteKey: string,
  request: SeasonRequest,
): Promise<SeasonReport> {
  const { data } = await tenantClient.post<SeasonReport>(
    `/sites/${encodeURIComponent(siteKey)}/plan/new-season`,
    request,
  );
  return data;
}

/**
 * GP-API-039, display only: the family (or families) that stood in a bed in `year`. An unrecorded year, a bed the
 * rotation does not apply to or a request that fails give an empty list - the hint is never a reason to stop.
 */
export async function familiesOfYear(
  bedKey: string,
  year: number,
  signal?: AbortSignal,
): Promise<string[]> {
  try {
    const timeline = await getRotationTimeline(
      bedKey,
      Math.min(Math.max(new Date().getFullYear() - year + 1, 1), 10),
    );
    if (signal?.aborted) return [];
    const names = (timeline.timeline.find((entry) => entry.year === year)?.plantings ?? [])
      .map((planting) => planting.family_name)
      .filter((name): name is string => typeof name === 'string' && name !== '');
    return [...new Set(names)];
  } catch {
    return [];
  }
}
