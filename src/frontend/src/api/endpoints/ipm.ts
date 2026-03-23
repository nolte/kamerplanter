import globalClient, { tenantClient } from '../client';
import type {
  Disease,
  DiseaseCreate,
  DiseaseUpdate,
  HarvestSafety,
  Inspection,
  InspectionCreate,
  KarenzPeriod,
  Pest,
  PestCreate,
  PestUpdate,
  Treatment,
  TreatmentApplication,
  TreatmentApplicationCreate,
  TreatmentCreate,
  TreatmentUpdate,
} from '../types';

const BASE = '/ipm';

// ── Pests ─────────────────────────────────────────────────────────────

export async function listPests(
  offset = 0,
  limit = 50,
): Promise<Pest[]> {
  const { data } = await globalClient.get<Pest[]>(`${BASE}/pests`, {
    params: { offset, limit },
  });
  return data;
}

export async function getPest(key: string): Promise<Pest> {
  const { data } = await globalClient.get<Pest>(`${BASE}/pests/${key}`);
  return data;
}

export async function createPest(payload: PestCreate): Promise<Pest> {
  const { data } = await globalClient.post<Pest>(`${BASE}/pests`, payload);
  return data;
}

export async function updatePest(
  key: string,
  payload: PestUpdate,
): Promise<Pest> {
  const { data } = await globalClient.put<Pest>(`${BASE}/pests/${key}`, payload);
  return data;
}

export async function deletePest(key: string): Promise<void> {
  await globalClient.delete(`${BASE}/pests/${key}`);
}

// ── Diseases ──────────────────────────────────────────────────────────

export async function listDiseases(
  offset = 0,
  limit = 50,
): Promise<Disease[]> {
  const { data } = await globalClient.get<Disease[]>(`${BASE}/diseases`, {
    params: { offset, limit },
  });
  return data;
}

export async function getDisease(key: string): Promise<Disease> {
  const { data } = await globalClient.get<Disease>(`${BASE}/diseases/${key}`);
  return data;
}

export async function createDisease(payload: DiseaseCreate): Promise<Disease> {
  const { data } = await globalClient.post<Disease>(`${BASE}/diseases`, payload);
  return data;
}

export async function updateDisease(
  key: string,
  payload: DiseaseUpdate,
): Promise<Disease> {
  const { data } = await globalClient.put<Disease>(
    `${BASE}/diseases/${key}`,
    payload,
  );
  return data;
}

export async function deleteDisease(key: string): Promise<void> {
  await globalClient.delete(`${BASE}/diseases/${key}`);
}

// ── Treatments ────────────────────────────────────────────────────────

export async function listTreatments(
  offset = 0,
  limit = 50,
): Promise<Treatment[]> {
  const { data } = await globalClient.get<Treatment[]>(`${BASE}/treatments`, {
    params: { offset, limit },
  });
  return data;
}

export async function getTreatment(key: string): Promise<Treatment> {
  const { data } = await globalClient.get<Treatment>(`${BASE}/treatments/${key}`);
  return data;
}

export async function createTreatment(
  payload: TreatmentCreate,
): Promise<Treatment> {
  const { data } = await globalClient.post<Treatment>(
    `${BASE}/treatments`,
    payload,
  );
  return data;
}

export async function updateTreatment(
  key: string,
  payload: TreatmentUpdate,
): Promise<Treatment> {
  const { data } = await globalClient.put<Treatment>(
    `${BASE}/treatments/${key}`,
    payload,
  );
  return data;
}

export async function deleteTreatment(key: string): Promise<void> {
  await globalClient.delete(`${BASE}/treatments/${key}`);
}

// ── Inspections ───────────────────────────────────────────────────────

export async function createInspection(
  plantKey: string,
  payload: InspectionCreate,
): Promise<Inspection> {
  const { data } = await tenantClient.post<Inspection>(
    `${BASE}/plants/${plantKey}/inspections`,
    payload,
  );
  return data;
}

export async function getInspections(
  plantKey: string,
  offset = 0,
  limit = 50,
): Promise<Inspection[]> {
  const { data } = await tenantClient.get<Inspection[]>(
    `${BASE}/plants/${plantKey}/inspections`,
    { params: { offset, limit } },
  );
  return data;
}

// ── Treatment Applications ────────────────────────────────────────────

export async function createTreatmentApplication(
  plantKey: string,
  payload: TreatmentApplicationCreate,
): Promise<TreatmentApplication> {
  const { data } = await tenantClient.post<TreatmentApplication>(
    `${BASE}/plants/${plantKey}/treatment-applications`,
    payload,
  );
  return data;
}

export async function getTreatmentApplications(
  plantKey: string,
  offset = 0,
  limit = 50,
): Promise<TreatmentApplication[]> {
  const { data } = await tenantClient.get<TreatmentApplication[]>(
    `${BASE}/plants/${plantKey}/treatment-applications`,
    { params: { offset, limit } },
  );
  return data;
}

// ── Karenz / Harvest Safety ───────────────────────────────────────────

export async function getKarenzPeriods(
  plantKey: string,
): Promise<KarenzPeriod[]> {
  const { data } = await tenantClient.get<KarenzPeriod[]>(
    `${BASE}/plants/${plantKey}/karenz`,
  );
  return data;
}

export async function checkHarvestSafety(
  plantKey: string,
  plannedDate?: string,
): Promise<HarvestSafety> {
  const params: Record<string, string> = {};
  if (plannedDate) params.planned_date = plannedDate;
  const { data } = await tenantClient.get<HarvestSafety>(
    `${BASE}/plants/${plantKey}/harvest-safety`,
    { params },
  );
  return data;
}
