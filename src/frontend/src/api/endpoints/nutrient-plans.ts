import { tenantClient as client } from '../client';
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

// ── Channel Fertilizer Assignment ─────────────────────────────────────

export async function addFertilizerToChannel(
  entryKey: string,
  channelId: string,
  data: { fertilizer_key: string; ml_per_liter: number; optional?: boolean },
): Promise<void> {
  await client.post(
    `${BASE}/entries/${entryKey}/channels/${channelId}/fertilizers`,
    data,
  );
}

export async function removeFertilizerFromChannel(
  entryKey: string,
  channelId: string,
  fertilizerKey: string,
): Promise<void> {
  await client.delete(
    `${BASE}/entries/${entryKey}/channels/${channelId}/fertilizers/${fertilizerKey}`,
  );
}

// ── Water Mix Recommendation ──────────────────────────────────────────

export interface WaterMixRecommendation {
  recommendation: {
    recommended_ro_percent: number;
    ec_headroom: number;
    effective_ec_ms: number;
    available_ec_for_nutrients: number;
    target_ec_ms: number;
    substrate_type: string;
    min_headroom_ratio: number;
    reasoning: string;
    alternatives: Array<{
      ro_percent: number;
      ec_headroom: number;
      trade_off: string;
    }>;
    calmag_correction: {
      calcium_deficit_ppm: number;
      magnesium_deficit_ppm: number;
      ca_mg_ratio: number | null;
      ca_mg_ratio_warning: string | null;
      needs_correction: boolean;
    } | null;
  };
  plan_name: string;
  plan_key: string;
  phase_name: string;
  sequence_order: number;
  site_name: string;
  site_key: string;
}

export async function fetchWaterMixRecommendation(
  planKey: string,
  sequenceOrder: number,
  siteKey: string,
  substrateType?: string,
): Promise<WaterMixRecommendation> {
  const params: Record<string, string | number> = {
    site_key: siteKey,
  };
  if (substrateType) {
    params.substrate_type = substrateType;
  }
  const { data } = await client.get<WaterMixRecommendation>(
    `${BASE}/${planKey}/entries/${sequenceOrder}/water-mix-recommendation`,
    { params },
  );
  return data;
}

export interface WaterMixBatchRecommendation {
  recommendations: WaterMixRecommendation[];
  site_name: string;
  site_key: string;
  plan_name: string;
  plan_key: string;
}

export async function fetchWaterMixRecommendationsBatch(
  planKey: string,
  siteKey: string,
  substrateType?: string,
): Promise<WaterMixBatchRecommendation> {
  const params: Record<string, string> = { site_key: siteKey };
  if (substrateType) params.substrate_type = substrateType;
  const { data } = await client.get<WaterMixBatchRecommendation>(
    `${BASE}/${planKey}/water-mix-recommendations`,
    { params },
  );
  return data;
}

// ── Dosage Calculation (REQ-004 §4b) ─────────────────────────────────

export interface CalculateDosagesRequest {
  site_key: string;
  phase_sequence_order: number;
  channel_id?: string | null;
  volume_liters?: number;
  ro_percent_override?: number | null;
}

export interface DosageEntry {
  product_name: string;
  fertilizer_key: string | null;
  ml_per_liter: number;
  total_ml: number;
  ec_contribution: number;
  source: string;
  mixing_order: number;
}

export interface EffectiveWater {
  ec_ms: number;
  ph: number;
  alkalinity_ppm: number;
  calcium_ppm: number;
  magnesium_ppm: number;
  chlorine_ppm: number;
  chloramine_ppm: number;
}

export interface CalMagCorrectionDetail {
  calcium_deficit_ppm: number;
  magnesium_deficit_ppm: number;
  ca_mg_ratio: number | null;
  ca_mg_ratio_warning: string | null;
  needs_correction: boolean;
}

export interface EcBudgetSummary {
  ec_base_water: number;
  ec_calmag: number;
  ec_ph_reserve: number;
  ec_fertilizers: number;
  ec_final: number;
}

export interface CalculateDosagesResponse {
  phase_name: string;
  channel_id: string;
  target_ec_ms: number;
  effective_water: EffectiveWater | null;
  ro_percent_used: number;
  calmag_correction: CalMagCorrectionDetail | null;
  calmag_dosage: DosageEntry | null;
  ec_budget: EcBudgetSummary;
  scaling_factor: number;
  dosages: DosageEntry[];
  mixing_instructions: string[];
  warnings: string[];
  reference_ec_ms: number | null;
  substrate_correction_applied: boolean;
}

export async function calculateDosages(
  planKey: string,
  request: CalculateDosagesRequest,
): Promise<CalculateDosagesResponse> {
  const { data } = await client.post<CalculateDosagesResponse>(
    `${BASE}/${planKey}/calculate-dosages`,
    request,
  );
  return data;
}

// ── Plant Instance Assignment ─────────────────────────────────────────

export async function assignPlanToPlant(
  plantKey: string,
  payload: { plan_key: string; assigned_by: string },
): Promise<void> {
  await client.post(`/plant-instances/${plantKey}/nutrient-plan`, payload);
}

export async function getPlantPlan(
  plantKey: string,
): Promise<NutrientPlan | null> {
  try {
    const { data } = await client.get<NutrientPlan>(
      `/plant-instances/${plantKey}/nutrient-plan`,
    );
    return data;
  } catch {
    return null;
  }
}

export async function removePlantPlan(plantKey: string): Promise<void> {
  await client.delete(`/plant-instances/${plantKey}/nutrient-plan`);
}
