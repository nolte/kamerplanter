import { tenantClient as client } from '../client';
import type {
  GenerateNextRunResponse,
  GenerateRunsResponse,
  SuccessionPlan,
  SuccessionPlanCreate,
  SuccessionPlanUpdate,
} from '../types';

const BASE = '/succession-plans';

export async function listSuccessionPlans(
  offset = 0,
  limit = 50,
): Promise<SuccessionPlan[]> {
  const { data } = await client.get<SuccessionPlan[]>(BASE, {
    params: { offset, limit },
  });
  return data;
}

export async function getSuccessionPlan(key: string): Promise<SuccessionPlan> {
  const { data } = await client.get<SuccessionPlan>(`${BASE}/${key}`);
  return data;
}

export async function createSuccessionPlan(
  payload: SuccessionPlanCreate,
): Promise<SuccessionPlan> {
  const { data } = await client.post<SuccessionPlan>(BASE, payload);
  return data;
}

export async function updateSuccessionPlan(
  key: string,
  payload: SuccessionPlanUpdate,
): Promise<SuccessionPlan> {
  const { data } = await client.put<SuccessionPlan>(`${BASE}/${key}`, payload);
  return data;
}

export async function deleteSuccessionPlan(key: string): Promise<void> {
  await client.delete(`${BASE}/${key}`);
}

/** Generates every remaining batch (PlantingRun) for the plan at once. */
export async function generateRuns(key: string): Promise<GenerateRunsResponse> {
  const { data } = await client.post<GenerateRunsResponse>(
    `${BASE}/${key}/generate`,
  );
  return data;
}

/** Generates only the next due batch (PlantingRun) for the plan. */
export async function generateNextRun(
  key: string,
): Promise<GenerateNextRunResponse> {
  const { data } = await client.post<GenerateNextRunResponse>(
    `${BASE}/${key}/generate-next`,
  );
  return data;
}
