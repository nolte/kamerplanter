import client from '../client';
import type { WateringEvent, WateringEventCreate, WateringEventWithWarnings, WateringStats } from '../types';

// ── Create ────────────────────────────────────────────────────────────

export async function createWateringEvent(
  payload: WateringEventCreate,
): Promise<WateringEventWithWarnings> {
  const { data } = await client.post<WateringEventWithWarnings>(
    '/watering-events',
    payload,
  );
  return data;
}

// ── List ──────────────────────────────────────────────────────────────

export async function listWateringEvents(
  offset = 0,
  limit = 50,
): Promise<WateringEvent[]> {
  const { data } = await client.get<WateringEvent[]>('/watering-events', {
    params: { offset, limit },
  });
  return data;
}

// ── Queries ───────────────────────────────────────────────────────────

export async function getSlotWateringEvents(
  slotKey: string,
  offset = 0,
  limit = 50,
): Promise<WateringEvent[]> {
  const { data } = await client.get<WateringEvent[]>(
    `/slots/${slotKey}/watering-events`,
    { params: { offset, limit } },
  );
  return data;
}

export async function getLocationWateringEvents(
  locationKey: string,
  offset = 0,
  limit = 50,
): Promise<WateringEvent[]> {
  const { data } = await client.get<WateringEvent[]>(
    `/locations/${locationKey}/watering-events`,
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
