import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { screen, waitFor, cleanup, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import i18n from 'i18next';
import { ApiError } from '@/api/errors';
import type { AdminTenant, AdminTenantMember, ApiErrorResponse } from '@/api/types';
import { createTestStore, authState, renderWithProviders } from '@/test/helpers';

/**
 * #2009 — a platform admin deactivating a tenant or removing a member proves it is really them.
 *
 * `PATCH /admin/platform/tenants/{key}` with a changed `is_active` and the member
 * removal `DELETE /admin/platform/tenants/{key}/members/{membershipKey}` locked
 * members out on nothing but the admin session. The backend now asks for the
 * **admin's own** step-up (`current_password`, or `step_up_token` /
 * `step_up_code` without one), bound to the tenant or the membership (#1884). The
 * page asks for it in the shared `StepUpConfirmDialog`; a rename saves as before.
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
  requestStepUpCode: vi.fn().mockResolvedValue({ expires_at: '2026-10-03T12:10:00Z', expires_in: 600 }),
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

async function renderPage(tenant: AdminTenant = TENANT) {
  (admin.fetchAdminTenants as ReturnType<typeof vi.fn>).mockResolvedValue([tenant]);
  const { default: Page } = await import('@/pages/admin/AdminEditTenantPage');
  renderWithProviders(<Page />, { store: createTestStore(authState({ platformAdmin: true })) });
  await screen.findByTestId('edit-tenant-save');
}

function activeSwitch(): HTMLInputElement {
  return screen.getByTestId('edit-tenant-active-switch').querySelector('input') as HTMLInputElement;
}

function passwordInput(dialog: HTMLElement, prefix: string): HTMLInputElement {
  return within(dialog).getByTestId(`${prefix}-password`).querySelector('input') as HTMLInputElement;
}

describe('AdminEditTenantPage — deactivation and member removal step-up (#2009)', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
    vi.clearAllMocks();
    sessionStorage.clear();
    (admin.fetchTenantMembers as ReturnType<typeof vi.fn>).mockResolvedValue([LEAD]);
    (admin.updateAdminTenant as ReturnType<typeof vi.fn>).mockImplementation(
      async (_key: string, payload: Record<string, unknown>) => ({ ...TENANT, ...payload }),
    );
    (admin.removeTenantMember as ReturnType<typeof vi.fn>).mockResolvedValue(undefined);
    (auth.listProviders as ReturnType<typeof vi.fn>).mockResolvedValue([{ provider: 'local' }]);
  });
  afterEach(() => {
    cleanup();
    sessionStorage.clear();
  });

  it("asks for the admin's own password before deactivating and sends it along", async () => {
    await renderPage();

    await userEvent.click(activeSwitch());
    await userEvent.click(screen.getByTestId('edit-tenant-save'));

    const dialog = await screen.findByTestId('update-tenant-dialog');
    // Nothing is saved before the step-up, and there is no echo to type back.
    expect(admin.updateAdminTenant).not.toHaveBeenCalled();
    expect(within(dialog).queryByTestId('update-tenant-echo')).toBeNull();
    expect(dialog).toHaveTextContent(i18n.t('pages.auth.adminDeleteUserPasswordHelper'));

    await userEvent.type(passwordInput(dialog, 'update-tenant'), ADMIN_PASSWORD);
    await userEvent.click(within(dialog).getByTestId('update-tenant-confirm'));

    await waitFor(() =>
      expect(admin.updateAdminTenant).toHaveBeenCalledWith('garden-key', {
        name: undefined,
        description: undefined,
        is_active: false,
        current_password: ADMIN_PASSWORD,
      }),
    );
    await waitFor(() => expect(screen.queryByTestId('update-tenant-dialog')).toBeNull());
  });

  it('asks for the step-up when reactivating as well', async () => {
    await renderPage({ ...TENANT, is_active: false } as AdminTenant);

    await userEvent.click(activeSwitch());
    await userEvent.click(screen.getByTestId('edit-tenant-save'));

    expect(await screen.findByTestId('update-tenant-dialog')).toBeInTheDocument();
    expect(admin.updateAdminTenant).not.toHaveBeenCalled();
  });

  it('saves a rename without a step-up', async () => {
    await renderPage();

    const name = screen.getByTestId('edit-tenant-name').querySelector('input') as HTMLInputElement;
    await userEvent.clear(name);
    await userEvent.type(name, 'Dachgarten');
    await userEvent.click(screen.getByTestId('edit-tenant-save'));

    await waitFor(() =>
      expect(admin.updateAdminTenant).toHaveBeenCalledWith('garden-key', {
        name: 'Dachgarten',
        description: undefined,
        is_active: undefined,
      }),
    );
    expect(screen.queryByTestId('update-tenant-dialog')).toBeNull();
  });

  it('keeps the dialog open and shows a refused step-up inside it', async () => {
    (admin.updateAdminTenant as ReturnType<typeof vi.fn>).mockRejectedValue(
      apiError(401, { error_code: 'UNAUTHORIZED', message: 'Password confirmation failed.' }),
    );
    await renderPage();

    await userEvent.click(activeSwitch());
    await userEvent.click(screen.getByTestId('edit-tenant-save'));
    const dialog = await screen.findByTestId('update-tenant-dialog');
    await userEvent.type(passwordInput(dialog, 'update-tenant'), 'wrong');
    await userEvent.click(within(dialog).getByTestId('update-tenant-confirm'));

    expect(await within(dialog).findByTestId('update-tenant-error')).toHaveTextContent(
      'Password confirmation failed.',
    );
    expect(passwordInput(dialog, 'update-tenant')).toHaveValue('');
  });

  it('asks a federated admin for a code bound to this tenant', async () => {
    (auth.listProviders as ReturnType<typeof vi.fn>).mockResolvedValue([{ provider: 'github' }]);
    await renderPage();

    await userEvent.click(activeSwitch());
    await userEvent.click(screen.getByTestId('edit-tenant-save'));
    const dialog = await screen.findByTestId('update-tenant-dialog');
    await userEvent.click(await within(dialog).findByTestId('update-tenant-send-code'));

    await waitFor(() => expect(auth.requestStepUpCode).toHaveBeenCalledWith('admin_tenant_update', 'garden-key'));
  });

  it("removes a member only with the admin's own password", async () => {
    await renderPage();

    await userEvent.click(await screen.findByTestId('remove-member-u-lead'));
    const dialog = await screen.findByTestId('remove-member-dialog');
    expect(admin.removeTenantMember).not.toHaveBeenCalled();
    expect(dialog).toHaveTextContent('Lena Lead');

    await userEvent.type(passwordInput(dialog, 'remove-member'), ADMIN_PASSWORD);
    await userEvent.click(within(dialog).getByTestId('remove-member-confirm'));

    await waitFor(() =>
      expect(admin.removeTenantMember).toHaveBeenCalledWith('garden-key', 'm-lead', {
        current_password: ADMIN_PASSWORD,
      }),
    );
    await waitFor(() => expect(screen.queryByTestId('remove-member-dialog')).toBeNull());
    expect(screen.queryByTestId('remove-member-u-lead')).toBeNull();
  });

  it('keeps the member when the removal is refused', async () => {
    (admin.removeTenantMember as ReturnType<typeof vi.fn>).mockRejectedValue(
      apiError(401, { error_code: 'UNAUTHORIZED', message: 'Password confirmation failed.' }),
    );
    await renderPage();

    await userEvent.click(await screen.findByTestId('remove-member-u-lead'));
    const dialog = await screen.findByTestId('remove-member-dialog');
    await userEvent.type(passwordInput(dialog, 'remove-member'), 'wrong');
    await userEvent.click(within(dialog).getByTestId('remove-member-confirm'));

    expect(await within(dialog).findByTestId('remove-member-error')).toHaveTextContent('Password confirmation failed.');
    expect(screen.getByTestId('remove-member-u-lead')).toBeInTheDocument();
  });

  it('asks a federated admin for a code bound to the membership', async () => {
    (auth.listProviders as ReturnType<typeof vi.fn>).mockResolvedValue([{ provider: 'github' }]);
    await renderPage();

    await userEvent.click(await screen.findByTestId('remove-member-u-lead'));
    const dialog = await screen.findByTestId('remove-member-dialog');
    await userEvent.click(await within(dialog).findByTestId('remove-member-send-code'));

    await waitFor(() => expect(auth.requestStepUpCode).toHaveBeenCalledWith('admin_membership_removal', 'm-lead'));
  });
});
