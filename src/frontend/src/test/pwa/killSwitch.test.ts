import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { runtimeConfigDisablesCaching } from '@/pwa/cachePolicy';

/**
 * REQ-053 WP 9.1 (#2741), guardrail G-W9 (e): `PWA_CACHING_ENABLED=false` in `runtime-config.js`
 * unregisters the service worker and deletes its caches. Two carriers, both pinned here:
 *
 * - the app (`src/lib/serviceWorkerRegistration.ts`): at boot it reads `window.__RUNTIME_CONFIG__`
 *   and unregisters + clears instead of registering;
 * - the worker (`src/sw.ts`): it reads the text of `/runtime-config.js` itself, so the switch also
 *   reaches a tab running an older app build.
 *
 * And the deployment writes the key: the image entrypoint, the dev entrypoint and the Helm init
 * container all render it with the default `true`.
 */

const root = process.cwd();
let register: ReturnType<typeof vi.fn>;
let unregister: ReturnType<typeof vi.fn>;
let deleted: string[];

beforeEach(() => {
  vi.resetModules();
  deleted = [];
  register = vi.fn().mockResolvedValue({ waiting: null, installing: null, addEventListener: vi.fn() });
  unregister = vi.fn().mockResolvedValue(true);
  Object.defineProperty(navigator, 'serviceWorker', {
    configurable: true,
    value: {
      register,
      controller: null,
      addEventListener: vi.fn(),
      getRegistration: vi.fn().mockResolvedValue(undefined),
      getRegistrations: vi.fn().mockResolvedValue([{ unregister }]),
    },
  });
  vi.stubGlobal('caches', {
    keys: vi.fn().mockResolvedValue(['workbox-precache-v2-x', 'kp:user_1:tenant_a']),
    delete: vi.fn(async (name: string) => {
      deleted.push(name);
      return true;
    }),
  });
});

afterEach(() => {
  delete window.__RUNTIME_CONFIG__;
  delete (navigator as unknown as Record<string, unknown>).serviceWorker;
  vi.unstubAllGlobals();
});

async function boot() {
  const { registerServiceWorker } = await import('@/lib/serviceWorkerRegistration');
  await registerServiceWorker();
}

describe('app-side kill switch', () => {
  it('registers /sw.js when the flag is absent (default on)', async () => {
    await boot();
    expect(register).toHaveBeenCalledTimes(1);
    expect(unregister).not.toHaveBeenCalled();
  });

  it('registers when the deployment says true', async () => {
    window.__RUNTIME_CONFIG__ = { PWA_CACHING_ENABLED: 'true' };
    await boot();
    expect(register).toHaveBeenCalledTimes(1);
  });

  it('PWA_CACHING_ENABLED=false unregisters and deletes every cache instead of registering', async () => {
    window.__RUNTIME_CONFIG__ = { PWA_CACHING_ENABLED: 'false' };
    await boot();
    expect(register).not.toHaveBeenCalled();
    expect(unregister).toHaveBeenCalledTimes(1);
    expect(deleted.sort()).toEqual(['kp:user_1:tenant_a', 'workbox-precache-v2-x']);
  });
});

describe('worker-side kill switch (src/sw.ts)', () => {
  const sw = readFileSync(join(root, 'src/sw.ts'), 'utf8');
  const probe = sw.slice(sw.indexOf('async function probeKillSwitch'), sw.indexOf('// Strategies'));
  const destruct = sw.slice(sw.indexOf('async function selfDestruct'), sw.indexOf('async function probeKillSwitch'));

  it('reads /runtime-config.js uncached and self-destructs on an off value', () => {
    expect(probe).toMatch(/fetch\('\/runtime-config\.js', \{\s*cache: 'no-store'/);
    expect(probe).toMatch(/runtimeConfigDisablesCaching\(await response\.text\(\)\)\) await selfDestruct\(\)/);
  });

  it('bounds the probe with an abort timeout (review finding 3a)', () => {
    expect(sw).toMatch(/const KILL_SWITCH_PROBE_TIMEOUT_MS = 3_000;/);
    expect(probe).toMatch(/setTimeout\(\(\) => abort\.abort\(\), KILL_SWITCH_PROBE_TIMEOUT_MS\)/);
    expect(probe).toMatch(/signal: abort\.signal/);
  });

  it('does not hold activation on the probe (fetches wait for activate)', () => {
    const activate = sw.slice(sw.indexOf("self.addEventListener('activate'"), sw.indexOf("self.addEventListener('message'"));
    expect(activate).toMatch(/event\.waitUntil\(self\.clients\.claim\(\)\);/);
    expect(activate).not.toMatch(/waitUntil\([^)]*probeKillSwitch/);
    expect(activate).toMatch(/void probeKillSwitch\(\);/);
    expect(sw).toMatch(/event\.request\.mode === 'navigate'[\s\S]*?probeKillSwitch\(\)/);
  });

  it('deletes every cache AND every IndexedDB database before unregistering (finding 3c)', () => {
    expect(destruct).toMatch(/Promise\.all\(\[deleteCaches\(\), deleteAllDatabases\(\)\]\)/);
    expect(destruct).toMatch(/self\.registration\.unregister\(\)/);
  });

  it('serves /runtime-config.js network-only, never from a cache (finding 3b)', () => {
    expect(sw).toMatch(/url\.pathname === '\/runtime-config\.js',\s*networkOnly,/);
    expect(sw).not.toMatch(/RUNTIME_CONFIG_CACHE|kp-runtime-config/);
  });
});

describe('every runtime-config.js generator writes the key, default true', () => {
  const generators = {
    'docker-entrypoint.d/10-runtime-config.sh': readFileSync(join(root, 'docker-entrypoint.d/10-runtime-config.sh'), 'utf8'),
    'docker-entrypoint.dev.sh': readFileSync(join(root, 'docker-entrypoint.dev.sh'), 'utf8'),
    'helm/kamerplanter/values.yaml': readFileSync(join(root, '../../helm/kamerplanter/values.yaml'), 'utf8'),
  };

  it.each(Object.keys(generators))('%s renders PWA_CACHING_ENABLED', (name) => {
    const text = generators[name as keyof typeof generators];
    expect(text).toContain('PWA_CACHING_ENABLED: "${PWA_CACHING_ENABLED:-true}"');
  });

  it('the rendered default keeps caching on and an off value is read by the worker', () => {
    expect(runtimeConfigDisablesCaching('  PWA_CACHING_ENABLED: "true"\n')).toBe(false);
    expect(runtimeConfigDisablesCaching('  PWA_CACHING_ENABLED: "false"\n')).toBe(true);
  });

  it('the placeholder in public/ stays without the key (vite dev = caching on)', () => {
    const placeholder = readFileSync(join(root, 'public/runtime-config.js'), 'utf8');
    expect(runtimeConfigDisablesCaching(placeholder)).toBe(false);
  });
});
