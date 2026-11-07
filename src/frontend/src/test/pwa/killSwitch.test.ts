import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { runtimeConfigDisablesCaching } from '@/pwa/cachePolicy';

/**
 * REQ-053 WP 9.1 (#2741), guardrail G-W9 (e): `PWA_CACHING_ENABLED=false` in `runtime-config.js`
 * unregisters the service worker and deletes its caches. Two carriers, both pinned here:
 *
 * - the app (`src/serviceWorkerRegistration.ts`): at boot it reads `window.__RUNTIME_CONFIG__`
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
  const { registerServiceWorker } = await import('@/serviceWorkerRegistration');
  await registerServiceWorker();
}

describe('app-side kill switch', () => {
  it('registers /sw.js when the flag is absent (default on)', async () => {
    await boot();
    expect(register).toHaveBeenCalledWith('/sw.js', { scope: '/', updateViaCache: 'none' });
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

  it('reads /runtime-config.js uncached and self-destructs on an off value', () => {
    const probe = sw.slice(sw.indexOf('async function probeKillSwitch'), sw.indexOf('// API cache plugins'));
    expect(probe).toMatch(/fetch\('\/runtime-config\.js', \{ cache: 'no-store'/);
    expect(probe).toMatch(/runtimeConfigDisablesCaching\(await response\.text\(\)\)\) await selfDestruct\(\)/);
    const destruct = sw.slice(sw.indexOf('async function selfDestruct'), sw.indexOf('async function probeKillSwitch'));
    expect(destruct).toMatch(/caches\.delete\(name\)/);
    expect(destruct).toMatch(/self\.registration\.unregister\(\)/);
  });

  it('probes on activation and on navigations', () => {
    expect(sw).toMatch(/addEventListener\('activate'[\s\S]*?await probeKillSwitch\(\)/);
    expect(sw).toMatch(/event\.request\.mode === 'navigate'[\s\S]*?probeKillSwitch\(\)/);
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
