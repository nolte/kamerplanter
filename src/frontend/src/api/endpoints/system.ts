import client from '../client';
import type { CredentialStepUp, TakeoverResult, TakeoverStatus } from '../types';

/**
 * REQ-027 §7a (#1855) — the take-over of a former light-mode installation's data.
 *
 * Mounted in full mode only. After the switch from light to full, the platform administrator
 * (or, on an instance without one, the first account) decides whether the light-mode garden
 * becomes theirs.
 */

const BASE = '/system';

/** GET /system/takeover-status — whether a take-over is open and whether the caller may decide it. */
export async function getTakeoverStatus(): Promise<TakeoverStatus> {
  const { data } = await client.get<TakeoverStatus>(`${BASE}/takeover-status`);
  return data;
}

/**
 * POST /system/takeover — accept (`true`) or decline (`false`) the take-over, with the caller's own
 * step-up (`light_mode_takeover`, bound to the light-mode garden's key).
 */
export async function decideTakeover(accept: boolean, stepUp: CredentialStepUp): Promise<TakeoverResult> {
  const { data } = await client.post<TakeoverResult>(`${BASE}/takeover`, { accept, ...stepUp });
  return data;
}
