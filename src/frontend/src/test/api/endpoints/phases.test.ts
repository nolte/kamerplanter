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

import * as phases from '@/api/endpoints/phases';

const client = mocks.client;

beforeEach(() => {
  vi.clearAllMocks();
});

describe('phases endpoints — phase control', () => {
  it('getCurrentPhase gets current phase for plant', async () => {
    client.get.mockResolvedValue({ data: { phase: 'veg' } });
    await phases.getCurrentPhase('pl1');
    expect(client.get).toHaveBeenCalledWith('/plant-instances/pl1/phases/current');
  });

  it('transitionPhase posts transition payload', async () => {
    client.post.mockResolvedValue({ data: { key: 'pl1' } });
    const payload = { target_phase: 'flower' } as never;
    await phases.transitionPhase('pl1', payload);
    expect(client.post).toHaveBeenCalledWith('/plant-instances/pl1/phases/transition', payload);
  });

  it('getPhaseHistory gets phase history', async () => {
    client.get.mockResolvedValue({ data: [] });
    await phases.getPhaseHistory('pl1');
    expect(client.get).toHaveBeenCalledWith('/plant-instances/pl1/phases/history');
  });

  it('updatePhaseHistoryDates patches a history entry', async () => {
    client.patch.mockResolvedValue({ data: { key: 'h1' } });
    const payload = { entered_at: '2026-01-01' } as never;
    await phases.updatePhaseHistoryDates('pl1', 'h1', payload);
    expect(client.patch).toHaveBeenCalledWith('/plant-instances/pl1/phases/history/h1', payload);
  });

  it('deletePhaseHistory deletes a history entry', async () => {
    client.delete.mockResolvedValue({ data: undefined });
    await phases.deletePhaseHistory('pl1', 'h1');
    expect(client.delete).toHaveBeenCalledWith('/plant-instances/pl1/phases/history/h1');
  });
});

describe('phases endpoints — growth phases', () => {
  it('listGrowthPhases gets with lifecycle_key param', async () => {
    client.get.mockResolvedValue({ data: [] });
    await phases.listGrowthPhases('lc1');
    expect(client.get).toHaveBeenCalledWith('/growth-phases', {
      params: { lifecycle_key: 'lc1' },
    });
  });

  it('getGrowthPhase gets phase by key', async () => {
    client.get.mockResolvedValue({ data: { key: 'g1' } });
    await phases.getGrowthPhase('g1');
    expect(client.get).toHaveBeenCalledWith('/growth-phases/g1');
  });

  it('createGrowthPhase posts payload', async () => {
    client.post.mockResolvedValue({ data: { key: 'g1' } });
    const payload = { name: 'Veg' } as never;
    await phases.createGrowthPhase(payload);
    expect(client.post).toHaveBeenCalledWith('/growth-phases', payload);
  });

  it('updateGrowthPhase puts payload by key', async () => {
    client.put.mockResolvedValue({ data: { key: 'g1' } });
    const payload = { name: 'X' } as never;
    await phases.updateGrowthPhase('g1', payload);
    expect(client.put).toHaveBeenCalledWith('/growth-phases/g1', payload);
  });

  it('deleteGrowthPhase deletes by key', async () => {
    client.delete.mockResolvedValue({ data: undefined });
    await phases.deleteGrowthPhase('g1');
    expect(client.delete).toHaveBeenCalledWith('/growth-phases/g1');
  });
});

describe('phases endpoints — lifecycle config', () => {
  it('getLifecycleConfig gets species lifecycle', async () => {
    client.get.mockResolvedValue({ data: { key: 'lc1' } });
    await phases.getLifecycleConfig('sp1');
    expect(client.get).toHaveBeenCalledWith('/species/sp1/lifecycle');
  });

  it('createLifecycleConfig posts payload with injected species_key', async () => {
    client.post.mockResolvedValue({ data: { key: 'lc1' } });
    await phases.createLifecycleConfig('sp1', { is_perennial: true } as never);
    expect(client.post).toHaveBeenCalledWith('/species/sp1/lifecycle', {
      is_perennial: true,
      species_key: 'sp1',
    });
  });

  it('updateLifecycleConfig puts payload with injected species_key', async () => {
    client.put.mockResolvedValue({ data: { key: 'lc1' } });
    await phases.updateLifecycleConfig('sp1', 'lc1', { is_perennial: false } as never);
    expect(client.put).toHaveBeenCalledWith('/species/sp1/lifecycle/lc1', {
      is_perennial: false,
      species_key: 'sp1',
    });
  });
});

describe('phases endpoints — profiles', () => {
  it('getRequirementProfile gets requirement profile by phase', async () => {
    client.get.mockResolvedValue({ data: { key: 'r1' } });
    await phases.getRequirementProfile('ph1');
    expect(client.get).toHaveBeenCalledWith('/profiles/requirements/ph1');
  });

  it('createRequirementProfile posts payload', async () => {
    client.post.mockResolvedValue({ data: { key: 'r1' } });
    const payload = { phase_key: 'ph1' } as never;
    await phases.createRequirementProfile(payload);
    expect(client.post).toHaveBeenCalledWith('/profiles/requirements', payload);
  });

  it('updateRequirementProfile puts payload by key', async () => {
    client.put.mockResolvedValue({ data: { key: 'r1' } });
    const payload = { vpd: 1 } as never;
    await phases.updateRequirementProfile('r1', payload);
    expect(client.put).toHaveBeenCalledWith('/profiles/requirements/r1', payload);
  });

  it('getNutrientProfile gets nutrient profile by phase', async () => {
    client.get.mockResolvedValue({ data: { key: 'n1' } });
    await phases.getNutrientProfile('ph1');
    expect(client.get).toHaveBeenCalledWith('/profiles/nutrients/ph1');
  });

  it('createNutrientProfile posts payload', async () => {
    client.post.mockResolvedValue({ data: { key: 'n1' } });
    const payload = { phase_key: 'ph1' } as never;
    await phases.createNutrientProfile(payload);
    expect(client.post).toHaveBeenCalledWith('/profiles/nutrients', payload);
  });

  it('updateNutrientProfile puts payload by key', async () => {
    client.put.mockResolvedValue({ data: { key: 'n1' } });
    const payload = { npk: '1-1-1' } as never;
    await phases.updateNutrientProfile('n1', payload);
    expect(client.put).toHaveBeenCalledWith('/profiles/nutrients/n1', payload);
  });

  it('generateDefaultProfiles posts to generate-defaults endpoint', async () => {
    client.post.mockResolvedValue({ data: { requirement: {}, nutrient: {} } });
    await phases.generateDefaultProfiles('ph1');
    expect(client.post).toHaveBeenCalledWith('/profiles/generate-defaults/ph1');
  });
});
