import { tenantClient as client } from '../client';
import { CATALOGUE_PAGE_SIZE, fetchAllPages, type OnPage } from '../paginate';
import type {
  PlantInstance,
  PlantInstanceCreate,
  PlantInstancesInPhase,
  RemovePlantRequest,
  RemovedPlantInstance,
  SurvivalStats,
  ValidatePlantingResponse,
} from '../types';

const BASE = '/plant-instances';

/** Server-side narrowing of the plant list (#3015). */
export interface PlantInstanceListFilter {
  /** Only the plants placed at this location; the tenant's other plants are never sent. */
  location_key?: string;
}

export async function listPlantInstances(
  offset = 0,
  limit = 50,
  filter: PlantInstanceListFilter = {},
): Promise<PlantInstance[]> {
  const { data } = await client.get<PlantInstance[]>(BASE, {
    params: { offset, limit, ...(filter.location_key ? { location_key: filter.location_key } : {}) },
  });
  return data;
}

/**
 * Loads every plant instance of the current tenant by paging through the list
 * endpoint until a short page is returned. The single-request wrapper above caps
 * at the backend's ``limit<=200``; callers that build a complete resolution map or
 * a "pick any plant" dropdown must see all instances, so a fixed ``limit=500`` both
 * 422'd (over the cap, #614) and would silently truncate a large tenant. Use this
 * instead of ``listPlantInstances()`` whenever the full set is required.
 */
export async function listAllPlantInstances(
  pageSize = CATALOGUE_PAGE_SIZE,
  onPage?: OnPage<PlantInstance>,
): Promise<PlantInstance[]> {
  return fetchAllPages((offset, limit) => listPlantInstances(offset, limit), pageSize, onPage);
}

/**
 * Every plant placed at one location, paged until a short page (#3015). The location view used to load the whole
 * tenant's plants and filter them in the browser.
 */
export async function listAllPlantInstancesAtLocation(
  locationKey: string,
  pageSize = CATALOGUE_PAGE_SIZE,
): Promise<PlantInstance[]> {
  return fetchAllPages(
    (offset, limit) => listPlantInstances(offset, limit, { location_key: locationKey }),
    pageSize,
  );
}

export async function getPlantInstance(key: string): Promise<PlantInstance> {
  const { data } = await client.get<PlantInstance>(`${BASE}/${key}`);
  return data;
}

export async function createPlantInstance(
  payload: PlantInstanceCreate,
): Promise<PlantInstance> {
  const { data } = await client.post<PlantInstance>(BASE, payload);
  return data;
}

export async function updatePlantInstance(
  key: string,
  payload: Partial<PlantInstanceCreate>,
): Promise<PlantInstance> {
  const { data } = await client.put<PlantInstance>(`${BASE}/${key}`, payload);
  return data;
}

/**
 * End a plant (REQ-003 E5). After a soil-borne loss the answer carries `soil_hazard_follow_up` (#2888 F-20): the
 * offer to take a confirmed pathogen over into the bed, or the clean-system hint at hydroponics. Nothing is written
 * to the bed by this call.
 */
export async function removePlantInstance(
  key: string,
  body?: RemovePlantRequest,
): Promise<RemovedPlantInstance> {
  const { data } = await client.post<RemovedPlantInstance>(`${BASE}/${key}/remove`, body ?? {});
  return data;
}

/**
 * List the current tenant's active plant instances currently in a phase definition
 * (FIX-01 R1/R8). Tenant-scoped via the tenant client; empty list is a valid result.
 */
export async function listPlantInstancesInPhaseDefinition(
  phaseDefinitionKey: string,
): Promise<PlantInstancesInPhase> {
  const { data } = await client.get<PlantInstancesInPhase>(
    `${BASE}/by-phase-definition/${phaseDefinitionKey}`,
  );
  return data;
}

export async function getSurvivalStats(): Promise<SurvivalStats> {
  const { data } = await client.get<SurvivalStats>(`${BASE}/survival-stats`);
  return data;
}

export async function validatePlanting(
  slotKey: string,
  speciesKey: string,
): Promise<ValidatePlantingResponse> {
  const { data } = await client.post<ValidatePlantingResponse>(
    `${BASE}/slots/${slotKey}/validate-planting`,
    { species_key: speciesKey },
  );
  return data;
}

export interface PlantRunRef {
  key: string;
  name: string;
  status: string;
}

export async function getPlantRuns(plantKey: string): Promise<PlantRunRef[]> {
  const { data } = await client.get<PlantRunRef[]>(`${BASE}/${plantKey}/planting-runs`);
  return data;
}
