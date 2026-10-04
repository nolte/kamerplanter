import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { screen, waitFor, cleanup, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import i18n from 'i18next';
import { ApiError } from '@/api/errors';
import type { AdminTenant, AdminTenantMember, ApiErrorResponse } from '@/api/types';
import { createTestStore, authState, renderWithProviders } from '@/test/helpers';

/**
 * #2032 — a platform admin changing a member's role proves it is really them.
 *
 * `PATCH /admin/platform/tenants/{key}/members/{membershipKey}/role` demoted a
 * tenant's last lead on nothing but the admin session. The backend now asks for the
 * **admin's own** step-up for an actual change (`current_password`, or
 * `step_up_token` / `step_up_code` without one), bound to the membership (#1884,
 * act `admin_membership_role_change`). Choosing a role in the select only opens the
 * shared `StepUpConfirmDialog`; the select keeps the stored role until it went through.
 */

vi.mock('react-router-dom', async () => ({
  ...(await vi.importActual<typeof import('react-router-dom')>('react-router-dom')),
  useParams: () => ({ key: 'garden-key' }),
}));

vi.mock('@/api/endpoints/adminPlatform', () => ({
  fetchAdminTenants: vi.fn(),
  fetchAdminUsers: vi.fn().mockResolvedValue([]),
  fetchTenantMembers: vi.fn(),
  updateAdminTenant: vi.fn(),
  deleteAdminTenant: vi.fn(),
  addTenantMember: vi.fn(),
  removeTenantMember: vi.fn(),
  changeTenantMemberRole: vi.fn(),
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

const TENANT = {
  key: 'garden-key',
  name: 'Gemeinschaftsgarten',
  slug: 'gemeinschaftsgarten',
  tenant_type: 'organization',
  description: '',
  owner_user_key: 'u-lead',
  is_active: true,
  is_platform: false,
  max_members: 50,
  member_count: 1,
  created_at: null,
  updated_at: null,
} as unknown as AdminTenant;

const LEAD: AdminTenantMember = {
  membership_key: 'm-lead',
  user_key: 'u-lead',
  display_name: 'Lena Lead',
  email: 'lena@example.org',
  role: 'lead',
  is_active: true,
  joined_at: null,
} as AdminTenantMember;

function apiError(status: number, body: Partial<ApiErrorResponse>): ApiError {
  return new ApiError(
    {
      error_id: 'err',
      error_code: 'X',
      message: 'x',
      details: [],
      timestamp: '',
      path: '/x',
      method: 'PATCH',
      ...body,
    } as ApiErrorResponse,
    status,
  );
}

async function renderPage() {
  (admin.fetchAdminTenants as ReturnType<typeof vi.fn>).mockResolvedValue([TENANT]);
  const { default: Page } = await import('@/pages/admin/AdminEditTenantPage');
  renderWithProviders(<Page />, { store: createTestStore(authState({ platformAdmin: true })) });
  await screen.findByTestId('edit-tenant-save');
}

/** Opens the MUI select of the lead's role and picks the option — a `mousedown`, as in MUI 9. */
async function chooseRole(label: string) {
  const select = await screen.findByTestId('role-select-u-lead');
  await userEvent.click(within(select).getByRole('combobox'));
  await userEvent.click(await screen.findByRole('option', { name: label }));
}

function passwordInput(dialog: HTMLElement): HTMLInputElement {
  return within(dialog).getByTestId('change-member-role-password').querySelector('input') as HTMLInputElement;
}

describe('AdminEditTenantPage — role change step-up (#2032)', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
    vi.clearAllMocks();
    sessionStorage.clear();
    (admin.fetchTenantMembers as ReturnType<typeof vi.fn>).mockResolvedValue([LEAD]);
    (admin.changeTenantMemberRole as ReturnType<typeof vi.fn>).mockImplementation(
      async (_key: string, _membership: string, role: string) => ({ ...LEAD, role }),
    );
    (auth.listProviders as ReturnType<typeof vi.fn>).mockResolvedValue([{ provider: 'local' }]);
  });
  afterEach(() => {
    cleanup();
    sessionStorage.clear();
  });

  it("changes the role only with the admin's own password", async () => {
    await renderPage();

    await chooseRole('Betrachter');

    const dialog = await screen.findByTestId('change-member-role-dialog');
    // Nothing is saved before the step-up, and the dialog names who and to what.
    expect(admin.changeTenantMemberRole).not.toHaveBeenCalled();
    expect(dialog).toHaveTextContent('Lena Lead');
    expect(dialog).toHaveTextContent('Betrachter');

    await userEvent.type(passwordInput(dialog), ADMIN_PASSWORD);
    await userEvent.click(within(dialog).getByTestId('change-member-role-confirm'));

    await waitFor(() =>
      expect(admin.changeTenantMemberRole).toHaveBeenCalledWith('garden-key', 'm-lead', 'viewer', {
        current_password: ADMIN_PASSWORD,
      }),
    );
    await waitFor(() => expect(screen.queryByTestId('change-member-role-dialog')).toBeNull());
  });

  it('keeps the stored role when the dialog is cancelled', async () => {
    await renderPage();
    await chooseRole('Betrachter');

    const dialog = await screen.findByTestId('change-member-role-dialog');
    await userEvent.click(within(dialog).getByTestId('change-member-role-cancel'));

    await waitFor(() => expect(screen.queryByTestId('change-member-role-dialog')).toBeNull());
    expect(admin.changeTenantMemberRole).not.toHaveBeenCalled();
    expect(screen.getByTestId('role-select-u-lead')).toHaveTextContent('Leitung');
  });

  it('keeps the stored role when the step-up is refused', async () => {
    (admin.changeTenantMemberRole as ReturnType<typeof vi.fn>).mockRejectedValue(
      apiError(401, { error_code: 'UNAUTHORIZED', message: 'Password confirmation failed.' }),
    );
    await renderPage();
    await chooseRole('Betrachter');

    const dialog = await screen.findByTestId('change-member-role-dialog');
    await userEvent.type(passwordInput(dialog), 'wrong');
    await userEvent.click(within(dialog).getByTestId('change-member-role-confirm'));

    expect(await within(dialog).findByTestId('change-member-role-error')).toHaveTextContent(
      'Password confirmation failed.',
    );
    expect(screen.getByTestId('role-select-u-lead')).toHaveTextContent('Leitung');
  });

  it('asks a federated admin for a code bound to the membership', async () => {
    (auth.listProviders as ReturnType<typeof vi.fn>).mockResolvedValue([{ provider: 'github' }]);
    await renderPage();
    await chooseRole('Betrachter');

    const dialog = await screen.findByTestId('change-member-role-dialog');
    await userEvent.click(await within(dialog).findByTestId('change-member-role-send-code'));

    await waitFor(() =>
      expect(auth.requestStepUpCode).toHaveBeenCalledWith('admin_membership_role_change', 'm-lead'),
    );
  });
});
