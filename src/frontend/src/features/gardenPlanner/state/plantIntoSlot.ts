/**
 * "Pflanze setzen" writes ONE plant into ONE slot (REQ-053 GP-UX-071, #2913) through the existing single-plant create
 * path (`POST /plant-instances` with `slot_key`) - the same API client the plant pages use, no second one. The plant
 * is no plan operation: it is written at once, outside the plan batch and its offline buffer, and the plan is read
 * again afterwards so the spot shows the plant.
 *
 * Because the re-read replaces the model and is dropped while edits are pending (`refreshGardenPlan`), unsaved edits
 * are saved first - the order `placeTemplateAt` uses. Offline nothing is sent and nothing is queued: the tool says it
 * needs a connection.
 */
import { isApiError } from '@/api/errors';
import { createPlantInstance } from '@/api/endpoints/plantInstances';
import { getSlot } from '@/api/endpoints/sites';
import type { ThunkDispatch, UnknownAction } from '@reduxjs/toolkit';
import { refreshGardenPlan, saveGardenPlan, selectGardenPlanState, type GardenPlanState } from './gardenPlanSlice';

export interface PlantIntoSlotArg {
  bedKey: string;
  slotKey: string;
  speciesKey: string;
  cultivarKey: string | null;
  /** `YYYY-MM-DD`. */
  plantedOn: string;
  instanceId: string;
}

/**
 * Why nothing was planted: `offline` - no connection; `busy` - a save or a template placement is running, or the plan
 * is in conflict; `save_first` - the unsaved edits could not be saved; `slot_taken` - the slot was occupied meanwhile;
 * `rotation` / `companion` - the server refuses the single plant for a critical crop-rotation finding or an
 * incompatible neighbour (no override for a single plant); `failed` - anything else, with the error.
 */
export type PlantRefusal = 'offline' | 'busy' | 'save_first' | 'slot_taken' | 'rotation' | 'companion' | 'failed';

export type PlantIntoSlotOutcome =
  | { ok: true; plantKey: string; refreshed: boolean }
  | { ok: false; code: PlantRefusal; error?: unknown };

type State = { gardenPlan?: GardenPlanState };
/** Any store that holds the plan slice: the app's root store, or a test store of the slice alone. */
type PlanDispatch = ThunkDispatch<State, unknown, UnknownAction>;

/** The server's codes for the two refusals of `create_plant` that the bed's planting dialog can override. */
const REFUSAL_BY_CODE: Record<string, PlantRefusal> = {
  ROTATION_VIOLATION: 'rotation',
  INCOMPATIBLE_COMPANION: 'companion',
};

export function plantIntoSlot(arg: PlantIntoSlotArg) {
  return async (dispatch: PlanDispatch, getState: () => State): Promise<PlantIntoSlotOutcome> => {
    let current = selectGardenPlanState(getState());
    if (current.plan === null) return { ok: false, code: 'failed' };
    if (current.offline) return { ok: false, code: 'offline' };
    if (current.saveStatus === 'saving' || current.saveStatus === 'conflict' || current.placing) {
      return { ok: false, code: 'busy' };
    }
    if (current.pending.length > 0) {
      await dispatch(saveGardenPlan());
      current = selectGardenPlanState(getState());
      if (current.plan === null || current.pending.length > 0 || current.saveStatus !== 'idle') {
        return { ok: false, code: 'save_first' };
      }
    }
    const siteKey = current.plan.siteKey;
    try {
      // The plan may be older than the slot: somebody may have planted it meanwhile (the server does not refuse a
      // second plant on an occupied slot).
      const slot = await getSlot(arg.slotKey);
      if (slot.currently_occupied) {
        await dispatch(refreshGardenPlan(siteKey));
        return { ok: false, code: 'slot_taken' };
      }
      const created = await createPlantInstance({
        instance_id: arg.instanceId,
        species_key: arg.speciesKey,
        cultivar_key: arg.cultivarKey,
        site_key: siteKey,
        location_key: arg.bedKey,
        slot_key: arg.slotKey,
        planted_on: arg.plantedOn,
      });
      const refreshed = await dispatch(refreshGardenPlan(siteKey));
      return { ok: true, plantKey: created.key, refreshed: refreshGardenPlan.fulfilled.match(refreshed) };
    } catch (error) {
      const code = isApiError(error) ? REFUSAL_BY_CODE[error.errorCode] : undefined;
      return code ? { ok: false, code } : { ok: false, code: 'failed', error };
    }
  };
}
