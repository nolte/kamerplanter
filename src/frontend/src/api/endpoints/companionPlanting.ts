import client from '../client';
import type {
  CompatibleSpecies,
  IncompatibleSpecies,
  CompatibilitySet,
  IncompatibilitySet,
} from '../types';

const BASE = '/companion-planting';

export async function getCompatibleSpecies(speciesKey: string): Promise<CompatibleSpecies[]> {
  const { data } = await client.get<CompatibleSpecies[]>(
    `${BASE}/species/${speciesKey}/compatible`,
  );
  return data;
}

export async function getIncompatibleSpecies(
  speciesKey: string,
): Promise<IncompatibleSpecies[]> {
  const { data } = await client.get<IncompatibleSpecies[]>(
    `${BASE}/species/${speciesKey}/incompatible`,
  );
  return data;
}

export async function setCompatible(payload: CompatibilitySet): Promise<void> {
  await client.post(`${BASE}/compatible`, payload);
}

export async function setIncompatible(payload: IncompatibilitySet): Promise<void> {
  await client.post(`${BASE}/incompatible`, payload);
}
