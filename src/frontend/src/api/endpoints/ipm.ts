import globalClient, { tenantClient } from '../client';
import { CATALOGUE_PAGE_SIZE, fetchAllPages } from '../paginate';
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
  PestDetail,
  PestImage,
  PestUpdate,
  Treatment,
  TreatmentApplication,
  TreatmentApplicationCreate,
  TreatmentCreate,
  TreatmentDetail,
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

/**
 * Loads the complete pest catalogue by paging through the ``/ipm/pests`` list
 * endpoint until a short page is returned. That endpoint uses the shared
 * pagination dependency (``limit<=200``), so a fixed ``limit=500`` both 422'd
 * (over the cap, #614) and would silently truncate a large catalogue.
 *
 * Callers that need the whole set — the admin contributions overview, and the
 * list view, whose search and sort run client-side and are therefore only
 * truthful over a complete set (#995) — use this instead of ``listPests()``.
 */
export async function listAllPests(pageSize = CATALOGUE_PAGE_SIZE): Promise<Pest[]> {
  return fetchAllPages(listPests, pageSize);
}

export async function getPest(key: string): Promise<Pest> {
  const { data } = await globalClient.get<Pest>(`${BASE}/pests/${key}`);
  return data;
}

export async function getPestDetail(key: string): Promise<PestDetail> {
  const { data } = await globalClient.get<PestDetail>(`${BASE}/pests/${key}/detail`);
  return data;
}

// ── Pest reference images (tenant-scoped, user-contributed) ─────────────

/**
 * List a pest's reference images for the caller's tenant.
 *
 * `includeInactive` is a platform-admin-only curation flag: it additionally
 * returns *deselected* contribution / recognition tiles (the backend silently
 * ignores it for non-admins, so it is safe to send). Omitted by default so a
 * normal request stays a plain `GET …/images` (active-only).
 */
export async function listPestImages(
  pestKey: string,
  options?: { includeInactive?: boolean },
): Promise<PestImage[]> {
  const params = options?.includeInactive ? { include_inactive: true } : undefined;
  const { data } = await tenantClient.get<PestImage[]>(
    `${BASE}/pests/${pestKey}/images`,
    params ? { params } : undefined,
  );
  return data;
}

export async function contributePestImage(
  pestKey: string,
  file: File,
  caption?: string,
): Promise<PestImage> {
  const formData = new FormData();
  formData.append('file', file);
  if (caption) formData.append('caption', caption);
  const { data } = await tenantClient.post<PestImage>(
    `${BASE}/pests/${pestKey}/images`,
    formData,
    { headers: { 'Content-Type': 'multipart/form-data' } },
  );
  return data;
}

export async function deletePestImage(pestKey: string, imageId: string): Promise<void> {
  await tenantClient.delete(`${BASE}/pests/${pestKey}/images/${imageId}`);
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

/**
 * Loads the complete disease catalogue (same contract as {@link listAllPests}).
 * The list view uses this: its search and sort run client-side, so a bounded
 * first page would make the search deny rows that exist (#995).
 */
export async function listAllDiseases(
  pageSize = CATALOGUE_PAGE_SIZE,
): Promise<Disease[]> {
  return fetchAllPages(listDiseases, pageSize);
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

/**
 * Loads the complete treatment catalogue (same contract as {@link listAllPests}).
 * 40 treatments are seeded against a single-page default of 50 — under it today,
 * with ten rows of headroom, which is not a resting state: the list view reads
 * the whole catalogue so the 51st treatment does not vanish (#995).
 */
export async function listAllTreatments(
  pageSize = CATALOGUE_PAGE_SIZE,
): Promise<Treatment[]> {
  return fetchAllPages(listTreatments, pageSize);
}

export async function getTreatment(key: string): Promise<Treatment> {
  const { data } = await globalClient.get<Treatment>(`${BASE}/treatments/${key}`);
  return data;
}

export async function getTreatmentDetail(key: string): Promise<TreatmentDetail> {
  const { data } = await globalClient.get<TreatmentDetail>(`${BASE}/treatments/${key}/detail`);
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
