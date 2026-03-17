import client, { tenantClient } from '../client';
import type {
  Site,
  SiteCreate,
  Location,
  LocationCreate,
  LocationTreeNode,
  LocationType,
  LiveStateResponse,
  Sensor,
  SensorCreate,
  Slot,
  SlotCreate,
} from '../types';

// Sites
const SITES = '/sites';

export async function listSites(offset = 0, limit = 50): Promise<Site[]> {
  const { data } = await tenantClient.get<Site[]>(SITES, { params: { offset, limit } });
  return data;
}

export async function getSite(key: string): Promise<Site> {
  const { data } = await tenantClient.get<Site>(`${SITES}/${key}`);
  return data;
}

export async function createSite(payload: SiteCreate): Promise<Site> {
  const { data } = await tenantClient.post<Site>(SITES, payload);
  return data;
}

export async function updateSite(key: string, payload: SiteCreate): Promise<Site> {
  const { data } = await tenantClient.put<Site>(`${SITES}/${key}`, payload);
  return data;
}

export async function deleteSite(key: string): Promise<void> {
  await tenantClient.delete(`${SITES}/${key}`);
}

// Locations
const LOCATIONS = '/locations';

export async function listLocations(siteKey: string): Promise<Location[]> {
  const { data } = await tenantClient.get<Location[]>(LOCATIONS, {
    params: { site_key: siteKey },
  });
  return data;
}

export async function getLocation(key: string): Promise<Location> {
  const { data } = await tenantClient.get<Location>(`${LOCATIONS}/${key}`);
  return data;
}

export async function createLocation(payload: LocationCreate): Promise<Location> {
  const { data } = await tenantClient.post<Location>(LOCATIONS, payload);
  return data;
}

export async function updateLocation(key: string, payload: LocationCreate): Promise<Location> {
  const { data } = await tenantClient.put<Location>(`${LOCATIONS}/${key}`, payload);
  return data;
}

export async function deleteLocation(key: string): Promise<void> {
  await tenantClient.delete(`${LOCATIONS}/${key}`);
}

export async function listLocationChildren(parentKey: string): Promise<Location[]> {
  const { data } = await tenantClient.get<Location[]>(`${LOCATIONS}/${parentKey}/children`);
  return data;
}

export async function getLocationTree(siteKey: string): Promise<LocationTreeNode[]> {
  const { data } = await tenantClient.get<LocationTreeNode[]>(`${SITES}/${siteKey}/location-tree`);
  return data;
}

// Location Types
const LOCATION_TYPES = '/location-types';

export async function listLocationTypes(): Promise<LocationType[]> {
  const { data } = await client.get<LocationType[]>(LOCATION_TYPES);
  return data;
}

// Slots
const SLOTS = '/slots';

export async function listSlots(locationKey: string): Promise<Slot[]> {
  const { data } = await tenantClient.get<Slot[]>(SLOTS, {
    params: { location_key: locationKey },
  });
  return data;
}

export async function getSlot(key: string): Promise<Slot> {
  const { data } = await tenantClient.get<Slot>(`${SLOTS}/${key}`);
  return data;
}

export async function createSlot(payload: SlotCreate): Promise<Slot> {
  const { data } = await tenantClient.post<Slot>(SLOTS, payload);
  return data;
}

export async function updateSlot(key: string, payload: SlotCreate): Promise<Slot> {
  const { data } = await tenantClient.put<Slot>(`${SLOTS}/${key}`, payload);
  return data;
}

export async function deleteSlot(key: string): Promise<void> {
  await tenantClient.delete(`${SLOTS}/${key}`);
}

// ── Site Sensors ────────────────────────────────────────────────────────

export async function getSiteSensors(siteKey: string): Promise<Sensor[]> {
  const { data } = await tenantClient.get<Sensor[]>(`${SITES}/${siteKey}/sensors`);
  return data;
}

export async function createSiteSensor(
  siteKey: string,
  payload: SensorCreate,
): Promise<Sensor> {
  const { data } = await tenantClient.post<Sensor>(
    `${SITES}/${siteKey}/sensors`,
    payload,
  );
  return data;
}

export async function getSiteSensorsLive(
  siteKey: string,
): Promise<LiveStateResponse> {
  const { data } = await tenantClient.get<LiveStateResponse>(
    `${SITES}/${siteKey}/sensors/live`,
  );
  return data;
}

// ── Location Sensors ────────────────────────────────────────────────────

export async function getLocationSensors(
  locationKey: string,
): Promise<Sensor[]> {
  const { data } = await tenantClient.get<Sensor[]>(
    `${LOCATIONS}/${locationKey}/sensors`,
  );
  return data;
}

export async function createLocationSensor(
  locationKey: string,
  payload: SensorCreate,
): Promise<Sensor> {
  const { data } = await tenantClient.post<Sensor>(
    `${LOCATIONS}/${locationKey}/sensors`,
    payload,
  );
  return data;
}

export async function getLocationSensorsLive(
  locationKey: string,
): Promise<LiveStateResponse> {
  const { data } = await tenantClient.get<LiveStateResponse>(
    `${LOCATIONS}/${locationKey}/sensors/live`,
  );
  return data;
}
