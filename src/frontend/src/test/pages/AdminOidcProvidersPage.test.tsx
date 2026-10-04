import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { screen, waitFor, cleanup, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import i18n from 'i18next';
import { ApiError } from '@/api/errors';
import type { ApiErrorResponse, OidcProvider, OidcProviderTestResult } from '@/api/types';
import { createTestStore, authState, renderWithProviders } from '@/test/helpers';
import { readStepUpResume, saveStepUpResume, storePendingStepUpToken } from '@/utils/stepUpReauth';

/**
 * #1906 — the OIDC provider admin page: list, create, edit, delete and discovery test over
 * `/api/v1/admin/oidc-providers`, with every write that can steer a sign-in behind the admin's
 * own step-up for `oidc_provider_change` (#1883): bound to the configuration's key, or to
 * `new:<slug>` on create (#1884). Only `display_name` / `icon_url` save without one.
 */

vi.mock('@/api/endpoints/adminOidcProviders', () => ({
  listOidcProviders: vi.fn(),
  createOidcProvider: vi.fn(),
  updateOidcProvider: vi.fn(),
  deleteOidcProvider: vi.fn(),
  testOidcProvider: vi.fn(),
}));

vi.mock('@/api/endpoints/auth', async () => ({
  ...(await vi.importActual<typeof import('@/api/endpoints/auth')>('@/api/endpoints/auth')),
  listProviders: vi.fn(),
  requestStepUpCode: vi.fn().mockResolvedValue({ expires_at: '2026-10-04T12:10:00Z', expires_in: 600 }),
}));

const api = await import('@/api/endpoints/adminOidcProviders');
const auth = await import('@/api/endpoints/auth');
const fn = (f: unknown) => f as ReturnType<typeof vi.fn>;

// Credential-shaped values are assembled at runtime (GitGuardian, #1838).
const ADMIN_PASSWORD = ['admin', 'Secr', '3t'].join('-');
const SECRET_LEAK = ['leaky', 'client', 'Secr', '3t'].join('-');
const NEW_SECRET = ['new', 'client', 'Secr', '3t'].join('-');

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
  discovery_refreshed_at: '2026-10-01T08:00:00Z',
  created_at: null,
  updated_at: null,
};

function apiError(status: number, body: Partial<ApiErrorResponse> = {}): ApiError {
  return new ApiError(
    {
      error_id: 'err',
      error_code: 'X',
      message: 'x',
      details: [],
      timestamp: '',
      path: '/x',
      method: 'GET',
      ...body,
    } as ApiErrorResponse,
    status,
  );
}

const TEST_OK: OidcProviderTestResult = {
  message: "OIDC discovery for 'keycloak' validated successfully.",
  scope_check: { ok: true, provider_type: 'oidc', configured_scopes: ['openid'], missing_scopes: [], detail: '' },
  provider_type_check: { ok: true, provider_type: 'oidc', known_provider_types: ['oidc'], detail: '' },
  jwks_check: {
    ok: true,
    applicable: true,
    jwks_url: 'https://id.example/jwks',
    key_count: 2,
    skipped_key_count: 0,
    key_ids: ['a', 'b'],
    detail: '',
  },
  issuer_check: {
    ok: false,
    applicable: true,
    configured_issuer: 'https://id.example',
    accepted_issuers: ['https://id.example'],
    discovery_issuer: 'https://id.example/realms/home',
    detail: 'The provider announces https://id.example/realms/home — set that as issuer_url.',
  },
};

async function renderPage(list: OidcProvider[] = [KC]) {
  fn(api.listOidcProviders).mockResolvedValue(list);
  const { default: Page } = await import('@/pages/admin/AdminOidcProvidersPage');
  renderWithProviders(<Page />, { store: createTestStore(authState({ platformAdmin: true })) });
  await screen.findByTestId('oidc-step-up-notice');
}

function input(testId: string): HTMLInputElement {
  const el = screen.getByTestId(testId);
  return (el.matches('input,select') ? el : el.querySelector('input,select')) as HTMLInputElement;
}

function passwordInput(dialog: HTMLElement, prefix: string): HTMLInputElement {
  return within(dialog).getByTestId(`${prefix}-password`).querySelector('input') as HTMLInputElement;
}

async function fillCreateForm(slug = 'keycloak-home') {
  await userEvent.click(screen.getAllByTestId('oidc-add')[0]);
  await screen.findByTestId('oidc-form-dialog');
  await userEvent.type(input('oidc-form-slug'), slug);
  await userEvent.type(input('oidc-form-display-name'), 'Keycloak Zuhause');
  await userEvent.type(input('oidc-form-issuer'), 'https://id.example/realms/home');
  await userEvent.type(input('oidc-form-client-id'), 'kamerplanter');
  await userEvent.type(input('oidc-form-client-secret'), NEW_SECRET);
}

describe('AdminOidcProvidersPage (#1906)', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
    vi.clearAllMocks();
    sessionStorage.clear();
    fn(auth.listProviders).mockResolvedValue([{ provider: 'local' }]);
    fn(api.createOidcProvider).mockImplementation(async (payload: Record<string, unknown>) => ({
      ...KC,
      key: 'p-new',
      slug: payload.slug,
      display_name: payload.display_name,
      enabled: payload.enabled,
    }));
    fn(api.updateOidcProvider).mockImplementation(async (key: string, payload: Record<string, unknown>) => ({
      ...KC,
      key,
      ...payload,
    }));
    fn(api.deleteOidcProvider).mockResolvedValue(undefined);
  });
  afterEach(() => {
    cleanup();
    sessionStorage.clear();
  });

  describe('list', () => {
    it('shows each provider with its type, issuer, client id and status', async () => {
      await renderPage();
      expect(screen.getByTestId('oidc-field-slug-p-kc')).toHaveTextContent('keycloak');
      expect(screen.getByTestId('oidc-field-issuer-p-kc')).toHaveTextContent('https://id.example/realms/home');
      expect(screen.getByTestId('oidc-field-client-id-p-kc')).toHaveTextContent('kamerplanter');
      expect(screen.getByTestId('oidc-field-scopes-p-kc')).toHaveTextContent('openid email profile');
      expect(screen.getByTestId('oidc-status-p-kc')).toHaveTextContent(i18n.t('pages.admin.oidc.list.enabled'));
    });

    it('shows the empty state with an add action when no provider is configured', async () => {
      await renderPage([]);
      expect(screen.getByTestId('empty-state')).toHaveTextContent(i18n.t('pages.admin.oidc.emptyTitle'));
      expect(screen.queryByTestId('oidc-list')).toBeNull();
    });

    it('never renders a client secret, even one a misbehaving response carries', async () => {
      // The API has no such field; this pins that the page does not render whatever arrives.
      const leaky = { ...KC, client_secret: SECRET_LEAK, client_secret_encrypted: SECRET_LEAK } as OidcProvider;
      await renderPage([leaky]);
      expect(document.body.innerHTML).not.toContain(SECRET_LEAK);

      await userEvent.click(screen.getByTestId('oidc-edit-p-kc'));
      await screen.findByTestId('oidc-form-dialog');
      expect(input('oidc-form-client-secret').value).toBe('');
      expect(input('oidc-form-client-secret').type).toBe('password');
      expect(document.body.innerHTML).not.toContain(SECRET_LEAK);
    });

    it.each([403, 500, 429])('shows an error state with retry for %i, not an empty list', async (status) => {
      fn(api.listOidcProviders).mockRejectedValue(apiError(status));
      const { default: Page } = await import('@/pages/admin/AdminOidcProvidersPage');
      renderWithProviders(<Page />, { store: createTestStore(authState({ platformAdmin: true })) });
      await screen.findByTestId('error-retry');
      expect(screen.queryByTestId('empty-state')).toBeNull();
    });

    it('shows an error state when the failure carries no status', async () => {
      fn(api.listOidcProviders).mockRejectedValue(new Error('network'));
      const { default: Page } = await import('@/pages/admin/AdminOidcProvidersPage');
      renderWithProviders(<Page />, { store: createTestStore(authState({ platformAdmin: true })) });
      await screen.findByTestId('error-retry');
    });
  });

  describe('create', () => {
    it('asks for the step-up before anything is sent, then creates with it', async () => {
      await renderPage([]);
      await fillCreateForm();
      await userEvent.click(screen.getByTestId('oidc-form-submit'));

      const dialog = await screen.findByTestId('oidc-provider-create-dialog');
      expect(api.createOidcProvider).not.toHaveBeenCalled();
      // No echo on a create: the password (or its federated substitute) is the factor.
      expect(within(dialog).queryByTestId('oidc-provider-create-echo')).toBeNull();

      await userEvent.type(passwordInput(dialog, 'oidc-provider-create'), ADMIN_PASSWORD);
      await userEvent.click(within(dialog).getByTestId('oidc-provider-create-confirm'));

      await waitFor(() =>
        expect(api.createOidcProvider).toHaveBeenCalledWith({
          slug: 'keycloak-home',
          display_name: 'Keycloak Zuhause',
          provider_type: 'oidc',
          issuer_url: 'https://id.example/realms/home',
          client_id: 'kamerplanter',
          client_secret: NEW_SECRET,
          scopes: ['openid', 'email', 'profile'],
          auto_discover: true,
          enabled: false,
          current_password: ADMIN_PASSWORD,
        }),
      );
      await waitFor(() => expect(screen.queryByTestId('oidc-form-dialog')).toBeNull());
      expect(screen.getByTestId('oidc-provider-p-new')).toBeInTheDocument();
    });

    it('binds a federated admin\'s code to "new:<slug>"', async () => {
      fn(auth.listProviders).mockResolvedValue([{ provider: 'github' }]);
      await renderPage([]);
      await fillCreateForm('keycloak-home');
      await userEvent.click(screen.getByTestId('oidc-form-submit'));

      const dialog = await screen.findByTestId('oidc-provider-create-dialog');
      await userEvent.click(await within(dialog).findByTestId('oidc-provider-create-send-code'));

      await waitFor(() =>
        expect(auth.requestStepUpCode).toHaveBeenCalledWith('oidc_provider_change', 'new:keycloak-home'),
      );
    });

    it('keeps the form and its values when the step-up dialog is cancelled', async () => {
      await renderPage([]);
      await fillCreateForm();
      await userEvent.click(screen.getByTestId('oidc-form-submit'));
      const dialog = await screen.findByTestId('oidc-provider-create-dialog');
      await userEvent.click(within(dialog).getByTestId('oidc-provider-create-cancel'));

      await waitFor(() => expect(screen.queryByTestId('oidc-provider-create-dialog')).toBeNull());
      expect(input('oidc-form-slug').value).toBe('keycloak-home');
      expect(api.createOidcProvider).not.toHaveBeenCalled();
    });

    it('shows a refusal (taken slug, wrong password) inside the step-up dialog and stays open', async () => {
      fn(api.createOidcProvider).mockRejectedValue(
        apiError(409, { error_code: 'DUPLICATE', message: 'Provider slug already exists.' }),
      );
      await renderPage([]);
      await fillCreateForm();
      await userEvent.click(screen.getByTestId('oidc-form-submit'));
      const dialog = await screen.findByTestId('oidc-provider-create-dialog');
      await userEvent.type(passwordInput(dialog, 'oidc-provider-create'), ADMIN_PASSWORD);
      await userEvent.click(within(dialog).getByTestId('oidc-provider-create-confirm'));

      expect(await within(dialog).findByTestId('oidc-provider-create-error')).toHaveTextContent(
        'Provider slug already exists.',
      );
      expect(screen.getByTestId('oidc-form-dialog')).toBeInTheDocument();
    });

    it('validates before it spends a step-up: missing fields, bad slug, plain-http issuer', async () => {
      await renderPage([]);
      await userEvent.click(screen.getAllByTestId('oidc-add')[0]);
      await screen.findByTestId('oidc-form-dialog');

      await userEvent.click(screen.getByTestId('oidc-form-submit'));
      expect(screen.queryByTestId('oidc-provider-create-dialog')).toBeNull();
      expect(screen.getByTestId('oidc-form-slug')).toHaveTextContent(i18n.t('pages.admin.oidc.form.slugInvalid'));

      await userEvent.type(input('oidc-form-slug'), 'ok-slug');
      await userEvent.type(input('oidc-form-display-name'), 'X');
      await userEvent.type(input('oidc-form-issuer'), 'http://id.example');
      await userEvent.type(input('oidc-form-client-id'), 'c');
      await userEvent.type(input('oidc-form-client-secret'), NEW_SECRET);
      expect(screen.getByTestId('oidc-form-issuer')).toHaveTextContent(i18n.t('pages.admin.oidc.form.urlInvalid'));
      await userEvent.click(screen.getByTestId('oidc-form-submit'));
      expect(screen.queryByTestId('oidc-provider-create-dialog')).toBeNull();
      expect(api.createOidcProvider).not.toHaveBeenCalled();
    });

    it('refuses a GitHub provider without user:email before the step-up', async () => {
      await renderPage([]);
      await fillCreateForm();
      await userEvent.selectOptions(input('oidc-form-type'), 'github');
      expect(screen.getByTestId('oidc-form-scopes')).toHaveTextContent(i18n.t('pages.admin.oidc.form.githubScopes'));
      await userEvent.click(screen.getByTestId('oidc-form-submit'));
      expect(screen.queryByTestId('oidc-provider-create-dialog')).toBeNull();
    });

    it('starts switched off', async () => {
      await renderPage([]);
      await userEvent.click(screen.getAllByTestId('oidc-add')[0]);
      await screen.findByTestId('oidc-form-dialog');
      expect(input('oidc-form-enabled')).not.toBeChecked();
    });
  });

  describe('edit', () => {
    async function openEdit() {
      await renderPage();
      await userEvent.click(screen.getByTestId('oidc-edit-p-kc'));
      await screen.findByTestId('oidc-form-dialog');
    }

    it('offers nothing to save until something changes, and locks the slug', async () => {
      await openEdit();
      expect(screen.getByTestId('oidc-form-submit')).toBeDisabled();
      expect(input('oidc-form-slug')).toBeDisabled();
      expect(input('oidc-form-slug').value).toBe('keycloak');
    });

    it('repointing the issuer asks for a step-up bound to the configuration key', async () => {
      fn(auth.listProviders).mockResolvedValue([{ provider: 'github' }]);
      await openEdit();
      const issuer = input('oidc-form-issuer');
      await userEvent.clear(issuer);
      await userEvent.type(issuer, 'https://other.example');
      expect(screen.getByTestId('oidc-form-step-up-hint')).toHaveTextContent(
        i18n.t('pages.admin.oidc.form.willAskStepUp'),
      );
      await userEvent.click(screen.getByTestId('oidc-form-submit'));

      const dialog = await screen.findByTestId('oidc-provider-update-dialog');
      expect(api.updateOidcProvider).not.toHaveBeenCalled();
      await userEvent.click(await within(dialog).findByTestId('oidc-provider-update-send-code'));
      await waitFor(() => expect(auth.requestStepUpCode).toHaveBeenCalledWith('oidc_provider_change', 'p-kc'));
    });

    it('sends only the changed fields plus the step-up', async () => {
      await openEdit();
      const issuer = input('oidc-form-issuer');
      await userEvent.clear(issuer);
      await userEvent.type(issuer, 'https://other.example');
      await userEvent.click(screen.getByTestId('oidc-form-submit'));

      const dialog = await screen.findByTestId('oidc-provider-update-dialog');
      await userEvent.type(passwordInput(dialog, 'oidc-provider-update'), ADMIN_PASSWORD);
      await userEvent.click(within(dialog).getByTestId('oidc-provider-update-confirm'));

      await waitFor(() =>
        expect(api.updateOidcProvider).toHaveBeenCalledWith('p-kc', {
          issuer_url: 'https://other.example',
          current_password: ADMIN_PASSWORD,
        }),
      );
    });

    it('a new client secret needs the step-up and is sent once, never shown', async () => {
      await openEdit();
      await userEvent.type(input('oidc-form-client-secret'), NEW_SECRET);
      await userEvent.click(screen.getByTestId('oidc-form-submit'));
      const dialog = await screen.findByTestId('oidc-provider-update-dialog');
      await userEvent.type(passwordInput(dialog, 'oidc-provider-update'), ADMIN_PASSWORD);
      await userEvent.click(within(dialog).getByTestId('oidc-provider-update-confirm'));

      await waitFor(() =>
        expect(api.updateOidcProvider).toHaveBeenCalledWith('p-kc', {
          client_secret: NEW_SECRET,
          current_password: ADMIN_PASSWORD,
        }),
      );
      await waitFor(() => expect(screen.queryByTestId('oidc-form-dialog')).toBeNull());
      expect(document.body.innerHTML).not.toContain(NEW_SECRET);
    });

    it('switching the provider off asks for the step-up too', async () => {
      await openEdit();
      await userEvent.click(input('oidc-form-enabled'));
      await userEvent.click(screen.getByTestId('oidc-form-submit'));
      expect(await screen.findByTestId('oidc-provider-update-dialog')).toBeInTheDocument();
      expect(api.updateOidcProvider).not.toHaveBeenCalled();
    });

    it('a presentation-only edit (display name, icon) saves without any dialog', async () => {
      await openEdit();
      const name = input('oidc-form-display-name');
      await userEvent.clear(name);
      await userEvent.type(name, 'Firmenkonto');
      await userEvent.type(input('oidc-form-icon-url'), 'https://cdn.example/icon.png');
      expect(screen.getByTestId('oidc-form-step-up-hint')).toHaveTextContent(
        i18n.t('pages.admin.oidc.form.presentationOnly'),
      );
      await userEvent.click(screen.getByTestId('oidc-form-submit'));

      await waitFor(() =>
        expect(api.updateOidcProvider).toHaveBeenCalledWith('p-kc', {
          display_name: 'Firmenkonto',
          icon_url: 'https://cdn.example/icon.png',
        }),
      );
      expect(screen.queryByTestId('oidc-provider-update-dialog')).toBeNull();
      await waitFor(() => expect(screen.queryByTestId('oidc-form-dialog')).toBeNull());
      expect(screen.getByTestId('oidc-provider-p-kc')).toHaveTextContent('Firmenkonto');
    });

    it('shows a refusal of a direct presentation save inside the form', async () => {
      fn(api.updateOidcProvider).mockRejectedValue(apiError(500, { message: 'Server broke.' }));
      await openEdit();
      const name = input('oidc-form-display-name');
      await userEvent.clear(name);
      await userEvent.type(name, 'X');
      await userEvent.click(screen.getByTestId('oidc-form-submit'));
      expect(await screen.findByTestId('oidc-form-error')).toBeInTheDocument();
      expect(screen.getByTestId('oidc-form-dialog')).toBeInTheDocument();
    });
  });

  describe('delete', () => {
    it('asks for the slug and a step-up bound to the key, then deletes', async () => {
      await renderPage();
      await userEvent.click(screen.getByTestId('oidc-delete-p-kc'));
      const dialog = await screen.findByTestId('oidc-provider-delete-dialog');
      expect(api.deleteOidcProvider).not.toHaveBeenCalled();

      const confirm = within(dialog).getByTestId('oidc-provider-delete-confirm');
      await userEvent.type(passwordInput(dialog, 'oidc-provider-delete'), ADMIN_PASSWORD);
      expect(confirm).toBeDisabled();
      await userEvent.type(
        within(dialog).getByTestId('oidc-provider-delete-echo').querySelector('input') as HTMLInputElement,
        'keycloak',
      );
      await userEvent.click(confirm);

      await waitFor(() =>
        expect(api.deleteOidcProvider).toHaveBeenCalledWith('p-kc', { current_password: ADMIN_PASSWORD }),
      );
      await waitFor(() => expect(screen.queryByTestId('oidc-provider-p-kc')).toBeNull());
    });

    it('binds a federated admin\'s code to the configuration key', async () => {
      fn(auth.listProviders).mockResolvedValue([{ provider: 'github' }]);
      await renderPage();
      await userEvent.click(screen.getByTestId('oidc-delete-p-kc'));
      const dialog = await screen.findByTestId('oidc-provider-delete-dialog');
      await userEvent.click(await within(dialog).findByTestId('oidc-provider-delete-send-code'));
      await waitFor(() => expect(auth.requestStepUpCode).toHaveBeenCalledWith('oidc_provider_change', 'p-kc'));
    });

    it('keeps the provider and shows the refusal when the step-up is wrong', async () => {
      fn(api.deleteOidcProvider).mockRejectedValue(
        apiError(401, { error_code: 'UNAUTHORIZED', message: 'Password confirmation failed.' }),
      );
      await renderPage();
      await userEvent.click(screen.getByTestId('oidc-delete-p-kc'));
      const dialog = await screen.findByTestId('oidc-provider-delete-dialog');
      await userEvent.type(passwordInput(dialog, 'oidc-provider-delete'), 'wrong');
      await userEvent.type(
        within(dialog).getByTestId('oidc-provider-delete-echo').querySelector('input') as HTMLInputElement,
        'keycloak',
      );
      await userEvent.click(within(dialog).getByTestId('oidc-provider-delete-confirm'));
      expect(await within(dialog).findByTestId('oidc-provider-delete-error')).toBeInTheDocument();
      expect(screen.getByTestId('oidc-provider-p-kc')).toBeInTheDocument();
    });
  });

  describe('discovery test', () => {
    it('runs without a step-up and shows every verdict with its detail', async () => {
      fn(api.testOidcProvider).mockResolvedValue(TEST_OK);
      await renderPage();
      await userEvent.click(screen.getByTestId('oidc-test-p-kc'));

      const result = await screen.findByTestId('oidc-test-result');
      expect(api.testOidcProvider).toHaveBeenCalledWith('p-kc');
      expect(screen.queryByTestId('oidc-provider-update-dialog')).toBeNull();
      expect(within(result).getByTestId('oidc-test-message')).toHaveTextContent('validated successfully');
      expect(within(result).getByTestId('oidc-verdict-scope-status')).toHaveTextContent(i18n.t('pages.admin.oidc.test.ok'));
      expect(within(result).getByTestId('oidc-verdict-jwks')).toHaveTextContent('2');
      // A failing verdict is words, not colour alone, and carries the server's cause.
      expect(within(result).getByTestId('oidc-verdict-issuer-status')).toHaveTextContent(
        i18n.t('pages.admin.oidc.test.failed'),
      );
      expect(within(result).getByTestId('oidc-verdict-issuer')).toHaveTextContent('set that as issuer_url');
    });

    it('says "not applicable" for a verdict the provider type has no use for', async () => {
      fn(api.testOidcProvider).mockResolvedValue({
        ...TEST_OK,
        jwks_check: { ...TEST_OK.jwks_check, ok: true, applicable: false },
      });
      await renderPage();
      await userEvent.click(screen.getByTestId('oidc-test-p-kc'));
      const result = await screen.findByTestId('oidc-test-result');
      expect(within(result).getByTestId('oidc-verdict-jwks-status')).toHaveTextContent(
        i18n.t('pages.admin.oidc.test.notApplicable'),
      );
    });

    it('reports a failed request instead of a result', async () => {
      fn(api.testOidcProvider).mockRejectedValue(apiError(404, { message: 'Provider not found.' }));
      await renderPage();
      await userEvent.click(screen.getByTestId('oidc-test-p-kc'));
      expect(await screen.findByTestId('oidc-test-error')).toHaveTextContent('Provider not found.');
    });
  });

  it.each(['oidc-provider-create', 'oidc-provider-update', 'oidc-provider-delete'])(
    'consumes the resume context of "%s" after the identity-provider round trip, without reopening a dialog',
    async (surface) => {
      storePendingStepUpToken('tok-123', 'oidc_provider_change', 'p-kc', Date.now());
      saveStepUpResume({ surface, action: 'oidc_provider_change', target: 'p-kc', returnPath: '/' });
      expect(readStepUpResume()).not.toBeNull();

      await renderPage();

      // Read once and removed — the typed form values and the chosen provider are gone, so the
      // dialog is not reopened; the token waits for the admin to repeat the act for the same key.
      expect(readStepUpResume()).toBeNull();
      expect(screen.queryByTestId(`${surface}-dialog`)).toBeNull();
    },
  );
});
