import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { screen, waitFor, cleanup, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import i18n from 'i18next';
import type { AdminTenant, AdminUser, AdminUserMembership } from '@/api/types';
import { createTestStore, authState, renderWithProviders } from '@/test/helpers';

/**
 * #2106 — adding an account to a tenant on the user page passes the admin's own step-up.
 *
 * `POST /admin/platform/users/{key}/memberships` is the user-side view of the same add as the
 * tenant page's; it carries the same body (`current_password`, or `step_up_token` /
 * `step_up_code` for `admin_membership_add`, bound to `<tenant_key>|<user_key>`, #1884).
 */

vi.mock('react-router-dom', async () => ({
  ...(await vi.importActual<typeof import('react-router-dom')>('react-router-dom')),
  useParams: () => ({ key: 'target-key' }),
}));

vi.mock('@/api/endpoints/adminPlatform', () => ({
  fetchAdminUsers: vi.fn(),
  fetchAdminTenants: vi.fn(),
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
  tenant_count: 0,
  roles: [],
} as unknown as AdminUser;

const GARDEN = {
  key: 'garden-key',
  name: 'Gemeinschaftsgarten',
  slug: 'gemeinschaftsgarten',
  tenant_type: 'organization',
  is_active: true,
  is_platform: false,
} as unknown as AdminTenant;

const ADDED: AdminUserMembership = {
  membership_key: 'm-garden',
  tenant_key: 'garden-key',
  tenant_name: 'Gemeinschaftsgarten',
  tenant_slug: 'gemeinschaftsgarten',
  role: 'viewer',
  is_active: true,
  joined_at: null,
} as AdminUserMembership;

async function pressAdd() {
  const { default: Page } = await import('@/pages/admin/AdminEditUserPage');
  renderWithProviders(<Page />, { store: createTestStore(authState({ platformAdmin: true })) });
  await userEvent.click(await screen.findByTestId('show-add-tenant-btn'));
  const input = within(await screen.findByTestId('add-tenant-input')).getByRole('combobox');
  await userEvent.click(input);
  await userEvent.click(await screen.findByRole('option', { name: /Gemeinschaftsgarten/ }));
  await userEvent.click(screen.getByTestId('add-membership-submit-btn'));
  return screen.findByTestId('add-membership-dialog');
}

describe('AdminEditUserPage — adding to a tenant needs the step-up (#2106)', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
    vi.clearAllMocks();
    sessionStorage.clear();
    (admin.fetchAdminUsers as ReturnType<typeof vi.fn>).mockResolvedValue([TARGET]);
    (admin.fetchAdminTenants as ReturnType<typeof vi.fn>).mockResolvedValue([GARDEN]);
    (admin.fetchUserMemberships as ReturnType<typeof vi.fn>).mockResolvedValue([]);
    (admin.addUserToTenant as ReturnType<typeof vi.fn>).mockResolvedValue(ADDED);
    (auth.listProviders as ReturnType<typeof vi.fn>).mockResolvedValue([{ provider: 'local' }]);
  });
  afterEach(() => {
    cleanup();
    sessionStorage.clear();
  });

  it("adds the account only with the admin's own password", async () => {
    const dialog = await pressAdd();
    expect(admin.addUserToTenant).not.toHaveBeenCalled();
    expect(dialog).toHaveTextContent('Gemeinschaftsgarten');
    expect(dialog).toHaveTextContent('Betrachter');

    await userEvent.type(
      within(dialog).getByTestId('add-membership-password').querySelector('input') as HTMLInputElement,
      ADMIN_PASSWORD,
    );
    await userEvent.click(within(dialog).getByTestId('add-membership-confirm'));

    await waitFor(() =>
      expect(admin.addUserToTenant).toHaveBeenCalledWith(
        'target-key',
        { tenant_key: 'garden-key', role: 'viewer' },
        { current_password: ADMIN_PASSWORD },
      ),
    );
    await waitFor(() => expect(screen.queryByTestId('add-membership-dialog')).toBeNull());
  });

  it('writes nothing when the dialog is cancelled', async () => {
    const dialog = await pressAdd();

    await userEvent.click(within(dialog).getByTestId('add-membership-cancel'));

    await waitFor(() => expect(screen.queryByTestId('add-membership-dialog')).toBeNull());
    expect(admin.addUserToTenant).not.toHaveBeenCalled();
  });

  it('asks a federated admin for a code bound to the tenant and the account', async () => {
    (auth.listProviders as ReturnType<typeof vi.fn>).mockResolvedValue([{ provider: 'github' }]);
    const dialog = await pressAdd();

    await userEvent.click(await within(dialog).findByTestId('add-membership-send-code'));

    await waitFor(() =>
      expect(auth.requestStepUpCode).toHaveBeenCalledWith('admin_membership_add', 'garden-key|target-key'),
    );
  });
});
