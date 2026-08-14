import { describe, it, expect, beforeEach, vi } from 'vitest';

const mocks = vi.hoisted(() => {
  const client = {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
  };
  return { client };
});

vi.mock('@/api/client', () => ({
  __esModule: true,
  default: mocks.client,
  tenantClient: mocks.client,
}));

import * as species from '@/api/endpoints/species';

const client = mocks.client;

beforeEach(() => {
  vi.clearAllMocks();
});

describe('species endpoints — species CRUD', () => {
  it('listSpecies gets paginated species', async () => {
    client.get.mockResolvedValue({ data: { items: [], total: 0 } });
    await species.listSpecies(5, 10);
    expect(client.get).toHaveBeenCalledWith('/species', {
      params: { offset: 5, limit: 10 },
    });
  });

  // #995: the list view asked for a fixed limit=1000 (this endpoint's own cap).
  // It held the 207 seeded species, but it was a bound on a tenant-extensible
  // catalogue whose overflow is invisible, since the page searches client-side.
  it('listAllSpecies pages until a short page and reports the real total', async () => {
    const full = Array.from({ length: 200 }, (_v, i) => ({ key: `sp${i}` }));
    client.get
      .mockResolvedValueOnce({ data: { items: full, total: 999, offset: 0, limit: 200 } })
      .mockResolvedValueOnce({ data: { items: [{ key: 'tail' }], total: 999, offset: 200, limit: 200 } });

    const page = await species.listAllSpecies();

    expect(page.items).toHaveLength(201);
    // `total` is the number actually loaded, not the envelope's — the store's
    // `total` must agree with `items` or the two disagree about the same set.
    expect(page.total).toBe(201);
    expect(client.get).toHaveBeenCalledTimes(2);
    expect(client.get).toHaveBeenNthCalledWith(2, '/species', {
      params: { offset: 200, limit: 200 },
    });
  });

  it('getSpecies gets species by key', async () => {
    client.get.mockResolvedValue({ data: { key: 'sp1' } });
    await species.getSpecies('sp1');
    expect(client.get).toHaveBeenCalledWith('/species/sp1');
  });

  it('createSpecies posts payload', async () => {
    client.post.mockResolvedValue({ data: { key: 'sp1' } });
    const payload = { scientific_name: 'Cannabis sativa' } as never;
    await species.createSpecies(payload);
    expect(client.post).toHaveBeenCalledWith('/species', payload);
  });

  it('updateSpecies puts payload by key', async () => {
    client.put.mockResolvedValue({ data: { key: 'sp1' } });
    const payload = { scientific_name: 'X' } as never;
    await species.updateSpecies('sp1', payload);
    expect(client.put).toHaveBeenCalledWith('/species/sp1', payload);
  });

  it('deleteSpecies deletes by key', async () => {
    client.delete.mockResolvedValue({ data: undefined });
    await species.deleteSpecies('sp1');
    expect(client.delete).toHaveBeenCalledWith('/species/sp1');
  });
});

describe('species endpoints — cultivars', () => {
  it('listCultivars gets cultivars for species', async () => {
    client.get.mockResolvedValue({ data: [] });
    await species.listCultivars('sp1');
    expect(client.get).toHaveBeenCalledWith('/species/sp1/cultivars');
  });

  // #1114: the parent species is the path segment. These two used to assert the
  // opposite — that the client *injects* `species_key` into the body — which it
  // only did to satisfy a required schema field the server then discarded.
  it('createCultivar posts the payload unchanged, with the species in the path', async () => {
    client.post.mockResolvedValue({ data: { key: 'cv1' } });
    await species.createCultivar('sp1', { name: 'OG' } as never);
    expect(client.post).toHaveBeenCalledWith('/species/sp1/cultivars', { name: 'OG' });
  });

  it('getCultivar gets cultivar by composite key', async () => {
    client.get.mockResolvedValue({ data: { key: 'cv1' } });
    await species.getCultivar('sp1', 'cv1');
    expect(client.get).toHaveBeenCalledWith('/species/sp1/cultivars/cv1');
  });

  it('updateCultivar puts the payload unchanged, with the species in the path', async () => {
    client.put.mockResolvedValue({ data: { key: 'cv1' } });
    await species.updateCultivar('sp1', 'cv1', { name: 'X' } as never);
    expect(client.put).toHaveBeenCalledWith('/species/sp1/cultivars/cv1', { name: 'X' });
  });

  it('deleteCultivar deletes by composite key', async () => {
    client.delete.mockResolvedValue({ data: undefined });
    await species.deleteCultivar('sp1', 'cv1');
    expect(client.delete).toHaveBeenCalledWith('/species/sp1/cultivars/cv1');
  });
});
