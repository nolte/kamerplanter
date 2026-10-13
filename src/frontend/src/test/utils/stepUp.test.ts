import { describe, it, expect } from 'vitest';
import { hasLocalPasswordFromProviders, toCredentialStepUpBody, toStepUpBody } from '@/utils/stepUp';
import type { AuthProviderInfo } from '@/api/types';

function list(...providers: string[]): AuthProviderInfo[] {
  return providers.map((provider, i) => ({
    key: `p-${i}`,
    provider,
    provider_email: null,
    provider_display_name: null,
    linked_at: null,
    last_used_at: null,
  })) as AuthProviderInfo[];
}

describe('hasLocalPasswordFromProviders (#1842)', () => {
  it('is unknown for a missing or empty list (fail closed)', () => {
    expect(hasLocalPasswordFromProviders(null)).toBeNull();
    expect(hasLocalPasswordFromProviders(undefined)).toBeNull();
    expect(hasLocalPasswordFromProviders([])).toBeNull();
  });

  it('is true when the list names `local`', () => {
    expect(hasLocalPasswordFromProviders(list('google', 'local'))).toBe(true);
  });

  it('is false only for a non-empty list without `local`', () => {
    expect(hasLocalPasswordFromProviders(list('google'))).toBe(false);
  });
});

describe('toStepUpBody (#1815)', () => {
  it('carries only what was supplied, in the backend naming', () => {
    const password = ['s3', 'cret'].join('');
    const code = '4'.repeat(6);
    expect(toStepUpBody({})).toEqual({});
    expect(toStepUpBody({ password })).toEqual({ password });
    expect(toStepUpBody({ code })).toEqual({ step_up_code: code });
    expect(toStepUpBody({ password, code })).toEqual({ password, step_up_code: code });
  });
});

describe('toCredentialStepUpBody (#1847, #1857)', () => {
  it('names the password `current_password` and carries only what was supplied', () => {
    const password = ['s3', 'cret'].join('');
    const code = '4'.repeat(6);
    const token = ['to', 'ken'].join('');
    expect(toCredentialStepUpBody({})).toEqual({});
    expect(toCredentialStepUpBody({ password })).toEqual({ current_password: password });
    expect(toCredentialStepUpBody({ code })).toEqual({ step_up_code: code });
    expect(toCredentialStepUpBody({ token })).toEqual({ step_up_token: token });
    // The erasure naming (`password`) must not leak into a credential change:
    // the backend's CredentialStepUp would silently ignore it and answer 401.
    expect(toCredentialStepUpBody({ password })).not.toHaveProperty('password');
  });
});
