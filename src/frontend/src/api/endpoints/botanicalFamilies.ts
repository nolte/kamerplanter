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
