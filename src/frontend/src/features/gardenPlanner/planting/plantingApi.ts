import { tenantClient } from '@/api/client';
import { createPlantingRun, deletePlantingRun as removePlantingRun, listEntries } from '@/api/endpoints/plantingRuns';
import { createTask } from '@/api/endpoints/tasks';
import type { PlantingRun, PlantingRunCreate, PlantingRunEntry, TaskItem } from '@/api/types';
import type {
  BedFrameGeometry,
  PlantingItem,
  PlantingState,
  PreviewEntry,
  PreviewResponse,
  QuickPlantingBody,
  QuickPlantingResponse,
  SlotBatchItem,
  SlotBatchResult,
  SlotRecord,
  ValidatePlantingResponse,
} from './plantingTypes';

/**
 * REST access of the planting dialog and the plant markers (REQ-053 WP 3.6) through the tenant-scoped
 * client: the layout preview (GP-API-016), the hints (GP-API-025), the plantings of a bed (GP-API-024),
 * the run with its layout (`POST /planting-runs`, GP-FR-064/065), the slot batch for freely placed
 * positions (GP-API-015), `plan-slots` (GP-API-021), the field-mode shortcut (GP-API-017) and the slot
 * correction (GP-API-014).
 */

/** GP-API-016: where the entry's plants would stand, without persisting anything. The server is authoritative. */
export async function previewLayout(bedKey: string, entry: PreviewEntry): Promise<PreviewResponse> {
  const { data } = await tenantClient.post<PreviewResponse>(
    `/locations/${bedKey}/planting-layout/preview`,
    { entry },
  );
  return data;
}

/** GP-API-025: crop-rotation and companion hints for planting a species in the bed. */
export async function validatePlanting(
  bedKey: string,
  speciesKey: string,
): Promise<ValidatePlantingResponse> {
  const { data } = await tenantClient.post<ValidatePlantingResponse>(
    `/locations/${bedKey}/validate-planting`,
    { species_key: speciesKey },
  );
  return data;
}

/** GP-API-024: the planned positions and plants of a bed, optionally of one state. */
export async function listPlantings(
  bedKey: string,
  state?: PlantingState,
): Promise<PlantingItem[]> {
  const { data } = await tenantClient.get<PlantingItem[]>(`/locations/${bedKey}/plantings`, {
    params: { ...(state ? { state } : {}), limit: 200 },
  });
  return data;
}

/** The run of the dialog; the server lays the entries out on the bed and reserves the slots (GP-FR-064/065). */
export async function createRun(payload: PlantingRunCreate): Promise<PlantingRun> {
  return createPlantingRun(payload);
}

/** Take a planned run back (with its reservations and the layout slots only it used); the lead role may. */
export async function deletePlantingRun(runKey: string): Promise<void> {
  await removePlantingRun(runKey);
}

export async function runEntries(runKey: string): Promise<PlantingRunEntry[]> {
  return listEntries(runKey);
}

/** GP-API-015: add slots to the bed (`append` keeps every slot there is). */
export async function appendSlots(
  bedKey: string,
  slots: SlotBatchItem[],
): Promise<SlotBatchResult> {
  const { data } = await tenantClient.post<SlotBatchResult>(`/locations/${bedKey}/slots/batch`, {
    mode: 'append',
    slots,
  });
  return data;
}

/** GP-API-021: reserve `slotKeys` (in `sequence` order) for one entry of a run. */
export async function planSlots(
  runKey: string,
  entryKey: string,
  slotKeys: string[],
): Promise<void> {
  await tenantClient.post(`/planting-runs/${runKey}/plan-slots`, {
    entry_key: entryKey,
    slot_keys: slotKeys,
  });
}

/** GP-API-017: *I planted n of this species here*. */
export async function quickPlant(
  bedKey: string,
  body: QuickPlantingBody,
): Promise<QuickPlantingResponse> {
  const { data } = await tenantClient.post<QuickPlantingResponse>(
    `/locations/${bedKey}/quick-planting`,
    body,
  );
  return data;
}

/** The slots of a bed (bed frame); the preview draws the ones that stand there already. */
export async function listBedSlots(bedKey: string): Promise<SlotRecord[]> {
  const { data } = await tenantClient.get<SlotRecord[]>('/slots', { params: { location_key: bedKey } });
  return data;
}

/** One slot, to start "Correct position" from its stored geometry. */
export async function getSlot(slotKey: string): Promise<SlotRecord> {
  const { data } = await tenantClient.get<SlotRecord>(`/slots/${slotKey}`);
  return data;
}

/**
 * GP-API-014 / GP-FR-068: "Correct position" is a new geometry for the plant's slot. The server logs
 * `care_event(position_corrected)` with the plant; the client does not write it.
 */
export async function correctSlotPosition(
  slotKey: string,
  geometry: BedFrameGeometry,
): Promise<void> {
  await tenantClient.patch(`/slots/${slotKey}`, { geometry });
}

/** The runs of a bed (any status), to find the ones planted despite a crop-rotation hint. */
export async function listBedRuns(bedKey: string): Promise<PlantingRun[]> {
  const { data } = await tenantClient.get<PlantingRun[]>('/planting-runs', {
    params: { location_key: bedKey, limit: 200 },
  });
  return data;
}

/** GP-FR-069: moving a plant to another bed is the existing `transplant` task, not a drag. */
export async function createTransplantTask(payload: {
  name: string;
  instruction: string;
  plantKey: string;
}): Promise<TaskItem> {
  return createTask({
    name: payload.name,
    instruction: payload.instruction,
    category: 'transplant',
    entity_type: 'plant_instance',
    entity_key: payload.plantKey,
  });
}
