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

import * as adminSettings from '@/api/endpoints/adminSettings';

const client = mocks.client;

beforeEach(() => {
  vi.clearAllMocks();
});

describe('adminSettings endpoints', () => {
  it('getSystemSettings gets /admin/settings', async () => {
    client.get.mockResolvedValue({ data: {} });
    await adminSettings.getSystemSettings();
    expect(client.get).toHaveBeenCalledWith('/admin/settings');
  });

  it('updateHaSettings puts to home-assistant subpath', async () => {
    client.put.mockResolvedValue({ data: {} });
    const body = { ha_url: 'http://ha' };
    await adminSettings.updateHaSettings(body);
    expect(client.put).toHaveBeenCalledWith('/admin/settings/home-assistant', body);
  });

  it('testHaConnection posts to home-assistant test', async () => {
    client.post.mockResolvedValue({ data: { success: true, message: 'ok' } });
    const body = { ha_url: 'http://ha' };
    await adminSettings.testHaConnection(body);
    expect(client.post).toHaveBeenCalledWith('/admin/settings/home-assistant/test', body);
  });

  it('clearHaSettings deletes home-assistant settings', async () => {
    client.delete.mockResolvedValue({ data: undefined });
    await adminSettings.clearHaSettings();
    expect(client.delete).toHaveBeenCalledWith('/admin/settings/home-assistant');
  });

  it('updatePlantIdentificationSettings puts to plant-identification subpath', async () => {
    client.put.mockResolvedValue({ data: {} });
    const body = { plantnet_api_key: 'my-key' };
    await adminSettings.updatePlantIdentificationSettings(body);
    expect(client.put).toHaveBeenCalledWith('/admin/settings/plant-identification', body);
  });

  it('testPlantIdentificationKey posts to plant-identification test', async () => {
    client.post.mockResolvedValue({ data: { success: true, message: 'ok' } });
    const body = { plantnet_api_key: 'my-key' };
    await adminSettings.testPlantIdentificationKey(body);
    expect(client.post).toHaveBeenCalledWith('/admin/settings/plant-identification/test', body);
  });

  it('clearPlantIdentificationSettings deletes plant-identification settings', async () => {
    client.delete.mockResolvedValue({ data: undefined });
    await adminSettings.clearPlantIdentificationSettings();
    expect(client.delete).toHaveBeenCalledWith('/admin/settings/plant-identification');
  });
});
