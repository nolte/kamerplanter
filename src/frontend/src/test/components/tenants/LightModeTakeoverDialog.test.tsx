import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import i18n from 'i18next';
import type { TakeoverStatus, TenantWithRole } from '@/api/types';
import LightModeTakeoverDialog from '@/components/tenants/LightModeTakeoverDialog';
import { authState, createTestStore, renderWithProviders } from '@/test/helpers';

/**
 * REQ-027 Szenario 5/6 (#1855) — after the switch from light to full mode the platform admin (or the
 * first account) is asked whether the light-mode garden becomes theirs. Accepting switches to it,
 * declining keeps it, "later" only closes the dialog.
 */

vi.mock('@/api/endpoints/system', () => ({
  getTakeoverStatus: vi.fn(),
  decideTakeover: vi.fn(),
}));
vi.mock('@/api/endpoints/auth', async () => ({
  ...(await vi.importActual<typeof import('@/api/endpoints/auth')>('@/api/endpoints/auth')),
  getProfile: vi.fn(),
}));
vi.mock('@/api/endpoints/tenants', async () => ({
  ...(await vi.importActual<typeof import('@/api/endpoints/tenants')>('@/api/endpoints/tenants')),
  listMyTenants: vi.fn(),
}));

const systemApi = await import('@/api/endpoints/system');
const authApi = await import('@/api/endpoints/auth');
const tenantApi = await import('@/api/endpoints/tenants');
const getStatus = systemApi.getTakeoverStatus as ReturnType<typeof vi.fn>;
const decide = systemApi.decideTakeover as ReturnType<typeof vi.fn>;

const OPEN: TakeoverStatus = {
  pending: true,
  eligible: true,
  tenant_name: 'Mein Garten',
  tenant_slug: 'mein-garten',
  resource_counts: { plants: 30, sites: 3, planting_runs: 0, nutrient_plans: 1, tasks: 0 },
};

const TAKEN_OVER = {
  key: 'system-tenant',
  name: 'Tester',
  slug: 'mein-garten',
  tenant_type: 'personal',
  role: 'lead',
  admin_scopes: ['management', 'technical'],
  is_active: true,
} as unknown as TenantWithRole;

const PROFILE = {
  key: 'user-1',
  display_name: 'Tester',
  email: 'tester@example.org',
  locale: 'de',
  timezone: 'Europe/Berlin',
  is_platform_admin: true,
};

function renderDialog() {
  const store = createTestStore(authState());
  renderWithProviders(<LightModeTakeoverDialog />, { store });
  return store;
}

describe('LightModeTakeoverDialog (REQ-027 §7a, #1855)', () => {
  beforeEach(async () => {
    getStatus.mockReset();
    decide.mockReset();
    (authApi.getProfile as ReturnType<typeof vi.fn>).mockResolvedValue(PROFILE);
    (tenantApi.listMyTenants as ReturnType<typeof vi.fn>).mockResolvedValue([TAKEN_OVER]);
    await i18n.changeLanguage('de');
  });

  it('lists what the light-mode garden holds, leaving out empty counts', async () => {
    getStatus.mockResolvedValue(OPEN);
    renderDialog();

    expect(await screen.findByTestId('light-mode-takeover-dialog')).toHaveTextContent('Mein Garten');
    expect(screen.getByTestId('light-mode-takeover-count-plants')).toHaveTextContent('30 Pflanzen');
    expect(screen.getByTestId('light-mode-takeover-count-sites')).toHaveTextContent('3 Standorte');
    expect(screen.getByTestId('light-mode-takeover-count-nutrient_plans')).toHaveTextContent('1 eigener Nährstoffplan');
    expect(screen.queryByTestId('light-mode-takeover-count-tasks')).toBeNull();
  });

  it('accepts, switches to the taken-over garden and closes', async () => {
    getStatus.mockResolvedValue(OPEN);
    decide.mockResolvedValue({ accepted: true, tenant_slug: 'mein-garten', platform_admin_granted: true });
    const store = renderDialog();

    await userEvent.click(await screen.findByTestId('light-mode-takeover-accept'));

    expect(decide).toHaveBeenCalledWith(true);
    await waitFor(() => expect(screen.queryByTestId('light-mode-takeover-dialog')).toBeNull());
    expect(store.getState().tenants.activeTenant?.slug).toBe('mein-garten');
  });

  it('declines without switching the garden', async () => {
    getStatus.mockResolvedValue(OPEN);
    decide.mockResolvedValue({ accepted: false, tenant_slug: null, platform_admin_granted: true });
    renderDialog();

    await userEvent.click(await screen.findByTestId('light-mode-takeover-decline'));

    expect(decide).toHaveBeenCalledWith(false);
    await waitFor(() => expect(screen.queryByTestId('light-mode-takeover-dialog')).toBeNull());
    expect(tenantApi.listMyTenants).not.toHaveBeenCalled();
  });

  it('keeps the dialog open with the error when the decision fails', async () => {
    getStatus.mockResolvedValue(OPEN);
    decide.mockRejectedValue(new Error('Only the platform administrator or the first account can decide.'));
    renderDialog();

    await userEvent.click(await screen.findByTestId('light-mode-takeover-accept'));

    expect(await screen.findByTestId('light-mode-takeover-error')).toBeInTheDocument();
    expect(screen.getByTestId('light-mode-takeover-dialog')).toBeInTheDocument();
  });

  it('"later" only closes the dialog and decides nothing', async () => {
    getStatus.mockResolvedValue(OPEN);
    renderDialog();

    await userEvent.click(await screen.findByTestId('light-mode-takeover-later'));

    await waitFor(() => expect(screen.queryByTestId('light-mode-takeover-dialog')).toBeNull());
    expect(decide).not.toHaveBeenCalled();
  });

  it('shows nothing to an account that may not decide, or when nothing is open', async () => {
    getStatus.mockResolvedValueOnce({ ...OPEN, eligible: false, tenant_name: null, resource_counts: null });
    renderDialog();
    await waitFor(() => expect(getStatus).toHaveBeenCalled());
    expect(screen.queryByTestId('light-mode-takeover-dialog')).toBeNull();
  });
});
