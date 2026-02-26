import client from '../client';
import type {
  Fertilizer,
  FertilizerCreate,
  FertilizerStock,
  FertilizerStockCreate,
  FertilizerUpdate,
  Incompatibility,
} from '../types';

const BASE = '/fertilizers';

// ── Fertilizer CRUD ───────────────────────────────────────────────────

export async function fetchFertilizers(
  offset = 0,
  limit = 50,
  filters?: Record<string, string>,
): Promise<Fertilizer[]> {
  const params: Record<string, string | number> = { offset, limit };
  if (filters) {
    for (const [key, value] of Object.entries(filters)) {
      params[key] = value;
    }
  }
  const { data } = await client.get<Fertilizer[]>(BASE, { params });
  return data;
}

export async function fetchFertilizer(key: string): Promise<Fertilizer> {
  const { data } = await client.get<Fertilizer>(`${BASE}/${key}`);
  return data;
}

export async function createFertilizer(
  payload: FertilizerCreate,
): Promise<Fertilizer> {
  const { data } = await client.post<Fertilizer>(BASE, payload);
  return data;
}

export async function updateFertilizer(
  key: string,
  payload: FertilizerUpdate,
): Promise<Fertilizer> {
  const { data } = await client.put<Fertilizer>(`${BASE}/${key}`, payload);
  return data;
}

export async function deleteFertilizer(key: string): Promise<void> {
  await client.delete(`${BASE}/${key}`);
}

// ── Stocks ────────────────────────────────────────────────────────────

export async function fetchFertilizerStocks(
  key: string,
): Promise<FertilizerStock[]> {
  const { data } = await client.get<FertilizerStock[]>(
    `${BASE}/${key}/stocks`,
  );
  return data;
}

export async function createFertilizerStock(
  key: string,
  payload: FertilizerStockCreate,
): Promise<FertilizerStock> {
  const { data } = await client.post<FertilizerStock>(
    `${BASE}/${key}/stocks`,
    payload,
  );
  return data;
}

export async function deleteFertilizerStock(
  key: string,
  stockKey: string,
): Promise<void> {
  await client.delete(`${BASE}/${key}/stocks/${stockKey}`);
}

// ── Incompatibilities ─────────────────────────────────────────────────

export async function fetchIncompatibilities(
  key: string,
): Promise<Incompatibility[]> {
  const { data } = await client.get<Incompatibility[]>(
    `${BASE}/${key}/incompatibilities`,
  );
  return data;
}
