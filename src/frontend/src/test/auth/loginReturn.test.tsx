/**
 * UI-NFR-014 R-009…R-011 (#2899, REQ-053 GP-UX-028): a page opened without a session survives the sign-in.
 *
 * Measured before the fix: `ProtectedRoute` sent every unauthenticated visitor to a bare `/login` and the sign-in went
 * to the dashboard, so a bed label's QR code (`/standorte/sites/:key/plan?mode=field&bed=:key`) scanned on a phone
 * without a session landed on the dashboard. Now the login URL names the page (`?returnTo=`), the sign-in continues
 * there, and only a same-origin app path is ever followed.
 */
import { cleanup, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import i18n from 'i18next';
import { Provider } from 'react-redux';
import { createMemoryRouter, RouterProvider } from 'react-router-dom';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import ProtectedRoute from '@/auth/ProtectedRoute';
import PublicOnlyRoute from '@/auth/PublicOnlyRoute';
import LoginPage from '@/pages/auth/LoginPage';
import { logoutUser } from '@/store/slices/authSlice';
import {
  forgetLoginReturn,
  loginPathFor,
  rememberLoginReturn,
  rememberedLoginReturn,
  safeReturnTo,
} from '@/utils/loginReturn';
import { postLoginPath } from '@/utils/pendingInvitation';
import { createTestStore } from '../helpers';

const BED_LINK = '/standorte/sites/site_1/plan?mode=field&bed=bed_7';

function authStore(isAuthenticated: boolean) {
  return createTestStore({
    auth: { user: null, accessToken: null, isAuthenticated, isLoading: false, error: null, initialized: true },
  });
}

function renderApp(entry: string, isAuthenticated: boolean) {
  const router = createMemoryRouter(
    [
      {
        element: <ProtectedRoute />,
        children: [
          { path: '/standorte/sites/:key/plan', element: <p data-testid="field-mode">field mode</p> },
          { path: '/dashboard', element: <p data-testid="dashboard">dashboard</p> },
        ],
      },
      { element: <PublicOnlyRoute />, children: [{ path: '/login', element: <LoginPage /> }] },
    ],
    { initialEntries: [entry] },
  );
  const store = authStore(isAuthenticated);
  render(
    <Provider store={store}>
      <RouterProvider router={router} />
    </Provider>,
  );
  return { router, store };
}

beforeEach(() => {
  i18n.changeLanguage('de');
  sessionStorage.clear();
});
afterEach(() => {
  cleanup();
  sessionStorage.clear();
});

describe('return to the page asked for after the sign-in (UI-NFR-014 R-009/R-010)', () => {
  it('names the bed deep link in the login URL when there is no session', async () => {
    const { router } = renderApp(BED_LINK, false);

    expect(await screen.findByTestId('login-return-hint')).toBeInTheDocument();
    expect(router.state.location.pathname).toBe('/login');
    expect(new URLSearchParams(router.state.location.search).get('returnTo')).toBe(BED_LINK);
  });

  it('signs in and opens the bed in field mode, not the dashboard', async () => {
    const { router } = renderApp(BED_LINK, false);
    await screen.findByTestId('login-return-hint');

    await userEvent.type(screen.getByLabelText(/E-Mail/), 'gaertner@example.org');
    await userEvent.type(screen.getByLabelText(/Passwort/), 'geheim-genug');
    await userEvent.click(screen.getByRole('button', { name: 'Anmelden' }));

    expect(await screen.findByTestId('field-mode')).toBeInTheDocument();
    expect(`${router.state.location.pathname}${router.state.location.search}`).toBe(BED_LINK);
    // Arrived: the path kept for an identity-provider sign-in is forgotten.
    await waitFor(() => expect(rememberedLoginReturn()).toBeNull());
  });

  it('sends a session restored on the login page straight on to the page', async () => {
    const { router } = renderApp(`/login?returnTo=${encodeURIComponent(BED_LINK)}`, true);

    await screen.findByTestId('field-mode');
    expect(router.state.location.search).toBe('?mode=field&bed=bed_7');
  });

  it('keeps the path for a sign-in with an identity provider, which comes back on another page', async () => {
    renderApp(BED_LINK, false);
    await screen.findByTestId('login-return-hint');

    // `OAuthCallbackPage` asks `postLoginPath()` without the login page's query.
    expect(postLoginPath()).toBe(BED_LINK);
  });

  it('opens the plain login without a hint for the start page, and forgets a stale path there', async () => {
    rememberLoginReturn('/standorte/sites/old/plan');
    const { router } = renderApp('/dashboard', false);

    await screen.findByRole('button', { name: 'Anmelden' });
    expect(router.state.location.search).toBe('?returnTo=%2Fdashboard');
    cleanup();

    renderApp('/login', false);
    await screen.findByRole('button', { name: 'Anmelden' });
    expect(screen.queryByTestId('login-return-hint')).toBeNull();
    await waitFor(() => expect(rememberedLoginReturn()).toBeNull());
  });

  it('forgets the path on sign-out', async () => {
    rememberLoginReturn(BED_LINK);

    await authStore(true).dispatch(logoutUser());

    expect(rememberedLoginReturn()).toBeNull();
  });
});

describe('only a same-origin app path is followed (UI-NFR-014 R-011)', () => {
  it.each([
    ['https://evil.example/standorte', null],
    ['//evil.example/standorte', null],
    ['/.//evil.example/x', null],
    ['/..//evil.example', null],
    ['/%2e%2e//evil.example', null],
    ['/%2e//evil.example', null],
    ['/a/../..//evil.example', null],
    ['/\\evil.example', null],
    ['javascript:alert(1)', null],
    ['standorte/sites/x', null],
    ['/login?returnTo=%2Fdashboard', null],
    ['/auth/callback?code=x', null],
    ['/', null],
    ['/standorte/sites/s/plan\nX', null],
    [BED_LINK, BED_LINK],
    ['/pflanzen/plant-instances/p1#care', '/pflanzen/plant-instances/p1#care'],
  ])('safeReturnTo(%j) is %j', (raw, expected) => {
    expect(safeReturnTo(raw)).toBe(expected);
  });

  it('never follows a hostile returnTo after the sign-in', async () => {
    const { router } = renderApp(`/login?returnTo=${encodeURIComponent('//evil.example/x')}`, true);

    await screen.findByTestId('dashboard');
    expect(router.state.location.pathname).toBe('/dashboard');
  });

  it('builds the plain login for a page nothing returns to', () => {
    expect(loginPathFor({ pathname: '/', search: '' })).toBe('/login');
    expect(loginPathFor({ pathname: '/standorte/sites/s1/plan', search: '?mode=field&bed=b1' })).toBe(
      '/login?returnTo=%2Fstandorte%2Fsites%2Fs1%2Fplan%3Fmode%3Dfield%26bed%3Db1',
    );
    forgetLoginReturn();
  });
});
