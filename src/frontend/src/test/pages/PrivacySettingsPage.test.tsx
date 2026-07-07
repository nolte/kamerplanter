import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach } from 'vitest';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';
import PrivacySettingsPage from '@/pages/auth/PrivacySettingsPage';
import { renderWithProviders } from '../helpers';
import { server } from '../mocks/server';

describe('PrivacySettingsPage', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
    server.use(
      http.get('/api/v1/privacy/consents', () =>
        HttpResponse.json([
          {
            purpose: 'analytics',
            label: 'Analyse',
            description: 'Analytische Daten zur Produktverbesserung',
            legal_basis: 'consent',
            required: false,
            granted: false,
            granted_at: null,
            revoked_at: null,
          },
        ]),
      ),
    );
  });

  it('renders the page title and four privacy tabs', async () => {
    renderWithProviders(<PrivacySettingsPage />);
    await waitFor(() => {
      expect(screen.getByTestId('privacy-settings-page')).toBeTruthy();
    });
    expect(screen.getByTestId('privacy-tab-consents')).toBeTruthy();
    expect(screen.getByTestId('privacy-tab-export')).toBeTruthy();
    expect(screen.getByTestId('privacy-tab-erasure')).toBeTruthy();
    expect(screen.getByTestId('privacy-tab-restrict')).toBeTruthy();
  });

  it('loads and displays consents on the default tab', async () => {
    renderWithProviders(<PrivacySettingsPage />);
    await waitFor(() => {
      expect(screen.getByText('Analyse')).toBeTruthy();
    });
    expect(screen.getByTestId('privacy-consents-list')).toBeTruthy();
  });

  it('shows a consent-loading error from the backend', async () => {
    server.use(
      http.get('/api/v1/privacy/consents', () =>
        HttpResponse.json(
          { error_id: 'e', error_code: 'INTERNAL', message: 'boom', details: [], timestamp: '', path: '', method: '' },
          { status: 500 },
        ),
      ),
    );
    renderWithProviders(<PrivacySettingsPage />);
    await waitFor(() => {
      expect(screen.getByRole('alert')).toBeTruthy();
    });
  });

  it('requests a data export and surfaces the resulting status', async () => {
    const user = userEvent.setup();
    renderWithProviders(<PrivacySettingsPage />);

    await user.click(await screen.findByTestId('privacy-tab-export'));
    await user.click(await screen.findByTestId('privacy-export-request-btn'));

    expect(await screen.findByTestId('privacy-export-result')).toBeTruthy();
  });

  it('confirms erasure without a password for federated accounts and sends an empty body', async () => {
    // Default providers mock returns no local provider → password-less flow.
    let sentBody: { password?: string } | undefined;
    server.use(
      http.post('/api/v1/privacy/erasure', async ({ request }) => {
        sentBody = (await request.json()) as { password?: string };
        return new HttpResponse(null, { status: 202 });
      }),
    );

    const user = userEvent.setup();
    renderWithProviders(<PrivacySettingsPage />);

    await user.click(await screen.findByTestId('privacy-tab-erasure'));
    await user.click(await screen.findByTestId('privacy-erasure-request-btn'));
    await screen.findByTestId('privacy-erasure-dialog');

    // Once the provider list resolves as federated (fail-closed lifts), the
    // confirm button enables without a password and no password field is shown.
    const confirmBtn = await screen.findByTestId('privacy-erasure-confirm-btn');
    await waitFor(() => expect(confirmBtn).not.toBeDisabled());
    expect(screen.queryByTestId('privacy-erasure-password')).toBeNull();

    await user.click(confirmBtn);

    await waitFor(() => {
      expect(screen.getByText(i18n.t('pages.privacy.erasureRequested'))).toBeTruthy();
    });
    // Federated accounts must not send a password field.
    expect(sentBody?.password).toBeUndefined();
  });

  it('fails closed and shows the password field when the provider load fails', async () => {
    // A transient provider-load failure must not hide the password field for a
    // (possibly local) account, otherwise the backend would reject with 401 and
    // the user would have no field to supply the password (issue #394).
    server.use(
      http.get('/api/v1/users/me/providers', () =>
        HttpResponse.json(
          { error_id: 'e', error_code: 'INTERNAL', message: 'boom', details: [], timestamp: '', path: '', method: '' },
          { status: 500 },
        ),
      ),
    );

    const user = userEvent.setup();
    renderWithProviders(<PrivacySettingsPage />);

    await user.click(await screen.findByTestId('privacy-tab-erasure'));
    await user.click(await screen.findByTestId('privacy-erasure-request-btn'));

    // Password field is present (fail-closed) and confirm is disabled until filled.
    expect(await screen.findByTestId('privacy-erasure-password')).toBeTruthy();
    expect(await screen.findByTestId('privacy-erasure-confirm-btn')).toBeDisabled();
  });

  it('requires and sends the current password for local-password accounts', async () => {
    server.use(
      http.get('/api/v1/users/me/providers', () =>
        HttpResponse.json([
          {
            key: 'prov-1',
            provider: 'local',
            provider_email: 'demo@kamerplanter.local',
            provider_display_name: null,
            linked_at: '2024-01-01T00:00:00Z',
            last_used_at: null,
          },
        ]),
      ),
    );
    let sentPassword: string | undefined;
    server.use(
      http.post('/api/v1/privacy/erasure', async ({ request }) => {
        const body = (await request.json()) as { password?: string };
        sentPassword = body.password;
        return new HttpResponse(null, { status: 202 });
      }),
    );

    const user = userEvent.setup();
    renderWithProviders(<PrivacySettingsPage />);

    await user.click(await screen.findByTestId('privacy-tab-erasure'));
    await user.click(await screen.findByTestId('privacy-erasure-request-btn'));

    // Password field is shown and the confirm button is disabled until filled.
    const passwordField = within(await screen.findByTestId('privacy-erasure-password')).getByLabelText(
      /passwort/i,
    );
    const confirmBtn = await screen.findByTestId('privacy-erasure-confirm-btn');
    expect(confirmBtn).toBeDisabled();

    await user.type(passwordField, 'demo-passwort-2024');
    await waitFor(() => expect(confirmBtn).not.toBeDisabled());

    await user.click(confirmBtn);

    await waitFor(() => {
      expect(screen.getByText(i18n.t('pages.privacy.erasureRequested'))).toBeTruthy();
    });
    expect(sentPassword).toBe('demo-passwort-2024');
  });

  it('shows the backend authorisation error and keeps the dialog open on a wrong password', async () => {
    server.use(
      http.get('/api/v1/users/me/providers', () =>
        HttpResponse.json([
          {
            key: 'prov-1',
            provider: 'local',
            provider_email: 'demo@kamerplanter.local',
            provider_display_name: null,
            linked_at: '2024-01-01T00:00:00Z',
            last_used_at: null,
          },
        ]),
      ),
      http.post('/api/v1/privacy/erasure', () =>
        HttpResponse.json(
          {
            error_id: 'e',
            error_code: 'UNAUTHORIZED',
            message: 'Password confirmation failed.',
            details: [],
            timestamp: '',
            path: '',
            method: '',
          },
          { status: 401 },
        ),
      ),
    );

    const user = userEvent.setup();
    renderWithProviders(<PrivacySettingsPage />);

    await user.click(await screen.findByTestId('privacy-tab-erasure'));
    await user.click(await screen.findByTestId('privacy-erasure-request-btn'));

    const passwordField = within(await screen.findByTestId('privacy-erasure-password')).getByLabelText(
      /passwort/i,
    );
    await user.type(passwordField, 'wrong-password');
    await user.click(await screen.findByTestId('privacy-erasure-confirm-btn'));

    // Error is surfaced inside the dialog and the dialog stays open.
    expect(await screen.findByTestId('privacy-erasure-dialog-error')).toBeTruthy();
    expect(screen.getByTestId('privacy-erasure-dialog')).toBeTruthy();
    expect(screen.getByTestId('privacy-erasure-password')).toBeTruthy();
  });

  it('shows an inline validation error when submitting an empty password via Enter', async () => {
    server.use(
      http.get('/api/v1/users/me/providers', () =>
        HttpResponse.json([
          {
            key: 'prov-1',
            provider: 'local',
            provider_email: 'demo@kamerplanter.local',
            provider_display_name: null,
            linked_at: '2024-01-01T00:00:00Z',
            last_used_at: null,
          },
        ]),
      ),
    );

    const user = userEvent.setup();
    renderWithProviders(<PrivacySettingsPage />);

    await user.click(await screen.findByTestId('privacy-tab-erasure'));
    await user.click(await screen.findByTestId('privacy-erasure-request-btn'));

    const passwordField = within(await screen.findByTestId('privacy-erasure-password')).getByLabelText(
      /passwort/i,
    );
    // Enter with an empty field bypasses the disabled confirm button and must
    // surface the client-side validation error rather than a silent 401.
    await user.click(passwordField);
    await user.keyboard('{Enter}');

    expect(await screen.findByTestId('privacy-erasure-dialog-error')).toHaveTextContent(
      i18n.t('pages.privacy.erasurePasswordRequired'),
    );
  });

  it('validates the restriction scope before submitting', async () => {
    const user = userEvent.setup();
    renderWithProviders(<PrivacySettingsPage />);

    await user.click(await screen.findByTestId('privacy-tab-restrict'));
    // Submit button is disabled until a scope is entered
    const submitBtn = await screen.findByTestId('privacy-restrict-submit-btn');
    expect(submitBtn).toBeDisabled();

    const scopeField = within(await screen.findByTestId('privacy-restrict-scope')).getByRole('textbox');
    await user.type(scopeField, 'sensor_data');
    await waitFor(() => expect(submitBtn).not.toBeDisabled());

    await user.click(submitBtn);
    // Created restriction is appended to the list
    await waitFor(() => {
      expect(screen.getByText('sensor_data')).toBeTruthy();
    });
  });
});
