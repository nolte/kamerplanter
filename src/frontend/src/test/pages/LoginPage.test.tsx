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

  describe('unverified address (#2037)', () => {
    function refuseAsUnverified() {
      server.use(
        http.post('/api/v1/auth/login', () =>
          HttpResponse.json(
            {
              error_id: 'e',
              error_code: 'EMAIL_NOT_VERIFIED',
              message: 'Email address has not been verified.',
              details: [],
              timestamp: '',
              path: '',
              method: '',
            },
            { status: 403 },
          ),
        ),
      );
    }

    async function signIn(user: ReturnType<typeof userEvent.setup>, email = 'pending@example.com') {
      await user.type(await screen.findByLabelText(/E-Mail/), email);
      await user.type(screen.getByLabelText(/Passwort/), 'correct-password');
      await user.click(screen.getByRole('button', { name: 'Anmelden' }));
    }

    it('names the way out instead of the backend text and offers the resend', async () => {
      refuseAsUnverified();
      const user = userEvent.setup();
      renderWithProviders(<LoginPage />, { store: idleAuthStore() });

      await signIn(user);

      const hint = await screen.findByTestId('login-email-not-verified');
      expect(hint).toHaveTextContent(/noch nicht bestätigt/);
      expect(screen.queryByText('Email address has not been verified.')).toBeNull();
      expect(screen.getByRole('button', { name: 'Neue Bestätigungs-E-Mail senden' })).toBeEnabled();
    });

    it('promises the link the refusal mails conditionally and never states it as sent (#2046)', async () => {
      refuseAsUnverified();
      const user = userEvent.setup();
      renderWithProviders(<LoginPage />, { store: idleAuthStore() });

      await signIn(user);

      const hint = await screen.findByTestId('login-email-not-verified');
      // The refusal answers alike whether a link went out, the budget was spent or
      // the delivery failed — so the text can only promise, conditionally.
      expect(hint).toHaveTextContent(/Falls ein neuer Bestätigungslink fällig war, ist er jetzt an deine Adresse unterwegs/);
      expect(hint).not.toHaveTextContent(/wurde (gesendet|verschickt)|haben wir (dir )?gesendet/);
      // Announced as it appears, and the anonymous resend stays as the fallback.
      expect(hint).toHaveAttribute('role', 'alert');
      expect(screen.getByRole('button', { name: 'Neue Bestätigungs-E-Mail senden' })).toBeEnabled();
      expect(screen.getByTestId('resend-verification-status')).toHaveAttribute('aria-live', 'polite');
    });

    it('requests a new link for the address that was refused and announces the neutral answer', async () => {
      refuseAsUnverified();
      const posted: unknown[] = [];
      server.use(
        http.post('/api/v1/auth/resend-verification', async ({ request }) => {
          posted.push(await request.json());
          return HttpResponse.json({ message: 'accepted' }, { status: 202 });
        }),
      );
      const user = userEvent.setup();
      renderWithProviders(<LoginPage />, { store: idleAuthStore() });
      await signIn(user);

      // Editing the field afterwards must not redirect the resend to another address.
      await user.type(screen.getByLabelText(/E-Mail/), 'x');
      await user.click(await screen.findByRole('button', { name: 'Neue Bestätigungs-E-Mail senden' }));

      await waitFor(() => {
        expect(screen.getByRole('status')).toHaveTextContent(/ist ein neuer Link unterwegs/);
      });
      expect(posted).toEqual([{ email: 'pending@example.com' }]);
      expect(screen.getByRole('button', { name: 'Neue Bestätigungs-E-Mail senden' })).toBeDisabled();
    });

    it('tells the user to wait when the per-IP limit answers 429', async () => {
      refuseAsUnverified();
      server.use(
        http.post('/api/v1/auth/resend-verification', () =>
          HttpResponse.json({ error: 'Rate limit exceeded: 10 per 1 hour' }, { status: 429 }),
        ),
      );
      const user = userEvent.setup();
      renderWithProviders(<LoginPage />, { store: idleAuthStore() });
      await signIn(user);

      await user.click(await screen.findByRole('button', { name: 'Neue Bestätigungs-E-Mail senden' }));

      await waitFor(() => {
        expect(screen.getByRole('status')).toHaveTextContent(/Zu viele Anfragen/);
      });
      expect(screen.getByRole('button', { name: 'Neue Bestätigungs-E-Mail senden' })).toBeEnabled();
    });

    it('keeps the generic error for every other refusal', async () => {
      server.use(
        http.post('/api/v1/auth/login', () =>
          HttpResponse.json(
            { error_id: 'e', error_code: 'UNAUTHORIZED', message: 'Invalid email or password.', details: [], timestamp: '', path: '', method: '' },
            { status: 401 },
          ),
        ),
      );
      const user = userEvent.setup();
      renderWithProviders(<LoginPage />, { store: idleAuthStore() });
      await signIn(user);

      expect(await screen.findByText('Invalid email or password.')).toBeTruthy();
      expect(screen.queryByTestId('login-email-not-verified')).toBeNull();
      expect(screen.queryByRole('button', { name: 'Neue Bestätigungs-E-Mail senden' })).toBeNull();
    });
  });

  it('offers a link to the registration page', async () => {
    renderWithProviders(<LoginPage />, { store: idleAuthStore() });
    const card = await screen.findByText('E-Mail');
    // The entry follows the registration mode, read from `GET /mode` (#2132) — so it appears once that answered.
    expect(await within(card.ownerDocument.body).findByText('Noch kein Konto? Registrieren')).toBeTruthy();
  });
});

describe('LoginPage registration entry (#2132)', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
  });

  function registrationMode(mode: 'open' | 'invite_only' | 'closed') {
    server.use(
      http.get('/api/v1/mode', () =>
        HttpResponse.json({
          mode: 'full',
          features: { auth: true, multi_tenant: true, privacy_consent: true },
          registration: { mode, domain_restricted: false },
        }),
      ),
    );
  }

  it('offers the registration link when registration is open', async () => {
    registrationMode('open');
    renderWithProviders(<LoginPage />, { store: idleAuthStore() });

    expect(await screen.findByTestId('login-register-link')).toHaveTextContent('Noch kein Konto? Registrieren');
  });

  it('labels the link as registration with an invitation when invite-only', async () => {
    registrationMode('invite_only');
    renderWithProviders(<LoginPage />, { store: idleAuthStore() });

    await waitFor(() => {
      expect(screen.getByTestId('login-register-link')).toHaveTextContent(/Mit Einladung registrieren/);
    });
  });

  it('hides the registration link and says so when registration is closed', async () => {
    registrationMode('closed');
    renderWithProviders(<LoginPage />, { store: idleAuthStore() });

    expect(await screen.findByTestId('login-registration-closed')).toBeTruthy();
    expect(screen.queryByTestId('login-register-link')).toBeNull();
    expect(screen.getByRole('link', { name: /Passwort vergessen/ })).toBeTruthy();
  });
});
