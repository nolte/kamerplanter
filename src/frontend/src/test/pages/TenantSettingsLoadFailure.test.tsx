import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { screen, cleanup, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import i18n from 'i18next';
import { ApiError } from '@/api/errors';
import type { Invitation, Membership } from '@/api/types';
import { createStoreWithTenantRole, renderWithProviders } from '@/test/helpers';

/**
 * #3013 (A-01) — members and open invitations are security-relevant lists: a member nobody
 * expects or a leaked invitation link must stay visible and revocable. A failed load therefore
 * renders an error with retry, never the "no members" / "no invitations" empty text.
 */

vi.mock('@/api/endpoints/tenants', () => ({
  listMyTenantsWithScheduledDeletion: vi.fn().mockResolvedValue([]),
  cancelTenantErasure: vi.fn(),
  listMembers: vi.fn().mockResolvedValue([]),
  listInvitations: vi.fn().mockResolvedValue([]),
  removeMember: vi.fn(),
  createEmailInvitation: vi.fn(),
  createLinkInvitation: vi.fn(),
  revokeInvitation: vi.fn(),
}));

const tenantApi = await import('@/api/endpoints/tenants');
const listMembers = tenantApi.listMembers as ReturnType<typeof vi.fn>;
const listInvitations = tenantApi.listInvitations as ReturnType<typeof vi.fn>;

const ENGLISH = 'An internal error occurred.';

function serverError(): ApiError {
  return new ApiError(
    { error_id: 'e', error_code: 'INTERNAL_ERROR', message: ENGLISH, details: [], timestamp: '', path: '', method: 'GET' },
    500,
  );
}

const MEMBER = {
  key: 'm-1',
  user_key: 'u-1',
  tenant_key: 't-1',
  role: 'viewer',
  admin_scopes: [],
  display_name: 'Unexpected Member',
  email: 'unexpected@example.org',
} as unknown as Membership;

const INVITATION = {
  key: 'i-1',
  email: 'leaked@example.org',
  role: 'viewer',
  status: 'pending',
  use_count: 0,
  max_uses: 5,
  expires_at: '2026-12-31T00:00:00Z',
  created_at: '2026-11-01T00:00:00Z',
} as unknown as Invitation;

async function renderPage(route: string) {
  const { default: Page } = await import('@/pages/tenants/TenantSettingsPage');
  renderWithProviders(<Page />, {
    store: createStoreWithTenantRole('lead', ['management']),
    route,
  });
}

describe('TenantSettingsPage — load failures (#3013)', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
    vi.clearAllMocks();
    listMembers.mockResolvedValue([]);
    listInvitations.mockResolvedValue([]);
  });
  afterEach(() => {
    cleanup();
  });

  it('a 500 on members shows an error with retry, not "no members"', async () => {
    listMembers.mockRejectedValueOnce(serverError()).mockResolvedValue([MEMBER]);
    await renderPage('/tenants/settings#members');

    const display = await screen.findByTestId('error-display');
    expect(display).toHaveTextContent(i18n.t('pages.tenants.membersLoadFailed'));
    expect(screen.queryByText(i18n.t('pages.tenants.noMembers'))).toBeNull();
    expect(screen.queryByText(ENGLISH)).toBeNull();

    await userEvent.click(within(display).getByTestId('error-retry-button'));
    expect((await screen.findAllByText('Unexpected Member')).length).toBeGreaterThan(0);
    expect(screen.queryByTestId('error-display')).toBeNull();
  });

  it('a 500 on invitations shows an error with retry, not "no invitations"', async () => {
    listInvitations.mockRejectedValueOnce(serverError()).mockResolvedValue([INVITATION]);
    await renderPage('/tenants/settings#invitations');

    const display = await screen.findByTestId('error-display');
    expect(display).toHaveTextContent(i18n.t('pages.tenants.invitationsLoadFailed'));
    expect(screen.queryByText(i18n.t('pages.tenants.noInvitations'))).toBeNull();
    expect(screen.queryByText(ENGLISH)).toBeNull();

    await userEvent.click(within(display).getByTestId('error-retry-button'));
    expect((await screen.findAllByText('leaked@example.org')).length).toBeGreaterThan(0);
    expect(screen.queryByTestId('error-display')).toBeNull();
  });
});
