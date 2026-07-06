import { screen, waitFor, within } from '@testing-library/react';
import { describe, it, expect, beforeEach } from 'vitest';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';
import SeasonOverviewPanel from '@/components/dashboard/SeasonOverviewPanel';
import type { SeasonState } from '@/api/types';
import { renderWithProviders } from '../helpers';
import { server } from '../mocks/server';

const overviewUrls = [
  '/api/v1/season/overview',
  '/api/v1/t/:tenant/season/overview',
];
const siteUrls = ['/api/v1/sites', '/api/v1/t/:tenant/sites'];

function mockOverview(states: SeasonState[]) {
  server.use(
    ...overviewUrls.map((u) => http.get(u, () => HttpResponse.json({ states }))),
  );
}

function mockSites() {
  server.use(
    ...siteUrls.map((u) =>
      http.get(u, () =>
        HttpResponse.json([
          { key: 'site-1', name: 'Balkon', type: 'outdoor', climate_zone: '8a' },
        ]),
      ),
    ),
  );
}

const preWinterState: SeasonState = {
  site_key: 'site-1',
  season_state_id: 'ss-1',
  phase: 'pre_winter',
  trigger_tier: 'live',
  trigger_reason_i18n_key: 'pages.season.trigger.frostForecast',
  season_year: 2026,
  entered_phase_at: null,
  last_min_temp_c: 3.0,
  // 5 days from now → live frost countdown.
  forecast_first_frost_date: new Date(Date.now() + 5 * 86_400_000)
    .toISOString()
    .slice(0, 10),
  estimated_first_frost_md: null,
  estimated_last_frost_md: null,
  evaluated_at: null,
};

describe('SeasonOverviewPanel', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
    mockSites();
  });

  it('renders a season row with phase, trigger badge and frost countdown', async () => {
    mockOverview([preWinterState]);
    renderWithProviders(<SeasonOverviewPanel />);

    const row = await screen.findByTestId('season-row-site-1');
    // Site name resolved from the sites slice.
    expect(within(row).getByText('Balkon')).toBeTruthy();
    // Phase label.
    expect(
      within(row).getByText(i18n.t('enums.seasonPhase.pre_winter')),
    ).toBeTruthy();
    // Trigger tier badge = live weather.
    const trigger = within(row).getByTestId('season-trigger-site-1');
    expect(trigger.textContent).toContain(
      i18n.t('enums.seasonTriggerTier.live'),
    );
    // Live frost countdown present.
    expect(within(row).getByTestId('season-frost-site-1')).toBeTruthy();
  });

  it('renders nothing when there are no outdoor season states', async () => {
    mockOverview([]);
    const { container } = renderWithProviders(<SeasonOverviewPanel />);

    await waitFor(() => {
      expect(screen.queryByTestId('season-overview-panel')).toBeNull();
    });
    expect(container.querySelector('[data-testid="season-row-site-1"]')).toBeNull();
  });

  it('falls back to the climatological typical-frost date when no live forecast', async () => {
    mockOverview([
      {
        ...preWinterState,
        trigger_tier: 'climatological',
        trigger_reason_i18n_key: 'pages.season.trigger.climateEstimate',
        forecast_first_frost_date: null,
        estimated_first_frost_md: '11-15',
      },
    ]);
    renderWithProviders(<SeasonOverviewPanel />);

    const frost = await screen.findByTestId('season-frost-site-1');
    // "Erster Frost typisch um …" — assert the static prefix, not the locale date.
    expect(frost.textContent).toContain('typisch');
    const trigger = screen.getByTestId('season-trigger-site-1');
    expect(trigger.textContent).toContain(
      i18n.t('enums.seasonTriggerTier.climatological'),
    );
  });
});
