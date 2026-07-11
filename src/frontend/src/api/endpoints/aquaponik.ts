import client, { tenantClient } from '../client';
import type {
  AquaponicSystem,
  AquaponicSystemCreate,
  AquaponicSystemUpdate,
  CyclingProgress,
  CyclingStatus,
  FeedingRecommendation,
  FishSpecies,
  FishStock,
  FishStockCreate,
  NitrogenCyclePoint,
  WaterQualityEvaluation,
  WaterTest,
  WaterTestCreate,
} from '../types';

const BASE = '/aquaponics';

// ── Systems ─────────────────────────────────────────────────────────────

export async function listSystems(): Promise<AquaponicSystem[]> {
  const { data } = await tenantClient.get<AquaponicSystem[]>(`${BASE}/systems`);
  return data;
}

export async function getSystem(key: string): Promise<AquaponicSystem> {
  const { data } = await tenantClient.get<AquaponicSystem>(`${BASE}/systems/${key}`);
  return data;
}

export async function createSystem(
  payload: AquaponicSystemCreate,
): Promise<AquaponicSystem> {
  const { data } = await tenantClient.post<AquaponicSystem>(`${BASE}/systems`, payload);
  return data;
}

export async function updateSystem(
  key: string,
  payload: AquaponicSystemUpdate,
): Promise<AquaponicSystem> {
  const { data } = await tenantClient.patch<AquaponicSystem>(
    `${BASE}/systems/${key}`,
    payload,
  );
  return data;
}

export async function deleteSystem(key: string): Promise<void> {
  await tenantClient.delete(`${BASE}/systems/${key}`);
}

export async function setCyclingStatus(
  key: string,
  cyclingStatus: CyclingStatus,
): Promise<AquaponicSystem> {
  const { data } = await tenantClient.post<AquaponicSystem>(
    `${BASE}/systems/${key}/cycling-status`,
    { cycling_status: cyclingStatus },
  );
  return data;
}

// ── Fish stocks ───────────────────────────────────────────────────────────

export async function listStocks(systemKey: string): Promise<FishStock[]> {
  const { data } = await tenantClient.get<FishStock[]>(
    `${BASE}/systems/${systemKey}/fish-stocks`,
  );
  return data;
}

export async function createStock(
  systemKey: string,
  payload: FishStockCreate,
): Promise<FishStock> {
  const { data } = await tenantClient.post<FishStock>(
    `${BASE}/systems/${systemKey}/fish-stocks`,
    payload,
  );
  return data;
}

export async function recordMortality(
  systemKey: string,
  stockKey: string,
  deaths: number,
): Promise<FishStock> {
  const { data } = await tenantClient.post<FishStock>(
    `${BASE}/systems/${systemKey}/fish-stocks/${stockKey}/mortality`,
    { deaths },
  );
  return data;
}

// ── Water tests ───────────────────────────────────────────────────────────

export async function listWaterTests(systemKey: string): Promise<WaterTest[]> {
  const { data } = await tenantClient.get<WaterTest[]>(
    `${BASE}/systems/${systemKey}/water-tests`,
  );
  return data;
}

export async function recordWaterTest(
  systemKey: string,
  payload: WaterTestCreate,
): Promise<WaterTest> {
  const { data } = await tenantClient.post<WaterTest>(
    `${BASE}/systems/${systemKey}/water-tests`,
    payload,
  );
  return data;
}

export async function getWaterQualityStatus(
  systemKey: string,
): Promise<WaterQualityEvaluation[]> {
  const { data } = await tenantClient.get<WaterQualityEvaluation[]>(
    `${BASE}/systems/${systemKey}/water-quality-status`,
  );
  return data;
}

export async function getNitrogenCycleChart(
  systemKey: string,
): Promise<NitrogenCyclePoint[]> {
  const { data } = await tenantClient.get<NitrogenCyclePoint[]>(
    `${BASE}/systems/${systemKey}/nitrogen-cycle-chart`,
  );
  return data;
}

export async function getCyclingProgress(
  systemKey: string,
): Promise<CyclingProgress> {
  const { data } = await tenantClient.get<CyclingProgress>(
    `${BASE}/systems/${systemKey}/cycling-progress`,
  );
  return data;
}

export async function getAlerts(
  systemKey: string,
): Promise<WaterQualityEvaluation[]> {
  const { data } = await tenantClient.get<WaterQualityEvaluation[]>(
    `${BASE}/systems/${systemKey}/alerts`,
  );
  return data;
}

export async function getFeedingRecommendation(
  systemKey: string,
): Promise<FeedingRecommendation> {
  const { data } = await tenantClient.get<FeedingRecommendation>(
    `${BASE}/systems/${systemKey}/feeding-recommendation`,
  );
  return data;
}

// ── Fish species (global catalog) ─────────────────────────────────────────

export async function listFishSpecies(): Promise<FishSpecies[]> {
  const { data } = await client.get<FishSpecies[]>('/fish-species');
  return data;
}
