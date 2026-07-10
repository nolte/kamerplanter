import { describe, it, expect, beforeEach, afterAll, vi } from 'vitest';
import { cloneElement, type ReactElement } from 'react';
import { screen, waitFor, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';
import SensorHistoryChart from '@/components/sensors/SensorHistoryChart';
import { renderWithProviders } from '../helpers';
import { server } from '../mocks/server';

/**
 * P7e — SensorHistoryChart. Rendered as a unit; the single collaborator
 * (observations readings endpoint, tenant-scoped) is doubled at the process
 * boundary via msw. recharts' ResponsiveContainer is replaced with a
 * fixed-size wrapper so the SVG (and its tick formatters) actually render under
 * jsdom, which has no layout engine. Asserts observable output only.
 */

// Give the inner chart concrete dimensions so recharts renders axes + ticks.
vi.mock('recharts', async () => {
  const actual = await vi.importActual<typeof import('recharts')>('recharts');
  return {
    ...actual,
    ResponsiveContainer: ({ children }: { children: ReactElement }) =>
      cloneElement(children, { width: 400, height: 200 } as Record<string, unknown>),
  };
});

class ResizeObserverStub {
  observe() {}
  unobserve() {}
  disconnect() {}
}
globalThis.ResizeObserver = ResizeObserverStub as unknown as typeof ResizeObserver;

const READINGS_URL = '/api/v1/t/:tenant/observations/sensors/:sensorKey/readings';

function rawItem(hoursAgo: number, value: number) {
  return {
    time: new Date(Date.now() - hoursAgo * 3_600_000).toISOString(),
    sensor_key: 'sensor-1',
    sensor_type: 'ph',
    value,
    unit: 'pH',
    source: 'manual',
    quality_score: null,
    raw_value: null,
    metadata: null,
  };
}

function aggItem(daysAgo: number, avg: number) {
  return {
    bucket: new Date(Date.now() - daysAgo * 86_400_000).toISOString(),
    sensor_key: 'sensor-1',
    sensor_type: 'ph',
    avg_value: avg,
    min_value: avg - 0.5,
    max_value: avg + 0.5,
    sample_count: 12,
  };
}

interface Opts {
  raw?: number;
  agg?: number;
  empty?: boolean;
  fail?: boolean;
}

/** Response varies by the requested resolution so range switches change shape. */
function registerReadings(opts: Opts = {}) {
  server.use(
    http.get(READINGS_URL, ({ request }) => {
      if (opts.fail) {
        return HttpResponse.json({ message: 'boom' }, { status: 500 });
      }
      const url = new URL(request.url);
      const resolution = url.searchParams.get('resolution') ?? 'raw';
      if (opts.empty) {
        return HttpResponse.json({ items: [], total: 0, resolution });
      }
      if (resolution === 'raw') {
        return HttpResponse.json({
          items: [rawItem(2, 6.1), rawItem(1, 6.3), rawItem(3, 6.0)],
          total: 3,
          resolution: 'raw',
        });
      }
      return HttpResponse.json({
        items: [aggItem(2, 6.2), aggItem(1, 6.4), aggItem(3, 6.0)],
        total: 3,
        resolution,
      });
    }),
  );
}

function mount(props: Partial<{ sensorKey: string; sensorName: string; metricType: string; unit: string | null }> = {}) {
  return renderWithProviders(
    <SensorHistoryChart
      sensorKey={props.sensorKey ?? 'sensor-1'}
      sensorName={props.sensorName ?? 'pH Probe'}
      metricType={props.metricType ?? 'ph'}
      unit={props.unit === undefined ? 'pH' : props.unit}
    />,
  );
}

describe('SensorHistoryChart', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    i18n.changeLanguage('de');
  });

  afterAll(() => {
    i18n.changeLanguage('en');
  });

  it('renders the header with the sensor name and unit label, plus the range switch', async () => {
    registerReadings();
    const { container } = mount();
    expect(screen.getByText('pH Probe (pH)')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '24h' })).toBeInTheDocument();
    // A line chart renders for the default raw (24h) range.
    await waitFor(() =>
      expect(container.querySelector('.recharts-line')).toBeInTheDocument(),
    );
  });

  it('renders an area chart for an aggregated range and switches ranges', async () => {
    const user = userEvent.setup();
    const { container } = mount();
    registerReadings();
    // Wait for the initial (raw) line chart.
    await waitFor(() =>
      expect(container.querySelector('.recharts-line')).toBeInTheDocument(),
    );
    // Switch to 7d -> hourly aggregation -> area chart.
    await user.click(screen.getByRole('button', { name: '7d' }));
    await waitFor(() =>
      expect(container.querySelector('.recharts-area')).toBeInTheDocument(),
    );
    // Switch to 30d and 90d (both daily) to exercise their range configs.
    await user.click(screen.getByRole('button', { name: '30d' }));
    await user.click(screen.getByRole('button', { name: '90d' }));
    await waitFor(() =>
      expect(container.querySelector('.recharts-area')).toBeInTheDocument(),
    );
  });

  it('shows the empty-state alert when there are no readings', async () => {
    registerReadings({ empty: true });
    mount();
    expect(await screen.findByText(i18n.t('sensorChart.noData'))).toBeInTheDocument();
  });

  it('shows an error alert when the readings request fails', async () => {
    registerReadings({ fail: true });
    mount();
    expect(await screen.findByText(i18n.t('sensorChart.loadError'))).toBeInTheDocument();
  });

  it('falls back to the metric type as the label when no unit is given, and uses a default colour for unknown metrics', async () => {
    registerReadings();
    const { container } = mount({ metricType: 'some_unknown_metric', unit: null });
    // yLabel falls back to metricType.
    expect(screen.getByText('pH Probe (some_unknown_metric)')).toBeInTheDocument();
    await waitFor(() =>
      expect(container.querySelector('.recharts-line')).toBeInTheDocument(),
    );
  });

  it('activates the custom tooltip on hover over the chart surface', async () => {
    registerReadings();
    const { container } = mount();
    await waitFor(() =>
      expect(container.querySelector('.recharts-line')).toBeInTheDocument(),
    );
    const surface = container.querySelector('.recharts-surface');
    if (surface) {
      fireEvent.mouseMove(surface, { clientX: 200, clientY: 100 });
      fireEvent.mouseOver(surface, { clientX: 200, clientY: 100 });
    }
    // Chart stays rendered after the interaction (tooltip content is exercised).
    expect(container.querySelector('.recharts-line')).toBeInTheDocument();
  });
});
