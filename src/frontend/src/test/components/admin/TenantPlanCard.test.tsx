import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import i18n from 'i18next';
import { ApiError } from '@/api/errors';
import type { AdminTenantDetail, Plan } from '@/api/types';
import TenantPlanCard from '@/components/admin/TenantPlanCard';
import { authState, createTestStore, renderWithProviders } from '@/test/helpers';

/**
 * REQ-056 §7.6/§7.7, §15 (AK-45) — plan selector and usage on the admin's tenant page. The plan is
 * assigned with `PATCH /admin/platform/tenants/{key}` (`plan_key`, no step-up); the platform tenant and
 * a tenant being erased take no plan (422 server-side) — the card says why instead of offering it.
 */

vi.mock('@/api/endpoints/adminPlatform', () => ({
  fetchAdminTenantDetail: vi.fn(),
  updateAdminTenant: vi.fn(),
}));
vi.mock('@/api/endpoints/adminPlans', () => ({
  listPlans: vi.fn(),
}));

const admin = await import('@/api/endpoints/adminPlatform');
const plans = await import('@/api/endpoints/adminPlans');
const fn = (f: unknown) => f as ReturnType<typeof vi.fn>;

const PLAN = (key: string, name: string, isDefault = false): Plan => ({
  key,
  name,
  description: null,
  limits: {},
  unlimited: [],
  is_default: isDefault,
  tenant_count: 1,
  created_at: null,
  updated_at: null,
});

function detail(over: Partial<AdminTenantDetail> = {}): AdminTenantDetail {
  return {
    key: 'garden-key',
    name: 'Gemeinschaftsgarten',
    slug: 'gemeinschaftsgarten',
    tenant_type: 'organization',
    description: null,
    owner_user_key: 'u-lead',
    is_active: true,
    status: 'active',
    is_platform: false,
    max_members: 50,
    member_count: 12,
    created_at: null,
    updated_at: null,
    plan_key: 'standard',
    entitlements: {
      plan: { key: 'standard', name: 'Standard' },
      limits: [
        { dimension: 'members', limit: 50, used: 12 },
        { dimension: 'service_accounts', limit: 20, used: 1 },
        { dimension: 'storage_mb', limit: null, used: 731 },
        { dimension: 'photos_per_instance', limit: 50, used: null },
        { dimension: 'ai_calls_per_user_day', limit: 50, used: 0 },
        { dimension: 'ai_tokens_per_tenant_day', limit: 2000000, used: 1900000 },
      ],
    },
    ...over,
  };
}

function render(props: Partial<Parameters<typeof TenantPlanCard>[0]> = {}) {
  const onAssigned = vi.fn();
  renderWithProviders(
    <TenantPlanCard tenantKey="garden-key" isPlatform={false} status="active" onAssigned={onAssigned} {...props} />,
    { store: createTestStore(authState({ platformAdmin: true })) },
  );
  return { onAssigned };
}

describe('TenantPlanCard (REQ-056 AK-45)', () => {
  beforeEach(async () => {
    vi.clearAllMocks();
    await i18n.changeLanguage('de');
    fn(plans.listPlans).mockResolvedValue([PLAN('standard', 'Standard', true), PLAN('community', 'Gemeinschaft')]);
  });

  it('shows every dimension with its usage, the lead-only ones included, and bars only where measurable', async () => {
    fn(admin.fetchAdminTenantDetail).mockResolvedValue(detail());
    render();
    expect(await screen.findByTestId('tenant-plan-usage-members-value')).toHaveTextContent('12 von 50 Mitglieder');
    expect(screen.getByTestId('tenant-plan-usage-service_accounts')).toBeInTheDocument();
    expect(screen.getByTestId('tenant-plan-usage-ai_tokens_per_tenant_day-bar')).toBeInTheDocument();
    expect(screen.getByTestId('tenant-plan-usage-storage_mb-value')).toHaveTextContent('731 MB – unbegrenzt');
    expect(screen.queryByTestId('tenant-plan-usage-storage_mb-bar')).toBeNull();
    expect(screen.getByTestId('tenant-plan-usage-photos_per_instance-value')).toHaveTextContent('je Pflanze gezählt');
    // The admin's own counter, labelled as such — never a member's.
    expect(screen.getByTestId('tenant-plan-usage-ai_calls_per_user_day')).toHaveTextContent('dein eigener');
  });

  it('assigns another plan with plan_key only and reloads the usage', async () => {
    fn(admin.fetchAdminTenantDetail).mockResolvedValue(detail());
    fn(admin.updateAdminTenant).mockResolvedValue({ ...detail(), plan_key: 'community' });
    const { onAssigned } = render();
    const select = await screen.findByRole('combobox', { name: /Plan/ });
    await waitFor(() => expect(select).toBeEnabled());
    expect(screen.getByTestId('tenant-plan-assign')).toBeDisabled();
    await userEvent.selectOptions(select, 'community');
    await userEvent.click(screen.getByTestId('tenant-plan-assign'));
    await waitFor(() => expect(admin.updateAdminTenant).toHaveBeenCalledWith('garden-key', { plan_key: 'community' }));
    expect(onAssigned).toHaveBeenCalled();
    await waitFor(() => expect(admin.fetchAdminTenantDetail).toHaveBeenCalledTimes(2));
  });

  it('offers no selector for the platform tenant and says it follows the instance settings', async () => {
    fn(admin.fetchAdminTenantDetail).mockResolvedValue(detail({ is_platform: true }));
    render({ isPlatform: true });
    expect(await screen.findByTestId('tenant-plan-platform')).toHaveTextContent('Instanz-Einstellungen');
    expect(screen.queryByTestId('tenant-plan-select')).toBeNull();
    expect(screen.getByTestId('tenant-plan-current')).toHaveTextContent('Standard');
    expect(plans.listPlans).not.toHaveBeenCalled();
  });

  it('offers no selector for a tenant being erased', async () => {
    fn(admin.fetchAdminTenantDetail).mockResolvedValue(detail({ status: 'deleted', is_active: false }));
    render({ status: 'deleted' });
    expect(await screen.findByTestId('tenant-plan-deleted')).toBeInTheDocument();
    expect(screen.queryByTestId('tenant-plan-select')).toBeNull();
  });

  it('says a failed read and retries, instead of showing no quotas', async () => {
    fn(admin.fetchAdminTenantDetail)
      .mockRejectedValueOnce(
        new ApiError(
          { error_id: 'e', error_code: 'INTERNAL_ERROR', message: 'x', details: [], timestamp: '', path: '/', method: 'GET' },
          500,
        ),
      )
      .mockResolvedValueOnce(detail());
    render();
    await userEvent.click(await screen.findByTestId('tenant-plan-retry'));
    expect(await screen.findByTestId('tenant-plan-usage-members')).toBeInTheDocument();
  });
});
