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

import * as plans from '@/api/endpoints/nutrient-plans';

const client = mocks.client;

beforeEach(() => {
  vi.clearAllMocks();
});

describe('nutrient-plans endpoints — plan CRUD', () => {
  it('fetchNutrientPlans uses default pagination', async () => {
    client.get.mockResolvedValue({ data: [] });
    await plans.fetchNutrientPlans();
    expect(client.get).toHaveBeenCalledWith('/nutrient-plans', {
      params: { offset: 0, limit: 50 },
    });
  });

  it('fetchNutrientPlans merges filter entries into params', async () => {
    client.get.mockResolvedValue({ data: [] });
    await plans.fetchNutrientPlans(10, 20, { plant_type: 'cannabis', author: 'x' });
    expect(client.get).toHaveBeenCalledWith('/nutrient-plans', {
      params: { offset: 10, limit: 20, plant_type: 'cannabis', author: 'x' },
    });
  });

  it('fetchAllNutrientPlans pages until a short page, keeping the filters (#995)', async () => {
    const full = Array.from({ length: 200 }, (_v, i) => ({ key: `p${i}` }));
    client.get
      .mockResolvedValueOnce({ data: full })
      .mockResolvedValueOnce({ data: [{ key: 'tail' }] });

    const all = await plans.fetchAllNutrientPlans(undefined, { is_template: 'true' });

    expect(all).toHaveLength(201);
    expect(client.get).toHaveBeenCalledTimes(2);
    expect(client.get).toHaveBeenNthCalledWith(1, '/nutrient-plans', {
      params: { offset: 0, limit: 200, is_template: 'true' },
    });
    expect(client.get).toHaveBeenNthCalledWith(2, '/nutrient-plans', {
      params: { offset: 200, limit: 200, is_template: 'true' },
    });
  });

  it('fetchNutrientPlan gets plan by key', async () => {
    client.get.mockResolvedValue({ data: { key: 'p1' } });
    await plans.fetchNutrientPlan('p1');
    expect(client.get).toHaveBeenCalledWith('/nutrient-plans/p1');
  });

  it('createNutrientPlan posts payload', async () => {
    client.post.mockResolvedValue({ data: { key: 'p1' } });
    const payload = { name: 'Plan' } as never;
    await plans.createNutrientPlan(payload);
    expect(client.post).toHaveBeenCalledWith('/nutrient-plans', payload);
  });

  it('updateNutrientPlan puts payload by key', async () => {
    client.put.mockResolvedValue({ data: { key: 'p1' } });
    const payload = { name: 'X' } as never;
    await plans.updateNutrientPlan('p1', payload);
    expect(client.put).toHaveBeenCalledWith('/nutrient-plans/p1', payload);
  });

  it('deleteNutrientPlan deletes by key', async () => {
    client.delete.mockResolvedValue({ data: undefined });
    await plans.deleteNutrientPlan('p1');
    expect(client.delete).toHaveBeenCalledWith('/nutrient-plans/p1');
  });
});

describe('nutrient-plans endpoints — clone & validate', () => {
  it('cloneNutrientPlan posts clone payload', async () => {
    client.post.mockResolvedValue({ data: { key: 'p2' } });
    const payload = { new_name: 'Copy', author: 'me' };
    await plans.cloneNutrientPlan('p1', payload);
    expect(client.post).toHaveBeenCalledWith('/nutrient-plans/p1/clone', payload);
  });

  it('validateNutrientPlan gets validation result', async () => {
    client.get.mockResolvedValue({ data: { valid: true } });
    await plans.validateNutrientPlan('p1');
    expect(client.get).toHaveBeenCalledWith('/nutrient-plans/p1/validate');
  });
});

describe('nutrient-plans endpoints — phase entries', () => {
  it('fetchPhaseEntries gets entries for plan', async () => {
    client.get.mockResolvedValue({ data: [] });
    await plans.fetchPhaseEntries('p1');
    expect(client.get).toHaveBeenCalledWith('/nutrient-plans/p1/entries');
  });

  it('createPhaseEntry posts entry payload', async () => {
    client.post.mockResolvedValue({ data: { key: 'e1' } });
    const payload = { phase_name: 'Veg' } as never;
    await plans.createPhaseEntry('p1', payload);
    expect(client.post).toHaveBeenCalledWith('/nutrient-plans/p1/entries', payload);
  });

  it('updatePhaseEntry puts entry by composite key', async () => {
    client.put.mockResolvedValue({ data: { key: 'e1' } });
    const payload = { phase_name: 'X' } as never;
    await plans.updatePhaseEntry('p1', 'e1', payload);
    expect(client.put).toHaveBeenCalledWith('/nutrient-plans/p1/entries/e1', payload);
  });

  it('deletePhaseEntry deletes entry by composite key', async () => {
    client.delete.mockResolvedValue({ data: undefined });
    await plans.deletePhaseEntry('p1', 'e1');
    expect(client.delete).toHaveBeenCalledWith('/nutrient-plans/p1/entries/e1');
  });
});

describe('nutrient-plans endpoints — channel fertilizer assignment', () => {
  it('addFertilizerToChannel posts to nested channel path', async () => {
    client.post.mockResolvedValue({ data: undefined });
    const payload = { fertilizer_key: 'f1', ml_per_liter: 2 };
    await plans.addFertilizerToChannel('e1', 'ch1', payload);
    expect(client.post).toHaveBeenCalledWith(
      '/nutrient-plans/entries/e1/channels/ch1/fertilizers',
      payload,
    );
  });

  it('removeFertilizerFromChannel deletes nested fertilizer', async () => {
    client.delete.mockResolvedValue({ data: undefined });
    await plans.removeFertilizerFromChannel('e1', 'ch1', 'f1');
    expect(client.delete).toHaveBeenCalledWith(
      '/nutrient-plans/entries/e1/channels/ch1/fertilizers/f1',
    );
  });
});

describe('nutrient-plans endpoints — water mix & dosages', () => {
  it('fetchWaterMixRecommendation gets with site_key only', async () => {
    client.get.mockResolvedValue({ data: {} });
    await plans.fetchWaterMixRecommendation('p1', 3, 's1');
    expect(client.get).toHaveBeenCalledWith(
      '/nutrient-plans/p1/entries/3/water-mix-recommendation',
      { params: { site_key: 's1' } },
    );
  });

  it('fetchWaterMixRecommendation adds substrate_type when provided', async () => {
    client.get.mockResolvedValue({ data: {} });
    await plans.fetchWaterMixRecommendation('p1', 3, 's1', 'coco');
    expect(client.get).toHaveBeenCalledWith(
      '/nutrient-plans/p1/entries/3/water-mix-recommendation',
      { params: { site_key: 's1', substrate_type: 'coco' } },
    );
  });

  it('fetchWaterMixRecommendationsBatch gets without substrate', async () => {
    client.get.mockResolvedValue({ data: {} });
    await plans.fetchWaterMixRecommendationsBatch('p1', 's1');
    expect(client.get).toHaveBeenCalledWith(
      '/nutrient-plans/p1/water-mix-recommendations',
      { params: { site_key: 's1' } },
    );
  });

  it('fetchWaterMixRecommendationsBatch adds substrate_type when provided', async () => {
    client.get.mockResolvedValue({ data: {} });
    await plans.fetchWaterMixRecommendationsBatch('p1', 's1', 'soil');
    expect(client.get).toHaveBeenCalledWith(
      '/nutrient-plans/p1/water-mix-recommendations',
      { params: { site_key: 's1', substrate_type: 'soil' } },
    );
  });

  it('calculateDosages posts request to calculate-dosages', async () => {
    client.post.mockResolvedValue({ data: {} });
    const request = { site_key: 's1', phase_sequence_order: 1 };
    await plans.calculateDosages('p1', request);
    expect(client.post).toHaveBeenCalledWith('/nutrient-plans/p1/calculate-dosages', request);
  });
});

describe('nutrient-plans endpoints — plant instance assignment', () => {
  it('assignPlanToPlant posts to plant-instances nutrient-plan', async () => {
    client.post.mockResolvedValue({ data: undefined });
    const payload = { plan_key: 'p1', assigned_by: 'me' };
    await plans.assignPlanToPlant('pl1', payload);
    expect(client.post).toHaveBeenCalledWith('/plant-instances/pl1/nutrient-plan', payload);
  });

  it('getPlantPlan returns plan data on success', async () => {
    client.get.mockResolvedValue({ data: { key: 'p1' } });
    await expect(plans.getPlantPlan('pl1')).resolves.toEqual({ key: 'p1' });
    expect(client.get).toHaveBeenCalledWith('/plant-instances/pl1/nutrient-plan');
  });

  it('getPlantPlan returns null when request rejects', async () => {
    client.get.mockRejectedValue(new Error('404'));
    await expect(plans.getPlantPlan('pl1')).resolves.toBeNull();
  });

  it('removePlantPlan deletes plant nutrient plan', async () => {
    client.delete.mockResolvedValue({ data: undefined });
    await plans.removePlantPlan('pl1');
    expect(client.delete).toHaveBeenCalledWith('/plant-instances/pl1/nutrient-plan');
  });
});
