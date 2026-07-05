import { screen, waitFor, within } from '@testing-library/react';
import { describe, it, expect, beforeEach } from 'vitest';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';
import SpringReturnAssistant from '@/pages/pflege/components/SpringReturnAssistant';
import type { OverwinteringProfile, SeasonState } from '@/api/types';
import { renderWithProviders, createTestStore } from '../helpers';
import { server } from '../mocks/server';

const overviewUrls = [
  '/api/v1/season/overview',
  '/api/v1/t/:tenant/season/overview',
];
const profileUrls = [
  '/api/v1/overwintering-profiles',
  '/api/v1/t/:tenant/overwintering-profiles',
];
const plantInstanceUrls = [
  '/api/v1/plant-instances',
  '/api/v1/t/:tenant/plant-instances',
];
const plantingRunUrls = ['/api/v1/planting-runs', '/api/v1/t/:tenant/planting-runs'];

function mockOverview(states: SeasonState[]) {
  server.use(
    ...overviewUrls.map((u) => http.get(u, () => HttpResponse.json({ states }))),
  );
}

function mockProfiles(list: OverwinteringProfile[]) {
  server.use(...profileUrls.map((u) => http.get(u, () => HttpResponse.json(list))));
}

function mockPlantInstances() {
  server.use(
    ...plantInstanceUrls.map((u) =>
      http.get(u, () =>
        HttpResponse.json([
          { key: 'plant-1', instance_id: 'plant-1', plant_name: 'Dahlie Balkon' },
        ]),
      ),
    ),
  );
}

function mockEmptyPlantingRuns() {
  server.use(...plantingRunUrls.map((u) => http.get(u, () => HttpResponse.json([]))));
}

const preSpringState: SeasonState = {
  site_key: 'site-1',
  season_state_id: 'ss-1',
  phase: 'pre_spring',
  trigger_tier: 'live',
  trigger_reason_i18n_key: 'pages.season.trigger.frostForecast',
  season_year: 2026,
  entered_phase_at: null,
  last_min_temp_c: 3.0,
  forecast_first_frost_date: null,
  estimated_first_frost_md: null,
  estimated_last_frost_md: null,
  evaluated_at: null,
};

describe('SpringReturnAssistant', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
    mockEmptyPlantingRuns();
  });

  it('renders nothing outside the pre_spring phase', async () => {
    mockOverview([]);
    mockProfiles([]);
    mockPlantInstances();
    renderWithProviders(<SpringReturnAssistant />);

    await waitFor(() => {
      expect(screen.queryByTestId('spring-return-assistant')).toBeNull();
    });
  });

  it('resolves the plant name instead of showing the raw key', async () => {
    mockOverview([preSpringState]);
    mockPlantInstances();
    mockProfiles([
      {
        key: 'ow-1',
        plant_key: 'plant-1',
        planting_run_key: null,
        spring_action: 'move_outdoors',
        hardiness_rating: 'needs_protection',
        winter_action: 'fleece',
        winter_action_month: 10,
        user_overridden: false,
        auto_generated: true,
        derived_path: 'A',
      } as unknown as OverwinteringProfile,
    ]);
    renderWithProviders(<SpringReturnAssistant />, { store: createTestStore() });

    const group = await screen.findByTestId('spring-action-move_outdoors');
    expect(within(group).getByText('Dahlie Balkon')).toBeTruthy();
    expect(within(group).queryByText('plant-1')).toBeNull();
  });

  it('shows the staggered hardening-off checklist while in pre_spring', async () => {
    mockOverview([preSpringState]);
    mockProfiles([]);
    mockPlantInstances();
    renderWithProviders(<SpringReturnAssistant />);

    await screen.findByTestId('spring-return-assistant');
    expect(screen.getByTestId('spring-harden-off-list')).toBeTruthy();
    expect(
      screen.getByText(i18n.t('pages.season.spring.hardenOffTitle')),
    ).toBeTruthy();
  });
});
