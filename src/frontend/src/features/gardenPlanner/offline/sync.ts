/**
 * The sync of the offline write buffer (REQ-053 WP 9.4, UI-NFR-012 R-021…R-027, R-045).
 *
 * - **FIFO** (R-023): entries go out one after the other in capture order — photos too, never in parallel
 *   (R-045). An entry that waits for its backoff holds back the ones captured after it.
 * - **Idempotent** (G-W9 f): every attempt sends the entry's own `client_event_id`. A lost answer is followed by
 *   a replay that the server answers `200` with the stored object — that is a success like a `201`.
 * - **Backoff** (R-026): a request without an answer, a 5xx, 408, 429 or `WRITE_CONFLICT` counts as a failed
 *   attempt; the next one waits 1 s, 2 s, 4 s, 8 s … at most 60 s. After {@link MAX_ATTEMPTS} the entry is
 *   `failed` (R-027) and the sync moves on to the next one.
 * - **Refused for good**: any other 4xx (a 422, a 403 after a role change, a deleted bed) makes the entry `failed`
 *   at once with the server's `error_code` — resending the same request cannot change the answer.
 * - **Conflicts** (R-028): `409 client_event.payload_mismatch`, `409 task.already_closed`, `404 task.missing` and
 *   `404 client_event.deleted` (WP 9.3) make the entry `conflict`; the dialog decides keep or discard.
 * - **401** stops the run without counting an attempt: the client refreshes the token, or the session ends and
 *   the clearing takes the buffer with it.
 * - **Owner** (G-W9 a): a run sends only entries of its scope and stops as soon as the active user or tenant is
 *   another one; a clearing that starts meanwhile drops every later status write (the clearing generation).
 * - **One sender**: one run at a time per tab, and across tabs through the Web Locks API where it exists; without
 *   it, two tabs sending the same entry are still harmless — the second request is a replay.
 */
import axios from 'axios';
import { uploadPlantPhoto } from '@/api/endpoints/plantPhotos';
import { isApiError } from '@/api/errors';
import { BACKGROUND_SYNC_TAG } from '@/pwa/cachePolicy';
import { addBedPhoto } from '../bed/bedPhotoApi';
import { completeBedTask, logCareEvent } from '../care/careApi';
import type { CacheScope } from './planCache';
import {
  MAX_ATTEMPTS,
  asConflictCode,
  backoffMs,
  listEntries,
  purgeExpiredEntries,
  queueGeneration,
  removeEntry,
  updateEntry,
} from './queue';
import { photoFile } from './queuedPhoto';
import type { ConflictCode, QueueEntry } from './queueTypes';

/** The entries a run of this tab is sending right now: a stale-claim reset never takes them back. */
const claimedHere = new Set<number>();

/** A `syncing` claim older than this belongs to a run that died (a closed tab); it is pending again. */
export const SYNC_STALE_MS = 2 * 60_000;
/** The Web Locks name: one sender per origin. */
export const SYNC_LOCK_NAME = 'kp-write-queue-sync';

/** What one failed send means for its entry. */
export type SendOutcome =
  | { kind: 'conflict'; code: ConflictCode }
  /** Try again after the backoff (no answer, 5xx, 408, 429, `WRITE_CONFLICT`). */
  | { kind: 'retry'; code: string }
  /** The same request can never succeed: `failed` at once. */
  | { kind: 'refused'; code: string }
  /** Stop the run, count nothing (401, a cancelled request). */
  | { kind: 'stop' };

function retryableStatus(status: number): boolean {
  return status === 408 || status === 429 || status >= 500;
}

/** Map a rejected send to what happens with the entry. Reads codes and statuses only — never a message. */
export function classifySendError(error: unknown): SendOutcome {
  if (isApiError(error)) {
    const conflict =
      asConflictCode(error.errorCode) ?? error.details.map((detail) => asConflictCode(detail.code)).find(Boolean);
    if (conflict) return { kind: 'conflict', code: conflict };
    if (error.statusCode === 401) return { kind: 'stop' };
    if (retryableStatus(error.statusCode) || error.errorCode === 'WRITE_CONFLICT') {
      return { kind: 'retry', code: error.errorCode };
    }
    return { kind: 'refused', code: error.errorCode || `HTTP_${error.statusCode}` };
  }
  if (axios.isAxiosError(error)) {
    if (error.code === 'ERR_CANCELED') return { kind: 'stop' };
    const status = error.response?.status;
    if (status === undefined) return { kind: 'retry', code: 'network' };
    if (status === 401) return { kind: 'stop' };
    if (retryableStatus(status)) return { kind: 'retry', code: `HTTP_${status}` };
    return { kind: 'refused', code: `HTTP_${status}` };
  }
  return { kind: 'refused', code: 'client' };
}

/**
 * Per-request timeouts of a buffered send (the app's Axios clients have none): a request that hangs on a bad
 * connection must end, count as a failed attempt (no answer → backoff, the resend is a replay) and free the single
 * sender. A photo upload gets longer.
 */
export const SEND_TIMEOUT_MS = 30_000;
export const PHOTO_SEND_TIMEOUT_MS = 120_000;

/** Send one entry with its own `client_event_id`. Resolves on a `201` and on a replay `200` alike. */
export async function sendEntry(entry: QueueEntry): Promise<void> {
  const { write, id } = entry;
  const json = { timeout: SEND_TIMEOUT_MS };
  const photo = { timeout: PHOTO_SEND_TIMEOUT_MS };
  switch (write.kind) {
    case 'complete':
      await completeBedTask(write.taskKey, write.payload, id, json);
      return;
    case 'note':
      await logCareEvent(write.body, id, json);
      return;
    case 'bedPhoto':
      await addBedPhoto(write.locationKey, photoFile(write.photo), id, photo);
      return;
    case 'plantPhoto':
      await uploadPlantPhoto(write.plantKey, photoFile(write.photo), id, photo);
      return;
  }
}

export interface SyncProgress {
  /** Entries handled in this run (sent, conflict or failed). */
  done: number;
  /** Entries this run set out to send. */
  total: number;
}

export interface SyncResult {
  sent: number;
  conflicts: number;
  failed: number;
  /** When the head of the queue may be tried again (its backoff), or `null`. */
  nextRetryAt: number | null;
  /** Nothing ran: offline, another sender holds the lock, or no scope. */
  skipped: boolean;
}

export interface SyncOptions {
  scope: CacheScope;
  /** The scope now; the run stops as soon as it is another one (a tenant switch, a sign-out). */
  currentScope?: () => CacheScope | null;
  now?: () => number;
  send?: (entry: QueueEntry) => Promise<void>;
  online?: () => boolean;
  onProgress?: (progress: SyncProgress) => void;
  /** Every `syncing` claim is stale (this run holds the origin-wide lock); default: only old ones. */
  ownsLock?: boolean;
}

const EMPTY: SyncResult = { sent: 0, conflicts: 0, failed: 0, nextRetryAt: null, skipped: true };

function browserOnline(): boolean {
  return typeof navigator === 'undefined' || navigator.onLine !== false;
}

function sameScope(a: CacheScope | null, b: CacheScope): boolean {
  return a !== null && a.userKey === b.userKey && a.tenantKey === b.tenantKey;
}

/** One FIFO run over the scope's pending entries (see the module comment). */
export async function syncQueue({
  scope,
  currentScope = () => scope,
  now = Date.now,
  send = sendEntry,
  online = browserOnline,
  onProgress,
  ownsLock = false,
}: SyncOptions): Promise<SyncResult> {
  if (!online() || !sameScope(currentScope(), scope)) return EMPTY;
  const generation = queueGeneration();
  if (generation === null) return EMPTY;
  const write = { generation };

  // Retention: what the server would refuse as too old is deleted, not sent.
  await purgeExpiredEntries(now());
  const entries = await listEntries(scope);
  const staleBefore = ownsLock ? Number.POSITIVE_INFINITY : now() - SYNC_STALE_MS;
  for (const entry of entries) {
    // A claim a live run of THIS tab holds is never taken back (runs are serialised, this is the safety net).
    if (entry.seq !== undefined && claimedHere.has(entry.seq)) continue;
    if (entry.status === 'syncing' && entry.seq && (entry.syncingSince ?? 0) < staleBefore) {
      // The run that claimed it is gone; the request may have reached the server — the resend is a replay.
      await updateEntry(scope, entry.seq, { status: 'pending', syncingSince: null }, { ...write, expect: 'syncing' });
      entry.status = 'pending';
    }
  }
  const work = entries.filter((entry) => entry.status === 'pending');
  const result: SyncResult = { sent: 0, conflicts: 0, failed: 0, nextRetryAt: null, skipped: false };
  const progress: SyncProgress = { done: 0, total: work.length };
  if (work.length > 0) onProgress?.({ ...progress });

  for (const entry of work) {
    const seq = entry.seq;
    if (seq === undefined) continue;
    if (!online() || !sameScope(currentScope(), scope) || queueGeneration() !== generation) break;
    if (entry.nextAttemptAt > now()) {
      // FIFO: the head waits for its backoff, everything captured after it waits too.
      result.nextRetryAt = entry.nextAttemptAt;
      break;
    }
    const claimed = await updateEntry(scope, seq, { status: 'syncing', syncingSince: now() }, { ...write, expect: 'pending' });
    if (!claimed) continue; // discarded meanwhile, or another sender has it
    claimedHere.add(seq);
    let outcome: SendOutcome | null = null;
    try {
      await send(entry);
    } catch (error) {
      outcome = classifySendError(error);
    }
    try {
      await settle(entry, outcome);
    } finally {
      claimedHere.delete(seq);
    }
    // A stop, or a retry still within its budget, holds the head (FIFO): the run ends here.
    if (outcome?.kind === 'stop' || (outcome?.kind === 'retry' && entry.attempts + 1 < MAX_ATTEMPTS)) break;
    progress.done += 1;
    onProgress?.({ ...progress });
  }
  return result;

  /** Write what the answer means for the entry (sent → deleted, conflict, failed, back to pending). */
  async function settle(current: QueueEntry, outcome: SendOutcome | null): Promise<void> {
    const seq = current.seq as number;
    if (outcome === null) {
      await removeEntry(scope, seq, write);
      result.sent += 1;
    } else if (outcome.kind === 'conflict') {
      await updateEntry(
        scope,
        seq,
        { status: 'conflict', conflictCode: outcome.code, lastErrorCode: outcome.code, syncingSince: null },
        write,
      );
      result.conflicts += 1;
    } else if (outcome.kind === 'refused') {
      await updateEntry(scope, seq, { status: 'failed', lastErrorCode: outcome.code, syncingSince: null }, write);
      result.failed += 1;
    } else if (outcome.kind === 'stop') {
      await updateEntry(scope, seq, { status: 'pending', syncingSince: null }, write);
      return;
    } else {
      const attempts = current.attempts + 1;
      if (attempts >= MAX_ATTEMPTS) {
        await updateEntry(
          scope,
          seq,
          { status: 'failed', attempts, lastErrorCode: outcome.code, syncingSince: null },
          write,
        );
        result.failed += 1;
      } else {
        const nextAttemptAt = now() + backoffMs(attempts);
        await updateEntry(
          scope,
          seq,
          { status: 'pending', attempts, nextAttemptAt, lastErrorCode: outcome.code, syncingSince: null },
          write,
        );
        result.nextRetryAt = nextAttemptAt;
        return;
      }
    }
  }
}

interface LockManagerLike {
  request: (
    name: string,
    options: { ifAvailable?: boolean; signal?: AbortSignal },
    callback: (lock: unknown) => Promise<SyncResult>,
  ) => Promise<SyncResult>;
}

/**
 * Run `task` while holding the origin-wide sync lock. `wait = false`: another tab holding it skips this run (the
 * app bar's sync tries again on the next trigger); `wait = true` (the logout dialog) queues for it. Without the
 * Web Locks API — or when `locks.request` itself is refused — the task runs without a lock (a second sender is
 * still harmless: its request is a replay). An error INSIDE the task is the task's and is never retried here.
 */
export async function withSyncLock(
  task: (ownsLock: boolean) => Promise<SyncResult>,
  wait = false,
  signal?: AbortSignal,
): Promise<SyncResult> {
  const locks = (typeof navigator !== 'undefined' ? (navigator as { locks?: LockManagerLike }).locks : undefined) ?? null;
  if (!locks || typeof locks.request !== 'function') return task(false);
  let started = false;
  try {
    return await locks.request(SYNC_LOCK_NAME, wait ? { signal } : { ifAvailable: true }, (lock) => {
      started = true;
      return lock ? task(true) : Promise.resolve(EMPTY);
    });
  } catch (error) {
    if (started) throw error;
    // The wait for the lock was given up (timeout, cancel): nothing is sent.
    if (signal?.aborted) return EMPTY;
    return task(false);
  }
}

/** This tab's runs, one after the other (the app bar's scheduler and the logout dialog share it). */
let tail: Promise<unknown> = Promise.resolve();

/** Run `task` after every run this tab already started has finished. */
export function runExclusive<T>(task: () => Promise<T>): Promise<T> {
  const next = tail.then(task, task);
  tail = next.catch(() => undefined);
  return next;
}

/**
 * One sync through the single sender: this tab's run queue, then the origin-wide lock (waiting for it). `signal`
 * ends the WAIT (a timeout, the user's cancel): the promise then resolves with nothing sent, while a run already
 * under way finishes on its own (it is the single sender; abandoning it mid-request would only cost a replay).
 */
export function runSyncExclusive(options: Omit<SyncOptions, 'ownsLock'>, signal?: AbortSignal): Promise<SyncResult> {
  const run = runExclusive(() =>
    signal?.aborted ? Promise.resolve(EMPTY) : withSyncLock((ownsLock) => syncQueue({ ...options, ownsLock }), true, signal),
  );
  if (!signal) return run;
  return new Promise<SyncResult>((resolve, reject) => {
    const onAbort = () => resolve(EMPTY);
    if (signal.aborted) return onAbort();
    signal.addEventListener('abort', onAbort, { once: true });
    run.then(resolve, reject).finally(() => signal.removeEventListener('abort', onAbort));
  });
}

export interface SyncSchedulerOptions {
  getScope: () => CacheScope | null;
  onStart?: () => void;
  onProgress?: (progress: SyncProgress) => void;
  onFinish?: (result: SyncResult) => void;
  /** Called once on dispose — also mid-run, where `onFinish` will not come (the host clears its progress). */
  onDispose?: () => void;
  /** Replaces {@link syncQueue} (tests). */
  run?: (options: SyncOptions) => Promise<SyncResult>;
  now?: () => number;
}

export interface SyncScheduler {
  /** Sync now (`online`, app focus, a new entry, "Sync now"); a request during a run starts one more after it. */
  request: () => Promise<void>;
  dispose: () => void;
}

/** Single-flight runs plus the backoff timer of the head of the queue. */
export function createSyncScheduler({
  getScope,
  onStart,
  onProgress,
  onFinish,
  onDispose,
  run = syncQueue,
  now = Date.now,
}: SyncSchedulerOptions): SyncScheduler {
  let running: Promise<void> | null = null;
  let again = false;
  let timer: ReturnType<typeof setTimeout> | null = null;
  let disposed = false;

  const clearTimer = () => {
    if (timer !== null) clearTimeout(timer);
    timer = null;
  };

  const start = async (): Promise<void> => {
    const scope = getScope();
    if (disposed || scope === null) return;
    clearTimer();
    onStart?.();
    let result: SyncResult;
    try {
      // A late progress of a disposed scheduler (scope changed, host unmounted) is dropped.
      const progress = (value: SyncProgress) => {
        if (!disposed) onProgress?.(value);
      };
      result = await runExclusive(() =>
        withSyncLock((ownsLock) => run({ scope, currentScope: getScope, onProgress: progress, ownsLock, now })),
      );
    } catch {
      result = EMPTY;
    }
    if (disposed) return;
    onFinish?.(result);
    if (result.nextRetryAt !== null) {
      timer = setTimeout(() => void request(), Math.max(0, result.nextRetryAt - now()));
    }
  };

  const request = (): Promise<void> => {
    if (running) {
      again = true;
      return running;
    }
    running = (async () => {
      try {
        do {
          again = false;
          await start();
        } while (again && !disposed);
      } finally {
        running = null;
      }
    })();
    return running;
  };

  return {
    request,
    dispose: () => {
      if (disposed) return;
      disposed = true;
      clearTimer();
      onDispose?.();
    },
  };
}

/**
 * R-022: ask the browser for a Background Sync after an offline capture, where it has the API (not Safari).
 * Best effort — the `online` event and the app focus trigger the sync anyway.
 */
export async function requestBackgroundSync(): Promise<void> {
  try {
    if (typeof navigator === 'undefined' || !('serviceWorker' in navigator) || !navigator.serviceWorker) return;
    const registration = (await navigator.serviceWorker.getRegistration()) as
      | (ServiceWorkerRegistration & { sync?: { register: (tag: string) => Promise<void> } })
      | undefined;
    await registration?.sync?.register(BACKGROUND_SYNC_TAG);
  } catch {
    // No permission, no worker: the other triggers remain.
  }
}
