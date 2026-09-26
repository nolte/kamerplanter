import { describe, it, expect } from 'vitest';
import { ApiError, getStepUpErrorMessage, getStepUpLockedMinutes, isStepUpCodeRequired } from '@/api/errors';
import type { ApiErrorDetail } from '@/api/types';

/**
 * #1816 — a throttled step-up answers 429 `STEP_UP_LOCKED` with the wait in
 * `details[0].retry_after_minutes` (a string). Every step-up surface maps it
 * through one helper so the lockout reads the same everywhere.
 */

function apiError(status: number, errorCode: string, details: ApiErrorDetail[] = []): ApiError {
  return new ApiError(
    {
      error_id: 'e',
      error_code: errorCode,
      message: 'Backend English message.',
      details,
      timestamp: '',
      path: '/x',
      method: 'DELETE',
    },
    status,
  );
}

const t = (key: string, options?: Record<string, unknown>) =>
  options ? `${key}:${JSON.stringify(options)}` : key;

describe('getStepUpLockedMinutes', () => {
  it('reads the minutes from the STEP_UP_LOCKED detail', () => {
    const err = apiError(429, 'STEP_UP_LOCKED', [
      { field: 'password', reason: 'locked', code: 'STEP_UP_LOCKED', retry_after_minutes: '15' },
    ]);
    expect(getStepUpLockedMinutes(err)).toBe('15');
  });

  it('answers the empty string for a lockout without a wait', () => {
    expect(getStepUpLockedMinutes(apiError(429, 'STEP_UP_LOCKED'))).toBe('');
  });

  it('answers null for any other error', () => {
    expect(getStepUpLockedMinutes(apiError(401, 'UNAUTHORIZED'))).toBeNull();
    expect(getStepUpLockedMinutes(apiError(429, 'RATE_LIMITED'))).toBeNull();
    expect(getStepUpLockedMinutes(new Error('network'))).toBeNull();
  });
});

describe('getStepUpErrorMessage', () => {
  it('translates the lockout with its minutes', () => {
    const err = apiError(429, 'STEP_UP_LOCKED', [
      { field: 'password', reason: 'locked', code: 'STEP_UP_LOCKED', retry_after_minutes: '7' },
    ]);
    expect(getStepUpErrorMessage(err, t)).toBe('pages.auth.stepUpLocked:{"minutes":"7"}');
  });

  it('falls back to the generic lockout wording without minutes', () => {
    expect(getStepUpErrorMessage(apiError(429, 'STEP_UP_LOCKED'), t)).toBe('pages.auth.stepUpLockedNoMinutes');
  });

  it('passes every other error through parseApiError', () => {
    expect(getStepUpErrorMessage(apiError(401, 'UNAUTHORIZED'), t)).toBe('Backend English message.');
  });
});

describe('STEP_UP_CODE_REQUIRED (#1815)', () => {
  it('is recognised by isStepUpCodeRequired', () => {
    expect(isStepUpCodeRequired(apiError(401, 'STEP_UP_CODE_REQUIRED'))).toBe(true);
    expect(isStepUpCodeRequired(apiError(401, 'UNAUTHORIZED'))).toBe(false);
    expect(isStepUpCodeRequired(new Error('network'))).toBe(false);
  });

  it('is translated by getStepUpErrorMessage', () => {
    expect(getStepUpErrorMessage(apiError(401, 'STEP_UP_CODE_REQUIRED'), t)).toBe('pages.auth.stepUpCodeRequired');
  });
});

describe('STEP_UP_CODE_UNDELIVERABLE (/code-review of #1862)', () => {
  it('reads as the translated "cannot be delivered, ask the operator" message', () => {
    expect(getStepUpErrorMessage(apiError(503, 'STEP_UP_CODE_UNDELIVERABLE'), t)).toBe(
      'pages.auth.stepUpCodeUndeliverable',
    );
  });

  it('has a translation in both languages', async () => {
    const de = (await import('@/i18n/locales/de/pages.json')).default;
    const en = (await import('@/i18n/locales/en/pages.json')).default;
    expect(de.pages.auth.stepUpCodeUndeliverable).toMatch(/Betreiber/);
    expect(en.pages.auth.stepUpCodeUndeliverable).toMatch(/operator/);
  });
});
