import type { AuthProviderInfo } from '@/api/types';

/** What the requester supplied to confirm a step-up — the credential part of it. */
export interface StepUpCredentials {
  /** The requester's current password; absent when it is not asked for. */
  password?: string;
  /** The e-mailed one-time code (#1815); absent when it is not asked for. */
  code?: string;
  /** The one-time token of a fresh sign-in at the identity provider (#1815). */
  token?: string;
}

/**
 * Whether the provider list proves the requester has a local password.
 *
 * Tri-state, and deliberately so (#1791, #1842): `true` when the list names a
 * `local` provider, `false` only when a **non-empty** list lacks one (positive
 * proof of a federated-only account), `null` when unknown — still loading,
 * failed, or empty. An empty list is unknown because seeded accounts carry a
 * password hash without a `local` provider row (#1791 review SEC-003).
 */
export function hasLocalPasswordFromProviders(
  providers: readonly AuthProviderInfo[] | null | undefined,
): boolean | null {
  if (!providers || providers.length === 0) return null;
  return providers.some((p) => p.provider === 'local');
}

/**
 * The request-body fields for a step-up credential, in the backend's naming.
 *
 * Only what was supplied is carried: a federated-only account sends no
 * `password`, an account with a local password sends no `step_up_code` or
 * `step_up_token`.
 */
export function toStepUpBody({ password, code, token }: StepUpCredentials): {
  password?: string;
  step_up_code?: string;
  step_up_token?: string;
} {
  const body: { password?: string; step_up_code?: string; step_up_token?: string } = {};
  if (password !== undefined) body.password = password;
  if (code !== undefined) body.step_up_code = code;
  if (token !== undefined) body.step_up_token = token;
  return body;
}
