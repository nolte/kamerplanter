import { renderHook } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { SnackbarProvider } from 'notistack';
import { type ReactNode } from 'react';
import { useApiError } from '@/hooks/useApiError';
import { ApiError } from '@/api/errors';
import '@/i18n';

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
});
