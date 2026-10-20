import { tenantClient } from '@/api/client';
import type { TaskItem } from '@/api/types';
import type {
  BatchResult,
  BedPlantRef,
  CareEventBody,
  CareEventRef,
  CareTask,
  CompletionPayload,
} from './careTypes';

/**
 * REST access of the bed care tab through the tenant-scoped client (REQ-053 GP-API-030…033): the
 * location queue, the atomic completion, the batch completion, create for each plant, reopen with `undo` and the
 * care log without a task.
 */

const TASKS = '/tasks';

/** GP-API-030: the pending tasks of a bed and the plants standing in it (suggestions included). */
export async function getBedQueue(
  locationKey: string,
  options: { includeChildren?: boolean; category?: string } = {},
): Promise<CareTask[]> {
  const { data } = await tenantClient.get<CareTask[]>(`${TASKS}/queue`, {
    params: {
      location_key: locationKey,
      include_children: options.includeChildren ?? true,
      ...(options.category ? { category: options.category } : {}),
    },
  });
  return data;
}

interface PlantingRow {
  state: string;
  plant_key?: string | null;
  instance_id?: string | null;
}

/** GP-API-024: the plants standing in the bed, to name the plant tasks. Informational only. */
export async function listActivePlants(bedKey: string): Promise<BedPlantRef[]> {
  const { data } = await tenantClient.get<PlantingRow[]>(`/locations/${bedKey}/plantings`, {
    params: { state: 'active', limit: 200 },
  });
  return data.flatMap((row) =>
    row.plant_key ? [{ plantKey: row.plant_key, instanceId: row.instance_id ?? row.plant_key }] : [],
  );
}

/** GP-API-031: the one completion transition; the task's care line is written in the same transaction. */
export async function completeBedTask(key: string, payload: CompletionPayload): Promise<TaskItem> {
  const { data } = await tenantClient.post<TaskItem>(`${TASKS}/${key}/complete`, payload);
  return data;
}

/** GP-API-032: `action = complete` for several tasks; an unknown or foreign key is a 404 for the whole batch. */
export async function completeTasksBatch(
  taskKeys: readonly string[],
  payload: CompletionPayload,
): Promise<BatchResult> {
  const { data } = await tenantClient.post<BatchResult>(`${TASKS}/batch/status`, {
    task_keys: taskKeys,
    action: 'complete',
    ...payload,
  });
  return data;
}

/** Skip a task; a suggestion is dismissed this way (there is no dismiss endpoint yet, GP-API-040). */
export async function skipBedTask(key: string): Promise<TaskItem> {
  const { data } = await tenantClient.post<TaskItem>(`${TASKS}/${key}/skip`);
  return data;
}

/** GP-FR-149: reopen and void the task's care line in the same transaction. */
export async function reopenWithUndo(key: string): Promise<TaskItem> {
  const { data } = await tenantClient.post<TaskItem>(`${TASKS}/${key}/reopen`, { undo: true });
  return data;
}

/** Reopen a skipped task (a dismissed suggestion has no care line to void). */
export async function reopenBedTask(key: string): Promise<TaskItem> {
  const { data } = await tenantClient.post<TaskItem>(`${TASKS}/${key}/reopen`, {});
  return data;
}

export interface BedTaskBody {
  name: string;
  category: string;
  entity_type: 'location';
  entity_key: string;
  due_date?: string;
  priority?: string;
  instruction?: string;
}

export async function createBedTask(body: BedTaskBody): Promise<CareTask> {
  const { data } = await tenantClient.post<CareTask>(TASKS, body);
  return data;
}

/**
 * GP-FR-081 / #2462: "for every plant" in one request. The server creates only the per-plant tasks, in one
 * transaction (no bed task, nothing half-done on a failure); a bed without plants answers an empty list.
 */
export async function createTasksForEachPlant(body: BedTaskBody): Promise<CareTask[]> {
  const { data } = await tenantClient.post<CareTask[]>(TASKS, { ...body, for_each_plant: true });
  return data;
}

/** GP-API-033 / GP-FR-090: log care without a task. */
export async function logCareEvent(body: CareEventBody): Promise<CareEventRef> {
  const { data } = await tenantClient.post<CareEventRef>('/care-events', body);
  return data;
}

/** GP-API-037: the author takes back an entry within ten minutes (`undo`). */
export async function voidCareEvent(key: string): Promise<void> {
  await tenantClient.post(`/care-events/${key}/void`, { reason: 'undo' });
}
