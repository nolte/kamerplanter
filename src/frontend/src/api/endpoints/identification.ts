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

/** GET /t/{slug}/identification/history?limit=N. */
export async function listIdentificationHistory(
  limit = 20,
): Promise<IdentificationHistoryEntry[]> {
  const { data } = await tenantClient.get<IdentificationHistoryEntry[]>(`${BASE}/history`, {
    params: { limit },
  });
  return data;
}
