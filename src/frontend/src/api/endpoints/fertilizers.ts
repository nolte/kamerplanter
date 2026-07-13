import { tenantClient as client } from '../client';
import type {
  Fertilizer,
  FertilizerCreate,
  FertilizerStock,
  FertilizerStockCreate,
  FertilizerUpdate,
  Incompatibility,
  NutrientPlanUsage,
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

/**
 * Loads the complete fertilizer catalogue by paging through the list endpoint
 * until a short page is returned. The single-request wrapper above caps at the
 * backend's ``limit<=200``; a fixed ``limit=500`` both 422'd (over the cap, #614)
 * and would silently truncate a large catalogue. Callers that populate a
 * "pick any fertilizer" selector must see every product, so use this instead.
 */
export async function fetchAllFertilizers(
  pageSize = 200,
  filters?: Record<string, string>,
): Promise<Fertilizer[]> {
  const all: Fertilizer[] = [];
  let offset = 0;
  // Guard against an unbounded loop if the backend ever ignores the offset.
  for (let page = 0; page < 1000; page += 1) {
    const batch = await fetchFertilizers(offset, pageSize, filters);
    all.push(...batch);
    if (batch.length < pageSize) break;
    offset += pageSize;
  }
  return all;
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

// ── Nutrient plan usage ──────────────────────────────────────────────

export async function fetchNutrientPlanUsage(
  key: string,
): Promise<NutrientPlanUsage[]> {
  const { data } = await client.get<NutrientPlanUsage[]>(
    `${BASE}/${key}/nutrient-plans`,
  );
  return data;
}
