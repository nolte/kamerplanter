import { tenantClient as client } from '../client';
import type { UserPreference, ExperienceLevel, ModuleVisibilityState } from '../types';

const BASE = '/user-preferences';

export async function getPreferences(): Promise<UserPreference> {
  const { data } = await client.get<UserPreference>(BASE);
  return data;
}

export async function updatePreferences(
  updates: {
    experience_level?: ExperienceLevel;
    locale?: string;
    theme?: string;
    onboarding_completed?: boolean;
    watering_can_liters?: number;
    smart_home_enabled?: boolean;
    module_visibility?: Record<string, ModuleVisibilityState>;
  },
): Promise<UserPreference> {
  const { data } = await client.patch<UserPreference>(BASE, updates);
  return data;
}
