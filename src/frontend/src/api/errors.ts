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
