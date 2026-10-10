import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { render, screen, cleanup } from '@testing-library/react';
import { Provider } from 'react-redux';
import { createMemoryRouter, RouterProvider } from 'react-router-dom';
import i18n from 'i18next';
import ProtectedRoute from '@/auth/ProtectedRoute';
import PublicOnlyRoute from '@/auth/PublicOnlyRoute';
import LoginPage from '@/pages/auth/LoginPage';
import InvitationAcceptPage from '@/pages/tenants/InvitationAcceptPage';
import {
  forgetPendingInvitation,
  pendingInvitationToken,
  postLoginPath,
  rememberPendingInvitation,
} from '@/utils/pendingInvitation';
import { createTestStore, renderWithProviders } from '../helpers';

/**
 * #2162 — an invitation link opened without a session survives the sign-in.
 *
 * `/invitations/accept?token=…` is protected; the redirect to `/login` dropped the token, and the
 * sign-in went to the dashboard: whoever followed an invitation mail without a session never
 * joined. The route guard now remembers the token, the sign-in continues at the accept page, and
 * the accept page forgets the token once it has it.
 */

function authStore(isAuthenticated: boolean) {
  return createTestStore({
    auth: { user: null, accessToken: null, isAuthenticated, isLoading: false, error: null, initialized: true },
  });
}

function renderRoutes(entry: string, isAuthenticated: boolean) {
  const router = createMemoryRouter(
    [
      { element: <ProtectedRoute />, children: [{ path: '/invitations/accept', element: <p>accept page</p> }] },
      {
        element: <PublicOnlyRoute />,
        children: [{ path: '/login', element: <p data-testid="login">login</p> }],
      },
      { path: '/dashboard', element: <p>dashboard</p> },
    ],
    { initialEntries: [entry] },
  );
  render(
    <Provider store={authStore(isAuthenticated)}>
      <RouterProvider router={router} />
    </Provider>,
  );
  return router;
}

describe('pending invitation across the sign-in (#2162)', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
    sessionStorage.clear();
  });
  afterEach(() => {
    cleanup();
    sessionStorage.clear();
  });

  it('remembers the token when an unauthenticated visitor is sent to the login', async () => {
    const router = renderRoutes('/invitations/accept?token=tok%2F2162', false);

    expect(await screen.findByTestId('login')).toBeInTheDocument();
    expect(router.state.location.pathname).toBe('/login');
    expect(pendingInvitationToken()).toBe('tok/2162');
    expect(postLoginPath()).toBe('/invitations/accept?token=tok%2F2162');
  });

  it('remembers nothing for any other protected page', () => {
    renderRoutes('/invitations/accept', false);

    expect(pendingInvitationToken()).toBeNull();
    expect(postLoginPath()).toBe('/dashboard');
  });

  it('sends a visitor who is already signed in from the login back to the invitation', async () => {
    rememberPendingInvitation('tok-2162');

    const router = renderRoutes('/login', true);

    await screen.findByText('accept page');
    expect(router.state.location.search).toBe('?token=tok-2162');
  });

  it('says on the login page that an invitation waits, and hands it to the registration', async () => {
    rememberPendingInvitation('tok-2162');

    renderWithProviders(<LoginPage />, { store: authStore(false), route: '/login' });

    expect(await screen.findByTestId('login-pending-invitation')).toHaveTextContent('Einladung');
    expect(screen.getByTestId('login-register-link')).toHaveAttribute('href', '/register?invitation=tok-2162');
  });

  it('shows no invitation hint without a pending invitation', async () => {
    renderWithProviders(<LoginPage />, { store: authStore(false), route: '/login' });

    expect(await screen.findByTestId('login-register-link')).toHaveAttribute('href', '/register');
    expect(screen.queryByTestId('login-pending-invitation')).toBeNull();
  });

  it('forgets the token once the accept page has it', () => {
    rememberPendingInvitation('tok-2162');

    renderWithProviders(<InvitationAcceptPage />, { route: '/invitations/accept?token=tok-2162' });

    expect(pendingInvitationToken()).toBeNull();
    expect(postLoginPath()).toBe('/dashboard');
  });

  it('forgets on request', () => {
    rememberPendingInvitation('tok-2162');
    forgetPendingInvitation();

    expect(pendingInvitationToken()).toBeNull();
  });
});
