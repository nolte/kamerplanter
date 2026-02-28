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

  it('parseApiError extracts message', () => {
    const err = new ApiError(errorResponse, 422);
    expect(parseApiError(err)).toBe('The input data is invalid.');
  });

  it('parseApiError handles plain Error', () => {
    expect(parseApiError(new Error('network fail'))).toBe('network fail');
  });

  it('parseApiError handles unknown', () => {
    expect(parseApiError('string error')).toBe('An unknown error occurred.');
  });

  it('parseApiError handles Redux serialized error (plain object with message)', () => {
    const serialized = { name: 'ApiError', message: 'Invalid email or password.' };
    expect(parseApiError(serialized)).toBe('Invalid email or password.');
  });

  it('parseApiError rejects empty message in plain object', () => {
    expect(parseApiError({ message: '' })).toBe('An unknown error occurred.');
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
