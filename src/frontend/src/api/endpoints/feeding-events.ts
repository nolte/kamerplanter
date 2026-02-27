import client from '../client';
import type {
  FeedingEvent,
  FeedingEventCreate,
  RunoffResponse,
} from '../types';

const BASE = '/feeding-events';

// ── CRUD ──────────────────────────────────────────────────────────────

export async function listFeedingEvents(
  offset = 0,
  limit = 50,
): Promise<FeedingEvent[]> {
  const { data } = await client.get<FeedingEvent[]>(BASE, {
    params: { offset, limit },
  });
  return data;
}

export async function getFeedingEvent(key: string): Promise<FeedingEvent> {
  const { data } = await client.get<FeedingEvent>(`${BASE}/${key}`);
  return data;
}

export async function createFeedingEvent(
  payload: FeedingEventCreate,
): Promise<FeedingEvent> {
  const { data } = await client.post<FeedingEvent>(BASE, payload);
  return data;
}

export async function updateFeedingEvent(
  key: string,
  payload: Record<string, unknown>,
): Promise<FeedingEvent> {
  const { data } = await client.put<FeedingEvent>(`${BASE}/${key}`, payload);
  return data;
}

export async function deleteFeedingEvent(key: string): Promise<void> {
  await client.delete(`${BASE}/${key}`);
}

// ── Queries ───────────────────────────────────────────────────────────

export async function getPlantFeedingHistory(
  plantKey: string,
  offset = 0,
  limit = 50,
): Promise<FeedingEvent[]> {
  const { data } = await client.get<FeedingEvent[]>(
    `${BASE}/plant/${plantKey}`,
    { params: { offset, limit } },
  );
  return data;
}

export async function analyzeRunoff(key: string): Promise<RunoffResponse> {
  const { data } = await client.get<RunoffResponse>(`${BASE}/${key}/runoff`);
  return data;
}
