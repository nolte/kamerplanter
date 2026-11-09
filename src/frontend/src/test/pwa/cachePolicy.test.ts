import { describe, expect, it } from 'vitest';
import {
  API_CACHE_MAX_BYTES,
  API_CACHE_TTL_SECONDS,
  isFresh,
  isPublicCacheName,
  isPwaCachingEnabled,
  namespaceCacheName,
  runtimeConfigDisablesCaching,
  selectEvictions,
} from '@/pwa/cachePolicy';

/**
 * UI-NFR-012 R-055 (namespace per user and tenant), R-012 (15-minute TTL), R-013 (50 MB ceiling, oldest evicted
 * first) and R-059 (parsing of the kill switch), plus what a logout leaves: the cache policy of the service worker
 * (REQ-053 WP 9.1, #2741).
 */
describe('namespaceCacheName — kp:{user_key}:{tenant_key}', () => {
  it('binds the cache to the user AND the tenant', () => {
    expect(namespaceCacheName('user_1', 'tenant_a')).toBe('kp:user_1:tenant_a');
    expect(namespaceCacheName('user_1', 'tenant_b')).not.toBe(namespaceCacheName('user_1', 'tenant_a'));
    expect(namespaceCacheName('user_2', 'tenant_a')).not.toBe(namespaceCacheName('user_1', 'tenant_a'));
  });

  it.each([
    [null, 'tenant_a'],
    ['user_1', null],
    ['', 'tenant_a'],
    ['user:1', 'tenant_a'],
    ['user_1', 'tenant/a'],
    ['x'.repeat(129), 'tenant_a'],
  ])('caches nothing for (%s, %s)', (userKey, tenantKey) => {
    expect(namespaceCacheName(userKey, tenantKey)).toBeNull();
  });
});

describe('isFresh — R-012 15 minute TTL', () => {
  const now = 1_800_000_000_000;
  it('serves an answer inside the TTL and refuses one past it', () => {
    expect(API_CACHE_TTL_SECONDS).toBe(900);
    expect(isFresh(String(now - 60_000), now)).toBe(true);
    expect(isFresh(String(now - API_CACHE_TTL_SECONDS * 1000), now)).toBe(true);
    expect(isFresh(String(now - API_CACHE_TTL_SECONDS * 1000 - 1), now)).toBe(false);
  });

  it('treats a missing, broken or future stamp as stale', () => {
    expect(isFresh(null, now)).toBe(false);
    expect(isFresh('soon', now)).toBe(false);
    expect(isFresh(String(now + 10_000), now)).toBe(false);
  });
});

describe('selectEvictions — R-013 50 MB ceiling, oldest first', () => {
  it('evicts nothing under the ceiling', () => {
    expect(API_CACHE_MAX_BYTES).toBe(50 * 1024 * 1024);
    expect(selectEvictions([{ url: 'a', size: 10, cachedAt: 1 }], 100)).toEqual([]);
  });

  it('evicts the oldest entries until the rest fits', () => {
    const entries = [
      { url: 'new', size: 40, cachedAt: 3 },
      { url: 'old', size: 40, cachedAt: 1 },
      { url: 'mid', size: 40, cachedAt: 2 },
    ];
    expect(selectEvictions(entries, 100)).toEqual(['old']);
    expect(selectEvictions(entries, 40)).toEqual(['old', 'mid']);
  });
});

describe('isPublicCacheName — what a logout leaves', () => {
  it('keeps only build and deployment-config caches', () => {
    expect(isPublicCacheName('workbox-precache-v2-https://kamerplanter.example/')).toBe(true);
    expect(isPublicCacheName('kp-static-assets')).toBe(true);
    expect(isPublicCacheName('kp-runtime-config')).toBe(true);
    expect(isPublicCacheName('kp:user_1:tenant_a')).toBe(false);
    expect(isPublicCacheName('kp-sw-state')).toBe(false);
    expect(isPublicCacheName('something-else')).toBe(false);
  });
});

describe('kill switch parsing (G-W9 e)', () => {
  it.each([undefined, '', 'true', 'TRUE', '1', 'yes', true])('keeps caching on for %s', (value) => {
    expect(isPwaCachingEnabled(value)).toBe(true);
  });

  it.each(['false', 'FALSE', ' false ', '0', 'off', 'no', false, 0])('switches caching off for %s', (value) => {
    expect(isPwaCachingEnabled(value)).toBe(false);
  });

  it('reads the flag from the generated runtime-config.js text', () => {
    const generated = (value: string) =>
      `window.__RUNTIME_CONFIG__ = {\n  KAMERPLANTER_MODE: "full",\n  PWA_CACHING_ENABLED: "${value}"\n};\n`;
    expect(runtimeConfigDisablesCaching(generated('false'))).toBe(true);
    expect(runtimeConfigDisablesCaching(generated('true'))).toBe(false);
    expect(runtimeConfigDisablesCaching(generated(''))).toBe(false);
    expect(runtimeConfigDisablesCaching('window.__RUNTIME_CONFIG__ = {};')).toBe(false);
    expect(runtimeConfigDisablesCaching("window.__RUNTIME_CONFIG__ = { PWA_CACHING_ENABLED: 'off' };")).toBe(true);
    expect(runtimeConfigDisablesCaching('window.__RUNTIME_CONFIG__ = { "PWA_CACHING_ENABLED": false };')).toBe(true);
  });
});
