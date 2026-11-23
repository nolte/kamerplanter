import { describe, it, expect, beforeEach, vi } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import { http, HttpResponse } from 'msw';
import { server } from '@/test/mocks/server';
import { renderWithProviders, createTestStore } from '@/test/helpers';
import AccountSettingsPage from '@/pages/auth/AccountSettingsPage';

/**
 * #1385 — the former Integrations tab carried two kinds of setting, and only one
 * of them belongs to the signed-in user. Since F-11 (#2935) they live in two
 * groups: the per-user switch in Integrations, the installation-wide cards in
 * Installation, which a plain member does not see at all.
 *
 * The smart-home master switch is a per-user preference: every member may turn
 * their own smart-home features on and off. The Home Assistant connection and
 * the Pl@ntNet key are installation-wide — one HA and one key per instance —
 * and the backend gates both behind `require_platform_admin`. Before #1385 it
 * did not, and the page rendered the forms for everyone.
 *
 * What this file is for: without it, hiding the cards has no falsifier on the
 * client, and the next edit to the tab can make them visible again while every
 * other suite (whose user is a platform admin) stays green.
 *
 * The groups are addressed by path (`/settings/<group>`), as in the sibling suites.
 */

const BASE_USER = {
  key: 'user-1',
  display_name: 'Tester',
  email: 'tester@example.org',
  locale: 'de',
  timezone: 'Europe/Berlin',
};

function storeFor(isPlatformAdmin: boolean) {
  return createTestStore({
    auth: {
      user: { ...BASE_USER, is_platform_admin: isPlatformAdmin },
      accessToken: 'tok',
      isAuthenticated: true,
      isLoading: false,
      error: null,
    },
    userPreferences: {
      preferences: {
        key: 'pref-1',
        user_key: 'user-1',
        experience_level: 'expert',
        onboarding_completed: true,
        locale: 'de',
        theme: 'light',
        watering_can_liters: 5,
        // On, so the HA connection card is not hidden by the unrelated
        // smart-home condition — a card absent for two reasons proves neither.
        smart_home_enabled: true,
      },
      loading: false,
      error: null,
    },
  });
}

/** Counts calls so the "not even requested" assertion has something to read. */
let settingsReads = 0;
/** Same for the weather fetch status (F-14, #2934). */
let weatherFetchStatusReads = 0;

beforeEach(() => {
  settingsReads = 0;
  weatherFetchStatusReads = 0;
  vi.clearAllMocks();
  server.use(
    http.get('/api/v1/admin/settings', () => {
      settingsReads += 1;
      return HttpResponse.json({
        home_assistant: {
          ha_url: 'http://homeassistant.local:8123',
          ha_access_token_masked: '••••1234',
          ha_timeout: 10,
          source_ha_url: 'db',
          source_ha_access_token: 'db',
          source_ha_timeout: 'default',
        },
        plant_identification: {
          plantnet_api_key_masked: '••••abcd',
          source_plantnet_api_key: 'db',
        },
      });
    }),
    // The page dispatches fetchPreferences() on mount, and the default handler
    // answers without smart_home_enabled — which overwrites the preloaded store
    // and hides the HA card for a reason that has nothing to do with the gate.
    // Answered here so the only thing varying between these cases is the role.
    http.get('/api/v1/user-preferences', () =>
      HttpResponse.json({ experience_level: 'expert', locale: 'de', theme: 'light', smart_home_enabled: true }),
    ),
    http.get('/api/v1/t/:tenant/user-preferences', () =>
      HttpResponse.json({ experience_level: 'expert', locale: 'de', theme: 'light', smart_home_enabled: true }),
    ),
    http.get('/api/v1/users/me/providers', () => HttpResponse.json([])),
    http.get('/api/v1/users/me/sessions', () => HttpResponse.json([])),
    http.get('/api/v1/auth/api-keys', () => HttpResponse.json([])),
    http.get('/api/v1/admin/weather-providers', () =>
      HttpResponse.json({
        providers: [
          { source_name: 'open-meteo', enabled: true, base_url: 'https://api.open-meteo.com', attribution: '' },
        ],
        openweathermap_global_api_key_set: false,
        fetch_timeout_s: 20,
        fetch_interval_hours: 6,
        default_public_source: 'open-meteo',
      }),
    ),
    http.get('/api/v1/admin/weather-providers/fetch-status', () => {
      weatherFetchStatusReads += 1;
      return HttpResponse.json({
        interval_hours: 6,
        last_run: null,
        last_success: null,
        next_scheduled_at: '2026-11-23T12:00:00Z',
        running: false,
        manual_fetch_available_in_s: 0,
      });
    }),
  );
});

function renderGroup(isPlatformAdmin: boolean, group: 'integrations' | 'installation') {
  return renderWithProviders(<AccountSettingsPage />, {
    store: storeFor(isPlatformAdmin),
    route: `/settings/${group}`,
  });
}

describe('Integrations and Installation — installation-wide settings are platform-admin only', () => {
  it('shows a plain member the per-user switch and neither instance-wide card', async () => {
    renderGroup(false, 'integrations');

    // The tab rendered, and the setting that is genuinely the user's own is here.
    // Asserted first: without it, the two absences below would also be satisfied
    // by a page that failed to render at all.
    expect(await screen.findByTestId('smart-home-master-toggle')).toBeInTheDocument();

    expect(screen.queryByTestId('ha-url-field')).not.toBeInTheDocument();
    expect(screen.queryByTestId('plantnet-key-field')).not.toBeInTheDocument();
    // Nor a pointer to a group this member cannot open.
    expect(screen.queryByTestId('integrations-installation-hint')).not.toBeInTheDocument();
  });

  it('does not even request the settings a plain member may not read', async () => {
    // The deep link into the Installation group itself: the group is not this
    // member's, so the page lands on the first group they see instead.
    const { router } = renderGroup(false, 'installation');
    await screen.findByTestId('settings-section-profile');
    expect(router.state.location.pathname).toBe('/settings/account');
    expect(screen.queryByTestId('settings-group-installation')).not.toBeInTheDocument();

    // The server answers 403 since #1385, and the page's loader swallows the
    // rejection — so a request fired here would be invisible rather than
    // harmless. Asserting the call count is what makes it visible.
    await waitFor(() => expect(settingsReads).toBe(0));
  });

  it('hides the two installation-wide recognition cards from a plain member', async () => {
    // #1401. The DINOv2 card renders an acquire button that dispatches an
    // installation-wide run, and its status read returns the inference service's
    // internal URL; the pest card's routes were gated server-side while the card
    // itself was shown to everyone, so its button answered 403.
    renderGroup(false, 'installation');
    await screen.findByTestId('settings-section-profile');

    expect(screen.queryByTestId('recognition-status-card')).not.toBeInTheDocument();
    expect(screen.queryByTestId('pest-recognition-admin-card')).not.toBeInTheDocument();
  });

  it('shows a platform admin both recognition cards', async () => {
    // The control. Without it the assertion above is satisfied by a page that
    // renders neither card for anyone.
    renderGroup(true, 'installation');
    expect(await screen.findByTestId('recognition-status-card')).toBeInTheDocument();
    expect(screen.getByTestId('pest-recognition-admin-card')).toBeInTheDocument();
  });

  it('shows a platform admin both cards, and reads the settings', async () => {
    // The control. Without it, a page that renders neither card for anyone
    // passes both tests above.
    renderGroup(true, 'installation');

    expect(await screen.findByTestId('ha-url-field')).toBeInTheDocument();
    expect(screen.getByTestId('plantnet-key-field')).toBeInTheDocument();
    // The operator group is listed, set apart under its own heading.
    expect(screen.getByTestId('settings-group-installation')).toBeInTheDocument();
    expect(screen.getByTestId('settings-nav-operator-heading')).toBeInTheDocument();
    await waitFor(() => expect(settingsReads).toBeGreaterThan(0));
  });

  // F-14 acceptance-5 (#2934): the fetch interval, the fetch status and "fetch now"
  // belong to whoever may manage instance settings (platform admin, or light mode).
  it('hides the weather fetch controls from a plain member in full mode, and never reads the fetch status', async () => {
    renderGroup(false, 'installation');
    // Landed on the member's own first group: the page rendered.
    await screen.findByTestId('settings-section-profile');

    expect(screen.queryByTestId('weather-fetch-interval')).not.toBeInTheDocument();
    expect(screen.queryByTestId('weather-fetch-now-button')).not.toBeInTheDocument();
    expect(screen.queryByTestId('weather-fetch-panel')).not.toBeInTheDocument();
    await waitFor(() => expect(weatherFetchStatusReads).toBe(0));
  });

  it('shows a platform admin the weather fetch interval, status and "fetch now"', async () => {
    // The control for the case above.
    renderGroup(true, 'installation');

    expect(await screen.findByTestId('weather-fetch-interval')).toBeInTheDocument();
    expect(await screen.findByTestId('weather-fetch-now-button')).toBeInTheDocument();
    expect(await screen.findByTestId('weather-fetch-last-success')).toBeInTheDocument();
    await waitFor(() => expect(weatherFetchStatusReads).toBeGreaterThan(0));
  });
});
