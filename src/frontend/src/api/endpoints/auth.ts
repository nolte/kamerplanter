import client from '../client';
import type {
  AccountErasureRequest,
  ApiKeyCreate,
  ApiKeyCreated,
  ApiKeySummary,
  AuthProviderInfo,
  CredentialStepUp,
  DevicePairingCreated,
  LoginRequest,
  LoginResponse,
  OAuthProviderListItem,
  PasswordChangeRequest,
  RegisterRequest,
  SessionInfo,
  StepUpAction,
  StepUpCodeRequest,
  StepUpCodeSent,
  StepUpReauthRequest,
  StepUpReauthStart,
  UserProfile,
  UserProfileUpdate,
} from '../types';

const BASE = '/auth';
const USERS = '/users';

function getCsrfToken(): string | null {
  const match = document.cookie.match(/(?:^|;\s*)csrf_token=([^;]*)/);
  return match ? decodeURIComponent(match[1]) : null;
}

function csrfHeaders(): Record<string, string> {
  const token = getCsrfToken();
  return token ? { 'X-CSRF-Token': token } : {};
}

// ── Auth endpoints ────────────────────────────────────────────────

export async function register(data: RegisterRequest): Promise<UserProfile> {
  const res = await client.post<UserProfile>(`${BASE}/register`, data);
  return res.data;
}

export async function login(data: LoginRequest): Promise<LoginResponse> {
  const res = await client.post<LoginResponse>(`${BASE}/login`, data);
  return res.data;
}

export async function refresh(): Promise<LoginResponse> {
  const res = await client.post<LoginResponse>(`${BASE}/refresh`, null, {
    headers: csrfHeaders(),
  });
  return res.data;
}

export async function logout(): Promise<void> {
  await client.post(`${BASE}/logout`, null, { headers: csrfHeaders() });
}

export async function logoutAll(): Promise<void> {
  await client.post(`${BASE}/logout-all`, null, { headers: csrfHeaders() });
}

export async function verifyEmail(token: string): Promise<UserProfile> {
  const res = await client.post<UserProfile>(`${BASE}/verify-email`, { token });
  return res.data;
}

export async function requestPasswordReset(email: string): Promise<void> {
  await client.post(`${BASE}/password-reset/request`, { email });
}

export async function confirmPasswordReset(token: string, newPassword: string): Promise<void> {
  await client.post(`${BASE}/password-reset/confirm`, { token, new_password: newPassword });
}

export async function getOAuthProviders(): Promise<OAuthProviderListItem[]> {
  const res = await client.get<OAuthProviderListItem[]>(`${BASE}/oauth/providers`);
  return res.data;
}

// ── User profile endpoints ────────────────────────────────────────

export async function getProfile(): Promise<UserProfile> {
  const res = await client.get<UserProfile>(`${USERS}/me`);
  return res.data;
}

export async function updateProfile(data: UserProfileUpdate): Promise<UserProfile> {
  const res = await client.patch<UserProfile>(`${USERS}/me`, data);
  return res.data;
}

export async function listProviders(): Promise<AuthProviderInfo[]> {
  const res = await client.get<AuthProviderInfo[]>(`${USERS}/me/providers`);
  return res.data;
}

/**
 * Remove a sign-in method from the own account.
 *
 * A credential change (#1847): the body carries the step-up — the current
 * password or, for an account without one, `step_up_token` / `step_up_code` for
 * the act `provider_unlink`. Without it the backend answers 401.
 */
export async function unlinkProvider(providerKey: string, stepUp?: CredentialStepUp): Promise<void> {
  const url = `${USERS}/me/providers/${encodeURIComponent(providerKey)}`;
  if (stepUp) {
    await client.delete(url, { data: stepUp });
  } else {
    await client.delete(url);
  }
}

/**
 * Change (or, for an account without one, set) the own password.
 *
 * An account with a local password confirms with `currentPassword`; one without
 * sends `null` and confirms with the e-mailed `stepUpCode` or — when a linked
 * provider can prove a fresh sign-in — with the `stepUpToken` of that sign-in
 * instead (#1815).
 */
export async function changePassword(
  currentPassword: string | null,
  newPassword: string,
  stepUpCode?: string,
  stepUpToken?: string,
): Promise<void> {
  const body: PasswordChangeRequest = {
    current_password: currentPassword,
    new_password: newPassword,
  };
  if (stepUpCode) body.step_up_code = stepUpCode;
  if (stepUpToken) body.step_up_token = stepUpToken;
  await client.post(`${USERS}/me/password`, body);
}

/**
 * E-mail a one-time step-up code for `action` to the signed-in user (#1815).
 *
 * The code confirms that act only (review SEC-003). Only for an account without
 * a local password — the backend answers 422 for one that has a password, 403
 * for an API-key caller and 429 `STEP_UP_LOCKED` while the step-up is throttled,
 * an unspent code is younger than a minute, or the hourly code budget is spent
 * (review SEC-002).
 */
export async function requestStepUpCode(action: StepUpAction): Promise<StepUpCodeSent> {
  const body: StepUpCodeRequest = { action };
  const res = await client.post<StepUpCodeSent>(`${USERS}/me/step-up-code`, body);
  return res.data;
}

/**
 * Start a fresh sign-in at a linked identity provider to confirm `action` (#1815).
 *
 * Answers the provider's authorization URL; the browser goes there and comes
 * back to `/auth/step-up/callback` with a one-time `step_up_token` in the URL
 * fragment. `providerKey` names one of the account's links
 * (`GET /users/me/providers`); omitted, the backend picks the first link that
 * can prove a fresh sign-in. The backend answers 403 for an API-key caller, a
 * service account or light mode, 422 when the account has a local password or
 * no linked provider can re-authenticate (the e-mailed code applies then), and
 * 429 `STEP_UP_LOCKED` while the step-up is locked.
 */
export async function startStepUpReauth(
  action: StepUpAction,
  providerKey?: string,
  clientNonce?: string,
): Promise<StepUpReauthStart> {
  const body: StepUpReauthRequest = { action };
  if (providerKey) body.provider_key = providerKey;
  if (clientNonce) body.client_nonce = clientNonce;
  const res = await client.post<StepUpReauthStart>(`${USERS}/me/step-up/oidc`, body);
  return res.data;
}

export async function listSessions(): Promise<SessionInfo[]> {
  const res = await client.get<SessionInfo[]>(`${USERS}/me/sessions`);
  return res.data;
}

export async function revokeSession(sessionKey: string): Promise<void> {
  await client.delete(`${USERS}/me/sessions/${sessionKey}`);
}

/**
 * Close the own account (#1813): opens the Art. 17 erasure request — the account
 * is closed at once and hard-deleted after the grace period. The body echoes the
 * own e-mail and, for an account with a local password, the current password.
 */
export async function deleteAccount(stepUp: AccountErasureRequest): Promise<void> {
  await client.delete(`${USERS}/me`, { data: stepUp });
}

// ── API Keys ──────────────────────────────────────────────────────

/**
 * Mint an M2M API key. In full mode this is a credential change (#1847): `data`
 * carries the step-up of the act `api_key_creation`; light mode (REQ-027) needs
 * none, every request there already is the system account.
 */
export async function createApiKey(data: ApiKeyCreate): Promise<ApiKeyCreated> {
  const res = await client.post<ApiKeyCreated>(`${BASE}/api-keys`, data);
  return res.data;
}

export async function listApiKeys(): Promise<ApiKeySummary[]> {
  const res = await client.get<ApiKeySummary[]>(`${BASE}/api-keys`);
  return res.data;
}

export async function revokeApiKey(keyId: string): Promise<void> {
  await client.delete(`${BASE}/api-keys/${keyId}`);
}

// ── Device pairing (QR) ───────────────────────────────────────────

/**
 * Mint a one-time QR pairing code for the signed-in user (#1118).
 *
 * Bearer-authenticated like {@link createApiKey}, so no CSRF header is sent —
 * the endpoint spends no ambient cookie credential. The backend answers **201**;
 * the raw code is returned exactly once and is never retrievable afterwards.
 *
 * The code redeems into a full session, so minting it is a credential change
 * (#1847): `stepUp` carries the current password or, for an account without
 * one, `step_up_token` / `step_up_code` for the act `device_pairing`.
 */
export async function createDevicePairing(stepUp?: CredentialStepUp): Promise<DevicePairingCreated> {
  const res = await client.post<DevicePairingCreated>(`${BASE}/device-pairing`, stepUp ?? null);
  return res.data;
}
