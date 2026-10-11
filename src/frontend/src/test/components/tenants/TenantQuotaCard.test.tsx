import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import i18n from 'i18next';
import type { TenantEntitlements } from '@/api/types';
import TenantQuotaCard from '@/components/tenants/TenantQuotaCard';
import { createStoreWithTenantRole, renderWithProviders } from '@/test/helpers';

/**
 * REQ-056 §7.7 / §15 (AK-45) — the quota card in the garden settings, shown to every member. The
 * backend leaves out `service_accounts` and `ai_tokens_per_tenant_day` for a member who is not a lead
 * and counts `ai_calls_per_user_day` for the reader only; the card renders what comes and labels the
 * per-account counter as the reader's own.
 */

vi.mock('@/api/endpoints/tenants', () => ({
  getTenantEntitlements: vi.fn(),
}));

const api = await import('@/api/endpoints/tenants');
const getEntitlements = api.getTenantEntitlements as ReturnType<typeof vi.fn>;

const MEMBER_VIEW: TenantEntitlements = {
  plan: { key: 'standard', name: 'Standard' },
  limits: [
    { dimension: 'members', limit: 50, used: 12 },
    { dimension: 'storage_mb', limit: 2048, used: 2048 },
    { dimension: 'photos_per_instance', limit: 50, used: null },
    { dimension: 'ai_calls_per_user_day', limit: 50, used: 3 },
    { dimension: 'ai_calls_per_tenant_day', limit: 500, used: 41 },
  ],
};

describe('TenantQuotaCard (REQ-056 AK-45)', () => {
  beforeEach(async () => {
    getEntitlements.mockReset();
    await i18n.changeLanguage('de');
  });

  it('shows a member the plan and the rows the backend lists, with the own AI counter', async () => {
    getEntitlements.mockResolvedValue(MEMBER_VIEW);
    renderWithProviders(<TenantQuotaCard slug="mein-garten" isLead={false} />, {
      store: createStoreWithTenantRole('grower'),
    });
    expect(await screen.findByTestId('tenant-quota-plan')).toHaveTextContent('Plan: Standard');
    expect(getEntitlements).toHaveBeenCalledWith('mein-garten');
    expect(screen.getByTestId('tenant-quota-ai_calls_per_user_day')).toHaveTextContent('Deine KI-Aufrufe heute');
    expect(screen.getByTestId('tenant-quota-ai_calls_per_user_day-value')).toHaveTextContent('3 von 50');
    expect(screen.queryByTestId('tenant-quota-service_accounts')).toBeNull();
    expect(screen.queryByTestId('tenant-quota-ai_tokens_per_tenant_day')).toBeNull();
    expect(screen.getByTestId('tenant-quota-card')).toHaveTextContent('sieht nur die Leitung');
  });

  it('marks a used-up quota and exposes the bar to assistive technology', async () => {
    getEntitlements.mockResolvedValue(MEMBER_VIEW);
    renderWithProviders(<TenantQuotaCard slug="mein-garten" isLead />, { store: createStoreWithTenantRole('lead') });
    const bar = await screen.findByTestId('tenant-quota-storage_mb-bar');
    expect(bar).toHaveAttribute('aria-valuenow', '100');
    expect(bar).toHaveAttribute('aria-valuetext', '2.048 von 2.048 MB');
    expect(screen.getByRole('progressbar', { name: 'Mitglieder' })).toHaveAttribute('aria-valuenow', '24');
  });

  it('says a failed read and offers a retry', async () => {
    getEntitlements.mockRejectedValueOnce(new Error('offline')).mockResolvedValueOnce(MEMBER_VIEW);
    renderWithProviders(<TenantQuotaCard slug="mein-garten" isLead />, { store: createStoreWithTenantRole('lead') });
    expect(await screen.findByTestId('tenant-quota-error')).toBeInTheDocument();
    await userEvent.click(screen.getByTestId('tenant-quota-retry'));
    expect(await screen.findByTestId('tenant-quota-members')).toBeInTheDocument();
  });
});
