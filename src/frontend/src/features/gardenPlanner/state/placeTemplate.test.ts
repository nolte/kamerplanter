import { configureStore } from '@reduxjs/toolkit';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { ApiError } from '@/api/errors';
import { planResponse } from '@/test/gardenPlanFixtures';
import * as api from '../api/gardenPlan';
import type { PlanBatchResponse } from '../model/types';
import gardenPlanReducer, {
  applyAction,
  loadGardenPlan,
  placeTemplateAt,
  selectGardenPlanState,
} from './gardenPlanSlice';

vi.mock('../api/gardenPlan', async (importOriginal) => ({
  ...(await importOriginal<typeof import('../api/gardenPlan')>()),
  getGardenPlan: vi.fn(),
  applyPlanBatch: vi.fn(),
  placeBedTemplate: vi.fn(),
}));

const getGardenPlan = vi.mocked(api.getGardenPlan);
const applyPlanBatch = vi.mocked(api.applyPlanBatch);
const placeBedTemplate = vi.mocked(api.placeBedTemplate);

const ARG = { templateKey: 'sys_bed_2x1', origin: [4, 1] as [number, number], rotationDeg: 90 };
const placed: PlanBatchResponse = {
  plan_revision: 8,
  key_map: { template_bed: 'loc_new' },
  updated: [],
  deleted: [],
  derived: {},
};

function apiError(status: number, code: string, details: Record<string, unknown>[]): ApiError {
  return new ApiError(
    {
      error_id: 'e1',
      error_code: code,
      message: code,
      details: details as never,
      timestamp: '',
      path: '/plan/place-template',
      method: 'POST',
    },
    status,
  );
}

async function loaded() {
  getGardenPlan.mockResolvedValue(planResponse());
  const store = configureStore({ reducer: { gardenPlan: gardenPlanReducer } });
  await store.dispatch(loadGardenPlan('site_1'));
  return store;
}

beforeEach(() => {
  vi.clearAllMocks();
});

describe('placeTemplateAt (GP-FR-044)', () => {
  it('sends the template, the point, the turn and the loaded revision, then refreshes the plan', async () => {
    const store = await loaded();
    const revision = selectGardenPlanState(store.getState()).plan!.revision;
    placeBedTemplate.mockResolvedValue(placed);
    const outcome = await store.dispatch(placeTemplateAt(ARG));
    expect(outcome.payload).toEqual({ ok: true, locationKey: 'loc_new' });
    expect(placeBedTemplate).toHaveBeenCalledWith('site_1', {
      template_key: 'sys_bed_2x1',
      origin: [4, 1],
      rotation_deg: 90,
      expected_revision: revision,
    });
    expect(getGardenPlan).toHaveBeenCalledTimes(2); // load + refresh
    expect(selectGardenPlanState(store.getState()).loadStatus).toBe('ready');
  });

  it('saves unsaved edits first and places on the revision the save returned', async () => {
    const store = await loaded();
    const plan = selectGardenPlanState(store.getState()).plan!;
    const key = Object.keys(plan.locations)[0];
    store.dispatch(
      applyAction([{ op: 'set_locked', entity: 'location', key, locked: true }], null),
    );
    applyPlanBatch.mockResolvedValue({
      plan_revision: plan.revision + 1,
      key_map: {},
      updated: [],
      deleted: [],
      derived: {},
    });
    placeBedTemplate.mockResolvedValue(placed);
    await store.dispatch(placeTemplateAt(ARG));
    expect(applyPlanBatch).toHaveBeenCalledTimes(1);
    expect(placeBedTemplate.mock.calls[0][1].expected_revision).toBe(plan.revision + 1);
  });

  it('places nothing when the save of the unsaved edits fails', async () => {
    const store = await loaded();
    const key = Object.keys(selectGardenPlanState(store.getState()).plan!.locations)[0];
    store.dispatch(
      applyAction([{ op: 'set_locked', entity: 'location', key, locked: true }], null),
    );
    applyPlanBatch.mockRejectedValue(new Error('offline'));
    const outcome = await store.dispatch(placeTemplateAt(ARG));
    expect(outcome.payload).toEqual({ ok: false, code: 'template.save_first' });
    expect(placeBedTemplate).not.toHaveBeenCalled();
  });

  it('reports a refusal by the published code of its first finding', async () => {
    const store = await loaded();
    placeBedTemplate.mockRejectedValue(
      apiError(422, 'validation_error', [
        { field: 'geometry', code: 'geometry.outside_parent', reason: 'outside' },
      ]),
    );
    const outcome = await store.dispatch(placeTemplateAt(ARG));
    expect(outcome.payload).toEqual({ ok: false, code: 'geometry.outside_parent' });
  });

  it('refreshes the plan on a revision conflict and asks the user to place again', async () => {
    const store = await loaded();
    placeBedTemplate.mockRejectedValue(
      apiError(409, 'plan.revision_conflict', [{ current_revision: 9 }]),
    );
    const outcome = await store.dispatch(placeTemplateAt(ARG));
    expect(outcome.payload).toEqual({ ok: false, code: 'plan.revision_conflict' });
    expect(getGardenPlan).toHaveBeenCalledTimes(2);
  });
});
