import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { Provider } from 'react-redux';
import { createMemoryRouter, RouterProvider } from 'react-router-dom';
import PublicOnlyRoute from '@/auth/PublicOnlyRoute';
import ProtectedRoute from '@/auth/ProtectedRoute';
import { createTestStore, type TestStore } from '../helpers';

type AuthPreload = {
  user?: unknown;
  accessToken?: string | null;
  isAuthenticated?: boolean;
  isLoading?: boolean;
  error?: string | null;
  initialized?: boolean;
};

function storeWithAuth(auth: AuthPreload): TestStore {
  return createTestStore({
    auth: {
      user: null,
      accessToken: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
      initialized: false,
      ...auth,
    },
  });
}

/**
 * Renders a guard (as a layout route) wrapping a child element, plus a distinct
 * `/login` and `/dashboard` target so redirect destinations are observable.
 */
function renderGuard(
  Guard: typeof PublicOnlyRoute | typeof ProtectedRoute,
  child: React.ReactNode,
  { store, route = '/' }: { store: TestStore; route?: string },
) {
  const router = createMemoryRouter(
    [
      {
        path: '/',
        element: <Guard />,
        children: [{ index: true, element: <>{child}</> }],
      },
      { path: '/login', element: <div>Login target</div> },
      { path: '/dashboard', element: <div>Dashboard target</div> },
    ],
    { initialEntries: [route] },
  );
  return render(
    <Provider store={store}>
      <RouterProvider router={router} />
    </Provider>,
  );
}

describe('PublicOnlyRoute', () => {
  it('shows the loading skeleton while the auth bootstrap has not finished', () => {
    const store = storeWithAuth({ initialized: false });
    renderGuard(PublicOnlyRoute, <div>Login form</div>, { store });

    expect(screen.getByTestId('loading-skeleton')).toBeTruthy();
    expect(screen.queryByText('Login form')).toBeNull();
  });

  it('keeps the child mounted while a login request is in flight (bootstrap done)', () => {
    // The regression: an in-flight login flips isLoading=true. The page must NOT
    // unmount — otherwise its form state and the pending error are lost.
    const store = storeWithAuth({ initialized: true, isLoading: true });
    renderGuard(PublicOnlyRoute, <div>Login form</div>, { store });

    expect(screen.getByText('Login form')).toBeTruthy();
    expect(screen.queryByTestId('loading-skeleton')).toBeNull();
  });

  it('keeps a child-rendered error alert visible after a failed login', () => {
    // Mirrors the post-rejected state: isLoading=false, error set, still on the page.
    const store = storeWithAuth({
      initialized: true,
      isLoading: false,
      error: 'Invalid credentials',
    });
    renderGuard(
      PublicOnlyRoute,
      <div role="alert">Invalid credentials</div>,
      { store },
    );

    expect(screen.getByRole('alert').textContent).toContain('Invalid credentials');
  });

  it('redirects an authenticated visitor to the dashboard', () => {
    const store = storeWithAuth({ initialized: true, isAuthenticated: true });
    renderGuard(PublicOnlyRoute, <div>Login form</div>, { store });

    expect(screen.getByText('Dashboard target')).toBeTruthy();
    expect(screen.queryByText('Login form')).toBeNull();
  });
});

describe('ProtectedRoute', () => {
  it('shows the skeleton (no redirect flash) until the bootstrap finishes', () => {
    const store = storeWithAuth({ initialized: false });
    renderGuard(ProtectedRoute, <div>Protected content</div>, { store });

    expect(screen.getByTestId('loading-skeleton')).toBeTruthy();
    // No premature redirect to /login while we still do not know the session state.
    expect(screen.queryByText('Login target')).toBeNull();
  });

  it('redirects to /login once bootstrap is done and the visitor is unauthenticated', () => {
    const store = storeWithAuth({ initialized: true, isAuthenticated: false });
    renderGuard(ProtectedRoute, <div>Protected content</div>, { store });

    expect(screen.getByText('Login target')).toBeTruthy();
    expect(screen.queryByText('Protected content')).toBeNull();
  });

  it('renders the protected content for an authenticated visitor', () => {
    const store = storeWithAuth({ initialized: true, isAuthenticated: true });
    renderGuard(ProtectedRoute, <div>Protected content</div>, { store });

    expect(screen.getByText('Protected content')).toBeTruthy();
  });

  it('does not bounce to the skeleton for an in-flight request post-bootstrap', () => {
    // A background profile refetch flips isLoading=true; an authenticated user
    // must keep seeing content, not the bootstrap skeleton.
    const store = storeWithAuth({
      initialized: true,
      isAuthenticated: true,
      isLoading: true,
    });
    renderGuard(ProtectedRoute, <div>Protected content</div>, { store });

    expect(screen.getByText('Protected content')).toBeTruthy();
    expect(screen.queryByTestId('loading-skeleton')).toBeNull();
  });
});
