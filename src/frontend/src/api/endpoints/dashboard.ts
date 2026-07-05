import { tenantClient as client } from '../client';
import type { DashboardWidgetCatalogResponse, DashboardAggregatedResponse } from '../types';

/**
 * REQ-045 — dashboard personalization read endpoints (tenant-scoped).
 * The layout itself is persisted via the user-preferences PATCH.
 */

const BASE = '/dashboard';

export async function getWidgetCatalog(): Promise<DashboardWidgetCatalogResponse> {
  const { data } = await client.get<DashboardWidgetCatalogResponse>(`${BASE}/widgets/catalog`);
  return data;
}

export async function getAggregated(widgetKeys: string[]): Promise<DashboardAggregatedResponse> {
  const { data } = await client.get<DashboardAggregatedResponse>(`${BASE}/aggregated`, {
    params: { widgets: widgetKeys.join(',') },
  });
  return data;
}
