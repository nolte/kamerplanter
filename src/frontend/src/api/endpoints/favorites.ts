import { tenantClient as client } from '../client';
import type { FavoriteEntry, NutrientPlanMatch } from '../types';

const BASE = '/favorites';

export async function listFavorites(type?: string): Promise<FavoriteEntry[]> {
  const { data } = await client.get<FavoriteEntry[]>(BASE, {
    params: type ? { type } : undefined,
  });
  return data;
}

export async function addFavorite(
  targetKey: string,
  source = 'manual',
): Promise<FavoriteEntry> {
  const { data } = await client.post<FavoriteEntry>(BASE, {
    target_key: targetKey,
    source,
  });
  return data;
}

export async function removeFavorite(targetKey: string): Promise<void> {
  await client.delete(`${BASE}/${targetKey}`);
}

export async function getMatchingNutrientPlans(
  speciesKeys: string[],
): Promise<NutrientPlanMatch[]> {
  const { data } = await client.get<NutrientPlanMatch[]>(
    `${BASE}/nutrient-plans/matching`,
    { params: { species_keys: speciesKeys.join(',') } },
  );
  return data;
}
