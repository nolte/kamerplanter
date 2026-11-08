/**
 * The offline write buffer (REQ-053 WP 9.4, GP-UX-024 part 2; UI-NFR-012 R-015…R-019, R-043): "Done", a note
 * and a photo captured without a connection wait here until the sync (`sync.ts`) sends them.
 *
 * - **IndexedDB only** (G-W9 a), database `kp-write-queue` (`queueDb.ts`). Every entry carries `user_key` AND
 *   `tenant_key`; every read filters on both, so an entry is only listed, sent, kept or discarded in the scope
 *   it was captured in.
 * - **≤ 500 entries** (R-019): the 501st capture is refused with {@link QueueFullError}; the caller says so and
 *   nothing more is taken in until the sync made room.
 * - **One `client_event_id` per entry** (G-W9 f), generated at capture time ({@link newClientEventId}) and never
 *   changed: every retry resends exactly that id.
 * - **Kept across sessions** (UI-NFR-012 R-050/R-051): a tenant switch, a forced sign-out and a refused refresh
 *   keep the entries; they wait, invisible to everyone else, until their owner is signed in again in that tenant.
 *   Only the explicit, confirmed logout and the account erasure discard the entries of that user
 *   (`pwa/writeQueueWipe.ts`), the kill switch deletes the database. A clearing in another tab for the session
 *   this tab holds retires the buffer here until this tab starts a new session — that tab may still hold the
 *   previous account's token (the plan cache rule, #2789 review S2). A capture whose call began before a clearing
 *   is dropped.
 * - **Retention** ({@link ENTRY_MAX_AGE_DAYS}): an entry older than the server accepts is deleted on app start and
 *   before every sync.
 * - **Kill switch** (G-W9 e): with `PWA_CACHING_ENABLED=false` the buffer is off — {@link writeQueueAvailable}
 *   is `false`, field mode keeps its offline locks, and the database is never opened.
 *
 * Dexie loads with the first call (`import('./queueDb')`), never with a route.
 */
import { runtimeConfig } from '@/config/runtimeConfig';
import { isPwaCachingEnabled } from '@/pwa/cachePolicy';
import { offlineDataGeneration, onOfflineDataEvent } from '@/pwa/offlineData';
import { WRITE_QUEUE_DB_NAME } from '@/pwa/storageWipe';
import type { CacheScope } from './planCache';
import type { WriteQueueDatabase } from './queueDb';
import { DAY_MS, ENTRY_MAX_AGE_DAYS, effectivePerformedAt, expiryOf } from './retention';
import type { ConflictCode, QueueEntry, QueuedWrite, QueueStatus } from './queueTypes';

/**
 * R-019: at most this many entries per USER are buffered. Other users' rows on a shared device never block a
 * capture and never show (their existence is not revealed).
 */
export const QUEUE_CAPACITY = 500;
/**
 * A storage safety net for the whole device (many users on one shared tablet), far above any one user's share.
 * Reaching it refuses a capture like a full buffer.
 */
export const QUEUE_DEVICE_CEILING = 5000;
/** R-027: after this many failed attempts an entry is `failed`. */
export const MAX_ATTEMPTS = 5;
export { ENTRY_MAX_AGE_DAYS, UNSENDABLE_MAX_AGE_DAYS } from './retention';

/** The capture names a `performed_at` the server no longer accepts (older than {@link ENTRY_MAX_AGE_DAYS}). */
export class PerformedTooOldError extends Error {
  constructor() {
    super('offline_queue.performed_too_old');
    this.name = 'PerformedTooOldError';
  }
}

/** R-026: the first retry waits 1 s, every next one twice as long, never more than 60 s. */
export const BACKOFF_BASE_MS = 1000;
export const BACKOFF_MAX_MS = 60_000;

/** The wait before attempt `attempts + 1`, after `attempts` failed ones (1 → 1 s, 2 → 2 s, … capped at 60 s). */
export function backoffMs(attempts: number): number {
  if (attempts <= 0) return 0;
  return Math.min(BACKOFF_MAX_MS, BACKOFF_BASE_MS * 2 ** (attempts - 1));
}

/** R-019: the buffer holds {@link QUEUE_CAPACITY} entries; nothing more is taken in. */
export class QueueFullError extends Error {
  constructor() {
    super('offline_queue.full');
    this.name = 'QueueFullError';
  }
}

/** No IndexedDB, the kill switch is off, a clearing is running or the buffer was retired in this tab. */
export class QueueUnavailableError extends Error {
  constructor() {
    super('offline_queue.unavailable');
    this.name = 'QueueUnavailableError';
  }
}

export function isQueueFull(error: unknown): error is QueueFullError {
  return error instanceof QueueFullError;
}

export function isPerformedTooOld(error: unknown): error is PerformedTooOldError {
  return error instanceof PerformedTooOldError;
}

// ── Retirement and clearing (the plan cache's rule, planCache.ts) ─────────────────────────────

let retired = false;
/** What retired the buffer: a clearing of THIS tab's session elsewhere, or a deletion no broadcast explained yet. */
let localClearing = false;
let dbModule: typeof import('./queueDb') | null = null;

function closeConnection(): void {
  dbModule?.forgetWriteQueueConnection();
}

/**
 * `versionchange`: another connection deletes the database (queueDb.ts has closed ours already). Since WP 9.4 only
 * the kill switch deletes `kp-write-queue` (logout, tenant switch and dead session keep it) — and a tab still on
 * the build before it, whose logout wipes every database. Either way this tab stops until a new session.
 */
function deletedElsewhere(): void {
  if (!localClearing) retired = true;
  changed();
}

onOfflineDataEvent((event) => {
  switch (event) {
    case 'local':
      localClearing = true;
      closeConnection();
      break;
    case 'local-done':
      localClearing = false;
      changed();
      break;
    case 'remote':
      retired = true;
      closeConnection();
      changed();
      break;
    case 'foreign':
      // Another account's clearing in another tab keeps the write buffer (it never deletes `kp-write-queue`):
      // nothing to do here — this tab's entries and session are untouched.
      break;
    case 'session':
      retired = false;
      closeConnection();
      changed();
      break;
  }
});

/** Whether this tab may buffer: IndexedDB present, the kill switch on, not retired. */
export function writeQueueAvailable(): boolean {
  if (retired || typeof indexedDB === 'undefined') return false;
  try {
    return isPwaCachingEnabled(runtimeConfig().PWA_CACHING_ENABLED);
  } catch {
    return false;
  }
}

async function database(): Promise<WriteQueueDatabase | null> {
  if (!writeQueueAvailable() || localClearing) return null;
  try {
    dbModule ??= await import('./queueDb');
    return retired || localClearing ? null : dbModule.writeQueueDatabase(deletedElsewhere);
  } catch {
    return null;
  }
}

/** The clearing generation now (`null` = unknown: nothing is written). */
export function queueGeneration(): number | null {
  try {
    return offlineDataGeneration();
  } catch {
    return null;
  }
}

/**
 * Whether the database exists, without creating it: a user who never buffered anything never gets one. Where
 * the browser cannot enumerate (Firefox before 126) the answer is `true` and the open creates an empty one.
 */
export async function writeQueueExists(): Promise<boolean> {
  if (!writeQueueAvailable()) return false;
  if (typeof indexedDB.databases !== 'function') return true;
  try {
    return (await indexedDB.databases()).some((entry) => entry.name === WRITE_QUEUE_DB_NAME);
  } catch {
    return true;
  }
}

// ── Change notification ───────────────────────────────────────────────────────────────────────

const listeners = new Set<() => void>();

/** Something in the buffer changed (in this tab); the snapshot hooks and the sync host re-read. */
export function onQueueChange(listener: () => void): () => void {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}

function changed(): void {
  listeners.forEach((listener) => {
    try {
      listener();
    } catch {
      // A listener's failure never stops a write.
    }
  });
}

// ── Ids ───────────────────────────────────────────────────────────────────────────────────────

/** A UUID v4 for `client_event_id`; `crypto.randomUUID` is missing outside a secure context. */
export function newClientEventId(): string {
  const cryptoApi = globalThis.crypto;
  if (typeof cryptoApi?.randomUUID === 'function') return cryptoApi.randomUUID();
  const bytes = new Uint8Array(16);
  cryptoApi.getRandomValues(bytes);
  bytes[6] = (bytes[6] & 0x0f) | 0x40;
  bytes[8] = (bytes[8] & 0x3f) | 0x80;
  const hex = [...bytes].map((byte) => byte.toString(16).padStart(2, '0')).join('');
  return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(16, 20)}-${hex.slice(20)}`;
}

/** Every `[userKey, tenantKey]` of one user: `['' … [])`, since an array sorts after every string. */
function userRange(userKey: string): [[string, string], [string, never[]]] {
  return [
    [userKey, ''],
    [userKey, []],
  ];
}

function owned(entry: QueueEntry, scope: CacheScope): boolean {
  return entry.userKey === scope.userKey && entry.tenantKey === scope.tenantKey;
}

// ── Capture ───────────────────────────────────────────────────────────────────────────────────

export interface CaptureInput {
  scope: CacheScope;
  bedKey: string;
  bedName: string;
  write: QueuedWrite;
  /** The id an online attempt already sent (its answer got lost): the entry resends exactly that one. */
  id?: string;
}

/**
 * Buffer one write. Rejects with {@link QueueFullError} at {@link QUEUE_CAPACITY} entries and with
 * {@link QueueUnavailableError} when the buffer cannot be used (or a clearing started since the call).
 */
export async function enqueue(input: CaptureInput, now: number = Date.now()): Promise<QueueEntry> {
  if (effectivePerformedAt({ capturedAt: now, write: input.write }) < now - ENTRY_MAX_AGE_DAYS * DAY_MS) {
    // The server would refuse it (V-11): say so now instead of keeping something that can never be sent.
    throw new PerformedTooOldError();
  }
  const generation = queueGeneration();
  const db = await database();
  if (!db || generation === null) throw new QueueUnavailableError();
  const entry: QueueEntry = {
    id: input.id ?? newClientEventId(),
    userKey: input.scope.userKey,
    tenantKey: input.scope.tenantKey,
    capturedAt: now,
    status: 'pending',
    attempts: 0,
    nextAttemptAt: 0,
    syncingSince: null,
    lastErrorCode: null,
    conflictCode: null,
    kept: false,
    expiresAt: 0,
    bedKey: input.bedKey,
    bedName: input.bedName,
    write: input.write,
  };
  entry.expiresAt = expiryOf(entry);
  try {
    await db.transaction('rw', db.entries, async () => {
      if (retired || queueGeneration() !== generation) throw new QueueUnavailableError();
      // R-019 per user: only the capturing user's rows count; the device ceiling is a storage safety net.
      const mine = await db.entries.where('[userKey+tenantKey]').between(...userRange(entry.userKey), true, false).count();
      if (mine >= QUEUE_CAPACITY || (await db.entries.count()) >= QUEUE_DEVICE_CEILING) throw new QueueFullError();
      entry.seq = await db.entries.add(entry);
    });
  } catch (error) {
    if (error instanceof QueueFullError || error instanceof QueueUnavailableError) throw error;
    // Quota, private mode, a deletion in progress.
    throw new QueueUnavailableError();
  }
  changed();
  return entry;
}

// ── Reads ─────────────────────────────────────────────────────────────────────────────────────

/** The scope's entries in capture order (FIFO). Empty without a database. */
export async function listEntries(scope: CacheScope): Promise<QueueEntry[]> {
  if (!(await writeQueueExists())) return [];
  const db = await database();
  if (!db) return [];
  try {
    const rows = await db.entries.where('[userKey+tenantKey]').equals([scope.userKey, scope.tenantKey]).toArray();
    return rows.filter((entry) => owned(entry, scope)).sort((a, b) => (a.seq ?? 0) - (b.seq ?? 0));
  } catch {
    return [];
  }
}

/** All entries of one user, in every tenant: what the capacity counts (R-019). */
export async function totalEntries(userKey: string): Promise<number> {
  return (await countUserEntries(userKey)) ?? 0;
}

/**
 * Every entry of one user, in all their tenants — what an explicit logout discards. Never another user's.
 * `null` = unknown (the buffer exists but cannot be read now: a clearing, a retired tab, a read error) — the
 * logout must then ask without a number, never discard silently (R-056 c).
 */
export async function countUserEntries(userKey: string): Promise<number | null> {
  // Retired or clearing: rows may well exist, this tab just must not read them now.
  if (typeof indexedDB !== 'undefined' && (retired || localClearing)) return null;
  if (!(await writeQueueExists())) return 0;
  const db = await database();
  if (!db) return writeQueueAvailable() ? null : 0;
  try {
    return await db.entries.where('[userKey+tenantKey]').between(...userRange(userKey), true, false).count();
  } catch {
    return null;
  }
}

/**
 * Retention ({@link ENTRY_MAX_AGE_DAYS} by the effective `performed_at`, {@link UNSENDABLE_MAX_AGE_DAYS} for
 * failed and conflict entries): delete the entries of the device — whoever captured them — the server would never
 * take or the user never decided. A database that does not exist is not created for it.
 */
export async function purgeExpiredEntries(now: number = Date.now()): Promise<number> {
  if (!(await writeQueueExists())) return 0;
  const generation = queueGeneration();
  const db = await database();
  if (!db || generation === null) return 0;
  let removed = 0;
  try {
    await db.transaction('rw', db.entries, db.notices, async () => {
      if (retired || queueGeneration() !== generation) return;
      // Keys only — `[expiresAt, userKey]` and the primary key — never a row with its photo bytes.
      const due = db.entries.where('[expiresAt+userKey]').below([now, []]);
      const [keys, seqs] = await Promise.all([due.keys(), due.primaryKeys()]);
      if (seqs.length === 0) return;
      await db.entries.bulkDelete(seqs);
      // Never a silent drop (UI-NFR-012 R-056): the count waits on the device for its owner's next sign-in.
      const perOwner = new Map<string, number>();
      for (const key of keys) {
        const owner = String((key as unknown as [number, string])[1]);
        perOwner.set(owner, (perOwner.get(owner) ?? 0) + 1);
      }
      for (const [userKey, count] of perOwner) {
        const notice = await db.notices.get(userKey);
        await db.notices.put({ userKey, count: (notice?.count ?? 0) + count });
      }
      removed = seqs.length;
    });
  } catch {
    return 0;
  }
  if (removed > 0) changed();
  return removed;
}

/** How many of `userKey`'s entries the retention purge deleted since the notice was last shown; the notice is used up. */
export async function takePurgedCount(userKey: string): Promise<number> {
  if (!(await writeQueueExists())) return 0;
  const db = await database();
  if (!db) return 0;
  try {
    let count = 0;
    await db.transaction('rw', db.notices, async () => {
      count = (await db.notices.get(userKey))?.count ?? 0;
      if (count > 0) await db.notices.delete(userKey);
    });
    return count;
  } catch {
    return 0;
  }
}

/** Entries not yet at the server — pending, syncing, failed and conflicts (kept ones too). */
export async function countUnsynced(scope: CacheScope): Promise<number> {
  return (await listEntries(scope)).length;
}

export interface QueueCounts {
  pending: number;
  failed: number;
  conflict: number;
  total: number;
}

export function countEntries(entries: readonly QueueEntry[]): QueueCounts {
  const counts: QueueCounts = { pending: 0, failed: 0, conflict: 0, total: entries.length };
  for (const entry of entries) {
    if (entry.status === 'failed') counts.failed += 1;
    else if (entry.status === 'conflict') counts.conflict += 1;
    else counts.pending += 1;
  }
  return counts;
}

// ── Updates (the sync and the dialogs) ────────────────────────────────────────────────────────

export type EntryChanges = Partial<Omit<QueueEntry, 'seq' | 'id' | 'userKey' | 'tenantKey' | 'write'>> & {
  write?: QueuedWrite;
};

/**
 * Change one entry of `scope` — unless a clearing started since `generation` (then nothing is written, so a late
 * answer never recreates a deleted database's row). `expect` names the status the entry must still have.
 */
export async function updateEntry(
  scope: CacheScope,
  seq: number,
  changes: EntryChanges,
  { generation = queueGeneration(), expect }: { generation?: number | null; expect?: QueueStatus } = {},
): Promise<boolean> {
  if (generation === null || queueGeneration() !== generation) return false;
  const db = await database();
  if (!db) return false;
  let done = false;
  try {
    await db.transaction('rw', db.entries, async () => {
      if (retired || queueGeneration() !== generation) return;
      const entry = await db.entries.get(seq);
      if (!entry || !owned(entry, scope) || (expect && entry.status !== expect)) return;
      // The retention follows the status: failed / conflict entries go after 90 days, pending ones after 365.
      const expiresAt = expiryOf({ ...entry, ...changes, write: changes.write ?? entry.write });
      await db.entries.update(seq, { ...changes, expiresAt });
      done = true;
    });
  } catch {
    return false;
  }
  if (done) changed();
  return done;
}

/** Delete one entry of `scope` (sent, or discarded). `unlessStatus` keeps an entry a sync is sending. */
export async function removeEntry(
  scope: CacheScope,
  seq: number,
  { generation = queueGeneration(), unlessStatus }: { generation?: number | null; unlessStatus?: QueueStatus } = {},
): Promise<boolean> {
  if (generation === null || queueGeneration() !== generation) return false;
  const db = await database();
  if (!db) return false;
  let done = false;
  try {
    await db.transaction('rw', db.entries, async () => {
      if (retired || queueGeneration() !== generation) return;
      const entry = await db.entries.get(seq);
      if (!entry || !owned(entry, scope) || (unlessStatus && entry.status === unlessStatus)) return;
      await db.entries.delete(seq);
      done = true;
    });
  } catch {
    return false;
  }
  if (done) changed();
  return done;
}

async function findOwn(scope: CacheScope, id: string): Promise<QueueEntry | null> {
  return (await listEntries(scope)).find((entry) => entry.id === id) ?? null;
}

/**
 * "Discard" (conflict, failed) and the undo of a fresh capture: the entry goes. Refused (`false`) while a sync
 * is sending it — the request is out, the server may already have it.
 */
export async function discardEntry(scope: CacheScope, id: string): Promise<boolean> {
  const entry = await findOwn(scope, id);
  if (!entry?.seq) return false;
  return removeEntry(scope, entry.seq, { unlessStatus: 'syncing' });
}

/**
 * "Keep" of a conflict (R-030/R-032, decided for WP 9.4): none of the four WP 9.3 conflict codes can be cured by
 * sending the same request again — the id names another request (`payload_mismatch`), the task is closed or
 * gone (`already_closed`, `missing`), or what it created was deleted (`client_event.deleted`). "Keep" therefore
 * keeps the entry ON THE DEVICE, readable in the dialog with its text and time, never resent; it leaves the
 * device with "Discard", the explicit logout (which asks first) or the retention limit.
 */
export async function keepEntry(scope: CacheScope, id: string): Promise<boolean> {
  const entry = await findOwn(scope, id);
  if (!entry?.seq || entry.status !== 'conflict') return false;
  return updateEntry(scope, entry.seq, { kept: true }, { expect: 'conflict' });
}

/** R-027 "Try again": a failed entry is pending again with a fresh attempt budget — and the SAME id. */
export async function retryEntry(scope: CacheScope, id: string): Promise<boolean> {
  const entry = await findOwn(scope, id);
  if (!entry?.seq || entry.status !== 'failed') return false;
  return updateEntry(
    scope,
    entry.seq,
    { status: 'pending', attempts: 0, nextAttemptAt: 0, lastErrorCode: null, syncingSince: null },
    { expect: 'failed' },
  );
}

/** Whether an error code is one of the four conflicts of WP 9.3. */
export function asConflictCode(code: string | null | undefined): ConflictCode | null {
  switch (code) {
    case 'client_event.payload_mismatch':
    case 'task.already_closed':
    case 'task.missing':
    case 'client_event.deleted':
      return code;
    default:
      return null;
  }
}

/** Tests only: a fresh page — the buffer is usable again and the next call opens a new connection. */
export function resetWriteQueueForTests(): void {
  retired = false;
  localClearing = false;
  dbModule?.forgetWriteQueueConnection();
}
