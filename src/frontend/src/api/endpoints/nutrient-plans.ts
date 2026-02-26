import client from '../client';
import type {
  NutrientPlan,
  NutrientPlanCreate,
  NutrientPlanPhaseEntry,
  NutrientPlanUpdate,
  PhaseEntryCreate,
  PhaseEntryUpdate,
  PlanValidationResult,
} from '../types';

const BASE = '/nutrient-plans';

// ── Nutrient Plan CRUD ────────────────────────────────────────────────

export async function fetchNutrientPlans(
  offset = 0,
  limit = 50,
  filters?: Record<string, string>,
): Promise<NutrientPlan[]> {
  const params: Record<string, string | number> = { offset, limit };
  if (filters) {
    for (const [key, value] of Object.entries(filters)) {
      params[key] = value;
    }
  }
  const { data } = await client.get<NutrientPlan[]>(BASE, { params });
  return data;
}

export async function fetchNutrientPlan(key: string): Promise<NutrientPlan> {
  const { data } = await client.get<NutrientPlan>(`${BASE}/${key}`);
  return data;
}

export async function createNutrientPlan(
  payload: NutrientPlanCreate,
): Promise<NutrientPlan> {
  const { data } = await client.post<NutrientPlan>(BASE, payload);
  return data;
}

export async function updateNutrientPlan(
  key: string,
  payload: NutrientPlanUpdate,
): Promise<NutrientPlan> {
  const { data } = await client.put<NutrientPlan>(`${BASE}/${key}`, payload);
  return data;
}

export async function deleteNutrientPlan(key: string): Promise<void> {
  await client.delete(`${BASE}/${key}`);
}

// ── Clone & Validate ──────────────────────────────────────────────────

export async function cloneNutrientPlan(
  key: string,
  payload: { new_name: string; author: string },
): Promise<NutrientPlan> {
  const { data } = await client.post<NutrientPlan>(
    `${BASE}/${key}/clone`,
    payload,
  );
  return data;
}

export async function validateNutrientPlan(
  key: string,
): Promise<PlanValidationResult> {
  const { data } = await client.get<PlanValidationResult>(
    `${BASE}/${key}/validate`,
  );
  return data;
}

// ── Phase Entries ─────────────────────────────────────────────────────

export async function fetchPhaseEntries(
  key: string,
): Promise<NutrientPlanPhaseEntry[]> {
  const { data } = await client.get<NutrientPlanPhaseEntry[]>(
    `${BASE}/${key}/entries`,
  );
  return data;
}

export async function createPhaseEntry(
  key: string,
  payload: PhaseEntryCreate,
): Promise<NutrientPlanPhaseEntry> {
  const { data } = await client.post<NutrientPlanPhaseEntry>(
    `${BASE}/${key}/entries`,
    payload,
  );
  return data;
}

export async function updatePhaseEntry(
  planKey: string,
  entryKey: string,
  payload: PhaseEntryUpdate,
): Promise<NutrientPlanPhaseEntry> {
  const { data } = await client.put<NutrientPlanPhaseEntry>(
    `${BASE}/${planKey}/entries/${entryKey}`,
    payload,
  );
  return data;
}

export async function deletePhaseEntry(
  planKey: string,
  entryKey: string,
): Promise<void> {
  await client.delete(`${BASE}/${planKey}/entries/${entryKey}`);
}
