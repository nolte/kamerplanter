import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach } from 'vitest';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';
import RegisterPage from '@/pages/auth/RegisterPage';
import { renderWithProviders, createTestStore } from '../helpers';
import { server } from '../mocks/server';

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

function registrationMode(mode: 'open' | 'invite_only' | 'closed', domainRestricted = false) {
  server.use(
    http.get('/api/v1/mode', () =>
      HttpResponse.json({
        mode: 'full',
        features: { auth: true, multi_tenant: true, privacy_consent: true },
        registration: { mode, domain_restricted: domainRestricted },
      }),
    ),
  );
}

/** Captures the body of `POST /auth/register`; answers with the given refusal or a 201. */
function captureRegister(refusal?: { code: string; status: number }) {
  const bodies: Record<string, unknown>[] = [];
  server.use(
    http.post('/api/v1/auth/register', async ({ request }) => {
      const body = (await request.json()) as Record<string, unknown>;
      bodies.push(body);
      if (refusal) {
        return HttpResponse.json(
          {
            error_id: 'e',
            error_code: refusal.code,
            message: 'Registration is not open for this address.',
            details: [],
            timestamp: '',
            path: '',
            method: '',
          },
          { status: refusal.status },
        );
      }
      return HttpResponse.json({ key: 'u-new', email: body.email, display_name: body.display_name }, { status: 201 });
    }),
  );
  return bodies;
}

function input(testId: string): HTMLInputElement {
  const field = screen.getByTestId(testId).querySelector('input');
  if (!field) throw new Error(`no input in ${testId}`);
  return field;
}

async function fillForm(user: ReturnType<typeof userEvent.setup>) {
  await screen.findByTestId('register-submit');
  await user.type(input('form-field-display-name'), 'Neu');
  await user.type(input('form-field-email'), 'neu@example.org');
  await user.type(input('form-field-password'), 'ein-langes-passwort');
  await user.type(input('form-field-confirm-password'), 'ein-langes-passwort');
}

describe('RegisterPage (#2132)', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
  });

  it('offers the form without an invitation field when registration is open', async () => {
    registrationMode('open');
    renderWithProviders(<RegisterPage />, { store: idleAuthStore(), route: '/register' });

    expect(await screen.findByTestId('register-submit')).toBeTruthy();
    expect(screen.queryByTestId('form-field-invitation-token')).toBeNull();
    expect(screen.queryByTestId('registration-closed')).toBeNull();
  });

  it('hides the form and explains a closed instance, with the way to the login', async () => {
    registrationMode('closed');
    renderWithProviders(<RegisterPage />, { store: idleAuthStore(), route: '/register' });

    expect(await screen.findByTestId('registration-closed')).toHaveTextContent(/keine neuen Konten/);
    expect(screen.queryByTestId('register-submit')).toBeNull();
    expect(screen.getByTestId('register-login-link')).toBeTruthy();
  });

  it('asks for the invitation code when invite-only and sends it with the registration', async () => {
    registrationMode('invite_only');
    const bodies = captureRegister();
    const user = userEvent.setup();
    renderWithProviders(<RegisterPage />, { store: idleAuthStore(), route: '/register' });

    expect(await screen.findByTestId('registration-invite-only')).toBeTruthy();
    await fillForm(user);
    const submit = screen.getByTestId('register-submit');
    expect(submit).toBeDisabled(); // the code is required in this mode

    await user.type(input('form-field-invitation-token'), 'the-invitation-token');
    expect(submit).not.toBeDisabled();
    await user.click(submit);

    await waitFor(() => expect(bodies).toHaveLength(1));
    expect(bodies[0].invitation_token).toBe('the-invitation-token');
  });

  it('prefills the invitation code from the link', async () => {
    registrationMode('invite_only');
    renderWithProviders(<RegisterPage />, { store: idleAuthStore(), route: '/register?invitation=from-the-link' });

    expect(await screen.findByLabelText(/Einladungscode/)).toHaveValue('from-the-link');
  });

  it('shows a refused registration in the user language, not the backend sentence', async () => {
    registrationMode('invite_only');
    captureRegister({ code: 'REGISTRATION_NOT_ALLOWED', status: 403 });
    const user = userEvent.setup();
    renderWithProviders(<RegisterPage />, { store: idleAuthStore(), route: '/register?invitation=wrong' });

    await fillForm(user);
    await user.click(screen.getByTestId('register-submit'));

    expect(await screen.findByTestId('registration-refused')).toHaveTextContent(/keine Registrierung möglich/);
    expect(screen.queryByText('Registration is not open for this address.')).toBeNull();
  });

  it('sends no invitation token when none was entered in open mode', async () => {
    registrationMode('open');
    const bodies = captureRegister();
    const user = userEvent.setup();
    renderWithProviders(<RegisterPage />, { store: idleAuthStore(), route: '/register' });

    await fillForm(user);
    await user.click(screen.getByTestId('register-submit'));

    await waitFor(() => expect(bodies).toHaveLength(1));
    expect('invitation_token' in bodies[0]).toBe(false);
  });

  it('mentions the domain restriction and offers the invitation field in open mode with an allowlist', async () => {
    registrationMode('open', true);
    renderWithProviders(<RegisterPage />, { store: idleAuthStore(), route: '/register' });

    expect(await screen.findByTestId('registration-domain-restricted')).toBeTruthy();
    expect(screen.getByTestId('form-field-invitation-token')).toBeTruthy();
    expect(screen.getByTestId('register-submit')).toBeTruthy();
  });

  it('falls back to the form when the mode cannot be read; the backend still decides', async () => {
    server.use(http.get('/api/v1/mode', () => new HttpResponse(null, { status: 503 })));
    renderWithProviders(<RegisterPage />, { store: idleAuthStore(), route: '/register' });

    expect(await screen.findByTestId('register-submit')).toBeTruthy();
  });

  it('renders in English', async () => {
    await i18n.changeLanguage('en');
    registrationMode('closed');
    renderWithProviders(<RegisterPage />, { store: idleAuthStore(), route: '/register' });

    expect(await screen.findByTestId('registration-closed')).toHaveTextContent(/New accounts cannot be created/);
  });
});
