import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { screen, waitFor, cleanup, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import i18n from 'i18next';
import { ApiError } from '@/api/errors';
import type { AdminTenant, AdminTenantMember, AdminUser, ApiErrorResponse } from '@/api/types';
import { createTestStore, authState, renderWithProviders } from '@/test/helpers';

/**
 * #2106 — a platform admin adding an account to a tenant proves it is really them.
 *
 * `POST /admin/platform/tenants/{key}/members` put any account into any tenant — the
 * `platform` tenant, with the `lead` role, included — on nothing but the admin session.
 * The backend now asks for the **admin's own** step-up (`current_password`, or
 * `step_up_token` / `step_up_code` without one), bound to `<tenant_key>|<user_key>` (#1884,
 * act `admin_membership_add`). Pressing "add" only opens the shared `StepUpConfirmDialog`;
 * nothing is written until it went through.
 */

vi.mock('react-router-dom', async () => ({
  ...(await vi.importActual<typeof import('react-router-dom')>('react-router-dom')),
  useParams: () => ({ key: 'garden-key' }),
}));

vi.mock('@/api/endpoints/adminPlatform', () => ({
  fetchAdminTenants: vi.fn(),
  fetchAdminUsers: vi.fn(),
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

const NEWCOMER = {
  key: 'u-new',
  email: 'nora@example.org',
  display_name: 'Nora Neu',
  is_active: true,
} as unknown as AdminUser;

const ADDED: AdminTenantMember = {
  membership_key: 'm-new',
  user_key: 'u-new',
  display_name: 'Nora Neu',
  email: 'nora@example.org',
  role: 'viewer',
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
      method: 'POST',
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

/** Opens the add form, picks the account and presses "add". */
async function pressAdd() {
  await userEvent.click(await screen.findByTestId('show-add-member-btn'));
  const input = within(await screen.findByTestId('add-member-user-input')).getByRole('combobox');
  await userEvent.click(input);
  await userEvent.click(await screen.findByRole('option', { name: /Nora Neu/ }));
  await userEvent.click(screen.getByTestId('add-member-submit-btn'));
}

function passwordInput(dialog: HTMLElement): HTMLInputElement {
  return within(dialog).getByTestId('add-member-password').querySelector('input') as HTMLInputElement;
}

describe('AdminEditTenantPage — adding a member needs the step-up (#2106)', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
    vi.clearAllMocks();
    sessionStorage.clear();
    (admin.fetchTenantMembers as ReturnType<typeof vi.fn>).mockResolvedValue([]);
    (admin.fetchAdminUsers as ReturnType<typeof vi.fn>).mockResolvedValue([NEWCOMER]);
    (admin.addTenantMember as ReturnType<typeof vi.fn>).mockResolvedValue(ADDED);
    (auth.listProviders as ReturnType<typeof vi.fn>).mockResolvedValue([{ provider: 'local' }]);
  });
  afterEach(() => {
    cleanup();
    sessionStorage.clear();
  });

  it("adds the member only with the admin's own password", async () => {
    await renderPage();

    await pressAdd();

    const dialog = await screen.findByTestId('add-member-dialog');
    // Nothing is written before the step-up, and the dialog names who and with which role.
    expect(admin.addTenantMember).not.toHaveBeenCalled();
    expect(dialog).toHaveTextContent('Nora Neu');
    expect(dialog).toHaveTextContent('Betrachter');

    await userEvent.type(passwordInput(dialog), ADMIN_PASSWORD);
    await userEvent.click(within(dialog).getByTestId('add-member-confirm'));

    await waitFor(() =>
      expect(admin.addTenantMember).toHaveBeenCalledWith(
        'garden-key',
        { user_key: 'u-new', role: 'viewer' },
        { current_password: ADMIN_PASSWORD },
      ),
    );
    await waitFor(() => expect(screen.queryByTestId('add-member-dialog')).toBeNull());
    expect(await screen.findByText('Nora Neu')).toBeInTheDocument();
  });

  it('writes nothing when the dialog is cancelled', async () => {
    await renderPage();
    await pressAdd();

    const dialog = await screen.findByTestId('add-member-dialog');
    await userEvent.click(within(dialog).getByTestId('add-member-cancel'));

    await waitFor(() => expect(screen.queryByTestId('add-member-dialog')).toBeNull());
    expect(admin.addTenantMember).not.toHaveBeenCalled();
  });

  it('shows a refused step-up inside the dialog and keeps it open', async () => {
    (admin.addTenantMember as ReturnType<typeof vi.fn>).mockRejectedValue(
      apiError(401, { error_code: 'UNAUTHORIZED', message: 'Password confirmation failed.' }),
    );
    await renderPage();
    await pressAdd();

    const dialog = await screen.findByTestId('add-member-dialog');
    await userEvent.type(passwordInput(dialog), 'wrong');
    await userEvent.click(within(dialog).getByTestId('add-member-confirm'));

    expect(await within(dialog).findByTestId('add-member-error')).toHaveTextContent('Password confirmation failed.');
    expect(screen.getByTestId('add-member-dialog')).toBeInTheDocument();
  });

  it('asks a federated admin for a code bound to the tenant and the account', async () => {
    (auth.listProviders as ReturnType<typeof vi.fn>).mockResolvedValue([{ provider: 'github' }]);
    await renderPage();
    await pressAdd();

    const dialog = await screen.findByTestId('add-member-dialog');
    await userEvent.click(await within(dialog).findByTestId('add-member-send-code'));

    await waitFor(() =>
      expect(auth.requestStepUpCode).toHaveBeenCalledWith('admin_membership_add', 'garden-key|u-new'),
    );
  });
});
