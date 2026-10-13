import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { screen, waitFor, cleanup, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';
import { server } from '@/test/mocks/server';
import { renderWithProviders, createTestStore, authState } from '@/test/helpers';
import AccountSettingsPage from '@/pages/auth/AccountSettingsPage';
import PrivacySettingsPage from '@/pages/auth/PrivacySettingsPage';
import { redirectTo } from '@/utils/browserNavigation';
import {
  STEP_UP_REAUTH_TOKEN_KEY,
  readStepUpResume,
  saveStepUpResume,
  storePendingStepUpToken,
  storeStepUpReauthError,
} from '@/utils/stepUpReauth';

vi.mock('@/utils/browserNavigation', () => ({ redirectTo: vi.fn() }));

/**
 * #1815 — the password form and the surfaces that confirm with a dialog pick the
 * fresh sign-in up again after the provider sent the browser back.
 */

// Credential-shaped values are assembled at runtime (GitGuardian, #1838).
const NEW_PASSWORD = ['new', 'Secr', '3t', '123'].join('-');
const TOKEN = ['re', 'auth', '-', 'tok', 'en'].join('');
const AUTH_URL = 'https://accounts.example.test/o/oauth2/auth?prompt=login';
const OWN_EMAIL = 'tester@example.org';

function googleOnly() {
  server.use(
    http.get('/api/v1/users/me/providers', () =>
      HttpResponse.json([{ key: 'prov-g', provider: 'google', provider_email: OWN_EMAIL }]),
    ),
  );
}

function input(testId: string): HTMLInputElement {
  return screen.getByTestId(testId).querySelector('input') as HTMLInputElement;
}

describe('AccountSettingsPage — password form with a fresh sign-in (#1815)', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
    sessionStorage.clear();
    vi.mocked(redirectTo).mockReset();
  });
  afterEach(() => cleanup());

  it('uses the fresh sign-in, not the code, for a google-only account', async () => {
    googleOnly();
    let startBody: unknown = null;
    server.use(
      http.post('/api/v1/users/me/step-up/oidc', async ({ request }) => {
        startBody = await request.json();
        return HttpResponse.json({ authorization_url: AUTH_URL });
      }),
    );
    const user = userEvent.setup();
    renderWithProviders(<AccountSettingsPage />, {
      store: createTestStore(authState()),
      route: '/account#security',
    });

    const reauth = await screen.findByTestId('change-password-reauth');
    expect(screen.queryByTestId('change-password-send-code')).not.toBeInTheDocument();
    expect(screen.queryByTestId('current-password-field')).not.toBeInTheDocument();
    await user.type(input('new-password-field'), NEW_PASSWORD);
    expect(screen.getByTestId('change-password-btn')).toBeDisabled();

    await user.click(reauth);

    await waitFor(() => expect(redirectTo).toHaveBeenCalledWith(AUTH_URL));
    expect(startBody).toEqual({
      action: 'password_change',
      provider_key: 'prov-g',
      client_nonce: readStepUpResume()?.nonce,
    });
    expect(readStepUpResume()).toMatchObject({
      surface: 'change-password',
      action: 'password_change',
      returnPath: '/account#security',
    });
  });

  it('sends the pending token as step_up_token after the return and consumes it', async () => {
    googleOnly();
    storePendingStepUpToken(TOKEN, 'password_change', null);
    saveStepUpResume({
      surface: 'change-password',
      action: 'password_change',
      returnPath: '/account#security',
    });
    let body: unknown = null;
    server.use(
      http.post('/api/v1/users/me/password', async ({ request }) => {
        body = await request.json();
        return HttpResponse.json({ message: 'ok' });
      }),
    );
    const user = userEvent.setup();
    renderWithProviders(<AccountSettingsPage />, {
      store: createTestStore(authState()),
      route: '/account#security',
    });

    expect(await screen.findByTestId('change-password-reauth-done')).toBeInTheDocument();
    await user.type(input('new-password-field'), NEW_PASSWORD);
    await user.click(screen.getByTestId('change-password-btn'));

    await waitFor(() =>
      expect(body).toEqual({
        current_password: null,
        new_password: NEW_PASSWORD,
        step_up_token: TOKEN,
      }),
    );
    expect(sessionStorage.getItem(STEP_UP_REAUTH_TOKEN_KEY)).toBeNull();
  });

  it('keeps the pending token when the new password is refused (422) and spends it on success', async () => {
    googleOnly();
    storePendingStepUpToken(TOKEN, 'password_change', null);
    const bodies: unknown[] = [];
    server.use(
      http.post('/api/v1/users/me/password', async ({ request }) => {
        bodies.push(await request.json());
        if (bodies.length === 1) {
          return HttpResponse.json(
            {
              error_id: 'e',
              error_code: 'VALIDATION_ERROR',
              message: 'Backend English message.',
              details: [{ field: 'body.new_password', reason: 'too weak', code: 'value_error' }],
              timestamp: '',
              path: '/api/v1/users/me/password',
              method: 'POST',
            },
            { status: 422 },
          );
        }
        return HttpResponse.json({ message: 'ok' });
      }),
    );
    const user = userEvent.setup();
    renderWithProviders(<AccountSettingsPage />, {
      store: createTestStore(authState()),
      route: '/account#security',
    });

    await screen.findByTestId('change-password-reauth-done');
    await user.type(input('new-password-field'), NEW_PASSWORD);
    await user.click(screen.getByTestId('change-password-btn'));

    await waitFor(() => expect(bodies).toHaveLength(1));
    expect(await screen.findByText('Backend English message.')).toBeInTheDocument();
    expect(sessionStorage.getItem(STEP_UP_REAUTH_TOKEN_KEY)).not.toBeNull();
    expect(screen.getByTestId('change-password-reauth-done')).toBeInTheDocument();

    await user.click(screen.getByTestId('change-password-btn'));
    await waitFor(() => expect(bodies).toHaveLength(2));
    expect(bodies[1]).toEqual({
      current_password: null,
      new_password: NEW_PASSWORD,
      step_up_token: TOKEN,
    });
    await waitFor(() => expect(sessionStorage.getItem(STEP_UP_REAUTH_TOKEN_KEY)).toBeNull());
  });

  it('drops the pending token when the step-up itself is refused (401)', async () => {
    googleOnly();
    storePendingStepUpToken(TOKEN, 'password_change', null);
    server.use(
      http.post('/api/v1/users/me/password', () =>
        HttpResponse.json(
          {
            error_id: 'e',
            error_code: 'STEP_UP_REAUTH_REQUIRED',
            message: 'Backend English message.',
            details: [{ field: 'step_up_token', reason: 'r', code: 'STEP_UP_REAUTH_REQUIRED' }],
            timestamp: '',
            path: '/api/v1/users/me/password',
            method: 'POST',
          },
          { status: 401 },
        ),
      ),
    );
    const user = userEvent.setup();
    renderWithProviders(<AccountSettingsPage />, {
      store: createTestStore(authState()),
      route: '/account#security',
    });

    await screen.findByTestId('change-password-reauth-done');
    await user.type(input('new-password-field'), NEW_PASSWORD);
    await user.click(screen.getByTestId('change-password-btn'));

    expect(await screen.findByTestId('change-password-reauth')).toBeInTheDocument();
    expect(sessionStorage.getItem(STEP_UP_REAUTH_TOKEN_KEY)).toBeNull();
  });

  it('keeps the button disabled while the new password is shorter than 10 characters', async () => {
    googleOnly();
    storePendingStepUpToken(TOKEN, 'password_change', null);
    const user = userEvent.setup();
    renderWithProviders(<AccountSettingsPage />, {
      store: createTestStore(authState()),
      route: '/account#security',
    });

    await screen.findByTestId('change-password-reauth-done');
    await user.type(input('new-password-field'), ['short', '-pw'].join(''));
    expect(screen.getByTestId('change-password-btn')).toBeDisabled();
    await user.type(input('new-password-field'), '12');
    expect(screen.getByTestId('change-password-btn')).toBeEnabled();
  });

  it('shows the callback error on the password form', async () => {
    googleOnly();
    storeStepUpReauthError('step_up_cancelled', 'password_change');
    renderWithProviders(<AccountSettingsPage />, {
      store: createTestStore(authState()),
      route: '/account#security',
    });

    expect(await screen.findByText(i18n.t('pages.auth.stepUpReauthCancelled'))).toBeInTheDocument();
  });
});

describe('Step-up dialogs reopen after the fresh sign-in (#1815)', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
    sessionStorage.clear();
  });
  afterEach(() => cleanup());

  it('reopens the account-deletion dialog with the pending token', async () => {
    googleOnly();
    storePendingStepUpToken(TOKEN, 'account_erasure', null);
    saveStepUpResume({
      surface: 'delete-account',
      action: 'account_erasure',
      returnPath: '/account#account',
    });
    let body: unknown = null;
    server.use(
      http.delete('/api/v1/users/me', async ({ request }) => {
        body = await request.json();
        return HttpResponse.json({ message: 'ok' });
      }),
    );
    const user = userEvent.setup();
    renderWithProviders(<AccountSettingsPage />, {
      store: createTestStore(authState()),
      route: '/account#account',
    });

    const dialog = await screen.findByTestId('delete-account-dialog');
    expect(await within(dialog).findByTestId('delete-account-reauth-done')).toBeInTheDocument();
    await user.type(
      within(dialog).getByTestId('delete-account-email').querySelector('input') as HTMLInputElement,
      OWN_EMAIL,
    );
    await user.click(within(dialog).getByTestId('delete-account-confirm'));

    await waitFor(() => expect(body).toEqual({ confirm_email: OWN_EMAIL, step_up_token: TOKEN }));
    expect(readStepUpResume()).toBeNull();
  });

  it('does not reopen the dialog for a resume of another surface', async () => {
    googleOnly();
    storePendingStepUpToken(TOKEN, 'account_erasure', null);
    saveStepUpResume({
      surface: 'privacy-erasure',
      action: 'account_erasure',
      returnPath: '/privacy',
    });
    renderWithProviders(<AccountSettingsPage />, {
      store: createTestStore(authState()),
      route: '/account#account',
    });

    await screen.findByTestId('delete-account-btn');
    expect(screen.queryByTestId('delete-account-dialog')).not.toBeInTheDocument();
  });

  it('reopens the privacy erasure dialog on its tab after a failed sign-in, with the message', async () => {
    googleOnly();
    storeStepUpReauthError('step_up_stale', 'account_erasure');
    saveStepUpResume({
      surface: 'privacy-erasure',
      action: 'account_erasure',
      returnPath: '/privacy',
    });
    renderWithProviders(<PrivacySettingsPage />, {
      store: createTestStore(authState()),
      route: '/privacy',
    });

    const dialog = await screen.findByTestId('privacy-erasure-dialog');
    expect(await within(dialog).findByTestId('privacy-erasure-dialog-error')).toHaveTextContent(
      i18n.t('pages.auth.stepUpReauthStale'),
    );
    expect(screen.getByTestId('privacy-erasure-panel')).toBeInTheDocument();
  });
});
