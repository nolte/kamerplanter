import { tenantClient } from '@/api/client';
import type { BedStatus, SunExposure } from '../model/types';
import type { BedListItem, BedPatchResult, BedSummary, SoilProfile, SunProfilePatch } from './types';

/**
 * REST access to beds (REQ-053 GP-API-010/011/012/018) through the tenant-scoped client. A bed is a
 * location whose type is flagged `is_bed`; the document lives at `/locations`.
 */

const LOCATIONS = '/locations';

/** GP-API-011: the beds of a site with `active_plant_count`, `open_task_count` and `next_due_at`. */
export async function listBeds(siteKey: string, status?: BedStatus): Promise<BedListItem[]> {
  const { data } = await tenantClient.get<BedListItem[]>(LOCATIONS, {
    params: { site_key: siteKey, is_bed: true, ...(status ? { bed_status: status } : {}) },
  });
  return data;
}

/** GP-API-012: the head data of the bed view. */
export async function getBedSummary(key: string): Promise<BedSummary> {
  const { data } = await tenantClient.get<BedSummary>(`${LOCATIONS}/${key}/summary`);
  return data;
}

/** GP-API-010: write the soil profile (GP-FR-120/121); an explicit `null` clears it. */
export async function patchSoilProfile(
  key: string,
  soilProfile: SoilProfile | null,
): Promise<BedPatchResult> {
  const { data } = await tenantClient.patch<BedPatchResult>(`${LOCATIONS}/${key}`, {
    soil_profile: soilProfile,
  });
  return data;
}

/**
 * GP-API-010: write the sun and shade class (GP-FR-157) and/or the sun profile - sun window, summer sun
 * hours, leaf-shade flag (GP-FR-158/159) - in ONE request. The server merges the profile keys sent into the
 * stored `site_conditions.sun_profile` and keeps the others (WP 3.9), so only the changed keys go out; an
 * explicit `null` clears the hours. A key the server does not know is a 422 (nothing is silently dropped).
 */
export async function patchSun(
  key: string,
  change: { sunExposure?: SunExposure; sunProfile?: SunProfilePatch },
): Promise<BedPatchResult> {
  const { data } = await tenantClient.patch<BedPatchResult>(`${LOCATIONS}/${key}`, {
    ...(change.sunExposure !== undefined ? { sun_exposure: change.sunExposure } : {}),
    ...(change.sunProfile !== undefined ? { site_conditions: { sun_profile: change.sunProfile } } : {}),
  });
  return data;
}

/** GP-API-018: move the bed through its lifecycle; `retired` needs a `reason` (GP-FR-046). */
export async function changeBedStatus(
  key: string,
  bedStatus: BedStatus,
  reason?: string,
): Promise<BedPatchResult> {
  const { data } = await tenantClient.post<BedPatchResult>(`${LOCATIONS}/${key}/status`, {
    bed_status: bedStatus,
    ...(reason ? { reason } : {}),
  });
  return data;
}
