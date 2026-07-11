import { tenantClient as client } from '../client';
import type {
  DryingProgress,
  DryingProgressCreate,
  MoldAlert,
  PostHarvestBatch,
  PostHarvestBatchDetail,
  PostHarvestStage,
  StartDryingRequest,
  StorageObservation,
  StorageObservationCreate,
} from '../types';

const BASE = '/post-harvest';

// -- Batches -------------------------------------------------------------

export async function getBatches(
  offset = 0,
  limit = 50,
): Promise<PostHarvestBatch[]> {
  const { data } = await client.get<PostHarvestBatch[]>(BASE, {
    params: { offset, limit },
  });
  return data;
}

export async function getBatchesForHarvest(
  harvestBatchKey: string,
): Promise<PostHarvestBatch[]> {
  const { data } = await client.get<PostHarvestBatch[]>(BASE, {
    params: { harvest_batch: harvestBatchKey },
  });
  return data;
}

export async function startDrying(
  payload: StartDryingRequest,
): Promise<PostHarvestBatch> {
  const { data } = await client.post<PostHarvestBatch>(
    `${BASE}/start-drying`,
    payload,
  );
  return data;
}

export async function getBatch(key: string): Promise<PostHarvestBatchDetail> {
  const { data } = await client.get<PostHarvestBatchDetail>(`${BASE}/${key}`);
  return data;
}

export async function advanceStage(
  key: string,
  targetStage: PostHarvestStage,
): Promise<PostHarvestBatch> {
  const { data } = await client.post<PostHarvestBatch>(`${BASE}/${key}/advance`, {
    target_stage: targetStage,
  });
  return data;
}

export async function deleteBatch(key: string): Promise<void> {
  await client.delete(`${BASE}/${key}`);
}

// -- Drying progress -----------------------------------------------------

export async function recordDryingProgress(
  key: string,
  payload: DryingProgressCreate,
): Promise<DryingProgress> {
  const { data } = await client.post<DryingProgress>(
    `${BASE}/${key}/drying-progress`,
    payload,
  );
  return data;
}

export async function getDryingProgress(
  key: string,
): Promise<DryingProgress[]> {
  const { data } = await client.get<DryingProgress[]>(
    `${BASE}/${key}/drying-progress`,
  );
  return data;
}

// -- Storage observations ------------------------------------------------

export async function recordObservation(
  key: string,
  payload: StorageObservationCreate,
): Promise<StorageObservation> {
  const { data } = await client.post<StorageObservation>(
    `${BASE}/${key}/observations`,
    payload,
  );
  return data;
}

export async function getObservations(
  key: string,
): Promise<StorageObservation[]> {
  const { data } = await client.get<StorageObservation[]>(
    `${BASE}/${key}/observations`,
  );
  return data;
}

// -- Mold alerts ---------------------------------------------------------

export async function getMoldAlerts(key: string): Promise<MoldAlert[]> {
  const { data } = await client.get<MoldAlert[]>(`${BASE}/${key}/mold-alerts`);
  return data;
}
