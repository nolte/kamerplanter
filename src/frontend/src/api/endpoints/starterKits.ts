import client from '../client';
import type { StarterKit } from '../types';

export async function listKits(difficulty?: string): Promise<StarterKit[]> {
  const params: Record<string, string> = {};
  if (difficulty) params.difficulty = difficulty;
  const { data } = await client.get<StarterKit[]>('/starter-kits', { params });
  return data;
}

export async function getKit(kitId: string): Promise<StarterKit> {
  const { data } = await client.get<StarterKit>(`/starter-kits/${kitId}`);
  return data;
}

export async function applyKit(
  kitId: string,
  siteName: string,
  plantCount: number,
): Promise<Record<string, unknown>> {
  const { data } = await client.post(`/starter-kits/${kitId}/apply`, {
    site_name: siteName,
    plant_count: plantCount,
  });
  return data as Record<string, unknown>;
}
