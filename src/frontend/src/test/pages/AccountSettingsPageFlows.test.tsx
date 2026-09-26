import { describe, it, expect, beforeEach, vi } from 'vitest';
import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { server } from '@/test/mocks/server';
import { renderWithProviders, createTestStore } from '@/test/helpers';
import AccountSettingsPage from '@/pages/auth/AccountSettingsPage';

/**
 * REQ-029 Phase 1 — broader AccountSettingsPage coverage.
 *
 * AccountSettingsPlantnet.test.tsx focuses on the Pl@ntNet key flows; this suite
 * exercises the surrounding tabs and the Home-Assistant handlers that share the
 * same Integrations tab the Pl@ntNet section lives in, plus the API-key, session
 * and danger-zone flows — the branch-heavy handlers added/touched alongside the
 * plant-identification feature.
 */

const AUTH_USER = {
  // #1385 put the installation-wide HA and Pl@ntNet cards behind the
  // platform-admin gate, on both sides. These suites drive exactly those
  // cards, so their user is the caller who may reach them. The refusal for
  // everyone else has its own test in AccountSettingsInstanceGating.test.tsx.
  is_platform_admin: true,
  key: 'user-1',
  display_name: 'Tester',
  email: 'tester@example.org',
  locale: 'de',
  timezone: 'Europe/Berlin',
};

function storeWithUser(smartHomeEnabled = false) {
  return createTestStore({
    auth: {
      user: AUTH_USER,
      accessToken: 'tok',
      isAuthenticated: true,
      isLoading: false,
      error: null,
    },
    userPreferences: {
      preferences: {
        key: 'pref-1',
        user_key: 'user-1',
        experience_level: 'expert',
        onboarding_completed: true,
        locale: 'de',
        theme: 'light',
        watering_can_liters: 5,
        smart_home_enabled: smartHomeEnabled,
      },
      loading: false,
      error: null,
    },
  });
}

const HA_BASE = {
  ha_url: '',
  ha_access_token_masked: '',
  ha_timeout: 10,
  source_ha_url: 'default',
  source_ha_access_token: 'default',
  source_ha_timeout: 'default',
};

const SETTINGS = {
  home_assistant: HA_BASE,
  plant_identification: { plantnet_api_key_masked: '', source_plantnet_api_key: 'none' },
};

const PROVIDERS = [
  { key: 'prov-1', provider: 'local', provider_email: 'tester@example.org' },
  { key: 'prov-2', provider: 'google', provider_email: 'tester@gmail.com' },
];

const SESSIONS = [
  {
    key: 'sess-1',
    user_agent: 'Mozilla/5.0 Chrome',
    ip_address: '10.0.0.1',
    is_current: true,
    is_persistent: true,
    expires_at: '2026-12-31T00:00:00Z',
  },
  {
    key: 'sess-2',
    user_agent: null,
    ip_address: null,
    is_current: false,
    is_persistent: false,
    expires_at: '2026-07-01T00:00:00Z',
  },
];

const API_KEYS = [
  {
    key: 'key-1',
    label: 'CI',
    key_prefix: 'kp_abc',
    revoked: false,
    last_used_at: '2026-06-01T00:00:00Z',
  },
];

function installBaseHandlers() {
  server.use(
    http.get('/api/v1/admin/settings', () => HttpResponse.json(SETTINGS)),
    http.get('/api/v1/users/me/providers', () => HttpResponse.json(PROVIDERS)),
    http.get('/api/v1/users/me/sessions', () => HttpResponse.json(SESSIONS)),
    http.get('/api/v1/auth/api-keys', () => HttpResponse.json(API_KEYS)),
  );
}

function renderAt(route: string, smartHome = false) {
  // The page re-fetches preferences on mount; echo the smart_home flag from the
  // server so the HA integration card (gated behind it) renders.
  const prefs = {
    experience_level: 'expert',
    locale: 'de',
    theme: 'light',
    smart_home_enabled: smartHome,
  };
  server.use(
    http.get('/api/v1/t/:tenant/user-preferences', () => HttpResponse.json(prefs)),
    http.get('/api/v1/user-preferences', () => HttpResponse.json(prefs)),
  );
  return renderWithProviders(<AccountSettingsPage />, {
    store: storeWithUser(smartHome),
    route,
  });
}

beforeEach(() => {
  vi.clearAllMocks();
  installBaseHandlers();
});

describe('AccountSettingsPage — profile tab', () => {
  it('renders the profile fields and saves the display name', async () => {
    let patchBody: unknown = null;
    server.use(
      http.patch('/api/v1/users/me', async ({ request }) => {
        patchBody = await request.json();
        return HttpResponse.json({ ...AUTH_USER, display_name: 'New Name' });
      }),
      http.get('/api/v1/users/me', () => HttpResponse.json({ ...AUTH_USER })),
    );
    const user = userEvent.setup();
    renderAt('/account#profile');

    const nameField = await screen.findByTestId('profile-display-name');
    const input = nameField.querySelector('input') as HTMLInputElement;
    await user.clear(input);
    await user.type(input, 'New Name');
    await user.click(screen.getByTestId('profile-save-btn'));

    await waitFor(() =>
      expect(patchBody).toMatchObject({ display_name: 'New Name', locale: 'de' }),
    );
  });
});

describe('AccountSettingsPage — security tab', () => {
  it('lists linked providers and shows the current-password field for local accounts', async () => {
    renderAt('/account#security');
    // Local provider present → current password field is shown.
    expect(await screen.findByTestId('current-password-field')).toBeInTheDocument();
    expect(screen.getByTestId('new-password-field')).toBeInTheDocument();
    expect(screen.getByText('google')).toBeInTheDocument();
  });

  it('changes the password through the change-password endpoint', async () => {
    let body: unknown = null;
    server.use(
      http.post('/api/v1/users/me/password', async ({ request }) => {
        body = await request.json();
        return HttpResponse.json({ success: true });
      }),
    );
    const user = userEvent.setup();
    renderAt('/account#security');

    const current = (await screen.findByTestId('current-password-field')).querySelector(
      'input',
    ) as HTMLInputElement;
    const next = screen
      .getByTestId('new-password-field')
      .querySelector('input') as HTMLInputElement;
    await user.type(current, 'old-secret');
    await user.type(next, 'new-secret-123');
    await user.click(screen.getByTestId('change-password-btn'));

    await waitFor(() => expect(body).not.toBeNull());
  });
});

describe('AccountSettingsPage — removing a sign-in method (#1847)', () => {
  it('asks for the step-up and sends it with the removal', async () => {
    let removed: string | null = null;
    let body: unknown = null;
    server.use(
      http.delete('/api/v1/users/me/providers/:key', async ({ params, request }) => {
        removed = params.key as string;
        body = await request.json();
        return HttpResponse.json({ message: 'Provider unlinked.' });
      }),
    );
    const user = userEvent.setup();
    renderAt('/account#security');

    await user.click(await screen.findByTestId('unlink-provider-prov-2'));

    // A confirmation first: no request leaves before the step-up.
    const dialog = await screen.findByTestId('unlink-provider-dialog');
    expect(dialog).toHaveTextContent('tester@gmail.com');
    expect(removed).toBeNull();
    // No echo to type back — the password alone confirms.
    expect(screen.queryByTestId('unlink-provider-echo')).toBeNull();

    await user.type(dialogInput('unlink-provider-password'), STEP_UP_PASSWORD);
    await user.click(screen.getByTestId('unlink-provider-confirm'));

    await waitFor(() => expect(removed).toBe('prov-2'));
    expect(body).toEqual({ current_password: STEP_UP_PASSWORD });
  });

  it('removes nothing when the confirmation is cancelled', async () => {
    let removed = false;
    server.use(
      http.delete('/api/v1/users/me/providers/:key', () => {
        removed = true;
        return HttpResponse.json({ message: 'Provider unlinked.' });
      }),
    );
    const user = userEvent.setup();
    renderAt('/account#security');

    await user.click(await screen.findByTestId('unlink-provider-prov-2'));
    await user.click(await screen.findByTestId('unlink-provider-cancel'));

    await waitFor(() => expect(screen.queryByTestId('unlink-provider-dialog')).toBeNull());
    expect(removed).toBe(false);
  });
});

describe('AccountSettingsPage — sessions tab', () => {
  it('renders sessions and revokes a non-current one', async () => {
    let revoked: string | null = null;
    server.use(
      http.delete('/api/v1/users/me/sessions/:key', ({ params }) => {
        revoked = params.key as string;
        return new HttpResponse(null, { status: 204 });
      }),
    );
    const user = userEvent.setup();
    renderAt('/account#sessions');

    // Current session chip rendered; only the non-current row has a revoke button.
    expect(await screen.findByText('Mozilla/5.0 Chrome')).toBeInTheDocument();
    const rows = screen.getAllByRole('row');
    // header + 2 data rows
    const nonCurrentRow = rows.find((r) =>
      within(r).queryByRole('button'),
    );
    expect(nonCurrentRow).toBeDefined();
    await user.click(within(nonCurrentRow!).getByRole('button'));
    await waitFor(() => expect(revoked).toBe('sess-2'));
  });
});

// Credential-shaped values are assembled at runtime (GitGuardian, #1838).
const STEP_UP_PASSWORD = ['acct', 'Secr', '3t'].join('-');

function dialogInput(testId: string): HTMLInputElement {
  return screen.getByTestId(testId).querySelector('input') as HTMLInputElement;
}

describe('AccountSettingsPage — API keys tab', () => {
  it('creates a new API key through the step-up and shows the raw key once (#1847)', async () => {
    let body: unknown = null;
    server.use(
      http.post('/api/v1/auth/api-keys', async ({ request }) => {
        body = await request.json();
        return HttpResponse.json({ raw_key: 'kp_secret_raw_value', key: 'key-2' });
      }),
    );
    const user = userEvent.setup();
    renderAt('/account#apikeys');

    await user.click(await screen.findByRole('button', { name: 'Create API Key' }));
    const dialog = await screen.findByRole('dialog');
    const label = within(dialog).getByRole('textbox');
    await user.type(label, 'Grafana');
    await user.click(within(dialog).getByRole('button', { name: 'Create' }));

    // Full mode: the label dialog hands over to the step-up; nothing is minted yet.
    const stepUp = await screen.findByTestId('create-api-key-dialog');
    expect(stepUp).toHaveTextContent('Grafana');
    expect(body).toBeNull();

    await user.type(dialogInput('create-api-key-password'), STEP_UP_PASSWORD);
    await user.click(screen.getByTestId('create-api-key-confirm'));

    expect(await screen.findByText('kp_secret_raw_value')).toBeInTheDocument();
    // The step-up reaches the API call in the backend's field naming.
    expect(body).toEqual({ label: 'Grafana', current_password: STEP_UP_PASSWORD });
  });

  it('keeps a refused API-key step-up inside the dialog and shows no key', async () => {
    server.use(
      http.post('/api/v1/auth/api-keys', () =>
        HttpResponse.json(
          {
            error_id: 'err',
            error_code: 'UNAUTHORIZED',
            message: 'Wrong password.',
            details: [],
            timestamp: '',
            path: '/api/v1/auth/api-keys',
            method: 'POST',
          },
          { status: 401 },
        ),
      ),
    );
    const user = userEvent.setup();
    renderAt('/account#apikeys');

    await user.click(await screen.findByRole('button', { name: 'Create API Key' }));
    const dialog = await screen.findByRole('dialog');
    await user.type(within(dialog).getByRole('textbox'), 'Grafana');
    await user.click(within(dialog).getByRole('button', { name: 'Create' }));
    await user.type(dialogInput('create-api-key-password'), 'wrong-password');
    await user.click(screen.getByTestId('create-api-key-confirm'));

    expect(await screen.findByTestId('create-api-key-error')).toBeInTheDocument();
    expect(screen.getByTestId('create-api-key-dialog')).toBeInTheDocument();
    expect(dialogInput('create-api-key-password').value).toBe('');
    expect(screen.queryByText('kp_secret_raw_value')).toBeNull();
  });

  it('revokes an existing API key', async () => {
    let revoked = false;
    server.use(
      http.delete('/api/v1/auth/api-keys/:id', () => {
        revoked = true;
        return new HttpResponse(null, { status: 204 });
      }),
    );
    const user = userEvent.setup();
    renderAt('/account#apikeys');

    await screen.findByText('CI');
    const row = screen.getByText('CI').closest('tr')!;
    await user.click(within(row).getByRole('button'));
    await waitFor(() => expect(revoked).toBe(true));
  });
});

describe('AccountSettingsPage — back from the fresh sign-in (#1815, #1847)', () => {
  const token = ['re', 'auth', '-', 'tok', 'en'].join('');

  beforeEach(() => sessionStorage.clear());

  it('reopens the API-key dialog and creates the key with the pending token', async () => {
    const { storePendingStepUpToken, saveStepUpResume } = await import('@/utils/stepUpReauth');
    storePendingStepUpToken(token, 'api_key_creation', null);
    saveStepUpResume({ surface: 'create-api-key', action: 'api_key_creation', returnPath: '/account#apikeys' });
    let body: unknown = null;
    server.use(
      http.post('/api/v1/auth/api-keys', async ({ request }) => {
        body = await request.json();
        return HttpResponse.json({ raw_key: 'kp_resumed_raw_value', key: 'key-3' });
      }),
    );
    const user = userEvent.setup();
    renderAt('/account#apikeys');

    // No click on "create": the label dialog reopens on its own.
    const labelDialog = await screen.findByTestId('api-key-label-dialog');
    await user.type(within(labelDialog).getByRole('textbox'), 'Grafana');
    await user.click(screen.getByTestId('api-key-label-submit'));

    expect(await screen.findByTestId('create-api-key-reauth-done')).toBeInTheDocument();
    await user.click(screen.getByTestId('create-api-key-confirm'));

    expect(await screen.findByText('kp_resumed_raw_value')).toBeInTheDocument();
    expect(body).toEqual({ label: 'Grafana', step_up_token: token });
  });

  it('reopens the device-pairing step-up and mints the code with the pending token', async () => {
    const { storePendingStepUpToken, saveStepUpResume } = await import('@/utils/stepUpReauth');
    storePendingStepUpToken(token, 'device_pairing', null);
    saveStepUpResume({
      surface: 'connect-device-step-up',
      action: 'device_pairing',
      returnPath: '/account#sessions',
    });
    let body: unknown = null;
    server.use(
      http.post('/api/v1/auth/device-pairing', async ({ request }) => {
        body = await request.json();
        return HttpResponse.json(
          {
            payload_version: 1,
            server_url: 'https://garten.example.org',
            code: 'resumed-pairing-code',
            expires_at: '2099-01-01T00:00:00Z',
            expires_in: 90,
          },
          { status: 201 },
        );
      }),
    );
    const user = userEvent.setup();
    renderAt('/account#sessions');

    expect(await screen.findByTestId('connect-device-step-up-reauth-done')).toBeInTheDocument();
    await user.click(screen.getByTestId('connect-device-step-up-confirm'));

    expect(await screen.findByTestId('device-pairing-qr')).toBeInTheDocument();
    expect(body).toEqual({ step_up_token: token });
  });
});

describe('AccountSettingsPage — Home Assistant section', () => {
  it('tests, saves and resets the HA connection', async () => {
    let saved = false;
    let cleared = false;
    server.use(
      http.post('/api/v1/admin/settings/home-assistant/test', () =>
        HttpResponse.json({ success: true, message: 'Connected', ha_version: '2026.6' }),
      ),
      http.put('/api/v1/admin/settings/home-assistant', () => {
        saved = true;
        return HttpResponse.json({ ...SETTINGS, home_assistant: HA_BASE });
      }),
      http.delete('/api/v1/admin/settings/home-assistant', () => {
        cleared = true;
        return new HttpResponse(null, { status: 204 });
      }),
    );
    const user = userEvent.setup();
    renderAt('/account#ha', true);

    const urlField = await screen.findByTestId('ha-url-field');
    const urlInput = urlField.querySelector('input') as HTMLInputElement;
    await user.type(urlInput, 'http://ha.local:8123');

    await user.click(screen.getByTestId('test-connection-btn'));
    expect(await screen.findByTestId('test-result-alert')).toHaveTextContent('Connected');

    await user.click(screen.getByTestId('save-settings-btn'));
    await waitFor(() => expect(saved).toBe(true));
    expect(await screen.findByTestId('save-success-alert')).toBeInTheDocument();

    await user.click(screen.getByTestId('reset-settings-btn'));
    await user.click(await screen.findByRole('button', { name: 'Confirm' }));
    await waitFor(() => expect(cleared).toBe(true));
  });

  it('shows a failure alert when the HA test request throws', async () => {
    server.use(
      http.post('/api/v1/admin/settings/home-assistant/test', () => HttpResponse.error()),
    );
    const user = userEvent.setup();
    renderAt('/account#ha', true);

    const urlField = await screen.findByTestId('ha-url-field');
    await user.type(urlField.querySelector('input') as HTMLInputElement, 'http://ha.local');
    await user.click(screen.getByTestId('test-connection-btn'));
    const alert = await screen.findByTestId('test-result-alert');
    expect(alert).toBeInTheDocument();
  });

  it('hides the HA integration card when smart home is disabled', async () => {
    renderAt('/account#ha', false);
    // Pl@ntNet card is always present; HA card is gated behind the toggle.
    expect(await screen.findByTestId('plantnet-key-field')).toBeInTheDocument();
    expect(screen.queryByTestId('ha-url-field')).not.toBeInTheDocument();
  });
});

describe('AccountSettingsPage — Pl@ntNet reset cancel', () => {
  it('closes the reset dialog without deleting when cancelled', async () => {
    let deleted = false;
    server.use(
      http.get('/api/v1/admin/settings', () =>
        HttpResponse.json({
          home_assistant: HA_BASE,
          plant_identification: {
            plantnet_api_key_masked: '****2345',
            source_plantnet_api_key: 'db',
          },
        }),
      ),
      http.delete('/api/v1/admin/settings/plant-identification', () => {
        deleted = true;
        return new HttpResponse(null, { status: 204 });
      }),
    );
    const user = userEvent.setup();
    renderAt('/account#ha');

    await user.click(await screen.findByTestId('plantnet-reset-btn'));
    await user.click(await screen.findByTestId('plantnet-reset-cancel-btn'));
    // Dialog dismissed, no DELETE issued.
    expect(deleted).toBe(false);
  });
});

describe('AccountSettingsPage — platform tab', () => {
  it('renders the mode cards and loads admin stats for a platform admin', async () => {
    server.use(
      http.get('/api/v1/admin/platform/stats', () =>
        HttpResponse.json({
          active_users: 3,
          total_users: 5,
          active_tenants: 2,
          total_memberships: 7,
        }),
      ),
      http.get('/api/v1/admin/platform/tenants', () => HttpResponse.json([])),
      http.get('/api/v1/admin/platform/users', () => HttpResponse.json([])),
    );
    renderAt('/account#platform');

    // The three mode cards (light/full/enterprise) always render.
    expect(await screen.findByText('Light Mode')).toBeInTheDocument();
    // Admin stats load lazily once the platform tab is shown.
    await waitFor(() => expect(screen.getByText('3')).toBeInTheDocument());
  });

  it('hides admin data when the stats request is forbidden', async () => {
    server.use(
      http.get('/api/v1/admin/platform/stats', () =>
        HttpResponse.json(
          {
            error_id: 'e',
            error_code: 'FORBIDDEN',
            message: 'no',
            details: [],
            timestamp: '',
            path: '',
            method: 'GET',
          },
          { status: 403 },
        ),
      ),
      http.get('/api/v1/admin/platform/tenants', () => HttpResponse.json([])),
      http.get('/api/v1/admin/platform/users', () => HttpResponse.json([])),
    );
    renderAt('/account#platform');
    // Mode cards still render; admin stat numbers do not.
    expect(await screen.findByText('Light Mode')).toBeInTheDocument();
    expect(screen.queryByText('Active Users')).not.toBeInTheDocument();
  });
});

describe('AccountSettingsPage — Pl@ntNet field interaction', () => {
  it('clears the success/test state as soon as the key field changes', async () => {
    server.use(
      http.get('/api/v1/admin/settings', () =>
        HttpResponse.json({
          home_assistant: HA_BASE,
          plant_identification: {
            plantnet_api_key_masked: '****old',
            source_plantnet_api_key: 'db',
          },
        }),
      ),
      http.post('/api/v1/admin/settings/plant-identification/test', () =>
        HttpResponse.json({ success: true, message: 'ok' }),
      ),
    );
    const user = userEvent.setup();
    renderAt('/account#ha');

    // Produce a test-result alert first.
    await user.click(await screen.findByTestId('plantnet-test-btn'));
    expect(await screen.findByTestId('plantnet-test-result-alert')).toBeInTheDocument();

    // Typing into the key field resets the transient result/success state.
    const field = screen.getByTestId('plantnet-key-field');
    await user.type(field.querySelector('input') as HTMLInputElement, 'x');
    await waitFor(() =>
      expect(screen.queryByTestId('plantnet-test-result-alert')).not.toBeInTheDocument(),
    );
  });
});

describe('AccountSettingsPage — account tab', () => {
  it('aborts deletion when the step-up dialog is cancelled', async () => {
    let deleteCalled = false;
    server.use(
      http.delete('/api/v1/users/me', () => {
        deleteCalled = true;
        return HttpResponse.json({ message: 'ok' });
      }),
    );
    const user = userEvent.setup();
    renderAt('/account#account');

    await user.click(await screen.findByTestId('delete-account-btn'));
    const dialog = await screen.findByTestId('delete-account-dialog');
    await user.click(within(dialog).getByTestId('delete-account-cancel'));
    await waitFor(() => expect(screen.queryByTestId('delete-account-dialog')).not.toBeInTheDocument());
    expect(deleteCalled).toBe(false);
  });

});
