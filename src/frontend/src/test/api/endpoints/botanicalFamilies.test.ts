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
});
