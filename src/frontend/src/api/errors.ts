import type { ApiErrorResponse, ApiErrorDetail } from './types';

export class ApiError extends Error {
  readonly errorId: string;
  readonly errorCode: string;
  readonly statusCode: number;
  readonly details: ApiErrorDetail[];
  readonly path: string;
  readonly method: string;

  constructor(response: ApiErrorResponse, statusCode: number) {
    super(response.message);
    this.name = 'ApiError';
    this.errorId = response.error_id;
    this.errorCode = response.error_code;
    this.statusCode = statusCode;
    // Defaulted, not trusted: `ApiErrorResponse` promises `details`, but the
    // interceptor builds this from whatever body came back — a proxy's error page
    // or an older deployment carries none, and every reader below would then walk
    // `undefined` and throw inside the caller's catch block (#1437).
    this.details = response.details ?? [];
    this.path = response.path;
    this.method = response.method;
  }
}

export function isApiError(error: unknown): error is ApiError {
  return error instanceof ApiError;
}

export function parseApiError(error: unknown): string {
  if (isApiError(error)) {
    return error.message;
  }
  if (error instanceof Error) {
    return error.message;
  }
  // Handle Redux Toolkit serialized errors (plain objects with message)
  if (typeof error === 'object' && error !== null && 'message' in error) {
    const msg = (error as { message: unknown }).message;
    if (typeof msg === 'string' && msg.length > 0) return msg;
  }
  return 'An unknown error occurred.';
}

export function getFieldErrors(error: unknown): Record<string, string> {
  if (!isApiError(error)) return {};

  const fieldErrors: Record<string, string> = {};
  for (const detail of error.details) {
    if (detail.field) {
      const fieldName = detail.field.replace(/^body\./, '');
      fieldErrors[fieldName] = detail.reason;
    }
  }
  return fieldErrors;
}

/** One field-scoped entry of a backend error envelope, with the `body.` prefix stripped. */
export interface FieldViolation {
  /** Request-body field the violation is about, e.g. `plant_keys`. */
  field: string;
  /** The backend's own wording. **English** — see {@link getFieldViolations}. */
  reason: string;
  /** Stable machine-readable marker, e.g. `watering_target_required`. */
  code: string;
}

/**
 * Field-scoped violations of an API error, `code` included.
 *
 * The difference to {@link getFieldErrors} is the `code`, and it matters
 * because `reason` is written by the backend and is **English**, while this app
 * renders German (NFR-003 keeps source and API messages English, the UI is
 * translated). Putting `reason` straight onto a form field therefore drops an
 * English sentence into a German form — which is why `HarvestCreateDialog`
 * overrides the reason it gets for a duplicate `batch_id`.
 *
 * `code` is the backend's stable contract for exactly this: a caller branches on
 * it and supplies its own translated message, while `reason` stays free to be
 * reworded. Callers that have no translation for a code should skip it and let
 * the generic validation toast stand, rather than showing the English text.
 *
 * Later entries win per field: the envelope may name one field twice, and the
 * last-checked rule is the more specific one.
 */
export function getFieldViolations(error: unknown): FieldViolation[] {
  if (!isApiError(error)) return [];

  return error.details
    .filter((detail) => !!detail.field)
    .map((detail) => ({
      field: detail.field.replace(/^body\./, ''),
      reason: detail.reason,
      code: detail.code,
    }));
}

/** Backend error code of a throttled step-up confirmation (429, #1816). */
const STEP_UP_LOCKED = 'STEP_UP_LOCKED';

/**
 * Minutes until a locked step-up may be retried, or `null` when the error is
 * not a `STEP_UP_LOCKED` refusal.
 *
 * Read from `details[].retry_after_minutes` (a string on the wire). A lockout
 * that carries no parseable wait still returns a value — the empty string — so
 * the caller shows the lockout rather than the backend's English message.
 */
export function getStepUpLockedMinutes(error: unknown): string | null {
  if (!isApiError(error)) return null;
  const detail = error.details.find((d) => d.code === STEP_UP_LOCKED);
  if (error.errorCode !== STEP_UP_LOCKED && !detail) return null;
  return detail?.retry_after_minutes ?? '';
}

/** Backend error code of a step-up code that could not be mailed (503, /code-review of #1862). */
const STEP_UP_CODE_UNDELIVERABLE = 'STEP_UP_CODE_UNDELIVERABLE';

/** Backend error code of a step-up that needs the e-mailed one-time code (401, #1815). */
const STEP_UP_CODE_REQUIRED = 'STEP_UP_CODE_REQUIRED';

/**
 * Whether the backend refused a step-up because the requester has no local
 * password and sent no e-mailed code (401 `STEP_UP_CODE_REQUIRED`, #1815).
 *
 * This is positive proof that the account confirms with a code, not a password.
 */
export function isStepUpCodeRequired(error: unknown): boolean {
  if (!isApiError(error)) return false;
  return (
    error.errorCode === STEP_UP_CODE_REQUIRED ||
    error.details.some((d) => d.code === STEP_UP_CODE_REQUIRED)
  );
}

/** Backend error code of a step-up that needs a fresh sign-in at the identity provider (401/422, #1815). */
const STEP_UP_REAUTH_REQUIRED = 'STEP_UP_REAUTH_REQUIRED';

/**
 * Whether the backend refused a step-up because the requester confirms by
 * signing in again at a linked identity provider (#1815): 401
 * `STEP_UP_REAUTH_REQUIRED` on the act itself (`details[0].field` is
 * `step_up_token`), or 422 with the same code when an e-mailed code was
 * requested for an account whose provider can prove a fresh sign-in.
 *
 * Positive proof that the account has no local password and should be offered
 * the "sign in again" button rather than the code form.
 */
export function isStepUpReauthRequired(error: unknown): boolean {
  if (!isApiError(error)) return false;
  return (
    error.errorCode === STEP_UP_REAUTH_REQUIRED ||
    error.details.some((d) => d.code === STEP_UP_REAUTH_REQUIRED)
  );
}

/** 422 from `POST /users/me/step-up/oidc` or `/step-up-code`: the account has a password — ask for it (#1815). */
const STEP_UP_PASSWORD_REQUIRED = 'STEP_UP_PASSWORD_REQUIRED';

/** 422 from `POST /users/me/step-up/oidc`: no linked provider can re-authenticate — the e-mailed code applies (#1815). */
const STEP_UP_REAUTH_UNAVAILABLE = 'STEP_UP_REAUTH_UNAVAILABLE';

function hasErrorCode(error: unknown, code: string): boolean {
  if (!isApiError(error)) return false;
  return error.errorCode === code || error.details.some((d) => d.code === code);
}

/** Whether the backend said the account confirms with its password (422 `STEP_UP_PASSWORD_REQUIRED`). */
export function isStepUpPasswordRequired(error: unknown): boolean {
  return hasErrorCode(error, STEP_UP_PASSWORD_REQUIRED);
}

/** Whether the backend said no linked provider can prove a fresh sign-in (422 `STEP_UP_REAUTH_UNAVAILABLE`). */
export function isStepUpReauthUnavailable(error: unknown): boolean {
  return hasErrorCode(error, STEP_UP_REAUTH_UNAVAILABLE);
}

/**
 * Whether the backend refused the **step-up itself** — a wrong or missing
 * factor (401) or the lockout (429). Only then is a sent step-up token spent;
 * any other refusal (e.g. 422 for a too-short new password) leaves it valid.
 */
export function isStepUpRejection(error: unknown): boolean {
  return isApiError(error) && (error.statusCode === 401 || error.statusCode === 429);
}

/**
 * The error codes the backend puts on `/auth/step-up/callback?error=…` (#1815),
 * mapped to their translation. Anything else reads as `step_up_failed`: the
 * query value is never rendered raw.
 */
const STEP_UP_REAUTH_CALLBACK_ERROR_KEYS: Readonly<Record<string, string>> = {
  step_up_failed: 'pages.auth.stepUpReauthFailed',
  step_up_stale: 'pages.auth.stepUpReauthStale',
  step_up_cancelled: 'pages.auth.stepUpReauthCancelled',
};

/** A whitelisted step-up callback error code; an unknown value becomes `step_up_failed`. */
export function normalizeStepUpReauthCallbackError(code: string | null | undefined): string {
  return code && Object.prototype.hasOwnProperty.call(STEP_UP_REAUTH_CALLBACK_ERROR_KEYS, code) ? code : 'step_up_failed';
}

type Translate = (key: string, options?: Record<string, unknown>) => string;

/**
 * The message a step-up surface shows for a failed confirmation.
 *
 * One place for every irreversible action guarded by a step-up (tenant and
 * account deletion, the Art. 17 erasure request, the password change): a
 * `STEP_UP_LOCKED` refusal becomes the translated lockout with its minutes, a
 * `STEP_UP_REAUTH_REQUIRED` refusal asks for a fresh sign-in at the identity
 * provider, a `STEP_UP_CODE_REQUIRED` one for the e-mailed code, anything else
 * falls back to {@link parseApiError}.
 */
export function getStepUpErrorMessage(error: unknown, t: Translate): string {
  if (isStepUpReauthRequired(error)) return t('pages.auth.stepUpReauthRequired');
  if (isStepUpPasswordRequired(error)) return t('pages.auth.stepUpCodeNotNeeded');
  if (isStepUpReauthUnavailable(error)) return t('pages.auth.stepUpReauthUnavailable');
  if (isStepUpCodeRequired(error)) return t('pages.auth.stepUpCodeRequired');
  // 503: the code could not be mailed; only the operator can fix that (/code-review of #1862).
  if (isApiError(error) && error.errorCode === STEP_UP_CODE_UNDELIVERABLE) {
    return t('pages.auth.stepUpCodeUndeliverable');
  }
  const minutes = getStepUpLockedMinutes(error);
  if (minutes === null) return parseApiError(error);
  return minutes
    ? t('pages.auth.stepUpLocked', { minutes })
    : t('pages.auth.stepUpLockedNoMinutes');
}

/**
 * The message for a failed fresh sign-in reported by `/auth/step-up/callback`
 * (#1815): failed, stale (the provider sign-in was older than five minutes — try
 * again) or cancelled.
 */
export function getStepUpReauthCallbackErrorMessage(code: string, t: Translate): string {
  return t(STEP_UP_REAUTH_CALLBACK_ERROR_KEYS[normalizeStepUpReauthCallbackError(code)]);
}
