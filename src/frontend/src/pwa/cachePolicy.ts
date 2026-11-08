/**
 * UI-NFR-012 basis (REQ-053 WP 9.1, #2741) — the caching rules of the service worker as pure
 * functions, shared by `src/sw.ts` (which applies them) and the app (which clears what they wrote).
 *
 * Kept free of worker- and window-only APIs so the rules are unit-testable in jsdom and type-check in
 * both TypeScript programs (`tsconfig.json` for the app, `tsconfig.sw.json` for the worker).
 *
 * Guardrail G-W9 (c): the worker caches only `GET` answers of an explicit allowlist of tenant-scoped
 * read paths, never `/api/v1/auth/*`, `/privacy/*`, `/admin/*` or attachment originals, and an answer
 * that says `Cache-Control: no-store` is never written. Everything else is network-only.
 */

/** R-012 — an API answer older than this is never served from the cache. */
export const API_CACHE_TTL_SECONDS = 15 * 60;

/** R-013 — byte ceiling of one namespace's API cache; the oldest entries go first. */
export const API_CACHE_MAX_BYTES = 50 * 1024 * 1024;

/** How long a network-first API read waits before it falls back to the cache. */
export const API_NETWORK_TIMEOUT_SECONDS = 5;

/** Prefix of every namespaced (user- and tenant-bound) API cache: `kp:{user_key}:{tenant_key}`. */
export const API_CACHE_PREFIX = 'kp:';

/**
 * Caches that hold only build output or deployment config — no personal data. They survive a logout
 * or tenant switch so the app shell stays loadable; the kill switch deletes them too.
 */
export const STATIC_ASSET_CACHE = 'kp-static-assets';
/**
 * The page's last `runtime-config.js` (network-first, #2786 review F2): offline, a light-mode
 * install must still start in light mode instead of falling back to `full`. The worker's own
 * kill-switch probe never reads it — it fetches with `cache: 'no-store'`, and a worker's own
 * `fetch()` does not pass through its fetch handler.
 */
export const RUNTIME_CONFIG_CACHE = 'kp-runtime-config';
/** How long the page's `runtime-config.js` waits for the network before the last copy answers. */
export const RUNTIME_CONFIG_NETWORK_TIMEOUT_SECONDS = 3;
/** Workbox names its precache `workbox-precache-v2-<scope>`. */
export const PRECACHE_CACHE_PREFIX = 'workbox-precache';

/**
 * Ceiling for the runtime static-asset cache: the lazy route chunks and illustrations outside the
 * app-shell precache. Above the ~380 files of one build, so one build's routes fit; older builds'
 * hashed files are evicted oldest-first.
 */
export const STATIC_ASSET_MAX_ENTRIES = 450;

/** Header the worker stamps on a stored API answer: epoch milliseconds of the write. */
export const CACHED_AT_HEADER = 'x-kp-cached-at';
/** Header the worker stamps on a stored API answer: body size in bytes. */
export const CACHED_SIZE_HEADER = 'x-kp-cached-size';

/** Messages the app posts to the worker (`navigator.serviceWorker.controller.postMessage`). */
export const SW_MESSAGE_SET_NAMESPACE = 'KP_SET_NAMESPACE';
export const SW_MESSAGE_CLEAR_DATA = 'KP_CLEAR_DATA';
export const SW_MESSAGE_SKIP_WAITING = 'SKIP_WAITING';

/**
 * REQ-053 WP 9.4 (UI-NFR-012 R-022): the Background Sync tag the app registers after buffering a write offline,
 * and the message the worker posts to the open windows when the browser fires it. The worker never sends a
 * buffered write itself — it holds no token — it only wakes a signed-in tab, which syncs in its own scope.
 */
export const BACKGROUND_SYNC_TAG = 'kp-write-queue';
export const SW_MESSAGE_SYNC_NOW = 'KP_SYNC_NOW';

/**
 * Paths that are never cached, whatever the allowlist says (checked first). The allowlist below
 * cannot reach them today; this list makes a future, too-broad allowlist entry fail closed.
 */
export const FORBIDDEN_API_PATH_PATTERNS: readonly RegExp[] = [
  /^\/api\/v1\/auth(\/|$)/,
  /\/privacy(\/|$)/,
  /\/admin(\/|$)/,
  /\/attachments(\/|$)/,
  /\/photos?(\/|$)/,
  /\/token(\/|$)/,
];

/** One path segment: no slash, not empty, not a dot segment. */
const SEGMENT = '(?!\\.{1,2}(?:/|$))[^/]+';

/**
 * Placeholder decision (12) of wave 9: `GET …/plan`, `GET …/sites`, `GET …/locations/{key}/summary`.
 * All three are tenant-scoped (`/api/v1/t/{slug}/…`); a global path is never on the list.
 */
export const API_CACHE_ALLOWLIST: readonly RegExp[] = [
  new RegExp(`^/api/v1/t/${SEGMENT}/sites/?$`),
  new RegExp(`^/api/v1/t/${SEGMENT}/sites/${SEGMENT}/plan/?$`),
  new RegExp(`^/api/v1/t/${SEGMENT}/locations/${SEGMENT}/summary/?$`),
];

/** Key shape accepted into a cache name; anything else disables API caching for the session. */
const NAMESPACE_KEY = /^[A-Za-z0-9_-]{1,128}$/;

/**
 * The cache name of one user in one tenant, or `null` when either key is missing or malformed —
 * `null` means "network only", never a shared fallback cache.
 */
export function namespaceCacheName(
  userKey: string | null | undefined,
  tenantKey: string | null | undefined,
): string | null {
  if (typeof userKey !== 'string' || typeof tenantKey !== 'string') return null;
  if (!NAMESPACE_KEY.test(userKey) || !NAMESPACE_KEY.test(tenantKey)) return null;
  return `${API_CACHE_PREFIX}${userKey}:${tenantKey}`;
}

/** The prefix of every namespace of one user: `kp:{user_key}:`, or `null` for a malformed key. */
export function userCachePrefix(userKey: string | null | undefined): string | null {
  if (typeof userKey !== 'string' || !NAMESPACE_KEY.test(userKey)) return null;
  return `${API_CACHE_PREFIX}${userKey}:`;
}

/** Whether a request may be answered from (and written into) the namespaced API cache. */
export function isAllowlistedApiRequest(method: string, url: URL, appOrigin: string): boolean {
  if (method.toUpperCase() !== 'GET') return false;
  if (url.origin !== appOrigin) return false;
  const path = url.pathname;
  if (FORBIDDEN_API_PATH_PATTERNS.some((pattern) => pattern.test(path))) return false;
  return API_CACHE_ALLOWLIST.some((pattern) => pattern.test(path));
}

/** The parts of a `Response` the cacheability rule reads. */
export interface ResponseLike {
  status: number;
  type?: string;
  headers: { get(name: string): string | null };
}

/** Whether a `Cache-Control` value forbids storing the answer anywhere. */
export function forbidsStorage(cacheControl: string | null): boolean {
  if (!cacheControl) return false;
  return cacheControl
    .split(',')
    .map((directive) => directive.trim().toLowerCase())
    .some((directive) => directive === 'no-store');
}

/** Whether an allowlisted answer may be written: a plain 200 JSON body without `no-store`. */
export function isCacheableApiResponse(response: ResponseLike): boolean {
  if (response.status !== 200) return false;
  if (response.type === 'opaque' || response.type === 'opaqueredirect' || response.type === 'error') {
    return false;
  }
  if (forbidsStorage(response.headers.get('cache-control'))) return false;
  if (response.headers.get('set-cookie')) return false;
  const contentType = response.headers.get('content-type') ?? '';
  return contentType.toLowerCase().includes('application/json');
}

/** R-012 — whether a stored answer is still inside its TTL. A missing or broken stamp is stale. */
export function isFresh(cachedAt: string | null, nowMs: number): boolean {
  if (!cachedAt) return false;
  const stamp = Number(cachedAt);
  if (!Number.isFinite(stamp)) return false;
  const age = nowMs - stamp;
  return age >= 0 && age <= API_CACHE_TTL_SECONDS * 1000;
}

/** One stored API answer as the eviction rule sees it. */
export interface CacheEntryInfo {
  url: string;
  size: number;
  cachedAt: number;
}

/**
 * R-013 — the entries to delete so the rest fits `maxBytes`, oldest write first. A network-first
 * read rewrites its entry on every successful fetch, so the write time is the last use online.
 */
export function selectEvictions(
  entries: readonly CacheEntryInfo[],
  maxBytes: number = API_CACHE_MAX_BYTES,
): string[] {
  let total = entries.reduce((sum, entry) => sum + Math.max(0, entry.size), 0);
  if (total <= maxBytes) return [];
  const evict: string[] = [];
  for (const entry of [...entries].sort((a, b) => a.cachedAt - b.cachedAt)) {
    if (total <= maxBytes) break;
    evict.push(entry.url);
    total -= Math.max(0, entry.size);
  }
  return evict;
}

/** Whether a cache is one of the public build/config caches a logout leaves in place. */
export function isPublicCacheName(name: string): boolean {
  return name.startsWith(PRECACHE_CACHE_PREFIX) || name === STATIC_ASSET_CACHE || name === RUNTIME_CONFIG_CACHE;
}

/**
 * G-W9 (e) — the kill switch. Caching stays on unless `PWA_CACHING_ENABLED` says off; the value
 * arrives as a string from a shell heredoc, so `"false"`, `"0"`, `"off"` and `"no"` all switch it off.
 */
export function isPwaCachingEnabled(value: unknown): boolean {
  if (value === false || value === 0) return false;
  if (typeof value !== 'string') return true;
  return !['false', '0', 'off', 'no'].includes(value.trim().toLowerCase());
}

/**
 * The kill switch read by the worker itself from the text of `/runtime-config.js` (the worker cannot
 * execute it). Only an explicit off value switches off; an unreadable file keeps the current state.
 */
export function runtimeConfigDisablesCaching(source: string): boolean {
  const match = /PWA_CACHING_ENABLED\s*["']?\s*:\s*(?:"([^"]*)"|'([^']*)'|([A-Za-z0-9]+))/.exec(source);
  if (!match) return false;
  const raw = match[1] ?? match[2] ?? match[3] ?? '';
  return !isPwaCachingEnabled(raw);
}
