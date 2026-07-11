import client, { tenantClient } from '../client';
import type {
  IdentificationHistoryEntry,
  IdentificationSelection,
  IdentificationStatus,
  IdentifyResult,
  PlantOrgan,
} from '../types';

/**
 * REQ-029 / REQ-029-A — AI plant identification API layer.
 *
 * The status endpoint is public (no tenant/auth) so the camera UI can be
 * toggled before login. All processing endpoints are tenant-scoped and run
 * through {@link tenantClient}, which prepends /t/{slug} automatically.
 */

const BASE = '/identification';

/** GET /recognition/status — public feature/adapter availability. */
export async function getIdentificationStatus(): Promise<IdentificationStatus> {
  const { data } = await client.get<IdentificationStatus>('/recognition/status');
  return data;
}

/**
 * POST /t/{slug}/identification/identify — multipart image upload.
 *
 * Consent `plant_identification` is enforced server-side; a 403
 * CONSENT_REQUIRED is surfaced to the caller for the consent gate.
 */
export async function identifyPlant(
  image: File,
  organ: PlantOrgan = 'auto',
  language = 'de',
): Promise<IdentifyResult> {
  const formData = new FormData();
  formData.append('image', image);
  formData.append('organ', organ);
  formData.append('language', language);
  const { data } = await tenantClient.post<IdentifyResult>(`${BASE}/identify`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data;
}

/** POST /t/{slug}/identification/{request_key}/select?selected_rank=N. */
export async function selectIdentificationResult(
  requestKey: string,
  selectedRank: number,
): Promise<IdentificationSelection> {
  const { data } = await tenantClient.post<IdentificationSelection>(
    `${BASE}/${requestKey}/select`,
    null,
    { params: { selected_rank: selectedRank } },
  );
  return data;
}

/** Adapter key of the self-hosted DINOv2 identification path (REQ-029-A). */
export const LOCAL_EMBEDDING_ADAPTER_KEY = 'local_embedding';

/** Result of contributing an identification photo as a species reference. */
export interface ReferenceContributionResult {
  indexed: boolean;
  species_key: string;
  dim: number | null;
}

/**
 * POST /t/{slug}/identification/reference — reuse an identification photo as a
 * DINOv2 few-shot reference for the resolved species (issue #447).
 *
 * Only meaningful when the self-hosted DINOv2 adapter is active; the backend
 * returns 409 ADAPTER_NOT_AVAILABLE otherwise. The photo is embedded locally
 * and indexed in pgvector; the original image is never persisted.
 */
export async function contributeReferenceImage(
  speciesKey: string,
  scientificName: string,
  image: File,
): Promise<ReferenceContributionResult> {
  const formData = new FormData();
  formData.append('image', image);
  formData.append('species_key', speciesKey);
  formData.append('scientific_name', scientificName);
  const { data } = await tenantClient.post<ReferenceContributionResult>(
    `${BASE}/reference`,
    formData,
    { headers: { 'Content-Type': 'multipart/form-data' } },
  );
  return data;
}

/** GET /t/{slug}/identification/history?limit=N. */
export async function listIdentificationHistory(
  limit = 20,
): Promise<IdentificationHistoryEntry[]> {
  const { data } = await tenantClient.get<IdentificationHistoryEntry[]>(`${BASE}/history`, {
    params: { limit },
  });
  return data;
}
