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
    this.details = response.details;
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
