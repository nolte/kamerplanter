import { tenantClient as client } from '../client';
import type {
  PlantInstance,
  PlantInstanceCreate,
  PlantInstancesInPhase,
  RemovePlantRequest,
  SurvivalStats,
  ValidatePlantingResponse,
} from '../types';

const BASE = '/plant-instances';

export async function listPlantInstances(
  offset = 0,
  limit = 50,
): Promise<PlantInstance[]> {
  const { data } = await client.get<PlantInstance[]>(BASE, {
    params: { offset, limit },
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
  pageSize = 200,
): Promise<PlantInstance[]> {
  const all: PlantInstance[] = [];
  let offset = 0;
  // Guard against an unbounded loop if the backend ever ignores the offset.
  for (let page = 0; page < 1000; page += 1) {
    const batch = await listPlantInstances(offset, pageSize);
    all.push(...batch);
    if (batch.length < pageSize) break;
    offset += pageSize;
  }
  return all;
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

export async function removePlantInstance(
  key: string,
  body?: RemovePlantRequest,
): Promise<PlantInstance> {
  const { data } = await client.post<PlantInstance>(`${BASE}/${key}/remove`, body ?? {});
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
