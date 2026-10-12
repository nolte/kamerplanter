import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { cleanup, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import i18n from 'i18next';
import TenantSettingsPage from '@/pages/tenants/TenantSettingsPage';
import { createStoreWithTenantRole, renderWithProviders } from '@/test/helpers';

/**
 * REQ-056 §8.2, §15 (#2138) — the garden settings offer the section "Export garden" to a lead
 * holding the `management` scope only, and only in full mode: the export routes are mounted in
 * full mode alone, and the backend refuses everybody else with 403. A grower with the scope and a
 * lead without it see no export tab.
 */

const mode = vi.hoisted(() => ({ light: false }));

vi.mock('@/config/mode', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/config/mode')>();
  return {
    ...actual,
    get isLightMode() {
      return mode.light;
    },
  };
});

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
  listTenantExports: vi.fn(),
  requestTenantExport: vi.fn(),
  downloadTenantExport: vi.fn(),
}));

const tenantApi = await import('@/api/endpoints/tenants');
const listExports = tenantApi.listTenantExports as ReturnType<typeof vi.fn>;

describe('TenantSettingsPage — export tab (REQ-056 §15, #2138)', () => {
  beforeEach(async () => {
    vi.clearAllMocks();
    mode.light = false;
    await i18n.changeLanguage('de');
    listExports.mockResolvedValue([]);
  });
  afterEach(() => {
    cleanup();
    mode.light = false;
  });

  it('offers a lead with management the export tab and loads the exports only when it is opened', async () => {
    renderWithProviders(<TenantSettingsPage />, {
      store: createStoreWithTenantRole('lead', ['management']),
    });
    const tab = await screen.findByTestId('tenant-tab-export');
    expect(tab).toHaveTextContent('Export');
    expect(listExports).not.toHaveBeenCalled();

    await userEvent.click(tab);

    expect(await screen.findByTestId('tenant-export-card')).toBeInTheDocument();
    expect(listExports).toHaveBeenCalledWith('testgarten');
  });

  it.each([
    ['a grower with management', 'grower', ['management']],
    ['a lead without management', 'lead', []],
    ['a viewer', 'viewer', []],
  ] as const)('hides the export tab from %s', async (_label, role, scopes) => {
    renderWithProviders(<TenantSettingsPage />, { store: createStoreWithTenantRole(role, scopes) });

    expect(await screen.findByTestId('tenant-tab-quota')).toBeInTheDocument();
    expect(screen.queryByTestId('tenant-tab-export')).toBeNull();
    expect(listExports).not.toHaveBeenCalled();
  });

  it('hides the export tab in light mode, where the routes do not exist', async () => {
    mode.light = true;
    renderWithProviders(<TenantSettingsPage />, {
      store: createStoreWithTenantRole('lead', ['management']),
    });

    expect(await screen.findByTestId('tenant-tab-quota')).toBeInTheDocument();
    expect(screen.queryByTestId('tenant-tab-export')).toBeNull();
  });
});
