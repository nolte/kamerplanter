import { tenantClient } from '../client';
import client from '../client';
import type {
  ReadingsListResponse,
  TimeseriesStatusResponse,
} from '../types';

const BASE = '/observations';

export async function getSensorReadings(
  sensorKey: string,
  start: string,
  end: string,
  resolution: 'raw' | 'hourly' | 'daily' = 'raw',
): Promise<ReadingsListResponse> {
  const { data } = await tenantClient.get<ReadingsListResponse>(
    `${BASE}/sensors/${sensorKey}/readings`,
    { params: { start, end, resolution } },
  );
  return data;
}

export async function getTimeseriesStatus(): Promise<TimeseriesStatusResponse> {
  const { data } = await client.get<TimeseriesStatusResponse>(
    `${BASE}/status`,
  );
  return data;
}
