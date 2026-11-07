import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import {
  clearAllOfflineStorage,
  clearOfflineData,
  postNamespace,
  repostNamespace,
} from '@/pwa/offlineData';

/**
 * REQ-053 WP 9.1 (#2741) — the app side of the cache boundary: what a logout / tenant switch
 * deletes (every API cache and every IndexedDB database), what it keeps (the public build caches),
 * and that the worker hears the namespace from the app.
 */

const CACHE_NAMES = [
  'workbox-precache-v2-https://kamerplanter.example/',
  'kp-static-assets',
  'kp-runtime-config',
  'kp-sw-state',
  'kp:user_1:tenant_a',
  'kp:user_1:tenant_b',
];

let deletedCaches: string[];
let deletedDatabases: string[];
let postMessage: ReturnType<typeof vi.fn>;

function install({ controller = true }: { controller?: boolean } = {}) {
  deletedCaches = [];
  deletedDatabases = [];
  postMessage = vi.fn();
  vi.stubGlobal('caches', {
    keys: vi.fn().mockResolvedValue(CACHE_NAMES),
    delete: vi.fn(async (name: string) => {
      deletedCaches.push(name);
      return true;
    }),
  });
  vi.stubGlobal('indexedDB', {
    databases: vi.fn().mockResolvedValue([{ name: 'kp-plan-cache' }, { name: 'workbox-expiration' }, {}]),
    deleteDatabase: vi.fn((name: string) => {
      deletedDatabases.push(name);
      const request: Record<string, (() => void) | null> = { onsuccess: null, onerror: null, onblocked: null };
      queueMicrotask(() => request.onsuccess?.());
      return request;
    }),
  });
  Object.defineProperty(navigator, 'serviceWorker', {
    configurable: true,
    value: {
      controller: controller ? { postMessage } : null,
      getRegistration: vi.fn().mockResolvedValue({ active: { postMessage } }),
    },
  });
}

afterEach(() => {
  vi.unstubAllGlobals();
  delete (navigator as unknown as Record<string, unknown>).serviceWorker;
});

describe('clearOfflineData (logout, tenant switch)', () => {
  beforeEach(() => install());

  it('deletes every API cache and the namespace state, keeps the public build caches', async () => {
    await clearOfflineData();
    expect(deletedCaches.sort()).toEqual([
      'kp-sw-state',
      'kp:user_1:tenant_a',
      'kp:user_1:tenant_b',
    ]);
  });

  it('deletes every named IndexedDB database', async () => {
    await clearOfflineData();
    expect(deletedDatabases).toEqual(['kp-plan-cache', 'workbox-expiration']);
  });

  it("tells the worker whose session ended, so it ends that user's namespace in every tab", async () => {
    await postNamespace('user_1', 'tenant_a');
    await clearOfflineData();
    expect(postMessage).toHaveBeenLastCalledWith({ type: 'KP_CLEAR_DATA', userKey: 'user_1' });
  });

  it('does not wait forever on a blocked IndexedDB deletion', async () => {
    vi.useFakeTimers();
    vi.stubGlobal('indexedDB', {
      databases: vi.fn().mockResolvedValue([{ name: 'held-open' }]),
      deleteDatabase: vi.fn(() => ({ onsuccess: null, onerror: null, onblocked: null })),
    });
    const done = clearOfflineData();
    await vi.advanceTimersByTimeAsync(2500);
    await expect(done).resolves.toBeUndefined();
    vi.useRealTimers();
  });

  it('never throws when the browser has no storage APIs at all', async () => {
    vi.stubGlobal('caches', undefined);
    vi.stubGlobal('indexedDB', undefined);
    delete (navigator as unknown as Record<string, unknown>).serviceWorker;
    await expect(clearOfflineData()).resolves.toBeUndefined();
  });

  it('survives a failing Cache Storage', async () => {
    vi.stubGlobal('caches', { keys: vi.fn().mockRejectedValue(new Error('insecure')) });
    await expect(clearOfflineData()).resolves.toBeUndefined();
  });
});

describe('clearAllOfflineStorage (kill switch)', () => {
  beforeEach(() => install());

  it('deletes the public build caches too', async () => {
    await clearAllOfflineStorage();
    expect(deletedCaches.sort()).toEqual([...CACHE_NAMES].sort());
    expect(deletedDatabases).toEqual(['kp-plan-cache', 'workbox-expiration']);
  });
});

describe('postNamespace', () => {
  it('posts the keys to the controlling worker and re-posts them on demand', async () => {
    install();
    await postNamespace('user_1', 'tenant_a');
    expect(postMessage).toHaveBeenCalledWith({ type: 'KP_SET_NAMESPACE', userKey: 'user_1', tenantKey: 'tenant_a' });
    postMessage.mockClear();
    await repostNamespace();
    expect(postMessage).toHaveBeenCalledWith({ type: 'KP_SET_NAMESPACE', userKey: 'user_1', tenantKey: 'tenant_a' });
  });

  it('reaches the active worker when none controls the page yet', async () => {
    install({ controller: false });
    await postNamespace('user_1', 'tenant_a');
    expect(postMessage).toHaveBeenCalledTimes(1);
  });

  it('forgets the namespace after a clear', async () => {
    install();
    await postNamespace('user_1', 'tenant_a');
    await clearOfflineData();
    postMessage.mockClear();
    await repostNamespace();
    expect(postMessage).toHaveBeenCalledWith({ type: 'KP_SET_NAMESPACE', userKey: null, tenantKey: null });
  });
});
