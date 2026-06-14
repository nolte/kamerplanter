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

import * as runs from '@/api/endpoints/plantingRuns';

const client = mocks.client;

beforeEach(() => {
  vi.clearAllMocks();
});

describe('plantingRuns endpoints — run CRUD', () => {
  it('listPlantingRuns uses default pagination only', async () => {
    client.get.mockResolvedValue({ data: [] });
    await runs.listPlantingRuns();
    expect(client.get).toHaveBeenCalledWith('/planting-runs', {
      params: { offset: 0, limit: 50 },
    });
  });

  it('listPlantingRuns merges status, run_type and location filters', async () => {
    client.get.mockResolvedValue({ data: [] });
    await runs.listPlantingRuns(5, 10, 'active', 'seed', 'loc1');
    expect(client.get).toHaveBeenCalledWith('/planting-runs', {
      params: { offset: 5, limit: 10, status: 'active', run_type: 'seed', location_key: 'loc1' },
    });
  });

  it('getPlantingRun gets run by key', async () => {
    client.get.mockResolvedValue({ data: { key: 'r1' } });
    await runs.getPlantingRun('r1');
    expect(client.get).toHaveBeenCalledWith('/planting-runs/r1');
  });

  it('createPlantingRun posts payload', async () => {
    client.post.mockResolvedValue({ data: { key: 'r1' } });
    const payload = { name: 'Run' } as never;
    await runs.createPlantingRun(payload);
    expect(client.post).toHaveBeenCalledWith('/planting-runs', payload);
  });

  it('updatePlantingRun puts payload by key', async () => {
    client.put.mockResolvedValue({ data: { key: 'r1' } });
    const payload = { name: 'X' } as never;
    await runs.updatePlantingRun('r1', payload);
    expect(client.put).toHaveBeenCalledWith('/planting-runs/r1', payload);
  });

  it('deletePlantingRun deletes by key', async () => {
    client.delete.mockResolvedValue({ data: undefined });
    await runs.deletePlantingRun('r1');
    expect(client.delete).toHaveBeenCalledWith('/planting-runs/r1');
  });
});

describe('plantingRuns endpoints — entry management', () => {
  it('listEntries gets entries for run', async () => {
    client.get.mockResolvedValue({ data: [] });
    await runs.listEntries('r1');
    expect(client.get).toHaveBeenCalledWith('/planting-runs/r1/entries');
  });

  it('addEntry posts entry payload', async () => {
    client.post.mockResolvedValue({ data: { key: 'e1' } });
    const payload = { species_key: 'sp1' } as never;
    await runs.addEntry('r1', payload);
    expect(client.post).toHaveBeenCalledWith('/planting-runs/r1/entries', payload);
  });

  it('updateEntry puts entry by composite key', async () => {
    client.put.mockResolvedValue({ data: { key: 'e1' } });
    const payload = { quantity: 5 } as never;
    await runs.updateEntry('r1', 'e1', payload);
    expect(client.put).toHaveBeenCalledWith('/planting-runs/r1/entries/e1', payload);
  });

  it('deleteEntry deletes entry by composite key', async () => {
    client.delete.mockResolvedValue({ data: undefined });
    await runs.deleteEntry('r1', 'e1');
    expect(client.delete).toHaveBeenCalledWith('/planting-runs/r1/entries/e1');
  });
});

describe('plantingRuns endpoints — batch operations', () => {
  it('batchCreatePlants posts to create-plants', async () => {
    client.post.mockResolvedValue({ data: { created: 3 } });
    await runs.batchCreatePlants('r1');
    expect(client.post).toHaveBeenCalledWith('/planting-runs/r1/create-plants');
  });

  it('adoptPlants posts plant keys', async () => {
    client.post.mockResolvedValue({ data: { adopted: 2 } });
    await runs.adoptPlants('r1', ['p1', 'p2']);
    expect(client.post).toHaveBeenCalledWith('/planting-runs/r1/adopt-plants', {
      plant_keys: ['p1', 'p2'],
    });
  });

  it('batchTransition posts transition payload', async () => {
    client.post.mockResolvedValue({ data: { transitioned: 1 } });
    const payload = { target_phase: 'flower' } as never;
    await runs.batchTransition('r1', payload);
    expect(client.post).toHaveBeenCalledWith('/planting-runs/r1/batch-transition', payload);
  });

  it('batchRemove posts provided payload', async () => {
    client.post.mockResolvedValue({ data: { removed: 1 } });
    const payload = { reason: 'disease' } as never;
    await runs.batchRemove('r1', payload);
    expect(client.post).toHaveBeenCalledWith('/planting-runs/r1/batch-remove', payload);
  });

  it('batchRemove posts default reason when no payload given', async () => {
    client.post.mockResolvedValue({ data: { removed: 1 } });
    await runs.batchRemove('r1');
    expect(client.post).toHaveBeenCalledWith('/planting-runs/r1/batch-remove', {
      reason: 'batch_remove',
    });
  });
});

describe('plantingRuns endpoints — plant management', () => {
  it('listRunPlants gets with include_detached false by default', async () => {
    client.get.mockResolvedValue({ data: [] });
    await runs.listRunPlants('r1');
    expect(client.get).toHaveBeenCalledWith('/planting-runs/r1/plants', {
      params: { include_detached: false },
    });
  });

  it('listRunPlants passes include_detached true', async () => {
    client.get.mockResolvedValue({ data: [] });
    await runs.listRunPlants('r1', true);
    expect(client.get).toHaveBeenCalledWith('/planting-runs/r1/plants', {
      params: { include_detached: true },
    });
  });

  it('detachPlant posts reason', async () => {
    client.post.mockResolvedValue({ data: undefined });
    await runs.detachPlant('r1', 'p1', 'moved');
    expect(client.post).toHaveBeenCalledWith('/planting-runs/r1/plants/p1/detach', {
      reason: 'moved',
    });
  });
});

describe('plantingRuns endpoints — nutrient plan & timeline', () => {
  it('assignNutrientPlan posts plan with assigned_by', async () => {
    client.post.mockResolvedValue({ data: {} });
    await runs.assignNutrientPlan('r1', 'pl1', 'me');
    expect(client.post).toHaveBeenCalledWith('/planting-runs/r1/nutrient-plan', {
      plan_key: 'pl1',
      assigned_by: 'me',
    });
  });

  it('assignNutrientPlan defaults assigned_by to empty string', async () => {
    client.post.mockResolvedValue({ data: {} });
    await runs.assignNutrientPlan('r1', 'pl1');
    expect(client.post).toHaveBeenCalledWith('/planting-runs/r1/nutrient-plan', {
      plan_key: 'pl1',
      assigned_by: '',
    });
  });

  it('getRunNutrientPlan gets nutrient plan', async () => {
    client.get.mockResolvedValue({ data: { plan: null } });
    await runs.getRunNutrientPlan('r1');
    expect(client.get).toHaveBeenCalledWith('/planting-runs/r1/nutrient-plan');
  });

  it('removeRunNutrientPlan deletes nutrient plan', async () => {
    client.delete.mockResolvedValue({ data: undefined });
    await runs.removeRunNutrientPlan('r1');
    expect(client.delete).toHaveBeenCalledWith('/planting-runs/r1/nutrient-plan');
  });

  it('getPhaseTimeline gets phase timeline', async () => {
    client.get.mockResolvedValue({ data: [] });
    await runs.getPhaseTimeline('r1');
    expect(client.get).toHaveBeenCalledWith('/planting-runs/r1/phase-timeline');
  });

  it('batchUpdatePhaseDates patches phase dates', async () => {
    client.patch.mockResolvedValue({ data: { updated_count: 1 } });
    const payload = { phase_key: 'ph1', entered_at: '2026-01-01' };
    await runs.batchUpdatePhaseDates('r1', payload);
    expect(client.patch).toHaveBeenCalledWith(
      '/planting-runs/r1/batch-update-phase-dates',
      payload,
    );
  });

  it('getWateringSchedule gets with default days_ahead', async () => {
    client.get.mockResolvedValue({ data: {} });
    await runs.getWateringSchedule('r1');
    expect(client.get).toHaveBeenCalledWith('/planting-runs/r1/watering-schedule', {
      params: { days_ahead: 14 },
    });
  });

  it('getWateringSchedule passes custom days_ahead', async () => {
    client.get.mockResolvedValue({ data: {} });
    await runs.getWateringSchedule('r1', 30);
    expect(client.get).toHaveBeenCalledWith('/planting-runs/r1/watering-schedule', {
      params: { days_ahead: 30 },
    });
  });
});
