import { describe, it, expect, vi } from 'vitest';
import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import AdminPlansPage from '@/pages/admin/AdminPlansPage';
import { ADMIN_PLATFORM_PATH } from '@/routes/adminPaths';
import { authState, createTestStore, renderWithProviders } from '@/test/helpers';

/**
 * F-12 (#2935) — every admin page leads back to the platform admin hub
 * `/admin/platform`, no longer to the settings page's former platform tab.
 *
 * One behavioural case (the plans page, whose load is the cheapest to stand up)
 * proves the wiring end to end through the router; the source scan below covers
 * every admin page, because a back link fixed on some siblings and not on others
 * is exactly how this class of drift survives (#948).
 */

vi.mock('@/api/endpoints/adminPlans', () => ({
  listPlans: vi.fn().mockResolvedValue([]),
  createPlan: vi.fn(),
  updatePlan: vi.fn(),
  deletePlan: vi.fn(),
}));

const ADMIN_PAGE_SOURCES = import.meta.glob('/src/pages/admin/*Page.tsx', {
  query: '?raw',
  import: 'default',
  eager: true,
}) as Record<string, string>;

/** Back-link and post-action navigations each admin page makes to the hub. */
const EXPECTED_HUB_NAVIGATIONS: Record<string, number> = {
  '/src/pages/admin/AdminEditTenantPage.tsx': 2,
  '/src/pages/admin/AdminEditUserPage.tsx': 2,
  '/src/pages/admin/AdminOidcProvidersPage.tsx': 1,
  '/src/pages/admin/AdminPlansPage.tsx': 1,
  '/src/pages/admin/AdminTenantImportsPage.tsx': 2,
};

describe('admin pages lead back to the platform admin hub (F-12)', () => {
  it('the plans page back link opens /admin/platform', async () => {
    const user = userEvent.setup();
    const { router } = renderWithProviders(<AdminPlansPage />, {
      store: createTestStore(authState({ platformAdmin: true })),
      route: '/admin/plans',
    });

    await user.click(await screen.findByTestId('plans-back'));
    expect(router.state.location.pathname).toBe(ADMIN_PLATFORM_PATH);
    expect(router.state.location.hash).toBe('');
  });

  it.each(Object.entries(EXPECTED_HUB_NAVIGATIONS))(
    '%s navigates to the hub %i time(s) and never to the settings page',
    (path, expected) => {
      const source = ADMIN_PAGE_SOURCES[path];
      expect(source, `${path} not found`).toBeDefined();
      expect(source.match(/navigate\(ADMIN_PLATFORM_PATH\)/g)?.length ?? 0).toBe(expected);
      expect(source).not.toMatch(/['"`]\/settings#platform/);
    },
  );

  it('leaves no admin page navigating to the former settings tab', () => {
    const offenders = Object.entries(ADMIN_PAGE_SOURCES)
      .filter(([, source]) => /\/settings#platform/.test(source))
      .map(([path]) => path);
    expect(offenders).toEqual([]);
  });
});
