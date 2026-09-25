import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { screen, waitFor, within, cleanup } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';
import { server } from '@/test/mocks/server';
import { renderWithProviders, createTestStore, authState } from '@/test/helpers';
import AccountSettingsPage from '@/pages/auth/AccountSettingsPage';

/**
 * #1813 / #1816 — deleting the own account asks for a step-up.
 *
 * `DELETE /users/me` opens the Art. 17 erasure request (the account is closed at
 * once and hard-deleted after the grace period). The backend refuses the request
 * unless its body echoes the account's own e-mail (422) and, for an account with
 * a local password, carries the current password (401); too many failed
 * confirmations answer 429 `STEP_UP_LOCKED` with the wait in minutes. The page
 * used to confirm through `window.confirm` and send no body at all — after the
 * backend change it could only fail.
 */

const OWN_EMAIL = 'tester@example.org';

function lockedResponse(minutes: string) {
  return HttpResponse.json(
    {
      error_id: 'err_lock',
      error_code: 'STEP_UP_LOCKED',
      message: `Too many failed confirmations. Try again in ${minutes} minutes.`,
      details: [
        {
          field: 'password',
          reason: 'Too many failed step-up confirmations.',
          code: 'STEP_UP_LOCKED',
          retry_after_minutes: minutes,
        },
      ],
      timestamp: '',
      path: '/api/v1/users/me',
      method: 'DELETE',
    },
    { status: 429 },
  );
}

function providers(list: { provider: string }[]) {
  server.use(
    http.get('/api/v1/users/me/providers', () =>
      HttpResponse.json(
        list.map((p, i) => ({ key: `prov-${i}`, provider: p.provider, provider_email: OWN_EMAIL })),
      ),
    ),
  );
}

function renderAccountTab(route = '/account#account') {
  return renderWithProviders(<AccountSettingsPage />, { store: createTestStore(authState()), route });
}

async function openDeleteDialog() {
  const user = userEvent.setup();
  renderAccountTab();
  await user.click(await screen.findByTestId('delete-account-btn'));
  const dialog = await screen.findByTestId('delete-account-dialog');
  return { user, dialog };
}

function emailInput(dialog: HTMLElement): HTMLInputElement {
  return within(dialog).getByTestId('delete-account-email').querySelector('input') as HTMLInputElement;
}

let originalLocation: Location;

describe('AccountSettingsPage — account deletion step-up (#1813)', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
    originalLocation = window.location;
    Object.defineProperty(window, 'location', {
      configurable: true,
      value: { ...originalLocation, href: 'http://localhost/account' },
    });
  });

  afterEach(() => {
    cleanup();
    Object.defineProperty(window, 'location', { configurable: true, value: originalLocation });
    vi.restoreAllMocks();
  });

  it('opens a step-up dialog instead of window.confirm', async () => {
    providers([{ provider: 'local' }]);
    const confirmSpy = vi.spyOn(window, 'confirm');
    const { dialog } = await openDeleteDialog();

    expect(confirmSpy).not.toHaveBeenCalled();
    expect(within(dialog).getByTestId('delete-account-confirm')).toBeDisabled();
  });

  it('sends the own e-mail echo and the current password, then leaves for the login page', async () => {
    providers([{ provider: 'local' }]);
    let body: unknown = null;
    server.use(
      http.delete('/api/v1/users/me', async ({ request }) => {
        body = await request.json();
        return HttpResponse.json({ message: 'ok' });
      }),
    );
    const { user, dialog } = await openDeleteDialog();

    // The e-mail echo is compared case-insensitively.
    await user.type(emailInput(dialog), 'Tester@Example.org');
    await user.type(within(dialog).getByLabelText(/passwort/i), 'my-password');
    await user.click(within(dialog).getByTestId('delete-account-confirm'));

    await waitFor(() => expect(body).toEqual({ confirm_email: 'Tester@Example.org', password: 'my-password' }));
    await waitFor(() => expect(window.location.href).toBe('/login'));
  });

  it('keeps the confirm button disabled while the echo is not the own e-mail', async () => {
    providers([{ provider: 'local' }]);
    const { user, dialog } = await openDeleteDialog();

    await user.type(emailInput(dialog), 'someone@else.org');
    await user.type(within(dialog).getByLabelText(/passwort/i), 'my-password');
    expect(within(dialog).getByTestId('delete-account-confirm')).toBeDisabled();
  });

  it('still asks for the password when the account lists no provider at all', async () => {
    providers([]);
    const { user, dialog } = await openDeleteDialog();

    await user.type(emailInput(dialog), OWN_EMAIL);
    expect(within(dialog).getByLabelText(/passwort/i)).toBeInTheDocument();
    expect(within(dialog).getByTestId('delete-account-confirm')).toBeDisabled();
  });

  it('shows the lockout with its minutes inside the dialog on 429 STEP_UP_LOCKED', async () => {
    providers([{ provider: 'local' }]);
    server.use(http.delete('/api/v1/users/me', () => lockedResponse('15')));
    const { user, dialog } = await openDeleteDialog();

    await user.type(emailInput(dialog), OWN_EMAIL);
    await user.type(within(dialog).getByLabelText(/passwort/i), 'wrong');
    await user.click(within(dialog).getByTestId('delete-account-confirm'));

    const error = await within(dialog).findByTestId('delete-account-error');
    expect(error).toHaveTextContent(i18n.t('pages.auth.stepUpLocked', { minutes: '15' }));
    expect(error).toHaveTextContent('15 Minuten');
    expect(screen.getByTestId('delete-account-dialog')).toBeInTheDocument();
  });

  it('describes the deletion truthfully: closed now, erased after the grace period', async () => {
    providers([{ provider: 'local' }]);
    renderAccountTab();
    const description = await screen.findByText(i18n.t('pages.auth.deleteAccountDescription'));
    expect(description.textContent).toMatch(/sofort/i);
    expect(description.textContent).toMatch(/Frist/i);
  });
});

describe('AccountSettingsPage — password change lockout (#1816)', () => {
  beforeEach(() => i18n.changeLanguage('de'));
  afterEach(() => cleanup());

  it('shows the translated lockout message on 429 STEP_UP_LOCKED', async () => {
    providers([{ provider: 'local' }]);
    server.use(http.post('/api/v1/users/me/password', () => lockedResponse('7')));
    const user = userEvent.setup();
    renderAccountTab('/account#security');

    const current = (await screen.findByTestId('current-password-field')).querySelector('input') as HTMLInputElement;
    const next = screen.getByTestId('new-password-field').querySelector('input') as HTMLInputElement;
    await user.type(current, 'old-secret');
    await user.type(next, 'new-secret-123');
    await user.click(screen.getByTestId('change-password-btn'));

    expect(await screen.findByText(i18n.t('pages.auth.stepUpLocked', { minutes: '7' }))).toBeInTheDocument();
  });
});
