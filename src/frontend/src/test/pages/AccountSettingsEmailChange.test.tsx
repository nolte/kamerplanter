import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { screen, waitFor, cleanup, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';
import { server } from '@/test/mocks/server';
import { renderWithProviders, createTestStore, authState } from '@/test/helpers';
import AccountSettingsPage from '@/pages/auth/AccountSettingsPage';
import { EMAIL_CHANGE_ADDRESS_KEY } from '@/pages/auth/EmailChangeCard';
import {
  STEP_UP_REAUTH_TOKEN_KEY,
  readStepUpResume,
  saveStepUpResume,
  storePendingStepUpToken,
} from '@/utils/stepUpReauth';

/**
 * #1848 — requesting an e-mail change from the account settings.
 *
 * `POST /privacy/email-change` sits behind the shared step-up (REQ-023 §3.9) with
 * the act `email_change` and **no echo**: `password` for an account with a local
 * password (this route's field is `password`, not `current_password`), else the
 * e-mailed `step_up_code` or the `step_up_token` of a fresh sign-in. The card
 * opens `StepUpConfirmDialog` for it and, on 201, says where the link went.
 */

const OWN_EMAIL = 'tester@example.org';
const NEW_EMAIL = 'tester.new@example.org';
// Credential-shaped values are assembled at runtime (GitGuardian, #1838).
const PASSWORD = ['my', 'Secr', '3t'].join('-');
const CODE = ['4', '8', '1', '5', '1', '6'].join('');
const TOKEN = ['reauth', 'token', '1848'].join('-');

function providers(list: { provider: string }[]) {
  server.use(
    http.get('/api/v1/users/me/providers', () =>
      HttpResponse.json(list.map((p, i) => ({ key: `prov-${i}`, provider: p.provider, provider_email: OWN_EMAIL }))),
    ),
  );
}

function created(newEmail: string) {
  return HttpResponse.json(
    {
      key: 'ec-1',
      new_email: newEmail,
      status: 'pending',
      requested_at: '2026-09-26T10:00:00Z',
      expires_at: '2026-09-27T10:00:00Z',
      confirmed_at: null,
    },
    { status: 201 },
  );
}

function errorResponse(status: number, errorCode: string, details: unknown[] = []) {
  return HttpResponse.json(
    {
      error_id: 'err',
      error_code: errorCode,
      message: 'Backend English message.',
      details,
      timestamp: '',
      path: '/api/v1/privacy/email-change',
      method: 'POST',
    },
    { status },
  );
}

function captureRequests() {
  const bodies: unknown[] = [];
  server.use(
    http.post('/api/v1/privacy/email-change', async ({ request }) => {
      const body = (await request.json()) as { new_email: string };
      bodies.push(body);
      return created(body.new_email);
    }),
  );
  return bodies;
}

function renderProfileTab(route = '/account') {
  return renderWithProviders(<AccountSettingsPage />, { store: createTestStore(authState()), route });
}

function newEmailInput(): HTMLInputElement {
  return screen.getByTestId('email-change-new-email').querySelector('input') as HTMLInputElement;
}

async function openDialog(address = NEW_EMAIL) {
  const user = userEvent.setup();
  renderProfileTab();
  await screen.findByTestId('email-change-card');
  await user.type(newEmailInput(), address);
  await user.click(screen.getByTestId('email-change-submit'));
  const dialog = await screen.findByTestId('email-change-dialog');
  return { user, dialog };
}

describe('AccountSettingsPage — e-mail change (#1848)', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
    sessionStorage.clear();
  });
  afterEach(() => cleanup());

  it('asks for no echo and sends the current password as `password`', async () => {
    providers([{ provider: 'local' }]);
    const bodies = captureRequests();
    const { user, dialog } = await openDialog();

    expect(within(dialog).queryByTestId('email-change-echo')).not.toBeInTheDocument();
    expect(within(dialog).getByText(NEW_EMAIL, { exact: false })).toBeInTheDocument();
    const confirm = within(dialog).getByTestId('email-change-confirm');
    expect(confirm).toBeDisabled();

    await user.type(
      within(dialog).getByTestId('email-change-password').querySelector('input') as HTMLInputElement,
      PASSWORD,
    );
    await user.click(confirm);

    await waitFor(() => expect(bodies).toEqual([{ new_email: NEW_EMAIL, password: PASSWORD }]));
    expect(await screen.findByTestId('email-change-pending')).toHaveTextContent(
      i18n.t('pages.emailChange.pending', { email: NEW_EMAIL }),
    );
    await waitFor(() => expect(screen.queryByTestId('email-change-dialog')).not.toBeInTheDocument());
    expect(newEmailInput().value).toBe('');
    expect(sessionStorage.getItem(EMAIL_CHANGE_ADDRESS_KEY)).toBeNull();
  });

  it('sends the e-mailed code as `step_up_code` for a federated-only account', async () => {
    providers([{ provider: 'github' }]);
    const bodies = captureRequests();
    let codeBody: unknown = null;
    server.use(
      http.post('/api/v1/users/me/step-up-code', async ({ request }) => {
        codeBody = await request.json();
        return HttpResponse.json({ expires_at: '2026-09-26T10:10:00Z', expires_in: 600 }, { status: 202 });
      }),
    );
    const { user, dialog } = await openDialog();

    await user.click(await within(dialog).findByTestId('email-change-send-code'));
    await waitFor(() => expect(codeBody).toEqual({ action: 'email_change' }));
    expect(within(dialog).queryByTestId('email-change-password')).not.toBeInTheDocument();

    await user.type(
      within(dialog).getByTestId('email-change-code').querySelector('input') as HTMLInputElement,
      CODE,
    );
    await user.click(within(dialog).getByTestId('email-change-confirm'));

    await waitFor(() => expect(bodies).toEqual([{ new_email: NEW_EMAIL, step_up_code: CODE }]));
  });

  it('shows the lockout with its minutes inside the dialog on 429 STEP_UP_LOCKED', async () => {
    providers([{ provider: 'local' }]);
    server.use(
      http.post('/api/v1/privacy/email-change', () =>
        errorResponse(429, 'STEP_UP_LOCKED', [
          {
            field: 'password',
            reason: 'Too many failed step-up confirmations.',
            code: 'STEP_UP_LOCKED',
            retry_after_minutes: '15',
          },
        ]),
      ),
    );
    const { user, dialog } = await openDialog();

    await user.type(
      within(dialog).getByTestId('email-change-password').querySelector('input') as HTMLInputElement,
      PASSWORD,
    );
    await user.click(within(dialog).getByTestId('email-change-confirm'));

    expect(await within(dialog).findByTestId('email-change-error')).toHaveTextContent(
      i18n.t('pages.auth.stepUpLocked', { minutes: '15' }),
    );
    expect(screen.queryByTestId('email-change-pending')).not.toBeInTheDocument();
  });

  it('closes the dialog and flags the address on 422', async () => {
    providers([{ provider: 'local' }]);
    server.use(http.post('/api/v1/privacy/email-change', () => errorResponse(422, 'VALIDATION_ERROR')));
    const { user, dialog } = await openDialog('someone@reserved.example');

    await user.type(
      within(dialog).getByTestId('email-change-password').querySelector('input') as HTMLInputElement,
      PASSWORD,
    );
    await user.click(within(dialog).getByTestId('email-change-confirm'));

    await waitFor(() => expect(screen.queryByTestId('email-change-dialog')).not.toBeInTheDocument());
    expect(
      within(screen.getByTestId('email-change-card')).getByText(i18n.t('pages.emailChange.addressRejected')),
    ).toBeInTheDocument();
    expect(screen.queryByTestId('email-change-pending')).not.toBeInTheDocument();
  });

  it('refuses the current address and a malformed one before any step-up', async () => {
    providers([{ provider: 'local' }]);
    const bodies = captureRequests();
    const user = userEvent.setup();
    renderProfileTab();
    await screen.findByTestId('email-change-card');

    await user.type(newEmailInput(), 'Tester@Example.org');
    await user.click(screen.getByTestId('email-change-submit'));
    expect(await screen.findByText(i18n.t('pages.emailChange.sameAsCurrent'))).toBeInTheDocument();

    await user.clear(newEmailInput());
    await user.type(newEmailInput(), 'not-an-address');
    await user.click(screen.getByTestId('email-change-submit'));
    expect(await screen.findByText(i18n.t('pages.emailChange.invalidEmail'))).toBeInTheDocument();

    expect(screen.queryByTestId('email-change-dialog')).not.toBeInTheDocument();
    expect(bodies).toEqual([]);
  });

  it('reopens the dialog after the fresh sign-in and sends the token as `step_up_token`', async () => {
    providers([{ provider: 'google' }]);
    const bodies = captureRequests();
    sessionStorage.setItem(EMAIL_CHANGE_ADDRESS_KEY, NEW_EMAIL);
    storePendingStepUpToken(TOKEN, 'email_change');
    saveStepUpResume({ surface: 'email-change', action: 'email_change', returnPath: '/account' });
    const user = userEvent.setup();
    renderProfileTab();

    const dialog = await screen.findByTestId('email-change-dialog');
    expect(await within(dialog).findByTestId('email-change-reauth-done')).toBeInTheDocument();
    await user.click(within(dialog).getByTestId('email-change-confirm'));

    await waitFor(() => expect(bodies).toEqual([{ new_email: NEW_EMAIL, step_up_token: TOKEN }]));
    expect(await screen.findByTestId('email-change-pending')).toBeInTheDocument();
    // The token is single use, the resume record and the kept address are spent.
    expect(sessionStorage.getItem(STEP_UP_REAUTH_TOKEN_KEY)).toBeNull();
    expect(readStepUpResume()).toBeNull();
    expect(sessionStorage.getItem(EMAIL_CHANGE_ADDRESS_KEY)).toBeNull();
  });

  it('does not reopen the dialog for a resume of another surface', async () => {
    providers([{ provider: 'google' }]);
    sessionStorage.setItem(EMAIL_CHANGE_ADDRESS_KEY, NEW_EMAIL);
    storePendingStepUpToken(TOKEN, 'account_erasure');
    saveStepUpResume({ surface: 'delete-account', action: 'account_erasure', returnPath: '/account' });
    renderProfileTab();

    await screen.findByTestId('email-change-card');
    expect(screen.queryByTestId('email-change-dialog')).not.toBeInTheDocument();
  });
});
