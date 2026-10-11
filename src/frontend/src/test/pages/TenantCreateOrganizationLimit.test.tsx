import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import i18n from 'i18next';
import { ApiError } from '@/api/errors';
import TenantCreatePage from '@/pages/tenants/TenantCreatePage';
import { renderWithProviders } from '@/test/helpers';

/**
 * REQ-056 §6.2 (#2142, AK-14/AK-15) — founding an organisation above `TENANT_MAX_ORGANIZATIONS_PER_USER`
 * answers `422 ORGANIZATION_LIMIT_REACHED`. The page used to show the backend's English message; the
 * thunk dropped the code, so nothing could translate it. It now reaches the page and is said in German.
 */

vi.mock('@/api/endpoints/tenants', async () => ({
  ...(await vi.importActual<typeof import('@/api/endpoints/tenants')>('@/api/endpoints/tenants')),
  createOrganization: vi.fn(),
  listMyTenants: vi.fn().mockResolvedValue([]),
}));

const api = await import('@/api/endpoints/tenants');

function refusal(code: string, message: string): ApiError {
  return new ApiError(
    {
      error_id: 'e',
      error_code: code,
      message,
      details: [{ field: 'tenant', reason: 'An account may own at most 2 organisations.', code }],
      timestamp: '',
      path: '/api/v1/tenants',
      method: 'POST',
    },
    422,
  );
}

describe('TenantCreatePage — organisation limit (REQ-056 §6.2)', () => {
  beforeEach(async () => {
    vi.clearAllMocks();
    await i18n.changeLanguage('de');
  });

  it('explains ORGANIZATION_LIMIT_REACHED in the reader’s language', async () => {
    (api.createOrganization as ReturnType<typeof vi.fn>).mockRejectedValue(
      refusal('ORGANIZATION_LIMIT_REACHED', 'Maximum number of organizations reached'),
    );
    renderWithProviders(<TenantCreatePage />);
    await userEvent.type(screen.getByRole('textbox', { name: /Name/ }), 'Kleingartenverein');
    await userEvent.click(screen.getByRole('button', { name: /Erstellen|Anlegen/ }));
    const error = await screen.findByTestId('tenant-create-error');
    expect(error).toHaveTextContent('Du kannst keine weitere Organisation gründen');
    expect(error).not.toHaveTextContent('Maximum number of organizations reached');
  });

  it('keeps showing other refusals as before', async () => {
    (api.createOrganization as ReturnType<typeof vi.fn>).mockRejectedValue(refusal('VALIDATION_ERROR', 'Name is taken'));
    renderWithProviders(<TenantCreatePage />);
    await userEvent.type(screen.getByRole('textbox', { name: /Name/ }), 'Kleingartenverein');
    await userEvent.click(screen.getByRole('button', { name: /Erstellen|Anlegen/ }));
    expect(await screen.findByTestId('tenant-create-error')).toHaveTextContent('Name is taken');
  });
});
