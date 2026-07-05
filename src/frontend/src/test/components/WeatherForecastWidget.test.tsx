import { describe, it, expect } from 'vitest';
import { screen } from '@testing-library/react';
import { renderWithProviders } from '@/test/helpers';
import WeatherForecastWidget from '@/components/dashboard/widgets/WeatherForecastWidget';
import WeatherProvenanceBadge from '@/components/weather/WeatherProvenanceBadge';

/**
 * REQ-046 §4.2 — dashboard weather widget (placeholder until a forecast read
 * endpoint lands) and the shared provenance badge (AC-10).
 */

describe('WeatherForecastWidget', () => {
  it('renders the widget label and a configuration call-to-action', () => {
    renderWithProviders(<WeatherForecastWidget />);
    expect(screen.getByTestId('widget-weather_forecast')).toBeInTheDocument();
    expect(screen.getByText('Weather forecast')).toBeInTheDocument();
    const cta = screen.getByTestId('weather-widget-configure');
    expect(cta).toHaveAttribute('href', '/standorte/sites');
  });
});

describe('WeatherProvenanceBadge', () => {
  it('labels a forecast record with source + forecast kind', () => {
    renderWithProviders(
      <WeatherProvenanceBadge source="open-meteo" dataKind="forecast" />,
    );
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
    renderWithProviders(
      <WeatherProvenanceBadge source="nasa-power" dataKind="reanalysis" />,
    );
    expect(screen.getByText('Reanalysis')).toBeInTheDocument();
  });
});
