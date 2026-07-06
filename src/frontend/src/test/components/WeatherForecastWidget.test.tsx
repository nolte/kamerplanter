import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import { renderWithProviders } from '@/test/helpers';
import WeatherForecastWidget from '@/components/dashboard/widgets/WeatherForecastWidget';
import WeatherProvenanceBadge from '@/components/weather/WeatherProvenanceBadge';

/**
 * REQ-046 §4.2 / Issue #392 (R7) — dashboard weather widget (forecast rows +
 * frost early-warning badge) and the shared provenance badge (AC-10).
 */

vi.mock('@/api/endpoints/sites', () => ({
  listSites: vi.fn(),
}));
vi.mock('@/api/endpoints/weatherSources', () => ({
  getSiteWeatherForecast: vi.fn(),
}));

import { listSites } from '@/api/endpoints/sites';
import { getSiteWeatherForecast } from '@/api/endpoints/weatherSources';
import type { Site, SiteWeatherForecastResponse } from '@/api/types';

const mockListSites = vi.mocked(listSites);
const mockGetForecast = vi.mocked(getSiteWeatherForecast);

const site: Site = {
  key: 'site-1',
  name: 'Gemüsegarten',
  gps_coordinates: [50.1, 8.7],
} as unknown as Site;

const forecastRows: SiteWeatherForecastResponse['forecasts'] = [
  { forecast_date: '2026-07-06', temp_min_c: 8.5, temp_max_c: 21.0, source: 'open-meteo', data_kind: 'forecast' },
  { forecast_date: '2026-07-07', temp_min_c: 6.0, temp_max_c: 19.5, source: 'open-meteo', data_kind: 'forecast' },
];

function forecast(overrides: Partial<SiteWeatherForecastResponse> = {}): SiteWeatherForecastResponse {
  return {
    site_key: 'site-1',
    forecasts: forecastRows,
    forecast_frost_warning: false,
    forecast_min_temperature: null,
    forecast_expected_date: null,
    forecast_source: 'open-meteo',
    ...overrides,
  };
}

describe('WeatherForecastWidget', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockListSites.mockResolvedValue([site]);
  });

  it('renders the daily forecast rows with a provenance badge', async () => {
    mockGetForecast.mockResolvedValue(forecast());

    renderWithProviders(<WeatherForecastWidget />);

    expect(await screen.findByTestId('weather-forecast-rows')).toBeInTheDocument();
    expect(screen.getByTestId('weather-forecast-row-2026-07-06')).toBeInTheDocument();
    expect(screen.getByTestId('weather-forecast-row-2026-07-07')).toBeInTheDocument();
    // Provenance badge rendered from source/data_kind.
    expect(screen.getAllByText('Open-Meteo').length).toBeGreaterThan(0);
    expect(mockGetForecast).toHaveBeenCalledWith('site-1');
  });

  it('shows the frost early-warning badge when forecast_frost_warning is true', async () => {
    mockGetForecast.mockResolvedValue(
      forecast({
        forecast_frost_warning: true,
        forecast_expected_date: '2026-07-07',
        forecast_min_temperature: -1.5,
      }),
    );

    renderWithProviders(<WeatherForecastWidget />);

    expect(await screen.findByTestId('weather-frost-warning')).toBeInTheDocument();
    expect(screen.getByText('Frost expected')).toBeInTheDocument();
  });

  it('does NOT show the frost badge when forecast_frost_warning is false', async () => {
    mockGetForecast.mockResolvedValue(forecast({ forecast_frost_warning: false }));

    renderWithProviders(<WeatherForecastWidget />);

    await screen.findByTestId('weather-forecast-rows');
    expect(screen.queryByTestId('weather-frost-warning')).not.toBeInTheDocument();
  });

  it('does NOT show the frost badge when forecast_frost_warning is null', async () => {
    mockGetForecast.mockResolvedValue(forecast({ forecast_frost_warning: null }));

    renderWithProviders(<WeatherForecastWidget />);

    await screen.findByTestId('weather-forecast-rows');
    expect(screen.queryByTestId('weather-frost-warning')).not.toBeInTheDocument();
  });

  it('falls back to the configure empty state when no forecast rows exist', async () => {
    mockGetForecast.mockResolvedValue(forecast({ forecasts: [], forecast_source: null }));

    renderWithProviders(<WeatherForecastWidget />);

    const cta = await screen.findByTestId('weather-widget-configure');
    expect(cta).toHaveAttribute('href', '/standorte/sites');
    expect(screen.queryByTestId('weather-forecast-rows')).not.toBeInTheDocument();
  });

  it('shows the configure empty state when the tenant has no site', async () => {
    mockListSites.mockResolvedValue([]);

    renderWithProviders(<WeatherForecastWidget />);

    expect(await screen.findByTestId('weather-widget-configure')).toBeInTheDocument();
    expect(mockGetForecast).not.toHaveBeenCalled();
  });

  it('renders a friendly error hint when the forecast endpoint fails', async () => {
    mockGetForecast.mockRejectedValue(new Error('boom'));

    renderWithProviders(<WeatherForecastWidget />);

    expect(await screen.findByTestId('weather-widget-error')).toBeInTheDocument();
    // Card shell survives — no crash.
    expect(screen.getByTestId('widget-weather_forecast')).toBeInTheDocument();
  });

  it('shows a site-name header when the tenant owns multiple sites', async () => {
    mockListSites.mockResolvedValue([site, { ...site, key: 'site-2', name: 'Balkon' } as Site]);
    mockGetForecast.mockResolvedValue(forecast());

    renderWithProviders(<WeatherForecastWidget />);

    await waitFor(() => expect(screen.getByTestId('weather-site-name')).toBeInTheDocument());
    expect(screen.getByTestId('weather-site-name')).toHaveTextContent('Gemüsegarten');
  });
});

describe('WeatherProvenanceBadge', () => {
  it('labels a forecast record with source + forecast kind', () => {
    renderWithProviders(<WeatherProvenanceBadge source="open-meteo" dataKind="forecast" />);
    expect(screen.getByText('Open-Meteo')).toBeInTheDocument();
    expect(screen.getByText('Forecast')).toBeInTheDocument();
  });

  it('labels a live HA reading as an observed/current value (AC-10)', () => {
    renderWithProviders(
      <WeatherProvenanceBadge source="ha_weather" dataKind="observed" isCurrentConditions />,
    );
    expect(screen.getByText('Home Assistant')).toBeInTheDocument();
    expect(screen.getByText('Current')).toBeInTheDocument();
  });

  it('labels a reanalysis record distinctly', () => {
    renderWithProviders(<WeatherProvenanceBadge source="nasa-power" dataKind="reanalysis" />);
    expect(screen.getByText('Reanalysis')).toBeInTheDocument();
  });
});
