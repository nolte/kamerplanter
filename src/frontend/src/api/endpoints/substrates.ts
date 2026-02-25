import client from '../client';
import type {
  Substrate,
  SubstrateCreate,
  Batch,
  BatchCreate,
  ReusabilityResponse,
} from '../types';

const BASE = '/substrates';

export async function listSubstrates(offset = 0, limit = 50): Promise<Substrate[]> {
  const { data } = await client.get<Substrate[]>(BASE, { params: { offset, limit } });
  return data;
}

export async function getSubstrate(key: string): Promise<Substrate> {
  const { data } = await client.get<Substrate>(`${BASE}/${key}`);
  return data;
}

export async function createSubstrate(payload: SubstrateCreate): Promise<Substrate> {
  const { data } = await client.post<Substrate>(BASE, payload);
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

export async function checkReusability(batchKey: string): Promise<ReusabilityResponse> {
  const { data } = await client.post<ReusabilityResponse>(
    `${BASE}/batches/${batchKey}/check-reusability`,
  );
  return data;
}
