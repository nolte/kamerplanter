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

type Translate = (key: string, options?: Record<string, unknown>) => string;

/**
 * The message a step-up surface shows for a failed confirmation.
 *
 * One place for every irreversible action guarded by a step-up (tenant and
 * account deletion, the Art. 17 erasure request, the password change): a
 * `STEP_UP_LOCKED` refusal becomes the translated lockout with its minutes,
 * anything else falls back to {@link parseApiError}.
 */
export function getStepUpErrorMessage(error: unknown, t: Translate): string {
  const minutes = getStepUpLockedMinutes(error);
  if (minutes === null) return parseApiError(error);
  return minutes
    ? t('pages.auth.stepUpLocked', { minutes })
    : t('pages.auth.stepUpLockedNoMinutes');
}
