import { describe, it, expect } from 'vitest';
import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { server } from '@/test/mocks/server';
import { renderWithProviders, createTestStore } from '@/test/helpers';
import AdminPlatformPage from '@/pages/admin/AdminPlatformPage';

/**
 * F-12 (#2935) — `/admin/platform`, the platform admin's hub. Shows what the
 * settings page's former platform tab showed (operating mode, statistics, the ways
 * into the admin pages, tenant and user tables) plus the pest-contribution
 * moderation card. Migrated from the "platform tab" suite of
 * `AccountSettingsPageFlows.test.tsx`.
 */

function adminStore() {
  return createTestStore({
    auth: {
      user: {
        key: 'user-1',
        display_name: 'Tester',
        email: 'tester@example.org',
        locale: 'de',
        timezone: 'Europe/Berlin',
        is_platform_admin: true,
      },
      accessToken: 'tok',
      isAuthenticated: true,
      isLoading: false,
      error: null,
      initialized: true,
    },
  });
}

const TENANT = {
  key: 'ten-1',
  name: 'Gemeinschaftsgarten',
  slug: 'gemeinschaftsgarten',
  tenant_type: 'organization',
  is_active: true,
  is_platform: false,
  status: 'active',
  member_count: 4,
};

const USER = {
  key: 'usr-1',
  display_name: 'Gärtnerin',
  email: 'gaertnerin@example.org',
  is_active: true,
  email_verified: true,
  roles: [{ tenant_key: 'ten-1', tenant_name: 'Gemeinschaftsgarten', role: 'lead' }],
};

const FORBIDDEN = {
  error_id: 'e',
  error_code: 'FORBIDDEN',
  message: 'no',
  details: [],
  timestamp: '',
  path: '',
  method: 'GET',
};

function serveAdminData() {
  server.use(
    http.get('/api/v1/admin/platform/stats', () =>
      HttpResponse.json({ active_users: 3, total_users: 5, active_tenants: 2, total_memberships: 7 }),
    ),
    http.get('/api/v1/admin/platform/tenants', () => HttpResponse.json([TENANT])),
    http.get('/api/v1/admin/platform/users', () => HttpResponse.json([USER])),
  );
}

describe('AdminPlatformPage — the platform admin hub', () => {
  it('renders the mode cards, the statistics and every way into the admin pages', async () => {
    serveAdminData();
    renderWithProviders(<AdminPlatformPage />, { store: adminStore(), route: '/admin/platform' });

    expect(screen.getByTestId('page-title')).toHaveTextContent(/Plattform-Verwaltung|Platform administration/);
    // The three mode cards (light/full/enterprise) always render.
    expect(await screen.findByText('Light Mode')).toBeInTheDocument();
    await waitFor(() => expect(screen.getByText('3')).toBeInTheDocument());
    expect(screen.getByTestId('admin-oidc-open')).toBeEnabled();
    expect(screen.getByTestId('admin-plans-open')).toBeEnabled();
    expect(screen.getByTestId('admin-tenant-imports-open')).toBeEnabled();
    // The tenant and user tables lead into the edit pages.
    expect(screen.getByTestId('edit-tenant-ten-1')).toBeInTheDocument();
    expect(screen.getByTestId('edit-user-usr-1')).toBeInTheDocument();
  });

  it('holds the pest-contribution moderation card that used to sit in the integrations tab', async () => {
    serveAdminData();
    renderWithProviders(<AdminPlatformPage />, { store: adminStore(), route: '/admin/platform' });

    expect(await screen.findByTestId('pest-contributions-admin-card')).toBeInTheDocument();
  });

  it.each([
    ['admin-oidc-open', '/admin/oidc-providers'],
    ['admin-plans-open', '/admin/plans'],
    ['admin-tenant-imports-open', '/admin/tenant-imports'],
    ['edit-tenant-ten-1', '/admin/tenants/ten-1'],
    ['edit-user-usr-1', '/admin/users/usr-1'],
  ])('%s leads to %s', async (testId, path) => {
    serveAdminData();
    const user = userEvent.setup();
    const { router } = renderWithProviders(<AdminPlatformPage />, {
      store: adminStore(),
      route: '/admin/platform',
    });

    await user.click(await screen.findByTestId(testId));
    expect(router.state.location.pathname).toBe(path);
  });

  it('shows a load error with retry instead of the admin half when the reads are refused', async () => {
    let statsCalls = 0;
    server.use(
      http.get('/api/v1/admin/platform/stats', () => {
        statsCalls += 1;
        return HttpResponse.json(FORBIDDEN, { status: 403 });
      }),
      http.get('/api/v1/admin/platform/tenants', () => HttpResponse.json([])),
      http.get('/api/v1/admin/platform/users', () => HttpResponse.json([])),
    );
    const user = userEvent.setup();
    renderWithProviders(<AdminPlatformPage />, { store: adminStore(), route: '/admin/platform' });

    // Mode cards still render; admin stat numbers and launchers do not.
    expect(await screen.findByText('Light Mode')).toBeInTheDocument();
    const loadError = await screen.findByTestId('admin-data-load-error');
    expect(screen.queryByTestId('admin-oidc-card')).not.toBeInTheDocument();
    expect(screen.queryByTestId('admin-plans-card')).not.toBeInTheDocument();

    // The retry reads again.
    await user.click(within(loadError).getByRole('button'));
    await waitFor(() => expect(statsCalls).toBe(2));
  });
});

describe('AdminPlatformPage — heading hierarchy', () => {
  it('puts every card heading one level below the page title (no skipped levels)', async () => {
    serveAdminData();
    renderWithProviders(<AdminPlatformPage />, { store: adminStore(), route: '/admin/platform' });
    await screen.findByTestId('edit-user-usr-1');
    await screen.findByTestId('pest-contributions-admin-card');

    expect(screen.getAllByRole('heading', { level: 1 })).toHaveLength(1);
    // Mode cards (3), launchers (3), tenant + user tables (2), moderation card (1).
    expect(screen.getAllByRole('heading', { level: 2 }).length).toBeGreaterThanOrEqual(9);
    for (const level of [3, 4, 5, 6]) {
      expect(screen.queryAllByRole('heading', { level })).toHaveLength(0);
    }
  });
});
