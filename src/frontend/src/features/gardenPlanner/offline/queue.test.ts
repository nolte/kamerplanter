import 'fake-indexeddb/auto';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { WRITE_QUEUE_DB_NAME, APP_DATABASE_NAMES } from '@/pwa/storageWipe';
import {
  ALICE_A,
  ALICE_B,
  BOB_A,
  capture,
  completeWrite,
  emptyWriteQueue,
  noteWrite,
  testWriteQueueDatabase,
} from '@/test/writeQueueTestKit';
import {
  BACKOFF_MAX_MS,
  QUEUE_CAPACITY,
  QueueFullError,
  ENTRY_MAX_AGE_DAYS,
  backoffMs,
  countUnsynced,
  countUserEntries,
  purgeExpiredEntries,
  discardEntry,
  keepEntry,
  listEntries,
  newClientEventId,
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

  it('counts the entries of every scope on the device', async () => {
    await fill(QUEUE_CAPACITY, BOB_A);
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

  it('deletes every entry of the device older than a year, whoever captured it, and keeps the rest', async () => {
    expect(ENTRY_MAX_AGE_DAYS).toBe(365);
    await capture(ALICE_A, noteWrite('too old'), NOW - 366 * DAY);
    await capture(BOB_A, noteWrite('too old, bob'), NOW - 400 * DAY);
    const fresh = await capture(ALICE_A, noteWrite('fresh'), NOW - 364 * DAY);
    expect(await purgeExpiredEntries(NOW)).toBe(2);
    expect((await listEntries(ALICE_A)).map((entry) => entry.id)).toEqual([fresh.id]);
    expect(await listEntries(BOB_A)).toEqual([]);
  });

  it('is purged before a sync sends anything', async () => {
    const { syncQueue } = await import('./sync');
    const sent: string[] = [];
    await capture(ALICE_A, noteWrite('too old'), NOW - 366 * DAY);
    await syncQueue({ scope: ALICE_A, now: () => NOW, send: async (entry) => void sent.push(entry.id) });
    expect(sent).toEqual([]);
    expect(await listEntries(ALICE_A)).toEqual([]);
  });

  it('does not create the database on app start when there is none', async () => {
    await indexedDB.deleteDatabase(WRITE_QUEUE_DB_NAME);
    const { resetWriteQueueForTests } = await import('./queue');
    resetWriteQueueForTests();
    await new Promise((resolve) => setTimeout(resolve, 10));
    expect(await purgeExpiredEntries(NOW)).toBe(0);
    expect((await indexedDB.databases()).map((database) => database.name)).not.toContain(WRITE_QUEUE_DB_NAME);
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
