import { describe, expect, it } from 'vitest';
import { clientIdOf, createApiCachePlugin, type ApiCacheContext, type CacheLike } from '@/pwa/apiCache';
import { CACHED_AT_HEADER, CACHED_SIZE_HEADER, namespaceCacheName } from '@/pwa/cachePolicy';
import { ByteLedger, NamespaceRegistry } from '@/pwa/namespaceRegistry';

/**
 * REQ-053 WP 9.1 (#2741), #2786 review findings 1, 2, 9 — the worker's API cache is per CLIENT.
 *
 * Two tabs of the same origin can belong to different users or tenants. Each tab's requests are
 * answered from, and written into, only its own `kp:{user_key}:{tenant_key}`; binding one tab never
 * deletes a cache another live tab uses; a logout ends that user's namespace in every tab; and a
 * write that lands after its namespace ended is undone. Driven through the plugin and registry the
 * worker uses (`src/sw.ts` wires exactly these — pinned in swCacheAllowlist.test.ts).
 */

const A_X = namespaceCacheName('user_a', 'tenant_x') as string;
const A_Y = namespaceCacheName('user_a', 'tenant_y') as string;
const B_X = namespaceCacheName('user_b', 'tenant_x') as string;
const URL_PLAN = 'https://kamerplanter.example/api/v1/t/garden/sites/site_1/plan';

class FakeCache implements CacheLike {
  readonly entries = new Map<string, Response>();
  async keys() {
    return [...this.entries.keys()].map((url) => new Request(url));
  }
  async match(request: Request | string) {
    return this.entries.get(typeof request === 'string' ? request : request.url)?.clone();
  }
  async delete(request: Request | string) {
    return this.entries.delete(typeof request === 'string' ? request : request.url);
  }
}

function setup() {
  const caches = new Map<string, FakeCache>();
  const ctx: ApiCacheContext = {
    registry: new NamespaceRegistry(),
    ledger: new ByteLedger(),
    maxBytes: 1000,
    isKilled: () => false,
    now: () => 1_000_000,
    openCache: async (name) => {
      if (!caches.has(name)) caches.set(name, new FakeCache());
      return caches.get(name) as FakeCache;
    },
    deleteCache: async (name) => {
      caches.delete(name);
    },
    persist: async () => undefined,
  };
  return { ctx, caches };
}

function json(body: string) {
  return new Response(body, { status: 200, headers: { 'content-type': 'application/json' } });
}

/** One network-first write as Workbox runs it: cacheWillUpdate → put → cacheDidUpdate. */
async function write(
  ctx: ApiCacheContext,
  cacheName: string,
  clientId: string,
  body: string,
  between?: () => void,
) {
  const plugin = createApiCachePlugin(cacheName, ctx);
  const event = { clientId };
  const state: Record<string, unknown> = {};
  const stored = await plugin.cacheWillUpdate({ response: json(body), event, state });
  if (!stored) return false;
  between?.();
  const cache = (await ctx.openCache(cacheName)) as FakeCache;
  const oldResponse = cache.entries.get(URL_PLAN);
  cache.entries.set(URL_PLAN, stored);
  await plugin.cacheDidUpdate({ request: new Request(URL_PLAN), oldResponse, newResponse: stored, event, state });
  return true;
}

async function read(ctx: ApiCacheContext, cacheName: string, clientId: string) {
  const cache = (await ctx.openCache(cacheName)) as FakeCache;
  const cached = await cache.match(URL_PLAN);
  const used = await createApiCachePlugin(cacheName, ctx).cachedResponseWillBeUsed({
    cachedResponse: cached,
    event: { clientId },
  });
  return used ? used.text() : null;
}

describe('per-client namespace (review finding 1)', () => {
  it('keeps two tabs of different users apart: no cross write, no cross read', async () => {
    const { ctx } = setup();
    ctx.registry.set('tab-1', A_X);
    ctx.registry.set('tab-2', B_X);

    expect(await write(ctx, A_X, 'tab-1', '"plan of A"')).toBe(true);
    // tab-2 (user B) cannot write into A's namespace, nor read from it.
    expect(await write(ctx, A_X, 'tab-2', '"plan of B"')).toBe(false);
    expect(await read(ctx, A_X, 'tab-2')).toBeNull();
    expect(await read(ctx, A_X, 'tab-1')).toBe('"plan of A"');
  });

  it('keeps two tenants of one user apart', async () => {
    const { ctx } = setup();
    ctx.registry.set('tab-1', A_X);
    ctx.registry.set('tab-2', A_Y);
    await write(ctx, A_X, 'tab-1', '"X"');
    expect(await read(ctx, A_X, 'tab-2')).toBeNull();
    expect(await write(ctx, A_X, 'tab-2', '"Y"')).toBe(false);
  });

  it('a client without a namespace caches and reads nothing', async () => {
    const { ctx } = setup();
    expect(await write(ctx, A_X, 'stranger', '"x"')).toBe(false);
    expect(await read(ctx, A_X, 'stranger')).toBeNull();
  });

  it('resolves the client of a fetch, including the client a navigation creates', () => {
    expect(clientIdOf({ clientId: 'tab-1', resultingClientId: '' })).toBe('tab-1');
    expect(clientIdOf({ clientId: '', resultingClientId: 'tab-new' })).toBe('tab-new');
    expect(clientIdOf({})).toBeNull();
    expect(clientIdOf(undefined)).toBeNull();
  });
});

describe('binding and pruning keep a live client cache (SET_NAMESPACE)', () => {
  it("switching one tab never deletes a cache another live tab still uses", () => {
    const registry = new NamespaceRegistry();
    registry.set('tab-1', A_X);
    registry.set('tab-2', A_X);
    expect(registry.set('tab-1', A_Y)).toEqual([]);
    expect(registry.inUse().has(A_X)).toBe(true);
    // The last user of A_X leaves: now it goes.
    expect(registry.set('tab-2', B_X)).toEqual([A_X]);
  });

  it('prune drops closed tabs and returns only caches no live tab uses', () => {
    const registry = new NamespaceRegistry();
    registry.set('tab-1', A_X);
    registry.set('tab-2', B_X);
    registry.set('tab-closed', A_Y);
    expect(registry.prune(new Set(['tab-1', 'tab-2']))).toEqual([A_Y]);
    expect(registry.forClient('tab-1')).toBe(A_X);
    expect(registry.forClient('tab-2')).toBe(B_X);
  });

  it('survives a worker restart through its JSON snapshot', () => {
    const registry = new NamespaceRegistry();
    registry.set('tab-1', A_X);
    const restored = NamespaceRegistry.fromJSON(JSON.parse(JSON.stringify(registry.toJSON())));
    expect(restored.forClient('tab-1')).toBe(A_X);
    expect(NamespaceRegistry.fromJSON({ clients: { evil: 'not-a-kp-cache' } }).forClient('evil')).toBeNull();
  });
});

describe('logout ends the user in every tab (CLEAR_DATA)', () => {
  it("unbinds every client of that user, leaves other users' tabs alone", () => {
    const registry = new NamespaceRegistry();
    registry.set('tab-1', A_X);
    registry.set('tab-2', A_Y);
    registry.set('tab-3', B_X);
    const ended = registry.endSession('kp:user_a:', 'tab-1');
    expect(ended.sort()).toEqual([A_X, A_Y].sort());
    expect(registry.forClient('tab-1')).toBeNull();
    expect(registry.forClient('tab-2')).toBeNull();
    expect(registry.forClient('tab-3')).toBe(B_X);
  });

  it("falls back to the sender's own namespace when the message names no user", () => {
    const registry = new NamespaceRegistry();
    registry.set('tab-1', A_X);
    registry.set('tab-2', A_Y);
    expect(registry.endSession(null, 'tab-1').sort()).toEqual([A_X, A_Y].sort());
  });
});

describe('logout race (review finding 2)', () => {
  it('undoes a write whose namespace ended between cacheWillUpdate and the put', async () => {
    const { ctx, caches } = setup();
    ctx.registry.set('tab-1', A_X);
    const landed = await write(ctx, A_X, 'tab-1', '"late answer"', () => {
      ctx.registry.endSession('kp:user_a:', 'tab-1');
    });
    expect(landed).toBe(true);
    // The put happened, cacheDidUpdate undid it and dropped the re-created cache.
    expect(caches.has(A_X)).toBe(false);
  });

  it('also undoes it when the namespace ended and was re-bound in between (generation moved)', async () => {
    const { ctx, caches } = setup();
    ctx.registry.set('tab-1', A_X);
    await write(ctx, A_X, 'tab-1', '"late answer"', () => {
      ctx.registry.endSession('kp:user_a:', 'tab-1');
      ctx.registry.set('tab-1', A_X);
    });
    expect(caches.get(A_X)?.entries.size ?? 0).toBe(0);
  });

  it('keeps a write that nothing interrupted', async () => {
    const { ctx, caches } = setup();
    ctx.registry.set('tab-1', A_X);
    await write(ctx, A_X, 'tab-1', '"answer"');
    expect(caches.get(A_X)?.entries.size).toBe(1);
  });
});

describe('byte ceiling without a scan per write (review finding 9)', () => {
  it('scans only when the running total may exceed the ceiling', async () => {
    const { ctx, caches } = setup();
    ctx.registry.set('tab-1', A_X);
    let matches = 0;
    const original = ctx.openCache;
    ctx.openCache = async (name) => {
      const cache = (await original(name)) as FakeCache;
      const match = cache.match.bind(cache);
      cache.match = async (request) => {
        matches += 1;
        return match(request);
      };
      return cache;
    };
    await write(ctx, A_X, 'tab-1', '"' + 'a'.repeat(100) + '"');
    expect(matches).toBe(0);
    expect(ctx.ledger.total(A_X)).toBe(102);
    // Replacing the entry subtracts the old size: still no scan.
    await write(ctx, A_X, 'tab-1', '"' + 'b'.repeat(200) + '"');
    expect(ctx.ledger.total(A_X)).toBe(202);
    expect(matches).toBe(0);
    // Past the ceiling: one scan, the total is re-measured.
    await write(ctx, A_X, 'tab-1', '"' + 'c'.repeat(2000) + '"');
    expect(matches).toBeGreaterThan(0);
    expect(caches.get(A_X)?.entries.size).toBe(0);
    expect(ctx.ledger.total(A_X)).toBe(0);
  });

  it('stamps the write time and size the TTL and the ceiling read', async () => {
    const { ctx, caches } = setup();
    ctx.registry.set('tab-1', A_X);
    await write(ctx, A_X, 'tab-1', '"abc"');
    const stored = caches.get(A_X)?.entries.get(URL_PLAN);
    expect(stored?.headers.get(CACHED_AT_HEADER)).toBe('1000000');
    expect(stored?.headers.get(CACHED_SIZE_HEADER)).toBe('5');
  });
});
