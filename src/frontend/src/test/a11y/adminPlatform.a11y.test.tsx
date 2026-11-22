/**
 * Axe pass for the platform admin hub `/admin/platform` (F-12, #2935, #1094).
 *
 * Scanned in the state a platform admin reaches in full mode: mode cards,
 * statistics, the launcher cards, the tenant and user tables and the
 * pest-contribution moderation card. The element floor stops a scan of a page
 * still waiting for its admin reads from counting.
 */

import { screen } from '@testing-library/react';
import { describe, it, beforeEach } from 'vitest';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';
import AdminPlatformPage from '@/pages/admin/AdminPlatformPage';
import { createTestStore, authState, renderWithProviders } from '@/test/helpers';
import { server } from '@/test/mocks/server';
import { expectNoA11yViolations } from './expectNoA11yViolations';

describe('platform admin hub a11y', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
    server.use(
      http.get('/api/v1/admin/platform/stats', () =>
        HttpResponse.json({ active_users: 3, total_users: 5, active_tenants: 2, total_memberships: 7 }),
      ),
      http.get('/api/v1/admin/platform/tenants', () =>
        HttpResponse.json([
          {
            key: 'ten-1',
            name: 'Gemeinschaftsgarten',
            slug: 'gemeinschaftsgarten',
            tenant_type: 'organization',
            is_active: true,
            is_platform: false,
            status: 'active',
            member_count: 4,
          },
        ]),
      ),
      http.get('/api/v1/admin/platform/users', () =>
        HttpResponse.json([
          {
            key: 'usr-1',
            display_name: 'Gärtnerin',
            email: 'gaertnerin@example.org',
            is_active: true,
            email_verified: true,
            roles: [{ tenant_key: 'ten-1', tenant_name: 'Gemeinschaftsgarten', role: 'lead' }],
          },
        ]),
      ),
    );
  });

  it('the loaded hub has no critical axe violations', async () => {
    renderWithProviders(<AdminPlatformPage />, {
      store: createTestStore(authState({ platformAdmin: true })),
      route: '/admin/platform',
    });
    await screen.findByTestId('edit-user-usr-1');
    await expectNoA11yViolations(document.body, { minElements: 80 });
  });
});
