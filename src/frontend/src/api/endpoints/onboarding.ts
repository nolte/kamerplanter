import { tenantClient as client } from '../client';
import type { OnboardingState, ExperienceLevel, PlantConfig } from '../types';

const BASE = '/onboarding';

export async function getState(): Promise<OnboardingState> {
  const { data } = await client.get<OnboardingState>(`${BASE}/state`);
  return data;
}

export async function complete(
  payload: {
    kit_id?: string;
    experience_level?: ExperienceLevel;
    site_name?: string;
    selected_site_key?: string;
    plant_count?: number;
    plant_configs?: PlantConfig[];
    has_ro_system?: boolean;
    tap_water_ec_ms?: number;
    tap_water_ph?: number;
    favorite_species_keys?: string[];
    favorite_nutrient_plan_keys?: string[];
    smart_home_enabled?: boolean;
  },
): Promise<Record<string, unknown>> {
  const { data } = await client.post(`${BASE}/complete`, payload);
  return data as Record<string, unknown>;
}

export async function skip(): Promise<OnboardingState> {
  const { data } = await client.post<OnboardingState>(`${BASE}/skip`);
  return data;
}

export async function updateProgress(
  payload: {
    wizard_step: number;
    selected_kit_id?: string;
    selected_experience_level?: ExperienceLevel;
    site_name?: string;
    site_type?: string;
    selected_site_key?: string;
    plant_count?: number;
    plant_configs?: PlantConfig[];
    smart_home_enabled?: boolean;
  },
): Promise<OnboardingState> {
  const { data } = await client.patch<OnboardingState>(`${BASE}/state`, payload);
  return data;
}

export async function reset(): Promise<OnboardingState> {
  const { data } = await client.post<OnboardingState>(`${BASE}/reset`);
  return data;
}
