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

import * as api from '@/api/endpoints/overwinteringProfiles';

const client = mocks.client;

beforeEach(() => {
  vi.clearAllMocks();
});

describe('overwinteringProfiles endpoints', () => {
  it('listOverwinteringProfiles defaults to offset 0 / limit 50', async () => {
    client.get.mockResolvedValue({ data: [] });
    await api.listOverwinteringProfiles();
    expect(client.get).toHaveBeenCalledWith('/overwintering-profiles', {
      params: { offset: 0, limit: 50 },
    });
  });

  it('listOverwinteringProfiles forwards pagination', async () => {
    client.get.mockResolvedValue({ data: [] });
    await api.listOverwinteringProfiles(100, 25);
    expect(client.get).toHaveBeenCalledWith('/overwintering-profiles', {
      params: { offset: 100, limit: 25 },
    });
  });

  it('getOverwinteringProfile GETs by key', async () => {
    client.get.mockResolvedValue({ data: { key: 'ow1' } });
    await api.getOverwinteringProfile('ow1');
    expect(client.get).toHaveBeenCalledWith('/overwintering-profiles/ow1');
  });

  it('createOverwinteringProfile POSTs the payload', async () => {
    const payload = { plant_instance_key: 'p1' } as never;
    client.post.mockResolvedValue({ data: { key: 'ow1' } });
    await api.createOverwinteringProfile(payload);
    expect(client.post).toHaveBeenCalledWith('/overwintering-profiles', payload);
  });

  it('updateOverwinteringProfile PUTs by key', async () => {
    const payload = { protection_method: 'mulch' } as never;
    client.put.mockResolvedValue({ data: { key: 'ow1' } });
    await api.updateOverwinteringProfile('ow1', payload);
    expect(client.put).toHaveBeenCalledWith('/overwintering-profiles/ow1', payload);
  });

  it('deleteOverwinteringProfile DELETEs by key', async () => {
    client.delete.mockResolvedValue({ data: undefined });
    await api.deleteOverwinteringProfile('ow1');
    expect(client.delete).toHaveBeenCalledWith('/overwintering-profiles/ow1');
  });

  it('autoGenerateOverwinteringProfile POSTs to the auto-generate path', async () => {
    const payload = { plant_instance_key: 'p1' } as never;
    client.post.mockResolvedValue({ data: { key: 'ow1' } });
    await api.autoGenerateOverwinteringProfile(payload);
    expect(client.post).toHaveBeenCalledWith('/overwintering-profiles/auto-generate', payload);
  });

  it('getHardinessOverview GETs the hardiness overview', async () => {
    client.get.mockResolvedValue({ data: { green: 0 } });
    await api.getHardinessOverview();
    expect(client.get).toHaveBeenCalledWith('/overwintering-profiles/hardiness-overview');
  });
});
