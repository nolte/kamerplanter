import { tenantClient } from '@/api/client';
import { isApiError } from '@/api/errors';
import type { GardenPlanResponse, PlanBatchRequest, PlanBatchResponse } from '../model/types';

/**
 * REST access to the garden plan of a site (REQ-053 §21.1) through the tenant-scoped client. Read and
 * batch only; the boundary and audit endpoints (GP-API-002/008) join with the packages that call them.
 */

const SITES = '/sites';

/** `include` values of GP-API-001. */
export type PlanInclude = 'plants' | 'tasks' | 'zones';

/** GP-API-001: the whole plan in one response. */
export async function getGardenPlan(
  siteKey: string,
  include?: readonly PlanInclude[],
): Promise<GardenPlanResponse> {
  const { data } = await tenantClient.get<GardenPlanResponse>(`${SITES}/${siteKey}/plan`, {
    params: include ? { include: include.join(',') } : undefined,
  });
  return data;
}

/** GP-API-003: all-or-nothing batch with the optimistic revision check. */
export async function applyPlanBatch(
  siteKey: string,
  request: PlanBatchRequest,
): Promise<PlanBatchResponse> {
  const { data } = await tenantClient.post<PlanBatchResponse>(
    `${SITES}/${siteKey}/plan/batch`,
    request,
  );
  return data;
}

// ── Failure mapping ──────────────────────────────────────────────────────────

/** One finding of a refused batch: the operation it belongs to and the published code. */
export interface PlanFinding {
  /** Index into the sent operations; `null` = not tied to one operation. */
  opIndex: number | null;
  field: string;
  code: string;
}

/**
 * A failed `POST /plan/batch`, as a plain serialisable value (it travels as a thunk's rejected
 * payload, and an `ApiError` instance would not survive the Redux serializability check).
 */
export type PlanSaveFailure =
  /** 409 `plan.revision_conflict` (V-14): someone else changed the structure meanwhile. */
  | {
      kind: 'conflict';
      currentRevision: number | null;
      changedBy: string | null;
      changedAt: string | null;
    }
  /** The server refused the request (403, 409 other than the revision, 422, ...). */
  | { kind: 'rejected'; status: number; code: string; findings: PlanFinding[] }
  /** The request did not get an answer (network, timeout, unexpected). */
  | { kind: 'failed'; message: string };

export const REVISION_CONFLICT_CODE = 'plan.revision_conflict';

function numberOrNull(value: unknown): number | null {
  return typeof value === 'number' ? value : null;
}

function stringOrNull(value: unknown): string | null {
  return typeof value === 'string' ? value : null;
}

/** Map whatever the batch request threw to a {@link PlanSaveFailure}. */
export function toPlanSaveFailure(error: unknown): PlanSaveFailure {
  if (!isApiError(error)) {
    return { kind: 'failed', message: error instanceof Error ? error.message : 'Unknown error' };
  }
  const details = error.details as unknown as Record<string, unknown>[];
  if (error.statusCode === 409 && error.errorCode === REVISION_CONFLICT_CODE) {
    const first = details[0] ?? {};
    return {
      kind: 'conflict',
      currentRevision: numberOrNull(first.current_revision),
      changedBy: stringOrNull(first.changed_by),
      changedAt: stringOrNull(first.changed_at),
    };
  }
  return {
    kind: 'rejected',
    status: error.statusCode,
    code: error.errorCode,
    findings: details.map((detail) => ({
      opIndex: numberOrNull(detail.op_index),
      field: stringOrNull(detail.field) ?? '',
      code: stringOrNull(detail.code) ?? '',
    })),
  };
}
