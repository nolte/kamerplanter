/**
 * Send now or buffer (REQ-053 WP 9.4): the one path of field mode's three bufferable actions — "Done", a note, a
 * photo. Nothing else ever goes into the buffer (operator question 4 of wave 9: an allowlist, no interceptor).
 *
 * - **Offline** (the browser says so): the write goes straight into the buffer.
 * - **Online**: it is sent at once, already carrying a fresh `client_event_id`. If that request gets no answer at
 *   all (the connection dropped, `navigator.onLine` was optimistic), the write is buffered WITH THE SAME ID and the
 *   same body, so the sync's resend is a replay if the first request did reach the server (G-W9 f).
 * - Without a usable buffer (no IndexedDB, kill switch off, no scope) nothing is buffered: offline the caller keeps
 *   its lock, online a failed request fails as before.
 */
import { isNetworkFailure, type CacheScope } from './planCache';
import { enqueue, newClientEventId, writeQueueAvailable } from './queue';
import { requestBackgroundSync } from './sync';
import type { QueueEntry, QueuedWrite } from './queueTypes';

export interface BufferTarget {
  scope: CacheScope | null;
  online: boolean;
  bedKey: string;
  bedName: string;
}

export type WriteOutcome<T> = { status: 'sent'; result: T } | { status: 'queued'; entry: QueueEntry };

/** Whether an offline write can be buffered for this scope in this tab. */
export function canBuffer(scope: CacheScope | null): scope is CacheScope {
  return scope !== null && writeQueueAvailable();
}

/**
 * Send `direct(id)` now or buffer `write(fallback)`. `write` is built only when it is needed; `fallback` is `true`
 * when an online request already went out under the id (its answer got lost) — the buffered copy must then carry
 * exactly what was sent (a photo: the same bytes), `false` for a capture made offline. Rejects with the buffer's
 * errors (`QueueFullError`, `PerformedTooOldError`, `QueueUnavailableError`) or the request's.
 */
export async function sendOrBuffer<T>(
  target: BufferTarget,
  write: (fallback: boolean) => QueuedWrite | Promise<QueuedWrite>,
  direct: (clientEventId: string | undefined) => Promise<T>,
): Promise<WriteOutcome<T>> {
  const { scope } = target;
  const bufferable = canBuffer(scope);
  const buffer = async (id?: string): Promise<WriteOutcome<T>> => {
    if (!canBuffer(scope)) throw new Error('offline_queue.unavailable');
    const queued = await write(id !== undefined);
    const entry = await enqueue({ scope, bedKey: target.bedKey, bedName: target.bedName, write: queued, id });
    void requestBackgroundSync();
    return { status: 'queued', entry };
  };
  if (!target.online && bufferable) return buffer();
  const id = bufferable ? newClientEventId() : undefined;
  try {
    return { status: 'sent', result: await direct(id) };
  } catch (error) {
    if (bufferable && id !== undefined && isNetworkFailure(error)) return buffer(id);
    throw error;
  }
}
