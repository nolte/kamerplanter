import apiClient from '@/api/client';

/**
 * MT-015 (#2112) — platform-admin API for the per-tenant Home Assistant entity
 * allowlist. Kamerplanter talks to one Home Assistant instance (the operator's);
 * a garden uses only the entities granted to it here. Global (not tenant-scoped)
 * like the rest of `/admin/...`, so the plain `apiClient` is used.
 */

export interface HaEntityGrant {
  entity_id: string;
  source: 'admin' | 'migration' | string;
  created_at: string | null;
}

export interface HaEntityInventoryItem {
  entity_id: string;
  domain: string;
  friendly_name: string | null;
  unit_of_measurement: string | null;
  device_class: string | null;
  granted: boolean;
  /** False for a granted entity Home Assistant no longer reports. */
  present: boolean;
}

export interface HaEntityInventory {
  ha_configured: boolean;
  entities: HaEntityInventoryItem[];
}

export interface HaEntityGrantsResult {
  created: number;
  grants: HaEntityGrant[];
}

const BASE = '/admin/ha-entity-grants/tenants';

/** The whole HA inventory, each entity marked `granted` for the tenant. */
export async function getHaEntityInventory(tenantKey: string): Promise<HaEntityInventory> {
  const { data } = await apiClient.get<HaEntityInventory>(`${BASE}/${encodeURIComponent(tenantKey)}/inventory`);
  return data;
}

/** Release entities for the tenant; already granted ones are left as they are. */
export async function grantHaEntities(tenantKey: string, entityIds: string[]): Promise<HaEntityGrantsResult> {
  const { data } = await apiClient.post<HaEntityGrantsResult>(`${BASE}/${encodeURIComponent(tenantKey)}`, {
    entity_ids: entityIds,
  });
  return data;
}

/** Withdraw one grant. */
export async function revokeHaEntityGrant(tenantKey: string, entityId: string): Promise<void> {
  await apiClient.delete(`${BASE}/${encodeURIComponent(tenantKey)}/${encodeURIComponent(entityId)}`);
}

/** Shape of a Home Assistant entity id — mirrors the backend's `HA_ENTITY_ID_PATTERN`. */
export const HA_ENTITY_ID_PATTERN = /^[a-z0-9_]{1,64}\.[a-z0-9_]{1,191}$/;
