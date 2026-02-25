import client from '../client';
import type {
  PlantInstance,
  PlantInstanceCreate,
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

export async function removePlantInstance(key: string): Promise<PlantInstance> {
  const { data } = await client.post<PlantInstance>(`${BASE}/${key}/remove`);
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
