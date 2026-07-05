import { tenantClient as client } from '../client';
import type {
  OverwinteringOverride,
  OverwinteringProfile,
  SeasonOverview,
  SeasonState,
} from '../types';

/**
 * REQ-047 §4.4 — tenant-scoped season & overwintering-automation API layer.
 * All paths are relative to `/api/v1`; the tenant client prepends
 * `/t/{tenant_slug}` automatically.
 */

/** Aggregated season states across all outdoor/greenhouse sites of the tenant. */
export async function getSeasonOverview(): Promise<SeasonOverview> {
  const { data } = await client.get<SeasonOverview>('/season/overview');
  return data;
}

/** Current season state (and trigger source) of a single site. */
export async function getSiteSeasonState(siteKey: string): Promise<SeasonState> {
  const { data } = await client.get<SeasonState>(
    `/sites/${siteKey}/season-state`,
  );
  return data;
}

/** Auto-materialised overwintering profile of a plant instance. */
export async function getPlantOverwintering(
  plantKey: string,
): Promise<OverwinteringProfile> {
  const { data } = await client.get<OverwinteringProfile>(
    `/plants/${plantKey}/overwintering`,
  );
  return data;
}

/** Override individual profile fields (sets `user_overridden=true`). */
export async function overridePlantOverwintering(
  plantKey: string,
  patch: OverwinteringOverride,
): Promise<OverwinteringProfile> {
  const { data } = await client.patch<OverwinteringProfile>(
    `/plants/${plantKey}/overwintering`,
    patch,
  );
  return data;
}

/** Reset to the automatic derivation (`user_overridden=false`) and re-materialise. */
export async function resetPlantOverwintering(
  plantKey: string,
): Promise<OverwinteringProfile> {
  const { data } = await client.post<OverwinteringProfile>(
    `/plants/${plantKey}/overwintering/reset`,
    {},
  );
  return data;
}
