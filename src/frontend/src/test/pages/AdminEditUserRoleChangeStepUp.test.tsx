import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { screen, waitFor, cleanup, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import i18n from 'i18next';
import type { AdminUser, AdminUserMembership } from '@/api/types';
import { createTestStore, authState, renderWithProviders } from '@/test/helpers';

/**
 * #2032 — changing an account's role in a tenant on the user page passes the admin's own step-up.
 *
 * `PATCH /admin/platform/users/{key}/memberships/{membershipKey}/role` is the user-side
 * view of the same role change as the tenant page's; it carries the same body
 * (`current_password`, or `step_up_token` / `step_up_code` for
 * `admin_membership_role_change`, bound to the membership's key, #1884).
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
  requestStepUpCode: vi.fn().mockResolvedValue({ expires_at: '2026-10-04T12:10:00Z', expires_in: 600 }),
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

async function openRoleDialog(label = 'Betrachter') {
  const { default: Page } = await import('@/pages/admin/AdminEditUserPage');
  renderWithProviders(<Page />, { store: createTestStore(authState({ platformAdmin: true })) });
  const select = await screen.findByTestId('role-select-garden-key');
  await userEvent.click(within(select).getByRole('combobox'));
  await userEvent.click(await screen.findByRole('option', { name: label }));
  return screen.findByTestId('change-membership-role-dialog');
}

describe('AdminEditUserPage — role change step-up (#2032)', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
    vi.clearAllMocks();
    sessionStorage.clear();
    (admin.fetchAdminUsers as ReturnType<typeof vi.fn>).mockResolvedValue([TARGET]);
    (admin.fetchUserMemberships as ReturnType<typeof vi.fn>).mockResolvedValue([MEMBERSHIP]);
    (admin.changeUserMembershipRole as ReturnType<typeof vi.fn>).mockImplementation(
      async (_user: string, _membership: string, role: string) => ({ ...MEMBERSHIP, role }),
    );
    (auth.listProviders as ReturnType<typeof vi.fn>).mockResolvedValue([{ provider: 'local' }]);
  });
  afterEach(() => {
    cleanup();
    sessionStorage.clear();
  });

  it("changes the role only with the admin's own password", async () => {
    const dialog = await openRoleDialog();
    expect(admin.changeUserMembershipRole).not.toHaveBeenCalled();
    expect(dialog).toHaveTextContent('Gemeinschaftsgarten');
    expect(dialog).toHaveTextContent('Betrachter');

    await userEvent.type(
      within(dialog).getByTestId('change-membership-role-password').querySelector('input') as HTMLInputElement,
      ADMIN_PASSWORD,
    );
    await userEvent.click(within(dialog).getByTestId('change-membership-role-confirm'));

    await waitFor(() =>
      expect(admin.changeUserMembershipRole).toHaveBeenCalledWith('target-key', 'm-garden', 'viewer', {
        current_password: ADMIN_PASSWORD,
      }),
    );
    await waitFor(() => expect(screen.queryByTestId('change-membership-role-dialog')).toBeNull());
  });

  it('keeps the stored role when the dialog is cancelled', async () => {
    const dialog = await openRoleDialog();

    await userEvent.click(within(dialog).getByTestId('change-membership-role-cancel'));

    await waitFor(() => expect(screen.queryByTestId('change-membership-role-dialog')).toBeNull());
    expect(admin.changeUserMembershipRole).not.toHaveBeenCalled();
    expect(screen.getByTestId('role-select-garden-key')).toHaveTextContent('Leitung');
  });

  it('asks a federated admin for a code bound to the membership', async () => {
    (auth.listProviders as ReturnType<typeof vi.fn>).mockResolvedValue([{ provider: 'github' }]);
    const dialog = await openRoleDialog();

    await userEvent.click(await within(dialog).findByTestId('change-membership-role-send-code'));

    await waitFor(() =>
      expect(auth.requestStepUpCode).toHaveBeenCalledWith('admin_membership_role_change', 'm-garden'),
    );
  });
});
