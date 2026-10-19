import { configureStore } from '@reduxjs/toolkit';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { ApiError } from '@/api/errors';
import { planResponse } from '@/test/gardenPlanFixtures';
import * as api from '../api/gardenPlan';
import type { Geometry, PlanBatchResponse, PlanOperation } from '../model/types';
import gardenPlanReducer, {
  applyAction,
  HISTORY_LIMIT,
  loadGardenPlan,
  redo,
  resetGardenPlan,
  saveGardenPlan,
  selectCanRedo,
  selectCanUndo,
  selectInvalidKeys,
  selectIsDirty,
  selectPendingCount,
  clearSelection,
  setSelection,
  setStack,
  setTool,
  undo,
} from './gardenPlanSlice';

vi.mock('../api/gardenPlan', async (importOriginal) => ({
  ...(await importOriginal<typeof import('../api/gardenPlan')>()),
  getGardenPlan: vi.fn(),
  applyPlanBatch: vi.fn(),
}));

const getGardenPlan = vi.mocked(api.getGardenPlan);
const applyPlanBatch = vi.mocked(api.applyPlanBatch);

function makeStore() {
  return configureStore({ reducer: { gardenPlan: gardenPlanReducer } });
}
type Store = ReturnType<typeof makeStore>;

const rect = (x: number, y: number): Geometry => ({
  kind: 'rect',
  origin: [x, y],
  width_m: 1.2,
  length_m: 2,
  rotation_deg: 0,
});
const move = (key: string, x: number, y: number): PlanOperation => ({
  op: 'update_geometry',
  entity: 'location',
  key,
  geometry: rect(x, y),
});

async function loaded(): Promise<Store> {
  getGardenPlan.mockResolvedValue(planResponse());
  const store = makeStore();
  await store.dispatch(loadGardenPlan('site_1'));
  return store;
}

const origin = (store: Store, key: string) => {
  const geometry = store.getState().gardenPlan.plan?.locations[key].geometry;
  return geometry?.kind === 'rect' ? geometry.origin : undefined;
};

function conflictError(): ApiError {
  return new ApiError(
    {
      error_id: 'e1',
      error_code: 'plan.revision_conflict',
      message: 'changed',
      details: [
        {
          field: 'expected_revision',
          reason: 'changed',
          code: 'plan.revision_conflict',
          current_revision: 44,
          changed_by: 'Sabine',
          changed_at: '2026-10-17T09:00:00Z',
        } as never,
      ],
      timestamp: '',
      path: '/plan/batch',
      method: 'POST',
    },
    409,
  );
}

beforeEach(() => {
  vi.resetAllMocks();
});

describe('load', () => {
  it('normalises the plan and starts clean', async () => {
    const store = await loaded();
    const state = store.getState().gardenPlan;
    expect(state.loadStatus).toBe('ready');
    expect(state.plan?.revision).toBe(42);
    expect(selectIsDirty(store.getState())).toBe(false);
    expect(selectCanUndo(store.getState())).toBe(false);
  });

  it('reports a failed load and an unsupported schema version', async () => {
    getGardenPlan.mockResolvedValue(planResponse({ schema_version: '2' }));
    const store = makeStore();
    await store.dispatch(loadGardenPlan('site_1'));
    expect(store.getState().gardenPlan.loadStatus).toBe('error');
    expect(store.getState().gardenPlan.loadError).toContain('schema_version');
    expect(store.getState().gardenPlan.plan).toBeNull();
  });

  it('drops the answer of a load that was overtaken', async () => {
    let releaseFirst: (value: ReturnType<typeof planResponse>) => void = () => undefined;
    getGardenPlan.mockReturnValueOnce(new Promise((resolve) => (releaseFirst = resolve)));
    getGardenPlan.mockResolvedValueOnce(planResponse({ site_key: 'site_2', site_name: 'Second' }));
    const store = makeStore();
    const first = store.dispatch(loadGardenPlan('site_1'));
    await store.dispatch(loadGardenPlan('site_2'));
    releaseFirst(planResponse({ site_key: 'site_1' }));
    await first;
    expect(store.getState().gardenPlan.plan?.siteKey).toBe('site_2');
  });

  it('a reload replaces pending edits and the history', async () => {
    const store = await loaded();
    store.dispatch(applyAction([move('loc_a', 5, 5)]));
    await store.dispatch(loadGardenPlan('site_1'));
    const state = store.getState().gardenPlan;
    expect(state.pending).toEqual([]);
    expect(state.past).toEqual([]);
    expect(origin(store, 'loc_a')).toEqual([1, 1]);
  });
});

describe('GP-ACC-007: undo and redo of a move', () => {
  it('Ctrl+Z puts the bed back and the save status shows 0; Ctrl+Shift+Z moves it again', async () => {
    const store = await loaded();
    store.dispatch(setSelection([{ entity: 'location', key: 'loc_a' }]));
    store.dispatch(applyAction([move('loc_a', 5, 6)], 'move'));
    expect(origin(store, 'loc_a')).toEqual([5, 6]);
    expect(selectPendingCount(store.getState())).toBe(1);
    expect(selectIsDirty(store.getState())).toBe(true);

    store.dispatch(undo());
    expect(origin(store, 'loc_a')).toEqual([1, 1]);
    expect(selectPendingCount(store.getState())).toBe(0);
    expect(selectIsDirty(store.getState())).toBe(false);
    expect(store.getState().gardenPlan.selection).toEqual([{ entity: 'location', key: 'loc_a' }]);
    expect(selectCanRedo(store.getState())).toBe(true);

    store.dispatch(redo());
    expect(origin(store, 'loc_a')).toEqual([5, 6]);
    expect(selectPendingCount(store.getState())).toBe(1);
  });

  it('one user action is one undo step even with several operations (GP-FR-155)', async () => {
    const store = await loaded();
    store.dispatch(applyAction([move('loc_a', 5, 5), move('loc_b', 8, 8)], 'move selection'));
    expect(store.getState().gardenPlan.past).toHaveLength(1);
    expect(selectPendingCount(store.getState())).toBe(2);
    store.dispatch(undo());
    expect(origin(store, 'loc_a')).toEqual([1, 1]);
    expect(origin(store, 'loc_b')).toEqual([4, 1]);
    expect(selectPendingCount(store.getState())).toBe(0);
  });

  it('a new action ends the redo branch', async () => {
    const store = await loaded();
    store.dispatch(applyAction([move('loc_a', 5, 5)]));
    store.dispatch(undo());
    store.dispatch(applyAction([move('loc_b', 9, 9)]));
    expect(selectCanRedo(store.getState())).toBe(false);
  });

  it('keeps only the last HISTORY_LIMIT steps', async () => {
    const store = await loaded();
    for (let i = 0; i < HISTORY_LIMIT + 10; i += 1)
      store.dispatch(applyAction([move('loc_a', i % 50, 1)]));
    expect(store.getState().gardenPlan.past).toHaveLength(HISTORY_LIMIT);
    expect(selectPendingCount(store.getState())).toBe(HISTORY_LIMIT + 10);
  });

  it('refuses an operation the model rejects without touching anything', async () => {
    const store = await loaded();
    store.dispatch(applyAction([move('loc_a', 5, 5), move('ghost', 1, 1)]));
    const state = store.getState().gardenPlan;
    expect(state.editError).toBe('reference.not_found');
    expect(state.pending).toEqual([]);
    expect(state.past).toEqual([]);
    expect(origin(store, 'loc_a')).toEqual([1, 1]);
  });

  it('undo of a created bed removes it again and its operation leaves pending', async () => {
    const store = await loaded();
    store.dispatch(
      applyAction([
        {
          op: 'create_location',
          temp_key: 'tmp1',
          data: { name: 'New', location_type_key: 'bed', geometry: rect(9, 9) },
        },
      ]),
    );
    expect(store.getState().gardenPlan.plan?.locations.tmp1.name).toBe('New');
    store.dispatch(undo());
    expect(store.getState().gardenPlan.plan?.locations.tmp1).toBeUndefined();
    expect(selectPendingCount(store.getState())).toBe(0);
  });

  it('undo of a deleted bed with slots restores bed, slots and plants exactly while unsaved', async () => {
    const store = await loaded();
    const before = store.getState().gardenPlan.plan;
    store.dispatch(applyAction([{ op: 'delete', entity: 'location', key: 'loc_a' }]));
    expect(store.getState().gardenPlan.plan?.slots.slot_1).toBeUndefined();
    store.dispatch(undo());
    expect(store.getState().gardenPlan.plan).toEqual(before);
  });

  it('is blocked and does nothing without a loaded plan', () => {
    const store = makeStore();
    store.dispatch(applyAction([move('loc_a', 5, 5)]));
    store.dispatch(undo());
    store.dispatch(redo());
    expect(store.getState().gardenPlan.plan).toBeNull();
  });
});

describe('save', () => {
  const ok = (overrides: Partial<PlanBatchResponse> = {}): PlanBatchResponse => ({
    plan_revision: 43,
    key_map: {},
    updated: [],
    deleted: [],
    derived: {},
    ...overrides,
  });

  it('sends pending with expected_revision, adopts the new revision and empties pending', async () => {
    const store = await loaded();
    store.dispatch(applyAction([move('loc_a', 5, 5)]));
    applyPlanBatch.mockResolvedValue(ok());
    await store.dispatch(saveGardenPlan());
    expect(applyPlanBatch).toHaveBeenCalledWith('site_1', {
      expected_revision: 42,
      operations: [move('loc_a', 5, 5)],
    });
    const state = store.getState().gardenPlan;
    expect(state.plan?.revision).toBe(43);
    expect(state.plan?.settings?.plan_revision).toBe(43);
    expect(state.saveStatus).toBe('idle');
    expect(selectIsDirty(store.getState())).toBe(false);
    expect(state.past).toHaveLength(1); // the stack survives a successful save (GP-FR-026)
  });

  it('does nothing when nothing is pending', async () => {
    const store = await loaded();
    await store.dispatch(saveGardenPlan());
    expect(applyPlanBatch).not.toHaveBeenCalled();
  });

  it('resolves temp keys and takes over derived values', async () => {
    const store = await loaded();
    store.dispatch(setSelection([]));
    store.dispatch(
      applyAction([
        {
          op: 'create_location',
          temp_key: 'tmp1',
          data: { name: 'New', location_type_key: 'bed', geometry: rect(9, 9) },
        },
        {
          op: 'create_location',
          temp_key: 'tmp2',
          data: {
            name: 'Child',
            location_type_key: 'bed',
            parent_location_key: 'tmp1',
            geometry: rect(9, 9),
          },
        },
      ]),
    );
    store.dispatch(setSelection([{ entity: 'location', key: 'tmp1' }]));
    applyPlanBatch.mockResolvedValue(
      ok({
        key_map: { tmp1: 'loc_n1', tmp2: 'loc_n2' },
        derived: { loc_n1: { area_m2: 2.4, bbox: [9, 9, 10.2, 11] } },
      }),
    );
    await store.dispatch(saveGardenPlan());
    const plan = store.getState().gardenPlan.plan!;
    expect(Object.keys(plan.locations).sort()).toEqual(['loc_a', 'loc_b', 'loc_n1', 'loc_n2']);
    expect(plan.locations.loc_n1.key).toBe('loc_n1');
    expect(plan.locations.loc_n2.parent_location_key).toBe('loc_n1');
    expect(plan.locations.loc_n1.bbox).toEqual([9, 9, 10.2, 11]);
    expect(store.getState().gardenPlan.selection).toEqual([{ entity: 'location', key: 'loc_n1' }]);
  });

  it('after a save, undo queues the counter-operation and makes the plan dirty again (GP-FR-155)', async () => {
    const store = await loaded();
    store.dispatch(applyAction([move('loc_a', 5, 5)]));
    applyPlanBatch.mockResolvedValue(ok());
    await store.dispatch(saveGardenPlan());

    store.dispatch(undo());
    expect(origin(store, 'loc_a')).toEqual([1, 1]);
    expect(store.getState().gardenPlan.pending.map((item) => item.op)).toEqual([
      move('loc_a', 1, 1),
    ]);
    expect(selectIsDirty(store.getState())).toBe(true);

    store.dispatch(redo());
    expect(origin(store, 'loc_a')).toEqual([5, 5]);
    expect(selectPendingCount(store.getState())).toBe(2); // counter-operation, then the move again
  });

  it('keeps the key of an undone create valid across a save (undo, then redo the delete)', async () => {
    const store = await loaded();
    store.dispatch(
      applyAction([
        {
          op: 'create_location',
          temp_key: 'tmp1',
          data: { name: 'New', location_type_key: 'bed', geometry: rect(9, 9) },
        },
      ]),
    );
    applyPlanBatch.mockResolvedValue(ok({ key_map: { tmp1: 'loc_n1' } }));
    await store.dispatch(saveGardenPlan());
    store.dispatch(undo());
    expect(store.getState().gardenPlan.pending.map((item) => item.op)).toEqual([
      { op: 'delete', entity: 'location', key: 'loc_n1' },
    ]);
    expect(store.getState().gardenPlan.plan?.locations.loc_n1).toBeUndefined();
  });

  it('refuses the undo of a saved step that has no wire inverse', async () => {
    const store = await loaded();
    store.dispatch(applyAction([{ op: 'delete', entity: 'location', key: 'loc_a' }])); // holds a plant
    applyPlanBatch.mockResolvedValue(ok());
    await store.dispatch(saveGardenPlan());
    store.dispatch(undo());
    const state = store.getState().gardenPlan;
    expect(state.editError).toBe('undo.not_reversible');
    expect(state.past).toHaveLength(1);
    expect(state.pending).toEqual([]);
  });

  it('is read-only while a save is in flight', async () => {
    const store = await loaded();
    store.dispatch(applyAction([move('loc_a', 5, 5)]));
    let finish: (value: PlanBatchResponse) => void = () => undefined;
    applyPlanBatch.mockReturnValue(new Promise((resolve) => (finish = resolve)));
    const saving = store.dispatch(saveGardenPlan());
    expect(store.getState().gardenPlan.saveStatus).toBe('saving');
    store.dispatch(applyAction([move('loc_b', 9, 9)]));
    store.dispatch(undo());
    expect(selectCanUndo(store.getState())).toBe(false);
    expect(selectPendingCount(store.getState())).toBe(1);
    finish(ok());
    await saving;
    expect(store.getState().gardenPlan.saveStatus).toBe('idle');
  });

  it('409 plan.revision_conflict keeps pending, empties the history and opens the conflict (GP-NFR-006, GP-FR-026)', async () => {
    const store = await loaded();
    store.dispatch(applyAction([move('loc_a', 5, 5)]));
    applyPlanBatch.mockRejectedValue(conflictError());
    await store.dispatch(saveGardenPlan());
    const state = store.getState().gardenPlan;
    expect(state.saveStatus).toBe('conflict');
    expect(state.conflict).toEqual({
      currentRevision: 44,
      changedBy: 'Sabine',
      changedAt: '2026-10-17T09:00:00Z',
    });
    expect(state.pending).toHaveLength(1);
    expect(state.past).toEqual([]);
    expect(state.future).toEqual([]);
    expect(origin(store, 'loc_a')).toEqual([5, 5]);

    // Neither editing nor saving the stale request again until the user reloads.
    store.dispatch(applyAction([move('loc_b', 9, 9)]));
    expect(selectPendingCount(store.getState())).toBe(1);
    await store.dispatch(saveGardenPlan());
    expect(applyPlanBatch).toHaveBeenCalledTimes(1);

    getGardenPlan.mockResolvedValue(planResponse({ plan_revision: 44 }));
    await store.dispatch(loadGardenPlan('site_1'));
    const reloaded = store.getState().gardenPlan;
    expect(reloaded.saveStatus).toBe('idle');
    expect(reloaded.conflict).toBeNull();
    expect(reloaded.pending).toEqual([]);
    expect(reloaded.plan?.revision).toBe(44);
  });

  it('keeps pending and the history on a refusal that is not a conflict', async () => {
    const store = await loaded();
    store.dispatch(applyAction([move('loc_a', 5, 5)]));
    applyPlanBatch.mockRejectedValue(
      new ApiError(
        {
          error_id: 'e2',
          error_code: 'geometry.outside_parent',
          message: 'outside',
          details: [
            {
              field: 'geometry',
              reason: 'outside',
              code: 'geometry.outside_parent',
              op_index: 0,
            } as never,
          ],
          timestamp: '',
          path: '',
          method: 'POST',
        },
        422,
      ),
    );
    await store.dispatch(saveGardenPlan());
    const state = store.getState().gardenPlan;
    expect(state.saveStatus).toBe('error');
    expect(state.saveFailure).toEqual({
      kind: 'rejected',
      status: 422,
      code: 'geometry.outside_parent',
      findings: [{ opIndex: 0, field: 'geometry', code: 'geometry.outside_parent' }],
    });
    expect(state.pending).toHaveLength(1);
    expect(state.past).toHaveLength(1);
    // A failed save can be retried.
    applyPlanBatch.mockResolvedValue(ok());
    await store.dispatch(saveGardenPlan());
    expect(store.getState().gardenPlan.saveStatus).toBe('idle');
  });

  it('names the objects a refusal points at, only while the refusal stands (GP-UX-017)', async () => {
    const store = await loaded();
    store.dispatch(applyAction([move('loc_a', 5, 5)]));
    applyPlanBatch.mockRejectedValue(
      new ApiError(
        {
          error_id: 'e3',
          error_code: 'geometry.outside_parent',
          message: 'outside',
          details: [{ field: 'geometry', reason: 'outside', code: 'geometry.outside_parent', op_index: 0 } as never],
          timestamp: '',
          path: '',
          method: 'POST',
        },
        422,
      ),
    );
    await store.dispatch(saveGardenPlan());
    expect(store.getState().gardenPlan.saveFailureOpIds).toHaveLength(1);
    expect([...selectInvalidKeys(store.getState())]).toEqual(['loc_a']);
    // The same set instance while nothing changed: the renderer redraws on identity.
    expect(selectInvalidKeys(store.getState())).toBe(selectInvalidKeys(store.getState()));

    // Undoing the refused change takes its outline away; another object's pending edit does not inherit it.
    store.dispatch(applyAction([move('loc_b', 3, 3)]));
    expect([...selectInvalidKeys(store.getState())]).toEqual(['loc_a']);
    store.dispatch(undo());
    store.dispatch(undo());
    expect(selectInvalidKeys(store.getState()).size).toBe(0);
    store.dispatch(redo());
    store.dispatch(redo());

    // Retrying clears the outline; a network failure names no object.
    applyPlanBatch.mockRejectedValue(new Error('Network Error'));
    await store.dispatch(saveGardenPlan());
    expect(store.getState().gardenPlan.saveFailureOpIds).toEqual([]);
    expect(selectInvalidKeys(store.getState()).size).toBe(0);
  });

  it('turns a network failure into a plain failed state', async () => {
    const store = await loaded();
    store.dispatch(applyAction([move('loc_a', 5, 5)]));
    applyPlanBatch.mockRejectedValue(new Error('Network Error'));
    await store.dispatch(saveGardenPlan());
    expect(store.getState().gardenPlan.saveFailure).toEqual({
      kind: 'failed',
      message: 'Network Error',
    });
  });

  it('never splits a batch: more than 500 operations are refused before the request', async () => {
    const store = await loaded();
    for (let i = 0; i < 501; i += 1) store.dispatch(applyAction([move('loc_a', i % 50, 1)]));
    await store.dispatch(saveGardenPlan());
    expect(applyPlanBatch).not.toHaveBeenCalled();
    expect(store.getState().gardenPlan.saveFailure).toMatchObject({
      code: 'batch.too_many_operations',
    });
  });
});

describe('tool, selection and reset', () => {
  it('holds tool and selection and forgets everything on reset', async () => {
    const store = await loaded();
    store.dispatch(setTool('bed'));
    store.dispatch(setSelection([{ entity: 'garden_object', key: 'go_1' }]));
    expect(store.getState().gardenPlan.tool).toBe('bed');
    store.dispatch(resetGardenPlan());
    expect(store.getState().gardenPlan.plan).toBeNull();
    expect(store.getState().gardenPlan.tool).toBe('select');
    expect(store.getState().gardenPlan.selection).toEqual([]);
  });

  it('drops a selected entity that an action removed', async () => {
    const store = await loaded();
    store.dispatch(setSelection([{ entity: 'garden_object', key: 'go_1' }]));
    store.dispatch(applyAction([{ op: 'delete', entity: 'garden_object', key: 'go_1' }]));
    expect(store.getState().gardenPlan.selection).toEqual([]);
  });

  it('keeps the stack under the last click (GP-UX-033) until the selection is cleared or the plan changes', async () => {
    const store = await loaded();
    const stack = { keys: ['loc_a', 'loc_b'], index: 0, pointPx: [10, 20] as [number, number] };
    store.dispatch(setStack(stack));
    expect(store.getState().gardenPlan.stack).toEqual(stack);
    store.dispatch(clearSelection());
    expect(store.getState().gardenPlan.stack).toBeNull();

    store.dispatch(setStack(stack));
    store.dispatch(applyAction([move('loc_a', 5, 5)]));
    expect(store.getState().gardenPlan.stack).toBeNull(); // the objects under it moved
    store.dispatch(setStack(stack));
    store.dispatch(undo());
    expect(store.getState().gardenPlan.stack).toBeNull();
  });
});
