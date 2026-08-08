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

import * as substrates from '@/api/endpoints/substrates';

const client = mocks.client;

beforeEach(() => {
  vi.clearAllMocks();
});

describe('substrates endpoints — substrate CRUD', () => {
  it('listSubstrates gets paginated substrates', async () => {
    client.get.mockResolvedValue({ data: [] });
    await substrates.listSubstrates(5, 10);
    expect(client.get).toHaveBeenCalledWith('/substrates', {
      params: { offset: 5, limit: 10 },
    });
  });

  it('listAllSubstrates pages until a short page (#995)', async () => {
    const full = Array.from({ length: 200 }, (_v, i) => ({ key: `s${i}` }));
    client.get
      .mockResolvedValueOnce({ data: full })
      .mockResolvedValueOnce({ data: [{ key: 'tail' }] });

    const all = await substrates.listAllSubstrates();

    expect(all).toHaveLength(201);
    expect(client.get).toHaveBeenCalledTimes(2);
    expect(client.get).toHaveBeenNthCalledWith(2, '/substrates', {
      params: { offset: 200, limit: 200 },
    });
  });

  it('getSubstrate gets substrate by key', async () => {
    client.get.mockResolvedValue({ data: { key: 's1' } });
    await substrates.getSubstrate('s1');
    expect(client.get).toHaveBeenCalledWith('/substrates/s1');
  });

  it('createSubstrate posts payload', async () => {
    client.post.mockResolvedValue({ data: { key: 's1' } });
    const payload = { name: 'Coco' } as never;
    await substrates.createSubstrate(payload);
    expect(client.post).toHaveBeenCalledWith('/substrates', payload);
  });

  it('updateSubstrate puts payload by key', async () => {
    client.put.mockResolvedValue({ data: { key: 's1' } });
    const payload = { name: 'X' } as never;
    await substrates.updateSubstrate('s1', payload);
    expect(client.put).toHaveBeenCalledWith('/substrates/s1', payload);
  });

  it('deleteSubstrate deletes by key', async () => {
    client.delete.mockResolvedValue({ data: undefined });
    await substrates.deleteSubstrate('s1');
    expect(client.delete).toHaveBeenCalledWith('/substrates/s1');
  });
});

describe('substrates endpoints — batches', () => {
  it('listBatches gets batches for substrate', async () => {
    client.get.mockResolvedValue({ data: [] });
    await substrates.listBatches('s1');
    expect(client.get).toHaveBeenCalledWith('/substrates/s1/batches');
  });

  it('getBatch gets batch by key', async () => {
    client.get.mockResolvedValue({ data: { key: 'b1' } });
    await substrates.getBatch('b1');
    expect(client.get).toHaveBeenCalledWith('/substrates/batches/b1');
  });

  it('createBatch posts payload', async () => {
    client.post.mockResolvedValue({ data: { key: 'b1' } });
    const payload = { substrate_key: 's1' } as never;
    await substrates.createBatch(payload);
    expect(client.post).toHaveBeenCalledWith('/substrates/batches', payload);
  });

  it('updateBatch puts payload by key', async () => {
    client.put.mockResolvedValue({ data: { key: 'b1' } });
    const payload = { ph: 6 } as never;
    await substrates.updateBatch('b1', payload);
    expect(client.put).toHaveBeenCalledWith('/substrates/batches/b1', payload);
  });

  it('deleteBatch deletes by key', async () => {
    client.delete.mockResolvedValue({ data: undefined });
    await substrates.deleteBatch('b1');
    expect(client.delete).toHaveBeenCalledWith('/substrates/batches/b1');
  });

  it('checkReusability posts to check-reusability', async () => {
    client.post.mockResolvedValue({ data: { reusable: true } });
    await substrates.checkReusability('b1');
    expect(client.post).toHaveBeenCalledWith('/substrates/batches/b1/check-reusability');
  });
});

describe('substrates endpoints — mixing', () => {
  it('createSubstrateMix posts to /substrates/mix', async () => {
    client.post.mockResolvedValue({ data: { key: 's2' } });
    const payload = { components: [] } as never;
    await substrates.createSubstrateMix(payload);
    expect(client.post).toHaveBeenCalledWith('/substrates/mix', payload);
  });

  it('previewSubstrateMix posts to /substrates/preview-mix', async () => {
    client.post.mockResolvedValue({ data: { key: 's2' } });
    const payload = { components: [] } as never;
    await substrates.previewSubstrateMix(payload);
    expect(client.post).toHaveBeenCalledWith('/substrates/preview-mix', payload);
  });
});
