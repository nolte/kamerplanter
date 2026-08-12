import { describe, it, expect, beforeEach, vi } from 'vitest';
import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { server } from '@/test/mocks/server';
import { renderWithProviders, createTestStore } from '@/test/helpers';
import AccountSettingsPage from '@/pages/auth/AccountSettingsPage';

/**
 * REQ-023 / #1118 — the sessions tab must tell a paired phone from a browser.
 *
 * The backend attaches an optional, self-chosen `device_name` to the session a
 * QR-code pairing creates. Every other session — browser login, OAuth callback,
 * and every document stored before the field existed — carries `null` there.
 * So the list has exactly two rendering paths, and both are pinned here:
 *
 * - a labelled session shows the label, with the user agent kept as secondary
 *   detail (the label is what the owner recognises, the user agent is what says
 *   "app, not browser");
 * - an unlabelled session renders as it always did: the user agent, or the
 *   "unknown device" fallback when even that is absent.
 *
 * The second case is the regression guard: the pairing feature must not change
 * a single pixel of how the browser's own session row looks.
 *
 * Rows are addressed by `data-testid="session-row-<session key>"` — the session
 * document key, a stable business key — rather than by table position, so the
 * assertions survive a re-ordering of the list.
 */

const AUTH_USER = {
  key: 'user-1',
  display_name: 'Tester',
  email: 'tester@example.org',
  locale: 'de',
  timezone: 'Europe/Berlin',
};

const PHONE_USER_AGENT = 'Kamerplanter/1.0 (Android 15)';
const BROWSER_USER_AGENT = 'Mozilla/5.0 (X11; Linux x86_64) Firefox/141.0';
const DEVICE_NAME = 'Pixel 8 (Gewaechshaus)';

/** A device paired by QR code: it named itself. */
const PAIRED_SESSION = {
  key: 'sess-paired',
  user_agent: PHONE_USER_AGENT,
  device_name: DEVICE_NAME,
  ip_address: '203.0.113.7',
  created_at: '2026-08-11T14:31:11Z',
  expires_at: '2026-09-10T14:31:11Z',
  is_current: false,
  is_persistent: true,
};

/** A browser login: no label, and none was ever sent. */
const BROWSER_SESSION = {
  key: 'sess-browser',
  user_agent: BROWSER_USER_AGENT,
  device_name: null,
  ip_address: '198.51.100.4',
  created_at: '2026-08-10T09:00:00Z',
  expires_at: '2026-08-11T09:00:00Z',
  is_current: true,
  is_persistent: false,
};

/**
 * A session document written before `device_name` existed. ArangoDB is
 * schemaless and no migration ran, so the API answers without the key at all —
 * not with `null`. The row must render, not blow up on `undefined`.
 */
const LEGACY_SESSION = {
  key: 'sess-legacy',
  user_agent: null,
  ip_address: null,
  created_at: '2026-08-01T09:00:00Z',
  expires_at: '2026-08-31T09:00:00Z',
  is_current: false,
  is_persistent: true,
};

function storeWithUser() {
  return createTestStore({
    auth: {
      user: AUTH_USER,
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
        smart_home_enabled: false,
      },
      loading: false,
      error: null,
    },
  });
}

function renderSessionsTab(sessions: unknown[]) {
  const prefs = {
    experience_level: 'expert',
    locale: 'de',
    theme: 'light',
    smart_home_enabled: false,
  };
  server.use(
    http.get('/api/v1/users/me/sessions', () => HttpResponse.json(sessions)),
    http.get('/api/v1/users/me/providers', () => HttpResponse.json([])),
    http.get('/api/v1/auth/api-keys', () => HttpResponse.json([])),
    http.get('/api/v1/admin/settings', () =>
      HttpResponse.json({
        home_assistant: {
          ha_url: '',
          ha_access_token_masked: '',
          ha_timeout: 10,
          source_ha_url: 'default',
          source_ha_access_token: 'default',
          source_ha_timeout: 'default',
        },
        plant_identification: { plantnet_api_key_masked: '', source_plantnet_api_key: 'none' },
      }),
    ),
    http.get('/api/v1/t/:tenant/user-preferences', () => HttpResponse.json(prefs)),
    http.get('/api/v1/user-preferences', () => HttpResponse.json(prefs)),
  );
  return renderWithProviders(<AccountSettingsPage />, {
    store: storeWithUser(),
    route: '/account#sessions',
  });
}

beforeEach(() => {
  vi.clearAllMocks();
});

describe('AccountSettingsPage — sessions tab device names', () => {
  it('shows the device name of a paired device, with its user agent as detail', async () => {
    renderSessionsTab([PAIRED_SESSION]);

    const row = await screen.findByTestId(`session-row-${PAIRED_SESSION.key}`);

    expect(within(row).getByTestId(`session-device-${PAIRED_SESSION.key}`)).toHaveTextContent(
      DEVICE_NAME,
    );
    expect(within(row).getByTestId(`session-user-agent-${PAIRED_SESSION.key}`)).toHaveTextContent(
      PHONE_USER_AGENT,
    );
  });

  it('falls back to the user agent for a session without a device name', async () => {
    renderSessionsTab([BROWSER_SESSION]);

    const row = await screen.findByTestId(`session-row-${BROWSER_SESSION.key}`);

    // The primary line is the user agent itself — not an empty cell, and not a
    // "no name" placeholder next to it.
    expect(within(row).getByTestId(`session-device-${BROWSER_SESSION.key}`)).toHaveTextContent(
      BROWSER_USER_AGENT,
    );
    // No second line: with nothing to distinguish, repeating the user agent
    // underneath itself would be noise.
    expect(
      within(row).queryByTestId(`session-user-agent-${BROWSER_SESSION.key}`),
    ).not.toBeInTheDocument();
  });

  it('falls back to the unknown-device label when neither name nor user agent is known', async () => {
    renderSessionsTab([LEGACY_SESSION]);

    const row = await screen.findByTestId(`session-row-${LEGACY_SESSION.key}`);

    expect(within(row).getByTestId(`session-device-${LEGACY_SESSION.key}`)).toHaveTextContent(
      'Unknown Device',
    );
  });

  it('renders a labelled and an unlabelled session side by side', async () => {
    renderSessionsTab([PAIRED_SESSION, BROWSER_SESSION]);

    const pairedRow = await screen.findByTestId(`session-row-${PAIRED_SESSION.key}`);
    const browserRow = screen.getByTestId(`session-row-${BROWSER_SESSION.key}`);

    expect(within(pairedRow).getByTestId(`session-device-${PAIRED_SESSION.key}`)).toHaveTextContent(
      DEVICE_NAME,
    );
    expect(
      within(browserRow).getByTestId(`session-device-${BROWSER_SESSION.key}`),
    ).toHaveTextContent(BROWSER_USER_AGENT);
    // The current session is not revocable from its own row; the paired one is.
    expect(screen.getByTestId(`session-revoke-${PAIRED_SESSION.key}`)).toBeInTheDocument();
    expect(
      screen.queryByTestId(`session-revoke-${BROWSER_SESSION.key}`),
    ).not.toBeInTheDocument();
  });

  it('revokes the paired device through its own row', async () => {
    let revoked: string | null = null;
    // The paired device is deliberately *not* the first row: a handler wired to
    // a position rather than to this row's session would still pass otherwise.
    renderSessionsTab([BROWSER_SESSION, PAIRED_SESSION]);
    server.use(
      http.delete('/api/v1/users/me/sessions/:key', ({ params }) => {
        revoked = params.key as string;
        return new HttpResponse(null, { status: 204 });
      }),
    );
    const user = userEvent.setup();

    await user.click(await screen.findByTestId(`session-revoke-${PAIRED_SESSION.key}`));

    // The key sent is the paired session's, not the row's position: a revoke
    // wired to the wrong row would end the browser's own session instead.
    await waitFor(() => expect(revoked).toBe(PAIRED_SESSION.key));
  });
});
