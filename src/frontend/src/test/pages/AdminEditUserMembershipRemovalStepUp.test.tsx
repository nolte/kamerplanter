import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { screen, waitFor, cleanup, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import i18n from 'i18next';
import type { AdminUser, AdminUserMembership } from '@/api/types';
import { createTestStore, authState, renderWithProviders } from '@/test/helpers';

/**
 * #2009 — removing an account from a tenant on the user page passes the admin's own step-up.
 *
 * `DELETE /admin/platform/users/{key}/memberships/{membershipKey}` is the user-side
 * view of the same removal as the tenant page's; it carries the same body
 * (`current_password`, or `step_up_token` / `step_up_code` for
 * `admin_membership_removal`, bound to the membership's key, #1884).
 */

vi.mock('react-router-dom', async () => ({
  ...(await vi.importActual<typeof import('react-router-dom')>('react-router-dom')),
  useParams: () => ({ key: 'target-key' }),
}));

vi.mock('@/api/endpoints/adminPlatform', () => ({
  fetchAdminUsers: vi.fn(),
  fetchAdminTenants: vi.fn().mockResolvedValue([]),
  updateAdminUser: vi.fn(),
  deleteAdminUser: vi.fn(),
  getAdminUserErasurePreview: vi.fn().mockResolvedValue({ personal_tenants: [] }),
  fetchUserMemberships: vi.fn(),
  addUserToTenant: vi.fn(),
  removeUserFromTenant: vi.fn(),
  changeUserMembershipRole: vi.fn(),
}));

vi.mock('@/api/endpoints/auth', async () => ({
  ...(await vi.importActual<typeof import('@/api/endpoints/auth')>('@/api/endpoints/auth')),
  listProviders: vi.fn(),
  requestStepUpCode: vi.fn().mockResolvedValue({ expires_at: '2026-10-03T12:10:00Z', expires_in: 600 }),
}));

const admin = await import('@/api/endpoints/adminPlatform');
const auth = await import('@/api/endpoints/auth');

// Credential-shaped values are assembled at runtime (GitGuardian, #1838).
const ADMIN_PASSWORD = ['admin', 'Secr', '3t'].join('-');

const TARGET = {
  key: 'target-key',
  email: 'target@example.org',
  display_name: 'Target User',
  is_active: true,
  email_verified: true,
  last_login_at: null,
  created_at: '2026-01-01T00:00:00Z',
  tenant_count: 1,
  roles: [],
} as unknown as AdminUser;

const MEMBERSHIP: AdminUserMembership = {
  membership_key: 'm-garden',
  tenant_key: 'garden-key',
  tenant_name: 'Gemeinschaftsgarten',
  tenant_slug: 'gemeinschaftsgarten',
  role: 'lead',
  is_active: true,
  joined_at: null,
} as AdminUserMembership;

async function openRemovalDialog() {
  const { default: Page } = await import('@/pages/admin/AdminEditUserPage');
  renderWithProviders(<Page />, { store: createTestStore(authState({ platformAdmin: true })) });
  await userEvent.click(await screen.findByTestId('remove-membership-garden-key'));
  return screen.findByTestId('remove-membership-dialog');
}

describe('AdminEditUserPage — membership removal step-up (#2009)', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
    vi.clearAllMocks();
    sessionStorage.clear();
    (admin.fetchAdminUsers as ReturnType<typeof vi.fn>).mockResolvedValue([TARGET]);
    (admin.fetchUserMemberships as ReturnType<typeof vi.fn>).mockResolvedValue([MEMBERSHIP]);
    (admin.removeUserFromTenant as ReturnType<typeof vi.fn>).mockResolvedValue(undefined);
    (auth.listProviders as ReturnType<typeof vi.fn>).mockResolvedValue([{ provider: 'local' }]);
  });
  afterEach(() => {
    cleanup();
    sessionStorage.clear();
  });

  it("removes the membership only with the admin's own password", async () => {
    const dialog = await openRemovalDialog();
    expect(admin.removeUserFromTenant).not.toHaveBeenCalled();
    expect(dialog).toHaveTextContent('Gemeinschaftsgarten');

    await userEvent.type(
      within(dialog).getByTestId('remove-membership-password').querySelector('input') as HTMLInputElement,
      ADMIN_PASSWORD,
    );
    await userEvent.click(within(dialog).getByTestId('remove-membership-confirm'));

    await waitFor(() =>
      expect(admin.removeUserFromTenant).toHaveBeenCalledWith('target-key', 'm-garden', {
        current_password: ADMIN_PASSWORD,
      }),
    );
    await waitFor(() => expect(screen.queryByTestId('remove-membership-garden-key')).toBeNull());
  });

  it('keeps the membership when the dialog is cancelled', async () => {
    const dialog = await openRemovalDialog();

    await userEvent.click(within(dialog).getByTestId('remove-membership-cancel'));

    await waitFor(() => expect(screen.queryByTestId('remove-membership-dialog')).toBeNull());
    expect(admin.removeUserFromTenant).not.toHaveBeenCalled();
    expect(screen.getByTestId('remove-membership-garden-key')).toBeInTheDocument();
  });

  it('asks a federated admin for a code bound to the membership', async () => {
    (auth.listProviders as ReturnType<typeof vi.fn>).mockResolvedValue([{ provider: 'github' }]);
    const dialog = await openRemovalDialog();

    await userEvent.click(await within(dialog).findByTestId('remove-membership-send-code'));

    await waitFor(() =>
      expect(auth.requestStepUpCode).toHaveBeenCalledWith('admin_membership_removal', 'm-garden'),
    );
  });
});
