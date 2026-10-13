import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { render, screen, cleanup } from '@testing-library/react';
import { createMemoryRouter, RouterProvider, useLocation } from 'react-router-dom';
import StepUpCallbackPage from '@/pages/auth/StepUpCallbackPage';
import {
  STEP_UP_REAUTH_TOKEN_KEY,
  peekPendingStepUpToken,
  saveStepUpResume,
  takeStepUpReauthError,
} from '@/utils/stepUpReauth';

/**
 * #1815 — the provider returns via the backend to `/auth/step-up/callback` with
 * the one-time step-up token in the URL fragment, or `?error=…` on failure.
 */

// Credential-shaped values are assembled at runtime (GitGuardian, #1838).
const TOKEN = ['st', 'ep', 'Up', 'Tok', '9z'].join('');

function Landing() {
  const location = useLocation();
  return <div data-testid="landed">{location.pathname + location.search + location.hash}</div>;
}

function renderCallback(entry: string) {
  // The real browser URL carries the fragment too; the page must strip it there.
  window.history.replaceState(null, '', entry);
  const router = createMemoryRouter(
    [
      { path: '/auth/step-up/callback', element: <StepUpCallbackPage /> },
      { path: '*', element: <Landing /> },
    ],
    { initialEntries: [entry] },
  );
  return render(<RouterProvider router={router} />);
}

describe('StepUpCallbackPage (#1815)', () => {
  beforeEach(() => {
    sessionStorage.clear();
    localStorage.clear();
  });
  afterEach(() => {
    cleanup();
    window.history.replaceState(null, '', '/');
  });

  it('stores the token from the fragment, strips the fragment and returns to the saved path', async () => {
    const nonce = saveStepUpResume({
      surface: 'delete-account',
      action: 'account_erasure',
      returnPath: '/settings/account#account',
    });
    renderCallback(
      `/auth/step-up/callback#step_up_token=${TOKEN}&action=account_erasure&client_nonce=${nonce}`,
    );

    expect(await screen.findByTestId('landed')).toHaveTextContent('/settings/account#account');
    expect(window.location.hash).toBe('');
    expect(window.location.href).not.toContain(TOKEN);
    expect(peekPendingStepUpToken('account_erasure', null)).toBe(TOKEN);
    expect(localStorage.length).toBe(0);
    const stored = JSON.parse(sessionStorage.getItem(STEP_UP_REAUTH_TOKEN_KEY) ?? '{}');
    expect(stored.expiresAt).toBeGreaterThan(Date.now() + 4 * 60 * 1000);
    expect(stored.expiresAt).toBeLessThanOrEqual(Date.now() + 5 * 60 * 1000);
  });

  it.each(['//evil.example/steal', 'https://evil.example/', '/\\evil.example'])(
    'refuses the external return path %j and lands on the app root',
    async (returnPath) => {
      sessionStorage.setItem(
        'kp.stepUp.resume',
        JSON.stringify({ surface: 'delete-account', action: 'account_erasure', returnPath }),
      );
      renderCallback(`/auth/step-up/callback#step_up_token=${TOKEN}&action=account_erasure`);

      expect(await screen.findByTestId('landed')).toHaveTextContent(/^\/$/);
    },
  );

  it('does not store a token for an unknown act', async () => {
    saveStepUpResume({ surface: 'x', action: 'account_erasure', returnPath: '/privacy' });
    renderCallback(`/auth/step-up/callback#step_up_token=${TOKEN}&action=drop_database`);

    expect(await screen.findByTestId('landed')).toHaveTextContent('/privacy');
    expect(sessionStorage.getItem(STEP_UP_REAUTH_TOKEN_KEY)).toBeNull();
    expect(window.location.hash).toBe('');
  });

  it.each(['step_up_failed', 'step_up_stale', 'step_up_cancelled'])(
    'returns with an error marker for ?error=%s',
    async (code) => {
      const nonce = saveStepUpResume({
        surface: 'tenant-delete',
        action: 'tenant_deletion',
        returnPath: '/admin/tenants/t1',
      });
      renderCallback(
        `/auth/step-up/callback?error=${code}&action=tenant_deletion&client_nonce=${nonce}`,
      );

      expect(await screen.findByTestId('landed')).toHaveTextContent('/admin/tenants/t1');
      expect(sessionStorage.getItem(STEP_UP_REAUTH_TOKEN_KEY)).toBeNull();
      expect(takeStepUpReauthError('tenant_deletion')).toBe(code);
    },
  );

  it('maps an unknown error code to step_up_failed', async () => {
    const nonce = saveStepUpResume({
      surface: 'tenant-delete',
      action: 'tenant_deletion',
      returnPath: '/admin/tenants/t1',
    });
    renderCallback(
      `/auth/step-up/callback?error=%3Cb%3Ephish%3C%2Fb%3E&action=tenant_deletion&client_nonce=${nonce}`,
    );

    await screen.findByTestId('landed');
    expect(takeStepUpReauthError('tenant_deletion')).toBe('step_up_failed');
  });

  it('discards a token when no step-up was started in this tab (no resume record)', async () => {
    renderCallback(`/auth/step-up/callback#step_up_token=${TOKEN}&action=account_erasure`);

    expect(await screen.findByTestId('landed')).toHaveTextContent(/^\/$/);
    expect(sessionStorage.getItem(STEP_UP_REAUTH_TOKEN_KEY)).toBeNull();
    expect(window.location.hash).toBe('');
  });

  it('discards a token for another act than the one started', async () => {
    saveStepUpResume({
      surface: 'tenant-delete',
      action: 'tenant_deletion',
      returnPath: '/admin/tenants/t1',
    });
    renderCallback(`/auth/step-up/callback#step_up_token=${TOKEN}&action=account_erasure`);

    await screen.findByTestId('landed');
    expect(sessionStorage.getItem(STEP_UP_REAUTH_TOKEN_KEY)).toBeNull();
    expect(peekPendingStepUpToken('account_erasure', null)).toBeNull();
    expect(peekPendingStepUpToken('tenant_deletion', null)).toBeNull();
  });

  it('discards a token when the step-up was started more than 10 minutes ago', async () => {
    saveStepUpResume({
      surface: 'delete-account',
      action: 'account_erasure',
      returnPath: '/settings/account',
    });
    const record = JSON.parse(sessionStorage.getItem('kp.stepUp.resume') ?? '{}');
    sessionStorage.setItem(
      'kp.stepUp.resume',
      JSON.stringify({ ...record, createdAt: Date.now() - 11 * 60 * 1000 }),
    );
    renderCallback(`/auth/step-up/callback#step_up_token=${TOKEN}&action=account_erasure`);

    await screen.findByTestId('landed');
    expect(sessionStorage.getItem(STEP_UP_REAUTH_TOKEN_KEY)).toBeNull();
  });

  it('discards a token whose client nonce is not the one this tab started with (SEC-005)', async () => {
    saveStepUpResume({
      surface: 'delete-account',
      action: 'account_erasure',
      returnPath: '/settings/account',
    });
    const planted = 'f'.repeat(32);
    renderCallback(
      `/auth/step-up/callback#step_up_token=${TOKEN}&action=account_erasure&client_nonce=${planted}`,
    );

    await screen.findByTestId('landed');
    expect(sessionStorage.getItem(STEP_UP_REAUTH_TOKEN_KEY)).toBeNull();
  });

  it('discards a token without a client nonce even when a resume record for the act exists', async () => {
    saveStepUpResume({
      surface: 'delete-account',
      action: 'account_erasure',
      returnPath: '/settings/account',
    });
    renderCallback(`/auth/step-up/callback#step_up_token=${TOKEN}&action=account_erasure`);

    await screen.findByTestId('landed');
    expect(sessionStorage.getItem(STEP_UP_REAUTH_TOKEN_KEY)).toBeNull();
  });

  it('ignores an error whose client nonce does not match', async () => {
    saveStepUpResume({
      surface: 'tenant-delete',
      action: 'tenant_deletion',
      returnPath: '/admin/tenants/t1',
    });
    renderCallback(
      `/auth/step-up/callback?error=step_up_failed&action=tenant_deletion&client_nonce=${'0'.repeat(32)}`,
    );

    await screen.findByTestId('landed');
    expect(takeStepUpReauthError('tenant_deletion')).toBeNull();
  });

  it('saves a random nonce and the start time with the resume record', () => {
    saveStepUpResume({ surface: 'a', action: 'account_erasure', returnPath: '/x' });
    const first = JSON.parse(sessionStorage.getItem('kp.stepUp.resume') ?? '{}');
    saveStepUpResume({ surface: 'a', action: 'account_erasure', returnPath: '/x' });
    const second = JSON.parse(sessionStorage.getItem('kp.stepUp.resume') ?? '{}');
    expect(first.nonce).toMatch(/^[0-9a-f]{32}$/);
    expect(second.nonce).not.toBe(first.nonce);
    expect(typeof first.createdAt).toBe('number');
  });
});
