import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { screen, waitFor, cleanup, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import i18n from 'i18next';
import { createTestStore, authState, renderWithProviders } from '@/test/helpers';

/**
 * #1961 (AK-FK-06) — the admin deleting another account sees which personal tenants that
 * erases, and how many other members it affects, **before** confirming. A failed read says so
 * instead of looking like "nothing affected". The admin deletion has no grace period; the text says that.
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
  getAdminUserErasurePreview: vi.fn(),
  fetchUserMemberships: vi.fn().mockResolvedValue([]),
  addUserToTenant: vi.fn(),
  removeUserFromTenant: vi.fn(),
  changeUserMembershipRole: vi.fn(),
}));

vi.mock('@/api/endpoints/auth', async () => ({
  ...(await vi.importActual<typeof import('@/api/endpoints/auth')>('@/api/endpoints/auth')),
  listProviders: vi.fn().mockResolvedValue([{ provider: 'local' }]),
}));

const admin = await import('@/api/endpoints/adminPlatform');
const preview = admin.getAdminUserErasurePreview as ReturnType<typeof vi.fn>;

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

async function openDeleteDialog() {
  const { default: Page } = await import('@/pages/admin/AdminEditUserPage');
  renderWithProviders(<Page />, { store: createTestStore(authState({ platformAdmin: true })) });
  await userEvent.click(await screen.findByTestId('delete-user-btn'));
  return screen.findByTestId('delete-user-dialog');
}

describe('AdminEditUserPage — erasure preview in the delete dialog (#1961)', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
    vi.clearAllMocks();
    (admin.fetchAdminUsers as ReturnType<typeof vi.fn>).mockResolvedValue([TARGET]);
  });
  afterEach(() => cleanup());

  it('asks for the preview of the target, not of the signed-in admin, only once the dialog is open', async () => {
    preview.mockResolvedValue({ personal_tenants: [] });
    const { default: Page } = await import('@/pages/admin/AdminEditUserPage');
    renderWithProviders(<Page />, { store: createTestStore(authState({ platformAdmin: true })) });
    await userEvent.click(await screen.findByTestId('delete-user-btn'));
    await screen.findByTestId('delete-user-dialog');

    await waitFor(() => expect(preview).toHaveBeenCalledWith('target-key'));
    expect(preview).toHaveBeenCalledTimes(1);
  });

  it('names the tenant and the number of other members, and says there is no grace period', async () => {
    preview.mockResolvedValue({ personal_tenants: [{ name: 'Targets Garten', other_member_count: 2 }] });
    const dialog = await openDeleteDialog();

    const line = await within(dialog).findByTestId('delete-user-preview-tenant');
    expect(line).toHaveTextContent('Targets Garten');
    expect(line).toHaveTextContent(/2 weitere Mitglieder/);
    expect(await within(dialog).findByTestId('delete-user-preview-shared-hint')).toHaveTextContent(/Frist/);
  });

  it('says nothing about other members when the tenant is used by nobody else', async () => {
    preview.mockResolvedValue({ personal_tenants: [{ name: 'Allein', other_member_count: 0 }] });
    const dialog = await openDeleteDialog();

    expect(await within(dialog).findByTestId('delete-user-preview-tenant')).toHaveTextContent('Allein');
    expect(within(dialog).queryByTestId('delete-user-preview-shared-hint')).not.toBeInTheDocument();
  });

  it('shows nothing for an account without a personal tenant', async () => {
    preview.mockResolvedValue({ personal_tenants: [] });
    const dialog = await openDeleteDialog();

    await waitFor(() => expect(preview).toHaveBeenCalled());
    expect(within(dialog).queryByTestId('delete-user-preview')).not.toBeInTheDocument();
    expect(within(dialog).queryByTestId('delete-user-preview-error')).not.toBeInTheDocument();
  });

  it('says so when the preview could not be read, instead of looking like "nothing affected"', async () => {
    preview.mockRejectedValue(new Error('boom'));
    const dialog = await openDeleteDialog();

    const error = await within(dialog).findByTestId('delete-user-preview-error');
    expect(error).toHaveTextContent(i18n.t('pages.auth.adminErasurePreviewError'));
    expect(error).toHaveAttribute('role', 'alert');
    // The deletion itself stays possible: the preview is information, not a gate.
    expect(within(dialog).getByTestId('confirm-delete-user-btn')).toBeInTheDocument();
  });

  it('shows a status while the preview loads', async () => {
    preview.mockReturnValue(new Promise(() => undefined));
    const dialog = await openDeleteDialog();

    expect(await within(dialog).findByTestId('delete-user-preview-loading')).toHaveAttribute('role', 'status');
  });

  it('is available in English', async () => {
    await i18n.changeLanguage('en');
    preview.mockResolvedValue({ personal_tenants: [{ name: 'Target Garden', other_member_count: 1 }] });
    const dialog = await openDeleteDialog();

    const line = await within(dialog).findByTestId('delete-user-preview-tenant');
    expect(line).toHaveTextContent(/1 other member is affected/);
    expect(await within(dialog).findByTestId('delete-user-preview-shared-hint')).toHaveTextContent(/no grace period/);
  });
});
