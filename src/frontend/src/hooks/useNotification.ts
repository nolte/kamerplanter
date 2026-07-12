import { useSnackbar, type VariantType } from 'notistack';
import { useCallback, useMemo } from 'react';

export function useNotification() {
  const { enqueueSnackbar } = useSnackbar();

  const notify = useCallback(
    (message: string, variant: VariantType = 'default') => {
      // Errors auto-dismiss after a longer 8s window (#571) so a stale toast can
      // never linger indefinitely; other variants keep their shorter timings.
      const autoHideDuration =
        variant === 'error' ? 8000 : variant === 'warning' ? 8000 : 5000;

      enqueueSnackbar(message, { variant, autoHideDuration, preventDuplicate: true });
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
