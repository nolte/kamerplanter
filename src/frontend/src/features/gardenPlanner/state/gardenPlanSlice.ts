/**
 * `gardenPlanSlice` - the state of the garden plan editor (REQ-053 GP-NFR-005..007, GP-FR-026/155).
 *
 * One slice, RTK `createSlice` with thunks for load and save (no RTK Query - the existing pattern).
 * The plan is held normalised; every edit is a list of `PlanOperation`s applied optimistically to
 * the model (`applyOperations`) and queued in `pending` for the next save:
 *
 * - **Undo/redo** (`past[]` / `future[]`): one history entry = one user action (GP-FR-155). Undoing
 *   an action that is still unsaved restores the touched entities and removes its operations from
 *   `pending`; undoing a saved one applies the inverse operations and queues them (dirty again).
 * - **Dirty** = `pending.length > 0`.
 * - **Save** sends `pending` with `expected_revision`; 2xx adopts `plan_revision`, resolves the temp
 *   keys and empties `pending`; 409 `plan.revision_conflict` keeps `pending`, empties the history
 *   (GP-FR-026) and enters the conflict state, which only a reload leaves.
 * - While a save is in flight or a conflict is open the plan is read-only for edits: there is no
 *   defined merge of an action with a request on the wire, and the revision the next save expects
 *   is not known yet.
 *
 * Not part of the initial bundle: the plan route injects it into the root reducer when it loads
 * (`registerLazySlice(gardenPlanSlice)`, REQ-053 WP 2.3). Until then `state.gardenPlan` is
 * absent, which is why the selectors fall back to the initial state.
 */
import { createAsyncThunk, createSelector, createSlice, original, type PayloadAction } from '@reduxjs/toolkit';
import {
  applyOperations,
  PlanOperationError,
  remapOperationKeys,
  type PlanOperationErrorCode,
} from '../model/applyOperation';
import { applyDerived, applyKeyMap, normalizePlan, type PlanModel } from '../model/planModel';
import { MAX_BATCH_OPERATIONS, type PlanEntity, type PlanOperation } from '../model/types';
import { applyUndoPatch, diffPlans, type UndoPatch } from '../model/undoPatch';
import * as api from '../api/gardenPlan';
import type { PlanSaveFailure } from '../api/gardenPlan';

/** Undo steps kept (GP-FR-026 asks for at least 50). */
export const HISTORY_LIMIT = 100;

/** The toolbar of GP-UX-001: at most eight tools on the top level. */
export type PlanTool =
  'select' | 'pan' | 'bed' | 'area' | 'garden_object' | 'plant' | 'measure' | 'label';

export interface SelectionRef {
  entity: PlanEntity | 'slot' | 'plant';
  key: string;
}

/**
 * The objects under the last click and the one that is selected from them (GP-UX-033): a repeated
 * click on the same spot walks down it. The panel list "Objekte an dieser Stelle (n)" reads it
 * (WP 2.6); `pointPx` is the click in canvas pixels.
 */
export interface SelectionStack {
  keys: string[];
  index: number;
  pointPx: [number, number];
}

/** An operation waiting for the next save. */
export interface PendingOperation {
  id: number;
  op: PlanOperation;
}

/** Ids of the pending operations a refusal's findings name; `sent` operations of `pending` were on the wire. */
function failedOpIds(
  failure: Exclude<PlanSaveFailure, { kind: 'conflict' }>,
  pending: readonly PendingOperation[],
  sent: number,
): number[] {
  if (failure.kind !== 'rejected') return [];
  const ids = new Set<number>();
  for (const finding of failure.findings) {
    if (finding.opIndex === null || finding.opIndex >= sent) continue;
    const item = pending[finding.opIndex];
    if (item) ids.add(item.id);
  }
  return [...ids];
}

/** One user action (GP-FR-155). */
export interface HistoryEntry {
  id: number;
  /** For the undo/redo tooltips ("Beet verschieben"); a translation key or plain text of the caller. */
  label: string | null;
  ops: PlanOperation[];
  /** Operations that undo `ops` once saved; `null` = not representable (undo only while pending). */
  inverse: PlanOperation[] | null;
  /** Restores the touched entities; present only while the action is unsaved. */
  undo: UndoPatch | null;
  /** The `pending` items this action produced; empty once saved. */
  pendingIds: number[];
}

export type LoadStatus = 'idle' | 'loading' | 'ready' | 'error';
export type SaveStatus = 'idle' | 'saving' | 'conflict' | 'error';

export interface PlanConflict {
  currentRevision: number | null;
  /** Display name of the last editor (§22.1), never an account key. */
  changedBy: string | null;
  changedAt: string | null;
}

/** Why an edit, undo or redo did nothing. */
export type PlanEditError = PlanOperationErrorCode | 'undo.not_reversible' | 'redo.failed';

export interface GardenPlanState {
  plan: PlanModel | null;
  loadStatus: LoadStatus;
  loadError: string | null;
  loadRequestId: string | null;
  selection: SelectionRef[];
  stack: SelectionStack | null;
  tool: PlanTool;
  past: HistoryEntry[];
  future: HistoryEntry[];
  pending: PendingOperation[];
  saveStatus: SaveStatus;
  /** The refusal of the last save that was not a conflict. */
  saveFailure: Exclude<PlanSaveFailure, { kind: 'conflict' }> | null;
  /** Ids of the pending operations a refusal's findings name (GP-UX-017); their objects are drawn with a red outline. */
  saveFailureOpIds: number[];
  conflict: PlanConflict | null;
  /** How many `pending` operations the request on the wire carries. */
  inFlight: number;
  editError: PlanEditError | null;
  /** Source of entry and pending ids. */
  sequence: number;
}

export const initialState: GardenPlanState = {
  plan: null,
  loadStatus: 'idle',
  loadError: null,
  loadRequestId: null,
  selection: [],
  stack: null,
  tool: 'select',
  past: [],
  future: [],
  pending: [],
  saveStatus: 'idle',
  saveFailure: null,
  saveFailureOpIds: [],
  conflict: null,
  inFlight: 0,
  editError: null,
  sequence: 0,
};

// ── Thunks ───────────────────────────────────────────────────────────────────

/** Load (or reload) the plan of a site; replaces the model, `pending` and the history. */
export const loadGardenPlan = createAsyncThunk<PlanModel, string, { rejectValue: string }>(
  'gardenPlan/load',
  async (siteKey, { rejectWithValue }) => {
    try {
      return normalizePlan(await api.getGardenPlan(siteKey));
    } catch (error) {
      return rejectWithValue(error instanceof Error ? error.message : 'Unknown error');
    }
  },
);

/**
 * Re-read the plan after the server changed it behind the editor's back (a placed template, GP-FR-044): the
 * model is replaced and the history emptied like on a load, but `loadStatus` stays `ready` and `loadRequestId`
 * stays put, so the editor is not unmounted and the view does not jump back to the fitted one.
 */
export const refreshGardenPlan = createAsyncThunk<PlanModel, string, { rejectValue: string }>(
  'gardenPlan/refresh',
  async (siteKey, { rejectWithValue }) => {
    try {
      return normalizePlan(await api.getGardenPlan(siteKey));
    } catch (error) {
      return rejectWithValue(error instanceof Error ? error.message : 'Unknown error');
    }
  },
);

interface SaveResult {
  response: Awaited<ReturnType<typeof api.applyPlanBatch>>;
}

/** Send `pending` with `expected_revision` (GP-NFR-006). */
export const saveGardenPlan = createAsyncThunk<
  SaveResult,
  void,
  // The slice is injected lazily, so the root state may not carry it yet (see the selectors).
  { state: { gardenPlan?: GardenPlanState }; rejectValue: PlanSaveFailure }
>(
  'gardenPlan/save',
  async (_arg, { getState, rejectWithValue }) => {
    const { plan, pending } = selectGardenPlanState(getState());
    if (plan === null) return rejectWithValue({ kind: 'failed', message: 'No plan loaded.' });
    if (pending.length > MAX_BATCH_OPERATIONS) {
      // V-17: a batch is all-or-nothing, so it is never split into several requests.
      return rejectWithValue({
        kind: 'rejected',
        status: 422,
        code: 'batch.too_many_operations',
        findings: [],
      });
    }
    try {
      const response = await api.applyPlanBatch(plan.siteKey, {
        expected_revision: plan.revision,
        operations: pending.map((item) => item.op),
      });
      return { response };
    } catch (error) {
      return rejectWithValue(api.toPlanSaveFailure(error));
    }
  },
  {
    condition: (_arg, { getState }) => {
      const { plan, pending, saveStatus } = selectGardenPlanState(getState());
      // A conflict is left by reloading, never by sending the same stale request again.
      if (plan === null || pending.length === 0) return false;
      return saveStatus !== 'saving' && saveStatus !== 'conflict';
    },
  },
);

/** The server-side placement of a bed template (GP-FR-044, WP 7.10). */
export interface PlaceTemplateArg {
  templateKey: string;
  origin: [number, number];
  rotationDeg: number;
}

/** `code` is a `notice.*` key of the editor: a server code (`bed.overlap`, ...) or one of the `template.*` codes. */
export type PlaceTemplateOutcome = { ok: true; locationKey: string | null } | { ok: false; code: string };

/**
 * Place a bed from a template. The server creates the bed in its own transaction (`POST .../plan/place-template`)
 * and the model learns of it by a refresh, so unsaved edits are saved first: a request that carries only the
 * template could not be ordered after them. A save that does not go through ends the placement before anything
 * is created. The placement is saved at once and is not an undo step (the history is emptied by the refresh).
 */
export const placeTemplateAt = createAsyncThunk<
  PlaceTemplateOutcome,
  PlaceTemplateArg,
  { state: { gardenPlan?: GardenPlanState } }
>('gardenPlan/placeTemplate', async (arg, { getState, dispatch }) => {
  let current = selectGardenPlanState(getState());
  if (current.plan === null) return { ok: false, code: 'template.failed' };
  if (current.saveStatus === 'saving' || current.saveStatus === 'conflict') {
    return { ok: false, code: 'template.busy' };
  }
  if (current.pending.length > 0) {
    await dispatch(saveGardenPlan());
    current = selectGardenPlanState(getState());
    if (current.plan === null || current.pending.length > 0 || current.saveStatus !== 'idle') {
      return { ok: false, code: 'template.save_first' };
    }
  }
  const { siteKey, revision } = current.plan;
  try {
    const response = await api.placeBedTemplate(siteKey, {
      template_key: arg.templateKey,
      origin: arg.origin,
      rotation_deg: arg.rotationDeg,
      expected_revision: revision,
    });
    await dispatch(refreshGardenPlan(siteKey));
    return { ok: true, locationKey: response.key_map.template_bed ?? null };
  } catch (error) {
    const failure = api.toPlanSaveFailure(error);
    if (failure.kind === 'conflict') {
      // Someone else changed the plan: show what is there now, then the user places again.
      await dispatch(refreshGardenPlan(siteKey));
      return { ok: false, code: 'plan.revision_conflict' };
    }
    if (failure.kind === 'rejected') {
      return { ok: false, code: failure.findings[0]?.code || failure.code };
    }
    return { ok: false, code: 'template.failed' };
  }
});

// ── Reducer helpers ──────────────────────────────────────────────────────────

/** The plain model behind the draft: pure model code must never see an Immer proxy. */
function plainPlan(state: GardenPlanState): PlanModel | null {
  return state.plan === null ? null : (original(state.plan) ?? state.plan);
}

function isEditable(state: GardenPlanState): boolean {
  return state.plan !== null && state.saveStatus !== 'saving' && state.saveStatus !== 'conflict';
}

function queue(state: GardenPlanState, ops: readonly PlanOperation[]): number[] {
  const ids: number[] = [];
  for (const op of ops) {
    state.sequence += 1;
    state.pending.push({ id: state.sequence, op });
    ids.push(state.sequence);
  }
  return ids;
}

function dropSelectionOfMissing(state: GardenPlanState): void {
  const plan = state.plan;
  if (plan === null) return;
  state.selection = state.selection.filter(({ entity, key }) => {
    if (entity === 'location') return key in plan.locations;
    if (entity === 'garden_object') return key in plan.gardenObjects;
    if (entity === 'slot') return key in plan.slots;
    return key in plan.plants;
  });
}

function errorCodeOf(error: unknown): PlanEditError {
  return error instanceof PlanOperationError ? error.code : 'operation.unsupported';
}

// ── Slice ────────────────────────────────────────────────────────────────────

export const gardenPlanSlice = createSlice({
  name: 'gardenPlan',
  initialState,
  reducers: {
    setTool(state, action: PayloadAction<PlanTool>) {
      state.tool = action.payload;
    },
    setSelection(state, action: PayloadAction<SelectionRef[]>) {
      state.selection = action.payload;
    },
    clearSelection(state) {
      state.selection = [];
      state.stack = null;
    },
    setStack(state, action: PayloadAction<SelectionStack | null>) {
      state.stack = action.payload;
    },
    clearEditError(state) {
      state.editError = null;
    },
    /** Leave the editor: forget the plan, the history and everything pending. */
    resetGardenPlan() {
      return initialState;
    },

    /**
     * One user action: apply `ops` to the model now and queue them for the next save. All or
     * nothing - an operation the model refuses leaves everything as it was and sets `editError`.
     * A new action ends the redo branch. The operations (and the geometries in them) become part of
     * the store and are frozen by Immer: build a fresh object for the next drag step, never reuse one.
     */
    applyAction: {
      reducer(state, action: PayloadAction<{ ops: PlanOperation[]; label: string | null }>) {
        const plan = plainPlan(state);
        const { ops, label } = action.payload;
        if (plan === null || !isEditable(state) || ops.length === 0) return;
        try {
          const applied = applyOperations(plan, ops);
          state.sequence += 1;
          const entryId = state.sequence;
          state.past.push({
            id: entryId,
            label,
            ops,
            inverse: applied.inverse,
            undo: diffPlans(plan, applied.plan),
            pendingIds: queue(state, ops),
          });
          if (state.past.length > HISTORY_LIMIT)
            state.past.splice(0, state.past.length - HISTORY_LIMIT);
          state.future = [];
          state.plan = applied.plan;
          state.editError = null;
          state.stack = null; // the objects under the old click may have moved
          dropSelectionOfMissing(state);
        } catch (error) {
          state.editError = errorCodeOf(error);
        }
      },
      prepare(ops: PlanOperation[], label: string | null = null) {
        return { payload: { ops, label } };
      },
    },

    undo(state) {
      const plan = plainPlan(state);
      if (plan === null || !isEditable(state) || state.past.length === 0) return;
      const entry = original(state.past)![state.past.length - 1];
      if (entry.undo !== null) {
        // Still unsaved: restore the entities and take the operations back out of `pending`.
        const gone = new Set(entry.pendingIds);
        state.pending = state.pending.filter((item) => !gone.has(item.id));
        state.plan = applyUndoPatch(plan, entry.undo);
      } else {
        // Saved: the counter-operations make the plan dirty again (GP-FR-155).
        if (entry.inverse === null) {
          state.editError = 'undo.not_reversible';
          return;
        }
        try {
          state.plan = applyOperations(plan, entry.inverse).plan;
        } catch (error) {
          state.editError = errorCodeOf(error);
          return;
        }
        queue(state, entry.inverse);
      }
      state.past.pop();
      state.future.push({ ...entry, undo: null, pendingIds: [] });
      state.editError = null;
      state.stack = null; // the objects under the old click may have moved
      dropSelectionOfMissing(state);
    },

    redo(state) {
      const plan = plainPlan(state);
      if (plan === null || !isEditable(state) || state.future.length === 0) return;
      const entry = original(state.future)![state.future.length - 1];
      try {
        const applied = applyOperations(plan, entry.ops);
        state.future.pop();
        state.past.push({
          ...entry,
          inverse: applied.inverse,
          undo: diffPlans(plan, applied.plan),
          pendingIds: queue(state, entry.ops),
        });
        state.plan = applied.plan;
        state.editError = null;
        state.stack = null; // the objects under the old click may have moved
        dropSelectionOfMissing(state);
      } catch {
        // The plan moved on (an entity the redo needs is gone): the redo branch is stale.
        state.future = [];
        state.editError = 'redo.failed';
      }
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(loadGardenPlan.pending, (state, action) => {
        state.loadStatus = 'loading';
        state.loadError = null;
        state.loadRequestId = action.meta.requestId;
      })
      .addCase(loadGardenPlan.fulfilled, (state, action) => {
        // Only the newest request counts: a slow answer for a site the user already left is dropped.
        if (action.meta.requestId !== state.loadRequestId) return;
        state.plan = action.payload;
        state.loadStatus = 'ready';
        state.past = [];
        state.future = [];
        state.pending = [];
        state.saveStatus = 'idle';
        state.saveFailure = null;
        state.saveFailureOpIds = [];
        state.conflict = null;
        state.inFlight = 0;
        state.editError = null;
        state.stack = null;
        dropSelectionOfMissing(state);
      })
      .addCase(loadGardenPlan.rejected, (state, action) => {
        if (action.meta.requestId !== state.loadRequestId) return;
        state.loadStatus = 'error';
        state.loadError = action.payload ?? action.error.message ?? 'Unknown error';
      })

      .addCase(refreshGardenPlan.fulfilled, (state, action) => {
        // Nothing may be pending here (the caller saved first); an edit made since stays where it is.
        if (state.pending.length > 0 || state.saveStatus === 'saving') return;
        state.plan = action.payload;
        state.past = [];
        state.future = [];
        state.saveStatus = 'idle';
        state.saveFailure = null;
        state.saveFailureOpIds = [];
        state.conflict = null;
        state.inFlight = 0;
        state.editError = null;
        state.stack = null;
        dropSelectionOfMissing(state);
      })

      .addCase(saveGardenPlan.pending, (state) => {
        state.saveStatus = 'saving';
        state.saveFailure = null;
        state.saveFailureOpIds = [];
        state.inFlight = state.pending.length;
      })
      .addCase(saveGardenPlan.fulfilled, (state, action) => {
        const plan = plainPlan(state);
        const { response } = action.payload;
        if (plan === null) return;
        const { key_map: keyMap } = response;
        let next = applyKeyMap({ ...plan, revision: response.plan_revision }, keyMap);
        next = applyDerived(next, response.derived);
        if (next.settings)
          next = { ...next, settings: { ...next.settings, plan_revision: response.plan_revision } };
        state.plan = next;
        state.pending = state.pending
          .slice(state.inFlight)
          .map((item) => ({ ...item, op: remapOperationKeys(item.op, keyMap) }));
        // Everything saved is a baseline now: undo goes through counter-operations from here on.
        const rebase = (entry: HistoryEntry): HistoryEntry => ({
          ...entry,
          ops: entry.ops.map((op) => remapOperationKeys(op, keyMap)),
          inverse: entry.inverse && entry.inverse.map((op) => remapOperationKeys(op, keyMap)),
          undo: null,
          pendingIds: [],
        });
        state.past = state.past.map(rebase);
        state.future = state.future.map(rebase);
        state.selection = state.selection.map((ref) =>
          ref.entity === 'location' || ref.entity === 'garden_object'
            ? { ...ref, key: keyMap[ref.key] ?? ref.key }
            : ref,
        );
        state.saveStatus = 'idle';
        state.inFlight = 0;
        dropSelectionOfMissing(state);
      })
      .addCase(saveGardenPlan.rejected, (state, action) => {
        // A save the `condition` skipped never reached `pending`: nothing to undo here.
        if (action.meta.condition) return;
        const sent = state.inFlight;
        state.inFlight = 0;
        const failure = action.payload ?? {
          kind: 'failed' as const,
          message: action.error.message ?? 'Unknown error',
        };
        if (failure.kind === 'conflict') {
          // `pending` stays (GP-NFR-006); the history is emptied and the user informed (GP-FR-026).
          state.saveStatus = 'conflict';
          state.conflict = {
            currentRevision: failure.currentRevision,
            changedBy: failure.changedBy,
            changedAt: failure.changedAt,
          };
          state.past = [];
          state.future = [];
          return;
        }
        state.saveStatus = 'error';
        state.saveFailure = failure;
        state.saveFailureOpIds = failedOpIds(failure, state.pending, sent);
      });
  },
});

export const {
  setTool,
  setSelection,
  clearSelection,
  setStack,
  clearEditError,
  resetGardenPlan,
  applyAction,
  undo,
  redo,
} = gardenPlanSlice.actions;

export default gardenPlanSlice.reducer;

// ── Selectors ────────────────────────────────────────────────────────────────

/** `gardenPlan` is absent until the plan route has injected the slice. */
type RootWithPlan = { gardenPlan?: GardenPlanState };

/** The whole slice state; the initial state while the slice is not injected yet. */
export const selectGardenPlanState = (state: RootWithPlan): GardenPlanState =>
  state.gardenPlan ?? initialState;
const planState = selectGardenPlanState;

const NO_KEYS: ReadonlySet<string> = new Set();

/**
 * Objects a refused save named, while the refusal still stands (GP-UX-017): the renderer draws them with a
 * red outline. Derived from the refused operations that are still pending - undo the change, or save it, and
 * the outline goes; a later edit of another object never inherits it. Memoised: the renderer redraws on identity.
 */
export const selectInvalidKeys = createSelector(
  [
    (state: RootWithPlan) => planState(state).saveFailureOpIds,
    (state: RootWithPlan) => planState(state).pending,
    (state: RootWithPlan) => planState(state).saveStatus === 'error',
  ],
  (opIds, pending, standing): ReadonlySet<string> => {
    if (!standing || opIds.length === 0) return NO_KEYS;
    const refused = new Set(opIds);
    const keys = new Set<string>();
    for (const item of pending) {
      if (refused.has(item.id) && 'key' in item.op && typeof item.op.key === 'string') keys.add(item.op.key);
    }
    return keys.size > 0 ? keys : NO_KEYS;
  },
);

/** The dirty flag of GP-NFR-005. */
export const selectIsDirty = (state: RootWithPlan): boolean => planState(state).pending.length > 0;

/** "Ungespeicherte Änderungen (n)". */
export const selectPendingCount = (state: RootWithPlan): number => planState(state).pending.length;

export const selectCanUndo = (state: RootWithPlan): boolean =>
  planState(state).past.length > 0 &&
  planState(state).saveStatus !== 'saving' &&
  planState(state).saveStatus !== 'conflict';

export const selectCanRedo = (state: RootWithPlan): boolean =>
  planState(state).future.length > 0 &&
  planState(state).saveStatus !== 'saving' &&
  planState(state).saveStatus !== 'conflict';

/** What the next undo would take back ("Beet verschieben"): a label key or text, or `null`. */
export const selectUndoLabel = (state: RootWithPlan): string | null => {
  const { past } = planState(state);
  return past.length > 0 ? past[past.length - 1].label : null;
};

/** What the next redo would redo. */
export const selectRedoLabel = (state: RootWithPlan): string | null => {
  const { future } = planState(state);
  return future.length > 0 ? future[future.length - 1].label : null;
};

/**
 * Whether an auto-save may fire now (GP-UX-004): something is pending and the last save left the plan quiet.
 * A save in flight, a conflict (paused until the reload) and a refused save (the user must look at the message)
 * all hold it back - sending the same request again every two seconds would only repeat the refusal.
 */
export const selectAutoSaveReady = (state: RootWithPlan): boolean =>
  planState(state).pending.length > 0 && planState(state).saveStatus === 'idle';
