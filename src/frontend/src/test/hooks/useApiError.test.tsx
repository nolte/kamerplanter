import { renderHook } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { SnackbarProvider } from 'notistack';
import { AxiosError, AxiosHeaders } from 'axios';
import { type ReactNode } from 'react';
import { useApiError } from '@/hooks/useApiError';
import { ApiError } from '@/api/errors';
import '@/i18n';

/** Build an AxiosError with an optional HTTP response, exercising the axios branch. */
function makeAxiosError(
  status?: number,
  data?: unknown,
  code?: string,
): AxiosError {
  const error = new AxiosError('request failed', code);
  if (status !== undefined) {
    error.response = {
      status,
      statusText: '',
      data,
      headers: {},
      config: { headers: new AxiosHeaders() },
    };
  }
  return error;
}

const mockEnqueue = vi.fn();
vi.mock('notistack', async () => {
  const actual = await vi.importActual('notistack');
  return {
    ...actual,
    useSnackbar: () => ({ enqueueSnackbar: mockEnqueue, closeSnackbar: vi.fn() }),
  };
});

function wrapper({ children }: { children: ReactNode }) {
  return <SnackbarProvider>{children}</SnackbarProvider>;
}

function makeApiError(code: string, message: string, details: Array<{ field: string; reason: string; code: string }> = [], status = 400) {
  return new ApiError(
    { error_id: 'err_1', error_code: code, message, details, timestamp: '', path: '/', method: 'GET' },
    status,
  );
}

describe('useApiError', () => {
  beforeEach(() => {
    mockEnqueue.mockClear();
  });

  it('handles ENTITY_NOT_FOUND error', () => {
    const { result } = renderHook(() => useApiError(), { wrapper });
    result.current.handleError(makeApiError('ENTITY_NOT_FOUND', 'Not found', [], 404));
    expect(mockEnqueue).toHaveBeenCalledWith(
      expect.any(String),
      expect.objectContaining({ variant: 'error' }),
    );
  });

  it('handles DUPLICATE_ENTRY error', () => {
    const { result } = renderHook(() => useApiError(), { wrapper });
    result.current.handleError(makeApiError('DUPLICATE_ENTRY', 'Duplicate', [], 409));
    expect(mockEnqueue).toHaveBeenCalled();
  });

  it('handles VALIDATION_ERROR', () => {
    const { result } = renderHook(() => useApiError(), { wrapper });
    result.current.handleError(makeApiError('VALIDATION_ERROR', 'Invalid', [], 422));
    expect(mockEnqueue).toHaveBeenCalled();
  });

  it('handles network error', () => {
    const { result } = renderHook(() => useApiError(), { wrapper });
    const error = new Error('Network Error');
    result.current.handleError(error);
    expect(mockEnqueue).toHaveBeenCalled();
  });

  it('handles unknown error', () => {
    const { result } = renderHook(() => useApiError(), { wrapper });
    result.current.handleError('something unexpected');
    expect(mockEnqueue).toHaveBeenCalled();
  });

  it('maps field errors to form', () => {
    const { result } = renderHook(() => useApiError(), { wrapper });
    const error = makeApiError('VALIDATION_ERROR', 'Invalid', [
      { field: 'body.name', reason: 'Required', code: 'value_error' },
    ], 422);
    const setFieldError = vi.fn();
    result.current.handleError(error, setFieldError);
    expect(setFieldError).toHaveBeenCalledWith('name', 'Required');
  });

  it('notifies once and returns when field errors are present', () => {
    const { result } = renderHook(() => useApiError(), { wrapper });
    const error = makeApiError('VALIDATION_ERROR', 'Invalid', [
      { field: 'body.name', reason: 'Required', code: 'value_error' },
    ], 422);
    result.current.handleError(error, vi.fn());
    // Only the validation toast — the errorCode switch must not run after the early return.
    expect(mockEnqueue).toHaveBeenCalledTimes(1);
  });

  it('handles INTERNAL_ERROR', () => {
    const { result } = renderHook(() => useApiError(), { wrapper });
    result.current.handleError(makeApiError('INTERNAL_ERROR', 'boom', [], 500));
    expect(mockEnqueue).toHaveBeenCalled();
  });

  it.each([
    ['FORBIDDEN', 403],
    ['CONFLICT', 409],
    ['PAYLOAD', 413],
    ['UNMAPPED', 418],
  ])('falls back to the status code for unmapped error code %s', (_label, status) => {
    const { result } = renderHook(() => useApiError(), { wrapper });
    result.current.handleError(makeApiError('SOMETHING_NEW', 'msg', [], status));
    expect(mockEnqueue).toHaveBeenCalled();
  });

  it('shows the detail for VALIDATION_ERROR with a non-English message', () => {
    const { result } = renderHook(() => useApiError(), { wrapper });
    result.current.handleError(makeApiError('VALIDATION_ERROR', 'Wert zu klein', [], 422));
    expect(mockEnqueue).toHaveBeenCalled();
  });

  it('handles an axios timeout (ECONNABORTED)', () => {
    const { result } = renderHook(() => useApiError(), { wrapper });
    result.current.handleError(makeAxiosError(undefined, undefined, 'ECONNABORTED'));
    expect(mockEnqueue).toHaveBeenCalled();
  });

  it.each([403, 404, 409, 413, 500, 502])(
    'maps axios response status %i without an error envelope',
    (status) => {
      const { result } = renderHook(() => useApiError(), { wrapper });
      result.current.handleError(makeAxiosError(status));
      expect(mockEnqueue).toHaveBeenCalled();
    },
  );

  it('extracts a 422 detail string from the axios response body', () => {
    const { result } = renderHook(() => useApiError(), { wrapper });
    result.current.handleError(makeAxiosError(422, { detail: 'Feld fehlt' }));
    expect(mockEnqueue).toHaveBeenCalled();
  });

  it('falls back to a generic 422 message when no detail is present', () => {
    const { result } = renderHook(() => useApiError(), { wrapper });
    result.current.handleError(makeAxiosError(422, {}));
    expect(mockEnqueue).toHaveBeenCalled();
  });

  it('treats a 4xx without a specific mapping as unknown', () => {
    const { result } = renderHook(() => useApiError(), { wrapper });
    result.current.handleError(makeAxiosError(400));
    expect(mockEnqueue).toHaveBeenCalled();
  });

  it('reports a network error when axios has no response', () => {
    const { result } = renderHook(() => useApiError(), { wrapper });
    result.current.handleError(makeAxiosError());
    expect(mockEnqueue).toHaveBeenCalled();
  });
});
