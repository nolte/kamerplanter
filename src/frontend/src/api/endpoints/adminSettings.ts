import client from '../client';
import type { RecognitionStatus } from '../types';

export interface HASettingsResponse {
  ha_url: string;
  ha_access_token_masked: string;
  ha_timeout: number;
  source_ha_url: string;
  source_ha_access_token: string;
  source_ha_timeout: string;
}

export interface PlantIdentificationSettingsResponse {
  plantnet_api_key_masked: string;
  source_plantnet_api_key: string;
}

export interface SystemSettingsResponse {
  home_assistant: HASettingsResponse;
  plant_identification: PlantIdentificationSettingsResponse;
}

export interface PlantIdentificationSettingsUpdate {
  plantnet_api_key?: string | null;
}

export interface PlantIdentificationTestRequest {
  plantnet_api_key?: string | null;
}

export interface PlantIdentificationTestResponse {
  success: boolean;
  message: string;
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

export async function updatePlantIdentificationSettings(
  body: PlantIdentificationSettingsUpdate,
): Promise<SystemSettingsResponse> {
  const { data } = await client.put<SystemSettingsResponse>(
    `${BASE}/plant-identification`,
    body,
  );
  return data;
}

export async function testPlantIdentificationKey(
  body: PlantIdentificationTestRequest,
): Promise<PlantIdentificationTestResponse> {
  const { data } = await client.post<PlantIdentificationTestResponse>(
    `${BASE}/plant-identification/test`,
    body,
  );
  return data;
}

export async function clearPlantIdentificationSettings(): Promise<void> {
  await client.delete(`${BASE}/plant-identification`);
}

/**
 * GET /admin/recognition/status — platform-admin-only, global (no tenant slug).
 *
 * Returns the read-only status of the self-hosted DINOv2 image recognition
 * (REQ-029-A): feature/adapter availability, inference-service health, species
 * coverage and the effective configuration sourced from server env/settings.
 */
export async function getRecognitionStatus(): Promise<RecognitionStatus> {
  const { data } = await client.get<RecognitionStatus>('/admin/recognition/status');
  return data;
}

/** Result of starting a reference-image acquisition run from the UI. */
export interface AcquisitionStartResponse {
  status: string;
  task_id: string | null;
}

/**
 * POST /admin/recognition/acquire — dispatch a reference-image acquisition run
 * for all species (GBIF + Wikimedia → pgvector index). Available in light + full
 * mode for any signed-in user (like the recognition status + Pl@ntNet settings).
 */
export async function startRecognitionAcquisition(): Promise<AcquisitionStartResponse> {
  const { data } = await client.post<AcquisitionStartResponse>('/admin/recognition/acquire');
  return data;
}
