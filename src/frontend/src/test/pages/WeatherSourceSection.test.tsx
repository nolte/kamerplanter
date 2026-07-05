import { describe, it, expect, beforeEach, vi } from 'vitest';
import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { server } from '@/test/mocks/server';
import { renderWithProviders } from '@/test/helpers';
import WeatherSourceSection from '@/pages/standorte/WeatherSourceSection';
import type {
  AvailableSourcesResponse,
  WeatherSourceConfigResponse,
} from '@/api/types';

/**
 * REQ-046 §4.1 (PR-5) — weather-source configurator: two-way switch, HA gating
 * without a token, connection-test flow and up/down reordering (D3).
 */

const SITE = 'site-1';
const T = 'test-tenant';

const AVAILABLE: AvailableSourcesResponse = {
  ha_token_set: true,
  sources: [
    { source_name: 'open-meteo', kind: 'public', requires_api_key: false },
    { source_name: 'dwd', kind: 'public', requires_api_key: false },
    { source_name: 'openweathermap', kind: 'public', requires_api_key: true },
    { source_name: 'ha_weather', kind: 'home_assistant', requires_api_key: false },
  ],
};

const TWO_SOURCE_CONFIG: WeatherSourceConfigResponse = {
  site_key: SITE,
  enabled: true,
  sources: [
    { source_name: 'open-meteo', kind: 'public', enabled: true, public_config: { api_key_set: false } },
    { source_name: 'dwd', kind: 'public', enabled: true, public_config: { api_key_set: false } },
  ],
};

interface Opts {
  config?: WeatherSourceConfigResponse;
  available?: AvailableSourcesResponse;
  testReachable?: boolean;
}

function setup(opts: Opts = {}) {
  let putBody: unknown = null;
  let testBody: unknown = null;

  const config = opts.config ?? {
    site_key: SITE,
    enabled: true,
    sources: [],
  };

  server.use(
    http.get(`/api/v1/t/${T}/sites/${SITE}/weather-source`, () => HttpResponse.json(config)),
    http.get(`/api/v1/t/${T}/weather-sources/available`, () =>
      HttpResponse.json(opts.available ?? AVAILABLE),
    ),
    http.put(`/api/v1/t/${T}/sites/${SITE}/weather-source`, async ({ request }) => {
      putBody = await request.json();
      return HttpResponse.json(config);
    }),
    http.post(`/api/v1/t/${T}/sites/${SITE}/weather-sources/test`, async ({ request }) => {
      testBody = await request.json();
      const reachable = opts.testReachable ?? true;
      return HttpResponse.json(
        reachable
          ? {
              reachable: true,
              preview: [
                {
                  forecast_date: '2026-07-06',
                  temp_min_c: 12,
                  temp_max_c: 24,
                  precipitation_mm: 0,
                  source: 'open-meteo',
                  data_kind: 'forecast',
                  is_current_conditions: false,
                },
              ],
              error: null,
            }
          : { reachable: false, preview: [], error: 'connection refused' },
      );
    }),
    http.get(`/api/v1/t/${T}/ha/weather-entities`, () =>
      HttpResponse.json([
        { entity_id: 'weather.home', friendly_name: 'Home' },
      ]),
    ),
    http.get(`/api/v1/t/${T}/ha/sensor-entities`, () =>
      HttpResponse.json([
        { entity_id: 'sensor.outdoor_temp', friendly_name: 'Outdoor temperature' },
      ]),
    ),
  );

  const result = renderWithProviders(<WeatherSourceSection siteKey={SITE} />);
  return { ...result, getPutBody: () => putBody, getTestBody: () => testBody };
}

beforeEach(() => {
  vi.clearAllMocks();
});

describe('WeatherSourceSection', () => {
  it('renders the loaded priority list with source + kind badges', async () => {
    setup({ config: TWO_SOURCE_CONFIG });
    expect(await screen.findByTestId('weather-entry-0')).toBeInTheDocument();
    const first = screen.getByTestId('weather-entry-0');
    expect(within(first).getByText('Open-Meteo')).toBeInTheDocument();
    expect(within(first).getByText('#1')).toBeInTheDocument();
    expect(screen.getByTestId('weather-entry-1')).toBeInTheDocument();
  });

  it('shows an empty state when no source is configured', async () => {
    setup();
    expect(await screen.findByTestId('weather-add-source-button')).toBeInTheDocument();
    expect(screen.queryByTestId('weather-entry-0')).not.toBeInTheDocument();
  });

  it('reorders sources with the up/down buttons (index 0 = highest priority)', async () => {
    const user = userEvent.setup();
    setup({ config: TWO_SOURCE_CONFIG });
    await screen.findByTestId('weather-entry-0');
    // Initially open-meteo is #1.
    expect(within(screen.getByTestId('weather-entry-0')).getByText('Open-Meteo')).toBeInTheDocument();
    // Move the second entry (dwd) up.
    await user.click(screen.getByTestId('weather-move-up-1'));
    await waitFor(() => {
      expect(
        within(screen.getByTestId('weather-entry-0')).getByText('German Weather Service (DWD)'),
      ).toBeInTheDocument();
    });
    // The top entry can no longer move up.
    expect(screen.getByTestId('weather-move-up-0')).toBeDisabled();
  });

  it('adds a public source via the two-way dialog (public branch)', async () => {
    const user = userEvent.setup();
    const { getPutBody } = setup();
    await user.click(await screen.findByTestId('weather-add-source-button'));
    expect(await screen.findByTestId('weather-source-add-dialog')).toBeInTheDocument();
    // Public is the default branch; provider select is shown.
    expect(screen.getByTestId('weather-provider-select')).toBeInTheDocument();
    await user.click(screen.getByTestId('weather-source-add-confirm'));
    // Entry appears in the list.
    expect(await screen.findByTestId('weather-entry-0')).toBeInTheDocument();
    // Save persists it via PUT.
    await user.click(screen.getByTestId('weather-save-button'));
    await waitFor(() => expect(getPutBody()).not.toBeNull());
    const body = getPutBody() as { sources: { source_name: string; kind: string }[] };
    expect(body.sources[0].kind).toBe('public');
  });

  it('switches to the Home Assistant branch and reveals mode toggles', async () => {
    const user = userEvent.setup();
    setup();
    await user.click(await screen.findByTestId('weather-add-source-button'));
    await screen.findByTestId('weather-source-add-dialog');
    await user.click(screen.getByTestId('weather-kind-ha'));
    // Mode toggles appear; default mode A shows the weather-entity autocomplete.
    expect(await screen.findByTestId('ha-mode-weather-entity')).toBeInTheDocument();
    expect(screen.getByTestId('ha-mode-sensor-mapping')).toBeInTheDocument();
    // Switch to mode B — per-field sensor pickers render.
    await user.click(screen.getByTestId('ha-mode-sensor-mapping'));
    expect(await screen.findByTestId('ha-sensor-temp_min_entity')).toBeInTheDocument();
    expect(screen.getByTestId('ha-sensor-pressure_entity')).toBeInTheDocument();
  });

  it('disables the HA option with a hint when no HA token is set', async () => {
    const user = userEvent.setup();
    setup({ available: { ...AVAILABLE, ha_token_set: false } });
    await user.click(await screen.findByTestId('weather-add-source-button'));
    await screen.findByTestId('weather-source-add-dialog');
    expect(screen.getByTestId('weather-kind-ha')).toBeDisabled();
    expect(screen.getByTestId('ha-token-missing-hint')).toBeInTheDocument();
  });

  it('runs a connection test and shows reachability + a value preview', async () => {
    const user = userEvent.setup();
    const { getTestBody } = setup({ config: TWO_SOURCE_CONFIG });
    await screen.findByTestId('weather-entry-0');
    await user.click(screen.getByTestId('weather-test-0'));
    const result = await screen.findByTestId('weather-test-result-0');
    expect(within(result).getByText(/reachable/i)).toBeInTheDocument();
    await waitFor(() => expect(getTestBody()).not.toBeNull());
  });

  it('shows a readable error when the tested source is unreachable', async () => {
    const user = userEvent.setup();
    setup({ config: TWO_SOURCE_CONFIG, testReachable: false });
    await screen.findByTestId('weather-entry-0');
    await user.click(screen.getByTestId('weather-test-0'));
    expect(await screen.findByTestId('weather-test-error-0')).toHaveTextContent('connection refused');
  });

  it('requires the OWM API-key field only for key-based providers', async () => {
    const user = userEvent.setup();
    setup();
    await user.click(await screen.findByTestId('weather-add-source-button'));
    await screen.findByTestId('weather-source-add-dialog');
    // Default provider (open-meteo) needs no key.
    expect(screen.queryByTestId('weather-api-key-field')).not.toBeInTheDocument();
    // Selecting OpenWeatherMap reveals the masked key field.
    const select = within(screen.getByTestId('weather-provider-select')).getByRole('combobox');
    await user.click(select);
    await user.click(await screen.findByRole('option', { name: 'OpenWeatherMap' }));
    const keyField = await screen.findByTestId('weather-api-key-field');
    expect(keyField.querySelector('input')?.type).toBe('password');
  });
});
