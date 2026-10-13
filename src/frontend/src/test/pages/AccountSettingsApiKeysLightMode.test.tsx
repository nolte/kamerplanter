import { describe, it, expect, beforeEach, vi } from 'vitest';
import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { server } from '@/test/mocks/server';
import { renderWithProviders, createTestStore } from '@/test/helpers';

/**
 * REQ-033 §4.3 — the API-key tab must load its data in light mode too.
 *
 * Light mode has no accounts, so the page skips loading linked providers and
 * sessions there. API keys are the exception: they are the only credential the
 * MCP interface accepts, which is why the tab is shown in light mode at all.
 *
 * The regression this pins: the mount effect began with `if (isLightMode) return`
 * and so never called loadApiKeys(). The tab rendered permanently empty — except
 * immediately after creating a key, because that handler refreshes the list
 * itself, which made the bug look intermittent rather than total.
 */

const AUTH_USER = {
  key: 'system-user',
  display_name: 'Gaertner',
  email: 'system@kamerplanter.example',
  locale: 'de',
  timezone: 'Europe/Berlin',
};

function lightModeStore() {
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
        user_key: 'system-user',
        experience_level: 'expert',
        onboarding_completed: true,
        locale: 'de',
        theme: 'light',
        watering_can_liters: 5,
        smart_home_enabled: false,
      },
      isLoading: false,
      error: null,
    },
  });
}

describe('AccountSettingsPage — API keys in light mode', () => {
  beforeEach(() => {
    vi.resetModules();
    window.location.hash = '#apikeys';
  });

  it('loads the existing keys on mount instead of showing an empty table', async () => {
    // The mode module reads runtime config at import time, so it has to be
    // mocked before the page is imported.
    vi.doMock('@/config/mode', () => ({
      KAMERPLANTER_MODE: 'light',
      isLightMode: true,
      isFullMode: false,
    }));

    let apiKeyCalls = 0;
    server.use(
      http.get('*/api/v1/auth/api-keys', () => {
        apiKeyCalls += 1;
        return HttpResponse.json([
          {
            key: 'ak-1',
            label: 'claude-code',
            key_prefix: 'kp_abcde',
            tenant_scope: null,
            revoked: false,
            last_used_at: null,
            created_at: '2026-08-04T10:00:00Z',
          },
        ]);
      }),
    );

    const { default: AccountSettingsPage } = await import('@/pages/auth/AccountSettingsPage');
    renderWithProviders(<AccountSettingsPage />, { store: lightModeStore() });

    // The assertion is the request itself, not the rendered row: the missing
    // fetch *was* the bug, and rendering the table is already covered by the
    // main AccountSettingsPage suites. Asserting on the mount effect keeps this
    // test pinned to the regression rather than to tab-activation mechanics.
    await waitFor(() => expect(apiKeyCalls).toBeGreaterThan(0));
  });
  it('creates a key without a step-up — light mode has no password to ask for (#1847)', async () => {
    vi.doMock('@/config/mode', () => ({
      KAMERPLANTER_MODE: 'light',
      isLightMode: true,
      isFullMode: false,
    }));

    let body: unknown = null;
    server.use(
      http.get('*/api/v1/auth/api-keys', () => HttpResponse.json([])),
      http.post('*/api/v1/auth/api-keys', async ({ request }) => {
        body = await request.json();
        return HttpResponse.json({ key: 'ak-2', label: 'mcp', raw_key: 'kp_light_raw_value' });
      }),
    );

    const { default: AccountSettingsPage } = await import('@/pages/auth/AccountSettingsPage');
    const user = userEvent.setup();
    renderWithProviders(<AccountSettingsPage />, { store: lightModeStore(), route: '/account#apikeys' });

    await user.click(await screen.findByTestId('create-api-key-button'));
    const dialog = await screen.findByTestId('api-key-label-dialog');
    await user.type(within(dialog).getByRole('textbox'), 'mcp');
    await user.click(screen.getByTestId('api-key-label-submit'));

    expect(await screen.findByText('kp_light_raw_value')).toBeInTheDocument();
    // The label alone — no step-up field, and no confirmation dialog on the way.
    expect(body).toEqual({ label: 'mcp' });
    expect(screen.queryByTestId('create-api-key-dialog')).toBeNull();
  });
});
