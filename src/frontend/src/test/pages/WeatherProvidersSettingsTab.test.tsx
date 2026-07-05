import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithProviders } from '../helpers';
import WeatherProvidersSettingsTab from '@/pages/auth/WeatherProvidersSettingsTab';
import type { WeatherProvidersResponse } from '@/api/types';

// Mock the admin weather-provider API module (REQ-046 follow-up endpoints).
vi.mock('@/api/endpoints/adminWeatherProviders', () => ({
  getWeatherProviders: vi.fn(),
  putWeatherProviders: vi.fn(),
  testWeatherProvider: vi.fn(),
}));

import {
  getWeatherProviders,
  putWeatherProviders,
  testWeatherProvider,
} from '@/api/endpoints/adminWeatherProviders';

const mockGet = vi.mocked(getWeatherProviders);
const mockPut = vi.mocked(putWeatherProviders);
const mockTest = vi.mocked(testWeatherProvider);

function buildResponse(overrides: Partial<WeatherProvidersResponse> = {}): WeatherProvidersResponse {
  return {
    providers: [
      { source_name: 'open-meteo', enabled: true, base_url: 'https://api.open-meteo.com', attribution: 'Weather data by Open-Meteo.com (CC BY 4.0)' },
      { source_name: 'dwd', enabled: false, base_url: 'https://opendata.dwd.de', attribution: 'Datenbasis: Deutscher Wetterdienst' },
      { source_name: 'openweathermap', enabled: false, base_url: 'https://api.openweathermap.org', attribution: 'Weather data by OpenWeatherMap' },
    ],
    openweathermap_global_api_key_set: false,
    fetch_timeout_s: 10,
    default_public_source: 'open-meteo',
    ...overrides,
  };
}

describe('WeatherProvidersSettingsTab', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders a card per provider with an enable toggle', async () => {
    mockGet.mockResolvedValue(buildResponse());
    renderWithProviders(<WeatherProvidersSettingsTab />);

    expect(await screen.findByTestId('weather-provider-open-meteo')).toBeInTheDocument();
    expect(screen.getByTestId('weather-provider-dwd')).toBeInTheDocument();
    expect(screen.getByTestId('weather-provider-openweathermap')).toBeInTheDocument();
    expect(screen.getByTestId('weather-provider-enabled-open-meteo')).toBeInTheDocument();
  });

  it('shows the masked placeholder and unset status when no global key is stored', async () => {
    mockGet.mockResolvedValue(buildResponse({ openweathermap_global_api_key_set: false }));
    renderWithProviders(<WeatherProvidersSettingsTab />);

    const status = await screen.findByTestId('weather-global-owm-key-status');
    expect(status).toHaveTextContent(/kein schlüssel|no key/i);
    // The field never carries a real key value — it starts empty.
    const input = screen.getByTestId('weather-global-owm-key').querySelector('input');
    expect(input).toHaveValue('');
  });

  it('marks the global key as stored and masks it with a placeholder', async () => {
    mockGet.mockResolvedValue(buildResponse({ openweathermap_global_api_key_set: true }));
    renderWithProviders(<WeatherProvidersSettingsTab />);

    const status = await screen.findByTestId('weather-global-owm-key-status');
    expect(status).toHaveTextContent(/gespeichert|stored/i);
    expect(screen.getByPlaceholderText('••••')).toBeInTheDocument();
  });

  it('saves toggles and leaves the key empty (unchanged) in the payload', async () => {
    const user = userEvent.setup();
    mockGet.mockResolvedValue(buildResponse());
    mockPut.mockResolvedValue(buildResponse({ default_public_source: 'open-meteo' }));
    renderWithProviders(<WeatherProvidersSettingsTab />);

    await screen.findByTestId('weather-provider-open-meteo');
    // Disable Open-Meteo (MUI forwards the data-testid onto the switch input).
    await user.click(screen.getByTestId('weather-provider-enabled-open-meteo'));
    await user.click(screen.getByTestId('weather-providers-save-button'));

    await waitFor(() => {
      expect(mockPut).toHaveBeenCalledTimes(1);
    });
    const payload = mockPut.mock.calls[0][0];
    expect(payload.open_meteo_enabled).toBe(false);
    // Empty key means "unchanged" — never send a masked/placeholder value.
    expect(payload.openweathermap_global_api_key).toBe('');
  });

  it('runs a provider connection test and shows the reachable result', async () => {
    const user = userEvent.setup();
    mockGet.mockResolvedValue(buildResponse());
    mockTest.mockResolvedValue({ reachable: true, preview: [], error: null });
    renderWithProviders(<WeatherProvidersSettingsTab />);

    await screen.findByTestId('weather-provider-open-meteo');
    await user.click(screen.getByTestId('weather-provider-test-open-meteo'));

    expect(await screen.findByTestId('weather-provider-test-result-open-meteo')).toBeInTheDocument();
    expect(mockTest).toHaveBeenCalledWith('open-meteo');
  });
});
