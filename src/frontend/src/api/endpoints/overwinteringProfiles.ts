import { tenantClient as client } from '../client';
import type {
  OverwinteringProfile,
  OverwinteringProfileAutoGenerate,
  OverwinteringProfileCreate,
  OverwinteringProfileUpdate,
  WinterHardinessOverview,
} from '../types';

const BASE = '/overwintering-profiles';

export async function listOverwinteringProfiles(
  offset = 0,
  limit = 50,
): Promise<OverwinteringProfile[]> {
  const { data } = await client.get<OverwinteringProfile[]>(BASE, {
    params: { offset, limit },
  });
  return data;
}

export async function getOverwinteringProfile(
  key: string,
): Promise<OverwinteringProfile> {
  const { data } = await client.get<OverwinteringProfile>(`${BASE}/${key}`);
  return data;
}

export async function createOverwinteringProfile(
  payload: OverwinteringProfileCreate,
): Promise<OverwinteringProfile> {
  const { data } = await client.post<OverwinteringProfile>(BASE, payload);
  return data;
}

export async function updateOverwinteringProfile(
  key: string,
  payload: OverwinteringProfileUpdate,
): Promise<OverwinteringProfile> {
  const { data } = await client.put<OverwinteringProfile>(
    `${BASE}/${key}`,
    payload,
  );
  return data;
}

export async function deleteOverwinteringProfile(key: string): Promise<void> {
  await client.delete(`${BASE}/${key}`);
}

export async function autoGenerateOverwinteringProfile(
  payload: OverwinteringProfileAutoGenerate,
): Promise<OverwinteringProfile> {
  const { data } = await client.post<OverwinteringProfile>(
    `${BASE}/auto-generate`,
    payload,
  );
  return data;
}

export async function getHardinessOverview(): Promise<WinterHardinessOverview> {
  const { data } = await client.get<WinterHardinessOverview>(
    `${BASE}/hardiness-overview`,
  );
  return data;
}
