import { tenantClient } from '@/api/client';
import type {
  IrrigationZone,
  WateringRoundRequest,
  WateringRoundResult,
  ZoneCreate,
  ZoneLocationsResult,
  ZoneStatus,
  ZoneUpdate,
} from './zoneTypes';

/**
 * REST access to the irrigation zones of a site (REQ-053 GP-API-050..053) through the tenant-scoped client.
 * Reads need a membership, writes the `grower` role, deleting the `lead` role (the backend decides).
 */

export async function listZones(siteKey: string, signal?: AbortSignal): Promise<IrrigationZone[]> {
  const { data } = await tenantClient.get<IrrigationZone[]>(`/sites/${siteKey}/irrigation-zones`, { signal });
  return data;
}

export async function createZone(siteKey: string, body: ZoneCreate): Promise<IrrigationZone> {
  const { data } = await tenantClient.post<IrrigationZone>(`/sites/${siteKey}/irrigation-zones`, body);
  return data;
}

export async function updateZone(zoneKey: string, body: ZoneUpdate): Promise<IrrigationZone> {
  const { data } = await tenantClient.patch<IrrigationZone>(`/irrigation-zones/${zoneKey}`, body);
  return data;
}

export async function deleteZone(zoneKey: string): Promise<void> {
  await tenantClient.delete(`/irrigation-zones/${zoneKey}`);
}

/** Replaces the beds of the zone; a bed that was in another zone moves (`moved_from`). */
export async function replaceZoneLocations(
  zoneKey: string,
  locationKeys: readonly string[],
): Promise<ZoneLocationsResult> {
  const { data } = await tenantClient.put<ZoneLocationsResult>(`/irrigation-zones/${zoneKey}/locations`, {
    location_keys: locationKeys,
  });
  return data;
}

export async function getZoneStatus(zoneKey: string, signal?: AbortSignal): Promise<ZoneStatus> {
  const { data } = await tenantClient.get<ZoneStatus>(`/irrigation-zones/${zoneKey}/status`, { signal });
  return data;
}

export async function logZoneWatering(
  zoneKey: string,
  body: WateringRoundRequest,
): Promise<WateringRoundResult> {
  const { data } = await tenantClient.post<WateringRoundResult>(`/irrigation-zones/${zoneKey}/log-watering`, body);
  return data;
}
