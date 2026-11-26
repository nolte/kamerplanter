import 'fake-indexeddb/auto';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { PLAN_CACHE_DB_NAME } from '@/pwa/storageWipe';
import { planEntry, readCached, resetPlanCacheForTests, writeCached, type CacheScope } from './planCache';

/**
 * #3082 — a document that is hidden (`pagehide`: it may enter the back/forward cache; `freeze`) must not leave a
 * connection, an open or an upgrade of `kp-plan-cache` behind: a frozen document runs no script, so an upgrade it
 * never finishes holds every later open of the database in the next document.
 *
 * What `fake-indexeddb` can model and what it cannot: it has the open queue, version change transactions, `abort()`
 * and `close()` as the spec defines them, so the tests assert what hiding does to them — the upgrade in flight is
 * aborted, the connection is closed, a queued open is undone when it comes through, nothing opens while hidden,
 * and the next open after `pageshow` works. It has no frozen event loop: that a running upgrade in a frozen
 * document blocks the next document's open is browser behaviour (Chrome, nightly 45796165432) and is not
 * reproduced here.
 */

const ALICE: CacheScope = { userKey: 'alice', tenantKey: 'tenant_a' };
const PLAN = { site: { key: 'site_1', name: 'Garten' }, locations: [] };

/** Every native open of the plan cache this test sees, in order. */
let opens: IDBOpenDBRequest[] = [];

function settle(ms = 50): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function deleteDatabase(name = PLAN_CACHE_DB_NAME): Promise<'success' | 'blocked' | 'error'> {
  return new Promise((resolve) => {
    const request = indexedDB.deleteDatabase(name);
    request.onsuccess = () => resolve('success');
    request.onerror = () => resolve('error');
    request.onblocked = () => resolve('blocked');
  });
}

async function databaseNames(): Promise<string[]> {
  return (await indexedDB.databases()).map((database) => database.name ?? '');
}

/** The page enters the back/forward cache (`persisted`) — what Chrome fires before it freezes the document. */
function hidePage(): void {
  const event = new Event('pagehide') as Event & { persisted: boolean };
  Object.defineProperty(event, 'persisted', { value: true });
  window.dispatchEvent(event);
}

function showPage(): void {
  window.dispatchEvent(new Event('pageshow'));
}

/** Whether a connection still takes transactions (`close()` makes `transaction()` throw InvalidStateError). */
function isOpen(connection: IDBDatabase): boolean {
  try {
    connection.transaction('plans').abort();
    return true;
  } catch {
    return false;
  }
}

/** What became of an open request: its outcome once it settled. */
function outcome(request: IDBOpenDBRequest): Promise<string> {
  return new Promise((resolve) => {
    if (request.readyState === 'done') {
      resolve(request.error ? request.error.name : 'success');
      return;
    }
    request.addEventListener('success', () => resolve('success'));
    request.addEventListener('error', () => resolve(request.error?.name ?? 'error'));
  });
}

beforeEach(async () => {
  resetPlanCacheForTests();
  await deleteDatabase();
  opens = [];
  const nativeOpen = indexedDB.open.bind(indexedDB);
  vi.spyOn(indexedDB, 'open').mockImplementation((name: string, version?: number) => {
    const request = version === undefined ? nativeOpen(name) : nativeOpen(name, version);
    if (name === PLAN_CACHE_DB_NAME) opens.push(request);
    return request;
  });
});

afterEach(async () => {
  vi.restoreAllMocks();
  showPage();
  resetPlanCacheForTests();
  await deleteDatabase();
});

describe('hiding the page leaves nothing of the plan cache behind (#3082)', () => {
  it('aborts the upgrade that creates the database and closes its connection', async () => {
    // The first write of a session creates the database (an upgrade 0 -> 20); the page is hidden while that
    // version change transaction still runs — the state the nightly's /login document entered the bfcache in.
    let upgrading: IDBOpenDBRequest | null = null;
    let connection: IDBDatabase | null = null;
    const hiddenDuringUpgrade = new Promise<void>((resolve) => {
      const nativeOpen = vi.mocked(indexedDB.open).getMockImplementation()!;
      vi.mocked(indexedDB.open).mockImplementation((name: string, version?: number) => {
        const request = nativeOpen(name, version);
        upgrading = request;
        request.addEventListener('upgradeneeded', () => {
          connection = request.result;
          // After every upgradeneeded listener (Dexie's creates the stores), before the transaction commits.
          queueMicrotask(() => {
            hidePage();
            resolve();
          });
        });
        return request;
      });
    });

    const write = writeCached(planEntry(ALICE, 'site_1'), PLAN, Date.now());
    await hiddenDuringUpgrade;
    await write;
    await settle();

    expect(upgrading).not.toBeNull();
    const request = upgrading as unknown as IDBOpenDBRequest;
    expect(await outcome(request)).toBe('AbortError');
    expect(connection).not.toBeNull();
    expect(isOpen(connection as unknown as IDBDatabase)).toBe(false);
    // An aborted creation leaves no database behind.
    expect(await databaseNames()).not.toContain(PLAN_CACHE_DB_NAME);
  });

  it('closes an open connection, opens nothing while hidden, and opens again after pageshow', async () => {
    await writeCached(planEntry(ALICE, 'site_1'), PLAN, Date.now());
    expect(opens).toHaveLength(1);
    const first = opens[0];
    expect(await outcome(first)).toBe('success');
    expect(isOpen(first.result)).toBe(true);

    hidePage();
    expect(isOpen(first.result)).toBe(false);

    await writeCached(planEntry(ALICE, 'site_2'), PLAN, Date.now());
    expect(await readCached(planEntry(ALICE, 'site_1'))).toBeNull();
    expect(opens).toHaveLength(1);

    showPage();
    expect(await readCached(planEntry(ALICE, 'site_1'))).toMatchObject({ data: PLAN });
    expect(opens).toHaveLength(2);
    expect(await outcome(opens[1])).toBe('success');
  });

  it('undoes an open that was still queued when the page was hidden', async () => {
    // Another document holds a connection and does not close it; a deletion queues behind it, and this page's
    // open queues behind the deletion. An open cannot be cancelled while it waits.
    const other = await new Promise<IDBDatabase>((resolve) => {
      const request = indexedDB.open(PLAN_CACHE_DB_NAME, 20);
      request.onupgradeneeded = () => request.result.createObjectStore('plans');
      request.onsuccess = () => resolve(request.result);
    });
    opens = [];
    const deletion = deleteDatabase();
    expect(await deletion).toBe('blocked');

    const write = writeCached(planEntry(ALICE, 'site_1'), PLAN, Date.now());
    await settle();
    expect(opens).toHaveLength(1);
    const queued = opens[0];
    expect(queued.readyState).toBe('pending');

    hidePage();
    // The other document lets go: the deletion runs, then the queued open comes through.
    other.close();
    await write;
    await settle(100);

    // Its upgrade was aborted when it came through: no connection, no database created from it.
    expect(await outcome(queued)).toBe('AbortError');
    expect(await databaseNames()).not.toContain(PLAN_CACHE_DB_NAME);
  });

  it('aborts a write transaction still running when the page is hidden', async () => {
    // Dexie binds `IDBDatabase.transaction` when it opens, so the hook sits on the prototype before the open; it
    // hides the page once the second write's transaction exists and before its requests are done.
    const prototype = Object.getPrototypeOf(
      await new Promise<IDBDatabase>((resolve) => {
        const request = indexedDB.open('kp-prototype-probe');
        request.onsuccess = () => {
          request.result.close();
          resolve(request.result);
        };
      }),
    ) as IDBDatabase;
    await deleteDatabase('kp-prototype-probe');
    let hideOnWrite = false;
    const nativeTransaction = prototype.transaction;
    const transactionSpy = vi.spyOn(prototype, 'transaction').mockImplementation(function (
      this: IDBDatabase,
      ...args: Parameters<IDBDatabase['transaction']>
    ) {
      const transaction = nativeTransaction.apply(this, args);
      if (hideOnWrite && args[1] === 'readwrite') {
        hideOnWrite = false;
        queueMicrotask(hidePage);
      }
      return transaction;
    });
    opens = [];
    await writeCached(planEntry(ALICE, 'site_0'), PLAN, Date.now());
    const connection = opens[0].result;
    const put = vi.spyOn(Object.getPrototypeOf(connection.transaction('plans', 'readonly').objectStore('plans')), 'put');

    hideOnWrite = true;
    await writeCached(planEntry(ALICE, 'site_1'), PLAN, Date.now());
    expect(hideOnWrite).toBe(false);
    transactionSpy.mockRestore();

    expect(put).not.toHaveBeenCalled();
    expect(isOpen(connection)).toBe(false);
    showPage();
    expect(await readCached(planEntry(ALICE, 'site_1'))).toBeNull();
    expect(await readCached(planEntry(ALICE, 'site_0'))).toMatchObject({ data: PLAN });
  });
});

describe('a page shown again (#3082 review S3, nits)', () => {
  it('freeze closes and opens nothing; resume opens again', async () => {
    await writeCached(planEntry(ALICE, 'site_1'), PLAN, Date.now());
    const first = opens[0];
    document.dispatchEvent(new Event('freeze'));
    expect(isOpen(first.result)).toBe(false);
    expect(await readCached(planEntry(ALICE, 'site_1'))).toBeNull();
    expect(opens).toHaveLength(1);

    document.dispatchEvent(new Event('resume'));
    expect(await readCached(planEntry(ALICE, 'site_1'))).toMatchObject({ data: PLAN });
  });

  it('a frozen page that becomes visible without a resume uses the cache again', async () => {
    await writeCached(planEntry(ALICE, 'site_1'), PLAN, Date.now());
    document.dispatchEvent(new Event('freeze'));
    vi.spyOn(document, 'visibilityState', 'get').mockReturnValue('visible');
    document.dispatchEvent(new Event('visibilitychange'));
    expect(await readCached(planEntry(ALICE, 'site_1'))).toMatchObject({ data: PLAN });
  });

  it('a database deleted while the page was in the bfcache retires the cache (no refill under the old scope)', async () => {
    await writeCached(planEntry(ALICE, 'site_1'), PLAN, Date.now());
    hidePage();
    // Another tab clears; this frozen page has no connection, so no versionchange reaches it.
    expect(await deleteDatabase()).toBe('success');
    showPage();
    await writeCached(planEntry(ALICE, 'site_2'), PLAN, Date.now());
    await settle();

    expect(await databaseNames()).not.toContain(PLAN_CACHE_DB_NAME);
  });

  it('without indexedDB.databases() a page shown again after holding the database retires as well', async () => {
    await writeCached(planEntry(ALICE, 'site_1'), PLAN, Date.now());
    hidePage();
    const databases = indexedDB.databases;
    Object.defineProperty(indexedDB, 'databases', { configurable: true, value: undefined });
    try {
      showPage();
      await writeCached(planEntry(ALICE, 'site_2'), PLAN, Date.now());
      await settle();
    } finally {
      Object.defineProperty(indexedDB, 'databases', { configurable: true, value: databases });
    }
    // Read back in a fresh page state: the write did not land, it is not just hidden by the retirement.
    resetPlanCacheForTests();
    expect(await readCached(planEntry(ALICE, 'site_1'))).toMatchObject({ data: PLAN });
    expect(await readCached(planEntry(ALICE, 'site_2'))).toBeNull();
  });

  it('a database still there keeps the cache in use after the page is shown', async () => {
    await writeCached(planEntry(ALICE, 'site_1'), PLAN, Date.now());
    hidePage();
    showPage();
    await writeCached(planEntry(ALICE, 'site_2'), PLAN, Date.now());
    expect(await readCached(planEntry(ALICE, 'site_2'))).toMatchObject({ data: PLAN });
  });
});
