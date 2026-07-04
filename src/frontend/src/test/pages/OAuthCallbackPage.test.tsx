import { screen, waitFor } from '@testing-library/react';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';
import OAuthCallbackPage from '@/pages/auth/OAuthCallbackPage';
import { renderWithProviders, createTestStore } from '../helpers';
import { server } from '../mocks/server';

const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom');
  return { ...actual, useNavigate: () => mockNavigate };
});

function callbackStore() {
  return createTestStore({
    auth: {
      user: null,
      accessToken: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
    },
  });
}

describe('OAuthCallbackPage', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
    mockNavigate.mockClear();
  });

  it('completes login via the cookie refresh flow and navigates to the dashboard', async () => {
    // Default MSW handlers: POST /auth/refresh -> { access_token } and GET /users/me -> profile.
    const store = callbackStore();
    renderWithProviders(<OAuthCallbackPage />, { store, route: '/auth/callback' });

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/dashboard', { replace: true });
    });
    // The access token comes from the cookie-based refresh, never from the URL.
    expect(store.getState().auth.accessToken).toBe('jwt-refreshed');
  });

  it('shows a localised session-failed message when the refresh fails', async () => {
    server.use(
      http.post('/api/v1/auth/refresh', () => new HttpResponse(null, { status: 401 })),
    );
    renderWithProviders(<OAuthCallbackPage />, { store: callbackStore(), route: '/auth/callback' });

    await waitFor(() => {
      expect(screen.getByRole('alert')).toHaveTextContent(/nicht abgeschlossen werden/i);
    });
    expect(mockNavigate).not.toHaveBeenCalledWith('/dashboard', { replace: true });
  });

  it('maps a whitelisted error code to a localised message without calling refresh', async () => {
    let refreshCalled = false;
    server.use(
      http.post('/api/v1/auth/refresh', () => {
        refreshCalled = true;
        return HttpResponse.json({ access_token: 'x', token_type: 'bearer' });
      }),
    );
    renderWithProviders(<OAuthCallbackPage />, {
      store: callbackStore(),
      route: '/auth/callback?error=access_denied',
    });

    await waitFor(() => {
      expect(screen.getByRole('alert')).toHaveTextContent(/beim Anbieter abgebrochen/i);
    });
    expect(refreshCalled).toBe(false);
    // A "back to login" escape hatch must be offered in the error state.
    expect(screen.getByRole('button', { name: /Anmeldung/i })).toBeTruthy();
  });

  it('never renders an unknown/attacker error param raw and falls back to the generic message', async () => {
    const attacker = '<script>alert(1)</script>';
    renderWithProviders(<OAuthCallbackPage />, {
      store: callbackStore(),
      route: `/auth/callback?error=${encodeURIComponent(attacker)}`,
    });

    await waitFor(() => {
      expect(screen.getByRole('alert')).toHaveTextContent(/ein Fehler aufgetreten/i);
    });
    // The raw attacker string must not appear anywhere in the DOM.
    expect(screen.queryByText(attacker)).toBeNull();
  });

  it('ignores an access_token injected via the URL and uses the cookie refresh instead', async () => {
    const store = callbackStore();
    renderWithProviders(<OAuthCallbackPage />, {
      store,
      route: '/auth/callback?access_token=evil-injected-token',
    });

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/dashboard', { replace: true });
    });
    // The injected token must never reach the store.
    expect(store.getState().auth.accessToken).toBe('jwt-refreshed');
    expect(store.getState().auth.accessToken).not.toBe('evil-injected-token');
  });
});
