import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import type { ReactElement } from 'react';
import { render, screen, waitFor, cleanup } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Provider } from 'react-redux';
import { createMemoryRouter, RouterProvider } from 'react-router-dom';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';
import { server } from '@/test/mocks/server';
import { createTestStore, authState } from '@/test/helpers';
import type { TestStore } from '@/test/helpers';
import { ThemeContextProvider } from '@/theme';
import EmailChangeConfirmPage from '@/pages/auth/EmailChangeConfirmPage';
import EmailChangeRevertPage from '@/pages/auth/EmailChangeRevertPage';

/**
 * #1848 — the landings of the two links in the e-mail-change mails.
 *
 * Neither page may post on load — mail scanners prefetch links:
 * - `/email-change/:token` (mail to the new address) confirms only after a click;
 *   a scanner at the new address would otherwise let someone squat a stranger's
 *   address by moving their own account onto it.
 * - `/email-change/revert/:token` (notice to the previous address) restores the
 *   previous address only after a click.
 */

const TOKEN = ['tok', 'en', '1848'].join('-');

function errorResponse(status: number, errorCode: string, path: string) {
  return HttpResponse.json(
    {
      error_id: 'err',
      error_code: errorCode,
      message: 'Backend English message.',
      details: [],
      timestamp: '',
      path,
      method: 'POST',
    },
    { status },
  );
}

function renderAt(path: string, route: string, element: ReactElement, store: TestStore) {
  const router = createMemoryRouter(
    [
      { path, element },
      { path: '/login', element: <div data-testid="login-page" /> },
      { path: '/password-reset', element: <div data-testid="password-reset-page" /> },
    ],
    { initialEntries: [route] },
  );
  return render(
    <Provider store={store}>
      <ThemeContextProvider>
        <RouterProvider router={router} />
      </ThemeContextProvider>
    </Provider>,
  );
}

describe('EmailChangeConfirmPage (#1848)', () => {
  beforeEach(() => i18n.changeLanguage('de'));
  afterEach(() => cleanup());

  function renderConfirm(store: TestStore = createTestStore(authState())) {
    renderAt('/email-change/:token', `/email-change/${TOKEN}`, <EmailChangeConfirmPage />, store);
    return store;
  }

  it('explains the confirmation and does not post before the click', async () => {
    let calls = 0;
    server.use(
      http.post('/api/v1/privacy/email-change/confirm', () => {
        calls += 1;
        return HttpResponse.json({ message: 'ok' });
      }),
    );
    renderConfirm();

    expect(await screen.findByTestId('email-change-confirm-btn')).toBeEnabled();
    expect(screen.getByText(i18n.t('pages.emailChange.confirmStepAddress'))).toBeInTheDocument();
    expect(screen.getByText(i18n.t('pages.emailChange.confirmStepSignOut'))).toBeInTheDocument();
    // Give a stray on-load request every chance to land before asserting its absence.
    await new Promise((resolve) => setTimeout(resolve, 50));
    expect(calls).toBe(0);
  });

  it('confirms on click, signs the local session out and links to the login', async () => {
    const bodies: unknown[] = [];
    server.use(
      http.post('/api/v1/privacy/email-change/confirm', async ({ request }) => {
        bodies.push(await request.json());
        return HttpResponse.json({ message: 'Email address has been updated.' });
      }),
    );
    const store = renderConfirm();
    const user = userEvent.setup();

    await user.click(await screen.findByTestId('email-change-confirm-btn'));

    expect(await screen.findByTestId('email-change-confirm-success')).toHaveTextContent(
      i18n.t('pages.emailChange.confirmSuccess'),
    );
    expect(screen.getByText(i18n.t('pages.emailChange.confirmSignedOut'))).toBeInTheDocument();
    expect(bodies).toEqual([{ token: TOKEN }]);
    // Every session was revoked server-side; the in-memory one must not linger.
    expect(store.getState().auth.isAuthenticated).toBe(false);
    expect(screen.queryByTestId('email-change-confirm-btn')).not.toBeInTheDocument();

    await user.click(screen.getByTestId('email-change-login-btn'));
    expect(await screen.findByTestId('login-page')).toBeInTheDocument();
  });

  it('says the link is invalid on 401 INVALID_TOKEN and keeps the session', async () => {
    server.use(
      http.post('/api/v1/privacy/email-change/confirm', () =>
        errorResponse(401, 'INVALID_TOKEN', '/api/v1/privacy/email-change/confirm'),
      ),
    );
    const store = renderConfirm();

    await userEvent.setup().click(await screen.findByTestId('email-change-confirm-btn'));

    expect(await screen.findByTestId('email-change-confirm-error')).toHaveTextContent(
      i18n.t('pages.emailChange.confirmInvalid'),
    );
    // Never the backend's English message.
    expect(screen.queryByText('Backend English message.')).not.toBeInTheDocument();
    expect(store.getState().auth.isAuthenticated).toBe(true);
    expect(screen.queryByTestId('email-change-confirm-btn')).not.toBeInTheDocument();
    expect(screen.getByTestId('email-change-login-btn')).toBeInTheDocument();
  });

  it('keeps the button for a retry after an unexpected failure', async () => {
    server.use(
      http.post('/api/v1/privacy/email-change/confirm', () =>
        errorResponse(500, 'INTERNAL_ERROR', '/api/v1/privacy/email-change/confirm'),
      ),
    );
    renderConfirm(createTestStore());

    await userEvent.setup().click(await screen.findByTestId('email-change-confirm-btn'));

    expect(await screen.findByTestId('email-change-confirm-error')).toHaveTextContent(
      i18n.t('pages.emailChange.confirmFailed'),
    );
    await waitFor(() => expect(screen.getByTestId('email-change-confirm-btn')).toBeEnabled());
  });
});

describe('EmailChangeRevertPage (#1848)', () => {
  beforeEach(() => i18n.changeLanguage('de'));
  afterEach(() => cleanup());

  function renderRevert(store: TestStore = createTestStore(authState())) {
    renderAt('/email-change/revert/:token', `/email-change/revert/${TOKEN}`, <EmailChangeRevertPage />, store);
    return store;
  }

  it('explains the revert and does not post before the click', async () => {
    let calls = 0;
    server.use(
      http.post('/api/v1/privacy/email-change/revert', () => {
        calls += 1;
        return HttpResponse.json({ message: 'ok' });
      }),
    );
    renderRevert();

    expect(await screen.findByTestId('email-change-revert-btn')).toBeEnabled();
    expect(screen.getByText(i18n.t('pages.emailChange.revertStepRestore'))).toBeInTheDocument();
    expect(screen.getByText(i18n.t('pages.emailChange.revertStepSignOut'))).toBeInTheDocument();
    expect(screen.getByText(i18n.t('pages.emailChange.revertStepResetLinks'))).toBeInTheDocument();
    // Give a stray on-load request every chance to land before asserting its absence.
    await new Promise((resolve) => setTimeout(resolve, 50));
    expect(calls).toBe(0);
  });

  it('restores the previous address on click, signs the session out and advises a password reset', async () => {
    const bodies: unknown[] = [];
    server.use(
      http.post('/api/v1/privacy/email-change/revert', async ({ request }) => {
        bodies.push(await request.json());
        return HttpResponse.json({ message: 'restored' });
      }),
    );
    const store = renderRevert();

    await userEvent.setup().click(await screen.findByTestId('email-change-revert-btn'));

    expect(await screen.findByTestId('email-change-revert-success')).toHaveTextContent(
      i18n.t('pages.emailChange.revertSuccess'),
    );
    expect(screen.getByText(i18n.t('pages.emailChange.revertResetAdvice'))).toBeInTheDocument();
    expect(screen.getByTestId('email-change-revert-reset-btn')).toHaveAttribute('href', '/password-reset');
    expect(bodies).toEqual([{ token: TOKEN }]);
    expect(store.getState().auth.isAuthenticated).toBe(false);
    expect(screen.queryByTestId('email-change-revert-btn')).not.toBeInTheDocument();
  });

  it('says the link is invalid, used or expired on 401 INVALID_TOKEN', async () => {
    server.use(
      http.post('/api/v1/privacy/email-change/revert', () =>
        errorResponse(401, 'INVALID_TOKEN', '/api/v1/privacy/email-change/revert'),
      ),
    );
    const store = renderRevert();

    await userEvent.setup().click(await screen.findByTestId('email-change-revert-btn'));

    expect(await screen.findByTestId('email-change-revert-error')).toHaveTextContent(
      i18n.t('pages.emailChange.revertInvalid'),
    );
    expect(store.getState().auth.isAuthenticated).toBe(true);
    expect(screen.queryByTestId('email-change-revert-btn')).not.toBeInTheDocument();
  });

  it('tells the user to contact the operator on 422 (previous address taken)', async () => {
    server.use(
      http.post('/api/v1/privacy/email-change/revert', () =>
        errorResponse(422, 'VALIDATION_ERROR', '/api/v1/privacy/email-change/revert'),
      ),
    );
    renderRevert();

    await userEvent.setup().click(await screen.findByTestId('email-change-revert-btn'));

    expect(await screen.findByTestId('email-change-revert-error')).toHaveTextContent(
      i18n.t('pages.emailChange.revertConflict'),
    );
    expect(screen.queryByText('Backend English message.')).not.toBeInTheDocument();
  });

  it('keeps the button for a retry after an unexpected failure', async () => {
    server.use(
      http.post('/api/v1/privacy/email-change/revert', () =>
        errorResponse(500, 'INTERNAL_ERROR', '/api/v1/privacy/email-change/revert'),
      ),
    );
    renderRevert();

    await userEvent.setup().click(await screen.findByTestId('email-change-revert-btn'));

    expect(await screen.findByTestId('email-change-revert-error')).toHaveTextContent(
      i18n.t('pages.emailChange.revertFailed'),
    );
    await waitFor(() => expect(screen.getByTestId('email-change-revert-btn')).toBeEnabled());
  });
});
