import { tenantClient } from '../client';
import type {
  PestCreateInspectionResult,
  PestDetectionResult,
  PestDetectionStatus,
} from '../types';

/**
 * REQ-044 — image-based pest detection API layer.
 *
 * All endpoints are tenant-scoped and run through {@link tenantClient}, which
 * prepends /t/{slug} automatically. The detection never triggers a treatment;
 * the strongest follow-up is an IPM inspection. Every response carries a
 * disclaimer (§8).
 */

const BASE = '/pests';

/** GET /t/{slug}/pests/status — which adapter is active (or none → hide button). */
export async function getPestDetectionStatus(): Promise<PestDetectionStatus> {
  const { data } = await tenantClient.get<PestDetectionStatus>(`${BASE}/status`);
  return data;
}

/** POST /t/{slug}/pests/plants/{plantKey}/detect — multipart image upload. */
export async function detectPests(
  plantKey: string,
  image: File,
  language = 'de',
): Promise<PestDetectionResult> {
  const formData = new FormData();
  formData.append('image', image);
  formData.append('language', language);
  const { data } = await tenantClient.post<PestDetectionResult>(
    `${BASE}/plants/${plantKey}/detect`,
    formData,
    { headers: { 'Content-Type': 'multipart/form-data' } },
  );
  return data;
}

/** GET /t/{slug}/pests/plants/{plantKey}/history?limit=N. */
export async function listPestDetectionHistory(
  plantKey: string,
  limit = 20,
): Promise<PestDetectionResult[]> {
  const { data } = await tenantClient.get<PestDetectionResult[]>(
    `${BASE}/plants/${plantKey}/history`,
    { params: { limit } },
  );
  return data;
}

/** POST /t/{slug}/pests/detections/{key}/feedback — HITL feedback (§5.3). */
export async function submitPestFeedback(
  detectionKey: string,
  body: { finding_label: string; confirmed: boolean; actual_label?: string | null; was_beneficial?: boolean },
): Promise<PestDetectionResult> {
  const { data } = await tenantClient.post<PestDetectionResult>(
    `${BASE}/detections/${detectionKey}/feedback`,
    body,
  );
  return data;
}

/** POST /t/{slug}/pests/detections/{key}/create-inspection?plant_key=… (REQ-010). */
export async function createInspectionFromDetection(
  detectionKey: string,
  plantKey: string,
): Promise<PestCreateInspectionResult> {
  const { data } = await tenantClient.post<PestCreateInspectionResult>(
    `${BASE}/detections/${detectionKey}/create-inspection`,
    null,
    { params: { plant_key: plantKey } },
  );
  return data;
}
