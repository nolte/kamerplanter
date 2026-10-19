import { tenantClient } from '@/api/client';
import { listSites } from '@/api/endpoints/sites';
import { listBeds } from '../bed/bedApi';
import type { HistoryQuery } from './historyFilters';
import type {
  BackfillBody,
  BackfillResult,
  CareEventLine,
  FilterOption,
  HistoryItem,
  RotationTimeline,
} from './historyTypes';

/**
 * REST access of the bed history and the tenant-wide history through the tenant-scoped client
 * (REQ-053 GP-API-034, GP-API-038, GP-API-039, GP-API-042).
 */

/** One page of the history lists (GP-FR-102: "Paginierung ab 50 Einträgen"). */
export const HISTORY_PAGE_SIZE = 50;

/** GP-API-038: care events and derived planting events of one bed, newest first. */
export async function getBedHistory(bedKey: string, query: HistoryQuery, offset: number): Promise<HistoryItem[]> {
  const { data } = await tenantClient.get<HistoryItem[]>(`/locations/${bedKey}/history`, {
    params: { ...query, offset, limit: HISTORY_PAGE_SIZE },
  });
  return data;
}

/** GP-API-034 / GP-FR-107: the care log of the whole tenant (90 days unless a range is sent). */
export async function getCareEvents(query: HistoryQuery, offset: number): Promise<CareEventLine[]> {
  const { include_corrections: corrections, ...rest } = query;
  const { data } = await tenantClient.get<CareEventLine[]>('/care-events', {
    params: { ...rest, ...(corrections ? { include_superseded: true } : {}), offset, limit: HISTORY_PAGE_SIZE },
  });
  return data;
}

/** GP-API-039: family, demand and role per year; the server picks `max(pause, 5)` years without `years`. */
export async function getRotationTimeline(bedKey: string, years?: number): Promise<RotationTimeline> {
  const { data } = await tenantClient.get<RotationTimeline>(`/locations/${bedKey}/rotation`, {
    params: years === undefined ? {} : { years },
  });
  return data;
}

/** GP-API-042: *what stood here in {year}?* - the server stamps the care event. */
export async function backfillYear(bedKey: string, body: BackfillBody): Promise<BackfillResult> {
  const { data } = await tenantClient.post<BackfillResult>(`/locations/${bedKey}/history/backfill`, body);
  return data;
}

/** GP-API-042: take a backfilled year back (its author, or a lead). */
export async function cancelBackfill(bedKey: string, careEventKey: string): Promise<void> {
  await tenantClient.delete(`/locations/${bedKey}/history/backfill/${careEventKey}`);
}

interface PlantingRow {
  plant_key?: string | null;
  instance_id?: string | null;
}

/** The plants the bed has had (every state), to filter the history by plant. Informational only. */
export async function listBedPlantOptions(bedKey: string): Promise<FilterOption[]> {
  const { data } = await tenantClient.get<PlantingRow[]>(`/locations/${bedKey}/plantings`, {
    params: { limit: 200 },
  });
  const seen = new Set<string>();
  return data.flatMap((row) => {
    if (!row.plant_key || seen.has(row.plant_key)) return [];
    seen.add(row.plant_key);
    return [{ key: row.plant_key, label: row.instance_id ?? row.plant_key }];
  });
}

/** Every bed of every site, to filter the tenant-wide history by bed. */
export async function listAllBedOptions(): Promise<FilterOption[]> {
  const sites = await listSites(0, 200);
  const perSite = await Promise.all(sites.map((site) => listBeds(site.key).catch(() => [])));
  return perSite.flat().map((bed) => ({ key: bed.key, label: bed.name }));
}
