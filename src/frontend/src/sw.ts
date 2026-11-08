/// <reference lib="webworker" />
/**
 * Kamerplanter service worker (UI-NFR-012 basis, REQ-053 WP 9.1, #2741).
 *
 * Built by `vite-plugin-pwa` in `injectManifest` mode and served as `/sw.js` — the same URL the former
 * hand-written push-only worker had, so an existing registration updates in place instead of a
 * second worker running beside it. Responsibilities:
 *
 * 1. Web Push delivery and notification clicks (taken over from `public/sw.js`).
 * 2. Precache of the app shell — `index.html`, the entry chunk and the chunks it preloads (R-007,
 *    R-010) — and a navigation fallback to `index.html`.
 * 3. Same-origin static assets cache-first (R-008): the lazy route chunks land here on first use.
 * 4. Allowlisted tenant-scoped API reads network-first, 15 min TTL, 50 MB per namespace (R-009,
 *    R-012, R-013), in a cache named `kp:{user_key}:{tenant_key}` — PER CLIENT: each tab posts its
 *    own keys (`postMessage`; the worker never reads a token), and a request is served from and
 *    written into only its own tab's namespace. Without a namespace a tab gets network only.
 * 5. Kill switch (G-W9 e): `PWA_CACHING_ENABLED=false` in `/runtime-config.js` makes the worker
 *    delete every cache and IndexedDB database and unregister itself.
 *
 * Updates wait for the user (R-014): a new worker stays `waiting` until the app posts `SKIP_WAITING`
 * from the update banner. Type-checked by `tsconfig.sw.json` (WebWorker lib), not the app program.
 * In `vite dev` (Skaffold's dev target) the plugin serves this worker as a module at
 * `/dev-sw.js?dev-sw` without the precache, so Web Push keeps working there.
 */
import { PrecacheController, PrecacheRoute, type PrecacheEntry } from 'workbox-precaching';
import { NavigationRoute, Route, Router } from 'workbox-routing';
import { CacheFirst, NetworkFirst, NetworkOnly } from 'workbox-strategies';
import type { WorkboxPlugin } from 'workbox-core/types';
import {
  API_CACHE_MAX_BYTES,
  API_NETWORK_TIMEOUT_SECONDS,
  BACKGROUND_SYNC_TAG,
  RUNTIME_CONFIG_CACHE,
  RUNTIME_CONFIG_NETWORK_TIMEOUT_SECONDS,
  STATIC_ASSET_CACHE,
  STATIC_ASSET_MAX_ENTRIES,
  SW_MESSAGE_CLEAR_DATA,
  SW_MESSAGE_SET_NAMESPACE,
  SW_MESSAGE_SKIP_WAITING,
  SW_MESSAGE_SYNC_NOW,
  isAllowlistedApiRequest,
  namespaceCacheName,
  runtimeConfigDisablesCaching,
  userCachePrefix,
} from './pwa/cachePolicy';
import { clientIdOf, createApiCachePlugin, type ApiCacheContext } from './pwa/apiCache';
import { ByteLedger, NamespaceRegistry } from './pwa/namespaceRegistry';
import { buildNotification, parsePushData, resolveTargetUrl } from './pwa/pushHandlers';
import { deleteAllDatabases, deleteCaches } from './pwa/storageWipe';

declare let self: ServiceWorkerGlobalScope & {
  __WB_MANIFEST: Array<PrecacheEntry | string>;
};

/** Where the per-client namespaces and byte totals survive a worker restart. */
const STATE_CACHE = 'kp-sw-state';
const STATE_URL = '/__kp-sw-state/namespaces';
/** Minimum spacing of the kill-switch probe on navigations. */
const KILL_SWITCH_PROBE_INTERVAL_MS = 60_000;
/** A probe never holds anything up longer than this. */
const KILL_SWITCH_PROBE_TIMEOUT_MS = 3_000;

let killed = false;
let lastKillSwitchProbe = 0;
let registry = new NamespaceRegistry();
let ledger = new ByteLedger();
const stateLoaded: Promise<void> = loadState();

// ---------------------------------------------------------------------------
// Per-client namespaces (`kp:{user_key}:{tenant_key}`)
// ---------------------------------------------------------------------------

async function loadState(): Promise<void> {
  try {
    const cache = await caches.open(STATE_CACHE);
    const stored = await cache.match(STATE_URL);
    if (!stored) return;
    const value = (await stored.json()) as { registry?: unknown; ledger?: unknown };
    registry = NamespaceRegistry.fromJSON(value.registry);
    ledger = ByteLedger.fromJSON(value.ledger);
  } catch {
    // Unreadable state: start empty — every tab re-posts its namespace on its next change.
  }
}

async function persistState(): Promise<void> {
  // After the kill switch nothing may re-create the state cache (#2786 review F3).
  if (killed) return;
  try {
    const cache = await caches.open(STATE_CACHE);
    if (killed) return;
    await cache.put(
      STATE_URL,
      new Response(JSON.stringify({ registry: registry.toJSON(), ledger: ledger.toJSON() }), {
        headers: { 'content-type': 'application/json' },
      }),
    );
  } catch {
    // Storage full or gone: the in-memory state still applies until the worker restarts.
  }
}

async function deleteApiCaches(names: readonly string[]): Promise<void> {
  await Promise.all(
    names.map(async (name) => {
      ledger.forget(name);
      apiStrategies.delete(name);
      await caches.delete(name);
    }),
  );
}

async function liveClientIds(): Promise<Set<string>> {
  const windows = await self.clients.matchAll({ type: 'window', includeUncontrolled: true });
  return new Set(windows.map((client) => client.id));
}

async function setClientNamespace(clientId: string, cacheName: string | null): Promise<void> {
  await stateLoaded;
  if (killed) return;
  const unused = registry.set(clientId, cacheName);
  // Closed or reloaded tabs leave stale ids; a cache stays as long as ANY live tab uses it.
  unused.push(...registry.prune(await liveClientIds()));
  await deleteApiCaches([...new Set(unused)].filter((name) => !registry.inUse().has(name)));
  await persistState();
}

async function endSession(userKey: unknown, senderClientId: string): Promise<void> {
  await stateLoaded;
  if (killed) return;
  const ended = registry.endSession(userCachePrefix(typeof userKey === 'string' ? userKey : null), senderClientId);
  await deleteApiCaches(ended);
  await persistState();
}

// ---------------------------------------------------------------------------
// Kill switch
// ---------------------------------------------------------------------------

async function selfDestruct(): Promise<void> {
  killed = true;
  // Forget every namespace and byte total, so nothing in memory can be written back.
  registry = new NamespaceRegistry();
  ledger = new ByteLedger();
  apiStrategies.clear();
  await Promise.all([deleteCaches(), deleteAllDatabases()]);
  await self.registration.unregister();
}

async function probeKillSwitch(): Promise<void> {
  lastKillSwitchProbe = Date.now();
  const abort = new AbortController();
  const timer = setTimeout(() => abort.abort(), KILL_SWITCH_PROBE_TIMEOUT_MS);
  try {
    const response = await fetch('/runtime-config.js', {
      cache: 'no-store',
      credentials: 'same-origin',
      signal: abort.signal,
    });
    if (!response.ok) return;
    if (runtimeConfigDisablesCaching(await response.text())) await selfDestruct();
  } catch {
    // Offline, unreachable or too slow: keep the current state; the next navigation probes again.
  } finally {
    clearTimeout(timer);
  }
}

// ---------------------------------------------------------------------------
// Strategies
// ---------------------------------------------------------------------------

const apiStrategies = new Map<string, NetworkFirst>();

const apiContext: ApiCacheContext = {
  get registry() {
    return registry;
  },
  get ledger() {
    return ledger;
  },
  maxBytes: API_CACHE_MAX_BYTES,
  isKilled: () => killed,
  now: () => Date.now(),
  openCache: (name) => caches.open(name),
  deleteCache: async (name) => {
    await caches.delete(name);
  },
  persist: persistState,
};

function apiStrategy(cacheName: string): NetworkFirst {
  let strategy = apiStrategies.get(cacheName);
  if (!strategy) {
    strategy = new NetworkFirst({
      cacheName,
      networkTimeoutSeconds: API_NETWORK_TIMEOUT_SECONDS,
      plugins: [createApiCachePlugin(cacheName, apiContext) as WorkboxPlugin],
    });
    apiStrategies.set(cacheName, strategy);
  }
  return strategy;
}

const networkOnly = new NetworkOnly();

const staticAssetPlugin: WorkboxPlugin = {
  cacheWillUpdate: async ({ response }) => (response.status === 200 ? response : null),
  cacheDidUpdate: async ({ cacheName }) => {
    const cache = await caches.open(cacheName);
    const requests = await cache.keys();
    // Cache.keys() lists in insertion order: drop the oldest beyond the ceiling.
    const excess = requests.length - STATIC_ASSET_MAX_ENTRIES;
    if (excess > 0) await Promise.all(requests.slice(0, excess).map((r) => cache.delete(r)));
  },
};

// ---------------------------------------------------------------------------
// Routing
// ---------------------------------------------------------------------------

const router = new Router();

// Allowlisted API reads first; every other API GET is network-only (explicit, so no later route can
// ever pick one up). Non-GET requests match no route and go straight to the network.
router.registerRoute(
  new Route(
    ({ url, request }) =>
      url.pathname.startsWith('/api/') && isAllowlistedApiRequest(request.method, url, self.location.origin),
    async (options) => {
      await stateLoaded;
      const cacheName = registry.forClient(clientIdOf(options.event));
      if (killed || !cacheName) return networkOnly.handle(options);
      return apiStrategy(cacheName).handle(options);
    },
  ),
);
router.registerRoute(new Route(({ url }) => url.pathname.startsWith('/api/'), networkOnly));

// The page's runtime config: fresh whenever the network answers, the last copy offline — so a
// light-mode install starts offline in light mode (#2786 review F2). The kill-switch probe does not
// go through here: it is the worker's own `fetch(..., { cache: 'no-store' })`.
router.registerRoute(
  new Route(
    ({ url }) => url.origin === self.location.origin && url.pathname === '/runtime-config.js',
    new NetworkFirst({
      cacheName: RUNTIME_CONFIG_CACHE,
      networkTimeoutSeconds: RUNTIME_CONFIG_NETWORK_TIMEOUT_SECONDS,
    }),
  ),
);

// The injection point must stay a literal `self.__WB_MANIFEST` for the build to fill it.
const precacheManifest = self.__WB_MANIFEST;
if (!import.meta.env.DEV) {
  const precache = new PrecacheController();
  precache.precache(precacheManifest);
  router.registerRoute(new PrecacheRoute(precache));
  router.registerRoute(
    new NavigationRoute(precache.createHandlerBoundToURL('/index.html'), {
      denylist: [/^\/api\//, /^\/sw\.js$/, /^\/runtime-config\.js$/, /^\/manifest\.json$/],
    }),
  );
}

router.registerRoute(
  new Route(
    ({ url, request }) =>
      url.origin === self.location.origin &&
      request.method === 'GET' &&
      (url.pathname.startsWith('/assets/') || url.pathname.startsWith('/icons/')),
    new CacheFirst({ cacheName: STATIC_ASSET_CACHE, plugins: [staticAssetPlugin] }),
  ),
);

self.addEventListener('fetch', (event: FetchEvent) => {
  if (killed) return;
  if (event.request.mode === 'navigate' && Date.now() - lastKillSwitchProbe > KILL_SWITCH_PROBE_INTERVAL_MS) {
    event.waitUntil(probeKillSwitch());
  }
  const response = router.handleRequest({ event, request: event.request });
  if (response) event.respondWith(response);
});

// ---------------------------------------------------------------------------
// Lifecycle and messages
// ---------------------------------------------------------------------------

self.addEventListener('activate', (event: ExtendableEvent) => {
  // Only the claim holds activation (fetches wait for it); the kill-switch probe runs beside it,
  // bounded by its own timeout, and every navigation probes again.
  event.waitUntil(self.clients.claim());
  void probeKillSwitch();
});

self.addEventListener('message', (event: ExtendableMessageEvent) => {
  const source = event.source;
  if (!source || !('type' in source) || source.type !== 'window') return;
  const data = event.data as { type?: unknown; userKey?: unknown; tenantKey?: unknown } | null;
  if (!data || typeof data.type !== 'string') return;

  if (data.type === SW_MESSAGE_SKIP_WAITING) {
    // An update must still be able to replace a killed worker.
    event.waitUntil(self.skipWaiting());
  } else if (killed) {
    // Switched off: namespace messages must not bring the state back.
    return;
  } else if (data.type === SW_MESSAGE_SET_NAMESPACE) {
    const cacheName = namespaceCacheName(
      typeof data.userKey === 'string' ? data.userKey : null,
      typeof data.tenantKey === 'string' ? data.tenantKey : null,
    );
    event.waitUntil(setClientNamespace(source.id, cacheName));
  } else if (data.type === SW_MESSAGE_CLEAR_DATA) {
    event.waitUntil(endSession(data.userKey, source.id));
  }
});

/**
 * Background Sync (REQ-053 WP 9.4, R-022) where the browser has it (not Safari): the browser fires `sync` once
 * the connection is back, and the worker wakes the open windows. A window syncs its own buffer with its own token
 * and scope; with no window open nothing is sent (the next app start syncs). Typed locally: `SyncEvent` is not
 * part of the TypeScript worker library.
 */
self.addEventListener('sync', (event: Event) => {
  const syncEvent = event as ExtendableEvent & { tag?: string };
  if (syncEvent.tag !== BACKGROUND_SYNC_TAG || killed) return;
  syncEvent.waitUntil(
    self.clients
      .matchAll({ type: 'window', includeUncontrolled: true })
      .then((windows) => windows.forEach((client) => client.postMessage({ type: SW_MESSAGE_SYNC_NOW }))),
  );
});

// ---------------------------------------------------------------------------
// Web Push (taken over from the former public/sw.js)
// ---------------------------------------------------------------------------

self.addEventListener('push', (event: PushEvent) => {
  const { title, options } = buildNotification(parsePushData(event.data));
  event.waitUntil(self.registration.showNotification(title, options as NotificationOptions));
});

self.addEventListener('notificationclick', (event: NotificationEvent) => {
  event.notification.close();
  const targetUrl = resolveTargetUrl(event.notification.data, event.action, self.location.origin);

  event.waitUntil(
    self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then((windowClients) => {
      // Focus an already-open client when one exists.
      for (const client of windowClients) {
        if ('focus' in client) {
          void client.focus();
          if ('navigate' in client && targetUrl) {
            client.navigate(targetUrl).catch(() => {
              /* navigation is best-effort */
            });
          }
          return undefined;
        }
      }
      // Otherwise open a new window at the target URL.
      return self.clients.openWindow ? self.clients.openWindow(targetUrl) : undefined;
    }),
  );
});
