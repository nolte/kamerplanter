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

import * as families from '@/api/endpoints/botanicalFamilies';

const client = mocks.client;

beforeEach(() => {
  vi.clearAllMocks();
});

describe('botanicalFamilies endpoints', () => {
  it('listBotanicalFamilies gets paginated families', async () => {
    client.get.mockResolvedValue({ data: [] });
    await families.listBotanicalFamilies(5, 10);
    expect(client.get).toHaveBeenCalledWith('/botanical-families', {
      params: { offset: 5, limit: 10 },
    });
  });

  it('getBotanicalFamily gets family by key', async () => {
    client.get.mockResolvedValue({ data: { key: 'fa1' } });
    await families.getBotanicalFamily('fa1');
    expect(client.get).toHaveBeenCalledWith('/botanical-families/fa1');
  });

  it('createBotanicalFamily posts payload', async () => {
    client.post.mockResolvedValue({ data: { key: 'fa1' } });
    const payload = { name: 'Araceae' } as never;
    await families.createBotanicalFamily(payload);
    expect(client.post).toHaveBeenCalledWith('/botanical-families', payload);
  });

  it('updateBotanicalFamily puts payload by key', async () => {
    client.put.mockResolvedValue({ data: { key: 'fa1' } });
    const payload = { name: 'X' } as never;
    await families.updateBotanicalFamily('fa1', payload);
    expect(client.put).toHaveBeenCalledWith('/botanical-families/fa1', payload);
  });

  it('deleteBotanicalFamily deletes by key', async () => {
    client.delete.mockResolvedValue({ data: undefined });
    await families.deleteBotanicalFamily('fa1');
    expect(client.delete).toHaveBeenCalledWith('/botanical-families/fa1');
  });

  it('listSpeciesByFamily gets species for family', async () => {
    client.get.mockResolvedValue({ data: [] });
    await families.listSpeciesByFamily('fa1');
    expect(client.get).toHaveBeenCalledWith('/botanical-families/fa1/species');
  });

  it('listAllBotanicalFamilies pages past the limit=50 cap until a short page', async () => {
    // Two full pages of 200 then a short page → proves the "load all" fix is not
    // capped at the single-request default (limit=50) or the backend max (200).
    const fullA = Array.from({ length: 200 }, (_v, i) => ({ key: `a${i}` }));
    const fullB = Array.from({ length: 200 }, (_v, i) => ({ key: `b${i}` }));
    const tail = [{ key: 'tail-1' }, { key: 'tail-2' }];
    client.get
      .mockResolvedValueOnce({ data: fullA })
      .mockResolvedValueOnce({ data: fullB })
      .mockResolvedValueOnce({ data: tail });

    const all = await families.listAllBotanicalFamilies();

    expect(all).toHaveLength(402);
    expect(client.get).toHaveBeenCalledTimes(3);
    expect(client.get).toHaveBeenNthCalledWith(1, '/botanical-families', {
      params: { offset: 0, limit: 200 },
    });
    expect(client.get).toHaveBeenNthCalledWith(2, '/botanical-families', {
      params: { offset: 200, limit: 200 },
    });
    expect(client.get).toHaveBeenNthCalledWith(3, '/botanical-families', {
      params: { offset: 400, limit: 200 },
    });
  });

  it('listAllBotanicalFamilies stops after a single short page', async () => {
    client.get.mockResolvedValueOnce({ data: [{ key: 'fa1' }, { key: 'fa2' }] });

    const all = await families.listAllBotanicalFamilies();

    expect(all).toHaveLength(2);
    expect(client.get).toHaveBeenCalledTimes(1);
  });
});
