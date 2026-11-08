/**
 * Retention of the offline write buffer (REQ-053 WP 9.4, GDPR; REQ-053 §32.6 item 14). Pure, so the database
 * schema upgrade, the queue and the tests share one rule.
 */
import type { QueueEntry } from './queueTypes';

export const DAY_MS = 24 * 60 * 60 * 1000;
/**
 * A PENDING entry: the backend refuses a client event whose `performed_at` lies further back than `MAX_AGE_DAYS`
 * (V-11, `domain/models/care_event.py`, 365 days — the placeholder default of §32.6 item 14), so an entry whose
 * effective `performed_at` is older can never be sent: it is deleted, and a capture already that old is refused.
 */
export const ENTRY_MAX_AGE_DAYS = 365;
/** An entry the sync will never send by itself — `failed`, `conflict`, kept: 90 days after its capture. */
export const UNSENDABLE_MAX_AGE_DAYS = 90;

/** The `performed_at` the request will carry (a note's is editable), or the capture time. */
export function effectivePerformedAt(entry: Pick<QueueEntry, 'capturedAt' | 'write'>): number {
  const { write } = entry;
  const stated = write.kind === 'note' ? write.body.performed_at : write.kind === 'complete' ? write.payload.performed_at : null;
  const parsed = stated ? Date.parse(stated) : Number.NaN;
  return Number.isFinite(parsed) ? parsed : entry.capturedAt;
}

/** From when retention deletes the entry (stored as `expiresAt`, recomputed on every status change). */
export function expiryOf(entry: Pick<QueueEntry, 'capturedAt' | 'write' | 'status'>): number {
  const sendable = effectivePerformedAt(entry) + ENTRY_MAX_AGE_DAYS * DAY_MS;
  if (entry.status === 'failed' || entry.status === 'conflict') {
    return Math.min(sendable, entry.capturedAt + UNSENDABLE_MAX_AGE_DAYS * DAY_MS);
  }
  return sendable;
}
