import client from '../client';
import type { UserPreference, ExperienceLevel } from '../types';

export async function getPreferences(): Promise<UserPreference> {
  const { data } = await client.get<UserPreference>('/user-preferences');
  return data;
}

export async function updatePreferences(updates: {
  experience_level?: ExperienceLevel;
  locale?: string;
  theme?: string;
  onboarding_completed?: boolean;
}): Promise<UserPreference> {
  const { data } = await client.patch<UserPreference>('/user-preferences', updates);
  return data;
}
