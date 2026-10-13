import { tenantClient } from '../client';
import { fetchAllPages } from '../paginate';
import type {
  Equipment,
  EquipmentCreate,
  EquipmentUpdate,
  InvenTreeConnection,
  InvenTreeConnectionCreate,
  InvenTreeReference,
  StockTransaction,
} from '../types';

const INV = '/inventree';
const EQUIP = '/equipment';

// ── Equipment ─────────────────────────────────────────────────────────────

export async function listEquipment(params?: {
  equipment_type?: string;
  status?: string;
  location_key?: string;
}): Promise<Equipment[]> {
  const { data } = await tenantClient.get<Equipment[]>(EQUIP, { params });
  return data;
}

export async function getEquipment(key: string): Promise<Equipment> {
  const { data } = await tenantClient.get<Equipment>(`${EQUIP}/${key}`);
  return data;
}

export async function createEquipment(payload: EquipmentCreate): Promise<Equipment> {
  const { data } = await tenantClient.post<Equipment>(EQUIP, payload);
  return data;
}

export async function updateEquipment(
  key: string,
  payload: EquipmentUpdate,
): Promise<Equipment> {
  const { data } = await tenantClient.put<Equipment>(`${EQUIP}/${key}`, payload);
  return data;
}

export async function deleteEquipment(key: string): Promise<void> {
  await tenantClient.delete(`${EQUIP}/${key}`);
}

// ── InvenTree connections ─────────────────────────────────────────────────

export async function listConnections(): Promise<InvenTreeConnection[]> {
  const { data } = await tenantClient.get<InvenTreeConnection[]>(`${INV}/connections`);
  return data;
}

export async function createConnection(
  payload: InvenTreeConnectionCreate,
): Promise<InvenTreeConnection> {
  const { data } = await tenantClient.post<InvenTreeConnection>(
    `${INV}/connections`,
    payload,
  );
  return data;
}

export async function checkConnectionHealth(key: string): Promise<{ healthy: boolean }> {
  const { data } = await tenantClient.post<{ healthy: boolean }>(
    `${INV}/connections/${key}/health-check`,
  );
  return data;
}

export async function deleteConnection(key: string): Promise<void> {
  await tenantClient.delete(`${INV}/connections/${key}`);
}

// ── References & transactions ──────────────────────────────────────────────

/**
 * Every InvenTree reference of the tenant. The route returns one bounded page since MT-035 (#2131); every page is read
 * so the reference list stays complete.
 */
export async function listReferences(
  entityCollection?: string,
): Promise<InvenTreeReference[]> {
  return fetchAllPages(async (offset, limit) => {
    const { data } = await tenantClient.get<InvenTreeReference[]>(`${INV}/references`, {
      params: {
        offset,
        limit,
        ...(entityCollection ? { entity_collection: entityCollection } : {}),
      },
    });
    return data;
  });
}

export async function listTransactions(status?: string): Promise<StockTransaction[]> {
  const { data } = await tenantClient.get<StockTransaction[]>(`${INV}/transactions`, {
    params: status ? { status } : undefined,
  });
  return data;
}

export async function triggerSync(): Promise<Record<string, unknown>> {
  const { data } = await tenantClient.post<Record<string, unknown>>(`${INV}/sync/trigger`);
  return data;
}
