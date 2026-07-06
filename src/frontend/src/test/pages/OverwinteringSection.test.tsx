import { screen, waitFor } from '@testing-library/react';
import { describe, it, expect, beforeEach } from 'vitest';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';
import OverwinteringSection from '@/pages/pflanzen/OverwinteringSection';
import type { OverwinteringProfile } from '@/api/types';
import { renderWithProviders } from '../helpers';
import { server } from '../mocks/server';

const profileUrls = [
  '/api/v1/plants/:key/overwintering',
  '/api/v1/t/:tenant/plants/:key/overwintering',
];

function mockProfile(profile: OverwinteringProfile) {
  server.use(...profileUrls.map((u) => http.get(u, () => HttpResponse.json(profile))));
}

/** A realistic backend error envelope (NFR-006) — the shape the axios
 * interceptor (`rethrowApiError`) converts into a typed `ApiError`. */
function mockApiError(status: number, errorCode: string) {
  server.use(
    ...profileUrls.map((u) =>
      http.get(
        u,
        () =>
          new HttpResponse(
            JSON.stringify({
              error_id: 'err-1',
              error_code: errorCode,
              message: 'boom',
              details: [],
              timestamp: new Date().toISOString(),
              path: u,
              method: 'GET',
            }),
            { status, headers: { 'Content-Type': 'application/json' } },
          ),
      ),
    ),
  );
}

const autoProfile: OverwinteringProfile = {
  key: 'ow-1',
  plant_key: 'plant-1',
  planting_run_key: null,
  hardiness_rating: 'needs_protection',
  winter_action: 'fleece',
  winter_action_month: 10,
  spring_action: null,
  spring_action_month: null,
  winter_quarter_temp_min: null,
  winter_quarter_temp_max: null,
  winter_quarter_light: null,
  winter_watering: null,
  storage_check_interval_days: null,
  tuber_status: null,
  notes: null,
  user_overridden: false,
  auto_generated: true,
  derived_path: 'A',
  dormancy_care_active: false,
  materialized_at: null,
  source_template_key: null,
} as unknown as OverwinteringProfile;

describe('OverwinteringSection', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
  });

  it('renders the auto-derived profile read-only with the automation badge', async () => {
    mockProfile(autoProfile);
    renderWithProviders(<OverwinteringSection plantKey="plant-1" />);

    await screen.findByTestId('overwintering-section');
    expect(screen.getByTestId('overwintering-auto-badge')).toBeTruthy();
    expect(screen.getByTestId('overwintering-adjust-button')).toBeTruthy();
    // No override yet — the "reset to automatic" action must not be offered.
    expect(screen.queryByTestId('overwintering-reset-button')).toBeNull();
  });

  it('shows the winter-hardy empty state when there is no profile (404)', async () => {
    mockApiError(404, 'ENTITY_NOT_FOUND');
    renderWithProviders(<OverwinteringSection plantKey="plant-1" />);

    await waitFor(() => {
      expect(screen.getByTestId('overwintering-section-empty')).toBeTruthy();
    });
    expect(
      screen.getByText(i18n.t('pages.season.override.emptyHint')),
    ).toBeTruthy();
  });

  it('shows an explicit error state instead of the misleading empty state on a server error (F4)', async () => {
    mockApiError(500, 'INTERNAL_ERROR');
    renderWithProviders(<OverwinteringSection plantKey="plant-1" />);

    await waitFor(() => {
      expect(screen.getByTestId('overwintering-section-error')).toBeTruthy();
    });
    expect(screen.getByTestId('error-display')).toBeTruthy();
    // Must not be confused with the "no winter protection needed" empty state.
    expect(screen.queryByTestId('overwintering-section-empty')).toBeNull();
    expect(screen.getByTestId('error-retry-button')).toBeTruthy();
  });
});
