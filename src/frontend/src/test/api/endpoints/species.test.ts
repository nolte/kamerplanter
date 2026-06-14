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

  it('createCultivar posts payload with injected species_key', async () => {
    client.post.mockResolvedValue({ data: { key: 'cv1' } });
    await species.createCultivar('sp1', { name: 'OG' } as never);
    expect(client.post).toHaveBeenCalledWith('/species/sp1/cultivars', {
      name: 'OG',
      species_key: 'sp1',
    });
  });

  it('getCultivar gets cultivar by composite key', async () => {
    client.get.mockResolvedValue({ data: { key: 'cv1' } });
    await species.getCultivar('sp1', 'cv1');
    expect(client.get).toHaveBeenCalledWith('/species/sp1/cultivars/cv1');
  });

  it('updateCultivar puts payload with injected species_key', async () => {
    client.put.mockResolvedValue({ data: { key: 'cv1' } });
    await species.updateCultivar('sp1', 'cv1', { name: 'X' } as never);
    expect(client.put).toHaveBeenCalledWith('/species/sp1/cultivars/cv1', {
      name: 'X',
      species_key: 'sp1',
    });
  });

  it('deleteCultivar deletes by composite key', async () => {
    client.delete.mockResolvedValue({ data: undefined });
    await species.deleteCultivar('sp1', 'cv1');
    expect(client.delete).toHaveBeenCalledWith('/species/sp1/cultivars/cv1');
  });
});
