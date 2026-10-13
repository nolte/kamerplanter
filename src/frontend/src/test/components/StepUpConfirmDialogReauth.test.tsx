import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { screen, waitFor, within, cleanup } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';
import { server } from '@/test/mocks/server';
import { renderWithProviders } from '@/test/helpers';
import StepUpConfirmDialog from '@/components/common/StepUpConfirmDialog';
import type { StepUpConfirmation } from '@/components/common/StepUpConfirmDialog';
import { ApiError } from '@/api/errors';
import { redirectTo } from '@/utils/browserNavigation';
import {
  STEP_UP_REAUTH_TOKEN_KEY,
  readStepUpResume,
  storePendingStepUpToken,
  storeStepUpReauthError,
} from '@/utils/stepUpReauth';

vi.mock('@/utils/browserNavigation', () => ({ redirectTo: vi.fn() }));

/**
 * #1815 — an account without a local password whose provider can prove a fresh
 * sign-in (Google, a generic OIDC provider) confirms by signing in again there.
 */

const ECHO = 'my-garden';
const TARGET = 'tenant-key-1';
// Credential-shaped values are assembled at runtime (GitGuardian, #1838).
const PASSWORD = ['s3', 'cret', '-pw'].join('');
const TOKEN = ['re', 'auth', '-', 'tok', 'en'].join('');
const AUTH_URL = 'https://accounts.example.test/o/oauth2/auth?prompt=login';

function providers(list: { provider: string; key?: string }[]) {
  server.use(
    http.get('/api/v1/users/me/providers', () =>
      HttpResponse.json(
        list.map((p, i) => ({
          key: p.key ?? `p-${i}`,
          provider: p.provider,
          provider_email: null,
        })),
      ),
    ),
  );
}

function apiError(status: number, errorCode: string, field = ''): ApiError {
  return new ApiError(
    {
      error_id: 'e',
      error_code: errorCode,
      message: 'Backend English message.',
      details: field ? [{ field, reason: 'r', code: errorCode }] : [],
      timestamp: '',
      path: '/x',
      method: 'DELETE',
    },
    status,
  );
}

function errorBody(status: number, errorCode: string, field = '') {
  return HttpResponse.json(
    {
      error_id: 'e',
      error_code: errorCode,
      message: 'Backend English message.',
      details: field ? [{ field, reason: 'r', code: errorCode }] : [],
      timestamp: '',
      path: '/x',
      method: 'POST',
    },
    { status },
  );
}

function renderDialog(
  onConfirm: (c: StepUpConfirmation) => Promise<void>,
  route = '/admin/tenants/t1',
) {
  return renderWithProviders(
    <StepUpConfirmDialog
      open
      title="Delete"
      description="Really?"
      echoLabel="Slug"
      echoHelper="Type the slug"
      expectedEcho={ECHO}
      confirmLabel="Delete now"
      testIdPrefix="su"
      stepUpAction="tenant_deletion"
      stepUpTarget={TARGET}
      onConfirm={onConfirm}
      onCancel={() => {}}
    />,
    { route },
  );
}

function field(dialog: HTMLElement, testId: string): HTMLInputElement {
  return within(dialog).getByTestId(testId).querySelector('input') as HTMLInputElement;
}

describe('StepUpConfirmDialog — fresh OIDC re-authentication (#1815)', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
    sessionStorage.clear();
    vi.mocked(redirectTo).mockReset();
  });
  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  it('offers "sign in again" instead of password or code for a google-only account', async () => {
    providers([{ provider: 'google', key: 'prov-g' }]);
    let startBody: unknown = null;
    server.use(
      http.post('/api/v1/users/me/step-up/oidc', async ({ request }) => {
        startBody = await request.json();
        return HttpResponse.json({ authorization_url: AUTH_URL });
      }),
    );
    const user = userEvent.setup();
    renderDialog(vi.fn(), '/admin/tenants/t1#danger');
    const dialog = await screen.findByTestId('su-dialog');

    const button = await within(dialog).findByTestId('su-reauth');
    expect(within(dialog).queryByTestId('su-password')).not.toBeInTheDocument();
    expect(within(dialog).queryByTestId('su-code')).not.toBeInTheDocument();
    await user.type(field(dialog, 'su-echo'), ECHO);
    // Without the fresh sign-in the act cannot be confirmed.
    expect(within(dialog).getByTestId('su-confirm')).toBeDisabled();

    await user.click(button);

    await waitFor(() => expect(redirectTo).toHaveBeenCalledWith(AUTH_URL));
    // The client nonce goes to the backend and is the one the resume record keeps (SEC-005).
    const resume = readStepUpResume();
    expect(resume).toMatchObject({
      surface: 'su',
      action: 'tenant_deletion',
      target: TARGET,
      returnPath: '/admin/tenants/t1#danger',
    });
    // #1884 — the sign-in is started for this tenant; the token is bound to it.
    expect(startBody).toEqual({
      action: 'tenant_deletion',
      target: TARGET,
      provider_key: 'prov-g',
      client_nonce: resume?.nonce,
    });
    expect(resume?.nonce).toMatch(/^[0-9a-f]{32}$/);
  });

  it('offers one button per provider that can re-authenticate', async () => {
    providers([
      { provider: 'google', key: 'g1' },
      { provider: 'github', key: 'gh1' },
      { provider: 'oidc', key: 'o1' },
    ]);
    renderDialog(vi.fn());
    const dialog = await screen.findByTestId('su-dialog');

    expect(await within(dialog).findByTestId('su-reauth-g1')).toBeInTheDocument();
    expect(within(dialog).getByTestId('su-reauth-o1')).toBeInTheDocument();
    expect(within(dialog).queryByTestId('su-reauth-gh1')).not.toBeInTheDocument();
  });

  it('sends step_up_token when a pending token for the act exists and consumes it', async () => {
    providers([{ provider: 'google' }]);
    storePendingStepUpToken(TOKEN, 'tenant_deletion', TARGET);
    const onConfirm = vi
      .fn<(c: StepUpConfirmation) => Promise<void>>()
      .mockResolvedValue(undefined);
    const user = userEvent.setup();
    renderDialog(onConfirm);
    const dialog = await screen.findByTestId('su-dialog');

    expect(await within(dialog).findByTestId('su-reauth-done')).toHaveTextContent(
      i18n.t('pages.auth.stepUpReauthDone'),
    );
    expect(within(dialog).queryByTestId('su-reauth')).not.toBeInTheDocument();
    // The echo stays required.
    expect(within(dialog).getByTestId('su-confirm')).toBeDisabled();
    await user.type(field(dialog, 'su-echo'), ECHO);
    await user.click(within(dialog).getByTestId('su-confirm'));

    await waitFor(() => expect(onConfirm).toHaveBeenCalledWith({ echo: ECHO, token: TOKEN }));
    expect(sessionStorage.getItem(STEP_UP_REAUTH_TOKEN_KEY)).toBeNull();
  });

  it('ignores a pending token of another act', async () => {
    providers([{ provider: 'google' }]);
    storePendingStepUpToken(TOKEN, 'account_erasure', null);
    renderDialog(vi.fn());
    const dialog = await screen.findByTestId('su-dialog');

    expect(await within(dialog).findByTestId('su-reauth')).toBeInTheDocument();
    expect(within(dialog).queryByTestId('su-reauth-done')).not.toBeInTheDocument();
  });

  it('drops a rejected token and offers the sign-in again', async () => {
    providers([{ provider: 'google' }]);
    storePendingStepUpToken(TOKEN, 'tenant_deletion', TARGET);
    const onConfirm = vi
      .fn<(c: StepUpConfirmation) => Promise<void>>()
      .mockRejectedValue(apiError(401, 'STEP_UP_REAUTH_REQUIRED', 'step_up_token'));
    const user = userEvent.setup();
    renderDialog(onConfirm);
    const dialog = await screen.findByTestId('su-dialog');

    await within(dialog).findByTestId('su-reauth-done');
    await user.type(field(dialog, 'su-echo'), ECHO);
    await user.click(within(dialog).getByTestId('su-confirm'));

    expect(await within(dialog).findByTestId('su-reauth')).toBeInTheDocument();
    expect(within(dialog).getByTestId('su-error')).toHaveTextContent(
      i18n.t('pages.auth.stepUpReauthRequired'),
    );
    expect(sessionStorage.getItem(STEP_UP_REAUTH_TOKEN_KEY)).toBeNull();
  });

  it('reveals the sign-in after 401 STEP_UP_REAUTH_REQUIRED for an unknown provider list', async () => {
    providers([]);
    const onConfirm = vi
      .fn<(c: StepUpConfirmation) => Promise<void>>()
      .mockRejectedValue(apiError(401, 'STEP_UP_REAUTH_REQUIRED', 'step_up_token'));
    const user = userEvent.setup();
    renderDialog(onConfirm);
    const dialog = await screen.findByTestId('su-dialog');

    expect(within(dialog).queryByTestId('su-reauth')).not.toBeInTheDocument();
    await user.type(field(dialog, 'su-echo'), ECHO);
    await user.type(field(dialog, 'su-password'), PASSWORD);
    await user.click(within(dialog).getByTestId('su-confirm'));

    expect(await within(dialog).findByTestId('su-reauth')).toBeInTheDocument();
    expect(within(dialog).queryByTestId('su-password')).not.toBeInTheDocument();
    expect(within(dialog).getByTestId('su-error')).toHaveTextContent(
      i18n.t('pages.auth.stepUpReauthRequired'),
    );
  });

  it('keeps the e-mailed code for a github-only account', async () => {
    providers([{ provider: 'github' }, { provider: 'apple' }]);
    renderDialog(vi.fn());
    const dialog = await screen.findByTestId('su-dialog');

    expect(await within(dialog).findByTestId('su-send-code')).toBeInTheDocument();
    expect(within(dialog).queryByTestId('su-reauth')).not.toBeInTheDocument();
  });

  it('falls back to the e-mailed code on 422 STEP_UP_REAUTH_UNAVAILABLE', async () => {
    providers([{ provider: 'oidc' }]);
    server.use(
      http.post('/api/v1/users/me/step-up/oidc', () =>
        errorBody(422, 'STEP_UP_REAUTH_UNAVAILABLE', 'provider_key'),
      ),
    );
    const user = userEvent.setup();
    renderDialog(vi.fn());
    const dialog = await screen.findByTestId('su-dialog');

    await user.click(await within(dialog).findByTestId('su-reauth'));

    expect(await within(dialog).findByTestId('su-send-code')).toBeInTheDocument();
    expect(within(dialog).queryByTestId('su-reauth')).not.toBeInTheDocument();
    expect(redirectTo).not.toHaveBeenCalled();
    expect(readStepUpResume()).toBeNull();
  });

  it('switches from the code to the sign-in when sending the code answers 422 STEP_UP_REAUTH_REQUIRED', async () => {
    providers([]);
    server.use(
      http.post('/api/v1/users/me/step-up-code', () =>
        errorBody(422, 'STEP_UP_REAUTH_REQUIRED', 'step_up_token'),
      ),
    );
    const onConfirm = vi
      .fn<(c: StepUpConfirmation) => Promise<void>>()
      .mockRejectedValue(apiError(401, 'STEP_UP_CODE_REQUIRED'));
    const user = userEvent.setup();
    renderDialog(onConfirm);
    const dialog = await screen.findByTestId('su-dialog');

    await user.type(field(dialog, 'su-echo'), ECHO);
    await user.type(field(dialog, 'su-password'), PASSWORD);
    await user.click(within(dialog).getByTestId('su-confirm'));
    await user.click(await within(dialog).findByTestId('su-send-code'));

    expect(await within(dialog).findByTestId('su-reauth')).toBeInTheDocument();
    expect(within(dialog).queryByTestId('su-code')).not.toBeInTheDocument();
  });

  it('shows a callback error ("try again") after the return', async () => {
    providers([{ provider: 'google' }]);
    storeStepUpReauthError('step_up_stale', 'tenant_deletion');
    renderDialog(vi.fn());
    const dialog = await screen.findByTestId('su-dialog');

    expect(await within(dialog).findByTestId('su-error')).toHaveTextContent(
      i18n.t('pages.auth.stepUpReauthStale'),
    );
    expect(await within(dialog).findByTestId('su-reauth')).toBeInTheDocument();
  });

  it('shows the password field, not the code, on 422 STEP_UP_PASSWORD_REQUIRED', async () => {
    providers([{ provider: 'oidc' }]);
    server.use(
      http.post('/api/v1/users/me/step-up/oidc', () =>
        errorBody(422, 'STEP_UP_PASSWORD_REQUIRED', 'password'),
      ),
    );
    const user = userEvent.setup();
    renderDialog(vi.fn());
    const dialog = await screen.findByTestId('su-dialog');

    await user.click(await within(dialog).findByTestId('su-reauth'));

    expect(await within(dialog).findByTestId('su-password')).toBeInTheDocument();
    expect(within(dialog).queryByTestId('su-send-code')).not.toBeInTheDocument();
    expect(within(dialog).queryByTestId('su-reauth')).not.toBeInTheDocument();
    expect(within(dialog).getByTestId('su-error')).toHaveTextContent(
      i18n.t('pages.auth.stepUpCodeNotNeeded'),
    );
    expect(redirectTo).not.toHaveBeenCalled();
  });

  it('keeps a pending token when the act is refused for another reason (422)', async () => {
    providers([{ provider: 'google' }]);
    storePendingStepUpToken(TOKEN, 'tenant_deletion', TARGET);
    const onConfirm = vi
      .fn<(c: StepUpConfirmation) => Promise<void>>()
      .mockRejectedValueOnce(apiError(422, 'VALIDATION_ERROR', 'confirm_slug'))
      .mockResolvedValueOnce(undefined);
    const user = userEvent.setup();
    renderDialog(onConfirm);
    const dialog = await screen.findByTestId('su-dialog');

    await within(dialog).findByTestId('su-reauth-done');
    await user.type(field(dialog, 'su-echo'), ECHO);
    await user.click(within(dialog).getByTestId('su-confirm'));

    await within(dialog).findByTestId('su-error');
    // Still valid: the backend refused before the step-up was checked.
    expect(within(dialog).getByTestId('su-reauth-done')).toBeInTheDocument();
    expect(sessionStorage.getItem(STEP_UP_REAUTH_TOKEN_KEY)).not.toBeNull();

    await user.click(within(dialog).getByTestId('su-confirm'));
    await waitFor(() => expect(onConfirm).toHaveBeenCalledTimes(2));
    expect(onConfirm.mock.calls[1][0]).toEqual({ echo: ECHO, token: TOKEN });
    await waitFor(() => expect(sessionStorage.getItem(STEP_UP_REAUTH_TOKEN_KEY)).toBeNull());
  });

  it('drops a pending token after 429 STEP_UP_LOCKED', async () => {
    providers([{ provider: 'google' }]);
    storePendingStepUpToken(TOKEN, 'tenant_deletion', TARGET);
    const onConfirm = vi
      .fn<(c: StepUpConfirmation) => Promise<void>>()
      .mockRejectedValue(apiError(429, 'STEP_UP_LOCKED', 'step_up_token'));
    const user = userEvent.setup();
    renderDialog(onConfirm);
    const dialog = await screen.findByTestId('su-dialog');

    await within(dialog).findByTestId('su-reauth-done');
    await user.type(field(dialog, 'su-echo'), ECHO);
    await user.click(within(dialog).getByTestId('su-confirm'));

    await within(dialog).findByTestId('su-error');
    expect(sessionStorage.getItem(STEP_UP_REAUTH_TOKEN_KEY)).toBeNull();
  });
});
