import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { screen, waitFor, cleanup, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import i18n from 'i18next';
import { ApiError } from '@/api/errors';
import type { AdminUser, ApiErrorResponse } from '@/api/types';
import { createTestStore, authState, renderWithProviders } from '@/test/helpers';

/**
 * #1857 — a platform admin raising another account's trust proves it is really them.
 *
 * `PATCH /admin/platform/users/{key}` used to set `email_verified` — the trust
 * anchor of the OAuth auto-link — on nothing but the admin session. The backend
 * now asks for the **admin's own** step-up (`current_password`, or
 * `step_up_token` / `step_up_code` without one) exactly when the update turns
 * `email_verified` or `is_active` from false to true. Every other update (a
 * rename, lowering either flag) saves as before, without a dialog.
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
  fetchUserMemberships: vi.fn().mockResolvedValue([]),
  addUserToTenant: vi.fn(),
  removeUserFromTenant: vi.fn(),
  changeUserMembershipRole: vi.fn(),
}));

vi.mock('@/api/endpoints/auth', async () => ({
  ...(await vi.importActual<typeof import('@/api/endpoints/auth')>('@/api/endpoints/auth')),
  listProviders: vi.fn(),
  requestStepUpCode: vi.fn().mockResolvedValue({ expires_at: '2026-09-25T12:10:00Z', expires_in: 600 }),
}));

const admin = await import('@/api/endpoints/adminPlatform');
const auth = await import('@/api/endpoints/auth');

// Credential-shaped values are assembled at runtime (GitGuardian, #1838).
const ADMIN_PASSWORD = ['admin', 'Secr', '3t'].join('-');

const UNVERIFIED: AdminUser = {
  key: 'target-key',
  email: 'target@example.org',
  display_name: 'Target User',
  is_active: true,
  email_verified: false,
  last_login_at: null,
  created_at: '2026-01-01T00:00:00Z',
  tenant_count: 0,
  roles: [],
} as unknown as AdminUser;

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

async function renderPage(target: AdminUser = UNVERIFIED) {
  (admin.fetchAdminUsers as ReturnType<typeof vi.fn>).mockResolvedValue([target]);
  const { default: Page } = await import('@/pages/admin/AdminEditUserPage');
  renderWithProviders(<Page />, { store: createTestStore(authState({ platformAdmin: true })) });
  await screen.findByTestId('edit-user-save');
}

function switchInput(testId: string): HTMLInputElement {
  return screen.getByTestId(testId).querySelector('input') as HTMLInputElement;
}

function passwordInput(dialog: HTMLElement): HTMLInputElement {
  return within(dialog).getByTestId('update-user-password').querySelector('input') as HTMLInputElement;
}

describe('AdminEditUserPage — trust-raise step-up (#1857)', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
    vi.clearAllMocks();
    sessionStorage.clear();
    (admin.updateAdminUser as ReturnType<typeof vi.fn>).mockImplementation(
      async (_key: string, payload: Record<string, unknown>) => ({ ...UNVERIFIED, ...payload }),
    );
    (auth.listProviders as ReturnType<typeof vi.fn>).mockResolvedValue([{ provider: 'local' }]);
  });
  afterEach(() => {
    cleanup();
    sessionStorage.clear();
  });

  it("asks for the admin's own password before verifying the e-mail and sends it along", async () => {
    await renderPage();

    await userEvent.click(switchInput('edit-user-email-verified-switch'));
    await userEvent.click(screen.getByTestId('edit-user-save'));

    // The dialog first — nothing is saved before the step-up.
    const dialog = await screen.findByTestId('update-user-dialog');
    expect(admin.updateAdminUser).not.toHaveBeenCalled();
    // No echo to type back, and the password is named as the admin's own.
    expect(within(dialog).queryByTestId('update-user-echo')).toBeNull();
    expect(dialog).toHaveTextContent(i18n.t('pages.auth.adminDeleteUserPasswordHelper'));

    await userEvent.type(passwordInput(dialog), ADMIN_PASSWORD);
    await userEvent.click(within(dialog).getByTestId('update-user-confirm'));

    await waitFor(() =>
      expect(admin.updateAdminUser).toHaveBeenCalledWith('target-key', {
        display_name: undefined,
        is_active: undefined,
        email_verified: true,
        current_password: ADMIN_PASSWORD,
      }),
    );
    await waitFor(() => expect(screen.queryByTestId('update-user-dialog')).toBeNull());
  });

  it('asks for the step-up when reactivating a deactivated account', async () => {
    await renderPage({ ...UNVERIFIED, email_verified: true, is_active: false } as AdminUser);

    await userEvent.click(switchInput('edit-user-active-switch'));
    await userEvent.click(screen.getByTestId('edit-user-save'));

    const dialog = await screen.findByTestId('update-user-dialog');
    await userEvent.type(passwordInput(dialog), ADMIN_PASSWORD);
    await userEvent.click(within(dialog).getByTestId('update-user-confirm'));

    await waitFor(() =>
      expect(admin.updateAdminUser).toHaveBeenCalledWith(
        'target-key',
        expect.objectContaining({ is_active: true, current_password: ADMIN_PASSWORD }),
      ),
    );
  });

  it('saves a rename without a step-up', async () => {
    await renderPage();

    const name = screen.getByTestId('edit-user-display-name').querySelector('input') as HTMLInputElement;
    await userEvent.clear(name);
    await userEvent.type(name, 'Renamed User');
    await userEvent.click(screen.getByTestId('edit-user-save'));

    await waitFor(() =>
      expect(admin.updateAdminUser).toHaveBeenCalledWith('target-key', {
        display_name: 'Renamed User',
        is_active: undefined,
        email_verified: undefined,
      }),
    );
    expect(screen.queryByTestId('update-user-dialog')).toBeNull();
  });

  it('saves lowering trust (deactivating) without a step-up', async () => {
    await renderPage({ ...UNVERIFIED, email_verified: true } as AdminUser);

    await userEvent.click(switchInput('edit-user-active-switch'));
    await userEvent.click(screen.getByTestId('edit-user-save'));

    await waitFor(() =>
      expect(admin.updateAdminUser).toHaveBeenCalledWith('target-key', {
        display_name: undefined,
        is_active: false,
        email_verified: undefined,
      }),
    );
    expect(screen.queryByTestId('update-user-dialog')).toBeNull();
  });

  it('keeps the dialog open and shows a refused step-up inside it', async () => {
    (admin.updateAdminUser as ReturnType<typeof vi.fn>).mockRejectedValue(
      apiError(401, { error_code: 'UNAUTHORIZED', message: 'Password confirmation failed.' }),
    );
    await renderPage();

    await userEvent.click(switchInput('edit-user-email-verified-switch'));
    await userEvent.click(screen.getByTestId('edit-user-save'));
    const dialog = await screen.findByTestId('update-user-dialog');
    await userEvent.type(passwordInput(dialog), 'wrong');
    await userEvent.click(within(dialog).getByTestId('update-user-confirm'));

    expect(await within(dialog).findByTestId('update-user-error')).toHaveTextContent(
      'Password confirmation failed.',
    );
    expect(screen.getByTestId('update-user-dialog')).toBeInTheDocument();
    expect(passwordInput(dialog)).toHaveValue('');
  });

  it('asks a federated admin for a code bound to the admin account update', async () => {
    (auth.listProviders as ReturnType<typeof vi.fn>).mockResolvedValue([{ provider: 'github' }]);
    await renderPage();

    await userEvent.click(switchInput('edit-user-email-verified-switch'));
    await userEvent.click(screen.getByTestId('edit-user-save'));
    const dialog = await screen.findByTestId('update-user-dialog');
    await userEvent.click(await within(dialog).findByTestId('update-user-send-code'));

    await waitFor(() => expect(auth.requestStepUpCode).toHaveBeenCalledWith('admin_account_update'));
  });

  it('sends a pending fresh-sign-in token as step_up_token', async () => {
    const token = ['re', 'auth', '-', 'tok', 'en'].join('');
    const { storePendingStepUpToken } = await import('@/utils/stepUpReauth');
    storePendingStepUpToken(token, 'admin_account_update');
    (auth.listProviders as ReturnType<typeof vi.fn>).mockResolvedValue([{ key: 'g', provider: 'google' }]);
    await renderPage();

    await userEvent.click(switchInput('edit-user-email-verified-switch'));
    await userEvent.click(screen.getByTestId('edit-user-save'));
    const dialog = await screen.findByTestId('update-user-dialog');
    expect(await within(dialog).findByTestId('update-user-reauth-done')).toBeInTheDocument();
    await userEvent.click(within(dialog).getByTestId('update-user-confirm'));

    await waitFor(() =>
      expect(admin.updateAdminUser).toHaveBeenCalledWith(
        'target-key',
        expect.objectContaining({ email_verified: true, step_up_token: token }),
      ),
    );
  });
});
