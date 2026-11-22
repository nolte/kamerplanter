import { describe, it, expect } from 'vitest';
import { ApiError, isApiError, parseApiError, getFieldErrors } from '@/api/errors';

describe('ApiError', () => {
  const errorResponse = {
    error_id: 'err_123',
    error_code: 'VALIDATION_ERROR',
    message: 'The input data is invalid.',
    details: [
      { field: 'body.name', reason: 'Field is required', code: 'missing' },
      { field: 'body.type', reason: 'Invalid value', code: 'invalid' },
    ],
    timestamp: '2024-01-01T00:00:00Z',
    path: '/api/v1/species',
    method: 'POST',
  };

  it('creates ApiError from response', () => {
    const err = new ApiError(errorResponse, 422);
    expect(err.message).toBe('The input data is invalid.');
    expect(err.errorCode).toBe('VALIDATION_ERROR');
    expect(err.statusCode).toBe(422);
    expect(err.errorId).toBe('err_123');
    expect(err.details).toHaveLength(2);
  });

  it('isApiError returns true for ApiError', () => {
    const err = new ApiError(errorResponse, 422);
    expect(isApiError(err)).toBe(true);
  });

  it('isApiError returns false for plain Error', () => {
    expect(isApiError(new Error('test'))).toBe(false);
  });

  // FRONTEND.md §10.3 / #3013: the stable code decides, the English `message` never comes back.
  const t = (key: string) => `t:${key}`;

  it('parseApiError resolves the error code, not the English message', () => {
    const err = new ApiError(errorResponse, 422);
    expect(parseApiError(err, t)).toBe('t:errors.validation');
  });

  it('parseApiError maps a plain Error to the generic fallback, not its message', () => {
    expect(parseApiError(new Error('network fail'), t)).toBe('t:errors.generic');
  });

  it('parseApiError handles unknown input with the generic fallback', () => {
    expect(parseApiError('string error', t)).toBe('t:errors.generic');
  });

  it('parseApiError reads the code of a Redux serialized error and ignores its message', () => {
    const serialized = { name: 'ApiError', message: 'Invalid email or password.', code: 'ENTITY_NOT_FOUND' };
    expect(parseApiError(serialized, t)).toBe('t:errors.notFound');
  });

  it('parseApiError ignores the message of a serialized error without a code', () => {
    expect(parseApiError({ message: 'English text' }, t)).toBe('t:errors.generic');
  });

  it('getFieldErrors maps body. fields correctly', () => {
    const err = new ApiError(errorResponse, 422);
    const fields = getFieldErrors(err);
    expect(fields).toEqual({
      name: 'Field is required',
      type: 'Invalid value',
    });
  });

  it('getFieldErrors returns empty for non-ApiError', () => {
    expect(getFieldErrors(new Error('test'))).toEqual({});
  });
});
