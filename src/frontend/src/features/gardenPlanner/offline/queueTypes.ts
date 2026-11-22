/**
 * The entries of the offline write buffer (REQ-053 WP 9.4, UI-NFR-012 R-017). Types only, so the field sheet,
 * the sync and the dialogs share them without loading the database.
 *
 * Only three actions are ever buffered (operator question 4 of wave 9, #2759 — an allowlist, no generic Axios
 * interceptor): "Done" on a task, a note, a photo of the bed or of a plant. Geometry stays online-only.
 */
import type { CareEventBody, CompletionPayload } from '../care/careTypes';

/**
 * R-017. `pending`: waits for the next sync; `syncing`: a sync is sending it; `failed`: five attempts failed, or
 * the server refused it for good — it waits for "Try again" or "Discard" (R-027); `conflict`: the server
 * answered one of the WP 9.3 conflict codes — it waits for "Keep" or "Discard" (R-028…R-032). A sent entry is
 * deleted, so there is no `synced` row.
 */
export type QueueStatus = 'pending' | 'syncing' | 'failed' | 'conflict';

/** The WP 9.3 answers a resend with the same `client_event_id` cannot change (docs "Buffered writes"). */
export type ConflictCode =
  | 'client_event.payload_mismatch'
  | 'task.already_closed'
  | 'task.missing'
  | 'client_event.deleted';

/**
 * A photo as it is kept on the device (R-043/R-044, G-W9 g): already downscaled to ≤ 1920 px and JPEG 80, the
 * bytes as an `ArrayBuffer` — IndexedDB stores it as binary like a Blob, and a Blob is rebuilt at send time.
 * EXIF stripping stays the server's (the canvas re-encode drops it already).
 */
export interface StoredPhoto {
  bytes: ArrayBuffer;
  type: string;
  name: string;
}

export type QueuedWrite =
  /** `POST /tasks/{key}/complete`; `payload.performed_at` is the capture time. */
  | { kind: 'complete'; taskKey: string; taskName: string; payload: CompletionPayload }
  /** `POST /care-events` with category `note`; `body.performed_at` is the capture time. */
  | { kind: 'note'; body: CareEventBody }
  /** `POST /attachments` (category `location`) then `POST /locations/{key}/photos` (idempotent link). */
  | { kind: 'bedPhoto'; locationKey: string; photo: StoredPhoto }
  /** `POST /plant-instances/{key}/photos`. */
  | { kind: 'plantPhoto'; plantKey: string; plantName: string; photo: StoredPhoto };

export type QueuedWriteKind = QueuedWrite['kind'];

export interface QueueEntry {
  /** Auto-increment: the capture order (FIFO, R-023). Absent before the first `add`. */
  seq?: number;
  /**
   * The `client_event_id` (UUID v4) generated once at capture time and sent unchanged on EVERY attempt
   * (G-W9 f): a retry after a lost answer is a replay the server answers with the stored object.
   */
  id: string;
  /** The owner: an entry is only ever sent in the user + tenant scope it was captured in (G-W9 a). */
  userKey: string;
  tenantKey: string;
  /** Epoch ms of the capture (R-017); sent as `performed_at` where the route takes one. */
  capturedAt: number;
  status: QueueStatus;
  /** Failed attempts so far (R-026/R-027). */
  attempts: number;
  /** Epoch ms before which no new attempt is made (the backoff). */
  nextAttemptAt: number;
  /** Epoch ms a sync claimed it; a claim older than the stale limit belongs to a sync that died. */
  syncingSince: number | null;
  /** The server's `error_code` of the last refusal, or `null`. Never a message or a stack. */
  lastErrorCode: string | null;
  /** The conflict code when `status` is `conflict`. */
  conflictCode: ConflictCode | null;
  /** "Keep" was chosen: the entry stays on the device, is never resent and does not reopen the dialog. */
  kept: boolean;
  /**
   * Epoch ms from which retention deletes the entry (`queue.ts` `expiryOf`): the effective `performed_at` + 365 days,
   * for a failed or conflict entry at most the capture + 90 days. Indexed, so the purge finds what is due by key
   * alone — without reading any row (photos included) into memory.
   */
  expiresAt: number;
  /** The bed it was captured at, for the lists (its name as shown then). */
  bedKey: string;
  bedName: string;
  write: QueuedWrite;
}

/** The retention notice of one user (R-056): how many of their entries the purge deleted, not yet shown. */
export interface PurgeNotice {
  userKey: string;
  count: number;
}
