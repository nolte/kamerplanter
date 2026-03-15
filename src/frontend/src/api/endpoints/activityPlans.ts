import api from '../client';
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

export const updateTaskTemplate = (key: string, req: TaskTemplateUpdateRequest) =>
  api.patch<TaskTemplateResponse>(`/activity-plans/templates/${key}`, req).then((r) => r.data);

export const deleteTaskTemplate = (key: string) =>
  api.delete(`/activity-plans/templates/${key}`);
