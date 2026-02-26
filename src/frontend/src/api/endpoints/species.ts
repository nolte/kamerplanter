import client from '../client';
import type {
  Species,
  SpeciesCreate,
  PaginatedResponse,
  Cultivar,
  CultivarCreate,
} from '../types';

const BASE = '/species';

export async function listSpecies(
  offset = 0,
  limit = 50,
): Promise<PaginatedResponse<Species>> {
  const { data } = await client.get<PaginatedResponse<Species>>(BASE, {
    params: { offset, limit },
  });
  return data;
}

export async function getSpecies(key: string): Promise<Species> {
  const { data } = await client.get<Species>(`${BASE}/${key}`);
  return data;
}

export async function createSpecies(payload: SpeciesCreate): Promise<Species> {
  const { data } = await client.post<Species>(BASE, payload);
  return data;
}

export async function updateSpecies(key: string, payload: SpeciesCreate): Promise<Species> {
  const { data } = await client.put<Species>(`${BASE}/${key}`, payload);
  return data;
}

export async function deleteSpecies(key: string): Promise<void> {
  await client.delete(`${BASE}/${key}`);
}

// Cultivars (nested under species)

export async function listCultivars(speciesKey: string): Promise<Cultivar[]> {
  const { data } = await client.get<Cultivar[]>(`${BASE}/${speciesKey}/cultivars`);
  return data;
}

export async function createCultivar(
  speciesKey: string,
  payload: Omit<CultivarCreate, 'species_key'>,
): Promise<Cultivar> {
  const { data } = await client.post<Cultivar>(`${BASE}/${speciesKey}/cultivars`, {
    ...payload,
    species_key: speciesKey,
  });
  return data;
}

export async function getCultivar(speciesKey: string, cultivarKey: string): Promise<Cultivar> {
  const { data } = await client.get<Cultivar>(`${BASE}/${speciesKey}/cultivars/${cultivarKey}`);
  return data;
}

export async function updateCultivar(
  speciesKey: string,
  cultivarKey: string,
  payload: Omit<CultivarCreate, 'species_key'>,
): Promise<Cultivar> {
  const { data } = await client.put<Cultivar>(`${BASE}/${speciesKey}/cultivars/${cultivarKey}`, {
    ...payload,
    species_key: speciesKey,
  });
  return data;
}

export async function deleteCultivar(speciesKey: string, cultivarKey: string): Promise<void> {
  await client.delete(`${BASE}/${speciesKey}/cultivars/${cultivarKey}`);
}
