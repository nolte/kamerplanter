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

import * as calc from '@/api/endpoints/nutrient-calculations';

const client = mocks.client;

beforeEach(() => {
  vi.clearAllMocks();
});

describe('nutrient-calculations endpoints', () => {
  it('calculateMixingProtocol posts to mixing-protocol', async () => {
    client.post.mockResolvedValue({ data: {} });
    const payload = { fertilizers: [] } as never;
    await calc.calculateMixingProtocol(payload);
    expect(client.post).toHaveBeenCalledWith('/nutrient-calculations/mixing-protocol', payload);
  });

  it('calculateAreaDosing posts to area-dosing', async () => {
    client.post.mockResolvedValue({ data: {} });
    const payload = { fertilizer_keys: ['compost'], area_m2: 12 } as never;
    await calc.calculateAreaDosing(payload);
    expect(client.post).toHaveBeenCalledWith('/nutrient-calculations/area-dosing', payload);
  });

  it('calculateFlushing posts to flushing', async () => {
    client.post.mockResolvedValue({ data: {} });
    const payload = { volume_liters: 10 } as never;
    await calc.calculateFlushing(payload);
    expect(client.post).toHaveBeenCalledWith('/nutrient-calculations/flushing', payload);
  });

  it('calculateRunoff posts to runoff', async () => {
    client.post.mockResolvedValue({ data: {} });
    const payload = { input_ec: 1.5 } as never;
    await calc.calculateRunoff(payload);
    expect(client.post).toHaveBeenCalledWith('/nutrient-calculations/runoff', payload);
  });

  it('validateMixingSafety posts to mixing-safety', async () => {
    client.post.mockResolvedValue({ data: {} });
    const payload = { fertilizers: [] } as never;
    await calc.validateMixingSafety(payload);
    expect(client.post).toHaveBeenCalledWith('/nutrient-calculations/mixing-safety', payload);
  });

  it('calculateWaterMixReverse posts to water-mix/reverse', async () => {
    client.post.mockResolvedValue({ data: {} });
    const payload = { target_ec: 1.2 } as never;
    await calc.calculateWaterMixReverse(payload);
    expect(client.post).toHaveBeenCalledWith('/nutrient-calculations/water-mix/reverse', payload);
  });

  it('calculateEcBudget posts to ec-budget', async () => {
    client.post.mockResolvedValue({ data: {} });
    const payload = { target_ec_ms: 1.8 } as never;
    await calc.calculateEcBudget(payload);
    expect(client.post).toHaveBeenCalledWith('/nutrient-calculations/ec-budget', payload);
  });
});
