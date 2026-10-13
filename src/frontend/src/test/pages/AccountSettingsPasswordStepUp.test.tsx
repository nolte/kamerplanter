import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { screen, waitFor, cleanup, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';
import { server } from '@/test/mocks/server';
import { renderWithProviders, createTestStore, authState } from '@/test/helpers';
import AccountSettingsPage from '@/pages/auth/AccountSettingsPage';

/**
 * #1842 / #1815 — the password form on the security tab.
 *
 * #1842: the "current password" field used to be shown only when the provider
 * list positively contained `local`. An empty or failed list hid it and sent
 * `current_password: null`, which the backend answers 401 — with no field left
 * to answer it (the #394 dead end). The form now follows the same fail-closed
 * rule as `StepUpConfirmDialog`.
 *
 * #1815: an account without a local password confirms setting one with a
 * one-time code sent by e-mail.
 */

// Credential-shaped values are assembled at runtime (GitGuardian, #1838).
const OLD_PASSWORD = ['old', 'Secr', '3t'].join('-');
const NEW_PASSWORD = ['new', 'Secr', '3t', '123'].join('-');
const CODE = ['4', '8', '1', '5', '1', '6'].join('');

function providers(list: { provider: string }[]) {
  server.use(
    http.get('/api/v1/users/me/providers', () =>
      HttpResponse.json(
        list.map((p, i) => ({ key: `prov-${i}`, provider: p.provider, provider_email: 'tester@example.org' })),
      ),
    ),
  );
}

function errorResponse(status: number, errorCode: string) {
  return HttpResponse.json(
    {
      error_id: 'err',
      error_code: errorCode,
      message: 'Backend English message.',
      details: [],
      timestamp: '',
      path: '/api/v1/users/me/password',
      method: 'POST',
    },
    { status },
  );
}

function renderSecurityTab() {
  return renderWithProviders(<AccountSettingsPage />, {
    store: createTestStore(authState()),
    route: '/account#security',
  });
}

function input(testId: string): HTMLInputElement {
  return screen.getByTestId(testId).querySelector('input') as HTMLInputElement;
}

describe('AccountSettingsPage — password form step-up (#1842)', () => {
  beforeEach(() => i18n.changeLanguage('de'));
  afterEach(() => cleanup());

  it('shows the current-password field when the provider list is empty', async () => {
    providers([]);
    renderSecurityTab();

    expect(await screen.findByTestId('current-password-field')).toBeInTheDocument();
    expect(screen.getByTestId('change-password-btn')).toBeDisabled();
  });

  it('shows the current-password field when the provider list fails to load', async () => {
    server.use(http.get('/api/v1/users/me/providers', () => errorResponse(500, 'INTERNAL_ERROR')));
    renderSecurityTab();

    expect(await screen.findByTestId('current-password-field')).toBeInTheDocument();
  });

  it('sends the typed current password for an empty provider list', async () => {
    providers([]);
    let body: unknown = null;
    server.use(
      http.post('/api/v1/users/me/password', async ({ request }) => {
        body = await request.json();
        return HttpResponse.json({ message: 'ok' });
      }),
    );
    const user = userEvent.setup();
    renderSecurityTab();

    await user.type(input('current-password-field'), OLD_PASSWORD);
    await user.type(input('new-password-field'), NEW_PASSWORD);
    await user.click(screen.getByTestId('change-password-btn'));

    await waitFor(() =>
      expect(body).toEqual({ current_password: OLD_PASSWORD, new_password: NEW_PASSWORD }),
    );
  });

  it('keeps the current-password field after a 401 for an empty provider list', async () => {
    providers([]);
    server.use(http.post('/api/v1/users/me/password', () => errorResponse(401, 'UNAUTHORIZED')));
    const user = userEvent.setup();
    renderSecurityTab();

    await screen.findByTestId('current-password-field');
    await user.type(input('current-password-field'), OLD_PASSWORD);
    await user.type(input('new-password-field'), NEW_PASSWORD);
    await user.click(screen.getByTestId('change-password-btn'));

    expect(await screen.findByText('Backend English message.')).toBeInTheDocument();
    expect(screen.getByTestId('current-password-field')).toBeInTheDocument();
    // The rejected password is cleared so it is not resent by accident.
    expect(input('current-password-field').value).toBe('');
  });

  it('keeps the current-password field after a 401, even for a federated-only list', async () => {
    providers([{ provider: 'github' }]);
    server.use(http.post('/api/v1/users/me/password', () => errorResponse(401, 'UNAUTHORIZED')));
    const user = userEvent.setup();
    renderSecurityTab();

    const send = await screen.findByTestId('change-password-send-code');
    expect(send).toBeInTheDocument();
    expect(screen.queryByTestId('current-password-field')).not.toBeInTheDocument();

    await user.type(input('change-password-code'), CODE);
    await user.type(input('new-password-field'), NEW_PASSWORD);
    await user.click(screen.getByTestId('change-password-btn'));

    expect(await screen.findByTestId('current-password-field')).toBeInTheDocument();
    // The rejected code is cleared so it is not resent by accident.
    expect(input('change-password-code').value).toBe('');
  });
});

describe('AccountSettingsPage — e-mailed step-up code (#1815)', () => {
  beforeEach(() => i18n.changeLanguage('de'));
  afterEach(() => cleanup());

  it('offers the code for a federated-only account and sends it as step_up_code', async () => {
    providers([{ provider: 'github' }]);
    let codeRequests = 0;
    let body: unknown = null;
    let codeBody: unknown = null;
    server.use(
      http.post('/api/v1/users/me/step-up-code', async ({ request }) => {
        codeRequests += 1;
        codeBody = await request.json();
        return HttpResponse.json({ expires_at: '2026-09-25T12:10:00Z', expires_in: 600 }, { status: 202 });
      }),
      http.post('/api/v1/users/me/password', async ({ request }) => {
        body = await request.json();
        return HttpResponse.json({ message: 'ok' });
      }),
    );
    const user = userEvent.setup();
    renderSecurityTab();

    await user.click(await screen.findByTestId('change-password-send-code'));
    await waitFor(() => expect(codeRequests).toBe(1));
    expect(codeBody).toEqual({ action: 'password_change' });
    expect(
      await screen.findByText(i18n.t('pages.auth.stepUpCodeSent', { minutes: 10 })),
    ).toBeInTheDocument();

    const codeInput = input('change-password-code');
    expect(codeInput).toHaveAttribute('autocomplete', 'one-time-code');
    expect(codeInput).toHaveAttribute('inputmode', 'numeric');

    await user.type(input('new-password-field'), NEW_PASSWORD);
    // The code is required in this state.
    expect(screen.getByTestId('change-password-btn')).toBeDisabled();
    await user.type(codeInput, CODE);
    await user.click(screen.getByTestId('change-password-btn'));

    await waitFor(() =>
      expect(body).toEqual({ current_password: null, new_password: NEW_PASSWORD, step_up_code: CODE }),
    );
  });

  it('switches to the code when the server answers STEP_UP_CODE_REQUIRED', async () => {
    providers([]);
    server.use(
      http.post('/api/v1/users/me/password', () => errorResponse(401, 'STEP_UP_CODE_REQUIRED')),
    );
    const user = userEvent.setup();
    renderSecurityTab();

    await screen.findByTestId('current-password-field');
    await user.type(input('current-password-field'), OLD_PASSWORD);
    await user.type(input('new-password-field'), NEW_PASSWORD);
    await user.click(screen.getByTestId('change-password-btn'));

    expect(await screen.findByTestId('change-password-send-code')).toBeInTheDocument();
    expect(screen.getByTestId('change-password-code')).toBeInTheDocument();
    expect(await screen.findByText(i18n.t('pages.auth.stepUpCodeRequired'))).toBeInTheDocument();
  });
});

describe('AccountSettingsPage — account deletion code (review SEC-003)', () => {
  beforeEach(() => i18n.changeLanguage('de'));
  afterEach(() => cleanup());

  it('asks for a code that confirms the account erasure only', async () => {
    providers([{ provider: 'github' }]);
    let codeBody: unknown = null;
    server.use(
      http.post('/api/v1/users/me/step-up-code', async ({ request }) => {
        codeBody = await request.json();
        return HttpResponse.json({ expires_at: '2026-09-25T12:10:00Z', expires_in: 600 }, { status: 202 });
      }),
    );
    const user = userEvent.setup();
    renderWithProviders(<AccountSettingsPage />, { store: createTestStore(authState()), route: '/account#account' });

    await user.click(await screen.findByTestId('delete-account-btn'));
    const dialog = await screen.findByTestId('delete-account-dialog');
    await user.click(await within(dialog).findByTestId('delete-account-send-code'));

    await waitFor(() => expect(codeBody).toEqual({ action: 'account_erasure' }));
  });
});
