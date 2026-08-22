import { tenantClient, getActiveTenantSlug } from '../client';
import type {
  DiaryOverviewResponse,
  DiaryAnalysisState,
  DiaryEntryType,
  PlantDiaryEntry,
  PlantDiaryEntryCreate,
  PlantDiaryEntryUpdate,
  PlantEnvironmentPreview,
} from '../types';

/**
 * REQ-051 §6.1 / REQ-013 §4.7 — plant diary API layer.
 *
 * Modelled on `plantPhotos.ts`: every path is tenant-scoped and goes through
 * {@link tenantClient}, which prepends `/t/{slug}` on its own. The frontend
 * never constructs a tenant prefix by hand, with the single documented
 * exception of {@link diaryPhotoUri} below.
 */

const base = (plantInstanceKey: string) =>
  `/plant-instances/${plantInstanceKey}/diary`;

/** Maximum number of photos a single diary entry may carry (REQ-013, §2.5.1). */
export const DIARY_MAX_PHOTOS = 5;

/** Page size of the diary tab listing; the backend caps `limit` at 200. */
export const DIARY_PAGE_SIZE = 50;

/** Every diary entry type, in the order §2.5.2 lists them. */
export const DIARY_ENTRY_TYPES: readonly DiaryEntryType[] = [
  'observation',
  'problem',
  'milestone',
  'measurement',
  'photo',
  'note',
] as const;

/** Every analysis state, in state-machine order (§2.2). */
export const DIARY_ANALYSIS_STATES: readonly DiaryAnalysisState[] = [
  'none',
  'requested',
  'in_progress',
  'completed',
  'failed',
] as const;

/** GET — one plant's diary entries, newest first. */
export async function listPlantDiaryEntries(
  plantInstanceKey: string,
  params: { offset?: number; limit?: number } = {},
): Promise<PlantDiaryEntry[]> {
  const { data } = await tenantClient.get<PlantDiaryEntry[]>(base(plantInstanceKey), {
    params: { offset: params.offset ?? 0, limit: params.limit ?? DIARY_PAGE_SIZE },
  });
  return data;
}

/** GET — a single diary entry, including its full analysis result. */
export async function getPlantDiaryEntry(
  plantInstanceKey: string,
  entryKey: string,
): Promise<PlantDiaryEntry> {
  const { data } = await tenantClient.get<PlantDiaryEntry>(
    `${base(plantInstanceKey)}/${entryKey}`,
  );
  return data;
}

/**
 * GET — what an entry's environment snapshot would contain right now.
 *
 * REQ-013 §2.3a. A *preview*, never an input: the dialog renders it read-only
 * and sends nothing back but the opt-out flag, and the server re-resolves
 * everything at create time. The two may legitimately differ if a sensor answers
 * in between — the entry records what was true when it was written.
 */
export async function getPlantEnvironmentPreview(
  plantInstanceKey: string,
): Promise<PlantEnvironmentPreview> {
  const { data } = await tenantClient.get<PlantEnvironmentPreview>(
    `/plant-instances/${plantInstanceKey}/environment`,
  );
  return data;
}

/** POST — create a diary entry on this plant instance (201). */
export async function createPlantDiaryEntry(
  plantInstanceKey: string,
  body: PlantDiaryEntryCreate,
): Promise<PlantDiaryEntry> {
  const { data } = await tenantClient.post<PlantDiaryEntry>(base(plantInstanceKey), body);
  return data;
}

/** PUT — update a diary entry. Analysis fields are not part of the body. */
export async function updatePlantDiaryEntry(
  plantInstanceKey: string,
  entryKey: string,
  body: PlantDiaryEntryUpdate,
): Promise<PlantDiaryEntry> {
  const { data } = await tenantClient.put<PlantDiaryEntry>(
    `${base(plantInstanceKey)}/${entryKey}`,
    body,
  );
  return data;
}

/** DELETE — remove a diary entry together with its analysis result (204). */
export async function deletePlantDiaryEntry(
  plantInstanceKey: string,
  entryKey: string,
): Promise<void> {
  await tenantClient.delete(`${base(plantInstanceKey)}/${entryKey}`);
}

/**
 * POST — mark an entry for AI analysis (`none|completed|failed → requested`).
 *
 * Answers with the **entry**, not 204, so the caller can render the state it
 * actually landed in instead of guessing. A caller without the right gets a 403
 * (§7.2); an entry of another tenant or plant gets a 404, never a 403.
 */
export async function requestDiaryEntryAnalysis(
  plantInstanceKey: string,
  entryKey: string,
): Promise<PlantDiaryEntry> {
  const { data } = await tenantClient.post<PlantDiaryEntry>(
    `${base(plantInstanceKey)}/${entryKey}/request-analysis`,
  );
  return data;
}

/**
 * DELETE — withdraw the marking (`requested → none`), only while unclaimed.
 *
 * On an entry an agent has already claimed the server answers 409
 * (`conflict.invalid_state`) — that is AK-03, and the UI must not pretend
 * otherwise by hiding the failure.
 */
export async function cancelDiaryEntryAnalysis(
  plantInstanceKey: string,
  entryKey: string,
): Promise<PlantDiaryEntry> {
  const { data } = await tenantClient.delete<PlantDiaryEntry>(
    `${base(plantInstanceKey)}/${entryKey}/request-analysis`,
  );
  return data;
}

/** Query parameters of the tenant-wide overview (REQ-051 §6.2). */
export interface DiaryOverviewParams {
  /** Repeatable: several states widen the filter. */
  analysis_state?: DiaryAnalysisState[];
  plant_key?: string;
  species_key?: string;
  entry_type?: DiaryEntryType;
  tag?: string;
  /** `YYYY-MM-DD`, inclusive lower bound on `created_at`. */
  from?: string;
  /** `YYYY-MM-DD`, inclusive upper bound on `created_at`. */
  to?: string;
  /** Free-text search over title and text. */
  q?: string;
  sort?: 'created_at' | 'analyzed_at';
  limit?: number;
  offset?: number;
}

/**
 * GET — the tenant-wide diary overview (REQ-051 §6.2).
 *
 * The cross-plant view: every plant of the tenant in one chronological list,
 * with the slim row of {@link DiaryOverviewItem}.
 *
 * **Not** the source of the analysis verdict for a single plant. The diary tab
 * used to call this endpoint a second time per open, filtered to one plant,
 * purely to read `can_request_analysis` — the entry payload did not carry it.
 * It does now ({@link PlantDiaryEntry}), evaluated server-side from the same
 * rule, so that second request is gone.
 */
export async function listDiaryOverview(
  params: DiaryOverviewParams = {},
): Promise<DiaryOverviewResponse> {
  const { data } = await tenantClient.get<DiaryOverviewResponse>('/diary', {
    params,
    // axios serialises `analysis_state: ['a','b']` as `analysis_state[]=a` by
    // default; FastAPI expects the parameter repeated without brackets.
    paramsSerializer: { indexes: null },
  });
  return data;
}

/** A diary photo as returned right after upload. */
export interface DiaryPhotoUploadResult {
  attachment_id: string;
  mime_type: string;
  byte_size: number;
}

/**
 * POST — upload a diary photo and return its attachment id.
 *
 * Goes to the generic attachment endpoint with `category=diary`, **not** to
 * `/plant-instances/{key}/photos`. The gallery endpoint stores
 * `category=plant` and links the file into the plant's gallery
 * (`photo_router.py:152`); a diary photo is neither. REQ-050 §0 pins diary
 * photos to `category = diary`, which is also what the DSGVO erasure scope and
 * the `STORAGE_KEEP_EXIF_DIARY` setting key off.
 */
export async function uploadDiaryPhoto(file: File): Promise<DiaryPhotoUploadResult> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('category', 'diary');
  const { data } = await tenantClient.post<DiaryPhotoUploadResult>('/attachments', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data;
}

/** Thumbnail renditions the backend generates for every image (NFR-013 §8.2). */
export type DiaryPhotoSize = 128 | 512 | 1280;

/**
 * Build the authenticated URI of a diary photo attachment.
 *
 * A diary entry stores bare attachment ids in `photo_refs`, not URIs — unlike a
 * gallery photo, which arrives with `uri`/`thumbnail_uris` already built by the
 * server. The shape mirrors `_base_uri()` in
 * `app/api/v1/attachments/tenant_router.py` exactly; pass the result to
 * {@link AuthImage}, which strips the `/api/v1` prefix again and sends the
 * Bearer header a bare `<img src>` could not.
 */
export function diaryPhotoUri(attachmentId: string, size?: DiaryPhotoSize): string {
  const slug = getActiveTenantSlug() ?? '';
  const uri = `/api/v1/t/${slug}/attachments/${attachmentId}`;
  return size ? `${uri}/thumbnails/${size}` : uri;
}
