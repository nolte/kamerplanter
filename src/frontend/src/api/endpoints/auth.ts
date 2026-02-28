import client from '../client';
import type {
  ApiKeyCreate,
  ApiKeyCreated,
  ApiKeySummary,
  AuthProviderInfo,
  LoginRequest,
  LoginResponse,
  OAuthProviderListItem,
  RegisterRequest,
  SessionInfo,
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

export async function unlinkProvider(providerKey: string): Promise<void> {
  await client.delete(`${USERS}/me/providers/${providerKey}`);
}

export async function changePassword(
  currentPassword: string | null,
  newPassword: string,
): Promise<void> {
  await client.post(`${USERS}/me/password`, {
    current_password: currentPassword,
    new_password: newPassword,
  });
}

export async function listSessions(): Promise<SessionInfo[]> {
  const res = await client.get<SessionInfo[]>(`${USERS}/me/sessions`);
  return res.data;
}

export async function revokeSession(sessionKey: string): Promise<void> {
  await client.delete(`${USERS}/me/sessions/${sessionKey}`);
}

export async function deleteAccount(): Promise<void> {
  await client.delete(`${USERS}/me`);
}

// ── API Keys ──────────────────────────────────────────────────────

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
