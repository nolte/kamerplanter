import { tenantClient as client } from '../client';
import type {
  DescendantsResponse,
  GraftCompatibilityResponse,
  LineageResponse,
  PropagationEvent,
  PropagationEventCreate,
} from '../types';

const BASE = '/propagation';

export async function listPropagationEvents(
  params: { method?: string; status?: string; offset?: number; limit?: number } = {},
): Promise<PropagationEvent[]> {
  const { data } = await client.get<PropagationEvent[]>(`${BASE}/events`, { params });
  return data;
}

export async function getPropagationEvent(key: string): Promise<PropagationEvent> {
  const { data } = await client.get<PropagationEvent>(`${BASE}/events/${key}`);
  return data;
}

export async function createPropagationEvent(
  payload: PropagationEventCreate,
): Promise<PropagationEvent> {
  const { data } = await client.post<PropagationEvent>(`${BASE}/events`, payload);
  return data;
}

export async function recordEventOutcome(
  key: string,
  payload: { survived_count: number; failure_reasons?: string[] },
): Promise<PropagationEvent> {
  const { data } = await client.patch<PropagationEvent>(
    `${BASE}/events/${key}/outcome`,
    payload,
  );
  return data;
}

export async function getLineage(
  plantKey: string,
  maxDepth = 10,
): Promise<LineageResponse> {
  const { data } = await client.get<LineageResponse>(
    `/plant-instances/${plantKey}/lineage`,
    { params: { max_depth: maxDepth } },
  );
  return data;
}

export async function getDescendants(
  plantKey: string,
  maxDepth = 10,
): Promise<DescendantsResponse> {
  const { data } = await client.get<DescendantsResponse>(
    `/plant-instances/${plantKey}/descendants`,
    { params: { max_depth: maxDepth } },
  );
  return data;
}

export async function checkGraftCompatibility(
  scionKey: string,
  rootstockKey: string,
): Promise<GraftCompatibilityResponse> {
  const { data } = await client.get<GraftCompatibilityResponse>(
    `${BASE}/graft-compatibility`,
    { params: { scion_key: scionKey, rootstock_key: rootstockKey } },
  );
  return data;
}
