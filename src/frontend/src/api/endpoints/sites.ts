import client from '../client';
import type {
  Site,
  SiteCreate,
  Location,
  LocationCreate,
  LocationTreeNode,
  LocationType,
  Slot,
  SlotCreate,
} from '../types';

// Sites
const SITES = '/sites';

export async function listSites(offset = 0, limit = 50): Promise<Site[]> {
  const { data } = await client.get<Site[]>(SITES, { params: { offset, limit } });
  return data;
}

export async function getSite(key: string): Promise<Site> {
  const { data } = await client.get<Site>(`${SITES}/${key}`);
  return data;
}

export async function createSite(payload: SiteCreate): Promise<Site> {
  const { data } = await client.post<Site>(SITES, payload);
  return data;
}

export async function updateSite(key: string, payload: SiteCreate): Promise<Site> {
  const { data } = await client.put<Site>(`${SITES}/${key}`, payload);
  return data;
}

export async function deleteSite(key: string): Promise<void> {
  await client.delete(`${SITES}/${key}`);
}

// Locations
const LOCATIONS = '/locations';

export async function listLocations(siteKey: string): Promise<Location[]> {
  const { data } = await client.get<Location[]>(LOCATIONS, {
    params: { site_key: siteKey },
  });
  return data;
}

export async function getLocation(key: string): Promise<Location> {
  const { data } = await client.get<Location>(`${LOCATIONS}/${key}`);
  return data;
}

export async function createLocation(payload: LocationCreate): Promise<Location> {
  const { data } = await client.post<Location>(LOCATIONS, payload);
  return data;
}

export async function updateLocation(key: string, payload: LocationCreate): Promise<Location> {
  const { data } = await client.put<Location>(`${LOCATIONS}/${key}`, payload);
  return data;
}

export async function deleteLocation(key: string): Promise<void> {
  await client.delete(`${LOCATIONS}/${key}`);
}

export async function listLocationChildren(parentKey: string): Promise<Location[]> {
  const { data } = await client.get<Location[]>(`${LOCATIONS}/${parentKey}/children`);
  return data;
}

export async function getLocationTree(siteKey: string): Promise<LocationTreeNode[]> {
  const { data } = await client.get<LocationTreeNode[]>(`${SITES}/${siteKey}/location-tree`);
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
  const { data } = await client.get<Slot[]>(SLOTS, {
    params: { location_key: locationKey },
  });
  return data;
}

export async function getSlot(key: string): Promise<Slot> {
  const { data } = await client.get<Slot>(`${SLOTS}/${key}`);
  return data;
}

export async function createSlot(payload: SlotCreate): Promise<Slot> {
  const { data } = await client.post<Slot>(SLOTS, payload);
  return data;
}

export async function updateSlot(key: string, payload: SlotCreate): Promise<Slot> {
  const { data } = await client.put<Slot>(`${SLOTS}/${key}`, payload);
  return data;
}

export async function deleteSlot(key: string): Promise<void> {
  await client.delete(`${SLOTS}/${key}`);
}
