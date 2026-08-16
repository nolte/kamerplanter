import { tenantClient as client } from '../client';

const BASE = '/ha-publish';

export type HaPublishEntityType = 'plant' | 'tank' | 'location';

export interface HaPublishSetting {
  entity_type: HaPublishEntityType;
  entity_key: string;
  enabled: boolean;
}

export interface HaPublishEnabledKeys {
  entity_type: HaPublishEntityType;
  entity_keys: string[];
}

export async function getHaPublishStatus(
  entityType: HaPublishEntityType,
  entityKey: string,
): Promise<HaPublishSetting> {
  const { data } = await client.get<HaPublishSetting>(`${BASE}/${entityType}/${entityKey}`);
  return data;
}

export async function setHaPublishStatus(
  entityType: HaPublishEntityType,
  entityKey: string,
  enabled: boolean,
): Promise<HaPublishSetting> {
  const { data } = await client.put<HaPublishSetting>(`${BASE}/${entityType}/${entityKey}`, {
    enabled,
  });
  return data;
}

export async function bulkSetHaPublishStatus(
  entityType: HaPublishEntityType,
  entries: { entity_key: string; enabled: boolean }[],
): Promise<HaPublishSetting[]> {
  const { data } = await client.put<HaPublishSetting[]>(BASE, {
    entity_type: entityType,
    entries,
  });
  return data;
}

export async function listHaPublishSettings(
  entityType?: HaPublishEntityType,
): Promise<HaPublishSetting[]> {
  const params = entityType ? { entity_type: entityType } : undefined;
  const { data } = await client.get<HaPublishSetting[]>(BASE, { params });
  return data;
}
