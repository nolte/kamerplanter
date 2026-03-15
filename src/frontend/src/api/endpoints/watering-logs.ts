import client from '../client';
import type {
  WateringLog,
  WateringLogCreate,
  WateringLogUpdate,
  RunoffResponse,
  WateringStats,
} from '../types';

const BASE = '/watering-logs';

// ── CRUD ──────────────────────────────────────────────────────────────

export async function listWateringLogs(
  offset = 0,
  limit = 50,
): Promise<WateringLog[]> {
  const { data } = await client.get<WateringLog[]>(BASE, {
    params: { offset, limit },
  });
  return data;
}

export async function getWateringLog(key: string): Promise<WateringLog> {
  const { data } = await client.get<WateringLog>(`${BASE}/${key}`);
  return data;
}

export async function createWateringLog(
  payload: WateringLogCreate,
): Promise<WateringLog> {
  const { data } = await client.post<WateringLog>(BASE, payload);
  return data;
}

export async function updateWateringLog(
  key: string,
  payload: WateringLogUpdate,
): Promise<WateringLog> {
  const { data } = await client.put<WateringLog>(`${BASE}/${key}`, payload);
  return data;
}

export async function deleteWateringLog(key: string): Promise<void> {
  await client.delete(`${BASE}/${key}`);
}

// ── Queries ───────────────────────────────────────────────────────────

export async function getPlantWateringHistory(
  plantKey: string,
  offset = 0,
  limit = 50,
): Promise<WateringLog[]> {
  const { data } = await client.get<WateringLog[]>(
    `${BASE}/plant/${plantKey}`,
    { params: { offset, limit } },
  );
  return data;
}

export async function analyzeRunoff(key: string): Promise<RunoffResponse> {
  const { data } = await client.get<RunoffResponse>(`${BASE}/${key}/runoff`);
  return data;
}

export async function getSlotWateringLogs(
  slotKey: string,
  offset = 0,
  limit = 50,
): Promise<WateringLog[]> {
  const { data } = await client.get<WateringLog[]>(
    `/slots/${slotKey}/watering-logs`,
    { params: { offset, limit } },
  );
  return data;
}

export async function getLocationWateringLogs(
  locationKey: string,
  offset = 0,
  limit = 50,
): Promise<WateringLog[]> {
  const { data } = await client.get<WateringLog[]>(
    `/locations/${locationKey}/watering-logs`,
    { params: { offset, limit } },
  );
  return data;
}

export async function getLocationWateringStats(
  locationKey: string,
): Promise<WateringStats> {
  const { data } = await client.get<WateringStats>(
    `/locations/${locationKey}/watering-stats`,
  );
  return data;
}
