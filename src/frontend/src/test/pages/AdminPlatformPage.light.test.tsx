import { describe, it, expect, beforeEach, vi } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import { http, HttpResponse } from 'msw';

// Light mode for the whole file (REQ-027): the sole operator is the platform admin,
// and the `/admin/platform` endpoints are not mounted.
vi.mock('@/config/mode', () => ({
  KAMERPLANTER_MODE: 'light',
  isLightMode: true,
  isFullMode: false,
}));

import { server } from '@/test/mocks/server';
import { renderWithProviders, createTestStore } from '@/test/helpers';
import AdminPlatformPage from '@/pages/admin/AdminPlatformPage';

let adminReads = 0;

beforeEach(() => {
  adminReads = 0;
  const count = () => {
    adminReads += 1;
    return HttpResponse.json({}, { status: 404 });
  };
  server.use(
    http.get('/api/v1/admin/platform/stats', count),
    http.get('/api/v1/admin/platform/tenants', count),
    http.get('/api/v1/admin/platform/users', count),
  );
});

describe('AdminPlatformPage (light mode) — F-12', () => {
  it('shows the operator the mode cards and the moderation card without any admin read', async () => {
    renderWithProviders(<AdminPlatformPage />, {
      store: createTestStore({
        auth: {
          user: { key: 'system-user', display_name: 'Operator', is_platform_admin: true },
          isAuthenticated: true,
          isLoading: false,
          initialized: true,
        },
      }),
      route: '/admin/platform',
    });

    expect(await screen.findByText('Light Mode')).toBeInTheDocument();
    // The pest-contribution card moved here from the integrations tab and must stay
    // reachable in light mode, where it was reachable before.
    expect(screen.getByTestId('pest-contributions-admin-card')).toBeInTheDocument();
    // No tenants or users to administer in light mode — and no request for them.
    expect(screen.queryByTestId('admin-oidc-card')).not.toBeInTheDocument();
    expect(screen.queryByTestId('admin-data-load-error')).not.toBeInTheDocument();
    await waitFor(() => expect(adminReads).toBe(0));
  });
});
