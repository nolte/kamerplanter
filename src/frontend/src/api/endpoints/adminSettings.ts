import client from '../client';

export interface HASettingsResponse {
  ha_url: string;
  ha_access_token_masked: string;
  ha_timeout: number;
  source_ha_url: string;
  source_ha_access_token: string;
  source_ha_timeout: string;
}

export interface SystemSettingsResponse {
  home_assistant: HASettingsResponse;
}

export interface HASettingsUpdate {
  ha_url?: string | null;
  ha_access_token?: string | null;
  ha_timeout?: number | null;
}

export interface HATestRequest {
  ha_url?: string | null;
  ha_access_token?: string | null;
  ha_timeout?: number | null;
}

export interface HATestResponse {
  success: boolean;
  message: string;
  ha_version?: string | null;
}

const BASE = '/admin/settings';

export async function getSystemSettings(): Promise<SystemSettingsResponse> {
  const { data } = await client.get<SystemSettingsResponse>(BASE);
  return data;
}

export async function updateHaSettings(
  body: HASettingsUpdate,
): Promise<SystemSettingsResponse> {
  const { data } = await client.put<SystemSettingsResponse>(`${BASE}/home-assistant`, body);
  return data;
}

export async function testHaConnection(
  body: HATestRequest,
): Promise<HATestResponse> {
  const { data } = await client.post<HATestResponse>(`${BASE}/home-assistant/test`, body);
  return data;
}

export async function clearHaSettings(): Promise<void> {
  await client.delete(`${BASE}/home-assistant`);
}
