import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { screen, waitFor, cleanup, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import i18n from 'i18next';
import { ApiError } from '@/api/errors';
import type { ApiErrorResponse } from '@/api/types';
import { createTestStore, authState, renderWithProviders } from '@/test/helpers';

/**
 * #1814 / #1816 — a platform admin erasing another account proves it is really them.
 *
 * `DELETE /admin/platform/users/{key}` erases the account at once. The backend
 * now refuses the request unless its body echoes the **target** account's
 * e-mail (422) and, when the **admin's own** account has a local password,
 * carries that password (401); too many failed confirmations answer 429
 * `STEP_UP_LOCKED`. The page used to confirm with one inline button and send no
 * body at all.
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
};

function apiError(status: number, body: Partial<ApiErrorResponse>): ApiError {
  return new ApiError(
    {
      error_id: 'err',
      error_code: 'X',
      message: 'x',
      details: [],
      timestamp: '',
      path: '/x',
      method: 'DELETE',
      ...body,
    } as ApiErrorResponse,
    status,
  );
}

async function openDeleteDialog() {
  const { default: Page } = await import('@/pages/admin/AdminEditUserPage');
  renderWithProviders(<Page />, { store: createTestStore(authState({ platformAdmin: true })) });
  await userEvent.click(await screen.findByTestId('delete-user-btn'));
  return screen.findByTestId('delete-user-dialog');
}

function emailInput(dialog: HTMLElement): HTMLInputElement {
  return within(dialog).getByTestId('delete-user-email').querySelector('input') as HTMLInputElement;
}

describe('AdminEditUserPage — user deletion step-up (#1814)', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
    vi.clearAllMocks();
    (admin.fetchAdminUsers as ReturnType<typeof vi.fn>).mockResolvedValue([TARGET]);
    (admin.deleteAdminUser as ReturnType<typeof vi.fn>).mockResolvedValue(undefined);
    (auth.listProviders as ReturnType<typeof vi.fn>).mockResolvedValue([{ provider: 'local' }]);
  });
  afterEach(() => cleanup());

  it("sends the target's e-mail echo and the admin's own password", async () => {
    const dialog = await openDeleteDialog();
    const confirm = within(dialog).getByTestId('confirm-delete-user-btn');

    // The admin's own e-mail is not the one to type back.
    await userEvent.type(emailInput(dialog), 'tester@example.org');
    await userEvent.type(within(dialog).getByLabelText(/passwort/i), 'admin-password');
    expect(confirm).toBeDisabled();

    await userEvent.clear(emailInput(dialog));
    await userEvent.type(emailInput(dialog), TARGET.email);
    await userEvent.click(confirm);

    await waitFor(() =>
      expect(admin.deleteAdminUser).toHaveBeenCalledWith('target-key', {
        confirm_email: TARGET.email,
        password: 'admin-password',
      }),
    );
  });

  it("says the password is the admin's own", async () => {
    const dialog = await openDeleteDialog();
    expect(dialog).toHaveTextContent(i18n.t('pages.auth.adminDeleteUserPasswordHelper'));
    expect(i18n.t('pages.auth.adminDeleteUserPasswordHelper')).toMatch(/dein/i);
  });

  it('keeps the dialog open and shows a refused step-up inside it', async () => {
    (admin.deleteAdminUser as ReturnType<typeof vi.fn>).mockRejectedValue(
      apiError(401, { error_code: 'UNAUTHORIZED', message: 'Password confirmation failed.' }),
    );
    const dialog = await openDeleteDialog();

    await userEvent.type(emailInput(dialog), TARGET.email);
    await userEvent.type(within(dialog).getByLabelText(/passwort/i), 'wrong');
    await userEvent.click(within(dialog).getByTestId('confirm-delete-user-btn'));

    expect(await within(dialog).findByTestId('delete-user-error')).toHaveTextContent('Password confirmation failed.');
    expect(screen.getByTestId('delete-user-dialog')).toBeInTheDocument();
    // The rejected password is cleared so it is not resent by accident.
    expect(within(dialog).getByLabelText(/passwort/i)).toHaveValue('');
  });

  it('shows the lockout with its minutes on 429 STEP_UP_LOCKED', async () => {
    (admin.deleteAdminUser as ReturnType<typeof vi.fn>).mockRejectedValue(
      apiError(429, {
        error_code: 'STEP_UP_LOCKED',
        message: 'Too many failed confirmations. Try again in 12 minutes.',
        details: [{ field: 'password', reason: 'locked', code: 'STEP_UP_LOCKED', retry_after_minutes: '12' }],
      }),
    );
    const dialog = await openDeleteDialog();

    await userEvent.type(emailInput(dialog), TARGET.email);
    await userEvent.type(within(dialog).getByLabelText(/passwort/i), 'x');
    await userEvent.click(within(dialog).getByTestId('confirm-delete-user-btn'));

    expect(await within(dialog).findByTestId('delete-user-error')).toHaveTextContent(
      i18n.t('pages.auth.stepUpLocked', { minutes: '12' }),
    );
  });

  it('still asks for the password when the admin lists no provider at all', async () => {
    (auth.listProviders as ReturnType<typeof vi.fn>).mockResolvedValue([]);
    const dialog = await openDeleteDialog();

    await waitFor(() => expect(auth.listProviders).toHaveBeenCalled());
    await userEvent.type(emailInput(dialog), TARGET.email);
    expect(within(dialog).getByLabelText(/passwort/i)).toBeInTheDocument();
    expect(within(dialog).getByTestId('confirm-delete-user-btn')).toBeDisabled();
  });

  it('asks a federated admin for a code that confirms the admin erasure only (review SEC-003)', async () => {
    (auth.listProviders as ReturnType<typeof vi.fn>).mockResolvedValue([{ provider: 'github' }]);
    const dialog = await openDeleteDialog();

    await userEvent.click(await within(dialog).findByTestId('delete-user-send-code'));

    await waitFor(() => expect(auth.requestStepUpCode).toHaveBeenCalledWith('admin_account_erasure', 'target-key'));
  });
});

describe('AdminEditUserPage — back from the fresh sign-in (#1815)', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
    vi.clearAllMocks();
    sessionStorage.clear();
    (admin.fetchAdminUsers as ReturnType<typeof vi.fn>).mockResolvedValue([TARGET]);
    (admin.deleteAdminUser as ReturnType<typeof vi.fn>).mockResolvedValue(undefined);
    (auth.listProviders as ReturnType<typeof vi.fn>).mockResolvedValue([{ key: 'g', provider: 'google' }]);
  });
  afterEach(() => {
    cleanup();
    sessionStorage.clear();
  });

  it('reopens the user-deletion dialog and sends the pending token as step_up_token', async () => {
    // Credential-shaped values are assembled at runtime (GitGuardian, #1838).
    const token = ['re', 'auth', '-', 'tok', 'en'].join('');
    const { storePendingStepUpToken, saveStepUpResume } = await import('@/utils/stepUpReauth');
    storePendingStepUpToken(token, 'admin_account_erasure', 'target-key');
    saveStepUpResume({
      surface: 'delete-user',
      action: 'admin_account_erasure',
      target: 'target-key',
      returnPath: '/',
    });

    const { default: Page } = await import('@/pages/admin/AdminEditUserPage');
    renderWithProviders(<Page />, { store: createTestStore(authState({ platformAdmin: true })) });

    // No click on "delete user": the page reopens the dialog on its own.
    const dialog = await screen.findByTestId('delete-user-dialog');
    expect(await within(dialog).findByTestId('delete-user-reauth-done')).toBeInTheDocument();
    await userEvent.type(emailInput(dialog), TARGET.email);
    await userEvent.click(within(dialog).getByTestId('confirm-delete-user-btn'));

    await waitFor(() =>
      expect(admin.deleteAdminUser).toHaveBeenCalledWith('target-key', {
        confirm_email: TARGET.email,
        step_up_token: token,
      }),
    );
  });
});
