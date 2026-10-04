import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { screen, waitFor, cleanup, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import i18n from 'i18next';
import { ApiError } from '@/api/errors';
import type { ApiErrorResponse, Membership } from '@/api/types';
import { createStoreWithTenantRole, renderWithProviders } from '@/test/helpers';

/**
 * #2032 — a tenant's member administrator removing a member proves it is really them.
 *
 * `DELETE /tenants/{slug}/members/{membershipKey}` removed a member — also the last
 * lead — on nothing but the session. The backend now asks for the **acting
 * administrator's own** step-up (`current_password`, or `step_up_token` /
 * `step_up_code` without one), bound to the membership (#1884, act
 * `tenant_member_removal`). The trash button only opens the shared
 * `StepUpConfirmDialog`.
 */

vi.mock('@/api/endpoints/tenants', () => ({
  listMembers: vi.fn(),
  listInvitations: vi.fn().mockResolvedValue([]),
  removeMember: vi.fn(),
  createEmailInvitation: vi.fn(),
  createLinkInvitation: vi.fn(),
  revokeInvitation: vi.fn(),
}));

vi.mock('@/api/endpoints/auth', async () => ({
  ...(await vi.importActual<typeof import('@/api/endpoints/auth')>('@/api/endpoints/auth')),
  listProviders: vi.fn(),
  requestStepUpCode: vi.fn().mockResolvedValue({ expires_at: '2026-10-04T12:10:00Z', expires_in: 600 }),
}));

const tenantApi = await import('@/api/endpoints/tenants');
const auth = await import('@/api/endpoints/auth');

// Credential-shaped values are assembled at runtime (GitGuardian, #1838).
const PASSWORD = ['member', 'Admin', 'pw', '1'].join('-');

const LEAD: Membership = {
  key: 'm-lead',
  user_key: 'u-lead',
  tenant_key: 'tenant-1',
  role: 'lead',
  admin_scopes: [],
  display_name: 'Lena Lead',
  email: 'lena@example.org',
  joined_at: null,
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

async function openRemovalDialog(scopes: readonly string[] = ['management']) {
  const { default: Page } = await import('@/pages/tenants/TenantSettingsPage');
  renderWithProviders(<Page />, { store: createStoreWithTenantRole('viewer', scopes) });
  const buttons = await screen.findAllByTestId('remove-member-m-lead');
  await userEvent.click(buttons[0]);
  return screen.findByTestId('remove-tenant-member-dialog');
}

describe('TenantSettingsPage — member removal step-up (#2032)', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
    vi.clearAllMocks();
    sessionStorage.clear();
    (tenantApi.listMembers as ReturnType<typeof vi.fn>).mockResolvedValue([LEAD]);
    (tenantApi.listInvitations as ReturnType<typeof vi.fn>).mockResolvedValue([]);
    (tenantApi.removeMember as ReturnType<typeof vi.fn>).mockResolvedValue(undefined);
    (auth.listProviders as ReturnType<typeof vi.fn>).mockResolvedValue([{ provider: 'local' }]);
  });
  afterEach(() => {
    cleanup();
    sessionStorage.clear();
  });

  it("removes the member only with the acting administrator's own password", async () => {
    const dialog = await openRemovalDialog();
    // Nothing is removed before the step-up, and there is no echo to type back.
    expect(tenantApi.removeMember).not.toHaveBeenCalled();
    expect(dialog).toHaveTextContent('Lena Lead');
    expect(within(dialog).queryByTestId('remove-tenant-member-echo')).toBeNull();

    await userEvent.type(
      within(dialog).getByTestId('remove-tenant-member-password').querySelector('input') as HTMLInputElement,
      PASSWORD,
    );
    await userEvent.click(within(dialog).getByTestId('remove-tenant-member-confirm'));

    await waitFor(() =>
      expect(tenantApi.removeMember).toHaveBeenCalledWith('testgarten', 'm-lead', { current_password: PASSWORD }),
    );
    await waitFor(() => expect(screen.queryByTestId('remove-tenant-member-dialog')).toBeNull());
  });

  it('keeps the member when the dialog is cancelled', async () => {
    const dialog = await openRemovalDialog();

    await userEvent.click(within(dialog).getByTestId('remove-tenant-member-cancel'));

    await waitFor(() => expect(screen.queryByTestId('remove-tenant-member-dialog')).toBeNull());
    expect(tenantApi.removeMember).not.toHaveBeenCalled();
  });

  it('keeps the dialog open and says why when the step-up is refused', async () => {
    (tenantApi.removeMember as ReturnType<typeof vi.fn>).mockRejectedValue(
      apiError(401, { error_code: 'UNAUTHORIZED', message: 'Password confirmation failed.' }),
    );
    const dialog = await openRemovalDialog();

    await userEvent.type(
      within(dialog).getByTestId('remove-tenant-member-password').querySelector('input') as HTMLInputElement,
      'wrong',
    );
    await userEvent.click(within(dialog).getByTestId('remove-tenant-member-confirm'));

    expect(await within(dialog).findByTestId('remove-tenant-member-error')).toHaveTextContent(
      'Password confirmation failed.',
    );
  });

  it('asks a federated administrator for a code bound to the membership', async () => {
    (auth.listProviders as ReturnType<typeof vi.fn>).mockResolvedValue([{ provider: 'github' }]);
    const dialog = await openRemovalDialog();

    await userEvent.click(await within(dialog).findByTestId('remove-tenant-member-send-code'));

    await waitFor(() => expect(auth.requestStepUpCode).toHaveBeenCalledWith('tenant_member_removal', 'm-lead'));
  });

  it('offers no removal to a member without the management scope', async () => {
    const { default: Page } = await import('@/pages/tenants/TenantSettingsPage');
    renderWithProviders(<Page />, { store: createStoreWithTenantRole('viewer', []) });

    await screen.findByText('Lena Lead');

    expect(screen.queryByTestId('remove-member-m-lead')).toBeNull();
  });
});
