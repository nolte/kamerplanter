import { describe, it, expect, beforeEach } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import { http, HttpResponse, type JsonBodyType } from 'msw';
import { server } from '@/test/mocks/server';
import { renderWithProviders, createTestStore } from '@/test/helpers';
import AccountSettingsPage from '@/pages/auth/AccountSettingsPage';

/**
 * MT-045.9 (#2144) — the *platform* tab is the platform admin's, decided by
 * `usePlatformAdmin()` (the `/users/me` flag), not by probing.
 *
 * Before: the tab was offered to every member, and the page found out whether
 * the user was an admin by firing the three `/admin/platform` GETs and catching
 * the 403 — on the platform tab *and* on the integrations tab. A plain member
 * opening either produced three 403s per visit (log and audit noise, and the
 * empty admin half of a tab they could see).
 *
 * The falsifier is the request count, not only the visible tab: a probe that
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
  );
});

describe('Platform tab — offered to platform admins only', () => {
  it('offers a plain member no platform tab and probes no admin endpoint', async () => {
    renderWithProviders(<AccountSettingsPage />, { store: storeFor(false), route: '/account#platform' });

    // The page rendered (the profile tab is the fallback for an unknown hash).
    expect(await screen.findByTestId('settings-tab-profile')).toBeInTheDocument();
    expect(screen.queryByTestId('settings-tab-platform')).not.toBeInTheDocument();
    await waitFor(() => expect(adminReads).toBe(0));
  });

  it('does not probe the admin endpoints from the integrations tab either', async () => {
    renderWithProviders(<AccountSettingsPage />, { store: storeFor(false), route: '/account#ha' });

    expect(await screen.findByTestId('settings-tab-ha')).toBeInTheDocument();
    await waitFor(() => expect(adminReads).toBe(0));
  });

  it('offers a platform admin the tab and loads the admin data once', async () => {
    renderWithProviders(<AccountSettingsPage />, { store: storeFor(true), route: '/account#platform' });

    expect(await screen.findByTestId('settings-tab-platform')).toBeInTheDocument();
    await waitFor(() => expect(adminReads).toBe(3));
  });
});
