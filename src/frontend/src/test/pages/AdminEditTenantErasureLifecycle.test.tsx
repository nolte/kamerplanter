import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { screen, waitFor, cleanup, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { createTestStore, renderWithProviders } from '@/test/helpers';

/**
 * #2123 (MT-027, REQ-024 AK-52) — a tenant deletion is scheduled, visible and cancellable.
 *
 * The admin panel shows the lifecycle state instead of the `is_active` bool: a tenant
 * whose deletion is scheduled (or that an account deletion orphaned, #2134) says when
 * it goes and offers the cancellation behind the admin's own step-up; the suspension
 * switch and the delete button are locked meanwhile. A scheduled deletion is announced
 * with its date, not as "being erased".
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
  cancelAdminTenantErasure: vi.fn(),
  addTenantMember: vi.fn(),
  removeTenantMember: vi.fn(),
  changeTenantMemberRole: vi.fn(),
}));

vi.mock('@/api/endpoints/auth', async () => ({
  ...(await vi.importActual<typeof import('@/api/endpoints/auth')>('@/api/endpoints/auth')),
  listProviders: vi.fn().mockResolvedValue([{ provider: 'local' }]),
}));

const admin = await import('@/api/endpoints/adminPlatform');

const BASE = {
  key: 'garden-key',
  name: 'Gemeinschaftsgarten',
  slug: 'gemeinschaftsgarten',
  tenant_type: 'organization',
  description: '',
  owner_user_key: 'u-1',
  is_platform: false,
  max_members: 50,
  member_count: 2,
  created_at: null,
  updated_at: null,
};
const PENDING = {
  ...BASE,
  is_active: false,
  status: 'pending_deletion',
  deletion_scheduled_at: '2027-01-03T09:00:00Z',
};

async function renderPage() {
  const { default: Page } = await import('@/pages/admin/AdminEditTenantPage');
  renderWithProviders(<Page />, { store: createTestStore() });
}

describe('AdminEditTenantPage — scheduled deletion (#2123)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });
  afterEach(() => cleanup());

  it('shows the scheduled state, locks switch and delete, and offers the cancellation', async () => {
    (admin.fetchAdminTenants as ReturnType<typeof vi.fn>).mockResolvedValue([PENDING]);
    await renderPage();

    const alert = await screen.findByTestId('edit-tenant-deletion-scheduled');
    expect(alert).toHaveTextContent(new Date(PENDING.deletion_scheduled_at).toLocaleDateString());
    expect(screen.getByTestId('edit-tenant-status-chip')).toHaveTextContent(/geplant|scheduled/i);
    expect(screen.getByTestId('delete-tenant-btn')).toBeDisabled();
    expect(screen.getByTestId('edit-tenant-active-switch').querySelector('input')).toBeDisabled();
    expect(within(alert).getByTestId('cancel-tenant-erasure-btn')).toBeEnabled();
  });

  it('cancels with the admin password and shows the tenant active again', async () => {
    (admin.fetchAdminTenants as ReturnType<typeof vi.fn>).mockResolvedValue([PENDING]);
    (admin.cancelAdminTenantErasure as ReturnType<typeof vi.fn>).mockResolvedValue({
      ...BASE,
      is_active: true,
      status: 'active',
      deletion_scheduled_at: null,
    });
    await renderPage();

    await userEvent.click(await screen.findByTestId('cancel-tenant-erasure-btn'));
    const dialog = await screen.findByTestId('cancel-tenant-erasure-dialog');
    await userEvent.type(within(dialog).getByLabelText(/passwort|password/i), 'admin-password');
    await userEvent.click(within(dialog).getByTestId('cancel-tenant-erasure-confirm'));

    await waitFor(() =>
      expect(admin.cancelAdminTenantErasure).toHaveBeenCalledWith('garden-key', { current_password: 'admin-password' }),
    );
    await waitFor(() => expect(screen.queryByTestId('edit-tenant-deletion-scheduled')).not.toBeInTheDocument());
    expect(screen.getByTestId('delete-tenant-btn')).toBeEnabled();
  });

  it('names an orphaned organization as such and offers no cancellation (#2134)', async () => {
    (admin.fetchAdminTenants as ReturnType<typeof vi.fn>).mockResolvedValue([{ ...PENDING, status: 'orphaned' }]);
    await renderPage();

    expect(await screen.findByTestId('edit-tenant-deletion-scheduled')).toHaveTextContent(/verwaist|orphaned/i);
    expect(screen.getByTestId('edit-tenant-status-chip')).toHaveTextContent(/verwaist|orphaned/i);
    expect(screen.queryByTestId('cancel-tenant-erasure-btn')).not.toBeInTheDocument();
    expect(screen.getByTestId('delete-tenant-btn')).toBeDisabled();
  });

  it('offers no cancellation once the erasure runs', async () => {
    (admin.fetchAdminTenants as ReturnType<typeof vi.fn>).mockResolvedValue([{ ...PENDING, status: 'deleted' }]);
    await renderPage();

    expect(await screen.findByTestId('edit-tenant-being-erased')).toBeInTheDocument();
    expect(screen.queryByTestId('cancel-tenant-erasure-btn')).not.toBeInTheDocument();
    expect(screen.getByTestId('delete-tenant-btn')).toBeDisabled();
  });

  it('falls back to the bool for a response without a status', async () => {
    (admin.fetchAdminTenants as ReturnType<typeof vi.fn>).mockResolvedValue([{ ...BASE, is_active: true }]);
    await renderPage();

    expect(await screen.findByTestId('edit-tenant-status-chip')).toHaveTextContent(/aktiv|active/i);
    expect(screen.queryByTestId('edit-tenant-deletion-scheduled')).not.toBeInTheDocument();
  });
});
