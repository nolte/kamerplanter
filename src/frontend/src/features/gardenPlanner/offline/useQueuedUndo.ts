/**
 * "Undo" for a buffered entry (REQ-053 WP 9.4, #2814): the entry leaves the buffer — refused once a sync has it on
 * its way — and the offer itself goes as soon as the entry is sent, discarded, on its way or in conflict. A toast
 * that outlives its entry offers to undo something already sent, or covers the conflict dialog.
 */
import { useCallback, useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import { UNDO_SNACKBAR_MS, useUndoSnackbar } from '../care/useUndoSnackbar';
import type { CacheScope } from './planCache';
import { discardEntry } from './queue';
import type { QueueEntry } from './queueTypes';
import { watchSettled } from './watchSettled';

export function useQueuedUndo(scope: CacheScope | null) {
  const { t } = useTranslation();
  const { offerUndo, withdraw } = useUndoSnackbar();

  const offerQueuedUndo = useCallback(
    (entry: QueueEntry, message: string) => {
      const offer = offerUndo({
        message,
        undo: async () => {
          if (!scope || !(await discardEntry(scope, entry.id))) {
            throw new Error(t('pages.gardenPlan.field.buffer.undoTooLate'));
          }
        },
        onUndone: () => undefined,
      });
      if (scope) {
        const stop = watchSettled(scope, entry.id, () => withdraw(offer));
        window.setTimeout(stop, UNDO_SNACKBAR_MS);
      }
    },
    [offerUndo, scope, t, withdraw],
  );

  return useMemo(() => ({ offerQueuedUndo }), [offerQueuedUndo]);
}
