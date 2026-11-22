import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

/**
 * UI-NFR-012 §3.2 / R-014 (REQ-053 WP 9.1, #2741) — the one registration module.
 *
 * Fresh module per test: the update store and the armed reload are module state.
 */

type Listener = () => void;

interface ContainerDouble {
  register: ReturnType<typeof vi.fn>;
  controller: unknown;
  listeners: Map<string, Listener[]>;
  fire(type: string): void;
}

let container: ContainerDouble;
let reload: ReturnType<typeof vi.fn>;
let originalLocation: Location;

function installContainer(registration: unknown, { controller = {} as unknown } = {}) {
  const listeners = new Map<string, Listener[]>();
  container = {
    register: vi.fn().mockResolvedValue(registration),
    controller,
    listeners,
    fire(type) {
      const current = listeners.get(type) ?? [];
      listeners.set(type, []);
      current.forEach((listener) => listener());
    },
  };
  Object.defineProperty(navigator, 'serviceWorker', {
    configurable: true,
    value: {
      register: container.register,
      get controller() {
        return container.controller;
      },
      addEventListener: (type: string, listener: Listener) => {
        listeners.set(type, [...(listeners.get(type) ?? []), listener]);
      },
      getRegistration: vi.fn().mockResolvedValue(undefined),
      getRegistrations: vi.fn().mockResolvedValue([]),
    },
  });
}

function registrationDouble(waiting: unknown = null) {
  const listeners = new Map<string, Listener>();
  return {
    waiting,
    installing: null as unknown,
    addEventListener: vi.fn((type: string, listener: Listener) => listeners.set(type, listener)),
    listeners,
  };
}

async function load() {
  vi.resetModules();
  return import('@/lib/serviceWorkerRegistration');
}

beforeEach(() => {
  originalLocation = window.location;
  reload = vi.fn();
  Object.defineProperty(window, 'location', { configurable: true, value: { ...originalLocation, reload } });
});

afterEach(() => {
  Object.defineProperty(window, 'location', { configurable: true, value: originalLocation });
  delete (navigator as unknown as Record<string, unknown>).serviceWorker;
  delete window.__RUNTIME_CONFIG__;
  vi.restoreAllMocks();
});

describe('registerServiceWorker', () => {
  it('does nothing without service-worker support', async () => {
    const { registerServiceWorker } = await load();
    await expect(registerServiceWorker()).resolves.toBeNull();
  });

  it('registers the built classic worker at /sw.js in production builds', async () => {
    vi.stubEnv('DEV', false);
    installContainer(registrationDouble());
    const { registerServiceWorker } = await load();
    await registerServiceWorker();
    expect(container.register).toHaveBeenCalledWith('/sw.js', { scope: '/', type: 'classic', updateViaCache: 'none' });
    vi.unstubAllEnvs();
  });

  it('registers the dev server module worker under vite dev, so Web Push works in development', async () => {
    vi.stubEnv('DEV', true);
    installContainer(registrationDouble());
    const { registerServiceWorker } = await load();
    await registerServiceWorker();
    expect(container.register).toHaveBeenCalledWith('/dev-sw.js?dev-sw', {
      scope: '/',
      type: 'module',
      updateViaCache: 'none',
    });
    vi.unstubAllEnvs();
  });

  it('reports a failed registration instead of swallowing it, and never throws', async () => {
    installContainer(registrationDouble());
    container.register.mockRejectedValue(new Error('no worker here'));
    const warn = vi.spyOn(console, 'warn').mockImplementation(() => undefined);
    const { registerServiceWorker } = await load();
    await expect(registerServiceWorker()).resolves.toBeNull();
    expect(warn).toHaveBeenCalledWith(expect.stringContaining('[pwa]'), expect.any(Error));
  });

  it('offers a worker that is already waiting', async () => {
    const registration = registrationDouble({ postMessage: vi.fn() });
    installContainer(registration);
    const lib = await load();
    await lib.registerServiceWorker();
    expect(lib.getWaitingRegistration()).toBe(registration);
  });

  it('offers an update found while a controller is active, not a first install', async () => {
    const registration = registrationDouble();
    installContainer(registration, { controller: null });
    const lib = await load();
    await lib.registerServiceWorker();
    const installing = { state: 'installed', addEventListener: vi.fn() };
    registration.installing = installing;
    registration.listeners.get('updatefound')?.();
    installing.addEventListener.mock.calls[0][1]();
    expect(lib.getWaitingRegistration()).toBeNull();

    container.controller = {};
    registration.listeners.get('updatefound')?.();
    installing.addEventListener.mock.calls[1][1]();
    expect(lib.getWaitingRegistration()).toBe(registration);
  });

  it('hands the namespace to a worker that takes control', async () => {
    installContainer(registrationDouble(), { controller: null });
    const lib = await load();
    const repost = vi.spyOn(await import('@/pwa/offlineData'), 'repostNamespace');
    await lib.registerServiceWorker();
    container.fire('controllerchange');
    expect(repost).toHaveBeenCalled();
  });
});

describe('update banner across tabs (R-014, review finding 7)', () => {
  it('reloads THIS tab when another tab activated the waiting update', async () => {
    const registration = registrationDouble({ postMessage: vi.fn() });
    installContainer(registration);
    const lib = await load();
    await lib.registerServiceWorker();
    expect(lib.getWaitingRegistration()).toBe(registration);

    // Another tab posted SKIP_WAITING; the new worker claims every client.
    container.fire('controllerchange');
    expect(lib.getWaitingRegistration()).toBeNull();
    expect(reload).toHaveBeenCalledTimes(1);
  });

  it('closes the banner and reloads when nothing waits any more at the click', async () => {
    installContainer(registrationDouble());
    const lib = await load();
    const stale = registrationDouble(null) as unknown as ServiceWorkerRegistration;
    lib.markUpdateAvailable(stale);
    lib.activateWaitingWorker(stale);
    expect(lib.getWaitingRegistration()).toBeNull();
    expect(reload).toHaveBeenCalledTimes(1);
  });

  it('posts SKIP_WAITING to a waiting worker and reloads on the controller change', async () => {
    installContainer(registrationDouble());
    const lib = await load();
    const postMessage = vi.fn();
    const registration = { waiting: { postMessage } } as unknown as ServiceWorkerRegistration;
    lib.activateWaitingWorker(registration);
    expect(postMessage).toHaveBeenCalledWith({ type: 'SKIP_WAITING' });
    expect(reload).not.toHaveBeenCalled();
    container.fire('controllerchange');
    expect(reload).toHaveBeenCalledTimes(1);
  });

  it('does not reload on the first install claim of a tab that never saw an update', async () => {
    installContainer(registrationDouble(), { controller: null });
    const lib = await load();
    await lib.registerServiceWorker();
    container.fire('controllerchange');
    expect(reload).not.toHaveBeenCalled();
  });
});

describe('the module is the only way to register', () => {
  it('exports no bare register helper that could skip the kill switch', async () => {
    const lib = await load();
    expect(Object.keys(lib).sort()).toEqual([
      'activateWaitingWorker',
      'getWaitingRegistration',
      'markUpdateAvailable',
      'pwaCachingEnabled',
      'registerServiceWorker',
      'subscribeToUpdate',
      'unregisterAll',
    ]);
  });
});
