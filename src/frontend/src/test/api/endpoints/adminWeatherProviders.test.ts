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

import * as api from '@/api/endpoints/adminWeatherProviders';

const client = mocks.client;

beforeEach(() => {
  vi.clearAllMocks();
});

describe('adminWeatherProviders endpoints', () => {
  it('getWeatherProviders GETs the global admin base', async () => {
    client.get.mockResolvedValue({ data: { providers: [] } });
    const result = await api.getWeatherProviders();
    expect(client.get).toHaveBeenCalledWith('/admin/weather-providers');
    expect(result).toEqual({ providers: [] });
  });

  it('putWeatherProviders PUTs the payload', async () => {
    const payload = { openweathermap_api_key: 'plain-key' } as never;
    client.put.mockResolvedValue({ data: { providers: [] } });
    await api.putWeatherProviders(payload);
    expect(client.put).toHaveBeenCalledWith('/admin/weather-providers', payload);
  });

  it('testWeatherProvider POSTs to the URL-encoded provider test path', async () => {
    client.post.mockResolvedValue({ data: { ok: true } });
    const result = await api.testWeatherProvider('open meteo');
    expect(client.post).toHaveBeenCalledWith('/admin/weather-providers/open%20meteo/test');
    expect(result).toEqual({ ok: true });
  });

  it('triggerWeatherFetch POSTs to the manual fetch path (F-14)', async () => {
    client.post.mockResolvedValue({ data: { status: 'queued', task_id: 't-1' } });
    const result = await api.triggerWeatherFetch();
    expect(client.post).toHaveBeenCalledWith('/admin/weather-providers/fetch');
    expect(result).toEqual({ status: 'queued', task_id: 't-1' });
  });

  it('getWeatherFetchStatus GETs the fetch status (F-14)', async () => {
    client.get.mockResolvedValue({ data: { interval_hours: 6 } });
    const result = await api.getWeatherFetchStatus();
    expect(client.get).toHaveBeenCalledWith('/admin/weather-providers/fetch-status', { signal: undefined });
    expect(result).toEqual({ interval_hours: 6 });
  });

  it('getWeatherFetchStatus hands the abort signal to the client', async () => {
    client.get.mockResolvedValue({ data: { interval_hours: 6 } });
    const controller = new AbortController();
    await api.getWeatherFetchStatus(controller.signal);
    expect(client.get).toHaveBeenCalledWith('/admin/weather-providers/fetch-status', { signal: controller.signal });
  });
});
