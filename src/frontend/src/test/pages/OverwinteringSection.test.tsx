import { screen, waitFor } from '@testing-library/react';
import { describe, it, expect, beforeEach } from 'vitest';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';
import OverwinteringSection from '@/pages/pflanzen/OverwinteringSection';
import type {
  OverwinteringProfile,
  PlantOverwinteringStatus,
} from '@/api/types';
import { renderWithProviders } from '../helpers';
import { server } from '../mocks/server';

const profileUrls = [
  '/api/v1/plants/:key/overwintering',
  '/api/v1/t/:tenant/plants/:key/overwintering',
];

const statusUrls = [
  '/api/v1/plants/:key/overwintering/status',
  '/api/v1/t/:tenant/plants/:key/overwintering/status',
];

function mockProfile(profile: OverwinteringProfile) {
  server.use(...profileUrls.map((u) => http.get(u, () => HttpResponse.json(profile))));
}

function mockStatus(status: PlantOverwinteringStatus) {
  server.use(...statusUrls.map((u) => http.get(u, () => HttpResponse.json(status))));
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

  it('shows the winter-hardy empty state when there is no profile and the ampel is green', async () => {
    mockApiError(404, 'ENTITY_NOT_FOUND');
    mockStatus({
      has_profile: false,
      hardiness_light: 'green',
      will_materialize: false,
      site_overwinterable: true,
    });
    renderWithProviders(<OverwinteringSection plantKey="plant-1" />);

    await waitFor(() => {
      expect(
        screen.getByText(i18n.t('pages.season.override.emptyHint')),
      ).toBeTruthy();
    });
    expect(screen.getByTestId('overwintering-section-empty')).toBeTruthy();
    // The winter-hardy hint must not be shown as the "profile coming in autumn" one.
    expect(screen.queryByTestId('overwintering-section-pending')).toBeNull();
    // Nor as the indoor hint — this plant is on a frost-relevant site.
    expect(screen.queryByTestId('overwintering-section-indoor')).toBeNull();
  });

  it('shows the "materialised in autumn" hint when no profile yet but the ampel is yellow/red', async () => {
    mockApiError(404, 'ENTITY_NOT_FOUND');
    mockStatus({
      has_profile: false,
      hardiness_light: 'yellow',
      will_materialize: true,
      site_overwinterable: true,
    });
    renderWithProviders(<OverwinteringSection plantKey="plant-1" />);

    await waitFor(() => {
      expect(screen.getByTestId('overwintering-section-pending')).toBeTruthy();
    });
    expect(
      screen.getByText(i18n.t('pages.season.override.pendingHint')),
    ).toBeTruthy();
    // Must never mislabel a protection-needing plant as winter-hardy.
    expect(
      screen.queryByText(i18n.t('pages.season.override.emptyHint')),
    ).toBeNull();
  });

  it('shows the indoor hint when the plant sits on a non-overwinterable site (even with a yellow ampel)', async () => {
    mockApiError(404, 'ENTITY_NOT_FOUND');
    // Indoor site: never materialised, so `will_materialize` is false despite a
    // yellow ampel — the section must explain no outdoor overwintering is due
    // rather than promise a plan "coming in autumn".
    mockStatus({
      has_profile: false,
      hardiness_light: 'yellow',
      will_materialize: false,
      site_overwinterable: false,
    });
    renderWithProviders(<OverwinteringSection plantKey="plant-1" />);

    await waitFor(() => {
      expect(screen.getByTestId('overwintering-section-indoor')).toBeTruthy();
    });
    expect(
      screen.getByText(i18n.t('pages.season.override.indoorHint')),
    ).toBeTruthy();
    // Must not fall through to the "plan coming in autumn" or winter-hardy hints.
    expect(screen.queryByTestId('overwintering-section-pending')).toBeNull();
    expect(
      screen.queryByText(i18n.t('pages.season.override.emptyHint')),
    ).toBeNull();
  });

  it('falls back to the pending hint (never "winter-hardy", never "indoor") when the status is unknown', async () => {
    mockApiError(404, 'ENTITY_NOT_FOUND');
    // Rejected status read → the slice stores a synthetic "unknown" object with
    // `site_overwinterable: true`, so the safe pending hint wins over the indoor hint.
    server.use(...statusUrls.map((u) => http.get(u, () => new HttpResponse(null, { status: 500 }))));
    renderWithProviders(<OverwinteringSection plantKey="plant-1" />);

    await waitFor(() => {
      expect(screen.getByTestId('overwintering-section-pending')).toBeTruthy();
    });
    expect(
      screen.queryByText(i18n.t('pages.season.override.emptyHint')),
    ).toBeNull();
    expect(screen.queryByTestId('overwintering-section-indoor')).toBeNull();
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
