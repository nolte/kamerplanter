import { renderHook, act } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { SnackbarProvider } from 'notistack';
import { useNotification } from '@/hooks/useNotification';
import type { ReactNode } from 'react';

const mockEnqueueSnackbar = vi.fn();

vi.mock('notistack', async () => {
  const actual = await vi.importActual('notistack');
  return {
    ...actual,
    useSnackbar: () => ({
      enqueueSnackbar: mockEnqueueSnackbar,
      closeSnackbar: vi.fn(),
    }),
  };
});

function Wrapper({ children }: { children: ReactNode }) {
  return <SnackbarProvider>{children}</SnackbarProvider>;
}

describe('useNotification', () => {
  it('calls success with correct variant and auto-hide', () => {
    const { result } = renderHook(() => useNotification(), { wrapper: Wrapper });
    act(() => result.current.success('Done!'));
    expect(mockEnqueueSnackbar).toHaveBeenCalledWith('Done!', {
      variant: 'success',
      autoHideDuration: 5000,
    });
  });

  it('calls error with persistent (null) auto-hide', () => {
    const { result } = renderHook(() => useNotification(), { wrapper: Wrapper });
    act(() => result.current.error('Failure'));
    expect(mockEnqueueSnackbar).toHaveBeenCalledWith('Failure', {
      variant: 'error',
      autoHideDuration: null,
    });
  });

  it('calls warning with 8s auto-hide', () => {
    const { result } = renderHook(() => useNotification(), { wrapper: Wrapper });
    act(() => result.current.warning('Watch out'));
    expect(mockEnqueueSnackbar).toHaveBeenCalledWith('Watch out', {
      variant: 'warning',
      autoHideDuration: 8000,
    });
  });
});
