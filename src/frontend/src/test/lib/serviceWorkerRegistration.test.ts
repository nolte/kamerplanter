import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import {
  registerServiceWorker,
  activateWaitingWorker,
  unregisterAll,
} from '@/lib/serviceWorkerRegistration';

describe('UI-NFR-012 service worker registration helper', () => {
  const originalNavigator = globalThis.navigator;

  afterEach(() => {
    Object.defineProperty(globalThis, 'navigator', {
      value: originalNavigator,
      configurable: true,
      writable: true,
    });
  });

  it('returns null when navigator is missing (SSR / Node)', async () => {
    Object.defineProperty(globalThis, 'navigator', {
      value: undefined,
      configurable: true,
      writable: true,
    });
    const result = await registerServiceWorker();
    expect(result).toBeNull();
  });

  it('returns null when service workers are unsupported', async () => {
    Object.defineProperty(globalThis, 'navigator', {
      value: {},
      configurable: true,
      writable: true,
    });
    const result = await registerServiceWorker();
    expect(result).toBeNull();
  });

  it('honours the disabled flag', async () => {
    const register = vi.fn();
    Object.defineProperty(globalThis, 'navigator', {
      value: { serviceWorker: { register, getRegistrations: vi.fn() } },
      configurable: true,
      writable: true,
    });
    const result = await registerServiceWorker({ disabled: true });
    expect(result).toBeNull();
    expect(register).not.toHaveBeenCalled();
  });

  it('returns null and swallows the error when register() rejects', async () => {
    const register = vi.fn().mockRejectedValue(new Error('boom'));
    Object.defineProperty(globalThis, 'navigator', {
      value: { serviceWorker: { register, getRegistrations: vi.fn() } },
      configurable: true,
      writable: true,
    });
    const result = await registerServiceWorker();
    expect(result).toBeNull();
    expect(register).toHaveBeenCalledWith('/sw.js', { scope: '/', updateViaCache: 'none' });
  });

  it('passes the waiting registration to onUpdateAvailable', async () => {
    const waiting = {} as ServiceWorker;
    const registration = {
      waiting,
      installing: null,
      addEventListener: vi.fn(),
    } as unknown as ServiceWorkerRegistration;
    const register = vi.fn().mockResolvedValue(registration);
    Object.defineProperty(globalThis, 'navigator', {
      value: { serviceWorker: { register, getRegistrations: vi.fn() } },
      configurable: true,
      writable: true,
    });
    const onUpdateAvailable = vi.fn();
    const result = await registerServiceWorker({ onUpdateAvailable });
    expect(result).toBe(registration);
    expect(onUpdateAvailable).toHaveBeenCalledWith(registration);
  });
});

describe('activateWaitingWorker', () => {
  it('posts SKIP_WAITING to the waiting worker', () => {
    const postMessage = vi.fn();
    const reg = { waiting: { postMessage } } as unknown as ServiceWorkerRegistration;
    activateWaitingWorker(reg);
    expect(postMessage).toHaveBeenCalledWith({ type: 'SKIP_WAITING' });
  });

  it('is a no-op when no worker is waiting', () => {
    expect(() => activateWaitingWorker({ waiting: null } as ServiceWorkerRegistration)).not.toThrow();
  });
});

describe('unregisterAll', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('unregisters every registration the browser knows about', async () => {
    const a = { unregister: vi.fn().mockResolvedValue(true) };
    const b = { unregister: vi.fn().mockResolvedValue(true) };
    Object.defineProperty(globalThis, 'navigator', {
      value: {
        serviceWorker: {
          getRegistrations: vi.fn().mockResolvedValue([a, b]),
          register: vi.fn(),
        },
      },
      configurable: true,
      writable: true,
    });
    await unregisterAll();
    expect(a.unregister).toHaveBeenCalled();
    expect(b.unregister).toHaveBeenCalled();
  });
});
