import client from '../client';
import type {
  PestAcquireResponse,
  PestCurationImageList,
  PestRecognitionStatus,
} from '../types';

/**
 * REQ-044 — admin API for the few-shot pest-recognition index.
 *
 * Platform-admin-only (in light mode the system user is the admin). Mirrors the
 * REQ-029-A recognition admin: coverage per class, a UI-startable acquisition
 * job, and the per-class reference-image gallery.
 */

const BASE = '/admin/pests';

/** GET /admin/pests/status — coverage per class + service availability. */
export async function getPestRecognitionStatus(): Promise<PestRecognitionStatus> {
  const { data } = await client.get<PestRecognitionStatus>(`${BASE}/status`);
  return data;
}

/** POST /admin/pests/acquire — start the cold-start acquisition job. */
export async function startPestAcquisition(): Promise<PestAcquireResponse> {
  const { data } = await client.post<PestAcquireResponse>(`${BASE}/acquire`);
  return data;
}

/** GET /admin/pests/{label}/images — reference-image gallery for one class. */
export async function getPestClassImages(label: string): Promise<PestCurationImageList> {
  const { data } = await client.get<PestCurationImageList>(`${BASE}/${label}/images`);
  return data;
}
