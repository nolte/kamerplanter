import { describe, it, expect, beforeEach } from 'vitest';
import {
  STEP_UP_ACTIONS,
  STEP_UP_REAUTH_RESUME_KEY,
  STEP_UP_REAUTH_TOKEN_KEY,
  consumePendingStepUpToken,
  isTargetedStepUpAction,
  readStepUpResume,
  saveStepUpResume,
  isSafeReturnPath,
  isStepUpAction,
  peekPendingStepUpToken,
  storePendingStepUpToken,
  takeStepUpReauthError,
  storeStepUpReauthError,
} from '@/utils/stepUpReauth';

// Credential-shaped values are assembled at runtime (GitGuardian, #1838).
const TOKEN = ['tok', 'en', '-', 'a1b2'].join('');

describe('stepUpReauth storage (#1815)', () => {
  beforeEach(() => {
    sessionStorage.clear();
    localStorage.clear();
  });

  it('keeps the pending token in sessionStorage only, under one key', () => {
    storePendingStepUpToken(TOKEN, 'account_erasure', null, 1_000);
    expect(Object.keys(sessionStorage)).toEqual([STEP_UP_REAUTH_TOKEN_KEY]);
    expect(localStorage.length).toBe(0);
    const stored = JSON.parse(sessionStorage.getItem(STEP_UP_REAUTH_TOKEN_KEY) ?? '{}');
    expect(stored).toEqual({
      token: TOKEN,
      action: 'account_erasure',
      target: null,
      expiresAt: 1_000 + 5 * 60 * 1000,
    });
  });

  it('answers the token only for its own act and only before it expires', () => {
    storePendingStepUpToken(TOKEN, 'tenant_deletion', 't-1', 0);
    expect(peekPendingStepUpToken('account_erasure', null, 1)).toBeNull();
    expect(peekPendingStepUpToken('tenant_deletion', 't-1', 1)).toBe(TOKEN);
    expect(peekPendingStepUpToken('tenant_deletion', 't-1', 5 * 60 * 1000 + 1)).toBeNull();
    // An expired token is dropped, not kept around.
    expect(sessionStorage.getItem(STEP_UP_REAUTH_TOKEN_KEY)).toBeNull();
  });

  it('answers a targeted token only for its own target, and keeps it for that one (#1884)', () => {
    storePendingStepUpToken(TOKEN, 'admin_account_update', 'user-a', 0);
    expect(peekPendingStepUpToken('admin_account_update', 'user-b', 1)).toBeNull();
    expect(consumePendingStepUpToken('admin_account_update', 'user-b', 1)).toBeNull();
    expect(peekPendingStepUpToken('admin_account_update', null, 1)).toBeNull();
    // Not dropped by the mismatch: the dialog for user A still finds it.
    expect(consumePendingStepUpToken('admin_account_update', 'user-a', 1)).toBe(TOKEN);
  });

  it('keeps the target in the resume record and refuses a malformed one (#1884)', () => {
    saveStepUpResume({
      surface: 's',
      action: 'provider_unlink',
      target: 'link-1',
      returnPath: '/account',
    });
    expect(readStepUpResume()).toMatchObject({ action: 'provider_unlink', target: 'link-1' });

    const raw = JSON.parse(sessionStorage.getItem(STEP_UP_REAUTH_RESUME_KEY) ?? '{}');
    sessionStorage.setItem(STEP_UP_REAUTH_RESUME_KEY, JSON.stringify({ ...raw, target: 42 }));
    expect(readStepUpResume()).toBeNull();
  });

  it('classifies every act as targeted or not, as the backend does (#1884)', () => {
    expect(STEP_UP_ACTIONS.filter(isTargetedStepUpAction).sort()).toEqual([
      'admin_account_erasure',
      'admin_account_update',
      'oidc_provider_change',
      'provider_unlink',
      'tenant_deletion',
    ]);
  });

  it('consumes the token once', () => {
    storePendingStepUpToken(TOKEN, 'password_change', null, Date.now());
    expect(consumePendingStepUpToken('password_change', null)).toBe(TOKEN);
    expect(consumePendingStepUpToken('password_change', null)).toBeNull();
  });

  it('ignores a malformed stored record', () => {
    sessionStorage.setItem(STEP_UP_REAUTH_TOKEN_KEY, '{not json');
    expect(peekPendingStepUpToken('account_erasure', null)).toBeNull();
  });

  it('hands a callback error marker out once, for its act only', () => {
    storeStepUpReauthError('step_up_stale', 'account_erasure');
    expect(takeStepUpReauthError('tenant_deletion')).toBeNull();
    expect(takeStepUpReauthError('account_erasure')).toBe('step_up_stale');
    expect(takeStepUpReauthError('account_erasure')).toBeNull();
  });

  it.each([
    ['/account#security', true],
    ['/admin/tenants/abc?x=1', true],
    ['/', true],
    ['//evil.example/path', false],
    ['/\\evil.example', false],
    ['https://evil.example/', false],
    ['javascript:alert(1)', false],
    ['account', false],
    ['', false],
    ['/\u0000x', false],
  ])('isSafeReturnPath(%j) === %s', (path, expected) => {
    expect(isSafeReturnPath(path)).toBe(expected);
  });
});

describe('isStepUpAction (#1847, #1857)', () => {
  it('accepts the credential-change acts, so their fresh sign-in can come back', () => {
    for (const action of [
      'api_key_creation',
      'device_pairing',
      'provider_unlink',
      'admin_account_update',
    ]) {
      expect(isStepUpAction(action)).toBe(true);
    }
  });

  it('still refuses an act the backend does not know', () => {
    expect(isStepUpAction('api_key_revocation')).toBe(false);
    expect(isStepUpAction(undefined)).toBe(false);
  });
});
