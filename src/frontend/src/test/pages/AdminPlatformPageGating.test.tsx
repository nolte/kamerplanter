import { describe, it, expect, beforeEach } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import { http, HttpResponse, type JsonBodyType } from 'msw';
import { server } from '@/test/mocks/server';
import { renderWithProviders, createTestStore } from '@/test/helpers';
import RequirePlatformAdmin from '@/auth/RequirePlatformAdmin';
import AccountSettingsPage from '@/pages/auth/AccountSettingsPage';
import AdminPlatformPage from '@/pages/admin/AdminPlatformPage';

/**
 * F-12 (#2935) — the platform administration moved from the *platform* tab of the
 * settings page to its own page, `/admin/platform`. Migrated from
 * `AccountSettingsPlatformTabGating.test.tsx` (MT-045.9, #2144), whose rule moves
 * with the content: who is a platform admin is the `/users/me` flag, never found
 * out by probing the three `/admin/platform` reads into a 403.
 *
 * The falsifier is the request count, not only the visible content: a probe that
 * swallowed its 403 would render nothing either way.
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
      initialized: true,
    },
  });
}

let adminReads = 0;

beforeEach(() => {
  adminReads = 0;
  const count = (body: JsonBodyType) => () => {
    adminReads += 1;
    return HttpResponse.json(body);
  };
  server.use(
    http.get('/api/v1/admin/platform/stats', count({ active_users: 1, total_users: 1, active_tenants: 1, total_memberships: 1 })),
    http.get('/api/v1/admin/platform/tenants', count([])),
    http.get('/api/v1/admin/platform/users', count([])),
    http.get('/api/v1/users/me/providers', () => HttpResponse.json([])),
    http.get('/api/v1/users/me/sessions', () => HttpResponse.json([])),
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
  );
});

describe('Settings page — carries no platform administration any more (F-12)', () => {
  it.each([false, true])(
    'offers no platform tab and reads no admin endpoint (platform admin: %s)',
    async (isPlatformAdmin) => {
      renderWithProviders(<AccountSettingsPage />, {
        store: storeFor(isPlatformAdmin),
        route: '/settings#platform',
      });

      // The page rendered; an old `#platform` bookmark lands on the first group (F-11).
      expect(await screen.findByTestId('settings-section-profile')).toBeInTheDocument();
      expect(screen.queryByTestId('settings-group-platform')).not.toBeInTheDocument();
      expect(screen.queryByTestId('settings-section-platform')).not.toBeInTheDocument();
      expect(screen.queryByTestId('admin-oidc-card')).not.toBeInTheDocument();
      await waitFor(() => expect(adminReads).toBe(0));
    },
  );

  it('does not probe the admin endpoints from the integrations group either', async () => {
    renderWithProviders(<AccountSettingsPage />, { store: storeFor(false), route: '/settings/integrations#ha' });

    expect(await screen.findByTestId('settings-section-ha')).toBeInTheDocument();
    await waitFor(() => expect(adminReads).toBe(0));
  });

  it('shows a platform admin no pest-contribution card in the installation group', async () => {
    // The card moved to /admin/platform; the Installation group (F-11) keeps the installation cards.
    renderWithProviders(<AccountSettingsPage />, { store: storeFor(true), route: '/settings/installation#recognition' });

    expect(await screen.findByTestId('settings-section-recognition')).toBeInTheDocument();
    // Its sibling installation card is still here — the group did render its admin half.
    expect(await screen.findByTestId('pest-recognition-admin-card')).toBeInTheDocument();
    expect(screen.queryByTestId('pest-contributions-admin-card')).not.toBeInTheDocument();
  });
});

describe('/admin/platform — the platform admin hub loads admin data for admins only', () => {
  it('loads the three admin reads once for a platform admin', async () => {
    renderWithProviders(<AdminPlatformPage />, { store: storeFor(true), route: '/admin/platform' });

    expect(await screen.findByTestId('admin-oidc-card')).toBeInTheDocument();
    await waitFor(() => expect(adminReads).toBe(3));
    // Once per visit, not once per render.
    await new Promise((resolve) => setTimeout(resolve, 50));
    expect(adminReads).toBe(3);
  });

  it('reads no admin endpoint for a member who is not a platform admin', async () => {
    // Defence in depth below the route guard: even mounted bare, the page decides
    // on the `/users/me` flag and does not probe.
    renderWithProviders(<AdminPlatformPage />, { store: storeFor(false), route: '/admin/platform' });

    expect(await screen.findByTestId('admin-platform-page')).toBeInTheDocument();
    expect(screen.queryByTestId('pest-contributions-admin-card')).not.toBeInTheDocument();
    await waitFor(() => expect(adminReads).toBe(0));
  });

  it('refuses a non-admin at the route guard and reads nothing', async () => {
    renderWithProviders(
      <RequirePlatformAdmin>
        <AdminPlatformPage />
      </RequirePlatformAdmin>,
      { store: storeFor(false), route: '/admin/platform' },
    );

    expect(await screen.findByTestId('platform-admin-required-page')).toBeInTheDocument();
    expect(screen.queryByTestId('admin-platform-page')).not.toBeInTheDocument();
    await waitFor(() => expect(adminReads).toBe(0));
  });

  it('lets a platform admin through the route guard — negative control', async () => {
    // Same wrapper, same store shape: the refusal above comes from the flag, not
    // from a page that never renders.
    renderWithProviders(
      <RequirePlatformAdmin>
        <AdminPlatformPage />
      </RequirePlatformAdmin>,
      { store: storeFor(true), route: '/admin/platform' },
    );

    expect(await screen.findByTestId('admin-platform-page')).toBeInTheDocument();
    await waitFor(() => expect(adminReads).toBe(3));
  });
});
