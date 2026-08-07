import client from '../client';
import { CATALOGUE_PAGE_SIZE, fetchAllPages } from '../paginate';
import type {
  Species,
  SpeciesCreate,
  SpeciesReferenceImages,
  PaginatedResponse,
  Cultivar,
  CultivarCreate,
} from '../types';

const BASE = '/species';

export async function listSpecies(offset = 0, limit = 50): Promise<PaginatedResponse<Species>> {
  const { data } = await client.get<PaginatedResponse<Species>>(BASE, {
    params: { offset, limit },
  });
  return data;
}

/**
 * Loads the complete species catalogue by paging until a short page is returned,
 * and re-wraps it in the envelope shape `listSpecies` returns so the slice's
 * `total`/`offset`/`limit` handling is unchanged.
 *
 * The list view used a fixed `limit=1000` — the species endpoint's own cap
 * (`le=1000`, not the shared `le=200`). That held 207 seeded species with 793
 * rows of headroom, so it never truncated in practice, but "under today" is not
 * a resting state: species are tenant-extensible, and the failure mode when the
 * bound is finally crossed is silent, since the list view's search and sort run
 * client-side (#995).
 */
export async function listAllSpecies(
  pageSize = CATALOGUE_PAGE_SIZE,
): Promise<PaginatedResponse<Species>> {
  const items = await fetchAllPages(
    async (offset, limit) => (await listSpecies(offset, limit)).items,
    pageSize,
  );
  return { items, total: items.length, offset: 0, limit: items.length };
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

export async function getSpeciesReferenceImages(key: string): Promise<SpeciesReferenceImages> {
  const { data } = await client.get<SpeciesReferenceImages>(`${BASE}/${key}/reference-images`);
  return data;
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
