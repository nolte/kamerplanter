import { describe, it, expect, beforeEach } from 'vitest';
import {
  STEP_UP_REAUTH_TOKEN_KEY,
  consumePendingStepUpToken,
  isSafeReturnPath,
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
    storePendingStepUpToken(TOKEN, 'account_erasure', 1_000);
    expect(Object.keys(sessionStorage)).toEqual([STEP_UP_REAUTH_TOKEN_KEY]);
    expect(localStorage.length).toBe(0);
    const stored = JSON.parse(sessionStorage.getItem(STEP_UP_REAUTH_TOKEN_KEY) ?? '{}');
    expect(stored).toEqual({ token: TOKEN, action: 'account_erasure', expiresAt: 1_000 + 5 * 60 * 1000 });
  });

  it('answers the token only for its own act and only before it expires', () => {
    storePendingStepUpToken(TOKEN, 'tenant_deletion', 0);
    expect(peekPendingStepUpToken('account_erasure', 1)).toBeNull();
    expect(peekPendingStepUpToken('tenant_deletion', 1)).toBe(TOKEN);
    expect(peekPendingStepUpToken('tenant_deletion', 5 * 60 * 1000 + 1)).toBeNull();
    // An expired token is dropped, not kept around.
    expect(sessionStorage.getItem(STEP_UP_REAUTH_TOKEN_KEY)).toBeNull();
  });

  it('consumes the token once', () => {
    storePendingStepUpToken(TOKEN, 'password_change', Date.now());
    expect(consumePendingStepUpToken('password_change')).toBe(TOKEN);
    expect(consumePendingStepUpToken('password_change')).toBeNull();
  });

  it('ignores a malformed stored record', () => {
    sessionStorage.setItem(STEP_UP_REAUTH_TOKEN_KEY, '{not json');
    expect(peekPendingStepUpToken('account_erasure')).toBeNull();
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
