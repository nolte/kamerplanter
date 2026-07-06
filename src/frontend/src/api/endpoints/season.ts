import { tenantClient as client } from '../client';
import type {
  OverwinteringOverride,
  OverwinteringProfile,
  PlantOverwinteringStatus,
  SeasonOverview,
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

/** Auto-materialised overwintering profile of a plant instance. */
export async function getPlantOverwintering(
  plantKey: string,
): Promise<OverwinteringProfile> {
  const { data } = await client.get<OverwinteringProfile>(
    `/plants/${plantKey}/overwintering`,
  );
  return data;
}

/**
 * Winter-hardiness status of a plant instance — always resolves (HTTP 200), even
 * when no profile exists yet. Used to distinguish "genuinely winter-hardy" from
 * "profile will be materialised in autumn" in the empty state.
 */
export async function getPlantOverwinteringStatus(
  plantKey: string,
): Promise<PlantOverwinteringStatus> {
  const { data } = await client.get<PlantOverwinteringStatus>(
    `/plants/${plantKey}/overwintering/status`,
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
