import { describe, it, expect, afterEach, vi } from 'vitest';
import { AxiosError, AxiosHeaders } from 'axios';
import { ApiError } from '@/api/errors';
import type { ApiErrorResponse } from '@/api/types';
import {
  TENANT_IMPORT_DEFAULT_MAX_UPLOAD_MB,
  archiveStepUpTarget,
  describeImportRefusal,
  exceedsDefaultCeiling,
  failureCodeKey,
  formatArchiveSize,
  isActiveImport,
  isStepUpRefusal,
  looksLikeZip,
} from '@/utils/tenantImport';

/**
 * REQ-056 §8.4 (#2138) — the helpers of the import page: the step-up target bound to the archive's
 * hash, the size hint against the server's default ceiling, and the reading of a refusal.
 */

function apiError(status: number, body: Partial<ApiErrorResponse>): ApiError {
  return new ApiError(
    {
      error_id: 'e',
      error_code: 'X',
      message: 'English',
      details: [],
      timestamp: '',
      path: '/admin/platform/tenant-imports',
      method: 'POST',
      ...body,
    } as ApiErrorResponse,
    status,
  );
}

function axiosError(status?: number): AxiosError {
  const config = { headers: new AxiosHeaders() };
  return new AxiosError(
    'Request failed',
    status === undefined ? 'ERR_NETWORK' : 'ERR_BAD_RESPONSE',
    config,
    undefined,
    status === undefined
      ? undefined
      : { status, statusText: '', headers: {}, config, data: '<html>413</html>' },
  );
}

describe('archiveStepUpTarget', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('binds to "archive:" and the first 32 hex digits of the SHA-256, as the backend does', async () => {
    // sha256("abc") = ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad
    const target = await archiveStepUpTarget(new Blob(['abc']));
    expect(target).toBe('archive:ba7816bf8f01cfea414140de5dae2223');
  });

  it('yields no target where the browser offers no Web Crypto (insecure context)', async () => {
    vi.stubGlobal('crypto', {});
    expect(await archiveStepUpTarget(new Blob(['abc']))).toBeUndefined();
  });
});

describe('size and type hints', () => {
  it('formats sizes in kB below one MB and in MB above', () => {
    expect(formatArchiveSize(10)).toMatch(/^1 kB$/);
    expect(formatArchiveSize(3 * 1024 * 1024)).toMatch(/^3 MB$/);
  });

  it('warns only above the default ceiling of TENANT_IMPORT_MAX_UPLOAD_MB', () => {
    const ceiling = TENANT_IMPORT_DEFAULT_MAX_UPLOAD_MB * 1024 * 1024;
    expect(TENANT_IMPORT_DEFAULT_MAX_UPLOAD_MB).toBe(512);
    expect(exceedsDefaultCeiling(ceiling)).toBe(false);
    expect(exceedsDefaultCeiling(ceiling + 1)).toBe(true);
  });

  it('recognises a ZIP by its name or its type', () => {
    expect(looksLikeZip(new File(['x'], 'garden.ZIP'))).toBe(true);
    expect(looksLikeZip(new File(['x'], 'garden', { type: 'application/zip' }))).toBe(true);
    expect(looksLikeZip(new File(['x'], 'garden.csv', { type: 'text/csv' }))).toBe(false);
  });
});

describe('import states', () => {
  it('is active while pending, validating or running', () => {
    expect(isActiveImport('pending')).toBe(true);
    expect(isActiveImport('validating')).toBe(true);
    expect(isActiveImport('running')).toBe(true);
    expect(isActiveImport('completed')).toBe(false);
    expect(isActiveImport('failed')).toBe(false);
    expect(isActiveImport('cleanup_pending')).toBe(false);
  });

  it('maps a known failure code to itself and anything else to UNKNOWN', () => {
    expect(failureCodeKey('IMPORT_ABANDONED')).toBe('IMPORT_ABANDONED');
    expect(failureCodeKey('SOMETHING_NEW')).toBe('UNKNOWN');
    expect(failureCodeKey(null)).toBe('UNKNOWN');
  });
});

describe('isStepUpRefusal', () => {
  it('treats a refused factor, a lockout and a step-up code as the dialog’s business', () => {
    expect(isStepUpRefusal(apiError(401, { error_code: 'UNAUTHORIZED' }))).toBe(true);
    expect(isStepUpRefusal(apiError(429, { error_code: 'STEP_UP_LOCKED' }))).toBe(true);
    expect(isStepUpRefusal(apiError(422, { error_code: 'STEP_UP_REAUTH_REQUIRED' }))).toBe(true);
    expect(
      isStepUpRefusal(
        apiError(422, {
          error_code: 'VALIDATION_ERROR',
          details: [{ field: 'step_up_code', reason: 'x', code: 'STEP_UP_CODE_REQUIRED' }],
        }),
      ),
    ).toBe(true);
  });

  it('leaves archive, quota, size and rate refusals to the page', () => {
    expect(isStepUpRefusal(apiError(422, { error_code: 'IMPORT_CHECKSUM_MISMATCH' }))).toBe(false);
    expect(isStepUpRefusal(apiError(409, { error_code: 'STORAGE_QUOTA_EXCEEDED' }))).toBe(false);
    expect(isStepUpRefusal(apiError(413, { error_code: 'PAYLOAD_TOO_LARGE' }))).toBe(false);
    expect(isStepUpRefusal(apiError(429, { error_code: 'RATE_LIMIT_EXCEEDED' }))).toBe(false);
    expect(isStepUpRefusal(axiosError(413))).toBe(false);
  });
});

describe('describeImportRefusal', () => {
  it('lists the offending entries of an IMPORT_* refusal', () => {
    const refusal = describeImportRefusal(
      apiError(422, {
        error_code: 'IMPORT_MISSING_CATALOG_ENTRIES',
        message: 'The archive points at catalogue entries this installation does not have.',
        details: [
          { field: 'archive', reason: 'species/abc', code: 'IMPORT_MISSING_CATALOG_ENTRIES' },
          { field: 'archive', reason: 'cultivars/def', code: 'IMPORT_MISSING_CATALOG_ENTRIES' },
        ],
      }),
    );
    expect(refusal.code).toBe('IMPORT_MISSING_CATALOG_ENTRIES');
    expect(refusal.entries).toEqual(['species/abc', 'cultivars/def']);
  });

  it('drops a detail that only repeats the message (a refusal without entries)', () => {
    const message = 'The archive checksums do not match.';
    const refusal = describeImportRefusal(
      apiError(422, {
        error_code: 'IMPORT_CHECKSUM_MISMATCH',
        message,
        details: [{ field: 'archive', reason: message, code: 'IMPORT_CHECKSUM_MISMATCH' }],
      }),
    );
    expect(refusal.entries).toEqual([]);
  });

  it('does not list the reason of a quota refusal as an entry', () => {
    const refusal = describeImportRefusal(
      apiError(422, {
        error_code: 'MEMBER_LIMIT_REACHED',
        details: [
          {
            field: 'tenant',
            reason: 'The tenant admits at most 5 active members.',
            code: 'MEMBER_LIMIT_REACHED',
          },
        ],
      }),
    );
    expect(refusal.code).toBe('MEMBER_LIMIT_REACHED');
    expect(refusal.entries).toEqual([]);
  });

  it('reads the ceiling the server named in a 413', () => {
    const route = describeImportRefusal(
      apiError(413, {
        error_code: 'PAYLOAD_TOO_LARGE',
        message: 'File exceeds maximum allowed size of 512 MB.',
      }),
    );
    expect(route).toMatchObject({ code: 'PAYLOAD_TOO_LARGE', limitMb: 512 });
    const body = describeImportRefusal(
      apiError(413, {
        error_code: 'REQUEST_BODY_TOO_LARGE',
        message: 'Request body exceeds the maximum allowed size of 26 MB.',
      }),
    );
    expect(body).toMatchObject({ code: 'REQUEST_BODY_TOO_LARGE', limitMb: 26 });
  });

  it('reads any other 413 as too large, without a limit when none was named', () => {
    expect(
      describeImportRefusal(apiError(413, { error_code: 'SOMETHING', message: 'nope' })),
    ).toMatchObject({
      code: 'PAYLOAD_TOO_LARGE',
      limitMb: null,
    });
    expect(describeImportRefusal(axiosError(413))).toMatchObject({
      code: 'PAYLOAD_TOO_LARGE',
      limitMb: null,
    });
  });

  it('reads a lost connection as NETWORK and another bare status as UNKNOWN', () => {
    expect(describeImportRefusal(axiosError())).toMatchObject({ code: 'NETWORK' });
    expect(describeImportRefusal(axiosError(502))).toMatchObject({
      code: 'UNKNOWN',
      rawCode: '502',
    });
  });

  it('keeps an unknown code verbatim beside the server message', () => {
    expect(
      describeImportRefusal(
        apiError(422, { error_code: 'IMPORT_SOMETHING_NEW', message: 'New rule.' }),
      ),
    ).toMatchObject({ code: 'UNKNOWN', rawCode: 'IMPORT_SOMETHING_NEW', message: 'New rule.' });
    expect(describeImportRefusal(new Error('boom'))).toMatchObject({
      code: 'UNKNOWN',
      message: 'boom',
    });
  });
});
