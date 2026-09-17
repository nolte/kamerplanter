import { describe, it, expect } from 'vitest';
import { ApiError, getFieldErrors, getFieldViolations, isApiError } from '@/api/errors';
import type { ApiErrorResponse } from '@/api/types';

function envelope(details: ApiErrorResponse['details']): ApiError {
  return new ApiError(
    {
      error_id: 'err_1',
      error_code: 'VALIDATION_ERROR',
      message: 'The input data is invalid.',
      details,
      timestamp: '2026-08-07T00:00:00Z',
      path: '/api/v1/t/test-tenant/watering-logs',
      method: 'POST',
    },
    422,
  );
}

describe('getFieldViolations', () => {
  it('strips the body prefix and keeps the violation code', () => {
    // The `code` is the reason this exists next to getFieldErrors: it is the
    // backend's stable marker, so a caller can supply its own translated
    // message instead of showing the English `reason` in a translated UI.
    const violations = getFieldViolations(
      envelope([
        {
          field: 'body.slot_keys',
          reason: 'At least one of slot_keys or plant_keys must be provided',
          code: 'watering_target_required',
        },
      ]),
    );

    expect(violations).toEqual([
      {
        field: 'slot_keys',
        reason: 'At least one of slot_keys or plant_keys must be provided',
        code: 'watering_target_required',
      },
    ]);
  });

  it('keeps every entry when one field breaks two rules', () => {
    // getFieldErrors collapses to one message per field; a caller that
    // translates per code needs all of them, so this must not deduplicate.
    const violations = getFieldViolations(
      envelope([
        { field: 'body.is_supplemental', reason: 'a', code: 'rule_one' },
        { field: 'body.is_supplemental', reason: 'b', code: 'rule_two' },
      ]),
    );

    expect(violations.map((v) => v.code)).toEqual(['rule_one', 'rule_two']);
    expect(getFieldErrors(envelope([
      { field: 'body.is_supplemental', reason: 'a', code: 'rule_one' },
      { field: 'body.is_supplemental', reason: 'b', code: 'rule_two' },
    ]))).toEqual({ is_supplemental: 'b' });
  });

  it('drops entries that name no field', () => {
    const violations = getFieldViolations(
      envelope([
        { field: '', reason: 'body-level complaint', code: 'value_error' },
        { field: 'body.volume_liters', reason: 'must be > 0', code: 'greater_than' },
      ]),
    );

    expect(violations.map((v) => v.field)).toEqual(['volume_liters']);
  });

  it('returns nothing for an error that is not an API envelope', () => {
    expect(getFieldViolations(new Error('Network Error'))).toEqual([]);
    expect(getFieldViolations(undefined)).toEqual([]);
    expect(isApiError(new Error('Network Error'))).toBe(false);
  });

  it('leaves a field name without the body prefix untouched', () => {
    // Query- and path-parameter errors are located as `query.…` / `path.…`;
    // only the body prefix is stripped, so those stay distinguishable.
    const violations = getFieldViolations(
      envelope([{ field: 'query.limit', reason: 'too large', code: 'less_than_equal' }]),
    );

    expect(violations[0].field).toBe('query.limit');
  });
});

/**
 * An envelope that carries no `details` at all.
 *
 * `ApiErrorResponse` declares `details` as required, and the interceptor builds
 * the error straight from whatever the response body was — so the declaration is
 * a promise about the *backend*, not about the value in hand. A proxy's own error
 * page, an older deployment, or any non-envelope 4xx body leaves the field
 * missing, and every reader here then walks `undefined`.
 *
 * Found by the #1437 work: `PhotoUpload` reads `err.details[0]?.entity` to decide
 * whether a 404 means the attachment is gone, and a 404 without `details` threw a
 * `TypeError` inside the catch block — turning a handled failure into an unhandled
 * rejection with no message shown at all. Defaulted in the constructor, once,
 * rather than at each reader.
 */
describe('an error envelope without details', () => {
  function bodyWithoutDetails(): ApiError {
    const body = {
      error_id: 'err_2',
      error_code: 'ENTITY_NOT_FOUND',
      message: 'gone',
      timestamp: '2026-09-16T00:00:00Z',
      path: '/api/v1/t/test-tenant/tasks/tk1/photos/att-1',
      method: 'DELETE',
    } as unknown as ApiErrorResponse;
    return new ApiError(body, 404);
  }

  it('reads as an empty detail list rather than undefined', () => {
    expect(bodyWithoutDetails().details).toEqual([]);
  });

  it('lets the field readers run instead of throwing', () => {
    expect(getFieldViolations(bodyWithoutDetails())).toEqual([]);
    expect(getFieldErrors(bodyWithoutDetails())).toEqual({});
  });
});
