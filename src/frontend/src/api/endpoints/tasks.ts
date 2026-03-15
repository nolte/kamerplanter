import client from '../client';
import type {
  BatchResponse,
  HSTValidationResult,
  PhotoUploadResponse,
  TaskAuditEntry,
  TaskCloneRequest,
  TaskComment,
  TaskCompleteRequest,
  TaskItem,
  TaskItemCreate,
  TaskItemUpdate,
  TaskTemplate,
  TaskTemplateCreate,
  TaskTemplateUpdate,
  WorkflowAddTaskRequest,
  WorkflowExecution,
  WorkflowInstantiateRequest,
  WorkflowTemplate,
  WorkflowTemplateCreate,
  WorkflowTemplateUpdate,
} from '../types';

const BASE = '/tasks';

// -- Workflow Templates --

export async function listWorkflows(
  offset = 0,
  limit = 50,
  speciesKey?: string,
): Promise<WorkflowTemplate[]> {
  const params: Record<string, unknown> = { offset, limit };
  if (speciesKey) params.species_key = speciesKey;
  const { data } = await client.get<WorkflowTemplate[]>(
    `${BASE}/workflows`,
    { params },
  );
  return data;
}

export async function createWorkflow(
  payload: WorkflowTemplateCreate,
): Promise<WorkflowTemplate> {
  const { data } = await client.post<WorkflowTemplate>(
    `${BASE}/workflows`,
    payload,
  );
  return data;
}

export async function getWorkflow(key: string): Promise<WorkflowTemplate> {
  const { data } = await client.get<WorkflowTemplate>(
    `${BASE}/workflows/${key}`,
  );
  return data;
}

export async function updateWorkflow(
  key: string,
  payload: WorkflowTemplateUpdate,
): Promise<WorkflowTemplate> {
  const { data } = await client.put<WorkflowTemplate>(
    `${BASE}/workflows/${key}`,
    payload,
  );
  return data;
}

export async function deleteWorkflow(key: string): Promise<void> {
  await client.delete(`${BASE}/workflows/${key}`);
}

export async function duplicateWorkflow(key: string, name: string): Promise<WorkflowTemplate> {
  const { data } = await client.post<WorkflowTemplate>(
    `${BASE}/workflows/${key}/duplicate`,
    null,
    { params: { name } },
  );
  return data;
}

export async function instantiateWorkflow(
  key: string,
  payload: WorkflowInstantiateRequest,
): Promise<WorkflowExecution> {
  const { data } = await client.post<WorkflowExecution>(
    `${BASE}/workflows/${key}/instantiate`,
    payload,
  );
  return data;
}

// -- Task Templates --

export async function listTaskTemplates(
  workflowKey: string,
): Promise<TaskTemplate[]> {
  const { data } = await client.get<TaskTemplate[]>(
    `${BASE}/workflows/${workflowKey}/templates`,
  );
  return data;
}

export async function createTaskTemplate(
  payload: TaskTemplateCreate,
): Promise<TaskTemplate> {
  const { data } = await client.post<TaskTemplate>(
    `${BASE}/templates`,
    payload,
  );
  return data;
}

export async function getTaskTemplate(key: string): Promise<TaskTemplate> {
  const { data } = await client.get<TaskTemplate>(`${BASE}/templates/${key}`);
  return data;
}

export async function updateTaskTemplate(
  key: string,
  payload: TaskTemplateUpdate,
): Promise<TaskTemplate> {
  const { data } = await client.put<TaskTemplate>(
    `${BASE}/templates/${key}`,
    payload,
  );
  return data;
}

export async function deleteTaskTemplate(key: string): Promise<void> {
  await client.delete(`${BASE}/templates/${key}`);
}

// -- Tasks --

export async function listTasks(
  offset = 0,
  limit = 50,
  filters?: { status?: string; plant_key?: string; category?: string },
): Promise<TaskItem[]> {
  const params: Record<string, string | number> = { offset, limit };
  if (filters?.status) params.status = filters.status;
  if (filters?.plant_key) params.plant_key = filters.plant_key;
  if (filters?.category) params.category = filters.category;
  const { data } = await client.get<TaskItem[]>(BASE, { params });
  return data;
}

export async function createTask(payload: TaskItemCreate): Promise<TaskItem> {
  const { data } = await client.post<TaskItem>(BASE, payload);
  return data;
}

export async function getTask(key: string): Promise<TaskItem> {
  const { data } = await client.get<TaskItem>(`${BASE}/${key}`);
  return data;
}

export async function updateTask(
  key: string,
  payload: TaskItemUpdate,
): Promise<TaskItem> {
  const { data } = await client.put<TaskItem>(`${BASE}/${key}`, payload);
  return data;
}

export async function deleteTask(key: string): Promise<void> {
  await client.delete(`${BASE}/${key}`);
}

export async function uploadTaskPhoto(
  key: string,
  file: File,
): Promise<PhotoUploadResponse> {
  const formData = new FormData();
  formData.append('file', file);
  const { data } = await client.post<PhotoUploadResponse>(
    `${BASE}/${key}/photos`,
    formData,
    { headers: { 'Content-Type': 'multipart/form-data' } },
  );
  return data;
}

export async function startTask(key: string): Promise<TaskItem> {
  const { data } = await client.post<TaskItem>(`${BASE}/${key}/start`);
  return data;
}

export async function completeTask(
  key: string,
  payload: TaskCompleteRequest,
): Promise<TaskItem> {
  const { data } = await client.post<TaskItem>(
    `${BASE}/${key}/complete`,
    payload,
  );
  return data;
}

export async function skipTask(key: string): Promise<TaskItem> {
  const { data } = await client.post<TaskItem>(`${BASE}/${key}/skip`);
  return data;
}

// -- Specialized queries --

export async function getTaskQueue(
  plantKey?: string,
): Promise<TaskItem[]> {
  const params: Record<string, string> = {};
  if (plantKey) params.plant_key = plantKey;
  const { data } = await client.get<TaskItem[]>(`${BASE}/queue`, { params });
  return data;
}

export async function getOverdueTasks(): Promise<TaskItem[]> {
  const { data } = await client.get<TaskItem[]>(`${BASE}/overdue`);
  return data;
}

export async function generateCareReminders(): Promise<{ created: number; skipped: number }> {
  const { data } = await client.post<{ created: number; skipped: number }>(`${BASE}/generate-care-reminders`);
  return data;
}

export async function getTasksForPlant(
  plantKey: string,
  status?: string,
): Promise<TaskItem[]> {
  const params: Record<string, string> = {};
  if (status) params.status = status;
  const { data } = await client.get<TaskItem[]>(
    `${BASE}/plants/${plantKey}`,
    { params },
  );
  return data;
}

// -- HST Validation --

export async function validateHST(payload: {
  task_name: string;
  current_phase: string;
  recent_hst_tasks?: Record<string, unknown>[];
  species_name?: string;
}): Promise<HSTValidationResult> {
  const { data } = await client.post<HSTValidationResult>(
    `${BASE}/validate-hst`,
    payload,
  );
  return data;
}

// -- Clone & Reopen --

export async function cloneTask(
  key: string,
  payload: TaskCloneRequest = {},
): Promise<TaskItem> {
  const { data } = await client.post<TaskItem>(
    `${BASE}/${key}/clone`,
    payload,
  );
  return data;
}

export async function reopenTask(key: string): Promise<TaskItem> {
  const { data } = await client.post<TaskItem>(`${BASE}/${key}/reopen`, {});
  return data;
}

// -- Batch Operations --

export async function batchStatusChange(
  taskKeys: string[],
  action: 'start' | 'complete' | 'skip',
  completionNotes?: string,
): Promise<BatchResponse> {
  const { data } = await client.post<BatchResponse>(
    `${BASE}/batch/status`,
    { task_keys: taskKeys, action, completion_notes: completionNotes },
  );
  return data;
}

export async function batchDelete(taskKeys: string[]): Promise<BatchResponse> {
  const { data } = await client.post<BatchResponse>(
    `${BASE}/batch/delete`,
    { task_keys: taskKeys },
  );
  return data;
}

export async function batchAssign(
  taskKeys: string[],
  assignedToUserKey: string,
): Promise<BatchResponse> {
  const { data } = await client.post<BatchResponse>(
    `${BASE}/batch/assign`,
    { task_keys: taskKeys, assigned_to_user_key: assignedToUserKey },
  );
  return data;
}

// -- Comments --

export async function listTaskComments(
  taskKey: string,
): Promise<TaskComment[]> {
  const { data } = await client.get<TaskComment[]>(
    `${BASE}/${taskKey}/comments`,
  );
  return data;
}

export async function createTaskComment(
  taskKey: string,
  commentText: string,
): Promise<TaskComment> {
  const { data } = await client.post<TaskComment>(
    `${BASE}/${taskKey}/comments`,
    { comment_text: commentText },
  );
  return data;
}

export async function updateTaskComment(
  taskKey: string,
  commentKey: string,
  commentText: string,
): Promise<TaskComment> {
  const { data } = await client.put<TaskComment>(
    `${BASE}/${taskKey}/comments/${commentKey}`,
    { comment_text: commentText },
  );
  return data;
}

export async function deleteTaskComment(
  taskKey: string,
  commentKey: string,
): Promise<void> {
  await client.delete(`${BASE}/${taskKey}/comments/${commentKey}`);
}

// -- Audit / History --

export async function getTaskHistory(
  taskKey: string,
): Promise<TaskAuditEntry[]> {
  const { data } = await client.get<TaskAuditEntry[]>(
    `${BASE}/${taskKey}/history`,
  );
  return data;
}

// -- Workflow Executions --

export async function getWorkflowExecution(
  key: string,
): Promise<WorkflowExecution> {
  const { data } = await client.get<WorkflowExecution>(
    `${BASE}/executions/${key}`,
  );
  return data;
}

export async function addTaskToWorkflow(
  executionKey: string,
  payload: WorkflowAddTaskRequest,
): Promise<TaskItem> {
  const { data } = await client.post<TaskItem>(
    `${BASE}/executions/${executionKey}/tasks`,
    payload,
  );
  return data;
}
