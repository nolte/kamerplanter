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

import * as plants from '@/api/endpoints/plantInstances';

const client = mocks.client;

beforeEach(() => {
  vi.clearAllMocks();
});

describe('plantInstances endpoints', () => {
  it('listPlantInstances gets paginated instances', async () => {
    client.get.mockResolvedValue({ data: [] });
    await plants.listPlantInstances(5, 10);
    expect(client.get).toHaveBeenCalledWith('/plant-instances', {
      params: { offset: 5, limit: 10 },
    });
  });

  it('getPlantInstance gets instance by key', async () => {
    client.get.mockResolvedValue({ data: { key: 'pl1' } });
    await plants.getPlantInstance('pl1');
    expect(client.get).toHaveBeenCalledWith('/plant-instances/pl1');
  });

  it('createPlantInstance posts payload', async () => {
    client.post.mockResolvedValue({ data: { key: 'pl1' } });
    const payload = { species_key: 'sp1' } as never;
    await plants.createPlantInstance(payload);
    expect(client.post).toHaveBeenCalledWith('/plant-instances', payload);
  });

  it('updatePlantInstance puts payload by key', async () => {
    client.put.mockResolvedValue({ data: { key: 'pl1' } });
    const payload = { nickname: 'X' } as never;
    await plants.updatePlantInstance('pl1', payload);
    expect(client.put).toHaveBeenCalledWith('/plant-instances/pl1', payload);
  });

  it('removePlantInstance posts an empty body for a plain removal', async () => {
    client.post.mockResolvedValue({ data: { key: 'pl1' } });
    await plants.removePlantInstance('pl1');
    expect(client.post).toHaveBeenCalledWith('/plant-instances/pl1/remove', {});
  });

  it('removePlantInstance forwards the termination body', async () => {
    client.post.mockResolvedValue({ data: { key: 'pl1' } });
    await plants.removePlantInstance('pl1', { termination_type: 'died', termination_cause: 'pest' });
    expect(client.post).toHaveBeenCalledWith('/plant-instances/pl1/remove', {
      termination_type: 'died',
      termination_cause: 'pest',
    });
  });

  it('getSurvivalStats gets the analytics endpoint', async () => {
    client.get.mockResolvedValue({ data: { total: 0 } });
    await plants.getSurvivalStats();
    expect(client.get).toHaveBeenCalledWith('/plant-instances/survival-stats');
  });

  it('validatePlanting posts species key to slot validation', async () => {
    client.post.mockResolvedValue({ data: { valid: true } });
    await plants.validatePlanting('sl1', 'sp1');
    expect(client.post).toHaveBeenCalledWith('/plant-instances/slots/sl1/validate-planting', {
      species_key: 'sp1',
    });
  });

  it('getPlantRuns gets runs for plant', async () => {
    client.get.mockResolvedValue({ data: [] });
    await plants.getPlantRuns('pl1');
    expect(client.get).toHaveBeenCalledWith('/plant-instances/pl1/planting-runs');
  });
});
