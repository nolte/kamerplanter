import client from '../client';
import type { OnboardingState, ExperienceLevel } from '../types';

export async function getState(userKey = 'demo'): Promise<OnboardingState> {
  const { data } = await client.get<OnboardingState>('/onboarding/state', {
    params: { user_key: userKey },
  });
  return data;
}

export async function complete(payload: {
  kit_id?: string;
  experience_level?: ExperienceLevel;
  site_name?: string;
  plant_count?: number;
}): Promise<Record<string, unknown>> {
  const { data } = await client.post('/onboarding/complete', payload);
  return data as Record<string, unknown>;
}

export async function skip(): Promise<OnboardingState> {
  const { data } = await client.post<OnboardingState>('/onboarding/skip');
  return data;
}

export async function updateProgress(payload: {
  wizard_step: number;
  selected_kit_id?: string;
  selected_experience_level?: ExperienceLevel;
}): Promise<OnboardingState> {
  const { data } = await client.patch<OnboardingState>('/onboarding/state', payload);
  return data;
}
