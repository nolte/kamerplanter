/**
 * Tell when a buffered entry stops being "waiting here" (#2814): it was sent, discarded, is on its way, failed or
 * ran into a conflict. Its "Undo" toast must not outlive that moment — an undo of a sent entry is a lie, and a toast
 * left over a conflict covers the conflict dialog.
 */
import type { CacheScope } from './planCache';
import { listEntries, onQueueChange } from './queue';

/** Calls `onSettled` once, the first time `id` is gone or no longer `pending`; returns the unsubscribe. */
export function watchSettled(scope: CacheScope, id: string, onSettled: () => void): () => void {
  let done = false;
  let unsubscribe: () => void = () => undefined;
  const stop = () => {
    done = true;
    unsubscribe();
  };
  const check = () => {
    void listEntries(scope).then(
      (entries) => {
        if (done) return;
        const entry = entries.find((candidate) => candidate.id === id);
        if (entry === undefined || entry.status !== 'pending') {
          stop();
          onSettled();
        }
      },
      () => undefined,
    );
  };
  unsubscribe = onQueueChange(check);
  return stop;
}
