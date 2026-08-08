import client from '../client';
import { CATALOGUE_PAGE_SIZE, fetchAllPages } from '../paginate';
import type {
  Substrate,
  SubstrateCreate,
  SubstrateMixRequest,
  Batch,
  BatchCreate,
  ReusabilityResponse,
} from '../types';

const BASE = '/substrates';

export async function listSubstrates(offset = 0, limit = 50): Promise<Substrate[]> {
  const { data } = await client.get<Substrate[]>(BASE, { params: { offset, limit } });
  return data;
}

/**
 * Loads the complete substrate catalogue by paging until a short page is
 * returned. The list view uses this: its search, sort and pagination all run
 * client-side, so a bounded first page makes the search deny substrates that
 * exist (#995).
 */
export async function listAllSubstrates(
  pageSize = CATALOGUE_PAGE_SIZE,
): Promise<Substrate[]> {
  return fetchAllPages(listSubstrates, pageSize);
}

export async function getSubstrate(key: string): Promise<Substrate> {
  const { data } = await client.get<Substrate>(`${BASE}/${key}`);
  return data;
}

export async function createSubstrate(payload: SubstrateCreate): Promise<Substrate> {
  const { data } = await client.post<Substrate>(BASE, payload);
  return data;
}

export async function updateSubstrate(key: string, payload: SubstrateCreate): Promise<Substrate> {
  const { data } = await client.put<Substrate>(`${BASE}/${key}`, payload);
  return data;
}

export async function deleteSubstrate(key: string): Promise<void> {
  await client.delete(`${BASE}/${key}`);
}

export async function listBatches(substrateKey: string): Promise<Batch[]> {
  const { data } = await client.get<Batch[]>(`${BASE}/${substrateKey}/batches`);
  return data;
}

export async function getBatch(key: string): Promise<Batch> {
  const { data } = await client.get<Batch>(`${BASE}/batches/${key}`);
  return data;
}

export async function createBatch(payload: BatchCreate): Promise<Batch> {
  const { data } = await client.post<Batch>(`${BASE}/batches`, payload);
  return data;
}

export async function updateBatch(key: string, payload: BatchCreate): Promise<Batch> {
  const { data } = await client.put<Batch>(`${BASE}/batches/${key}`, payload);
  return data;
}

export async function deleteBatch(key: string): Promise<void> {
  await client.delete(`${BASE}/batches/${key}`);
}

export async function checkReusability(batchKey: string): Promise<ReusabilityResponse> {
  const { data } = await client.post<ReusabilityResponse>(
    `${BASE}/batches/${batchKey}/check-reusability`,
  );
  return data;
}

export async function createSubstrateMix(payload: SubstrateMixRequest): Promise<Substrate> {
  const { data } = await client.post<Substrate>(`${BASE}/mix`, payload);
  return data;
}

export async function previewSubstrateMix(payload: SubstrateMixRequest): Promise<Substrate> {
  const { data } = await client.post<Substrate>(`${BASE}/preview-mix`, payload);
  return data;
}
