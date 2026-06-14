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

import * as importApi from '@/api/endpoints/import';

const client = mocks.client;

beforeEach(() => {
  vi.clearAllMocks();
});

describe('import endpoints', () => {
  it('uploadImportFile posts FormData with file, entity type and strategy', async () => {
    client.post.mockResolvedValue({ data: { key: 'j1' } });
    const file = new File(['name\n'], 'data.csv', { type: 'text/csv' });
    await importApi.uploadImportFile(file, 'species' as never, 'skip' as never);
    expect(client.post).toHaveBeenCalledTimes(1);
    const [url, body, opts] = client.post.mock.calls[0];
    expect(url).toBe('/import/upload');
    expect(body).toBeInstanceOf(FormData);
    const fd = body as FormData;
    expect(fd.get('file')).toBe(file);
    expect(fd.get('entity_type')).toBe('species');
    expect(fd.get('duplicate_strategy')).toBe('skip');
    expect(opts).toEqual({ headers: { 'Content-Type': 'multipart/form-data' } });
  });

  it('getImportJob gets job by key', async () => {
    client.get.mockResolvedValue({ data: { key: 'j1' } });
    await importApi.getImportJob('j1');
    expect(client.get).toHaveBeenCalledWith('/import/jobs/j1');
  });

  it('listImportJobs gets paginated jobs', async () => {
    client.get.mockResolvedValue({ data: { items: [], total: 0 } });
    await importApi.listImportJobs(5, 10);
    expect(client.get).toHaveBeenCalledWith('/import/jobs', {
      params: { offset: 5, limit: 10 },
    });
  });

  it('confirmImportJob posts to confirm endpoint', async () => {
    client.post.mockResolvedValue({ data: { key: 'j1' } });
    await importApi.confirmImportJob('j1');
    expect(client.post).toHaveBeenCalledWith('/import/jobs/j1/confirm');
  });

  it('deleteImportJob deletes job by key', async () => {
    client.delete.mockResolvedValue({ data: undefined });
    await importApi.deleteImportJob('j1');
    expect(client.delete).toHaveBeenCalledWith('/import/jobs/j1');
  });

  it('getImportTemplate gets template for entity type', async () => {
    client.get.mockResolvedValue({ data: 'name,type\n' });
    await expect(importApi.getImportTemplate('species' as never)).resolves.toBe('name,type\n');
    expect(client.get).toHaveBeenCalledWith('/import/templates/species');
  });
});
