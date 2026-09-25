import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { screen, waitFor, cleanup, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import i18n from 'i18next';
import { ApiError } from '@/api/errors';
import { createTestStore, renderWithProviders } from '@/test/helpers';

/**
 * #1791 — erasing a whole tenant asks the requester to prove it is really them.
 *
 * Since #1769 `DELETE /admin/platform/tenants/{key}` erases every tenant-scoped
 * collection irreversibly. The backend now refuses the request unless its body
 * echoes the tenant's slug (422) and, for an account with a local password,
 * carries the current password (401). This page used to confirm with one
 * button and send no body at all, so after the backend change it could only
 * fail — and before it, one click erased a garden.
 *
 * The password field fails **closed** (the #394 lesson): it is shown unless the
 * account is positively known to be federated-only. A failed provider load must
 * not hide it, or a local account would hit 401 with no field to answer it.
 */

vi.mock('react-router-dom', async () => ({
  ...(await vi.importActual<typeof import('react-router-dom')>('react-router-dom')),
  useParams: () => ({ key: 'garden-key' }),
}));

vi.mock('@/api/endpoints/adminPlatform', () => ({
  fetchAdminTenants: vi.fn(),
  fetchAdminUsers: vi.fn().mockResolvedValue([]),
  fetchTenantMembers: vi.fn().mockResolvedValue([]),
  updateAdminTenant: vi.fn(),
  deleteAdminTenant: vi.fn(),
  addTenantMember: vi.fn(),
  removeTenantMember: vi.fn(),
  changeTenantMemberRole: vi.fn(),
}));

vi.mock('@/api/endpoints/auth', async () => ({
  ...(await vi.importActual<typeof import('@/api/endpoints/auth')>('@/api/endpoints/auth')),
  listProviders: vi.fn(),
}));

const admin = await import('@/api/endpoints/adminPlatform');
const auth = await import('@/api/endpoints/auth');

const TENANT = {
  key: 'garden-key',
  name: 'Gemeinschaftsgarten',
  slug: 'gemeinschaftsgarten',
  tenant_type: 'organization',
  description: '',
  is_active: true,
  is_platform: false,
};

function providers(list: { provider: string }[] | Error) {
  const mock = auth.listProviders as ReturnType<typeof vi.fn>;
  if (list instanceof Error) mock.mockRejectedValue(list);
  else mock.mockResolvedValue(list);
}

async function openDeleteDialog() {
  const { default: Page } = await import('@/pages/admin/AdminEditTenantPage');
  renderWithProviders(<Page />, { store: createTestStore() });
  await userEvent.click(await screen.findByTestId('delete-tenant-btn'));
  return screen.findByTestId('tenant-delete-dialog');
}

describe('AdminEditTenantPage — tenant deletion step-up (#1791)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (admin.fetchAdminTenants as ReturnType<typeof vi.fn>).mockResolvedValue([TENANT]);
    (admin.deleteAdminTenant as ReturnType<typeof vi.fn>).mockResolvedValue(undefined);
  });
  afterEach(() => cleanup());

  it('keeps the confirm button disabled until the slug is typed back and the password given', async () => {
    providers([{ provider: 'local' }]);
    const dialog = await openDeleteDialog();
    const confirm = within(dialog).getByTestId('tenant-delete-confirm');

    expect(confirm).toBeDisabled();
    await userEvent.type(within(dialog).getByTestId('tenant-delete-slug').querySelector('input')!, 'gemeinschaftsgarte');
    await userEvent.type(within(dialog).getByLabelText(/passwort|password/i), 'my-password');
    expect(confirm).toBeDisabled();
    await userEvent.type(within(dialog).getByTestId('tenant-delete-slug').querySelector('input')!, 'n');
    expect(confirm).toBeEnabled();
  });

  it('sends the slug echo and the password with the deletion', async () => {
    providers([{ provider: 'local' }]);
    const dialog = await openDeleteDialog();

    await userEvent.type(within(dialog).getByTestId('tenant-delete-slug').querySelector('input')!, TENANT.slug);
    await userEvent.type(within(dialog).getByLabelText(/passwort|password/i), 'my-password');
    await userEvent.click(within(dialog).getByTestId('tenant-delete-confirm'));

    await waitFor(() =>
      expect(admin.deleteAdminTenant).toHaveBeenCalledWith('garden-key', {
        confirm_slug: TENANT.slug,
        password: 'my-password',
      }),
    );
  });

  it('asks a federated account for the slug alone', async () => {
    providers([{ provider: 'google' }]);
    const dialog = await openDeleteDialog();
    const confirm = within(dialog).getByTestId('tenant-delete-confirm');

    await userEvent.type(within(dialog).getByTestId('tenant-delete-slug').querySelector('input')!, TENANT.slug);
    // Sync point: the confirm button enables only once the provider list said
    // "federated" — before that the password field is shown (fail closed).
    await waitFor(() => expect(confirm).toBeEnabled());
    expect(within(dialog).queryByLabelText(/passwort|password/i)).not.toBeInTheDocument();
    await userEvent.click(confirm);

    await waitFor(() =>
      expect(admin.deleteAdminTenant).toHaveBeenCalledWith('garden-key', { confirm_slug: TENANT.slug }),
    );
  });

  it('still asks for the password when the provider list could not be loaded', async () => {
    providers(new Error('network down'));
    const dialog = await openDeleteDialog();

    await waitFor(() => expect(auth.listProviders).toHaveBeenCalled());
    expect(within(dialog).getByLabelText(/passwort|password/i)).toBeInTheDocument();
  });

  it('still asks for the password when the account lists no provider at all', async () => {
    // Review SEC-003: seeded accounts (demo admin, E2E platform admin) carry a
    // password hash but no `local` provider row. An empty list is "unknown",
    // not "federated" — hiding the field there is the #394 dead end.
    providers([]);
    const dialog = await openDeleteDialog();

    await waitFor(() => expect(auth.listProviders).toHaveBeenCalled());
    await userEvent.type(within(dialog).getByTestId('tenant-delete-slug').querySelector('input')!, TENANT.slug);
    expect(within(dialog).getByLabelText(/passwort|password/i)).toBeInTheDocument();
    expect(within(dialog).getByTestId('tenant-delete-confirm')).toBeDisabled();
  });

  it('shows the password field after the server asked for one, even for a federated-looking account', async () => {
    providers([{ provider: 'google' }]);
    (admin.deleteAdminTenant as ReturnType<typeof vi.fn>).mockRejectedValueOnce(
      new ApiError(
        {
          error_id: 'err_2',
          error_code: 'UNAUTHORIZED',
          message: 'Password confirmation failed.',
          details: [],
          timestamp: '',
          path: '/x',
          method: 'DELETE',
        },
        401,
      ),
    );
    const dialog = await openDeleteDialog();
    const confirm = within(dialog).getByTestId('tenant-delete-confirm');
    await userEvent.type(within(dialog).getByTestId('tenant-delete-slug').querySelector('input')!, TENANT.slug);
    await waitFor(() => expect(confirm).toBeEnabled());

    await userEvent.click(confirm);

    expect(await within(dialog).findByLabelText(/passwort|password/i)).toBeInTheDocument();
  });

  it('shows the lockout with its minutes on 429 STEP_UP_LOCKED (#1816)', async () => {
    providers([{ provider: 'local' }]);
    (admin.deleteAdminTenant as ReturnType<typeof vi.fn>).mockRejectedValue(
      new ApiError(
        {
          error_id: 'err_3',
          error_code: 'STEP_UP_LOCKED',
          message: 'Too many failed confirmations. Try again in 15 minutes.',
          details: [{ field: 'password', reason: 'locked', code: 'STEP_UP_LOCKED', retry_after_minutes: '15' }],
          timestamp: '',
          path: '/x',
          method: 'DELETE',
        },
        429,
      ),
    );
    const dialog = await openDeleteDialog();

    await userEvent.type(within(dialog).getByTestId('tenant-delete-slug').querySelector('input')!, TENANT.slug);
    await userEvent.type(within(dialog).getByLabelText(/passwort|password/i), 'wrong');
    await userEvent.click(within(dialog).getByTestId('tenant-delete-confirm'));

    expect(await within(dialog).findByTestId('tenant-delete-error')).toHaveTextContent(
      i18n.t('pages.auth.stepUpLocked', { minutes: '15' }),
    );
  });

  it('keeps the dialog open and shows a refused step-up inside it', async () => {
    providers([{ provider: 'local' }]);
    (admin.deleteAdminTenant as ReturnType<typeof vi.fn>).mockRejectedValue(
      new ApiError(
        {
          error_id: 'err_1',
          error_code: 'UNAUTHORIZED',
          message: 'Password confirmation failed.',
          details: [],
          timestamp: '',
          path: '/x',
          method: 'DELETE',
        },
        401,
      ),
    );
    const dialog = await openDeleteDialog();

    await userEvent.type(within(dialog).getByTestId('tenant-delete-slug').querySelector('input')!, TENANT.slug);
    await userEvent.type(within(dialog).getByLabelText(/passwort|password/i), 'wrong');
    await userEvent.click(within(dialog).getByTestId('tenant-delete-confirm'));

    expect(await within(dialog).findByTestId('tenant-delete-error')).toBeInTheDocument();
    expect(screen.getByTestId('tenant-delete-dialog')).toBeInTheDocument();
  });
});
