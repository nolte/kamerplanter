import client from '../client';
import type {
  BatchCreatePlantsResponse,
  BatchRemoveRequest,
  BatchRemoveResponse,
  BatchTransitionRequest,
  BatchTransitionResponse,
  PlantInRun,
  PlantingRun,
  PlantingRunCreate,
  PlantingRunEntry,
  PlantingRunEntryCreate,
  PlantingRunUpdate,
} from '../types';

const BASE = '/planting-runs';

// ── Run CRUD ──────────────────────────────────────────────────────────

export async function listPlantingRuns(
  offset = 0,
  limit = 50,
  status?: string,
  runType?: string,
): Promise<PlantingRun[]> {
  const params: Record<string, string | number> = { offset, limit };
  if (status) params.status = status;
  if (runType) params.run_type = runType;
  const { data } = await client.get<PlantingRun[]>(BASE, { params });
  return data;
}

export async function getPlantingRun(key: string): Promise<PlantingRun> {
  const { data } = await client.get<PlantingRun>(`${BASE}/${key}`);
  return data;
}

export async function createPlantingRun(
  payload: PlantingRunCreate,
): Promise<PlantingRun> {
  const { data } = await client.post<PlantingRun>(BASE, payload);
  return data;
}

export async function updatePlantingRun(
  key: string,
  payload: PlantingRunUpdate,
): Promise<PlantingRun> {
  const { data } = await client.put<PlantingRun>(`${BASE}/${key}`, payload);
  return data;
}

export async function deletePlantingRun(key: string): Promise<void> {
  await client.delete(`${BASE}/${key}`);
}

// ── Entry management ──────────────────────────────────────────────────

export async function listEntries(
  runKey: string,
): Promise<PlantingRunEntry[]> {
  const { data } = await client.get<PlantingRunEntry[]>(
    `${BASE}/${runKey}/entries`,
  );
  return data;
}

export async function addEntry(
  runKey: string,
  payload: PlantingRunEntryCreate,
): Promise<PlantingRunEntry> {
  const { data } = await client.post<PlantingRunEntry>(
    `${BASE}/${runKey}/entries`,
    payload,
  );
  return data;
}

export async function updateEntry(
  runKey: string,
  entryKey: string,
  payload: Partial<PlantingRunEntryCreate>,
): Promise<PlantingRunEntry> {
  const { data } = await client.put<PlantingRunEntry>(
    `${BASE}/${runKey}/entries/${entryKey}`,
    payload,
  );
  return data;
}

export async function deleteEntry(
  runKey: string,
  entryKey: string,
): Promise<void> {
  await client.delete(`${BASE}/${runKey}/entries/${entryKey}`);
}

// ── Batch operations ──────────────────────────────────────────────────

export async function batchCreatePlants(
  runKey: string,
): Promise<BatchCreatePlantsResponse> {
  const { data } = await client.post<BatchCreatePlantsResponse>(
    `${BASE}/${runKey}/create-plants`,
  );
  return data;
}

export async function batchTransition(
  runKey: string,
  payload: BatchTransitionRequest,
): Promise<BatchTransitionResponse> {
  const { data } = await client.post<BatchTransitionResponse>(
    `${BASE}/${runKey}/batch-transition`,
    payload,
  );
  return data;
}

export async function batchRemove(
  runKey: string,
  payload?: BatchRemoveRequest,
): Promise<BatchRemoveResponse> {
  const { data } = await client.post<BatchRemoveResponse>(
    `${BASE}/${runKey}/batch-remove`,
    payload ?? { reason: 'batch_remove' },
  );
  return data;
}

// ── Plant management ──────────────────────────────────────────────────

export async function listRunPlants(
  runKey: string,
  includeDetached = false,
): Promise<PlantInRun[]> {
  const { data } = await client.get<PlantInRun[]>(
    `${BASE}/${runKey}/plants`,
    { params: { include_detached: includeDetached } },
  );
  return data;
}

export async function detachPlant(
  runKey: string,
  plantKey: string,
  reason: string,
): Promise<void> {
  await client.post(`${BASE}/${runKey}/plants/${plantKey}/detach`, { reason });
}
