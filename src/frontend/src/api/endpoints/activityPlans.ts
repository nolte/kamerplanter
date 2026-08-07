import api, { tenantClient } from '../client';
import type {
  ActivityPlanGenerateRequest,
  ActivityPlanResponse,
  ActivityPlanApplyRequest,
  ActivityPlanApplyResponse,
  TaskTemplateResponse,
  TaskTemplateUpdateRequest,
} from '../types';

export const generatePlan = (req: ActivityPlanGenerateRequest) =>
  api.post<ActivityPlanResponse>('/activity-plans/generate', req).then((r) => r.data);

export const applyPlan = (req: ActivityPlanApplyRequest) =>
  api.post<ActivityPlanApplyResponse>('/activity-plans/apply', req).then((r) => r.data);

/*
 * The two template writes moved under /t/{tenant_slug}/ (#992): they had no
 * tenant context at all, so the document key was the entire authorisation and
 * any authenticated user could retime or delete any tenant's task template.
 * `tenantClient` prepends the active slug; the backend now answers 404 for a
 * template whose parent workflow belongs to another tenant and 422 for one that
 * belongs to a shared system workflow. Both arrive as the standard error
 * envelope, which `ActivityPlanTab`'s `handleError` already surfaces.
 */
export const updateTaskTemplate = (key: string, req: TaskTemplateUpdateRequest) =>
  tenantClient
    .patch<TaskTemplateResponse>(`/activity-plans/templates/${key}`, req)
    .then((r) => r.data);

export const deleteTaskTemplate = (key: string) =>
  tenantClient.delete(`/activity-plans/templates/${key}`);
