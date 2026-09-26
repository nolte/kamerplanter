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

/**
 * #1815 — an account without a local password confirms a step-up with a
 * one-time code sent by e-mail.
 */

const ECHO = 'my-garden';
// Credential-shaped values are assembled at runtime (GitGuardian, #1838).
const PASSWORD = ['s3', 'cret', '-pw'].join('');
const CODE = ['7', '3', '0', '9', '1', '2'].join('');

function providers(list: { provider: string }[]) {
  server.use(
    http.get('/api/v1/users/me/providers', () =>
      HttpResponse.json(list.map((p, i) => ({ key: `p-${i}`, provider: p.provider, provider_email: null }))),
    ),
  );
}

function apiError(status: number, errorCode: string): ApiError {
  return new ApiError(
    {
      error_id: 'e',
      error_code: errorCode,
      message: 'Backend English message.',
      details: [],
      timestamp: '',
      path: '/x',
      method: 'DELETE',
    },
    status,
  );
}

function renderDialog(onConfirm: (c: StepUpConfirmation) => Promise<void>) {
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
      onConfirm={onConfirm}
      onCancel={() => {}}
    />,
  );
}

function field(dialog: HTMLElement, testId: string): HTMLInputElement {
  return within(dialog).getByTestId(testId).querySelector('input') as HTMLInputElement;
}

describe('StepUpConfirmDialog — e-mailed step-up code (#1815)', () => {
  beforeEach(() => i18n.changeLanguage('de'));
  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  it('reveals the code field after 401 STEP_UP_CODE_REQUIRED and forwards the code', async () => {
    providers([]);
    const onConfirm = vi
      .fn<(c: StepUpConfirmation) => Promise<void>>()
      .mockRejectedValueOnce(apiError(401, 'STEP_UP_CODE_REQUIRED'))
      .mockResolvedValueOnce(undefined);
    const user = userEvent.setup();
    renderDialog(onConfirm);
    const dialog = await screen.findByTestId('su-dialog');

    expect(within(dialog).queryByTestId('su-code')).not.toBeInTheDocument();
    await user.type(field(dialog, 'su-echo'), ECHO);
    await user.type(field(dialog, 'su-password'), PASSWORD);
    await user.click(within(dialog).getByTestId('su-confirm'));

    expect(await within(dialog).findByTestId('su-code')).toBeInTheDocument();
    expect(within(dialog).getByTestId('su-send-code')).toBeInTheDocument();
    expect(within(dialog).getByTestId('su-error')).toHaveTextContent(i18n.t('pages.auth.stepUpCodeRequired'));
    // The code is now required.
    expect(within(dialog).getByTestId('su-confirm')).toBeDisabled();

    await user.type(field(dialog, 'su-code'), CODE);
    await user.click(within(dialog).getByTestId('su-confirm'));

    await waitFor(() => expect(onConfirm).toHaveBeenCalledTimes(2));
    expect(onConfirm.mock.calls[1][0]).toMatchObject({ echo: ECHO, code: CODE });
  });

  it('sends the code by e-mail for a federated-only account and allows a resend', async () => {
    providers([{ provider: 'github' }]);
    let codeRequests = 0;
    let codeBody: unknown = null;
    server.use(
      http.post('/api/v1/users/me/step-up-code', async ({ request }) => {
        codeRequests += 1;
        codeBody = await request.json();
        return HttpResponse.json({ expires_at: '2026-09-25T12:15:00Z', expires_in: 900 }, { status: 202 });
      }),
    );
    const onConfirm = vi.fn<(c: StepUpConfirmation) => Promise<void>>().mockResolvedValue(undefined);
    const user = userEvent.setup();
    renderDialog(onConfirm);
    const dialog = await screen.findByTestId('su-dialog');

    await user.click(await within(dialog).findByTestId('su-send-code'));
    await waitFor(() => expect(codeRequests).toBe(1));
    // The code is requested for the act this dialog confirms, and only that one (review SEC-003).
    expect(codeBody).toEqual({ action: 'tenant_deletion' });
    expect(
      await within(dialog).findByText(i18n.t('pages.auth.stepUpCodeSent', { minutes: 15 })),
    ).toBeInTheDocument();
    expect(within(dialog).queryByTestId('su-password')).not.toBeInTheDocument();

    await user.click(within(dialog).getByTestId('su-send-code'));
    await waitFor(() => expect(codeRequests).toBe(2));

    const codeInput = field(dialog, 'su-code');
    expect(codeInput).toHaveAttribute('autocomplete', 'one-time-code');
    expect(codeInput).toHaveAttribute('inputmode', 'numeric');

    await user.type(field(dialog, 'su-echo'), ECHO);
    expect(within(dialog).getByTestId('su-confirm')).toBeDisabled();
    await user.type(codeInput, CODE);
    await user.click(within(dialog).getByTestId('su-confirm'));

    await waitFor(() => expect(onConfirm).toHaveBeenCalledWith({ echo: ECHO, code: CODE }));
  });

  it('shows the lockout when sending the code answers 429 STEP_UP_LOCKED', async () => {
    providers([{ provider: 'github' }]);
    server.use(
      http.post('/api/v1/users/me/step-up-code', () =>
        HttpResponse.json(
          {
            error_id: 'e',
            error_code: 'STEP_UP_LOCKED',
            message: 'locked',
            details: [{ field: 'step_up_code', reason: 'locked', code: 'STEP_UP_LOCKED', retry_after_minutes: '12' }],
            timestamp: '',
            path: '/api/v1/users/me/step-up-code',
            method: 'POST',
          },
          { status: 429 },
        ),
      ),
    );
    const user = userEvent.setup();
    renderDialog(vi.fn());
    const dialog = await screen.findByTestId('su-dialog');

    await user.click(await within(dialog).findByTestId('su-send-code'));
    expect(
      await within(dialog).findByText(i18n.t('pages.auth.stepUpLocked', { minutes: '12' })),
    ).toBeInTheDocument();
  });

  it('clears the code after a rejection', async () => {
    providers([{ provider: 'github' }]);
    const onConfirm = vi
      .fn<(c: StepUpConfirmation) => Promise<void>>()
      .mockRejectedValue(apiError(401, 'UNAUTHORIZED'));
    const user = userEvent.setup();
    renderDialog(onConfirm);
    const dialog = await screen.findByTestId('su-dialog');

    await user.type(field(dialog, 'su-echo'), ECHO);
    await user.type(await within(dialog).findByTestId('su-code').then(() => field(dialog, 'su-code')), CODE);
    await user.click(within(dialog).getByTestId('su-confirm'));

    await within(dialog).findByTestId('su-error');
    expect(field(dialog, 'su-code').value).toBe('');
  });
});
