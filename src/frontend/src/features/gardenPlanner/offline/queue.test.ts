import 'fake-indexeddb/auto';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { WRITE_QUEUE_DB_NAME, APP_DATABASE_NAMES } from '@/pwa/storageWipe';
import {
  ALICE_A,
  ALICE_B,
  BOB_A,
  capture,
  completeWrite,
  emptyWriteQueue,
  noteWrite,
  storeRow,
  testWriteQueueDatabase,
} from '@/test/writeQueueTestKit';
import {
  BACKOFF_MAX_MS,
  QUEUE_CAPACITY,
  QueueFullError,
  ENTRY_MAX_AGE_DAYS,
  PerformedTooOldError,
  UNSENDABLE_MAX_AGE_DAYS,
  backoffMs,
  countUnsynced,
  countUserEntries,
  purgeExpiredEntries,
  discardEntry,
  keepEntry,
  listEntries,
  newClientEventId,
  resetWriteQueueForTests,
  retryEntry,
  updateEntry,
  writeQueueAvailable,
} from './queue';
import type { QueueEntry } from './queueTypes';

/**
 * REQ-053 WP 9.4 (#2744), UI-NFR-012 R-016…R-019 — the offline write buffer against a real IndexedDB
 * (`fake-indexeddb`): the capacity of 500, the capture order, the owner scope (G-W9 a), one `client_event_id` per
 * entry (G-W9 f), keep / discard / try again, and the kill switch.
 */

const UUID_V4 = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/;

beforeEach(async () => {
  await emptyWriteQueue();
});

afterEach(() => {
  delete (window as { __RUNTIME_CONFIG__?: unknown }).__RUNTIME_CONFIG__;
});

/** `count` entries of `scope` written straight into the table (the capacity test needs 499 of them). */
async function fill(count: number, scope = ALICE_A): Promise<void> {
  const rows: QueueEntry[] = Array.from({ length: count }, (_, index) => ({
    id: newClientEventId(),
    userKey: scope.userKey,
    tenantKey: scope.tenantKey,
    capturedAt: index,
    status: 'pending',
    attempts: 0,
    nextAttemptAt: 0,
    syncingSince: null,
    lastErrorCode: null,
    conflictCode: null,
    kept: false,
    expiresAt: Number.MAX_SAFE_INTEGER,
    bedKey: 'loc_a',
    bedName: 'Raised bed 1',
    write: noteWrite(`n${index}`),
  }));
  await testWriteQueueDatabase().entries.bulkAdd(rows);
}

describe('capacity (R-019)', () => {
  it('takes the 500th entry and refuses the 501st with QueueFullError', async () => {
    await fill(QUEUE_CAPACITY - 1);
    await expect(capture(ALICE_A)).resolves.toMatchObject({ status: 'pending' });
    await expect(capture(ALICE_A)).rejects.toBeInstanceOf(QueueFullError);
    expect(await testWriteQueueDatabase().entries.count()).toBe(QUEUE_CAPACITY);
  });

  it("counts only the capturing user's entries — another user's full buffer neither blocks nor shows", async () => {
    await fill(QUEUE_CAPACITY, BOB_A);
    await expect(capture(ALICE_A)).resolves.toMatchObject({ userKey: 'alice' });
    await expect(capture(BOB_A)).rejects.toBeInstanceOf(QueueFullError);
    // Alice's tenants share her 500.
    await fill(QUEUE_CAPACITY - 1, ALICE_B);
    await expect(capture(ALICE_A)).rejects.toBeInstanceOf(QueueFullError);
  });

  it('refuses at the device ceiling, a storage safety net far above one user', async () => {
    const { QUEUE_DEVICE_CEILING } = await import('./queue');
    for (let user = 0; user < QUEUE_DEVICE_CEILING / QUEUE_CAPACITY; user += 1) {
      await fill(QUEUE_CAPACITY - 1, { userKey: `u${user}`, tenantKey: 't' });
    }
    await fill(QUEUE_DEVICE_CEILING - (await testWriteQueueDatabase().entries.count()), { userKey: 'filler', tenantKey: 't' });
    await expect(capture(ALICE_A)).rejects.toBeInstanceOf(QueueFullError);
  });
});

describe('entries (R-017, G-W9 f)', () => {
  it('carries capture time, user, tenant, status pending and its own UUID client_event_id', async () => {
    const at = Date.UTC(2026, 10, 8, 6, 30);
    const entry = await capture(ALICE_A, completeWrite(), at);
    expect(entry).toMatchObject({
      userKey: 'alice',
      tenantKey: 'tenant_a',
      capturedAt: at,
      status: 'pending',
      attempts: 0,
    });
    expect(entry.id).toMatch(UUID_V4);
    const other = await capture(ALICE_A);
    expect(other.id).not.toBe(entry.id);
  });

  it('keeps an id an online attempt already sent', async () => {
    const id = newClientEventId();
    const { enqueue } = await import('./queue');
    const entry = await enqueue({ scope: ALICE_A, bedKey: 'loc_a', bedName: 'B', write: noteWrite(), id });
    expect(entry.id).toBe(id);
  });

  it('lists in capture order (FIFO, R-023)', async () => {
    await capture(ALICE_A, noteWrite('first'), 3000);
    await capture(ALICE_A, noteWrite('second'), 1000); // an earlier clock does not jump the queue
    await capture(ALICE_A, noteWrite('third'), 2000);
    const summaries = (await listEntries(ALICE_A)).map((entry) =>
      entry.write.kind === 'note' ? entry.write.body.summary : null,
    );
    expect(summaries).toEqual(['first', 'second', 'third']);
  });
});

describe('owner scope (G-W9 a)', () => {
  it('lists, counts, keeps and discards only the entries of the scope they were captured in', async () => {
    const mine = await capture(ALICE_A);
    const otherTenant = await capture(ALICE_B);
    const otherUser = await capture(BOB_A);
    expect((await listEntries(ALICE_A)).map((entry) => entry.id)).toEqual([mine.id]);
    expect(await countUnsynced(ALICE_B)).toBe(1);
    expect(await discardEntry(ALICE_A, otherUser.id)).toBe(false);
    expect(await discardEntry(ALICE_A, otherTenant.id)).toBe(false);
    expect(await updateEntry(ALICE_A, otherUser.seq!, { status: 'failed' })).toBe(false);
    expect((await listEntries(BOB_A))[0].status).toBe('pending');
    expect(await discardEntry(ALICE_A, mine.id)).toBe(true);
    expect(await testWriteQueueDatabase().entries.count()).toBe(2);
  });
});

describe('keep, discard, try again (R-027, R-030/R-032)', () => {
  it('"Keep" marks a conflict kept and leaves it on the device; it never applies to a pending entry', async () => {
    const entry = await capture(ALICE_A);
    expect(await keepEntry(ALICE_A, entry.id)).toBe(false);
    await updateEntry(ALICE_A, entry.seq!, { status: 'conflict', conflictCode: 'task.already_closed' });
    expect(await keepEntry(ALICE_A, entry.id)).toBe(true);
    const [kept] = await listEntries(ALICE_A);
    expect(kept).toMatchObject({ status: 'conflict', kept: true, id: entry.id });
  });

  it('"Try again" makes a failed entry pending with a fresh budget and the SAME id', async () => {
    const entry = await capture(ALICE_A);
    await updateEntry(ALICE_A, entry.seq!, { status: 'failed', attempts: 5, lastErrorCode: 'network', nextAttemptAt: 99 });
    expect(await retryEntry(ALICE_A, entry.id)).toBe(true);
    const [again] = await listEntries(ALICE_A);
    expect(again).toMatchObject({ id: entry.id, status: 'pending', attempts: 0, nextAttemptAt: 0, lastErrorCode: null });
  });

  it('refuses to discard an entry a sync is sending', async () => {
    const entry = await capture(ALICE_A);
    await updateEntry(ALICE_A, entry.seq!, { status: 'syncing', syncingSince: 1 });
    expect(await discardEntry(ALICE_A, entry.id)).toBe(false);
    expect(await countUnsynced(ALICE_A)).toBe(1);
  });
});

describe("retention (GDPR, the server's MAX_AGE_DAYS)", () => {
  const DAY = 24 * 60 * 60 * 1000;
  const NOW = Date.UTC(2026, 10, 8, 12);

  it('deletes every pending entry of the device whose performed_at is older than a year, whoever captured it', async () => {
    expect(ENTRY_MAX_AGE_DAYS).toBe(365);
    await storeRow(ALICE_A, { capturedAt: NOW - 366 * DAY });
    await storeRow(BOB_A, { capturedAt: NOW - 400 * DAY });
    // Captured yesterday, but the note is dated back past the limit: the server would refuse it — it goes too.
    await storeRow(ALICE_A, { capturedAt: NOW - DAY, performedAt: NOW - 370 * DAY });
    const fresh = await storeRow(ALICE_A, { capturedAt: NOW - 364 * DAY });
    expect(await purgeExpiredEntries(NOW)).toBe(3);
    expect((await listEntries(ALICE_A)).map((entry) => entry.id)).toEqual([fresh.id]);
    expect(await listEntries(BOB_A)).toEqual([]);
  });

  it('deletes failed and conflict entries 90 days after capture; a pending one of the same age stays', async () => {
    expect(UNSENDABLE_MAX_AGE_DAYS).toBe(90);
    await storeRow(ALICE_A, { capturedAt: NOW - 91 * DAY, status: 'failed' });
    await storeRow(ALICE_A, { capturedAt: NOW - 91 * DAY, status: 'conflict' });
    const young = await storeRow(ALICE_A, { capturedAt: NOW - 89 * DAY, status: 'conflict' });
    const pending = await storeRow(ALICE_A, { capturedAt: NOW - 91 * DAY });
    expect(await purgeExpiredEntries(NOW)).toBe(2);
    expect((await listEntries(ALICE_A)).map((entry) => entry.id)).toEqual([young.id, pending.id]);
  });

  it('refuses a capture whose performed_at the server would no longer accept', async () => {
    const old = { ...noteWrite(), body: { ...(noteWrite() as Extract<ReturnType<typeof noteWrite>, { kind: 'note' }>).body, performed_at: new Date(NOW - 366 * DAY).toISOString() } };
    await expect(capture(ALICE_A, old as ReturnType<typeof noteWrite>, NOW)).rejects.toBeInstanceOf(PerformedTooOldError);
    expect(await listEntries(ALICE_A)).toEqual([]);
  });

  it('is purged before a sync sends anything', async () => {
    const { syncQueue } = await import('./sync');
    const sent: string[] = [];
    await storeRow(ALICE_A, { capturedAt: NOW - 366 * DAY });
    await syncQueue({ scope: ALICE_A, now: () => NOW, send: async (entry) => void sent.push(entry.id) });
    expect(sent).toEqual([]);
    expect(await listEntries(ALICE_A)).toEqual([]);
  });

  it('does not create the database on app start when there is none', async () => {
    const { resetWriteQueueForTests } = await import('./queue');
    resetWriteQueueForTests(); // closes this tab's connection, so the deletion goes through
    await new Promise<void>((resolve) => {
      const request = indexedDB.deleteDatabase(WRITE_QUEUE_DB_NAME);
      request.onsuccess = () => resolve();
      request.onerror = () => resolve();
    });
    expect(await purgeExpiredEntries(NOW)).toBe(0);
    expect((await indexedDB.databases()).map((database) => database.name)).not.toContain(WRITE_QUEUE_DB_NAME);
  });
});

describe("another account's clearing (review 9)", () => {
  it('keeps this tab buffering: it neither deletes kp-write-queue nor retires the buffer here', async () => {
    const { retireFromOtherTab } = await import('@/test/writeQueueTestKit');
    await capture(ALICE_A);
    const { OFFLINE_CLEAR_CHANNEL } = await import('@/pwa/offlineData');
    await retireFromOtherTab('alice'); // sets this tab's namespace to alice, then retires…
    resetWriteQueueForTests(); // a fresh page for this tab, its namespace still alice
    const channel = new BroadcastChannel(OFFLINE_CLEAR_CHANNEL);
    channel.postMessage({ type: 'offline-data-cleared', userKey: 'bob' }); // …bob logs out in another tab
    channel.close();
    await new Promise((resolve) => setTimeout(resolve, 30));
    expect(writeQueueAvailable()).toBe(true);
    await expect(capture(ALICE_A)).resolves.toMatchObject({ userKey: 'alice' });
    expect(await listEntries(ALICE_A)).toHaveLength(2);
  });
});

describe('the logout count', () => {
  it("counts the user's entries in every tenant, never another user's", async () => {
    await capture(ALICE_A);
    await capture(ALICE_B);
    await capture(BOB_A);
    expect(await countUserEntries('alice')).toBe(2);
    expect(await countUserEntries('bob')).toBe(1);
    expect(await countUserEntries('carol')).toBe(0);
  });

  it('answers null (unknown) — never 0 — while the buffer cannot be read in this tab', async () => {
    await capture(ALICE_A);
    const { retireFromOtherTab } = await import('@/test/writeQueueTestKit');
    await retireFromOtherTab('alice'); // another tab ended this session: the buffer is retired here
    expect(await countUserEntries('alice')).toBeNull();
  });
});

describe('backoff (R-026)', () => {
  it('waits 1 s, 2 s, 4 s, 8 s … and never more than 60 s', () => {
    expect([1, 2, 3, 4, 5].map(backoffMs)).toEqual([1000, 2000, 4000, 8000, 16000]);
    expect(backoffMs(7)).toBe(BACKOFF_MAX_MS);
    expect(backoffMs(30)).toBe(60_000);
    expect(backoffMs(0)).toBe(0);
  });
});

describe('database and kill switch', () => {
  it('lives in its own database that every clearing knows by name', async () => {
    await capture(ALICE_A);
    expect((await indexedDB.databases()).map((database) => database.name)).toContain(WRITE_QUEUE_DB_NAME);
    expect(APP_DATABASE_NAMES).toContain(WRITE_QUEUE_DB_NAME);
  });

  it('is off with PWA_CACHING_ENABLED=false: nothing is buffered', async () => {
    (window as { __RUNTIME_CONFIG__?: unknown }).__RUNTIME_CONFIG__ = { PWA_CACHING_ENABLED: 'false' };
    expect(writeQueueAvailable()).toBe(false);
    await expect(capture(ALICE_A)).rejects.toThrow('offline_queue.unavailable');
    expect(await listEntries(ALICE_A)).toEqual([]);
  });
});

describe('the purge reads keys only and keeps its notice on the device (review 3/4)', () => {
  const DAY = 24 * 60 * 60 * 1000;
  const NOW = Date.UTC(2026, 10, 8, 12);

  it('selects what is due by the [expiresAt+userKey] index — no row (and no photo) is read', async () => {
    await storeRow(ALICE_A, { capturedAt: NOW - 400 * DAY });
    await storeRow(BOB_A, { capturedAt: NOW - 100 * DAY, status: 'failed' });
    await storeRow(ALICE_A, { capturedAt: NOW - DAY });
    const spies = [
      vi.spyOn(IDBObjectStore.prototype, 'getAll'),
      vi.spyOn(IDBObjectStore.prototype, 'openCursor'),
      vi.spyOn(IDBIndex.prototype, 'getAll'),
      vi.spyOn(IDBIndex.prototype, 'openCursor'),
    ];
    try {
      expect(await purgeExpiredEntries(NOW)).toBe(2);
      for (const spy of spies) expect(spy).not.toHaveBeenCalled();
    } finally {
      spies.forEach((spy) => spy.mockRestore());
    }
    expect(await listEntries(ALICE_A)).toHaveLength(1);
  });

  it("keeps each owner's notice across a reload until that owner takes it — then it is used up", async () => {
    const { acknowledgePurged, readPurgedCount } = await import('./queue');
    const takePurgedCount = async (userKey: string) => {
      const count = await readPurgedCount(userKey);
      await acknowledgePurged(userKey, count);
      return count;
    };
    await storeRow(BOB_A, { capturedAt: NOW - 400 * DAY });
    await storeRow(BOB_A, { capturedAt: NOW - 95 * DAY, status: 'conflict' });
    await storeRow(ALICE_A, { capturedAt: NOW - 400 * DAY });
    expect(await purgeExpiredEntries(NOW)).toBe(3); // alice is signed in, bob is not
    resetWriteQueueForTests(); // a reload: nothing in memory survives
    expect(await takePurgedCount('bob')).toBe(2);
    expect(await takePurgedCount('bob')).toBe(0);
    expect(await takePurgedCount('alice')).toBe(1);
  });

  it('a notice that was read but not acknowledged (nobody saw it) is still there; an acknowledge takes off only what was shown', async () => {
    const { acknowledgePurged, readPurgedCount } = await import('./queue');
    await storeRow(BOB_A, { capturedAt: NOW - 400 * DAY });
    await purgeExpiredEntries(NOW);
    expect(await readPurgedCount('bob')).toBe(1);
    expect(await readPurgedCount('bob')).toBe(1); // reading consumes nothing
    await storeRow(BOB_A, { capturedAt: NOW - 400 * DAY });
    await purgeExpiredEntries(NOW); // a purge between showing and acknowledging
    await acknowledgePurged('bob', 1);
    expect(await readPurgedCount('bob')).toBe(1);
  });

  it('a status change moves the expiry: failed after 90 days of capture, back to 365 on "Try again"', async () => {
    const entry = await capture(ALICE_A, noteWrite(), NOW - 100 * DAY);
    await updateEntry(ALICE_A, entry.seq!, { status: 'failed' });
    expect((await testWriteQueueDatabase().entries.get(entry.seq!))?.expiresAt).toBe(NOW - 10 * DAY);
    await retryEntry(ALICE_A, entry.id);
    expect((await testWriteQueueDatabase().entries.get(entry.seq!))?.expiresAt).toBeGreaterThan(NOW);
  });

  it('upgrades a version-1 database: every row gets its expiry', async () => {
    const Dexie = (await import('dexie')).default;
    resetWriteQueueForTests();
    await new Promise<void>((resolve) => {
      const request = indexedDB.deleteDatabase(WRITE_QUEUE_DB_NAME);
      request.onsuccess = () => resolve();
      request.onerror = () => resolve();
    });
    const v1 = new Dexie(WRITE_QUEUE_DB_NAME);
    v1.version(1).stores({ entries: '++seq, &id, [userKey+tenantKey], status, capturedAt' });
    // A version-1 row has no `expiresAt`.
    const legacy: Partial<QueueEntry> = await storeRowShape(ALICE_A, NOW - 400 * DAY);
    delete legacy.expiresAt;
    await v1.table('entries').add(legacy);
    v1.close();
    expect(await purgeExpiredEntries(NOW)).toBe(1);
  });
});

async function storeRowShape(scope: { userKey: string; tenantKey: string }, capturedAt: number): Promise<QueueEntry> {
  return {
    id: newClientEventId(),
    userKey: scope.userKey,
    tenantKey: scope.tenantKey,
    capturedAt,
    status: 'pending',
    attempts: 0,
    nextAttemptAt: 0,
    syncingSince: null,
    lastErrorCode: null,
    conflictCode: null,
    kept: false,
    expiresAt: 0,
    bedKey: 'loc_a',
    bedName: 'B',
    write: {
      kind: 'note',
      body: { location_key: 'loc_a', category: 'note', summary: 'legacy', performed_at: new Date(capturedAt).toISOString() },
    },
  };
}
