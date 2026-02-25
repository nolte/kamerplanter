import { useSnackbar, type VariantType } from 'notistack';
import { useCallback } from 'react';

export function useNotification() {
  const { enqueueSnackbar } = useSnackbar();

  const notify = useCallback(
    (message: string, variant: VariantType = 'default') => {
      const autoHideDuration =
        variant === 'error' ? null : variant === 'warning' ? 8000 : 5000;

      enqueueSnackbar(message, { variant, autoHideDuration });
    },
    [enqueueSnackbar],
  );

  return {
    success: (msg: string) => notify(msg, 'success'),
    error: (msg: string) => notify(msg, 'error'),
    warning: (msg: string) => notify(msg, 'warning'),
    info: (msg: string) => notify(msg, 'info'),
  };
}
