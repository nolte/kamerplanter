/**
 * What an explicit logout has to know about the offline write buffer (REQ-053 WP 9.4, G-W9 b, UI-NFR-012
 * R-050/R-051).
 *
 * The logout discards the user's unsent entries — in every tenant (`pwa/offlineData.ts`, `discardWriteQueueOf`).
 * So the app bar asks first (`UnsyncedWritesDialog`): it counts them and, with a connection, sends what belongs to
 * the active tenant. A tenant switch, a forced sign-out and a refused refresh keep the entries for their owner;
 * the kill switch and the account erasure delete them without asking.
 *
 * Loaded on demand by `hooks/useUnsyncedWritesGuard.ts`, so the app shell does not carry the buffer.
 */
import type { CacheScope } from './planCache';
import { countUserEntries } from './queue';
import { runSyncExclusive, type SyncOptions, type SyncProgress } from './sync';

/**
 * The user's entries not yet at the server, in all tenants (pending, syncing, failed, conflicts, kept ones);
 * `null` = could not be counted — the logout then asks without a number (never discards unasked, R-056 c).
 */
export async function unsyncedEntries(userKey: string | null): Promise<number | null> {
  if (userKey === null) return 0;
  // Not `writeQueueExists()` first: it answers "no" in a retired tab, where rows may well exist (null, not 0).
  return countUserEntries(userKey);
}

/** Send what the active tenant holds now, then count the user's entries again. */
export async function syncThenCount(
  userKey: string,
  scope: CacheScope | null,
  onProgress?: (progress: SyncProgress) => void,
  /** The sender, the clock and the wait limit (tests). */
  { waitMs = LOGOUT_SYNC_WAIT_MS, ...options }: Pick<SyncOptions, 'send' | 'now'> & { waitMs?: number } = {},
  /** Ends the wait (the dialog's cancel); the timeout below ends it in any case. */
  signal?: AbortSignal,
): Promise<number | null> {
  // Through the shared single sender (this tab's queue of runs + the origin-wide Web Lock): never beside the
  // app bar's sync, never resetting its claims. Never longer than LOGOUT_SYNC_WAIT_MS: then it only counts.
  if (scope !== null) {
    const wait = waitSignal(waitMs, signal);
    try {
      await runSyncExclusive({ scope, onProgress, ...options }, wait.signal);
    } finally {
      wait.done();
    }
  }
  return unsyncedEntries(userKey);
}

/** How long the logout dialog waits for the single sender before it just counts (and frees its buttons). */
export const LOGOUT_SYNC_WAIT_MS = 30_000;

/** `signal` or the timeout, whichever ends first (without `AbortSignal.any`/`timeout` in older browsers). */
function waitSignal(waitMs: number, signal?: AbortSignal): { signal: AbortSignal; done: () => void } {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), waitMs);
  const end = () => {
    clearTimeout(timer);
    controller.abort();
  };
  if (signal?.aborted) end();
  else signal?.addEventListener('abort', end, { once: true });
  return {
    signal: controller.signal,
    done: () => {
      clearTimeout(timer);
      signal?.removeEventListener('abort', end);
    },
  };
}
