/**
 * The "Done - Undo" snackbar of the care tab (REQ-053 GP-FR-149): eight seconds to take the line
 * back. The undo itself is a call the caller supplies (reopen with `undo` for a task, `void` for a
 * log line); the author may do it within ten minutes, a lead any time, so a 403 after the snackbar is
 * gone cannot happen through this button.
 */
import { useCallback, useMemo, type ReactNode } from 'react';
import { useSnackbar } from 'notistack';
import { useTranslation } from 'react-i18next';
import Button from '@mui/material/Button';
import { useApiError } from '@/hooks/useApiError';

/** How long the undo stays on offer (plan WP 5.1, field mode). */
export const UNDO_SNACKBAR_MS = 8000;

export interface UndoRequest {
  message: string;
  /** Takes the action back; rejects when the server refuses. */
  undo: () => Promise<void>;
  /** Called after a successful undo, so the list can reload. */
  onUndone: () => void;
}

export function useUndoSnackbar() {
  const { t } = useTranslation();
  const { enqueueSnackbar, closeSnackbar } = useSnackbar();
  const { handleError } = useApiError();

  const offerUndo = useCallback(
    ({ message, undo, onUndone }: UndoRequest) => {
      enqueueSnackbar(message, {
        variant: 'success',
        autoHideDuration: UNDO_SNACKBAR_MS,
        action: (id): ReactNode => (
          <Button
            color="inherit"
            size="small"
            sx={{ minHeight: 44, minWidth: 64 }}
            data-testid="care-undo"
            onClick={() => {
              closeSnackbar(id);
              undo().then(onUndone, (error: unknown) => handleError(error));
            }}
          >
            {t('pages.bed.care.undo.action')}
          </Button>
        ),
      });
    },
    [closeSnackbar, enqueueSnackbar, handleError, t],
  );

  return useMemo(() => ({ offerUndo }), [offerUndo]);
}
