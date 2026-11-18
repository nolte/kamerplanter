import { useSnackbar, type SnackbarKey, type VariantType } from 'notistack';
import { createElement, useCallback, useMemo } from 'react';
import SnackbarCloseButton from '@/components/common/SnackbarCloseButton';

/** Every toast gets a keyboard-reachable close button (UI-NFR-004, #3013 N-10). */
const closeAction = (snackbarKey: SnackbarKey) => createElement(SnackbarCloseButton, { snackbarKey });

export function useNotification() {
  const { enqueueSnackbar } = useSnackbar();

  const notify = useCallback(
    (message: string, variant: VariantType = 'default') => {
      // Errors auto-dismiss after a longer 8s window (#571) so a stale toast can
      // never linger indefinitely; other variants keep their shorter timings.
      const autoHideDuration =
        variant === 'error' ? 8000 : variant === 'warning' ? 8000 : 5000;

      enqueueSnackbar(message, { variant, autoHideDuration, preventDuplicate: true, action: closeAction });
    },
    [enqueueSnackbar],
  );

  return useMemo(
    () => ({
      success: (msg: string) => notify(msg, 'success'),
      error: (msg: string) => notify(msg, 'error'),
      warning: (msg: string) => notify(msg, 'warning'),
      info: (msg: string) => notify(msg, 'info'),
    }),
    [notify],
  );
}
