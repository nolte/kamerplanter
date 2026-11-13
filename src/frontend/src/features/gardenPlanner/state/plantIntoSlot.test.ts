/**
 * The write of "Pflanze setzen" (REQ-053 GP-UX-071, #2913): one plant through the single-plant API with `slot_key`,
 * outside the plan batch - never offline, never on top of unsaved plan edits, never onto a slot taken meanwhile.
 */
import { configureStore } from '@reduxjs/toolkit';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { ApiError } from '@/api/errors';
import * as plantApi from '@/api/endpoints/plantInstances';
import * as sitesApi from '@/api/endpoints/sites';
import type { PlantInstance, Slot } from '@/api/types';
import { bed, planResponse } from '@/test/gardenPlanFixtures';
import * as api from '../api/gardenPlan';
import gardenPlanReducer, {
  applyAction,
  loadGardenPlan,
  selectGardenPlanState,
  setPlanOffline,
} from './gardenPlanSlice';
import { plantIntoSlot, type PlantIntoSlotArg } from './plantIntoSlot';

vi.mock('../api/gardenPlan', async (importOriginal) => ({
  ...(await importOriginal<typeof import('../api/gardenPlan')>()),
  getGardenPlan: vi.fn(),
  applyPlanBatch: vi.fn(),
}));
vi.mock('@/api/endpoints/plantInstances', async (importOriginal) => ({
  ...(await importOriginal<typeof import('@/api/endpoints/plantInstances')>()),
  createPlantInstance: vi.fn(),
}));
vi.mock('@/api/endpoints/sites', async (importOriginal) => ({
  ...(await importOriginal<typeof import('@/api/endpoints/sites')>()),
  getSlot: vi.fn(),
}));

const getGardenPlan = vi.mocked(api.getGardenPlan);
const applyPlanBatch = vi.mocked(api.applyPlanBatch);
const createPlantInstance = vi.mocked(plantApi.createPlantInstance);
const getSlot = vi.mocked(sitesApi.getSlot);

const ARG: PlantIntoSlotArg = {
  bedKey: 'loc_b1',
  slotKey: 'slot_1',
  speciesKey: 'sp_lettuce',
  cultivarKey: null,
  plantedOn: '2026-11-13',
  instanceId: 'LACTU-1113-ABC',
};

function slot(occupied: boolean): Slot {
  return {
    key: 'slot_1',
    slot_id: 'B1_1',
    location_key: 'loc_b1',
    capacity_plants: 1,
    currently_occupied: occupied,
    last_sanitization: null,
    created_at: null,
    updated_at: null,
  };
}

function apiError(status: number, code: string): ApiError {
  return new ApiError(
    { error_id: 'e1', error_code: code, message: code, details: [], timestamp: '', path: '/plant-instances', method: 'POST' },
    status,
  );
}

async function loaded() {
  getGardenPlan.mockResolvedValue(planResponse({ locations: [bed('loc_b1', 1, 1)] }));
  const store = configureStore({ reducer: { gardenPlan: gardenPlanReducer } });
  await store.dispatch(loadGardenPlan('site_1'));
  return store;
}

beforeEach(() => {
  vi.clearAllMocks();
});

describe('plantIntoSlot', () => {
  it('creates one plant with the slot, its bed and the site, then reads the plan again', async () => {
    const store = await loaded();
    getSlot.mockResolvedValue(slot(false));
    createPlantInstance.mockResolvedValue({ key: 'p_new' } as PlantInstance);
    const outcome = await store.dispatch(plantIntoSlot(ARG));
    expect(outcome).toEqual({ ok: true, plantKey: 'p_new', refreshed: true });
    expect(createPlantInstance).toHaveBeenCalledWith({
      instance_id: 'LACTU-1113-ABC',
      species_key: 'sp_lettuce',
      cultivar_key: null,
      site_key: 'site_1',
      location_key: 'loc_b1',
      slot_key: 'slot_1',
      planted_on: '2026-11-13',
    });
    expect(getGardenPlan).toHaveBeenCalledTimes(2); // load + the read after the write
    expect(applyPlanBatch).not.toHaveBeenCalled(); // no plan operation
  });

  it('offline: nothing is sent and nothing is queued', async () => {
    const store = await loaded();
    store.dispatch(setPlanOffline(true));
    expect(await store.dispatch(plantIntoSlot(ARG))).toEqual({ ok: false, code: 'offline' });
    expect(getSlot).not.toHaveBeenCalled();
    expect(createPlantInstance).not.toHaveBeenCalled();
    expect(selectGardenPlanState(store.getState()).pending).toHaveLength(0);
  });

  it('saves unsaved plan edits first; a save that fails plants nothing', async () => {
    const store = await loaded();
    store.dispatch(applyAction([{ op: 'set_locked', entity: 'location', key: 'loc_b1', locked: true }], null));
    applyPlanBatch.mockRejectedValue(new Error('down'));
    expect(await store.dispatch(plantIntoSlot(ARG))).toEqual({ ok: false, code: 'save_first' });
    expect(createPlantInstance).not.toHaveBeenCalled();

    const revision = selectGardenPlanState(store.getState()).plan!.revision;
    applyPlanBatch.mockResolvedValue({ plan_revision: revision + 1, key_map: {}, updated: [], deleted: [], derived: {} });
    getSlot.mockResolvedValue(slot(false));
    createPlantInstance.mockResolvedValue({ key: 'p_new' } as PlantInstance);
    // A failed save leaves the plan in its failed state: a retry reloads first in the editor; here the save goes again.
    const second = await loaded();
    second.dispatch(applyAction([{ op: 'set_locked', entity: 'location', key: 'loc_b1', locked: true }], null));
    const outcome = await second.dispatch(plantIntoSlot(ARG));
    expect(outcome).toMatchObject({ ok: true, plantKey: 'p_new' });
    expect(applyPlanBatch).toHaveBeenCalledTimes(2);
  });

  it('a slot taken meanwhile is refused before the create, and the plan is read again', async () => {
    const store = await loaded();
    getSlot.mockResolvedValue(slot(true));
    expect(await store.dispatch(plantIntoSlot(ARG))).toEqual({ ok: false, code: 'slot_taken' });
    expect(createPlantInstance).not.toHaveBeenCalled();
    expect(getGardenPlan).toHaveBeenCalledTimes(2);
  });

  it('maps the two refusals the bed dialog can override; anything else carries its error', async () => {
    const store = await loaded();
    getSlot.mockResolvedValue(slot(false));
    createPlantInstance.mockRejectedValueOnce(apiError(422, 'ROTATION_VIOLATION'));
    expect(await store.dispatch(plantIntoSlot(ARG))).toEqual({ ok: false, code: 'rotation' });
    createPlantInstance.mockRejectedValueOnce(apiError(422, 'INCOMPATIBLE_COMPANION'));
    expect(await store.dispatch(plantIntoSlot(ARG))).toEqual({ ok: false, code: 'companion' });
    const other = apiError(409, 'SOMETHING');
    createPlantInstance.mockRejectedValueOnce(other);
    expect(await store.dispatch(plantIntoSlot(ARG))).toEqual({ ok: false, code: 'failed', error: other });
  });
});
