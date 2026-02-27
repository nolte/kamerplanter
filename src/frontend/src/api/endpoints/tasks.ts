import client from '../client';
import type {
  HSTValidationResult,
  TaskCompleteRequest,
  TaskItem,
  TaskItemCreate,
  TaskItemUpdate,
  TaskTemplate,
  TaskTemplateCreate,
  WorkflowExecution,
  WorkflowInstantiateRequest,
  WorkflowTemplate,
  WorkflowTemplateCreate,
} from '../types';

const BASE = '/tasks';

// -- Workflow Templates --

export async function listWorkflows(
  offset = 0,
  limit = 50,
): Promise<WorkflowTemplate[]> {
  const { data } = await client.get<WorkflowTemplate[]>(
    `${BASE}/workflows`,
    { params: { offset, limit } },
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

// -- Workflow Executions --

export async function getWorkflowExecution(
  key: string,
): Promise<WorkflowExecution> {
  const { data } = await client.get<WorkflowExecution>(
    `${BASE}/executions/${key}`,
  );
  return data;
}
