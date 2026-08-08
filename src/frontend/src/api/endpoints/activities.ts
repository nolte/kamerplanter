import client from '../client';
import { CATALOGUE_PAGE_SIZE, fetchAllPages } from '../paginate';
import type { Activity, ActivityCreate } from '../types';

const BASE = '/activities';

/** Filters the activity catalogue accepts; all optional, all AND-combined. */
export interface ActivityFilters {
  category?: string;
  scope?: 'universal' | 'restricted';
  species?: string;
}

/**
 * Loads one page of the activity catalogue.
 *
 * Sending no `offset`/`limit` does **not** mean "everything": the endpoint uses
 * the shared pagination dependency, so the backend applies its own default of
 * 50. That is how 51 seeded activities became 50 visible ones (#995) — prefer
 * {@link listAllActivities} whenever the whole catalogue is the subject.
 */
export async function listActivities(
  params?: ActivityFilters,
  offset = 0,
  limit = 50,
): Promise<Activity[]> {
  const { data } = await client.get<Activity[]>(BASE, {
    params: { ...params, offset, limit },
  });
  return data;
}

/**
 * Loads the complete activity catalogue by paging until a short page is
 * returned. The list view uses this: its search, sort and pagination all run
 * client-side, so a bounded first page makes the search deny rows that exist.
 */
export async function listAllActivities(
  params?: ActivityFilters,
  pageSize = CATALOGUE_PAGE_SIZE,
): Promise<Activity[]> {
  return fetchAllPages(
    (offset, limit) => listActivities(params, offset, limit),
    pageSize,
  );
}

export async function getActivity(key: string): Promise<Activity> {
  const { data } = await client.get<Activity>(`${BASE}/${key}`);
  return data;
}

export async function createActivity(payload: ActivityCreate): Promise<Activity> {
  const { data } = await client.post<Activity>(BASE, payload);
  return data;
}

export async function updateActivity(key: string, payload: Partial<ActivityCreate>): Promise<Activity> {
  const { data } = await client.put<Activity>(`${BASE}/${key}`, payload);
  return data;
}

export async function deleteActivity(key: string): Promise<void> {
  await client.delete(`${BASE}/${key}`);
}
