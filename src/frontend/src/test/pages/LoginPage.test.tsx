import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';
import LoginPage from '@/pages/auth/LoginPage';
import { renderWithProviders, createTestStore } from '../helpers';
import { server } from '../mocks/server';

/** Auth store seeded so the login button is enabled (initial state has isLoading=true). */
function idleAuthStore() {
  return createTestStore({
    auth: {
      user: null,
      accessToken: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
      initialized: true,
    },
  });
}

describe('LoginPage', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
  });

  it('renders the login form with email and password fields', async () => {
    renderWithProviders(<LoginPage />, { store: idleAuthStore() });

    expect(await screen.findByLabelText(/E-Mail/)).toBeTruthy();
    expect(screen.getByLabelText(/Passwort/)).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Anmelden' })).toBeTruthy();
  });

  it('shows a spinner and disables submit while a login is in flight', async () => {
    const store = createTestStore({
      auth: {
        user: null,
        accessToken: null,
        isAuthenticated: false,
        isLoading: true,
        error: null,
        initialized: true,
      },
    });
    renderWithProviders(<LoginPage />, { store });

    // The submit button keeps its accessible name while loading (the spinner is
    // a decorative, aria-hidden startIcon, not a replacement for the label).
    const submit = screen.getByRole('button', { name: 'Anmelden' });
    expect(submit).toBeDisabled();
    expect(submit.querySelector('.MuiCircularProgress-root')).toBeTruthy();
  });

  it('renders an error alert after a failed login attempt', async () => {
    // The page clears any pre-existing error on mount, so the error must arise
    // from an actual failed login dispatch rather than from preloaded state.
    server.use(
      http.post('/api/v1/auth/login', () =>
        HttpResponse.json(
          { error_id: 'e', error_code: 'INVALID_CREDENTIALS', message: 'bad creds', details: [], timestamp: '', path: '', method: '' },
          { status: 401 },
        ),
      ),
    );
    const user = userEvent.setup();
    renderWithProviders(<LoginPage />, { store: idleAuthStore() });

    await user.type(await screen.findByLabelText(/E-Mail/), 'demo@kamerplanter.local');
    await user.type(screen.getByLabelText(/Passwort/), 'wrong');
    await user.click(screen.getByRole('button', { name: 'Anmelden' }));

    await waitFor(() => {
      expect(screen.getByRole('alert')).toBeTruthy();
    });
  });

  it('updates the remember-me checkbox on toggle', async () => {
    const user = userEvent.setup();
    renderWithProviders(<LoginPage />, { store: idleAuthStore() });

    const checkbox = await screen.findByRole('checkbox');
    expect(checkbox).not.toBeChecked();
    await user.click(checkbox);
    expect(checkbox).toBeChecked();
  });

  it('submits credentials and authenticates the user', async () => {
    const user = userEvent.setup();
    const store = idleAuthStore();
    renderWithProviders(<LoginPage />, { store });

    await user.type(await screen.findByLabelText(/E-Mail/), 'demo@kamerplanter.local');
    await user.type(screen.getByLabelText(/Passwort/), 'secret');
    await user.click(screen.getByRole('button', { name: 'Anmelden' }));

    await waitFor(() => {
      expect(store.getState().auth.isAuthenticated).toBe(true);
    });
  });

  it('renders OAuth provider buttons when providers are configured', async () => {
    server.use(
      http.get('/api/v1/auth/oauth/providers', () =>
        HttpResponse.json([{ slug: 'google', display_name: 'Google', icon_url: null }]),
      ),
    );
    renderWithProviders(<LoginPage />, { store: idleAuthStore() });

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Google/ })).toBeTruthy();
    });
  });

  it('surfaces a warning when the OAuth provider list fails to load (FE-L3)', async () => {
    server.use(
      http.get('/api/v1/auth/oauth/providers', () =>
        HttpResponse.json({ detail: 'boom' }, { status: 500 }),
      ),
    );
    renderWithProviders(<LoginPage />, { store: idleAuthStore() });

    // A failed optional load must be visible, not a silent empty list.
    await waitFor(() => {
      expect(screen.getByText(/Alternative Anmeldeoptionen.*konnten nicht geladen werden/)).toBeTruthy();
    });
    // The password login form remains fully usable.
    expect(screen.getByRole('button', { name: 'Anmelden' })).toBeTruthy();
  });

  it('URL-encodes the provider slug when starting the OAuth flow (FE-S4)', async () => {
    server.use(
      http.get('/api/v1/auth/oauth/providers', () =>
        HttpResponse.json([{ slug: 'a/b?c#d', display_name: 'Weird', icon_url: null }]),
      ),
    );

    const user = userEvent.setup();
    renderWithProviders(<LoginPage />, { store: idleAuthStore() });
    // Wait for the provider to load with the real window.location so axios can
    // resolve the relative request URL, THEN stub only the href setter.
    const providerButton = await screen.findByRole('button', { name: /Weird/ });

    const hrefSetter = vi.fn();
    const originalLocation = window.location;
    Object.defineProperty(window, 'location', {
      configurable: true,
      value: {
        ...originalLocation,
        get href() {
          return '';
        },
        set href(value: string) {
          hrefSetter(value);
        },
      },
    });

    try {
      await user.click(providerButton);
      expect(hrefSetter).toHaveBeenCalledWith('/api/v1/auth/oauth/a%2Fb%3Fc%23d');
    } finally {
      Object.defineProperty(window, 'location', {
        configurable: true,
        value: originalLocation,
      });
    }
  });

  it('offers a link to the registration page', async () => {
    renderWithProviders(<LoginPage />, { store: idleAuthStore() });
    const card = await screen.findByText('E-Mail');
    expect(within(card.ownerDocument.body).getByText('Noch kein Konto? Registrieren')).toBeTruthy();
  });
});
