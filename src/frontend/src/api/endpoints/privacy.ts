import client from '../client';
import type { ConsentRecord } from '../types';

/**
 * REQ-025 — privacy / consent self-service (Art. 7 DSGVO).
 *
 * Used by feature-level consent gates (e.g. REQ-029 plant identification)
 * to read and grant the per-purpose consent the backend requires.
 */

const BASE = '/privacy';

/** GET /privacy/consents — all known purposes with current consent state. */
export async function listConsents(): Promise<ConsentRecord[]> {
  const { data } = await client.get<ConsentRecord[]>(`${BASE}/consents`);
  return data;
}

/** POST /privacy/consents — grant consent for a processing purpose. */
export async function grantConsent(purpose: string): Promise<ConsentRecord> {
  const { data } = await client.post<ConsentRecord>(`${BASE}/consents`, { purpose });
  return data;
}

/** DELETE /privacy/consents/{purpose} — revoke an optional consent. */
export async function revokeConsent(purpose: string): Promise<ConsentRecord> {
  const { data } = await client.delete<ConsentRecord>(`${BASE}/consents/${purpose}`);
  return data;
}
