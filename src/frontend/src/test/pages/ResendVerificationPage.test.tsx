import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach } from 'vitest';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';
import ResendVerificationPage from '@/pages/auth/ResendVerificationPage';
import EmailVerificationPage from '@/pages/auth/EmailVerificationPage';
import { renderWithProviders } from '../helpers';
import { server } from '../mocks/server';

/**
 * #2037 — the way to a fresh verification link without signing in first, and the
 * pointer to it from a verification link that no longer works.
 */
describe('ResendVerificationPage', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
  });

  async function submit(email: string) {
    const user = userEvent.setup();
    await user.type(await screen.findByLabelText(/E-Mail/), email);
    await user.click(screen.getByRole('button', { name: 'Neue Bestätigungs-E-Mail senden' }));
  }

  it('posts the address and shows the neutral confirmation', async () => {
    const posted: unknown[] = [];
    server.use(
      http.post('/api/v1/auth/resend-verification', async ({ request }) => {
        posted.push(await request.json());
        return HttpResponse.json({ message: 'accepted' }, { status: 202 });
      }),
    );
    renderWithProviders(<ResendVerificationPage />);

    expect(screen.getByTestId('resend-verification-page')).toBeTruthy();
    expect(screen.getByRole('heading', { level: 1, name: 'Bestätigungslink neu anfordern' })).toBeTruthy();
    await submit('pending@example.com');

    await waitFor(() => {
      expect(screen.getByTestId('resend-verification-status')).toHaveTextContent(/ist ein neuer Link unterwegs/);
    });
    expect(posted).toEqual([{ email: 'pending@example.com' }]);
    expect(screen.getByRole('link', { name: 'Zurück zur Anmeldung' })).toHaveAttribute('href', '/login');
  });

  it('asks the user to wait when the per-IP limit answers 429, keeping the form', async () => {
    server.use(
      http.post('/api/v1/auth/resend-verification', () =>
        HttpResponse.json({ error: 'Rate limit exceeded: 10 per 1 hour' }, { status: 429 }),
      ),
    );
    renderWithProviders(<ResendVerificationPage />);

    await submit('pending@example.com');

    await waitFor(() => {
      expect(screen.getByTestId('resend-verification-status')).toHaveTextContent(/Zu viele Anfragen/);
    });
    expect(screen.getByRole('button', { name: 'Neue Bestätigungs-E-Mail senden' })).toBeEnabled();
  });

  it('reports a failed request instead of claiming success', async () => {
    server.use(
      http.post('/api/v1/auth/resend-verification', () => HttpResponse.json({ detail: 'boom' }, { status: 500 })),
    );
    renderWithProviders(<ResendVerificationPage />);

    await submit('pending@example.com');

    await waitFor(() => {
      expect(screen.getByTestId('resend-verification-status')).toHaveTextContent(/konnte nicht gesendet werden/);
    });
  });
});

describe('EmailVerificationPage error state', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
  });

  it('points an expired link to a fresh one', async () => {
    server.use(
      http.post('/api/v1/auth/verify-email', () =>
        HttpResponse.json(
          {
            error_id: 'e',
            error_code: 'INVALID_TOKEN',
            message: 'Invalid or expired verification token.',
            details: [],
            timestamp: '',
            path: '',
            method: '',
          },
          { status: 401 },
        ),
      ),
    );
    renderWithProviders(<EmailVerificationPage />, { route: '/verify-email/expired-token' });

    const link = await screen.findByTestId('request-new-verification-link');
    expect(link).toHaveAttribute('href', '/resend-verification');
    expect(link).toHaveTextContent('Neuen Bestätigungslink anfordern');
  });
});
