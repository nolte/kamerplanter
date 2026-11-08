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
import { countUserEntries, writeQueueExists } from './queue';
import { syncQueue, type SyncProgress } from './sync';

/** The user's entries not yet at the server, in all tenants (pending, syncing, failed, conflicts, kept ones). */
export async function unsyncedEntries(userKey: string | null): Promise<number> {
  if (userKey === null || !(await writeQueueExists())) return 0;
  return countUserEntries(userKey);
}

/** Send what the active tenant holds now, then count the user's entries again. */
export async function syncThenCount(
  userKey: string,
  scope: CacheScope | null,
  onProgress?: (progress: SyncProgress) => void,
): Promise<number> {
  if (scope !== null) await syncQueue({ scope, onProgress });
  return unsyncedEntries(userKey);
}
