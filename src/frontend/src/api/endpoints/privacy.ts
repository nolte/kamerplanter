import client from '../client';
import type {
  ConsentRecord,
  EmailChangeCreateRequest,
  EmailChangeResponse,
  PrivacyMessageResponse,
} from '../types';

/**
 * REQ-025 — privacy self-service (DSGVO).
 *
 * Consents (Art. 7) are read and granted by feature-level consent gates (e.g.
 * REQ-029 plant identification); the e-mail change (Art. 16) is requested from
 * the account settings and confirmed or reverted from the links in the mails.
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

/**
 * POST /privacy/email-change — request an e-mail change behind the step-up
 * (#1841). 201: a verification link goes to the new address and the current
 * one is told; nothing changes until the link is followed.
 */
export async function requestEmailChange(body: EmailChangeCreateRequest): Promise<EmailChangeResponse> {
  const { data } = await client.post<EmailChangeResponse>(`${BASE}/email-change`, body);
  return data;
}

/**
 * POST /privacy/email-change/confirm — public; the token from the link mailed to
 * the new address. 401 `INVALID_TOKEN` for an unknown, expired or withdrawn one.
 * On success every session of the account is signed out.
 */
export async function confirmEmailChange(token: string): Promise<PrivacyMessageResponse> {
  const { data } = await client.post<PrivacyMessageResponse>(`${BASE}/email-change/confirm`, { token });
  return data;
}

/**
 * POST /privacy/email-change/revert — public; the token from the notice mailed to
 * the previous address (#1848). Restores that address, signs out every session
 * and voids pending password-reset links. 401 `INVALID_TOKEN` for an unknown,
 * spent or expired token; 422 when the previous address now belongs to another
 * account.
 */
export async function revertEmailChange(token: string): Promise<PrivacyMessageResponse> {
  const { data } = await client.post<PrivacyMessageResponse>(`${BASE}/email-change/revert`, { token });
  return data;
}
