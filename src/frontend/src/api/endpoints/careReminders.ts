import client from '../client';
import type {
  CareProfile,
  CareConfirmation,
  CareDashboardEntry,
  ReminderType,
} from '../types';

const BASE = '/care-reminders';

export interface ConfirmFeedingDetail {
  fertilizer_key: string;
  ml_applied: number;
}

export interface ConfirmReminderOptions {
  notes?: string;
  volume_liters?: number;
  fertilizers_used?: ConfirmFeedingDetail[];
  measured_ec?: number;
  measured_ph?: number;
}

export async function getDashboard(hemisphere = 'north'): Promise<CareDashboardEntry[]> {
  const { data } = await client.get<CareDashboardEntry[]>(`${BASE}/dashboard`, {
    params: { hemisphere },
  });
  return data;
}

export async function getOrCreateProfile(
  plantKey: string,
  speciesName?: string,
  botanicalFamily?: string,
): Promise<CareProfile> {
  const params: Record<string, string> = {};
  if (speciesName) params.species_name = speciesName;
  if (botanicalFamily) params.botanical_family = botanicalFamily;
  const { data } = await client.get<CareProfile>(
    `${BASE}/plants/${plantKey}/profile`,
    { params },
  );
  return data;
}

export async function updateProfile(
  plantKey: string,
  updates: Partial<CareProfile>,
): Promise<CareProfile> {
  const { data } = await client.patch<CareProfile>(
    `${BASE}/plants/${plantKey}/profile`,
    updates,
  );
  return data;
}

export async function confirmReminder(
  plantKey: string,
  reminderType: ReminderType,
  options?: ConfirmReminderOptions,
): Promise<CareConfirmation> {
  const { data } = await client.post<CareConfirmation>(
    `${BASE}/plants/${plantKey}/confirm`,
    {
      reminder_type: reminderType,
      notes: options?.notes,
      volume_liters: options?.volume_liters,
      fertilizers_used: options?.fertilizers_used,
      measured_ec: options?.measured_ec,
      measured_ph: options?.measured_ph,
    },
  );
  return data;
}

export async function snoozeReminder(
  plantKey: string,
  reminderType: ReminderType,
  snoozeDays = 1,
): Promise<CareConfirmation> {
  const { data } = await client.post<CareConfirmation>(
    `${BASE}/plants/${plantKey}/snooze`,
    { reminder_type: reminderType, snooze_days: snoozeDays },
  );
  return data;
}

export async function getHistory(
  plantKey: string,
  reminderType?: ReminderType,
): Promise<CareConfirmation[]> {
  const params: Record<string, string> = {};
  if (reminderType) params.reminder_type = reminderType;
  const { data } = await client.get<CareConfirmation[]>(
    `${BASE}/plants/${plantKey}/history`,
    { params },
  );
  return data;
}

export async function resetProfile(plantKey: string): Promise<CareProfile> {
  const { data } = await client.post<CareProfile>(
    `${BASE}/plants/${plantKey}/reset-profile`,
  );
  return data;
}
