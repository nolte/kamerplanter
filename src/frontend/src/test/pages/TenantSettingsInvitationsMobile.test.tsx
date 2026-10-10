import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { screen, within, cleanup, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import i18n from 'i18next';
import type { Invitation } from '@/api/types';
import { createStoreWithTenantRole, renderWithProviders } from '@/test/helpers';

/**
 * #2182 review SCR-001 — below `sm` the invitation list is a list of cards, not a five-column
 * table that scrolls sideways. Type, role and status are keyed chips, the uses are the subtitle,
 * and the revoke control keeps its `revoke-invitation-<key>` hook as the card's trailing action.
 */

// Force the mobile breakpoint so DataTable takes the mobileCardRenderer branch.
vi.mock('@mui/material/useMediaQuery', () => ({ default: () => true }));

vi.mock('@/api/endpoints/tenants', () => ({
  listMyTenantsWithScheduledDeletion: vi.fn().mockResolvedValue([]),
  cancelTenantErasure: vi.fn(),
  listMembers: vi.fn().mockResolvedValue([]),
  listInvitations: vi.fn().mockResolvedValue([]),
  removeMember: vi.fn(),
  createEmailInvitation: vi.fn(),
  createLinkInvitation: vi.fn(),
  revokeInvitation: vi.fn().mockResolvedValue(undefined),
}));

const tenantApi = await import('@/api/endpoints/tenants');

function invitation(overrides: Partial<Invitation>): Invitation {
  return {
    key: 'i-link',
    tenant_key: 't1',
    email: null,
    role: 'viewer',
    invitation_type: 'link',
    status: 'pending',
    created_by: 'u-lead',
    expires_at: '2026-10-17T00:00:00Z',
    created_at: null,
    max_uses: 20,
    use_count: 3,
    ...overrides,
  };
}

async function renderInvitationCards() {
  const { default: Page } = await import('@/pages/tenants/TenantSettingsPage');
  renderWithProviders(<Page />, {
    store: createStoreWithTenantRole('lead', ['management']),
    route: '/tenants/settings#invitations',
  });
  await screen.findByTestId('invite-email-field');
  return screen.findByTestId('data-table-cards');
}

describe('TenantSettingsPage — invitations as cards on a phone (#2182 review SCR-001)', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
    vi.clearAllMocks();
    (tenantApi.listMembers as ReturnType<typeof vi.fn>).mockResolvedValue([]);
    (tenantApi.listInvitations as ReturnType<typeof vi.fn>).mockResolvedValue([
      invitation({}),
      invitation({
        key: 'i-mail',
        email: 'friend@example.org',
        invitation_type: 'email',
        role: 'grower',
        status: 'accepted',
        max_uses: 1,
        use_count: 1,
      }),
    ]);
  });
  afterEach(() => {
    cleanup();
  });

  it('renders one card per invitation with type, role and status chips and the uses as subtitle', async () => {
    const cards = await renderInvitationCards();

    await waitFor(() => expect(within(cards).getAllByTestId('card-title')).toHaveLength(2));
    expect(screen.queryByRole('table')).toBeNull();

    const [linkCard, mailCard] = within(cards).getAllByTestId('card-title').map((title) => title.closest('.MuiCard-root') as HTMLElement);
    expect(within(linkCard).getByTestId('card-title')).toHaveTextContent('Einladungslink');
    expect(within(linkCard).getByTestId('card-chip-invitation_type')).toHaveTextContent('Link');
    expect(within(linkCard).getByTestId('card-chip-role')).toHaveTextContent('Betrachter');
    expect(within(linkCard).getByTestId('card-chip-status')).toHaveAttribute('data-chip-color', 'warning');
    expect(within(linkCard).getByTestId('card-field-uses')).toHaveTextContent('Genutzt: 3 von 20');
    expect(within(linkCard).getByTestId('invitation-uses-i-link')).toBeInTheDocument();

    expect(within(mailCard).getByTestId('card-title')).toHaveTextContent('friend@example.org');
    expect(within(mailCard).getByTestId('card-field-uses')).toHaveTextContent('Genutzt: 1 von 1');
  });

  it('offers the revoke control only on a pending invitation and keeps its test hook', async () => {
    await renderInvitationCards();

    const revoke = await screen.findByTestId('revoke-invitation-i-link');
    expect(revoke).toHaveAccessibleName('Einladung widerrufen');
    expect(screen.queryByTestId('revoke-invitation-i-mail')).toBeNull();

    await userEvent.click(revoke);

    await waitFor(() => expect(tenantApi.revokeInvitation).toHaveBeenCalledWith('testgarten', 'i-link'));
  });
});
