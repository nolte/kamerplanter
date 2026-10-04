/**
 * Axe pass for the OIDC provider admin page and its dialogs (#1906, #1094).
 *
 * Scanned in the states a user reaches: the populated list, the create form, the edit form,
 * the step-up confirmation over the form and the discovery-test result. Dialogs render into a
 * portal, so the container is `document.body` and the element floor is what stops a scan of an
 * empty portal from counting.
 */

import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, beforeEach, vi } from 'vitest';
import i18n from 'i18next';
import type { OidcProvider } from '@/api/types';
import AdminOidcProvidersPage from '@/pages/admin/AdminOidcProvidersPage';
import { createTestStore, authState, renderWithProviders } from '@/test/helpers';
import { expectNoA11yViolations } from './expectNoA11yViolations';

vi.mock('@/api/endpoints/adminOidcProviders', () => ({
  listOidcProviders: vi.fn(),
  createOidcProvider: vi.fn(),
  updateOidcProvider: vi.fn(),
  deleteOidcProvider: vi.fn(),
  testOidcProvider: vi.fn(),
}));
vi.mock('@/api/endpoints/auth', async () => ({
  ...(await vi.importActual<typeof import('@/api/endpoints/auth')>('@/api/endpoints/auth')),
  listProviders: vi.fn().mockResolvedValue([{ provider: 'local' }]),
}));

const api = await import('@/api/endpoints/adminOidcProviders');
const fn = (f: unknown) => f as ReturnType<typeof vi.fn>;

const KC: OidcProvider = {
  key: 'p-kc',
  slug: 'keycloak',
  display_name: 'Keycloak Zuhause',
  provider_type: 'oidc',
  issuer_url: 'https://id.example/realms/home',
  client_id: 'kamerplanter',
  scopes: ['openid', 'email', 'profile'],
  enabled: true,
  icon_url: null,
  auto_discover: true,
  discovery_refreshed_at: null,
  created_at: null,
  updated_at: null,
};

async function renderPage() {
  fn(api.listOidcProviders).mockResolvedValue([KC]);
  fn(api.testOidcProvider).mockResolvedValue({
    message: 'ok',
    scope_check: { ok: true, provider_type: 'oidc', configured_scopes: [], missing_scopes: [], detail: '' },
    provider_type_check: { ok: true, provider_type: 'oidc', known_provider_types: [], detail: '' },
    jwks_check: { ok: true, applicable: true, jwks_url: null, key_count: 1, skipped_key_count: 0, key_ids: [], detail: '' },
    issuer_check: {
      ok: false,
      applicable: true,
      configured_issuer: 'a',
      accepted_issuers: [],
      discovery_issuer: 'b',
      detail: 'set b',
    },
  });
  renderWithProviders(<AdminOidcProvidersPage />, { store: createTestStore(authState({ platformAdmin: true })) });
  await screen.findByTestId('oidc-provider-p-kc');
}

describe('OIDC provider admin page a11y', () => {
  beforeEach(() => i18n.changeLanguage('de'));

  it('the populated list has no critical axe violations', async () => {
    await renderPage();
    await expectNoA11yViolations(document.body, { minElements: 40 });
  });

  it('the create form has no critical axe violations', async () => {
    await renderPage();
    await userEvent.click(screen.getByTestId('oidc-add'));
    await screen.findByTestId('oidc-form-dialog');
    await expectNoA11yViolations(document.body, { minElements: 60 });
  });

  it('the edit form with its step-up hint has no critical axe violations', async () => {
    await renderPage();
    await userEvent.click(screen.getByTestId('oidc-edit-p-kc'));
    await screen.findByTestId('oidc-form-dialog');
    await userEvent.click(screen.getByTestId('oidc-form-enabled').querySelector('input') as HTMLInputElement);
    await screen.findByTestId('oidc-form-step-up-hint');
    await expectNoA11yViolations(document.body, { minElements: 60 });
  });

  it('the step-up confirmation over the form has no critical axe violations', async () => {
    await renderPage();
    await userEvent.click(screen.getByTestId('oidc-delete-p-kc'));
    await screen.findByTestId('oidc-provider-delete-dialog');
    await expectNoA11yViolations(document.body, { minElements: 40 });
  });

  it('the test result dialog has no critical axe violations', async () => {
    await renderPage();
    await userEvent.click(screen.getByTestId('oidc-test-p-kc'));
    await screen.findByTestId('oidc-test-result');
    await expectNoA11yViolations(document.body, { minElements: 40 });
  });
});
