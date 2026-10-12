import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import i18n from 'i18next';
import TenantSettingsPage from '@/pages/tenants/TenantSettingsPage';
import { createStoreWithTenantRole, renderWithProviders } from '@/test/helpers';

/**
 * REQ-056 §15 (AK-45) — the garden settings show every member the quota tab, not only those with the
 * `management` scope that see the invitations tab: reading the plan and the usage is open to all
 * members (REQ-024 §1a). The tab asks for the active garden's entitlements only once it is opened.
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
  getTenantEntitlements: vi.fn(),
  listTenantExports: vi.fn().mockResolvedValue([]),
}));

const tenantApi = await import('@/api/endpoints/tenants');
const getEntitlements = tenantApi.getTenantEntitlements as ReturnType<typeof vi.fn>;

describe('TenantSettingsPage — quota tab (REQ-056 AK-45)', () => {
  beforeEach(async () => {
    vi.clearAllMocks();
    await i18n.changeLanguage('de');
    getEntitlements.mockResolvedValue({
      plan: { key: 'standard', name: 'Standard' },
      limits: [{ dimension: 'members', limit: 50, used: 3 }],
    });
  });

  it('offers a viewer the quota tab and loads the active garden only when it is opened', async () => {
    renderWithProviders(<TenantSettingsPage />, { store: createStoreWithTenantRole('viewer') });
    const tab = await screen.findByTestId('tenant-tab-quota');
    expect(screen.queryByRole('tab', { name: 'Einladungen' })).toBeNull();
    expect(getEntitlements).not.toHaveBeenCalled();

    await userEvent.click(tab);
    expect(await screen.findByTestId('tenant-quota-card')).toBeInTheDocument();
    expect(getEntitlements).toHaveBeenCalledWith('testgarten');
    expect(screen.getByTestId('tenant-quota-members-value')).toHaveTextContent('3 von 50 Mitglieder');
  });

  it('keeps the invitations tab for management and adds the quota tab after it (export last, #2138)', async () => {
    renderWithProviders(<TenantSettingsPage />, { store: createStoreWithTenantRole('lead', ['management']) });
    const tabs = await screen.findAllByRole('tab');
    expect(tabs.map((t) => t.textContent)).toEqual(['Mitglieder', 'Einladungen', 'Kontingente', 'Export']);
    await userEvent.click(screen.getByRole('tab', { name: 'Einladungen' }));
    expect(screen.queryByTestId('tenant-quota-card')).toBeNull();
    await userEvent.click(screen.getByRole('tab', { name: 'Kontingente' }));
    expect(await screen.findByTestId('tenant-quota-card')).toHaveTextContent('Den Plan legt der Betreiber');
  });
});
