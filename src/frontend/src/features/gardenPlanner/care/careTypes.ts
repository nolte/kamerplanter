/**
 * Wire types of the bed care tab (REQ-053 WP 4.4). Derived from the served contracts:
 * `app/api/v1/tasks/schemas.py` (queue, complete, batch, fan-out, reopen) and
 * `app/api/v1/care_events/schemas.py` (`POST /care-events`, `POST /care-events/{key}/void`).
 */
import type { TaskItem } from '@/api/types';

/** `TaskItem` plus the proposal fields of §20.9 (a system proposal the user has not accepted yet). */
export interface CareTask extends TaskItem {
  suggested?: boolean;
  suggestion_reason?: string | null;
}

/** `ProductRef` of a care event: a fertilizer of the catalogue, resolved server-side (GP-NFR-058). */
export interface FertilizerRef {
  kind: 'fertilizer';
  key: string;
}

/** `unit` values the server accepts (GP-FR-100). */
export type CareUnit = 'l' | 'ml' | 'g' | 'kg' | 'l_per_m2' | 'g_per_m2' | 'cm' | 'pieces';

/**
 * The care fields of a completion (`TaskCompletionDetails`) plus the task's own note. Every field is
 * optional (GP-FR-084); `extra="forbid"` on the server means nothing else may be sent.
 */
export interface CompletionPayload {
  completion_notes?: string;
  performed_at?: string;
  product_ref?: FertilizerRef;
  product_label?: string;
  quantity?: number;
  unit?: CareUnit;
  material?: string;
}

/** `POST /care-events` (GP-API-033): a care line without a task. `trigger` is `manual` (default). */
export interface CareEventBody {
  location_key: string;
  category: string;
  summary: string;
  performed_at: string;
  product_ref?: FertilizerRef;
  product_label?: string;
  quantity?: number;
  unit?: CareUnit;
  material?: string;
  observed_outcome?: string;
}

/** The slice of the `CareEventResponse` the tab needs. */
export interface CareEventRef {
  key: string;
  category: string;
}

/** `BatchResponse` of `POST /tasks/batch/status`. */
export interface BatchResult {
  succeeded: string[];
  failed: { key: string; error: string }[];
}

/** One standing plant of the bed (`GET /locations/{key}/plantings?state=active`). */
export interface BedPlantRef {
  plantKey: string;
  instanceId: string;
}

/** What a task is bound to, as the tab shows it. */
export type TaskTarget = 'bed' | 'plant' | 'other';

/** Where a task is created: on the bed itself, or on each plant standing in it (fan-out, GP-FR-081). */
export type TaskScope = 'bed' | 'plants';
