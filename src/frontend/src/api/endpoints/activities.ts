import client from '../client';
import type { Activity, ActivityCreate } from '../types';

const BASE = '/activities';

export async function listActivities(params?: { category?: string; scope?: 'universal' | 'restricted'; species?: string }): Promise<Activity[]> {
  const { data } = await client.get<Activity[]>(BASE, { params });
  return data;
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
