import { tenantClient } from '../client';
import type {
  AvailableSourcesResponse,
  HaEntityItem,
  SiteClimateResponse,
  SiteWeatherForecastResponse,
  WeatherSourceConfigRequest,
  WeatherSourceConfigResponse,
  WeatherSourceEntryRequest,
  WeatherTestResponse,
} from '../types';

/**
 * REQ-046 §4.3 — tenant-scoped weather-source API. All calls use
 * {@link tenantClient}, whose request interceptor prepends `/t/{slug}` from the
 * active tenant (client.ts). Paths here therefore carry no `/t` prefix.
 */

const SITES = '/sites';

export async function getWeatherSource(
  siteKey: string,
): Promise<WeatherSourceConfigResponse> {
  const { data } = await tenantClient.get<WeatherSourceConfigResponse>(
    `${SITES}/${siteKey}/weather-source`,
  );
  return data;
}

export async function putWeatherSource(
  siteKey: string,
  payload: WeatherSourceConfigRequest,
): Promise<WeatherSourceConfigResponse> {
  const { data } = await tenantClient.put<WeatherSourceConfigResponse>(
    `${SITES}/${siteKey}/weather-source`,
    payload,
  );
  return data;
}

export async function getAvailableSources(): Promise<AvailableSourcesResponse> {
  const { data } = await tenantClient.get<AvailableSourcesResponse>(
    '/weather-sources/available',
  );
  return data;
}

export async function testSource(
  siteKey: string,
  entry: WeatherSourceEntryRequest,
): Promise<WeatherTestResponse> {
  const { data } = await tenantClient.post<WeatherTestResponse>(
    `${SITES}/${siteKey}/weather-sources/test`,
    entry,
  );
  return data;
}

/**
 * Issue #392 — per-site daily weather forecast plus the proactive frost
 * early-warning summary consumed by the dashboard `WeatherForecastWidget`.
 * Graceful by contract: an unconfigured site returns an empty `forecasts` list
 * with `null` frost fields rather than an error.
 */
export async function getSiteWeatherForecast(
  siteKey: string,
): Promise<SiteWeatherForecastResponse> {
  const { data } = await tenantClient.get<SiteWeatherForecastResponse>(
    `${SITES}/${siteKey}/weather-forecast`,
  );
  return data;
}

/**
 * REQ-041 — the site's long-term climate normals (NASA POWER) for the
 * "Klima am Standort" section. Graceful by contract: a site without populated
 * normals returns an empty `normals` list rather than an error.
 */
export async function getSiteClimateNormals(
  siteKey: string,
): Promise<SiteClimateResponse> {
  const { data } = await tenantClient.get<SiteClimateResponse>(
    `${SITES}/${siteKey}/climate-normals`,
  );
  return data;
}

export async function listHaWeatherEntities(): Promise<HaEntityItem[]> {
  const { data } = await tenantClient.get<HaEntityItem[]>('/ha/weather-entities');
  return data;
}

export async function listHaSensorEntities(): Promise<HaEntityItem[]> {
  const { data } = await tenantClient.get<HaEntityItem[]>('/ha/sensor-entities');
  return data;
}
