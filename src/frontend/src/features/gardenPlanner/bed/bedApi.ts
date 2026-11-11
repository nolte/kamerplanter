import { tenantClient } from '@/api/client';
import type { BedStatus, SunExposure } from '../model/types';
import type {
  BedListItem,
  BedPatchResult,
  BedSummary,
  SiteConditionsPatch,
  SoilProfile,
  SunProfilePatch,
  TentRulesPatch,
} from './types';
import type { SoilAnalysesResponse, SoilAnalysisBody } from './soilAnalysisTypes';

/**
 * REST access to beds (REQ-053 GP-API-010/011/012/018) through the tenant-scoped client. A bed is a
 * location whose type is flagged `is_bed`; the document lives at `/locations`.
 */

const LOCATIONS = '/locations';

/**
 * GP-API-011 with `supports_layout` (WP 10.8, GP-FR-183, G-W10 e): every location of a site that can carry a slot
 * layout - the beds and, indoors, tents and shelves (the "Pflanzplätze") - with the same counters as `listBeds`.
 * A bed is still a bed: every `is_bed` type supports a layout, so a garden lists the same beds as before.
 */
export async function listLayoutLocations(siteKey: string): Promise<BedListItem[]> {
  const { data } = await tenantClient.get<BedListItem[]>(LOCATIONS, {
    params: { site_key: siteKey, supports_layout: true },
  });
  return data;
}

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

/**
 * GP-API-010: write the site conditions beyond the sun - microclimate, wind, slope, aspect, access sides
 * (GP-FR-162/163/168) - in ONE request. The server merges the keys sent into the stored `site_conditions`
 * (and moves `frost_exposed` with a changed frost risk, #2512), so only the changed keys go out.
 */
export async function patchSiteConditions(key: string, patch: SiteConditionsPatch): Promise<BedPatchResult> {
  const { data } = await tenantClient.patch<BedPatchResult>(`${LOCATIONS}/${key}`, { site_conditions: patch });
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

/**
 * GP-FR-137: switch the crop-rotation check of one bed - `rotation_enabled` (`null` = default of the bed type) and/or
 * `rotation_exempt` (permanent crop). Only the keys sent are changed. Both `true` is a 422
 * `patch.rotation_exempt_and_enabled`; the caller shows it.
 */
export async function patchRotationSwitch(
  key: string,
  change: { rotationEnabled?: boolean | null; rotationExempt?: boolean },
): Promise<BedPatchResult> {
  const { data } = await tenantClient.patch<BedPatchResult>(`${LOCATIONS}/${key}`, {
    ...(change.rotationEnabled !== undefined ? { rotation_enabled: change.rotationEnabled } : {}),
    ...(change.rotationExempt !== undefined ? { rotation_exempt: change.rotationExempt } : {}),
  });
  return data;
}

/**
 * W-016 (WP 10.11): the location's own neighbourhood factor and its lighting. Only the keys sent are changed; the
 * lighting is replaced whole, and `null` clears either. A value the server refuses is a 422; the caller shows it.
 */
export async function patchTentRules(key: string, patch: TentRulesPatch): Promise<BedPatchResult> {
  const { data } = await tenantClient.patch<BedPatchResult>(`${LOCATIONS}/${key}`, patch);
  return data;
}

/**
 * GP-FR-122: the bed's soil analyses as series per parameter and method, the marked method changes and the
 * "liming likely" hint of the current profile. Values of different methods are never merged or converted.
 */
export async function getSoilAnalyses(key: string, signal?: AbortSignal): Promise<SoilAnalysesResponse> {
  const { data } = await tenantClient.get<SoilAnalysesResponse>(`/locations/${key}/soil-analyses`, { signal });
  return data;
}

/**
 * GP-FR-122 / GP-API-033: record a soil analysis as a care event. The server writes the newest pH, EC, humus and
 * lime values with their method into the soil profile in the same transaction (never an older analysis).
 */
export async function recordSoilAnalysis(body: SoilAnalysisBody): Promise<{ key: string }> {
  const { data } = await tenantClient.post<{ key: string }>('/care-events', body);
  return data;
}
