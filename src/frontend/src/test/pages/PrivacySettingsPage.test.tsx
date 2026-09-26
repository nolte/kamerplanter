import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';
import PrivacySettingsPage from '@/pages/auth/PrivacySettingsPage';
import { renderWithProviders, createTestStore, authState } from '../helpers';
import { server } from '../mocks/server';

/** The erasure dialog echoes the signed-in account's own e-mail (#1813). */
const OWN_EMAIL = 'tester@example.org';

function renderErasurePage() {
  return renderWithProviders(<PrivacySettingsPage />, { store: createTestStore(authState()) });
}

function localProvider() {
  return http.get('/api/v1/users/me/providers', () =>
    HttpResponse.json([
      {
        key: 'prov-1',
        provider: 'local',
        provider_email: OWN_EMAIL,
        provider_display_name: null,
        linked_at: '2024-01-01T00:00:00Z',
        last_used_at: null,
      },
    ]),
  );
}

async function typeEmailEcho(user: ReturnType<typeof userEvent.setup>, value = OWN_EMAIL) {
  const field = (await screen.findByTestId('privacy-erasure-email')).querySelector('input') as HTMLInputElement;
  await user.type(field, value);
}

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

  it('tells the user why a failed export delivered nothing (#1645)', async () => {
    server.use(
      http.post('/api/v1/privacy/export', () =>
        HttpResponse.json({
          key: 'exp-1',
          status: 'failed',
          requested_at: '2024-01-01T00:00:00Z',
          completed_at: null,
          error_message: 'object storage is not configured',
        }),
      ),
    );
    const user = userEvent.setup();
    renderWithProviders(<PrivacySettingsPage />);

    await user.click(await screen.findByTestId('privacy-tab-export'));
    await user.click(await screen.findByTestId('privacy-export-request-btn'));

    const result = await screen.findByTestId('privacy-export-result');
    // The reason, not just a red box: the panel used to render `severity=success`
    // and the bare status word whatever had happened.
    expect(result.textContent).toContain('object storage is not configured');
    expect(screen.queryByTestId('privacy-export-download-btn')).toBeNull();
  });

  it('says why an expired export shows no download (#1662 SCR-009)', async () => {
    server.use(
      http.post('/api/v1/privacy/export', () =>
        HttpResponse.json({ key: 'exp-1', status: 'expired', requested_at: null, completed_at: null }),
      ),
    );
    const user = userEvent.setup();
    renderWithProviders(<PrivacySettingsPage />);

    await user.click(await screen.findByTestId('privacy-tab-export'));
    await user.click(await screen.findByTestId('privacy-export-request-btn'));

    const result = await screen.findByTestId('privacy-export-result');
    expect(result.textContent).toContain('72');
    expect(screen.queryByTestId('privacy-export-download-btn')).toBeNull();
    // The way forward stays available: the request button is still there.
    expect(screen.getByTestId('privacy-export-request-btn')).toBeTruthy();
  });

  it('hands the completed export bundle to the browser (#1645)', async () => {
    const bundle = JSON.stringify({ sections: [{ collection: 'users', records: [{ email: 'x@example.invalid' }] }] });
    let downloadRequested = false;
    server.use(
      http.post('/api/v1/privacy/export', () =>
        HttpResponse.json({ key: 'exp-1', status: 'pending', requested_at: null, completed_at: null }),
      ),
      http.get('/api/v1/privacy/export/exp-1', () =>
        HttpResponse.json({
          key: 'exp-1',
          status: 'completed',
          requested_at: null,
          completed_at: '2024-01-02T00:00:00Z',
          file_size_bytes: bundle.length,
        }),
      ),
      http.get('/api/v1/privacy/export/exp-1/download', () => {
        downloadRequested = true;
        return new HttpResponse(bundle, { headers: { 'Content-Type': 'application/json' } });
      }),
    );
    // jsdom has no object-URL support. Patch the two methods rather than
    // replacing the global `URL`: spreading the class drops its constructor,
    // which breaks every other test in the file that builds a URL.
    const createObjectURL = vi.fn((_blob: Blob) => 'blob:export');
    const urlApi = URL as unknown as Record<string, unknown>;
    const originalCreate = urlApi.createObjectURL;
    const originalRevoke = urlApi.revokeObjectURL;
    urlApi.createObjectURL = createObjectURL;
    urlApi.revokeObjectURL = vi.fn();
    // jsdom cannot navigate to a blob: URL; the click is the hand-over to the
    // browser, so it is recorded instead of performed.
    const anchorClick = vi
      .spyOn(HTMLAnchorElement.prototype, 'click')
      .mockImplementation(() => undefined);

    const user = userEvent.setup();
    renderWithProviders(<PrivacySettingsPage />);

    await user.click(await screen.findByTestId('privacy-tab-export'));
    await user.click(await screen.findByTestId('privacy-export-request-btn'));
    // The request starts `pending`, so the panel offers a refresh rather than
    // claiming success - the defect being repaired is exactly a surface that
    // reported success without a payload.
    await user.click(await screen.findByTestId('privacy-export-refresh-btn'));
    await user.click(await screen.findByTestId('privacy-export-download-btn'));

    try {
      // `downloadRequested` flips inside the MSW handler, i.e. when the request
      // *arrives*; the response still has to travel back through the MSW XHR
      // interceptor and axios and be read as a Blob before the component
      // reaches `URL.createObjectURL`. Asserting on the mock right after that
      // flag certifies only that a request was sent, so the wait is anchored
      // on the hand-over itself, which is also the #1645 claim: the bundle
      // bytes, not just a request, reach the browser. (The CI-only failure of
      // this test on Node 22 was that the blob response never left the
      // interceptor at all - see the `Blob.prototype.stream` note in setup.ts.)
      await waitFor(() => {
        expect(anchorClick).toHaveBeenCalledTimes(1);
      });
      expect(downloadRequested).toBe(true);
      expect(createObjectURL).toHaveBeenCalledTimes(1);
      const handedOver = createObjectURL.mock.calls[0][0];
      expect(handedOver).toBeInstanceOf(Blob);
      expect(await handedOver.text()).toBe(bundle);
      const anchor = anchorClick.mock.instances[0] as HTMLAnchorElement;
      expect(anchor.href).toBe('blob:export');
      expect(anchor.download).toBe('kamerplanter-export-exp-1.json');
    } finally {
      anchorClick.mockRestore();
      urlApi.createObjectURL = originalCreate;
      urlApi.revokeObjectURL = originalRevoke;
    }
  });

  it('confirms erasure of a federated account with the e-mailed code instead of a password (#1815)', async () => {
    let sentBody: { password?: string; confirm_email?: string; step_up_code?: string } | undefined;
    let codeBody: unknown = null;
    const code = ['9', '8', '7', '6', '5', '4'].join('');
    server.use(
      http.post('/api/v1/users/me/step-up-code', async ({ request }) => {
        codeBody = await request.json();
        return HttpResponse.json({ expires_at: '2026-09-25T12:10:00Z', expires_in: 600 }, { status: 202 });
      }),
      http.get('/api/v1/users/me/providers', () =>
        HttpResponse.json([
          {
            key: 'prov-g',
            provider: 'github',
            provider_email: OWN_EMAIL,
            provider_display_name: null,
            linked_at: '2024-01-01T00:00:00Z',
            last_used_at: null,
          },
        ]),
      ),
      http.post('/api/v1/privacy/erasure', async ({ request }) => {
        sentBody = (await request.json()) as { password?: string; confirm_email?: string; step_up_code?: string };
        return new HttpResponse(null, { status: 202 });
      }),
    );

    const user = userEvent.setup();
    renderErasurePage();

    await user.click(await screen.findByTestId('privacy-tab-erasure'));
    await user.click(await screen.findByTestId('privacy-erasure-request-btn'));
    await screen.findByTestId('privacy-erasure-dialog');
    await typeEmailEcho(user);

    // Once the provider list resolves as federated (fail-closed lifts), the
    // password field gives way to the e-mailed code, which the confirm needs.
    const confirmBtn = await screen.findByTestId('privacy-erasure-confirm-btn');
    const codeInput = (await screen.findByTestId('privacy-erasure-code')).querySelector('input') as HTMLInputElement;
    expect(screen.queryByTestId('privacy-erasure-password')).toBeNull();
    expect(confirmBtn).toBeDisabled();
    await user.click(screen.getByTestId('privacy-erasure-send-code'));
    // The code is requested for the account erasure only (review SEC-003).
    await waitFor(() => expect(codeBody).toEqual({ action: 'account_erasure' }));
    await user.type(codeInput, code);
    await waitFor(() => expect(confirmBtn).not.toBeDisabled());

    await user.click(confirmBtn);

    await waitFor(() => {
      expect(screen.getByText(i18n.t('pages.privacy.erasureRequested'))).toBeTruthy();
    });
    // Federated accounts send the echo and the code, no password.
    expect(sentBody).toEqual({ confirm_email: OWN_EMAIL, step_up_code: code });
  });

  it('keeps the password field when the account lists no provider at all (fail closed)', async () => {
    // Seeded accounts carry a password hash without a `local` provider row, so
    // an empty list is "unknown", not "federated" (#1791 SEC-003).
    const user = userEvent.setup();
    renderErasurePage();

    await user.click(await screen.findByTestId('privacy-tab-erasure'));
    await user.click(await screen.findByTestId('privacy-erasure-request-btn'));
    await typeEmailEcho(user);

    expect(await screen.findByTestId('privacy-erasure-password')).toBeTruthy();
    expect(screen.getByTestId('privacy-erasure-confirm-btn')).toBeDisabled();
  });

  it('keeps the confirm button disabled until the own e-mail is typed back', async () => {
    server.use(localProvider());
    const user = userEvent.setup();
    renderErasurePage();

    await user.click(await screen.findByTestId('privacy-tab-erasure'));
    await user.click(await screen.findByTestId('privacy-erasure-request-btn'));
    const passwordField = within(await screen.findByTestId('privacy-erasure-password')).getByLabelText(/passwort/i);
    await user.type(passwordField, 'demo-passwort-2024');
    const confirmBtn = screen.getByTestId('privacy-erasure-confirm-btn');
    expect(confirmBtn).toBeDisabled();

    await typeEmailEcho(user, 'TESTER@example.org');
    await waitFor(() => expect(confirmBtn).not.toBeDisabled());
  });

  it('shows the lockout with its minutes inside the dialog on 429 STEP_UP_LOCKED', async () => {
    server.use(
      localProvider(),
      http.post('/api/v1/privacy/erasure', () =>
        HttpResponse.json(
          {
            error_id: 'e',
            error_code: 'STEP_UP_LOCKED',
            message: 'Too many failed confirmations. Try again in 15 minutes.',
            details: [{ field: 'password', reason: 'locked', code: 'STEP_UP_LOCKED', retry_after_minutes: '15' }],
            timestamp: '',
            path: '',
            method: '',
          },
          { status: 429 },
        ),
      ),
    );
    const user = userEvent.setup();
    renderErasurePage();

    await user.click(await screen.findByTestId('privacy-tab-erasure'));
    await user.click(await screen.findByTestId('privacy-erasure-request-btn'));
    await typeEmailEcho(user);
    await user.type(within(await screen.findByTestId('privacy-erasure-password')).getByLabelText(/passwort/i), 'x');
    await user.click(screen.getByTestId('privacy-erasure-confirm-btn'));

    expect(await screen.findByTestId('privacy-erasure-dialog-error')).toHaveTextContent(
      i18n.t('pages.auth.stepUpLocked', { minutes: '15' }),
    );
    expect(screen.getByTestId('privacy-erasure-dialog')).toBeTruthy();
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
    let sentBody: unknown;
    server.use(
      http.post('/api/v1/privacy/erasure', async ({ request }) => {
        sentBody = await request.json();
        return new HttpResponse(null, { status: 202 });
      }),
    );

    const user = userEvent.setup();
    renderErasurePage();

    await user.click(await screen.findByTestId('privacy-tab-erasure'));
    await user.click(await screen.findByTestId('privacy-erasure-request-btn'));
    await typeEmailEcho(user);

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
    expect(sentBody).toEqual({ confirm_email: OWN_EMAIL, password: 'demo-passwort-2024' });
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
    renderErasurePage();

    await user.click(await screen.findByTestId('privacy-tab-erasure'));
    await user.click(await screen.findByTestId('privacy-erasure-request-btn'));
    await typeEmailEcho(user);

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
