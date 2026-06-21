import client from '../client';
import type {
  PestAcquireResponse,
  PestContributionList,
  PestCurationImageList,
  PestRecognitionStatus,
  PromotePestContributionResponse,
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

/**
 * PATCH /admin/pests/{label}/images/{id} — deselect/re-include a reference image.
 *
 * Deselected images are kept (audit trail) but excluded from few-shot matching,
 * so a wrongly-acquired image no longer skews the detection result.
 */
export async function setPestImageActive(
  label: string,
  imageId: number,
  payload: { is_active: boolean; reason?: string | null },
): Promise<{ label: string; id: number; is_active: boolean }> {
  const { data } = await client.patch<{ label: string; id: number; is_active: boolean }>(
    `${BASE}/${label}/images/${imageId}`,
    payload,
  );
  return data;
}

// ── REQ-010 — user-contributed pest image moderation (global promotion) ──
//
// Cross-tenant, platform-admin-only. Lets the admin review every tenant's
// contributed photos for a pest and promote the good ones to global visibility.

/**
 * GET /admin/pests/{pestKey}/contributions — list ALL tenants' contributed
 * images for a pest (cross-tenant moderation feed).
 */
export async function listPestContributions(pestKey: string): Promise<PestContributionList> {
  const { data } = await client.get<PestContributionList>(`${BASE}/${pestKey}/contributions`);
  return data;
}

/**
 * PATCH /admin/pests/{pestKey}/contributions/{id} — promote/demote a single
 * contribution to/from global visibility (idempotent).
 */
export async function setPestContributionPromotion(
  pestKey: string,
  contributionId: string,
  promote: boolean,
): Promise<PromotePestContributionResponse> {
  const { data } = await client.patch<PromotePestContributionResponse>(
    `${BASE}/${pestKey}/contributions/${contributionId}`,
    { promote },
  );
  return data;
}
