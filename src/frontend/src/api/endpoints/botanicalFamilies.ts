import client from '../client';
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
 */
export async function listAllBotanicalFamilies(
  pageSize = 200,
): Promise<BotanicalFamily[]> {
  const all: BotanicalFamily[] = [];
  let offset = 0;
  // Guard against an unbounded loop if the backend ever ignores the offset.
  for (let page = 0; page < 1000; page += 1) {
    const batch = await listBotanicalFamilies(offset, pageSize);
    all.push(...batch);
    if (batch.length < pageSize) break;
    offset += pageSize;
  }
  return all;
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
