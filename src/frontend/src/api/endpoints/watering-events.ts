import { tenantClient as client } from '../client';
import type { VolumeSuggestion, WateringEvent, WateringEventCreate, WateringEventWithWarnings, WateringStats } from '../types';

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

// ── Get ───────────────────────────────────────────────────────────────

export async function getWateringEvent(key: string): Promise<WateringEvent> {
  const { data } = await client.get<WateringEvent>(`/watering-events/${key}`);
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

export async function getPlantWateringEvents(
  plantKey: string,
  offset = 0,
  limit = 50,
): Promise<WateringEvent[]> {
  const { data } = await client.get<WateringEvent[]>(
    `/plant-instances/${plantKey}/watering-events`,
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

// ── Volume Suggestion ────────────────────────────────────────────────

export async function getWateringVolumeSuggestion(
  plantKey: string,
  referenceDate?: string,
  hemisphere: string = 'north',
): Promise<VolumeSuggestion> {
  const { data } = await client.get<VolumeSuggestion>(
    `/plant-instances/${plantKey}/watering-volume-suggestion`,
    { params: { reference_date: referenceDate, hemisphere } },
  );
  return data;
}
