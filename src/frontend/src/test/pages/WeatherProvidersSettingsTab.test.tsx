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
  getWeatherFetchStatus: vi.fn(),
  triggerWeatherFetch: vi.fn(),
}));

import {
  getWeatherFetchStatus,
  getWeatherProviders,
  putWeatherProviders,
  testWeatherProvider,
} from '@/api/endpoints/adminWeatherProviders';

const mockGet = vi.mocked(getWeatherProviders);
const mockPut = vi.mocked(putWeatherProviders);
const mockTest = vi.mocked(testWeatherProvider);
const mockStatus = vi.mocked(getWeatherFetchStatus);

function buildResponse(overrides: Partial<WeatherProvidersResponse> = {}): WeatherProvidersResponse {
  return {
    providers: [
      { source_name: 'open-meteo', enabled: true, base_url: 'https://api.open-meteo.com', attribution: 'Weather data by Open-Meteo.com (CC BY 4.0)' },
      { source_name: 'dwd', enabled: false, base_url: 'https://opendata.dwd.de', attribution: 'Datenbasis: Deutscher Wetterdienst' },
      { source_name: 'openweathermap', enabled: false, base_url: 'https://api.openweathermap.org', attribution: 'Weather data by OpenWeatherMap' },
    ],
    openweathermap_global_api_key_set: false,
    fetch_timeout_s: 10,
    fetch_interval_hours: 6,
    default_public_source: 'open-meteo',
    ...overrides,
  };
}

describe('WeatherProvidersSettingsTab', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // The fetch card's status panel (F-14) reads the status on mount.
    mockStatus.mockResolvedValue({
      interval_hours: 6,
      last_run: null,
      last_success: null,
      next_scheduled_at: '2026-11-23T12:00:00Z',
      running: false,
      manual_fetch_available_in_s: 0,
    });
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

  // ── F-14 (#2934) — fetch interval, per-request timeout wording ──

  it('acceptance-1: shows the fetch interval in hours with a minimum of 6', async () => {
    mockGet.mockResolvedValue(buildResponse({ fetch_interval_hours: 12 }));
    renderWithProviders(<WeatherProvidersSettingsTab />);

    const field = await screen.findByTestId('weather-fetch-interval');
    const input = field.querySelector('input');
    expect(input).toHaveValue(12);
    expect(input).toHaveAttribute('min', '6');
    expect(input).toHaveAttribute('max', '168');
    expect(field).toHaveTextContent(/abrufintervall|fetch interval/i);
  });

  it('acceptance-1: saves the fetch interval with the other fields', async () => {
    const user = userEvent.setup();
    mockGet.mockResolvedValue(buildResponse());
    mockPut.mockResolvedValue(buildResponse({ fetch_interval_hours: 12 }));
    renderWithProviders(<WeatherProvidersSettingsTab />);

    const input = (await screen.findByTestId('weather-fetch-interval')).querySelector('input')!;
    await user.clear(input);
    await user.type(input, '12');
    await user.click(screen.getByTestId('weather-providers-save-button'));

    await waitFor(() => expect(mockPut).toHaveBeenCalledTimes(1));
    const payload = mockPut.mock.calls[0][0];
    expect(payload.fetch_interval_hours).toBe(12);
    // The other fields still travel in the same payload.
    expect(payload.fetch_timeout_s).toBe(10);
    expect(payload.default_public_source).toBe('open-meteo');
    // A new interval moves the next scheduled fetch: the status is read again after the save.
    await waitFor(() => expect(mockStatus).toHaveBeenCalledTimes(2));
  });

  it('acceptance-1: refuses an interval below 6 hours before it reaches the server', async () => {
    const user = userEvent.setup();
    mockGet.mockResolvedValue(buildResponse());
    renderWithProviders(<WeatherProvidersSettingsTab />);

    const field = await screen.findByTestId('weather-fetch-interval');
    const input = field.querySelector('input')!;
    await user.clear(input);
    await user.type(input, '5');

    expect(input).toHaveAttribute('aria-invalid', 'true');
    expect(field).toHaveTextContent(/6.*168/);
    expect(screen.getByTestId('weather-providers-save-button')).toBeDisabled();
    expect(mockPut).not.toHaveBeenCalled();
  });

  it('acceptance-4: labels the timeout as a limit per request, not as the fetch frequency', async () => {
    mockGet.mockResolvedValue(buildResponse());
    renderWithProviders(<WeatherProvidersSettingsTab />);

    const field = await screen.findByTestId('weather-fetch-timeout');
    expect(field).toHaveTextContent(/zeitlimit pro anfrage|timeout per request/i);
    expect(field).toHaveTextContent(/abrufintervall|fetch interval/i);
  });

  it('renders the fetch status panel inside the fetch settings card', async () => {
    mockGet.mockResolvedValue(buildResponse());
    renderWithProviders(<WeatherProvidersSettingsTab />);

    expect(await screen.findByTestId('weather-fetch-panel')).toBeInTheDocument();
    expect(await screen.findByTestId('weather-fetch-now-button')).toBeInTheDocument();
  });
});
