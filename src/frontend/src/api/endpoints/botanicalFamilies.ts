import client from '../client';
import { CATALOGUE_PAGE_SIZE, fetchAllPages } from '../paginate';
import type { BotanicalFamily, BotanicalFamilyCreate, Species } from '../types';

const BASE = '/botanical-families';

export async function listBotanicalFamilies(
  offset = 0,
  limit = 50,
): Promise<BotanicalFamily[]> {
  const { data } = await client.get<BotanicalFamily[]>(BASE, {
    params: { offset, limit },
  });
  return data;
}

/**
 * Loads the complete botanical-family catalogue by paging through the list
 * endpoint until a short page is returned. The single-request wrapper above caps
 * at the backend's `limit<=200`, which would silently truncate a large catalogue
 * (the "Von Familie" dropdown must show every family, #550), so callers that need
 * the whole set use this instead of `listBotanicalFamilies()`.
 *
 * The list view is one of those callers, and was not: 57 families are seeded
 * against a single-page default of 50, so seven of them never reached the
 * browser and the client-side search reported them as non-existent (#995).
 */
export async function listAllBotanicalFamilies(
  pageSize = CATALOGUE_PAGE_SIZE,
): Promise<BotanicalFamily[]> {
  return fetchAllPages(listBotanicalFamilies, pageSize);
}

export async function getBotanicalFamily(key: string): Promise<BotanicalFamily> {
  const { data } = await client.get<BotanicalFamily>(`${BASE}/${key}`);
  return data;
}

export async function createBotanicalFamily(
  payload: BotanicalFamilyCreate,
): Promise<BotanicalFamily> {
  const { data } = await client.post<BotanicalFamily>(BASE, payload);
  return data;
}

export async function updateBotanicalFamily(
  key: string,
  payload: BotanicalFamilyCreate,
): Promise<BotanicalFamily> {
  const { data } = await client.put<BotanicalFamily>(`${BASE}/${key}`, payload);
  return data;
}

export async function deleteBotanicalFamily(key: string): Promise<void> {
  await client.delete(`${BASE}/${key}`);
}

export async function listSpeciesByFamily(familyKey: string): Promise<Species[]> {
  const { data } = await client.get<Species[]>(`${BASE}/${familyKey}/species`);
  return data;
}
