import apiClient from '@/api/client';
import type {
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
