import apiClient from '@/api/client';
import type {
  CredentialStepUp,
  OidcProvider,
  OidcProviderCreate,
  OidcProviderTestResult,
  OidcProviderUpdate,
} from '@/api/types';

/**
 * #1906 — platform-admin API for the installation's OIDC / OAuth provider
 * configurations. Global (NOT tenant-scoped), so the plain `apiClient` on
 * `/admin/...` like `adminPlatform.ts`. The client secret is write-only: it goes
 * out in a create/update body and is never part of any response.
 */

const BASE = '/admin/oidc-providers';

export async function listOidcProviders(): Promise<OidcProvider[]> {
  const { data } = await apiClient.get<OidcProvider[]>(BASE);
  return data;
}

/**
 * Create a provider (#1883). The body carries the **admin's own** step-up —
 * `current_password`, or `step_up_token` / `step_up_code` for the act
 * `oidc_provider_change` with the target `new:<slug>`; 401 without it.
 */
export async function createOidcProvider(payload: OidcProviderCreate): Promise<OidcProvider> {
  const { data } = await apiClient.post<OidcProvider>(BASE, payload);
  return data;
}

/**
 * Partial update. Anything beyond `display_name` / `icon_url` (including switching the
 * provider on or off and sending a new client secret) carries the admin's step-up for
 * `oidc_provider_change`, bound to the configuration's key.
 */
export async function updateOidcProvider(
  key: string,
  payload: OidcProviderUpdate,
): Promise<OidcProvider> {
  const { data } = await apiClient.put<OidcProvider>(`${BASE}/${encodeURIComponent(key)}`, payload);
  return data;
}

/** Delete a provider and every sign-in link made through it; the body is the step-up only. */
export async function deleteOidcProvider(key: string, stepUp: CredentialStepUp): Promise<void> {
  await apiClient.delete(`${BASE}/${encodeURIComponent(key)}`, { data: stepUp });
}

/** Fetch and judge the discovery document; stores it on success. Needs no step-up. */
export async function testOidcProvider(key: string): Promise<OidcProviderTestResult> {
  const { data } = await apiClient.post<OidcProviderTestResult>(
    `${BASE}/${encodeURIComponent(key)}/test`,
  );
  return data;
}
