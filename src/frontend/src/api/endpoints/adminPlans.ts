import apiClient from '@/api/client';
import type { Plan, PlanCreate, PlanUpdate } from '@/api/types';

/**
 * The plan catalogue of the installation (REQ-056 §7.6, #2142). Every route is
 * `require_platform_admin`, the list included, and none needs a step-up.
 */
const BASE = '/admin/platform/plans';

/** Every plan with the number of tenants assigned to it, ordered by key (not paged: a handful of plans). */
export async function listPlans(): Promise<Plan[]> {
  const { data } = await apiClient.get<Plan[]>(BASE);
  return data;
}

/** Create a plan; 409 for a taken key, 422 for a limit out of range. */
export async function createPlan(payload: PlanCreate): Promise<Plan> {
  const { data } = await apiClient.post<Plan>(BASE, payload);
  return data;
}

/** Change name, description or single limits, or make the plan the default (`is_default: true`). */
export async function updatePlan(planKey: string, payload: PlanUpdate): Promise<Plan> {
  const { data } = await apiClient.patch<Plan>(`${BASE}/${encodeURIComponent(planKey)}`, payload);
  return data;
}

/** Delete a plan; 409 while it is the default or a tenant is assigned to it. */
export async function deletePlan(planKey: string): Promise<void> {
  await apiClient.delete(`${BASE}/${encodeURIComponent(planKey)}`);
}
