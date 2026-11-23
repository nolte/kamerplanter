import apiClient from '@/api/client';
import type {
  WeatherFetchStatusResponse,
  WeatherFetchTriggerResponse,
  WeatherProvidersResponse,
  WeatherProvidersUpdate,
  WeatherProviderTestResponse,
} from '@/api/types';

/**
 * REQ-046 follow-up — platform-admin API for the instance-wide public weather
 * providers (Open-Meteo, DWD, OpenWeatherMap). These endpoints are global (NOT
 * tenant-scoped), so they use the plain `apiClient` on `/admin/...` like the
 * platform-admin surface in `adminPlatform.ts`.
 */

const BASE = '/admin/weather-providers';

/** GET the masked, effective provider config (no key/ciphertext ever). */
export async function getWeatherProviders(): Promise<WeatherProvidersResponse> {
  const { data } = await apiClient.get<WeatherProvidersResponse>(BASE);
  return data;
}

/** PUT the provider overrides; the global OWM key is plaintext in the body. */
export async function putWeatherProviders(
  payload: WeatherProvidersUpdate,
): Promise<WeatherProvidersResponse> {
  const { data } = await apiClient.put<WeatherProvidersResponse>(BASE, payload);
  return data;
}

/** POST a connection test for one provider (never a 500 — errors are mapped). */
export async function testWeatherProvider(
  sourceName: string,
): Promise<WeatherProviderTestResponse> {
  const { data } = await apiClient.post<WeatherProviderTestResponse>(
    `${BASE}/${encodeURIComponent(sourceName)}/test`,
  );
  return data;
}

/**
 * POST a manual weather fetch over all sites (REQ-046 §3.6a, #2934). Answers 202
 * once queued; the run's result appears in {@link getWeatherFetchStatus}.
 * Refusals arrive as an `ApiError`: 409 `WEATHER_FETCH_RUNNING` /
 * `WEATHER_FETCH_DISABLED`, 429 `WEATHER_FETCH_COOLDOWN` (with
 * `retryAfterSeconds` from `Retry-After`), 503 `WEATHER_FETCH_UNAVAILABLE`.
 */
export async function triggerWeatherFetch(): Promise<WeatherFetchTriggerResponse> {
  const { data } = await apiClient.post<WeatherFetchTriggerResponse>(`${BASE}/fetch`);
  return data;
}

/** GET the newest run, the newest successful run and the next scheduled fetch. */
export async function getWeatherFetchStatus(): Promise<WeatherFetchStatusResponse> {
  const { data } = await apiClient.get<WeatherFetchStatusResponse>(`${BASE}/fetch-status`);
  return data;
}
