/**
 * The service worker's API cache rules as a Workbox plugin (REQ-053 WP 9.1, #2741).
 *
 * Every read and write goes through the namespace of the client that sent the request (review
 * finding 1): a tab of user A in tenant X never reads or writes `kp:B:…` or `kp:A:Y`. A write that
 * started before its namespace was invalidated (logout, tenant switch) is undone when it lands
 * (finding 2), and the 50 MB ceiling is kept from a running byte total instead of a scan per write
 * (finding 9).
 *
 * Kept free of worker globals — the worker injects Cache Storage, the clock and persistence — so
 * the rules are exercised in jsdom through the same functions the worker calls.
 */
import {
  CACHED_AT_HEADER,
  CACHED_SIZE_HEADER,
  isCacheableApiResponse,
  isFresh,
  selectEvictions,
  type CacheEntryInfo,
} from './cachePolicy';
import type { ByteLedger, NamespaceRegistry } from './namespaceRegistry';

/** The part of Cache Storage the plugin uses. */
export interface CacheLike {
  keys(): Promise<readonly Request[]>;
  match(request: Request | string): Promise<Response | undefined>;
  delete(request: Request | string): Promise<boolean>;
}

export interface ApiCacheContext {
  registry: NamespaceRegistry;
  ledger: ByteLedger;
  maxBytes: number;
  isKilled(): boolean;
  now(): number;
  openCache(cacheName: string): Promise<CacheLike>;
  deleteCache(cacheName: string): Promise<void>;
  /** Write registry and ledger to durable storage. */
  persist(): Promise<void>;
}

/** The plugin callback arguments the rules read (a subset of Workbox's). */
interface PluginArgs {
  request?: Request;
  response?: Response;
  cachedResponse?: Response;
  oldResponse?: Response;
  newResponse?: Response;
  event?: unknown;
  state?: Record<string, unknown>;
}

/** The id of the client a fetch belongs to; navigations name the client they will create. */
export function clientIdOf(event: unknown): string | null {
  if (!event || typeof event !== 'object') return null;
  const { clientId, resultingClientId } = event as { clientId?: unknown; resultingClientId?: unknown };
  if (typeof clientId === 'string' && clientId) return clientId;
  if (typeof resultingClientId === 'string' && resultingClientId) return resultingClientId;
  return null;
}

function sizeOf(response: Response | undefined): number {
  return response ? Number(response.headers.get(CACHED_SIZE_HEADER)) || 0 : 0;
}

/** R-013 — full scan: evict the oldest entries until the cache fits, and return the new total. */
export async function enforceByteCeiling(cache: CacheLike, maxBytes: number): Promise<number> {
  const entries: CacheEntryInfo[] = [];
  for (const request of await cache.keys()) {
    const response = await cache.match(request);
    if (!response) continue;
    entries.push({
      url: request.url,
      size: sizeOf(response),
      cachedAt: Number(response.headers.get(CACHED_AT_HEADER)) || 0,
    });
  }
  const evicted = new Set(selectEvictions(entries, maxBytes));
  await Promise.all([...evicted].map((url) => cache.delete(url)));
  return entries.filter((entry) => !evicted.has(entry.url)).reduce((sum, entry) => sum + entry.size, 0);
}

const GENERATION = 'kpGeneration';

/** The plugin for one namespace's NetworkFirst strategy. */
export function createApiCachePlugin(cacheName: string, ctx: ApiCacheContext) {
  const ownedByRequester = (event: unknown) => ctx.registry.forClient(clientIdOf(event)) === cacheName;

  return {
    cacheWillUpdate: async ({ response, event, state }: PluginArgs): Promise<Response | null> => {
      if (!response || ctx.isKilled() || !isCacheableApiResponse(response)) return null;
      if (!ownedByRequester(event)) return null;
      if (state) state[GENERATION] = ctx.registry.generationOf(cacheName);
      const body = await response.arrayBuffer();
      const headers = new Headers(response.headers);
      headers.set(CACHED_AT_HEADER, String(ctx.now()));
      headers.set(CACHED_SIZE_HEADER, String(body.byteLength));
      return new Response(body, { status: response.status, statusText: response.statusText, headers });
    },

    cachedResponseWillBeUsed: async ({ cachedResponse, event }: PluginArgs): Promise<Response | null> => {
      if (!cachedResponse || ctx.isKilled() || !ownedByRequester(event)) return null;
      return isFresh(cachedResponse.headers.get(CACHED_AT_HEADER), ctx.now()) ? cachedResponse : null;
    },

    cacheDidUpdate: async ({ request, oldResponse, newResponse, event, state }: PluginArgs): Promise<void> => {
      const cache = await ctx.openCache(cacheName);
      const invalidated =
        ctx.isKilled() ||
        !ownedByRequester(event) ||
        (state !== undefined && state[GENERATION] !== ctx.registry.generationOf(cacheName));
      if (invalidated) {
        // The namespace ended while the answer was in flight: undo the write, and drop the cache
        // the write re-created if no live client uses it.
        if (request) await cache.delete(request);
        if (!ctx.registry.inUse().has(cacheName)) {
          await ctx.deleteCache(cacheName);
          ctx.ledger.forget(cacheName);
        }
        await ctx.persist();
        return;
      }
      if (ctx.ledger.record(cacheName, sizeOf(newResponse), sizeOf(oldResponse), ctx.maxBytes)) {
        ctx.ledger.set(cacheName, await enforceByteCeiling(cache, ctx.maxBytes));
      }
      await ctx.persist();
    },
  };
}
