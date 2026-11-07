/// <reference lib="webworker" />
/**
 * Kamerplanter service worker (UI-NFR-012 basis, REQ-053 WP 9.1, #2741).
 *
 * Built by `vite-plugin-pwa` in `injectManifest` mode and served as `/sw.js` — the same URL the former
 * hand-written push-only worker had, so an existing registration updates in place instead of a
 * second worker running beside it. Responsibilities:
 *
 * 1. Web Push delivery and notification clicks (taken over from `public/sw.js`).
 * 2. Precache of the app shell (R-007, R-010) and a navigation fallback to `index.html`.
 * 3. Same-origin static assets cache-first (R-008).
 * 4. Allowlisted tenant-scoped API reads network-first, 15 min TTL, 50 MB per namespace (R-009,
 *    R-012, R-013) — in a cache named `kp:{user_key}:{tenant_key}`. The keys come from the app via
 *    `postMessage`; the worker never reads a token. Without a namespace it caches no API answer.
 * 5. Kill switch (G-W9 e): `PWA_CACHING_ENABLED=false` in `/runtime-config.js` makes the worker
 *    delete every cache and unregister itself.
 *
 * Updates wait for the user (R-014): a new worker stays `waiting` until the app posts `SKIP_WAITING`
 * from the update banner. Type-checked by `tsconfig.sw.json` (WebWorker lib), not the app program.
 */
import { PrecacheController, PrecacheRoute, type PrecacheEntry } from 'workbox-precaching';
import { NavigationRoute, Route, Router } from 'workbox-routing';
import { CacheFirst, NetworkFirst, NetworkOnly } from 'workbox-strategies';
import type { WorkboxPlugin } from 'workbox-core/types';
import {
  API_CACHE_MAX_BYTES,
  API_CACHE_PREFIX,
  API_NETWORK_TIMEOUT_SECONDS,
  CACHED_AT_HEADER,
  CACHED_SIZE_HEADER,
  RUNTIME_CONFIG_CACHE,
  STATIC_ASSET_CACHE,
  STATIC_ASSET_MAX_ENTRIES,
  SW_MESSAGE_CLEAR_DATA,
  SW_MESSAGE_SET_NAMESPACE,
  SW_MESSAGE_SKIP_WAITING,
  isAllowlistedApiRequest,
  isCacheableApiResponse,
  isFresh,
  namespaceCacheName,
  runtimeConfigDisablesCaching,
  selectEvictions,
  type CacheEntryInfo,
} from './pwa/cachePolicy';
import { buildNotification, parsePushData, resolveTargetUrl } from './pwa/pushHandlers';

declare let self: ServiceWorkerGlobalScope & {
  __WB_MANIFEST: Array<PrecacheEntry | string>;
};

/** Where the current namespace survives a worker restart (deleted with every data clear). */
const STATE_CACHE = 'kp-sw-state';
const NAMESPACE_STATE_URL = '/__kp-sw-state/namespace';
/** Minimum spacing of the kill-switch probe on navigations. */
const KILL_SWITCH_PROBE_INTERVAL_MS = 60_000;

let killed = false;
let lastKillSwitchProbe = 0;
let namespace: Promise<string | null> = loadNamespace();

// ---------------------------------------------------------------------------
// Namespace (`kp:{user_key}:{tenant_key}`)
// ---------------------------------------------------------------------------

async function loadNamespace(): Promise<string | null> {
  try {
    const cache = await caches.open(STATE_CACHE);
    const stored = await cache.match(NAMESPACE_STATE_URL);
    if (!stored) return null;
    const value = (await stored.json()) as { cacheName?: unknown };
    return typeof value.cacheName === 'string' && value.cacheName.startsWith(API_CACHE_PREFIX)
      ? value.cacheName
      : null;
  } catch {
    return null;
  }
}

async function deleteApiCaches(keep: string | null): Promise<void> {
  const names = await caches.keys();
  await Promise.all(
    names
      .filter((name) => (name.startsWith(API_CACHE_PREFIX) && name !== keep) || name === STATE_CACHE)
      .map((name) => caches.delete(name)),
  );
}

async function setNamespace(cacheName: string | null): Promise<void> {
  namespace = Promise.resolve(cacheName);
  // A different user or tenant never reads the previous one's answers, even if the app's own clear
  // did not run (e.g. a tab closed mid-switch).
  await deleteApiCaches(cacheName);
  if (!cacheName) return;
  const cache = await caches.open(STATE_CACHE);
  await cache.put(
    NAMESPACE_STATE_URL,
    new Response(JSON.stringify({ cacheName }), { headers: { 'content-type': 'application/json' } }),
  );
}

// ---------------------------------------------------------------------------
// Kill switch
// ---------------------------------------------------------------------------

async function selfDestruct(): Promise<void> {
  killed = true;
  const names = await caches.keys();
  await Promise.all(names.map((name) => caches.delete(name)));
  await self.registration.unregister();
}

async function probeKillSwitch(): Promise<void> {
  lastKillSwitchProbe = Date.now();
  try {
    const response = await fetch('/runtime-config.js', { cache: 'no-store', credentials: 'same-origin' });
    if (!response.ok) return;
    if (runtimeConfigDisablesCaching(await response.text())) await selfDestruct();
  } catch {
    // Offline or unreachable: keep the current state; the next navigation probes again.
  }
}

// ---------------------------------------------------------------------------
// API cache plugins: TTL stamp, no-store respect, byte ceiling
// ---------------------------------------------------------------------------

async function enforceByteCeiling(cacheName: string): Promise<void> {
  const cache = await caches.open(cacheName);
  const requests = await cache.keys();
  const entries: CacheEntryInfo[] = [];
  for (const request of requests) {
    const response = await cache.match(request);
    if (!response) continue;
    entries.push({
      url: request.url,
      size: Number(response.headers.get(CACHED_SIZE_HEADER)) || 0,
      cachedAt: Number(response.headers.get(CACHED_AT_HEADER)) || 0,
    });
  }
  await Promise.all(selectEvictions(entries, API_CACHE_MAX_BYTES).map((url) => cache.delete(url)));
}

function apiCachePlugin(cacheName: string): WorkboxPlugin {
  return {
    cacheWillUpdate: async ({ response }) => {
      if (killed || !isCacheableApiResponse(response)) return null;
      // The namespace may have changed (logout, tenant switch) while the request was in flight.
      if ((await namespace) !== cacheName) return null;
      const body = await response.blob();
      const headers = new Headers(response.headers);
      headers.set(CACHED_AT_HEADER, String(Date.now()));
      headers.set(CACHED_SIZE_HEADER, String(body.size));
      return new Response(body, { status: response.status, statusText: response.statusText, headers });
    },
    cachedResponseWillBeUsed: async ({ cachedResponse }) => {
      if (!cachedResponse || killed) return null;
      if ((await namespace) !== cacheName) return null;
      return isFresh(cachedResponse.headers.get(CACHED_AT_HEADER), Date.now()) ? cachedResponse : null;
    },
    cacheDidUpdate: async () => {
      await enforceByteCeiling(cacheName);
    },
  };
}

const apiStrategies = new Map<string, NetworkFirst>();

function apiStrategy(cacheName: string): NetworkFirst {
  let strategy = apiStrategies.get(cacheName);
  if (!strategy) {
    strategy = new NetworkFirst({
      cacheName,
      networkTimeoutSeconds: API_NETWORK_TIMEOUT_SECONDS,
      plugins: [apiCachePlugin(cacheName)],
    });
    apiStrategies.set(cacheName, strategy);
  }
  return strategy;
}

const networkOnly = new NetworkOnly();

// ---------------------------------------------------------------------------
// Static assets: bounded cache-first
// ---------------------------------------------------------------------------

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

const precache = new PrecacheController();
precache.precache(self.__WB_MANIFEST);

const router = new Router();

// Allowlisted API reads first; every other API GET is network-only (explicit, so no later route can
// ever pick one up). Non-GET requests match no route and go straight to the network.
router.registerRoute(
  new Route(
    ({ url, request }) =>
      url.pathname.startsWith('/api/') && isAllowlistedApiRequest(request.method, url, self.location.origin),
    async (options) => {
      const cacheName = await namespace;
      if (killed || !cacheName) return networkOnly.handle(options);
      return apiStrategy(cacheName).handle(options);
    },
  ),
);
router.registerRoute(new Route(({ url }) => url.pathname.startsWith('/api/'), networkOnly));

// The kill switch must always be read fresh; the last copy only serves an offline start.
router.registerRoute(
  new Route(
    ({ url }) => url.origin === self.location.origin && url.pathname === '/runtime-config.js',
    new NetworkFirst({ cacheName: RUNTIME_CONFIG_CACHE, networkTimeoutSeconds: 3 }),
  ),
);

router.registerRoute(new PrecacheRoute(precache));

router.registerRoute(
  new NavigationRoute(precache.createHandlerBoundToURL('/index.html'), {
    denylist: [/^\/api\//, /^\/sw\.js$/, /^\/runtime-config\.js$/, /^\/manifest\.json$/],
  }),
);

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
  event.waitUntil(
    (async () => {
      await self.clients.claim();
      await probeKillSwitch();
    })(),
  );
});

self.addEventListener('message', (event: ExtendableMessageEvent) => {
  const source = event.source;
  if (!source || !('type' in source) || source.type !== 'window') return;
  const data = event.data as { type?: unknown; userKey?: unknown; tenantKey?: unknown } | null;
  if (!data || typeof data.type !== 'string') return;

  if (data.type === SW_MESSAGE_SKIP_WAITING) {
    event.waitUntil(self.skipWaiting());
  } else if (data.type === SW_MESSAGE_SET_NAMESPACE) {
    const cacheName = killed
      ? null
      : namespaceCacheName(
          typeof data.userKey === 'string' ? data.userKey : null,
          typeof data.tenantKey === 'string' ? data.tenantKey : null,
        );
    event.waitUntil(setNamespace(cacheName));
  } else if (data.type === SW_MESSAGE_CLEAR_DATA) {
    event.waitUntil(setNamespace(null));
  }
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
