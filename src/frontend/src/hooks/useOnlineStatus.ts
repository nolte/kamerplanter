/**
 * Whether the browser believes it is online. Lifted out of the garden planner's field mode (REQ-053
 * GP-UX-024, D-23) into the app shell for the permanent connectivity indicator (UI-NFR-012 R-033,
 * REQ-053 WP 9.1). Field mode still shows its offline notice and locks "Done" — the offline write
 * buffer is a later work package. `navigator.onLine` can be optimistic; a request that fails anyway
 * still surfaces its error toast.
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
