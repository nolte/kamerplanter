import { tenantClient as client } from '../client';
import type { UserPreference, ExperienceLevel, ModuleVisibilityState, DashboardLayout } from '../types';

const BASE = '/user-preferences';

export interface UserPreferenceUpdate {
  experience_level?: ExperienceLevel;
  locale?: string;
  theme?: string;
  onboarding_completed?: boolean;
  watering_can_liters?: number;
  smart_home_enabled?: boolean;
  /** UI-NFR-019 — kiosk shell + high-contrast theme flags. */
  kiosk_enabled?: boolean;
  high_contrast?: boolean;
  module_visibility?: Record<string, ModuleVisibilityState>;
  /** REQ-045 — explicit null resets to the experience-level default. */
  dashboard_layout?: DashboardLayout | null;
}

export async function getPreferences(): Promise<UserPreference> {
  const { data } = await client.get<UserPreference>(BASE);
  return data;
}

export async function updatePreferences(updates: UserPreferenceUpdate): Promise<UserPreference> {
  const { data } = await client.patch<UserPreference>(BASE, updates);
  return data;
}
