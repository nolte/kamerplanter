/**
 * Whether the browser believes it is online (REQ-053 GP-UX-024, MVP part, D-23): field mode shows an
 * offline notice and locks "Done" instead of losing the entry - there is no offline buffer before the
 * UI-NFR-012 basis (wave 9). `navigator.onLine` can be optimistic; a request that fails anyway still
 * surfaces its error toast.
 */
import { useSyncExternalStore } from 'react';

function subscribe(onChange: () => void): () => void {
  window.addEventListener('online', onChange);
  window.addEventListener('offline', onChange);
  return () => {
    window.removeEventListener('online', onChange);
    window.removeEventListener('offline', onChange);
  };
}

function snapshot(): boolean {
  return typeof navigator === 'undefined' || navigator.onLine !== false;
}

export function useOnlineStatus(): boolean {
  return useSyncExternalStore(subscribe, snapshot, () => true);
}
