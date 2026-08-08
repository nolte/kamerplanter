import { tenantClient } from '../client';
import type {
  ActivityPlanGenerateRequest,
  ActivityPlanResponse,
  ActivityPlanApplyRequest,
  ActivityPlanApplyResponse,
  TaskTemplateResponse,
  TaskTemplateUpdateRequest,
} from '../types';

/*
 * Generation moved under /t/{tenant_slug}/ (#1003). Which plan comes back now
 * depends on who asks: the shared generated template until this tenant has
 * edited it, their own private copy afterwards. A global request cannot express
 * that distinction, so it always got the shared one — and every edit the tenant
 * made would have vanished from their view on the next reload.
 */
export const generatePlan = (req: ActivityPlanGenerateRequest) =>
  tenantClient.post<ActivityPlanResponse>('/activity-plans/generate', req).then((r) => r.data);

/*
 * Applying a plan moved under /t/{tenant_slug}/ (#1000). It used to be global and
 * took its tenant from the request body, so any authenticated user could create
 * tasks in an arbitrary tenant by naming it. The tenant now comes from the path
 * (`tenantClient` prepends the active slug) and the body no longer carries a
 * `tenant_key`; the created tasks are stamped with the path tenant, and the
 * target plant/run is verified against it (404 for a foreign or unknown key).
 */
export const applyPlan = (req: ActivityPlanApplyRequest) =>
  tenantClient.post<ActivityPlanApplyResponse>('/activity-plans/apply', req).then((r) => r.data);

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
